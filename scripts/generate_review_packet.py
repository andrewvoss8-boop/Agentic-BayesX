#!/usr/bin/env python3
"""Generate a human-reviewable packet for the 2DOF StatFEM/FBS workflow."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.twodof.model import TwoDofParams, power_law_force_spectrum, tray_accel_from_m1_force


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "artifacts" / "reports"
FIG_DIR = REPORT_DIR / "figures"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _complex_from_json(raw: dict) -> np.ndarray:
    return np.asarray(raw["real"], dtype=float) + 1j * np.asarray(raw["imag"], dtype=float)


def _latest_canary_metadata() -> dict:
    runs = sorted((ROOT / "artifacts" / "runs").glob("canary-*/metadata.json"))
    return _load_json(runs[-1]) if runs else {}


def _format_float(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}g}"


def _plot_text_panel(title: str, rows: list[tuple[str, str]], path: Path, figsize: tuple[float, float] = (10, 6)) -> Path:
    fig, ax = plt.subplots(figsize=figsize)
    ax.axis("off")
    ax.set_title(title, loc="left", fontsize=15, fontweight="bold", pad=18)
    y = 0.92
    for label, text in rows:
        ax.text(0.02, y, label, fontsize=10, fontweight="bold", va="top")
        ax.text(0.32, y, text, fontsize=10, va="top", wrap=True)
        y -= 0.105
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_model_schematic(path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.axis("off")

    ax.plot([0.7, 0.7], [0.9, 4.1], color="black", lw=2)
    ax.text(0.45, 4.3, "fixed base", fontsize=10)

    dome = plt.Rectangle((3.0, 2.9), 1.4, 0.8, fc="#8ecae6", ec="black")
    tray = plt.Rectangle((6.6, 1.3), 1.4, 0.8, fc="#ffb703", ec="black")
    ax.add_patch(dome)
    ax.add_patch(tray)
    ax.text(3.7, 3.3, "m1\nprimary dome", ha="center", va="center", fontsize=10)
    ax.text(7.3, 1.7, "m2\ntray", ha="center", va="center", fontsize=10)

    ax.plot([0.7, 3.0], [3.3, 3.3], color="black", lw=1.8)
    ax.text(1.6, 3.55, "k1, c1", fontsize=10)
    ax.plot([4.4, 6.6], [2.9, 2.1], color="black", lw=1.8)
    ax.text(5.0, 2.75, "k12=k2,\nc12=c2", fontsize=9)
    ax.plot([0.7, 6.6], [1.7, 1.7], color="gray", lw=1.3, ls="--")
    ax.text(2.1, 1.95, "tray standalone test uses k2, c2 to fixed base", fontsize=9, color="dimgray")

    ax.annotate("Ch2: F1/a1\nprimary-side coupled apparent mass", xy=(3.7, 3.75), xytext=(5.0, 4.35),
                arrowprops={"arrowstyle": "->"}, fontsize=9)
    ax.annotate("Ch3: F2/a2\ntray impact apparent mass", xy=(7.3, 2.15), xytext=(7.8, 3.25),
                arrowprops={"arrowstyle": "->"}, fontsize=9)
    ax.annotate("flight forcing F1(?)", xy=(3.0, 3.45), xytext=(2.2, 4.5),
                arrowprops={"arrowstyle": "->"}, fontsize=9)
    ax.set_title("2DOF aerospace analog: primary dome + secondary tray", loc="left", fontsize=15, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_error_taxonomy(path: Path) -> Path:
    rows = [
        ("Parameter uncertainty", "Unknown k1, k2, c1, c2 represented by log-parameter posterior samples; k12 and c12 are tied to k2 and c2."),
        ("Observation noise", "Additive complex Gaussian noise on real and imaginary channel parts."),
        ("Model discrepancy", "Zero-mean GP over natural log frequency with squared-exponential covariance."),
        ("Forcing uncertainty", "Unknown flight forcing compressed to force_amp and force_fc in the current toy model."),
        ("QOI uncertainty", "Peak tray acceleration during flight computed from posterior samples."),
        ("Human judgment", "Question framing, objective choice, and whether the test menu is the right test class."),
    ]
    return _plot_text_panel("STATFEM error and uncertainty taxonomy", rows, path, figsize=(11, 6.3))


def plot_error_hyperparameters(dataset: dict, post: dict, path: Path) -> Path:
    noise = dataset["truth"]["noise"]
    rows = [
        ("Synthetic iid real sigma", _format_float(noise["sigma_re"])),
        ("Synthetic iid imag sigma", _format_float(noise["sigma_im"])),
        ("Synthetic GP discrepancy scale", _format_float(noise["discrepancy_scale"])),
        ("Synthetic GP coordinate", noise.get("discrepancy_coordinate", "natural_log_frequency")),
        ("Synthetic GP log-frequency corr length", _format_float(noise["discrepancy_corr_logfreq"])),
        ("MCMC posterior mean sigma_d", _format_float(post["posterior_mean"]["sigma_d"])),
        ("MCMC posterior mean ell_d_logfreq", _format_float(post["posterior_mean"]["ell_d_logfreq"])),
        ("MCMC posterior mean sigma_n", _format_float(post["posterior_mean"]["sigma_n"])),
        ("Coupling parameterization", "k12 = k2 and c12 = c2"),
    ]
    return _plot_text_panel("Actual error and discrepancy hyperparameters", rows, path, figsize=(11, 6.2))


def plot_channel_error_vs_truth(dataset: dict, path: Path) -> Path:
    freqs = np.asarray(dataset["freqs_hz"], dtype=float)
    clean = {name: _complex_from_json(raw) for name, raw in dataset["channels_clean"].items()}
    components = dataset.get("error_components", {})
    channels = list(clean)

    fig, axes = plt.subplots(3, 2, figsize=(11, 10), sharex=True)
    axes_flat = axes.ravel()
    for ax, name in zip(axes_flat, channels):
        gp = _complex_from_json(components[name]["gp_discrepancy"])
        iid = _complex_from_json(components[name]["iid_sensor_noise"])
        total = _complex_from_json(components[name]["total_error"])
        denom = np.maximum(np.abs(clean[name]), 1e-12)
        ax.plot(freqs, np.abs(total) / denom, label="total |error|/|truth|", lw=1.3)
        ax.plot(freqs, np.abs(gp) / denom, label="GP", lw=1.0, alpha=0.8)
        ax.plot(freqs, np.abs(iid) / denom, label="iid", lw=1.0, alpha=0.8)
        ax.set_title(name.replace("_", " "), fontsize=8)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=6)
    axes_flat[-1].axis("off")
    for ax in axes_flat[3:5]:
        ax.set_xlabel("Frequency (Hz)")
    fig.suptitle("Realized synthetic error vs clean truth by channel", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_channel_truth_vs_observed(dataset: dict, path: Path) -> Path:
    freqs = np.asarray(dataset["freqs_hz"], dtype=float)
    clean = {name: _complex_from_json(raw) for name, raw in dataset["channels_clean"].items()}
    observed = {name: _complex_from_json(raw) for name, raw in dataset["channels_obs"].items()}
    channels = list(clean)

    fig, axes = plt.subplots(3, 2, figsize=(11, 10), sharex=True)
    axes_flat = axes.ravel()
    for ax, name in zip(axes_flat, channels):
        ax.plot(freqs, np.abs(clean[name]), label="clean truth", lw=1.4, color="black")
        ax.plot(freqs, np.abs(observed[name]), label="truth + GP + iid", lw=1.1, alpha=0.85, color="#2563eb")
        ax.set_title(name.replace("_", " "), fontsize=8)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=6)
    axes_flat[-1].axis("off")
    for ax in axes_flat[3:5]:
        ax.set_xlabel("Frequency (Hz)")
    fig.suptitle("Synthetic measurements: clean truth vs observed data", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_channel_absolute_error(dataset: dict, path: Path) -> Path:
    freqs = np.asarray(dataset["freqs_hz"], dtype=float)
    components = dataset.get("error_components", {})
    channels = list(dataset["channels_clean"])

    fig, axes = plt.subplots(3, 2, figsize=(11, 10), sharex=True)
    axes_flat = axes.ravel()
    for ax, name in zip(axes_flat, channels):
        gp = _complex_from_json(components[name]["gp_discrepancy"])
        iid = _complex_from_json(components[name]["iid_sensor_noise"])
        total = _complex_from_json(components[name]["total_error"])
        ax.plot(freqs, np.abs(total), label="|total error|", lw=1.3)
        ax.plot(freqs, np.abs(gp), label="|GP discrepancy|", lw=1.0, alpha=0.85)
        ax.plot(freqs, np.abs(iid), label="|iid sensor noise|", lw=1.0, alpha=0.85)
        ax.set_title(name.replace("_", " "), fontsize=8)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=6)
    axes_flat[-1].axis("off")
    for ax in axes_flat[3:5]:
        ax.set_xlabel("Frequency (Hz)")
    fig.suptitle("Absolute injected synthetic error by channel", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _log_frequency_coordinate(freqs_hz: np.ndarray) -> np.ndarray:
    if np.any(freqs_hz <= 0.0):
        raise ValueError("log-frequency GP requires positive frequencies")
    return np.log(freqs_hz)


def _sqexp_cov(freqs_hz: np.ndarray, scale: float, corr_logfreq: float) -> np.ndarray:
    eta = _log_frequency_coordinate(freqs_hz)
    d = np.subtract.outer(eta, eta)
    return scale**2 * np.exp(-0.5 * (d / corr_logfreq) ** 2) + 1e-10 * np.eye(len(freqs_hz))


def plot_gp_sample_paths(dataset: dict, path: Path) -> Path:
    freqs = np.asarray(dataset["freqs_hz"], dtype=float)
    noise = dataset["truth"]["noise"]
    scale = float(noise["discrepancy_scale"])
    corr_logfreq = float(noise["discrepancy_corr_logfreq"])
    cov = _sqexp_cov(freqs, scale, corr_logfreq)
    rng = np.random.default_rng(20260601)
    samples = rng.multivariate_normal(np.zeros(len(freqs)), cov, size=6)

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6), gridspec_kw={"width_ratios": [1.4, 1.0]})
    for i, sample in enumerate(samples):
        axes[0].plot(freqs, sample, lw=1.2, label=f"draw {i + 1}")
    axes[0].axhline(0.0, color="black", lw=0.8)
    axes[0].set_xscale("log")
    axes[0].set_xlabel("Frequency (Hz)")
    axes[0].set_ylabel("additive discrepancy, real part")
    axes[0].set_title("Example GP discrepancy sample paths", loc="left", fontweight="bold")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=7, ncol=2)

    ref_freq = freqs[len(freqs) // 2]
    corr = np.exp(-0.5 * ((np.log(freqs) - np.log(ref_freq)) / corr_logfreq) ** 2)
    axes[1].plot(freqs, corr, color="#7c3aed", lw=1.8)
    axes[1].axvline(ref_freq, color="black", ls="--", lw=1)
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Frequency (Hz)")
    axes[1].set_ylabel("correlation to center frequency")
    axes[1].set_title("Squared-exponential correlation", loc="left", fontweight="bold")
    axes[1].grid(True, alpha=0.3)

    fig.suptitle(
        f"Zero-mean squared-exponential GP on eta=ln(f): k = sigma_d^2 exp(-0.5((eta-eta')/ell_d)^2), "
        f"sigma_d={scale:g}, ell_d={corr_logfreq:g}",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_parameter_error_summary(post: dict, path: Path) -> Path:
    truth = post["truth"]
    mean = post["posterior_mean"]
    labels = ["k1", "k2/k12", "c1", "c2/c12", "force_amp", "force_fc", "QOI"]
    truth_vals = [
        truth["params"]["k1"],
        truth["params"]["k2"],
        truth["params"]["c1"],
        truth["params"]["c2"],
        truth["force_amp"],
        truth["force_fc"],
        truth["qoi_peak_tray_accel"],
    ]
    mean_vals = [
        mean["k1"],
        mean["k2"],
        mean["c1"],
        mean["c2"],
        mean["force_amp"],
        mean["force_fc"],
        mean["qoi_peak_tray_accel"],
    ]
    rel_err = [abs(a - b) / max(abs(b), 1e-12) for a, b in zip(mean_vals, truth_vals)]

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.bar(np.arange(len(labels)), rel_err, color="#2563eb", alpha=0.85)
    ax.set_xticks(np.arange(len(labels)), labels, rotation=30, ha="right")
    ax.set_ylabel("relative error vs synthetic truth")
    ax.set_title("Posterior mean error by estimated variable", loc="left", fontweight="bold")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_question_framing(path: Path) -> Path:
    rows = [
        ("Engineering decision", "Which tests and data channels best reduce uncertainty in tray flight response?"),
        ("Objective", "Recover stiffness/damping parameters and estimate peak tray acceleration under unknown primary forcing."),
        ("BOED can optimize", "A fixed menu of candidate tests once objective, simulator, prior, and noise/discrepancy model are stated."),
        ("BOED cannot reframe", "Whether peak tray acceleration is the right QOI, whether the toy model is adequate, or whether a different experiment class is needed."),
        ("Near-term stance", "Question-first synthetic STATFEM packet now; BOED-lite experiment comparison deferred to Milestone 3."),
    ]
    return _plot_text_panel("Question framing before optimization", rows, path, figsize=(11, 5.7))


def plot_experimental_workflow(path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.axis("off")
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)

    boxes = [
        (0.4, 3.1, "1. Declare\nquestion +\nassumptions"),
        (2.5, 3.1, "2. Generate\nclean 2DOF\nFRFs"),
        (4.6, 3.1, "3. Add GP\nmodel error +\nsensor noise"),
        (6.7, 3.1, "4. Infer k, c,\nforcing, QOI\nwith MCMC"),
        (8.8, 3.1, "5. Run checks\nand make\nfigures"),
        (10.1, 1.0, "6. Human\nreviews and\nreframes"),
    ]
    for x, y, text in boxes:
        rect = plt.Rectangle((x, y), 1.65, 1.05, fc="#f1f5f9", ec="#334155", lw=1.2)
        ax.add_patch(rect)
        ax.text(x + 0.825, y + 0.525, text, ha="center", va="center", fontsize=9)

    arrow_pairs = [
        ((2.05, 3.62), (2.48, 3.62)),
        ((4.15, 3.62), (4.58, 3.62)),
        ((6.25, 3.62), (6.68, 3.62)),
        ((8.35, 3.62), (8.78, 3.62)),
        ((9.9, 3.1), (10.55, 2.1)),
    ]
    for start, end in arrow_pairs:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.3})

    ax.text(
        0.45,
        1.1,
        "Current scope: one synthetic 2DOF dome/tray model. Future scope: two MDOF/FEM structures coupled through FBS.",
        fontsize=10,
        color="#334155",
    )
    ax.set_title("Virtual experiment and agent workflow", loc="left", fontsize=15, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_qoi_uncertainty(post: dict, path: Path) -> Path:
    mean = post["posterior_mean"]["qoi_peak_tray_accel"]
    ci_low, ci_high = post["posterior_ci_95"]["qoi_peak_tray_accel"]
    truth = post["truth"]["qoi_peak_tray_accel"]

    fig, ax = plt.subplots(figsize=(8, 3.8))
    ax.errorbar([0], [mean], yerr=[[mean - ci_low], [ci_high - mean]], fmt="o", capsize=8, label="posterior QOI")
    ax.axhline(truth, color="black", lw=1.2, ls="--", label="synthetic truth")
    ax.set_xticks([0], ["peak tray accel"])
    ax.set_ylabel("synthetic acceleration units")
    ax.set_title("Flight QOI uncertainty", loc="left", fontsize=14, fontweight="bold")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _qoi_sample_spectra(post: dict, freqs: np.ndarray, max_samples: int = 8) -> tuple[np.ndarray, np.ndarray]:
    samples = np.asarray(post.get("samples_physical", []), dtype=float)
    if samples.size == 0:
        return np.empty((0, len(freqs))), np.empty(0)
    idx = np.linspace(0, len(samples) - 1, min(max_samples, len(samples)), dtype=int)
    spectra = []
    peaks = []
    truth = post["truth"]
    for vals in samples[idx]:
        p = TwoDofParams(
            m1=truth["params"]["m1"],
            m2=truth["params"]["m2"],
            k1=vals[0],
            k2=vals[1],
            k12=vals[1],
            c1=vals[2],
            c2=vals[3],
            c12=vals[3],
        )
        force = power_law_force_spectrum(freqs, amp=vals[4], fc=vals[5])
        tray = np.abs(tray_accel_from_m1_force(p, freqs, force))
        spectra.append(tray)
        peaks.append(float(np.max(tray)))
    return np.asarray(spectra, dtype=float), np.asarray(peaks, dtype=float)


def plot_qoi_samples(dataset: dict, post: dict, path: Path) -> Path:
    freqs = np.asarray(dataset["freqs_hz"], dtype=float)
    qoi_samples = np.asarray(post.get("qoi_samples", {}).get("peak_tray_accel", []), dtype=float)
    spectra, sample_peaks = _qoi_sample_spectra(post, freqs)
    truth_peak = float(post["truth"]["qoi_peak_tray_accel"])
    mean_peak = float(post["posterior_mean"]["qoi_peak_tray_accel"])

    fig = plt.figure(figsize=(12, 7.2))
    grid = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.15], height_ratios=[1.0, 0.82])
    ax_hist = fig.add_subplot(grid[:, 0])
    ax_spectra = fig.add_subplot(grid[0, 1])
    ax_residual = fig.add_subplot(grid[1, 1], sharex=ax_spectra)

    if len(qoi_samples):
        ax_hist.hist(qoi_samples, bins=24, color="#2563eb", alpha=0.75, edgecolor="white")
        ax_hist.plot(qoi_samples, np.zeros_like(qoi_samples), "|", color="#1e293b", markersize=8, alpha=0.35, label="retained samples")
    ax_hist.axvline(truth_peak, color="black", ls="--", lw=1.2, label="synthetic truth")
    ax_hist.axvline(mean_peak, color="#dc2626", lw=1.2, label="posterior mean")
    if len(qoi_samples):
        bias = mean_peak - truth_peak
        frac_above = 100.0 * float(np.mean(qoi_samples > truth_peak))
        ax_hist.text(
            0.03,
            0.97,
            f"mean bias = {bias:+.3g}\nposterior samples above truth = {frac_above:.1f}%",
            transform=ax_hist.transAxes,
            va="top",
            fontsize=8,
            bbox={"boxstyle": "round,pad=0.25", "facecolor": "white", "edgecolor": "#cbd5e1", "alpha": 0.9},
        )
    ax_hist.set_xlabel("Peak tray acceleration QOI")
    ax_hist.set_ylabel("retained posterior samples")
    ax_hist.set_title("Posterior QOI samples", loc="left", fontweight="bold")
    ax_hist.grid(True, axis="y", alpha=0.3)
    ax_hist.legend(fontsize=8)

    clean = np.abs(_complex_from_json(dataset["channels_clean"]["flight_tray_accel_from_unknown_m1_force"]))
    for i, spectrum in enumerate(spectra):
        ax_spectra.plot(freqs, spectrum, lw=1.1, alpha=0.70, label=f"posterior draw {i + 1}" if i < 4 else None)
        rel = (spectrum - clean) / np.maximum(clean, 1e-12)
        ax_residual.plot(freqs, 100.0 * rel, lw=1.1, alpha=0.75)
    ax_spectra.plot(freqs, clean, color="black", ls="--", lw=1.5, label="synthetic truth")
    ax_spectra.set_xscale("log")
    ax_spectra.set_ylabel("|tray acceleration spectrum|")
    ax_spectra.set_title("Example posterior tray-response spectra", loc="left", fontweight="bold")
    ax_spectra.grid(True, which="both", alpha=0.3)
    ax_spectra.legend(fontsize=8)

    ax_residual.axhline(0.0, color="black", lw=1.0, ls="--")
    ax_residual.set_xscale("log")
    ax_residual.set_xlabel("Frequency (Hz)")
    ax_residual.set_ylabel("posterior draw - truth (%)")
    ax_residual.set_title("Same samples as percent residuals", loc="left", fontweight="bold")
    ax_residual.grid(True, which="both", alpha=0.3)

    fig.suptitle("QOI is computed as max frequency-bin tray acceleration for each retained posterior parameter sample", fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_sampler_diagnostics(post: dict, path: Path) -> Path:
    history = post.get("sampler_diagnostics", {}).get("adaptation_history", [])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    if history:
        steps = [h["step"] for h in history]
        rates = [h["window_acceptance_rate"] for h in history]
        scales = [h["proposal_scale"] for h in history]
        axes[0].plot(steps, rates, marker="o", ms=3)
        axes[0].axhline(post["sampler_diagnostics"]["target_acceptance"], color="black", ls="--", lw=1)
        axes[0].set_title("burn-in acceptance windows")
        axes[0].set_xlabel("step")
        axes[0].set_ylabel("acceptance rate")
        axes[1].plot(steps, scales, marker="o", ms=3, color="#bc6c25")
        axes[1].set_title("proposal scale adaptation")
        axes[1].set_xlabel("step")
        axes[1].set_ylabel("proposal scale")
    else:
        axes[0].text(0.1, 0.5, "No adaptation history found")
        axes[1].axis("off")
    for ax in axes:
        ax.grid(True, alpha=0.3)
    fig.suptitle("Sampler diagnostics", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _markdown_table(rows: list[tuple[str, str]]) -> str:
    def escape(value: str) -> str:
        return str(value).replace("|", r"\|").replace("\n", "<br>")

    out = ["| Item | Value |", "|---|---|"]
    out.extend(f"| {escape(a)} | {escape(b)} |" for a, b in rows)
    return "\n".join(out)


def _image_markdown(alt: str, path: Path) -> str:
    return f"![{alt}](<{path.resolve()}>)"


def _file_link(label: str, path: Path) -> str:
    return f"[{label}](<{path.resolve()}>)"


def build_report() -> tuple[Path, dict]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    dataset = _load_json(ROOT / "artifacts" / "synthetic" / "twodof_dataset.json")
    post = _load_json(ROOT / "artifacts" / "inference" / "twodof_mcmc_result.json")
    posterior_test = _load_json(ROOT / "artifacts" / "tests" / "posterior_recovery_report.json")
    mdof_test = _load_json(ROOT / "artifacts" / "tests" / "mdof_transfer_report.json")
    channel_test = _load_json(ROOT / "artifacts" / "tests" / "channel_definitions_report.json")
    key_frf_test = _load_json(ROOT / "artifacts" / "tests" / "key_transfer_functions_report.json")
    tied_error_test = _load_json(ROOT / "artifacts" / "tests" / "tied_coupling_and_errors_report.json")
    sensitivity_test = _load_json(ROOT / "artifacts" / "tests" / "sensitivity_artifact_report.json")
    key_frf_summary = _load_json(ROOT / "artifacts" / "reports" / "key_frf_summary.json")
    sensitivity_summary = _load_json(ROOT / "artifacts" / "reports" / "sensitivity_assumptions" / "sensitivity_assumptions.json")
    plot_manifest = _load_json(ROOT / "artifacts" / "plots" / "manifest.json")
    canary = _latest_canary_metadata()

    figures = [
        plot_model_schematic(FIG_DIR / "model_schematic.png"),
        plot_experimental_workflow(FIG_DIR / "experimental_workflow.png"),
        plot_error_taxonomy(FIG_DIR / "error_taxonomy.png"),
        plot_error_hyperparameters(dataset, post, FIG_DIR / "error_hyperparameters.png"),
        plot_channel_truth_vs_observed(dataset, FIG_DIR / "channel_truth_vs_observed.png"),
        plot_channel_absolute_error(dataset, FIG_DIR / "channel_absolute_error.png"),
        plot_channel_error_vs_truth(dataset, FIG_DIR / "channel_error_vs_truth.png"),
        plot_gp_sample_paths(dataset, FIG_DIR / "gp_discrepancy_samples.png"),
        plot_parameter_error_summary(post, FIG_DIR / "parameter_error_summary.png"),
        plot_question_framing(FIG_DIR / "question_framing.png"),
        plot_qoi_uncertainty(post, FIG_DIR / "qoi_uncertainty.png"),
        plot_qoi_samples(dataset, post, FIG_DIR / "qoi_samples.png"),
        plot_sampler_diagnostics(post, FIG_DIR / "sampler_diagnostics.png"),
    ]

    metadata = dataset.get("channel_metadata", {})
    channel_rows = [
        (name, f"{info.get('quantity', '?')}: {info.get('definition', '')}")
        for name, info in metadata.items()
    ]
    checker_rows = [
        ("Canary harness", canary.get("status", "missing")),
        ("Checker manifest mismatches before", str(canary.get("checker_manifest_mismatch_before", "missing"))),
        ("Checker manifest mismatches after", str(canary.get("checker_manifest_mismatch_after", "missing"))),
        ("Posterior recovery", str(posterior_test.get("pass"))),
        ("Channel definitions", str(channel_test.get("pass"))),
        ("Tied coupling and saved errors", str(tied_error_test.get("pass"))),
        ("Key linear FRFs", str(key_frf_test.get("pass"))),
        ("Sensitivity artifact", str(sensitivity_test.get("pass"))),
        ("MDOF transfer", str(mdof_test.get("pass"))),
    ]
    diagnostic_rows = [
        ("MCMC acceptance rate", _format_float(post["acceptance_rate"])),
        ("Post-burn acceptance rate", _format_float(post["post_burn_acceptance_rate"])),
        ("Ch2 vs Ch3 clean relative L2", _format_float(channel_test["channel_2_3_relative_l2"])),
        ("Key FRFs reported", str(key_frf_summary.get("frf_count", "missing"))),
        ("Sensitivity scenarios", str(sensitivity_test.get("scenario_count", "missing"))),
    ]
    mdof_rows = [
        ("MDOF transfer prototype", "Separate check, not the system updated in this packet."),
        ("MDOF relative L2 error", _format_float(mdof_test["relative_l2_error"])),
        ("Future role", "Supports later two-MDOF/FEM transfer-function workflow."),
    ]

    qoi_ci = post["posterior_ci_95"]["qoi_peak_tray_accel"]
    qoi_samples = np.asarray(post.get("qoi_samples", {}).get("peak_tray_accel", []), dtype=float)
    qoi_truth = float(post["truth"]["qoi_peak_tray_accel"])
    qoi_mean = float(post["posterior_mean"]["qoi_peak_tray_accel"])
    qoi_bias = qoi_mean - qoi_truth
    qoi_frac_above = float(np.mean(qoi_samples > qoi_truth)) if len(qoi_samples) else float("nan")
    qoi_rows = [
        ("Synthetic truth", _format_float(qoi_truth)),
        ("Posterior mean", _format_float(qoi_mean)),
        ("Posterior mean bias", f"{_format_float(qoi_bias)} ({_format_float(100.0 * qoi_bias / max(abs(qoi_truth), 1e-12))}%)"),
        ("95% interval", f"[{_format_float(qoi_ci[0])}, {_format_float(qoi_ci[1])}]"),
        ("Retained QOI samples", str(len(qoi_samples))),
        ("Fraction of retained samples above truth", f"{_format_float(100.0 * qoi_frac_above)}%"),
    ]
    reference_lines = key_frf_summary.get("reference_lines", {})
    mass_refs = reference_lines.get("mass_units", {})
    freq_refs = reference_lines.get("uncoupled_natural_frequencies_hz", {})
    reference_rows = [
        ("m1 primary/dome mass", _format_float(mass_refs.get("m1_primary_dome", float("nan")))),
        ("m2 secondary/tray mass", _format_float(mass_refs.get("m2_secondary_tray", float("nan")))),
        ("m1 + m2 total mass", _format_float(mass_refs.get("m1_plus_m2_total", float("nan")))),
        ("tray uncoupled fn", f"{_format_float(freq_refs.get('tray_uncoupled_fn_hz', float('nan')))} Hz"),
        ("dome uncoupled fn", f"{_format_float(freq_refs.get('dome_uncoupled_fn_hz', float('nan')))} Hz"),
    ]
    noise = dataset["truth"]["noise"]
    error_value_rows = [
        ("GP type", "zero-mean squared-exponential/RBF GP over natural log frequency"),
        ("GP covariance", "eta = ln(f); k(eta, eta') = sigma_d^2 exp(-0.5 ((eta - eta') / ell_d)^2)"),
        ("GP draw structure", "independent real and imaginary GP draws per channel with shared hyperparameters"),
        ("iid real sigma", _format_float(noise["sigma_re"])),
        ("iid imaginary sigma", _format_float(noise["sigma_im"])),
        ("GP discrepancy scale", _format_float(noise["discrepancy_scale"])),
        ("GP discrepancy coordinate", noise.get("discrepancy_coordinate", "natural_log_frequency")),
        ("GP discrepancy log-frequency corr length", _format_float(noise["discrepancy_corr_logfreq"])),
        ("posterior mean sigma_d", _format_float(post["posterior_mean"]["sigma_d"])),
        ("posterior mean ell_d_logfreq", _format_float(post["posterior_mean"]["ell_d_logfreq"])),
        ("posterior mean sigma_n", _format_float(post["posterior_mean"]["sigma_n"])),
    ]
    sensitivity_rows = [
        (
            scenario["name"],
            (
                f"median rel error = {_format_float(scenario['median_channel_relative_error'])}; "
                f"max p95 rel error = {_format_float(scenario['max_channel_p95_relative_error'])}"
            ),
        )
        for scenario in sensitivity_summary.get("scenarios", [])
    ]
    key_frf_rows = [
        (
            frf["name"],
            (
                f"{frf['quantity']}; units = {frf['units']}; "
                f"max magnitude = {_format_float(frf['max_magnitude'])} at "
                f"{_format_float(frf['max_frequency_hz'])} Hz; "
                f"min magnitude = {_format_float(frf['min_magnitude'])} at "
                f"{_format_float(frf['min_frequency_hz'])} Hz"
            ),
        )
        for frf in key_frf_summary.get("frfs", [])
        if frf.get("quantity") != "drivepoint_reciprocal_inertance"
    ]
    reciprocal_inertance_rows = [
        (
            frf["name"],
            (
                f"reciprocal inertance; units = {frf['units']}; "
                f"minimum magnitude = {_format_float(frf['min_magnitude'])} at "
                f"{_format_float(frf['min_frequency_hz'])} Hz"
            ),
        )
        for frf in key_frf_summary.get("frfs", [])
        if frf.get("quantity") == "drivepoint_reciprocal_inertance"
    ]

    rel_figures = [str(p.relative_to(ROOT)) for p in figures]
    rel_plots = plot_manifest["plots"]
    frequency_axis_metadata = {
        "artifacts/reports/figures/channel_truth_vs_observed.png": "log",
        "artifacts/reports/figures/channel_absolute_error.png": "log",
        "artifacts/reports/figures/channel_error_vs_truth.png": "log",
        "artifacts/reports/figures/gp_discrepancy_samples.png": "log",
        "artifacts/reports/figures/qoi_samples.png": "log",
        "artifacts/plots/key_2dof_transfer_functions_linear.png": "log",
    }
    today = dt.date.today().isoformat()
    report_text = f"""# Agentic BayesX Synthetic StatFEM Packet

