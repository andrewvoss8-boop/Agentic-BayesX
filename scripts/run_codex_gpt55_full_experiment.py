#!/usr/bin/env python3
"""Runner-only full sequential vibe/modal/flight HMC experiment.

This script is intentionally scoped to the Codex GPT-5.5 runner output folder.
It does not edit immutable checker files and it does not claim NumPyro/NUTS is
available. Posterior inference is done with a custom PyTorch-autograd HMC
backend because Python is 3.9.6 and NumPyro/JAX/PyMC are absent in this copy.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image

from fresh_2dof_statfem_fbs import (
    G0_M_PER_S2,
    Constants,
    Params,
    accel_over_force,
    coupled_reciprocal_inertance,
    damping_values,
    dome_only_reciprocal_inertance,
    frequency_channels,
    grms_from_psd,
    prior_model_summary,
    tray_transmissibility,
    true_params,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "reports" / "runner_codex_gpt55_20260602"
FIG_DIR = OUT_DIR / "figures"
RUN_SEED = 20260602
DTYPE = torch.float64


@dataclass(frozen=True)
class RunnerConfig:
    smoothline_freq_hz: tuple[float, ...] = (20.0, 100.0, 750.0, 2000.0)
    smoothline_psd_g2_per_hz: tuple[float, ...] = (0.01, 0.1, 0.1, 0.001)
    flight_to_flight_sigma_db_psd: float = 3.0
    build_sigma_db_psd_truth: float = 1.5
    sensor_sigma_db_psd_truth: float = 0.75
    flight_mean_force_below_original_db_psd: float = -6.0
    forcing_matern_length_logfreq: float = 0.08
    n_later_builds_and_flights: int = 10
    n_freq: int = 56
    n_modal_freq: int = 48
    hmc_warmup: int = 100
    hmc_samples: int = 160
    hmc_chains: int = 2
    hmc_leapfrog_steps: int = 10
    hmc_initial_step_size_full: float = 0.0008
    hmc_initial_step_size_feature: float = 0.0015
    hmc_target_accept: float = 0.72
    posterior_predictive_draws: int = 700
    feature_temperature: float = 0.16


IMAGE_QA: list[dict[str, Any]] = []


def prepare_output() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for path in FIG_DIR.glob("*.png"):
        path.unlink()
    IMAGE_QA.clear()


def psd_db_to_factor(db: float) -> float:
    return float(10.0 ** (db / 10.0))


def psd_db_sigma_to_ln_sigma(db_sigma: float) -> float:
    return float(db_sigma * math.log(10.0) / 10.0)


def ln_sigma_to_psd_db_sigma(ln_sigma: np.ndarray | float) -> np.ndarray | float:
    return np.asarray(ln_sigma) * 10.0 / math.log(10.0)


def loglog_interp_psd(freqs_hz: np.ndarray, spec_freqs: np.ndarray, spec_psd: np.ndarray) -> np.ndarray:
    return np.exp(np.interp(np.log(freqs_hz), np.log(spec_freqs), np.log(spec_psd)))


def matern32_corr_logfreq(freqs_hz: np.ndarray, ell: float) -> np.ndarray:
    eta = np.log(freqs_hz)
    r = np.abs(np.subtract.outer(eta, eta)) / ell
    sqrt3_r = math.sqrt(3.0) * r
    return (1.0 + sqrt3_r) * np.exp(-sqrt3_r)


def sample_matern_log_psd_factor(
    rng: np.random.Generator,
    freqs_hz: np.ndarray,
    sigma_db_psd: float,
    ell_logfreq: float,
) -> np.ndarray:
    sigma_ln = psd_db_sigma_to_ln_sigma(sigma_db_psd)
    corr = matern32_corr_logfreq(freqs_hz, ell_logfreq)
    cov = sigma_ln**2 * corr + 1e-12 * np.eye(len(freqs_hz))
    return np.linalg.cholesky(cov) @ rng.normal(size=len(freqs_hz))


def dome_accel_per_force_g(p: Params, c: Constants, freqs_hz: np.ndarray) -> np.ndarray:
    reciprocal = dome_only_reciprocal_inertance(p, c, freqs_hz)
    return (1.0 / reciprocal) / G0_M_PER_S2


def qoi_3grms(freqs_hz: np.ndarray, psd_g2_per_hz: np.ndarray) -> float:
    return 3.0 * grms_from_psd(freqs_hz, psd_g2_per_hz)


def pack_complex(x: np.ndarray) -> dict[str, list[float]]:
    return {"real": x.real.tolist(), "imag": x.imag.tolist()}


def env_status() -> dict[str, Any]:
    packages = {}
    for name in ["numpyro", "jax", "pymc", "arviz", "torch", "numpy", "scipy", "matplotlib"]:
        spec = importlib.util.find_spec(name)
        packages[name] = {"installed": spec is not None, "origin": spec.origin if spec else None}
    return {
        "python_version": platform.python_version(),
        "python_executable": os.environ.get("_", "python3"),
        "packages": packages,
        "numpyro_resolution": (
            "numpyro is not installed. JAX, PyMC, and ArviZ are also absent. "
            "No package installation was attempted. The run uses a labeled custom "
            "PyTorch-autograd fixed-trajectory HMC backend; NUTS is not active."
        ),
    }


def make_build_samples(rng: np.random.Generator, cfg: RunnerConfig, n_builds: int) -> list[dict[str, float]]:
    sigma_ln = psd_db_sigma_to_ln_sigma(cfg.build_sigma_db_psd_truth)
    rows = []
    for build_id in range(n_builds):
        dome = float(rng.normal(0.0, sigma_ln))
        tray = float(rng.normal(0.0, sigma_ln))
        rows.append(
            {
                "build_id": build_id,
                "dome_log_psd_effect": dome,
                "tray_log_psd_effect": tray,
                "dome_effect_db_psd": float(10.0 * dome / math.log(10.0)),
                "tray_effect_db_psd": float(10.0 * tray / math.log(10.0)),
            }
        )
    return rows


def generate_dataset(cfg: RunnerConfig) -> dict[str, Any]:
    rng = np.random.default_rng(RUN_SEED)
    c = Constants()
    truth = true_params(c)
    freqs = np.geomspace(20.0, 2000.0, cfg.n_freq)
    modal_freqs = np.geomspace(20.0, 300.0, cfg.n_modal_freq)
    spec_freqs = np.asarray(cfg.smoothline_freq_hz, dtype=float)
    spec_psd = np.asarray(cfg.smoothline_psd_g2_per_hz, dtype=float)
    smoothline = loglog_interp_psd(freqs, spec_freqs, spec_psd)

    dome_h = dome_accel_per_force_g(truth, c, freqs)
    original_force_psd = np.full_like(freqs, 0.1 / float(np.max(np.abs(dome_h) ** 2)))
    mean_flight_force_psd = original_force_psd * psd_db_to_factor(cfg.flight_mean_force_below_original_db_psd)

    n_builds = 1 + cfg.n_later_builds_and_flights
    build_samples = make_build_samples(rng, cfg, n_builds)
    sensor_sigma_ln = psd_db_sigma_to_ln_sigma(cfg.sensor_sigma_db_psd_truth)

    tray_t = tray_transmissibility(truth, c, freqs)
    vibe_clean = np.abs(tray_t) ** 2 * smoothline
    vibe_tests = []
    for build in build_samples:
        sensor_log = rng.normal(0.0, sensor_sigma_ln, size=len(freqs))
        observed = vibe_clean * np.exp(build["tray_log_psd_effect"] + sensor_log)
        vibe_tests.append(
            {
                "build_id": build["build_id"],
                "clean_psd_g2_per_hz": vibe_clean.tolist(),
                "observed_psd_g2_per_hz": observed.tolist(),
                "sensor_log_psd_effect": sensor_log.tolist(),
                "observed_3grms_g": qoi_3grms(freqs, observed),
            }
        )

    modal_clean = frequency_channels(truth, c, modal_freqs)
    first_build = build_samples[0]
    modal_observations: dict[str, dict[str, Any]] = {}
    modal_channels = {
        "dome_only": ("ch1_dome_only_reciprocal_inertance", "dome_log_psd_effect"),
        "coupled_interface": ("ch2_coupled_primary_reciprocal_inertance", "dome_log_psd_effect"),
        "coupled_tray": ("ch3_coupled_tray_reciprocal_inertance", "tray_log_psd_effect"),
    }
    for name, (channel, build_key) in modal_channels.items():
        sensor_log = rng.normal(0.0, sensor_sigma_ln, size=len(modal_freqs))
        log_psd_effect = first_build[build_key] + sensor_log
        observed = modal_clean[channel] * np.exp(0.5 * log_psd_effect)
        modal_observations[name] = {
            "source_channel": channel,
            "build_id": 0,
            "clean": pack_complex(modal_clean[channel]),
            "observed": pack_complex(observed),
            "sensor_log_psd_effect": sensor_log.tolist(),
        }

    h = accel_over_force(truth, c, freqs) / G0_M_PER_S2
    flight_observations = []
    for flight_id, build in enumerate(build_samples):
        forcing_log = sample_matern_log_psd_factor(
            rng, freqs, cfg.flight_to_flight_sigma_db_psd, cfg.forcing_matern_length_logfreq
        )
        force_psd = mean_flight_force_psd * np.exp(forcing_log)
        tray_clean = np.abs(h[:, 1, 0]) ** 2 * force_psd
        interface_clean = np.abs(h[:, 0, 0]) ** 2 * force_psd
        tray_sensor = rng.normal(0.0, sensor_sigma_ln, size=len(freqs))
        interface_sensor = rng.normal(0.0, sensor_sigma_ln, size=len(freqs))
        tray_observed = tray_clean * np.exp(build["tray_log_psd_effect"] + tray_sensor)
        interface_observed = interface_clean * np.exp(build["dome_log_psd_effect"] + interface_sensor)
        flight_observations.append(
            {
                "flight_id": flight_id,
                "build_id": build["build_id"],
                "force_log_psd_matern_factor": forcing_log.tolist(),
                "force_psd_n2_per_hz": force_psd.tolist(),
                "tray_clean_psd_g2_per_hz": tray_clean.tolist(),
                "tray_observed_psd_g2_per_hz": tray_observed.tolist(),
                "interface_clean_psd_g2_per_hz": interface_clean.tolist(),
                "interface_observed_psd_g2_per_hz": interface_observed.tolist(),
                "tray_sensor_log_psd_effect": tray_sensor.tolist(),
                "interface_sensor_log_psd_effect": interface_sensor.tolist(),
                "tray_3grms_g_observed": qoi_3grms(freqs, tray_observed),
                "interface_3grms_g_observed": qoi_3grms(freqs, interface_observed),
            }
        )

    return {
        "run_seed": RUN_SEED,
        "freqs_hz": freqs.tolist(),
        "modal_freqs_hz": modal_freqs.tolist(),
        "smoothline_psd_g2_per_hz": smoothline.tolist(),
        "original_flat_force_psd_n2_per_hz": original_force_psd.tolist(),
        "mean_flight_force_psd_n2_per_hz": mean_flight_force_psd.tolist(),
        "truth": {
            "k1": truth.k1,
            "k2": truth.k2,
            "zeta1": truth.zeta1,
            "zeta2": truth.zeta2,
            "dome_hz": math.sqrt(truth.k1 / c.m1) / (2.0 * math.pi),
            "tray_hz": math.sqrt(truth.k2 / c.m2) / (2.0 * math.pi),
            "force_global_psd_scale": 1.0,
            "build_sigma_db_psd": cfg.build_sigma_db_psd_truth,
            "sensor_sigma_db_psd": cfg.sensor_sigma_db_psd_truth,
            "flight_to_flight_sigma_db_psd_fixed": cfg.flight_to_flight_sigma_db_psd,
        },
        "constants": {
            "m1_kg": c.m1,
            "m2_kg": c.m2,
            "dome_nominal_hz": c.dome_nominal_hz,
            "tray_nominal_hz": c.tray_nominal_hz,
            "dome_nominal_zeta": c.dome_nominal_zeta,
            "tray_nominal_zeta": c.tray_nominal_zeta,
        },
        "smoothline_points": list(zip(cfg.smoothline_freq_hz, cfg.smoothline_psd_g2_per_hz)),
        "build_samples": build_samples,
        "vibe_tests": vibe_tests,
        "modal_observations": modal_observations,
        "flight_observations": flight_observations,
        "data_count": {
            "tray_vibe_tests": len(vibe_tests),
            "dome_modal_tests": 1,
            "coupled_modal_tests": 1,
            "flights": len(flight_observations),
            "later_builds_and_flights": cfg.n_later_builds_and_flights,
            "frequency_points_per_psd": len(freqs),
            "frequency_points_per_modal_frf": len(modal_freqs),
        },
        "fixed_not_inferred": {
            "flight_to_flight_sigma_db_psd": cfg.flight_to_flight_sigma_db_psd,
            "forcing_covariance": "Matern-3/2 over natural log frequency",
            "forcing_matern_length_logfreq": cfg.forcing_matern_length_logfreq,
            "masses_kg": [c.m1, c.m2],
            "smoothline_psd_points": list(zip(cfg.smoothline_freq_hz, cfg.smoothline_psd_g2_per_hz)),
        },
    }


def torch_interp_const(values: np.ndarray) -> torch.Tensor:
    return torch.tensor(values, dtype=DTYPE)


class TorchSequentialModel:
    def __init__(self, data: dict[str, Any], cfg: RunnerConfig):
        self.data = data
        self.cfg = cfg
        self.c = Constants()
        self.freqs = torch_interp_const(np.asarray(data["freqs_hz"], dtype=float))
        self.modal_freqs = torch_interp_const(np.asarray(data["modal_freqs_hz"], dtype=float))
        self.log_freqs = torch.log(self.freqs)
        self.log_modal_freqs = torch.log(self.modal_freqs)
        self.smoothline = torch_interp_const(np.asarray(data["smoothline_psd_g2_per_hz"], dtype=float))
        self.mean_force = torch_interp_const(np.asarray(data["mean_flight_force_psd_n2_per_hz"], dtype=float))
        self.vibe_obs = [
            torch.log(torch_interp_const(np.asarray(row["observed_psd_g2_per_hz"], dtype=float)))
            for row in data["vibe_tests"]
        ]
        self.flight_tray_obs = [
            torch.log(torch_interp_const(np.asarray(row["tray_observed_psd_g2_per_hz"], dtype=float)))
            for row in data["flight_observations"]
        ]
        self.flight_interface_obs = [
            torch.log(torch_interp_const(np.asarray(row["interface_observed_psd_g2_per_hz"], dtype=float)))
            for row in data["flight_observations"]
        ]
        self.modal_obs = {
            name: torch.log(
                torch.abs(
                    torch.complex(
                        torch_interp_const(np.asarray(row["observed"]["real"], dtype=float)),
                        torch_interp_const(np.asarray(row["observed"]["imag"], dtype=float)),
                    )
                )
                + 1e-18
            )
            for name, row in data["modal_observations"].items()
        }
        self.flight_cov_fixed = torch_interp_const(
            psd_db_sigma_to_ln_sigma(cfg.flight_to_flight_sigma_db_psd) ** 2
            * matern32_corr_logfreq(np.asarray(data["freqs_hz"], dtype=float), cfg.forcing_matern_length_logfreq)
        )
        self.eye_freq = torch.eye(len(self.freqs), dtype=DTYPE)
        self.ones_freq = torch.ones((len(self.freqs), len(self.freqs)), dtype=DTYPE)
        self.eye_modal = torch.eye(len(self.modal_freqs), dtype=DTYPE)
        self.ones_modal = torch.ones((len(self.modal_freqs), len(self.modal_freqs)), dtype=DTYPE)
        self.feature_obs = self._extract_observed_features()

    def physical(self, theta: torch.Tensor) -> dict[str, torch.Tensor]:
        k1 = self.c.k1_nom * torch.exp(theta[0])
        k2 = self.c.k2_nom * torch.exp(theta[1])
        zeta1 = torch.exp(theta[2])
        zeta2 = torch.exp(theta[3])
        c1 = 2.0 * zeta1 * torch.sqrt(k1 * self.c.m1)
        c2 = 2.0 * zeta2 * torch.sqrt(k2 * self.c.m2)
        return {
            "k1": k1,
            "k2": k2,
            "zeta1": zeta1,
            "zeta2": zeta2,
            "c1": c1,
            "c2": c2,
            "force_offset_ln": theta[4],
            "build_sigma_ln": torch.exp(theta[5]),
            "sensor_sigma_ln": torch.exp(theta[6]),
        }

    def accel_components(self, theta: torch.Tensor, freqs: torch.Tensor) -> dict[str, torch.Tensor]:
        p = self.physical(theta)
        w = 2.0 * math.pi * freqs
        iw = 1j * w.to(torch.complex128)
        wc = w.to(torch.complex128)
        k1 = p["k1"].to(torch.complex128)
        k2 = p["k2"].to(torch.complex128)
        c1 = p["c1"].to(torch.complex128)
        c2 = p["c2"].to(torch.complex128)
        a = k1 + k2 + iw * (c1 + c2) - (wc**2) * self.c.m1
        b = -k2 - iw * c2
        d = k2 + iw * c2 - (wc**2) * self.c.m2
        det = a * d - b * b
        inv00 = d / det
        inv11 = a / det
        inv10 = -b / det
        return {
            "h00": -(wc**2) * inv00,
            "h11": -(wc**2) * inv11,
            "h10": -(wc**2) * inv10,
        }

    def log_prediction_curves(self, theta: torch.Tensor) -> dict[str, torch.Tensor]:
        p = self.physical(theta)
        h = self.accel_components(theta, self.freqs)
        hm = self.accel_components(theta, self.modal_freqs)
        w_modal = 2.0 * math.pi * self.modal_freqs
        wc = w_modal.to(torch.complex128)
        iw = 1j * wc
        k1 = p["k1"].to(torch.complex128)
        c1 = p["c1"].to(torch.complex128)
        z = k1 + iw * p["c1"].to(torch.complex128) - (wc**2) * self.c.m1
        dome_a_over_f = -(wc**2) / z
        dome_recip = 1.0 / dome_a_over_f
        k2 = p["k2"].to(torch.complex128)
        c2 = p["c2"].to(torch.complex128)
        w = 2.0 * math.pi * self.freqs
        mount = k2 + 1j * w.to(torch.complex128) * c2
        tray_t = mount / (mount - self.c.m2 * (w.to(torch.complex128) ** 2))
        eps = 1e-30
        return {
            "vibe_tray_log_psd": torch.log(torch.abs(tray_t) ** 2 + eps) + torch.log(self.smoothline),
            "modal_dome_only_log_abs": torch.log(torch.abs(dome_recip) + eps),
            "modal_coupled_interface_log_abs": torch.log(torch.abs(1.0 / hm["h00"]) + eps),
            "modal_coupled_tray_log_abs": torch.log(torch.abs(1.0 / hm["h11"]) + eps),
            "flight_tray_log_psd": torch.log(torch.abs(h["h10"] / G0_M_PER_S2) ** 2 + eps)
            + torch.log(self.mean_force)
            + p["force_offset_ln"],
            "flight_interface_log_psd": torch.log(torch.abs(h["h00"] / G0_M_PER_S2) ** 2 + eps)
            + torch.log(self.mean_force)
            + p["force_offset_ln"],
        }

    def log_prior(self, theta: torch.Tensor) -> torch.Tensor:
        cfg = self.cfg
        c = self.c
        means = torch.tensor(
            [
                0.0,
                0.0,
                math.log(c.dome_nominal_zeta),
                math.log(c.tray_nominal_zeta),
                0.0,
                math.log(psd_db_sigma_to_ln_sigma(cfg.build_sigma_db_psd_truth)),
                math.log(psd_db_sigma_to_ln_sigma(cfg.sensor_sigma_db_psd_truth)),
            ],
            dtype=DTYPE,
        )
        sigmas = torch.tensor(
            [
                0.18,
                0.18,
                0.35,
                0.35,
                psd_db_sigma_to_ln_sigma(1.5),
                0.55,
                0.55,
            ],
            dtype=DTYPE,
        )
        z = (theta - means) / sigmas
        lp = -0.5 * torch.sum(z * z + torch.log(2.0 * math.pi * sigmas * sigmas))
        phys = self.physical(theta)
        # Soft physical guardrails. These keep HMC away from numerical nonsense without
        # presenting a hard checker as physics validation.
        bad = (
            (phys["zeta1"] < 0.002)
            | (phys["zeta1"] > 0.12)
            | (phys["zeta2"] < 0.002)
            | (phys["zeta2"] > 0.12)
            | (phys["build_sigma_ln"] > 2.5)
            | (phys["sensor_sigma_ln"] > 2.5)
        )
        return torch.where(bad, torch.tensor(-1e12, dtype=DTYPE), lp)

    @staticmethod
    def mvn_logpdf(resid: torch.Tensor, cov: torch.Tensor) -> torch.Tensor:
        jitter = 1e-9 * torch.eye(cov.shape[0], dtype=DTYPE)
        chol = torch.linalg.cholesky(cov + jitter)
        sol = torch.cholesky_solve(resid[:, None], chol)[:, 0]
        quad = torch.dot(resid, sol)
        logdet = 2.0 * torch.sum(torch.log(torch.diag(chol)))
        n = resid.numel()
        return -0.5 * (quad + logdet + n * math.log(2.0 * math.pi))

    def full_log_prob(self, theta: torch.Tensor) -> torch.Tensor:
        p = self.physical(theta)
        pred = self.log_prediction_curves(theta)
        build = p["build_sigma_ln"]
        sensor = p["sensor_sigma_ln"]
        cov_freq = build**2 * self.ones_freq + sensor**2 * self.eye_freq
        cov_modal = 0.25 * build**2 * self.ones_modal + 0.25 * sensor**2 * self.eye_modal
        cov_flight = self.flight_cov_fixed + build**2 * self.ones_freq + sensor**2 * self.eye_freq

        lp = self.log_prior(theta)
        for obs in self.vibe_obs:
            lp = lp + self.mvn_logpdf(obs - pred["vibe_tray_log_psd"], cov_freq)
        lp = lp + self.mvn_logpdf(
            self.modal_obs["dome_only"] - pred["modal_dome_only_log_abs"], cov_modal
        )
        lp = lp + self.mvn_logpdf(
            self.modal_obs["coupled_interface"] - pred["modal_coupled_interface_log_abs"], cov_modal
        )
        lp = lp + self.mvn_logpdf(
            self.modal_obs["coupled_tray"] - pred["modal_coupled_tray_log_abs"], cov_modal
        )
        for tray, interface in zip(self.flight_tray_obs, self.flight_interface_obs):
            lp = lp + self.mvn_logpdf(tray - pred["flight_tray_log_psd"], cov_flight)
            lp = lp + self.mvn_logpdf(interface - pred["flight_interface_log_psd"], cov_flight)
        return lp

    def _hard_feature(self, values: np.ndarray, freqs: np.ndarray, kind: str) -> dict[str, float]:
        if kind == "peak":
            idx = int(np.argmax(values))
        elif kind == "notch":
            idx = int(np.argmin(values))
        else:
            raise ValueError(kind)
        return {"logfreq": float(np.log(freqs[idx])), "logvalue": float(values[idx]), "index": idx}

    def _extract_observed_features(self) -> list[dict[str, Any]]:
        freqs = np.asarray(self.data["freqs_hz"], dtype=float)
        modal_freqs = np.asarray(self.data["modal_freqs_hz"], dtype=float)
        rows: list[dict[str, Any]] = []
        for row in self.data["vibe_tests"]:
            y = np.log(np.asarray(row["observed_psd_g2_per_hz"], dtype=float))
            feat = self._hard_feature(y, freqs, "peak")
            rows.append({"family": "vibe_tray", "kind": "peak", "build_id": row["build_id"], **feat})
        modal_map = {
            "dome_only": "modal_dome_only",
            "coupled_interface": "modal_coupled_interface",
            "coupled_tray": "modal_coupled_tray",
        }
        for name, family in modal_map.items():
            raw = self.data["modal_observations"][name]["observed"]
            y = np.log(np.abs(np.asarray(raw["real"]) + 1j * np.asarray(raw["imag"])) + 1e-18)
            feat = self._hard_feature(y, modal_freqs, "notch")
            rows.append({"family": family, "kind": "notch", "build_id": 0, **feat})
        for row in self.data["flight_observations"]:
            tray = np.log(np.asarray(row["tray_observed_psd_g2_per_hz"], dtype=float))
            interface = np.log(np.asarray(row["interface_observed_psd_g2_per_hz"], dtype=float))
            rows.append(
                {
                    "family": "flight_tray",
                    "kind": "peak",
                    "flight_id": row["flight_id"],
                    "build_id": row["build_id"],
                    **self._hard_feature(tray, freqs, "peak"),
                }
            )
            rows.append(
                {
                    "family": "flight_interface",
                    "kind": "peak",
                    "flight_id": row["flight_id"],
                    "build_id": row["build_id"],
                    **self._hard_feature(interface, freqs, "peak"),
                }
            )
        return rows

    def soft_feature(self, log_values: torch.Tensor, log_freqs: torch.Tensor, kind: str) -> tuple[torch.Tensor, torch.Tensor]:
        sign = 1.0 if kind == "peak" else -1.0
        scaled = sign * (log_values - torch.mean(log_values)) / self.cfg.feature_temperature
        weights = torch.softmax(scaled, dim=0)
        return torch.sum(weights * log_freqs), torch.sum(weights * log_values)

    def feature_log_prob(self, theta: torch.Tensor) -> torch.Tensor:
        p = self.physical(theta)
        pred = self.log_prediction_curves(theta)
        amp_sigma_vibe = torch.sqrt(p["build_sigma_ln"] ** 2 + p["sensor_sigma_ln"] ** 2 + 0.03**2)
        amp_sigma_modal = torch.sqrt(0.25 * p["build_sigma_ln"] ** 2 + 0.25 * p["sensor_sigma_ln"] ** 2 + 0.02**2)
        amp_sigma_flight = torch.sqrt(
            p["build_sigma_ln"] ** 2
            + p["sensor_sigma_ln"] ** 2
            + psd_db_sigma_to_ln_sigma(self.cfg.flight_to_flight_sigma_db_psd) ** 2
            + 0.03**2
        )
        family_curve = {
            "vibe_tray": (pred["vibe_tray_log_psd"], self.log_freqs, amp_sigma_vibe, 0.055),
            "modal_dome_only": (pred["modal_dome_only_log_abs"], self.log_modal_freqs, amp_sigma_modal, 0.035),
            "modal_coupled_interface": (
                pred["modal_coupled_interface_log_abs"],
                self.log_modal_freqs,
                amp_sigma_modal,
                0.035,
            ),
            "modal_coupled_tray": (pred["modal_coupled_tray_log_abs"], self.log_modal_freqs, amp_sigma_modal, 0.035),
            "flight_tray": (pred["flight_tray_log_psd"], self.log_freqs, amp_sigma_flight, 0.075),
            "flight_interface": (pred["flight_interface_log_psd"], self.log_freqs, amp_sigma_flight, 0.075),
        }
        lp = self.log_prior(theta)
        for row in self.feature_obs:
            curve, log_freqs, amp_sigma, freq_sigma = family_curve[row["family"]]
            pred_logfreq, pred_logvalue = self.soft_feature(curve, log_freqs, row["kind"])
            obs_logfreq = torch.tensor(row["logfreq"], dtype=DTYPE)
            obs_logvalue = torch.tensor(row["logvalue"], dtype=DTYPE)
            freq_sigma_t = torch.tensor(freq_sigma, dtype=DTYPE)
            lp = lp - 0.5 * (
                ((obs_logfreq - pred_logfreq) / freq_sigma_t) ** 2
                + torch.log(2.0 * math.pi * freq_sigma_t * freq_sigma_t)
            )
            lp = lp - 0.5 * (
                ((obs_logvalue - pred_logvalue) / amp_sigma) ** 2
                + torch.log(2.0 * math.pi * amp_sigma * amp_sigma)
            )
        return lp


def value_and_grad(log_prob_fn: Callable[[torch.Tensor], torch.Tensor], theta: torch.Tensor) -> tuple[float, torch.Tensor]:
    x = theta.detach().clone().requires_grad_(True)
    lp = log_prob_fn(x)
    if not torch.isfinite(lp):
        return -math.inf, torch.zeros_like(theta)
    lp.backward()
    grad = x.grad.detach().clone()
    return float(lp.detach()), grad


def hmc_chain(
    log_prob_fn: Callable[[torch.Tensor], torch.Tensor],
    initial: np.ndarray,
    seed: int,
    warmup: int,
    samples: int,
    step_size: float,
    leapfrog_steps: int,
    target_accept: float,
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    theta = torch.tensor(initial, dtype=DTYPE)
    cur_lp, cur_grad = value_and_grad(log_prob_fn, theta)
    total = warmup + samples
    draws = []
    logps = []
    accept_probs = []
    accepted = []
    energy_errors = []
    step = float(step_size)
    divergences = 0
    final_step_history = []

    for i in range(total):
        momentum = torch.tensor(rng.normal(size=len(initial)), dtype=DTYPE)
        start_theta = theta.detach().clone()
        start_momentum = momentum.detach().clone()
        start_lp = cur_lp
        start_energy = -cur_lp + 0.5 * float(torch.dot(momentum, momentum))

        prop_theta = theta.detach().clone()
        prop_momentum = momentum + 0.5 * step * cur_grad
        prop_lp = cur_lp
        prop_grad = cur_grad
        diverged = False
        for lf in range(leapfrog_steps):
            prop_theta = prop_theta + step * prop_momentum
            prop_lp, prop_grad = value_and_grad(log_prob_fn, prop_theta)
            if not math.isfinite(prop_lp) or not torch.all(torch.isfinite(prop_grad)):
                diverged = True
                break
            if lf != leapfrog_steps - 1:
                prop_momentum = prop_momentum + step * prop_grad
        if not diverged:
            prop_momentum = prop_momentum + 0.5 * step * prop_grad
            prop_momentum = -prop_momentum
            prop_energy = -prop_lp + 0.5 * float(torch.dot(prop_momentum, prop_momentum))
            energy_error = prop_energy - start_energy
            if not math.isfinite(energy_error) or abs(energy_error) > 100.0:
                diverged = True
        else:
            energy_error = math.inf

        if diverged:
            accept_prob = 0.0
            divergences += 1
            is_accepted = False
            theta = start_theta
            cur_lp = start_lp
            cur_grad = value_and_grad(log_prob_fn, theta)[1]
        else:
            accept_prob = min(1.0, math.exp(-energy_error))
            is_accepted = bool(rng.uniform() < accept_prob)
            if is_accepted:
                theta = prop_theta.detach().clone()
                cur_lp = prop_lp
                cur_grad = prop_grad.detach().clone()
            else:
                theta = start_theta
                cur_lp = start_lp
                cur_grad = value_and_grad(log_prob_fn, theta)[1]

        if i < warmup:
            adapt_gain = 0.05 / math.sqrt(i + 1.0)
            step *= math.exp(adapt_gain * (accept_prob - target_accept))
            step = float(np.clip(step, 1e-5, 0.05))
            if (i + 1) % 20 == 0:
                final_step_history.append({"warmup_step": i + 1, "step_size": step, "accept_prob": accept_prob})
        else:
            draws.append(theta.detach().numpy().copy())
            logps.append(cur_lp)
            accept_probs.append(accept_prob)
            accepted.append(is_accepted)
            energy_errors.append(energy_error)

    return {
        "samples": np.asarray(draws, dtype=float),
        "log_prob": np.asarray(logps, dtype=float),
        "accept_probs": np.asarray(accept_probs, dtype=float),
        "accepted": np.asarray(accepted, dtype=bool),
        "energy_errors": np.asarray(energy_errors, dtype=float),
        "divergences": divergences,
        "final_step_size": step,
        "warmup_step_history": final_step_history,
    }


def run_hmc(
    model: TorchSequentialModel,
    mode: str,
    initial: np.ndarray,
    cfg: RunnerConfig,
) -> dict[str, Any]:
    log_prob_fn = model.full_log_prob if mode == "full" else model.feature_log_prob
    step = cfg.hmc_initial_step_size_full if mode == "full" else cfg.hmc_initial_step_size_feature
    chains = []
    for chain_id in range(cfg.hmc_chains):
        init = initial + np.random.default_rng(RUN_SEED + 1000 + chain_id).normal(0.0, 0.015, size=len(initial))
        chains.append(
            hmc_chain(
                log_prob_fn,
                init,
                seed=RUN_SEED + (17 if mode == "full" else 117) + chain_id,
                warmup=cfg.hmc_warmup,
                samples=cfg.hmc_samples,
                step_size=step,
                leapfrog_steps=cfg.hmc_leapfrog_steps,
                target_accept=cfg.hmc_target_accept,
            )
        )
    samples = np.stack([c["samples"] for c in chains], axis=0)
    return {
        "mode": mode,
        "chains": chains,
        "samples": samples,
        "diagnostics": summarize_diagnostics(samples, chains, cfg),
    }


def autocorr_1d(x: np.ndarray, max_lag: int) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    x = x - np.mean(x)
    denom = np.dot(x, x)
    if denom <= 0:
        return np.zeros(max_lag + 1)
    out = [1.0]
    for lag in range(1, max_lag + 1):
        out.append(float(np.dot(x[:-lag], x[lag:]) / denom))
    return np.asarray(out)


def ess_per_param(chains: np.ndarray) -> np.ndarray:
    c, n, d = chains.shape
    out = np.zeros(d)
    for j in range(d):
        rhos = []
        max_lag = min(n - 1, 80)
        for chain_id in range(c):
            rhos.append(autocorr_1d(chains[chain_id, :, j], max_lag))
        rho = np.mean(rhos, axis=0)
        positive_sum = 0.0
        for lag in range(1, len(rho)):
            if rho[lag] <= 0:
                break
            positive_sum += rho[lag]
        out[j] = c * n / max(1.0 + 2.0 * positive_sum, 1e-12)
    return out


def rhat_per_param(chains: np.ndarray) -> np.ndarray:
    c, n, d = chains.shape
    means = np.mean(chains, axis=1)
    variances = np.var(chains, axis=1, ddof=1)
    w = np.mean(variances, axis=0)
    b = n * np.var(means, axis=0, ddof=1)
    var_hat = ((n - 1.0) / n) * w + b / n
    return np.sqrt(np.maximum(var_hat / np.maximum(w, 1e-30), 0.0))


def summarize_diagnostics(samples: np.ndarray, chains: list[dict[str, Any]], cfg: RunnerConfig) -> dict[str, Any]:
    names = PARAM_NAMES
    ess = ess_per_param(samples)
    rhat = rhat_per_param(samples)
    accept = [float(np.mean(c["accept_probs"])) for c in chains]
    return {
        "sampler": "custom PyTorch fixed-trajectory HMC",
        "nuts_active": False,
        "hmc_active": True,
        "tree_depth": {
            "status": "not_applicable_fixed_trajectory_hmc",
            "max_tree_depth": None,
            "fixed_leapfrog_steps": cfg.hmc_leapfrog_steps,
        },
        "warmup_draws_per_chain": cfg.hmc_warmup,
        "posterior_draws_per_chain": cfg.hmc_samples,
        "chains": cfg.hmc_chains,
        "divergences": int(sum(c["divergences"] for c in chains)),
        "step_size_final_by_chain": [float(c["final_step_size"]) for c in chains],
        "acceptance_rate_by_chain": accept,
        "mean_acceptance_rate": float(np.mean(accept)),
        "max_abs_energy_error_by_chain": [
            float(np.nanmax(np.abs(c["energy_errors"]))) if len(c["energy_errors"]) else None for c in chains
        ],
        "ess_bulk_approx": {name: float(value) for name, value in zip(names, ess)},
        "r_hat": {name: float(value) for name, value in zip(names, rhat)},
        "diagnostic_limitations": [
            "ESS is an autocorrelation-based approximation implemented locally, not ArviZ bulk/tail ESS.",
            "R-hat is classical split-free chain R-hat. Tail R-hat is not computed.",
            "Tree depth is not applicable because this is fixed-trajectory HMC, not NUTS.",
        ],
    }


PARAM_NAMES = [
    "log_k1_rel",
    "log_k2_rel",
    "log_zeta1",
    "log_zeta2",
    "flight_force_offset_ln_psd",
    "log_build_sigma_ln_psd",
    "log_sensor_sigma_ln_psd",
]


def transform_samples(samples: np.ndarray, c: Constants) -> dict[str, np.ndarray]:
    flat = samples.reshape((-1, samples.shape[-1]))
    k1 = c.k1_nom * np.exp(flat[:, 0])
    k2 = c.k2_nom * np.exp(flat[:, 1])
    zeta1 = np.exp(flat[:, 2])
    zeta2 = np.exp(flat[:, 3])
    return {
        "k1": k1,
        "k2": k2,
        "dome_hz": np.sqrt(k1 / c.m1) / (2.0 * math.pi),
        "tray_hz": np.sqrt(k2 / c.m2) / (2.0 * math.pi),
        "zeta1": zeta1,
        "zeta2": zeta2,
        "flight_force_offset_db_psd": flat[:, 4] * 10.0 / math.log(10.0),
        "build_sigma_db_psd": ln_sigma_to_psd_db_sigma(np.exp(flat[:, 5])),
        "sensor_sigma_db_psd": ln_sigma_to_psd_db_sigma(np.exp(flat[:, 6])),
        "build_sigma_ln_psd": np.exp(flat[:, 5]),
        "sensor_sigma_ln_psd": np.exp(flat[:, 6]),
        "raw": flat,
    }


def posterior_summary(samples: np.ndarray, qoi: dict[str, np.ndarray], c: Constants) -> dict[str, Any]:
    phys = transform_samples(samples, c)
    names = [
        "dome_hz",
        "tray_hz",
        "zeta1",
        "zeta2",
        "flight_force_offset_db_psd",
        "build_sigma_db_psd",
        "sensor_sigma_db_psd",
    ]
    out = {}
    for name in names:
        arr = np.asarray(phys[name], dtype=float)
        out[name] = {
            "mean": float(np.mean(arr)),
            "sd": float(np.std(arr, ddof=1)),
            "q025": float(np.quantile(arr, 0.025)),
            "q975": float(np.quantile(arr, 0.975)),
            "q005": float(np.quantile(arr, 0.005)),
            "q995": float(np.quantile(arr, 0.995)),
        }
    for name, arr in qoi.items():
        arr = np.asarray(arr, dtype=float)
        out[name] = {
            "mean": float(np.mean(arr)),
            "sd": float(np.std(arr, ddof=1)),
            "q025": float(np.quantile(arr, 0.025)),
            "q975": float(np.quantile(arr, 0.975)),
            "q005": float(np.quantile(arr, 0.005)),
            "q995": float(np.quantile(arr, 0.995)),
        }
    return out


def numpy_accel_components(theta_row: np.ndarray, freqs: np.ndarray, c: Constants) -> dict[str, np.ndarray]:
    k1 = c.k1_nom * math.exp(theta_row[0])
    k2 = c.k2_nom * math.exp(theta_row[1])
    zeta1 = math.exp(theta_row[2])
    zeta2 = math.exp(theta_row[3])
    p = Params(k1=k1, k2=k2, zeta1=zeta1, zeta2=zeta2, force_amp=1.0, force_fc=95.0)
    h = accel_over_force(p, c, freqs) / G0_M_PER_S2
    return {"h00": h[:, 0, 0], "h10": h[:, 1, 0]}


def posterior_predictive_qoi(
    data: dict[str, Any], samples: np.ndarray, cfg: RunnerConfig, seed: int
) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    c = Constants()
    freqs = np.asarray(data["freqs_hz"], dtype=float)
    mean_force = np.asarray(data["mean_flight_force_psd_n2_per_hz"], dtype=float)
    flat = samples.reshape((-1, samples.shape[-1]))
    n_draws = min(cfg.posterior_predictive_draws, len(flat))
    idx = rng.choice(len(flat), size=n_draws, replace=len(flat) < n_draws)
    force_draws = []
    tray_qoi = []
    interface_qoi = []
    tray_psd_draws = []
    for i in idx:
        theta = flat[i]
        h = numpy_accel_components(theta, freqs, c)
        force_log = sample_matern_log_psd_factor(
            rng, freqs, cfg.flight_to_flight_sigma_db_psd, cfg.forcing_matern_length_logfreq
        )
        build_log = rng.normal(0.0, math.exp(theta[5]))
        force_psd = mean_force * math.exp(theta[4]) * np.exp(force_log)
        tray_psd = np.abs(h["h10"]) ** 2 * force_psd * math.exp(build_log)
        interface_psd = np.abs(h["h00"]) ** 2 * force_psd * math.exp(build_log)
        force_draws.append(force_psd)
        tray_psd_draws.append(tray_psd)
        tray_qoi.append(qoi_3grms(freqs, tray_psd))
        interface_qoi.append(qoi_3grms(freqs, interface_psd))
    force_arr = np.asarray(force_draws)
    tray_arr = np.asarray(tray_psd_draws)
    return {
        "input_force_psd_n2_per_hz": {
            "q005": np.quantile(force_arr, 0.005, axis=0),
            "q025": np.quantile(force_arr, 0.025, axis=0),
            "q500": np.quantile(force_arr, 0.5, axis=0),
            "q975": np.quantile(force_arr, 0.975, axis=0),
            "q995": np.quantile(force_arr, 0.995, axis=0),
        },
        "tray_psd_g2_per_hz": {
            "q025": np.quantile(tray_arr, 0.025, axis=0),
            "q500": np.quantile(tray_arr, 0.5, axis=0),
            "q975": np.quantile(tray_arr, 0.975, axis=0),
        },
        "tray_3grms_g": np.asarray(tray_qoi),
        "tray_3rms_g": np.asarray(tray_qoi),
        "interface_3grms_g": np.asarray(interface_qoi),
        "posterior_predictive_draws": n_draws,
        "includes": [
            "posterior structural/forcing-scale uncertainty",
            "learned build-to-build variability",
            "fixed known 3 dB flight-to-flight Matern forcing variability",
        ],
        "excludes": ["sensor noise in design QOI intervals"],
    }


def feature_map_for_theta(model: TorchSequentialModel, theta: np.ndarray) -> np.ndarray:
    x = torch.tensor(theta, dtype=DTYPE)
    pred = model.log_prediction_curves(x)
    families = [
        ("vibe_tray", pred["vibe_tray_log_psd"], model.log_freqs, "peak"),
        ("modal_dome_only", pred["modal_dome_only_log_abs"], model.log_modal_freqs, "notch"),
        ("modal_coupled_interface", pred["modal_coupled_interface_log_abs"], model.log_modal_freqs, "notch"),
        ("modal_coupled_tray", pred["modal_coupled_tray_log_abs"], model.log_modal_freqs, "notch"),
        ("flight_tray", pred["flight_tray_log_psd"], model.log_freqs, "peak"),
        ("flight_interface", pred["flight_interface_log_psd"], model.log_freqs, "peak"),
    ]
    out = []
    for _, curve, logfreq, kind in families:
        lf, lv = model.soft_feature(curve, logfreq, kind)
        out.extend([float(lf.detach()), float(lv.detach())])
    return np.asarray(out, dtype=float)


def feature_sensitivity(model: TorchSequentialModel, center: np.ndarray) -> dict[str, Any]:
    names = [
        "vibe peak logfreq",
        "vibe peak logPSD",
        "dome modal notch logfreq",
        "dome modal notch log|FRF|",
        "coupled interface notch logfreq",
        "coupled interface notch log|FRF|",
        "coupled tray notch logfreq",
        "coupled tray notch log|FRF|",
        "flight tray peak logfreq",
        "flight tray peak logPSD",
        "flight interface peak logfreq",
        "flight interface peak logPSD",
    ]
    base = feature_map_for_theta(model, center)
    sens = np.zeros((len(base), 5), dtype=float)
    steps = np.array([0.02, 0.02, 0.02, 0.02, 0.02])
    for j in range(5):
        plus = center.copy()
        minus = center.copy()
        plus[j] += steps[j]
        minus[j] -= steps[j]
        sens[:, j] = (feature_map_for_theta(model, plus) - feature_map_for_theta(model, minus)) / (2.0 * steps[j])
    return {
        "feature_names": names,
        "parameter_names": PARAM_NAMES[:5],
        "center": center.tolist(),
        "sensitivity_matrix": sens.tolist(),
        "note": "Predicted features are soft peak/notch transfer-function features from the forward model, not natural frequencies.",
    }


def savefig(fig: plt.Figure, filename: str, *, text_heavy: bool = False, min_font_pt: float = 7.0) -> None:
    path = FIG_DIR / filename
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_bbox = fig.bbox
    texts = [t for t in fig.findobj(match=matplotlib.text.Text) if t.get_visible() and t.get_text().strip()]
    fonts = [float(t.get_fontsize()) for t in texts]
    clipped = []
    for text in texts:
        bbox = text.get_window_extent(renderer=renderer)
        if bbox.x0 < fig_bbox.x0 - 5 or bbox.y0 < fig_bbox.y0 - 5 or bbox.x1 > fig_bbox.x1 + 5 or bbox.y1 > fig_bbox.y1 + 5:
            clipped.append(text.get_text()[:80])
    fig.savefig(path, dpi=170)
    with Image.open(path) as image:
        width, height = image.size
    issues = []
    if width < 950 or height < 520:
        issues.append(f"image too small: {width}x{height}")
    if fonts and min(fonts) < min_font_pt:
        issues.append(f"minimum font {min(fonts):.1f} pt below {min_font_pt:.1f} pt")
    if clipped and text_heavy:
        issues.append(f"{len(clipped)} clipped text labels")
    IMAGE_QA.append(
        {
            "figure": f"figures/{filename}",
            "width_px": width,
            "height_px": height,
            "text_count": len(texts),
            "min_font_pt_observed": min(fonts) if fonts else None,
            "text_heavy": text_heavy,
            "clipped_examples": clipped[:4],
            "issues": issues,
            "pass": not issues,
        }
    )
    plt.close(fig)


def plot_observations(data: dict[str, Any]) -> None:
    freqs = np.asarray(data["freqs_hz"], dtype=float)
    modal_freqs = np.asarray(data["modal_freqs_hz"], dtype=float)
    fig, axes = plt.subplots(2, 2, figsize=(13.2, 9.0))
    axes[0, 0].loglog(freqs, data["smoothline_psd_g2_per_hz"], lw=2.0, label="smoothline input")
    axes[0, 0].loglog(freqs, data["vibe_tests"][0]["clean_psd_g2_per_hz"], lw=1.8, label="clean tray response")
    axes[0, 0].scatter(freqs, data["vibe_tests"][0]["observed_psd_g2_per_hz"], s=16, alpha=0.75, label="first build observed")
    axes[0, 0].set_title("Tray vibe test")
    axes[0, 0].set_xlabel("frequency [Hz]")
    axes[0, 0].set_ylabel("PSD [g^2/Hz]")
    axes[0, 0].grid(True, which="both", alpha=0.25)
    axes[0, 0].legend(fontsize=8)

    dome_obs = data["modal_observations"]["dome_only"]["observed"]
    ci_obs = data["modal_observations"]["coupled_interface"]["observed"]
    ct_obs = data["modal_observations"]["coupled_tray"]["observed"]
    axes[0, 1].semilogx(modal_freqs, np.abs(np.asarray(dome_obs["real"]) + 1j * np.asarray(dome_obs["imag"])), label="dome only")
    axes[0, 1].semilogx(modal_freqs, np.abs(np.asarray(ci_obs["real"]) + 1j * np.asarray(ci_obs["imag"])), label="coupled interface")
    axes[0, 1].semilogx(modal_freqs, np.abs(np.asarray(ct_obs["real"]) + 1j * np.asarray(ct_obs["imag"])), label="coupled tray")
    axes[0, 1].set_title("Modal FRF observations")
    axes[0, 1].set_xlabel("frequency [Hz]")
    axes[0, 1].set_ylabel("|F/a| [kg]")
    axes[0, 1].grid(True, which="both", alpha=0.25)
    axes[0, 1].legend(fontsize=8)

    first = data["flight_observations"][0]
    axes[1, 0].loglog(freqs, first["force_psd_n2_per_hz"], lw=1.8, label="sampled input force PSD")
    ax2 = axes[1, 0].twinx()
    ax2.loglog(freqs, first["tray_observed_psd_g2_per_hz"], color="#d62728", lw=1.5, label="tray observed PSD")
    axes[1, 0].set_title("First flight input and tray response")
    axes[1, 0].set_xlabel("frequency [Hz]")
    axes[1, 0].set_ylabel("force PSD [N^2/Hz]")
    ax2.set_ylabel("tray PSD [g^2/Hz]")
    axes[1, 0].grid(True, which="both", alpha=0.25)

    flight_ids = [row["flight_id"] for row in data["flight_observations"]]
    tray_qoi = [row["tray_3grms_g_observed"] for row in data["flight_observations"]]
    interface_qoi = [row["interface_3grms_g_observed"] for row in data["flight_observations"]]
    axes[1, 1].plot(flight_ids, tray_qoi, "o-", label="tray")
    axes[1, 1].plot(flight_ids, interface_qoi, "s-", label="interface")
    axes[1, 1].set_title("Observed flight 3*GRMS sequence")
    axes[1, 1].set_xlabel("flight id")
    axes[1, 1].set_ylabel("3*GRMS [g]")
    axes[1, 1].grid(True, alpha=0.25)
    axes[1, 1].legend(fontsize=8)
    fig.tight_layout()
    savefig(fig, "sequential_observations_truth_vs_observed.png")


def plot_absolute_error(data: dict[str, Any]) -> None:
    freqs = np.asarray(data["freqs_hz"], dtype=float)
    vibe = data["vibe_tests"][0]
    clean = np.asarray(vibe["clean_psd_g2_per_hz"], dtype=float)
    obs = np.asarray(vibe["observed_psd_g2_per_hz"], dtype=float)
    flight = data["flight_observations"][0]
    fclean = np.asarray(flight["tray_clean_psd_g2_per_hz"], dtype=float)
    fobs = np.asarray(flight["tray_observed_psd_g2_per_hz"], dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 4.9))
    axes[0].semilogx(freqs, obs - clean, label="absolute PSD error")
    axes[0].semilogx(freqs, (obs - clean) / np.maximum(clean, 1e-18), label="normalized diagnostic")
    axes[0].set_title("Tray vibe injected error")
    axes[0].set_xlabel("frequency [Hz]")
    axes[0].set_ylabel("error")
    axes[0].grid(True, which="both", alpha=0.25)
    axes[0].legend(fontsize=8)
    axes[1].semilogx(freqs, fobs - fclean, label="absolute PSD error")
    axes[1].semilogx(freqs, (fobs - fclean) / np.maximum(fclean, 1e-18), label="normalized diagnostic")
    axes[1].set_title("First-flight tray injected error")
    axes[1].set_xlabel("frequency [Hz]")
    axes[1].grid(True, which="both", alpha=0.25)
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    savefig(fig, "absolute_error_and_normalized_diagnostics.png")


def plot_posteriors(full: np.ndarray, peak: np.ndarray, c: Constants) -> None:
    full_phys = transform_samples(full, c)
    peak_phys = transform_samples(peak, c)
    rows = [
        ("dome_hz", "dome frequency [Hz]"),
        ("tray_hz", "tray frequency [Hz]"),
        ("zeta1", "dome damping ratio"),
        ("zeta2", "tray damping ratio"),
        ("build_sigma_db_psd", "build sigma [dB PSD]"),
        ("sensor_sigma_db_psd", "sensor sigma [dB PSD]"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(13.5, 7.4))
    for ax, (name, label) in zip(axes.flat, rows):
        ax.hist(full_phys[name], bins=28, alpha=0.55, density=True, label="full")
        ax.hist(peak_phys[name], bins=28, alpha=0.45, density=True, label="peak-feature")
        ax.set_title(label)
        ax.grid(True, alpha=0.2)
    axes.flat[0].legend(fontsize=8)
    fig.tight_layout()
    savefig(fig, "posterior_full_vs_peak_parameters.png")


def plot_qoi_and_input(
    data: dict[str, Any],
    full_pred: dict[str, Any],
    peak_pred: dict[str, Any],
    full_qoi: dict[str, np.ndarray],
    peak_qoi: dict[str, np.ndarray],
) -> None:
    freqs = np.asarray(data["freqs_hz"], dtype=float)
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.3))
    for pred, color, label in [(full_pred, "#1f77b4", "full"), (peak_pred, "#d62728", "peak-feature")]:
        force = pred["input_force_psd_n2_per_hz"]
        axes[0].loglog(freqs, force["q500"], color=color, lw=2.0, label=f"{label} median")
        axes[0].fill_between(freqs, force["q025"], force["q975"], color=color, alpha=0.18, label=f"{label} 95%")
        axes[0].fill_between(freqs, force["q005"], force["q995"], color=color, alpha=0.10, label=f"{label} 99%")
    axes[0].set_title("Input force PSD intervals after flights")
    axes[0].set_xlabel("frequency [Hz]")
    axes[0].set_ylabel("force PSD [N^2/Hz]")
    axes[0].grid(True, which="both", alpha=0.25)
    axes[0].legend(fontsize=8)

    axes[1].hist(full_qoi["tray_3grms_g"], bins=32, alpha=0.58, label="full")
    axes[1].hist(peak_qoi["tray_3grms_g"], bins=32, alpha=0.48, label="peak-feature")
    axes[1].set_title("Tray QOI posterior predictive")
    axes[1].set_xlabel("tray 3*GRMS [g]; 3*RMS is equivalent here")
    axes[1].set_ylabel("draw count")
    axes[1].grid(True, alpha=0.25)
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    savefig(fig, "input_spectra_and_tray_qoi_intervals_after_flights.png")


def plot_qoi_widths(summary: dict[str, Any]) -> None:
    ratios = summary["likelihood_comparison"]["interval_width_ratio_peak_over_full"]
    labels = list(ratios.keys())
    vals = [ratios[k] for k in labels]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.bar(labels, vals, color="#9467bd")
    ax.axhline(1.0, color="#333333", lw=1.2)
    ax.set_ylabel("95% interval width ratio")
    ax.set_title("Peak-feature posterior width divided by full-data width")
    ax.tick_params(axis="x", rotation=25)
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    savefig(fig, "full_vs_peak_likelihood_qoi_differences.png")


def plot_diagnostics(full_run: dict[str, Any], peak_run: dict[str, Any]) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13.0, 7.8))
    for ax, run, title in [(axes[0, 0], full_run, "Full-data HMC traces"), (axes[0, 1], peak_run, "Peak-feature HMC traces")]:
        samples = run["samples"]
        for chain_id in range(samples.shape[0]):
            ax.plot(samples[chain_id, :, 0], alpha=0.8, lw=1.0, label=f"chain {chain_id}" if chain_id < 2 else None)
        ax.set_title(title)
        ax.set_xlabel("draw")
        ax.set_ylabel("log_k1_rel")
        ax.grid(True, alpha=0.25)
        ax.legend(fontsize=8)
    for ax, run, title in [(axes[1, 0], full_run, "Full accept probability"), (axes[1, 1], peak_run, "Peak accept probability")]:
        for chain_id, chain in enumerate(run["chains"]):
            ax.plot(chain["accept_probs"], lw=1.0, alpha=0.75, label=f"chain {chain_id}")
        ax.set_title(title)
        ax.set_xlabel("draw")
        ax.set_ylabel("accept probability")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, alpha=0.25)
        ax.legend(fontsize=8)
    fig.tight_layout()
    savefig(fig, "hmc_diagnostics.png")


def plot_feature_sensitivity(sens: dict[str, Any]) -> None:
    mat = np.asarray(sens["sensitivity_matrix"], dtype=float)
    fig, ax = plt.subplots(figsize=(11.5, 7.2))
    im = ax.imshow(mat, aspect="auto", cmap="coolwarm")
    ax.set_yticks(np.arange(len(sens["feature_names"])))
    ax.set_yticklabels(sens["feature_names"], fontsize=7)
    ax.set_xticks(np.arange(len(sens["parameter_names"])))
    ax.set_xticklabels(sens["parameter_names"], rotation=25, ha="right", fontsize=8)
    ax.set_title("Forward-model feature sensitivities")
    fig.colorbar(im, ax=ax, shrink=0.82, label="finite-difference sensitivity")
    fig.tight_layout()
    savefig(fig, "peak_feature_mapping_sensitivity.png", text_heavy=True, min_font_pt=6.5)


def plot_graphical_model() -> None:
    fig, ax = plt.subplots(figsize=(12.6, 6.4))
    ax.axis("off")
    boxes = [
        (0.05, 0.68, "structural parameters\nk1,k2,zeta1,zeta2"),
        (0.35, 0.68, "build variability\nsigma_build learned"),
        (0.65, 0.68, "sensor scale\nsigma_sensor learned"),
        (0.05, 0.35, "tray vibe PSD\n11 builds, full log PSD"),
        (0.35, 0.35, "modal FRFs\n1 dome + 1 coupled test"),
        (0.65, 0.35, "flight PSDs\n11 flights, Matern forcing"),
        (0.35, 0.08, "posterior QOI\ninput spectra and tray 3*GRMS"),
    ]
    for x, y, text in boxes:
        rect = plt.Rectangle((x, y), 0.24, 0.16, fill=False, lw=1.8, ec="#333333")
        ax.add_patch(rect)
        ax.text(x + 0.12, y + 0.08, text, ha="center", va="center", fontsize=10)
    arrows = [
        ((0.17, 0.68), (0.17, 0.51)),
        ((0.47, 0.68), (0.17, 0.51)),
        ((0.77, 0.68), (0.17, 0.51)),
        ((0.17, 0.68), (0.47, 0.51)),
        ((0.47, 0.68), (0.47, 0.51)),
        ((0.77, 0.68), (0.47, 0.51)),
        ((0.17, 0.68), (0.77, 0.51)),
        ((0.47, 0.68), (0.77, 0.51)),
        ((0.77, 0.68), (0.77, 0.51)),
        ((0.17, 0.35), (0.47, 0.24)),
        ((0.47, 0.35), (0.47, 0.24)),
        ((0.77, 0.35), (0.47, 0.24)),
    ]
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.2, "color": "#555555"})
    ax.text(
        0.04,
        0.94,
        "Run-specific likelihood graph:\nfull-data uses every generated frequency point; peak-feature uses soft peak/notch forward maps.",
        fontsize=10,
        weight="bold",
        va="top",
    )
    fig.tight_layout()
    savefig(fig, "graphical_model_likelihood.png", text_heavy=True)


def interval_width(summary: dict[str, Any], name: str, lo: str = "q025", hi: str = "q975") -> float:
    return float(summary[name][hi] - summary[name][lo])


def build_results(
    data: dict[str, Any],
    full_run: dict[str, Any],
    peak_run: dict[str, Any],
    cfg: RunnerConfig,
    model: TorchSequentialModel,
) -> dict[str, Any]:
    c = Constants()
    full_pred = posterior_predictive_qoi(data, full_run["samples"], cfg, RUN_SEED + 501)
    peak_pred = posterior_predictive_qoi(data, peak_run["samples"], cfg, RUN_SEED + 601)
    full_qoi = {
        "tray_3grms_g": full_pred["tray_3grms_g"],
        "tray_3rms_g": full_pred["tray_3rms_g"],
        "interface_3grms_g": full_pred["interface_3grms_g"],
    }
    peak_qoi = {
        "tray_3grms_g": peak_pred["tray_3grms_g"],
        "tray_3rms_g": peak_pred["tray_3rms_g"],
        "interface_3grms_g": peak_pred["interface_3grms_g"],
    }
    full_summary = posterior_summary(full_run["samples"], full_qoi, c)
    peak_summary = posterior_summary(peak_run["samples"], peak_qoi, c)
    compare_names = [
        "dome_hz",
        "tray_hz",
        "zeta1",
        "zeta2",
        "build_sigma_db_psd",
        "sensor_sigma_db_psd",
        "tray_3grms_g",
    ]
    ratios = {}
    for name in compare_names:
        fw = max(interval_width(full_summary, name), 1e-12)
        ratios[name] = interval_width(peak_summary, name) / fw
    center = np.median(full_run["samples"].reshape((-1, full_run["samples"].shape[-1])), axis=0)
    sens = feature_sensitivity(model, center)
    return {
        "full": {
            "posterior_summary": full_summary,
            "posterior_predictive": serialize_predictive(full_pred),
            "diagnostics": full_run["diagnostics"],
        },
        "peak_feature": {
            "posterior_summary": peak_summary,
            "posterior_predictive": serialize_predictive(peak_pred),
            "diagnostics": peak_run["diagnostics"],
        },
        "likelihood_comparison": {
            "data_usage": {
                "full": "all generated tray-vibe log PSD points, modal log-FRF magnitudes, and flight tray/interface log PSD points",
                "peak_feature": "hard observed peak/notch features compared to differentiable soft peak/notch forward-model features",
            },
            "feature_noise_assumptions": {
                "vibe_peak_log_frequency_sigma": 0.055,
                "modal_notch_log_frequency_sigma": 0.035,
                "flight_peak_log_frequency_sigma": 0.075,
                "amplitude_noise": "learned build/sensor scales plus fixed feature floors; flight amplitudes also include fixed 3 dB forcing variability",
            },
            "interval_width_ratio_peak_over_full": ratios,
            "posterior_mean_differences_peak_minus_full": {
                name: peak_summary[name]["mean"] - full_summary[name]["mean"] for name in compare_names
            },
        },
        "feature_sensitivity": sens,
        "qoi_interval_contract": {
            "tray_3rms_equals_3grms": True,
            "reason": "The acceleration PSD is expressed in g^2/Hz; integrating gives g RMS, commonly GRMS.",
            "sensor_noise_included_in_qoi": False,
            "build_variability_included_in_qoi": True,
            "flight_to_flight_forcing_included_in_qoi": True,
        },
    }


def serialize_predictive(pred: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "posterior_predictive_draws": pred["posterior_predictive_draws"],
        "includes": pred["includes"],
        "excludes": pred["excludes"],
    }
    for key in ["input_force_psd_n2_per_hz", "tray_psd_g2_per_hz"]:
        out[key] = {q: np.asarray(v).tolist() for q, v in pred[key].items()}
    for key in ["tray_3grms_g", "tray_3rms_g", "interface_3grms_g"]:
        arr = np.asarray(pred[key], dtype=float)
        out[key] = {
            "samples": arr.tolist(),
            "q005": float(np.quantile(arr, 0.005)),
            "q025": float(np.quantile(arr, 0.025)),
            "q500": float(np.quantile(arr, 0.5)),
            "q975": float(np.quantile(arr, 0.975)),
            "q995": float(np.quantile(arr, 0.995)),
        }
    return out


def write_assumptions(data: dict[str, Any], cfg: RunnerConfig) -> None:
    rows = [
        ("PSD-space dB convention", "factor = 10 ** (dB / 10)", "dimensionless PSD multiplier", "Prompt/setup packet", "All dB variability is applied in PSD/power space.", "High", "fixed"),
        ("Dome/source coordinate", "m1", "coordinate label", "Prompt", "Dome/tank/source is modeled as primary mass.", "High", "fixed"),
        ("Tray/load coordinate", "m2", "coordinate label", "Prompt", "Tray/load/secondary structure is modeled as secondary mass.", "High", "fixed"),
        ("Smoothline PSD points", data["smoothline_points"], "Hz, g^2/Hz", "Prompt/setup packet", "Defines tray vibe input by log-log interpolation.", "High", "fixed"),
        ("Flight-to-flight forcing variability", cfg.flight_to_flight_sigma_db_psd, "dB PSD sigma", "Prompt", "Known forcing variability; fixed, not learned.", "High", "fixed"),
        ("Forcing covariance", f"Matern-3/2 ell={cfg.forcing_matern_length_logfreq}", "natural log frequency", "Prompt", "Required Matérn forcing GP; RBF not used.", "High", "fixed"),
        ("Build-to-build variability", "learned; synthetic truth 1.5", "dB PSD sigma", "Prompt/setup packet", "Hierarchical variability over builds.", "High", "inferred"),
        ("Sensor-noise scale", "learned; synthetic truth 0.75", "dB PSD sigma", "Prompt/setup packet", "Fresh multiplicative PSD/log-FRF sensor noise.", "High", "inferred"),
        ("Flight mean force offset", cfg.flight_mean_force_below_original_db_psd, "dB PSD", "Setup packet", "Mean force PSD is below original flat force PSD.", "High", "fixed mean with learned global scale"),
        ("Masses", [data["constants"]["m1_kg"], data["constants"]["m2_kg"]], "kg", "Fresh 2DOF model", "Toy dome/tray structural model.", "Medium", "fixed"),
        ("Likelihood full-data choice", "all generated frequency points", "categorical", "Runner implementation", "Uses full log PSD and log FRF magnitude arrays.", "High", "fixed method choice"),
        ("Likelihood peak-feature choice", "soft peak/notch forward features", "categorical", "Runner implementation", "Compares observed hard features to predicted transfer-function features.", "High", "fixed method choice"),
    ]
    md = "# Assumptions Ledger\n\n| Assumption | Value | Units | Source | Rationale | Sensitivity | Status |\n|---|---|---|---|---|---|---|\n"
    for row in rows:
        md += "| " + " | ".join(str(x) for x in row) + " |\n"
    (OUT_DIR / "assumptions_ledger.md").write_text(md)
    (OUT_DIR / "assumptions_ledger.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "assumption": r[0],
                        "value": r[1],
                        "units": r[2],
                        "source": r[3],
                        "rationale": r[4],
                        "sensitivity_priority": r[5],
                        "status": r[6],
                    }
                    for r in rows
                ],
                "inferred_variables": [
                    "dome natural frequency via k1",
                    "tray natural frequency via k2",
                    "dome damping zeta1",
                    "tray damping zeta2",
                    "global flight force PSD scale",
                    "build-to-build PSD variability scale",
                    "sensor-noise PSD variability scale",
                ],
                "fixed_variables": [
                    "m1 and m2 masses",
                    "flight-to-flight forcing variability sigma = 3 dB PSD",
                    "Matern-3/2 forcing covariance length scale",
                    "smoothline PSD table",
                ],
                "not_inferred_latent_variables": [
                    "individual build effects are marginalized/approximated, not sampled",
                    "individual flight forcing GP paths are marginalized/used in posterior predictive draws, not sampled in HMC state",
                    "phase noise for modal FRFs is not inferred",
                ],
            },
            indent=2,
        )
    )


def write_quantity_contracts() -> None:
    text = """# Quantity Contracts

