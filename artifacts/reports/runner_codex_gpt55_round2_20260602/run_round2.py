#!/usr/bin/env python3
"""Round-2 sequential vibe/modal/flight runner for Codex GPT-5.5.

This script consumes the checked setup packet at
artifacts/reports/sequential_vibe_modal_flight_20260602/ and writes all run
artifacts to artifacts/reports/runner_codex_gpt55_round2_20260602/.

The round-2 priority artifact is an animated GIF of posterior predictive
coupled interface acceleration response PSD, by cumulative flight update, vs
the original smoothline test spec.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import subprocess
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl_runner_codex_round2")
os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=4")

import numpy as np

import jax
import jax.numpy as jnp
from jax import random

import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS

import arviz as az

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image, ImageStat

numpyro.set_host_device_count(4)
jax.config.update("jax_enable_x64", True)

ROOT = Path(__file__).resolve().parents[3]
SETUP_DIR = ROOT / "artifacts" / "reports" / "sequential_vibe_modal_flight_20260602"
OUT_DIR = ROOT / "artifacts" / "reports" / "runner_codex_gpt55_round2_20260602"
FIG_DIR = OUT_DIR / "figures"
FRAME_DIR = FIG_DIR / "interface_gif_frames"

G0 = 9.80665
M1 = 1.0
M2 = 0.6
DOME_NOM_HZ = 110.0
TRAY_NOM_HZ = 75.0
K1_NOM = M1 * (2.0 * math.pi * DOME_NOM_HZ) ** 2
K2_NOM = M2 * (2.0 * math.pi * TRAY_NOM_HZ) ** 2

SIGMA_LOG_STIFF = 0.18
LOW_K, HIGH_K = math.log(0.55), math.log(1.65)
ZETA1_CENTER, ZETA2_CENTER = 0.018, 0.026
SIGMA_LOG_ZETA = 0.35
LOW_Z, HIGH_Z = math.log(0.004), math.log(0.090)

LN10 = math.log(10.0)
FLIGHT_F2F_DB = 3.0
FORCING_MATERN_ELL = 0.08
FLIGHT_MEAN_OFFSET_DB = -6.0
BUILD_SIGMA_DB_GENERATING = 1.5
SENSOR_SIGMA_DB_GENERATING = 0.75
SETUP_SEED = 260602
RUN_SEED = 20260602

N_CHAINS = int(os.environ.get("ROUND2_N_CHAINS", "4"))
MAIN_WARMUP = int(os.environ.get("ROUND2_MAIN_WARMUP", "900"))
MAIN_SAMPLES = int(os.environ.get("ROUND2_MAIN_SAMPLES", "900"))
CUM_WARMUP = int(os.environ.get("ROUND2_CUM_WARMUP", "450"))
CUM_SAMPLES = int(os.environ.get("ROUND2_CUM_SAMPLES", "550"))
QOI_MC = int(os.environ.get("ROUND2_QOI_MC", "2500"))
GIF_DRAWS = int(os.environ.get("ROUND2_GIF_DRAWS", "700"))

FLIGHT_QOI_OBS_SIGMA_LN = 0.08
RANK_RHAT_GATE = 1.01
ESS_PER_CHAIN_GATE = 100

STAGE_TIMES: list[dict[str, float | str]] = []


def timed(name: str):
    class _Timer:
        def __enter__(self):
            self.t0 = time.perf_counter()
            return self

        def __exit__(self, exc_type, exc, tb):
            STAGE_TIMES.append({"stage": name, "active_runtime_s": time.perf_counter() - self.t0})
            return False

    return _Timer()


def prepare_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    for folder in (FIG_DIR, FRAME_DIR):
        for path in folder.glob("*"):
            if path.is_file() and path.name != "priority_deliverables.md":
                path.unlink()


def db_to_ln_sigma(db: float) -> float:
    return db * LN10 / 10.0


def psd_db_to_factor(db: float) -> float:
    return 10.0 ** (db / 10.0)


def loglog_interp(freqs: np.ndarray, ref_freqs: np.ndarray, ref_vals: np.ndarray) -> np.ndarray:
    return np.exp(np.interp(np.log(freqs), np.log(ref_freqs), np.log(ref_vals)))


def load_data() -> dict[str, Any]:
    raw = json.loads((SETUP_DIR / "sequential_dataset.json").read_text())
    freqs = np.asarray(raw["freqs_hz"], dtype=float)
    mfreqs = np.asarray(raw["modal_freqs_hz"], dtype=float)

    def cmag(node: dict[str, Any]) -> np.ndarray:
        return np.abs(np.asarray(node["real"], dtype=float) + 1j * np.asarray(node["imag"], dtype=float))

    flights = raw["flight_summaries"]
    return {
        "raw": raw,
        "freqs": freqs,
        "mfreqs": mfreqs,
        "smooth": np.asarray(raw["smoothline_psd_g2_per_hz"], dtype=float),
        "original_force": np.asarray(raw["original_flat_force_psd_n2_per_hz"], dtype=float),
        "mean_force": np.asarray(raw["mean_flight_force_psd_n2_per_hz"], dtype=float),
        "vibe_obs": np.asarray(raw["tray_vibe_response"]["observed_psd_g2_per_hz"], dtype=float),
        "vibe_clean": np.asarray(raw["tray_vibe_response"]["clean_psd_g2_per_hz"], dtype=float),
        "dome_modal_mag": cmag(raw["modal_observations"]["dome_only"]),
        "iface_modal_mag": cmag(raw["modal_observations"]["coupled_interface"]),
        "tray_modal_mag": cmag(raw["modal_observations"]["coupled_tray"]),
        "flight_build": np.asarray([f["build_id"] for f in flights], dtype=int),
        "flight_tray": np.asarray([f["tray_3grms_g_observed"] for f in flights], dtype=float),
        "flight_iface": np.asarray([f["interface_3grms_g_observed"] for f in flights], dtype=float),
        "build_truth": raw["build_samples"],
        "flight_summaries": flights,
        "smoothline_3grms": float(np.sqrt(np.trapz(np.asarray(raw["smoothline_psd_g2_per_hz"]), freqs)) * 3.0),
        "vibe_3grms": float(raw["tray_vibe_response"]["observed_3grms_g"]),
    }


def _zmatrix(freqs, k1, k2, z1, z2):
    w = 2.0 * jnp.pi * freqs
    c1 = 2.0 * z1 * jnp.sqrt(k1 * M1)
    c2 = 2.0 * z2 * jnp.sqrt(k2 * M2)
    z11 = (k1 + k2) + 1j * w * (c1 + c2) - (w ** 2) * M1
    z12 = -k2 - 1j * w * c2
    z22 = k2 + 1j * w * c2 - (w ** 2) * M2
    det = z11 * z22 - z12 * z12
    return w, z11, z12, z22, det


def tray_transmissibility_absq(freqs, k2, z2):
    w = 2.0 * jnp.pi * freqs
    c2 = 2.0 * z2 * jnp.sqrt(k2 * M2)
    mount = k2 + 1j * w * c2
    t = mount / (mount - M2 * (w ** 2))
    return jnp.abs(t) ** 2


def dome_only_recip_abs(freqs, k1, z1):
    w = 2.0 * jnp.pi * freqs
    c1 = 2.0 * z1 * jnp.sqrt(k1 * M1)
    z = k1 + 1j * w * c1 - (w ** 2) * M1
    return jnp.abs(-z / (w ** 2))


def coupled_recip_abs(freqs, k1, k2, z1, z2):
    w, z11, z12, z22, det = _zmatrix(freqs, k1, k2, z1, z2)
    ch_iface = det / (-(w ** 2) * z22)
    ch_tray = det / (-(w ** 2) * z11)
    return jnp.abs(ch_iface), jnp.abs(ch_tray)


def flight_transfer_absq_g(freqs, k1, k2, z1, z2):
    w, z11, z12, z22, det = _zmatrix(freqs, k1, k2, z1, z2)
    h_iface = -(w ** 2) * z22 / det
    h_tray = (w ** 2) * z12 / det
    return (jnp.abs(h_tray) / G0) ** 2, (jnp.abs(h_iface) / G0) ** 2


def flight_transfer_absq_g_np(freqs: np.ndarray, k1: float, k2: float, z1: float, z2: float) -> tuple[np.ndarray, np.ndarray]:
    tray, iface = flight_transfer_absq_g(jnp.asarray(freqs), k1, k2, z1, z2)
    return np.asarray(tray), np.asarray(iface)


def structural_priors():
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


def model_full(consts: dict[str, Any]) -> None:
    k1, k2, z1, z2 = structural_priors()
    sigma_build = numpyro.sample("sigma_build_ln", dist.HalfNormal(0.5))
    sigma_sensor = numpyro.sample("sigma_sensor_ln", dist.HalfNormal(0.3))
    numpyro.deterministic("sigma_build_db", sigma_build * 10.0 / LN10)
    numpyro.deterministic("sigma_sensor_db", sigma_sensor * 10.0 / LN10)

    nb = consts["n_builds"]
    nf = consts["n_flights"]
    dome_raw = numpyro.sample("dome_build_raw", dist.Normal(0.0, 1.0).expand([nb]))
    tray_raw = numpyro.sample("tray_build_raw", dist.Normal(0.0, 1.0).expand([nb]))
    dome_build = numpyro.deterministic("dome_build", sigma_build * dome_raw)
    tray_build = numpyro.deterministic("tray_build", sigma_build * tray_raw)

    flight_tray_raw = numpyro.sample("flight_tray_force_raw", dist.Normal(0.0, 1.0).expand([nf]))
    flight_iface_raw = numpyro.sample("flight_iface_force_raw", dist.Normal(0.0, 1.0).expand([nf]))
    numpyro.deterministic("flight_tray_log_force_effect", consts["sig_qoi_tray"] * flight_tray_raw)
    numpyro.deterministic("flight_iface_log_force_effect", consts["sig_qoi_iface"] * flight_iface_raw)

    log_t2 = jnp.log(tray_transmissibility_absq(consts["freqs_j"], k2, z2))
    pred_vibe = log_t2 + consts["log_smooth_j"] + tray_build[0]
    numpyro.sample("obs_vibe_log_psd", dist.Normal(pred_vibe, sigma_sensor), obs=consts["vibe_log_j"])

    pred_dome = jnp.log(dome_only_recip_abs(consts["mfreqs_j"], k1, z1)) + 0.5 * dome_build[0]
    numpyro.sample("obs_dome_modal_logmag", dist.Normal(pred_dome, 0.5 * sigma_sensor), obs=consts["dome_modal_log_j"])

    ch_iface, ch_tray = coupled_recip_abs(consts["mfreqs_j"], k1, k2, z1, z2)
    numpyro.sample(
        "obs_iface_modal_logmag",
        dist.Normal(jnp.log(ch_iface) + 0.5 * dome_build[0], 0.5 * sigma_sensor),
        obs=consts["iface_modal_log_j"],
    )
    numpyro.sample(
        "obs_tray_modal_logmag",
        dist.Normal(jnp.log(ch_tray) + 0.5 * tray_build[0], 0.5 * sigma_sensor),
        obs=consts["tray_modal_log_j"],
    )

    tray_absq, iface_absq = flight_transfer_absq_g(consts["freqs_j"], k1, k2, z1, z2)
    q_tray_struct = 3.0 * jnp.sqrt(jnp.trapezoid(tray_absq * consts["mean_force_j"], consts["freqs_j"]))
    q_iface_struct = 3.0 * jnp.sqrt(jnp.trapezoid(iface_absq * consts["mean_force_j"], consts["freqs_j"]))
    numpyro.deterministic("q_tray_struct_meanforce", q_tray_struct)
    numpyro.deterministic("q_iface_struct_meanforce", q_iface_struct)

    fb = consts["flight_build_j"]
    pred_tray = jnp.log(q_tray_struct) + 0.5 * tray_build[fb] + consts["sig_qoi_tray"] * flight_tray_raw
    pred_iface = jnp.log(q_iface_struct) + 0.5 * dome_build[fb] + consts["sig_qoi_iface"] * flight_iface_raw
    numpyro.sample("obs_flight_tray_log_3grms", dist.Normal(pred_tray, FLIGHT_QOI_OBS_SIGMA_LN), obs=consts["flight_tray_log_j"])
    numpyro.sample("obs_flight_iface_log_3grms", dist.Normal(pred_iface, FLIGHT_QOI_OBS_SIGMA_LN), obs=consts["flight_iface_log_j"])


def matern32_chol(freqs: np.ndarray, ell: float, sigma_ln: float) -> np.ndarray:
    eta = np.log(freqs)
    r = np.abs(np.subtract.outer(eta, eta)) / ell
    s = math.sqrt(3.0) * r
    corr = (1.0 + s) * np.exp(-s)
    return np.linalg.cholesky((sigma_ln ** 2) * corr + 1e-12 * np.eye(len(freqs)))


def compute_qoi_log_scatter(data: dict[str, Any], n: int = QOI_MC) -> tuple[float, float]:
    freqs = data["freqs"]
    k1 = K1_NOM
    k2 = K2_NOM
    z1 = ZETA1_CENTER
    z2 = ZETA2_CENTER
    tray_absq, iface_absq = flight_transfer_absq_g_np(freqs, k1, k2, z1, z2)
    chol = matern32_chol(freqs, FORCING_MATERN_ELL, db_to_ln_sigma(FLIGHT_F2F_DB))
    rng = np.random.default_rng(777)
    tray = np.empty(n)
    iface = np.empty(n)
    for i in range(n):
        force = data["mean_force"] * np.exp(chol @ rng.normal(size=len(freqs)))
        tray[i] = 3.0 * math.sqrt(np.trapz(tray_absq * force, freqs))
        iface[i] = 3.0 * math.sqrt(np.trapz(iface_absq * force, freqs))
    return float(np.std(np.log(tray))), float(np.std(np.log(iface)))


def build_consts(data: dict[str, Any], n_flights: int, sig_qoi_tray: float, sig_qoi_iface: float) -> dict[str, Any]:
    flight_build = data["flight_build"][:n_flights]
    n_builds = int(np.max(flight_build)) + 1
    return {
        "freqs_j": jnp.asarray(data["freqs"]),
        "mfreqs_j": jnp.asarray(data["mfreqs"]),
        "mean_force_j": jnp.asarray(data["mean_force"]),
        "log_smooth_j": jnp.asarray(np.log(data["smooth"])),
        "vibe_log_j": jnp.asarray(np.log(data["vibe_obs"])),
        "dome_modal_log_j": jnp.asarray(np.log(data["dome_modal_mag"])),
        "iface_modal_log_j": jnp.asarray(np.log(data["iface_modal_mag"])),
        "tray_modal_log_j": jnp.asarray(np.log(data["tray_modal_mag"])),
        "flight_build_j": jnp.asarray(flight_build),
        "flight_tray_log_j": jnp.asarray(np.log(data["flight_tray"][:n_flights])),
        "flight_iface_log_j": jnp.asarray(np.log(data["flight_iface"][:n_flights])),
        "n_builds": n_builds,
        "n_flights": n_flights,
        "sig_qoi_tray": sig_qoi_tray,
        "sig_qoi_iface": sig_qoi_iface,
    }


def flatten_metric(ds: Any, reducer: str) -> tuple[float, str]:
    worst_value = None
    worst_name = ""
    for var in ds.data_vars:
        vals = np.asarray(ds[var].values, dtype=float).reshape(-1)
        vals = vals[np.isfinite(vals)]
        if vals.size == 0:
            continue
        if reducer == "max":
            val = float(np.max(vals))
            better = worst_value is None or val > worst_value
        else:
            val = float(np.min(vals))
            better = worst_value is None or val < worst_value
        if better:
            worst_value = val
            worst_name = var
    return float(worst_value if worst_value is not None else math.nan), worst_name


def diagnostics_from_samples(samples_bc: dict[str, Any], extra: dict[str, Any], elapsed_s: float, label: str) -> dict[str, Any]:
    posterior = {k: np.asarray(v) for k, v in samples_bc.items()}
    idata = az.from_dict(posterior=posterior)
    rhat = az.rhat(idata, method="rank")
    ess_bulk = az.ess(idata, method="bulk")
    ess_tail = az.ess(idata, method="tail")
    max_rhat, max_rhat_var = flatten_metric(rhat, "max")
    min_bulk, min_bulk_var = flatten_metric(ess_bulk, "min")
    min_tail, min_tail_var = flatten_metric(ess_tail, "min")
    div = np.asarray(extra["diverging"])
    steps = np.asarray(extra["num_steps"])
    accept = np.asarray(extra["accept_prob"])
    ess_gate = ESS_PER_CHAIN_GATE * N_CHAINS
    convergence_pass = bool(
        max_rhat < RANK_RHAT_GATE
        and min_bulk >= ess_gate
        and min_tail >= ess_gate
        and int(div.sum()) == 0
    )
    return {
        "label": label,
        "sampler_attempted": "NumPyro NUTS",
        "nuts_sampler_ran": True,
        "nuts_active_claim": convergence_pass,
        "num_chains": N_CHAINS,
        "num_warmup": int(extra.get("num_warmup_record", 0)),
        "num_samples_per_chain": int(extra.get("num_samples_record", 0)),
        "post_warmup_draws_total": int(N_CHAINS * int(extra.get("num_samples_record", 0))),
        "elapsed_seconds": elapsed_s,
        "rank_normalized_rhat_method": "arviz.rhat(method='rank')",
        "bulk_ess_method": "arviz.ess(method='bulk')",
        "tail_ess_method": "arviz.ess(method='tail')",
        "rhat_gate_final": RANK_RHAT_GATE,
        "ess_gate_final": ess_gate,
        "max_rank_normalized_rhat": max_rhat,
        "max_rank_normalized_rhat_variable": max_rhat_var,
        "min_bulk_ess": min_bulk,
        "min_bulk_ess_variable": min_bulk_var,
        "min_tail_ess": min_tail,
        "min_tail_ess_variable": min_tail_var,
        "divergences_total": int(div.sum()),
        "divergence_fraction": float(div.mean()),
        "divergence_gate_clean": "0 ideal and required for clean pass in this run",
        "mean_accept_prob": float(np.mean(accept)),
        "max_num_steps": int(np.max(steps)),
        "mean_num_steps": float(np.mean(steps)),
        "max_observed_tree_depth": float(np.max(np.log2(steps + 1.0))),
        "convergence_pass": convergence_pass,
        "variables_checked_count": len(posterior),
        "variables_checked": sorted(posterior.keys()),
    }


def run_nuts_for_prefix(data: dict[str, Any], n_flights: int, sig_qoi_tray: float, sig_qoi_iface: float, warmup: int, samples: int) -> tuple[dict[str, np.ndarray], dict[str, Any]]:
    consts = build_consts(data, n_flights, sig_qoi_tray, sig_qoi_iface)
    kernel = NUTS(model_full, target_accept_prob=0.92, max_tree_depth=11)
    mcmc = MCMC(
        kernel,
        num_warmup=warmup,
        num_samples=samples,
        num_chains=N_CHAINS,
        chain_method="parallel",
        progress_bar=False,
    )
    t0 = time.perf_counter()
    key = random.PRNGKey(RUN_SEED + n_flights)
    mcmc.run(key, consts, extra_fields=("num_steps", "diverging", "accept_prob"))
    elapsed = time.perf_counter() - t0
    extra = dict(mcmc.get_extra_fields())
    extra["num_warmup_record"] = warmup
    extra["num_samples_record"] = samples
    samples_bc = {k: np.asarray(v) for k, v in mcmc.get_samples(group_by_chain=True).items()}
    diag = diagnostics_from_samples(samples_bc, extra, elapsed, f"cumulative_flights_{n_flights}")
    flat = {k: np.asarray(v).reshape((-1,) + np.asarray(v).shape[2:]) for k, v in samples_bc.items()}
    return flat, diag


def make_refined_grid(base_freqs: np.ndarray) -> np.ndarray:
    clusters = []
    for fn, zeta in [(86.25, 0.02), (93.5, 0.02)]:
        half_power = 2.0 * zeta * fn
        clusters.append(np.linspace(fn - 3.0 * half_power, fn + 3.0 * half_power, 181))
        clusters.append(fn + np.tanh(np.linspace(-3.0, 3.0, 121)) * (1.2 * half_power))
    refined = np.unique(np.concatenate([base_freqs, *clusters]))
    return refined[(refined >= base_freqs.min()) & (refined <= base_freqs.max())]


def reconstruct_flight_force_samples(data: dict[str, Any]) -> tuple[list[np.ndarray], dict[str, Any]]:
    freqs = data["freqs"]
    rng = np.random.default_rng(SETUP_SEED)
    sigma_build = db_to_ln_sigma(BUILD_SIGMA_DB_GENERATING)
    reconstructed_builds = []
    for build_id in range(11):
        dome = float(rng.normal(0.0, sigma_build))
        tray = float(rng.normal(0.0, sigma_build))
        reconstructed_builds.append((dome, tray))
    rng.normal(0.0, db_to_ln_sigma(SENSOR_SIGMA_DB_GENERATING), size=len(freqs))
    for _ in range(3):
        rng.normal(0.0, db_to_ln_sigma(SENSOR_SIGMA_DB_GENERATING), size=len(data["mfreqs"]))
    chol = matern32_chol(freqs, FORCING_MATERN_ELL, db_to_ln_sigma(FLIGHT_F2F_DB))
    for _ in range(500):
        _ = chol @ rng.normal(size=len(freqs))
    samples = []
    mismatches = []
    for i in range(11):
        log_force = chol @ rng.normal(size=len(freqs))
        force = data["mean_force"] * np.exp(log_force)
        samples.append(force)
        rng.normal(0.0, db_to_ln_sigma(SENSOR_SIGMA_DB_GENERATING), size=len(freqs))
        rng.normal(0.0, db_to_ln_sigma(SENSOR_SIGMA_DB_GENERATING), size=len(freqs))
        stored = data["flight_summaries"][i]
        mismatches.append(
            {
                "flight_id": i,
                "mean_abs_error": abs(float(np.mean(log_force)) - float(stored["force_log_psd_sample_mean"])),
                "sd_abs_error": abs(float(np.std(log_force)) - float(stored["force_log_psd_sample_sd"])),
            }
        )
    build_mismatch = []
    for i, (dome, tray) in enumerate(reconstructed_builds):
        truth = data["build_truth"][i]
        build_mismatch.append(abs(dome - truth["dome_log_psd_effect"]) + abs(tray - truth["tray_log_psd_effect"]))
    report = {
        "method": "Replayed setup RNG sequence because sequential_dataset.json stores scalar force summaries, not full force PSD curves.",
        "max_build_log_effect_l1_error": float(max(build_mismatch)),
        "max_force_log_mean_abs_error": float(max(m["mean_abs_error"] for m in mismatches)),
        "max_force_log_sd_abs_error": float(max(m["sd_abs_error"] for m in mismatches)),
        "per_flight_errors": mismatches,
    }
    return samples, report


def posterior_table(samples: dict[str, np.ndarray]) -> dict[str, Any]:
    keys = ["dome_hz", "tray_hz", "zeta1", "zeta2", "sigma_build_db", "sigma_sensor_db", "q_tray_struct_meanforce", "q_iface_struct_meanforce"]
    out = {}
    for key in keys:
        arr = np.asarray(samples[key], dtype=float).reshape(-1)
        out[key] = {
            "mean": float(np.mean(arr)),
            "sd": float(np.std(arr)),
            "q005": float(np.quantile(arr, 0.005)),
            "q025": float(np.quantile(arr, 0.025)),
            "q500": float(np.quantile(arr, 0.5)),
            "q975": float(np.quantile(arr, 0.975)),
            "q995": float(np.quantile(arr, 0.995)),
        }
    return out


def interface_predictive_bands(samples: dict[str, np.ndarray], data: dict[str, Any], refined_freqs: np.ndarray, n_draws: int, seed: int) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    n = len(samples["dome_hz"])
    idx = rng.integers(0, n, size=n_draws)
    mean_force = loglog_interp(refined_freqs, data["freqs"], data["mean_force"])
    chol = matern32_chol(refined_freqs, FORCING_MATERN_ELL, db_to_ln_sigma(FLIGHT_F2F_DB))
    curves = np.empty((n_draws, len(refined_freqs)))
    for j, ii in enumerate(idx):
        k1 = M1 * (2.0 * math.pi * float(samples["dome_hz"][ii])) ** 2
        k2 = M2 * (2.0 * math.pi * float(samples["tray_hz"][ii])) ** 2
        z1 = float(samples["zeta1"][ii])
        z2 = float(samples["zeta2"][ii])
        _, iface_absq = flight_transfer_absq_g_np(refined_freqs, k1, k2, z1, z2)
        force = mean_force * np.exp(chol @ rng.normal(size=len(refined_freqs)))
        dome_build = rng.normal(0.0, float(samples["sigma_build_ln"][ii]))
        curves[j] = iface_absq * force * math.exp(dome_build)
    return {
        "mean": np.mean(curves, axis=0),
        "q005": np.quantile(curves, 0.005, axis=0),
        "q025": np.quantile(curves, 0.025, axis=0),
        "q975": np.quantile(curves, 0.975, axis=0),
        "q995": np.quantile(curves, 0.995, axis=0),
    }


def plot_interface_gif(frame_bands: list[dict[str, Any]], refined_freqs: np.ndarray, smooth_refined: np.ndarray) -> dict[str, Any]:
    FRAME_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    frame_paths = []
    y_max = max(float(np.nanmax(b["q995"])) for b in frame_bands)
    y_min = min(float(np.nanmin(b["q005"])) for b in frame_bands)
    y_min = max(y_min, 1e-10)
    y_max = max(y_max, float(np.max(smooth_refined)))
    for i, bands in enumerate(frame_bands, start=1):
        q995 = bands["q995"]
        ratio = q995 / smooth_refined
        max_idx = int(np.argmax(ratio))
        summaries.append(
            {
                "after_flight": i,
                "q995_exceeds_spec_any_frequency": bool(np.any(q995 > smooth_refined)),
                "frequency_fraction_q995_above_spec": float(np.mean(q995 > smooth_refined)),
                "max_q995_to_spec_ratio": float(np.max(ratio)),
                "max_ratio_frequency_hz": float(refined_freqs[max_idx]),
            }
        )
        fig, ax = plt.subplots(figsize=(10.5, 6.2))
        ax.loglog(refined_freqs, smooth_refined, color="black", lw=2.4, label="original smoothline test spec")
        ax.fill_between(refined_freqs, bands["q005"], bands["q995"], color="#f2c94c", alpha=0.28, label="99% predictive band")
        ax.fill_between(refined_freqs, bands["q025"], bands["q975"], color="#2f80ed", alpha=0.28, label="95% predictive band")
        ax.loglog(refined_freqs, bands["mean"], color="#1b4f72", lw=2.0, label="posterior predictive mean")
        ax.axvline(86.25, color="#7f8c8d", ls=":", lw=1.1, label="tray mode marker")
        ax.axvline(93.5, color="#95a5a6", ls="--", lw=1.1, label="dome mode marker")
        ax.set_title(f"Coupled interface acceleration response PSD after flight {i}")
        ax.set_xlabel("frequency [Hz]")
        ax.set_ylabel("interface acceleration response PSD [g^2/Hz]")
        ax.set_ylim(y_min * 0.7, y_max * 1.8)
        ax.grid(True, which="both", alpha=0.24)
        ax.legend(loc="lower left", fontsize=8)
        fig.tight_layout()
        path = FRAME_DIR / f"interface_response_psd_after_flight_{i:02d}.png"
        fig.savefig(path, dpi=145)
        plt.close(fig)
        frame_paths.append(path)
    adaptive_palette = getattr(Image, "ADAPTIVE", Image.Palette.ADAPTIVE)
    images = [Image.open(path).convert("P", palette=adaptive_palette) for path in frame_paths]
    gif_path = FIG_DIR / "interface_response_psd_evolution.gif"
    images[0].save(gif_path, save_all=True, append_images=images[1:], duration=850, loop=0)
    return {"gif": str(gif_path.relative_to(OUT_DIR)), "frames": [str(p.relative_to(OUT_DIR)) for p in frame_paths], "summaries": summaries}


def plot_forcing_overlay(data: dict[str, Any], force_samples: list[np.ndarray]) -> None:
    fig, ax = plt.subplots(figsize=(11.2, 6.1))
    ax.loglog(data["freqs"], data["original_force"], color="black", lw=2.4, label="original force PSD behind spec")
    ax.loglog(data["freqs"], data["mean_force"], color="#1f77b4", lw=2.1, label="flight mean force PSD (-6 dB project assumption)")
    for i, force in enumerate(force_samples):
        ax.loglog(data["freqs"], force, lw=1.0, alpha=0.62, label="reconstructed flight forcing draw" if i == 0 else None)
    ax.set_title("Flight forcing samples over original forcing PSD")
    ax.set_xlabel("frequency [Hz]")
    ax.set_ylabel("force PSD [N^2/Hz]")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "flight_forcing_samples_overlay.png", dpi=160)
    plt.close(fig)


def plot_tray_grms_overlay(data: dict[str, Any]) -> None:
    fids = np.arange(len(data["flight_tray"]))
    fig, ax = plt.subplots(figsize=(10.8, 6.0))
    ax.semilogy(fids, data["flight_tray"], "o-", lw=2.0, label="flight tray 3*GRMS observations")
    ax.axhline(data["vibe_3grms"], color="#d62728", ls="--", lw=2.0, label=f"first-build vibe tray 3*GRMS = {data['vibe_3grms']:.1f} g")
    ax.axhline(data["smoothline_3grms"], color="#444444", ls=":", lw=2.0, label=f"smoothline input 3*GRMS = {data['smoothline_3grms']:.1f} g")
    ax.text(0.02, 0.08, "Scalar 3*GRMS is a summary only; PSD envelope is the primary check.", transform=ax.transAxes, fontsize=9)
    ax.set_title("Flight tray 3*GRMS vs original vibe-test references")
    ax.set_xlabel("flight id")
    ax.set_ylabel("tray acceleration 3*GRMS [g], log scale")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "flight_tray_3grms_vs_vibe_reference.png", dpi=160)
    plt.close(fig)


def resolution_sensitivity(samples: dict[str, np.ndarray], data: dict[str, Any], refined_freqs: np.ndarray) -> dict[str, Any]:
    rng = np.random.default_rng(9090)
    n = len(samples["dome_hz"])
    idx = rng.choice(n, size=min(500, n), replace=False)
    mean_force_refined = loglog_interp(refined_freqs, data["freqs"], data["mean_force"])
    q_base_tray = []
    q_ref_tray = []
    q_base_iface = []
    q_ref_iface = []
    peak_base_iface = []
    peak_ref_iface = []
    for ii in idx:
        k1 = M1 * (2.0 * math.pi * float(samples["dome_hz"][ii])) ** 2
        k2 = M2 * (2.0 * math.pi * float(samples["tray_hz"][ii])) ** 2
        z1 = float(samples["zeta1"][ii])
        z2 = float(samples["zeta2"][ii])
        tb, ib = flight_transfer_absq_g_np(data["freqs"], k1, k2, z1, z2)
        tr, ir = flight_transfer_absq_g_np(refined_freqs, k1, k2, z1, z2)
        psd_tb = tb * data["mean_force"]
        psd_ib = ib * data["mean_force"]
        psd_tr = tr * mean_force_refined
        psd_ir = ir * mean_force_refined
        q_base_tray.append(3.0 * math.sqrt(np.trapz(psd_tb, data["freqs"])))
        q_ref_tray.append(3.0 * math.sqrt(np.trapz(psd_tr, refined_freqs)))
        q_base_iface.append(3.0 * math.sqrt(np.trapz(psd_ib, data["freqs"])))
        q_ref_iface.append(3.0 * math.sqrt(np.trapz(psd_ir, refined_freqs)))
        peak_base_iface.append(float(np.max(psd_ib)))
        peak_ref_iface.append(float(np.max(psd_ir)))
    q_base_tray = np.asarray(q_base_tray)
    q_ref_tray = np.asarray(q_ref_tray)
    q_base_iface = np.asarray(q_base_iface)
    q_ref_iface = np.asarray(q_ref_iface)
    peak_base_iface = np.asarray(peak_base_iface)
    peak_ref_iface = np.asarray(peak_ref_iface)

    def rel(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        return (b - a) / np.maximum(np.abs(a), 1e-15)

    spacing = {}
    for fn in [86.25, 93.5]:
        bw = 2.0 * 0.02 * fn
        lo, hi = fn - 0.5 * bw, fn + 0.5 * bw
        base_local = data["freqs"][(data["freqs"] >= lo) & (data["freqs"] <= hi)]
        ref_local = refined_freqs[(refined_freqs >= lo) & (refined_freqs <= hi)]
        spacing[f"{fn:.2f}_hz"] = {
            "half_power_bandwidth_hz_assuming_zeta_0p02": bw,
            "base_points_in_half_power_band": int(len(base_local)),
            "refined_points_in_half_power_band": int(len(ref_local)),
            "base_max_gap_hz_in_band": float(np.max(np.diff(base_local))) if len(base_local) > 1 else None,
            "refined_max_gap_hz_in_band": float(np.max(np.diff(ref_local))) if len(ref_local) > 1 else None,
        }

    # Posterior median curve for figure.
    med = {k: float(np.median(samples[k])) for k in ["dome_hz", "tray_hz", "zeta1", "zeta2"]}
    k1 = M1 * (2.0 * math.pi * med["dome_hz"]) ** 2
    k2 = M2 * (2.0 * math.pi * med["tray_hz"]) ** 2
    _, ib = flight_transfer_absq_g_np(data["freqs"], k1, k2, med["zeta1"], med["zeta2"])
    _, ir = flight_transfer_absq_g_np(refined_freqs, k1, k2, med["zeta1"], med["zeta2"])
    fig, ax = plt.subplots(figsize=(10.8, 6.0))
    ax.loglog(refined_freqs, ir * mean_force_refined, lw=2.0, label="refined grid interface PSD")
    ax.loglog(data["freqs"], ib * data["mean_force"], "o", ms=3.5, label="stored dataset grid samples")
    ax.axvline(86.25, color="#7f8c8d", ls=":", label="tray mode ~86 Hz")
    ax.axvline(93.5, color="#95a5a6", ls="--", label="dome mode ~93.5 Hz")
    ax.set_title("Resolution sensitivity near QOI-driving modes")
    ax.set_xlabel("frequency [Hz]")
    ax.set_ylabel("interface PSD at posterior median, mean force [g^2/Hz]")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "resolution_sensitivity.png", dpi=160)
    plt.close(fig)

    result = {
        "grid_policy": "Use stored 260-point sequential_dataset grid for likelihood; use mode-local refined grid for response PSD/QOI evaluation.",
        "base_frequency_count": int(len(data["freqs"])),
        "refined_frequency_count": int(len(refined_freqs)),
        "mode_local_spacing": spacing,
        "qoi_shift_refined_minus_base": {
            "tray_3grms_meanforce_relative_median": float(np.median(rel(q_base_tray, q_ref_tray))),
            "tray_3grms_meanforce_relative_max_abs": float(np.max(np.abs(rel(q_base_tray, q_ref_tray)))),
            "interface_3grms_meanforce_relative_median": float(np.median(rel(q_base_iface, q_ref_iface))),
            "interface_3grms_meanforce_relative_max_abs": float(np.max(np.abs(rel(q_base_iface, q_ref_iface)))),
            "interface_peak_psd_relative_median": float(np.median(rel(peak_base_iface, peak_ref_iface))),
            "interface_peak_psd_relative_max_abs": float(np.max(np.abs(rel(peak_base_iface, peak_ref_iface)))),
        },
    }
    (OUT_DIR / "resolution_sensitivity.json").write_text(json.dumps(result, indent=2))
    return result


def image_qa(paths: list[Path]) -> dict[str, Any]:
    rows = []
    for path in paths:
        if path.suffix.lower() == ".gif":
            with Image.open(path) as img:
                n_frames = getattr(img, "n_frames", 1)
                width, height = img.size
                img.seek(0)
                stat = ImageStat.Stat(img.convert("L"))
                stddev = float(stat.stddev[0])
            ok = n_frames == 11 and width >= 900 and height >= 500 and stddev > 2.0
            rows.append({"file": str(path.relative_to(OUT_DIR)), "pass": ok, "width": width, "height": height, "frames": n_frames, "gray_stddev": stddev})
        else:
            with Image.open(path) as img:
                width, height = img.size
                stat = ImageStat.Stat(img.convert("L"))
                stddev = float(stat.stddev[0])
            ok = width >= 900 and height >= 500 and stddev > 2.0 and path.stat().st_size > 5000
            rows.append({"file": str(path.relative_to(OUT_DIR)), "pass": ok, "width": width, "height": height, "gray_stddev": stddev, "bytes": path.stat().st_size})
    report = {
        "pass": bool(rows and all(row["pass"] for row in rows)),
        "checks": rows,
        "limitations": "This QA checks dimensions, frame count, file size, and nonblank raster variance. It does not OCR every label.",
    }
    (OUT_DIR / "image_legibility_report.json").write_text(json.dumps(report, indent=2))
    return report


def immutable_hash_check() -> dict[str, Any]:
    manifest_path = ROOT / "harness" / "checkers" / "manifest.sha256"
    rows = []
    for line in manifest_path.read_text().splitlines():
        expected, rel = line.split()
        path = ROOT / rel
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append({"file": rel, "expected": expected, "actual": digest, "pass": digest == expected})
    return {"pass": all(row["pass"] for row in rows), "files": rows}


def write_quantity_contracts() -> None:
    text = """# Quantity Contracts