Generated: {today}

## Scope: 2DOF, Not Two MDOFs

This packet is for the current synthetic **2DOF** workflow:

- `m1` is the primary dome analog.
- `m2` is the secondary tray analog.
- Coupling is tied to the tray fixed-base properties: `k12 = k2` and `c12 = c2`.

It is not yet the future workflow with **two separate MDOF/FEM structures** coupled through FBS. The repository does contain a small MDOF transfer-function prototype, but that is a separate sanity check and not the system being updated in this packet.

## Question Framing

Engineering question: which synthetic tests best inform the stiffness, damping, unknown forcing, and peak tray response of a primary dome plus secondary tray system?

Decision being supported: prepare a clear, auditable toy workflow before moving to F-16/Vibrationdata real-data pilots.

BOED stance: BOED can optimize a stated objective over a fixed menu of experiments, but it cannot decide whether the QOI, model class, or experiment family is the right one. Those remain human-in-the-loop decisions.

{_image_markdown("question framing", FIG_DIR / "question_framing.png")}

## Assumptions and Units

- Frequencies are in Hz.
- `m1 = 1.0` and `m2 = 0.6` are synthetic mass units.
- Stiffness and damping are SI-like only relative to those synthetic masses and Hz inputs.
- Coupling is not independently estimated in this version: `k12 = k2` and `c12 = c2`.
- Apparent masses use synthetic mass units.
- Tray flight QOI uses synthetic acceleration spectrum units.
- The unknown flight input is currently represented by two parameters, `force_amp` and `force_fc`.