## Smoothline PSD
- Numerator: base acceleration squared.
- Denominator: one-sided frequency bandwidth.
- Coordinate: tray shaker/base input.
- Excitation: commanded random-vibration smoothline.
- Boundary condition: standalone tray/load vibe test.
- Units: g^2/Hz.
- Expected behavior: log-log interpolation through 20, 100, 750, and 2000 Hz points.
- Reference: user task card and setup packet.

## Tray Vibe Response PSD
- Numerator: tray acceleration squared.
- Denominator: one-sided frequency bandwidth.
- Coordinate: tray/load m2.
- Excitation: smoothline base acceleration PSD.
- Boundary condition: standalone tray.
- Units: g^2/Hz.
- Expected behavior: low-frequency transmissibility near unity, resonance peak near tray mode, high-frequency rolloff.
- Reference: existing tray transmissibility convention in fresh 2DOF packet.

## Dome-Only Modal FRF
- Numerator: applied force at dome coordinate.
- Denominator: acceleration at dome coordinate.
- Coordinate: dome/source m1.
- Excitation: dome-only modal impact/shaker.
- Boundary condition: tray uncoupled.
- Units: kg for reciprocal inertance F/a.
- Expected behavior: reciprocal-inertance notch near dome resonance and large low-frequency apparent inertia trend.
- Reference: fresh 2DOF reciprocal-inertance convention.

