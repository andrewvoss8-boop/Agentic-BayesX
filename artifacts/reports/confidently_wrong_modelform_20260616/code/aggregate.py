#!/usr/bin/env python3
"""Aggregate per-cell JSONs into out/sweep_summary.json (the single schema the figures read).
Also records the injected band-average discrepancy std per delta (the thermometer reference)."""
from __future__ import annotations

import glob
import json
from pathlib import Path

import numpy as np

import core
import run_sweep as rs

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"

freqs = core.freq_grid()
logf = np.log(freqs)
g = (logf - logf.min()) / (logf.max() - logf.min())
bmask = core.band_mask(freqs, *rs.QOI_BAND)


def inj_band_avg(delta):
    std = delta / 6.0 + (delta - delta / 6.0) * g
    return float(std[bmask].mean())


def load_cells():
    return [json.load(open(p)) for p in glob.glob(str(OUT / "cell_*.json"))]


def arm_rows(cells, cls, arm, observed):
    rows = [r for r in cells if r["class"] == cls and r["arm"] == arm and r.get("observed") == observed]
    rows = sorted(rows, key=lambda r: r["level"])
    out = []
    for r in rows:
        if arm == "A0":
            out.append({"level": r["level"],
                        "det_qoi_err_db": [v["err_db"] for v in r["det_qoi"].values()]})
            continue
        hc = r["heldout_coverage"]
        aw = [a["width"] for a in r["alpha_intervals"]]
        out.append({
            "level": r["level"], "converged": r["converged"],
            "max_rhat": r["nuts"]["max_rhat"], "min_ess": r["nuts"]["min_ess"],
            "div_frac": r["nuts"]["div_frac"],
            "cov_truth": hc["truth_frac"], "cov_noisy": hc["noisy_frac"],
            "sigma_d_med": r["sigma_d"]["med"], "sigma_d_lo": r["sigma_d"]["lo"],
            "sigma_d_hi": r["sigma_d"]["hi"],
            "qoi_covered": r["qoi_covered"], "qoi_n": r["qoi_n"],
            "alpha": r["alpha_intervals"], "alpha_width_mean": float(np.mean(aw)),
            "injected_band_avg_std": inj_band_avg(r["level"]),
            "injected_hi_std": r["level"],
        })
    return out


def main():
    cells = load_cells()
    summary = {}
    # main correlated class (observed Ch1/Ch2)
    summary["correlated"] = {a: arm_rows(cells, "correlated", a, [0, 1]) for a in ["A0", "A1", "A2", "A3"]}
    # missing-mode class
    summary["missingmode"] = {a: arm_rows(cells, "missingmode", a, [0, 1]) for a in ["A0", "A1", "A2", "A3"]}
    # alt-channel sensitivity (observed Ch3/Ch4)
    summary["altchannel"] = {a: arm_rows(cells, "correlated", a, [2, 3]) for a in ["A1", "A2"]}
    summary["meta"] = {"deltas": rs.DELTAS, "mm_severities": rs.MM_SEVERITIES,
                       "sigma_meas": rs.SIGMA_MEAS, "nominal": 0.95,
                       "alpha_truth_main": rs.ALPHA_TRUE.tolist()}
    json.dump(summary, open(OUT / "sweep_summary.json", "w"), indent=2)
    # quick console view
    for arm in ["A1", "A2", "A3"]:
        rows = summary["correlated"][arm]
        print(arm, "cov_noisy:", [f"{r['level']:.2f}:{r['cov_noisy']:.2f}" for r in rows],
              "| sigma_d:", [f"{r['sigma_d_med']:.2f}" for r in rows])


if __name__ == "__main__":
    main()
