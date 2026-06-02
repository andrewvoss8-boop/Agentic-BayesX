#!/usr/bin/env python3
"""Set up the sequential vibe/modal/flight research question artifacts.

This script creates data, plots, and a review packet for the next research
question. It does not run posterior inference and does not claim NUTS/HMC is
implemented.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl")

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from fresh_2dof_statfem_fbs import (
    G0_M_PER_S2,
    CHANNEL_LABELS,
    Constants,
    Params,
    accel_over_force,
    damping_values,
    dome_only_reciprocal_inertance,
    frequency_channels,
    grms_from_psd,
    prior_model_summary,
    tray_transmissibility,
    true_params,
)


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "reports" / "sequential_vibe_modal_flight_20260602"
FIG_DIR = OUT_DIR / "figures"
RUN_SEED = 260602


@dataclass(frozen=True)
class SequentialConstants:
    smoothline_freq_hz: tuple[float, ...] = (20.0, 100.0, 750.0, 2000.0)
    smoothline_psd_g2_per_hz: tuple[float, ...] = (0.01, 0.1, 0.1, 0.001)
    flight_to_flight_sigma_db_psd: float = 3.0
    build_to_build_initial_sigma_db_psd: float = 1.5
    sensor_noise_initial_sigma_db_psd: float = 0.75
    flight_mean_force_below_original_db_psd: float = -6.0
    forcing_matern_length_logfreq: float = 0.08
    forcing_matern_nu: str = "3/2"
    n_later_builds_and_flights: int = 10
    n_prior_predictive_samples: int = 500


def prepare_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for path in FIG_DIR.glob("*.png"):
        path.unlink()


def psd_db_to_factor(db: float) -> float:
    """Convert PSD-space dB to a power/PSD multiplier."""
    return float(10.0 ** (db / 10.0))


def psd_db_sigma_to_ln_sigma(db_sigma: float) -> float:
    """Convert a PSD-space dB standard deviation to natural-log PSD sigma."""
    return float(db_sigma * math.log(10.0) / 10.0)


def loglog_interp_psd(freqs_hz: np.ndarray, spec_freqs: np.ndarray, spec_psd: np.ndarray) -> np.ndarray:
    """Log-log interpolation of a positive PSD table."""
    return np.exp(np.interp(np.log(freqs_hz), np.log(spec_freqs), np.log(spec_psd)))


def matern32_corr_logfreq(freqs_hz: np.ndarray, ell: float) -> np.ndarray:
    eta = np.log(freqs_hz)
    r = np.abs(np.subtract.outer(eta, eta)) / ell
    sqrt3_r = math.sqrt(3.0) * r
    return (1.0 + sqrt3_r) * np.exp(-sqrt3_r)


def sample_matern_log_psd_at_freqs(
    rng: np.random.Generator,
    freqs_hz: np.ndarray,
    mean_psd: np.ndarray,
    sigma_db_psd: float,
    ell_logfreq: float,
) -> tuple[np.ndarray, np.ndarray]:
    sigma_ln = psd_db_sigma_to_ln_sigma(sigma_db_psd)
    corr = matern32_corr_logfreq(freqs_hz, ell_logfreq)
    cov = (sigma_ln**2) * corr + 1e-12 * np.eye(len(freqs_hz))
    log_factor = np.linalg.cholesky(cov) @ rng.normal(size=len(freqs_hz))
    return mean_psd * np.exp(log_factor), log_factor


def dome_accel_per_force_g(p: Params, c: Constants, freqs_hz: np.ndarray) -> np.ndarray:
    reciprocal = dome_only_reciprocal_inertance(p, c, freqs_hz)
    return (1.0 / reciprocal) / G0_M_PER_S2


def one_sided_grms(freqs_hz: np.ndarray, psd_g2_per_hz: np.ndarray) -> float:
    return grms_from_psd(freqs_hz, psd_g2_per_hz)


def qoi_3grms(freqs_hz: np.ndarray, psd_g2_per_hz: np.ndarray) -> float:
    return 3.0 * one_sided_grms(freqs_hz, psd_g2_per_hz)


def apply_psd_space_log_variability(psd: np.ndarray, log_psd_effect: np.ndarray | float) -> np.ndarray:
    return psd * np.exp(log_psd_effect)


def apply_psd_space_log_variability_to_complex_frf(
    frf: np.ndarray, log_psd_effect: np.ndarray | float
) -> np.ndarray:
    # PSD is proportional to |FRF|^2, so a PSD-space multiplier becomes the
    # square-root multiplier on complex FRF amplitude.
    return frf * np.exp(0.5 * log_psd_effect)


def make_build_samples(
    rng: np.random.Generator, sc: SequentialConstants, n_builds: int
) -> list[dict[str, float]]:
    sigma_ln = psd_db_sigma_to_ln_sigma(sc.build_to_build_initial_sigma_db_psd)
    builds = []
    for build_id in range(n_builds):
        dome = float(rng.normal(0.0, sigma_ln))
        tray = float(rng.normal(0.0, sigma_ln))
        builds.append(
            {
                "build_id": build_id,
                "dome_log_psd_effect": dome,
                "tray_log_psd_effect": tray,
                "dome_effect_db_psd": float(10.0 * dome / math.log(10.0)),
                "tray_effect_db_psd": float(10.0 * tray / math.log(10.0)),
            }
        )
    return builds


def lognormal_sensor_effect(
    rng: np.random.Generator, sigma_db_psd: float, n: int
) -> np.ndarray:
    return rng.normal(0.0, psd_db_sigma_to_ln_sigma(sigma_db_psd), size=n)


def plot_smoothline_and_dome_fem(
    freqs_hz: np.ndarray,
    smoothline_psd: np.ndarray,
    dome_psd: np.ndarray,
    original_force_psd: np.ndarray,
    mean_flight_force_psd: np.ndarray,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.4))
    axes[0].loglog(freqs_hz, smoothline_psd, label="smoothline spec", lw=2.4)
    axes[0].loglog(freqs_hz, dome_psd, label="dome FEM response to flat input", lw=2.0)
    axes[0].set_xlabel("frequency [Hz]")
    axes[0].set_ylabel("acceleration PSD [g^2/Hz]")
    axes[0].set_title("Spec and dome-only pre-data model")
    axes[0].grid(True, which="both", alpha=0.25)
    axes[0].legend()

    axes[1].loglog(freqs_hz, original_force_psd, label="original flat force PSD", lw=2.2)
    axes[1].loglog(freqs_hz, mean_flight_force_psd, label="flight mean, 6 dB lower in PSD", lw=2.0)
    axes[1].set_xlabel("frequency [Hz]")
    axes[1].set_ylabel("force PSD [N^2/Hz]")
    axes[1].set_title("Derived forcing convention")
    axes[1].grid(True, which="both", alpha=0.25)
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "smoothline_vs_dome_fem_psd.png", dpi=170)
    plt.close(fig)


def plot_vibe_and_modal(
    freqs_hz: np.ndarray,
    smoothline_psd: np.ndarray,
    vibe_clean: np.ndarray,
    vibe_observed: np.ndarray,
    modal_freqs_hz: np.ndarray,
    dome_modal: np.ndarray,
    coupled_interface: np.ndarray,
    coupled_tray: np.ndarray,
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.2))
    axes[0, 0].loglog(freqs_hz, smoothline_psd, label="base input spec", lw=2.2)
    axes[0, 0].loglog(freqs_hz, vibe_clean, label="tray clean response", lw=2.0)
    axes[0, 0].scatter(freqs_hz[::5], vibe_observed[::5], s=12, label="tray observed", alpha=0.75)
    axes[0, 0].set_xlabel("frequency [Hz]")
    axes[0, 0].set_ylabel("PSD [g^2/Hz]")
    axes[0, 0].set_title("Tray vibe test to smoothline")
    axes[0, 0].grid(True, which="both", alpha=0.25)
    axes[0, 0].legend()

    axes[0, 1].semilogx(modal_freqs_hz, np.abs(dome_modal), lw=2.0)
    axes[0, 1].set_xlabel("frequency [Hz]")
    axes[0, 1].set_ylabel("|F1/a1| [kg]")
    axes[0, 1].set_title("Dome-only modal observation")
    axes[0, 1].grid(True, which="both", alpha=0.25)

    axes[1, 0].semilogx(modal_freqs_hz, np.abs(coupled_interface), label="interface impact/response", lw=2.0)
    axes[1, 0].semilogx(modal_freqs_hz, np.abs(coupled_tray), label="tray impact/response", lw=2.0)
    axes[1, 0].set_xlabel("frequency [Hz]")
    axes[1, 0].set_ylabel("|reciprocal inertance| [kg]")
    axes[1, 0].set_title("Coupled modal observations")
    axes[1, 0].grid(True, which="both", alpha=0.25)
    axes[1, 0].legend()

    axes[1, 1].axis("off")
    axes[1, 1].text(
        0.02,
        0.92,
        "Planned likelihood comparison",
        fontsize=14,
        weight="bold",
        transform=axes[1, 1].transAxes,
    )
    axes[1, 1].text(
        0.02,
        0.78,
        "For tray vibe, dome modal, and coupled modal tests:\n"
        "- full FRF/PSD likelihood uses every frequency point\n"
        "- peak-feature likelihood uses only peak/notch frequency and amplitude\n"
        "- NUTS/HMC is required before posterior claims",
        fontsize=11,
        va="top",
        transform=axes[1, 1].transAxes,
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "staged_test_observations.png", dpi=170)
    plt.close(fig)


def plot_flight_forcing(
    freqs_hz: np.ndarray,
    original_force_psd: np.ndarray,
    mean_force_psd: np.ndarray,
    sampled_force_psds: list[np.ndarray],
    prior_ci: dict[str, list[float]],
) -> None:
    arr = np.asarray(sampled_force_psds)
    fig, ax = plt.subplots(figsize=(12.5, 6.2))
    ax.loglog(freqs_hz, original_force_psd, color="#444444", lw=2.0, label="original force PSD behind spec")
    ax.loglog(freqs_hz, mean_force_psd, color="#1f77b4", lw=2.4, label="flight GP mean, 6 dB lower")
    ax.fill_between(freqs_hz, prior_ci["q005"], prior_ci["q995"], color="#f1c40f", alpha=0.25, label="99% known f2f band")
    ax.fill_between(freqs_hz, prior_ci["q025"], prior_ci["q975"], color="#2ca02c", alpha=0.28, label="95% known f2f band")
    for i, force in enumerate(sampled_force_psds[:11]):
        ax.loglog(freqs_hz, force, lw=0.9, alpha=0.55, label="sampled flight force" if i == 0 else None)
    ax.set_xlabel("frequency [Hz]")
    ax.set_ylabel("force PSD [N^2/Hz]")
    ax.set_title("Matérn GP flight forcing in PSD space")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "flight_forcing_matern_gp_samples.png", dpi=170)
    plt.close(fig)


def plot_build_and_flight_sequence(
    build_samples: list[dict[str, float]],
    flight_summaries: list[dict[str, float]],
    vibe_3grms_g: float,
    smoothline_3grms_g: float,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.6))
    build_ids = [item["build_id"] for item in build_samples]
    axes[0].plot(build_ids, [item["dome_effect_db_psd"] for item in build_samples], "o-", label="dome/source")
    axes[0].plot(build_ids, [item["tray_effect_db_psd"] for item in build_samples], "s-", label="tray/load")
    axes[0].axhline(0.0, color="#444444", lw=1.0)
    axes[0].set_xlabel("build id")
    axes[0].set_ylabel("build effect [dB, PSD space]")
    axes[0].set_title("Generated build-to-build effects")
    axes[0].grid(True, alpha=0.25)
    axes[0].legend()

    flight_ids = [item["flight_id"] for item in flight_summaries]
    axes[1].plot(flight_ids, [item["tray_3grms_g_observed"] for item in flight_summaries], "o-", label="flight tray 3*GRMS")
    axes[1].plot(flight_ids, [item["interface_3grms_g_observed"] for item in flight_summaries], "s-", label="flight interface 3*GRMS")
    axes[1].axhline(vibe_3grms_g, color="#d62728", ls="--", lw=1.7, label="first-build vibe tray 3*GRMS")
    axes[1].axhline(smoothline_3grms_g, color="#444444", ls=":", lw=1.7, label="smoothline input 3*GRMS")
    axes[1].set_xlabel("flight id")
    axes[1].set_ylabel("acceleration [g]")
    axes[1].set_title("Flight-by-flight response preview")
    axes[1].grid(True, alpha=0.25)
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "flight_qoi_interface_sequence.png", dpi=170)
    plt.close(fig)


def plot_cumulative_ci_summary(
    freqs_hz: np.ndarray,
    smoothline_psd: np.ndarray,
    mean_force_psd: np.ndarray,
    prior_ci: dict[str, list[float]],
    flight_summaries: list[dict[str, float]],
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.8))
    axes[0].loglog(freqs_hz, smoothline_psd, color="#444444", lw=2.0, label="original smoothline accel PSD")
    ax2 = axes[0].twinx()
    ax2.loglog(freqs_hz, mean_force_psd, color="#1f77b4", lw=2.0, label="flight force mean")
    ax2.fill_between(freqs_hz, prior_ci["q025"], prior_ci["q975"], color="#2ca02c", alpha=0.24, label="force 95% band")
    ax2.fill_between(freqs_hz, prior_ci["q005"], prior_ci["q995"], color="#f1c40f", alpha=0.18, label="force 99% band")
    axes[0].set_xlabel("frequency [Hz]")
    axes[0].set_ylabel("smoothline accel PSD [g^2/Hz]")
    ax2.set_ylabel("force PSD [N^2/Hz]")
    axes[0].set_title("Spec and forcing bands use different units")
    axes[0].grid(True, which="both", alpha=0.25)
    lines, labels = axes[0].get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    axes[0].legend(lines + lines2, labels + labels2, loc="lower left")

    flight_ids = [item["flight_id"] for item in flight_summaries]
    cumulative_means = []
    cumulative_lows = []
    cumulative_highs = []
    qois = np.asarray([item["tray_3grms_g_observed"] for item in flight_summaries])
    for i in range(1, len(qois) + 1):
        chunk = qois[:i]
        cumulative_means.append(float(np.mean(chunk)))
        cumulative_lows.append(float(np.quantile(chunk, 0.025)))
        cumulative_highs.append(float(np.quantile(chunk, 0.975)))
    axes[1].plot(flight_ids, qois, "o-", label="flight tray 3*GRMS")
    axes[1].plot(flight_ids, cumulative_means, lw=2.0, label="cumulative mean")
    axes[1].fill_between(flight_ids, cumulative_lows, cumulative_highs, alpha=0.22, label="empirical cumulative 95% interval")
    axes[1].set_xlabel("flight id")
    axes[1].set_ylabel("tray response [g]")
    axes[1].set_title("Graph shown after every flight in data form")
    axes[1].grid(True, alpha=0.25)
    axes[1].legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "cumulative_flight_ci_preview.png", dpi=170)
    plt.close(fig)


def write_markdown_files(
    sc: SequentialConstants,
    summary: dict[str, Any],
    schema: dict[str, Any],
    qoi_prior_ci: dict[str, float],
) -> None:
    assumptions = {
        "rows": [
            {
                "assumption": "PSD-space dB convention",
                "value": "factor = 10 ** (dB / 10)",
                "units": "dimensionless PSD multiplier",
                "source": "Human clarification on 2026-06-02",
                "rationale": "The smoothline, flight-to-flight, build-to-build, and sensor-noise values are PSD/power quantities.",
                "sensitivity_priority": "High",
                "where_used": "All staged data generation",
            },
            {
                "assumption": "Smoothline PSD points",
                "value": list(zip(sc.smoothline_freq_hz, sc.smoothline_psd_g2_per_hz)),
                "units": "Hz, g^2/Hz",
                "source": "Human research plan",
                "rationale": "Defines the vibe-test input spec by log-log interpolation.",
                "sensitivity_priority": "High",
                "where_used": "Tray vibe test and reference plots",
            },
            {
                "assumption": "Flight-to-flight variability",
                "value": sc.flight_to_flight_sigma_db_psd,
                "units": "dB, PSD space",
                "source": "Human research plan",
                "rationale": "Known forcing variability; fixed rather than learned.",
                "sensitivity_priority": "High",
                "where_used": "Matérn GP forcing samples",
            },
            {
                "assumption": "Build-to-build initial variability",
                "value": sc.build_to_build_initial_sigma_db_psd,
                "units": "dB, PSD space",
                "source": "Human research plan",
                "rationale": "Initial generated scale; future NUTS/HMC model should learn this scale.",
                "sensitivity_priority": "High",
                "where_used": "Build-level dome/tray effects",
            },
            {
                "assumption": "Sensor-noise initial variability",
                "value": sc.sensor_noise_initial_sigma_db_psd,
                "units": "dB, PSD space",
                "source": "Setup assumption",
                "rationale": "A concrete starting value is needed for preview data; future NUTS/HMC model should learn it.",
                "sensitivity_priority": "High",
                "where_used": "Fresh sensor noise for each observation",
            },
            {
                "assumption": "Flight forcing mean offset",
                "value": sc.flight_mean_force_below_original_db_psd,
                "units": "dB, PSD space",
                "source": "Human research plan",
                "rationale": "Mean flight forcing PSD is lower than the pre-data dynamics engineer's original forcing function.",
                "sensitivity_priority": "High",
                "where_used": "Flight forcing GP mean",
            },
            {
                "assumption": "Flight forcing covariance",
                "value": f"Matérn-{sc.forcing_matern_nu}, ell={sc.forcing_matern_length_logfreq}",
                "units": "natural log frequency",
                "source": "Human research plan",
                "rationale": "Use Matérn, not RBF, with tight frequency correlation.",
                "sensitivity_priority": "High",
                "where_used": "Flight forcing GP samples",
            },
            {
                "assumption": "NUTS/HMC status",
                "value": "not implemented in this setup",
                "units": "categorical",
                "source": "Project sampler rule",
                "rationale": "Avoid claiming posterior updates before a checked NUTS/HMC implementation exists.",
                "sensitivity_priority": "High",
                "where_used": "Report and next task",
            },
        ]
    }
    (OUT_DIR / "assumptions_ledger.json").write_text(json.dumps(assumptions, indent=2))
    assumptions_md = "# Assumptions Ledger\n\n| Assumption | Value | Units | Source | Rationale | Sensitivity |\n|---|---|---|---|---|---|\n"
    for row in assumptions["rows"]:
        assumptions_md += (
            f"| {row['assumption']} | {row['value']} | {row['units']} | "
            f"{row['source']} | {row['rationale']} | {row['sensitivity_priority']} |\n"
        )
    (OUT_DIR / "assumptions_ledger.md").write_text(assumptions_md)

    quantity_contracts = """# Quantity Contracts

