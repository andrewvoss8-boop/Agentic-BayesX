#!/usr/bin/env python3
"""Fresh 2DOF StatFEM/FBS rerun with scoped artifacts and checks."""

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
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "reports" / "fresh_2dof_statfem_fbs_20260601"
FIG_DIR = OUT_DIR / "figures"
RUN_SEED = 260601
G0_M_PER_S2 = 9.80665
PRIOR_DENSITY_MC_SAMPLES = 80000
PRIOR_DENSITY_MC_BINS = 90
PRIOR_PREDICTIVE_MC_SAMPLES = 4000
PREDICTIVE_BAND_SMOOTHING_SIGMA_POINTS = 1.8
IMAGE_LEGIBILITY_RESULTS: list[dict[str, Any]] = []

CHANNELS = [
    "ch1_dome_only_reciprocal_inertance",
    "ch2_coupled_primary_reciprocal_inertance",
    "ch3_coupled_tray_reciprocal_inertance",
    "ch4_standalone_tray_accel_transmissibility",
]

CHANNEL_LABELS = {
    "ch1_dome_only_reciprocal_inertance": "Ch1 dome-only F1/a1",
    "ch2_coupled_primary_reciprocal_inertance": "Ch2 coupled primary F1/a1",
    "ch3_coupled_tray_reciprocal_inertance": "Ch3 coupled tray F2/a2",
    "ch4_standalone_tray_accel_transmissibility": "Ch4 tray a/a_base",
}

CHANNEL_UNITS = {
    "ch1_dome_only_reciprocal_inertance": "kg",
    "ch2_coupled_primary_reciprocal_inertance": "kg",
    "ch3_coupled_tray_reciprocal_inertance": "kg",
    "ch4_standalone_tray_accel_transmissibility": "dimensionless",
}


def save_figure(
    fig: plt.Figure,
    filename: str,
    *,
    dpi: int = 170,
    min_font_pt: float = 7.0,
    min_width_px: int = 1200,
    min_height_px: int = 540,
    text_heavy: bool = False,
) -> None:
    """Save a PNG and record lightweight legibility checks for the generated image."""
    path = FIG_DIR / filename
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    fig_bbox = fig.bbox
    text_artists = [
        text
        for text in fig.findobj(match=matplotlib.text.Text)
        if text.get_visible() and text.get_text().strip()
    ]
    font_sizes = [float(text.get_fontsize()) for text in text_artists]
    clipped_text = []
    plain_math_text = []
    text_bboxes = []
    for text in text_artists:
        raw = text.get_text()
        bbox = text.get_window_extent(renderer=renderer)
        if bbox.width > 2 and bbox.height > 2:
            text_bboxes.append((raw, bbox))
        if (
            bbox.x0 < fig_bbox.x0 - 4
            or bbox.y0 < fig_bbox.y0 - 4
            or bbox.x1 > fig_bbox.x1 + 4
            or bbox.y1 > fig_bbox.y1 + 4
        ):
            clipped_text.append(raw[:80])
        if text_heavy and "$" not in raw and any(token in raw for token in ["_i", "_j", "^", "sigma_", "theta)", "|H", "Sobs", "Sa2"]):
            plain_math_text.append(raw[:80])

    fig.savefig(path, dpi=dpi)
    with Image.open(path) as image:
        width_px, height_px = image.size

    issues = []
    min_observed_font = min(font_sizes) if font_sizes else None
    if width_px < min_width_px or height_px < min_height_px:
        issues.append(f"image too small: {width_px}x{height_px}, required at least {min_width_px}x{min_height_px}")
    if min_observed_font is not None and min_observed_font < min_font_pt:
        issues.append(f"minimum font {min_observed_font:.1f} pt below required {min_font_pt:.1f} pt")
    warnings = []
    if clipped_text and text_heavy:
        issues.append(f"{len(clipped_text)} text labels appear clipped")
    elif clipped_text:
        warnings.append(f"{len(clipped_text)} edge text/tick labels appear near the image boundary")
    if plain_math_text:
        issues.append("plain underscore/caret math-like text found in text-heavy figure")
    if text_heavy:
        overlaps = []
        for i, (raw_i, bbox_i) in enumerate(text_bboxes):
            for raw_j, bbox_j in text_bboxes[i + 1 :]:
                x0 = max(bbox_i.x0, bbox_j.x0)
                y0 = max(bbox_i.y0, bbox_j.y0)
                x1 = min(bbox_i.x1, bbox_j.x1)
                y1 = min(bbox_i.y1, bbox_j.y1)
                if x1 <= x0 or y1 <= y0:
                    continue
                intersection = (x1 - x0) * (y1 - y0)
                smaller = min(bbox_i.width * bbox_i.height, bbox_j.width * bbox_j.height)
                if smaller > 0 and intersection / smaller > 0.10:
                    overlaps.append([raw_i[:50], raw_j[:50]])
        if overlaps:
            issues.append(f"{len(overlaps)} overlapping text-label pairs found")

    IMAGE_LEGIBILITY_RESULTS.append(
        {
            "figure": f"figures/{filename}",
            "width_px": width_px,
            "height_px": height_px,
            "text_count": len(text_artists),
            "min_font_pt_required": min_font_pt,
            "min_font_pt_observed": min_observed_font,
            "text_heavy": text_heavy,
            "clipped_text_examples": clipped_text[:5],
            "plain_math_text_examples": plain_math_text[:5],
            "overlap_examples": overlaps[:5] if text_heavy else [],
            "issues": issues,
            "warnings": warnings,
            "pass": not issues,
        }
    )


def write_image_legibility_report() -> dict[str, Any]:
    result = {
        "checks": IMAGE_LEGIBILITY_RESULTS,
        "pass": bool(IMAGE_LEGIBILITY_RESULTS) and all(item["pass"] for item in IMAGE_LEGIBILITY_RESULTS),
        "strict_text_heavy_figures": [
            item["figure"] for item in IMAGE_LEGIBILITY_RESULTS if item.get("text_heavy")
        ],
    }
    (OUT_DIR / "image_legibility_report.json").write_text(json.dumps(result, indent=2))
    return result


def prepare_output_dirs() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_LEGIBILITY_RESULTS.clear()
    for path in FIG_DIR.glob("*.png"):
        path.unlink()


@dataclass(frozen=True)
class Params:
    k1: float
    k2: float
    zeta1: float
    zeta2: float
    force_amp: float
    force_fc: float


@dataclass(frozen=True)
class Constants:
    m1: float = 1.0
    m2: float = 0.6
    dome_nominal_hz: float = 110.0
    tray_nominal_hz: float = 75.0
    dome_frequency_model_error_rel: float = -0.150
    tray_frequency_model_error_rel: float = 0.150
    dome_damping_model_error_rel: float = 0.250
    tray_damping_model_error_rel: float = -0.250
    dome_nominal_zeta: float = 0.018
    tray_nominal_zeta: float = 0.026
    obs_noise_rel: float = 0.080
    discrepancy_rel: float = 0.200
    discrepancy_floor_rel: float = 0.200
    discrepancy_corr_logfreq: float = 0.160
    flight_force_bandwidth_logfreq: float = 0.330
    response_psd_noise_log_sigma: float = 0.180
    response_psd_discrepancy_log_sigma: float = 0.350
    response_psd_discrepancy_corr_logfreq: float = 0.180
    flight_noise_rel_std: float = 0.080
    flight_discrepancy_rel_std: float = 0.200
    t_end_s: float = 0.350
    dt_s: float = 0.001

    @property
    def k1_nom(self) -> float:
        return self.m1 * (2.0 * math.pi * self.dome_nominal_hz) ** 2

    @property
    def k2_nom(self) -> float:
        return self.m2 * (2.0 * math.pi * self.tray_nominal_hz) ** 2


def true_params(c: Constants) -> Params:
    return Params(
        k1=((1.0 + c.dome_frequency_model_error_rel) ** 2) * c.k1_nom,
        k2=((1.0 + c.tray_frequency_model_error_rel) ** 2) * c.k2_nom,
        zeta1=(1.0 + c.dome_damping_model_error_rel) * c.dome_nominal_zeta,
        zeta2=(1.0 + c.tray_damping_model_error_rel) * c.tray_nominal_zeta,
        force_amp=1.0,
        force_fc=92.0,
    )


def damping_values(p: Params, c: Constants) -> tuple[float, float]:
    c1 = 2.0 * p.zeta1 * math.sqrt(p.k1 * c.m1)
    c2 = 2.0 * p.zeta2 * math.sqrt(p.k2 * c.m2)
    return c1, c2


def mck(p: Params, c: Constants) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    c1, c2 = damping_values(p, c)
    m = np.array([[c.m1, 0.0], [0.0, c.m2]], dtype=float)
    # Fresh assembly convention: one tray-to-primary spring/damper in the coupled system.
    k = np.array([[p.k1 + p.k2, -p.k2], [-p.k2, p.k2]], dtype=float)
    damp = np.array([[c1 + c2, -c2], [-c2, c2]], dtype=float)
    return m, damp, k


def accel_over_force(p: Params, c: Constants, freqs_hz: np.ndarray) -> np.ndarray:
    m, damp, k = mck(p, c)
    out = np.zeros((len(freqs_hz), 2, 2), dtype=np.complex128)
    for i, freq in enumerate(freqs_hz):
        w = 2.0 * math.pi * float(freq)
        z = k + 1j * w * damp - (w**2) * m
        out[i] = -(w**2) * np.linalg.inv(z)
    return out


def dome_only_reciprocal_inertance(p: Params, c: Constants, freqs_hz: np.ndarray) -> np.ndarray:
    c1, _ = damping_values(p, c)
    out = []
    for freq in freqs_hz:
        w = 2.0 * math.pi * float(freq)
        z = p.k1 + 1j * w * c1 - (w**2) * c.m1
        a_over_f = -(w**2) / z
        out.append(1.0 / a_over_f)
    return np.asarray(out, dtype=np.complex128)


def coupled_reciprocal_inertance(
    p: Params, c: Constants, freqs_hz: np.ndarray, dof: int
) -> np.ndarray:
    h = accel_over_force(p, c, freqs_hz)
    return 1.0 / h[:, dof, dof]


def tray_transmissibility(p: Params, c: Constants, freqs_hz: np.ndarray) -> np.ndarray:
    _, c2 = damping_values(p, c)
    out = []
    for freq in freqs_hz:
        w = 2.0 * math.pi * float(freq)
        mount = p.k2 + 1j * w * c2
        out.append(mount / (mount - c.m2 * (w**2)))
    return np.asarray(out, dtype=np.complex128)


def sdof_source_apparent_mass(
    freqs_hz: np.ndarray,
    mass: float,
    stiffness: float,
    damping: float,
) -> np.ndarray:
    """NASA-HDBK-7004C-style source apparent mass looking back into a source."""
    out = []
    for freq in freqs_hz:
        w = 2.0 * math.pi * float(freq)
        z = stiffness + 1j * w * damping - (w**2) * mass
        out.append(-z / (w**2))
    return np.asarray(out, dtype=np.complex128)


def sdof_load_apparent_mass(
    freqs_hz: np.ndarray,
    mass: float,
    stiffness: float,
    damping: float,
) -> np.ndarray:
    """NASA-HDBK-7004C-style load apparent mass, base reaction over base acceleration."""
    out = []
    for freq in freqs_hz:
        w = 2.0 * math.pi * float(freq)
        mount = stiffness + 1j * w * damping
        dynamic = mount - (w**2) * mass
        out.append(mass * mount / dynamic)
    return np.asarray(out, dtype=np.complex128)


def nasa_7004c_figure9_normalized(r: np.ndarray, q: float = 50.0) -> dict[str, np.ndarray]:
    """Normalized Figure 9 source/load apparent-mass benchmark for identical oscillators."""
    source = np.abs(1.0 - r**2 + 1j * r / q) / np.maximum(r**2, 1e-12)
    load = np.abs(1.0 + 1j * r / q) / np.abs(1.0 - r**2 + 1j * r / q)
    return {"source": source, "load": load}


def frequency_channels(p: Params, c: Constants, freqs_hz: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "ch1_dome_only_reciprocal_inertance": dome_only_reciprocal_inertance(p, c, freqs_hz),
        "ch2_coupled_primary_reciprocal_inertance": coupled_reciprocal_inertance(
            p, c, freqs_hz, dof=0
        ),
        "ch3_coupled_tray_reciprocal_inertance": coupled_reciprocal_inertance(
            p, c, freqs_hz, dof=1
        ),
        "ch4_standalone_tray_accel_transmissibility": tray_transmissibility(p, c, freqs_hz),
    }


def integration_widths(freqs_hz: np.ndarray) -> np.ndarray:
    edges = np.empty(len(freqs_hz) + 1, dtype=float)
    edges[1:-1] = 0.5 * (freqs_hz[:-1] + freqs_hz[1:])
    edges[0] = freqs_hz[0] - 0.5 * (freqs_hz[1] - freqs_hz[0])
    edges[-1] = freqs_hz[-1] + 0.5 * (freqs_hz[-1] - freqs_hz[-2])
    return np.maximum(np.diff(edges), 1e-12)


def force_psd_n2_per_hz(
    freqs_hz: np.ndarray,
    amp: float,
    fc: float,
    bandwidth_logfreq: float,
) -> np.ndarray:
    """One-sided force PSD in N^2/Hz with amp in N/sqrt(Hz)."""
    envelope = np.exp(-0.5 * (np.log(freqs_hz / fc) / bandwidth_logfreq) ** 2)
    return (amp**2) * envelope


def force_coefficients_from_psd(
    freqs_hz: np.ndarray,
    amp: float,
    fc: float,
    bandwidth_logfreq: float,
    phases: np.ndarray,
) -> np.ndarray:
    psd = force_psd_n2_per_hz(freqs_hz, amp, fc, bandwidth_logfreq)
    widths = integration_widths(freqs_hz)
    return np.sqrt(2.0 * psd * widths) * np.exp(1j * phases)


