#!/usr/bin/env python3
"""The four StatFEM arms on the REAL matched-path FRF observable (Card A). Patterned on the copied
`nuts_arms.py` (NOT edited) but adds the GLOBAL units-gain nuisance c (D4) and uses the real forward.

Likelihood = whole log|H| over the quality-passed band frequencies x observed channels (D6):
  R(theta,c) = log|H_meas_obs| - (log|H_fem_obs(theta)| + c)        c = global units-gain (log-additive)
  M0 naive     R ~ N(0, sigma_meas^2 I)                       sigma_d = 0
  M1 iid       R ~ N(0, (sigma_meas^2 + sigma_d^2) I)         learn sigma_d
  M2 Schneider R ~ N(0, sigma_meas^2 I + sigma_d^2 C)         C = C_f (x) C_z (freq+space)
  M3 orthogonal R ~ N(0, sigma_meas^2 I + sigma_d^2 P_perp C P_perp)   P_perp removes theta->FRF span

theta ~ LogNormal(0, 0.25); sigma_d ~ HalfNormal(0.3); c ~ Normal(c0, 1.5). NUTS 4 chains, dense mass,
depth 6, all-variable convergence gate (AGENTS.md).
"""
from __future__ import annotations
import numpy as np
import jax, jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from numpyro.diagnostics import summary as nuts_summary
from numpyro.infer import MCMC, NUTS, init_to_median

jax.config.update("jax_enable_x64", True)

import core           # reused (copied): corr helpers
import realfrf as rf

NSIG_THETA = 0.25
SIGMA_D_PRIOR = 0.3
SIGMA_MEAS = 0.15      # iid log measurement+window+map noise floor on the real FRF (assumption, swept)
GAIN_PRIOR_SD = 1.5


def corr_freq(freqs, length):
    lf = np.log(freqs); d = lf[:, None] - lf[None, :]
    return np.exp(-0.5 * (d / length) ** 2)


def corr_space(coords, length):
    d = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1))
    return np.exp(-np.abs(d) / length)


def theta_jac(jforward):
    Jf = np.asarray(jax.jacfwd(jforward)(jnp.ones(9)))      # (Nf, Ns, 9)
    nf, ns, ng = Jf.shape
    return Jf.reshape(nf * ns, ng)


def build_cov(arm, freqs, coords_obs, jforward, len_logf=core.DISC_LEN_LOGF, len_z=core.DISC_LEN_Z):
    if arm in ("M0", "M1"):
        return None
    C = np.kron(corr_freq(freqs, len_logf), corr_space(coords_obs, len_z))
    if arm == "M3":
        J = theta_jac(jforward)
        Pp = np.eye(J.shape[0]) - J @ np.linalg.solve(J.T @ J, J.T)
        C = Pp @ C @ Pp; C = 0.5 * (C + C.T)
    lam, U = np.linalg.eigh(C)
    return jnp.asarray(U), jnp.asarray(np.clip(lam, 0.0, None))


def make_model(arm, jforward, target_obs, c0, sigma_meas=SIGMA_MEAS, cov=None,
               free_groups=None, fixed_sigma_d=None):
    """free_groups: list of group indices to CALIBRATE (others fixed at 1.0); None = all 9.
    fixed_sigma_d: if not None, the discrepancy std is FIXED (no runaway) instead of sampled."""
    tgt = jnp.asarray(target_obs)                 # (Nf, Ns)
    if cov is not None:
        U, Lam = cov
    fg = list(range(9)) if free_groups is None else list(free_groups)
    fg_arr = jnp.asarray(np.array(fg))
    nfree = len(fg)

    def model():
        log_theta_f = numpyro.sample("log_theta", dist.Normal(0.0, NSIG_THETA).expand([nfree]).to_event(1))
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(log_theta_f))
        c = numpyro.sample("gain", dist.Normal(c0, GAIN_PRIOR_SD))
        if arm == "M0":
            sigma_d = 0.0
        elif fixed_sigma_d is not None:
            sigma_d = float(fixed_sigma_d)
        else:
            sigma_d = numpyro.sample("sigma_d", dist.HalfNormal(SIGMA_D_PRIOR))
        R = tgt - (jforward(theta) + c)
        if arm in ("M0", "M1"):
            var = sigma_meas ** 2 + sigma_d ** 2
            numpyro.factor("lik", -0.5 * jnp.sum(R ** 2 / var + jnp.log(2 * jnp.pi * var)))
        else:
            rt = U.T @ R.reshape(-1)
            var = sigma_meas ** 2 + sigma_d ** 2 * Lam
            numpyro.factor("lik", -0.5 * jnp.sum(rt ** 2 / var + jnp.log(2 * jnp.pi * var)))
    return model


def run_arm(arm, R, freqs, target_obs, resp_rows_obs, drive_row, coords_obs, c0,
            zeta=rf.ZETA_NOM, sigma_meas=SIGMA_MEAS, num_warmup=1000, num_samples=1000,
            num_chains=4, seed=20260617, max_tree_depth=6, free_groups=None, fixed_sigma_d=None):
    jfwd = rf.jax_fem_logmag_factory(R, freqs, resp_rows_obs, drive_row, zeta=zeta)
    cov = build_cov(arm, freqs, coords_obs, jfwd)
    model = make_model(arm, jfwd, target_obs, c0, sigma_meas=sigma_meas, cov=cov,
                       free_groups=free_groups, fixed_sigma_d=fixed_sigma_d)
    kernel = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median,
                  dense_mass=True, max_tree_depth=max_tree_depth)
    mcmc = MCMC(kernel, num_warmup=num_warmup, num_samples=num_samples, num_chains=num_chains,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    grouped = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in grouped.items()}
    stats = nuts_summary(grouped, group_by_chain=True)
    max_rhat = max(float(np.nanmax(v["r_hat"])) for v in stats.values())
    min_ess = min(float(np.nanmin(v["n_eff"])) for v in stats.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    diag = {"max_rhat": max_rhat, "min_ess": min_ess, "divergences": div,
            "div_frac": div / (num_chains * num_samples), "n_chains": num_chains,
            "draws": num_chains * num_samples}
    return flat, diag