{_image_markdown("model schematic", FIG_DIR / "model_schematic.png")}

## Experimental Setup and Workflow

The synthetic experiment is a sequence of virtual tests on the same 2DOF dome/tray system:

1. Dome-only modal test: estimate primary drive-point apparent mass before tray attachment.
2. Coupled primary-side apparent mass: assembled system response at the primary/interface coordinate.
3. Coupled tray impact test: assembled system response at the tray coordinate.
4. Tray standalone shaker-table test: tray base-to-tray acceleration transfer without the dome.
5. Flight-like response case: unknown primary forcing drives the coupled system, and the QOI is peak tray acceleration.

The agent workflow is: declare the question, generate clean 2DOF channels, add GP discrepancy and sensor noise, infer parameters/forcing/QOI, run checks, then package results for human review.

{_image_markdown("experimental workflow", FIG_DIR / "experimental_workflow.png")}

## Measurement Channels

{_markdown_table(channel_rows)}

The key Milestone 2 correction is that channel 2 and channel 3 now use different coordinates: channel 2 is primary-side `F1/a1`, while channel 3 is tray-side `F2/a2`.

## Key Transfer Functions (Linear Units)

The workflow now reports key 2DOF transfer functions as linear magnitudes, not dB. Acceleration/force FRFs use `a/F`. The apparent-mass panel distinguishes the NASA-HDBK-7004C source and load conventions: the source apparent mass has a resonance notch, while the load apparent mass has a fixed-base resonance peak. The plot uses a log-scaled frequency axis and mass units; the apparent-mass panel also uses a logarithmic magnitude axis to show both the source notch and load peaks.

