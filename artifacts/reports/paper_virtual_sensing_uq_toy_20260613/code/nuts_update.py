#!/usr/bin/env python3
"""Discrepancy-aware Bayesian (NUTS) closed-loop update.

Implements the uncertainty quantification the paper defers (Future-Work #3): the masked
("virtual ground truth") channels are down-weighted by an inflated credibility noise, and a
model-form discrepancy scale sigma_d is learned. Optional correlated (Schneider-style)
discrepancy for E4.

Likelihood is on log-amplitude FRF (paper Eq. 21 uses log magnitude). NUTS, >=4 chains,
all-variable convergence diagnostics (AGENTS.md gate).
"""
from __future__ import annotations

import math

import jax
import jax.numpy as jnp
import numpy as np
import numpyro
import numpyro.distributions as dist
from numpyro.diagnostics import summary as nuts_summary
from numpyro.infer import MCMC, NUTS, init_to_median

import core

jax.config.update("jax_enable_x64", True)
numpyro.set_host_device_count(4)


def _corr_eig(freqs, corr_logf):
    """Eigendecomposition of the squared-exponential correlation matrix over log-frequency.
    Used for a numerically stable correlated-discrepancy likelihood with an iid nugget:
      cov = sigma_d^2 * K_corr + sig_iid^2 * I = U diag(sigma_d^2 lam + sig_iid^2) U^T."""
    logf = np.log(freqs)
    dl = logf[:, None] - logf[None, :]
    K = np.exp(-0.5 * (dl / corr_logf) ** 2)
    lam, U = np.linalg.eigh(K)
    lam = np.clip(lam, 0.0, None)
    return lam, U


def run_nuts(freqs, modes: core.Modes, target_logmag, channels_used, sigma_per_channel,
             correlated=False, corr_logf=0.25, corr_channels=None, dense_mass=False,
             num_warmup=800, num_samples=800, num_chains=4, seed=20260613):
    frf_j = core.frf_jax_factory()
    nm = modes.nm
    freqs_j = jnp.asarray(freqs)
    wi = jnp.asarray(2.0 * np.pi * modes.f)
    two_zeta_wi = jnp.asarray(2.0 * modes.zeta * (2.0 * np.pi * modes.f))
    Phi_part = jnp.asarray(modes.Phi * modes.part[None, :])
    tgt = jnp.asarray(np.asarray(target_logmag))
    used = np.asarray(channels_used)
    sig_ch = jnp.asarray(np.asarray(sigma_per_channel, dtype=float))
    # Which channels carry a CORRELATED discrepancy (default: all used channels).
    corr_set = set(used.tolist()) if corr_channels is None else set(np.asarray(corr_channels).tolist())
    if correlated:
        lam_np, U_np = _corr_eig(freqs, corr_logf)
        lam = jnp.asarray(lam_np)
        U = jnp.asarray(U_np)

    def model():
        log_alpha = numpyro.sample("log_alpha", dist.Normal(0.0, 0.15).expand([nm]).to_event(1))
        log_beta = numpyro.sample("log_beta", dist.Normal(0.0, 0.5).expand([nm]).to_event(1))
        log_gamma = numpyro.sample("log_gamma", dist.Normal(math.log(core.GAMMA0), 0.2))
        sigma_d = numpyro.sample("sigma_d", dist.HalfNormal(0.3))
        alpha = jnp.exp(log_alpha)
        beta = jnp.exp(log_beta)
        gamma = jnp.exp(log_gamma)
        H = frf_j(freqs_j, alpha, beta, gamma, Phi_part, wi, two_zeta_wi)
        logmag = jnp.log(jnp.abs(H))  # (Nf, Nc)
        for c in used:
            r = tgt[:, c] - logmag[:, c]
            if correlated and c in corr_set:
                # cov = sigma_d^2 K_corr + sig_ch^2 I, via eigenbasis (stable, iid nugget)
                rt = U.T @ r
                var = sigma_d ** 2 * lam + sig_ch[c] ** 2
                numpyro.factor(f"ch{c}", -0.5 * jnp.sum(rt ** 2 / var + jnp.log(2.0 * jnp.pi * var)))
            else:
                sig = jnp.sqrt(sig_ch[c] ** 2 + sigma_d ** 2)
                numpyro.sample(f"ch{c}", dist.Normal(logmag[:, c], sig).to_event(1), obs=tgt[:, c])

    kernel = NUTS(model, target_accept_prob=0.95 if dense_mass else 0.92,
                  init_strategy=init_to_median, dense_mass=dense_mass)
    mcmc = MCMC(kernel, num_warmup=num_warmup, num_samples=num_samples, num_chains=num_chains,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    grouped = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in grouped.items()}
    stats = nuts_summary(grouped, group_by_chain=True)
    max_rhat = max(float(np.nanmax(v["r_hat"])) for v in stats.values())
    min_ess = min(float(np.nanmin(v["n_eff"])) for v in stats.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    diagnostics = {
        "max_rhat": max_rhat,
        "min_ess": min_ess,
        "divergences": div,
        "div_frac": div / (num_chains * num_samples),
        "n_chains": num_chains,
        "draws": num_chains * num_samples,
    }
    return flat, diagnostics


def posterior_predict(samples, freqs, modes: core.Modes, sigma_per_channel, rng,
                      thin=4):
    """Posterior predictive log-amplitude per channel, with output-space residual inflation
    by each channel's total noise (sigma_channel; discrepancy added separately by caller if
    desired). Returns arrays of shape (S, Nf, Nc) for clean predicted log-mag and a noisy
    predictive draw."""
    n = len(samples["log_gamma"])
    idx = np.arange(0, n, thin)
    S = len(idx)
    nf, nc = len(freqs), modes.nc
    clean = np.zeros((S, nf, nc))
    noisy = np.zeros((S, nf, nc))
    sig_ch = np.asarray(sigma_per_channel, dtype=float)
    sd = samples.get("sigma_d", np.zeros(n))
    for j, s in enumerate(idx):
        alpha = np.exp(samples["log_alpha"][s])
        beta = np.exp(samples["log_beta"][s])
        gamma = float(np.exp(samples["log_gamma"][s]))
        H = core.frf_np(freqs, alpha, beta, gamma, modes)
        lm = np.log(np.abs(H))
        clean[j] = lm
        total = np.sqrt(sig_ch[None, :] ** 2 + float(sd[s]) ** 2)
        noisy[j] = lm + rng.normal(0, 1, (nf, nc)) * total
    return clean, noisy, idx


def interval(x, probs=(2.5, 50.0, 97.5)):
    return [float(v) for v in np.percentile(x, probs)]
