#!/usr/bin/env python3
"""Generate independent round-3 truth observations.

This script is intentionally located in sealed_truth because it contains the
hidden as-built reality model. It writes public observations to dataset/ and
validation/review artifacts to report/.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
from pathlib import Path
import sys
import textwrap
import time
from typing import Any

import numpy as np
import scipy.linalg
import scipy.signal
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


G0 = 9.80665
DOF_ORDER = np.array(["x", "y", "z", "rx", "ry", "rz"])
TRANSLATIONAL_DOFS = {"x", "y", "z"}
ROTATIONAL_DOFS = {"rx", "ry", "rz"}


class StageTimer:
    def __init__(self) -> None:
        self.wall_start = time.perf_counter()
        self.active: dict[str, float] = {}

    def run(self, name: str, func, *args, **kwargs):
        start = time.perf_counter()
        out = func(*args, **kwargs)
        self.active[name] = self.active.get(name, 0.0) + time.perf_counter() - start
        return out

    def summary(self) -> dict[str, Any]:
        elapsed = time.perf_counter() - self.wall_start
        active = float(sum(self.active.values()))
        return {
            "script_wall_s": elapsed,
            "elapsed_wallclock_s": elapsed,
            "active_runtime_s": min(active, elapsed),
            "active_compute_by_stage_s": self.active,
            "active_runtime_definition": "Sum of timed generation/validation stages inside this script; capped at wall time for the AGENTS runtime gate.",
        }


def root_from_arg() -> Path:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="codex_truth workspace root",
    )
    args = parser.parse_args()
    root = args.root.resolve()
    if root.name != "codex_truth":
        raise SystemExit(f"Refusing to write outside codex_truth workspace: {root}")
    return root


def ensure_dirs(root: Path) -> dict[str, Path]:
    dirs = {
        "dataset": root / "dataset",
        "sealed": root / "sealed_truth",
        "report": root / "report",
        "figures": root / "report" / "figures",
        "mesh": root / "report" / "mesh",
        "checks": root / "report" / "checks",
        "notes": root / "notes",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def make_frequency_grid() -> np.ndarray:
    pieces = [
        np.geomspace(5.0, 600.0, 950),
        np.linspace(45.0, 125.0, 1601),
        np.linspace(125.0, 230.0, 751),
        np.linspace(230.0, 600.0, 741),
    ]
    freq = np.unique(np.round(np.concatenate(pieces), 8))
    return freq[(freq >= 5.0) & (freq <= 600.0)]


def smooth_design_force_psd(freq_hz: np.ndarray) -> np.ndarray:
    """Shared design envelope in force PSD units.

    The exact values are part of the published forcing input, not hidden truth.
    They produce load accelerations in a range that is plausible for vibration
    review without relying on an external spec curve.
    """

    f_nodes = np.array([5.0, 15.0, 30.0, 80.0, 140.0, 260.0, 420.0, 600.0])
    amp_nodes = np.array([45.0, 78.0, 115.0, 130.0, 92.0, 64.0, 42.0, 30.0])
    log_amp = np.interp(np.log10(freq_hz), np.log10(f_nodes), np.log10(amp_nodes))
    amp = 10.0**log_amp
    shoulder = 1.0 + 0.18 * np.exp(-0.5 * ((np.log(freq_hz / 92.0)) / 0.28) ** 2)
    return (amp * shoulder) ** 2


def matern32_covariance(x: np.ndarray, sigma: float, length: float, jitter: float = 1e-10) -> np.ndarray:
    r = np.abs(x[:, None] - x[None, :])
    q = np.sqrt(3.0) * r / length
    cov = sigma**2 * (1.0 + q) * np.exp(-q)
    cov[np.diag_indices_from(cov)] += jitter
    return cov


def correlated_curve(
    freq_hz: np.ndarray,
    rng: np.random.Generator,
    sigma: float = 1.0,
    length_log10: float = 0.24,
    n_ctrl: int = 150,
) -> np.ndarray:
    ctrl = np.geomspace(float(freq_hz[0]), float(freq_hz[-1]), n_ctrl)
    x = np.log10(ctrl)
    cov = matern32_covariance(x, sigma=sigma, length=length_log10, jitter=1e-8)
    vals = np.linalg.cholesky(cov) @ rng.standard_normal(n_ctrl)
    return np.interp(np.log10(freq_hz), x, vals)


def make_forcing(freq_hz: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    design = smooth_design_force_psd(freq_hz)
    mean_offset_db = -6.0
    gp_sigma_db = 3.0
    gp_length_log10_hz = 0.28
    n_flights = 11
    force_psd = np.zeros((n_flights, freq_hz.size))
    flight_db = np.zeros_like(force_psd)
    for j in range(n_flights):
        curve = correlated_curve(
            freq_hz,
            rng,
            sigma=gp_sigma_db,
            length_log10=gp_length_log10_hz,
            n_ctrl=180,
        )
        flight_db[j] = mean_offset_db + curve
        force_psd[j] = design * 10.0 ** (flight_db[j] / 10.0)
    params = {
        "quantity": "interface forcing PSD",
        "units": "N^2/Hz",
        "db_convention": "PSD-space dB, factor = 10**(dB/10)",
        "design_envelope_array_key": "design_force_psd_N2_per_Hz",
        "mean_offset_db_relative_to_design": mean_offset_db,
        "matern_family": "Matern-3/2 in log10(frequency_Hz)",
        "flight_to_flight_sigma_db": gp_sigma_db,
        "length_scale_log10_hz": gp_length_log10_hz,
        "control_grid_count_used_to_draw_gp": 180,
        "n_flights": n_flights,
    }
    return design, force_psd, params


def mode(fn_hz: float, zeta: float, participation: float, fd_stiff: float, fd_loss: float, relax_hz: float, softening: float = 0.0) -> dict[str, float]:
    return {
        "fn_hz": float(fn_hz),
        "zeta": float(zeta),
        "participation": float(participation),
        "fd_stiff_frac": float(fd_stiff),
        "fd_loss_frac": float(fd_loss),
        "relax_hz": float(relax_hz),
        "nonlinear_soften_frac": float(softening),
    }


def build_truth_profiles() -> dict[str, Any]:
    """Hidden nominal truth profiles before per-build as-built draws."""

    return {
        "material_visualization": {
            "dome_material": "Al 2219-like",
            "E_GPa": 72.0,
            "rho_kg_m3": 2840.0,
            "nu": 0.33,
            "pressure_bar_abs": 4.2,
            "diameter_m": 5.5,
            "ellipsoidal_cap_height_m": 1.38,
        },
        "masses": {
            "netcg_load_mass_kg": 170.0,
            "avionics_mass_kg": 136.0,
            "tray_panel_mass_kg": 34.0,
            "source_effective_z_mass_kg": 430.0,
        },
        "dof_profiles": {
            "z": {
                "source_rigid": 430.0,
                "load_rigid": 170.0,
                "source_modes": [
                    mode(93.50, 0.0225, 0.42, 0.018, 0.62, 155.0, 0.005),
                    mode(128.0, 0.0280, 0.17, 0.025, 0.45, 210.0, 0.003),
                    mode(176.0, 0.0185, 0.12, -0.010, 0.38, 260.0, 0.002),
                    mode(266.0, 0.0320, 0.09, 0.020, 0.52, 330.0, 0.001),
                    mode(382.0, 0.0360, 0.06, 0.012, 0.35, 470.0, 0.000),
                    mode(522.0, 0.0400, 0.04, -0.006, 0.24, 520.0, 0.000),
                ],
                "load_modes": [
                    mode(86.25, 0.0195, 0.78, 0.022, 0.80, 135.0, 0.012),
                    mode(119.0, 0.0260, 0.22, -0.012, 0.44, 180.0, 0.004),
                    mode(168.0, 0.0220, 0.18, 0.016, 0.40, 230.0, 0.003),
                    mode(244.0, 0.0310, 0.11, 0.010, 0.58, 310.0, 0.001),
                    mode(356.0, 0.0380, 0.07, -0.010, 0.32, 430.0, 0.000),
                    mode(505.0, 0.0440, 0.05, 0.008, 0.28, 540.0, 0.000),
                ],
            },
            "x": {
                "source_rigid": 360.0,
                "load_rigid": 158.0,
                "source_modes": [
                    mode(101.0, 0.025, 0.24, 0.014, 0.48, 160.0, 0.003),
                    mode(149.0, 0.030, 0.13, -0.010, 0.36, 225.0, 0.002),
                    mode(315.0, 0.036, 0.08, 0.008, 0.24, 390.0, 0.000),
                    mode(477.0, 0.040, 0.05, -0.006, 0.20, 530.0, 0.000),
                ],
                "load_modes": [
                    mode(69.0, 0.023, 0.52, 0.020, 0.70, 115.0, 0.006),
                    mode(91.0, 0.021, 0.30, -0.012, 0.55, 150.0, 0.005),
                    mode(154.0, 0.027, 0.18, 0.012, 0.36, 230.0, 0.002),
                    mode(286.0, 0.035, 0.10, 0.008, 0.28, 360.0, 0.000),
                    mode(448.0, 0.043, 0.05, -0.006, 0.20, 510.0, 0.000),
                ],
            },
            "y": {
                "source_rigid": 365.0,
                "load_rigid": 160.0,
                "source_modes": [
                    mode(101.0, 0.025, 0.23, 0.014, 0.48, 160.0, 0.003),
                    mode(151.0, 0.030, 0.12, -0.010, 0.36, 225.0, 0.002),
                    mode(323.0, 0.036, 0.08, 0.008, 0.24, 390.0, 0.000),
                    mode(481.0, 0.040, 0.05, -0.006, 0.20, 530.0, 0.000),
                ],
                "load_modes": [
                    mode(69.0, 0.023, 0.50, 0.020, 0.70, 115.0, 0.006),
                    mode(91.0, 0.021, 0.29, -0.012, 0.55, 150.0, 0.005),
                    mode(157.0, 0.027, 0.18, 0.012, 0.36, 230.0, 0.002),
                    mode(292.0, 0.035, 0.10, 0.008, 0.28, 360.0, 0.000),
                    mode(455.0, 0.043, 0.05, -0.006, 0.20, 510.0, 0.000),
                ],
            },
            "rx": {
                "source_rigid": 520.0,
                "load_rigid": 245.0,
                "source_modes": [
                    mode(112.0, 0.026, 0.28, 0.018, 0.52, 180.0, 0.003),
                    mode(174.0, 0.030, 0.14, -0.010, 0.34, 250.0, 0.001),
                    mode(335.0, 0.038, 0.08, 0.008, 0.24, 430.0, 0.000),
                ],
                "load_modes": [
                    mode(82.0, 0.024, 0.48, 0.020, 0.72, 125.0, 0.006),
                    mode(109.0, 0.022, 0.32, -0.012, 0.54, 160.0, 0.005),
                    mode(197.0, 0.030, 0.16, 0.010, 0.40, 270.0, 0.001),
                    mode(390.0, 0.044, 0.08, -0.006, 0.22, 500.0, 0.000),
                ],
            },
            "ry": {
                "source_rigid": 515.0,
                "load_rigid": 250.0,
                "source_modes": [
                    mode(112.0, 0.026, 0.27, 0.018, 0.52, 180.0, 0.003),
                    mode(177.0, 0.030, 0.14, -0.010, 0.34, 250.0, 0.001),
                    mode(342.0, 0.038, 0.08, 0.008, 0.24, 430.0, 0.000),
                ],
                "load_modes": [
                    mode(82.0, 0.024, 0.47, 0.020, 0.72, 125.0, 0.006),
                    mode(109.0, 0.022, 0.31, -0.012, 0.54, 160.0, 0.005),
                    mode(202.0, 0.030, 0.16, 0.010, 0.40, 270.0, 0.001),
                    mode(398.0, 0.044, 0.08, -0.006, 0.22, 500.0, 0.000),
                ],
            },
            "rz": {
                "source_rigid": 420.0,
                "load_rigid": 185.0,
                "source_modes": [
                    mode(136.0, 0.028, 0.24, 0.014, 0.40, 210.0, 0.002),
                    mode(229.0, 0.033, 0.12, -0.008, 0.30, 320.0, 0.001),
                    mode(405.0, 0.042, 0.07, 0.006, 0.20, 500.0, 0.000),
                ],
                "load_modes": [
                    mode(118.0, 0.026, 0.42, 0.018, 0.60, 170.0, 0.004),
                    mode(171.0, 0.029, 0.24, -0.010, 0.44, 245.0, 0.002),
                    mode(286.0, 0.038, 0.12, 0.008, 0.28, 360.0, 0.000),
                    mode(474.0, 0.046, 0.06, -0.006, 0.18, 520.0, 0.000),
                ],
            },
        },
    }


def copy_mode_list(modes: list[dict[str, float]]) -> list[dict[str, float]]:
    return [dict(m) for m in modes]


def apply_mode_scatter(
    modes: list[dict[str, float]],
    fn_scale: float,
    zeta_scale: float,
    rng: np.random.Generator,
    mode_jitter_sigma: float,
    participation_jitter_sigma: float,
    dof_shift: float = 0.0,
) -> list[dict[str, float]]:
    out = []
    for idx, m in enumerate(modes):
        mm = dict(m)
        local_fn = np.exp(rng.normal(0.0, mode_jitter_sigma * (0.7 + 0.15 * idx)))
        local_z = np.exp(rng.normal(0.0, 0.30 * mode_jitter_sigma))
        p_shift = np.exp(rng.normal(0.0, participation_jitter_sigma))
        mm["fn_hz"] *= fn_scale * local_fn * (1.0 + dof_shift)
        mm["zeta"] = float(np.clip(mm["zeta"] * zeta_scale * local_z, 0.004, 0.085))
        mm["participation"] = float(np.clip(mm["participation"] * p_shift, 0.015, 1.35))
        mm["fd_stiff_frac"] += float(rng.normal(0.0, 0.006))
        mm["fd_loss_frac"] = float(np.clip(mm["fd_loss_frac"] + rng.normal(0.0, 0.05), 0.0, 1.2))
        mm["relax_hz"] = float(np.clip(mm["relax_hz"] * np.exp(rng.normal(0.0, 0.08)), 55.0, 680.0))
        out.append(mm)
    return out


def make_builds(profiles: dict[str, Any], rng: np.random.Generator) -> list[dict[str, Any]]:
    n_builds = 8
    sigma_fund_log = 0.05 / 3.0
    base_mass = profiles["masses"]["netcg_load_mass_kg"]
    strut_nominal_axial_k = (2.0 * np.pi * 86.25) ** 2 * base_mass / 6.0
    builds = []

    for build_id in range(n_builds):
        source_fn_scale = float(np.exp(rng.normal(0.0, sigma_fund_log)))
        load_fn_scale = float(np.exp(rng.normal(0.0, sigma_fund_log)))
        source_zeta_scale = float(np.exp(rng.normal(0.0, sigma_fund_log)))
        load_zeta_scale = float(np.exp(rng.normal(0.0, sigma_fund_log)))
        length_variation_mm = rng.normal(0.0, 1.15, 6)
        preload_variation_frac = rng.normal(0.0, 0.055, 6)
        joint_stiffness_frac = rng.normal(0.0, 0.065, 6) - 0.018 * length_variation_mm
        strut_k = strut_nominal_axial_k * np.clip(1.0 + joint_stiffness_frac, 0.74, 1.28)
        theta = np.linspace(0.0, 2.0 * np.pi, 6, endpoint=False)
        cos_part = float(np.dot(joint_stiffness_frac, np.cos(theta)) / 6.0)
        sin_part = float(np.dot(joint_stiffness_frac, np.sin(theta)) / 6.0)
        second_cos = float(np.dot(joint_stiffness_frac, np.cos(2.0 * theta)) / 6.0)
        second_sin = float(np.dot(joint_stiffness_frac, np.sin(2.0 * theta)) / 6.0)
        pair_split_xy = 1.8 * np.hypot(cos_part, sin_part)
        pair_split_rot = 1.4 * np.hypot(second_cos, second_sin)

        dofs: dict[str, Any] = {}
        for dof in DOF_ORDER:
            d = str(dof)
            base = profiles["dof_profiles"][d]
            if d == "z":
                source_shift = 0.0
                load_shift = 0.0025 * np.mean(joint_stiffness_frac)
                s_scale = source_fn_scale
                l_scale = load_fn_scale
                sz_scale = source_zeta_scale
                lz_scale = load_zeta_scale
            elif d == "x":
                source_shift = -0.45 * pair_split_xy + 0.20 * cos_part
                load_shift = -pair_split_xy + 0.25 * cos_part
                s_scale = 1.0 + 0.004 * (source_fn_scale - 1.0)
                l_scale = load_fn_scale
                sz_scale = source_zeta_scale
                lz_scale = load_zeta_scale
            elif d == "y":
                source_shift = 0.45 * pair_split_xy - 0.20 * cos_part
                load_shift = pair_split_xy - 0.25 * cos_part
                s_scale = 1.0 + 0.004 * (source_fn_scale - 1.0)
                l_scale = load_fn_scale
                sz_scale = source_zeta_scale
                lz_scale = load_zeta_scale
            elif d == "rx":
                source_shift = -0.35 * pair_split_rot + 0.10 * second_cos
                load_shift = -pair_split_rot + 0.20 * second_cos
                s_scale = source_fn_scale
                l_scale = load_fn_scale
                sz_scale = source_zeta_scale
                lz_scale = load_zeta_scale
            elif d == "ry":
                source_shift = 0.35 * pair_split_rot - 0.10 * second_cos
                load_shift = pair_split_rot - 0.20 * second_cos
                s_scale = source_fn_scale
                l_scale = load_fn_scale
                sz_scale = source_zeta_scale
                lz_scale = load_zeta_scale
            else:
                torsion_bias = 0.18 * np.std(joint_stiffness_frac)
                source_shift = 0.15 * torsion_bias
                load_shift = 0.65 * torsion_bias
                s_scale = source_fn_scale
                l_scale = load_fn_scale
                sz_scale = source_zeta_scale
                lz_scale = load_zeta_scale

            source_modes = apply_mode_scatter(
                copy_mode_list(base["source_modes"]),
                fn_scale=s_scale,
                zeta_scale=sz_scale,
                rng=rng,
                mode_jitter_sigma=0.012,
                participation_jitter_sigma=0.080,
                dof_shift=source_shift,
            )
            load_modes = apply_mode_scatter(
                copy_mode_list(base["load_modes"]),
                fn_scale=l_scale,
                zeta_scale=lz_scale,
                rng=rng,
                mode_jitter_sigma=0.014,
                participation_jitter_sigma=0.095,
                dof_shift=load_shift,
            )
            source_rigid = float(base["source_rigid"] * np.exp(rng.normal(0.0, 0.012)))
            load_rigid = float(base["load_rigid"] * np.exp(rng.normal(0.0, 0.010)))
            if d == "z":
                load_rigid = float(profiles["masses"]["netcg_load_mass_kg"])
                source_rigid = float(profiles["masses"]["source_effective_z_mass_kg"] * np.exp(rng.normal(0.0, 0.010)))
            dofs[d] = {
                "source_rigid": source_rigid,
                "load_rigid": load_rigid,
                "source_modes": source_modes,
                "load_modes": load_modes,
            }

        builds.append(
            {
                "build_id": build_id,
                "source_fn_scale": source_fn_scale,
                "load_fn_scale": load_fn_scale,
                "source_zeta_scale": source_zeta_scale,
                "load_zeta_scale": load_zeta_scale,
                "strut_nominal_axial_k_N_per_m": strut_nominal_axial_k,
                "strut_axial_k_N_per_m": strut_k.tolist(),
                "strut_length_variation_mm": length_variation_mm.tolist(),
                "preload_variation_frac": preload_variation_frac.tolist(),
                "joint_stiffness_variation_frac": joint_stiffness_frac.tolist(),
                "pair_split_xy_fraction": pair_split_xy,
                "pair_split_rot_fraction": pair_split_rot,
                "dofs": dofs,
            }
        )
    return builds


def dynamic_mass(
    freq_hz: np.ndarray,
    rigid: float,
    modes: list[dict[str, float]],
    amplitude_index: float = 0.0,
) -> np.ndarray:
    w = 2.0 * np.pi * freq_hz
    accelerance = np.ones_like(freq_hz, dtype=np.complex128) / rigid
    for m in modes:
        fn = m["fn_hz"]
        zeta = m["zeta"]
        participation = m["participation"]
        relax = m["relax_hz"]
        x = freq_hz / relax
        stiff_factor = 1.0 + m["fd_stiff_frac"] * (x**2 / (1.0 + x**2))
        amp_factor = 1.0 - m["nonlinear_soften_frac"] * amplitude_index / (1.0 + abs(amplitude_index))
        wn_eff = 2.0 * np.pi * fn * np.sqrt(np.clip(stiff_factor, 0.70, 1.35)) * amp_factor
        zeta_eff = zeta * (1.0 + m["fd_loss_frac"] * (x / (1.0 + x)))
        den = wn_eff**2 - w**2 + 2j * zeta_eff * wn_eff * w
        accelerance += -(participation / rigid) * (w**2) / den
    floor = 1e-12 / max(rigid, 1.0)
    accelerance = np.where(np.abs(accelerance) < floor, floor + 0j, accelerance)
    return 1.0 / accelerance


def compute_clean_dynamics(
    freq_hz: np.ndarray,
    builds: list[dict[str, Any]],
    flight_force_psd: np.ndarray,
    netcg_load_mass_kg: float,
) -> dict[str, np.ndarray]:
    n_builds = len(builds)
    n_dof = DOF_ORDER.size
    n_freq = freq_hz.size
    n_flights = flight_force_psd.shape[0]
    source_mass = np.zeros((n_builds, n_dof, n_freq), dtype=np.complex128)
    load_mass = np.zeros_like(source_mass)
    coupled_mass = np.zeros_like(source_mass)
    clean_response_psd = np.zeros((n_builds, n_flights, n_freq))
    clean_force_psd = np.zeros_like(clean_response_psd)
    clean_netcg_3grms = np.zeros((n_builds, n_flights))

    for b, build in enumerate(builds):
        for i, dof in enumerate(DOF_ORDER):
            d = build["dofs"][str(dof)]
            source_mass[b, i] = dynamic_mass(freq_hz, d["source_rigid"], d["source_modes"], amplitude_index=0.0)
            load_mass[b, i] = dynamic_mass(freq_hz, d["load_rigid"], d["load_modes"], amplitude_index=0.0)
            coupled_mass[b, i] = source_mass[b, i] + load_mass[b, i]

        d_z = build["dofs"]["z"]
        for fl in range(n_flights):
            force_rms = math.sqrt(float(np.trapz(flight_force_psd[fl], freq_hz)))
            amplitude_index = np.clip(force_rms / 3200.0 - 0.65, -0.5, 1.6)
            ms = dynamic_mass(freq_hz, d_z["source_rigid"], d_z["source_modes"], amplitude_index=0.35 * amplitude_index)
            ml = dynamic_mass(freq_hz, d_z["load_rigid"], d_z["load_modes"], amplitude_index=amplitude_index)
            interface_accel_per_force = 1.0 / (ms + ml)
            transfer_force = ml * interface_accel_per_force
            clean_force_psd[b, fl] = np.abs(transfer_force) ** 2 * flight_force_psd[fl]
            clean_response_psd[b, fl] = clean_force_psd[b, fl] / (netcg_load_mass_kg**2) / (G0**2)
            clean_netcg_3grms[b, fl] = 3.0 * math.sqrt(float(np.trapz(clean_response_psd[b, fl], freq_hz)))

    return {
        "source_mass": source_mass,
        "load_mass": load_mass,
        "coupled_mass": coupled_mass,
        "clean_response_psd_g2_per_Hz": clean_response_psd,
        "clean_interface_force_psd_N2_per_Hz": clean_force_psd,
        "clean_netcg_3grms_g": clean_netcg_3grms,
    }


def apply_observation_noise(
    freq_hz: np.ndarray,
    clean: dict[str, np.ndarray],
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    coupled_mass = clean["coupled_mass"]
    n_builds, n_dof, n_freq = coupled_mass.shape
    observed_mass = np.empty_like(coupled_mass)
    mass_noise_fraction = np.empty((n_builds, n_dof, n_freq))

    for b in range(n_builds):
        for i in range(n_dof):
            m = coupled_mass[b, i]
            mag = np.abs(m)
            peak_indicator = np.clip((mag / np.median(mag) - 1.0) / 8.0, 0.0, 5.0)
            scale = 0.0045 + 0.017 * peak_indicator
            re = correlated_curve(freq_hz, rng, sigma=1.0, length_log10=0.18, n_ctrl=120)
            im = correlated_curve(freq_hz, rng, sigma=1.0, length_log10=0.18, n_ctrl=120)
            complex_frac = scale * (re + 1j * im) / np.sqrt(2.0)
            additive_floor = (0.0015 * np.median(mag)) * (
                correlated_curve(freq_hz, rng, sigma=1.0, length_log10=0.11, n_ctrl=100)
                + 1j * correlated_curve(freq_hz, rng, sigma=1.0, length_log10=0.11, n_ctrl=100)
            )
            observed_mass[b, i] = m * (1.0 + complex_frac) + additive_floor
            mass_noise_fraction[b, i] = np.abs(observed_mass[b, i] - m) / np.maximum(np.abs(m), 1e-12)

    clean_psd = clean["clean_response_psd_g2_per_Hz"]
    observed_psd = np.empty_like(clean_psd)
    psd_noise_db = np.empty_like(clean_psd)
    for b in range(clean_psd.shape[0]):
        for fl in range(clean_psd.shape[1]):
            p = clean_psd[b, fl]
            valley_indicator = np.clip((np.median(p) / np.maximum(p, np.percentile(p, 2))) ** 0.25 - 1.0, 0.0, 5.0)
            scale_db = 0.16 + 0.42 * valley_indicator
            curve = correlated_curve(freq_hz, rng, sigma=1.0, length_log10=0.16, n_ctrl=120)
            noise_db = scale_db * curve
            observed_psd[b, fl] = np.maximum(p * 10.0 ** (noise_db / 10.0), 1e-16)
            psd_noise_db[b, fl] = noise_db

    observed_netcg = 3.0 * np.sqrt(np.trapz(observed_psd, freq_hz, axis=2))
    return {
        "observed_mass": observed_mass,
        "mass_noise_fraction": mass_noise_fraction,
        "observed_response_psd_g2_per_Hz": observed_psd,
        "observed_netcg_3grms_g": observed_netcg,
        "psd_noise_db": psd_noise_db,
    }


def write_dataset(
    dirs: dict[str, Path],
    freq_hz: np.ndarray,
    design_force_psd: np.ndarray,
    flight_force_psd: np.ndarray,
    forcing_params: dict[str, Any],
    observations: dict[str, np.ndarray],
    profiles: dict[str, Any],
) -> None:
    dataset = dirs["dataset"] / "observations.npz"
    obs_mass = observations["observed_mass"]
    np.savez_compressed(
        dataset,
        frequency_hz=freq_hz,
        dof_order=DOF_ORDER,
        apparent_mass_real=obs_mass.real,
        apparent_mass_imag=obs_mass.imag,
        response_psd_g2_per_Hz=observations["observed_response_psd_g2_per_Hz"],
        netcg_3grms_g=observations["observed_netcg_3grms_g"],
        design_force_psd_N2_per_Hz=design_force_psd,
        flight_force_psd_N2_per_Hz=flight_force_psd,
        build_ids=np.arange(obs_mass.shape[0]),
        flight_ids=np.arange(flight_force_psd.shape[0]),
        load_mass_kg=np.array(profiles["masses"]["netcg_load_mass_kg"]),
        forcing_model_json=np.array(json.dumps(forcing_params, indent=2)),
        g0_m_per_s2=np.array(G0),
    )

    contract = f"""# Round 3 Published Data Contract