## Smoothline PSD

- Numerator: acceleration-squared spectral density.
- Denominator: frequency bandwidth.
- Coordinate: commanded/base vibe input for the tray test.
- Excitation: smoothline random vibration specification.
- Boundary condition: tray tested as standalone load article.
- Units: `g^2/Hz`.
- Expected behavior: log-log interpolation through the four specified points.
- Reference: human research plan.

## Dome FEM Response PSD

- Numerator: dome acceleration-squared spectral density.
- Denominator: frequency bandwidth.
- Coordinate: dome/source `m1`.
- Excitation: simple flat broadband force PSD.
- Boundary condition: dome-only, uncoupled from tray.
- Units: `g^2/Hz`.
- Expected behavior: peak scaled to `0.1 g^2/Hz`.
- Reference: human research plan.

## Tray Vibe Response PSD

- Numerator: tray acceleration-squared spectral density.
- Denominator: frequency bandwidth.
- Coordinate: tray/load `m2`.
- Excitation: smoothline base acceleration PSD.
- Boundary condition: standalone tray/load vibe test.
- Units: `g^2/Hz`.
- Expected behavior: smoothline shaped by tray transmissibility, plus first-build tray effect and fresh sensor noise.
- Reference: existing fresh 2DOF tray transmissibility convention.

