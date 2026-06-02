#!/usr/bin/env python3
"""Full sequential dome/tray vibe -> modal -> flight Bayesian experiment (NUTS/HMC).

Runner: Claude Code Opus 4.8 (isolated copy). This script consumes the checked
setup packet at artifacts/reports/sequential_vibe_modal_flight_20260602/ and runs
hierarchical NumPyro NUTS inference, producing posterior + QOI intervals,
diagnostics, figures, and the runner report contract.

Conventions inherited from the setup packet (do not change silently):
  - PSD-space dB: factor = 10 ** (dB / 10). Dome = m1, tray = m2.
  - Flight-to-flight forcing variability fixed/known at 3 dB (Matern-3/2 GP in log freq).
  - Build-to-build variability and sensor-noise scale are LEARNED.
  - Forcing GP is Matern-3/2 (NOT RBF) with log-frequency length scale 0.08.

NUTS/HMC is the real sampler here (numpyro). No random-walk/random-scan Metropolis.

Backend note: numpyro/jax are not in the system Python 3.9.6. They were installed
into ./.venv_nuts. Run via scripts/run_runner_claude_opus48.sh.
"""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl_runner_opus48")
os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=4")

import numpy as np

import jax
import jax.numpy as jnp
from jax import random

import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
from numpyro.diagnostics import summary as nps_summary

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

numpyro.set_host_device_count(4)
jax.config.update("jax_enable_x64", True)

ROOT = Path(__file__).resolve().parents[1]
SETUP_DIR = ROOT / "artifacts" / "reports" / "sequential_vibe_modal_flight_20260602"
OUT_DIR = ROOT / "artifacts" / "reports" / "runner_claude_opus48_20260602"
FIG_DIR = OUT_DIR / "figures"

# ---- Fixed physical constants (from setup packet / fresh 2DOF Constants) ----
G0 = 9.80665
M1 = 1.0
M2 = 0.6
DOME_NOM_HZ = 110.0
TRAY_NOM_HZ = 75.0
K1_NOM = M1 * (2.0 * math.pi * DOME_NOM_HZ) ** 2
K2_NOM = M2 * (2.0 * math.pi * TRAY_NOM_HZ) ** 2

# Prior hyperparameters (from prior_model_summary in the setup packet)
SIGMA_LOG_STIFF = 0.18
LOW_K, HIGH_K = math.log(0.55), math.log(1.65)
ZETA1_CENTER, ZETA2_CENTER = 0.018, 0.026
SIGMA_LOG_ZETA = 0.35
LOW_Z, HIGH_Z = math.log(0.004), math.log(0.090)

# dB -> natural-log-PSD sigma
LN10 = math.log(10.0)
FLIGHT_F2F_DB = 3.0            # fixed/known, NOT learned
FORCING_MATERN_ELL = 0.08     # log-frequency length scale (Matern-3/2)
FLIGHT_MEAN_OFFSET_DB = -6.0

SEED = 20260602
N_WARMUP = 1000
N_SAMPLES = 1000
N_CHAINS = 4
SOFT_BETA = 45.0              # temperature for differentiable (soft) feature extraction
QOI_PRED_DRAWS = 4000


def db_to_ln_sigma(db: float) -> float:
    return db * LN10 / 10.0


# ----------------------------------------------------------------------------
# Forward model (JAX, fully vectorized over frequency; no python loops).
# 2DOF assembly matches fresh_2dof_statfem_fbs.mck:
#   k = [[k1+k2, -k2],[-k2, k2]], c = [[c1+c2,-c2],[-c2,c2]]
#   c1 = 2 z1 sqrt(k1 m1), c2 = 2 z2 sqrt(k2 m2)
#   accel/force H(w) = -w^2 * Z^{-1}, Z = k + i w c - w^2 m
# ----------------------------------------------------------------------------
def _zmatrix(freqs, k1, k2, z1, z2):
    w = 2.0 * jnp.pi * freqs
    c1 = 2.0 * z1 * jnp.sqrt(k1 * M1)
    c2 = 2.0 * z2 * jnp.sqrt(k2 * M2)
    Z11 = (k1 + k2) + 1j * w * (c1 + c2) - (w ** 2) * M1
    Z12 = -k2 - 1j * w * c2          # Z21 == Z12 (symmetric)
    Z22 = k2 + 1j * w * c2 - (w ** 2) * M2
    det = Z11 * Z22 - Z12 * Z12
    return w, Z11, Z12, Z22, det


def tray_transmissibility_absq(freqs, k2, z2):
    """|tray accel / base accel|^2 for standalone tray (m2 on mount k2,c2)."""
    w = 2.0 * jnp.pi * freqs
    c2 = 2.0 * z2 * jnp.sqrt(k2 * M2)
    mount = k2 + 1j * w * c2
    T = mount / (mount - M2 * (w ** 2))
    return jnp.abs(T) ** 2


def dome_only_recip_abs(freqs, k1, z1):
    """|F/a| reciprocal inertance [kg] for dome-only SDOF (notch near resonance)."""
    w = 2.0 * jnp.pi * freqs
    c1 = 2.0 * z1 * jnp.sqrt(k1 * M1)
    z = k1 + 1j * w * c1 - (w ** 2) * M1
    recip = -z / (w ** 2)            # 1 / (a/F)
    return jnp.abs(recip)


def coupled_recip_abs(freqs, k1, k2, z1, z2):
    """|F/a| reciprocal inertance for coupled primary (dof0) and tray (dof1)."""
    w, Z11, Z12, Z22, det = _zmatrix(freqs, k1, k2, z1, z2)
    # h_00 = -w^2 * Zinv00 = -w^2 * Z22/det ; ch2 = 1/h_00
    ch2 = det / (-(w ** 2) * Z22)
    # h_11 = -w^2 * Zinv11 = -w^2 * Z11/det ; ch3 = 1/h_11
    ch3 = det / (-(w ** 2) * Z11)
    return jnp.abs(ch2), jnp.abs(ch3)