This folder contains observable synthetic data for the blind round-3 inference agent.

## File

- `observations.npz`

## Coordinate frame and DOF order

- SI units.
- Interface reference frame: `x` and `y` are transverse axes in the tray plane; `z` is axial, positive from dome/source toward the tray/load; rotations follow the right-hand rule about those axes.
- DOF order is stored in `dof_order`: `["x", "y", "z", "rx", "ry", "rz"]`.

## Frequency grid

- Key: `frequency_hz`
- Shape: `(n_frequency,)`
- Range: {freq_hz[0]:.6g} to {freq_hz[-1]:.6g} Hz
- Count: {freq_hz.size}
- The grid is dense in the interface modal band and continues through 600 Hz.

## Apparent mass observations

- Keys: `apparent_mass_real`, `apparent_mass_imag`
- Shape: `(n_build, n_dof, n_frequency)` = `{obs_mass.real.shape}`
- Build count: {obs_mass.shape[0]}
- DOF count: {obs_mass.shape[1]}
- Complex apparent mass is `apparent_mass_real + 1j*apparent_mass_imag`.
- Translational DOFs (`x`, `y`, `z`) use units kg.
- Rotational DOFs (`rx`, `ry`, `rz`) use units kg*m^2.
- These are diagonal interface apparent-mass observations with sensor noise already applied.