## Dome-Only Modal FRF

- Numerator: force at dome coordinate.
- Denominator: acceleration at dome coordinate.
- Coordinate: dome/source `m1`.
- Excitation: modal impact/shaker on dome only.
- Boundary condition: dome-only, uncoupled from tray.
- Units: kg, reciprocal inertance style `F/a`.
- Expected behavior: notch near the dome mode for reciprocal inertance.
- Reference: existing fresh 2DOF quantity contracts.

## Coupled Modal FRFs

- Numerator: impact force at interface or tray coordinate.
- Denominator: acceleration at the same coordinate.
- Coordinates: interface/primary side and tray/load side.
- Excitation: modal impacts at the interface and on the tray.
- Boundary condition: dome and tray coupled.
- Units: kg, reciprocal inertance style `F/a`.
- Expected behavior: coupled features depend on both dome and tray parameters.
- Reference: existing fresh 2DOF coupled-channel convention.

## Flight Forcing PSD

- Numerator: force-squared spectral density into `m1`.
- Denominator: frequency bandwidth.
- Coordinate: source/dome input `m1`.
- Excitation: latent flight forcing process.
- Boundary condition: coupled dome/tray flight configuration.
- Units: `N^2/Hz`.
- Expected behavior: Matérn-3/2 GP in log PSD around a mean 6 dB below the original force PSD.
- Reference: human research plan.