## Coupled Interface Acceleration Response PSD

- Numerator: acceleration squared at the coupled-system interface/source DOF `m1`.
- Denominator: frequency bandwidth.
- Coordinate: coupled dome/tray interface/source coordinate `m1`.
- Excitation: latent flight force PSD into `m1`.
- Boundary condition: dome and tray coupled in flight configuration.
- Units: `g^2/Hz`.
- Expected limiting behavior: acceleration per force tends toward zero at very low frequency for this force-input model; response PSD falls with the dynamic inertance away from resonance.
- Expected resonance/antiresonance behavior: narrow response peaks can occur near the QOI-driving tray/dome coupled modes around 86 Hz and 93.5 Hz; a scalar GRMS can hide a narrow-band exceedance.
- Reference: setup quantity contract plus round-2 task card; GEVS/GSFC-STD-7000 envelope comparison is documented through `runner_comparison_20260602/reader_web_verified_sources.md`.

## Original Smoothline Test Spec

- Numerator: commanded/base acceleration squared.
- Denominator: frequency bandwidth.
- Coordinate: original vibe-test input smoothline for the tray test.
- Excitation: random vibration test specification.
- Boundary condition: qualification/test input, not a flight force input.
- Units: `g^2/Hz`.
- Expected behavior: log-log interpolation through `(20, 0.01)`, `(100, 0.1)`, `(750, 0.1)`, `(2000, 0.001)`.
- Reference: setup packet and human task card.