def tray_response_psd_g2_per_hz(
    p: Params,
    c: Constants,
    freqs_hz: np.ndarray,
    bandwidth_logfreq: float | None = None,
    damping_scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    p_eff = Params(
        k1=p.k1,
        k2=p.k2,
        zeta1=p.zeta1 * damping_scale,
        zeta2=p.zeta2 * damping_scale,
        force_amp=p.force_amp,
        force_fc=p.force_fc,
    )
    bw = c.flight_force_bandwidth_logfreq if bandwidth_logfreq is None else bandwidth_logfreq
    force_psd = force_psd_n2_per_hz(freqs_hz, p.force_amp, p.force_fc, bw)
    accel_per_force_g = accel_over_force(p_eff, c, freqs_hz)[:, 1, 0] / G0_M_PER_S2
    response_psd = np.abs(accel_per_force_g) ** 2 * force_psd
    return response_psd, force_psd


def grms_from_psd(freqs_hz: np.ndarray, response_psd_g2_per_hz: np.ndarray) -> float:
    return float(math.sqrt(max(np.trapz(response_psd_g2_per_hz, freqs_hz), 0.0)))


def qoi_3grms_from_psd(
    p: Params,
    c: Constants,
    freqs_hz: np.ndarray,
    bandwidth_logfreq: float | None = None,
    damping_scale: float = 1.0,
) -> float:
    response_psd, _ = tray_response_psd_g2_per_hz(
        p, c, freqs_hz, bandwidth_logfreq=bandwidth_logfreq, damping_scale=damping_scale
    )
    return 3.0 * grms_from_psd(freqs_hz, response_psd)


def tray_time_response(
    p: Params,
    c: Constants,
    freqs_hz: np.ndarray,
    times_s: np.ndarray,
    phases: np.ndarray,
    bandwidth_logfreq: float | None = None,
    damping_scale: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    p_eff = Params(
        k1=p.k1,
        k2=p.k2,
        zeta1=p.zeta1 * damping_scale,
        zeta2=p.zeta2 * damping_scale,
        force_amp=p.force_amp,
        force_fc=p.force_fc,
    )
    bw = c.flight_force_bandwidth_logfreq if bandwidth_logfreq is None else bandwidth_logfreq
    coeff = force_coefficients_from_psd(freqs_hz, p.force_amp, p.force_fc, bw, phases)
    h = accel_over_force(p_eff, c, freqs_hz)[:, 1, 0]
    a_coeff = h * coeff
    basis = np.exp(1j * 2.0 * math.pi * times_s[:, None] * freqs_hz[None, :])
    response = np.real(basis @ a_coeff)
    force = np.real(basis @ coeff)
    return response, force


def pack_complex(x: np.ndarray) -> dict[str, list[float]]:
    return {"real": x.real.tolist(), "imag": x.imag.tolist()}


def unpack_params(x: np.ndarray, c: Constants) -> Params:
    return Params(
        k1=c.k1_nom * math.exp(float(x[0])),
        k2=c.k2_nom * math.exp(float(x[1])),
        zeta1=math.exp(float(x[2])),
        zeta2=math.exp(float(x[3])),
        force_amp=math.exp(float(x[4])),
        force_fc=math.exp(float(x[5])),
    )


def param_vector(p: Params, c: Constants) -> np.ndarray:
    return np.array(
        [
            math.log(p.k1 / c.k1_nom),
            math.log(p.k2 / c.k2_nom),
            math.log(p.zeta1),
            math.log(p.zeta2),
            math.log(p.force_amp),
            math.log(p.force_fc),
        ],
        dtype=float,
    )


def physical_sample_table(samples: np.ndarray, c: Constants) -> dict[str, np.ndarray]:
    out = {
        "k1": c.k1_nom * np.exp(samples[:, 0]),
        "k2": c.k2_nom * np.exp(samples[:, 1]),
        "zeta1": np.exp(samples[:, 2]),
        "zeta2": np.exp(samples[:, 3]),
        "force_amp": np.exp(samples[:, 4]),
        "force_fc": np.exp(samples[:, 5]),
    }
    out["dome_hz"] = np.sqrt(out["k1"] / c.m1) / (2.0 * math.pi)
    out["tray_hz"] = np.sqrt(out["k2"] / c.m2) / (2.0 * math.pi)
    return out


def sqexp_cov_logfreq(freqs_hz: np.ndarray, sigma: float, ell: float) -> np.ndarray:
    eta = np.log(freqs_hz)
    d = np.subtract.outer(eta, eta)
    return sigma**2 * np.exp(-0.5 * (d / ell) ** 2)


def sqexp_corr_logfreq(freqs_hz: np.ndarray, ell: float) -> np.ndarray:
    eta = np.log(freqs_hz)
    d = np.subtract.outer(eta, eta)
    return np.exp(-0.5 * (d / ell) ** 2)


def local_error_scale(y: np.ndarray, rel: float, floor_rel: float) -> np.ndarray:
    mag = np.abs(y)
    floor = floor_rel * max(float(np.median(mag)), 1e-12)
    return rel * np.maximum(mag, floor)


def gaussian_logpdf_chol(resid: np.ndarray, chol: np.ndarray) -> float:
    alpha = np.linalg.solve(chol, resid)
    quad = float(alpha @ alpha)
    logdet = 2.0 * float(np.log(np.diag(chol)).sum())
    return -0.5 * (quad + logdet + len(resid) * math.log(2.0 * math.pi))


def generate_synthetic(c: Constants) -> dict[str, Any]:
    rng = np.random.default_rng(RUN_SEED)
    freqs_hz = np.geomspace(12.0, 220.0, 120)
    flight_freqs_hz = np.geomspace(20.0, 200.0, 181)
    times_s = np.arange(0.0, c.t_end_s + 0.5 * c.dt_s, c.dt_s)
    phases = rng.uniform(0.0, 2.0 * math.pi, size=len(flight_freqs_hz))
    truth = true_params(c)
    clean = frequency_channels(truth, c, freqs_hz)
    flight_clean, force_time = tray_time_response(truth, c, flight_freqs_hz, times_s, phases)
    response_psd_clean, force_psd_clean = tray_response_psd_g2_per_hz(truth, c, flight_freqs_hz)

    observed: dict[str, np.ndarray] = {}
    error_components: dict[str, dict[str, np.ndarray]] = {}
    noise_scales: dict[str, dict[str, Any]] = {}
    for name, y in clean.items():
        scale_ref = max(float(np.median(np.abs(y))), 1e-8)
        sigma_obs = local_error_scale(y, c.obs_noise_rel, c.discrepancy_floor_rel)
        sigma_disc = local_error_scale(y, c.discrepancy_rel, c.discrepancy_floor_rel)
        corr = sqexp_corr_logfreq(freqs_hz, c.discrepancy_corr_logfreq)
        cov = np.outer(sigma_disc, sigma_disc) * corr
        cov = cov + 1e-12 * max(float(np.max(sigma_disc**2)), 1.0) * np.eye(len(freqs_hz))
        chol = np.linalg.cholesky(cov)
        gp = chol @ rng.normal(size=len(freqs_hz)) + 1j * (chol @ rng.normal(size=len(freqs_hz)))
        iid = rng.normal(0.0, sigma_obs) + 1j * rng.normal(0.0, sigma_obs)
        observed[name] = y + gp + iid
        error_components[name] = {
            "gp_discrepancy": gp,
            "iid_sensor_noise": iid,
            "total_error": gp + iid,
        }
        noise_scales[name] = {
            "scale_reference": scale_ref,
            "sigma_observation_median": float(np.median(sigma_obs)),
            "sigma_discrepancy_median": float(np.median(sigma_disc)),
            "sigma_observation_by_frequency": sigma_obs.tolist(),
            "sigma_discrepancy_by_frequency": sigma_disc.tolist(),
            "ell_log_frequency": c.discrepancy_corr_logfreq,
            "local_floor_relative_to_median": c.discrepancy_floor_rel,
            "units": CHANNEL_UNITS[name],
        }

    flight_std = max(float(np.std(flight_clean)), 1e-8)
    flight_discrepancy = (
        c.flight_discrepancy_rel_std
        * flight_std
        * np.sin(2.0 * math.pi * 7.0 * times_s + 0.4)
    )
    flight_noise = rng.normal(0.0, c.flight_noise_rel_std * flight_std, len(times_s))
    flight_observed = flight_clean + flight_discrepancy + flight_noise
    response_corr = sqexp_corr_logfreq(flight_freqs_hz, c.response_psd_discrepancy_corr_logfreq)
    response_cov = (c.response_psd_discrepancy_log_sigma**2) * response_corr
    response_chol = np.linalg.cholesky(response_cov + 1e-12 * np.eye(len(flight_freqs_hz)))
    response_log_gp = response_chol @ rng.normal(size=len(flight_freqs_hz))
    response_log_iid = rng.normal(0.0, c.response_psd_noise_log_sigma, len(flight_freqs_hz))
    response_log_error = response_log_gp + response_log_iid
    response_psd_observed = response_psd_clean * np.exp(response_log_error)

    return {
        "constants": c,
        "truth": truth,
        "freqs_hz": freqs_hz,
        "flight_freqs_hz": flight_freqs_hz,
        "times_s": times_s,
        "flight_phases": phases,
        "clean": clean,
        "observed": observed,
        "error_components": error_components,
        "noise_scales": noise_scales,
        "flight_clean": flight_clean,
        "flight_observed": flight_observed,
        "flight_force_time": force_time,
        "force_psd_clean": force_psd_clean,
        "response_psd_clean": response_psd_clean,
        "response_psd_observed": response_psd_observed,
        "response_psd_error_components": {
            "log_gp_discrepancy": response_log_gp,
            "log_iid_sensor_noise": response_log_iid,
            "log_total_error": response_log_error,
            "absolute_total_error": response_psd_observed - response_psd_clean,
            "sigma_log_observation": c.response_psd_noise_log_sigma,
            "sigma_log_discrepancy": c.response_psd_discrepancy_log_sigma,
            "ell_log_frequency": c.response_psd_discrepancy_corr_logfreq,
            "units": "g^2/Hz",
        },
        "flight_error_components": {
            "time_discrepancy": flight_discrepancy,
            "iid_sensor_noise": flight_noise,
            "total_error": flight_discrepancy + flight_noise,
            "sigma_observation": c.flight_noise_rel_std * flight_std,
            "sigma_discrepancy": c.flight_discrepancy_rel_std * flight_std,
            "scale_reference": flight_std,
            "units": "m/s^2",
        },
        "simulation_replicates": {
            "frequency_domain_realizations_per_channel": 1,
            "flight_like_response_psd_realizations": 1,
            "flight_time_history_realizations": 1,
            "flight_to_flight_variability_modeled": False,
            "flight_to_flight_variability_realizations": 0,
            "note": "This fresh trial generates one synthetic dataset. It does not model flight-to-flight variability or repeated experiment scatter.",
        },
    }


def prior_arrays() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    means = np.array([0.0, 0.0, math.log(0.018), math.log(0.026), math.log(0.85), math.log(95.0)])
    sigmas = np.array([0.18, 0.18, 0.35, 0.35, 0.65, 0.22])
    lower = np.array([math.log(0.55), math.log(0.55), math.log(0.004), math.log(0.004), math.log(0.10), math.log(35.0)])
    upper = np.array([math.log(1.65), math.log(1.65), math.log(0.090), math.log(0.090), math.log(5.0), math.log(170.0)])
    return means, sigmas, lower, upper


def log_prior(x: np.ndarray) -> float:
    means, sigmas, lower, upper = prior_arrays()
    if np.any(x < lower) or np.any(x > upper):
        return -math.inf
    z = (x - means) / sigmas
    return float(-0.5 * np.sum(z**2 + np.log(2.0 * math.pi * sigmas**2)))


def draw_prior_transformed(n: int, seed: int = RUN_SEED + 101) -> np.ndarray:
    rng = np.random.default_rng(seed)
    means, sigmas, lower, upper = prior_arrays()
    chunks = []
    needed = n
    while needed > 0:
        batch = rng.normal(means, sigmas, size=(max(needed * 3, 512), len(means)))
        keep = batch[np.all((batch >= lower) & (batch <= upper), axis=1)]
        if len(keep):
            chunks.append(keep[:needed])
            needed -= min(needed, len(keep))
    return np.vstack(chunks)[:n]


def prior_model_summary(c: Constants) -> dict[str, Any]:
    stiffness_sigma_log = 0.18
    frequency_sigma_log = 0.5 * stiffness_sigma_log
    damping_sigma_log = 0.35
    force_amp_sigma_log = 0.65
    force_fc_sigma_log = 0.22

    def factor_interval(sigma: float) -> list[float]:
        return [float(math.exp(-1.96 * sigma)), float(math.exp(1.96 * sigma))]

    return {
        "parameterization": "transformed positive variables: log(k1/k1_nom), log(k2/k2_nom), log(zeta1), log(zeta2), log(force_amp), log(force_fc)",
        "stiffness_prior": {
            "distribution": "log(k/k_nom) ~ Normal(0, 0.18^2), truncated to log([0.55, 1.65])",
            "sigma_log_stiffness": stiffness_sigma_log,
            "approx_95_factor_untruncated": factor_interval(stiffness_sigma_log),
        },
        "natural_frequency_prior": {
            "distribution": "because f is proportional to sqrt(k), log(f/f_nom) ~ Normal(0, 0.09^2) before truncation",
            "sigma_log_frequency": frequency_sigma_log,
            "approx_95_factor_untruncated": factor_interval(frequency_sigma_log),
            "dome_prior_center_hz": c.dome_nominal_hz,
            "tray_prior_center_hz": c.tray_nominal_hz,
        },
        "damping_prior": {
            "distribution": "log(zeta/zeta_nom) ~ Normal(0, 0.35^2), with zeta truncated to [0.004, 0.090]",
            "sigma_log_damping_ratio": damping_sigma_log,
            "approx_95_factor_untruncated": factor_interval(damping_sigma_log),
            "dome_prior_center_zeta": c.dome_nominal_zeta,
            "tray_prior_center_zeta": c.tray_nominal_zeta,
        },
        "force_prior": {
            "force_amp": "log(A/0.85 N/sqrt(Hz)) ~ Normal(0, 0.65^2), truncated to [0.10, 5.0]",
            "force_amp_sigma_log": force_amp_sigma_log,
            "force_center": "log(fc/95 Hz) ~ Normal(0, 0.22^2), truncated to [35, 170] Hz",
            "force_center_sigma_log": force_fc_sigma_log,
        },
    }


def likelihood_formulation_summary(c: Constants) -> dict[str, Any]:
    return {
        "uses_whole_frf_not_peak_summary": True,
        "frequency_channels": {
            "data_used": "all complex FRF/transfer values at 120 log-spaced frequencies for Ch1-Ch4",
            "residual": "observed complex channel value minus model complex channel value at every frequency point",
            "covariance": "C = K_discrepancy + diag(sigma_sensor^2), with K_ij = sigma_d(f_i) sigma_d(f_j) exp(-0.5*((ln f_i - ln f_j)/ell)^2)",
            "real_imag_treatment": "real and imaginary residual vectors are evaluated independently with the same covariance",
            "peak_usage": "peak/notch locations are used only for reference checks and plots, not as likelihood summary statistics",
        },
        "flight_response_psd": {
            "data_used": "all log response-PSD values at 181 log-spaced frequencies",
            "residual": "log(observed PSD) minus log(model response PSD) at every frequency point",
            "covariance": "C_logPSD = sigma_log_discrepancy^2 R_logfreq + sigma_log_sensor^2 I",
            "qoi": "3*GRMS is computed after posterior sampling from each sampled response PSD; it is not the only data used in the likelihood",
        },
        "not_inferred": {
            "realized_discrepancy_field": True,
            "noise_hyperparameters": True,
            "flight_to_flight_variability": True,
        },
        "desired_next_step": "Infer discrepancy fields and/or hyperparameters in a hierarchical StatFEM model, preferably with replicate data so sensor noise, flight-to-flight variability, and model discrepancy are identifiable.",
    }


def make_likelihood(data: dict[str, Any]) -> Any:
    c: Constants = data["constants"]
    freqs_hz = data["freqs_hz"]
    observed = data["observed"]
    cov_chol = {}
    for name in CHANNELS:
        ns = data["noise_scales"][name]
        sigma_disc = np.asarray(ns["sigma_discrepancy_by_frequency"], dtype=float)
        sigma_obs = np.asarray(ns["sigma_observation_by_frequency"], dtype=float)
        corr = sqexp_corr_logfreq(freqs_hz, c.discrepancy_corr_logfreq)
        cov = np.outer(sigma_disc, sigma_disc) * corr + np.diag(sigma_obs**2)
        cov_chol[name] = np.linalg.cholesky(cov + 1e-12 * np.eye(len(freqs_hz)))

    psd_freqs = data["flight_freqs_hz"]
    psd_corr = sqexp_corr_logfreq(psd_freqs, c.response_psd_discrepancy_corr_logfreq)
    psd_cov = (
        (c.response_psd_discrepancy_log_sigma**2) * psd_corr
        + (c.response_psd_noise_log_sigma**2) * np.eye(len(psd_freqs))
    )
    psd_chol = np.linalg.cholesky(psd_cov + 1e-12 * np.eye(len(psd_freqs)))
    log_response_psd_observed = np.log(np.maximum(data["response_psd_observed"], 1e-30))

    def log_likelihood(x: np.ndarray) -> float:
        p = unpack_params(x, c)
        pred = frequency_channels(p, c, freqs_hz)
        total = 0.0
        for name in CHANNELS:
            resid = observed[name] - pred[name]
            total += gaussian_logpdf_chol(resid.real, cov_chol[name])
            total += gaussian_logpdf_chol(resid.imag, cov_chol[name])
        response_psd_pred, _ = tray_response_psd_g2_per_hz(p, c, psd_freqs)
        psd_resid = log_response_psd_observed - np.log(np.maximum(response_psd_pred, 1e-30))
        total += gaussian_logpdf_chol(psd_resid, psd_chol)
        return total

    return log_likelihood


FEATURE_SPECS = [
    ("ch1_dome_notch", "ch1_dome_only_reciprocal_inertance", "min", "FRF"),
    ("ch2_primary_notch", "ch2_coupled_primary_reciprocal_inertance", "min", "FRF"),
    ("ch3_tray_notch", "ch3_coupled_tray_reciprocal_inertance", "min", "FRF"),
    ("ch4_tray_peak", "ch4_standalone_tray_accel_transmissibility", "max", "FRF"),
    ("ch5_response_psd_peak", "response_psd", "max", "PSD"),
]


def extremum_feature(freqs_hz: np.ndarray, values: np.ndarray, kind: str) -> dict[str, float]:
    mag = np.maximum(np.abs(values), 1e-30)
    score = np.log(mag)
    idx = int(np.argmax(score) if kind == "max" else np.argmin(score))
    eta = np.log(freqs_hz)
    eta_star = float(eta[idx])
    log_amp = float(score[idx])
    if 0 < idx < len(freqs_hz) - 1:
        local_eta = eta[idx - 1 : idx + 2]
        local_score = score[idx - 1 : idx + 2]
        a, b, cc = np.polyfit(local_eta, local_score, 2)
        if abs(a) > 1e-12:
            candidate = float(-b / (2.0 * a))
            curvature_ok = (kind == "max" and a < 0.0) or (kind == "min" and a > 0.0)
            bracket_ok = float(local_eta[0]) <= candidate <= float(local_eta[-1])
            if curvature_ok and bracket_ok:
                eta_star = candidate
                log_amp = float(a * candidate**2 + b * candidate + cc)
    return {
        "frequency_hz": float(math.exp(eta_star)),
        "log_amplitude": log_amp,
        "amplitude": float(math.exp(log_amp)),
    }


def extract_peak_feature_vector(
    data: dict[str, Any],
    p: Params | None = None,
    observed: bool = False,
) -> dict[str, dict[str, float | str]]:
    c: Constants = data["constants"]
    freqs = data["freqs_hz"]
    flight_freqs = data["flight_freqs_hz"]
    if observed:
        channels = data["observed"]
        response_psd = data["response_psd_observed"]
    else:
        if p is None:
            raise ValueError("A model parameter set is required unless observed=True")
        channels = frequency_channels(p, c, freqs)
        response_psd, _ = tray_response_psd_g2_per_hz(p, c, flight_freqs)
    features: dict[str, dict[str, float | str]] = {}
    for feature_name, channel_name, kind, source in FEATURE_SPECS:
        if source == "PSD":
            feature = extremum_feature(flight_freqs, response_psd, kind)
        else:
            feature = extremum_feature(freqs, channels[channel_name], kind)
        feature["kind"] = kind
        feature["source"] = source
        feature["channel"] = channel_name
        features[feature_name] = feature
    return features


def feature_likelihood_assumptions() -> dict[str, float | str]:
    return {
        "description": "Lossy comparison likelihood using only selected peak/notch frequency and magnitude features, not whole curves.",
        "frf_log_frequency_sigma": 0.06,
        "frf_log_amplitude_sigma": 0.30,
        "psd_log_frequency_sigma": 0.06,
        "psd_log_amplitude_sigma": 0.40,
        "independence_assumption": "Feature residuals are treated as independent for this comparison artifact.",
    }


def make_peak_feature_likelihood(data: dict[str, Any]) -> Any:
    c: Constants = data["constants"]
    observed_features = extract_peak_feature_vector(data, observed=True)
    assumptions = feature_likelihood_assumptions()

    def normal_logpdf(resid: float, sigma: float) -> float:
        return -0.5 * ((resid / sigma) ** 2 + math.log(2.0 * math.pi * sigma**2))

    def log_likelihood(x: np.ndarray) -> float:
        p = unpack_params(x, c)
        model_features = extract_peak_feature_vector(data, p=p, observed=False)
        total = 0.0
        for name, obs in observed_features.items():
            pred = model_features[name]
            if obs["source"] == "PSD":
                sigma_f = float(assumptions["psd_log_frequency_sigma"])
                sigma_a = float(assumptions["psd_log_amplitude_sigma"])
            else:
                sigma_f = float(assumptions["frf_log_frequency_sigma"])
                sigma_a = float(assumptions["frf_log_amplitude_sigma"])
            total += normal_logpdf(
                math.log(float(obs["frequency_hz"]) / max(float(pred["frequency_hz"]), 1e-30)),
                sigma_f,
            )
            total += normal_logpdf(float(obs["log_amplitude"]) - float(pred["log_amplitude"]), sigma_a)
        return total

    log_likelihood.observed_features = observed_features  # type: ignore[attr-defined]
    log_likelihood.assumptions = assumptions  # type: ignore[attr-defined]
    return log_likelihood


def run_mcmc(
    data: dict[str, Any],
    *,
    likelihood_kind: str = "full_curve",
    seed_offset: int = 17,
    n_steps: int = 3800,
    burn: int = 1000,
    thin: int = 5,
) -> dict[str, Any]:
    c: Constants = data["constants"]
    rng = np.random.default_rng(RUN_SEED + seed_offset)
    if likelihood_kind == "full_curve":
        log_likelihood = make_likelihood(data)
        proposal = np.array([0.022, 0.022, 0.050, 0.050, 0.055, 0.024])
    elif likelihood_kind == "peak_feature":
        log_likelihood = make_peak_feature_likelihood(data)
        proposal = np.array([0.035, 0.035, 0.075, 0.075, 0.085, 0.040])
    else:
        raise ValueError(f"Unknown likelihood kind {likelihood_kind}")
    x = np.array([0.0, 0.0, math.log(0.018), math.log(0.026), math.log(0.85), math.log(95.0)])
    current = log_prior(x) + log_likelihood(x)
    accepted = 0
    traces = np.zeros((n_steps, len(x)))
    logps = np.zeros(n_steps)
    samples = []
    sample_logps = []
    for step in range(n_steps):
        j = int(rng.integers(0, len(x)))
        cand = x.copy()
        cand[j] += rng.normal(0.0, proposal[j])
        cand_logp = log_prior(cand)
        if math.isfinite(cand_logp):
            cand_logp += log_likelihood(cand)
        if math.log(rng.uniform()) < cand_logp - current:
            x = cand
            current = cand_logp
            accepted += 1
        traces[step] = x
        logps[step] = current
        if step >= burn and (step - burn) % thin == 0:
            samples.append(x.copy())
            sample_logps.append(current)
    samples_arr = np.asarray(samples)
    qoi_samples = compute_qoi_samples(samples_arr, data)
    phys = physical_sample_table(samples_arr, c)
    return {
        "samples_transformed": samples_arr,
        "sample_logps": np.asarray(sample_logps),
        "traces": traces,
        "logps": logps,
        "acceptance_rate": accepted / n_steps,
        "burn": burn,
        "thin": thin,
        "proposal_scales": proposal,
        "physical_samples": phys,
        "qoi_samples": qoi_samples,
        "likelihood_kind": likelihood_kind,
    }


def compute_qoi_samples(
    samples: np.ndarray,
    data: dict[str, Any],
    damping_scale: float = 1.0,
    bandwidth_logfreq: float | None = None,
    metric: str = "three_grms",
    max_samples: int | None = None,
) -> np.ndarray:
    c: Constants = data["constants"]
    selected = samples if max_samples is None else samples[:max_samples]
    out = []
    for x in selected:
        p = unpack_params(x, c)
        response_psd, _ = tray_response_psd_g2_per_hz(
            p,
            c,
            data["flight_freqs_hz"],
            bandwidth_logfreq=bandwidth_logfreq,
            damping_scale=damping_scale,
        )
        grms = grms_from_psd(data["flight_freqs_hz"], response_psd)
        if metric == "grms":
            out.append(grms)
        else:
            out.append(3.0 * grms)
    return np.asarray(out, dtype=float)


def summarize(values: np.ndarray) -> dict[str, float]:
    return {
        "mean": float(np.mean(values)),
        "median": float(np.median(values)),
        "sd": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
        "q025": float(np.quantile(values, 0.025)),
        "q05": float(np.quantile(values, 0.05)),
        "q95": float(np.quantile(values, 0.95)),
        "q975": float(np.quantile(values, 0.975)),
    }


def truth_summary(data: dict[str, Any]) -> dict[str, float]:
    c: Constants = data["constants"]
    truth: Params = data["truth"]
    c1, c2 = damping_values(truth, c)
    return {
        "m1": c.m1,
        "m2": c.m2,
        "k1_nom": c.k1_nom,
        "k2_nom": c.k2_nom,
        "k1": truth.k1,
        "k2": truth.k2,
        "zeta1": truth.zeta1,
        "zeta2": truth.zeta2,
        "c1": c1,
        "c2": c2,
        "dome_nominal_hz": c.dome_nominal_hz,
        "tray_nominal_hz": c.tray_nominal_hz,
        "dome_true_hz": math.sqrt(truth.k1 / c.m1) / (2.0 * math.pi),
        "tray_true_hz": math.sqrt(truth.k2 / c.m2) / (2.0 * math.pi),
        "force_amp": truth.force_amp,
        "force_fc": truth.force_fc,
        "flight_force_bandwidth_logfreq": c.flight_force_bandwidth_logfreq,
        "flight_time_peak_tray_accel_m_per_s2": float(np.max(np.abs(data["flight_clean"]))),
        "qoi_truth_3grms_tray_accel_g": 3.0 * grms_from_psd(
            data["flight_freqs_hz"], data["response_psd_clean"]
        ),
        "qoi_truth_grms_tray_accel_g": grms_from_psd(data["flight_freqs_hz"], data["response_psd_clean"]),
    }


def save_dataset(data: dict[str, Any]) -> None:
    ts = truth_summary(data)
    out = {
        "seed": RUN_SEED,
        "freqs_hz": data["freqs_hz"].tolist(),
        "flight_freqs_hz": data["flight_freqs_hz"].tolist(),
        "times_s": data["times_s"].tolist(),
        "flight_phases_rad": data["flight_phases"].tolist(),
        "channels_clean": {k: pack_complex(v) for k, v in data["clean"].items()},
        "channels_observed": {k: pack_complex(v) for k, v in data["observed"].items()},
        "error_components": {
            ch: {name: pack_complex(value) for name, value in comp.items()}
            for ch, comp in data["error_components"].items()
        },
        "noise_scales": data["noise_scales"],
        "flight_clean": data["flight_clean"].tolist(),
        "flight_observed": data["flight_observed"].tolist(),
        "flight_force_time": data["flight_force_time"].tolist(),
        "force_psd_clean_n2_per_hz": data["force_psd_clean"].tolist(),
        "response_psd_clean_g2_per_hz": data["response_psd_clean"].tolist(),
        "response_psd_observed_g2_per_hz": data["response_psd_observed"].tolist(),
        "response_psd_error_components": {
            key: (value.tolist() if isinstance(value, np.ndarray) else value)
            for key, value in data["response_psd_error_components"].items()
        },
        "flight_error_components": {
            key: (value.tolist() if isinstance(value, np.ndarray) else value)
            for key, value in data["flight_error_components"].items()
        },
        "simulation_replicates": data["simulation_replicates"],
        "truth": ts,
        "channel_units": CHANNEL_UNITS,
        "channel_labels": CHANNEL_LABELS,
    }
    (OUT_DIR / "fresh_2dof_dataset.json").write_text(json.dumps(out, indent=2))


def write_assumptions_json(data: dict[str, Any]) -> None:
    c: Constants = data["constants"]
    ts = truth_summary(data)
    rows = [
        ("Primary/dome mass m1", c.m1, "kg", "Synthetic choice", "Smaller audit-friendly model", "Medium", "Model/QOI"),
        ("Tray mass m2", c.m2, "kg", "Synthetic choice", "Secondary is lighter than primary", "Medium", "Model/QOI"),
        ("Nominal dome natural frequency", c.dome_nominal_hz, "Hz", "User prompt", "Required nominal dome frequency", "High", "Priors/reference"),
        ("Nominal tray natural frequency", c.tray_nominal_hz, "Hz", "User prompt", "Required nominal tray frequency", "High", "Priors/reference"),
        ("Nominal dome stiffness k1_nom", c.k1_nom, "N/m", "Derived", "m1*(2*pi*f)^2", "High", "Priors/model"),
        ("Nominal tray coupling stiffness k2_nom", c.k2_nom, "N/m", "Derived", "m2*(2*pi*f)^2", "High", "Priors/model"),
        ("Dome frequency model error", c.dome_frequency_model_error_rel, "fractional frequency shift", "Human review", "Model-form error shifts dome frequency -15% from nominal", "High", "Synthetic truth/sensitivity"),
        ("Tray frequency model error", c.tray_frequency_model_error_rel, "fractional frequency shift", "Human review", "Model-form error shifts tray frequency +15% from nominal", "High", "Synthetic truth/sensitivity"),
        ("Dome damping model error", c.dome_damping_model_error_rel, "fractional damping-ratio shift", "Human review", "Model-form error shifts dome damping +25% from nominal", "High", "Synthetic truth/sensitivity"),
        ("Tray damping model error", c.tray_damping_model_error_rel, "fractional damping-ratio shift", "Human review", "Model-form error shifts tray damping -25% from nominal", "High", "Synthetic truth/sensitivity"),
        ("True dome stiffness k1", ts["k1"], "N/m", "Derived synthetic truth", "Implements -15% dome frequency error through stiffness", "High", "Synthetic truth"),
        ("True tray coupling stiffness k2", ts["k2"], "N/m", "Derived synthetic truth", "Implements +15% tray frequency error through stiffness", "High", "Synthetic truth"),
        ("True dome local frequency", ts["dome_true_hz"], "Hz", "Derived synthetic truth", "Computed from true k1 and m1 after -15% model-form frequency shift", "High", "Synthetic truth/reference"),
        ("True tray local frequency", ts["tray_true_hz"], "Hz", "Derived synthetic truth", "Computed from true k2 and m2 after +15% model-form frequency shift", "High", "Synthetic truth/reference"),
        ("True dome damping ratio zeta1", ts["zeta1"], "ratio", "Derived synthetic truth", "Implements +25% dome damping model error", "High", "Synthetic truth/sensitivity"),
        ("True tray damping ratio zeta2", ts["zeta2"], "ratio", "Derived synthetic truth", "Implements -25% tray damping model error", "High", "Synthetic truth/sensitivity"),
        ("True dome damping c1", ts["c1"], "N s/m", "Derived synthetic truth", "Computed from true k1, m1, and zeta1", "Medium", "Synthetic truth"),
        ("True tray damping c2", ts["c2"], "N s/m", "Derived synthetic truth", "Computed from true k2, m2, and zeta2", "Medium", "Synthetic truth"),
        ("Observation noise scale", c.obs_noise_rel, "relative to local channel magnitude with floor", "NASA/ECSS-informed synthetic choice", "Test tolerances and FRF estimation scatter make the earlier 2.5% assumption too clean", "High", "Synthetic data/likelihood"),
        ("Discrepancy GP scale", c.discrepancy_rel, "relative to local channel magnitude with floor", "NASA/NESC-informed synthetic choice", "Model-form and boundary-condition errors should dominate sensor noise in this toy", "High", "Synthetic data/likelihood"),
        ("Local error floor", c.discrepancy_floor_rel, "fraction of channel median magnitude", "Synthetic robustness choice", "Prevents noise from vanishing at reciprocal-inertance notches", "High", "Synthetic data/likelihood"),
        ("Discrepancy GP correlation length", c.discrepancy_corr_logfreq, "natural log frequency", "Harness convention", "Frequency-ratio correlation", "High", "Synthetic data/likelihood"),
        ("Response PSD log observation scatter", c.response_psd_noise_log_sigma, "natural log PSD", "ECSS/NASA-informed synthetic choice", "Represents random vibration PSD estimate/control scatter", "High", "Synthetic data/likelihood/QOI"),
        ("Response PSD log discrepancy", c.response_psd_discrepancy_log_sigma, "natural log PSD", "NASA/NESC-informed synthetic choice", "Represents correlated model-form error in response PSD", "High", "Synthetic data/likelihood/QOI"),
        ("Flight force amplitude", ts["force_amp"], "N/sqrt(Hz)", "Synthetic choice", "Sets one-sided force PSD level for a visible tray response", "High", "Synthetic truth/QOI"),
        ("Flight force center", ts["force_fc"], "Hz", "Synthetic choice", "Forcing overlaps tray/dome band", "High", "Synthetic truth/QOI"),
        ("Flight force bandwidth", c.flight_force_bandwidth_logfreq, "natural log frequency", "Synthetic choice", "Broad flight-like band", "High", "Synthetic truth/sensitivity"),
        ("Generated dataset count", "1 synthetic realization per measurement class", "categorical", "Implementation fact", "This trial does not simulate repeated flights or repeated tests", "High", "Report/checker"),
        ("Flight-to-flight variability modeled", "No", "categorical", "Implementation fact", "Repeated-flight scatter is a missing capability and is not included in the posterior", "High", "Limitations/human review"),
        ("QOI definition", "3 * GRMS of tray acceleration response PSD", "g", "NASA-STD-5002B random-vibration practice", "Peak-equivalent random vibration metric from response PSD", "High", "QOI/report/checker"),
        ("Stiffness prior standard deviation", 0.18, "natural log stiffness ratio", "Synthetic inference choice", "log(k/k_nom) prior spread for k1 and k2", "High", "Posterior"),
        ("Implied natural-frequency prior standard deviation", 0.09, "natural log frequency ratio", "Derived from stiffness prior", "Because natural frequency is proportional to sqrt(k), log(f/f_nom) has half the stiffness log spread", "High", "Posterior/report"),
        ("Implied natural-frequency prior 95% factor", "0.838 to 1.193 before truncation", "frequency ratio", "Derived from sigma_log_frequency=0.09", "Shows the initial frequency uncertainty implied by the stiffness prior", "High", "Posterior/report"),
        ("Damping prior standard deviation", 0.35, "natural log damping-ratio ratio", "Synthetic inference choice", "log(zeta/zeta_nom) prior spread for zeta1 and zeta2", "High", "Posterior"),
        ("Damping prior 95% factor", "0.504 to 1.986 before truncation", "damping-ratio multiplier", "Derived from sigma_log_zeta=0.35", "Shows the initial damping uncertainty before truncation to [0.004, 0.090]", "High", "Posterior/report"),
        ("Likelihood data usage", "Whole complex FRFs and whole log response PSD", "categorical", "Implementation fact", "The likelihood uses every frequency point, not only peak locations or magnitudes", "High", "Likelihood/report/checker"),
        ("Peak-feature comparison frequency scatter", 0.06, "natural log frequency", "Comparison assumption", "Feature-only likelihood needs a peak-picking frequency error model", "High", "Peak-feature comparison"),
        ("Peak-feature comparison FRF amplitude scatter", 0.30, "natural log amplitude", "Comparison assumption", "Lumped peak/notch amplitude uncertainty for FRF feature residuals", "High", "Peak-feature comparison"),
        ("Peak-feature comparison PSD amplitude scatter", 0.40, "natural log PSD amplitude", "Comparison assumption", "Lumped response-PSD peak amplitude uncertainty for feature residuals", "High", "Peak-feature comparison"),
        ("Frequency plot x-axis", "log", "categorical", "Harness gate", "Broadband structural dynamics default", "High", "Plots/checker"),
        ("Magnitude scale", "linear", "categorical", "Harness gate", "Preserve units", "High", "Plots/report"),
        ("Coupled assembly boundary", "fixed base; m1-to-base, m2-to-m1 only", "categorical", "Fresh modeling choice", "Avoid double-counting tray stiffness", "High", "Model/contracts"),
    ]
    ledger = [
        {
            "assumption": r[0],
            "value": r[1],
            "units": r[2],
            "source": r[3],
            "rationale": r[4],
            "sensitivity_priority": r[5],
            "where_used": r[6],
        }
        for r in rows
    ]
    (OUT_DIR / "assumptions_ledger.json").write_text(json.dumps({"rows": ledger}, indent=2))


def plot_model_schematic(data: dict[str, Any]) -> None:
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.set_axis_off()
    ax.plot([0.05, 0.05], [0.15, 0.85], color="black", lw=3)
    ax.add_patch(plt.Rectangle((0.28, 0.42), 0.16, 0.16, fc="#d9e7f5", ec="black"))
    ax.add_patch(plt.Rectangle((0.68, 0.42), 0.16, 0.16, fc="#f8d9cf", ec="black"))
    ax.text(0.36, 0.50, "m1\nprimary dome", ha="center", va="center")
    ax.text(0.76, 0.50, "m2\ntray", ha="center", va="center")
    ax.plot([0.05, 0.28], [0.50, 0.50], color="#555", lw=2)
    ax.plot([0.44, 0.68], [0.50, 0.50], color="#555", lw=2)
    ax.text(0.165, 0.57, "k1, c1", ha="center")
    ax.text(0.56, 0.57, "k2, c2", ha="center")
    ax.annotate("F1", xy=(0.36, 0.67), xytext=(0.36, 0.92), arrowprops={"arrowstyle": "->"})
    ax.annotate("F2", xy=(0.76, 0.67), xytext=(0.76, 0.92), arrowprops={"arrowstyle": "->"})
    ax.text(0.5, 0.08, "Fresh assembly: fixed base, one tray-to-primary coupling, no tray-to-base spring in coupled model", ha="center")
    fig.tight_layout()
    save_figure(fig, "model_schematic.png")
    plt.close(fig)


def plot_workflow() -> None:
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.set_axis_off()
    labels = ["Question\ncontracts", "Synthetic\ntruth", "Noisy + GP\nmeasurements", "StatFEM-like\nlikelihood", "Posterior\nsamples", "QOI +\nsensitivity", "Checker +\nreport"]
    xs = np.linspace(0.08, 0.92, len(labels))
    for x, label in zip(xs, labels):
        ax.add_patch(plt.Rectangle((x - 0.055, 0.42), 0.11, 0.18, fc="#f4f4f4", ec="#333"))
        ax.text(x, 0.51, label, ha="center", va="center", fontsize=9)
    for x0, x1 in zip(xs[:-1], xs[1:]):
        ax.annotate("", xy=(x1 - 0.06, 0.51), xytext=(x0 + 0.06, 0.51), arrowprops={"arrowstyle": "->"})
    ax.text(0.5, 0.22, "Anti-cheating trace: generated data, error components, assumptions, posterior samples, sensitivity, and checks are all written to disk.", ha="center")
    fig.tight_layout()
    save_figure(fig, "workflow_diagram.png")
    plt.close(fig)


def plot_statfem_likelihood_graphical_model() -> None:
    fig, ax = plt.subplots(figsize=(14, 9.2))
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_axis_off()

    def card(
        x: float,
        y: float,
        w: float,
        h: float,
        text: str,
        fc: str,
        ec: str = "#333333",
        lw: float = 1.3,
        fontsize: float = 12.0,
        linespacing: float = 1.15,
    ) -> None:
        patch = mpatches.FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.018,rounding_size=0.018",
            fc=fc,
            ec=ec,
            lw=lw,
        )
        ax.add_patch(patch)
        ax.text(
            x + 0.018,
            y + h - 0.035,
            text,
            ha="left",
            va="top",
            fontsize=fontsize,
            linespacing=linespacing,
        )

    def arrow(start: tuple[float, float], end: tuple[float, float]) -> None:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.5, "color": "#222222"})

    ax.text(
        0.50,
        0.955,
        "Fresh 2DOF StatFEM/FBS method summary",
        ha="center",
        va="center",
        fontsize=18,
        weight="bold",
    )
    ax.text(
        0.50,
        0.915,
        "Run-specific assumptions and likelihood; this is not a generic paper diagram.",
        ha="center",
        va="center",
        fontsize=12.5,
    )

    card(
        0.04,
        0.70,
        0.28,
        0.17,
        "Inferred variables\n"
        r"$\theta=\{k_1,k_2,\zeta_1,\zeta_2,A,f_c\}$" "\n"
        "stiffness, damping, forcing",
        "#d9e7f5",
        fontsize=12.8,
    )
    card(
        0.36,
        0.70,
        0.28,
        0.17,
        "Observed data\n"
        "Ch1-Ch4 complex FRFs\n"
        "120 frequencies/channel\n"
        "Ch5 response PSD: 181 points",
        "#d9ead3",
        fontsize=12.8,
    )
    card(
        0.68,
        0.70,
        0.28,
        0.17,
        "Fixed or not inferred\n"
        "m1, m2, fixed base\n"
        "noise/discrepancy hyperparams\n"
        "no flight-to-flight variability",
        "#f7cccc",
        ec="#9b2d2d",
        lw=1.5,
        fontsize=12.8,
    )
    card(
        0.04,
        0.43,
        0.28,
        0.18,
        "2DOF forward model\n"
        r"$M,\ C(\theta),\ K(\theta)$" "\n"
        r"$H_i(f;\theta)$ for FRFs" "\n"
        r"$S_{a2}(f;\theta)=|H_{21}/g|^2S_F$",
        "#ffffff",
        fontsize=13.0,
    )
    card(
        0.04,
        0.22,
        0.28,
        0.13,
        "Outputs\n"
        "posterior samples\n"
        "posterior predictive bands\n"
        "QOI = 3*GRMS samples",
        "#d9ead3",
        fontsize=12.8,
    )
    card(
        0.38,
        0.30,
        0.58,
        0.33,
        "",
        "#fff2cc",
        fontsize=13.0,
    )
    ax.text(0.41, 0.585, "Whole-curve likelihood actually fit", fontsize=15, weight="bold", ha="left", va="center")
    ax.text(
        0.41,
        0.530,
        r"$y_i^{\mathrm{FRF}}(f_j)=H_i(f_j;\theta)+d_i(f_j)+e_i(f_j)$",
        fontsize=15,
        ha="left",
        va="center",
    )
    ax.text(
        0.41,
        0.475,
        r"$\mathrm{Re}(r_i),\mathrm{Im}(r_i)\sim\mathcal{N}(0,\ K_{d,i}+\mathrm{diag}(\sigma_{e,i}^2))$",
        fontsize=15,
        ha="left",
        va="center",
    )
    ax.text(
        0.41,
        0.410,
        r"$\log S_{\mathrm{obs}}(f_j)=\log S_{a2}(f_j;\theta)+d_{\mathrm{PSD}}(f_j)+e_{\mathrm{PSD}}(f_j)$",
        fontsize=15,
        ha="left",
        va="center",
    )
    ax.text(
        0.41,
        0.355,
        r"$r_{\mathrm{PSD}}\sim\mathcal{N}(0,\ K_{d,\mathrm{PSD}}+\sigma_e^2I)$",
        fontsize=15,
        ha="left",
        va="center",
    )

    arrow((0.18, 0.70), (0.18, 0.61))
    arrow((0.50, 0.70), (0.62, 0.63))
    arrow((0.82, 0.70), (0.72, 0.63))
    arrow((0.32, 0.52), (0.38, 0.50))
    arrow((0.67, 0.30), (0.30, 0.285))
    ax.text(
        0.50,
        0.095,
        "Peak and notch locations are reference checks only. They are not likelihood summary statistics.",
        ha="center",
        va="center",
        fontsize=13.0,
        weight="bold",
    )
    fig.tight_layout()
    save_figure(
        fig,
        "statfem_likelihood_graphical_model_legible.png",
        dpi=190,
        min_font_pt=12.0,
        min_width_px=2400,
        min_height_px=1500,
        text_heavy=True,
    )
    plt.close(fig)