## Coupled Modal FRFs
- Numerator: applied force at interface or tray drive point.
- Denominator: collocated acceleration.
- Coordinate: interface/primary m1 and tray/load m2.
- Excitation: modal impacts on assembled dome/tray system.
- Boundary condition: coupled 2DOF assembly.
- Units: kg for reciprocal inertance F/a.
- Expected behavior: coupled notches/features affected by both k1 and k2; not identical to uncoupled natural frequencies.
- Reference: fresh 2DOF coupled-channel convention.

## Flight Forcing PSD
- Numerator: input force squared.
- Denominator: one-sided frequency bandwidth.
- Coordinate: force into dome/source m1.
- Excitation: latent flight forcing process.
- Boundary condition: coupled flight assembly.
- Units: N^2/Hz.
- Expected behavior: Matern-3/2 log-PSD variation around the mean force PSD; fixed 3 dB flight-to-flight variability.
- Reference: task card and setup packet.

## Interface Acceleration Spectrum
- Numerator: interface acceleration squared.
- Denominator: one-sided frequency bandwidth.
- Coordinate: dome/interface side m1.
- Excitation: flight force into m1.
- Boundary condition: coupled flight assembly.
- Units: g^2/Hz.
- Expected behavior: shaped by coupled acceleration-over-force H00; resonant amplification near coupled modes.
- Reference: 2DOF acceleration-over-force convention.