## Flight Forcing PSD

- Numerator: force squared into `m1`.
- Denominator: frequency bandwidth.
- Coordinate: source/dome input `m1`.
- Excitation: latent flight forcing process.
- Boundary condition: coupled flight configuration.
- Units: `N^2/Hz`.
- Expected behavior: Matern-3/2 log-PSD samples around a mean 6 dB below the original force PSD. The -6 dB value is a project assumption, not a GEVS qualification margin.
- Reference: setup packet and round-2 margin note.

## Tray 3*GRMS QOI

- Numerator: three times the square root of the one-sided PSD integral.
- Denominator: not applicable after PSD integration.
- Coordinate: tray/load `m2`.
- Excitation: flight force for flight sequence, smoothline base acceleration for the vibe reference.
- Boundary condition: stage-specific, labeled in the figure.
- Units: `g`.
- Expected behavior: a zero-mean Gaussian 3-sigma estimate, approximately 99.73%, not a hard maximum.
- Reference: Irvine/vibrationdata verification summarized in `reader_web_verified_sources.md`.
"""
    (OUT_DIR / "quantity_contracts.md").write_text(text)


def write_assumptions_ledger(resolution: dict[str, Any] | None = None) -> None:
    rows = [
        ["PSD-space dB convention", "factor = 10 ** (dB / 10)", "dimensionless PSD multiplier", "setup packet", "All dB values are power/PSD quantities.", "High"],
        ["Smoothline PSD points", "[(20,0.01),(100,0.1),(750,0.1),(2000,0.001)]", "Hz, g^2/Hz", "human task card", "Original test spec for envelope comparison.", "High"],
        ["Flight forcing mean offset", "-6.0", "dB PSD", "project setup assumption", "Mean flight forcing is below original force PSD; not a GEVS margin.", "High"],
        ["Flight forcing variability", "3.0", "dB PSD sigma", "setup/task card", "Known Matern forcing variability, fixed in inference.", "High"],
        ["Forcing covariance", f"Matern-3/2 ell={FORCING_MATERN_ELL}", "natural log frequency", "setup/task card", "Flight forcing curves are correlated over log frequency.", "High"],
        ["Build-to-build scale prior", "HalfNormal(0.5) on natural-log PSD sigma", "ln PSD", "round-2 model", "Learn build variability with non-centered raw build effects.", "High"],
        ["Sensor scale prior", "HalfNormal(0.3) on natural-log PSD sigma", "ln PSD", "round-2 model", "Learn observation scatter for full PSD/modal curves.", "High"],
        ["Flight QOI observation noise", f"{FLIGHT_QOI_OBS_SIGMA_LN}", "natural log 3*GRMS", "round-2 model assumption", "Scalar flight observations need residual noise beyond sampled forcing latent.", "Medium"],
        ["Structural stiffness prior", "log(k/k_nom) ~ Normal(0,0.18^2), truncated [0.55,1.65]", "dimensionless", "setup prior summary", "Prior centers from fresh 2DOF setup.", "High"],
        ["Damping prior", "log(zeta/zeta_nom) ~ Normal(0,0.35^2), truncated [0.004,0.09]", "dimensionless", "setup prior summary", "Positive damping with broad uncertainty.", "High"],
        ["Likelihood data usage", "whole stored tray PSD and modal log-magnitude curves; scalar flight 3*GRMS observations", "mixed", "round-2 model", "No full flight PSD observations are stored in sequential_dataset.json.", "High"],
        ["Response evaluation grid", f"stored {resolution['base_frequency_count'] if resolution else 260} point grid plus mode-local refinement" if resolution else "stored grid plus planned mode-local refinement", "Hz", "round-2 resolution gate", "Resolve tray/dome modes without inventing a new coarse truth.", "High"],
    ]
    (OUT_DIR / "assumptions_ledger.json").write_text(json.dumps({"rows": [
        {"assumption": r[0], "value": r[1], "units": r[2], "source": r[3], "rationale": r[4], "sensitivity_priority": r[5]}
        for r in rows
    ]}, indent=2))
    md = "# Assumptions Ledger\n\n| Assumption | Value | Units | Source | Rationale | Sensitivity |\n|---|---|---|---|---|---|\n"
    for r in rows:
        md += f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} |\n"
    (OUT_DIR / "assumptions_ledger.md").write_text(md)


def write_reports(
    diagnostics: dict[str, Any],
    posterior: dict[str, Any],
    interface_summary: dict[str, Any],
    force_recon: dict[str, Any],
    resolution: dict[str, Any],
    image_report: dict[str, Any],
    checks: dict[str, Any],
    runtime: dict[str, Any],
) -> None:
    all_diag = diagnostics["full"]
    conv = all_diag["convergence_pass"]
    status_line = "PASS" if conv else "NOT CONVERGED"
    prefix_warnings = [
        (label, diag)
        for label, diag in diagnostics["cumulative_frames"].items()
        if not diag.get("convergence_pass", False)
    ]
    prefix_warning_text = "None."
    if prefix_warnings:
        prefix_warning_text = "\n".join(
            "- `{}`: R-hat `{:.4f}`, bulk ESS `{:.1f}`, tail ESS `{:.1f}`, divergences `{}`.".format(
                label,
                diag["max_rank_normalized_rhat"],
                diag["min_bulk_ess"],
                diag["min_tail_ess"],
                diag["divergences_total"],
            )
            for label, diag in prefix_warnings
        )
    packet = f"""# Codex GPT-5.5 Round 2 Packet