def plot_assumptions(data: dict[str, Any]) -> None:
    ts = truth_summary(data)
    c: Constants = data["constants"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
    axes[0].bar(["dome\nnom", "dome\ntrue", "tray\nnom", "tray\ntrue"], [c.dome_nominal_hz, ts["dome_true_hz"], c.tray_nominal_hz, ts["tray_true_hz"]], color=["#9fbad7", "#4f7cac", "#e5aa9b", "#c65b42"])
    axes[0].set_ylabel("Hz")
    axes[0].set_title("Natural-frequency assumptions")
    axes[1].bar(["zeta1", "zeta2"], [ts["zeta1"], ts["zeta2"]], color=["#4f7cac", "#c65b42"])
    axes[1].set_ylabel("damping ratio")
    axes[1].set_title("True damping")
    axes[2].bar(["iid obs", "GP discrep.", "GP ell"], [c.obs_noise_rel, c.discrepancy_rel, c.discrepancy_corr_logfreq], color=["#767676", "#6a9f58", "#d08c2f"])
    axes[2].set_title("Relative error assumptions")
    axes[2].set_ylabel("relative or ln-frequency")
    fig.tight_layout()
    save_figure(fig, "assumptions_graphical.png")
    plt.close(fig)


def plot_channels(data: dict[str, Any]) -> None:
    freqs = data["freqs_hz"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    for ax, name in zip(axes.flat, CHANNELS):
        ax.plot(freqs, np.abs(data["clean"][name]), label="clean truth", lw=2)
        ax.scatter(freqs, np.abs(data["observed"][name]), label="observed", s=10, alpha=0.65)
        ax.set_xscale("log")
        ax.set_title(f"{CHANNEL_LABELS[name]} [{CHANNEL_UNITS[name]}]")
        ax.set_ylabel("linear magnitude")
        ax.grid(True, which="both", alpha=0.25)
    axes[-1, 0].set_xlabel("frequency [Hz]")
    axes[-1, 1].set_xlabel("frequency [Hz]")
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.tight_layout()
    save_figure(fig, "channel_truth_vs_observed.png")
    plt.close(fig)


def plot_errors(data: dict[str, Any]) -> None:
    freqs = data["freqs_hz"]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    for ax, name in zip(axes.flat, CHANNELS):
        comp = data["error_components"][name]
        ax.plot(freqs, np.abs(comp["gp_discrepancy"]), label="|GP discrepancy|", lw=1.6)
        ax.plot(freqs, np.abs(comp["iid_sensor_noise"]), label="|iid noise|", lw=1.2)
        ax.plot(freqs, np.abs(comp["total_error"]), label="|total injected error|", lw=1.4)
        ax.set_xscale("log")
        ax.set_title(CHANNEL_LABELS[name])
        ax.set_ylabel(f"absolute error [{CHANNEL_UNITS[name]}]")
        ax.grid(True, which="both", alpha=0.25)
    axes[-1, 0].set_xlabel("frequency [Hz]")
    axes[-1, 1].set_xlabel("frequency [Hz]")
    axes[0, 0].legend(loc="best", fontsize=8)
    fig.tight_layout()
    save_figure(fig, "channel_absolute_error.png")
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    for ax, name in zip(axes.flat, CHANNELS):
        clean_mag = np.abs(data["clean"][name])
        denom = np.maximum(clean_mag, np.quantile(clean_mag, 0.10))
        ratio = np.abs(data["error_components"][name]["total_error"]) / denom
        ax.plot(freqs, ratio, lw=1.6)
        ax.set_xscale("log")
        ax.set_title(CHANNEL_LABELS[name])
        ax.set_ylabel("|error| / max(|truth|, p10)")
        ax.grid(True, which="both", alpha=0.25)
    axes[-1, 0].set_xlabel("frequency [Hz]")
    axes[-1, 1].set_xlabel("frequency [Hz]")
    fig.suptitle("Normalized error diagnostic; denominator effects can dominate near notches", y=1.01)
    fig.tight_layout()
    save_figure(fig, "channel_normalized_error_diagnostic.png")
    plt.close(fig)


def plot_gp_samples(data: dict[str, Any]) -> None:
    c: Constants = data["constants"]
    freqs = data["freqs_hz"]
    rng = np.random.default_rng(RUN_SEED + 29)
    sigma = 1.0
    cov = sqexp_cov_logfreq(freqs, sigma, c.discrepancy_corr_logfreq) + 1e-10 * np.eye(len(freqs))
    samples = rng.multivariate_normal(np.zeros(len(freqs)), cov, size=8)
    ref = freqs[len(freqs) // 2]
    corr = np.exp(-0.5 * ((np.log(freqs) - math.log(ref)) / c.discrepancy_corr_logfreq) ** 2)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for s in samples:
        axes[0].plot(freqs, s, lw=1.0, alpha=0.8)
    axes[0].set_xscale("log")
    axes[0].set_title("Zero-mean GP discrepancy samples, sigma=1")
    axes[0].set_xlabel("frequency [Hz]")
    axes[0].set_ylabel("normalized discrepancy")
    axes[0].grid(True, which="both", alpha=0.25)
    axes[1].plot(freqs, corr, lw=2)
    axes[1].axvline(ref, color="black", lw=1, ls="--", label=f"reference {ref:.1f} Hz")
    axes[1].set_xscale("log")
    axes[1].set_title("Squared-exponential covariance vs ln-frequency gap")
    axes[1].set_xlabel("frequency [Hz]")
    axes[1].set_ylabel("correlation")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    save_figure(fig, "gp_discrepancy_samples.png")
    plt.close(fig)


def plot_flight_data(data: dict[str, Any]) -> None:
    t = data["times_s"]
    f = data["flight_freqs_hz"]
    comp = data["flight_error_components"]
    psd_comp = data["response_psd_error_components"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    axes[0, 0].plot(f, data["force_psd_clean"], lw=1.6)
    axes[0, 0].set_xscale("log")
    axes[0, 0].set_yscale("log")
    axes[0, 0].set_title("Flight-like forcing PSD on m1")
    axes[0, 0].set_ylabel("N^2/Hz")
    axes[0, 0].set_xlabel("frequency [Hz]")
    axes[0, 1].plot(f, data["response_psd_clean"], label="clean response PSD", lw=1.8)
    axes[0, 1].scatter(f, data["response_psd_observed"], label="observed PSD", s=10, alpha=0.65)
    axes[0, 1].set_xscale("log")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("Tray acceleration response PSD")
    axes[0, 1].set_ylabel("g^2/Hz")
    axes[0, 1].set_xlabel("frequency [Hz]")
    axes[0, 1].legend(fontsize=8)
    axes[1, 0].plot(f, psd_comp["log_gp_discrepancy"], label="log-GP discrepancy", lw=1.3)
    axes[1, 0].plot(f, psd_comp["log_iid_sensor_noise"], label="log-iid noise", lw=0.9, alpha=0.75)
    axes[1, 0].plot(f, psd_comp["log_total_error"], label="total log error", lw=1.1)
    axes[1, 0].set_xscale("log")
    axes[1, 0].set_title("Injected response-PSD log error")
    axes[1, 0].set_ylabel("ln(observed / clean)")
    axes[1, 0].set_xlabel("frequency [Hz]")
    axes[1, 0].legend(fontsize=8)
    axes[1, 1].plot(t, data["flight_clean"] / G0_M_PER_S2, label="clean realization", lw=1.3)
    axes[1, 1].plot(t, data["flight_observed"] / G0_M_PER_S2, label="observed realization", lw=0.9, alpha=0.75)
    axes[1, 1].plot(t, comp["total_error"] / G0_M_PER_S2, label="time-domain error", lw=0.8)
    axes[1, 1].set_title("Secondary time-history realization")
    axes[1, 1].set_xlabel("time [s]")
    axes[1, 1].set_ylabel("tray accel [g]")
    axes[1, 1].legend(fontsize=8)
    for ax in axes.flat:
        ax.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    save_figure(fig, "flight_truth_vs_observed.png")
    plt.close(fig)


def posterior_mean_params(mcmc: dict[str, Any], c: Constants) -> Params:
    phys = mcmc["physical_samples"]
    return Params(
        k1=float(np.mean(phys["k1"])),
        k2=float(np.mean(phys["k2"])),
        zeta1=float(np.mean(phys["zeta1"])),
        zeta2=float(np.mean(phys["zeta2"])),
        force_amp=float(np.mean(phys["force_amp"])),
        force_fc=float(np.mean(phys["force_fc"])),
    )


def plot_posterior_fit(data: dict[str, Any], mcmc: dict[str, Any]) -> None:
    c: Constants = data["constants"]
    freqs = data["freqs_hz"]
    pmean = posterior_mean_params(mcmc, c)
    pred = frequency_channels(pmean, c, freqs)
    fig, axes = plt.subplots(4, 2, figsize=(13, 12), sharex="col")
    for row, name in enumerate(CHANNELS):
        axes[row, 0].plot(freqs, np.abs(data["clean"][name]), label="clean truth", lw=1.7)
        axes[row, 0].scatter(freqs, np.abs(data["observed"][name]), label="observed", s=8, alpha=0.55)
        axes[row, 0].plot(freqs, np.abs(pred[name]), label="posterior mean pred.", lw=1.4)
        axes[row, 0].set_xscale("log")
        axes[row, 0].set_ylabel(f"{CHANNEL_UNITS[name]}")
        axes[row, 0].set_title(CHANNEL_LABELS[name])
        resid = data["observed"][name] - pred[name]
        axes[row, 1].plot(freqs, np.abs(resid), label="|observed - posterior mean|", lw=1.2)
        axes[row, 1].plot(freqs, np.abs(data["observed"][name] - data["clean"][name]), label="|observed - clean|", lw=1.0, alpha=0.75)
        axes[row, 1].set_xscale("log")
        axes[row, 1].set_title("Residual/zoom evidence")
        axes[row, 1].set_ylabel(f"{CHANNEL_UNITS[name]}")
        for col in range(2):
            axes[row, col].grid(True, which="both", alpha=0.25)
    axes[0, 0].legend(fontsize=8)
    axes[0, 1].legend(fontsize=8)
    axes[-1, 0].set_xlabel("frequency [Hz]")
    axes[-1, 1].set_xlabel("frequency [Hz]")
    fig.tight_layout()
    save_figure(fig, "posterior_fit_and_residuals.png")
    plt.close(fig)


def plot_sampler(mcmc: dict[str, Any]) -> None:
    names = ["log k1 factor", "log k2 factor", "log zeta1", "log zeta2", "log force amp", "log force fc"]
    traces = mcmc["traces"]
    fig, axes = plt.subplots(3, 2, figsize=(12, 8), sharex=True)
    for ax, idx, name in zip(axes.flat, range(len(names)), names):
        ax.plot(traces[:, idx], lw=0.8)
        ax.set_title(name)
        ax.grid(True, alpha=0.25)
    axes[-1, 0].set_xlabel("MCMC step")
    axes[-1, 1].set_xlabel("MCMC step")
    fig.suptitle(f"Random-walk MH traces; acceptance = {mcmc['acceptance_rate']:.3f}", y=1.01)
    fig.tight_layout()
    save_figure(fig, "sampler_diagnostics.png")
    plt.close(fig)


def plot_qoi(data: dict[str, Any], mcmc: dict[str, Any]) -> None:
    c: Constants = data["constants"]
    qoi = mcmc["qoi_samples"]
    truth_qoi = 3.0 * grms_from_psd(data["flight_freqs_hz"], data["response_psd_clean"])
    sample_ids = np.linspace(0, len(mcmc["samples_transformed"]) - 1, min(35, len(mcmc["samples_transformed"]))).astype(int)
    f = data["flight_freqs_hz"]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    axes[0, 0].hist(qoi, bins=28, color="#7aa6c2", edgecolor="white")
    axes[0, 0].axvline(truth_qoi, color="black", lw=2, label="synthetic truth")
    axes[0, 0].set_xlabel("3 * GRMS tray acceleration [g]")
    axes[0, 0].set_ylabel("retained samples")
    axes[0, 0].legend(fontsize=8)
    axes[0, 0].set_title("Posterior QOI samples")
    axes[0, 1].plot(f, data["response_psd_clean"], color="black", lw=2.2, label="truth PSD")
    axes[0, 1].scatter(f, data["response_psd_observed"], s=8, alpha=0.35, label="observed PSD")
    for idx in sample_ids:
        p = unpack_params(mcmc["samples_transformed"][idx], c)
        response_psd, _ = tray_response_psd_g2_per_hz(p, c, f)
        axes[0, 1].plot(f, response_psd, color="#c65b42", alpha=0.18, lw=0.8)
    axes[0, 1].set_xscale("log")
    axes[0, 1].set_yscale("log")
    axes[0, 1].set_title("Posterior tray-response PSD samples")
    axes[0, 1].set_xlabel("frequency [Hz]")
    axes[0, 1].set_ylabel("g^2/Hz")
    axes[0, 1].legend(fontsize=8)
    peak_i = int(np.argmax(data["response_psd_clean"]))
    lo = max(0, peak_i - 14)
    hi = min(len(f), peak_i + 15)
    axes[1, 0].plot(f[lo:hi], data["response_psd_clean"][lo:hi], color="black", lw=2.2)
    axes[1, 0].scatter(f[lo:hi], data["response_psd_observed"][lo:hi], s=14, alpha=0.45)
    for idx in sample_ids:
        p = unpack_params(mcmc["samples_transformed"][idx], c)
        response_psd, _ = tray_response_psd_g2_per_hz(p, c, f)
        axes[1, 0].plot(f[lo:hi], response_psd[lo:hi], color="#c65b42", alpha=0.18, lw=0.8)
    axes[1, 0].set_xscale("log")
    axes[1, 0].set_yscale("log")
    axes[1, 0].set_title("Zoom near response-PSD peak")
    axes[1, 0].set_xlabel("frequency [Hz]")
    axes[1, 0].set_ylabel("g^2/Hz")
    pmean = posterior_mean_params(mcmc, c)
    mean_psd, _ = tray_response_psd_g2_per_hz(pmean, c, f)
    axes[1, 1].plot(f, np.log(np.maximum(mean_psd, 1e-30)) - np.log(np.maximum(data["response_psd_clean"], 1e-30)), lw=1.4)
    axes[1, 1].axhline(0.0, color="black", lw=1)
    axes[1, 1].set_xscale("log")
    axes[1, 1].set_title("Posterior-mean log-PSD residual vs clean truth")
    axes[1, 1].set_xlabel("frequency [Hz]")
    axes[1, 1].set_ylabel("ln(pred / truth)")
    for ax in axes.flat:
        ax.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    save_figure(fig, "qoi_samples.png")
    plt.close(fig)


PARAMETER_VIEWS = [
    {
        "name": "dome_hz",
        "title": "Dome natural frequency",
        "unit": "Hz",
        "nominal": lambda c: c.dome_nominal_hz,
        "truth": lambda data: truth_summary(data)["dome_true_hz"],
    },
    {
        "name": "tray_hz",
        "title": "Tray natural frequency",
        "unit": "Hz",
        "nominal": lambda c: c.tray_nominal_hz,
        "truth": lambda data: truth_summary(data)["tray_true_hz"],
    },
    {
        "name": "zeta1",
        "title": "Dome damping ratio",
        "unit": "ratio",
        "nominal": lambda c: c.dome_nominal_zeta,
        "truth": lambda data: truth_summary(data)["zeta1"],
    },
    {
        "name": "zeta2",
        "title": "Tray damping ratio",
        "unit": "ratio",
        "nominal": lambda c: c.tray_nominal_zeta,
        "truth": lambda data: truth_summary(data)["zeta2"],
    },
]


def parameter_grid(view_name: str, c: Constants) -> np.ndarray:
    if view_name == "dome_hz":
        return np.linspace(math.sqrt(0.55) * c.dome_nominal_hz, math.sqrt(1.65) * c.dome_nominal_hz, 120)
    if view_name == "tray_hz":
        return np.linspace(math.sqrt(0.55) * c.tray_nominal_hz, math.sqrt(1.65) * c.tray_nominal_hz, 120)
    return np.geomspace(0.004, 0.090, 120)


def set_parameter_in_transformed(x_base: np.ndarray, view_name: str, value: float, c: Constants) -> np.ndarray:
    x = x_base.copy()
    if view_name == "dome_hz":
        x[0] = 2.0 * math.log(value / c.dome_nominal_hz)
    elif view_name == "tray_hz":
        x[1] = 2.0 * math.log(value / c.tray_nominal_hz)
    elif view_name == "zeta1":
        x[2] = math.log(value)
    elif view_name == "zeta2":
        x[3] = math.log(value)
    else:
        raise ValueError(f"Unknown parameter view {view_name}")
    return x


def normalized_hist_curve(
    values: np.ndarray,
    grid: np.ndarray,
    bins: int = PRIOR_DENSITY_MC_BINS,
) -> tuple[np.ndarray, np.ndarray, float]:
    counts, edges = np.histogram(values, bins=bins, range=(float(grid[0]), float(grid[-1])), density=True)
    centers = 0.5 * (edges[:-1] + edges[1:])
    if np.max(counts) > 0.0:
        counts = counts / np.max(counts)
    width = float(edges[1] - edges[0])
    return centers, counts, width


def plot_prior_mc_histogram(ax: plt.Axes, values: np.ndarray, grid: np.ndarray, *, label: str) -> None:
    centers, heights, width = normalized_hist_curve(values, grid)
    ax.bar(
        centers,
        heights,
        width=width,
        color="#4f7cac",
        alpha=0.14,
        edgecolor="#4f7cac",
        linewidth=0.25,
        label=label,
        zorder=1,
    )


def normalized_kde_curve(values: np.ndarray, grid: np.ndarray) -> np.ndarray:
    vals = np.asarray(values, dtype=float)
    vals = vals[np.isfinite(vals)]
    if len(vals) < 2:
        return np.zeros_like(grid)
    std = float(np.std(vals))
    span = max(float(grid[-1] - grid[0]), 1e-12)
    bandwidth = max(1.06 * std * (len(vals) ** (-1.0 / 5.0)), span / 250.0)
    z = (grid[:, None] - vals[None, :]) / bandwidth
    density = np.exp(-0.5 * z**2).mean(axis=1) / (bandwidth * math.sqrt(2.0 * math.pi))
    if np.max(density) > 0.0:
        density = density / np.max(density)
    return density


def analytic_prior_relative_density(view_name: str, grid: np.ndarray, c: Constants) -> np.ndarray:
    if view_name == "dome_hz":
        center = c.dome_nominal_hz
        sigma = 0.09
        lower = math.sqrt(0.55) * center
        upper = math.sqrt(1.65) * center
        density = np.where(
            (grid >= lower) & (grid <= upper),
            np.exp(-0.5 * (np.log(grid / center) / sigma) ** 2) / np.maximum(grid, 1e-30),
            0.0,
        )
    elif view_name == "tray_hz":
        center = c.tray_nominal_hz
        sigma = 0.09
        lower = math.sqrt(0.55) * center
        upper = math.sqrt(1.65) * center
        density = np.where(
            (grid >= lower) & (grid <= upper),
            np.exp(-0.5 * (np.log(grid / center) / sigma) ** 2) / np.maximum(grid, 1e-30),
            0.0,
        )
    elif view_name == "zeta1":
        center = c.dome_nominal_zeta
        sigma = 0.35
        density = np.where(
            (grid >= 0.004) & (grid <= 0.090),
            np.exp(-0.5 * (np.log(grid / center) / sigma) ** 2) / np.maximum(grid, 1e-30),
            0.0,
        )
    elif view_name == "zeta2":
        center = c.tray_nominal_zeta
        sigma = 0.35
        density = np.where(
            (grid >= 0.004) & (grid <= 0.090),
            np.exp(-0.5 * (np.log(grid / center) / sigma) ** 2) / np.maximum(grid, 1e-30),
            0.0,
        )
    else:
        raise ValueError(f"Unknown parameter view {view_name}")
    if np.max(density) > 0.0:
        density = density / np.max(density)
    return density


def select_even_samples(samples: np.ndarray, n: int) -> np.ndarray:
    if len(samples) <= n:
        return samples
    idx = np.linspace(0, len(samples) - 1, n).astype(int)
    return samples[idx]


def summarize_parameter_samples(values: np.ndarray, truth: float, nominal: float, units: str) -> dict[str, float | str]:
    s = summarize(values)
    s["truth"] = float(truth)
    s["nominal"] = float(nominal)
    s["units"] = units
    s["truth_in_95_ci"] = bool(s["q025"] <= truth <= s["q975"])
    return s


def plot_bayes_parameter_update(data: dict[str, Any], mcmc: dict[str, Any]) -> dict[str, Any]:
    c: Constants = data["constants"]
    prior_x = draw_prior_transformed(PRIOR_DENSITY_MC_SAMPLES)
    prior_phys = physical_sample_table(prior_x, c)
    posterior_phys = mcmc["physical_samples"]
    log_likelihood = make_likelihood(data)
    posterior_mode_x = mcmc["samples_transformed"][int(np.argmax(mcmc["sample_logps"]))]
    prior_center_x = prior_arrays()[0]
    truth_x = param_vector(data["truth"], c)
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    parameter_summary: dict[str, Any] = {}
    likelihood_summary: dict[str, Any] = {
        "likelihood_curve_type": "one-dimensional conditional slices with all other transformed variables held at the retained posterior sample with largest log posterior",
        "log_likelihood_at_prior_center": float(log_likelihood(prior_center_x)),
        "log_likelihood_at_truth": float(log_likelihood(truth_x)),
        "log_likelihood_at_retained_posterior_mode": float(log_likelihood(posterior_mode_x)),
        "log_prior_at_prior_center": float(log_prior(prior_center_x)),
        "log_prior_at_truth": float(log_prior(truth_x)),
        "log_prior_at_retained_posterior_mode": float(log_prior(posterior_mode_x)),
    }
    for ax, view in zip(axes.flat, PARAMETER_VIEWS):
        name = view["name"]
        grid = parameter_grid(name, c)
        prior_density = analytic_prior_relative_density(name, grid, c)
        post_density = normalized_kde_curve(posterior_phys[name], grid)
        log_like = np.asarray([log_likelihood(set_parameter_in_transformed(posterior_mode_x, name, float(v), c)) for v in grid])
        like = np.exp(log_like - np.max(log_like))
        nominal = float(view["nominal"](c))
        truth = float(view["truth"](data))
        post_ci = np.quantile(posterior_phys[name], [0.025, 0.975])
        plot_prior_mc_histogram(ax, prior_phys[name], grid, label=f"MC prior histogram (n={PRIOR_DENSITY_MC_SAMPLES:,})")
        ax.plot(grid, prior_density, color="#174f82", lw=2.0, label="analytic prior density", zorder=4)
        ax.plot(grid, like, color="#6a9f58", lw=1.8, label="conditional likelihood")
        ax.plot(grid, post_density, color="#c65b42", lw=2.0, label="posterior KDE")
        ax.axvspan(post_ci[0], post_ci[1], color="#c65b42", alpha=0.16, label="posterior 95% CI")
        ax.axvline(nominal, color="#555555", ls=":", lw=1.4, label="nominal")
        ax.axvline(truth, color="black", ls="--", lw=1.4, label="synthetic truth")
        ax.set_title(view["title"])
        ax.set_xlabel(f"{view['unit']}")
        ax.set_ylabel("relative density / likelihood")
        ax.grid(True, alpha=0.25)
        parameter_summary[name] = {
            "prior": summarize_parameter_samples(prior_phys[name], truth, nominal, view["unit"]),
            "posterior": summarize_parameter_samples(posterior_phys[name], truth, nominal, view["unit"]),
            "conditional_likelihood_max_at": float(grid[int(np.argmax(log_like))]),
            "conditional_likelihood_units": view["unit"],
        }
    axes[0, 0].legend(fontsize=7)
    fig.suptitle("Bayes rule in action: prior x likelihood -> posterior", y=0.985)
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.955])
    save_figure(fig, "bayes_parameter_update.png")
    plt.close(fig)

    out = {
        "parameter_summaries": parameter_summary,
        "likelihood_summary": likelihood_summary,
        "prior_model": prior_model_summary(c),
        "likelihood_formulation": likelihood_formulation_summary(c),
        "simulation_replicates": data["simulation_replicates"],
        "statfem_noise_model": {
            "frf_generation": "observed = clean + realized GP model discrepancy + realized iid sensor noise",
            "frf_likelihood": "complex residuals use covariance K_discrepancy + diagonal sensor-noise covariance; real and imaginary parts are treated independently",
            "response_psd_generation": "observed PSD = clean PSD * exp(log-GP discrepancy + log-iid sensor noise)",
            "response_psd_likelihood": "log PSD residual uses GP discrepancy covariance plus diagonal log sensor-noise covariance",
            "kept_separate_in_generated_data": True,
            "realized_discrepancy_inferred_as_latent_field": False,
            "hyperparameters_inferred": False,
        },
        "prior_visualization": {
            "analytic_prior_density_plotted": True,
            "mc_prior_histogram_plotted": True,
            "mc_prior_histogram_samples": PRIOR_DENSITY_MC_SAMPLES,
            "mc_prior_histogram_bins": PRIOR_DENSITY_MC_BINS,
            "prior_predictive_mc_samples": PRIOR_PREDICTIVE_MC_SAMPLES,
            "prior_predictive_quantiles_smoothed_for_display": True,
            "predictive_band_smoothing_sigma_points": PREDICTIVE_BAND_SMOOTHING_SIGMA_POINTS,
            "policy": "Analytic prior density is the primary prior representation; high-sample MC histogram is shown as a labeled diagnostic.",
        },
    }
    (OUT_DIR / "bayes_update_summary.json").write_text(json.dumps(out, indent=2))
    return out


def plot_parameter_posterior_samples(data: dict[str, Any], mcmc: dict[str, Any], bayes: dict[str, Any]) -> None:
    c: Constants = data["constants"]
    posterior_phys = mcmc["physical_samples"]
    prior_phys = physical_sample_table(draw_prior_transformed(PRIOR_DENSITY_MC_SAMPLES, seed=RUN_SEED + 202), c)
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    for ax, view in zip(axes.flat, PARAMETER_VIEWS):
        name = view["name"]
        grid = parameter_grid(name, c)
        prior_density = analytic_prior_relative_density(name, grid, c)
        post_density = normalized_kde_curve(posterior_phys[name], grid)
        summary = bayes["parameter_summaries"][name]["posterior"]
        plot_prior_mc_histogram(ax, prior_phys[name], grid, label=f"MC prior histogram (n={PRIOR_DENSITY_MC_SAMPLES:,})")
        ax.plot(grid, prior_density, color="#174f82", lw=2.0, label="analytic prior density", zorder=4)
        ax.fill_between(grid, 0.0, post_density, color="#c65b42", alpha=0.35, label="posterior KDE")
        ax.axvspan(summary["q025"], summary["q975"], color="#c65b42", alpha=0.18, label="posterior 95% CI")
        ax.axvline(summary["truth"], color="black", ls="--", lw=1.4, label="truth")
        ax.axvline(summary["nominal"], color="#555555", ls=":", lw=1.2, label="nominal")
        ax.set_title(
            f"{view['title']}: median {summary['median']:.4g}, 95% CI [{summary['q025']:.4g}, {summary['q975']:.4g}]"
        )
        ax.set_xlabel(view["unit"])
        ax.set_ylabel("relative density")
        ax.grid(True, alpha=0.25)
    axes[0, 0].legend(fontsize=7)
    fig.tight_layout()
    save_figure(fig, "parameter_posterior_samples.png")
    plt.close(fig)


def smooth_series_by_index(values: np.ndarray, sigma_points: float, *, positive_log: bool = False) -> np.ndarray:
    if sigma_points <= 0.0 or len(values) < 5:
        return values.copy()
    half_width = max(2, int(math.ceil(4.0 * sigma_points)))
    offsets = np.arange(-half_width, half_width + 1, dtype=float)
    kernel = np.exp(-0.5 * (offsets / sigma_points) ** 2)
    kernel = kernel / np.sum(kernel)
    source = np.log(np.maximum(values, 1e-300)) if positive_log else values
    padded = np.pad(source, (half_width, half_width), mode="edge")
    smoothed = np.convolve(padded, kernel, mode="valid")
    return np.exp(smoothed) if positive_log else smoothed


def predictive_band(
    curves: np.ndarray,
    *,
    smooth: bool = False,
    yscale: str = "linear",
) -> dict[str, np.ndarray]:
    band = {
        "q05": np.quantile(curves, 0.05, axis=0),
        "median": np.quantile(curves, 0.50, axis=0),
        "q95": np.quantile(curves, 0.95, axis=0),
    }
    if smooth:
        use_log_y = yscale == "log"
        for key in ["q05", "median", "q95"]:
            band[key] = smooth_series_by_index(
                band[key],
                PREDICTIVE_BAND_SMOOTHING_SIGMA_POINTS,
                positive_log=use_log_y,
            )
        band["q05"] = np.minimum(band["q05"], band["median"])
        band["q95"] = np.maximum(band["q95"], band["median"])
    return band


def plot_prior_predictive_vs_data(data: dict[str, Any], mcmc: dict[str, Any]) -> None:
    c: Constants = data["constants"]
    freqs = data["freqs_hz"]
    flight_freqs = data["flight_freqs_hz"]
    prior_x = draw_prior_transformed(PRIOR_PREDICTIVE_MC_SAMPLES, seed=RUN_SEED + 303)
    posterior_x = select_even_samples(mcmc["samples_transformed"], 120)

    def channel_curves(samples: np.ndarray, channel: str) -> np.ndarray:
        return np.asarray([np.abs(frequency_channels(unpack_params(x, c), c, freqs)[channel]) for x in samples])

    def response_psd_curves(samples: np.ndarray) -> np.ndarray:
        return np.asarray([tray_response_psd_g2_per_hz(unpack_params(x, c), c, flight_freqs)[0] for x in samples])

    def force_psd_curves(samples: np.ndarray) -> np.ndarray:
        out = []
        for x in samples:
            p = unpack_params(x, c)
            out.append(force_psd_n2_per_hz(flight_freqs, p.force_amp, p.force_fc, c.flight_force_bandwidth_logfreq))
        return np.asarray(out)

    panels = [
        {
            "title": "Base-driven standalone tray data (Ch4)",
            "x": freqs,
            "prior": channel_curves(prior_x, "ch4_standalone_tray_accel_transmissibility"),
            "posterior": channel_curves(posterior_x, "ch4_standalone_tray_accel_transmissibility"),
            "observed": np.abs(data["observed"]["ch4_standalone_tray_accel_transmissibility"]),
            "truth": np.abs(data["clean"]["ch4_standalone_tray_accel_transmissibility"]),
            "ylabel": "|a_tray / a_base|",
            "yscale": "linear",
        },
        {
            "title": "Coupled tray drive-point data (Ch3)",
            "x": freqs,
            "prior": channel_curves(prior_x, "ch3_coupled_tray_reciprocal_inertance"),
            "posterior": channel_curves(posterior_x, "ch3_coupled_tray_reciprocal_inertance"),
            "observed": np.abs(data["observed"]["ch3_coupled_tray_reciprocal_inertance"]),
            "truth": np.abs(data["clean"]["ch3_coupled_tray_reciprocal_inertance"]),
            "ylabel": "|F2 / a2| [kg]",
            "yscale": "linear",
        },
        {
            "title": "Flight-like tray response PSD data",
            "x": flight_freqs,
            "prior": response_psd_curves(prior_x),
            "posterior": response_psd_curves(posterior_x),
            "observed": data["response_psd_observed"],
            "truth": data["response_psd_clean"],
            "ylabel": "g^2/Hz",
            "yscale": "log",
        },
        {
            "title": "Latent unknown force PSD (not directly observed)",
            "x": flight_freqs,
            "prior": force_psd_curves(prior_x),
            "posterior": force_psd_curves(posterior_x),
            "observed": None,
            "truth": data["force_psd_clean"],
            "ylabel": "N^2/Hz",
            "yscale": "log",
        },
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    for ax, panel in zip(axes.flat, panels):
        pb = predictive_band(panel["prior"], smooth=True, yscale=panel["yscale"])
        qb = predictive_band(panel["posterior"], smooth=True, yscale=panel["yscale"])
        ax.fill_between(panel["x"], pb["q05"], pb["q95"], color="#4f7cac", alpha=0.18, label="prior 5-95% (MC smoothed)")
        ax.plot(panel["x"], pb["median"], color="#4f7cac", lw=1.5, label="prior median (MC smoothed)")
        ax.fill_between(panel["x"], qb["q05"], qb["q95"], color="#c65b42", alpha=0.20, label="posterior 5-95% (MC smoothed)")
        ax.plot(panel["x"], qb["median"], color="#c65b42", lw=1.5, label="posterior median (MC smoothed)")
        ax.plot(panel["x"], panel["truth"], color="black", lw=1.4, label="synthetic truth")
        if panel["observed"] is not None:
            ax.scatter(panel["x"], panel["observed"], s=9, color="#222222", alpha=0.45, label="observed data")
        ax.set_xscale("log")
        ax.set_yscale(panel["yscale"])
        ax.set_title(panel["title"])
        ax.set_xlabel("frequency [Hz]")
        ax.set_ylabel(panel["ylabel"])
        ax.grid(True, which="both", alpha=0.25)
    axes[0, 0].legend(fontsize=7)
    fig.suptitle(f"Prior/posterior predictive spectra against data; prior MC n={PRIOR_PREDICTIVE_MC_SAMPLES}", y=0.985)
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.955])
    save_figure(fig, "prior_predictive_vs_data.png")
    plt.close(fig)


def plot_posterior_predictive_spectra(data: dict[str, Any], mcmc: dict[str, Any]) -> None:
    c: Constants = data["constants"]
    freqs = data["freqs_hz"]
    flight_freqs = data["flight_freqs_hz"]
    samples = select_even_samples(mcmc["samples_transformed"], 160)
    panels = [
        ("Ch1 dome-only F1/a1", freqs, "kg", "linear", np.abs(data["observed"]["ch1_dome_only_reciprocal_inertance"]), np.abs(data["clean"]["ch1_dome_only_reciprocal_inertance"]), lambda p: np.abs(frequency_channels(p, c, freqs)["ch1_dome_only_reciprocal_inertance"])),
        ("Ch2 coupled primary F1/a1", freqs, "kg", "linear", np.abs(data["observed"]["ch2_coupled_primary_reciprocal_inertance"]), np.abs(data["clean"]["ch2_coupled_primary_reciprocal_inertance"]), lambda p: np.abs(frequency_channels(p, c, freqs)["ch2_coupled_primary_reciprocal_inertance"])),
        ("Ch3 coupled tray F2/a2", freqs, "kg", "linear", np.abs(data["observed"]["ch3_coupled_tray_reciprocal_inertance"]), np.abs(data["clean"]["ch3_coupled_tray_reciprocal_inertance"]), lambda p: np.abs(frequency_channels(p, c, freqs)["ch3_coupled_tray_reciprocal_inertance"])),
        ("Flight-like tray response PSD", flight_freqs, "g^2/Hz", "log", data["response_psd_observed"], data["response_psd_clean"], lambda p: tray_response_psd_g2_per_hz(p, c, flight_freqs)[0]),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    for ax, (title, xvals, unit, yscale, observed, truth, fn) in zip(axes.flat, panels):
        curves = np.asarray([fn(unpack_params(x, c)) for x in samples])
        band = predictive_band(curves)
        ax.fill_between(xvals, band["q05"], band["q95"], color="#c65b42", alpha=0.22, label="posterior 5-95%")
        ax.plot(xvals, band["median"], color="#c65b42", lw=1.5, label="posterior median")
        ax.plot(xvals, truth, color="black", lw=1.4, label="synthetic truth")
        ax.scatter(xvals, observed, s=8, color="#222222", alpha=0.42, label="observed")
        ax.set_xscale("log")
        ax.set_yscale(yscale)
        ax.set_title(title)
        ax.set_xlabel("frequency [Hz]")
        ax.set_ylabel(unit)
        ax.grid(True, which="both", alpha=0.25)
    axes[0, 0].legend(fontsize=7)
    fig.suptitle("Posterior predictive distribution, not a single posterior spectrum", y=0.985)
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.955])
    save_figure(fig, "posterior_predictive_spectra.png")
    plt.close(fig)