## Tray Acceleration Spectrum
- Numerator: tray acceleration squared.
- Denominator: one-sided frequency bandwidth.
- Coordinate: tray/load m2.
- Excitation: flight force into m1.
- Boundary condition: coupled flight assembly.
- Units: g^2/Hz.
- Expected behavior: shaped by cross transfer H10 and forcing PSD; sensitive to damping and build variability.
- Reference: 2DOF acceleration-over-force convention.

## Tray 3*RMS / 3*GRMS QOI
- Numerator: three times the square root of integrated tray acceleration PSD.
- Denominator: not applicable after frequency integration.
- Coordinate: tray/load m2.
- Excitation: flight forcing into m1.
- Boundary condition: coupled flight assembly.
- Units: g.
- Expected behavior: increases with tray PSD energy; 3*RMS and 3*GRMS are equivalent because acceleration is expressed in g.
- Reference: random-vibration GRMS convention used in the fresh 2DOF packet.
"""
    (OUT_DIR / "quantity_contracts.md").write_text(text)


def write_packet(data: dict[str, Any], results: dict[str, Any], env: dict[str, Any], checks: dict[str, Any]) -> None:
    full = results["full"]["posterior_summary"]
    peak = results["peak_feature"]["posterior_summary"]
    comp = results["likelihood_comparison"]
    md = f"""# Codex GPT-5.5 Sequential Vibe/Modal/Flight Packet