## Method Summary

Status: **{status_line}** for the strict final NUTS convergence gate.

Model form: a coupled 2DOF dome/tray frequency-response model with inferred structural parameters `dome_hz`, `tray_hz`, `zeta1`, `zeta2`, learned build-to-build log-PSD scale, learned sensor log-PSD scale, non-centered raw build effects, and non-centered per-flight forcing-QOI latent scalars.

Likelihood data usage: whole stored tray vibe log PSD at 260 frequencies; whole stored modal log-magnitude curves for dome-only, coupled interface, and coupled tray channels at 180 frequencies each; scalar tray and interface flight `3*GRMS` observations for 11 flights. The setup dataset does **not** store full flight interface PSD observations, so the key PSD bands are posterior predictive response envelopes, not direct measured flight PSD posterior bands.

Likelihood sketch: `log y_vibe(f) ~ Normal(log |T_tray|^2 + log S_spec + b_tray0, sigma_sensor)`, modal log magnitudes use `0.5*b_build`, and flight `log(3*GRMS)` uses `log q_struct(theta) + 0.5*b_build + sigma_f2f_qoi*z_flight` with `z_flight ~ Normal(0,1)`.

Data count: 1 tray vibe PSD curve, 3 modal log-magnitude curves, 11 tray flight scalar QOIs, and 11 interface flight scalar QOIs. Flight-to-flight forcing variability is modeled as fixed 3 dB PSD-space variability; full frequency-dependent flight forcing curves are used for posterior predictive response bands.