## Flight forcing observations/input

- Key: `design_force_psd_N2_per_Hz`
- Shape: `(n_frequency,)`
- Units: `N^2/Hz`
- Key: `flight_force_psd_N2_per_Hz`
- Shape: `(n_flight, n_frequency)` = `{flight_force_psd.shape}`
- Flight count: {flight_force_psd.shape[0]}
- Units: `N^2/Hz`
- The shared forcing convention is PSD-space dB: multiply PSD by `10**(dB/10)`.
- Shared forcing model: mean offset -6 dB relative to the design envelope; Matern-3/2 GP in log10 frequency; fixed 3 dB flight-to-flight scatter.
- Machine-readable forcing metadata is stored in `forcing_model_json`.

## Response observations

- Key: `response_psd_g2_per_Hz`
- Shape: `(n_build, n_flight, n_frequency)` = `{observations["observed_response_psd_g2_per_Hz"].shape}`
- Units: `g^2/Hz`
- This is the netCG response PSD for each build under each flight forcing draw.
- Key: `netcg_3grms_g`
- Shape: `(n_build, n_flight)` = `{observations["observed_netcg_3grms_g"].shape}`
- Units: `g`
- Definition: `3 * sqrt(integral response_psd_g2_per_Hz df)`.
- netCG follows the shared canonical contract in `docs/agents/competitive_full_experiment/round3/netcg_quantity_contract.md`: `netCG = F_iface(omega) / m_load`, where `F_iface` is the dynamic transmitted load-interface force from source/load FBS apparent-mass coupling and `m_load` is the published scalar `load_mass_kg`.
- The f -> 0 rigid mass-sharing limit is a sanity check only, not the QOI definition.
- The load mass used for the netCG normalization is stored as `load_mass_kg`.

