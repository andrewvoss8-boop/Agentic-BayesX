#!/usr/bin/env python3
"""Marginalised-Gaussian field likelihoods + NUTS for the two physics-residual constructions, on the
HARMONIC FORCED drive-point-FRF observable (decisions_log D11-D13).

Forward physics (discrete): dynamic-stiffness operator A(theta, omega) = -theta*c^2*D2 - omega^2*I
(D2 = cell-centred FD 2nd-derivative, eigen-decomposed once per resolution N: D2 = V diag(d_k) V^T, so
A = V diag(a_k) V^T with a_k = -theta*c^2*d_k - omega^2). A uniform unit load collocates to f_vec, with
eigen-projection g = V^T f_vec. The latent response field u is integrated out in closed form; the
forcing makes the marginal a Gaussian on the m sensor responses with a theta-DEPENDENT MEAN (so theta
is strongly identified through the data, unlike the eigenproblem framing). Both constructions share the
SAME residual operator and data; the ONLY difference is how the residual is weighted:

  M-lik (physics in LIKELIHOOD): residual "A u ~= f_vec" is FICTITIOUS data with FIXED noise sigma_r,
        plus a vague field prior u ~ N(0, tau^2 I). Per drive-frequency log-likelihood =
          (i)  physics pseudo-data evidence  -1/2 sum_k log(2pi (a_k^2 tau^2 + sigma_r^2))
          (ii) sensor term  logN(y_u; SV @ mu_k, (SV)diag(s_k^2)(SV)^T + sigma_u^2 I),
               s_k^2 = 1/(1/tau^2 + a_k^2/sigma_r^2),  mu_k = s_k^2 a_k g_k / sigma_r^2
        Knobs swept = N_c (size of d_k/SV) and sigma_r. Term (i) is the sigma_r/N_c-dependent piece.

  M-ift (physics in PRIOR, IFT/PIFT-style): u prior ~ exp(-beta/2 ||A u - f_vec||^2 - tau0/2||u||^2),
        i.e. precision beta*A^2 + tau0*I and mean mu0 = beta*P^-1 A f_vec; inverse-temperature beta is
        LEARNED. Per drive-frequency log-likelihood = logN(y_u; SV @ (beta t_k^2 a_k g_k),
        (SV)diag(t_k^2)(SV)^T + sigma_u^2 I), t_k^2 = 1/(tau0 + beta a_k^2). No sigma_r, no pseudo-data
        evidence (physics is the prior). Knob = N_c.

References: physics-in-likelihood = standard PINN/collocation residual penalty; physics-in-prior with a
learned inverse-temperature = IFT 2306.02150 / PIFT 2301.07609 (Alberts & Bilionis). Minimal
re-implementation; no results copied from github.com/PredictiveScienceLab/pift-paper-2023.
"""
from __future__ import annotations

import math
import time

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

LOG2PI = math.log(2.0 * math.pi)
TAU = 1.0       # M-lik vague field-prior std (nodal)
TAU0 = 1e-3     # M-ift ridge that makes the physics prior proper


def _gauss_loglik(SV, var_k, mean_eig, Yt, sigma_u2, m, n_rep, jitter=1e-12):
    """logN(y_u; SV @ mean_eig, (SV)diag(var_k)(SV)^T + sigma_u2 I_m) summed over replicates.
    Yt is (m, n_rep)."""
    Sigma = (SV * var_k) @ SV.T + (sigma_u2 + jitter) * jnp.eye(m)
    mu = SV @ mean_eig                                   # (m,)
    Lc = jnp.linalg.cholesky(Sigma)
    resid = Yt - mu[:, None]                             # (m, n_rep)
    sol = jax.scipy.linalg.solve_triangular(Lc, resid, lower=True)
    quad = jnp.sum(sol ** 2)
    logdet = 2.0 * jnp.sum(jnp.log(jnp.diag(Lc)))
    return -0.5 * quad - 0.5 * n_rep * (logdet + m * LOG2PI)


def _make_model(precomp, data, construction, sigma_r=None):
    d_k = jnp.asarray(precomp["d_k"])            # (N,)
    SV = jnp.asarray(precomp["SV"])              # (m, N)
    g = jnp.asarray(precomp["g"])                # (N,)
    m = SV.shape[0]
    y_u = jnp.asarray(data.y_u)                  # (n_rep, m, n_freq)
    drive = jnp.asarray(data.drive_fit)          # (n_freq,)
    sig_u2 = jnp.asarray(data.sigma_u) ** 2      # (n_freq,)
    n_freq = drive.shape[0]
    n_rep = y_u.shape[0]
    is_ift = (construction == "M-ift")
    sr2 = None if sigma_r is None else float(sigma_r) ** 2

    def model():
        theta = numpyro.sample("theta", dist.LogNormal(0.0, 0.20))
        beta = numpyro.sample("beta", dist.LogNormal(math.log(1e3), 2.0)) if is_ift else None
        total = 0.0
        for f in range(n_freq):
            a = -theta * core.C2 * d_k - drive[f] ** 2          # (N,) eigenvalues of A
            Yt = y_u[:, :, f].T
            if is_ift:
                t_k = 1.0 / (TAU0 + beta * a ** 2)
                mean_eig = beta * t_k * a * g
                total = total + _gauss_loglik(SV, t_k, mean_eig, Yt, sig_u2[f], m, n_rep)
            else:
                s_k = 1.0 / (1.0 / TAU ** 2 + a ** 2 / sr2)
                mean_eig = s_k * a * g / sr2
                total = total + _gauss_loglik(SV, s_k, mean_eig, Yt, sig_u2[f], m, n_rep)
                total = total - 0.5 * jnp.sum(jnp.log(2.0 * jnp.pi * (a ** 2 * TAU ** 2 + sr2)))
        numpyro.factor("loglik", total)

    return model


