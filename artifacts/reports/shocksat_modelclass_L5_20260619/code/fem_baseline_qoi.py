#!/usr/bin/env python3
"""Phase D1 — the 'beat this' baseline for the GOAL: the ORIGINAL (uncalibrated, deterministic) FEM's held-out
peak-QOI error, vs the calibrated twin's CI coverage, on the SAME held-out channels.

Original FEM = nominal theta=1, zeta=1% (+ optional measurement window), one deterministic prediction (NO UQ),
with the SAME global units-gain c fit on observed channels (the gain is a units conversion, not a physics
calibration). A deterministic point has no CI -> we report how far it MISSES the held-out truth (median |error|,
fraction off by >3 dB / >6 dB). The calibrated twin (dampcorr ARM1 = L5 freq + window) COVERS 94-97% on the same
split; the contrast = 'honest calibrated CI vs confidently-wrong point' = the GOAL's 'better than the original FEM'.
Output: out/fem_baseline_qoi_seed<seed>.json.
"""
from __future__ import annotations
import json, sys, time
from types import SimpleNamespace
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq
import dampcorr_qoi as dc

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"


def run(seed=0, obs_frac=0.6, write=True):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    tau = -(rf.PROC["N"] - 1) / (rf.FS * np.log(rf.PROC["exp_end"]))

    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    all_rows = np.vstack([obs_rows, ho_rows]); n_o = len(obs_pos); n_ho = len(ho_pos)

    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T
    wq_obs = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T
    peak_tru_ho = np.array([hq.SC_qoi_peak(np.exp(tru_ho[:, c])) for c in range(n_ho)])

    theta1 = np.ones((1, 9))
    eta_uniform = np.full(R.A.shape[1], 2.0 * rf.ZETA_NOM)
    res = {}
    for tag, use_w in (("FEM_nominal_1pct", False), ("FEM_nominal_1pct_window", True)):
        lm = dc.fem_logmag_batch_permode(R, freqs, theta1, all_rows, ch.drive_row,
                                         eta_uniform, tau if use_w else None)[0]
        lm_obs = lm[:, :n_o]; lm_ho = lm[:, n_o:]
        c = hq.wmedian((tru_obs - lm_obs).ravel(), wq_obs.ravel())     # units-gain on observed
        ph = np.exp(lm_ho + c)
        peak_pred = np.array([hq.SC_qoi_peak(ph[:, k]) for k in range(n_ho)])
        err_db = 20.0 * np.log10(peak_pred / peak_tru_ho)              # signed dB error per held-out channel
        ab = np.abs(err_db)
        res[tag] = {"gain_c": float(c), "median_abs_err_db": float(np.median(ab)),
                    "frac_off_gt3db": float(np.mean(ab > 3)), "frac_off_gt6db": float(np.mean(ab > 6)),
                    "max_abs_err_db": float(np.max(ab)), "mean_signed_err_db": float(np.mean(err_db))}

    # calibrated-twin contrast (same split): pull ARM1 (L5 freq + window) from dampcorr if present
    twin = None
    dcf = OUT / f"dampcorr_qoi_seed{seed:02d}.json"
    if dcf.exists():
        dd = json.load(open(dcf))["arms"]["ARM1_uniform1pct_plus_window"]["scores_theta_plus_qoi_discrepancy"]["peak"]
        twin = {"coverage_frac": dd["coverage_frac"], "interval_score_mean": dd["interval_score_mean"],
                "mean_width_db": dd.get("mean_width_db"), "z_std": dd.get("z_std")}

    rec = {"deliverable": "Phase-D1 original-FEM held-out QOI baseline (beat-this) vs calibrated twin",
           "split_seed": seed, "n_observed": n_o, "n_heldout": n_ho,
           "original_fem_point": res, "calibrated_twin_L5_window": twin, "runtime_s": time.time() - t0}
    if write:
        OUT.mkdir(exist_ok=True)
        (OUT / f"fem_baseline_qoi_seed{seed:02d}.json").write_text(json.dumps(rec, indent=2))
    print(f"seed {seed}: held out {n_ho} channels")
    for tag, v in res.items():
        print(f"  ORIGINAL {tag:24s} median|err| {v['median_abs_err_db']:.1f} dB | "
              f">3dB {v['frac_off_gt3db']*100:.0f}% >6dB {v['frac_off_gt6db']*100:.0f}% | max {v['max_abs_err_db']:.1f} dB")
    if twin:
        print(f"  CALIBRATED twin (L5+window): coverage {twin['coverage_frac']*100:.0f}% "
              f"interval {twin['interval_score_mean']:.0f} width {twin['mean_width_db']:.1f} dB")
    print(f"  runtime {rec['runtime_s']:.1f}s")
    return rec


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(seed=seed)