def flight_transfer_absq_g(freqs, k1, k2, z1, z2):
    """|accel/force|^2 in (g/N)^2 for tray (h21) and interface/dome (h11)."""
    w, Z11, Z12, Z22, det = _zmatrix(freqs, k1, k2, z1, z2)
    h11 = -(w ** 2) * Z22 / det      # interface (dof0) accel per force on dof0 [m/s^2 / N]
    h21 = (w ** 2) * Z12 / det       # tray (dof1) accel per force on dof0
    return (jnp.abs(h21) / G0) ** 2, (jnp.abs(h11) / G0) ** 2


def soft_feature(eta, log_mag, kind, beta=SOFT_BETA):
    """Differentiable soft-argmax/min feature in log-frequency.

    Returns (soft_log_frequency, soft_log_amplitude). For a notch use kind='min'.
    Uses a softmax over beta*score (score = +/- log|y|). Documented approximation
    of the hard extremum so NUTS can differentiate the peak-feature likelihood.
    """
    s = log_mag if kind == "max" else -log_mag
    w = jax.nn.softmax(beta * s)
    soft_eta = jnp.sum(w * eta)
    soft_log_amp = jnp.sum(w * log_mag)   # softmax-weighted log amplitude
    return soft_eta, soft_log_amp


# ----------------------------------------------------------------------------
# Data container
# ----------------------------------------------------------------------------
def load_data() -> dict[str, Any]:
    d = json.loads((SETUP_DIR / "sequential_dataset.json").read_text())
    freqs = np.asarray(d["freqs_hz"], dtype=float)
    mfreqs = np.asarray(d["modal_freqs_hz"], dtype=float)
    smooth = np.asarray(d["smoothline_psd_g2_per_hz"], dtype=float)
    meanF = np.asarray(d["mean_flight_force_psd_n2_per_hz"], dtype=float)

    vibe_obs = np.asarray(d["tray_vibe_response"]["observed_psd_g2_per_hz"], dtype=float)

    def cmag(node):
        return np.abs(np.asarray(node["real"]) + 1j * np.asarray(node["imag"]))

    dome_modal_mag = cmag(d["modal_observations"]["dome_only"])
    iface_modal_mag = cmag(d["modal_observations"]["coupled_interface"])
    tray_modal_mag = cmag(d["modal_observations"]["coupled_tray"])

    flights = d["flight_summaries"]
    flight_build = np.asarray([f["build_id"] for f in flights], dtype=int)
    flight_tray = np.asarray([f["tray_3grms_g_observed"] for f in flights], dtype=float)
    flight_iface = np.asarray([f["interface_3grms_g_observed"] for f in flights], dtype=float)
    n_builds = len(d["build_samples"])

    return {
        "raw": d,
        "freqs": freqs,
        "mfreqs": mfreqs,
        "smooth": smooth,
        "meanF": meanF,
        "vibe_obs": vibe_obs,
        "dome_modal_mag": dome_modal_mag,
        "iface_modal_mag": iface_modal_mag,
        "tray_modal_mag": tray_modal_mag,
        "flight_build": flight_build,
        "flight_tray": flight_tray,
        "flight_iface": flight_iface,
        "n_builds": n_builds,
        "build_truth": d["build_samples"],
    }


# ----------------------------------------------------------------------------
# Fixed flight-to-flight QOI log-scatter from the 3 dB Matern-3/2 forcing GP.
# Computed by deterministic MC at NOMINAL-prior-center structure (allowed: it is
# the *known* fixed contribution). Sensor noise averages out over 260 bins.
# ----------------------------------------------------------------------------
def matern32_chol(freqs, ell, sigma_ln):
    eta = np.log(freqs)
    r = np.abs(np.subtract.outer(eta, eta)) / ell
    s = math.sqrt(3.0) * r
    corr = (1.0 + s) * np.exp(-s)
    cov = (sigma_ln ** 2) * corr + 1e-12 * np.eye(len(freqs))
    return np.linalg.cholesky(cov)


def compute_flight_qoi_f2f_sigma(data, n=4000, seed=777):
    """Return (sigma_tray, sigma_iface) of log(3GRMS) due to fixed 3 dB forcing."""
    freqs = data["freqs"]
    meanF = data["meanF"]
    # nominal-center structure (prior centers): truth is unknown to inference,
    # so use prior-center natural frequencies / damping for this fixed term.
    k1 = K1_NOM * 1.0
    k2 = K2_NOM * 1.0
    z1, z2 = ZETA1_CENTER, ZETA2_CENTER
    absh21, absh11 = flight_transfer_absq_g(jnp.asarray(freqs), k1, k2, z1, z2)
    absh21 = np.asarray(absh21)
    absh11 = np.asarray(absh11)
    L = matern32_chol(freqs, FORCING_MATERN_ELL, db_to_ln_sigma(FLIGHT_F2F_DB))
    rng = np.random.default_rng(seed)
    tq = np.empty(n)
    iq = np.empty(n)
    for i in range(n):
        lf = L @ rng.normal(size=len(freqs))
        F = meanF * np.exp(lf)
        tq[i] = 3.0 * math.sqrt(np.trapz(absh21 * F, freqs))
        iq[i] = 3.0 * math.sqrt(np.trapz(absh11 * F, freqs))
    return float(np.std(np.log(tq))), float(np.std(np.log(iq)))