def summarize_posterior_parameters(mcmc: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    c: Constants = data["constants"]
    phys = mcmc["physical_samples"]
    out = {}
    for view in PARAMETER_VIEWS:
        name = view["name"]
        out[name] = summarize_parameter_samples(
            phys[name],
            float(view["truth"](data)),
            float(view["nominal"](c)),
            view["unit"],
        )
    return out


def qoi_summary_from_samples(samples: np.ndarray, data: dict[str, Any]) -> dict[str, Any]:
    q = summarize(samples)
    q["truth"] = truth_summary(data)["qoi_truth_3grms_tray_accel_g"]
    q["units"] = "g"
    q["definition"] = "3 * GRMS of tray acceleration response PSD"
    q["mean_bias"] = q["mean"] - q["truth"]
    q["fraction_above_truth"] = float(np.mean(samples > q["truth"]))
    return q


def save_peak_feature_likelihood_comparison(
    data: dict[str, Any],
    full_mcmc: dict[str, Any],
    feature_mcmc: dict[str, Any],
) -> dict[str, Any]:
    observed_features = extract_peak_feature_vector(data, observed=True)
    truth_features = extract_peak_feature_vector(data, p=data["truth"], observed=False)
    parameter_comparison = {
        "full_curve": summarize_posterior_parameters(full_mcmc, data),
        "peak_feature": summarize_posterior_parameters(feature_mcmc, data),
    }
    qoi_comparison = {
        "full_curve": qoi_summary_from_samples(full_mcmc["qoi_samples"], data),
        "peak_feature": qoi_summary_from_samples(feature_mcmc["qoi_samples"], data),
    }
    interval_width_ratios = {}
    for view in PARAMETER_VIEWS:
        name = view["name"]
        full = parameter_comparison["full_curve"][name]
        feat = parameter_comparison["peak_feature"][name]
        full_width = max(float(full["q975"]) - float(full["q025"]), 1e-30)
        feat_width = float(feat["q975"]) - float(feat["q025"])
        interval_width_ratios[name] = float(feat_width / full_width)
    qoi_width_full = max(qoi_comparison["full_curve"]["q975"] - qoi_comparison["full_curve"]["q025"], 1e-30)
    qoi_width_feature = qoi_comparison["peak_feature"]["q975"] - qoi_comparison["peak_feature"]["q025"]
    out = {
        "comparison_label": "Whole FRF/PSD likelihood versus peak/notch feature likelihood",
        "feature_likelihood_assumptions": feature_likelihood_assumptions(),
        "observed_features": observed_features,
        "truth_features": truth_features,
        "parameter_comparison": parameter_comparison,
        "qoi_comparison": qoi_comparison,
        "interval_width_ratio_peak_feature_over_full_curve": interval_width_ratios,
        "qoi_95_width_ratio_peak_feature_over_full_curve": float(qoi_width_feature / qoi_width_full),
        "sampler": {
            "full_curve_acceptance_rate": float(full_mcmc["acceptance_rate"]),
            "peak_feature_acceptance_rate": float(feature_mcmc["acceptance_rate"]),
            "full_curve_retained_samples": int(len(full_mcmc["samples_transformed"])),
            "peak_feature_retained_samples": int(len(feature_mcmc["samples_transformed"])),
        },
        "interpretation_warning": "The peak-feature likelihood is intentionally lossy and uses independent feature residuals. It is a comparison artifact, not a recommended replacement for the whole-curve likelihood.",
    }
    (OUT_DIR / "peak_feature_likelihood_summary.json").write_text(json.dumps(out, indent=2))
    return out


def plot_peak_feature_likelihood_comparison(
    data: dict[str, Any],
    full_mcmc: dict[str, Any],
    feature_mcmc: dict[str, Any],
    comp: dict[str, Any],
) -> None:
    c: Constants = data["constants"]
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.0))
    colors = {"full_curve": "#4f7cac", "peak_feature": "#c65b42"}

    def interval_panel(ax: plt.Axes, names: list[str], title: str, xlabel: str) -> None:
        y_ticks = []
        y_labels = []
        for i, name in enumerate(names):
            y_base = len(names) - 1 - i
            y_ticks.append(y_base)
            y_labels.append(next(v["title"] for v in PARAMETER_VIEWS if v["name"] == name))
            for offset, key in [(0.10, "full_curve"), (-0.10, "peak_feature")]:
                s = comp["parameter_comparison"][key][name]
                y = y_base + offset
                ax.plot([s["q025"], s["q975"]], [y, y], color=colors[key], lw=4, solid_capstyle="round")
                ax.scatter([s["median"]], [y], color=colors[key], s=38, zorder=3, label=key.replace("_", " ") if i == 0 else None)
            truth = next(v["truth"](data) for v in PARAMETER_VIEWS if v["name"] == name)
            ax.scatter([truth], [y_base], color="black", marker="x", s=60, zorder=4, label="truth" if i == 0 else None)
        ax.set_yticks(y_ticks, y_labels)
        ax.set_xlabel(xlabel)
        ax.set_title(title)
        ax.grid(True, axis="x", alpha=0.25)
        ax.legend(fontsize=8)

    interval_panel(axes[0, 0], ["dome_hz", "tray_hz"], "Natural-frequency posterior intervals", "Hz")
    interval_panel(axes[0, 1], ["zeta1", "zeta2"], "Damping-ratio posterior intervals", "ratio")

    truth_qoi = truth_summary(data)["qoi_truth_3grms_tray_accel_g"]
    axes[1, 0].hist(full_mcmc["qoi_samples"], bins=28, density=True, alpha=0.45, color=colors["full_curve"], label="full FRF/PSD")
    axes[1, 0].hist(feature_mcmc["qoi_samples"], bins=28, density=True, alpha=0.45, color=colors["peak_feature"], label="peak-feature")
    axes[1, 0].axvline(truth_qoi, color="black", lw=2, label="truth")
    axes[1, 0].set_title("QOI posterior samples")
    axes[1, 0].set_xlabel("3*GRMS tray response [g]")
    axes[1, 0].set_ylabel("density")
    axes[1, 0].legend(fontsize=8)
    axes[1, 0].grid(True, alpha=0.25)

    f = data["flight_freqs_hz"]

    def response_band(samples: np.ndarray) -> dict[str, np.ndarray]:
        selected = select_even_samples(samples, 120)
        curves = []
        for x in selected:
            p = unpack_params(x, c)
            response_psd, _ = tray_response_psd_g2_per_hz(p, c, f)
            curves.append(response_psd)
        return predictive_band(np.asarray(curves))

    full_band = response_band(full_mcmc["samples_transformed"])
    feature_band = response_band(feature_mcmc["samples_transformed"])
    ax = axes[1, 1]
    ax.plot(f, data["response_psd_clean"], color="black", lw=1.8, label="truth PSD")
    ax.scatter(f, data["response_psd_observed"], s=8, alpha=0.22, color="#555555", label="observed PSD")
    ax.fill_between(f, full_band["q05"], full_band["q95"], color=colors["full_curve"], alpha=0.22, label="full 5-95%")
    ax.plot(f, full_band["median"], color=colors["full_curve"], lw=1.5, label="full median")
    ax.fill_between(f, feature_band["q05"], feature_band["q95"], color=colors["peak_feature"], alpha=0.20, label="feature 5-95%")
    ax.plot(f, feature_band["median"], color=colors["peak_feature"], lw=1.5, label="feature median")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title("Flight-like response PSD posterior predictive")
    ax.set_xlabel("frequency [Hz]")
    ax.set_ylabel("g^2/Hz")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(fontsize=7)

    width_ratio = comp["qoi_95_width_ratio_peak_feature_over_full_curve"]
    fig.suptitle(
        f"Whole-curve likelihood vs peak-feature likelihood; QOI 95% width ratio = {width_ratio:.2f}",
        y=0.985,
    )
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.955])
    save_figure(fig, "full_vs_peak_feature_likelihood_comparison.png")
    plt.close(fig)