## Interface Acceleration Spectrum

- Numerator: interface acceleration-squared spectral density.
- Denominator: frequency bandwidth.
- Coordinate: source/interface side of the coupled model.
- Excitation: flight forcing into `m1`.
- Boundary condition: coupled dome/tray flight configuration.
- Units: `g^2/Hz`.
- Expected behavior: shaped by coupled transfer from `m1` force to interface acceleration.
- Reference: current 2DOF coupled transfer convention.

## Tray `3*GRMS` QOI

- Numerator: three times root integral of tray acceleration PSD.
- Denominator: not applicable after PSD integration.
- Coordinate: tray/load `m2`.
- Excitation: vibe-test base input or flight forcing, as labeled.
- Boundary condition: stage-specific.
- Units: `g`.
- Expected behavior: increases with response PSD energy and is sensitive to damping/forcing assumptions.
- Reference: random vibration review convention used in the fresh 2DOF packet.
"""
    (OUT_DIR / "quantity_contracts.md").write_text(quantity_contracts)

    sources = """# Source Register

| Source | Path or URL | What It Supports | Limits |
|---|---|---|---|
| Human research plan | current user prompt, 2026-06-02 | PSD points, dB convention, staged test sequence, fixed 3 dB flight variability, learnable build/sensor variability, Matérn forcing request. | Not a validated hardware dataset. |
| Fresh 2DOF packet | `artifacts/reports/fresh_2dof_statfem_fbs_20260601/fresh_2dof_statfem_packet.md` | Prior parameter assumptions, existing 2DOF transfer conventions, `3*GRMS` QOI precedent. | Current inference is prototype/legacy random-walk/random-scan Metropolis, not NUTS/HMC. |
| Fresh quantity contracts | `artifacts/reports/fresh_2dof_statfem_fbs_20260601/quantity_contracts.md` | Existing reciprocal-inertance and tray transmissibility conventions. | Does not cover the new sequential build/flight hierarchy. |
| Project sampler rule | `AGENTS.md` and `CLAUDE.md` | NUTS/HMC must be the future default and cannot be claimed active without code/checks. | Does not implement the sampler. |
"""
    (OUT_DIR / "sources.md").write_text(sources)

    task = """# Sequential Vibe/Modal/Flight Task