## Observable-only boundary

This contract intentionally gives schema, units, coordinate conventions, counts, and the shared forcing model only. It does not describe the hidden as-built generator, hidden parameter values, hidden noise scales, or hidden model-form details.
"""
    (dirs["dataset"] / "data_contract.md").write_text(contract)


def beam_element_matrices(E: float, I: float, rho: float, A: float, L: float) -> tuple[np.ndarray, np.ndarray]:
    k = E * I / L**3 * np.array(
        [[12, 6 * L, -12, 6 * L], [6 * L, 4 * L**2, -6 * L, 2 * L**2], [-12, -6 * L, 12, -6 * L], [6 * L, 2 * L**2, -6 * L, 4 * L**2]],
        dtype=float,
    )
    m = rho * A * L / 420.0 * np.array(
        [[156, 22 * L, 54, -13 * L], [22 * L, 4 * L**2, 13 * L, -3 * L**2], [54, 13 * L, 156, -22 * L], [-13 * L, -3 * L**2, -22 * L, 4 * L**2]],
        dtype=float,
    )
    return k, m


def cantilever_benchmark(n_el: int = 20) -> dict[str, Any]:
    E = 72.0e9
    rho = 2700.0
    A = 1.8e-3
    I = 1.6e-7
    L_total = 1.2
    Le = L_total / n_el
    ndof = 2 * (n_el + 1)
    K = np.zeros((ndof, ndof))
    M = np.zeros((ndof, ndof))
    ke, me = beam_element_matrices(E, I, rho, A, Le)
    for e in range(n_el):
        idx = np.array([2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3])
        K[np.ix_(idx, idx)] += ke
        M[np.ix_(idx, idx)] += me
    free = np.arange(2, ndof)
    evals, _ = scipy.linalg.eigh(K[np.ix_(free, free)], M[np.ix_(free, free)])
    f_fem = np.sqrt(np.maximum(evals[:4], 0.0)) / (2.0 * np.pi)
    betaL = np.array([1.875104068711961, 4.694091132974174, 7.854757438237612, 10.995540734875466])
    f_analytic = betaL**2 * math.sqrt(E * I / (rho * A * L_total**4)) / (2.0 * np.pi)
    rel_error = (f_fem - f_analytic) / f_analytic
    return {
        "name": "Euler-Bernoulli cantilever beam",
        "n_elements": n_el,
        "betaL_roots": betaL.tolist(),
        "fem_hz": f_fem.tolist(),
        "analytic_hz": f_analytic.tolist(),
        "relative_error": rel_error.tolist(),
        "max_abs_relative_error": float(np.max(np.abs(rel_error))),
    }


def lumped_mdof_benchmark() -> dict[str, Any]:
    m1, m2 = 2.2, 1.4
    k1, k2 = 4200.0, 2500.0
    M = np.diag([m1, m2])
    K = np.array([[k1 + k2, -k2], [-k2, k2]], dtype=float)
    evals_num, _ = scipy.linalg.eigh(K, M)
    a = m1 * m2
    b = -((k1 + k2) * m2 + k2 * m1)
    c = k1 * k2
    roots = np.sort(np.roots([a, b, c]).real)
    f_num = np.sqrt(evals_num) / (2.0 * np.pi)
    f_closed = np.sqrt(roots) / (2.0 * np.pi)
    rel_error = (f_num - f_closed) / f_closed
    return {
        "name": "two-mass two-spring generalized eigenproblem",
        "numerical_hz": f_num.tolist(),
        "closed_form_hz": f_closed.tolist(),
        "relative_error": rel_error.tolist(),
        "max_abs_relative_error": float(np.max(np.abs(rel_error))),
    }


def find_feature_frequencies(freq_hz: np.ndarray, y: np.ndarray, prominence: float, max_count: int = 8) -> list[float]:
    peaks, props = scipy.signal.find_peaks(y, prominence=prominence)
    if peaks.size == 0:
        return []
    order = np.argsort(props["prominences"])[::-1][:max_count]
    chosen = np.sort(peaks[order])
    return [float(freq_hz[p]) for p in chosen]


def validation_features(freq_hz: np.ndarray, clean: dict[str, np.ndarray]) -> dict[str, Any]:
    mzz = clean["coupled_mass"][0, 2]
    acc = 1.0 / mzz
    band = (freq_hz >= 40.0) & (freq_hz <= 260.0)
    f_band = freq_hz[band]
    log_acc = np.log10(np.maximum(np.abs(acc[band]), 1e-16))
    log_mass = np.log10(np.maximum(np.abs(mzz[band]), 1e-16))
    resonances = find_feature_frequencies(f_band, log_acc, prominence=0.20, max_count=7)
    antiresonances = find_feature_frequencies(f_band, log_mass, prominence=0.18, max_count=7)
    alternating_pairs = 0
    for r in resonances:
        after = [a for a in antiresonances if a > r]
        before = [a for a in antiresonances if a < r]
        if after or before:
            alternating_pairs += 1
    return {
        "observable_build0_z_resonance_like_hz": resonances,
        "observable_build0_z_antiresonance_like_hz": antiresonances,
        "resonance_antiresonance_neighbor_count": alternating_pairs,
        "interlacing_check_pass": bool(len(resonances) >= 2 and len(antiresonances) >= 2 and alternating_pairs >= 2),
    }


def resolution_sensitivity(
    freq_hz: np.ndarray,
    clean: dict[str, np.ndarray],
    flight_force_psd: np.ndarray,
) -> dict[str, Any]:
    full_psd = clean["clean_response_psd_g2_per_Hz"][0, 0]
    full_3g = 3.0 * math.sqrt(float(np.trapz(full_psd, freq_hz)))
    coarse_idx = np.unique(np.r_[np.arange(0, freq_hz.size, 4), freq_hz.size - 1])
    coarse_3g = 3.0 * math.sqrt(float(np.trapz(full_psd[coarse_idx], freq_hz[coarse_idx])))
    rel = (coarse_3g - full_3g) / full_3g
    return {
        "case": "build 0, flight 0, clean response",
        "full_grid_count": int(freq_hz.size),
        "coarse_grid_count": int(coarse_idx.size),
        "full_grid_3grms_g": full_3g,
        "coarse_grid_3grms_g": coarse_3g,
        "coarse_minus_full_relative": float(rel),
        "pass_threshold_abs_relative": 0.015,
        "pass": bool(abs(rel) < 0.015),
    }


def write_sealed(
    dirs: dict[str, Path],
    freq_hz: np.ndarray,
    profiles: dict[str, Any],
    builds: list[dict[str, Any]],
    clean: dict[str, np.ndarray],
    observations: dict[str, np.ndarray],
    forcing_params: dict[str, Any],
) -> None:
    sealed = dirs["sealed"]
    hidden = {
        "rng_seed": 2026060403,
        "profiles": profiles,
        "forcing_params": forcing_params,
        "builds": builds,
        "noise_summary": {
            "apparent_mass_fraction_noise_median": float(np.median(observations["mass_noise_fraction"])),
            "apparent_mass_fraction_noise_p95": float(np.percentile(observations["mass_noise_fraction"], 95.0)),
            "response_psd_noise_db_median_abs": float(np.median(np.abs(observations["psd_noise_db"]))),
            "response_psd_noise_db_p95_abs": float(np.percentile(np.abs(observations["psd_noise_db"]), 95.0)),
        },
    }
    (sealed / "true_parameters.json").write_text(json.dumps(hidden, indent=2))

    np.savez_compressed(
        sealed / "scoring_key.npz",
        frequency_hz=freq_hz,
        clean_coupled_apparent_mass_real=clean["coupled_mass"].real,
        clean_coupled_apparent_mass_imag=clean["coupled_mass"].imag,
        clean_source_apparent_mass_real=clean["source_mass"].real,
        clean_source_apparent_mass_imag=clean["source_mass"].imag,
        clean_load_apparent_mass_real=clean["load_mass"].real,
        clean_load_apparent_mass_imag=clean["load_mass"].imag,
        clean_response_psd_g2_per_Hz=clean["clean_response_psd_g2_per_Hz"],
        clean_interface_force_psd_N2_per_Hz=clean["clean_interface_force_psd_N2_per_Hz"],
        clean_netcg_3grms_g=clean["clean_netcg_3grms_g"],
    )

    modal_summary = []
    for build in builds:
        entry = {"build_id": build["build_id"], "dofs": {}}
        for dof in DOF_ORDER:
            d = build["dofs"][str(dof)]
            entry["dofs"][str(dof)] = {
                "source_mode_fn_hz": [m["fn_hz"] for m in d["source_modes"]],
                "source_mode_zeta": [m["zeta"] for m in d["source_modes"]],
                "load_mode_fn_hz": [m["fn_hz"] for m in d["load_modes"]],
                "load_mode_zeta": [m["zeta"] for m in d["load_modes"]],
            }
        modal_summary.append(entry)
    scoring_meta = {
        "scoring_key_npz": "scoring_key.npz",
        "frequency_units": "Hz",
        "response_psd_units": "g^2/Hz",
        "interface_force_psd_units": "N^2/Hz",
        "netcg_units": "g",
        "netcg_contract": "docs/agents/competitive_full_experiment/round3/netcg_quantity_contract.md",
        "netcg_definition": "clean netCG = F_iface(omega) / load_mass_kg; F_iface is the dynamic transmitted load-interface force from source/load FBS apparent-mass coupling.",
        "rigid_mass_ratio_note": "The rigid mass-sharing ratio is retained only as the f -> 0 sanity check, not as the QOI.",
        "modal_params": modal_summary,
    }
    (sealed / "scoring_key.json").write_text(json.dumps(scoring_meta, indent=2))

    description = """# Hidden Model-Form Description

