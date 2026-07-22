#!/usr/bin/env python3
"""Create the two advisor-summary figures from frozen ShockSat artifacts.

This script changes presentation only. It does not refit a model or change any
study verdict. The JSON manifest records the inputs and the deterministic panel
selection so the simplified figures remain traceable.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


HERE = Path(__file__).resolve()
SUMMARY = HERE.parent.parent
REPORTS = SUMMARY.parent
NETCG = REPORTS / "shocksat_netcg_method_selection_20260701"
FRF = REPORTS / "shocksat_psd_envelope_twin_20260623"
FIGDIR = SUMMARY / "figures_revised"
OUTDIR = SUMMARY / "out_revised"

BLUE = "#326891"
ORANGE = "#C06C3B"
GREEN = "#3A7D44"
INK = "#222222"
MID = "#727272"
LIGHT = "#D9E6EF"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_axis(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8, colors=INK)
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.55)
    ax.set_axisbelow(True)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def make_load_bands() -> tuple[Path, dict]:
    nq = load_module("summary_netcg_qoi", NETCG / "code" / "netcg_qoi.py")
    posterior_file = NETCG / "out" / "theta_post_L5.npz"
    theta = np.load(posterior_file)["theta_post"]
    theta_map = np.median(theta, axis=0)
    model = nq.QOIModel()

    labels = ["Shear X", "Shear Y", "Normal Z"]
    fig, axes = plt.subplots(1, 3, figsize=(9.4, 3.25), sharex=True)
    panel_metrics: list[dict] = []
    for axis, (ax, label) in enumerate(zip(axes, labels)):
        method = nq.Method(model, axis, theta, kind="statfem_fk", n_disc=40, seed=100 + axis)
        low, median, high = method.band()
        truths = nq.truth_ensemble(model, axis, theta_map, n=200, seed=7 + axis)
        truth_median = np.median(truths, axis=0)

        ax.fill_between(nq.FGRID, low, high, color=LIGHT, alpha=0.9, linewidth=0,
                        label="Delivered 95% band")
        ax.plot(nq.FGRID, median, color=BLUE, linewidth=1.35, label="Band median")
        ax.plot(nq.FGRID, truth_median, color=GREEN, linewidth=1.15,
                label="Plausible-truth median")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(45, 260)
        ax.set_title(label, fontsize=10, color=INK, pad=5)
        ax.set_xlabel("Frequency (Hz, log scale)", fontsize=8.5)
        clean_axis(ax)
        panel_metrics.append({
            "direction": label,
            "band_median_grms_proxy": float(nq.grms(median)),
            "plausible_truth_median_grms_proxy": float(nq.grms(truth_median)),
        })
    axes[0].set_ylabel("Net-CG load proxy (arbitrary scale, log)", fontsize=8.5)
    handles, legend_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 1.02),
               ncol=3, frameon=False, fontsize=8.5)
    fig.suptitle("Load uncertainty differs by direction because modal observation differs",
                 fontsize=12, x=0.06, ha="left", y=1.11, color=INK)
    fig.text(0.06, -0.025,
             "Source: net-CG method-selection run, 2026-07-01. The green curve is a modeled plausible-truth median, not a direct force measurement.",
             fontsize=7.2, color=MID, ha="left")
    fig.tight_layout(rect=[0.04, 0.05, 1, 0.94])
    output = FIGDIR / "fig1_load_bands.png"
    fig.savefig(output, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output, {"panels": panel_metrics, "selection": "all three load directions"}


def make_frf_examples() -> tuple[Path, dict]:
    code_dir = FRF / "code"
    sys.path.insert(0, str(code_dir))
    modal_multiref = load_module("summary_modal_multiref", code_dir / "modal_multiref.py")

    modes_file = FRF / "out" / "edits" / "baseline" / "modes.npz"
    measured_modes_file = FRF / "data" / "measured_modes.npz"
    measured_frf_file = modal_multiref.CACHE / "m_xpos_990x.npz"

    z = np.load(modes_file, allow_pickle=True)
    phi, drive_part = z["Phi"], z["pd"]
    fem_freq = z["freqs_fem"]
    daq = [int(v) for v in z["daq"]]
    measured = dict(np.load(measured_frf_file, allow_pickle=True))
    measured["daq"] = [int(v) for v in measured["daq"]]
    frequency = measured["freqs"]
    omega = 2 * np.pi * frequency
    channel_index = {d: measured["daq"].index(d) for d in daq}
    h_data = np.array([measured["H1"][channel_index[d]] for d in daq]).T

    measured_modes = np.load(measured_modes_file, allow_pickle=True)
    observed_freq = measured_modes["freqs"]
    observed_damping = measured_modes["damp"] / 100.0
    nearest = np.array([int(np.argmin(np.abs(observed_freq - value))) for value in fem_freq])
    decay_tau = -(122880 - 1) / (250000.0 * np.log(0.05))

    def synth(resonance_omega: np.ndarray, eta: np.ndarray) -> np.ndarray:
        denominator = ((1 + 1j * eta)[None, :] * resonance_omega[None, :] ** 2
                       - omega[:, None] ** 2)
        h = (-(omega ** 2)[:, None, None]) * (phi[None, :, :] * drive_part[None, None, :])
        h = (h / denominator[:, None, :]).sum(axis=2)
        global_gain = np.median(np.log(np.abs(h_data) + 1e-30)
                                - np.log(np.abs(h) + 1e-30))
        return h * np.exp(global_gain)

    h_original = synth(
        fem_freq * 2 * np.pi,
        2.0 * (0.01 + 1.0 / (2 * np.pi * fem_freq * decay_tau)),
    )
    h_updated = synth(
        observed_freq[nearest] * 2 * np.pi,
        2.0 * (observed_damping[nearest]
               + 1.0 / (2 * np.pi * observed_freq[nearest] * decay_tau)),
    )

    def correlations(array: np.ndarray) -> np.ndarray:
        return np.array([
            np.corrcoef(np.log(np.abs(array[:, k]) + 1e-30),
                        np.log(np.abs(h_data[:, k]) + 1e-30))[0, 1]
            for k in range(len(daq))
        ])

    original_corr = correlations(h_original)
    updated_corr = correlations(h_updated)
    order = np.argsort(updated_corr)
    quantiles = [0.10, 0.40, 0.60, 0.90]
    picked_positions = [int(round(q * (len(order) - 1))) for q in quantiles]
    picked = [int(order[position]) for position in picked_positions]

    fig, axes = plt.subplots(2, 2, figsize=(8.0, 6.0), sharex=True)
    for ax, k, q in zip(axes.ravel(), picked, quantiles):
        ax.plot(frequency, np.abs(h_data[:, k]), color=INK, linewidth=1.25, label="Measured")
        ax.plot(frequency, np.abs(h_original[:, k]), color=BLUE, linewidth=1.0,
                linestyle="--", label="Original FEM")
        ax.plot(frequency, np.abs(h_updated[:, k]), color=ORANGE, linewidth=1.05,
                label="Frequency/damping update")
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(45, 260)
        ax.set_title(f"Channel {daq[k]}", fontsize=10, color=INK, pad=4)
        clean_axis(ax)
    for ax in axes[-1, :]:
        ax.set_xlabel("Frequency (Hz, log scale)", fontsize=8.5)
    for ax in axes[:, 0]:
        ax.set_ylabel("|FRF| (g/lbf, log scale)", fontsize=8.5)
    handles, legend_labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, legend_labels, loc="upper center", bbox_to_anchor=(0.5, 1.02),
               ncol=3, frameon=False, fontsize=8.5)
    fig.suptitle("Peak alignment improves, but channel-specific FRF shape error remains",
                 fontsize=12, x=0.075, ha="left", y=1.08, color=INK)
    fig.text(0.075, 0.005,
             "Source: +X FRF comparison run, 2026-06-23. Four channels are fixed 10th, 40th, 60th, and 90th percentiles of updated agreement.",
             fontsize=7.2, color=MID, ha="left")
    fig.tight_layout(rect=[0.04, 0.045, 1, 0.94])
    output = FIGDIR / "fig2_frf_examples.png"
    fig.savefig(output, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    panel_records = []
    for k, q in zip(picked, quantiles):
        panel_records.append({
            "agreement_quantile": q,
            "daq_channel": daq[k],
            "original_log_magnitude_correlation": float(original_corr[k]),
            "updated_log_magnitude_correlation": float(updated_corr[k]),
        })
    metrics = {
        "reference_direction": "+X",
        "n_channels": len(daq),
        "median_log_magnitude_correlation_original": float(np.median(original_corr)),
        "median_log_magnitude_correlation_updated": float(np.median(updated_corr)),
        "fraction_channels_improved": float(np.mean(updated_corr > original_corr)),
        "panels": panel_records,
        "selection": "fixed quantiles of updated per-channel log-magnitude correlation",
    }
    return output, metrics


def main() -> None:
    FIGDIR.mkdir(parents=True, exist_ok=True)
    OUTDIR.mkdir(parents=True, exist_ok=True)
    figure1, load_metrics = make_load_bands()
    figure2, frf_metrics = make_frf_examples()

    source_files = [
        NETCG / "code" / "netcg_qoi.py",
        NETCG / "out" / "theta_post_L5.npz",
        NETCG / "out" / "bakeoff_scorecard.json",
        NETCG / "out" / "heldout_drive.json",
        NETCG / "out" / "stage0_trust.json",
        FRF / "code" / "fig_frf_comparison.py",
        FRF / "out" / "edits" / "baseline" / "modes.npz",
        FRF / "data" / "measured_modes.npz",
    ]
    manifest = {
        "purpose": "presentation-only simplification for the ShockSat advisor summary",
        "science_recomputed": False,
        "figures": [
            {
                "file": str(figure1.relative_to(SUMMARY)),
                "story": "Load uncertainty differs by direction because modal observation differs.",
                "status": "YELLOW: shear has held-out response checks; normal has no direct net-CG force answer key.",
                "metrics": load_metrics,
            },
            {
                "file": str(figure2.relative_to(SUMMARY)),
                "story": "Frequency and damping updates improve peak alignment but leave channel-specific FRF shape error.",
                "status": "GREEN deterministic comparison; no posterior or delivery-validation claim.",
                "metrics": frf_metrics,
            },
        ],
        "inputs": [{"path": str(path), "sha256": sha256(path)} for path in source_files],
    }
    manifest_path = OUTDIR / "figure_source_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"figures": [str(figure1), str(figure2)],
                      "manifest": str(manifest_path)}, indent=2))


if __name__ == "__main__":
    main()
