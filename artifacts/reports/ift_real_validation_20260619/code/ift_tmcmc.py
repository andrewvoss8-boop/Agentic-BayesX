#!/usr/bin/env python3
"""IFT arm under TMCMC — the pre-authorized escalation when the whole-FRF IFT likelihood goes multimodal under
NUTS (decisions_log D6; card §2/§5; StatFEM D9/D10). TMCMC (copied byte-identical tmcmc.py, bimodal-self-test
validated) populates MULTIPLE modes, gives cross-run R-hat over >=4 independent runs (the diag the immutable
checker expects), and an unbiased model EVIDENCE.

The decision-relevant question (vs StatFEM M2 = physics-in-LIKELIHOOD whole-FRF, which under TMCMC did NOT
reproduce: cross-run R-hat 129 from the sigma_d 'variance->inf' singularity): does IFT = physics-in-PRIOR with a
BOUNDED learned beta give a REPRODUCIBLE multimodal posterior + calibrated held-out QOI, with NO variance
runaway? If yes -> ROBUSTNESS-WIN; if also useless -> HONEST-NEGATIVE.

Parameter vector x = [log_theta(4 identifiable groups), log_beta, gain]. The likelihood is the SAME IFT
log-magnitude moment-approximation as ift_arm (reused moments_np_batch); only the SAMPLER changes.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ift_arm
import realfrf as rf
import score as SC
import tmcmc as T

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
GNAMES = rf.GNAMES
IDENT = ift_arm.IDENT_GROUPS
NSIG_THETA = ift_arm.NSIG_THETA
GAIN_PRIOR_SD = ift_arm.GAIN_PRIOR_SD


def _split(seed, obs_frac=0.6):
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= ift_arm.DR_MIN)[0]
    perm = np.random.default_rng(seed).permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T
    wq_obs = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T
    lm0 = rf.fem_logmag(R, freqs, np.ones(9), obs_rows, ch.drive_row, zeta=rf.ZETA_NOM)
    c0 = ift_arm.wmedian((tru_obs - lm0).ravel(), wq_obs.ravel())
    bstar = ift_arm.beta_star(R, freqs, obs_rows, ch.drive_row, zeta=rf.ZETA_NOM)
    return dict(R=R, freqs=freqs, ch=ch, obs_rows=obs_rows, ho_rows=ho_rows, tru_obs=tru_obs,
                tru_ho=tru_ho, c0=c0, bstar=bstar, obs_daqs=obs_daqs, ho_daqs=ho_daqs)


def _x_to_tbg(X, fg):
    """X (M,6) -> theta (M,9), beta (M,), gain (M,)."""
    M = X.shape[0]
    th = np.ones((M, 9)); th[:, fg] = np.exp(X[:, :4])
    return th, np.exp(X[:, 4]), X[:, 5]


def run_split_tmcmc(seed=0, n=1500, n_runs=4, n_mcmc=8, beta_prior_sd=ift_arm.BETA_PRIOR_SD,
                    sigma_meas=ift_arm.SIGMA_MEAS, n_draws=400, force=False, write=True, tag="ift_tmcmc"):
    cell = OUT / "ift_tmcmc_cells" / f"{tag}_seed{seed:02d}.json"
    if write and cell.exists() and not force:
        print(f"[skip] {cell.name}")
        return json.loads(cell.read_text())
    t0 = time.time()
    S = _split(seed)
    R, freqs = S["R"], S["freqs"]; obs_rows, ho_rows = S["obs_rows"], S["ho_rows"]
    tru_obs, tru_ho = S["tru_obs"], S["tru_ho"]; c0, bstar = S["c0"], S["bstar"]
    drive = S["ch"].drive_row; fg = IDENT; logbstar = float(np.log(bstar))
    sm2 = sigma_meas ** 2

    def log_like(X):
        th, beta, gain = _x_to_tbg(np.atleast_2d(X), fg)
        lm, flv = ift_arm.moments_np_batch(R, freqs, th, beta, obs_rows, drive, zeta=rf.ZETA_NOM)
        mean = lm + gain[:, None, None]; var = sm2 + flv
        Rr = tru_obs[None] - mean
        return -0.5 * np.sum(Rr ** 2 / var + np.log(2 * np.pi * var), axis=(1, 2))

    def log_prior(X):
        X = np.atleast_2d(X)
        lp = -0.5 * np.sum(X[:, :4] ** 2, axis=1) / NSIG_THETA ** 2 - 4 * np.log(NSIG_THETA * np.sqrt(2 * np.pi))
        lp += -0.5 * ((X[:, 4] - logbstar) / beta_prior_sd) ** 2 - np.log(beta_prior_sd * np.sqrt(2 * np.pi))
        lp += -0.5 * ((X[:, 5] - c0) / GAIN_PRIOR_SD) ** 2 - np.log(GAIN_PRIOR_SD * np.sqrt(2 * np.pi))
        return lp

    def sample_prior(m):
        rng = np.random.default_rng(20260619 + seed)
        X = np.zeros((m, 6))
        X[:, :4] = rng.normal(0.0, NSIG_THETA, (m, 4))
        X[:, 4] = rng.normal(logbstar, beta_prior_sd, m)
        X[:, 5] = rng.normal(c0, GAIN_PRIOR_SD, m)
        return X

    runs, diag = T.run_independent(log_like, log_prior, sample_prior, n=n, n_runs=n_runs,
                                   seed0=1000 + seed, n_mcmc=n_mcmc)
    Xall = np.concatenate([r["samples"] for r in runs], 0)          # (n_runs*n, 6)

    # ---- held-out QOI predictive (physics-derived field std as a QOI-level multiplier; same as ift_arm) ----
    rng = np.random.default_rng(seed + 17)
    sub = rng.choice(len(Xall), size=min(len(Xall), n_draws), replace=False)
    th_b, beta_b, gain_b = _x_to_tbg(Xall[sub], fg)
    lm_ho, flv_ho = ift_arm.moments_np_batch(R, freqs, th_b, beta_b, ho_rows, drive, zeta=rf.ZETA_NOM)
    M, Nf, Nho = lm_ho.shape
    peak_pred = np.zeros((M, Nho)); band_pred = np.zeros((M, Nho))
    for j in range(M):
        Hmag = np.exp(lm_ho[j] + gain_b[j]); std = np.sqrt(sm2 + flv_ho[j])
        for k in range(Nho):
            col = Hmag[:, k]; ipk = int(np.argmax(col))
            peak_pred[j, k] = col[ipk] * np.exp(rng.normal(0.0, std[ipk, k]))
            wE = col ** 2 / max((col ** 2).sum(), 1e-300)
            s_band = float(np.sqrt(np.sum(wE * std[:, k] ** 2)))
            band_pred[j, k] = np.sqrt(np.trapz(col ** 2, freqs)) * np.exp(rng.normal(0.0, s_band))
    peak_tru = np.array([np.exp(tru_ho[:, k]).max() for k in range(Nho)])
    band_tru = np.array([np.sqrt(np.trapz(np.exp(tru_ho[:, k]) ** 2, freqs)) for k in range(Nho)])
    pk = [SC.score_qoi(peak_pred[:, k], peak_tru[k]) for k in range(Nho)]
    bd = [SC.score_qoi(band_pred[:, k], band_tru[k]) for k in range(Nho)]
    scores = {"peak": ift_arm._agg(pk), "band": ift_arm._agg(bd)}

    # ---- beta posterior + boundedness/singularity check + reproducibility ----
    logbeta = Xall[:, 4]; bmed, blo, bhi = np.percentile(logbeta, [50, 2.5, 97.5])
    converged = bool(diag["max_rhat"] <= 1.2 and diag["min_ess"] >= 200)   # TMCMC cross-run threshold (documented)
    beta_med = float(np.exp(bmed))
    beta_bounded = bool(beta_med > bstar / 1e4 and beta_med < bstar * 1e2)   # no variance runaway either way
    beta_collapsed = bool(beta_med < bstar / 100.0)
    rec = {
        "deliverable": "IFT_TMCMC_heldout_sensor_QOI", "arm": "IFT_physics_prior_learned_beta_TMCMC",
        "sampler": "TMCMC (multimodal escalation; copied tmcmc.py)", "split_seed": seed,
        "observable": "log|H| (SAME as M2; log-magnitude moment approximation, D0/D1)",
        "n_population": n, "n_runs": n_runs, "n_observed": tru_obs.shape[1], "n_heldout": Nho,
        "convergence": {"max_rhat_crossrun": diag["max_rhat"], "min_ess": diag["min_ess"],
                        "rhat_per_dim": diag["rhat_per_dim"], "converged": converged,
                        "log_evidence_mean": diag["log_evidence_mean"],
                        "log_evidence_std": diag["log_evidence_std"],
                        "mean_accept_rate": diag["mean_accept_rate"], "mean_stages": diag["mean_stages"]},
        "beta_posterior": {"beta_med": beta_med, "logbeta_med": float(bmed), "logbeta_lo": float(blo),
                           "logbeta_hi": float(bhi), "logbeta_ci_width": float(bhi - blo),
                           "beta_star": bstar, "log_beta_star": logbstar, "prior_logsd": beta_prior_sd,
                           "bounded_no_runaway": beta_bounded, "collapsed": beta_collapsed,
                           "weakly_identified": bool((bhi - blo) > 0.5 * 2 * 1.96 * beta_prior_sd)},
        "gain_c0": float(c0), "scores": scores, "n_draws_used": int(len(sub)),
        "runtime_s": time.time() - t0,
    }
    if write:
        cell.parent.mkdir(parents=True, exist_ok=True); cell.write_text(json.dumps(rec, indent=2))
        cv = rec["convergence"]; bp = rec["beta_posterior"]
        print(f"IFT-TMCMC seed {seed}: cross-run R-hat {cv['max_rhat_crossrun']:.3f} ESS {cv['min_ess']:.0f} "
              f"converged={cv['converged']} | logEvid {cv['log_evidence_mean']:.1f}±{cv['log_evidence_std']:.1f}")
        print(f"  beta_med {bp['beta_med']:.3g} (beta* {bstar:.3g}) bounded={bp['bounded_no_runaway']} "
              f"collapsed={bp['collapsed']}")
        print(f"  PEAK cover {scores['peak']['coverage_frac']:.2f} interval {scores['peak']['interval_score_mean']:.3g} "
              f"CRPS {scores['peak']['crps_mean']:.3g} | BAND cover {scores['band']['coverage_frac']:.2f} "
              f"interval {scores['band']['interval_score_mean']:.3g}")
        print(f"  runtime {rec['runtime_s']:.0f}s -> {cell}")
    return rec


if __name__ == "__main__":
    kw = {}
    for a in sys.argv[1:]:
        if a.startswith("--seed="): kw["seed"] = int(a.split("=")[1])
        elif a.startswith("--n="): kw["n"] = int(a.split("=")[1])
        elif a.startswith("--runs="): kw["n_runs"] = int(a.split("=")[1])
        elif a == "--force": kw["force"] = True
    run_split_tmcmc(**kw)