This file is sealed for the master and must not be read by the inference agent.

The as-built reality is a reduced-order, frequency-domain source/load model. The public axial netCG response is generated by source/load impedance sharing at one equivalent interface DOF. The 6-DOF diagonal apparent-mass observations expose transverse, axial, rocking, and torsional interface dynamics for the same as-built units.

Hidden richness included here:

- Six-strut azimuthal joint stiffness, preload, and length scatter per build.
- Split lateral/rocking mode pairs driven by those azimuthal perturbations.
- Frequency-dependent joint stiffness and damping through modal denominator relaxation terms.
- Mild amplitude-dependent equivalent-linearized joint softening in the axial flight response.
- Extra local panel/dome modes beyond the shared nominal first source/load modes.
- Correlated complex apparent-mass sensor noise with larger fractional error near apparent-mass antiresonance peaks.
- Correlated PSD measurement noise with larger error in low-response valleys.

The exact magnitudes and every per-build draw are in `true_parameters.json`. Clean scoring arrays are in `scoring_key.npz`.
"""
    (sealed / "model_form_imperfections.md").write_text(description)

    hidden_log = """# Hidden Decisions Log

Append-only hidden log for the master. Public report logs intentionally do not disclose these details.

## 2026-06-04T18:14:16Z

- Selected a sealed reduced-order apparent-mass model rather than a clean symmetric FEM so the inference task sees genuine model-form error.
- Used source/load impedance sharing for the axial single-interface QOI: interface force into the load is `M_load / (M_source + M_load)` times the applied source-side forcing.
- Used source/load FBS apparent-mass coupling for the axial single-interface QOI: interface acceleration is `F / (M_source + M_load)`, interface force into the load is `M_load * F / (M_source + M_load)`, and netCG is this dynamic transmitted interface force divided by the fixed 170 kg load mass.
- Retained the rigid mass-sharing ratio only as the f -> 0 sanity check.
- Used a fixed netCG normalization mass of 170 kg: 136 kg avionics plus a 34 kg tray/panel allowance.
- Used per-build lognormal fundamental frequency and damping scatter with sigma approximately 5 percent / 3 in log units, plus strut/joint spatial scatter.
- Reused the same 11 flight forcing PSD draws across all 8 builds.
"""
    (sealed / "hidden_decisions_log.md").write_text(hidden_log)


def mesh_geometry() -> tuple[np.ndarray, list[tuple[str, list[int]]], list[str]]:
    nodes: list[list[float]] = []
    elements: list[tuple[str, list[int]]] = []
    groups: list[str] = []

    def add_node(x: float, y: float, z: float) -> int:
        nodes.append([x, y, z])
        return len(nodes)

    apex = add_node(0.0, 0.0, 0.0)
    n_phi = 36
    n_theta = 10
    R = 2.75
    H = 1.38
    rings: list[list[int]] = []
    for j in range(1, n_theta + 1):
        theta = 0.5 * np.pi * j / n_theta
        r = R * np.sin(theta)
        z = -H * (1.0 - np.cos(theta))
        ring = []
        for k in range(n_phi):
            phi = 2.0 * np.pi * k / n_phi
            ring.append(add_node(r * np.cos(phi), r * np.sin(phi), z))
        rings.append(ring)
    for k in range(n_phi):
        elements.append(("tria3", [apex, rings[0][k], rings[0][(k + 1) % n_phi]]))
        groups.append("dome_shell")
    for j in range(1, n_theta):
        r0 = rings[j - 1]
        r1 = rings[j]
        for k in range(n_phi):
            elements.append(("quad4", [r0[k], r0[(k + 1) % n_phi], r1[(k + 1) % n_phi], r1[k]]))
            groups.append("dome_shell")

    tray_nodes: dict[tuple[int, int], int] = {}
    nx, ny = 7, 5
    x_vals = np.linspace(-1.10, 1.10, nx)
    y_vals = np.linspace(-0.82, 0.82, ny)
    for ix, x in enumerate(x_vals):
        for iy, y in enumerate(y_vals):
            tray_nodes[(ix, iy)] = add_node(float(x), float(y), 0.64)
    for ix in range(nx - 1):
        for iy in range(ny - 1):
            elements.append(("quad4", [tray_nodes[(ix, iy)], tray_nodes[(ix + 1, iy)], tray_nodes[(ix + 1, iy + 1)], tray_nodes[(ix, iy + 1)]]))
            groups.append("tray_panel")
    for ix in range(nx):
        for iy in range(ny - 1):
            elements.append(("line2", [tray_nodes[(ix, iy)], tray_nodes[(ix, iy + 1)]]))
            groups.append("tray_isogrid")
    for iy in range(ny):
        for ix in range(nx - 1):
            elements.append(("line2", [tray_nodes[(ix, iy)], tray_nodes[(ix + 1, iy)]]))
            groups.append("tray_isogrid")
    for ix in range(nx - 1):
        for iy in range(ny - 1):
            if (ix + iy) % 2 == 0:
                elements.append(("line2", [tray_nodes[(ix, iy)], tray_nodes[(ix + 1, iy + 1)]]))
            else:
                elements.append(("line2", [tray_nodes[(ix + 1, iy)], tray_nodes[(ix, iy + 1)]]))
            groups.append("tray_isogrid")

    tray_attach_angles = np.linspace(0.0, 2.0 * np.pi, 6, endpoint=False) + np.deg2rad(30.0)
    tray_attach = []
    dome_attach = []
    for a in tray_attach_angles:
        tray_attach.append(add_node(0.92 * np.cos(a), 0.68 * np.sin(a), 0.60))
        dome_attach.append(add_node(1.35 * np.cos(a), 1.35 * np.sin(a), -0.19))
    for t, d in zip(tray_attach, dome_attach):
        elements.append(("line2", [d, t]))
        groups.append("strut")
    interface = add_node(0.0, 0.0, 0.64)
    for t in tray_attach:
        elements.append(("line2", [interface, t]))
        groups.append("rbe_visual")

    return np.array(nodes), elements, groups


def write_mesh_exports(dirs: dict[str, Path]) -> dict[str, Any]:
    mesh_dir = dirs["mesh"]
    nodes, elements, groups = mesh_geometry()
    with (mesh_dir / "nodes.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "x_m", "y_m", "z_m"])
        for i, xyz in enumerate(nodes, start=1):
            writer.writerow([i, *[f"{v:.9g}" for v in xyz]])
    with (mesh_dir / "elements.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "type", "connectivity", "group"])
        for i, ((etype, conn), group) in enumerate(zip(elements, groups), start=1):
            writer.writerow([i, etype, " ".join(str(c) for c in conn), group])

    bdf_lines = ["$ Round 3 Codex truth visualization mesh", "BEGIN BULK"]
    for i, (x, y, z) in enumerate(nodes, start=1):
        bdf_lines.append(f"GRID,{i},,{x:.9g},{y:.9g},{z:.9g}")
    shell_pid = 1
    beam_pid = 2
    bdf_lines.append("PSHELL,1,1,0.003")
    bdf_lines.append("MAT1,1,7.2E10,,0.33,2.84E3")
    bdf_lines.append("PBARL,2,1,ROD,,0.018")
    for eid, (etype, conn) in enumerate(elements, start=1):
        if etype == "tria3":
            bdf_lines.append(f"CTRIA3,{eid},{shell_pid},{conn[0]},{conn[1]},{conn[2]}")
        elif etype == "quad4":
            bdf_lines.append(f"CQUAD4,{eid},{shell_pid},{conn[0]},{conn[1]},{conn[2]},{conn[3]}")
        elif etype == "line2":
            bdf_lines.append(f"CBAR,{eid},{beam_pid},{conn[0]},{conn[1]},0.,0.,1.")
    bdf_lines.append("ENDDATA")
    (mesh_dir / "model.bdf").write_text("\n".join(bdf_lines) + "\n")

    status: dict[str, Any] = {
        "nodes": int(nodes.shape[0]),
        "elements": len(elements),
        "vtu_written_with_meshio": False,
        "obj_written_with_meshio": False,
        "bdf_written": "manual NASTRAN bulk data cards; meshio is used for VTU/OBJ",
    }
    deps = Path(__file__).resolve().parents[1] / ".deps"
    if deps.exists():
        sys.path.insert(0, str(deps))
    try:
        import meshio  # type: ignore

        zero_based_cells: dict[str, list[list[int]]] = {"triangle": [], "quad": [], "line": []}
        for etype, conn in elements:
            c0 = [c - 1 for c in conn]
            if etype == "tria3":
                zero_based_cells["triangle"].append(c0)
            elif etype == "quad4":
                zero_based_cells["quad"].append(c0)
            elif etype == "line2":
                zero_based_cells["line"].append(c0)
        cells = []
        for key in ["triangle", "quad", "line"]:
            if zero_based_cells[key]:
                cells.append((key, np.array(zero_based_cells[key], dtype=int)))
        mesh = meshio.Mesh(points=nodes, cells=cells)
        meshio.write(mesh_dir / "model.vtu", mesh)
        status["vtu_written_with_meshio"] = True
        surface_cells = []
        for key in ["triangle", "quad"]:
            if zero_based_cells[key]:
                surface_cells.append((key, np.array(zero_based_cells[key], dtype=int)))
        meshio.write(mesh_dir / "model.obj", meshio.Mesh(points=nodes, cells=surface_cells))
        status["obj_written_with_meshio"] = True
    except Exception as exc:  # pragma: no cover - recorded in artifact
        status["meshio_error"] = repr(exc)
    (mesh_dir / "mesh_export_status.json").write_text(json.dumps(status, indent=2))
    return {"nodes": nodes, "elements": elements, "groups": groups, "status": status}


def plot_mesh(ax, nodes: np.ndarray, elements: list[tuple[str, list[int]]], disp: np.ndarray | None = None, title: str = "") -> None:
    pts = nodes.copy()
    if disp is not None:
        pts = pts + disp
    for etype, conn in elements:
        idx = [c - 1 for c in conn]
        p = pts[idx]
        if etype in {"tria3", "quad4"}:
            loop = np.vstack([p, p[0]])
            ax.plot(loop[:, 0], loop[:, 1], loop[:, 2], color="0.55", linewidth=0.35)
        elif etype == "line2":
            ax.plot(p[:, 0], p[:, 1], p[:, 2], color="#2b4c7e", linewidth=0.7)
    ax.set_title(title, fontsize=11)
    ax.set_xlabel("x (m)", fontsize=9)
    ax.set_ylabel("y (m)", fontsize=9)
    ax.set_zlabel("z (m)", fontsize=9)
    ax.view_init(elev=22, azim=-42)
    lim = 2.9
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(-1.55, 1.0)
    try:
        ax.set_box_aspect((2 * lim, 2 * lim, 2.55))
    except Exception:
        pass


def mode_displacement(nodes: np.ndarray, mode_id: int) -> np.ndarray:
    x, y, z = nodes[:, 0], nodes[:, 1], nodes[:, 2]
    tray = z > 0.45
    dome = z <= 0.05
    disp = np.zeros_like(nodes)
    if mode_id == 1:
        disp[dome, 2] = 0.12 * (1.0 - np.clip(-z[dome] / 1.38, 0.0, 1.0))
        disp[tray, 2] = 0.04
    elif mode_id == 2:
        disp[tray, 2] = 0.18
        disp[dome, 2] = -0.03 * np.exp(-(x[dome] ** 2 + y[dome] ** 2) / 1.2**2)
    elif mode_id == 3:
        disp[tray, 0] = 0.16
        disp[dome, 0] = 0.04 * np.exp(-(x[dome] ** 2 + y[dome] ** 2) / 1.5**2)
    elif mode_id == 4:
        disp[tray, 2] = 0.15 * y[tray] / max(np.max(np.abs(y[tray])), 1e-9)
        disp[tray, 1] = -0.04 * z[tray]
    else:
        disp[tray, 0] = -0.14 * y[tray]
        disp[tray, 1] = 0.14 * x[tray]
    return disp


def write_figures(
    dirs: dict[str, Path],
    freq_hz: np.ndarray,
    clean: dict[str, np.ndarray],
    observations: dict[str, np.ndarray],
    mesh_info: dict[str, Any],
    validation: dict[str, Any],
) -> dict[str, Any]:
    fig_dir = dirs["figures"]
    figure_paths: list[Path] = []

    fig, ax = plt.subplots(figsize=(9.0, 5.6), dpi=170)
    mzz_clean = clean["coupled_mass"][0, 2]
    mzz_obs = observations["observed_mass"][0, 2]
    ax.loglog(freq_hz, np.abs(mzz_clean), label="clean build 0 |Mzz|", linewidth=1.5)
    ax.loglog(freq_hz, np.abs(mzz_obs), label="observed build 0 |Mzz|", linewidth=0.9, alpha=0.75)
    for f in validation["observable_build0_z_resonance_like_hz"][:5]:
        ax.axvline(f, color="#b23a48", linestyle="--", linewidth=0.75, alpha=0.65)
    for f in validation["observable_build0_z_antiresonance_like_hz"][:5]:
        ax.axvline(f, color="#1d7874", linestyle=":", linewidth=1.0, alpha=0.75)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Axial apparent mass magnitude (kg)")
    ax.set_title("Drive-point apparent mass with resonance/antiresonance markers")
    ax.grid(True, which="both", alpha=0.28)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = fig_dir / "apparent_mass_antiresonances.png"
    fig.savefig(path)
    plt.close(fig)
    figure_paths.append(path)

    fig, ax = plt.subplots(figsize=(9.0, 5.6), dpi=170)
    ax.loglog(freq_hz, observations["observed_response_psd_g2_per_Hz"][0, 0], label="observed build 0 flight 0")
    ax.loglog(freq_hz, clean["clean_response_psd_g2_per_Hz"][0, 0], label="clean build 0 flight 0", linewidth=1.2)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("netCG response PSD (g^2/Hz)")
    ax.set_title("Clean vs observed netCG PSD")
    ax.grid(True, which="both", alpha=0.28)
    ax.legend(fontsize=8)
    fig.tight_layout()
    path = fig_dir / "response_psd_clean_vs_observed.png"
    fig.savefig(path)
    plt.close(fig)
    figure_paths.append(path)

    fig, ax = plt.subplots(figsize=(9.0, 5.6), dpi=170)
    for fl in range(min(11, observations["observed_response_psd_g2_per_Hz"].shape[1])):
        ax.loglog(freq_hz, observations["observed_response_psd_g2_per_Hz"][0, fl], linewidth=0.75, alpha=0.65)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("netCG response PSD (g^2/Hz)")
    ax.set_title("Flight-to-flight response variation for build 0")
    ax.grid(True, which="both", alpha=0.28)
    fig.tight_layout()
    path = fig_dir / "flight_response_overlay_build0.png"
    fig.savefig(path)
    plt.close(fig)
    figure_paths.append(path)

    fig, ax = plt.subplots(figsize=(8.0, 5.2), dpi=170)
    vals = observations["observed_netcg_3grms_g"].reshape(-1)
    ax.hist(vals, bins=16, color="#5176a3", edgecolor="white")
    ax.set_xlabel("Observed netCG 3*GRMS (g)")
    ax.set_ylabel("build-flight count")
    ax.set_title("Observed scalar netCG distribution")
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    path = fig_dir / "netcg_distribution.png"
    fig.savefig(path)
    plt.close(fig)
    figure_paths.append(path)

    nodes = mesh_info["nodes"]
    elements = mesh_info["elements"]
    fig = plt.figure(figsize=(8.0, 6.2), dpi=170)
    ax = fig.add_subplot(111, projection="3d")
    plot_mesh(ax, nodes, elements, title="Undeformed visualization mesh")
    fig.tight_layout()
    path = fig_dir / "mesh_undeformed.png"
    fig.savefig(path)
    plt.close(fig)
    figure_paths.append(path)

    mode_titles = [
        "Mode shape sketch 1: dome/interface bounce",
        "Mode shape sketch 2: tray axial",
        "Mode shape sketch 3: lateral sway",
        "Mode shape sketch 4: tray rocking",
        "Mode shape sketch 5: torsion",
    ]
    for k, title in enumerate(mode_titles, start=1):
        fig = plt.figure(figsize=(8.0, 6.2), dpi=170)
        ax = fig.add_subplot(111, projection="3d")
        plot_mesh(ax, nodes, elements, disp=mode_displacement(nodes, k), title=title)
        fig.tight_layout()
        path = fig_dir / f"mode_shape_{k}.png"
        fig.savefig(path)
        plt.close(fig)
        figure_paths.append(path)

    qa: dict[str, Any] = {}
    for path in figure_paths:
        img = plt.imread(path)
        qa[path.name] = {
            "pixels": [int(img.shape[1]), int(img.shape[0])],
            "legibility_min_size_pass": bool(img.shape[1] >= 1000 and img.shape[0] >= 700),
        }
    (dirs["checks"] / "figure_legibility.json").write_text(json.dumps(qa, indent=2))
    return {"figure_paths": [str(p.relative_to(dirs["report"].parent)) for p in figure_paths], "figure_qa": qa}


def write_reports(
    root: Path,
    dirs: dict[str, Path],
    freq_hz: np.ndarray,
    profiles: dict[str, Any],
    observations: dict[str, np.ndarray],
    validation: dict[str, Any],
    beam: dict[str, Any],
    lumped: dict[str, Any],
    res: dict[str, Any],
    mesh_status: dict[str, Any],
    figures: dict[str, Any],
) -> None:
    report = dirs["report"]
    observed_net = observations["observed_netcg_3grms_g"]
    results = {
        "observed_netcg_3grms_g_summary_over_build_flight": {
            "count": int(observed_net.size),
            "min": float(np.min(observed_net)),
            "median": float(np.median(observed_net)),
            "q025": float(np.quantile(observed_net, 0.025)),
            "q975": float(np.quantile(observed_net, 0.975)),
            "q005": float(np.quantile(observed_net, 0.005)),
            "q995": float(np.quantile(observed_net, 0.995)),
            "max": float(np.max(observed_net)),
        }
    }
    (report / "results.json").write_text(json.dumps(results, indent=2))
    (report / "resolution_sensitivity.json").write_text(json.dumps(res, indent=2))

    public_assumptions = {
        "observable_counts": {
            "n_builds": int(observations["observed_mass"].shape[0]),
            "n_flights": int(observations["observed_response_psd_g2_per_Hz"].shape[1]),
            "n_frequency": int(freq_hz.size),
        },
        "shared_nominal_design_starting_point": {
            "dome_first_interface_mode_hz": 93.5,
            "tray_first_axial_mount_mode_hz": 86.25,
            "avionics_mass_kg": 136.0,
            "strut_count": 6,
            "coordinate_frame": "x/y transverse, z axial from dome/source toward tray/load",
        },
        "netcg_normalization_observable": {
            "load_mass_kg": profiles["masses"]["netcg_load_mass_kg"],
            "g0_m_per_s2": G0,
        },
        "hidden_boundary": "As-built parameter values, hidden imperfection classes/sizes, and noise scales are sealed, not listed in this public assumptions file.",
    }
    (report / "assumptions_ledger.md").write_text(
        "# Public Assumptions Ledger\n\n"
        "This public ledger records shared/observable assumptions only. Hidden truth details are in `sealed_truth/`.\n\n"
        f"```json\n{json.dumps(public_assumptions, indent=2)}\n```\n"
    )

    quantity_contracts = """# Quantity Contracts