# ----------------------------------------------------------------------------
# NumPyro models
# ----------------------------------------------------------------------------
def _structural_priors():
    u_k1 = numpyro.sample("u_k1", dist.TruncatedNormal(0.0, SIGMA_LOG_STIFF, low=LOW_K, high=HIGH_K))
    u_k2 = numpyro.sample("u_k2", dist.TruncatedNormal(0.0, SIGMA_LOG_STIFF, low=LOW_K, high=HIGH_K))
    u_z1 = numpyro.sample("u_z1", dist.TruncatedNormal(math.log(ZETA1_CENTER), SIGMA_LOG_ZETA, low=LOW_Z, high=HIGH_Z))
    u_z2 = numpyro.sample("u_z2", dist.TruncatedNormal(math.log(ZETA2_CENTER), SIGMA_LOG_ZETA, low=LOW_Z, high=HIGH_Z))
    k1 = K1_NOM * jnp.exp(u_k1)
    k2 = K2_NOM * jnp.exp(u_k2)
    z1 = jnp.exp(u_z1)
    z2 = jnp.exp(u_z2)
    numpyro.deterministic("dome_hz", jnp.sqrt(k1 / M1) / (2.0 * jnp.pi))
    numpyro.deterministic("tray_hz", jnp.sqrt(k2 / M2) / (2.0 * jnp.pi))
    numpyro.deterministic("zeta1", z1)
    numpyro.deterministic("zeta2", z2)
    return k1, k2, z1, z2


def _hier_build():
    sigma_build = numpyro.sample("sigma_build_ln", dist.HalfNormal(0.5))
    sigma_sensor = numpyro.sample("sigma_sensor_ln", dist.HalfNormal(0.3))
    numpyro.deterministic("sigma_build_db", sigma_build * 10.0 / LN10)
    numpyro.deterministic("sigma_sensor_db", sigma_sensor * 10.0 / LN10)
    return sigma_build, sigma_sensor


def _flight_qoi_terms(consts, k1, k2, z1, z2, dome_build, tray_build, sigma_build):
    freqs = consts["freqs_j"]
    meanF = consts["meanF_j"]
    absh21, absh11 = flight_transfer_absq_g(freqs, k1, k2, z1, z2)
    # deterministic structural QOI at mean force (3*sqrt of PSD integral)
    q_tray_struct = 3.0 * jnp.sqrt(jnp.trapezoid(absh21 * meanF, freqs))
    q_iface_struct = 3.0 * jnp.sqrt(jnp.trapezoid(absh11 * meanF, freqs))
    numpyro.deterministic("q_tray_struct_meanforce", q_tray_struct)
    numpyro.deterministic("q_iface_struct_meanforce", q_iface_struct)

    fb = consts["flight_build_j"]
    pred_tray = jnp.log(q_tray_struct) + 0.5 * tray_build[fb]
    pred_iface = jnp.log(q_iface_struct) + 0.5 * dome_build[fb]
    numpyro.sample(
        "obs_flight_tray",
        dist.Normal(pred_tray, consts["sig_qoi_tray"]),
        obs=consts["flight_tray_log_j"],
    )
    numpyro.sample(
        "obs_flight_iface",
        dist.Normal(pred_iface, consts["sig_qoi_iface"]),
        obs=consts["flight_iface_log_j"],
    )


def model_full(consts):
    """Whole-curve (full FRF/PSD) likelihood + flight QOI likelihood."""
    k1, k2, z1, z2 = _structural_priors()
    sigma_build, sigma_sensor = _hier_build()
    nb = consts["n_builds"]
    dome_raw = numpyro.sample("dome_build_raw", dist.Normal(0.0, 1.0).expand([nb]))
    tray_raw = numpyro.sample("tray_build_raw", dist.Normal(0.0, 1.0).expand([nb]))
    dome_build = numpyro.deterministic("dome_build", sigma_build * dome_raw)
    tray_build = numpyro.deterministic("tray_build", sigma_build * tray_raw)

    # Stage 2: tray vibe PSD (260 pts). log PSD = log|T|^2 + log smooth + tray_build[0] + sensor.
    log_T2 = jnp.log(tray_transmissibility_absq(consts["freqs_j"], k2, z2))
    pred_vibe = log_T2 + consts["log_smooth_j"] + tray_build[0]
    numpyro.sample("obs_vibe", dist.Normal(pred_vibe, sigma_sensor), obs=consts["vibe_log_j"])

    # Stage 3: dome-only modal log|F/a| (180). amplitude scale exp(0.5*(build0+sensor)).
    pred_dome = jnp.log(dome_only_recip_abs(consts["mfreqs_j"], k1, z1)) + 0.5 * dome_build[0]
    numpyro.sample("obs_dome_modal", dist.Normal(pred_dome, 0.5 * sigma_sensor), obs=consts["dome_modal_log_j"])

    # Stage 4: coupled interface & tray modal log|F/a|.
    ch2, ch3 = coupled_recip_abs(consts["mfreqs_j"], k1, k2, z1, z2)
    pred_iface = jnp.log(ch2) + 0.5 * dome_build[0]
    pred_tray = jnp.log(ch3) + 0.5 * tray_build[0]
    numpyro.sample("obs_iface_modal", dist.Normal(pred_iface, 0.5 * sigma_sensor), obs=consts["iface_modal_log_j"])
    numpyro.sample("obs_tray_modal", dist.Normal(pred_tray, 0.5 * sigma_sensor), obs=consts["tray_modal_log_j"])

    # Stages 5-6: flight QOIs.
    _flight_qoi_terms(consts, k1, k2, z1, z2, dome_build, tray_build, sigma_build)


