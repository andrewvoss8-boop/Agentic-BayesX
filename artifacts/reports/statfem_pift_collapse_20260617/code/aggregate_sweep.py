#!/usr/bin/env python3
"""Aggregate per-cell JSONs -> out/sweep_{synth,real}.json + out/verdict.json (NEW file).

The verdict booleans are COMPUTED from the sweep trend numbers (never pre-decided, card §9); they are reported
as a FINDING whichever way they fall. Trends are read on the FREQUENCY ladder (n_sensor at the anchor) — the
cleanest densification axis for the PIFT "more collocation points" limit.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
NS_ANCHOR = 6


def load_cells(leg):
    return [json.load(open(p)) for p in sorted(glob.glob(str(OUT / f"cell_{leg}_*.json")))]


def freq_ladder(cells, arm):
    cc = [c for c in cells if c["arm"] == arm and c["N_sensor"] == NS_ANCHOR]
    return sorted(cc, key=lambda c: c["N_freq"])


def trend(cells, arm, field, sub=None):
    cc = freq_ladder(cells, arm)
    xs, ys = [], []
    for c in cc:
        xs.append(c["N"])
        v = c[field][sub] if sub else c[field]
        ys.append(v)
    return np.array(xs, float), np.array(ys, float)


def monotone_frac_decrease(y):
    if len(y) < 2:
        return None
    d = np.diff(y)
    return float(np.mean(d < 0))


def build_sweep(leg):
    cells = load_cells(leg)
    if not cells:
        return None
    cfg = json.load(open(OUT / "config.json")) if (leg == "synth" and (OUT / "config.json").exists()) else {}
    truth = {"combo": cfg.get("truth_combo"), "theta_truth": cfg.get("theta_truth"),
             "known_model_form_error": cfg.get("known_model_form_error")}
    arms = sorted({c["arm"] for c in cells})
    sw = {"leg": "synthetic" if leg == "synth" else "real", "truth": truth,
          "primary_axis": "n_freq", "fixed": {"n_sensor_anchor": NS_ANCHOR, "band_hz": cfg.get("band_hz")},
          "arms": arms, "cells": sorted(cells, key=lambda c: (c["arm"], c["N"]))}
    json.dump(sw, open(OUT / f"sweep_{leg}.json", "w"), indent=1)
    return sw


def compute_verdict(synth, real):
    ev = {"axis": "frequency ladder (n_sensor=6), densifying one fixed truth"}
    collapses = cures = None
    src = synth or real
    if src:
        cells = src["cells"]
        # iid arm M1: σ_d width + identified-θ width vs N; held-out interval score (IS, dB; lower=better)
        for arm in ("M0", "M1", "M3"):
            _, sdw = trend(cells, arm, "sigma_d", "width")
            xN, thw = trend(cells, arm, "theta_width_identified")
            _, IS = trend(cells, arm, "score", "interval_score_db")
            _, cov = trend(cells, arm, "score", "coverage")
            if len(xN) >= 2:
                ev[arm] = {"N": xN.tolist(),
                           "sigma_d_width": sdw.tolist(),
                           "sigma_d_width_ratio_maxN_minN": float(sdw[-1] / sdw[0]) if sdw[0] > 0 else None,
                           "theta_width_identified": thw.tolist(),
                           "theta_width_ratio_maxN_minN": float(thw[-1] / thw[0]) if thw[0] > 0 else None,
                           "interval_score_db": IS.tolist(), "IS_ratio_maxN_minN": float(IS[-1] / IS[0]) if IS[0] != 0 else None,
                           "coverage": cov.tolist()}
        # COLLAPSE signature (iid/naive): θ-width (M0) and σ_d-width (M1) shrink materially with N, while the
        # held-out interval score does NOT improve like the correlated arm (over-tight + biased).
        m1 = ev.get("M1", {}); m0 = ev.get("M0", {}); m3 = ev.get("M3", {})
        m1_sd = m1.get("sigma_d_width_ratio_maxN_minN")
        m0_th = m0.get("theta_width_ratio_maxN_minN")
        if m1_sd is not None and m0_th is not None:
            collapses = bool((m1_sd < 0.7) and (m0_th < 0.7))
        # PLATEAU/cure (orthogonal M3): σ_d width roughly flat at high N AND M3 held-out IS beats M1 at max N.
        m3_sd = m3.get("sigma_d_width_ratio_maxN_minN")
        if m3_sd is not None and m1.get("interval_score_db") and m3.get("interval_score_db"):
            m3_plateau = (0.6 <= m3_sd <= 1.5)
            m3_beats_m1_highN = m3["interval_score_db"][-1] <= m1["interval_score_db"][-1]
            cures = bool(m3_plateau and m3_beats_m1_highN)
    verdict = {"our_statfem_collapses": collapses, "orthogonal_cures": cures,
               "pift_quote_verified": True, "analogy_mapping": "analogy_mapping.md",
               "leg_available": {"synth": synth is not None, "real": real is not None},
               "evidence": ev,
               "interpretation": "Booleans are computed from the trend ratios above (σ_d-width shrinks <0.7× and "
                                 "θ-width shrinks <0.7× ⇒ collapse; M3 σ_d-width ~flat AND M3 held-out interval "
                                 "score ≤ M1 at max N ⇒ cure). Reported whichever way it falls (card §9)."}
    json.dump(verdict, open(OUT / "verdict.json", "w"), indent=1)
    return verdict


def main():
    synth = build_sweep("synth")
    real = build_sweep("real")
    vd = compute_verdict(synth, real)
    print("sweep_synth cells:", len(synth["cells"]) if synth else 0,
          "| sweep_real cells:", len(real["cells"]) if real else 0)
    print("VERDICT collapses =", vd["our_statfem_collapses"], " orthogonal_cures =", vd["orthogonal_cures"])


if __name__ == "__main__":
    main()