FEATURE_LABELS = {
    "ch1_dome_notch": "Ch1 dome notch",
    "ch2_primary_notch": "Ch2 primary notch",
    "ch3_tray_notch": "Ch3 tray notch",
    "ch4_tray_peak": "Ch4 tray peak",
    "ch5_response_psd_peak": "Ch5 PSD peak",
}


def perturb_for_log_sensitivity(x_base: np.ndarray, variable: str, delta: float) -> np.ndarray:
    x = x_base.copy()
    if variable == "dome_hz":
        # x[0] is log stiffness ratio, so a log-frequency perturbation is doubled.
        x[0] += 2.0 * delta
    elif variable == "tray_hz":
        x[1] += 2.0 * delta
    elif variable == "zeta1":
        x[2] += delta
    elif variable == "zeta2":
        x[3] += delta
    elif variable == "force_fc":
        x[5] += delta
    else:
        raise ValueError(f"Unknown sensitivity variable {variable}")
    return x


def feature_sigma_for_source(source: str, assumptions: dict[str, float | str]) -> tuple[float, float]:
    if source == "PSD":
        return (
            float(assumptions["psd_log_frequency_sigma"]),
            float(assumptions["psd_log_amplitude_sigma"]),
        )
    return (
        float(assumptions["frf_log_frequency_sigma"]),
        float(assumptions["frf_log_amplitude_sigma"]),
    )


def save_peak_feature_mapping_benchmark(data: dict[str, Any]) -> dict[str, Any]:
    c: Constants = data["constants"]
    p_truth: Params = data["truth"]
    x_truth = param_vector(p_truth, c)
    observed = extract_peak_feature_vector(data, observed=True)
    clean = extract_peak_feature_vector(data, p=p_truth, observed=False)
    assumptions = feature_likelihood_assumptions()
    variables = ["dome_hz", "tray_hz", "zeta1", "zeta2", "force_fc"]
    variable_labels = {
        "dome_hz": "dome freq",
        "tray_hz": "tray freq",
        "zeta1": "dome zeta",
        "zeta2": "tray zeta",
        "force_fc": "force center",
    }
    delta = 0.02

    feature_rows: dict[str, dict[str, Any]] = {}
    frequency_sensitivity = np.zeros((len(FEATURE_SPECS), len(variables)))
    amplitude_sensitivity = np.zeros_like(frequency_sensitivity)
    for i, (feature_name, _channel_name, _kind, source) in enumerate(FEATURE_SPECS):
        sigma_f, sigma_a = feature_sigma_for_source(source, assumptions)
        obs = observed[feature_name]
        base = clean[feature_name]
        freq_z = math.log(float(obs["frequency_hz"]) / float(base["frequency_hz"])) / sigma_f
        amp_z = (float(obs["log_amplitude"]) - float(base["log_amplitude"])) / sigma_a
        sensitivities = {}
        for j, variable in enumerate(variables):
            plus = unpack_params(perturb_for_log_sensitivity(x_truth, variable, delta), c)
            minus = unpack_params(perturb_for_log_sensitivity(x_truth, variable, -delta), c)
            f_plus = extract_peak_feature_vector(data, p=plus, observed=False)[feature_name]
            f_minus = extract_peak_feature_vector(data, p=minus, observed=False)[feature_name]
            s_freq = (
                math.log(float(f_plus["frequency_hz"]))
                - math.log(float(f_minus["frequency_hz"]))
            ) / (2.0 * delta)
            s_amp = (
                float(f_plus["log_amplitude"])
                - float(f_minus["log_amplitude"])
            ) / (2.0 * delta)
            frequency_sensitivity[i, j] = s_freq
            amplitude_sensitivity[i, j] = s_amp
            sensitivities[variable] = {
                "dlog_feature_frequency_dlog_variable": float(s_freq),
                "dlog_feature_amplitude_dlog_variable": float(s_amp),
            }
        structural_mix = (
            abs(sensitivities["dome_hz"]["dlog_feature_frequency_dlog_variable"]) > 0.25
            and abs(sensitivities["tray_hz"]["dlog_feature_frequency_dlog_variable"]) > 0.25
        )
        force_confounded = abs(sensitivities["force_fc"]["dlog_feature_amplitude_dlog_variable"]) > 1.0
        shifted_by_error = abs(freq_z) > 0.75 or abs(amp_z) > 0.75
        if feature_name in {"ch1_dome_notch", "ch4_tray_peak"} and not structural_mix:
            interpretation = "direct structural feature"
        elif force_confounded:
            interpretation = "forcing/response-shape confounded feature"
        elif structural_mix:
            interpretation = "coupled structural feature"
        else:
            interpretation = "weak or context-dependent feature"
        feature_rows[feature_name] = {
            "label": FEATURE_LABELS[feature_name],
            "source": source,
            "clean_feature_frequency_hz": float(base["frequency_hz"]),
            "observed_feature_frequency_hz": float(obs["frequency_hz"]),
            "frequency_observation_z_score_vs_clean_feature": float(freq_z),
            "amplitude_observation_z_score_vs_clean_feature": float(amp_z),
            "sensitivities": sensitivities,
            "structural_frequency_mix": bool(structural_mix),
            "force_confounded": bool(force_confounded),
            "observed_feature_shifted_by_error": bool(shifted_by_error),
            "interpretation": interpretation,
        }

    dome_grid = parameter_grid("dome_hz", c)
    tray_grid = parameter_grid("tray_hz", c)
    ch1_pred = []
    ch1_like = []
    ch4_pred = []
    ch4_like = []
    for value in dome_grid:
        p = unpack_params(set_parameter_in_transformed(x_truth, "dome_hz", float(value), c), c)
        pred = extract_peak_feature_vector(data, p=p, observed=False)["ch1_dome_notch"]
        ch1_pred.append(float(pred["frequency_hz"]))
        sigma_f, _ = feature_sigma_for_source("FRF", assumptions)
        ch1_like.append(-0.5 * (math.log(float(observed["ch1_dome_notch"]["frequency_hz"]) / float(pred["frequency_hz"])) / sigma_f) ** 2)
    for value in tray_grid:
        p = unpack_params(set_parameter_in_transformed(x_truth, "tray_hz", float(value), c), c)
        pred = extract_peak_feature_vector(data, p=p, observed=False)["ch4_tray_peak"]
        ch4_pred.append(float(pred["frequency_hz"]))
        sigma_f, _ = feature_sigma_for_source("FRF", assumptions)
        ch4_like.append(-0.5 * (math.log(float(observed["ch4_tray_peak"]["frequency_hz"]) / float(pred["frequency_hz"])) / sigma_f) ** 2)
    ch1_like_arr = np.exp(np.asarray(ch1_like) - np.max(ch1_like))
    ch4_like_arr = np.exp(np.asarray(ch4_like) - np.max(ch4_like))

    summary = {
        "description": "Benchmark of feature likelihood mapping: observed peaks/notches are compared with predicted transfer-function feature locations, not directly with natural frequencies.",
        "feature_likelihood_assumptions": assumptions,
        "feature_rows": feature_rows,
        "direct_feature_maps": {
            "ch1_dome_notch": {
                "x_parameter": "dome_hz",
                "candidate_dome_hz": dome_grid.tolist(),
                "predicted_notch_hz": ch1_pred,
                "relative_frequency_likelihood": ch1_like_arr.tolist(),
            },
            "ch4_tray_peak": {
                "x_parameter": "tray_hz",
                "candidate_tray_hz": tray_grid.tolist(),
                "predicted_peak_hz": ch4_pred,
                "relative_frequency_likelihood": ch4_like_arr.tolist(),
            },
        },
        "sensitivity_variables": variables,
        "sensitivity_variable_labels": [variable_labels[v] for v in variables],
        "feature_frequency_sensitivity_matrix": frequency_sensitivity.tolist(),
        "feature_amplitude_sensitivity_matrix": amplitude_sensitivity.tolist(),
        "reference_note": "This is the same concern as MAC-style likelihoods: correlated or redundant data should not be counted as independent information without an adequate covariance or feature model.",
    }
    (OUT_DIR / "peak_feature_mapping_benchmark.json").write_text(json.dumps(summary, indent=2))
    return summary