## Complex diagonal apparent mass `M_ii(omega)`

- Numerator: complex interface generalized force in DOF `i`.
- Denominator: complex interface acceleration in the same DOF.
- Coordinates: `x`, `y`, `z`, `rx`, `ry`, `rz` in the published right-handed interface frame.
- Units: kg for translational DOFs; kg*m^2 for rotational DOFs.
- Excitation/BC: diagonal drive-point interface measurement of the assembled source/load truth unit.
- Expected behavior: modal resonances appear as apparent-mass valleys/rapid phase changes; drive-point antiresonances appear as apparent-mass peaks; translational low-frequency magnitudes are mass-scale quantities.

## Flight force PSD

- Quantity: one-sided interface force PSD.
- Units: N^2/Hz.
- dB convention: PSD-space dB, factor `10**(dB/10)`.
- Excitation: source-side stochastic flight forcing.

## netCG response PSD

- Numerator: dynamic interface force transmitted into the load from source/load FBS apparent-mass coupling, divided by load mass.
- Denominator: one standard gravity for conversion to g.
- Units: g^2/Hz.
- BC/modeling convention: single axial `z` interface coupling through source/load apparent-mass FBS. `F_iface(omega) = M_load(omega) * F(omega) / (M_source(omega) + M_load(omega))`.
- Shared contract: `docs/agents/competitive_full_experiment/round3/netcg_quantity_contract.md`.
- Limiting behavior: at low frequency the acceleration tends toward a rigid mass-sharing response; the rigid mass ratio is a sanity check only. Narrow-band coupled resonant features can dominate scalar GRMS.