def model_peak(consts):
    """Peak/notch-feature likelihood (lossy) + same flight QOI likelihood."""
    k1, k2, z1, z2 = _structural_priors()
    sigma_build, sigma_sensor = _hier_build()
    nb = consts["n_builds"]
    dome_raw = numpyro.sample("dome_build_raw", dist.Normal(0.0, 1.0).expand([nb]))
    tray_raw = numpyro.sample("tray_build_raw", dist.Normal(0.0, 1.0).expand([nb]))
    dome_build = numpyro.deterministic("dome_build", sigma_build * dome_raw)
    tray_build = numpyro.deterministic("tray_build", sigma_build * tray_raw)

    sf, sa = consts["feat_sigma_f"], consts["feat_sigma_a"]

    # Tray vibe PSD peak (max).
    log_vibe_pred = jnp.log(tray_transmissibility_absq(consts["freqs_j"], k2, z2)) + consts["log_smooth_j"] + tray_build[0]
    fe, ae = soft_feature(consts["log_freqs_j"], log_vibe_pred, "max")
    numpyro.sample("feat_vibe_f", dist.Normal(fe, sf), obs=consts["obs_vibe_feat"][0])
    numpyro.sample("feat_vibe_a", dist.Normal(ae, sa), obs=consts["obs_vibe_feat"][1])

    # Dome-only modal notch (min of |F/a|).
    log_dome_pred = jnp.log(dome_only_recip_abs(consts["mfreqs_j"], k1, z1)) + 0.5 * dome_build[0]
    fe, ae = soft_feature(consts["log_mfreqs_j"], log_dome_pred, "min")
    numpyro.sample("feat_dome_f", dist.Normal(fe, sf), obs=consts["obs_dome_feat"][0])
    numpyro.sample("feat_dome_a", dist.Normal(ae, sa), obs=consts["obs_dome_feat"][1])

    # Coupled interface & tray modal notches (min).
    ch2, ch3 = coupled_recip_abs(consts["mfreqs_j"], k1, k2, z1, z2)
    log_iface_pred = jnp.log(ch2) + 0.5 * dome_build[0]
    log_tray_pred = jnp.log(ch3) + 0.5 * tray_build[0]
    fe, ae = soft_feature(consts["log_mfreqs_j"], log_iface_pred, "min")
    numpyro.sample("feat_iface_f", dist.Normal(fe, sf), obs=consts["obs_iface_feat"][0])
    numpyro.sample("feat_iface_a", dist.Normal(ae, sa), obs=consts["obs_iface_feat"][1])
    fe, ae = soft_feature(consts["log_mfreqs_j"], log_tray_pred, "min")
    numpyro.sample("feat_tray_f", dist.Normal(fe, sf), obs=consts["obs_tray_feat"][0])
    numpyro.sample("feat_tray_a", dist.Normal(ae, sa), obs=consts["obs_tray_feat"][1])

    _flight_qoi_terms(consts, k1, k2, z1, z2, dome_build, tray_build, sigma_build)


# ----------------------------------------------------------------------------
# Hard feature extraction for OBSERVED data (numpy, offline; quadratic refine).
# ----------------------------------------------------------------------------
def hard_feature(freqs, values_log_mag, kind):
    eta = np.log(freqs)
    score = values_log_mag if kind == "max" else -values_log_mag
    idx = int(np.argmax(score))
    eta_star = float(eta[idx])
    log_amp = float(values_log_mag[idx])
    if 0 < idx < len(freqs) - 1:
        le = eta[idx - 1: idx + 2]
        ls = score[idx - 1: idx + 2]
        a, b, cc = np.polyfit(le, ls, 2)
        if abs(a) > 1e-12:
            cand = -b / (2.0 * a)
            if le[0] <= cand <= le[-1] and a < 0:
                eta_star = float(cand)
                refined = a * cand ** 2 + b * cand + cc
                log_amp = float(refined if kind == "max" else -refined)
    return eta_star, log_amp


# ----------------------------------------------------------------------------
# Build constants dict shared by models
# ----------------------------------------------------------------------------
def build_consts(data, sig_qoi_tray, sig_qoi_iface):
    freqs = data["freqs"]
    mfreqs = data["mfreqs"]
    consts = {
        "freqs_j": jnp.asarray(freqs),
        "mfreqs_j": jnp.asarray(mfreqs),
        "log_freqs_j": jnp.asarray(np.log(freqs)),
        "log_mfreqs_j": jnp.asarray(np.log(mfreqs)),
        "meanF_j": jnp.asarray(data["meanF"]),
        "log_smooth_j": jnp.asarray(np.log(data["smooth"])),
        "vibe_log_j": jnp.asarray(np.log(data["vibe_obs"])),
        "dome_modal_log_j": jnp.asarray(np.log(data["dome_modal_mag"])),
        "iface_modal_log_j": jnp.asarray(np.log(data["iface_modal_mag"])),
        "tray_modal_log_j": jnp.asarray(np.log(data["tray_modal_mag"])),
        "flight_build_j": jnp.asarray(data["flight_build"]),
        "flight_tray_log_j": jnp.asarray(np.log(data["flight_tray"])),
        "flight_iface_log_j": jnp.asarray(np.log(data["flight_iface"])),
        "n_builds": data["n_builds"],
        "sig_qoi_tray": sig_qoi_tray,
        "sig_qoi_iface": sig_qoi_iface,
    }
    # Feature noise assumptions (from fresh setup feature_likelihood_assumptions, FRF set)
    consts["feat_sigma_f"] = 0.06
    consts["feat_sigma_a"] = 0.30
    # Observed hard features (log-freq, log-amp)
    obs_vibe = hard_feature(freqs, np.log(data["vibe_obs"]), "max")
    obs_dome = hard_feature(mfreqs, np.log(data["dome_modal_mag"]), "min")
    obs_iface = hard_feature(mfreqs, np.log(data["iface_modal_mag"]), "min")
    obs_tray = hard_feature(mfreqs, np.log(data["tray_modal_mag"]), "min")
    consts["obs_vibe_feat"] = obs_vibe
    consts["obs_dome_feat"] = obs_dome
    consts["obs_iface_feat"] = obs_iface
    consts["obs_tray_feat"] = obs_tray
    return consts