def run(precomp, data, construction, sigma_r=None,
        num_warmup=1000, num_samples=1000, num_chains=4, seed=20260616, target_accept=0.9):
    model = _make_model(precomp, data, construction, sigma_r=sigma_r)
    kernel = NUTS(model, target_accept_prob=target_accept, init_strategy=init_to_median)
    mcmc = MCMC(kernel, num_warmup=num_warmup, num_samples=num_samples, num_chains=num_chains,
                chain_method="sequential", progress_bar=False)
    t0 = time.time()
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    rt = time.time() - t0
    grouped = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in grouped.items()}
    stats = nuts_summary(grouped, group_by_chain=True)
    max_rhat = max(float(np.nanmax(v["r_hat"])) for v in stats.values())
    min_ess = min(float(np.nanmin(v["n_eff"])) for v in stats.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    diag = {"max_rhat": max_rhat, "min_ess": min_ess, "divergences": div,
            "div_frac": div / (num_chains * num_samples),
            "n_chains": num_chains, "draws": num_chains * num_samples}
    return flat, diag, rt


def _pred_mean_var(precomp, theta, omega, construction, sigma_r=None, beta=None):
    """Posterior-predictive sensor mean and per-sensor variance at a (held-out) drive frequency for one
    parameter draw (the construction's own field uncertainty, sensor noise added by the caller)."""
    d_k = np.asarray(precomp["d_k"]); SV = np.asarray(precomp["SV"]); g = np.asarray(precomp["g"])
    a = -theta * core.C2 * d_k - omega ** 2
    if construction == "M-ift":
        var_k = 1.0 / (TAU0 + beta * a ** 2)
        mean_eig = beta * var_k * a * g
    else:
        sr2 = sigma_r ** 2
        var_k = 1.0 / (1.0 / TAU ** 2 + a ** 2 / sr2)
        mean_eig = var_k * a * g / sr2
    mu = SV @ mean_eig
    var = np.sum((SV ** 2) * var_k, axis=1)         # diag of (SV)diag(var_k)(SV)^T
    return mu, var


def heldout_coverage(precomp, data, samples, construction, sigma_r=None, prob=95.0, thin=2, seed=7):
    """Posterior-predictive 95% coverage of the held-out drive-point-FRF responses (all sensors x all
    held-out frequencies). Each construction uses its OWN predictive (field uncertainty + sensor noise)."""
    rng = np.random.default_rng(seed)
    th = samples["theta"][::thin]
    bt = samples["beta"][::thin] if "beta" in samples else [None] * len(th)
    held = data.drive_held
    truth = data.u_held_true                          # (m, n_freqH)
    sig_h = data.sigma_u_held
    covered = 0; ntot = 0
    los, meds, his = [], [], []
    for j, w in enumerate(held):
        draws = []
        for s in range(len(th)):
            mu, var = _pred_mean_var(precomp, float(th[s]), float(w), construction,
                                     sigma_r=sigma_r, beta=(None if bt[s] is None else float(bt[s])))
            tot = np.sqrt(np.clip(var, 0, None) + sig_h[j] ** 2)
            draws.append(mu + rng.normal(0, 1, len(mu)) * tot)
        draws = np.array(draws)                        # (S, m)
        lo = np.percentile(draws, (100 - prob) / 2, axis=0)
        hi = np.percentile(draws, 100 - (100 - prob) / 2, axis=0)
        med = np.median(draws, axis=0)
        inside = (truth[:, j] >= lo) & (truth[:, j] <= hi)
        covered += int(inside.sum()); ntot += len(inside)
        los.append(lo.tolist()); meds.append(med.tolist()); his.append(hi.tolist())
    return {"covered": covered, "n": ntot, "frac": covered / max(ntot, 1),
            "lo": los, "med": meds, "hi": his, "held_freqs": held.tolist()}


def mift_beta_posterior(precomp, data, samples, thin=4):
    """Report the learned IFT inverse-temperature: percentiles of the sampled beta (median + 95% CI in
    log-beta) and whether it is weakly identified relative to its prior."""
    lb = np.log(samples["beta"][::thin])
    med, lo, hi = np.percentile(lb, [50, 2.5, 97.5])
    width = hi - lo
    return {"logbeta_med": float(med), "logbeta_lo": float(lo), "logbeta_hi": float(hi),
            "logbeta_ci_width": float(width), "beta_med": float(np.exp(med)),
            "weakly_identified": bool(width > 0.5 * 2 * 1.96 * 2.0)}  # vs prior log-sd 2.0