def plot_peak_feature_mapping_benchmark(data: dict[str, Any], benchmark: dict[str, Any]) -> None:
    ts = truth_summary(data)
    observed = extract_peak_feature_vector(data, observed=True)
    clean = extract_peak_feature_vector(data, p=data["truth"], observed=False)
    ch1 = benchmark["direct_feature_maps"]["ch1_dome_notch"]
    ch4 = benchmark["direct_feature_maps"]["ch4_tray_peak"]

    fig, axes = plt.subplots(2, 2, figsize=(12.5, 8.0))
    ax = axes[0, 0]
    dome_grid = np.asarray(ch1["candidate_dome_hz"])
    ch1_pred = np.asarray(ch1["predicted_notch_hz"])
    ax.plot(dome_grid, ch1_pred, color="#4f7cac", lw=2.0, label="predicted notch")
    ax.plot(dome_grid, dome_grid, color="#777777", ls=":", lw=1.2, label="one-to-one")
    ax.axhline(float(observed["ch1_dome_notch"]["frequency_hz"]), color="#c65b42", ls="--", lw=1.5, label="observed notch")
    ax.scatter([ts["dome_true_hz"]], [float(clean["ch1_dome_notch"]["frequency_hz"])], color="black", zorder=3, label="clean truth feature")
    ax.set_title("Ch1 dome-only reciprocal-inertance notch")
    ax.set_xlabel("candidate dome natural frequency [Hz]")
    ax.set_ylabel("predicted notch frequency [Hz]")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)

    ax = axes[0, 1]
    tray_grid = np.asarray(ch4["candidate_tray_hz"])
    ch4_pred = np.asarray(ch4["predicted_peak_hz"])
    ax.plot(tray_grid, ch4_pred, color="#4f7cac", lw=2.0, label="predicted peak")
    ax.plot(tray_grid, tray_grid, color="#777777", ls=":", lw=1.2, label="one-to-one")
    ax.axhline(float(observed["ch4_tray_peak"]["frequency_hz"]), color="#c65b42", ls="--", lw=1.5, label="observed peak")
    ax.scatter([ts["tray_true_hz"]], [float(clean["ch4_tray_peak"]["frequency_hz"])], color="black", zorder=3, label="clean truth feature")
    ax.set_title("Ch4 standalone tray transmissibility peak")
    ax.set_xlabel("candidate tray natural frequency [Hz]")
    ax.set_ylabel("predicted peak frequency [Hz]")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)

    ax = axes[1, 0]
    ax.plot(dome_grid, np.asarray(ch1["relative_frequency_likelihood"]), color="#c65b42", lw=2.0)
    ax.axvline(ts["dome_true_hz"], color="black", ls="--", lw=1.4, label="truth")
    ax.set_title("Ch1 frequency-feature likelihood slice")
    ax.set_xlabel("candidate dome natural frequency [Hz]")
    ax.set_ylabel("relative likelihood")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    ax.plot(tray_grid, np.asarray(ch4["relative_frequency_likelihood"]), color="#c65b42", lw=2.0)
    ax.axvline(ts["tray_true_hz"], color="black", ls="--", lw=1.4, label="truth")
    ax.set_title("Ch4 frequency-feature likelihood slice")
    ax.set_xlabel("candidate tray natural frequency [Hz]")
    ax.set_ylabel("relative likelihood")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)

    fig.suptitle("Feature likelihood maps observed transfer-function features to predicted features")
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.95])
    save_figure(fig, "peak_feature_mapping_benchmark.png")
    plt.close(fig)


def plot_peak_feature_sensitivity_matrix(benchmark: dict[str, Any]) -> None:
    freq_sens = np.asarray(benchmark["feature_frequency_sensitivity_matrix"], dtype=float)
    amp_sens = np.asarray(benchmark["feature_amplitude_sensitivity_matrix"], dtype=float)
    feature_labels = [FEATURE_LABELS[name] for name, *_ in FEATURE_SPECS]
    variable_labels = benchmark["sensitivity_variable_labels"]

    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0))
    for ax, values, title in [
        (axes[0], freq_sens, "feature-frequency sensitivity"),
        (axes[1], amp_sens, "feature-amplitude sensitivity"),
    ]:
        vmax = max(1.0, float(np.nanmax(np.abs(values))))
        im = ax.imshow(values, cmap="coolwarm", vmin=-vmax, vmax=vmax, aspect="auto")
        ax.set_xticks(range(len(variable_labels)), variable_labels, rotation=30, ha="right")
        ax.set_yticks(range(len(feature_labels)), feature_labels)
        ax.set_title(title)
        for i in range(values.shape[0]):
            for j in range(values.shape[1]):
                val = values[i, j]
                color = "white" if abs(val) > 0.55 * vmax else "black"
                ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8, color=color)
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)
        cbar.set_label("log-log slope")
    fig.suptitle("Peak/notch feature sensitivity benchmark at synthetic truth")
    fig.tight_layout(rect=[0.0, 0.0, 1.0, 0.93])
    save_figure(fig, "peak_feature_sensitivity_matrix.png", min_width_px=1200, min_height_px=520)
    plt.close(fig)


def run_sensitivity(data: dict[str, Any], mcmc: dict[str, Any]) -> dict[str, Any]:
    base_samples = mcmc["samples_transformed"]
    scenarios = []
    truth_qoi = 3.0 * grms_from_psd(data["flight_freqs_hz"], data["response_psd_clean"])
    qoi_scenarios = [
        ("baseline_3grms", 1.0, None, "three_grms", "QOI recomputed from retained posterior samples"),
        ("damping_0p75_3grms", 0.75, None, "three_grms", "QOI recomputed from retained posterior samples"),
        ("damping_1p25_3grms", 1.25, None, "three_grms", "QOI recomputed from retained posterior samples"),
        ("force_bandwidth_narrow_3grms", 1.0, 0.220, "three_grms", "forcing model sensitivity"),
        ("force_bandwidth_wide_3grms", 1.0, 0.480, "three_grms", "forcing model sensitivity"),
        ("baseline_grms_qoi", 1.0, None, "grms", "QOI definition sensitivity"),
    ]
    for name, dscale, bw, metric, label in qoi_scenarios:
        vals = compute_qoi_samples(
            base_samples, data, damping_scale=dscale, bandwidth_logfreq=bw, metric=metric, max_samples=260
        )
        summary = summarize(vals)
        summary.update(
            {
                "name": name,
                "type": label,
                "metric": metric,
                "damping_scale": dscale,
                "force_bandwidth_logfreq": bw if bw is not None else data["constants"].flight_force_bandwidth_logfreq,
                "mean_ratio_to_truth": float(np.mean(vals) / truth_qoi) if metric == "three_grms" else None,
            }
        )
        scenarios.append(summary)
    baseline_mean = next(s["mean"] for s in scenarios if s["name"] == "baseline_3grms")
    for s in scenarios:
        s["mean_ratio_to_baseline_3grms"] = float(s["mean"] / baseline_mean) if s["metric"] == "three_grms" else None

    synthetic_error = []
    clean = data["clean"]
    c: Constants = data["constants"]
    for name, noise_mult, disc_mult in [
        ("baseline_error_model", 1.0, 1.0),
        ("observation_noise_x2", 2.0, 1.0),
        ("discrepancy_scale_x2", 1.0, 2.0),
        ("observation_noise_half", 0.5, 1.0),
        ("discrepancy_scale_half", 1.0, 0.5),
    ]:
        ch_values = {}
        for ch, y in clean.items():
            scale = max(float(np.median(np.abs(y))), 1e-8)
            local = local_error_scale(y, 1.0, c.discrepancy_floor_rel)
            expected_rms = float(np.median(np.sqrt((noise_mult * c.obs_noise_rel * local) ** 2 + (disc_mult * c.discrepancy_rel * local) ** 2)))
            ch_values[ch] = {
                "expected_rms_absolute_error": expected_rms,
                "expected_rms_over_median_truth": expected_rms / scale,
            }
        synthetic_error.append(
            {
                "name": name,
                "type": "synthetic-data sensitivity",
                "noise_multiplier": noise_mult,
                "discrepancy_multiplier": disc_mult,
                "channels": ch_values,
            }
        )
    out = {
        "truth_qoi_3grms_tray_accel_g": truth_qoi,
        "decision_threshold": None,
        "qoi_scenarios": scenarios,
        "synthetic_error_scenarios": synthetic_error,
        "limitation": "Posterior samples are not refit for each scenario; QOI scenarios are conditional predictive sensitivities, not full posterior sensitivity refits.",
    }
    (OUT_DIR / "sensitivity_summary.json").write_text(json.dumps(out, indent=2))
    return out


def plot_sensitivity(sens: dict[str, Any]) -> None:
    qoi = sens["qoi_scenarios"]
    peak = [s for s in qoi if s["metric"] == "three_grms"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
    labels = [s["name"].replace("_", "\n") for s in peak]
    means = [s["mean"] for s in peak]
    lo = [s["mean"] - s["q05"] for s in peak]
    hi = [s["q95"] - s["mean"] for s in peak]
    axes[0].bar(labels, means, yerr=[lo, hi], color="#7aa6c2", capsize=4)
    axes[0].axhline(sens["truth_qoi_3grms_tray_accel_g"], color="black", lw=1.4, label="truth 3*GRMS")
    axes[0].set_ylabel("3 * GRMS tray accel [g]")
    axes[0].set_title("QOI sensitivity using same posterior samples")
    axes[0].tick_params(axis="x", labelrotation=35)
    axes[0].legend(fontsize=8)
    percent_change = [(s["mean_ratio_to_baseline_3grms"] - 1.0) * 100.0 for s in peak]
    axes[1].bar(labels, percent_change, color="#c65b42")
    axes[1].axhline(0.0, color="black", lw=1)
    axes[1].set_ylabel("mean QOI change from baseline [%]")
    axes[1].set_title("Fragility to damping/forcing assumptions")
    axes[1].tick_params(axis="x", labelrotation=35)
    fig.tight_layout()
    save_figure(fig, "sensitivity_qoi.png")
    plt.close(fig)

    synth = sens["synthetic_error_scenarios"]
    ch = "ch2_coupled_primary_reciprocal_inertance"
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(
        [s["name"].replace("_", "\n") for s in synth],
        [s["channels"][ch]["expected_rms_over_median_truth"] for s in synth],
        color="#6a9f58",
    )
    ax.set_ylabel("expected RMS error / median |truth|")
    ax.set_title("Synthetic-data sensitivity example: Ch2 error assumptions")
    ax.tick_params(axis="x", labelrotation=25)
    fig.tight_layout()
    save_figure(fig, "sensitivity_synthetic_error.png")
    plt.close(fig)


def reference_comparison(data: dict[str, Any]) -> dict[str, Any]:
    freqs = data["freqs_hz"]
    clean = data["clean"]
    ts = truth_summary(data)
    ch4_mag = np.abs(clean["ch4_standalone_tray_accel_transmissibility"])
    ch1_mag = np.abs(clean["ch1_dome_only_reciprocal_inertance"])
    ch2 = clean["ch2_coupled_primary_reciprocal_inertance"]
    ch3 = clean["ch3_coupled_tray_reciprocal_inertance"]
    low_ch4 = float(np.median(ch4_mag[freqs < 18.0]))
    high_ch4 = float(np.median(ch4_mag[freqs > 180.0]))
    peak_freq_ch4 = float(freqs[int(np.argmax(ch4_mag))])
    ch1_band = (freqs > 70.0) & (freqs < 150.0)
    ch1_notch_freq = float(freqs[ch1_band][int(np.argmin(ch1_mag[ch1_band]))])
    rel_l2_ch2_ch3 = float(np.linalg.norm(ch2 - ch3) / max(np.linalg.norm(ch2), np.linalg.norm(ch3), 1e-12))
    bench_values = nasa_7004c_figure9_normalized(np.array([0.62, 1.0]), q=50.0)
    load_at_0p62 = float(bench_values["load"][0])
    load_at_1 = float(bench_values["load"][1])
    source_at_1 = float(bench_values["source"][1])
    checks = {
        "nasa_7004c_scope": "Applied explicitly through Figure 9 normalized source/load apparent-mass benchmark curves and fresh source/load-style curves.",
        "vibrationdata_scope": "Applied as SDOF/2DOF shape sanity checks for transmissibility, resonances, and non-duplicate drive points.",
        "ch4_low_frequency_transmissibility_near_one": abs(low_ch4 - 1.0) < 0.20,
        "ch4_high_frequency_rolloff": high_ch4 < 0.30,
        "ch4_peak_near_tray_frequency": abs(peak_freq_ch4 - ts["tray_true_hz"]) / ts["tray_true_hz"] < 0.18,
        "ch1_reciprocal_inertance_notch_near_dome_frequency": abs(ch1_notch_freq - ts["dome_true_hz"]) / ts["dome_true_hz"] < 0.18,
        "ch2_ch3_not_duplicate": rel_l2_ch2_ch3 > 0.05,
        "nasa_7004c_figure9_load_at_0p62_near_1p62": abs(load_at_0p62 - 1.62) < 0.08,
        "nasa_7004c_figure9_load_peak_near_50": abs(load_at_1 - 50.01) < 1.0,
        "nasa_7004c_figure9_source_notch_near_0p02": abs(source_at_1 - 0.02) < 0.01,
    }
    out = {
        "checks": checks,
        "metrics": {
            "ch4_low_frequency_median": low_ch4,
            "ch4_high_frequency_median": high_ch4,
            "ch4_peak_frequency_hz": peak_freq_ch4,
            "tray_true_frequency_hz": ts["tray_true_hz"],
            "ch1_notch_frequency_hz": ch1_notch_freq,
            "dome_true_frequency_hz": ts["dome_true_hz"],
            "ch2_ch3_relative_l2": rel_l2_ch2_ch3,
            "nasa_7004c_q": 50.0,
            "nasa_7004c_load_at_r_0p62": load_at_0p62,
            "nasa_7004c_load_at_r_1": load_at_1,
            "nasa_7004c_source_at_r_1": source_at_1,
        },
        "pass": all(v for v in checks.values() if isinstance(v, bool)),
    }
    (OUT_DIR / "reference_comparison.json").write_text(json.dumps(out, indent=2))
    return out


def plot_reference_comparison(ref: dict[str, Any]) -> None:
    metrics = ref["metrics"]
    cards = [
        (
            "Ch4 low-frequency",
            f"computed {metrics['ch4_low_frequency_median']:.3f}",
            "expected near 1.0",
            "Base and tray move together below resonance.",
        ),
        (
            "Ch4 high-frequency",
            f"computed {metrics['ch4_high_frequency_median']:.3f}",
            "expected < 0.30",
            "Fixed-base tray transmissibility rolls off.",
        ),
        (
            "Ch4 peak",
            f"{metrics['ch4_peak_frequency_hz']:.2f} Hz",
            f"near tray {metrics['tray_true_frequency_hz']:.2f} Hz",
            "Standalone tray resonance is in band.",
        ),
        (
            "Ch1 notch",
            f"{metrics['ch1_notch_frequency_hz']:.2f} Hz",
            f"near dome {metrics['dome_true_frequency_hz']:.2f} Hz",
            "Reciprocal inertance has a notch, not a load-AM peak.",
        ),
        (
            "Ch2/Ch3 distinct",
            f"relative L2 = {metrics['ch2_ch3_relative_l2']:.3f}",
            "expected > 0.05",
            "Primary and tray drive-point channels are not duplicates.",
        ),
        (
            "7004C load value",
            f"M(0.62) = {metrics['nasa_7004c_load_at_r_0p62']:.3f}",
            "about 1.62",
            "NASA-HDBK-7004C Fig. 9 normalized value.",
        ),
        (
            "7004C load peak",
            f"M(1) = {metrics['nasa_7004c_load_at_r_1']:.2f}",
            "about 50.01 for Q=50",
            "Load apparent mass peaks at fixed-base resonance.",
        ),
        (
            "7004C source notch",
            f"M(1) = {metrics['nasa_7004c_source_at_r_1']:.3f}",
            "about 0.02 for Q=50",
            "Source apparent mass has a resonance notch.",
        ),
    ]
    fig, ax = plt.subplots(figsize=(14, 10.2))
    ax.set_axis_off()
    ax.text(0.5, 0.965, "Reference and standards comparison values", ha="center", va="center", fontsize=17, weight="bold")
    ax.text(0.5, 0.925, "Values are shown for human review. Boolean pass/fail remains in reference_comparison.json.", ha="center", va="center", fontsize=11.5)
    x_positions = [0.045, 0.525]
    y_positions = [0.70, 0.49, 0.28, 0.07]
    width = 0.43
    height = 0.17
    for idx, (title, value, expected, _meaning) in enumerate(cards):
        col = idx % 2
        row = idx // 2
        x = x_positions[col]
        y = y_positions[row]
        patch = mpatches.FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.012,rounding_size=0.012",
            fc="#f6f6f6" if idx % 2 else "#eef4fa",
            ec="#333333",
            lw=1.1,
        )
        ax.add_patch(patch)
        ax.text(x + 0.018, y + height - 0.030, title, fontsize=13.0, weight="bold", ha="left", va="top")
        ax.text(x + 0.018, y + height - 0.082, value, fontsize=12.6, ha="left", va="top")
        ax.text(x + 0.018, y + height - 0.132, expected, fontsize=11.8, ha="left", va="top", color="#333333")
    fig.subplots_adjust(left=0.02, right=0.98, top=0.97, bottom=0.03)
    save_figure(
        fig,
        "reference_standards_comparison_cards.png",
        dpi=190,
        min_font_pt=11.5,
        min_width_px=2400,
        min_height_px=1700,
        text_heavy=True,
    )
    plt.close(fig)


def plot_nasa_7004c_apparent_mass(data: dict[str, Any]) -> None:
    c: Constants = data["constants"]
    truth: Params = data["truth"]
    freqs = data["freqs_hz"]
    c1, c2 = damping_values(truth, c)
    source = sdof_source_apparent_mass(freqs, c.m1, truth.k1, c1)
    load = sdof_load_apparent_mass(freqs, c.m2, truth.k2, c2)
    interface_effective = source * load / (source + load)
    r = np.geomspace(0.2, 2.0, 600)
    bench = nasa_7004c_figure9_normalized(r, q=50.0)
    bench_values = nasa_7004c_figure9_normalized(np.array([0.62, 1.0]), q=50.0)
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    axes[0].plot(r, bench["source"], label="source apparent mass, Q=50", lw=1.8)
    axes[0].plot(r, bench["load"], label="load apparent mass, Q=50", lw=1.8)
    axes[0].scatter([0.62], [bench_values["load"][0]], color="black", zorder=3, label="load M(0.62) ≈ 1.62")
    axes[0].scatter([1.0], [bench_values["load"][1]], color="#c65b42", zorder=3, label="load peak ≈ 50.01")
    axes[0].scatter([1.0], [bench_values["source"][1]], color="#4f7cac", zorder=3, label="source notch ≈ 0.02")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("frequency ratio r = f / f0")
    axes[0].set_ylabel("normalized apparent mass magnitude")
    axes[0].set_title("NASA-HDBK-7004C Figure 9 benchmark values")
    axes[0].legend(fontsize=7)
    axes[0].grid(True, which="both", alpha=0.25)
    axes[1].plot(freqs, np.abs(source), label="fresh source AM: dome support", lw=1.7)
    axes[1].plot(freqs, np.abs(load), label="fresh load AM: tray fixed-base", lw=1.7)
    axes[1].plot(freqs, np.abs(interface_effective), label="|Ms Ml / (Ms + Ml)|", lw=1.3)
    axes[1].axvline(math.sqrt(truth.k1 / c.m1) / (2.0 * math.pi), color="#4f7cac", ls="--", lw=1, label="dome local f")
    axes[1].axvline(math.sqrt(truth.k2 / c.m2) / (2.0 * math.pi), color="#c65b42", ls="--", lw=1, label="tray local f")
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("frequency [Hz]")
    axes[1].set_ylabel("apparent mass magnitude [kg]")
    axes[1].set_title("Fresh source/load-style apparent mass")
    axes[1].legend(fontsize=7)
    axes[1].grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    save_figure(fig, "nasa_7004c_apparent_mass_benchmark.png")
    plt.close(fig)