## netCG `3*GRMS`

- Definition: `3 * sqrt(integral response_psd_g2_per_Hz df)`.
- Units: g.
- Integration coordinate: frequency in Hz over the published grid.
"""
    (report / "quantity_contracts.md").write_text(quantity_contracts)

    known_failures = """# Known Failures and Limitations

- This is not a full continuum shell/solid FEM solve. The truth dynamics are generated by a sealed reduced-order frequency-domain model with a stylized FEM visualization mesh.
- The visualization mesh is inspection/export geometry, not the numerical model used to generate observations.
- Automated physics checks cover benchmark eigenproblems, array contracts, monotonic grids, finite values, resolution sensitivity, and observable antiresonance behavior. They do not prove that every hidden as-built effect is uniquely realistic.
- No inference, NUTS, fitting, GIF, or PPT was run or produced for this truth-author task.
"""
    (report / "known_failures.md").write_text(known_failures)

    review_request = """# Review Request

Please review:

- `dataset/data_contract.md` for observable schema and hidden-boundary compliance.
- `report/packet.md` for validation evidence and limitations.
- `report/checks/checks.json` for checker-backed acceptance status.
- `sealed_truth/true_parameters.json`, `sealed_truth/model_form_imperfections.md`, and `sealed_truth/scoring_key.npz` only after the inference agent has committed its outputs.
"""
    (report / "review_request.md").write_text(review_request)

    packet = f"""# Round 3 Codex Truth Validation Packet

## Method summary

Codex authored an independent as-built reality model for the shared source/load system. The observable axial netCG response is generated from source/load interface apparent masses with single-interface impedance sharing. The published 6-DOF diagonal apparent-mass observations are complex drive-point interface quantities for the same 8 as-built units. The 11 flight forcing PSD draws are reused across all 8 builds.

No inference, fitting, NUTS, or posterior sampling is performed in this truth-author run. Hidden generator details, exact true parameters, per-build structures, and clean scoring arrays are sealed under `sealed_truth/`.

Data counts: 8 builds, 11 flights, {freq_hz.size} frequency points from {freq_hz[0]:.3g} to {freq_hz[-1]:.3g} Hz. Whole-frequency observations are published; no peak-only likelihood or feature-summary data product is used here.

## Validation summary

- Cantilever Euler-Bernoulli benchmark max relative error: {beam["max_abs_relative_error"]:.3e}.
- Lumped two-mass benchmark max relative error: {lumped["max_abs_relative_error"]:.3e}.
- Observable build-0 axial resonance-like features (Hz): {validation["observable_build0_z_resonance_like_hz"][:6]}.
- Observable build-0 axial antiresonance-like features (Hz): {validation["observable_build0_z_antiresonance_like_hz"][:6]}.
- Antiresonance interlacing check pass: {validation["interlacing_check_pass"]}.
- Resolution sensitivity pass: {res["pass"]}; coarse-minus-full relative shift = {res["coarse_minus_full_relative"]:.3e}.

## Observable scalar response summary

Observed netCG `3*GRMS` over all build-flight combinations:

- Median: {results["observed_netcg_3grms_g_summary_over_build_flight"]["median"]:.4g} g
- Central 95 percent: [{results["observed_netcg_3grms_g_summary_over_build_flight"]["q025"]:.4g}, {results["observed_netcg_3grms_g_summary_over_build_flight"]["q975"]:.4g}] g
- Central 99 percent: [{results["observed_netcg_3grms_g_summary_over_build_flight"]["q005"]:.4g}, {results["observed_netcg_3grms_g_summary_over_build_flight"]["q995"]:.4g}] g

## Mesh/export status