{_image_markdown("key 2DOF transfer functions in linear units", ROOT / key_frf_summary["plot"])}

Reference lines added to the apparent-mass panel:

{_markdown_table(reference_rows)}

{_markdown_table(key_frf_rows)}

Important convention fix: earlier versions of this plot collapsed source and load apparent mass. In NASA-HDBK-7004C, source and load apparent masses are both interface quantities, but the source and load constraints are different. The drive-point `F/a` terms below are retained for traceability as reciprocal inertance.

{_markdown_table(reciprocal_inertance_rows)}

## Error and Uncertainty Taxonomy

{_image_markdown("error taxonomy", FIG_DIR / "error_taxonomy.png")}

Actual error hyperparameters used in this run:

{_markdown_table(error_value_rows)}

{_image_markdown("error hyperparameters", FIG_DIR / "error_hyperparameters.png")}

The discrepancy model is a zero-mean squared-exponential Gaussian process over natural log frequency, `eta = ln(f)`. This makes correlation depend on frequency ratio rather than an absolute Hz gap, which is a more natural first assumption for broad-band structural dynamics plots and modal features that are usually reviewed on logarithmic frequency axes. In this bootstrap, real and imaginary parts are drawn independently for each channel, all channels share the same `sigma_d` and `ell_d`, and the discrepancy is additive in raw complex channel units.