# ----------------------------------------------------------------------------
# Run NUTS
# ----------------------------------------------------------------------------
def run_nuts(model, consts, label):
    kernel = NUTS(model, target_accept_prob=0.9, max_tree_depth=10)
    mcmc = MCMC(
        kernel,
        num_warmup=N_WARMUP,
        num_samples=N_SAMPLES,
        num_chains=N_CHAINS,
        chain_method="sequential",
        progress_bar=False,
    )
    key = random.PRNGKey(SEED if label == "full" else SEED + 1)
    t0 = time.time()
    mcmc.run(key, consts, extra_fields=("num_steps", "diverging", "accept_prob"))
    elapsed = time.time() - t0
    extra = mcmc.get_extra_fields()
    samples_bc = mcmc.get_samples(group_by_chain=True)
    samples = mcmc.get_samples(group_by_chain=False)

    # Diagnostics for scalar/vector params (skip very large build_raw arrays in summary table)
    diag_vars = ["dome_hz", "tray_hz", "zeta1", "zeta2",
                 "sigma_build_ln", "sigma_sensor_ln",
                 "sigma_build_db", "sigma_sensor_db",
                 "q_tray_struct_meanforce", "q_iface_struct_meanforce"]
    sub = {k: np.asarray(samples_bc[k]) for k in diag_vars}
    summ = nps_summary(sub, group_by_chain=True)

    num_steps = np.asarray(extra["num_steps"])
    diverging = np.asarray(extra["diverging"])
    accept = np.asarray(extra["accept_prob"])
    try:
        step_size = float(np.asarray(mcmc.last_state.adapt_state.step_size).reshape(-1)[0])
    except Exception:
        step_size = float("nan")
    # implied tree depth from leapfrog steps (NUTS: steps ~ 2^depth - 1)
    tree_depth = np.log2(num_steps + 1.0)

    diagnostics = {
        "label": label,
        "sampler": "NUTS (numpyro)",
        "num_chains": N_CHAINS,
        "num_warmup": N_WARMUP,
        "num_samples_per_chain": N_SAMPLES,
        "total_post_warmup_draws": int(N_CHAINS * N_SAMPLES),
        "elapsed_seconds": round(elapsed, 2),
        "divergences_total": int(diverging.sum()),
        "divergence_fraction": float(diverging.mean()),
        "final_step_size": step_size,
        "mean_accept_prob": float(accept.mean()),
        "max_leapfrog_steps": int(num_steps.max()),
        "mean_leapfrog_steps": float(num_steps.mean()),
        "max_tree_depth_setting": 10,
        "max_observed_tree_depth": float(tree_depth.max()),
        "mean_observed_tree_depth": float(tree_depth.mean()),
        "param_table": {
            k: {
                "mean": float(summ[k]["mean"]),
                "std": float(summ[k]["std"]),
                "5%": float(summ[k]["5.0%"]),
                "95%": float(summ[k]["95.0%"]),
                "n_eff": float(summ[k]["n_eff"]),
                "r_hat": float(summ[k]["r_hat"]),
            }
            for k in diag_vars
        },
        "min_n_eff": float(min(summ[k]["n_eff"] for k in diag_vars)),
        "max_r_hat": float(max(summ[k]["r_hat"] for k in diag_vars)),
    }
    return samples, diagnostics