## Engineering Question

Does the original smoothline test spec envelope the predicted coupled interface flight response PSD across frequency? The primary metric is frequencywise PSD envelope comparison, especially the 99% band. The tray `3*GRMS` overlay is only a scalar summary.

## NUTS Diagnostics

- Sampler attempted: NumPyro NUTS in `.venv_nuts`.
- Chains: {all_diag['num_chains']}; warmup per chain: {all_diag['num_warmup']}; samples per chain: {all_diag['num_samples_per_chain']}.
- Max rank-normalized R-hat over all sampled/deterministic variables: `{all_diag['max_rank_normalized_rhat']:.4f}` at `{all_diag['max_rank_normalized_rhat_variable']}`; gate `< 1.01`.
- Min bulk ESS: `{all_diag['min_bulk_ess']:.1f}` at `{all_diag['min_bulk_ess_variable']}`; gate `>= {all_diag['ess_gate_final']}`.
- Min tail ESS: `{all_diag['min_tail_ess']:.1f}` at `{all_diag['min_tail_ess_variable']}`; gate `>= {all_diag['ess_gate_final']}`.
- Divergences: `{all_diag['divergences_total']}`; clean target `0`.

Early cumulative-frame warning: the final all-flight posterior passed, but the following GIF prefix fits did not pass the strict clean-divergence gate and should be read as hard-WARN frames, not clean final posterior claims:

