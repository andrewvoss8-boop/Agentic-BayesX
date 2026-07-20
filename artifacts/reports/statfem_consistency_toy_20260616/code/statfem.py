#!/usr/bin/env python3
"""M-statfem construction (Girolami et al. 2021, arXiv:1905.06391) on the forced drive-point FRF
(decisions_log D11-D13). The FE model gives the prediction; data = FE prediction + additive zero-mean
model discrepancy d + measurement noise; infer theta together with the discrepancy scale sigma_d.
Knob = mesh h (number of elements n_el).

Forward (consistent-mass axial-bar FE): u_FE(theta, omega; h) = (theta*K0 - omega^2 M)^-1 b, with b the
consistent uniform load. Differentiable in theta via the linear solve (no eigendecomposition). The
prediction at the m sensors is S @ u_FE.

Observation model (statFEM additive discrepancy in the OBSERVATION space, here a spatially correlated
zero-mean discrepancy over the sensors with scale sigma_d and a fixed length-scale, plus sensor noise):
    y_u(omega_f) ~ Normal( S u_FE(theta,omega_f;h) + d_f, sigma_u_f ),  d_f ~ N(0, sigma_d^2 * C)
    => marginal y_u ~ Normal( S u_FE, sigma_d^2 C + sigma_u_f^2 I )
Infer theta, sigma_d. NUTS, >=4 chains, all-variable convergence gate.
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

DISC_LEN = 0.4   # fixed spatial correlation length of the statFEM discrepancy over the sensors (nondim)


def _disc_corr(sensors=core.SENSORS, length=DISC_LEN):
    """Squared-exponential spatial correlation of the additive discrepancy across sensors."""
    dx = sensors[:, None] - sensors[None, :]
    return np.exp(-0.5 * (dx / length) ** 2)


def fe_precompute(n_el):
    """Precompute FE stiffness K0, mass M, consistent load b, and the sensor-interpolation of the FE
    basis so that S u = (sensor map) applied to the nodal solution. Returns matrices for the model."""
    K0, M, x_nodes = core.fe_assemble(n_el)
    b = core.fe_assemble_load(n_el)
    # sensor interpolation matrix over FE nodes (include fixed node value 0)
    xn = np.concatenate(([0.0], x_nodes))
    m = len(core.SENSORS)
    Smap = np.zeros((m, len(x_nodes)))
    for i, xs in enumerate(core.SENSORS):
        j = np.searchsorted(xn, xs); j = min(max(j, 1), len(x_nodes))
        x0, x1 = xn[j - 1], xn[j]
        w = (xs - x0) / (x1 - x0) if x1 > x0 else 0.0
        if j - 1 >= 1:
            Smap[i, j - 2] += (1 - w)
        Smap[i, j - 1] += w
    return {"n_el": n_el, "K0": K0, "M": M, "b": b, "Smap": Smap}


def _make_model(precomp, data):
    K0 = jnp.asarray(precomp["K0"]); M = jnp.asarray(precomp["M"]); b = jnp.asarray(precomp["b"])
    Smap = jnp.asarray(precomp["Smap"])
    y_u = jnp.asarray(data.y_u)                   # (n_rep, m, n_freq)
    drive = jnp.asarray(data.drive_fit)
    sig_u2 = jnp.asarray(data.sigma_u) ** 2
    n_freq = drive.shape[0]; n_rep = y_u.shape[0]
    m = Smap.shape[0]
    C = jnp.asarray(_disc_corr())
    u_ref = float(np.sqrt(np.mean(data.u_true ** 2)))   # response scale, for the sigma_d prior

    def model():
        theta = numpyro.sample("theta", dist.LogNormal(0.0, 0.20))
        sigma_d = numpyro.sample("sigma_d", dist.HalfNormal(0.5 * u_ref))
        total = 0.0
        for f in range(n_freq):
            u = jnp.linalg.solve(theta * K0 - drive[f] ** 2 * M, b)   # FE forced solve
            mu = Smap @ u                                              # (m,)
            Sigma = sigma_d ** 2 * C + sig_u2[f] * jnp.eye(m)
            Lc = jnp.linalg.cholesky(Sigma + 1e-12 * jnp.eye(m))
            resid = y_u[:, :, f].T - mu[:, None]                      # (m, n_rep)
            sol = jax.scipy.linalg.solve_triangular(Lc, resid, lower=True)
            logdet = 2.0 * jnp.sum(jnp.log(jnp.diag(Lc)))
            total = total - 0.5 * jnp.sum(sol ** 2) - 0.5 * n_rep * (logdet + m * math.log(2 * math.pi))
        numpyro.factor("loglik", total)

    return model


def run(precomp, data, num_warmup=1000, num_samples=1000, num_chains=4, seed=20260616, target_accept=0.9):
    model = _make_model(precomp, data)
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


def heldout_coverage(precomp, data, samples, prob=95.0, thin=2, seed=11):
    """Posterior-predictive 95% coverage of the held-out drive-point-FRF responses: FE forward at theta
    PLUS a draw of the learned additive discrepancy d ~ N(0, sigma_d^2 C) and measurement noise."""
    rng = np.random.default_rng(seed)
    K0 = precomp["K0"]; M = precomp["M"]; b = precomp["b"]; Smap = precomp["Smap"]
    C = _disc_corr(); Lc = np.linalg.cholesky(C + 1e-12 * np.eye(C.shape[0]))
    th = samples["theta"][::thin]; sd = samples["sigma_d"][::thin]
    held = data.drive_held; truth = data.u_held_true; sig_h = data.sigma_u_held
    covered = 0; ntot = 0; los, meds, his = [], [], []
    for j, w in enumerate(held):
        draws = []
        for s in range(len(th)):
            u = np.linalg.solve(th[s] * K0 - w ** 2 * M, b)
            mu = Smap @ u
            disc = sd[s] * (Lc @ rng.normal(0, 1, len(mu)))
            noise = rng.normal(0, 1, len(mu)) * sig_h[j]
            draws.append(mu + disc + noise)
        draws = np.array(draws)
        lo = np.percentile(draws, (100 - prob) / 2, axis=0)
        hi = np.percentile(draws, 100 - (100 - prob) / 2, axis=0)
        med = np.median(draws, axis=0)
        inside = (truth[:, j] >= lo) & (truth[:, j] <= hi)
        covered += int(inside.sum()); ntot += len(inside)
        los.append(lo.tolist()); meds.append(med.tolist()); his.append(hi.tolist())
    return {"covered": covered, "n": ntot, "frac": covered / max(ntot, 1),
            "lo": los, "med": meds, "hi": his, "held_freqs": held.tolist()}
