#!/usr/bin/env python3
"""Explore the current GP-over-log-frequency discrepancy model."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.twodof.synthetic_data import NoiseConfig, generate_dataset


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "reports" / "gp_error_exploration"


def _sqexp_cov(freqs_hz: np.ndarray, scale: float, corr_logfreq: float, jitter: float = 1e-10) -> np.ndarray:
    eta = np.log(freqs_hz)
    d = np.subtract.outer(eta, eta)
    return scale**2 * np.exp(-0.5 * (d / corr_logfreq) ** 2) + jitter * np.eye(len(freqs_hz))


def _component_noise(
    freqs_hz: np.ndarray,
    noise: NoiseConfig,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    n = len(freqs_hz)
    cov = _sqexp_cov(freqs_hz, noise.discrepancy_scale, noise.discrepancy_corr_logfreq)
    gp_re = rng.multivariate_normal(np.zeros(n), cov)
    gp_im = rng.multivariate_normal(np.zeros(n), cov)
    iid_re = rng.normal(0.0, noise.sigma_re, size=n)
    iid_im = rng.normal(0.0, noise.sigma_im, size=n)
    return {
        "gp": gp_re + 1j * gp_im,
        "iid": iid_re + 1j * iid_im,
        "total": gp_re + iid_re + 1j * (gp_im + iid_im),
    }


def _mag_db(z: np.ndarray) -> np.ndarray:
    return 20.0 * np.log10(np.maximum(np.abs(z), 1e-12))


def plot_covariance(freqs: np.ndarray, cov: np.ndarray, path: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6.6, 5.4))
    im = ax.imshow(
        cov,
        origin="lower",
        extent=[freqs[0], freqs[-1], freqs[0], freqs[-1]],
        aspect="auto",
        cmap="viridis",
    )
    fig.colorbar(im, ax=ax, label="covariance")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title("Squared-exponential GP covariance over ln(frequency)", loc="left", fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_gp_samples(freqs: np.ndarray, cov: np.ndarray, path: Path) -> Path:
    rng = np.random.default_rng(123)
    samples = rng.multivariate_normal(np.zeros(len(freqs)), cov, size=5)
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for i, sample in enumerate(samples, start=1):
        ax.plot(freqs, sample, lw=1.3, label=f"draw {i}")
    ax.axhline(0.0, color="black", lw=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("discrepancy amplitude")
    ax.set_title("Example zero-mean GP discrepancy draws", loc="left", fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend(ncol=5, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_channel_components(
    freqs: np.ndarray,
    clean: np.ndarray,
    components: dict[str, np.ndarray],
    path: Path,
) -> Path:
    observed = clean + components["total"]
    fig, axes = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    axes[0].plot(freqs, components["gp"].real, label="GP discrepancy, real", lw=1.4)
    axes[0].plot(freqs, components["iid"].real, label="iid sensor noise, real", lw=1.0, alpha=0.8)
    axes[0].plot(freqs, components["total"].real, label="total real error", lw=1.0, alpha=0.9)
    axes[0].axhline(0.0, color="black", lw=0.7)
    axes[0].set_ylabel("real error")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend(fontsize=8)

    axes[1].plot(freqs, _mag_db(clean), label="clean Ch2", lw=1.5)
    axes[1].plot(freqs, _mag_db(observed), label="observed Ch2", lw=1.1, alpha=0.85)
    axes[1].set_xscale("log")
    axes[1].set_xlabel("Frequency (Hz)")
    axes[1].set_ylabel("|.| dB (arb.)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend(fontsize=8)
    fig.suptitle("GP discrepancy plus iid sensor noise on Ch2", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    noise = NoiseConfig()
    data = generate_dataset(noise=noise)
    freqs = np.asarray(data["freqs_hz"], dtype=float)
    cov = _sqexp_cov(freqs, noise.discrepancy_scale, noise.discrepancy_corr_logfreq)

    rng = np.random.default_rng(noise.seed)
    components_by_channel = {
        name: _component_noise(freqs, noise, rng)
        for name in data["channels_clean"].keys()
    }
    ch2 = "coupled_interface_apparent_mass_modal"

    paths = [
        plot_covariance(freqs, cov, OUT_DIR / "gp_frequency_covariance.png"),
        plot_gp_samples(freqs, cov, OUT_DIR / "gp_error_samples.png"),
        plot_channel_components(
            freqs,
            data["channels_clean"][ch2],
            components_by_channel[ch2],
            OUT_DIR / "gp_error_components_ch2.png",
        ),
    ]

    target_ratio = float(np.exp(noise.discrepancy_corr_logfreq))
    short_lag = int(np.argmin(np.abs(freqs - (freqs[0] * target_ratio))))
    far_lag = -1
    report = {
        "noise_config": {
            "sigma_re": noise.sigma_re,
            "sigma_im": noise.sigma_im,
            "discrepancy_scale": noise.discrepancy_scale,
            "discrepancy_corr_logfreq": noise.discrepancy_corr_logfreq,
            "discrepancy_coordinate": noise.discrepancy_coordinate,
            "seed": noise.seed,
        },
        "interpretation": {
            "already_in_main_generator": True,
            "main_generator_function": "src/twodof/synthetic_data.py::_complex_noise",
            "inference_likelihood_function": "src/inference/mcmc.py::_log_likelihood",
            "current_limitations": [
                "GP discrepancy and iid sensor noise are added together and not stored separately in twodof_dataset.json.",
                "Real and imaginary parts get independent GP draws with the same covariance.",
                "Each channel gets an independent discrepancy draw but shares the same hyperparameters.",
                "The discrepancy is additive in raw complex channel units rather than normalized or per-channel scaled.",
                "The inference marginalizes the discrepancy through covariance; it does not sample latent discrepancy functions.",
            ],
        },
        "covariance_checks": {
            "diag_mean": float(np.mean(np.diag(cov))),
            "near_corr_reference": float(cov[0, short_lag] / cov[0, 0]),
            "far_corr_reference": float(cov[0, far_lag] / cov[0, 0]),
        },
        "figures": [str(path.relative_to(ROOT)) for path in paths],
    }
    (OUT_DIR / "gp_error_exploration.json").write_text(json.dumps(report, indent=2))

    md = f"""# GP Error Exploration