## Method Summary

Decision supported: estimate post-flight input spectra and tray acceleration QOI intervals for a dome/tray coupled structure after tray vibe, dome modal, coupled modal, first flight, and ten later build/flight observations.

Objective/success metric: posterior uncertainty in input force PSD and tray 3*GRMS/3*RMS QOI, with a comparison between full FRF/PSD likelihoods and peak-feature likelihoods.

Allowed experiment/search choices in this runner: none. The staged data sequence is fixed by the task card. Human judgment remains responsible for whether this toy 2DOF framing is an adequate aerospace decision model.

Wrong-question triggers: the real structure is not well approximated by a 2DOF dome/tray model; phase/complex FRF errors matter more than log-magnitude errors; flight forcing is not stationary in log frequency; or build/test variability is correlated in a way this marginal likelihood omits.

Model form: two masses, dome/source `m1` and tray/load `m2`, coupled by the tray stiffness/damping convention used in the fresh 2DOF packet. Full-data likelihood uses every generated log PSD and log FRF-magnitude point. Peak-feature likelihood uses observed hard peak/notch summaries compared with differentiable soft peak/notch features predicted from the same forward model.

Likelihood equation, full-data sketch: residual vectors are `r = log(y_obs) - log(y_model(theta))`; vibe/modal residual covariance includes learned build and sensor PSD-space scales; flight residual covariance additionally includes fixed known 3 dB Matern-3/2 forcing covariance in natural log frequency. Modal FRFs use log magnitude only, so phase is a documented limitation.