{_image_markdown("GP discrepancy sample paths", FIG_DIR / "gp_discrepancy_samples.png")}

Primary measurement view:

{_image_markdown("clean truth vs observed synthetic data", FIG_DIR / "channel_truth_vs_observed.png")}

Primary error-injection view:

{_image_markdown("absolute injected synthetic error", FIG_DIR / "channel_absolute_error.png")}

Secondary diagnostic: normalized error shows where the injected error is large relative to the clean signal. Peaks in this plot can be caused by small `|truth|` in the denominator, so it should not be read as evidence that the random error model is physically locked to resonances or antiresonances.

{_image_markdown("relative error diagnostic", FIG_DIR / "channel_error_vs_truth.png")}

Frequency-axis note: packet frequency-domain plots use log-scaled frequency axes. The prior packet revision missed this on newly-added channel/error plots; that was an agent workflow miss, not a physics choice.

Related workflow note: {_file_link("log-frequency plot and GP coordinate postmortem", ROOT / "docs" / "lab" / "log-frequency-plot-gp-postmortem.md")}.

{_image_markdown("parameter error summary", FIG_DIR / "parameter_error_summary.png")}

## Sensitivity to Assumptions

This is a first-pass sensitivity artifact over synthetic error assumptions. It is not yet full posterior sensitivity, but it documents a miss in the prior packet: uncertainty categories were named without showing how conclusions move under different assumptions.