def save_posterior(mcmc: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    ts = truth_summary(data)
    phys = mcmc["physical_samples"]
    summaries = {name: summarize(values) for name, values in phys.items()}
    qoi_summary = summarize(mcmc["qoi_samples"])
    qoi_summary["truth"] = ts["qoi_truth_3grms_tray_accel_g"]
    qoi_summary["units"] = "g"
    qoi_summary["definition"] = "3 * GRMS of tray acceleration response PSD"
    qoi_summary["mean_bias"] = qoi_summary["mean"] - qoi_summary["truth"]
    qoi_summary["fraction_above_truth"] = float(np.mean(mcmc["qoi_samples"] > qoi_summary["truth"]))
    out = {
        "sampler": {
            "method": "single-coordinate random-walk Metropolis-Hastings",
            "steps": int(len(mcmc["traces"])),
            "burn": int(mcmc["burn"]),
            "thin": int(mcmc["thin"]),
            "retained_samples": int(len(mcmc["samples_transformed"])),
            "acceptance_rate": float(mcmc["acceptance_rate"]),
            "proposal_scales": mcmc["proposal_scales"].tolist(),
        },
        "parameter_summaries": summaries,
        "qoi_summary": qoi_summary,
        "qoi_samples_3grms_tray_accel_g": mcmc["qoi_samples"].tolist(),
        "samples": {name: values.tolist() for name, values in phys.items()},
    }
    (OUT_DIR / "posterior_summary.json").write_text(json.dumps(out, indent=2))
    return out


def fresh_prior_comparison() -> dict[str, Any]:
    prior_packet = ROOT / "artifacts" / "reports" / "synthetic_statfem_packet.md"
    prior_key = ROOT / "artifacts" / "reports" / "key_frf_summary.json"
    prior_dataset = ROOT / "artifacts" / "synthetic" / "twodof_dataset.json"
    result = {
        "generated_after_fresh_outputs": True,
        "prior_artifacts_checked": {
            "synthetic_statfem_packet": prior_packet.exists(),
            "key_frf_summary": prior_key.exists(),
            "twodof_dataset": prior_dataset.exists(),
        },
        "matched": [
            "same nominal 75 Hz tray and 110 Hz dome problem class",
            "synthetic observation noise plus model-form discrepancy",
            "log-scaled frequency-domain review plots",
            "separate Ch2 and Ch3 drive/response definitions",
            "posterior QOI samples, sampler diagnostics, sensitivity, and checker-backed packet",
            "NASA-HDBK-7004C used to prevent apparent-mass convention overclaiming",
        ],
        "differed": [
            "fresh coupled assembly uses one tray-to-primary stiffness/damping and no direct tray-to-base spring in the coupled model",
            "updated flight-like measurement uses a response PSD likelihood and 3*GRMS QOI rather than a deterministic time-history peak",
            "updated noise/discrepancy is larger, local-magnitude scaled, and visibly separates observed from clean curves",
            "synthetic truth now includes explicit model-form shifts of -15%/+15% in natural frequency and +25%/-25% in damping ratio",
            "fresh checker and artifacts are scoped under a separate rerun directory",
        ],
        "improvements": [
            "question framing, assumptions, and contracts were written before fresh plots/fits",
            "absolute injected GP, iid, and total errors are stored for every channel",
            "the report includes explicit NASA-HDBK-7004C Figure 9 source/load apparent-mass benchmark values",
            "reference comparison is now a value table instead of a pass/fail bar chart",
        ],
        "unresolved": [
            "synthetic-only toy with no physical hardware data",
            "simple random-walk MH rather than NUTS/HMC or formal convergence diagnostics",
            "sensitivity does not refit the posterior for every noise/discrepancy scenario",
            "the larger discrepancy assumptions are literature-informed but not calibrated to a specific tank/tray test article",
        ],
        "gates_that_prevented_mistakes": [
            "Question gate prevented optimizing a QOI before stating the engineering decision",
            "Quantity-contract gate forced separation between reciprocal inertance and 7004C source/load apparent mass",
            "Plot gate forced log frequency axes and linear magnitude units",
            "Verification gate forced a duplicate-channel numerical check and report-content checker",
        ],
    }
    (OUT_DIR / "fresh_vs_prior_comparison.json").write_text(json.dumps(result, indent=2))
    return result


def axis_metadata() -> dict[str, str]:
    return {
        "figures/channel_truth_vs_observed.png": "log",
        "figures/channel_absolute_error.png": "log",
        "figures/channel_normalized_error_diagnostic.png": "log",
        "figures/gp_discrepancy_samples.png": "log",
        "figures/posterior_fit_and_residuals.png": "log",
        "figures/statfem_likelihood_graphical_model_legible.png": "not a frequency-domain plot",
        "figures/bayes_parameter_update.png": "parameter axes; likelihood slices over physical parameters",
        "figures/parameter_posterior_samples.png": "analytic prior density plus MC prior histogram and posterior KDE; parameter axes",
        "figures/prior_predictive_vs_data.png": "log frequency for spectral/FRF panels",
        "figures/posterior_predictive_spectra.png": "log frequency for spectral/FRF panels",
        "figures/full_vs_peak_feature_likelihood_comparison.png": "mixed parameter/QOI axes plus log frequency for PSD panel",
        "figures/peak_feature_mapping_benchmark.png": "not a frequency-domain plot; feature-map parameter/frequency axes",
        "figures/peak_feature_sensitivity_matrix.png": "not a frequency-domain plot; feature sensitivity matrix",
        "figures/flight_truth_vs_observed.png": "log frequency for PSD panels; time axis for realization panel",
        "figures/qoi_samples.png": "log frequency for PSD panels; histogram for QOI samples",
        "figures/reference_standards_comparison_cards.png": "not a frequency-domain plot",
        "figures/nasa_7004c_apparent_mass_benchmark.png": "log frequency/frequency-ratio axes",
    }


def write_manifest(posterior: dict[str, Any], ref: dict[str, Any], sens: dict[str, Any]) -> None:
    figures = sorted(str(p.relative_to(OUT_DIR)) for p in FIG_DIR.glob("*.png"))
    manifest = {
        "report": "fresh_2dof_statfem_packet.md",
        "question_framing": "question_framing_and_plan.md",
        "quantity_contracts": "quantity_contracts.md",
        "assumptions_ledger_markdown": "assumptions_ledger.md",
        "assumptions_ledger_json": "assumptions_ledger.json",
        "dataset": "fresh_2dof_dataset.json",
        "posterior": "posterior_summary.json",
        "bayes_update_summary": "bayes_update_summary.json",
        "peak_feature_likelihood_comparison": "peak_feature_likelihood_summary.json",
        "peak_feature_mapping_benchmark": "peak_feature_mapping_benchmark.json",
        "sensitivity": "sensitivity_summary.json",
        "reference_comparison": "reference_comparison.json",
        "checker_report": "checker_report.json",
        "image_legibility_report": "image_legibility_report.json",
        "figures": figures,
        "frequency_axis_scale": axis_metadata(),
        "magnitude_scale": "linear",
        "qoi_summary_exists": "qoi_summary" in posterior,
        "reference_comparison_pass": bool(ref["pass"]),
        "image_legibility_pass": json.loads((OUT_DIR / "image_legibility_report.json").read_text()).get("pass")
        if (OUT_DIR / "image_legibility_report.json").exists()
        else False,
        "sensitivity_scenarios": len(sens["qoi_scenarios"]) + len(sens["synthetic_error_scenarios"]),
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))


def run_acceptance_checks() -> dict[str, Any]:
    required_figures = [
        "figures/model_schematic.png",
        "figures/workflow_diagram.png",
        "figures/statfem_likelihood_graphical_model_legible.png",
        "figures/assumptions_graphical.png",
        "figures/channel_truth_vs_observed.png",
        "figures/channel_absolute_error.png",
        "figures/channel_normalized_error_diagnostic.png",
        "figures/gp_discrepancy_samples.png",
        "figures/flight_truth_vs_observed.png",
        "figures/posterior_fit_and_residuals.png",
        "figures/bayes_parameter_update.png",
        "figures/parameter_posterior_samples.png",
        "figures/prior_predictive_vs_data.png",
        "figures/posterior_predictive_spectra.png",
        "figures/full_vs_peak_feature_likelihood_comparison.png",
        "figures/peak_feature_mapping_benchmark.png",
        "figures/peak_feature_sensitivity_matrix.png",
        "figures/sampler_diagnostics.png",
        "figures/qoi_samples.png",
        "figures/sensitivity_qoi.png",
        "figures/sensitivity_synthetic_error.png",
        "figures/reference_standards_comparison_cards.png",
        "figures/nasa_7004c_apparent_mass_benchmark.png",
    ]
    required_files = [
        "fresh_2dof_statfem_packet.md",
        "question_framing_and_plan.md",
        "quantity_contracts.md",
        "assumptions_ledger.md",
        "assumptions_ledger.json",
        "fresh_2dof_dataset.json",
        "posterior_summary.json",
        "bayes_update_summary.json",
        "peak_feature_likelihood_summary.json",
        "peak_feature_mapping_benchmark.json",
        "sensitivity_summary.json",
        "reference_comparison.json",
        "image_legibility_report.json",
        "fresh_vs_prior_comparison.json",
        "noise_qoi_7004c_lit_review.md",
        "manifest.json",
        *required_figures,
    ]
    missing = [path for path in required_files if not (OUT_DIR / path).exists()]
    report_text = (OUT_DIR / "fresh_2dof_statfem_packet.md").read_text() if (OUT_DIR / "fresh_2dof_statfem_packet.md").exists() else ""
    required_snippets = [
        "## Question Framing",
        "## Assumptions Ledger",
        "## Quantity Contracts",
        "## Reference and Standards Comparison",
        "NASA-HDBK-7004C",
        "vibrationdata.com",
        "## Sensitivity to Assumptions",
        "## Checker Status",
        "## Limitations",
        "## Fresh-Agent Comparison",
        "QOI posterior samples",
        "3 * GRMS",
        "NASA-HDBK-7004C Figure 9",
        "noise_qoi_7004c_lit_review.md",
        "Frequency-axis metadata",
        "Bayes rule in action",
        "one synthetic dataset",
        "flight-to-flight variability is not modeled",
        "StatFEM-style noise/discrepancy model",
        "Central methodology",
        "Prior variance assumptions",
        "MC prior histogram",
        "analytic prior density",
        "Likelihood formulation",
        "not only resonance peak locations or magnitudes",
        "## Method Summary",
        "Whole FRF/PSD likelihood",
        "Inferred variables",
        "Fixed assumptions",
        "Not inferred",
        "Specific likelihood function",
        "## Whole FRF vs Peak-Feature Likelihood Comparison",
        "peak-feature likelihood",
        "## Peak/Notch Feature Mapping Benchmark",
        "predicted transfer-function feature",
        "not directly compared with the true natural frequency",
        "Image legibility QA",
    ]
    missing_snippets = [s for s in required_snippets if s not in report_text]
    assumptions = json.loads((OUT_DIR / "assumptions_ledger.json").read_text()) if (OUT_DIR / "assumptions_ledger.json").exists() else {"rows": []}
    numeric_assumptions = [
        r for r in assumptions.get("rows", []) if isinstance(r.get("value"), (int, float)) and r.get("units")
    ]
    assumption_values = {r.get("assumption"): r.get("value") for r in assumptions.get("rows", [])}
    model_error_assumptions_present = (
        abs(float(assumption_values.get("Dome frequency model error", 999.0)) + 0.15) < 1e-12
        and abs(float(assumption_values.get("Tray frequency model error", 999.0)) - 0.15) < 1e-12
        and abs(float(assumption_values.get("Dome damping model error", 999.0)) - 0.25) < 1e-12
        and abs(float(assumption_values.get("Tray damping model error", 999.0)) + 0.25) < 1e-12
    )
    dataset = json.loads((OUT_DIR / "fresh_2dof_dataset.json").read_text()) if (OUT_DIR / "fresh_2dof_dataset.json").exists() else {}
    ch2_ch3_rel = None
    if dataset:
        ch2 = np.asarray(dataset["channels_clean"]["ch2_coupled_primary_reciprocal_inertance"]["real"]) + 1j * np.asarray(dataset["channels_clean"]["ch2_coupled_primary_reciprocal_inertance"]["imag"])
        ch3 = np.asarray(dataset["channels_clean"]["ch3_coupled_tray_reciprocal_inertance"]["real"]) + 1j * np.asarray(dataset["channels_clean"]["ch3_coupled_tray_reciprocal_inertance"]["imag"])
        ch2_ch3_rel = float(np.linalg.norm(ch2 - ch3) / max(np.linalg.norm(ch2), np.linalg.norm(ch3), 1e-12))
    manifest = json.loads((OUT_DIR / "manifest.json").read_text()) if (OUT_DIR / "manifest.json").exists() else {}
    axis_metadata = manifest.get("frequency_axis_scale", {})
    frequency_axis_items = {
        key: value
        for key, value in axis_metadata.items()
        if "parameter" not in key
        and "qoi_samples" not in key
        and "not a frequency-domain plot" not in str(value)
    }
    declared_axis_exceptions_ok = all(
        "log" in str(value)
        or "parameter" in str(value)
        or "histogram" in str(value)
        or "not a frequency-domain plot" in str(value)
        for value in axis_metadata.values()
    )
    axis_ok = bool(frequency_axis_items) and all("log" in str(v) for v in frequency_axis_items.values()) and declared_axis_exceptions_ok
    posterior = json.loads((OUT_DIR / "posterior_summary.json").read_text()) if (OUT_DIR / "posterior_summary.json").exists() else {}
    qoi_ok = bool(posterior.get("qoi_summary")) and len(posterior.get("qoi_samples_3grms_tray_accel_g", [])) >= 100
    bayes = json.loads((OUT_DIR / "bayes_update_summary.json").read_text()) if (OUT_DIR / "bayes_update_summary.json").exists() else {}
    parameter_ci_ok = all(
        name in bayes.get("parameter_summaries", {})
        and "q025" in bayes["parameter_summaries"][name].get("posterior", {})
        and "q975" in bayes["parameter_summaries"][name].get("posterior", {})
        for name in ["dome_hz", "tray_hz", "zeta1", "zeta2"]
    )
    replicate_info = dataset.get("simulation_replicates", {}) if dataset else {}
    simulation_replicates_documented = (
        replicate_info.get("frequency_domain_realizations_per_channel") == 1
        and replicate_info.get("flight_like_response_psd_realizations") == 1
        and replicate_info.get("flight_time_history_realizations") == 1
        and replicate_info.get("flight_to_flight_variability_modeled") is False
        and "one synthetic dataset" in report_text
    )
    statfem_noise_documented = (
        bayes.get("statfem_noise_model", {}).get("kept_separate_in_generated_data") is True
        and bayes.get("statfem_noise_model", {}).get("realized_discrepancy_inferred_as_latent_field") is False
        and "StatFEM-style noise/discrepancy model" in report_text
    )
    prior_likelihood_methodology_documented = (
        bayes.get("prior_model", {}).get("natural_frequency_prior", {}).get("sigma_log_frequency") == 0.09
        and bayes.get("prior_model", {}).get("damping_prior", {}).get("sigma_log_damping_ratio") == 0.35
        and bayes.get("likelihood_formulation", {}).get("uses_whole_frf_not_peak_summary") is True
        and bayes.get("prior_visualization", {}).get("analytic_prior_density_plotted") is True
        and bayes.get("prior_visualization", {}).get("mc_prior_histogram_plotted") is True
        and int(bayes.get("prior_visualization", {}).get("mc_prior_histogram_samples", 0)) >= 50000
        and int(bayes.get("prior_visualization", {}).get("prior_predictive_mc_samples", 0)) >= 3000
        and bayes.get("prior_visualization", {}).get("prior_predictive_quantiles_smoothed_for_display") is True
        and float(bayes.get("prior_visualization", {}).get("predictive_band_smoothing_sigma_points", 0.0)) > 0.0
        and "Likelihood formulation" in report_text
        and "MC prior histogram" in report_text
        and "analytic prior density" in report_text
        and "smoothed MC predictive summaries" in report_text
        and "not only resonance peak locations or magnitudes" in report_text
    )
    method_summary_documented = (
        "## Method Summary" in report_text
        and "Whole FRF/PSD likelihood" in report_text
        and "Inferred variables" in report_text
        and "Fixed assumptions" in report_text
        and "Not inferred" in report_text
        and "Specific likelihood function" in report_text
        and (OUT_DIR / "figures/statfem_likelihood_graphical_model_legible.png").exists()
    )
    image_legibility = json.loads((OUT_DIR / "image_legibility_report.json").read_text()) if (OUT_DIR / "image_legibility_report.json").exists() else {}
    image_legibility_pass = (
        image_legibility.get("pass") is True
        and "figures/statfem_likelihood_graphical_model_legible.png" in image_legibility.get("strict_text_heavy_figures", [])
        and "figures/reference_standards_comparison_cards.png" in image_legibility.get("strict_text_heavy_figures", [])
        and "Image legibility QA" in report_text
    )
    peak_comp = json.loads((OUT_DIR / "peak_feature_likelihood_summary.json").read_text()) if (OUT_DIR / "peak_feature_likelihood_summary.json").exists() else {}
    peak_feature_comparison_present = (
        bool(peak_comp.get("parameter_comparison"))
        and bool(peak_comp.get("qoi_comparison"))
        and peak_comp.get("feature_likelihood_assumptions", {}).get("description", "").startswith("Lossy comparison")
        and (OUT_DIR / "figures/full_vs_peak_feature_likelihood_comparison.png").exists()
        and "## Whole FRF vs Peak-Feature Likelihood Comparison" in report_text
        and "peak-feature likelihood" in report_text
    )
    feature_benchmark = json.loads((OUT_DIR / "peak_feature_mapping_benchmark.json").read_text()) if (OUT_DIR / "peak_feature_mapping_benchmark.json").exists() else {}
    feature_rows = feature_benchmark.get("feature_rows", {})
    feature_mapping_benchmark_present = (
        feature_benchmark.get("description", "").startswith("Benchmark of feature likelihood mapping")
        and bool(feature_rows)
        and feature_rows.get("ch1_dome_notch", {}).get("interpretation") == "direct structural feature"
        and feature_rows.get("ch2_primary_notch", {}).get("structural_frequency_mix") is True
        and feature_rows.get("ch3_tray_notch", {}).get("structural_frequency_mix") is True
        and feature_rows.get("ch5_response_psd_peak", {}).get("force_confounded") is True
        and (OUT_DIR / "figures/peak_feature_mapping_benchmark.png").exists()
        and (OUT_DIR / "figures/peak_feature_sensitivity_matrix.png").exists()
        and "## Peak/Notch Feature Mapping Benchmark" in report_text
        and "not directly compared with the true natural frequency" in report_text
    )
    sens = json.loads((OUT_DIR / "sensitivity_summary.json").read_text()) if (OUT_DIR / "sensitivity_summary.json").exists() else {}
    ref = json.loads((OUT_DIR / "reference_comparison.json").read_text()) if (OUT_DIR / "reference_comparison.json").exists() else {}
    forbidden_sensitivity_text = [
        "Sensitivity labels:",
        "Decision threshold used only for sensitivity illustration",
        "1.10 x synthetic truth",
    ]
    no_arbitrary_threshold_language = (
        all(text not in report_text for text in forbidden_sensitivity_text)
        and sens.get("decision_threshold") is None
        and "decision_threshold_110pct_truth_3grms_g" not in sens
    )
    ref_metrics = ref.get("metrics", {})
    reference_value_metrics_present = all(
        key in ref_metrics
        for key in [
            "ch4_low_frequency_median",
            "ch4_peak_frequency_hz",
            "nasa_7004c_load_at_r_0p62",
            "nasa_7004c_load_at_r_1",
            "nasa_7004c_source_at_r_1",
        ]
    )
    checks = {
        "required_files_exist": not missing,
        "required_report_snippets_present": not missing_snippets,
        "numerical_assumptions_present": len(numeric_assumptions) >= 10,
        "model_error_assumptions_present": model_error_assumptions_present,
        "reference_comparison_present": bool(ref.get("checks")) and "NASA-HDBK-7004C" in report_text and "vibrationdata.com" in report_text,
        "reference_value_metrics_present": reference_value_metrics_present,
        "sensitivity_artifact_present": bool(sens.get("qoi_scenarios")) and bool(sens.get("synthetic_error_scenarios")),
        "no_arbitrary_sensitivity_threshold_language": no_arbitrary_threshold_language,
        "channel_2_and_3_not_duplicates": ch2_ch3_rel is not None and ch2_ch3_rel > 0.05,
        "frequency_axis_metadata_log": axis_ok,
        "qoi_sample_summary_exists": qoi_ok,
        "bayes_parameter_update_artifact_present": bool(bayes.get("parameter_summaries")),
        "posterior_parameter_95_ci_exists": parameter_ci_ok,
        "simulation_replicate_count_reported": simulation_replicates_documented,
        "statfem_noise_model_documented": statfem_noise_documented,
        "prior_likelihood_methodology_documented": prior_likelihood_methodology_documented,
        "method_summary_documented": method_summary_documented,
        "peak_feature_likelihood_comparison_present": peak_feature_comparison_present,
        "peak_feature_mapping_benchmark_present": feature_mapping_benchmark_present,
        "image_legibility_report_pass": image_legibility_pass,
        "checker_status_and_limitations_included": "## Checker Status" in report_text and "## Limitations" in report_text,
    }
    result = {
        "missing_files": missing,
        "missing_snippets": missing_snippets,
        "numeric_assumption_count": len(numeric_assumptions),
        "channel_2_3_relative_l2": ch2_ch3_rel,
        "checks": checks,
        "pass": all(checks.values()),
    }
    (OUT_DIR / "checker_report.json").write_text(json.dumps(result, indent=2))
    return result