## Task

Set up a staged synthetic research problem for a rocket company that starts with a dome/tray model, a smoothline vibe spec, no test data, and then gathers tray vibe, modal, and flight data over multiple builds.

## Scope Of This Setup

This setup generates the PSD convention ledger, staged data schema, synthetic preview data, plots, and checker-backed packet. It does not run posterior inference and does not claim NUTS/HMC is active.

## Main Future Inference Questions

- How different are posteriors from full FRF/PSD likelihoods versus peak-frequency/peak-amplitude likelihoods?
- How much do tray vibe data, dome-only modal data, coupled modal data, and flight-only updates change `fn`, damping, interface acceleration spectra, and tray `3*GRMS` QOI?
- How much do repeated builds and flights help learn build-to-build variability and sensor noise?
"""
    (OUT_DIR / "task.md").write_text(task)

    db = f"""# PSD-Space dB Conventions

All dB values in this setup are interpreted in PSD/power space:

`factor = 10 ** (dB / 10)`

| Item | Value | Meaning |
|---|---:|---|
| Flight-to-flight forcing variability | {sc.flight_to_flight_sigma_db_psd} dB | Known PSD-space GP marginal sigma; not learned. |
| Build-to-build initial variability | {sc.build_to_build_initial_sigma_db_psd} dB | Initial PSD-space scale used to generate build effects; intended to be learned later. |
| Sensor noise initial variability | {sc.sensor_noise_initial_sigma_db_psd} dB | Initial PSD-space sensor/noise scale; intended to be learned later. |
| Flight mean forcing offset | {sc.flight_mean_force_below_original_db_psd} dB | Mean flight force PSD is 6 dB below the original force PSD behind the test spec. |

For complex FRFs, PSD is proportional to `|FRF|^2`, so a PSD-space multiplier is applied as the square root multiplier on complex FRF amplitude.
"""
    (OUT_DIR / "db_conventions.md").write_text(db)

    nuts = """# NUTS/HMC Backend Choice Note

Status: NUTS/HMC is not implemented in this setup. This file chooses the likely path for the next coding milestone.

## Recommendation

Use NumPyro NUTS first.

## Why

- The future model is hierarchical: structural parameters, build-to-build variability, sensor noise, and repeated flight/vibe observations.
- NUTS needs gradients, so the current NumPy likelihood should be rewritten or wrapped in a differentiable backend.
- NumPyro gives a Python/JAX path for NUTS and posterior predictive samples while keeping command-line artifact generation possible.

## Alternatives

- PyMC: friendlier model syntax, but the current hand-written complex FRF likelihood may need more translation work.
- BlackJAX: good low-level NUTS engine, but more custom plumbing for model definition and diagnostics.
- Stan: robust HMC/NUTS, but adds a separate toolchain and more friction for local agent loops.

## Acceptance Before Claiming NUTS Is Active

