#!/usr/bin/env python3
"""Generate review plots from existing Agentic BayesX artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.inference.mcmc import load_dataset
from src.mdof.reduced_transfer import chain_system, frf_drivepoint, reduced_drivepoint_frf
from src.twodof.model import TwoDofParams, default_from_natural_frequencies
from src.twodof.model import (
    accel_over_force_matrix,
    apparent_mass_dome_uncoupled,
    apparent_mass_from_drivepoint,
    common_base_reaction_apparent_mass,
    power_law_force_spectrum,
    sdof_base_reaction_apparent_mass,
    sdof_source_apparent_mass,
    tray_accel_from_m1_force,
    tray_base_to_tray_accel_transfer,
)


def _load_complex_channel(raw: dict) -> np.ndarray:
    return np.asarray(raw["real"]) + 1j * np.asarray(raw["imag"])


def _mag_db(z: np.ndarray) -> np.ndarray:
    return 20.0 * np.log10(np.maximum(np.abs(z), 1e-12))


def _summarize_linear_frf(
    frf_id: str,
    name: str,
    units: str,
    quantity: str,
    definition: str,
    freqs_hz: np.ndarray,
    values: np.ndarray,
) -> dict:
    mag = np.abs(values)
    if not np.all(np.isfinite(mag)):
        raise ValueError(f"non-finite FRF magnitude in {frf_id}")
    max_idx = int(np.argmax(mag))
    min_idx = int(np.argmin(mag))
    return {
        "id": frf_id,
        "name": name,
        "quantity": quantity,
        "units": units,
        "definition": definition,
        "reported_scale": "linear_magnitude_not_db",
        "first_magnitude": float(mag[0]),
        "first_frequency_hz": float(freqs_hz[0]),
        "min_magnitude": float(mag[min_idx]),
        "min_frequency_hz": float(freqs_hz[min_idx]),
        "min_is_interior_frequency": bool(0 < min_idx < len(freqs_hz) - 1),
        "max_magnitude": float(mag[max_idx]),
        "max_frequency_hz": float(freqs_hz[max_idx]),
        "max_is_interior_frequency": bool(0 < max_idx < len(freqs_hz) - 1),
        "last_magnitude": float(mag[-1]),
        "last_frequency_hz": float(freqs_hz[-1]),
    }


def plot_synthetic_channels(root: Path, out_dir: Path) -> Path:
    raw = json.loads((root / "artifacts/synthetic/twodof_dataset.json").read_text())
    freqs = np.asarray(raw["freqs_hz"], dtype=float)

    channels = [
        ("dome_drive_apparent_mass_modal", "Ch1: dome drive apparent mass"),
        ("coupled_interface_apparent_mass_modal", "Ch2: primary-side coupled apparent mass"),
        ("coupled_tray_impact_apparent_mass_test", "Ch3: tray impact apparent mass"),
        ("tray_standalone_accel_over_base", "Ch4: tray accel/base (standalone)"),
        ("flight_tray_accel_from_unknown_m1_force", "Ch5: flight tray accel"),
    ]

    fig, axes = plt.subplots(3, 2, figsize=(11, 10), sharex=True)
    axes = axes.ravel()
    for ax, (key, title) in zip(axes, channels):
        clean = _load_complex_channel(raw["channels_clean"][key])
        obs = _load_complex_channel(raw["channels_obs"][key])
        ax.plot(freqs, _mag_db(clean), label="clean", lw=1.5)
        ax.plot(freqs, _mag_db(obs), label="observed", lw=1.0, alpha=0.85)
        ax.set_title(title, fontsize=9)
        ax.set_ylabel("|.| dB (arb.)")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    axes[-1].axis("off")
    for ax in axes[3:5]:
        ax.set_xlabel("Frequency (Hz)")
    fig.suptitle("Synthetic measurement channels (clean vs noisy)", fontsize=11)
    fig.tight_layout()
    path = out_dir / "synthetic_channels.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_posterior_vs_truth(root: Path, out_dir: Path) -> Path:
    post = json.loads((root / "artifacts/inference/twodof_mcmc_result.json").read_text())
    truth = post["truth"]
    mean = post["posterior_mean"]

    labels = ["k1", "k2", "k12", "c1", "c2", "c12", "force_amp", "force_fc", "qoi_peak"]
    truth_vals = [
        truth["params"]["k1"],
        truth["params"]["k2"],
        truth["params"]["k12"],
        truth["params"]["c1"],
        truth["params"]["c2"],
        truth["params"]["c12"],
        truth["force_amp"],
        truth["force_fc"],
        truth["qoi_peak_tray_accel"],
    ]
    mean_vals = [
        mean["k1"],
        mean["k2"],
        mean["k12"],
        mean["c1"],
        mean["c2"],
        mean["c12"],
        mean["force_amp"],
        mean["force_fc"],
        mean["qoi_peak_tray_accel"],
    ]

    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(x - width / 2, truth_vals, width, label="truth")
    ax.bar(x + width / 2, mean_vals, width, label="posterior mean")
    ax.set_xticks(x, labels, rotation=35, ha="right")
    ax.set_title("Posterior mean vs synthetic truth")
    ax.set_ylabel("parameter value")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    path = out_dir / "posterior_vs_truth.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_posterior_fit_channels(root: Path, out_dir: Path) -> Path:
    data = load_dataset(root / "artifacts/synthetic/twodof_dataset.json")
    post = json.loads((root / "artifacts/inference/twodof_mcmc_result.json").read_text())
    freqs = data["freqs_hz"]
    mean = post["posterior_mean"]

    p = TwoDofParams(
        m1=data["truth"]["params"]["m1"],
        m2=data["truth"]["params"]["m2"],
        k1=mean["k1"],
        k2=mean["k2"],
        k12=mean["k12"],
        c1=mean["c1"],
        c2=mean["c2"],
        c12=mean["c12"],
    )
    force = power_law_force_spectrum(freqs, amp=mean["force_amp"], fc=mean["force_fc"])
    pred = {
        "dome_drive_apparent_mass_modal": apparent_mass_dome_uncoupled(freqs, p.m1, p.k1, p.c1),
        "coupled_interface_apparent_mass_modal": apparent_mass_from_drivepoint(p, freqs, dof=0),
        "coupled_tray_impact_apparent_mass_test": apparent_mass_from_drivepoint(p, freqs, dof=1),
        "tray_standalone_accel_over_base": tray_base_to_tray_accel_transfer(freqs, p),
        "flight_tray_accel_from_unknown_m1_force": tray_accel_from_m1_force(p, freqs, force),
    }

    keys = list(pred.keys())
    fig, axes = plt.subplots(3, 2, figsize=(11, 10), sharex=True)
    for ax, key in zip(axes.ravel(), keys):
        obs = data["channels_obs"][key]
        ax.plot(freqs, _mag_db(obs), label="obs", lw=1.0, alpha=0.9)
        ax.plot(freqs, _mag_db(pred[key]), label="posterior mean pred", lw=1.5)
        ax.set_title(key.replace("_", " "), fontsize=8)
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7)
    axes.ravel()[-1].axis("off")
    for ax in axes.ravel()[3:5]:
        ax.set_xlabel("Frequency (Hz)")
    fig.suptitle("Observed vs posterior-mean prediction", fontsize=11)
    fig.tight_layout()
    path = out_dir / "posterior_channel_fit.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_mcmc_traces(root: Path, out_dir: Path, max_points: int = 400) -> Path | None:
    post = json.loads((root / "artifacts/inference/twodof_mcmc_result.json").read_text())
    samples = np.asarray(post.get("samples_physical", []), dtype=float)
    if samples.size == 0:
        return None

    if len(samples) > max_points:
        idx = np.linspace(0, len(samples) - 1, max_points, dtype=int)
        samples = samples[idx]

    names = ["k1", "k2/k12", "c1", "c2/c12", "force_amp", "sigma_d"]
    cols = [0, 1, 2, 3, 4, 6]
    fig, axes = plt.subplots(3, 2, figsize=(10, 8), sharex=True)
    for ax, name, col in zip(axes.ravel(), names, cols):
        ax.plot(samples[:, col], lw=0.8)
        ax.set_title(name)
        ax.grid(True, alpha=0.3)
    fig.suptitle("MCMC traces (thinned subsample)", fontsize=11)
    fig.tight_layout()
    path = out_dir / "mcmc_traces.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_mdof_comparison(root: Path, out_dir: Path) -> Path:
    report = json.loads((root / "artifacts/tests/mdof_transfer_report.json").read_text())
    freqs = np.linspace(5.0, 220.0, 200)
    sys = chain_system(n=7, m0=1.2, k0=7.5e5, zeta=0.01)
    h_full = frf_drivepoint(sys.m, sys.c, sys.k, freqs, dof=0)
    h_red = reduced_drivepoint_frf(sys, freqs, dof=0, n_modes=4)

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(freqs, _mag_db(h_full), label="full DOF")
    ax.plot(freqs, _mag_db(h_red), label="4-mode reduction", alpha=0.9)
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("|H| dB")
    ax.set_title(f"MDOF drive-point FRF (rel L2 err = {report['relative_l2_error']:.3f})")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = out_dir / "mdof_frf_comparison.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_nominal_modes(root: Path, out_dir: Path) -> Path:
    p = default_from_natural_frequencies(f1_hz=110.0, f2_hz=75.0)
    m, c, k = (
        np.array([[p.m1, 0], [0, p.m2]]),
        np.array([[p.c1 + p.c12, -p.c12], [-p.c12, p.c2 + p.c12]]),
        np.array([[p.k1 + p.k12, -p.k12], [-p.k12, p.k2 + p.k12]]),
    )
    w2, modes = np.linalg.eigh(np.linalg.solve(m, k))
    fn_hz = np.sqrt(np.maximum(w2, 0)) / (2 * np.pi)

    freqs = np.linspace(10, 180, 300)
    h11 = []
    h22 = []
    for f in freqs:
        w = 2 * np.pi * f
        z = k + 1j * w * c - (w**2) * m
        h = np.linalg.inv(z)
        h11.append(h[0, 0])
        h22.append(h[1, 1])

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(freqs, _mag_db(np.asarray(h11)), label="H11 (dome)")
    ax.plot(freqs, _mag_db(np.asarray(h22)), label="H22 (tray)")
    for i, fn in enumerate(fn_hz):
        ax.axvline(fn, color="gray", ls="--", lw=0.8, alpha=0.6)
        ax.text(fn, ax.get_ylim()[1] * 0.95, f"f{i+1}={fn:.0f}Hz", rotation=90, fontsize=7, va="top")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("|H| dB")
    ax.set_title("Nominal 2DOF FRFs (110 Hz dome, 75 Hz tray targets)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    path = out_dir / "nominal_2dof_frfs.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_key_linear_transfer_functions(root: Path, out_dir: Path) -> Path:
    raw = json.loads((root / "artifacts/synthetic/twodof_dataset.json").read_text())
    truth = raw["truth"]["params"]
    p = TwoDofParams(
        m1=truth["m1"],
        m2=truth["m2"],
        k1=truth["k1"],
        k2=truth["k2"],
        k12=truth["k12"],
        c1=truth["c1"],
        c2=truth["c2"],
        c12=truth["c12"],
    )
    dataset_freqs = np.asarray(raw["freqs_hz"], dtype=float)
    freqs = np.geomspace(float(np.min(dataset_freqs)), float(np.max(dataset_freqs)), 600)
    uncoupled_natural_frequencies = {
        "tray_uncoupled_fn_hz": float(np.sqrt(p.k2 / p.m2) / (2.0 * np.pi)),
        "dome_uncoupled_fn_hz": float(np.sqrt(p.k1 / p.m1) / (2.0 * np.pi)),
    }
    mass_reference_lines = {
        "m1_primary_dome": float(p.m1),
        "m2_secondary_tray": float(p.m2),
        "m1_plus_m2_total": float(p.m1 + p.m2),
    }

    coupled_accel_over_force = accel_over_force_matrix(p, freqs)
    dome_app_mass = apparent_mass_dome_uncoupled(freqs, p.m1, p.k1, p.c1)
    primary_app_mass = apparent_mass_from_drivepoint(p, freqs, dof=0)
    tray_app_mass = apparent_mass_from_drivepoint(p, freqs, dof=1)
    dome_source_app_mass = sdof_source_apparent_mass(freqs, p.m1, p.k1, p.c1)
    dome_load_app_mass = sdof_base_reaction_apparent_mass(freqs, p.m1, p.k1, p.c1)
    tray_load_app_mass = sdof_base_reaction_apparent_mass(freqs, p.m2, p.k2, p.c2)
    coupled_load_app_mass = common_base_reaction_apparent_mass(p, freqs)
    tray_base_transfer = tray_base_to_tray_accel_transfer(freqs, p)

    accel_frfs = [
        {
            "id": "dome_only_a1_over_f1",
            "name": "Dome-only a1/F1",
            "values": 1.0 / dome_app_mass,
            "definition": "Uncoupled primary acceleration per primary force before tray attachment.",
        },
        {
            "id": "coupled_a1_over_f1",
            "name": "Coupled a1/F1",
            "values": coupled_accel_over_force[:, 0, 0],
            "definition": "Assembled primary acceleration per primary-side force.",
        },
        {
            "id": "coupled_a2_over_f1",
            "name": "Coupled a2/F1",
            "values": coupled_accel_over_force[:, 1, 0],
            "definition": "Assembled tray acceleration per primary-side force.",
        },
        {
            "id": "coupled_a1_over_f2",
            "name": "Coupled a1/F2",
            "values": coupled_accel_over_force[:, 0, 1],
            "definition": "Assembled primary acceleration per tray-side force.",
        },
        {
            "id": "coupled_a2_over_f2",
            "name": "Coupled a2/F2",
            "values": coupled_accel_over_force[:, 1, 1],
            "definition": "Assembled tray acceleration per tray-side force.",
        },
    ]
    apparent_mass_frfs = [
        {
            "id": "dome_source_apparent_mass_7004c",
            "name": "Source dome apparent mass",
            "values": dome_source_app_mass,
            "quantity": "source_apparent_mass",
            "definition": "Source apparent mass looking back into the fixed-base primary/dome oscillator; this has a resonance notch.",
        },
        {
            "id": "dome_load_apparent_mass_7004c",
            "name": "Dome load apparent mass",
            "values": dome_load_app_mass,
            "quantity": "load_apparent_mass",
            "definition": "Base reaction force over base acceleration for the standalone primary/dome oscillator.",
        },
        {
            "id": "tray_load_apparent_mass_7004c",
            "name": "Tray load apparent mass",
            "values": tray_load_app_mass,
            "quantity": "load_apparent_mass",
            "definition": "Base reaction force over base acceleration for the standalone tray oscillator.",
        },
        {
            "id": "coupled_primary_support_apparent_mass",
            "name": "Coupled primary support apparent mass",
            "values": coupled_load_app_mass["primary_support"],
            "quantity": "base_reaction_apparent_mass",
            "definition": "Primary support reaction force over common base acceleration for the coupled system.",
        },
        {
            "id": "coupled_tray_support_apparent_mass",
            "name": "Coupled tray support apparent mass",
            "values": coupled_load_app_mass["tray_support"],
            "quantity": "base_reaction_apparent_mass",
            "definition": "Tray support reaction force over common base acceleration for the coupled system.",
        },
        {
            "id": "coupled_total_base_apparent_mass",
            "name": "Coupled total base apparent mass",
            "values": coupled_load_app_mass["total_base"],
            "quantity": "base_reaction_apparent_mass",
            "definition": "Total base reaction force over common base acceleration for the coupled system.",
        },
    ]
    reciprocal_inertance_frfs = [
        {
            "id": "drivepoint_dome_f1_over_a1",
            "name": "Drive-point dome F1/a1",
            "values": dome_app_mass,
            "definition": "Reciprocal inertance at the primary coordinate; this has resonance minima, not 7004C-style peaks.",
        },
        {
            "id": "drivepoint_primary_f1_over_a1",
            "name": "Drive-point primary-side F1/a1",
            "values": primary_app_mass,
            "definition": "Reciprocal inertance at the coupled primary coordinate; this has resonance minima.",
        },
        {
            "id": "drivepoint_tray_f2_over_a2",
            "name": "Drive-point tray-side F2/a2",
            "values": tray_app_mass,
            "definition": "Reciprocal inertance at the coupled tray coordinate; this has resonance minima.",
        },
    ]
    other_frfs = [
        {
            "id": "tray_standalone_a2_over_abase",
            "name": "Standalone tray a2/abase",
            "values": tray_base_transfer,
            "definition": "Standalone tray acceleration over base acceleration for shaker-table analog.",
        }
    ]

    fig, axes = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    for spec in accel_frfs:
        axes[0].plot(freqs, np.abs(spec["values"]), lw=1.4, label=spec["name"])
    for spec in apparent_mass_frfs:
        axes[1].plot(freqs, np.abs(spec["values"]), lw=1.4, label=spec["name"])
    for spec in other_frfs:
        axes[2].plot(freqs, np.abs(spec["values"]), lw=1.4, label=spec["name"])

    mass_line_specs = [
        ("m1 dome mass", mass_reference_lines["m1_primary_dome"], "#334155"),
        ("m2 tray mass", mass_reference_lines["m2_secondary_tray"], "#64748b"),
        ("m1+m2 total mass", mass_reference_lines["m1_plus_m2_total"], "#0f172a"),
    ]
    for label, value, color in mass_line_specs:
        axes[1].axhline(value, color=color, lw=1.0, ls="--", alpha=0.8, label=label)

    fn_line_specs = [
        ("tray fn=75 Hz", uncoupled_natural_frequencies["tray_uncoupled_fn_hz"], "#16a34a"),
        ("dome fn=110 Hz", uncoupled_natural_frequencies["dome_uncoupled_fn_hz"], "#2563eb"),
    ]
    for label, value, color in fn_line_specs:
        for ax in axes:
            ax.axvline(value, color=color, lw=0.9, ls=":", alpha=0.7)
        axes[1].text(
            value,
            0.98,
            label,
            transform=axes[1].get_xaxis_transform(),
            rotation=90,
            va="top",
            ha="right",
            fontsize=7,
            color=color,
        )

    axes[0].set_title("Key acceleration/force FRFs (linear magnitude)")
    axes[0].set_ylabel("magnitude, accel/force")
    axes[1].set_title("7004C-style source/load apparent masses (linear magnitude)")
    axes[1].set_ylabel("magnitude, mass units")
    axes[2].set_title("Standalone tray base transfer (linear magnitude)")
    axes[2].set_ylabel("magnitude, accel/accel")
    axes[2].set_xlabel("Frequency (Hz)")

    for ax in axes:
        ax.set_xscale("log")
        ax.grid(True, which="both", alpha=0.3)
        ax.ticklabel_format(axis="y", style="sci", scilimits=(-2, 3))
        ax.legend(fontsize=8, loc="best")
    axes[1].set_yscale("log")

    fig.suptitle("2DOF key transfer functions for review: log frequency axis, no dB scaling", fontsize=12)
    fig.tight_layout()
    path = out_dir / "key_2dof_transfer_functions_linear.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)

    frf_summaries = []
    for spec in accel_frfs:
        frf_summaries.append(
            _summarize_linear_frf(
                spec["id"],
                spec["name"],
                "accel/force",
                "acceleration_over_force",
                spec["definition"],
                freqs,
                spec["values"],
            )
        )
    for spec in apparent_mass_frfs:
        frf_summaries.append(
            _summarize_linear_frf(
                spec["id"],
                spec["name"],
                "mass",
                spec["quantity"],
                spec["definition"],
                freqs,
                spec["values"],
            )
        )
    for spec in reciprocal_inertance_frfs:
        frf_summaries.append(
            _summarize_linear_frf(
                spec["id"],
                spec["name"],
                "mass",
                "drivepoint_reciprocal_inertance",
                spec["definition"],
                freqs,
                spec["values"],
            )
        )
    for spec in other_frfs:
        frf_summaries.append(
            _summarize_linear_frf(
                spec["id"],
                spec["name"],
                "accel/accel",
                "transmissibility",
                spec["definition"],
                freqs,
                spec["values"],
            )
        )

    summary = {
        "model_scope": "synthetic_truth_2dof",
        "plot": str(path.relative_to(root)),
        "frf_count": len(frf_summaries),
        "frequency_grid": {
            "min_hz": float(freqs[0]),
            "max_hz": float(freqs[-1]),
            "count": int(len(freqs)),
            "x_axis_scale": "log",
            "plot_grid_spacing": "geometric",
        },
        "reference_lines": {
            "mass_units": mass_reference_lines,
            "uncoupled_natural_frequencies_hz": uncoupled_natural_frequencies,
        },
        "conventions": [
            "Acceleration/force FRFs are computed as a/F = -omega^2 x/F.",
            "7004C-style source and load apparent masses are both interface quantities but have different source/load constraints.",
            "The source apparent mass has a resonance notch; the load apparent mass has a fixed-base resonance peak.",
            "Drive-point reciprocal inertance F/a terms are included in the JSON summary but are not the plotted apparent-mass convention.",
            "Reported magnitudes are absolute values in linear units, not dB.",
        ],
        "frfs": frf_summaries,
    }
    summary_path = root / "artifacts" / "reports" / "key_frf_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2))
    return path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "artifacts" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)

    paths = [
        plot_nominal_modes(root, out_dir),
        plot_key_linear_transfer_functions(root, out_dir),
        plot_synthetic_channels(root, out_dir),
        plot_posterior_vs_truth(root, out_dir),
        plot_posterior_fit_channels(root, out_dir),
        plot_mdof_comparison(root, out_dir),
    ]
    trace_path = plot_mcmc_traces(root, out_dir)
    if trace_path:
        paths.append(trace_path)

    manifest = {"plots": [str(p.relative_to(root)) for p in paths if p]}
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
