#!/usr/bin/env python3
"""Faithful Schneider discrepancy under TMCMC (Card A next-action #2, decisions_log D13).

Fixes the THREE unfaithfulnesses of real_arms.py M2/M3 (D8/D10) and tests:
  Q-A: does FAITHFUL Schneider TAME the whole-FRF-magnitude pathology that the unfaithful config could not
       (NUTS R-hat 104 / TMCMC R-hat 129, evidence +-739 -- D6/D7/D10)?
  Q-B: does the M3 ORTHOGONAL projection STARVE the discrepancy vs plain Schneider M2?

Likelihood = whole log|H| over band frequencies x observed channels (matched-path g/lbf + global gain c):
  R(theta,c) = log|H_meas_obs| - (log|H_fem_obs(theta)| + c)
  M0 naive     R ~ N(0, sigma_meas^2 I)                              (no discrepancy)
  M1 iid       R ~ N(0, (sigma_meas^2 + sigma_w^2) I)                (marginal)
  M2 Schneider R ~ N(0, sigma_meas^2 I + sigma_w^2 C_add)           C_add = r(R_ff x I)+(1-r)(I x R_zz) ADDITIVE
  M3 orthogonal R ~ N(0, sigma_meas^2 I + sigma_w^2 Pperp C_add Pperp)  Pperp removes theta->log|H| span

Fixes vs real_arms: (1) ADDITIVE (commuting-Kronecker) correlation -> exact product-eigenbasis diagonalization
for M2; (2) INFORMATIVE sigma_w prior LogNormal centered at the FIM-realized floor sigma_d0~=1.73 (kills the
variance->inf singularity); (3) parsimonious 4-group theta. Lengths/split FIXED at Schneider posterior values
(learning them = a batched-eigh extension, documented). Sampler = TMCMC (>=4 independent runs) -> cross-run
R-hat + log-evidence into the SAME immutable-checker diag fields. Magnitude first (single-hit phase noisy).

Output: out/tmcmc_faithful_<arm>_<tag>.json   (resumable: skips if present unless force=True).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("JAX_ENABLE_X64", "1")   # float64 (hard constraint) for the M3 Jacobian / jax forward

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import tmcmc as T

WS = Path(__file__).resolve().parent.parent

# fixed hyperparameters (Schneider posterior values, mapped to our problem; D13)
L_F_HZ = 10.0          # linear-frequency correlation length [Hz] (Schneider l_co,f ~ 10 Hz)
L_Z_IN = 2000.0        # spatial correlation length [in] >> structure -> near-fully spatially correlated (l_co,z ~ 50 m)
R_SPLIT = 0.82         # additive freq/space split r (Schneider posterior)
SIGMA_MEAS = 0.15      # iid log measurement+window+map floor (run_config)
ZETA = rf.ZETA_NOM     # 0.01
NSIG_THETA = 0.25      # theta LogNormal prior sigma
GAIN_C0 = 5.6          # empirical global units-gain center (run_config global_gain_c0_empirical)
GAIN_SD = 1.5
SIGMA_W_FLOOR = 1.726  # FIM-realized discrepancy floor sigma_d0 (identifiability.json) = informative-prior center
SIGMA_W_LOGSD = 0.6    # informative-prior log-spread -> 95% ~ [0.53, 5.6]; caps the variance->inf runaway
IDENT4 = [2, 4, 6, 8]  # bottom_box, cross_beam, plates, top_box (peak strain-energy > 0.3)


def corr_freq_linear(freqs, length):
    d = np.asarray(freqs)[:, None] - np.asarray(freqs)[None, :]
    return np.exp(-0.5 * (d / length) ** 2)


def corr_space(coords, length):
    d = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1))
    return np.exp(-np.abs(d) / length)


def select_observed(R, meas, ch, n_obs):
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    obs_pos = np.argsort(dr)[::-1][:n_obs]          # top-DR channels (Schneider clean-channel discipline)
    obs_pos = np.sort(obs_pos)
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    tgt = np.log(np.abs(np.array([meas["H"][didx[ch.daq[p]]][fb] for p in obs_pos])) + 1e-300).T  # (Nf, Ns)
    return obs_pos, freqs, tgt, ch.coords[obs_pos], dr[obs_pos]


def build_arm_pieces(arm, R, freqs, coords_obs, resp_rows, drive_row, fg):
    """Precompute the fixed covariance pieces for the chosen arm (lengths/r fixed -> done ONCE)."""
    Nf, Ns = len(freqs), len(coords_obs)
    if arm in ("M0", "M1"):
        return {}
    Rff = corr_freq_linear(freqs, L_F_HZ)
    Rzz = corr_space(coords_obs, L_Z_IN)
    if arm == "M2":
        lam_f, U_f = np.linalg.eigh(Rff); lam_z, U_z = np.linalg.eigh(Rzz)
        return {"U_f": U_f, "lam_f": np.clip(lam_f, 0, None), "U_z": U_z, "lam_z": np.clip(lam_z, 0, None)}
    # M3: full additive C_add, project off the theta->log|H| Jacobian span, eigh once
    Iz = np.eye(Ns); If = np.eye(Nf)
    C_add = R_SPLIT * np.kron(Rff, Iz) + (1 - R_SPLIT) * np.kron(If, Rzz)      # (Nf*Ns, Nf*Ns)
    import jax
    jax.config.update("jax_enable_x64", True)                                 # float64 (hard constraint)
    import jax.numpy as jnp
    jfwd = rf.jax_fem_logmag_factory(R, freqs, resp_rows, drive_row, zeta=ZETA)
    Jfull = np.asarray(jax.jacfwd(jfwd)(jnp.ones(9)))                          # (Nf, Ns, 9)
    assert Jfull.dtype == np.float64, f"Jacobian not float64 ({Jfull.dtype}) — x64 not enabled"
    J = Jfull[:, :, fg].reshape(Nf * Ns, len(fg))                             # span of the CALIBRATED groups
    Pp = np.eye(Nf * Ns) - J @ np.linalg.pinv(J)                              # robust to collinear theta directions
    Cproj = Pp @ C_add @ Pp; Cproj = 0.5 * (Cproj + Cproj.T)
    lam, U = np.linalg.eigh(Cproj)
    return {"U": U, "Lam": np.clip(lam, 0, None)}


def make_loglike(arm, R, freqs, tgt, resp_rows, drive_row, fg, pieces):
    Nf, Ns = tgt.shape
    nfree = len(fg); fg = list(fg)
    tgtb = tgt[None]
    sm2 = SIGMA_MEAS ** 2

    def loglike(X):
        X = np.atleast_2d(X); M = X.shape[0]
        theta = np.ones((M, 9)); theta[:, fg] = np.exp(X[:, :nfree])
        c = X[:, nfree]
        lm = rf.fem_logmag_batch(R, freqs, theta, resp_rows, drive_row, zeta=ZETA)   # (M, Nf, Ns)
        Res = tgtb - (lm + c[:, None, None])
        if arm == "M0":
            return -0.5 * np.sum(Res ** 2 / sm2 + np.log(2 * np.pi * sm2), axis=(1, 2))
        sw = np.exp(X[:, nfree + 1])                                                  # (M,)
        if arm == "M1":
            var = sm2 + sw ** 2
            return -0.5 * (np.sum(Res ** 2, axis=(1, 2)) / var + Nf * Ns * np.log(2 * np.pi * var))
        if arm == "M2":
            U_f, lf, U_z, lz = pieces["U_f"], pieces["lam_f"], pieces["U_z"], pieces["lam_z"]
            Mij = np.matmul(np.matmul(U_f.T, Res), U_z)                               # whiten (product basis, BLAS)
            base = R_SPLIT * lf[:, None] + (1 - R_SPLIT) * lz[None, :]                # (Nf, Ns)
            var = sm2 + (sw ** 2)[:, None, None] * base[None]                         # (M, Nf, Ns)
            return -0.5 * np.sum(Mij ** 2 / var + np.log(2 * np.pi * var), axis=(1, 2))
        # M3
        U, Lam = pieces["U"], pieces["Lam"]
        rt = Res.reshape(M, Nf * Ns) @ U                                             # (M, D)
        var = sm2 + (sw ** 2)[:, None] * Lam[None, :]
        return -0.5 * np.sum(rt ** 2 / var + np.log(2 * np.pi * var), axis=1)

    return loglike


def make_prior(arm, nfree):
    has_sw = arm != "M0"
    d = nfree + 1 + (1 if has_sw else 0)

    def logprior(X):
        X = np.atleast_2d(X)
        lp = np.sum(-0.5 * (X[:, :nfree] / NSIG_THETA) ** 2 - np.log(NSIG_THETA * np.sqrt(2 * np.pi)), axis=1)
        lp += -0.5 * ((X[:, nfree] - GAIN_C0) / GAIN_SD) ** 2 - np.log(GAIN_SD * np.sqrt(2 * np.pi))
        if has_sw:
            ls = X[:, nfree + 1]
            lp += -0.5 * ((ls - np.log(SIGMA_W_FLOOR)) / SIGMA_W_LOGSD) ** 2 - np.log(SIGMA_W_LOGSD * np.sqrt(2 * np.pi))
        return lp

    def sample_prior(m):
        rng = np.random.default_rng(12345)
        cols = [rng.normal(0, NSIG_THETA, (m, nfree)), rng.normal(GAIN_C0, GAIN_SD, (m, 1))]
        if has_sw:
            cols.append(rng.normal(np.log(SIGMA_W_FLOOR), SIGMA_W_LOGSD, (m, 1)))
        return np.concatenate(cols, axis=1)

    return logprior, sample_prior, d


def run(arm, n_obs=10, free_groups=None, n=3000, n_runs=4, seed0=0, tag=None, force=False):
    fg = IDENT4 if free_groups is None else list(free_groups)
    tag = tag or f"ident{len(fg)}_n{n_obs}"
    outp = WS / "out" / f"tmcmc_faithful_{arm}_{tag}.json"
    if outp.exists() and not force:
        print(f"[skip] {outp.name} exists"); return json.loads(outp.read_text())
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    obs_pos, freqs, tgt, coords_obs, dr_obs = select_observed(R, meas, ch, n_obs)
    resp_rows = ch.rows[obs_pos]
    pieces = build_arm_pieces(arm, R, freqs, coords_obs, resp_rows, ch.drive_row, fg)
    loglike = make_loglike(arm, R, freqs, tgt, resp_rows, ch.drive_row, fg, pieces)
    logprior, sample_prior, d = make_prior(arm, len(fg))
    runs, diag = T.run_independent(loglike, logprior, sample_prior, n=n, n_runs=n_runs, seed0=seed0)
    S = np.concatenate([r["samples"] for r in runs])
    nfree = len(fg)
    theta_post = np.ones((S.shape[0], 9)); theta_post[:, fg] = np.exp(S[:, :nfree])
    conv = diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02
    rec = {
        "arm": arm, "likelihood": f"faithful_schneider_additive_{arm}", "tag": tag,
        "free_groups": [rf.GNAMES[i] for i in fg], "n_obs_channels": int(n_obs), "n_band_freqs": int(len(freqs)),
        "dim": int(d), "tmcmc": {"n": n, "n_runs": n_runs},
        "fixed_hyper": {"l_f_hz": L_F_HZ, "l_z_in": L_Z_IN, "r_split": R_SPLIT, "sigma_meas": SIGMA_MEAS,
                        "zeta": ZETA, "sigma_w_prior_logN_center": SIGMA_W_FLOOR, "sigma_w_prior_logsd": SIGMA_W_LOGSD},
        "diag": diag, "converged": bool(conv),
        "gain_c": {"med": float(np.median(S[:, nfree])), "lo": float(np.percentile(S[:, nfree], 2.5)),
                   "hi": float(np.percentile(S[:, nfree], 97.5))},
        "sigma_w": ({"med": float(np.median(np.exp(S[:, nfree + 1]))),
                     "lo": float(np.percentile(np.exp(S[:, nfree + 1]), 2.5)),
                     "hi": float(np.percentile(np.exp(S[:, nfree + 1]), 97.5))} if arm != "M0" else None),
        "theta_post": {rf.GNAMES[g_]: {"med": float(np.median(theta_post[:, g_])),
                                       "lo": float(np.percentile(theta_post[:, g_], 2.5)),
                                       "hi": float(np.percentile(theta_post[:, g_], 97.5))} for g_ in fg},
        "runtime_s": time.time() - t0,
    }
    (WS / "out").mkdir(exist_ok=True)
    outp.write_text(json.dumps(rec, indent=2))
    print(f"[{arm}] faithful Schneider | obs {n_obs} ch x {len(freqs)} f, theta {rec['free_groups']}")
    print(f"  CONVERGED={conv} cross-run R-hat {diag['max_rhat']:.3f} ESS {diag['min_ess']:.0f} "
          f"div {diag['div_frac']:.3f} | log-evidence {diag['log_evidence_mean']:.1f} +- {diag['log_evidence_std']:.1f}")
    if arm != "M0":
        print(f"  sigma_w med {rec['sigma_w']['med']:.2f} [{rec['sigma_w']['lo']:.2f},{rec['sigma_w']['hi']:.2f}]"
              f" (vs old runaway 9.8) | gain c {rec['gain_c']['med']:.2f}")
    print(f"  theta medians: " + ", ".join(f"{rf.GNAMES[g_]} {np.median(theta_post[:,g_]):.2f}" for g_ in fg))
    print(f"  runtime {rec['runtime_s']:.0f}s -> {outp}")
    return rec


if __name__ == "__main__":
    arm = sys.argv[1] if len(sys.argv) > 1 else "M2"
    kw = {}
    for a in sys.argv[2:]:
        if a.startswith("--n_obs="): kw["n_obs"] = int(a.split("=")[1])
        elif a.startswith("--n="): kw["n"] = int(a.split("=")[1])
        elif a.startswith("--runs="): kw["n_runs"] = int(a.split("=")[1])
        elif a == "--force": kw["force"] = True
    run(arm, **kw)