- A one-command run exists.
- The run writes sampler diagnostics: divergences, step size, tree depth, ESS, R-hat where applicable.
- The checker fails if NUTS diagnostics are missing.
- The report states which variables are inferred, fixed, and not inferred.
"""
    (OUT_DIR / "nuts_backend_choice.md").write_text(nuts)

    schema_md = """# Experiment Stage Schema

The schema is machine-readable in `experiment_schema.json`.

## Stages

1. `pre_data_dome_fem`: dome-only model response to a flat force PSD; scaled so dome response peak is 0.1 g^2/Hz.
2. `tray_vibe_test`: tray/load tested to the smoothline base PSD; first-build tray build effect and fresh sensor noise are included.
3. `dome_modal_test`: dome/source-only modal observation; same first-build dome effect and fresh sensor noise.
4. `coupled_modal_test`: dome plus tray modal observation; interface and tray impacts use the same first-build dome/tray effects.
5. `first_build_flight`: first build flight with fresh Matérn GP forcing sample and fresh sensor noise.
6. `later_builds_and_flights`: ten later builds, each with a tray vibe test and flight, no more modal tests.

## Learning Plan

Future NUTS/HMC inference should learn natural frequencies, damping, build-to-build variability scale, sensor-noise scale, interface acceleration spectra, and tray `3*GRMS` QOI. Flight-to-flight forcing variability remains fixed at 3 dB in PSD space.
"""
    (OUT_DIR / "experiment_schema.md").write_text(schema_md)
    (OUT_DIR / "experiment_schema.json").write_text(json.dumps(schema, indent=2))

    packet = f"""# Sequential Vibe/Modal/Flight Setup Packet

## Status

This packet sets up the research problem and generates preview data/plots. It does not perform posterior inference.

## Key Assumptions

- dB values are PSD-space dB.
- Tank/dome/source is `m1`; tray/load/secondary structure is `m2`.
- Flight-to-flight forcing variability is fixed and known at 3 dB.
- Build-to-build variability and sensor noise are generated here and should be learned in the later NUTS/HMC model.
- Flight forcing uses a Matérn-3/2 GP in log PSD with tight log-frequency length scale `{sc.forcing_matern_length_logfreq}`.
- Mean flight forcing PSD is 6 dB below the original force PSD used by the pre-data dynamics model.

See `assumptions_ledger.md`, `quantity_contracts.md`, `db_conventions.md`, and `sources.md` before implementing inference.

## Smoothline PSD

The smoothline is log-log interpolated through:

| Frequency [Hz] | PSD [g^2/Hz] |
|---:|---:|
| 20 | 0.01 |
| 100 | 0.1 |
| 750 | 0.1 |
| 2000 | 0.001 |

## Generated Values

- Dome FEM peak response PSD: `{summary['dome_fem_peak_psd_g2_per_hz']:.5g}` g^2/Hz.
- First-build tray vibe observed `3*GRMS`: `{summary['first_build_vibe_3grms_g_observed']:.5g}` g.
- Smoothline input `3*GRMS`: `{summary['smoothline_3grms_g']:.5g}` g.
- Flight prior-predictive tray `3*GRMS` 95% interval: `[{qoi_prior_ci['q025']:.5g}, {qoi_prior_ci['q975']:.5g}]` g.
- Flight prior-predictive tray `3*GRMS` 99% interval: `[{qoi_prior_ci['q005']:.5g}, {qoi_prior_ci['q995']:.5g}]` g.

## Figures

![smoothline_vs_dome_fem_psd](figures/smoothline_vs_dome_fem_psd.png)

![staged_test_observations](figures/staged_test_observations.png)

![flight_forcing_matern_gp_samples](figures/flight_forcing_matern_gp_samples.png)

![flight_qoi_interface_sequence](figures/flight_qoi_interface_sequence.png)

![cumulative_flight_ci_preview](figures/cumulative_flight_ci_preview.png)

## Next Implementation Step