{_image_markdown("sensitivity to error assumptions", ROOT / sensitivity_summary["plot"])}

{_markdown_table(sensitivity_rows)}

Full sensitivity note: {_file_link("sensitivity assumptions", ROOT / "artifacts" / "reports" / "sensitivity_assumptions" / "sensitivity_assumptions.md")}.

## Checker Status

{_markdown_table(checker_rows)}

## Diagnostics

These diagnostics are for the 2DOF StatFEM workflow.

{_markdown_table(diagnostic_rows)}

{_image_markdown("sampler diagnostics", FIG_DIR / "sampler_diagnostics.png")}

## QOI Summary

{_markdown_table(qoi_rows)}

Concern to carry forward: the current retained QOI samples are all above the synthetic truth in this run. The full-scale response overlays look nearly identical, so the residual panel is included to make small but QOI-relevant differences visible.

{_image_markdown("qoi uncertainty", FIG_DIR / "qoi_uncertainty.png")}

{_image_markdown("QOI posterior samples", FIG_DIR / "qoi_samples.png")}

## Existing Plot Artifacts

2DOF result plots:

- `artifacts/plots/nominal_2dof_frfs.png`
- `artifacts/plots/key_2dof_transfer_functions_linear.png`
- `artifacts/plots/synthetic_channels.png`
- `artifacts/plots/posterior_vs_truth.png`
- `artifacts/plots/posterior_channel_fit.png`
- `artifacts/plots/mcmc_traces.png`

