#!/usr/bin/env python3
"""Post-hoc frequency-grid sensitivity for the IFT real-data comparison.

This is deliberately scoped: it reuses the split-0 posterior samples and varies
the frequency grid used to compute held-out QOIs. It does not rerun NUTS on each
grid, so it is a YELLOW diagnostic for the prompt's invariance request, not a
certified posterior-invariance result.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import heldout_qoi as hq
import ift_arm as IFT
import realfrf as rf
import score as SC

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
PROV = WS / "provenance"


def _aggregate(scores):
    keys = ("interval_score", "crps", "logpd")
    out = {k: {"mean": float(np.mean([s[k] for s in scores])), "med": float(np.median([s[k] for s in scores]))} for k in keys}
    out["coverage"] = {"mean": float(np.mean([s["covered"] for s in scores])), "med": float(np.median([s["covered"] for s in scores]))}
    out["zstd"] = {"mean": float(np.nanmean([s["z"] for s in scores])), "std": float(np.nanstd([s["z"] for s in scores]))}
    return out


def _score_qois(draw_peak, draw_band, truth_peak, truth_band):
    peak_scores = [SC.score_qoi(draw_peak[:, k], truth_peak[k]) for k in range(draw_peak.shape[1])]
    band_scores = [SC.score_qoi(draw_band[:, k], truth_band[k]) for k in range(draw_band.shape[1])]
    return {"peak": _aggregate(peak_scores), "band": _aggregate(band_scores)}


def _ift_predictions(split, samples, mask, n_draws=80):
    rng = np.random.default_rng(12345 + int(mask.sum()))
    freqs = split["freqs"][mask]
    y_ho = split["y_ho"][mask]
    n_ho = y_ho.shape[1]
    idx = np.linspace(0, len(samples["beta"]) - 1, min(n_draws, len(samples["beta"]))).astype(int)
    peak = np.zeros((len(idx), n_ho))
    band = np.zeros((len(idx), n_ho))
    for j, s in enumerate(idx):
        mu, var = IFT._ift_moments_np(
            split["R"],
            freqs,
            split["ho_rows"],
            split["drive_row"],
            samples["theta"][s],
            samples["beta"][s],
            samples["gain_c"][s],
        )
        mag = np.exp(mu + rng.normal(0.0, np.sqrt(var + IFT.SIGMA_MEAS ** 2)))
        for k in range(n_ho):
            peak[j, k] = rf.core.qoi_peak(mag[:, k])
            band[j, k] = rf.core.qoi_band(mag[:, k], freqs)
    truth = np.exp(y_ho)
    truth_peak = np.array([rf.core.qoi_peak(truth[:, k]) for k in range(n_ho)])
    truth_band = np.array([rf.core.qoi_band(truth[:, k], freqs) for k in range(n_ho)])
    return _score_qois(peak, band, truth_peak, truth_band)


def _l5_predictions(split, mask, n_draws=120):
    l5 = np.load(PROV / "l5_theta_0.npz")
    theta = l5["theta"]
    idx = np.linspace(0, len(theta) - 1, min(n_draws, len(theta))).astype(int)
    freqs = split["freqs"][mask]
    all_rows = np.vstack([split["obs_rows"], split["ho_rows"]])
    lm = rf.fem_logmag_batch(split["R"], freqs, theta[idx], all_rows, split["drive_row"], zeta=rf.ZETA_NOM)
    n_obs = len(split["obs_daqs"])
    didx = {d: i for i, d in enumerate(split["meas"]["daq"])}
    fb_full = (split["meas"]["freqs"] >= rf.BAND[0]) & (split["meas"]["freqs"] <= rf.BAND[1])
    w_obs_full = np.array([split["meas"]["weight"][didx[d]][fb_full] for d in split["obs_daqs"]]).T
    w_obs = w_obs_full[mask]
    y_obs = split["y_obs"][mask]
    c = np.array([hq.wmedian((y_obs - lm[j, :, :n_obs]).ravel(), w_obs.ravel()) for j in range(len(idx))])
    pred = np.exp(lm[:, :, n_obs:] + c[:, None, None])
    n_ho = pred.shape[2]
    peak = np.zeros((len(idx), n_ho))
    band = np.zeros((len(idx), n_ho))
    for j in range(len(idx)):
        for k in range(n_ho):
            peak[j, k] = rf.core.qoi_peak(pred[j, :, k])
            band[j, k] = rf.core.qoi_band(pred[j, :, k], freqs)
    truth = np.exp(split["y_ho"][mask])
    truth_peak = np.array([rf.core.qoi_peak(truth[:, k]) for k in range(n_ho)])
    truth_band = np.array([rf.core.qoi_band(truth[:, k], freqs) for k in range(n_ho)])
    return _score_qois(peak, band, truth_peak, truth_band)


def _rel_shift(a, base):
    return float((a - base) / max(abs(base), 1e-30))


def main():
    OUT.mkdir(exist_ok=True)
    split = IFT.load_split(seed=0, obs_frac=0.6)
    samples = np.load(OUT / "ift_split_0_headline_samples.npz")
    n = len(split["freqs"])
    grids = {
        "full_173": np.ones(n, dtype=bool),
        "every_2nd_87": (np.arange(n) % 2) == 0,
        "every_4th_44": (np.arange(n) % 4) == 0,
    }
    arms = {"IFT": {}, "L5": {}}
    for gname, mask in grids.items():
        arms["IFT"][gname] = _ift_predictions(split, samples, mask)
        arms["L5"][gname] = _l5_predictions(split, mask)

    base = {
        arm: {
            qoi: arms[arm]["full_173"][qoi]["interval_score"]["med"]
            for qoi in ("peak", "band")
        }
        for arm in arms
    }
    shifts = {}
    for arm in arms:
        shifts[arm] = {}
        for gname in grids:
            shifts[arm][gname] = {}
            for qoi in ("peak", "band"):
                shifts[arm][gname][qoi + "_interval_rel_shift"] = _rel_shift(
                    arms[arm][gname][qoi]["interval_score"]["med"], base[arm][qoi]
                )

    rec = {
        "study": "ift_real_validation_20260619_codex",
        "kind": "posthoc_frequency_grid_qoi_sensitivity",
        "status": "YELLOW",
        "posterior_invariance_certified": False,
        "reason": (
            "Uses the same split-0 posterior samples and varies only the QOI frequency grid. "
            "Because the headline IFT run is non-converged and this does not rerun the sampler "
            "on each grid, it is a bounded diagnostic, not a certified IFT invariance result."
        ),
        "split_seed": 0,
        "grids": {k: {"n_freq": int(v.sum()), "spacing": "subsampled from copied 45-260 Hz StatFEM grid"} for k, v in grids.items()},
        "arms": arms,
        "relative_shifts_vs_full": shifts,
    }
    (OUT / "discretization_sensitivity.json").write_text(json.dumps(rec, indent=2))
    print("wrote out/discretization_sensitivity.json")


if __name__ == "__main__":
    main()