Implement the NumPyro NUTS model for the staged observations. The checker must fail if NUTS diagnostics are missing or if the report implies NUTS is active before the sampler exists.
"""
    (OUT_DIR / "sequential_research_packet.md").write_text(packet)


def main() -> int:
    prepare_dirs()
    rng = np.random.default_rng(RUN_SEED)
    sc = SequentialConstants()
    c = Constants()
    truth = true_params(c)
    spec_freqs = np.asarray(sc.smoothline_freq_hz, dtype=float)
    spec_psd = np.asarray(sc.smoothline_psd_g2_per_hz, dtype=float)
    freqs = np.geomspace(20.0, 2000.0, 260)
    modal_freqs = np.geomspace(20.0, 300.0, 180)
    smoothline_psd = loglog_interp_psd(freqs, spec_freqs, spec_psd)

    dome_h = dome_accel_per_force_g(truth, c, freqs)
    original_flat_force_psd = np.full_like(freqs, 0.1 / float(np.max(np.abs(dome_h) ** 2)))
    dome_fem_psd = np.abs(dome_h) ** 2 * original_flat_force_psd
    mean_flight_force_psd = original_flat_force_psd * psd_db_to_factor(sc.flight_mean_force_below_original_db_psd)

    build_samples = make_build_samples(rng, sc, 1 + sc.n_later_builds_and_flights)
    first_build = build_samples[0]

    tray_trans = tray_transmissibility(truth, c, freqs)
    vibe_clean = np.abs(tray_trans) ** 2 * smoothline_psd
    vibe_with_build = apply_psd_space_log_variability(vibe_clean, first_build["tray_log_psd_effect"])
    vibe_observed = apply_psd_space_log_variability(
        vibe_with_build, lognormal_sensor_effect(rng, sc.sensor_noise_initial_sigma_db_psd, len(freqs))
    )
    vibe_3grms = qoi_3grms(freqs, vibe_observed)
    smoothline_3grms = qoi_3grms(freqs, smoothline_psd)

    modal_clean = frequency_channels(truth, c, modal_freqs)
    dome_modal_observed = apply_psd_space_log_variability_to_complex_frf(
        modal_clean["ch1_dome_only_reciprocal_inertance"],
        first_build["dome_log_psd_effect"]
        + lognormal_sensor_effect(rng, sc.sensor_noise_initial_sigma_db_psd, len(modal_freqs)),
    )
    coupled_interface_observed = apply_psd_space_log_variability_to_complex_frf(
        modal_clean["ch2_coupled_primary_reciprocal_inertance"],
        first_build["dome_log_psd_effect"]
        + lognormal_sensor_effect(rng, sc.sensor_noise_initial_sigma_db_psd, len(modal_freqs)),
    )
    coupled_tray_observed = apply_psd_space_log_variability_to_complex_frf(
        modal_clean["ch3_coupled_tray_reciprocal_inertance"],
        first_build["tray_log_psd_effect"]
        + lognormal_sensor_effect(rng, sc.sensor_noise_initial_sigma_db_psd, len(modal_freqs)),
    )

    force_prior_samples = []
    qoi_prior_samples = []
    interface_prior_samples = []
    h = accel_over_force(truth, c, freqs) / G0_M_PER_S2
    for _ in range(sc.n_prior_predictive_samples):
        force_psd, _ = sample_matern_log_psd_at_freqs(
            rng,
            freqs,
            mean_flight_force_psd,
            sc.flight_to_flight_sigma_db_psd,
            sc.forcing_matern_length_logfreq,
        )
        force_prior_samples.append(force_psd)
        tray_psd = np.abs(h[:, 1, 0]) ** 2 * force_psd * math.exp(first_build["tray_log_psd_effect"])
        interface_psd = np.abs(h[:, 0, 0]) ** 2 * force_psd * math.exp(first_build["dome_log_psd_effect"])
        qoi_prior_samples.append(qoi_3grms(freqs, tray_psd))
        interface_prior_samples.append(qoi_3grms(freqs, interface_psd))
    force_prior_arr = np.asarray(force_prior_samples)
    force_prior_ci = {
        "q005": np.quantile(force_prior_arr, 0.005, axis=0).tolist(),
        "q025": np.quantile(force_prior_arr, 0.025, axis=0).tolist(),
        "q975": np.quantile(force_prior_arr, 0.975, axis=0).tolist(),
        "q995": np.quantile(force_prior_arr, 0.995, axis=0).tolist(),
    }
    qoi_prior_arr = np.asarray(qoi_prior_samples)
    qoi_prior_ci = {
        "q005": float(np.quantile(qoi_prior_arr, 0.005)),
        "q025": float(np.quantile(qoi_prior_arr, 0.025)),
        "q975": float(np.quantile(qoi_prior_arr, 0.975)),
        "q995": float(np.quantile(qoi_prior_arr, 0.995)),
    }

    flight_summaries = []
    sampled_flight_force_psds = []
    for flight_id, build in enumerate(build_samples):
        force_psd, log_force = sample_matern_log_psd_at_freqs(
            rng,
            freqs,
            mean_flight_force_psd,
            sc.flight_to_flight_sigma_db_psd,
            sc.forcing_matern_length_logfreq,
        )
        sampled_flight_force_psds.append(force_psd)
        tray_psd = np.abs(h[:, 1, 0]) ** 2 * force_psd
        interface_psd = np.abs(h[:, 0, 0]) ** 2 * force_psd
        tray_observed = apply_psd_space_log_variability(
            tray_psd * math.exp(build["tray_log_psd_effect"]),
            lognormal_sensor_effect(rng, sc.sensor_noise_initial_sigma_db_psd, len(freqs)),
        )
        interface_observed = apply_psd_space_log_variability(
            interface_psd * math.exp(build["dome_log_psd_effect"]),
            lognormal_sensor_effect(rng, sc.sensor_noise_initial_sigma_db_psd, len(freqs)),
        )
        flight_summaries.append(
            {
                "flight_id": flight_id,
                "build_id": build["build_id"],
                "tray_3grms_g_observed": qoi_3grms(freqs, tray_observed),
                "interface_3grms_g_observed": qoi_3grms(freqs, interface_observed),
                "force_log_psd_sample_mean": float(np.mean(log_force)),
                "force_log_psd_sample_sd": float(np.std(log_force)),
            }
        )

    plot_smoothline_and_dome_fem(freqs, smoothline_psd, dome_fem_psd, original_flat_force_psd, mean_flight_force_psd)
    plot_vibe_and_modal(
        freqs,
        smoothline_psd,
        vibe_clean,
        vibe_observed,
        modal_freqs,
        dome_modal_observed,
        coupled_interface_observed,
        coupled_tray_observed,
    )
    plot_flight_forcing(freqs, original_flat_force_psd, mean_flight_force_psd, sampled_flight_force_psds, force_prior_ci)
    plot_build_and_flight_sequence(build_samples, flight_summaries, vibe_3grms, smoothline_3grms)
    plot_cumulative_ci_summary(freqs, smoothline_psd, mean_flight_force_psd, force_prior_ci, flight_summaries)

    schema = {
        "dB_convention": {
            "space": "PSD/power",
            "factor_formula": "10 ** (dB / 10)",
            "complex_frf_multiplier": "sqrt(PSD factor)",
        },
        "stages": [
            "pre_data_dome_fem",
            "tray_vibe_test",
            "dome_modal_test",
            "coupled_modal_test",
            "first_build_flight",
            "later_builds_and_flights",
        ],
        "learning_targets_future_nuts": [
            "dome natural frequency",
            "dome damping",
            "tray natural frequency",
            "tray damping",
            "build-to-build variability scale",
            "sensor-noise scale",
            "interface acceleration spectrum",
            "tray 3*GRMS response QOI",
        ],
        "fixed_not_learned": {
            "flight_to_flight_variability_sigma_db_psd": sc.flight_to_flight_sigma_db_psd,
            "flight_forcing_covariance": "Matérn-3/2 in natural log frequency",
        },
        "priors_source": "artifacts/reports/fresh_2dof_statfem_fbs_20260601/fresh_2dof_statfem_packet.md and prior_model_summary from fresh setup",
        "prior_model_summary": prior_model_summary(c),
    }

    dataset = {
        "freqs_hz": freqs.tolist(),
        "modal_freqs_hz": modal_freqs.tolist(),
        "smoothline_psd_g2_per_hz": smoothline_psd.tolist(),
        "original_flat_force_psd_n2_per_hz": original_flat_force_psd.tolist(),
        "mean_flight_force_psd_n2_per_hz": mean_flight_force_psd.tolist(),
        "dome_fem_response_psd_g2_per_hz": dome_fem_psd.tolist(),
        "tray_vibe_response": {
            "clean_psd_g2_per_hz": vibe_clean.tolist(),
            "observed_psd_g2_per_hz": vibe_observed.tolist(),
            "observed_3grms_g": vibe_3grms,
        },
        "modal_observations": {
            "dome_only": {
                "label": CHANNEL_LABELS["ch1_dome_only_reciprocal_inertance"],
                "real": dome_modal_observed.real.tolist(),
                "imag": dome_modal_observed.imag.tolist(),
            },
            "coupled_interface": {
                "label": CHANNEL_LABELS["ch2_coupled_primary_reciprocal_inertance"],
                "real": coupled_interface_observed.real.tolist(),
                "imag": coupled_interface_observed.imag.tolist(),
            },
            "coupled_tray": {
                "label": CHANNEL_LABELS["ch3_coupled_tray_reciprocal_inertance"],
                "real": coupled_tray_observed.real.tolist(),
                "imag": coupled_tray_observed.imag.tolist(),
            },
        },
        "build_samples": build_samples,
        "flight_summaries": flight_summaries,
        "force_prior_ci": force_prior_ci,
        "qoi_prior_predictive_ci_3grms_g": qoi_prior_ci,
    }
    (OUT_DIR / "sequential_dataset.json").write_text(json.dumps(dataset, indent=2))

    summary = {
        "dome_fem_peak_psd_g2_per_hz": float(np.max(dome_fem_psd)),
        "smoothline_3grms_g": smoothline_3grms,
        "first_build_vibe_3grms_g_observed": vibe_3grms,
        "flight_count": len(flight_summaries),
        "later_builds": sc.n_later_builds_and_flights,
        "flight_to_flight_sigma_db_psd_known_not_learned": sc.flight_to_flight_sigma_db_psd,
        "build_to_build_sigma_db_psd_initial_to_be_learned": sc.build_to_build_initial_sigma_db_psd,
        "sensor_noise_sigma_db_psd_initial_to_be_learned": sc.sensor_noise_initial_sigma_db_psd,
        "forcing_covariance": {
            "type": "Matern",
            "nu": sc.forcing_matern_nu,
            "ell_log_frequency": sc.forcing_matern_length_logfreq,
        },
        "nuts_active": False,
        "nuts_backend_recommendation": "NumPyro NUTS",
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    write_markdown_files(sc, summary, schema, qoi_prior_ci)

    manifest = {
        "trial_id": "sequential_vibe_modal_flight_20260602",
        "date": "2026-06-02",
        "command": "python3 scripts/sequential_vibe_modal_flight_setup.py",
        "report": "artifacts/reports/sequential_vibe_modal_flight_20260602/sequential_research_packet.md",
        "dataset": "artifacts/reports/sequential_vibe_modal_flight_20260602/sequential_dataset.json",
        "schema": "artifacts/reports/sequential_vibe_modal_flight_20260602/experiment_schema.json",
        "checker": "artifacts/tests/sequential_vibe_modal_flight_setup_report.json",
        "figures": [
            "figures/smoothline_vs_dome_fem_psd.png",
            "figures/staged_test_observations.png",
            "figures/flight_forcing_matern_gp_samples.png",
            "figures/flight_qoi_interface_sequence.png",
            "figures/cumulative_flight_ci_preview.png",
        ],
        "supporting_docs": [
            "assumptions_ledger.md",
            "assumptions_ledger.json",
            "quantity_contracts.md",
            "db_conventions.md",
            "sources.md",
            "nuts_backend_choice.md",
        ],
        "status": "setup_only_no_posterior_inference",
        "nuts_active": False,
        "open_next_step": "Implement checked NumPyro NUTS inference for the staged schema.",
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({"out_dir": str(OUT_DIR), "summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