def write_report(
    posterior: dict[str, Any],
    bayes: dict[str, Any],
    peak_comp: dict[str, Any],
    feature_benchmark: dict[str, Any],
    sens: dict[str, Any],
    ref: dict[str, Any],
    comparison: dict[str, Any],
    checker: dict[str, Any] | None,
) -> None:
    ts = json.loads((OUT_DIR / "fresh_2dof_dataset.json").read_text())["truth"]
    qoi = posterior["qoi_summary"]
    sampler = posterior["sampler"]
    ref_metrics = ref["metrics"]
    checker_text = "pending first pass" if checker is None else ("PASS" if checker["pass"] else "FAIL")
    image_qc = json.loads((OUT_DIR / "image_legibility_report.json").read_text()) if (OUT_DIR / "image_legibility_report.json").exists() else {"pass": False, "checks": [], "strict_text_heavy_figures": []}
    image_qc_text = "PASS" if image_qc.get("pass") else "FAIL"
    image_qc_strict = ", ".join(image_qc.get("strict_text_heavy_figures", [])) or "none"
    fig = lambda name: f"![{name}](<{(FIG_DIR / name).resolve()}>)"
    checks_table = ""
    if checker is not None:
        checks_table = "\n".join(
            f"| {name} | {value} |" for name, value in checker["checks"].items()
        )
    else:
        checks_table = "| Checker generated | pending |"
    param_rows = []
    for view in PARAMETER_VIEWS:
        name = view["name"]
        post = bayes["parameter_summaries"][name]["posterior"]
        prior = bayes["parameter_summaries"][name]["prior"]
        param_rows.append(
            f"| {view['title']} | {prior['median']:.5g} | {post['median']:.5g} | [{post['q025']:.5g}, {post['q975']:.5g}] | {post['truth']:.5g} | {post['units']} |"
        )
    param_table = "\n".join(param_rows)
    ci_misses = [
        view["title"]
        for view in PARAMETER_VIEWS
        if not bayes["parameter_summaries"][view["name"]]["posterior"]["truth_in_95_ci"]
    ]
    ci_miss_text = (
        "Posterior interval diagnostic: all four synthetic truths fall inside the displayed 95% CIs."
        if not ci_misses
        else "Posterior interval diagnostic: synthetic truth falls outside the displayed 95% CI for "
        + ", ".join(ci_misses)
        + ". This is a warning, not a pass."
    )
    repl = bayes["simulation_replicates"]
    like = bayes["likelihood_summary"]
    prior_model = bayes["prior_model"]
    likelihood_form = bayes["likelihood_formulation"]
    peak_qoi = peak_comp["qoi_comparison"]["peak_feature"]
    full_qoi = peak_comp["qoi_comparison"]["full_curve"]
    peak_width_ratio = peak_comp["qoi_95_width_ratio_peak_feature_over_full_curve"]
    feature_rows = feature_benchmark["feature_rows"]
    feature_table = "\n".join(
        [
            "| Feature | Clean predicted feature | Observed feature | Frequency z-score | Interpretation |",
            "|---|---:|---:|---:|---|",
            *[
                f"| {row['label']} | {row['clean_feature_frequency_hz']:.3f} Hz | {row['observed_feature_frequency_hz']:.3f} Hz | {row['frequency_observation_z_score_vs_clean_feature']:.2f} | {row['interpretation']} |"
                for row in feature_rows.values()
            ],
        ]
    )
    freq95 = prior_model["natural_frequency_prior"]["approx_95_factor_untruncated"]
    damp95 = prior_model["damping_prior"]["approx_95_factor_untruncated"]
    lines = [
        "# Fresh 2DOF StatFEM/FBS Human-Review Packet",
        "",
        "Date: 2026-06-01",
        "",
        "One-command replay: `bash scripts/run_fresh_2dof_statfem_fbs.sh`.",
        "",
        "## Question Framing",
        "",
        "Engineering decision: decide whether the secondary tray analog has acceptable random-vibration response under a flight-like forcing case after updating a fixed-base 2DOF model with synthetic evidence.",
        "",
        "Objective/QOI: estimate the posterior distribution of `3 * GRMS` from the tray acceleration response PSD, reported in `g`. The run is successful only if the review packet, sensitivity, references, and checker pass are artifact-backed.",
        "",
        "BOED/optimization could choose future measurement class, frequency grid, drive level, sensor set, and forcing basis. Human judgment still chooses the risk threshold, whether this toy model is relevant, and whether apparent-mass-like conventions match real hardware.",
        "",
        "Wrong-question trigger: channel convention mismatch, non-distinct Ch2/Ch3 channels, residuals dominated by arbitrary discrepancy/forcing assumptions, or failure to reproduce expected resonance/antiresonance behavior.",
        "",
        fig("workflow_diagram.png"),
        "",
        "## Method Summary",
        "",
        "This first-pass review summary is intentionally redundant with later sections. These choices control how every plot should be interpreted and should be visible before a reviewer reaches posterior fits.",
        "",
        fig("statfem_likelihood_graphical_model_legible.png"),
        "",
        "| Item | Current run choice |",
        "|---|---|",
        "| Inferred variables | `theta = {k1, k2, zeta1, zeta2, force_amp, force_fc}` |",
        "| Fixed assumptions | `m1=1 kg`, `m2=0.6 kg`, fixed base, one 2DOF coupling convention, frequency grids, QOI definition, and fixed noise/discrepancy hyperparameters |",
        f"| Data count | one synthetic dataset: `{repl['frequency_domain_realizations_per_channel']}` realization per FRF/transfer channel, `{repl['flight_like_response_psd_realizations']}` flight-like response PSD, and `{repl['flight_time_history_realizations']}` secondary time-history realization |",
        "| Flight-to-flight variability | Not modeled; there are no repeated flights or repeated tests in this trial |",
        "| Whole FRF/PSD likelihood | Yes. Ch1-Ch4 use all complex FRF/transfer values at 120 log-spaced frequencies; Ch5 uses all 181 log response-PSD points |",
        "| Peak-only likelihood | No. Peak and notch locations are reference checks and plot diagnostics only |",
        "| Not inferred variables/hyperparameters | Realized discrepancy fields, sensor-noise scales, discrepancy scales, correlation lengths, flight-to-flight effects, and replicate random effects are fixed/not inferred in this toy |",
        "| Posterior spectra | Posterior predictive spectra are distributions over retained samples; a single posterior-mean spectrum is only a visual summary |",
        "",
        "Specific likelihood function: for FRF channel `i`, `y_i(f_j) = H_i(f_j; theta) + d_i(f_j) + e_i(f_j)`, with real and imaginary residual vectors evaluated against `K_discrepancy_i + diag(sigma_sensor_i^2)`. For the flight-like response, `log S_obs(f_j) = log S_a2(f_j; theta) + d_psd(f_j) + e_psd(f_j)`, evaluated against `K_discrepancy_psd + sigma_sensor_psd^2 I`. This is a whole-curve likelihood, not a peak-summary likelihood.",
        "",
        "## Assumptions Ledger",
        "",
        f"Key numerical values: `m1={ts['m1']:.3f} kg`, `m2={ts['m2']:.3f} kg`, nominal tray `75 Hz`, nominal dome `110 Hz`, true tray `{ts['tray_true_hz']:.3f} Hz`, true dome `{ts['dome_true_hz']:.3f} Hz`, model-form frequency errors `dome -15%` and `tray +15%`, damping errors `dome +25%` and `tray -25%`, complex FRF observation noise `{Constants().obs_noise_rel:.3f}` times local magnitude with a `{Constants().discrepancy_floor_rel:.3f}` median floor, complex FRF GP discrepancy `{Constants().discrepancy_rel:.3f}` times local magnitude, response PSD log-noise sigma `{Constants().response_psd_noise_log_sigma:.3f}`, response PSD log-discrepancy sigma `{Constants().response_psd_discrepancy_log_sigma:.3f}`.",
        "",
        "Full ledgers: `assumptions_ledger.md`, `assumptions_ledger.json`, and `noise_qoi_7004c_lit_review.md`.",
        "",
        fig("assumptions_graphical.png"),
        "",
        "## Quantity Contracts",
        "",
        "Quantity contracts were written before fitting or plotting in `quantity_contracts.md`. The apparent-mass-like channels Ch1-Ch3 are explicitly reciprocal inertance `F/a`, not NASA-HDBK-7004C load apparent mass. Ch4 is standalone tray absolute acceleration transmissibility `a_tray/a_base`. Ch5 QOI is `3 * GRMS` of the tray acceleration response PSD.",
        "",
        "Frequency-domain plots use linear magnitudes and log-scaled frequency axes. Frequency-axis metadata is recorded in `manifest.json`.",
        "",
        fig("model_schematic.png"),
        "",
        "## Measurement Channels",
        "",
        "| Channel | Numerator | Denominator | Boundary/excitation | Units |",
        "|---|---|---|---|---|",
        "| Ch1 dome-only | `F1` | `a1` | fixed base, tray absent, force on m1 | kg |",
        "| Ch2 coupled primary | `F1` | `a1` | fixed base, tray attached, force on m1 | kg |",
        "| Ch3 coupled tray | `F2` | `a2` | fixed base, tray attached, force on m2 | kg |",
        "| Ch4 standalone tray | `a_tray` | `a_base` | fixed-base shaker-table tray-only test | dimensionless |",
        "| Ch5 flight-like | tray acceleration PSD response | force PSD on m1 | unknown force PSD on m1; QOI `3 * GRMS` | g |",
        "",
        "## Synthetic Data and Error Evidence",
        "",
        "Clean truth vs observed synthetic data is shown separately from absolute injected GP discrepancy, iid sensor noise, and total error. The updated observation/discrepancy assumptions are intentionally larger and local-magnitude-scaled so the curves are not visually line-on-line. The normalized error plot is only a diagnostic because the denominator can amplify notches.",
        "",
        f"Dataset count: this run generates one synthetic dataset: `{repl['frequency_domain_realizations_per_channel']}` realization for each FRF/transfer channel, `{repl['flight_like_response_psd_realizations']}` flight-like response PSD realization, and `{repl['flight_time_history_realizations']}` secondary time-history realization; flight-to-flight variability is not modeled. Repeated-flight scatter is a missing capability, not a hidden feature.",
        "",
        "The time-domain flight trace is retained only as a secondary synthetic realization for intuition and plotting. The fitted flight-like likelihood and the QOI are PSD-domain quantities, so the time trace is not the acceptance metric.",
        "",
        fig("channel_truth_vs_observed.png"),
        "",
        fig("channel_absolute_error.png"),
        "",
        fig("channel_normalized_error_diagnostic.png"),
        "",
        fig("flight_truth_vs_observed.png"),
        "",
        "## GP Discrepancy",
        "",
        "Covariance definition for FRF discrepancy: `k(f, f') = sigma_d(f) sigma_d(f') exp(-0.5 ((ln f - ln f') / ell_d)^2)`. Real and imaginary parts are independent GP draws for this toy run. Response PSD discrepancy is modeled in log PSD with the same log-frequency idea.",
        "",
        "StatFEM-style noise/discrepancy model: generated model discrepancy and sensor noise are kept separate in `fresh_2dof_dataset.json` (`gp_discrepancy`, `iid_sensor_noise`, and `total_error`). The likelihood then uses the sum of discrepancy covariance and sensor-noise covariance. It does not infer a realized discrepancy field or its hyperparameters; those are fixed assumptions in this trial.",
        "",
        fig("gp_discrepancy_samples.png"),
        "",
        "## Bayes Rule Update",
        "",
        "Central methodology: the prior has explicit variance assumptions and the likelihood uses the whole frequency-domain data, not only resonance peak locations or magnitudes.",
        "",
        f"Prior variance assumptions: stiffness uses `log(k/k_nom) ~ Normal(0, 0.18^2)`, so natural frequency has implied `sigma_log(f/f_nom)=0.09` because `f` is proportional to `sqrt(k)`. The untruncated 95% natural-frequency factor is approximately `[{freq95[0]:.3f}, {freq95[1]:.3f}]`, centered at 110 Hz for the dome and 75 Hz for the tray. Damping uses `log(zeta/zeta_nom) ~ Normal(0, 0.35^2)`, giving an untruncated 95% damping multiplier of approximately `[{damp95[0]:.3f}, {damp95[1]:.3f}]`, centered at zeta1={Constants().dome_nominal_zeta:.3f} and zeta2={Constants().tray_nominal_zeta:.3f}.",
        "",
        "Likelihood formulation: Ch1-Ch4 use all complex FRF/transfer values at 120 log-spaced frequencies. For each channel, residuals are `observed complex FRF - model complex FRF`; real and imaginary residual vectors are evaluated independently with covariance `K_discrepancy + diag(sensor_noise^2)`. The flight-like response uses all 181 log response-PSD frequency points with covariance `sigma_log_discrepancy^2 R_logfreq + sigma_log_sensor^2 I`. Peak and notch locations are used only for reference checks and plots, not as likelihood summary statistics.",
        "",
        f"Method status: realized discrepancy fields and noise/discrepancy hyperparameters are not inferred in this toy. We would like to infer them in the longer-term StatFEM version, but that needs a hierarchical discrepancy/noise model and preferably repeated tests/flights so structural parameters, sensor noise, flight-to-flight variability, and model discrepancy are not hopelessly confounded. Current desired next step: {likelihood_form['desired_next_step']}",
        "",
        "Plain-language model-family caveat: the synthetic data were generated by the same 2DOF equations used in fitting, just with shifted stiffness, damping, and forcing parameters. That means the posterior can fit by moving those parameters. A real FEM may be wrong in ways that no parameter shift can represent, such as missing modes, nonlinear joints, slosh, preload, or incorrect boundary conditions.",
        "",
        f"Bayes rule in action: the parameter plot shows analytic prior density, a high-sample MC prior histogram diagnostic (`n={PRIOR_DENSITY_MC_SAMPLES:,}`), a one-dimensional conditional likelihood slice, and posterior density for the two natural frequencies and two damping ratios. The likelihood slices hold all other transformed variables at the retained posterior sample with largest log posterior; they are visual diagnostics, not full marginal likelihoods.",
        "",
        "Prior visualization policy: the smooth blue curve is the analytic prior density and is the primary prior representation. The light-blue MC prior histogram is shown only as a sampling diagnostic and is labeled separately so histogram roughness is not mistaken for mathematical prior structure. Posterior curves are kernel-density estimates from retained samples.",
        "",
        f"Likelihood diagnostic: log likelihood at the prior center is `{like['log_likelihood_at_prior_center']:.3g}`, at synthetic truth `{like['log_likelihood_at_truth']:.3g}`, and at the retained posterior mode `{like['log_likelihood_at_retained_posterior_mode']:.3g}`.",
        "",
        fig("bayes_parameter_update.png"),
        "",
        "| Parameter | Prior median | Posterior median | Posterior 95% CI | Synthetic truth | Units |",
        "|---|---:|---:|---:|---:|---|",
        param_table,
        "",
        ci_miss_text,
        "",
        fig("parameter_posterior_samples.png"),
        "",
        f"Prior predictive versus data: the base-driven standalone tray transfer, coupled tray drive-point channel, flight-like tray response PSD, and latent force PSD are shown with prior and posterior predictive bands. These are not analytic prior densities; they are smoothed MC predictive summaries. The prior predictive bands use `{PRIOR_PREDICTIVE_MC_SAMPLES}` prior draws, and plotted pointwise quantile summaries are smoothed over frequency with Gaussian sigma `{PREDICTIVE_BAND_SMOOTHING_SIGMA_POINTS}` grid points so resonance-ordering wiggles are not mistaken for prior structure. The force PSD is latent in this toy; the observed flight-like data are the tray response PSD, not a direct force measurement.",
        "",
        fig("prior_predictive_vs_data.png"),
        "",
        "## Whole FRF vs Peak-Feature Likelihood Comparison",
        "",
        "This side-by-side comparison asks what changes if the likelihood uses only selected peak/notch frequency and magnitude features instead of the whole complex FRFs and whole response PSD. The peak-feature likelihood uses one dominant feature from each frequency channel plus the response-PSD peak. It treats feature residuals as independent with broad log-frequency and log-amplitude uncertainty. This is a deliberately lossy comparison artifact, not a recommended replacement for the whole-curve StatFEM likelihood.",
        "",
        f"QOI comparison: full FRF/PSD likelihood mean `{full_qoi['mean']:.5g} g`, 95% interval `[{full_qoi['q025']:.5g}, {full_qoi['q975']:.5g}] g`; peak-feature likelihood mean `{peak_qoi['mean']:.5g} g`, 95% interval `[{peak_qoi['q025']:.5g}, {peak_qoi['q975']:.5g}] g`. Peak-feature QOI 95% width divided by full-curve width is `{peak_width_ratio:.3g}`.",
        "",
        "Feature likelihood assumptions and observed feature values are stored in `peak_feature_likelihood_summary.json`.",
        "",
        fig("full_vs_peak_feature_likelihood_comparison.png"),
        "",
        "## Peak/Notch Feature Mapping Benchmark",
        "",
        "A peak or notch is not assumed to equal a natural frequency. The feature likelihood compares an observed transfer-function feature with the predicted transfer-function feature from each candidate parameter set. It is therefore benchmarked against `feature(theta)`, not directly compared with the true natural frequency.",
        "",
        "In a clean one-DOF-like channel, the feature can sit very near the natural frequency but still depends on the exact quantity, damping, and boundary condition. In coupled channels, notches and response-PSD peaks are mixed features: they can depend on dome frequency, tray frequency, damping, and forcing assumptions at the same time.",
        "",
        feature_table,
        "",
        "The sensitivity matrix below reports log-log slopes of each selected feature with respect to the inferred variables at the synthetic truth. Ch1 and Ch4 are close to direct structural features. Ch2 and Ch3 mix dome and tray frequency information. Ch5 is a response/forcing feature, so its amplitude is strongly confounded with the assumed force spectrum.",
        "",
        fig("peak_feature_mapping_benchmark.png"),
        "",
        fig("peak_feature_sensitivity_matrix.png"),
        "",
        "## Posterior Fit and Diagnostics",
        "",
        f"Sampler: {sampler['method']}; steps `{sampler['steps']}`, burn `{sampler['burn']}`, thin `{sampler['thin']}`, retained samples `{sampler['retained_samples']}`, acceptance rate `{sampler['acceptance_rate']:.3f}`.",
        "",
        "The older posterior-fit plot uses a posterior-mean prediction as a summary line. The posterior predictive figure below shows the distribution across retained samples; that is the correct object to inspect when asking how much spectral uncertainty remains.",
        "",
        fig("posterior_fit_and_residuals.png"),
        "",
        fig("posterior_predictive_spectra.png"),
        "",
        "Why the fit can move far from nominal: the synthetic truth is inside the same parametric model family used by the likelihood, and the priors are broad enough that the many FRF/PSD frequency points dominate the nominal prior center. This is useful for checking Bayes-rule plumbing, but it is optimistic compared with a real FEM/model-form misspecification problem.",
        "",
        fig("sampler_diagnostics.png"),
        "",
        "## QOI Summary",
        "",
        f"QOI posterior samples: definition `{qoi['definition']}`, mean `{qoi['mean']:.6g} g`, 5-95% interval `[{qoi['q05']:.6g}, {qoi['q95']:.6g}] g`, truth `{qoi['truth']:.6g} g`, mean bias `{qoi['mean_bias']:.6g} g`, fraction above truth `{qoi['fraction_above_truth']:.3f}`.",
        "",
        fig("qoi_samples.png"),
        "",
        "## Sensitivity to Assumptions",
        "",
        "Sensitivity meaning: the synthetic-data error sensitivity asks how large the injected measurement/model-error terms become if the assumed noise or discrepancy scale changes. It does not rerun inference. The QOI sensitivity keeps the retained posterior samples fixed and re-computes `3 * GRMS` under damping and forcing-band variants. It is a quick fragility check, not a full posterior refit for every scenario.",
        "",
        "No pass/fail decision threshold is asserted in this synthetic run; a real threshold is a human engineering decision.",
        "",
        fig("sensitivity_qoi.png"),
        "",
        fig("sensitivity_synthetic_error.png"),
        "",
        "## Reference and Standards Comparison",
        "",
        "NASA-HDBK-7004C comparison: the packet now includes NASA-HDBK-7004C Figure 9 normalized source/load apparent-mass benchmark values and fresh source/load-style apparent-mass curves. Ch1-Ch3 remain reciprocal inertance and are labeled separately.",
        "",
        "The previous green pass/fail bar chart was only a checker scoreboard. It has been replaced by a value table so a reviewer can see the actual computed numbers, the reference expectations, and the engineering meaning.",
        "",
        "vibrationdata.com comparison: used as a classical SDOF/2DOF sanity-check family for transmissibility, resonance location, rolloff, and distinct drive-point behavior.",
        "",
        f"Reference metrics: Ch4 low-frequency median `{ref_metrics['ch4_low_frequency_median']:.4g}`, Ch4 high-frequency median `{ref_metrics['ch4_high_frequency_median']:.4g}`, Ch4 peak `{ref_metrics['ch4_peak_frequency_hz']:.3f} Hz` vs tray truth `{ref_metrics['tray_true_frequency_hz']:.3f} Hz`, Ch1 notch `{ref_metrics['ch1_notch_frequency_hz']:.3f} Hz` vs dome truth `{ref_metrics['dome_true_frequency_hz']:.3f} Hz`, Ch2/Ch3 relative L2 `{ref_metrics['ch2_ch3_relative_l2']:.4f}`, NASA-HDBK-7004C Figure 9 load `M(0.62)={ref_metrics['nasa_7004c_load_at_r_0p62']:.3f}`, load `M(1)={ref_metrics['nasa_7004c_load_at_r_1']:.3f}`, source `M(1)={ref_metrics['nasa_7004c_source_at_r_1']:.4f}`.",
        "",
        fig("reference_standards_comparison_cards.png"),
        "",
        fig("nasa_7004c_apparent_mass_benchmark.png"),
        "",
        "## Checker Status",
        "",
        f"Fresh checker status: **{checker_text}**.",
        "",
        f"Image legibility QA: **{image_qc_text}**. Strict text-heavy figures checked: `{image_qc_strict}`. Full details are in `image_legibility_report.json`.",
        "",
        "| Acceptance condition | Result |",
        "|---|---:|",
        checks_table,
        "",
        "Checker-backed acceptance conditions include required report/figures, numerical assumptions, reference comparison, sensitivity artifact, Ch2/Ch3 non-duplication, frequency-axis metadata, QOI samples, checker status, and limitations.",
        "",
        "## Fresh-Agent Comparison",
        "",
        "This comparison was generated after fresh outputs were written.",
        "",
        "**Matched:** " + "; ".join(comparison["matched"]) + ".",
        "",
        "**Differed:** " + "; ".join(comparison["differed"]) + ".",
        "",
        "**Improvements:** " + "; ".join(comparison["improvements"]) + ".",
        "",
        "**Unresolved:** " + "; ".join(comparison["unresolved"]) + ".",
        "",
        "**Gates that prevented mistakes:** " + "; ".join(comparison["gates_that_prevented_mistakes"]) + ".",
        "",
        "## Limitations",
        "",
        "- Synthetic-only data; no real tank, tray, dome, shaker, or flight data are used.",
        "- Only one synthetic realization is generated per measurement class; flight-to-flight variability and repeated-test variability are not modeled.",
        "- The two-DOF model is linear, fixed-base, and low order; no slosh, nonlinear joints, preload, build variability, or FEM modal reduction is represented.",
        "- The larger GP/log-PSD discrepancy assumptions are literature-informed but not calibrated to a real tank/tray dataset.",
        "- Random-walk MH is auditable but not a production-grade sampler; convergence is not proven by trace plots.",
        "- Sensitivity is first-pass and does not refit the posterior for all error-model scenarios.",
        "- Reference/standards checks are shape, convention, and benchmark-value checks, not qualification or NASA compliance evidence.",
        "",
        "## Human Reflection Prompts",
        "",
        "- Is `3 * GRMS` tray acceleration the right QOI, or should stress, relative displacement, fatigue damage, or interface force be used?",
        "- Would a real apparent-mass test use the same numerator/denominator and source/load boundary conditions?",
        "- How many repeated flights/tests are needed before flight-to-flight variability can be separated from sensor noise and model discrepancy?",
        "- Which uncertainty source should be reduced before an autonomous experiment loop is trusted?",
        "- What threshold would make the flight-like QOI a decision rather than a plot?",
    ]
    (OUT_DIR / "fresh_2dof_statfem_packet.md").write_text("\n".join(lines) + "\n")


def main() -> int:
    prepare_output_dirs()
    c = Constants()
    data = generate_synthetic(c)
    save_dataset(data)
    write_assumptions_json(data)
    plot_model_schematic(data)
    plot_workflow()
    plot_statfem_likelihood_graphical_model()
    plot_assumptions(data)
    plot_channels(data)
    plot_errors(data)
    plot_gp_samples(data)
    plot_flight_data(data)
    mcmc = run_mcmc(data)
    posterior = save_posterior(mcmc, data)
    plot_posterior_fit(data, mcmc)
    plot_sampler(mcmc)
    plot_qoi(data, mcmc)
    bayes = plot_bayes_parameter_update(data, mcmc)
    plot_parameter_posterior_samples(data, mcmc, bayes)
    plot_prior_predictive_vs_data(data, mcmc)
    plot_posterior_predictive_spectra(data, mcmc)
    feature_mcmc = run_mcmc(data, likelihood_kind="peak_feature", seed_offset=311, n_steps=3600, burn=900, thin=5)
    peak_comp = save_peak_feature_likelihood_comparison(data, mcmc, feature_mcmc)
    plot_peak_feature_likelihood_comparison(data, mcmc, feature_mcmc, peak_comp)
    feature_benchmark = save_peak_feature_mapping_benchmark(data)
    plot_peak_feature_mapping_benchmark(data, feature_benchmark)
    plot_peak_feature_sensitivity_matrix(feature_benchmark)
    sens = run_sensitivity(data, mcmc)
    plot_sensitivity(sens)
    ref = reference_comparison(data)
    plot_reference_comparison(ref)
    plot_nasa_7004c_apparent_mass(data)
    write_image_legibility_report()
    comparison = fresh_prior_comparison()
    write_manifest(posterior, ref, sens)
    write_report(posterior, bayes, peak_comp, feature_benchmark, sens, ref, comparison, checker=None)
    checker = run_acceptance_checks()
    write_report(posterior, bayes, peak_comp, feature_benchmark, sens, ref, comparison, checker=checker)
    checker = run_acceptance_checks()
    print(json.dumps({"report": str(OUT_DIR / "fresh_2dof_statfem_packet.md"), "checker": checker}, indent=2))
    return 0 if checker["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