# ----------------------------------------------------------------------------
# Posterior QOI predictive
# ----------------------------------------------------------------------------
def qoi_predictive(samples, sig_qoi_tray, sig_qoi_iface, seed=2024):
    """Future-flight / future-build tray & interface 3GRMS predictive intervals."""
    rng = np.random.default_rng(seed)
    q_tray = np.asarray(samples["q_tray_struct_meanforce"])
    q_iface = np.asarray(samples["q_iface_struct_meanforce"])
    sb = np.asarray(samples["sigma_build_ln"])
    n = len(q_tray)
    idx = rng.integers(0, n, size=QOI_PRED_DRAWS)
    # future build effect ~ N(0, sigma_build); future flight forcing ~ N(0, sig_qoi)
    new_build_t = rng.normal(0.0, sb[idx])
    new_build_i = rng.normal(0.0, sb[idx])
    f2f_t = rng.normal(0.0, sig_qoi_tray, QOI_PRED_DRAWS)
    f2f_i = rng.normal(0.0, sig_qoi_iface, QOI_PRED_DRAWS)
    tray_pred = q_tray[idx] * np.exp(0.5 * new_build_t + f2f_t)
    iface_pred = q_iface[idx] * np.exp(0.5 * new_build_i + f2f_i)
    # structural-only epistemic (no build/f2f): posterior of structural QOI
    def ci(x):
        return {
            "median": float(np.median(x)),
            "q005": float(np.quantile(x, 0.005)),
            "q025": float(np.quantile(x, 0.025)),
            "q975": float(np.quantile(x, 0.975)),
            "q995": float(np.quantile(x, 0.995)),
        }
    return {
        "tray_3grms_structural_posterior": ci(q_tray),
        "iface_3grms_structural_posterior": ci(q_iface),
        "tray_3grms_future_flight_predictive": ci(tray_pred),
        "iface_3grms_future_flight_predictive": ci(iface_pred),
    }, tray_pred, iface_pred, q_tray


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------
def fig_truth_vs_observed(data):
    freqs, mfreqs = data["freqs"], data["mfreqs"]
    truth = _truth_curves(data)
    fig, ax = plt.subplots(2, 2, figsize=(13.5, 9.0))
    ax[0, 0].loglog(freqs, data["smooth"], label="base input smoothline", lw=2.0)
    ax[0, 0].loglog(freqs, truth["vibe_clean"], label="tray clean response", lw=1.8)
    ax[0, 0].loglog(freqs, data["vibe_obs"], ".", ms=3, alpha=0.5, label="tray observed")
    ax[0, 0].set_title("Tray vibe PSD (full curve)")
    ax[0, 0].set_xlabel("frequency [Hz]"); ax[0, 0].set_ylabel("PSD [g^2/Hz]")
    ax[0, 0].grid(True, which="both", alpha=0.25); ax[0, 0].legend(fontsize=8)

    ax[0, 1].loglog(mfreqs, truth["dome_clean"], label="dome clean |F/a|", lw=1.8)
    ax[0, 1].loglog(mfreqs, data["dome_modal_mag"], ".", ms=3, alpha=0.5, label="dome observed")
    ax[0, 1].set_title("Dome-only modal |F/a| (notch at resonance)")
    ax[0, 1].set_xlabel("frequency [Hz]"); ax[0, 1].set_ylabel("|F/a| [kg]")
    ax[0, 1].grid(True, which="both", alpha=0.25); ax[0, 1].legend(fontsize=8)

    ax[1, 0].loglog(mfreqs, data["iface_modal_mag"], ".", ms=3, alpha=0.5, label="coupled interface obs")
    ax[1, 0].loglog(mfreqs, data["tray_modal_mag"], ".", ms=3, alpha=0.5, label="coupled tray obs")
    ax[1, 0].loglog(mfreqs, truth["iface_clean"], lw=1.5, label="iface clean")
    ax[1, 0].loglog(mfreqs, truth["tray_clean"], lw=1.5, label="tray clean")
    ax[1, 0].set_title("Coupled modal |F/a| channels")
    ax[1, 0].set_xlabel("frequency [Hz]"); ax[1, 0].set_ylabel("|F/a| [kg]")
    ax[1, 0].grid(True, which="both", alpha=0.25); ax[1, 0].legend(fontsize=8)

    fids = data["flight_build"]
    ax[1, 1].plot(fids, data["flight_tray"], "o-", label="flight tray 3*GRMS obs")
    ax[1, 1].plot(fids, data["flight_iface"], "s-", label="flight iface 3*GRMS obs")
    ax[1, 1].set_title("Flight QOI observations (scalar per flight)")
    ax[1, 1].set_xlabel("flight / build id"); ax[1, 1].set_ylabel("3*GRMS [g]")
    ax[1, 1].grid(True, alpha=0.25); ax[1, 1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "01_truth_vs_observed.png", dpi=150)
    plt.close(fig)


def _truth_curves(data):
    freqs, mfreqs = jnp.asarray(data["freqs"]), jnp.asarray(data["mfreqs"])
    k1 = K1_NOM * (1 - 0.150) ** 2
    k2 = K2_NOM * (1 + 0.150) ** 2
    z1 = (1 + 0.250) * 0.018
    z2 = (1 - 0.250) * 0.026
    vibe = np.asarray(tray_transmissibility_absq(freqs, k2, z2)) * data["smooth"]
    dome = np.asarray(dome_only_recip_abs(mfreqs, k1, z1))
    ch2, ch3 = coupled_recip_abs(mfreqs, k1, k2, z1, z2)
    return {
        "vibe_clean": vibe,
        "dome_clean": dome,
        "iface_clean": np.asarray(ch2),
        "tray_clean": np.asarray(ch3),
        "truth": {"dome_hz": float(np.sqrt(k1 / M1) / (2 * np.pi)),
                  "tray_hz": float(np.sqrt(k2 / M2) / (2 * np.pi)),
                  "zeta1": z1, "zeta2": z2},
    }


def fig_posterior_compare(s_full, s_peak, data):
    truth = _truth_curves(data)["truth"]
    names = [("dome_hz", "dome fn [Hz]", truth["dome_hz"]),
             ("tray_hz", "tray fn [Hz]", truth["tray_hz"]),
             ("zeta1", "dome zeta", truth["zeta1"]),
             ("zeta2", "tray zeta", truth["zeta2"]),
             ("sigma_build_db", "sigma_build [dB]", 1.5),
             ("sigma_sensor_db", "sigma_sensor [dB]", 0.75)]
    fig, axes = plt.subplots(2, 3, figsize=(14.0, 8.0))
    for ax, (key, lab, tv) in zip(axes.ravel(), names):
        a = np.asarray(s_full[key]); b = np.asarray(s_peak[key])
        ax.hist(a, bins=40, density=True, alpha=0.55, label="full FRF/PSD")
        ax.hist(b, bins=40, density=True, alpha=0.55, label="peak feature")
        ax.axvline(tv, color="k", ls="--", lw=1.5, label="generating truth")
        ax.set_title(lab); ax.grid(True, alpha=0.25); ax.legend(fontsize=8)
    fig.suptitle("Posterior comparison: full-curve vs peak-feature likelihood", fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(FIG_DIR / "02_posterior_full_vs_peak.png", dpi=150)
    plt.close(fig)


def fig_input_spectra(data, force_bands):
    freqs = data["freqs"]
    fig, ax = plt.subplots(figsize=(11.0, 6.0))
    ax.loglog(freqs, data["meanF"], color="#1f77b4", lw=2.2, label="flight mean force PSD (known)")
    ax.fill_between(freqs, force_bands["q025"], force_bands["q975"], alpha=0.28, color="#2ca02c",
                    label="95% input force band (fixed 3 dB f2f)")
    ax.fill_between(freqs, force_bands["q005"], force_bands["q995"], alpha=0.16, color="#f1c40f",
                    label="99% input force band (fixed 3 dB f2f)")
    ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("force PSD [N^2/Hz]")
    ax.set_title("95% / 99% flight input force spectra (Matern-3/2, fixed 3 dB, not learned)")
    ax.grid(True, which="both", alpha=0.25); ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "03_input_spectra_95_99.png", dpi=150)
    plt.close(fig)