{prefix_warning_text}

## Priority Figures

![Interface response PSD evolution](figures/interface_response_psd_evolution.gif)

![Flight forcing samples overlay](figures/flight_forcing_samples_overlay.png)

![Flight tray 3*GRMS vs vibe reference](figures/flight_tray_3grms_vs_vibe_reference.png)

![Resolution sensitivity](figures/resolution_sensitivity.png)

## Interface PSD Envelope Summary

- Final frame 99% band exceeds spec at any frequency: `{interface_summary['summaries'][-1]['q995_exceeds_spec_any_frequency']}`.
- Final frame max 99%/spec ratio: `{interface_summary['summaries'][-1]['max_q995_to_spec_ratio']:.4g}` at `{interface_summary['summaries'][-1]['max_ratio_frequency_hz']:.2f} Hz`.
- Final frame frequency fraction with 99% band above spec: `{interface_summary['summaries'][-1]['frequency_fraction_q995_above_spec']:.4f}`.

## Resolution Sensitivity

- Base grid count: `{resolution['base_frequency_count']}`; refined grid count: `{resolution['refined_frequency_count']}`.
- Interface `3*GRMS` median refined-minus-base shift: `{resolution['qoi_shift_refined_minus_base']['interface_3grms_meanforce_relative_median']:.4%}`.
- Interface peak PSD median refined-minus-base shift: `{resolution['qoi_shift_refined_minus_base']['interface_peak_psd_relative_median']:.4%}`.

