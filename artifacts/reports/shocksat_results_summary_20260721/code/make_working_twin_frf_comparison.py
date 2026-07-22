#!/usr/bin/env python3
"""Simplified held-out FRF evidence for the advisor report.

No inference is performed here. The script reads the frozen Monte Carlo cache
from the 2026-06-17 real-data validation packet. That cache already contains,
for every held-out channel, measured and original-FEM curves, the converged
modal posterior's 5/50/95 percentiles, and the 5/95 percentiles after adding
the observed-channel-estimated marginal log-amplitude discrepancy.

Quantity contract
-----------------
|H(f)| = |a_response(f) / F_drive(f)| [g/lbf], +X impact excitation,
45--260 Hz. Frequency and magnitude axes are logarithmic. The data represent
one ShockSat article and one main impact hit; build-to-build variation is not
modeled. The outer band is a modular predictive construction, not a jointly
sampled whole-FRF StatFEM posterior.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import numpy as np


HERE = Path(__file__).resolve()
REPORT = HERE.parent.parent
REPO_REPORTS = REPORT.parent
SOURCE = REPO_REPORTS / "statfem_real_validation_20260617" / "out" / "mc_cache.npz"
FIGURE = REPORT / "figures_revised" / "fig2_working_twin_good_bad_frf.png"
METRICS = REPORT / "out" / "working_twin_frf_metrics.json"

SPLIT_SEED = 10
GOOD_DAQ = 20
BAD_DAQ = 24

INK = "#171717"
FEM = "#747474"
UPDATE = "#1769aa"
PARAM_FILL = "#8fc1e3"
TOTAL_FILL = "#efc17d"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def log_error(pred: np.ndarray, measured: np.ndarray) -> float:
    return float(np.mean(np.abs(np.log10(pred + 1e-300) - np.log10(measured + 1e-300))))


def load_case() -> tuple[np.ndarray, dict, list[tuple[str, dict]]]:
    cache = np.load(SOURCE, allow_pickle=True)
    freqs = np.asarray(cache["freqs"], float)
    split = next(s for s in cache["splits"] if int(s["seed"]) == SPLIT_SEED)
    by_daq = {int(c["daq"]): c for c in split["chans"]}
    panels = [("Improves after updating", by_daq[GOOD_DAQ]),
              ("Persistent model-to-test miss", by_daq[BAD_DAQ])]
    return freqs, split, panels


def main() -> None:
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    freqs, split, panels = load_case()

    plt.rcParams.update({
        "font.size": 9.5,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.edgecolor": "#555555",
        "axes.linewidth": 0.7,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "legend.frameon": False,
    })
    fig, axes = plt.subplots(1, 2, figsize=(10.8, 5.1), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.085, right=0.985, top=0.70, bottom=0.18, wspace=0.12)

    panel_metrics = []
    for ax, (story, channel) in zip(axes, panels):
        measured = np.asarray(channel["tru"], float)
        original = np.asarray(channel["det"], float)
        param = np.asarray(channel["param"], float)
        total = np.asarray(channel["total"], float)

        # Draw the wider band first so the nested parameter band remains visible.
        ax.fill_between(freqs, total[0], total[1], color=TOTAL_FILL, alpha=0.48, lw=0, zorder=1)
        ax.fill_between(freqs, param[0], param[2], color=PARAM_FILL, alpha=0.72, lw=0, zorder=2)
        ax.plot(freqs, original, color=FEM, lw=1.15, ls=(0, (4, 2)), zorder=3)
        ax.plot(freqs, param[1], color=UPDATE, lw=1.55, zorder=4)
        ax.plot(freqs, measured, color=INK, lw=1.20, zorder=5)

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(45.0, 260.0)
        ax.grid(True, axis="y", color="#dddddd", linewidth=0.45)
        ax.grid(False, axis="x")
        ax.tick_params(labelsize=8.5, length=3)
        ax.set_title(f"DAQ {int(channel['daq'])}: {story}", loc="left", fontsize=10.2, color=INK, pad=7)
        ax.set_xlabel("frequency [Hz, log]")

        original_error = log_error(original, measured)
        updated_error = log_error(param[1], measured)
        panel_metrics.append({
            "daq": int(channel["daq"]),
            "story": story,
            "original_mean_abs_log10_error": original_error,
            "updated_mean_abs_log10_error": updated_error,
            "change_mean_abs_log10_error": updated_error - original_error,
            "total_interval_contains_parameter_interval": bool(
                np.all(total[0] <= param[0]) and np.all(total[1] >= param[2])
            ),
            "heldout_qoi_covered": bool(channel["covered"]),
        })

    axes[0].set_ylabel("accelerance magnitude |H| [g/lbf, log]")
    fig.suptitle(
        "Modal updating moves one held-out FRF, but model-form uncertainty dominates prediction",
        x=0.085, y=0.965, ha="left", fontsize=13.0, color=INK,
    )
    handles = [
        Line2D([0], [0], color=INK, lw=1.3, label="measured data"),
        Line2D([0], [0], color=FEM, lw=1.2, ls=(0, (4, 2)), label="original FEM"),
        Line2D([0], [0], color=UPDATE, lw=1.6, label="updated posterior median"),
        Patch(facecolor=PARAM_FILL, alpha=0.72, label="parameter uncertainty (5th–95th)"),
        Patch(facecolor=TOTAL_FILL, alpha=0.48, label="parameter + model-form uncertainty (5th–95th)"),
    ]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.082, 0.895), ncol=3,
               columnspacing=1.25, handlelength=2.6, fontsize=8.4)
    fig.text(
        0.085, 0.052,
        f"Held-out sensor split seed {SPLIT_SEED}; 45–260 Hz; one ShockSat article and one main impact hit. "
        f"Modal NUTS converged (max R-hat {float(split['rhat']):.4f}). The outer band adds a marginal "
        "log-amplitude discrepancy estimated on observed channels; it was not jointly sampled with the FEM parameters.",
        ha="left", fontsize=8.1, color="#4c4c4c",
    )
    fig.savefig(FIGURE, dpi=240, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    payload = {
        "figure": str(FIGURE),
        "source": str(SOURCE),
        "source_sha256": sha256(SOURCE),
        "split_seed": SPLIT_SEED,
        "selection": {
            "good": "DAQ 20: strongest original-to-updated reduction among channels paired with DAQ 24 in one retained held-out split",
            "bad": "DAQ 24: largest remaining updated error in the same retained held-out split",
        },
        "quantity": "accelerance magnitude |a_response/F_drive| [g/lbf]",
        "frequency_hz": [float(freqs[0]), float(freqs[-1])],
        "interval_probability": 0.90,
        "parameter_interval": "5th/50th/95th percentiles from the converged modal-frequency posterior",
        "total_interval": "5th/95th percentiles after the observed-channel-estimated marginal log-amplitude discrepancy",
        "model_classification": "two-stage modular predictive construction; not a jointly sampled whole-FRF StatFEM posterior",
        "calibration": {
            "max_rhat": float(split["rhat"]),
            "sigma_log_amplitude": float(split["sig"]),
        },
        "panels": panel_metrics,
    }
    METRICS.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))
    print(f"wrote {FIGURE}")


if __name__ == "__main__":
    main()