def fig_qoi_intervals(qoi_full, qoi_peak, tray_pred_full, q_tray_full, prior_ci, data):
    fig, ax = plt.subplots(1, 2, figsize=(13.5, 5.6))
    # left: histogram of future-flight tray predictive (full) vs structural posterior
    ax[0].hist(tray_pred_full, bins=60, density=True, alpha=0.55, label="future-flight predictive (full)")
    ax[0].hist(q_tray_full, bins=60, density=True, alpha=0.55, label="structural posterior (mean force)")
    for q, c, l in [(prior_ci["q025"], "#888", "setup prior 95%"), (prior_ci["q975"], "#888", None)]:
        ax[0].axvline(q, color=c, ls=":", lw=1.4, label=l)
    ax[0].axhline(0, color="k", lw=0)
    obs_mean = float(np.mean(data["flight_tray"]))
    ax[0].axvline(obs_mean, color="r", ls="--", lw=1.4, label="mean observed flight tray 3*GRMS")
    ax[0].set_title("Tray 3*GRMS QOI (full likelihood)")
    ax[0].set_xlabel("tray 3*GRMS [g]"); ax[0].grid(True, alpha=0.25); ax[0].legend(fontsize=8)

    # right: interval comparison full vs peak
    labels = ["tray struct\n(full)", "tray struct\n(peak)", "tray pred\n(full)", "tray pred\n(peak)"]
    keys = [("tray_3grms_structural_posterior", qoi_full),
            ("tray_3grms_structural_posterior", qoi_peak),
            ("tray_3grms_future_flight_predictive", qoi_full),
            ("tray_3grms_future_flight_predictive", qoi_peak)]
    for i, (k, qd) in enumerate(keys):
        d = qd[k]
        ax[1].plot([i, i], [d["q025"], d["q975"]], lw=6, alpha=0.5, color="#1f77b4")
        ax[1].plot([i, i], [d["q005"], d["q995"]], lw=2, color="#d62728")
        ax[1].plot(i, d["median"], "o", color="k")
    ax[1].set_xticks(range(4)); ax[1].set_xticklabels(labels, fontsize=8)
    ax[1].set_ylabel("tray 3*GRMS [g]")
    ax[1].set_title("95% (blue) / 99% (red) QOI intervals")
    ax[1].grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "04_qoi_intervals.png", dpi=150)
    plt.close(fig)


def fig_build_recovery(s_full, data):
    nb = data["n_builds"]
    dome_post = np.asarray(s_full["dome_build"])
    tray_post = np.asarray(s_full["tray_build"])
    truth = data["build_truth"]
    fig, ax = plt.subplots(1, 2, figsize=(13.0, 5.2))
    x = np.arange(nb)
    for arr, tkey, title, axi in [(dome_post, "dome_log_psd_effect", "dome build effect", ax[0]),
                                  (tray_post, "tray_log_psd_effect", "tray build effect", ax[1])]:
        med = np.median(arr, axis=0)
        lo = np.quantile(arr, 0.025, axis=0); hi = np.quantile(arr, 0.975, axis=0)
        axi.errorbar(x, med, yerr=[med - lo, hi - med], fmt="o", capsize=3, label="posterior 95%")
        axi.plot(x, [truth[b][tkey] for b in range(nb)], "rx", ms=9, label="generating truth")
        axi.axhline(0, color="k", lw=0.8)
        axi.set_title(f"{title} (log PSD)"); axi.set_xlabel("build id")
        axi.set_ylabel("log-PSD effect"); axi.grid(True, alpha=0.25); axi.legend(fontsize=8)
    fig.suptitle("Build-to-build effect recovery (full likelihood)")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(FIG_DIR / "05_build_effect_recovery.png", dpi=150)
    plt.close(fig)


def fig_feature_diagnostic(consts, data):
    """Show where the peak/notch features sit on the observed curves."""
    freqs, mfreqs = data["freqs"], data["mfreqs"]
    fig, ax = plt.subplots(2, 2, figsize=(13.0, 8.4))
    panels = [
        (ax[0, 0], freqs, data["vibe_obs"], consts["obs_vibe_feat"], "Tray vibe PSD peak", "PSD [g^2/Hz]"),
        (ax[0, 1], mfreqs, data["dome_modal_mag"], consts["obs_dome_feat"], "Dome modal notch", "|F/a| [kg]"),
        (ax[1, 0], mfreqs, data["iface_modal_mag"], consts["obs_iface_feat"], "Coupled interface notch", "|F/a| [kg]"),
        (ax[1, 1], mfreqs, data["tray_modal_mag"], consts["obs_tray_feat"], "Coupled tray notch", "|F/a| [kg]"),
    ]
    for axi, fr, val, feat, title, ylab in panels:
        axi.loglog(fr, val, ".", ms=3, alpha=0.5)
        axi.axvline(math.exp(feat[0]), color="r", ls="--", lw=1.5,
                    label=f"feature f={math.exp(feat[0]):.1f} Hz")
        axi.set_title(title); axi.set_xlabel("frequency [Hz]"); axi.set_ylabel(ylab)
        axi.grid(True, which="both", alpha=0.25); axi.legend(fontsize=8)
    fig.suptitle("Peak/notch feature map used by the lossy feature likelihood")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(FIG_DIR / "06_feature_map.png", dpi=150)
    plt.close(fig)


