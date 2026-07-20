#!/usr/bin/env python3
"""Run ONE (split, arm) calibration cell on the REAL matched-path FRF and write out/cells/<id>.json.
P1 deliverable = one converged sanity cell; reused by P2/P4. Resumable: skips an existing cell json.

Usage:  run_cell.py --arm M3 --nobs 8 --split 0 [--zeta 0.01] [--seed ...] [--force]
"""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import real_arms as ra

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
DR_MIN = 30.0           # keep channels with in-band dynamic range > 30x (15 dB)


def select_split(ch, meas, nobs, split, dr_min=DR_MIN):
    """Good channels (dynamic range), ordered by z; observed = nobs spread; held-out = the rest (spread)."""
    didx = {d: i for i, d in enumerate(meas["daq"])}
    good = [k for k, d in enumerate(ch.daq) if meas["dyn_range"][didx[d]] > dr_min]
    z = ch.coords[good, 2]
    order = [good[i] for i in np.argsort(z)]
    n = len(order)
    # rotate the observed picks by `split` for MC variety
    obs_idx_in_order = (np.linspace(0, n - 1, nobs).astype(int) + split) % n
    obs = sorted({order[i] for i in obs_idx_in_order})
    rest = [k for k in order if k not in set(obs)]
    keep = np.linspace(0, len(rest) - 1, min(16, len(rest))).astype(int)
    held = sorted({rest[i] for i in keep})
    return obs, held, didx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="M3")
    ap.add_argument("--nobs", type=int, default=8)
    ap.add_argument("--split", type=int, default=0)
    ap.add_argument("--zeta", type=float, default=rf.ZETA_NOM)
    ap.add_argument("--seed", type=int, default=20260617)
    ap.add_argument("--warmup", type=int, default=1000)
    ap.add_argument("--samples", type=int, default=1000)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    cid = f"split{a.split}_n{a.nobs}_z{a.zeta}_{a.arm}"
    (OUT / "cells").mkdir(parents=True, exist_ok=True)
    cf = OUT / "cells" / f"{cid}.json"
    if cf.exists() and not a.force:
        print("exists, skip:", cf.name); return

    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    obs, held, didx = select_split(ch, meas, a.nobs, a.split)

    fr = meas["freqs"]
    bmask = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1])
    freqs = fr[bmask]
    # measured target log|H| (Nf, Nobs) and quality weight on observed channels
    obs_daq = [ch.daq[k] for k in obs]
    Hobs = np.array([np.abs(meas["H"][didx[d]][bmask]) for d in obs_daq]).T      # (Nf, Nobs)
    Wobs = np.array([meas["weight"][didx[d]][bmask] for d in obs_daq]).T
    target = np.log(np.maximum(Hobs, 1e-30))
    resp_rows_obs = ch.rows[obs]
    coords_obs = ch.coords[obs]

    # empirical global gain c0 = median(target - fem_logmag(theta=1)) over observed
    fem1 = rf.fem_logmag(R, freqs, np.ones(9), resp_rows_obs, ch.drive_row, zeta=a.zeta)
    c0 = float(np.median(target - fem1))

    if not (OUT / "run_config.json").exists() or a.force:
        (OUT / "run_config.json").write_text(json.dumps({
            "testbed": "plain_shocksat_9group", "uses_tray": False, "observable": "matched_path_real_frf",
            "impact_xyz": list(rf.IMPACT_XYZ), "impact_axis": rf.IMPACT_AXIS, "drive_node": ch.drive_node,
            "band_hz": list(rf.BAND), "nfreq_band": int(bmask.sum()), "df_hz": float(fr[1] - fr[0]),
            "n_channels_mapped": len(ch.daq), "sigma_meas": ra.SIGMA_MEAS, "zeta_nom": rf.ZETA_NOM,
            "global_gain_c0_empirical": c0, "proc": rf.PROC, "groups": rf.GNAMES,
            "single_hit_quality_weight": True, "n_raw_hits": 1, "n_impact_locations": 1}, indent=2))

    t0 = time.time()
    flat, diag = ra.run_arm(a.arm, R, freqs, target, resp_rows_obs, ch.drive_row, coords_obs, c0,
                            zeta=a.zeta, num_warmup=a.warmup, num_samples=a.samples, seed=a.seed)
    dt = time.time() - t0
    conv = (diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02)
    theta = np.exp(flat["log_theta"])
    rec = {
        "cell_id": cid, "arm": a.arm, "split": a.split, "n_observed": len(obs), "n_heldout": len(held),
        "observed_daq": obs_daq, "heldout_daq": [ch.daq[k] for k in held],
        "zeta": a.zeta, "seed": a.seed, "runtime_s": dt, "diag": diag,
        "not_yet_converged": (not conv),
        "global_gain": {"c0_empirical": c0,
                        "post_med": float(np.median(flat["gain"])),
                        "post_lo": float(np.percentile(flat["gain"], 2.5)),
                        "post_hi": float(np.percentile(flat["gain"], 97.5))},
        "sigma_d": ({"med": float(np.median(flat["sigma_d"])),
                     "lo": float(np.percentile(flat["sigma_d"], 2.5)),
                     "hi": float(np.percentile(flat["sigma_d"], 97.5))} if a.arm != "M0" else None),
        "theta_post": {g: {"med": float(np.median(theta[:, i])),
                           "lo": float(np.percentile(theta[:, i], 2.5)),
                           "hi": float(np.percentile(theta[:, i], 97.5))}
                       for i, g in enumerate(rf.GNAMES)},
    }
    cf.write_text(json.dumps(rec, indent=2))
    print(f"{cid}: {'CONVERGED' if conv else 'NOT-YET-CONVERGED'}  "
          f"R-hat {diag['max_rhat']:.3f} ESS {diag['min_ess']:.0f} div {diag['divergences']} "
          f"| gain {rec['global_gain']['post_med']:.2f} (c0 {c0:.2f}) "
          f"| sigma_d {rec['sigma_d']['med'] if rec['sigma_d'] else 0:.3f} | {dt:.0f}s")


if __name__ == "__main__":
    main()
