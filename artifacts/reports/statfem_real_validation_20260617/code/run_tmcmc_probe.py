#!/usr/bin/env python3
"""Keystone test (D9): does TMCMC RESOLVE the exact split0-M3 cell that NUTS went multimodal on (R-hat 104)?
Same fixed-length whitened M3 likelihood, same data — ONLY the sampler changes. 4 independent TMCMC runs.

Output: out/tmcmc_probe_M3.json (cross-run R-hat/ESS, log-evidence, theta posterior).
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import real_arms as ra
import tmcmc as T
from diagnose_convergence import setup

WS = Path(__file__).resolve().parent.parent
SIGMA_MEAS = ra.SIGMA_MEAS
NSIG_THETA = ra.NSIG_THETA
SD_PRIOR = ra.SIGMA_D_PRIOR
GAIN_SD = ra.GAIN_PRIOR_SD
HN = lambda x, s: 0.5 * np.log(2.0 / (np.pi * s * s)) - x * x / (2 * s * s)   # HalfNormal logpdf (x>=0)


def build_loglike(arm="M3", free_groups=None):
    R, freqs, target, rr, drive, co, c0 = setup()
    cov = ra.build_cov(arm, freqs, co, rf.jax_fem_logmag_factory(R, freqs, rr, drive))
    U = np.asarray(cov[0]); Lam = np.asarray(cov[1])
    fg = list(range(9)) if free_groups is None else list(free_groups)
    nfree = len(fg)
    d = nfree + 2                       # log_theta_free + gain + log_sigma_d
    tgt = target

    tgt_flat = tgt.ravel()                                    # (N,)
    Nf, Ns = tgt.shape

    def log_like(Xmat):
        Xmat = np.atleast_2d(Xmat)
        M = len(Xmat)
        theta = np.ones((M, 9))
        theta[:, fg] = np.exp(Xmat[:, :nfree])
        gain = Xmat[:, nfree][:, None]                       # (M,1)
        sd = np.exp(Xmat[:, nfree + 1])[:, None]             # (M,1)
        lm = rf.fem_logmag_batch(R, freqs, theta, rr, drive)  # (M,Nf,Ns)
        Rres = tgt_flat[None, :] - (lm.reshape(M, -1) + gain)  # (M,N)
        rt = Rres @ U                                         # (M,N): rt[m]=U.T@Rres[m]
        var = SIGMA_MEAS ** 2 + (sd ** 2) * Lam[None, :]      # (M,N)
        return -0.5 * np.sum(rt ** 2 / var + np.log(2 * np.pi * var), axis=1)

    def log_prior(Xmat):
        Xmat = np.atleast_2d(Xmat)
        lt = Xmat[:, :nfree]; gain = Xmat[:, nfree]; s = Xmat[:, nfree + 1]
        lp = (-0.5 * (lt ** 2).sum(1) / NSIG_THETA ** 2 - nfree * np.log(NSIG_THETA * np.sqrt(2 * np.pi)))
        lp += -0.5 * ((gain - c0) / GAIN_SD) ** 2 - np.log(GAIN_SD * np.sqrt(2 * np.pi))
        lp += HN(np.exp(s), SD_PRIOR) + s            # sigma_d=exp(s); +s = Jacobian
        return lp

    def sample_prior(mm):
        rng = np.random.default_rng(12345)
        lt = rng.normal(0, NSIG_THETA, (mm, nfree))
        gain = rng.normal(c0, GAIN_SD, (mm, 1))
        sd = np.abs(rng.normal(0, SD_PRIOR, (mm, 1)))
        return np.hstack([lt, gain, np.log(np.maximum(sd, 1e-6))])

    return log_like, log_prior, sample_prior, d, fg, c0


def main():
    t0 = time.time()
    log_like, log_prior, sample_prior, d, fg, c0 = build_loglike("M3")
    runs, diag = T.run_independent(log_like, log_prior, sample_prior, n=1500, n_runs=4, seed0=0,
                                   n_mcmc=5, target_cov=1.0)
    S = np.concatenate([r["samples"] for r in runs])        # pooled posterior
    theta = np.exp(S[:, :len(fg)])
    gain = S[:, len(fg)]; sd = np.exp(S[:, len(fg) + 1])
    conv = diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200
    rec = {"arm": "M3", "sampler": "TMCMC", "free_groups": fg, "c0": c0, "runtime_s": time.time() - t0,
           "converged": bool(conv), "diag": diag,
           "gain": {"med": float(np.median(gain)), "lo": float(np.percentile(gain, 2.5)),
                    "hi": float(np.percentile(gain, 97.5))},
           "sigma_d": {"med": float(np.median(sd)), "lo": float(np.percentile(sd, 2.5)),
                       "hi": float(np.percentile(sd, 97.5))},
           "theta_post": {rf.GNAMES[g]: {"med": float(np.median(theta[:, i])),
                                         "lo": float(np.percentile(theta[:, i], 2.5)),
                                         "hi": float(np.percentile(theta[:, i], 97.5))}
                          for i, g in enumerate(fg)},
           "nuts_comparison": {"nuts_max_rhat": 104.04, "nuts_min_ess": 2, "nuts_sigma_d": 9.82,
                               "note": "same likelihood; NUTS went multimodal, TMCMC result here"}}
    (WS / "out").mkdir(exist_ok=True)
    (WS / "out" / "tmcmc_probe_M3.json").write_text(json.dumps(rec, indent=2))
    print(f"TMCMC M3: converged={conv} | cross-run R-hat {diag['max_rhat']:.3f} ESS {diag['min_ess']:.0f} "
          f"| log-evid {diag['log_evidence_mean']:.2f}±{diag['log_evidence_std']:.2f} "
          f"| sigma_d {rec['sigma_d']['med']:.2f} [{rec['sigma_d']['lo']:.2f},{rec['sigma_d']['hi']:.2f}] "
          f"| gain {rec['gain']['med']:.2f} | {rec['runtime_s']:.0f}s")
    print(f"  (NUTS on SAME likelihood: R-hat 104, ESS 2, sigma_d 9.8 -> multimodal)")
    print("  theta medians:", {rf.GNAMES[g]: round(float(np.median(theta[:, i])), 2) for i, g in enumerate(fg)})


if __name__ == "__main__":
    main()