# ----------------------------------------------------------------------------
def input_force_bands(data):
    sig = db_to_ln_sigma(FLIGHT_F2F_DB)
    m = data["meanF"]
    return {
        "q005": (m * np.exp(-2.5758 * sig)).tolist(),
        "q025": (m * np.exp(-1.96 * sig)).tolist(),
        "q975": (m * np.exp(1.96 * sig)).tolist(),
        "q995": (m * np.exp(2.5758 * sig)).tolist(),
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    data = load_data()

    sig_qoi_tray, sig_qoi_iface = compute_flight_qoi_f2f_sigma(data)
    consts = build_consts(data, sig_qoi_tray, sig_qoi_iface)

    print(f"[info] fixed flight-to-flight QOI log-sigma: tray={sig_qoi_tray:.4f} iface={sig_qoi_iface:.4f}")

    print("[info] running NUTS (full FRF/PSD likelihood)...")
    s_full, diag_full = run_nuts(model_full, consts, "full")
    print(f"[info] full: divergences={diag_full['divergences_total']} "
          f"max_rhat={diag_full['max_r_hat']:.3f} min_ess={diag_full['min_n_eff']:.0f}")

    print("[info] running NUTS (peak-feature likelihood)...")
    s_peak, diag_peak = run_nuts(model_peak, consts, "peak")
    print(f"[info] peak: divergences={diag_peak['divergences_total']} "
          f"max_rhat={diag_peak['max_r_hat']:.3f} min_ess={diag_peak['min_n_eff']:.0f}")

    qoi_full, tray_pred_full, iface_pred_full, q_tray_full = qoi_predictive(s_full, sig_qoi_tray, sig_qoi_iface)
    qoi_peak, _, _, _ = qoi_predictive(s_peak, sig_qoi_tray, sig_qoi_iface)

    force_bands = input_force_bands(data)
    prior_ci = data["raw"]["qoi_prior_predictive_ci_3grms_g"]

    # Figures
    fig_truth_vs_observed(data)
    fig_posterior_compare(s_full, s_peak, data)
    fig_input_spectra(data, force_bands)
    fig_qoi_intervals(qoi_full, qoi_peak, tray_pred_full, q_tray_full, prior_ci, data)
    fig_build_recovery(s_full, data)
    fig_feature_diagnostic(consts, data)

    # interval-width ratios (peak/full) for tray QOI
    def width(d):
        return d["q975"] - d["q025"]
    width_ratio = {
        "tray_structural_95_peak_over_full": width(qoi_peak["tray_3grms_structural_posterior"]) /
        max(width(qoi_full["tray_3grms_structural_posterior"]), 1e-12),
        "tray_predictive_95_peak_over_full": width(qoi_peak["tray_3grms_future_flight_predictive"]) /
        max(width(qoi_full["tray_3grms_future_flight_predictive"]), 1e-12),
    }

    truth = _truth_curves(data)["truth"]
    results = {
        "fixed_flight_to_flight_qoi_log_sigma": {"tray": sig_qoi_tray, "iface": sig_qoi_iface},
        "generating_truth_reference": truth,
        "posterior_full": _posterior_table(s_full, truth),
        "posterior_peak": _posterior_table(s_peak, truth),
        "qoi_full": qoi_full,
        "qoi_peak": qoi_peak,
        "qoi_interval_width_ratio_peak_over_full": width_ratio,
        "setup_prior_predictive_tray_3grms": prior_ci,
        "observed_flight_tray_3grms": {
            "mean": float(np.mean(data["flight_tray"])),
            "min": float(np.min(data["flight_tray"])),
            "max": float(np.max(data["flight_tray"])),
        },
        "feature_likelihood_assumptions": {
            "frf_log_frequency_sigma": consts["feat_sigma_f"],
            "frf_log_amplitude_sigma": consts["feat_sigma_a"],
            "soft_argmax_beta": SOFT_BETA,
            "note": "Soft (temperature) argmax used for differentiable peak features in NUTS; observed features use hard quadratic-refined extremum.",
        },
    }
    (OUT_DIR / "results.json").write_text(json.dumps(results, indent=2))
    (OUT_DIR / "nuts_diagnostics.json").write_text(
        json.dumps({"full": diag_full, "peak": diag_peak}, indent=2)
    )

    # Save thinned posterior samples for traceability
    np.savez_compressed(
        OUT_DIR / "posterior_samples.npz",
        full_dome_hz=np.asarray(s_full["dome_hz"]),
        full_tray_hz=np.asarray(s_full["tray_hz"]),
        full_zeta1=np.asarray(s_full["zeta1"]),
        full_zeta2=np.asarray(s_full["zeta2"]),
        full_sigma_build_db=np.asarray(s_full["sigma_build_db"]),
        full_sigma_sensor_db=np.asarray(s_full["sigma_sensor_db"]),
        full_q_tray=np.asarray(s_full["q_tray_struct_meanforce"]),
        peak_dome_hz=np.asarray(s_peak["dome_hz"]),
        peak_tray_hz=np.asarray(s_peak["tray_hz"]),
        peak_q_tray=np.asarray(s_peak["q_tray_struct_meanforce"]),
    )

    print("[info] wrote results.json, nuts_diagnostics.json, posterior_samples.npz, 6 figures.")
    return 0


def _posterior_table(s, truth):
    def stat(key):
        a = np.asarray(s[key])
        return {"mean": float(a.mean()), "std": float(a.std()),
                "q025": float(np.quantile(a, 0.025)), "q975": float(np.quantile(a, 0.975))}
    return {
        "dome_hz": {**stat("dome_hz"), "truth": truth["dome_hz"]},
        "tray_hz": {**stat("tray_hz"), "truth": truth["tray_hz"]},
        "zeta1": {**stat("zeta1"), "truth": truth["zeta1"]},
        "zeta2": {**stat("zeta2"), "truth": truth["zeta2"]},
        "sigma_build_db": {**stat("sigma_build_db"), "truth": 1.5},
        "sigma_sensor_db": {**stat("sigma_sensor_db"), "truth": 0.75},
    }


if __name__ == "__main__":
    raise SystemExit(main())
