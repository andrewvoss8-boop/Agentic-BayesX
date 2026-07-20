#!/usr/bin/env python3
"""Generators for figC (held-out FRF overlay), figD (discretization-invariance, §8), and the beta-prior
sensitivity sub-test (§11). Each is resumable (writes out/*.json|npz, skips if present unless --force).

Reuses the VERIFIED IFT moment-approximation likelihood (ift_arm/ift_tmcmc machinery), the M2 Kronecker arm
(m2_arm, == dense real_arms.M2 to ~2e-15), the L5 modal-feature calibration (modal_feature), and the byte-
identical forward (realfrf) + scorer (score). Short TMCMC settings (labeled) for the figure/sub-test posteriors;
the headline 5-split scorecard uses the full n=1500 x 4-run cells.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ift_arm
import ift_tmcmc as itm
import m2_arm
import modal_feature as mf
import realfrf as rf
import score as SC
import tmcmc as T

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
IDENT = ift_arm.IDENT_GROUPS
SM = ift_arm.SIGMA_MEAS


def _split(seed, decim=1):
    """Reuse ift_tmcmc._split, then optionally decimate the in-band frequency grid by `decim` (§8 knob)."""
    S = itm._split(seed)
    if decim > 1:
        idx = np.arange(0, len(S["freqs"]), decim)
        S = dict(S)
        S["freqs"] = S["freqs"][idx]
        S["tru_obs"] = S["tru_obs"][idx]
        S["tru_ho"] = S["tru_ho"][idx]
        # re-center gain + beta* on the decimated grid (forward-model only)
        lm0 = rf.fem_logmag(S["R"], S["freqs"], np.ones(9), S["obs_rows"], S["ch"].drive_row, zeta=rf.ZETA_NOM)
        wq = np.ones_like(S["tru_obs"])
        S["c0"] = ift_arm.wmedian((S["tru_obs"] - lm0).ravel(), wq.ravel())
        S["bstar"] = ift_arm.beta_star(S["R"], S["freqs"], S["obs_rows"], S["ch"].drive_row, zeta=rf.ZETA_NOM)
    return S


def _ift_posterior(S, n=600, n_runs=2, beta_prior_sd=ift_arm.BETA_PRIOR_SD, seed=0):
    """Short IFT-TMCMC; return pooled posterior X (Nsamp,6)=[logth(4),logbeta,gain] + beta*."""
    R, freqs = S["R"], S["freqs"]; obs_rows = S["obs_rows"]; tru_obs = S["tru_obs"]
    drive = S["ch"].drive_row; c0, bstar = S["c0"], S["bstar"]; logbstar = float(np.log(bstar)); fg = IDENT

    def log_like(X):
        th, beta, gain = itm._x_to_tbg(np.atleast_2d(X), fg)
        lm, flv = ift_arm.moments_np_batch(R, freqs, th, beta, obs_rows, drive, zeta=rf.ZETA_NOM)
        var = SM ** 2 + flv
        Rr = tru_obs[None] - (lm + gain[:, None, None])
        return -0.5 * np.sum(Rr ** 2 / var + np.log(2 * np.pi * var), axis=(1, 2))

    def log_prior(X):
        X = np.atleast_2d(X)
        lp = -0.5 * np.sum(X[:, :4] ** 2, axis=1) / ift_arm.NSIG_THETA ** 2
        lp += -0.5 * ((X[:, 4] - logbstar) / beta_prior_sd) ** 2
        lp += -0.5 * ((X[:, 5] - c0) / ift_arm.GAIN_PRIOR_SD) ** 2
        return lp

    def sample_prior(m):
        rng = np.random.default_rng(20260619 + seed)
        X = np.zeros((m, 6)); X[:, :4] = rng.normal(0, ift_arm.NSIG_THETA, (m, 4))
        X[:, 4] = rng.normal(logbstar, beta_prior_sd, m); X[:, 5] = rng.normal(c0, ift_arm.GAIN_PRIOR_SD, m)
        return X

    runs, diag = T.run_independent(log_like, log_prior, sample_prior, n=n, n_runs=n_runs, seed0=2000 + seed)
    X = np.concatenate([r["samples"] for r in runs], 0)
    return X, bstar, diag


# ---------------------------------------------------------------- figC: held-out FRF overlay
def frf_overlay(seed=1, force=False):
    outp = OUT / "frf_overlay.npz"
    if outp.exists() and not force:
        print("[skip] frf_overlay.npz"); return
    t0 = time.time(); S = _split(seed)
    R, freqs = S["R"], S["freqs"]; ho_rows = S["ho_rows"]; tru_ho = S["tru_ho"]; drive = S["ch"].drive_row
    # choose the held-out channel with the largest measured peak (clearest resonance to overlay)
    k = int(np.argmax(np.exp(tru_ho).max(0)))
    meas_curve = np.exp(tru_ho[:, k])
    ho1 = ho_rows[k:k + 1]

    # IFT predictive band (physics-derived field std)
    X, bstar, _ = _ift_posterior(S, n=600, n_runs=2, seed=seed)
    rng = np.random.default_rng(7); sub = rng.choice(len(X), size=min(len(X), 400), replace=False)
    th, beta, gain = itm._x_to_tbg(X[sub], IDENT)
    lm, flv = ift_arm.moments_np_batch(R, freqs, th, beta, ho1, drive, zeta=rf.ZETA_NOM)
    ift_draws = np.exp(lm[:, :, 0] + gain[:, None]) * np.exp(rng.normal(0, np.sqrt(SM ** 2 + flv[:, :, 0])))
    ift_lo, ift_md, ift_hi = np.percentile(ift_draws, [2.5, 50, 97.5], axis=0)

    # L5 predictive band (modal-feature theta posterior + global gain)
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    obs_daqs = [S["ch"].daq[p] for p in []]  # placeholder; recompute split daqs
    # reuse the same split to get observed daqs for L5 calibration
    didx = {d: i for i, d in enumerate(meas["daq"])}
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1])
    dr = np.array([meas["dyn_range"][didx[d]] for d in S["ch"].daq]); elig = np.where(dr >= ift_arm.DR_MIN)[0]
    perm = np.random.default_rng(seed).permutation(elig); n_obs = int(round(0.6 * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); obs_daqs = [S["ch"].daq[p] for p in obs_pos]
    obs_rows = S["ch"].rows[obs_pos]
    tru_obs_full = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    wq_obs = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T
    freqs_full = fr[fb]
    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    omi = np.array([p[0] for p in pairs]); owh = np.array([p[1] for p in pairs])
    theta_post, _, _ = mf.calibrate_modal(R, omi, owh, seed=20260617, warmup=600, samples=600, chains=4)
    sub5 = np.linspace(0, theta_post.shape[0] - 1, 300).astype(int)
    lm_ho5 = rf.fem_logmag_batch(R, freqs, theta_post[sub5], ho1, drive, zeta=rf.ZETA_NOM)[:, :, 0]
    lm_ob5 = rf.fem_logmag_batch(R, freqs_full, theta_post[sub5], obs_rows, drive, zeta=rf.ZETA_NOM)
    c5 = np.array([ift_arm.wmedian((tru_obs_full - lm_ob5[m]).ravel(), wq_obs.ravel()) for m in range(len(sub5))])
    l5_draws = np.exp(lm_ho5 + c5[:, None])
    l5_lo, l5_md, l5_hi = np.percentile(l5_draws, [2.5, 50, 97.5], axis=0)

    # M2 predictive band (whole-FRF; non-converged -> flagged). freqs == freqs_full at decim=1 (seed default).
    coords_obs = S["ch"].coords[obs_pos]
    flatM, diagM = m2_arm.run_m2(R, freqs, tru_obs_full, obs_rows, drive, coords_obs, S["c0"],
                                 num_warmup=150, num_samples=150, num_chains=2)  # illustrative flagged band only
    sm = np.linspace(0, flatM["log_theta"].shape[0] - 1, 300).astype(int)
    thM = np.exp(flatM["log_theta"][sm]); gM = flatM["gain"][sm]
    lmM = rf.fem_logmag_batch(R, freqs, thM, ho1, drive, zeta=rf.ZETA_NOM)[:, :, 0]
    m2_draws = np.exp(lmM + gM[:, None]); m2_lo, m2_md, m2_hi = np.percentile(m2_draws, [2.5, 50, 97.5], axis=0)

    np.savez(outp, freqs=freqs, meas=meas_curve, ift_lo=ift_lo, ift_md=ift_md, ift_hi=ift_hi,
             l5_lo=l5_lo, l5_md=l5_md, l5_hi=l5_hi, m2_lo=m2_lo, m2_md=m2_md, m2_hi=m2_hi,
             channel_daq=int(S["ho_daqs"][k]), m2_rhat=diagM["max_rhat"], seed=seed)
    print(f"frf_overlay.npz: ho ch {S['ho_daqs'][k]} | M2 R-hat {diagM['max_rhat']:.0f} | {time.time()-t0:.0f}s")


# ---------------------------------------------------------------- figD: discretization invariance (§8)
def discretization(seed=1, decims=(1, 2, 4), force=False):
    outp = OUT / "discretization.json"
    if outp.exists() and not force:
        print("[skip] discretization.json"); return
    t0 = time.time(); rows = []
    for dc in decims:
        S = _split(seed, decim=dc)
        X, bstar, diag = _ift_posterior(S, n=600, n_runs=2, seed=seed)
        th, beta, gain = itm._x_to_tbg(X, IDENT)
        # held-out QOI medians on this grid
        lm, flv = ift_arm.moments_np_batch(S["R"], S["freqs"], th[:300], beta[:300], S["ho_rows"], S["ch"].drive_row)
        peak = np.median([np.exp(lm[j] + gain[j]).max(0) for j in range(min(300, len(th)))], axis=0)
        rows.append({"decim": dc, "n_freq": int(len(S["freqs"])),
                     "ift_beta_med": float(np.median(np.exp(X[:, 4]))),
                     "ift_theta_med": [float(np.median(np.exp(X[:, i]))) for i in range(4)],
                     "ift_peak_qoi_med": float(np.median(peak)),
                     "ift_crossrun_rhat": float(diag["max_rhat"])})
        print(f"  IFT decim {dc} (n_freq {len(S['freqs'])}): beta_med {rows[-1]['ift_beta_med']:.3f} "
              f"peak_qoi_med {rows[-1]['ift_peak_qoi_med']:.3g} R-hat {diag['max_rhat']:.3f}", flush=True)
    # invariance metric: spread of beta_med + peak_qoi across grids (relative)
    bm = np.array([r["ift_beta_med"] for r in rows]); pm = np.array([r["ift_peak_qoi_med"] for r in rows])
    rec = {"deliverable": "IFT_discretization_invariance", "seed": seed, "grids": rows,
           "ift_beta_rel_spread": float((bm.max() - bm.min()) / np.median(bm)),
           "ift_peak_qoi_rel_spread": float((pm.max() - pm.min()) / np.median(pm)),
           "note": "IFT theta/QOI/beta posterior vs analysis-grid density; small spread = discretization-invariant.",
           "runtime_s": time.time() - t0}
    outp.write_text(json.dumps(rec, indent=2))
    print(f"discretization.json: beta rel-spread {rec['ift_beta_rel_spread']:.2%}, "
          f"peak-QOI rel-spread {rec['ift_peak_qoi_rel_spread']:.2%}")


# ---------------------------------------------------------------- §11: beta-prior sensitivity
def sensitivity(seed=1, sds=(0.66, 2.0, 6.0), force=False):
    outp = OUT / "sensitivity.json"
    if outp.exists() and not force:
        print("[skip] sensitivity.json"); return
    t0 = time.time(); S = _split(seed); rows = []
    for sd in sds:
        X, bstar, diag = _ift_posterior(S, n=600, n_runs=2, beta_prior_sd=sd, seed=seed)
        th, beta, gain = itm._x_to_tbg(X[:300], IDENT)
        lm, flv = ift_arm.moments_np_batch(S["R"], S["freqs"], th, beta, S["ho_rows"], S["ch"].drive_row)
        peak_pred = np.array([np.exp(lm[j] + gain[j]).max(0) for j in range(len(th))])
        peak_tru = np.exp(S["tru_ho"]).max(0)
        sc = [SC.score_qoi(peak_pred[:, c], peak_tru[c]) for c in range(peak_pred.shape[1])]
        rows.append({"beta_prior_sd": sd, "beta_med": float(np.median(np.exp(X[:, 4]))),
                     "crossrun_rhat": float(diag["max_rhat"]),
                     "peak_interval_med": float(np.median([s["interval_score"] for s in sc])),
                     "peak_coverage": float(np.mean([s["covered"] for s in sc]))})
        print(f"  beta_prior_sd {sd}: beta_med {rows[-1]['beta_med']:.3f} peak_interval "
              f"{rows[-1]['peak_interval_med']:.3g} cover {rows[-1]['peak_coverage']:.2f}", flush=True)
    iv = np.array([r["peak_interval_med"] for r in rows])
    rec = {"deliverable": "IFT_beta_prior_sensitivity", "seed": seed, "rows": rows,
           "peak_interval_rel_spread": float((iv.max() - iv.min()) / np.median(iv)),
           "verdict_robust": bool((iv.max() - iv.min()) / np.median(iv) < 0.5),
           "note": "Does the IFT held-out peak score survive a 3x wider/tighter beta prior?",
           "runtime_s": time.time() - t0}
    outp.write_text(json.dumps(rec, indent=2))
    print(f"sensitivity.json: peak-interval rel-spread {rec['peak_interval_rel_spread']:.2%} "
          f"robust={rec['verdict_robust']}")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    force = "--force" in sys.argv
    if which in ("frf", "all"):
        frf_overlay(force=force)
    if which in ("disc", "all"):
        discretization(force=force)
    if which in ("sens", "all"):
        sensitivity(force=force)