2DOF machine-readable results:

- `artifacts/synthetic/twodof_dataset.json`
- `artifacts/inference/twodof_mcmc_result.json`
- `artifacts/reports/key_frf_summary.json`
- `artifacts/reports/sensitivity_assumptions/sensitivity_assumptions.json`
- `artifacts/tests/posterior_recovery_report.json`
- `artifacts/tests/channel_definitions_report.json`
- `artifacts/tests/tied_coupling_and_errors_report.json`
- `artifacts/tests/key_transfer_functions_report.json`
- `artifacts/tests/sensitivity_artifact_report.json`

Separate MDOF prototype result:

{_markdown_table(mdof_rows)}

- `artifacts/plots/mdof_frf_comparison.png`
- `artifacts/tests/mdof_transfer_report.json`

## What Changed in This Run

- Added a shareable Markdown + PNG review packet.
- Added explicit question framing and BOED boundary language.
- Defined STATFEM-style error and uncertainty terms in the packet.
- Added actual error hyperparameter values and plots of realized synthetic error versus clean truth.
- Added a first sensitivity-to-assumptions artifact for the synthetic error model.
- Tied coupling to tray properties with `k12 = k2` and `c12 = c2`.
- Switched the synthetic discrepancy GP and inference covariance from linear-Hz distance to natural-log-frequency distance.
- Set packet channel/error/GP frequency axes to log scale and documented the earlier miss.
- Corrected channel 2 and channel 3 so they are not duplicate clean forward models.
- Added a linear-unit key FRF artifact with acceleration/force and 7004C-style source/load apparent-mass curves.
- Added a channel-definition check and report-packet completeness check.

