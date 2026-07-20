#!/usr/bin/env python3
"""The four StatFEM-evaluation arms (NUTS calibration on observed channels).

Likelihood = whole log|H| over the observed channels (all 160 band points; NO peak/feature selection).
Residual R(theta) = log|H_meas_obs| - log|H_model_obs(theta)|, vec C-order (freq outer, sensor inner).

  M0 naive        R ~ N(0, sigma_meas^2 I)                      sigma_d FIXED 0 (no model-form mechanism)
  M1 StatFEM-iid  R ~ N(0, (sigma_meas^2 + sigma_d^2) I)        learn sigma_d, iid discrepancy
  M2 Schneider    R ~ N(0, sigma_meas^2 I + sigma_d^2 C)        C = C_f (x) C_z, freq+space correlated
  M3 orthogonal   R ~ N(0, sigma_meas^2 I + sigma_d^2 P_perp C P_perp)   P_perp removes the theta->FRF span

For M2/M3 the covariance STRUCTURE (C or P_perp C P_perp) is fixed -> eigendecompose ONCE in numpy,
pass (U, Lam); inside NUTS only the scale sigma_d and theta vary. Whitened likelihood:
  rt = U^T vec(R);  var = sigma_meas^2 + sigma_d^2 Lam;  loglik = -0.5 sum(rt^2/var + log(2 pi var)).

theta ~ LogNormal(0, 0.25) (9 groups); sigma_d ~ HalfNormal(0.3). NUTS, 4 chains, dense mass,
all-variable convergence diagnostics (AGENTS.md gate).
"""
from __future__ import annotations

import numpy as np

import jax
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from numpyro.diagnostics import summary as nuts_summary
from numpyro.infer import MCMC, NUTS, init_to_median

jax.config.update("jax_enable_x64", True)

import core  # noqa: E402

NSIG_THETA = core.NSIG_THETA
SIGMA_D_PRIOR = 0.3


def corr_freq(freqs, length):
    lf = np.log(freqs)
    d = lf[:, None] - lf[None, :]
    return np.exp(-0.5 * (d / length) ** 2)


def corr_space(coords, length):
    d = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1))
    return np.exp(-np.abs(d) / length)


def theta_jacobian(model, freqs, observed, drive, zeta=core.ZETA_NOM):
    """J = d vec(log|H_obs|) / d theta at nominal theta=1, shape (Nf*Ns, 9), C-order (freq outer)."""
    fwd = core.jax_forward_factory(model, freqs, observed, drive, zeta=zeta)
    Jf = jax.jacfwd(fwd)(jnp.ones(9))           # (Nf, Ns, 9)
    Jf = np.asarray(Jf)
    nf, ns, ng = Jf.shape
    return Jf.reshape(nf * ns, ng)


def build_cov(arm, freqs, coords_obs, model=None, observed=None, drive=None, zeta=core.ZETA_NOM,
              len_logf=core.DISC_LEN_LOGF, len_z=core.DISC_LEN_Z):
    """Return (U, Lam) eigenbasis of the discrepancy correlation structure for M2/M3, else None.
    C = C_f (x) C_z (full Nf*Ns matrix). M3 projects: M = P_perp C P_perp, P_perp = I - J(J^T J)^-1 J^T."""
    if arm in ("M0", "M1"):
        return None
    Cf = corr_freq(freqs, len_logf)
    Cz = corr_space(coords_obs, len_z)
    C = np.kron(Cf, Cz)                          # (N, N), N = Nf*Ns, C-order matches vec(R)
    if arm == "M3":
        J = theta_jacobian(model, freqs, observed, drive, zeta=zeta)   # (N, 9)
        # orthogonal projector onto complement of col(J)
        JTJ = J.T @ J
        Pperp = np.eye(J.shape[0]) - J @ np.linalg.solve(JTJ, J.T)
        C = Pperp @ C @ Pperp
        C = 0.5 * (C + C.T)                      # symmetrize
    lam, U = np.linalg.eigh(C)
    lam = np.clip(lam, 0.0, None)
    return jnp.asarray(U), jnp.asarray(lam)


def make_model(arm, logmag_fn, target_obs, sigma_meas, cov=None):
    tgt = jnp.asarray(target_obs)               # (Nf, Ns)
    N = tgt.size
    if cov is not None:
        U, Lam = cov

    def model():
        log_theta = numpyro.sample("log_theta", dist.Normal(0.0, NSIG_THETA).expand([9]).to_event(1))
        theta = jnp.exp(log_theta)
        if arm == "M0":
            sigma_d = 0.0
        else:
            sigma_d = numpyro.sample("sigma_d", dist.HalfNormal(SIGMA_D_PRIOR))
        lm = logmag_fn(theta)                    # (Nf, Ns)
        R = tgt - lm
        if arm in ("M0", "M1"):
            var = sigma_meas ** 2 + sigma_d ** 2
            numpyro.factor("lik", -0.5 * jnp.sum(R ** 2 / var + jnp.log(2.0 * jnp.pi * var)))
        else:  # M2, M3: whitened correlated likelihood
            rt = U.T @ R.reshape(-1)
            var = sigma_meas ** 2 + sigma_d ** 2 * Lam
            numpyro.factor("lik", -0.5 * jnp.sum(rt ** 2 / var + jnp.log(2.0 * jnp.pi * var)))

    return model


def run_arm(arm, model_obj, freqs, target_obs, observed, drive, zeta=core.ZETA_NOM,
            sigma_meas=core.SIGMA_MEAS, num_warmup=1000, num_samples=1000, num_chains=4,
            seed=20260616, dense_mass=True, max_tree_depth=6,
            len_logf=core.DISC_LEN_LOGF, len_z=core.DISC_LEN_Z):
    """Run one arm. target_obs = log|H_meas| on observed channels, shape (Nf, Ns).

    max_tree_depth capped at 6 (64 leapfrog steps): the FRF magnitude is hyper-sensitive near resonances, so
    the identified groups are pinned VERY tightly -> a stiff posterior direction that uncapped NUTS chases to
    depth 10 (1023 steps). Probe (D12): depth-6 gives R-hat 1.019 / mean 49 steps; depth-8 gives R-hat 1.020 /
    mean 59 / max 255 at 2x cost -> depth 6 is the sweet spot. The convergence gate (R-hat/ESS/div over ALL
    variables incl. the flat unidentified groups) still decides; capping only bounds cost."""
    logmag_fn = core.jax_forward_factory(model_obj, freqs, observed, drive, zeta=zeta)
    coords_obs = model_obj.dof_xyz[np.asarray(observed)]
    cov = build_cov(arm, freqs, coords_obs, model=model_obj, observed=observed, drive=drive, zeta=zeta,
                    len_logf=len_logf, len_z=len_z)
    model = make_model(arm, logmag_fn, target_obs, sigma_meas, cov=cov)
    kernel = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median, dense_mass=dense_mass,
                  max_tree_depth=max_tree_depth)
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
    return flat, diag, cov
