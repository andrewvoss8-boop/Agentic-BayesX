#!/usr/bin/env python3
"""M2 whole-FRF Schneider arm (physics-in-LIKELIHOOD), computed KRONECKER-EFFICIENTLY.

real_arms.run_arm("M2",...) forms the full (Nf*Ns)x(Nf*Ns) covariance via np.kron + a dense eigh (~7912x7912
here) -> ~1.5 GB and OOM-prone on this machine. The covariance is sigma_meas^2 I + sigma_d^2 (C_f (x) C_z), a
KRONECKER structure, so it whitens via the tiny separate eigh of C_f (Nf x Nf) and C_z (Ns x Ns) -- NO dense
NfNs matrix. This is the IDENTICAL likelihood as real_arms.M2 (verified to ~1e-9 in m2_verify(); same
correlation lengths core.DISC_LEN_LOGF / core.DISC_LEN_Z, same sigma_meas, same HalfNormal(0.3) sigma_d, same
9 free groups), just memory-light. We do NOT edit the byte-identical real_arms.py; this is a faithful, faster
equivalent used only because the dense form OOMs.

Kronecker whitening (row-major vec of R (Nf,Ns)): cov = sigma_meas^2 I + sigma_d^2 (C_f (x) C_z),
C_f=Vf Df Vf^T, C_z=Vz Dz Vz^T  =>  whitened Rt = Vf^T R Vz, var[i,j] = sigma_meas^2 + sigma_d^2 Df[i] Dz[j].
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

import core
import realfrf as rf

NSIG_THETA = 0.25
SIGMA_D_PRIOR = 0.3
SIGMA_MEAS = 0.15
GAIN_PRIOR_SD = 1.5


def corr_freq(freqs, length):
    lf = np.log(freqs); d = lf[:, None] - lf[None, :]
    return np.exp(-0.5 * (d / length) ** 2)


def corr_space(coords, length):
    d = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1))
    return np.exp(-np.abs(d) / length)


def _make_model(jfwd, target_obs, c0, Vf, Df, Vz, Dz, sigma_meas, free_groups):
    tgt = jnp.asarray(target_obs)
    Vf = jnp.asarray(Vf); Df = jnp.asarray(Df); Vz = jnp.asarray(Vz); Dz = jnp.asarray(Dz)
    fg = list(range(9)) if free_groups is None else list(free_groups)
    fg_arr = jnp.asarray(np.array(fg)); nfree = len(fg)
    Lam = Df[:, None] * Dz[None, :]                      # (Nf, Ns) eigenvalues of C_f (x) C_z

    def model():
        log_theta = numpyro.sample("log_theta", dist.Normal(0.0, NSIG_THETA).expand([nfree]).to_event(1))
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(log_theta))
        c = numpyro.sample("gain", dist.Normal(c0, GAIN_PRIOR_SD))
        sigma_d = numpyro.sample("sigma_d", dist.HalfNormal(SIGMA_D_PRIOR))
        R = tgt - (jfwd(theta) + c)                       # (Nf, Ns)
        Rt = Vf.T @ R @ Vz                                # whitened residual
        var = sigma_meas ** 2 + sigma_d ** 2 * Lam
        numpyro.factor("lik", -0.5 * jnp.sum(Rt ** 2 / var + jnp.log(2 * jnp.pi * var)))
    return model


def run_m2(R, freqs, target_obs, obs_rows, drive_row, coords_obs, c0, sigma_meas=SIGMA_MEAS,
           len_logf=core.DISC_LEN_LOGF, len_z=core.DISC_LEN_Z, free_groups=None,
           num_warmup=500, num_samples=500, num_chains=4, seed=20260619):
    jfwd = rf.jax_fem_logmag_factory(R, freqs, obs_rows, drive_row, zeta=rf.ZETA_NOM)
    Df, Vf = np.linalg.eigh(corr_freq(freqs, len_logf))      # match dense real_arms: no jitter, clip at 0
    Dz, Vz = np.linalg.eigh(corr_space(coords_obs, len_z))
    Df = np.clip(Df, 0, None); Dz = np.clip(Dz, 0, None)
    model = _make_model(jfwd, target_obs, c0, Vf, Df, Vz, Dz, sigma_meas, free_groups)
    kernel = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median, dense_mass=True, max_tree_depth=6)
    mcmc = MCMC(kernel, num_warmup=num_warmup, num_samples=num_samples, num_chains=num_chains,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    grouped = mcmc.get_samples(group_by_chain=True)
    stats = nuts_summary(grouped, group_by_chain=True)
    max_rhat = max(float(np.nanmax(v["r_hat"])) for v in stats.values())
    min_ess = min(float(np.nanmin(v["n_eff"])) for v in stats.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in grouped.items()}
    diag = {"max_rhat": max_rhat, "min_ess": min_ess, "divergences": div,
            "div_frac": div / (num_chains * num_samples), "n_chains": num_chains,
            "draws": num_chains * num_samples,
            "converged": bool(max_rhat <= 1.05 and min_ess >= 200 and div / (num_chains * num_samples) < 0.02)}
    return flat, diag


def m2_verify(seed=0):
    """Verify the Kronecker-efficient M2 loglik == the dense real_arms M2 loglik on a TINY grid (so the dense
    7912->~ small matrix is cheap). Returns max abs diff over random parameter draws."""
    import real_arms as ra
    import ift_tmcmc as it
    S = it._split(seed)
    R = S["R"]; ch = S["ch"]
    # tiny grid: 8 freqs x first 5 observed channels
    freqs = S["freqs"][:: max(1, len(S["freqs"]) // 8)][:8]
    obs_rows = S["obs_rows"][:5]; coords = ch.coords[:5]
    # rebuild tiny target/obs consistently
    tgt = S["tru_obs"][:: max(1, S["tru_obs"].shape[0] // 8)][:8, :5]
    c0 = S["c0"]
    jf = rf.jax_fem_logmag_factory(R, freqs, obs_rows, ch.drive_row, zeta=rf.ZETA_NOM)
    # dense cov (real_arms machinery)
    U, Lam = ra.build_cov("M2", freqs, coords, jf)
    U = np.asarray(U); Lam = np.asarray(Lam)
    # efficient pieces
    Df, Vf = np.linalg.eigh(corr_freq(freqs, core.DISC_LEN_LOGF))
    Dz, Vz = np.linalg.eigh(corr_space(coords, core.DISC_LEN_Z))
    Df = np.clip(Df, 0, None); Dz = np.clip(Dz, 0, None)
    rng = np.random.default_rng(0); diffs = []; rels = []
    for _ in range(5):
        theta = np.exp(rng.normal(0, 0.25, 9)); c = c0 + rng.normal(0, 0.5); sd = abs(rng.normal(0.3, 0.1))
        Rm = tgt - (np.asarray(jf(theta)) + c)            # (8,5)
        # dense loglik
        rt = U.T @ Rm.reshape(-1); var = SIGMA_MEAS ** 2 + sd ** 2 * Lam
        ll_dense = -0.5 * np.sum(rt ** 2 / var + np.log(2 * np.pi * var))
        # efficient loglik
        Rt = Vf.T @ Rm @ Vz; var2 = SIGMA_MEAS ** 2 + sd ** 2 * (Df[:, None] * Dz[None, :])
        ll_eff = -0.5 * np.sum(Rt ** 2 / var2 + np.log(2 * np.pi * var2))
        diffs.append(abs(ll_dense - ll_eff)); rels.append(abs(ll_dense - ll_eff) / max(abs(ll_dense), 1e-30))
    return float(max(diffs)), float(max(rels))


if __name__ == "__main__":
    print("M2 dense-vs-Kronecker loglik max abs diff:", m2_verify())