Data count: {data['data_count']['tray_vibe_tests']} tray vibe tests, 1 dome modal test, 1 coupled modal test with interface and tray drive-point channels, {data['data_count']['flights']} flights, {data['data_count']['frequency_points_per_psd']} PSD frequency points, and {data['data_count']['frequency_points_per_modal_frf']} modal FRF frequency points.

Inferred variables: dome/tray natural frequencies via `k1,k2`, dome/tray damping ratios, global flight force PSD scale, build-to-build variability scale, and sensor-noise scale. Fixed variables: masses, smoothline table, Matern-3/2 length scale, and fixed 3 dB flight-to-flight variability. Non-inferred latent variables: individual build effects, individual flight forcing paths, phase noise, and FRF complex phase discrepancy.

## Backend Handling

Python version: {env['python_version']}. NumPyro installed: {env['packages']['numpyro']['installed']}. JAX installed: {env['packages']['jax']['installed']}. PyMC installed: {env['packages']['pymc']['installed']}. PyTorch installed: {env['packages']['torch']['installed']}.

Resolution: {env['numpyro_resolution']}

This is real gradient-based HMC, not random-walk Metropolis. It is not NUTS; tree depth is therefore marked not applicable in `nuts_diagnostics.json`.

## Quantity Contracts And Assumptions

