"""Synthetic multi-channel data generator for 2DOF StatFEM/FBS prototype."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from src.twodof.model import (
    TwoDofParams,
    apparent_mass_dome_uncoupled,
    apparent_mass_from_drivepoint,
    default_from_natural_frequencies,
    power_law_force_spectrum,
    tray_accel_from_m1_force,
    tray_base_to_tray_accel_transfer,
)


CHANNEL_METADATA = {
    "dome_drive_apparent_mass_modal": {
        "label": "Ch1 dome-only modal drive-point apparent mass",
        "quantity": "F1/a1",
        "units": "synthetic mass units",
        "definition": "Uncoupled primary/dome drive-point apparent mass before tray attachment.",
    },
    "coupled_interface_apparent_mass_modal": {
        "label": "Ch2 assembled primary-side interface apparent mass",
        "quantity": "F1/a1",
        "units": "synthetic mass units",
        "definition": "Coupled system drive-point apparent mass at the primary-side interface coordinate m1.",
    },
    "coupled_tray_impact_apparent_mass_test": {
        "label": "Ch3 assembled tray impact apparent mass",
        "quantity": "F2/a2",
        "units": "synthetic mass units",
        "definition": "Coupled system drive-point apparent mass at the tray coordinate m2 during an impact/response test.",
    },
    "tray_standalone_accel_over_base": {
        "label": "Ch4 standalone tray base-to-tray acceleration transfer",
        "quantity": "a_tray/a_base",
        "units": "dimensionless complex transfer",
        "definition": "Fixed-base tray-only acceleration transmissibility from shaker table base acceleration.",
    },
    "flight_tray_accel_from_unknown_m1_force": {
        "label": "Ch5 flight tray acceleration from unknown primary forcing",
        "quantity": "a2",
        "units": "synthetic acceleration spectrum units",
        "definition": "Tray acceleration response to an unknown force spectrum applied to primary coordinate m1.",
    },
}


@dataclass(frozen=True)
class NoiseConfig:
    sigma_re: float = 0.02
    sigma_im: float = 0.02
    discrepancy_scale: float = 0.03
    discrepancy_corr_logfreq: float = 0.08
    discrepancy_coordinate: str = "natural_log_frequency"
    seed: int = 42


def _log_frequency_coordinate(freqs_hz: np.ndarray) -> np.ndarray:
    if np.any(freqs_hz <= 0.0):
        raise ValueError("log-frequency GP requires positive frequencies")
    return np.log(freqs_hz)


def _sqexp_cov(freqs_hz: np.ndarray, scale: float, corr_logfreq: float) -> np.ndarray:
    eta = _log_frequency_coordinate(freqs_hz)
    d = np.subtract.outer(eta, eta)
    return (scale**2) * np.exp(-0.5 * (d / corr_logfreq) ** 2)


def _complex_noise(
    freqs_hz: np.ndarray,
    sigma_re: float,
    sigma_im: float,
    discrepancy_scale: float,
    discrepancy_corr_logfreq: float,
    rng: np.random.Generator,
) -> np.ndarray:
    n = len(freqs_hz)
    kd = _sqexp_cov(freqs_hz, discrepancy_scale, discrepancy_corr_logfreq) + 1e-10 * np.eye(n)
    re = rng.multivariate_normal(np.zeros(n), kd) + rng.normal(0.0, sigma_re, size=n)
    im = rng.multivariate_normal(np.zeros(n), kd) + rng.normal(0.0, sigma_im, size=n)
    return re + 1j * im


def _complex_error_components(
    freqs_hz: np.ndarray,
    sigma_re: float,
    sigma_im: float,
    discrepancy_scale: float,
    discrepancy_corr_logfreq: float,
    rng: np.random.Generator,
) -> dict[str, np.ndarray]:
    n = len(freqs_hz)
    kd = _sqexp_cov(freqs_hz, discrepancy_scale, discrepancy_corr_logfreq) + 1e-10 * np.eye(n)
    gp = rng.multivariate_normal(np.zeros(n), kd) + 1j * rng.multivariate_normal(np.zeros(n), kd)
    iid = rng.normal(0.0, sigma_re, size=n) + 1j * rng.normal(0.0, sigma_im, size=n)
    return {"gp_discrepancy": gp, "iid_sensor_noise": iid, "total_error": gp + iid}


def generate_dataset(
    params: TwoDofParams | None = None,
    freqs_hz: np.ndarray | None = None,
    noise: NoiseConfig = NoiseConfig(),
) -> dict:
    p = params or default_from_natural_frequencies()
    f = freqs_hz if freqs_hz is not None else np.linspace(10.0, 180.0, 240)
    rng = np.random.default_rng(noise.seed)

    ch1_clean = apparent_mass_dome_uncoupled(f, p.m1, p.k1, p.c1)
    ch2_clean = apparent_mass_from_drivepoint(p, f, dof=0)
    ch3_clean = apparent_mass_from_drivepoint(p, f, dof=1)
    ch4_clean = tray_base_to_tray_accel_transfer(f, p)

    force_amp_true = 120.0
    force_fc_true = 85.0
    force = power_law_force_spectrum(f, amp=force_amp_true, fc=force_fc_true)
    flight_tray_accel_clean = tray_accel_from_m1_force(p, f, force)
    qoi_peak_tray_accel = float(np.max(np.abs(flight_tray_accel_clean)))

    channels_clean = {
        "dome_drive_apparent_mass_modal": ch1_clean,
        "coupled_interface_apparent_mass_modal": ch2_clean,
        "coupled_tray_impact_apparent_mass_test": ch3_clean,
        "tray_standalone_accel_over_base": ch4_clean,
        "flight_tray_accel_from_unknown_m1_force": flight_tray_accel_clean,
    }

    channels_obs: dict[str, np.ndarray] = {}
    error_components: dict[str, dict[str, np.ndarray]] = {}
    for name, arr in channels_clean.items():
        components = _complex_error_components(
            f,
            sigma_re=noise.sigma_re,
            sigma_im=noise.sigma_im,
            discrepancy_scale=noise.discrepancy_scale,
            discrepancy_corr_logfreq=noise.discrepancy_corr_logfreq,
            rng=rng,
        )
        error_components[name] = components
        channels_obs[name] = arr + components["total_error"]

    return {
        "freqs_hz": f,
        "channels_clean": channels_clean,
        "channels_obs": channels_obs,
        "error_components": error_components,
        "channel_metadata": CHANNEL_METADATA,
        "truth": {
            "params": asdict(p),
            "parameterization": {
                "tied_parameters": {"k12": "k2", "c12": "c2"},
                "independent_structural_parameters": ["k1", "k2", "c1", "c2"],
            },
            "force_amp": force_amp_true,
            "force_fc": force_fc_true,
            "qoi_peak_tray_accel": qoi_peak_tray_accel,
            "noise": asdict(noise),
        },
    }


def _pack_complex(x: np.ndarray) -> dict:
    return {"real": x.real.tolist(), "imag": x.imag.tolist()}


def save_dataset(path: Path, data: dict) -> None:
    out = {
        "freqs_hz": data["freqs_hz"].tolist(),
        "channels_clean": {k: _pack_complex(v) for k, v in data["channels_clean"].items()},
        "channels_obs": {k: _pack_complex(v) for k, v in data["channels_obs"].items()},
        "error_components": {
            channel: {name: _pack_complex(values) for name, values in components.items()}
            for channel, components in data.get("error_components", {}).items()
        },
        "channel_metadata": data.get("channel_metadata", CHANNEL_METADATA),
        "truth": data["truth"],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, indent=2))


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    d = generate_dataset()
    save_dataset(root / "artifacts" / "synthetic" / "twodof_dataset.json", d)