## Agentic Workflow Lesson

The first linear-unit FRF artifact mislabeled drive-point reciprocal inertance as apparent mass. The second version still blurred source and load apparent-mass constraints. Andrew caught the issue because the source and load curves in NASA-HDBK-7004C Figure 9 have different shapes: source apparent mass has a notch, while load apparent mass has a peak.

This has been documented as a workflow failure case for lab review: {_file_link("apparent mass convention postmortem", ROOT / "docs" / "lab" / "apparent-mass-convention-postmortem.md")}.

Guardrail added: future structural-dynamics quantities should state numerator, denominator, coordinate, excitation, boundary condition, source/load constraint, units, expected limiting behavior, expected resonance behavior, and reference before a plot is accepted.

## Limitations

- This remains a synthetic toy model, not a validated aerospace structural dynamics model.
- Channel 2 uses the primary-side coordinate as a proxy for an interface apparent mass because the toy model has no explicit boundary/interface DOF.
- Measurement channels 1-3 still use drive-point `F/a` proxies; the key-FRF review plot now separately reports 7004C-style source and load apparent masses.
- Flight forcing remains parametric, not a nonparametric force spectrum.
- Per-channel discrepancy scaling and posterior predictive checks are still future work.
- BOED-lite experiment comparison is deferred to Milestone 3.

## Human Reflection

- What result surprised me?
- Which assumption feels most fragile?
- Is peak tray acceleration still the right QOI?
- What should be reframed before adding BOED or real data?
"""

    report_path = REPORT_DIR / "synthetic_statfem_packet.md"
    report_path.write_text(report_text)
    manifest = {
        "report": str(report_path.relative_to(ROOT)),
        "figures": rel_figures,
        "source_plots": rel_plots,
        "frequency_axis_scale": frequency_axis_metadata,
    }
    (REPORT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return report_path, manifest


def main() -> int:
    report_path, manifest = build_report()
    print(json.dumps({"report": str(report_path.relative_to(ROOT)), "figures": manifest["figures"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