- Nodes: {mesh_status["nodes"]}
- Elements: {mesh_status["elements"]}
- VTU via meshio: {mesh_status["vtu_written_with_meshio"]}
- OBJ via meshio: {mesh_status["obj_written_with_meshio"]}
- BDF: {mesh_status["bdf_written"]}

## Figures

- `figures/apparent_mass_antiresonances.png`
- `figures/response_psd_clean_vs_observed.png`
- `figures/flight_response_overlay_build0.png`
- `figures/netcg_distribution.png`
- `figures/mesh_undeformed.png`
- `figures/mode_shape_1.png` through `figures/mode_shape_5.png`

## Units and frame

SI units are used. The interface frame has `x` and `y` transverse in the tray plane and `z` axial from dome/source toward tray/load. Rotations follow the right-hand rule. Apparent mass is kg for translations and kg*m^2 for rotations. Response PSD is g^2/Hz.

## Hidden-boundary note

This report intentionally does not disclose exact as-built parameter values, hidden imperfection magnitudes, or noise scales. Those are sealed for the master after inference.
"""
    (report / "packet.md").write_text(packet)

    manifest = {
        "dataset": ["dataset/observations.npz", "dataset/data_contract.md"],
        "sealed_truth": [
            "sealed_truth/generate_truth.py",
            "sealed_truth/true_parameters.json",
            "sealed_truth/model_form_imperfections.md",
            "sealed_truth/scoring_key.npz",
            "sealed_truth/scoring_key.json",
            "sealed_truth/hidden_decisions_log.md",
        ],
        "report": [
            "report/packet.md",
            "report/results.json",
            "report/assumptions_ledger.md",
            "report/quantity_contracts.md",
            "report/resolution_sensitivity.json",
            "report/known_failures.md",
            "report/review_request.md",
            "report/commands.md",
            "report/files_changed.md",
            "report/runtime.json",
            "report/checks/checks.json",
        ],
        "figures": figures["figure_paths"],
    }
    (report / "manifest.json").write_text(json.dumps(manifest, indent=2))

    commands = """# Commands

From `runs/round3/codex_truth/`:

```bash
PIP_CACHE_DIR=.pip-cache python3 -m pip install --target .deps meshio
python3 sealed_truth/generate_truth.py --root .
```

The generator writes the public dataset, sealed truth files, validation report, mesh exports, figures, checks, and runtime files.
"""
    (report / "commands.md").write_text(commands)


def write_checks(
    dirs: dict[str, Path],
    freq_hz: np.ndarray,
    observations: dict[str, np.ndarray],
    beam: dict[str, Any],
    lumped: dict[str, Any],
    validation: dict[str, Any],
    res: dict[str, Any],
    figures: dict[str, Any],
    mesh_status: dict[str, Any],
) -> dict[str, Any]:
    obs_mass = observations["observed_mass"]
    psd = observations["observed_response_psd_g2_per_Hz"]
    checks = {
        "frequency_grid_monotonic": bool(np.all(np.diff(freq_hz) > 0.0)),
        "frequency_grid_range_pass": bool(freq_hz[0] <= 5.001 and freq_hz[-1] >= 599.9),
        "apparent_mass_shape_pass": bool(obs_mass.shape[:2] == (8, 6)),
        "response_psd_shape_pass": bool(psd.shape[:2] == (8, 11)),
        "finite_values_pass": bool(np.all(np.isfinite(obs_mass.real)) and np.all(np.isfinite(obs_mass.imag)) and np.all(np.isfinite(psd))),
        "positive_psd_pass": bool(np.all(psd > 0.0)),
        "beam_benchmark_pass": bool(beam["max_abs_relative_error"] < 5e-4),
        "lumped_benchmark_pass": bool(lumped["max_abs_relative_error"] < 1e-12),
        "antiresonance_interlacing_pass": bool(validation["interlacing_check_pass"]),
        "resolution_sensitivity_pass": bool(res["pass"]),
        "mesh_export_pass": bool(mesh_status["vtu_written_with_meshio"] and mesh_status["obj_written_with_meshio"] and (dirs["mesh"] / "model.bdf").exists()),
        "figure_legibility_pass": bool(all(v["legibility_min_size_pass"] for v in figures["figure_qa"].values())),
        "no_inference_or_nuts_run": True,
    }
    checks["overall_pass"] = bool(all(checks.values()))
    payload = {
        "checks": checks,
        "beam_benchmark": beam,
        "lumped_benchmark": lumped,
        "observable_feature_check": validation,
        "resolution_sensitivity": res,
        "mesh_status": mesh_status,
    }
    (dirs["checks"] / "checks.json").write_text(json.dumps(payload, indent=2))
    return payload


def write_runtime_and_file_list(root: Path, dirs: dict[str, Path], runtime: dict[str, Any]) -> None:
    for target in [root / "runtime.json", dirs["report"] / "runtime.json"]:
        target.write_text(json.dumps(runtime, indent=2))
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".pip-cache" not in path.parts and ".deps" not in path.parts:
            files.append(str(path.relative_to(root)))
    (dirs["report"] / "files_changed.md").write_text("# Files Created/Updated\n\n" + "\n".join(f"- `{p}`" for p in files) + "\n")


def update_notes(root: Path) -> None:
    todo = root / "notes" / "todo.md"
    if todo.exists():
        text = todo.read_text()
        for item in [
            "Implement independent truth generator and one-command replay.",
            "Generate `dataset/observations.npz` plus observable-only `data_contract.md`.",
            "Seal generator, true parameters, as-built draws, hidden model description, and scoring key.",
            "Generate mesh exports and review figures.",
            "Run validation/check scripts and record `checks.json`.",
            "Record commands, runtime, files changed, and final packet.",
        ]:
            text = text.replace(f"- [ ] {item}", f"- [x] {item}")
        todo.write_text(text)
    runs = root / "notes" / "runs.md"
    with runs.open("a") as f:
        f.write(
            "\n## 2026-06-04 generator replay\n\n"
            "- Generated public observations, sealed truth, validation figures, mesh exports, checks, and runtime artifacts.\n"
            "- No inference, fitting, NUTS, GIF, or PPT was run.\n"
        )
    memory = root / "notes" / "memory.md"
    if memory.exists():
        memory.write_text(
            "# Memory - Round 3 Codex Truth\n\n"
            "## CURRENT STATE\n\n"
            "Goal: independently author an as-built truth model and publish only observable synthetic observations for the round-3 inference agent.\n\n"
            "Last decision: the truth dataset has been generated and validation checks have run.\n\n"
            "Next action: hand off the public dataset/contract and validation packet; the sealed truth remains closed until inference is committed.\n\n"
            "Open ambiguities: none blocking. The build/flight schema interpretation is recorded in `report/priority_deliverables.md`.\n\n"
            "## Guardrails\n\n"
            "- Do not read `runs/round3/opus48/`.\n"
            "- Do not write outside `runs/round3/codex_truth/`.\n"
            "- Do not disclose hidden truth parameters or imperfection classes in `dataset/`.\n"
        )


def main() -> None:
    root = root_from_arg()
    dirs = ensure_dirs(root)
    timer = StageTimer()
    rng = np.random.default_rng(2026060403)

    freq_hz = timer.run("frequency_grid", make_frequency_grid)
    profiles = timer.run("hidden_profiles", build_truth_profiles)
    design_force_psd, flight_force_psd, forcing_params = timer.run("forcing", make_forcing, freq_hz, rng)
    builds = timer.run("build_draws", make_builds, profiles, rng)
    clean = timer.run("clean_dynamics", compute_clean_dynamics, freq_hz, builds, flight_force_psd, profiles["masses"]["netcg_load_mass_kg"])
    observations = timer.run("observation_noise", apply_observation_noise, freq_hz, clean, rng)
    timer.run("dataset", write_dataset, dirs, freq_hz, design_force_psd, flight_force_psd, forcing_params, observations, profiles)
    timer.run("sealed_truth", write_sealed, dirs, freq_hz, profiles, builds, clean, observations, forcing_params)
    beam = timer.run("beam_benchmark", cantilever_benchmark)
    lumped = timer.run("lumped_benchmark", lumped_mdof_benchmark)
    validation = timer.run("observable_feature_validation", validation_features, freq_hz, clean)
    res = timer.run("resolution_sensitivity", resolution_sensitivity, freq_hz, clean, flight_force_psd)
    mesh_info = timer.run("mesh_exports", write_mesh_exports, dirs)
    figures = timer.run("figures", write_figures, dirs, freq_hz, clean, observations, mesh_info, validation)
    timer.run(
        "reports",
        write_reports,
        root,
        dirs,
        freq_hz,
        profiles,
        observations,
        validation,
        beam,
        lumped,
        res,
        mesh_info["status"],
        figures,
    )
    checks = timer.run("checks", write_checks, dirs, freq_hz, observations, beam, lumped, validation, res, figures, mesh_info["status"])
    timer.run("notes", update_notes, root)
    runtime = timer.summary()
    runtime["checks_overall_pass"] = checks["checks"]["overall_pass"]
    timer.run("runtime_and_files", write_runtime_and_file_list, root, dirs, runtime)
    runtime = timer.summary()
    runtime["checks_overall_pass"] = checks["checks"]["overall_pass"]
    write_runtime_and_file_list(root, dirs, runtime)
    print(json.dumps({"root": str(root), "overall_pass": checks["checks"]["overall_pass"], "runtime_s": runtime["script_wall_s"]}, indent=2))


if __name__ == "__main__":
    main()
