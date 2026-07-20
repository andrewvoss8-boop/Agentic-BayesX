#!/usr/bin/env python3
"""statFEM whole-curve transmissibility calibration engine (NUTS, convergence-gated) + held-out scoring +
climatology. The forward log|T_a(f;theta,zeta)| is made DIFFERENTIABLE in theta via first-order eigenvalue
sensitivity (Fox-Kapoor): lam_i(theta) = lam0_i * (1 + sum_g f^K_{i,g} (theta_g-1)), f^K_{i,g} = phi_i^T K_g phi_i
/ lam_i (the modal strain-energy fraction, = the identifiability statistic). Mode SHAPES and the load participation
gamma are held at nominal (their first-order effect on the resonance RATIO is absorbed by the discrepancy). zeta
(modal damping) enters D_i and is a free lever. Likelihood = peak-weighted Gaussian on log|T| over the TRAINING
locations (statFEM y=rho P u + d + e; Kiran Eq 18). ONE global training-only centering c (gain-free already;
no per-channel gain). Discrepancy: iid (M0). Reuses score.py BYTE-IDENTICAL for all proper scores.

Convergence gate (AGENTS): >=4 chains, report max R-hat / min ESS / divergence frac over ALL sampled variables;
non-converged => YELLOW, never "calibrated".
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
import numpy as np

os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=4")

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mpl_fem as FF
import score as SC

WS = Path(__file__).resolve().parents[1]; OUT = WS / "out"
FMAX_KEEP = 300.0                 # keep modes a bit past the 260 Hz band edge (tails)
HELD = ["interface", "beam", "valve", "avi-L", "avi-R"]
REF = "shield"
# default calibrated K-groups (major structural stiffnesses); a model-class lever
M0_GROUPS = ["K_shield_bend", "K_shield_mem", "K_beam_wall", "K_beam_rest", "K_plate_bend", "K_bush_joints"]


def precompute():
    """Solve nominal modes; cache lam0, phi_x at each location, gamma, and per-group SE fractions f^K_{i,g}."""
    fem = FF.FEM_model()
    freqs, Phi = fem.solve_modes()
    keep = freqs <= FMAX_KEEP
    freqs = freqs[keep]; Phi = Phi[:, keep]
    lam0 = (2 * np.pi * freqs) ** 2
    phix, gamma = fem.oop_shapes(Phi)
    # per-group strain-energy fraction f^K_{i,g} = phi_i^T K_g phi_i / lam_i for each calibrated K-group
    se = {}
    for g in M0_GROUPS:
        n = g[2:]  # strip 'K_'
        Kg = fem.KG[n]
        se[g] = np.einsum("ij,ij->j", Phi, (Kg @ Phi)) / np.maximum(lam0, 1e-30)
    d = np.load(OUT / "measured_transmissibility.npz")
    fgrid = d["freqs"]
    Tmeas = {l: d[f"T_{l}"] for l in (HELD + [REF])}
    return dict(fem=fem, freqs=freqs, lam0=lam0, phix=phix, gamma=gamma, se=se,
                fgrid=fgrid, Tmeas=Tmeas, groups=list(M0_GROUPS))


# ---------------------------------------------------------------- JAX forward + NUTS
def calibrate_split(P, train, groups, seed=20260620, warmup=1000, samples=1000, chains=4,
                    prior_theta_sd=0.12, zeta0=0.01):
    import jax, jax.numpy as jnp
    import numpyro, numpyro.distributions as dist
    from numpyro.infer import MCMC, NUTS
    numpyro.set_host_device_count(chains)

    fgrid = P["fgrid"]; w = 2 * np.pi * fgrid
    lam0 = jnp.asarray(P["lam0"]); wj = jnp.asarray(w)
    SE = jnp.asarray(np.stack([P["se"][g] for g in groups], 0))     # (G, nmodes)
    gamma = jnp.asarray(P["gamma"])
    phix = {l: jnp.asarray(P["phix"][l]) for l in (train + [REF])}
    # measured log|T| + peak weights over the TRAINING locations
    logTm = {l: jnp.asarray(np.log(np.maximum(P["Tmeas"][l], 1e-12))) for l in train}
    pw = {l: jnp.asarray(SC.peak_weight(P["Tmeas"][l], fgrid)) for l in train}

    def forward_logT(theta, zeta):
        lam = lam0 * (1.0 + jnp.sum(SE * (theta[:, None] - 1.0), axis=0))     # (nmodes,)
        lam = jnp.maximum(lam, 1e-6)
        D = (lam[:, None] - wj[None, :] ** 2) + 1j * (2.0 * zeta * jnp.sqrt(lam)[:, None] * wj[None, :])
        Href = jnp.sum((phix[REF] * gamma)[:, None] / D, axis=0)
        out = {}
        for l in train:
            Ha = jnp.sum((phix[l] * gamma)[:, None] / D, axis=0)
            out[l] = jnp.log(jnp.abs(Ha) / jnp.maximum(jnp.abs(Href), 1e-12) + 1e-12)
        return out

    G = len(groups)

    def model():
        tau = numpyro.sample("tau", dist.Normal(jnp.zeros(G), prior_theta_sd))    # theta = exp(tau)
        theta = numpyro.deterministic("theta", jnp.exp(tau))
        logz = numpyro.sample("log_zeta", dist.Normal(jnp.log(zeta0), 0.5))
        zeta = numpyro.deterministic("zeta", jnp.exp(logz))
        c = numpyro.sample("c", dist.Normal(0.0, 1.0))                            # ONE global centering
        sigd = numpyro.sample("sigma_d", dist.HalfNormal(1.0))
        pred = forward_logT(theta, zeta)
        ll = 0.0
        for l in train:
            r = logTm[l] - (pred[l] + c)
            wl = pw[l] / jnp.mean(pw[l])                                          # mean-1 weights
            ll = ll + jnp.sum(wl * dist.Normal(0.0, sigd).log_prob(r))
        numpyro.factor("whole_curve", ll)

    kernel = NUTS(model, target_accept_prob=0.9)
    mcmc = MCMC(kernel, num_warmup=warmup, num_samples=samples, num_chains=chains,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed))
    post = mcmc.get_samples(group_by_chain=False)
    # convergence over ALL sampled variables (incl. raw tau, log_zeta, c, sigma_d)
    import numpyro.diagnostics as diag
    grp = mcmc.get_samples(group_by_chain=True)
    rhats, esss = [], []
    for k, v in grp.items():
        va = np.asarray(v)
        if va.ndim == 2:
            rhats.append(float(diag.gelman_rubin(va))); esss.append(float(diag.effective_sample_size(va)))
        else:
            for j in range(va.shape[-1]):
                rhats.append(float(diag.gelman_rubin(va[:, :, j]))); esss.append(float(diag.effective_sample_size(va[:, :, j])))
    ndiv = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum()) if "diverging" in mcmc.get_extra_fields() else 0
    nsamp = samples * chains
    conv = dict(max_rhat=float(np.nanmax(rhats)), min_ess=float(np.nanmin(esss)),
                div_frac=float(ndiv / max(nsamp, 1)), n_samples=int(nsamp))
    conv["converged"] = bool(conv["max_rhat"] <= 1.05 and conv["min_ess"] >= 200 and conv["div_frac"] < 0.02)
    return post, conv


def predict_logT_np(P, theta, zeta, loc):
    """numpy forward log|T| at a location for given theta (G,) and scalar zeta (post-hoc prediction)."""
    fgrid = P["fgrid"]; w = 2 * np.pi * fgrid
    SE = np.stack([P["se"][g] for g in P["groups_used"]], 0)
    lam = P["lam0"] * (1.0 + np.sum(SE * (theta[:, None] - 1.0), axis=0))
    lam = np.maximum(lam, 1e-6)
    D = (lam[:, None] - w[None, :] ** 2) + 1j * (2.0 * zeta * np.sqrt(lam)[:, None] * w[None, :])
    Href = np.sum((P["phix"][REF] * P["gamma"])[:, None] / D, axis=0)
    Ha = np.sum((P["phix"][loc] * P["gamma"])[:, None] / D, axis=0)
    return np.log(np.abs(Ha) / np.maximum(np.abs(Href), 1e-12) + 1e-12)