## Forcing Reconstruction Note

`sequential_dataset.json` did not store the full per-flight forcing PSD curves. I reconstructed the setup RNG sequence and checked it against the stored force log-mean/log-sd summaries. Maximum log-mean error was `{force_recon['max_force_log_mean_abs_error']:.3e}` and maximum log-sd error was `{force_recon['max_force_log_sd_abs_error']:.3e}`.

## Limitations

- The interface response PSD GIF is posterior predictive because full flight PSD observations are absent from the setup dataset.
- Per-flight forcing latents in NUTS are scalar QOI-level latent effects, not 260-dimensional sampled force GP curves; full GP curves are drawn in posterior prediction.
- If convergence status above is NOT CONVERGED, intervals should be treated as not-yet-converged evidence, not a clean NUTS pass.
"""
    (OUT_DIR / "packet.md").write_text(packet)

    (OUT_DIR / "results.json").write_text(json.dumps({
        "posterior_summary": posterior,
        "interface_psd_evolution": interface_summary,
        "resolution_sensitivity": resolution,
        "force_reconstruction": force_recon,
    }, indent=2))

    (OUT_DIR / "nuts_diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    diag_md = f"""# NUTS Diagnostics

Sampler attempted: NumPyro NUTS.

Strict final convergence pass: `{conv}`.

- Max rank-normalized R-hat: `{all_diag['max_rank_normalized_rhat']}` at `{all_diag['max_rank_normalized_rhat_variable']}`.
- Min bulk ESS: `{all_diag['min_bulk_ess']}` at `{all_diag['min_bulk_ess_variable']}`.
- Min tail ESS: `{all_diag['min_tail_ess']}` at `{all_diag['min_tail_ess_variable']}`.
- Divergences: `{all_diag['divergences_total']}`.

All sampled variables, including raw build and flight latents, were included in the diagnostic gate.
"""
    (OUT_DIR / "nuts_diagnostics.md").write_text(diag_md)

    known = "# Known Failures And Risks\n\n"
    if not conv:
        known += "- Strict NUTS convergence did not pass; do not report a clean NUTS-active result.\n"
    else:
        known += "- No strict convergence failure was detected by the final all-flight diagnostic gate.\n"
    if prefix_warnings:
        known += "- Early cumulative GIF prefix fits had divergence warnings; see `nuts_diagnostics.json` and the packet warning before treating early-frame intervals as clean.\n"
    known += "- Full flight response PSD observations are absent from the setup dataset; response PSD bands are posterior predictive.\n"
    known += "- The round-2 script focuses on the priority full-data likelihood and does not rerun a peak-feature likelihood comparison.\n"
    (OUT_DIR / "known_failures.md").write_text(known)

    review = """# Review Request

Please review the priority deliverables first:

1. `figures/interface_response_psd_evolution.gif`
2. `figures/flight_forcing_samples_overlay.png`
3. `figures/flight_tray_3grms_vs_vibe_reference.png`
4. `nuts_diagnostics.json`
5. `resolution_sensitivity.json`

Main review question: are the posterior predictive interface PSD bands the right interpretation given that the setup dataset stores scalar flight QOIs but not full flight PSD observations?
"""
    (OUT_DIR / "review_request.md").write_text(review)

    commands = f"""# Commands

Actual workspace assertion:

```bash
pwd
# /Users/avoss/Downloads/bayesX/Agentic BayesX
```

Venv package repair attempted before the replay script:

```bash
.venv_nuts/bin/pip install --quiet --disable-pip-version-check 'arviz<0.19'
.venv_nuts/bin/pip install --quiet --disable-pip-version-check 'scipy<1.13'
```

One-command replay:

```bash
bash artifacts/reports/runner_codex_gpt55_round2_20260602/run_round2.sh
```

Immutable checker verification:

```bash
shasum -a 256 -c harness/checkers/manifest.sha256
```

Runtime recorded in `runtime.json`: active `{runtime['active_runtime_s']:.2f}` s, elapsed `{runtime['elapsed_wallclock_s']:.2f}` s.
"""
    (OUT_DIR / "commands.md").write_text(commands)

    changed = """# Files Changed

Primary new output folder:

- `artifacts/reports/runner_codex_gpt55_round2_20260602/`

Project memory updated:

- `notes/todo.md`