See `quantity_contracts.md` and `assumptions_ledger.md`. Key conventions: PSD-space dB uses `factor = 10 ** (dB / 10)`, dome is `m1`, tray is `m2`, and flight-to-flight forcing variability remains fixed at 3 dB.

## Posterior Summary

| Quantity | Full mean | Full 95% | Peak mean | Peak 95% |
|---|---:|---:|---:|---:|
| Dome frequency [Hz] | {full['dome_hz']['mean']:.4g} | [{full['dome_hz']['q025']:.4g}, {full['dome_hz']['q975']:.4g}] | {peak['dome_hz']['mean']:.4g} | [{peak['dome_hz']['q025']:.4g}, {peak['dome_hz']['q975']:.4g}] |
| Tray frequency [Hz] | {full['tray_hz']['mean']:.4g} | [{full['tray_hz']['q025']:.4g}, {full['tray_hz']['q975']:.4g}] | {peak['tray_hz']['mean']:.4g} | [{peak['tray_hz']['q025']:.4g}, {peak['tray_hz']['q975']:.4g}] |
| Build sigma [dB PSD] | {full['build_sigma_db_psd']['mean']:.4g} | [{full['build_sigma_db_psd']['q025']:.4g}, {full['build_sigma_db_psd']['q975']:.4g}] | {peak['build_sigma_db_psd']['mean']:.4g} | [{peak['build_sigma_db_psd']['q025']:.4g}, {peak['build_sigma_db_psd']['q975']:.4g}] |
| Sensor sigma [dB PSD] | {full['sensor_sigma_db_psd']['mean']:.4g} | [{full['sensor_sigma_db_psd']['q025']:.4g}, {full['sensor_sigma_db_psd']['q975']:.4g}] | {peak['sensor_sigma_db_psd']['mean']:.4g} | [{peak['sensor_sigma_db_psd']['q025']:.4g}, {peak['sensor_sigma_db_psd']['q975']:.4g}] |
| Tray 3*GRMS [g] | {full['tray_3grms_g']['mean']:.4g} | [{full['tray_3grms_g']['q025']:.4g}, {full['tray_3grms_g']['q975']:.4g}] | {peak['tray_3grms_g']['mean']:.4g} | [{peak['tray_3grms_g']['q025']:.4g}, {peak['tray_3grms_g']['q975']:.4g}] |
| Tray 3*GRMS 99% [g] | - | [{full['tray_3grms_g']['q005']:.4g}, {full['tray_3grms_g']['q995']:.4g}] | - | [{peak['tray_3grms_g']['q005']:.4g}, {peak['tray_3grms_g']['q995']:.4g}] |

## Likelihood Comparison

Full-data usage: {comp['data_usage']['full']}.

Peak-feature usage: {comp['data_usage']['peak_feature']}.

Interval-width ratios, peak/full: {json.dumps(comp['interval_width_ratio_peak_over_full'], indent=2)}

The feature likelihood uses transfer-function peak/notch features predicted from the same forward model. It does not equate a peak or notch with a natural frequency; see `feature_sensitivity.json` and `figures/peak_feature_mapping_sensitivity.png`.

## Figures

![observations](figures/sequential_observations_truth_vs_observed.png)

![errors](figures/absolute_error_and_normalized_diagnostics.png)

![posterior](figures/posterior_full_vs_peak_parameters.png)

![qoi](figures/input_spectra_and_tray_qoi_intervals_after_flights.png)

![comparison](figures/full_vs_peak_likelihood_qoi_differences.png)

![diagnostics](figures/hmc_diagnostics.png)

![feature sensitivity](figures/peak_feature_mapping_sensitivity.png)

![graphical model](figures/graphical_model_likelihood.png)

## Checker Status

Self-check pass: {checks.get('self_check_pass')}. Immutable checker hash command is recorded in `checks.json` and `commands.md`.

## Limitations

- NUTS was not achieved; fixed-trajectory HMC was used and labeled.
- Modal likelihood uses log magnitude, not complex real/imag phase.
- Individual build effects and individual flight forcing GP paths are not in the HMC state; they are marginalized approximately and sampled for posterior predictive QOI intervals.
- A checker pass is not proof of physical correctness.
"""
    (OUT_DIR / "packet.md").write_text(md)


def write_static_docs(data: dict[str, Any], results: dict[str, Any], env: dict[str, Any]) -> None:
    write_assumptions(data, RunnerConfig())
    write_quantity_contracts()
    (OUT_DIR / "task.md").write_text(
        "# Runner Task\n\nImplement the full sequential dome/tray vibe-modal-flight experiment for Codex GPT-5.5 outputs.\n"
    )
    (OUT_DIR / "nuts_diagnostics.json").write_text(
        json.dumps(
            {
                "backend_note": env["numpyro_resolution"],
                "full": results["full"]["diagnostics"],
                "peak_feature": results["peak_feature"]["diagnostics"],
            },
            indent=2,
        )
    )
    diag_md = "# NUTS/HMC Diagnostics\n\n"
    diag_md += "NUTS active: false. HMC active: true. Backend: custom PyTorch fixed-trajectory HMC.\n\n"
    for mode in ["full", "peak_feature"]:
        d = results[mode]["diagnostics"]
        diag_md += f"## {mode}\n\n"
        diag_md += f"- Divergences: {d['divergences']}\n"
        diag_md += f"- Final step sizes: {d['step_size_final_by_chain']}\n"
        diag_md += f"- Tree depth: {d['tree_depth']['status']}; fixed leapfrog steps = {d['tree_depth']['fixed_leapfrog_steps']}\n"
        diag_md += f"- Acceptance rates: {d['acceptance_rate_by_chain']}\n"
        diag_md += f"- ESS approximation: {json.dumps(d['ess_bulk_approx'], indent=2)}\n"
        diag_md += f"- R-hat: {json.dumps(d['r_hat'], indent=2)}\n\n"
    (OUT_DIR / "nuts_diagnostics.md").write_text(diag_md)

    known = f"""# Known Failures And Risks