This artifact makes the current frequency-domain model discrepancy visible.

## Short Answer

Yes, Agentic BayesX generates additive model error with a zero-mean Gaussian process over natural log frequency. The current synthetic generator draws independent real and imaginary GP discrepancy functions for each channel, then adds independent sensor noise.

The inference likelihood also uses a squared-exponential log-frequency covariance, plus iid noise variance, to marginalize residual error.

## Current Settings

| Term | Value |
|---|---|
| GP scale `discrepancy_scale` | {noise.discrepancy_scale} |
| GP coordinate | {noise.discrepancy_coordinate} |
| GP correlation length `discrepancy_corr_logfreq` | {noise.discrepancy_corr_logfreq} natural-log-frequency units |
| iid real noise `sigma_re` | {noise.sigma_re} |
| iid imaginary noise `sigma_im` | {noise.sigma_im} |

## Figures

![GP covariance](<{(OUT_DIR / "gp_frequency_covariance.png").resolve()}>)

![GP samples](<{(OUT_DIR / "gp_error_samples.png").resolve()}>)

![Ch2 components](<{(OUT_DIR / "gp_error_components_ch2.png").resolve()}>)

## Important Limitations

- The main dataset currently stores only clean and observed channels. It does not store the realized GP discrepancy separately from iid sensor noise.
- Real and imaginary parts are modeled as independent GPs. That is simple and transparent, but it is not a full complex-valued GP.
- All channels share the same discrepancy scale and correlation length. This is unlikely to be adequate for real FRFs with different units and magnitudes.
- The GP discrepancy is additive in raw channel units. A per-channel or relative-error model is probably more defensible later.
- Inference marginalizes discrepancy through the covariance instead of estimating latent discrepancy curves.
"""
    (OUT_DIR / "gp_error_exploration.md").write_text(md)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