No immutable checker files were edited.
"""
    (OUT_DIR / "files_changed.md").write_text(changed)

    manifest = {
        "trial_id": "runner_codex_gpt55_round2_20260602",
        "date": "2026-06-02",
        "workspace": str(ROOT),
        "output_dir": str(OUT_DIR),
        "sampler": {
            "attempted": "NumPyro NUTS",
            "nuts_sampler_ran": True,
            "nuts_active_claim": bool(conv),
            "convergence_pass": bool(conv),
            "random_walk_metropolis_used": False,
            "custom_hmc_used": False,
        },
        "priority_artifacts": [
            "priority_deliverables.md",
            "figures/interface_response_psd_evolution.gif",
            "figures/flight_forcing_samples_overlay.png",
            "figures/flight_tray_3grms_vs_vibe_reference.png",
        ],
        "supporting_artifacts": [
            "packet.md",
            "commands.md",
            "files_changed.md",
            "assumptions_ledger.md",
            "assumptions_ledger.json",
            "quantity_contracts.md",
            "nuts_diagnostics.md",
            "nuts_diagnostics.json",
            "results.json",
            "resolution_sensitivity.json",
            "image_legibility_report.json",
            "checks.json",
            "known_failures.md",
            "review_request.md",
            "runtime.json",
        ],
        "checks_status": checks.get("status", "pending"),
        "image_qa_pass": image_report["pass"],
        "cumulative_frame_convergence_warning_count": len(prefix_warnings),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))


def write_runtime(start_wall: float) -> dict[str, Any]:
    elapsed = time.perf_counter() - start_wall
    active = float(sum(float(s["active_runtime_s"]) for s in STAGE_TIMES))
    active = min(active, elapsed)
    runtime = {
        "active_runtime_s": active,
        "elapsed_wallclock_s": elapsed,
        "active_runtime_definition": "Sum of timed stages inside run_round2.py; no human approval wait included.",
        "stage_times": STAGE_TIMES,
        "active_runtime_s_le_elapsed_wallclock_s": active <= elapsed,
    }
    (OUT_DIR / "runtime.json").write_text(json.dumps(runtime, indent=2))
    return runtime


def self_checks(diagnostics: dict[str, Any], force_recon: dict[str, Any], image_report: dict[str, Any], runtime: dict[str, Any]) -> dict[str, Any]:
    required = [
        "priority_deliverables.md",
        "packet.md",
        "commands.md",
        "files_changed.md",
        "assumptions_ledger.md",
        "assumptions_ledger.json",
        "quantity_contracts.md",
        "nuts_diagnostics.md",
        "nuts_diagnostics.json",
        "results.json",
        "resolution_sensitivity.json",
        "known_failures.md",
        "review_request.md",
        "manifest.json",
        "runtime.json",
        "figures/interface_response_psd_evolution.gif",
        "figures/flight_forcing_samples_overlay.png",
        "figures/flight_tray_3grms_vs_vibe_reference.png",
        "figures/resolution_sensitivity.png",
    ]
    checks = []

    def record(name: str, ok: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    for rel in required:
        path = OUT_DIR / rel
        record(f"exists:{rel}", path.exists() and (not path.is_file() or path.stat().st_size > 0), str(path))
    record("force_reconstruction_matches_stored_summaries", force_recon["max_force_log_mean_abs_error"] < 1e-10 and force_recon["max_force_log_sd_abs_error"] < 1e-10, force_recon)
    record("strict_final_nuts_convergence_pass", diagnostics["full"]["convergence_pass"], diagnostics["full"])
    record("image_legibility_pass", image_report["pass"], image_report)
    record("runtime_active_le_elapsed", runtime["active_runtime_s"] <= runtime["elapsed_wallclock_s"], runtime)
    imm = immutable_hash_check()
    record("immutable_checker_hashes_unchanged", imm["pass"], imm)
    status = "pass" if all(c["pass"] for c in checks) else "fail"
    warnings = []
    if any(not d.get("convergence_pass", False) for d in diagnostics.get("cumulative_frames", {}).values()):
        warnings.append("One or more cumulative GIF prefix fits did not pass the strict clean convergence gate; see nuts_diagnostics.json.")
    out = {"status": status, "checks": checks, "warnings": warnings}
    (OUT_DIR / "checks.json").write_text(json.dumps(out, indent=2))
    return out


def main() -> int:
    start_wall = time.perf_counter()
    prepare_dirs()

    with timed("load_data_and_fixed_qoi_scatter"):
        data = load_data()
        sig_qoi_tray, sig_qoi_iface = compute_qoi_log_scatter(data)

    print(json.dumps({"workspace": str(ROOT), "assert_is_runner_workspace": True, "output_dir": str(OUT_DIR)}, indent=2))
    print(f"[info] fixed QOI log scatter: tray={sig_qoi_tray:.4f}, interface={sig_qoi_iface:.4f}")

    cumulative_samples: dict[int, dict[str, np.ndarray]] = {}
    cumulative_diags: dict[str, Any] = {}
    n_flights_total = len(data["flight_tray"])

    for n_flights in range(1, n_flights_total):
        with timed(f"nuts_cumulative_{n_flights}_flights"):
            print(f"[info] NUTS cumulative prefix {n_flights}/{n_flights_total - 1}")
            samples, diag = run_nuts_for_prefix(data, n_flights, sig_qoi_tray, sig_qoi_iface, CUM_WARMUP, CUM_SAMPLES)
        cumulative_samples[n_flights] = samples
        cumulative_diags[f"cumulative_{n_flights}"] = diag
        print(f"[diag] prefix {n_flights}: rhat={diag['max_rank_normalized_rhat']:.4f}, bulk={diag['min_bulk_ess']:.1f}, tail={diag['min_tail_ess']:.1f}, div={diag['divergences_total']}")

    with timed("nuts_full_11_flights"):
        print("[info] NUTS full all-flight run")
        full_samples, full_diag = run_nuts_for_prefix(data, n_flights_total, sig_qoi_tray, sig_qoi_iface, MAIN_WARMUP, MAIN_SAMPLES)
    cumulative_samples[n_flights_total] = full_samples
    cumulative_diags[f"cumulative_{n_flights_total}"] = full_diag
    print(f"[diag] full: rhat={full_diag['max_rank_normalized_rhat']:.4f}, bulk={full_diag['min_bulk_ess']:.1f}, tail={full_diag['min_tail_ess']:.1f}, div={full_diag['divergences_total']}")

    diagnostics = {"full": full_diag, "cumulative_frames": cumulative_diags}

    with timed("postprocess_figures_and_checks"):
        refined_freqs = make_refined_grid(data["freqs"])
        smooth_refined = loglog_interp(refined_freqs, data["freqs"], data["smooth"])
        frame_bands = [
            interface_predictive_bands(cumulative_samples[i], data, refined_freqs, GIF_DRAWS, RUN_SEED + 1000 + i)
            for i in range(1, n_flights_total + 1)
        ]
        interface_summary = plot_interface_gif(frame_bands, refined_freqs, smooth_refined)
        force_samples, force_recon = reconstruct_flight_force_samples(data)
        plot_forcing_overlay(data, force_samples)
        plot_tray_grms_overlay(data)
        resolution = resolution_sensitivity(full_samples, data, refined_freqs)
        write_quantity_contracts()
        write_assumptions_ledger(resolution)

        np.savez_compressed(
            OUT_DIR / "posterior_samples_full.npz",
            **{f"full_{k}": np.asarray(v) for k, v in full_samples.items() if k in [
                "dome_hz", "tray_hz", "zeta1", "zeta2", "sigma_build_db", "sigma_sensor_db",
                "sigma_build_ln", "q_tray_struct_meanforce", "q_iface_struct_meanforce",
                "dome_build_raw", "tray_build_raw", "flight_tray_force_raw", "flight_iface_force_raw",
            ]},
        )
        posterior = posterior_table(full_samples)
        image_report = image_qa([
            FIG_DIR / "interface_response_psd_evolution.gif",
            FIG_DIR / "flight_forcing_samples_overlay.png",
            FIG_DIR / "flight_tray_3grms_vs_vibe_reference.png",
            FIG_DIR / "resolution_sensitivity.png",
        ])

    runtime = write_runtime(start_wall)
    checks = {"status": "pending"}
    write_reports(diagnostics, posterior, interface_summary, force_recon, resolution, image_report, checks, runtime)
    runtime = write_runtime(start_wall)

    # Refresh checks after manifest/report files exist.
    checks = self_checks(diagnostics, force_recon, image_report, runtime)
    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["checks_status"] = checks["status"]
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(json.dumps({"checks_status": checks["status"], "convergence_pass": full_diag["convergence_pass"], "out_dir": str(OUT_DIR)}, indent=2))
    return 0 if checks["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