- NumPyro NUTS was not achieved because NumPyro/JAX are not installed under Python 3.9.6. I used a labeled custom PyTorch HMC backend instead. This is not a random-walk sampler, but it is also not NUTS.
- Tree depth is not applicable to fixed-trajectory HMC; the diagnostics file records fixed leapfrog steps instead.
- Sampler diagnostics are not perfect. Recorded divergences: full = {results['full']['diagnostics']['divergences']}, peak-feature = {results['peak_feature']['diagnostics']['divergences']}. R-hat and ESS should be inspected in `nuts_diagnostics.json` before trusting intervals as final engineering evidence.
- Modal FRF inference uses log magnitudes only. Complex phase and real/imag residual structure are generated but not used in the HMC likelihood.
- Individual build effects and forcing GP paths are not sampled as HMC latent variables. The runner learns their scales and uses posterior predictive draws for QOI intervals.
- The model is a 2DOF synthetic pressure test. It is not a validated rocket hardware analysis.
- Checker-backed artifact existence and consistency do not prove physical correctness.
"""
    (OUT_DIR / "known_failures.md").write_text(known)

    review = """# Review Request

Please scrutinize:

- whether the HMC substitution is acceptable for this pressure test or should be treated as incomplete because NUTS itself was not active;
- whether marginalizing build effects and flight forcing paths is too aggressive for the stated hierarchy;
- whether log-magnitude modal FRF likelihood loses information that should be included before any physical conclusion;
- whether the peak-feature likelihood noise assumptions are defensible;
- whether the input spectra and tray 3*GRMS QOI intervals include the correct uncertainty categories.
"""
    (OUT_DIR / "review_request.md").write_text(review)

    sources = """# Sources

| Source | What it supports | Limit |
|---|---|---|
| AGENTS.md / CLAUDE.md | Harness gates, anti-cheating, NUTS/HMC rule | Does not implement sampler |
| docs/agents/competitive_full_experiment/task_card_full_experiment.md | Required staged experiment scope | Synthetic pressure-test spec |
| artifacts/reports/sequential_vibe_modal_flight_20260602/* | Setup conventions, smoothline, staged data schema | Setup only; no posterior |
| artifacts/reports/fresh_2dof_statfem_fbs_20260601/* | Existing 2DOF conventions and quantity precedents | Legacy random-walk inference is not reused |
"""
    (OUT_DIR / "sources.md").write_text(sources)


def write_manifest(results: dict[str, Any], env: dict[str, Any], checks: dict[str, Any]) -> None:
    figures = sorted([f"figures/{p.name}" for p in FIG_DIR.glob("*.png")])
    manifest = {
        "trial_id": "runner_codex_gpt55_20260602",
        "date": "2026-06-02",
        "tool": "Codex GPT-5.5",
        "command": "PYTHONPATH=. python3 scripts/run_codex_gpt55_full_experiment.py",
        "output_dir": str(OUT_DIR.relative_to(ROOT)),
        "packet": "packet.md",
        "dataset": "sequential_full_dataset.json",
        "posterior": "posterior_results.json",
        "diagnostics": ["nuts_diagnostics.json", "nuts_diagnostics.md"],
        "figures": figures,
        "checks": "checks.json",
        "env": env,
        "sampler": {
            "nuts_active": False,
            "hmc_active": True,
            "backend": "custom PyTorch fixed-trajectory HMC",
            "random_walk_metropolis_used": False,
        },
        "immutable_checker_files_untouched_claim": "verified by shasum command recorded in checks.json after external command run",
        "open_risks": [
            "NUTS not active",
            "phase ignored in modal likelihood",
            "individual latent build/forcing paths not sampled in HMC state",
        ],
        "checks_snapshot": checks,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))


def initial_commands_md(env: dict[str, Any]) -> None:
    text = f"""# Commands

Working directory: `{ROOT}`

## Environment Resolution

- `python3 --version` -> `{platform.python_version()}`
- NumPyro installed: `{env['packages']['numpyro']['installed']}`
- JAX installed: `{env['packages']['jax']['installed']}`
- PyMC installed: `{env['packages']['pymc']['installed']}`
- PyTorch installed: `{env['packages']['torch']['installed']}`

Resolution: {env['numpyro_resolution']}

## Commands To Reproduce

1. `PYTHONPATH=. python3 scripts/run_codex_gpt55_full_experiment.py`
2. `PYTHONPATH=. python3 tests/test_runner_codex_gpt55_full_experiment.py`
3. `shasum -a 256 -c harness/checkers/manifest.sha256`

Actual exit codes and console snippets are filled in after the commands are run.
"""
    (OUT_DIR / "commands.md").write_text(text)


def write_files_changed_placeholder() -> None:
    text = """# Files Changed

Created/edited by this runner:

- `scripts/run_codex_gpt55_full_experiment.py`
- `tests/test_runner_codex_gpt55_full_experiment.py`
- `notes/todo.md`
- `notes/runs.md`
- `artifacts/reports/runner_codex_gpt55_20260602/`

Immutable checker files were not edited by this runner:

- `harness/checkers/verify_artifacts.py`
- `harness/checkers/check_canary.py`
- `tests/test_posterior_recovery.py`
- `tests/test_mdof_transfer.py`

The immutable hash check result is recorded in `checks.json` and `commands.md`.
"""
    (OUT_DIR / "files_changed.md").write_text(text)


def self_checks(data: dict[str, Any], results: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    required = [
        "commands.md",
        "files_changed.md",
        "assumptions_ledger.md",
        "assumptions_ledger.json",
        "nuts_diagnostics.md",
        "nuts_diagnostics.json",
        "known_failures.md",
        "review_request.md",
        "manifest.json",
        "packet.md",
        "posterior_results.json",
        "sequential_full_dataset.json",
        "quantity_contracts.md",
    ]
    for rel in required:
        if not (OUT_DIR / rel).exists():
            failures.append(f"missing {rel}")
    if data["data_count"]["flights"] != 11:
        failures.append("expected 11 flights")
    if data["fixed_not_inferred"]["flight_to_flight_sigma_db_psd"] != 3.0:
        failures.append("flight-to-flight sigma not fixed at 3 dB")
    for mode in ["full", "peak_feature"]:
        diag = results[mode]["diagnostics"]
        for key in ["divergences", "step_size_final_by_chain", "ess_bulk_approx", "r_hat", "tree_depth"]:
            if key not in diag:
                failures.append(f"{mode} diagnostics missing {key}")
        qoi = results[mode]["posterior_summary"]["tray_3grms_g"]
        if not (qoi["q005"] < qoi["q025"] < qoi["q975"] < qoi["q995"]):
            failures.append(f"{mode} qoi intervals not ordered")
    if not IMAGE_QA or not all(item["pass"] for item in IMAGE_QA):
        failures.append("image QA failed or missing")
    return {
        "self_check_pass": not failures,
        "self_check_failures": failures,
        "image_legibility": IMAGE_QA,
        "immutable_checker_command": {
            "command": "shasum -a 256 -c harness/checkers/manifest.sha256",
            "status": "pending_external_run",
        },
        "runner_checker_command": {
            "command": "PYTHONPATH=. python3 tests/test_runner_codex_gpt55_full_experiment.py",
            "status": "pending_external_run",
        },
    }


def main() -> int:
    prepare_output()
    cfg = RunnerConfig()
    env = env_status()
    initial_commands_md(env)
    write_files_changed_placeholder()
    data = generate_dataset(cfg)
    (OUT_DIR / "sequential_full_dataset.json").write_text(json.dumps(data, indent=2))
    model = TorchSequentialModel(data, cfg)

    c = Constants()
    initial = np.array(
        [
            0.0,
            0.0,
            math.log(c.dome_nominal_zeta),
            math.log(c.tray_nominal_zeta),
            0.0,
            math.log(psd_db_sigma_to_ln_sigma(cfg.build_sigma_db_psd_truth)),
            math.log(psd_db_sigma_to_ln_sigma(cfg.sensor_sigma_db_psd_truth)),
        ],
        dtype=float,
    )
    full_run = run_hmc(model, "full", initial, cfg)
    peak_run = run_hmc(model, "peak", initial, cfg)
    results = build_results(data, full_run, peak_run, cfg, model)

    # Figures are generated after results so the packet and checker can cite exact artifacts.
    plot_observations(data)
    plot_absolute_error(data)
    plot_posteriors(full_run["samples"], peak_run["samples"], c)
    full_pred = posterior_predictive_qoi(data, full_run["samples"], cfg, RUN_SEED + 501)
    peak_pred = posterior_predictive_qoi(data, peak_run["samples"], cfg, RUN_SEED + 601)
    plot_qoi_and_input(
        data,
        full_pred,
        peak_pred,
        {"tray_3grms_g": full_pred["tray_3grms_g"]},
        {"tray_3grms_g": peak_pred["tray_3grms_g"]},
    )
    plot_qoi_widths(results)
    plot_diagnostics(full_run, peak_run)
    plot_feature_sensitivity(results["feature_sensitivity"])
    plot_graphical_model()

    (OUT_DIR / "feature_sensitivity.json").write_text(json.dumps(results["feature_sensitivity"], indent=2))
    (OUT_DIR / "posterior_results.json").write_text(json.dumps(results, indent=2))
    write_static_docs(data, results, env)
    provisional_checks = {"self_check_pass": "pending"}
    write_packet(data, results, env, provisional_checks)
    write_manifest(results, env, provisional_checks)
    checks = self_checks(data, results)
    (OUT_DIR / "checks.json").write_text(json.dumps(checks, indent=2))
    write_packet(data, results, env, checks)
    write_manifest(results, env, checks)
    print(
        json.dumps(
            {
                "out_dir": str(OUT_DIR),
                "self_check_pass": checks["self_check_pass"],
                "full_divergences": results["full"]["diagnostics"]["divergences"],
                "peak_divergences": results["peak_feature"]["diagnostics"]["divergences"],
                "full_tray_3grms_95": [
                    results["full"]["posterior_summary"]["tray_3grms_g"]["q025"],
                    results["full"]["posterior_summary"]["tray_3grms_g"]["q975"],
                ],
                "peak_tray_3grms_95": [
                    results["peak_feature"]["posterior_summary"]["tray_3grms_g"]["q025"],
                    results["peak_feature"]["posterior_summary"]["tray_3grms_g"]["q975"],
                ],
            },
            indent=2,
        )
    )
    return 0 if checks["self_check_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
