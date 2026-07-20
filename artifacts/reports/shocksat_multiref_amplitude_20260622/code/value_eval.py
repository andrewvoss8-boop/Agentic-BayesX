#!/usr/bin/env python3
"""Value of L5 model-updating on the NON-HARD sensors (Andrew's Q2). Proper skill comparison on held-out channels:
  twin   = calibrated L5 (theta posterior) + uniform zeta=1% + window (ARM1, our best) + pooled QOI discrepancy
  FEM    = original nominal theta=1 deterministic point (+window), units-gain only (no UQ)
  clim   = no-skill calibrated baseline: predict each held-out channel's peak from the POPULATION of OBSERVED
           channel peaks (knows nothing channel-specific) -- the bar the twin must beat to show it carries
           location information.
Metrics per held-out channel: CRPS, interval score, coverage (twin); CRPS (clim); |error| dB (FEM point).
Skill = 1 - CRPS_twin / CRPS_clim  (>0 => the twin is better than guessing the population). Reported NON-HARD vs
HARD, and binned by sensor->FEM-node snap distance. Output: out/value_eval_seed<seed>.json.
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
import score as SC

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
HARD = {4, 27, 38, 40, 52, 69, 92, 98}


def run(seed=0, obs_frac=0.6, n_draws=400, warmup=1000, samples=1000, chains=4, write=True):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    tau = -(rf.PROC["N"] - 1) / (rf.FS * np.log(rf.PROC["exp_end"]))
    eta = np.full(R.A.shape[1], 2.0 * rf.ZETA_NOM)

    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    hard_ho = np.array([1 if d in HARD else 0 for d in ho_daqs])
    snap_ho = np.array([ch.snap_in[p] for p in ho_pos])

    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    theta_post, sigw2, cdiag = mf.calibrate_modal(R, np.array([p[0] for p in pairs]),
                                                  np.array([p[1] for p in pairs]),
                                                  seed=20260617, warmup=warmup, samples=samples, chains=chains)
    sub = np.linspace(0, theta_post.shape[0] - 1, min(theta_post.shape[0], n_draws)).astype(int)
    thsub = theta_post[sub]
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]; allr = np.vstack([obs_rows, ho_rows]); n_o = len(obs_pos)

    # twin draws (ARM1) + FEM-deterministic point (theta=1), both +window
    lm = dc.fem_logmag_batch_permode(R, freqs, thsub, allr, ch.drive_row, eta, tau)
    lm_fem = dc.fem_logmag_batch_permode(R, freqs, np.ones((1, 9)), allr, ch.drive_row, eta, tau)[0]
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T
    wflat = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T.ravel()

    peak_ho = np.zeros((len(sub), len(ho_pos))); peak_ob = np.zeros((len(sub), n_o))
    for j in range(len(sub)):
        c = hq.wmedian((tru_obs - lm[j, :, :n_o]).ravel(), wflat)
        po = np.exp(lm[j, :, :n_o] + c); ph = np.exp(lm[j, :, n_o:] + c)
        for k in range(n_o): peak_ob[j, k] = hq.SC_qoi_peak(po[:, k])
        for k in range(len(ho_pos)): peak_ho[j, k] = hq.SC_qoi_peak(ph[:, k])
    c_fem = hq.wmedian((tru_obs - lm_fem[:, :n_o]).ravel(), wflat)
    peak_fem_ho = np.array([hq.SC_qoi_peak(np.exp(lm_fem[:, n_o + k] + c_fem)) for k in range(len(ho_pos))])
    peak_tru_ob = np.array([hq.SC_qoi_peak(np.exp(tru_obs[:, k])) for k in range(n_o)])
    peak_tru_ho = np.array([hq.SC_qoi_peak(np.exp(tru_ho[:, k])) for k in range(len(ho_pos))])

    # pooled QOI discrepancy (NOT the over-fit two-pop) from observed residuals
    res_ob = np.log(np.median(peak_ob, axis=0) + 1e-300) - np.log(peak_tru_ob + 1e-300)
    sig = float(np.std(res_ob))
    drng = np.random.default_rng(seed + 5)
    twin_draws = peak_ho * np.exp(drng.normal(0, sig, peak_ho.shape))
    clim_sample = peak_tru_ob.copy()                      # climatology = observed-channel peaks (population)

    def block(mask, label):
        idx = np.where(mask)[0]
        if len(idx) == 0:
            return None
        crps_t, crps_c, iv_t, cov_t, fem_db = [], [], [], [], []
        for k in idx:
            st = SC.score_qoi(twin_draws[:, k], peak_tru_ho[k])
            sc = SC.score_qoi(clim_sample, peak_tru_ho[k])
            crps_t.append(st["crps"]); iv_t.append(st["interval_score"]); cov_t.append(st["covered"])
            crps_c.append(sc["crps"])
            fem_db.append(abs(20 * np.log10(peak_fem_ho[k] / peak_tru_ho[k])))
        ct, cc = float(np.mean(crps_t)), float(np.mean(crps_c))
        return {"n": len(idx), "twin_crps": ct, "clim_crps": cc, "crps_skill_vs_clim": float(1 - ct / cc),
                "twin_interval": float(np.mean(iv_t)), "twin_coverage": float(np.mean(cov_t)),
                "fem_point_median_abs_db": float(np.median(fem_db)), "fem_point_frac_gt6db": float(np.mean(np.array(fem_db) > 6))}

    rec = {"deliverable": "value of L5 updating on NON-HARD sensors (skill vs climatology + vs FEM)",
           "split_seed": seed, "qoi_discrepancy_sigma_log_pooled": sig, "calib_converged": bool(cdiag["converged"]),
           "n_heldout": int(len(ho_pos)), "n_heldout_hard": int(hard_ho.sum()),
           "NON_HARD": block(hard_ho == 0, "non-hard"), "HARD": block(hard_ho == 1, "hard"),
           "ALL": block(np.ones(len(ho_pos), bool), "all"),
           "by_snap_distance_in": {}, "runtime_s": time.time() - t0}
    for lo, hi in [(0, 1), (1, 3), (3, 99)]:
        b = block((hard_ho == 0) & (snap_ho >= lo) & (snap_ho < hi), f"nonhard_snap{lo}-{hi}")
        if b: rec["by_snap_distance_in"][f"{lo}-{hi}"] = b
    if write:
        OUT.mkdir(exist_ok=True)
        (OUT / f"value_eval_seed{seed:02d}.json").write_text(json.dumps(rec, indent=2))
    nh = rec["NON_HARD"]; hd = rec["HARD"]
    print(f"seed {seed}: held out {len(ho_pos)} ({int(hard_ho.sum())} hard); QOI-disc sigma {sig:.2f}")
    print(f"  NON-HARD (n{nh['n']}): twin coverage {nh['twin_coverage']:.2f}  CRPS-skill vs climatology "
          f"{nh['crps_skill_vs_clim']:+.2f}  (twin CRPS {nh['twin_crps']:.0f} vs clim {nh['clim_crps']:.0f}); "
          f"FEM point miss median {nh['fem_point_median_abs_db']:.1f} dB ({nh['fem_point_frac_gt6db']*100:.0f}% >6dB)")
    print(f"  HARD     (n{hd['n']}): twin coverage {hd['twin_coverage']:.2f}  CRPS-skill {hd['crps_skill_vs_clim']:+.2f}; "
          f"FEM point miss median {hd['fem_point_median_abs_db']:.1f} dB")
    print(f"  by snap (non-hard): " + " | ".join(f"{k}in skill {v['crps_skill_vs_clim']:+.2f} (n{v['n']})"
          for k, v in rec["by_snap_distance_in"].items()))
    print(f"  runtime {rec['runtime_s']:.0f}s")
    return rec


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(seed=seed)
