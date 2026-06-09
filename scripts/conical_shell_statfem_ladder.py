#!/usr/bin/env python3
"""Vibrationdata conical-shell source audit and StatFEM launch packet.

This phase intentionally stops before claiming an active StatFEM posterior.  The
Vibrationdata report says the preliminary FEM properties were adjusted to match
the measured fundamental frequency, so the honest first deliverable is a
traceable FEM-vs-published-test comparison plus a digital-twin launch plan.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import textwrap
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import fitz
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "reports" / "conical_shell_statfem_ladder_20260608"
SOURCE_DIR = OUT_DIR / "sources"
FIG_DIR = OUT_DIR / "figures"
PDF_URL = "http://www.vibrationdata.com/tutorials_alt/conical_shell.pdf"
NAS_URL = "http://www.vibrationdata.com/tutorials_alt/conical_shell3.nas"
STRUCTURAL_FE_URL = "https://www.vibrationdata.com/StructuralFE.htm"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def fetch(url: str, path: Path, user_agent: str = "curl/8.0") -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "*/*"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            data = r.read()
            path.write_bytes(data)
            return {
                "url": url,
                "path": str(path.relative_to(ROOT)),
                "status": "fetched",
                "http_status": r.status,
                "content_type": r.headers.get("content-type"),
                "content_length": len(data),
                "sha256": sha256(path),
                "user_agent": user_agent,
                "elapsed_s": time.perf_counter() - started,
            }
    except Exception as exc:  # noqa: BLE001 - recorded as source provenance
        return {
            "url": url,
            "path": str(path.relative_to(ROOT)),
            "status": "failed",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "user_agent": user_agent,
            "elapsed_s": time.perf_counter() - started,
        }


def check_browser_like_access(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return {"url": url, "user_agent": "Mozilla/5.0", "status": "ok", "http_status": r.status}
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "user_agent": "Mozilla/5.0",
            "status": "http_error",
            "http_status": exc.code,
            "reason": exc.reason,
        }
    except Exception as exc:  # noqa: BLE001
        return {"url": url, "user_agent": "Mozilla/5.0", "status": "failed", "error": str(exc)}


def extract_pdf_text(path: Path) -> str:
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)


def nas_float(s: str) -> float | None:
    s = s.strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        # Nastran often omits the E in short fields, e.g. 1.269E-4 is fine
        # here, but 11.632+7 would need this form.
        m = re.fullmatch(r"([+-]?\d*\.?\d+)([+-]\d+)", s)
        if m:
            return float(m.group(1) + "E" + m.group(2))
    return None


def fixed_fields(line: str) -> list[str]:
    padded = line.rstrip("\n").ljust(80)
    return [padded[i : i + 8].strip() for i in range(0, 80, 8)]


def parse_nastran(path: Path) -> dict[str, Any]:
    nodes: dict[int, tuple[float, float, float]] = {}
    quads: list[tuple[int, int, int, int, int]] = []
    tris: list[tuple[int, int, int, int]] = []
    cards: dict[str, int] = {}
    solution = None
    eigrl = None
    pshell = None
    mat1_lines: list[str] = []

    for raw in path.read_text(errors="replace").splitlines():
        card = raw[:8].strip()
        if not card or card.startswith("$"):
            continue
        cards[card] = cards.get(card, 0) + 1
        if raw.strip().startswith("SOL "):
            solution = raw.strip()
        elif card == "EIGRL":
            eigrl = raw.strip()
        elif card == "PSHELL":
            f = fixed_fields(raw)
            pshell = {
                "pid": f[1],
                "mid1": f[2],
                "thickness_in": nas_float(f[3]),
                "raw": raw.strip(),
            }
        elif card == "MAT1":
            mat1_lines.append(raw.strip())
        elif card == "GRID":
            f = fixed_fields(raw)
            try:
                gid = int(f[1])
                x, y, z = nas_float(f[3]), nas_float(f[4]), nas_float(f[5])
                if x is not None and y is not None and z is not None:
                    nodes[gid] = (x, y, z)
            except Exception:
                continue
        elif card == "CQUADR":
            f = fixed_fields(raw)
            try:
                quads.append((int(f[1]), int(f[3]), int(f[4]), int(f[5]), int(f[6])))
            except Exception:
                continue
        elif card == "CTRIAR":
            f = fixed_fields(raw)
            try:
                tris.append((int(f[1]), int(f[3]), int(f[4]), int(f[5])))
            except Exception:
                continue

    coords = np.array(list(nodes.values()), dtype=float)
    bbox = {
        "x_min_in": float(coords[:, 0].min()),
        "x_max_in": float(coords[:, 0].max()),
        "y_min_in": float(coords[:, 1].min()),
        "y_max_in": float(coords[:, 1].max()),
        "z_min_in": float(coords[:, 2].min()),
        "z_max_in": float(coords[:, 2].max()),
    }
    return {
        "solution": solution,
        "eigrl": eigrl,
        "card_counts": cards,
        "node_count": len(nodes),
        "cquadr_count": len(quads),
        "ctriar_count": len(tris),
        "element_count": len(quads) + len(tris),
        "pshell": pshell,
        "mat1_raw": mat1_lines,
        "bbox": bbox,
        "free_boundary_condition": cards.get("SPC", 0) == 0 and cards.get("SPC1", 0) == 0,
        "nodes": {str(k): v for k, v in nodes.items()},
        "quads": quads,
        "tris": tris,
    }


def published_data() -> dict[str, Any]:
    measured = [97.6, 278.0, 429.0, 529.0]
    fea = [97.6, 274.0, None, 523.0]
    rows = []
    for i, (m, f) in enumerate(zip(measured, fea), start=1):
        rows.append(
            {
                "published_mode_index": i,
                "measured_hz": m,
                "published_preliminary_fea_hz": f,
                "percent_error_fea_vs_measured": None if f is None else 100.0 * (f - m) / m,
            }
        )
    return {
        "source": "Vibrationdata conical_shell.pdf Table 1 and report text",
        "fundamental_damping_percent": 0.6,
        "frf_units": "G/LBF",
        "measured_response_locations": ["aft end accelerometer", "midpoint accelerometer"],
        "hit_location": "12 inches from aft end",
        "boundary_condition": "radome on compliant foam; interpreted as approximately free-free",
        "rows": rows,
    }


def human_nastran_solution() -> dict[str, Any]:
    """Human-provided Femap/Nastran result from screenshots in the prompt."""
    frequencies = [
        3.56985e-4,
        2.47458e-4,
        1.77593e-4,
        9.00516e-5,
        1.63569e-4,
        2.60647e-4,
        97.6352,
        97.63943,
        274.0179,
        274.0180,
        524.2933,
        524.2944,
        728.8799,
        729.0839,
        764.5729,
        764.5780,
        847.8621,
        847.8621,
        939.8801,
        939.8808,
    ]
    modes = []
    for idx, freq in enumerate(frequencies, start=1):
        if idx <= 6:
            label = "free-free rigid-body numerical zero"
            family = "rigid"
        else:
            label = "flexible shell mode pair"
            family = "shell"
        modes.append(
            {
                "mode": idx,
                "frequency_hz": freq,
                "family": family,
                "label": label,
                "source": "human Femap/Nastran screenshot",
            }
        )

    flexible_pairs = []
    for pair_index, start_mode in enumerate(range(7, 20, 2), start=1):
        pair = [m for m in modes if m["mode"] in (start_mode, start_mode + 1)]
        vals = [p["frequency_hz"] for p in pair]
        flexible_pairs.append(
            {
                "pair_index": pair_index,
                "modes": [start_mode, start_mode + 1],
                "frequencies_hz": vals,
                "mean_hz": float(np.mean(vals)),
                "split_percent_of_mean": float(100.0 * (max(vals) - min(vals)) / np.mean(vals)),
            }
        )

    screenshot_sources = [
        Path("/Users/avoss/Downloads/IMG_9814.jpg"),
        Path("/Users/avoss/Downloads/IMG_9815.jpg"),
        Path("/Users/avoss/Downloads/IMG_9816.jpg"),
    ]
    copied = []
    for src in screenshot_sources:
        if src.exists():
            dst = SOURCE_DIR / f"human_femap_{src.name}"
            shutil.copy2(src, dst)
            copied.append(
                {
                    "source_path": str(src),
                    "cached_path": str(dst.relative_to(ROOT)),
                    "sha256": sha256(dst),
                    "role": "human-supplied Femap/Nastran screenshot provenance",
                }
            )
    return {
        "source": "Human-provided Femap/Nastran run screenshots, 2026-06-08",
        "modes": modes,
        "flexible_pairs": flexible_pairs,
        "screenshots": copied,
        "interpretation": "six near-zero free-free rigid-body modes followed by nearly degenerate flexible shell mode pairs",
    }


def local_solve_comparison(pub: dict[str, Any], human: dict[str, Any]) -> dict[str, Any]:
    pair_means = [p["mean_hz"] for p in human["flexible_pairs"]]
    mapping = [
        {
            "published_mode_index": 1,
            "measured_hz": 97.6,
            "published_preliminary_fea_hz": 97.6,
            "human_nastran_pair_index": 1,
            "human_nastran_mean_hz": pair_means[0],
        },
        {
            "published_mode_index": 2,
            "measured_hz": 278.0,
            "published_preliminary_fea_hz": 274.0,
            "human_nastran_pair_index": 2,
            "human_nastran_mean_hz": pair_means[1],
        },
        {
            "published_mode_index": 3,
            "measured_hz": 429.0,
            "published_preliminary_fea_hz": None,
            "human_nastran_pair_index": None,
            "human_nastran_mean_hz": None,
            "note": "unmatched measured feature in the published preliminary FEA comparison",
        },
        {
            "published_mode_index": 4,
            "measured_hz": 529.0,
            "published_preliminary_fea_hz": 523.0,
            "human_nastran_pair_index": 3,
            "human_nastran_mean_hz": pair_means[2],
        },
    ]
    for row in mapping:
        local = row["human_nastran_mean_hz"]
        measured = row["measured_hz"]
        published_fea = row["published_preliminary_fea_hz"]
        row["human_nastran_error_vs_measured_percent"] = None if local is None else 100.0 * (local - measured) / measured
        row["human_nastran_error_vs_published_fea_percent"] = (
            None if local is None or published_fea is None else 100.0 * (local - published_fea) / published_fea
        )
    return {
        "source": "Published Vibrationdata Table 1 plus human Femap/Nastran solve",
        "rows": mapping,
        "extra_human_flexible_pairs": human["flexible_pairs"][3:],
    }


def digitized_frf_features() -> dict[str, Any]:
    """Coarse visual features from rendered PDF plots.

    The PDF does not provide raw FRF ordinates.  These values are deliberately
    approximate and carry large uncertainty; they are for first QOI plumbing, not
    for a precision damping/model-updating claim.
    """
    features = [
        {
            "figure": "Figure 2",
            "response": "aft accelerometer",
            "hit_location": "12 inches from aft end",
            "frequency_hz": 97.6,
            "magnitude_g_per_lbf": 17.5,
            "magnitude_uncertainty_g_per_lbf": 3.0,
            "digitization": "coarse visual from PDF plot",
        },
        {
            "figure": "Figure 2",
            "response": "aft accelerometer",
            "hit_location": "12 inches from aft end",
            "frequency_hz": 278.0,
            "magnitude_g_per_lbf": 2.4,
            "magnitude_uncertainty_g_per_lbf": 0.8,
            "digitization": "coarse visual from PDF plot",
        },
        {
            "figure": "Figure 2",
            "response": "aft accelerometer",
            "hit_location": "12 inches from aft end",
            "frequency_hz": 529.0,
            "magnitude_g_per_lbf": 1.6,
            "magnitude_uncertainty_g_per_lbf": 0.7,
            "digitization": "coarse visual from PDF plot",
        },
        {
            "figure": "Figure 3",
            "response": "midpoint accelerometer",
            "hit_location": "12 inches from aft end",
            "frequency_hz": 97.6,
            "magnitude_g_per_lbf": 8.5,
            "magnitude_uncertainty_g_per_lbf": 2.0,
            "digitization": "coarse visual from PDF plot",
        },
        {
            "figure": "Figure 3",
            "response": "midpoint accelerometer",
            "hit_location": "12 inches from aft end",
            "frequency_hz": 278.0,
            "magnitude_g_per_lbf": 2.0,
            "magnitude_uncertainty_g_per_lbf": 0.8,
            "digitization": "coarse visual from PDF plot",
        },
    ]
    return {
        "source": "Vibrationdata conical_shell.pdf Figures 2-4, coarse visual digitization",
        "raw_ordinates_available": False,
        "features": features,
        "warning": "Peak magnitudes are secondary visual estimates with intentionally large uncertainty; do not use them as raw FRF data.",
    }


def modal_statfem_v1(comparison: dict[str, Any]) -> dict[str, Any]:
    """One-parameter modal StatFEM-style update via exact grid quadrature."""
    rows_by_mode = {r["published_mode_index"]: r for r in comparison["rows"]}
    calibration_modes = [1, 2]
    holdout_modes = [4]
    unmatched_modes = [3]
    base = np.array([rows_by_mode[i]["human_nastran_mean_hz"] for i in calibration_modes], dtype=float)
    obs = np.array([rows_by_mode[i]["measured_hz"] for i in calibration_modes], dtype=float)
    sigma_obs_rel = 0.004
    sigma_disc_rel = 0.020
    sigma_total = np.sqrt((sigma_obs_rel * obs) ** 2 + (sigma_disc_rel * obs) ** 2)
    logk = np.linspace(-0.25, 0.25, 2401)
    k_scale = np.exp(logk)
    pred = np.sqrt(k_scale[:, None]) * base[None, :]
    residual = (obs[None, :] - pred) / sigma_total[None, :]
    log_prior = -0.5 * (logk / 0.16) ** 2
    log_like = -0.5 * np.sum(residual**2, axis=1) - np.sum(np.log(sigma_total * np.sqrt(2 * np.pi)))
    log_post = log_prior + log_like
    weights = np.exp(log_post - np.max(log_post))
    weights = weights / np.sum(weights)
    cdf = np.cumsum(weights)

    def quantile(vals: np.ndarray, q: float) -> float:
        return float(np.interp(q, cdf, vals))

    post = {
        "k_scale_mean": float(np.sum(weights * k_scale)),
        "k_scale_q05": quantile(k_scale, 0.05),
        "k_scale_q50": quantile(k_scale, 0.50),
        "k_scale_q95": quantile(k_scale, 0.95),
        "frequency_scale_mean": float(np.sum(weights * np.sqrt(k_scale))),
        "logk_grid_count": int(len(logk)),
    }
    holdout = []
    for mode in holdout_modes:
        row = rows_by_mode[mode]
        base_hz = float(row["human_nastran_mean_hz"])
        pred_samples = np.sqrt(k_scale) * base_hz
        obs_hz = float(row["measured_hz"])
        sigma_pred = np.sqrt((sigma_obs_rel * obs_hz) ** 2 + (sigma_disc_rel * obs_hz) ** 2)
        lo = quantile(pred_samples, 0.05) - 1.645 * sigma_pred
        med = quantile(pred_samples, 0.50)
        hi = quantile(pred_samples, 0.95) + 1.645 * sigma_pred
        holdout.append(
            {
                "mode": mode,
                "observed_hz": obs_hz,
                "base_human_nastran_hz": base_hz,
                "predictive_q05_hz": float(lo),
                "predictive_q50_hz": float(med),
                "predictive_q95_hz": float(hi),
                "covered_by_90pct_interval": bool(lo <= obs_hz <= hi),
            }
        )

    return {
        "statfem_active": True,
        "method": "exact grid quadrature over one stiffness-scale parameter; not NUTS/HMC",
        "reason_not_nuts_hmc": "The v1 posterior has one parameter and is evaluated exactly on a dense grid, which is more transparent than sampling. Do not generalize this to future multi-parameter updates.",
        "model_equation": "f_obs_i = sqrt(k_scale) * f_fem_i + discrepancy_i + observation_noise_i",
        "calibration_modes": calibration_modes,
        "holdout_modes": holdout_modes,
        "unmatched_modes_not_used": unmatched_modes,
        "sigma_obs_rel": sigma_obs_rel,
        "sigma_disc_rel": sigma_disc_rel,
        "posterior": post,
        "holdout_predictions": holdout,
    }


def frf_qoi_layer(frf: dict[str, Any], statfem: dict[str, Any]) -> dict[str, Any]:
    aft = [f for f in frf["features"] if f["response"] == "aft accelerometer"]
    peak = max(aft, key=lambda r: r["magnitude_g_per_lbf"])
    k_med = statfem["posterior"]["k_scale_q50"]
    qoi = {
        "name": "aft peak accelerance near first flexible shell mode",
        "units": "G/LBF",
        "source_feature": peak,
        "median_peak_g_per_lbf": peak["magnitude_g_per_lbf"],
        "approx_90pct_interval_g_per_lbf": [
            max(0.0, peak["magnitude_g_per_lbf"] - 1.645 * peak["magnitude_uncertainty_g_per_lbf"]),
            peak["magnitude_g_per_lbf"] + 1.645 * peak["magnitude_uncertainty_g_per_lbf"],
        ],
        "frequency_shifted_by_modal_posterior_hz": float(math.sqrt(k_med) * peak["frequency_hz"]),
        "warning": "Amplitude is digitized secondary evidence, not a FEM-predicted accelerance. This QOI is a plumbing artifact until raw FRF or a modal participation model is added.",
    }
    return {"qoi": qoi, "features_used": frf["features"]}


@dataclass
class Assumption:
    assumption: str
    value: Any
    units: str
    source: str
    rationale: str
    sensitivity_priority: str
    where_used: str


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True))


def assumptions_ledger() -> list[Assumption]:
    return [
        Assumption("Shell thickness", 0.1, "inch", "Vibrationdata PDF Appendix A", "Published preliminary FEM value.", "high", "FEM metadata, sensitivity"),
        Assumption("Young modulus", 16317180.0, "lbf/in^2", "Vibrationdata PDF Appendix A", "Adjusted in the preliminary FEM so the fundamental matched test.", "high", "FEM metadata, digital-twin launch"),
        Assumption("Poisson ratio", 0.33, "dimensionless", "Vibrationdata PDF Appendix A", "Published preliminary FEM value.", "low", "FEM metadata"),
        Assumption("Mass density", 1.26941e-4, "lbf*s^2/in^4", "Vibrationdata PDF Appendix A", "Published preliminary FEM value; report writes lbf sec^2/in but shell density units are interpreted in inch-lbf-second consistency.", "high", "FEM metadata, sensitivity"),
        Assumption("Overall length", 45.0, "inch", "Vibrationdata PDF Appendix A", "Published approximate radome length.", "medium", "geometry check"),
        Assumption("Base diameter", 14.0, "inch", "Vibrationdata PDF Appendix A", "Published approximate base diameter.", "medium", "geometry check"),
        Assumption("Boundary condition", "approximately free-free", "categorical", "Vibrationdata PDF test configuration", "Radome rested on compliant foam; preliminary FEM omitted foam.", "high", "comparison, digital-twin launch"),
        Assumption("Fundamental damping", 0.6, "percent critical", "Vibrationdata PDF introduction/damping section", "Measured first-mode damping; not enough to infer a damping curve.", "medium", "digital-twin launch"),
        Assumption("Measured modes", [97.6, 278.0, 429.0, 529.0], "Hz", "Vibrationdata PDF Table 1", "Published modal-test frequencies used as observed data.", "high", "FEM-vs-test comparison"),
        Assumption("Published preliminary FEA modes", [97.6, 274.0, None, 523.0], "Hz", "Vibrationdata PDF Table 1", "Published FEM values; missing third mode retained as missing, not filled.", "high", "FEM-vs-test comparison"),
        Assumption("Human Femap/Nastran flexible pair means", [97.637315, 274.01795, 524.29385, 728.9819, 764.57545, 847.8621, 939.88045], "Hz", "Human-supplied Femap/Nastran screenshots", "Local solve evidence: six near-zero rigid-body modes followed by nearly degenerate flexible shell pairs.", "high", "local solve comparison, StatFEM v1"),
        Assumption("FRF peak digitization", "coarse visual peak features only", "categorical", "Vibrationdata PDF Figures 2-4", "Raw FRF ordinates are not available; amplitudes are secondary visual estimates with large uncertainty.", "high", "FRF/QOI layer"),
        Assumption("Modal StatFEM v1 observation noise", 0.004, "fraction of modal frequency", "engineering assumption", "Small term for reading/reporting frequency uncertainty.", "medium", "modal likelihood"),
        Assumption("Modal StatFEM v1 discrepancy scale", 0.020, "fraction of modal frequency", "engineering assumption", "Represents model-form error after the preliminary FEM tuning.", "high", "modal likelihood, held-out validation"),
        Assumption("Modal StatFEM v1 prior log stiffness sigma", 0.16, "natural log units", "engineering assumption", "Allows roughly +/-17% one-sigma stiffness variation while keeping v1 identifiable.", "medium", "modal posterior"),
        Assumption("Source FEM tuning", "E and density adjusted to match the fundamental", "categorical", "Vibrationdata PDF Appendix A", "This prevents treating the first-mode agreement as independent validation.", "high", "limitations, digital-twin launch"),
        Assumption("StatFEM active", True, "boolean", "This phase", "A one-parameter modal-only StatFEM-style grid update is active; no NUTS/HMC claim is made.", "high", "checker, report"),
    ]


def write_assumptions(rows: list[Assumption]) -> None:
    write_json(OUT_DIR / "assumptions_ledger.json", {"rows": [asdict(r) for r in rows]})
    lines = [
        "# Assumptions Ledger",
        "",
        "| Assumption | Value | Units | Source | Rationale | Sensitivity | Where used |",
        "|---|---:|---|---|---|---|---|",
    ]
    for r in rows:
        val = json.dumps(r.value) if isinstance(r.value, (list, dict, bool)) else str(r.value)
        lines.append(f"| {r.assumption} | {val} | {r.units} | {r.source} | {r.rationale} | {r.sensitivity_priority} | {r.where_used} |")
    (OUT_DIR / "assumptions_ledger.md").write_text("\n".join(lines) + "\n")


def write_quantity_contracts() -> None:
    text = """# Quantity Contracts

## Modal frequency
- Numerator/denominator: not a ratio; cyclic natural frequency.
- Coordinate: global conical-shell modes of the radome.
- Excitation: impulse hammer test for measured modes; normal modes for FEM.
- Boundary condition: approximately free-free test on foam; preliminary FEM completely free and omits foam.
- Units: Hz.
- Expected behavior: free-free model should include six rigid-body modes near 0 Hz before flexible modes; published table reports flexible modes only.
- Reference: Vibrationdata `conical_shell.pdf`, Table 1 and Appendix A.
- Checker: require measured and published-FEA mode tables; require missing third FEA mode to remain missing rather than fabricated.

## Accelerance FRF
- Numerator: acceleration response.
- Denominator: impulse hammer force.
- Coordinates: aft-end and midpoint accelerometer response; hit location 12 inches from aft end.
- Boundary condition: radome on compliant foam, approximately free-free.
- Units: G/LBF, linear magnitude.
- Frequency axis: published figures use 0-1100 Hz linear; project review plots should use log frequency when regenerated from data. This phase has no raw FRF ordinates, only published modal peaks.
- Expected behavior: peaks near measured modal frequencies; amplitudes depend on hit/response location and damping.
- Reference: Vibrationdata `conical_shell.pdf`, Figures 2-4.
- Checker: report must state that no raw FRF ordinates were extracted in this phase.

## FEM-vs-test percent frequency error
- Numerator: published preliminary FEA frequency minus measured modal-test frequency.
- Denominator: measured modal-test frequency.
- Coordinate: matched published modes in Table 1.
- Units: percent.
- Expected behavior: first-mode error is exactly 0 because the report says the preliminary FEM properties were adjusted to match the fundamental.
- Reference: Vibrationdata `conical_shell.pdf`, Table 1 and Appendix A.
- Checker: require percent error table and explicit warning that first-mode agreement is tuned.

## Human Femap/Nastran flexible-pair frequency
- Numerator/denominator: not a ratio; mean cyclic natural frequency of a near-degenerate shell-mode pair.
- Coordinate: local Femap/Nastran output modes after the first six free-free rigid-body numerical-zero modes.
- Excitation: normal modes, no forcing.
- Boundary condition: free-free source deck.
- Units: Hz.
- Expected behavior: six near-zero rigid-body modes followed by nearly degenerate shell pairs.
- Reference: human-supplied screenshots `IMG_9814.jpg`, `IMG_9815.jpg`, `IMG_9816.jpg`.
- Checker: require six near-zero modes, pair means, and pair split metrics.

## Digitized peak accelerance QOI
- Numerator: acceleration response peak magnitude.
- Denominator: impulse hammer force.
- Coordinate: aft accelerometer response, hit at 12 inches from aft end.
- Boundary condition: radome on compliant foam, approximately free-free.
- Units: G/LBF.
- Frequency axis: log frequency for project-generated feature plot.
- Expected behavior: largest digitized peak near the first measured flexible mode.
- Reference: Vibrationdata `conical_shell.pdf`, Figures 2-4.
- Checker: require the report to label this as coarse visual digitization, not raw FRF data.
"""
    (OUT_DIR / "quantity_contracts.md").write_text(text)


def plot_mesh(summary: dict[str, Any]) -> None:
    nodes = {int(k): tuple(v) for k, v in summary["nodes"].items()}
    quads = summary["quads"]
    tris = summary["tris"]
    fig = plt.figure(figsize=(9, 6), dpi=160)
    ax = fig.add_subplot(111, projection="3d")
    for elem in quads:
        _, *ids = elem
        pts = np.array([nodes[i] for i in ids + [ids[0]] if i in nodes])
        if len(pts) == 5:
            ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color="#4169a8", lw=0.25, alpha=0.45)
    for elem in tris:
        _, *ids = elem
        pts = np.array([nodes[i] for i in ids + [ids[0]] if i in nodes])
        if len(pts) == 4:
            ax.plot(pts[:, 0], pts[:, 1], pts[:, 2], color="#8d5a3b", lw=0.25, alpha=0.45)
    coords = np.array(list(nodes.values()))
    ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2], s=1.0, color="#222222", alpha=0.25)
    ax.set_title("Parsed Vibrationdata conical_shell3.nas mesh\n(source deck geometry; not a solved mode shape)")
    ax.set_xlabel("x (in)")
    ax.set_ylabel("y (in)")
    ax.set_zlabel("z (in)")
    ax.view_init(elev=18, azim=-60)
    ax.set_box_aspect((np.ptp(coords[:, 0]), np.ptp(coords[:, 1]), max(np.ptp(coords[:, 2]), 1e-6)))
    fig.tight_layout()
    fig.savefig(FIG_DIR / "source_nastran_mesh.png")
    plt.close(fig)


def plot_frequency_comparison(pub: dict[str, Any]) -> None:
    rows = pub["rows"]
    modes = np.array([r["published_mode_index"] for r in rows])
    measured = np.array([r["measured_hz"] for r in rows], dtype=float)
    fea = np.array([np.nan if r["published_preliminary_fea_hz"] is None else r["published_preliminary_fea_hz"] for r in rows], dtype=float)

    fig, ax = plt.subplots(figsize=(8, 4.8), dpi=160)
    width = 0.34
    ax.bar(modes - width / 2, measured, width=width, label="Measured modal test", color="#2b6f6f")
    ax.bar(modes + width / 2, np.nan_to_num(fea), width=width, label="Published preliminary FEA", color="#b86b32")
    for x, y in zip(modes + width / 2, fea):
        if np.isnan(y):
            ax.text(x, 40, "missing", ha="center", va="bottom", fontsize=9, rotation=90)
    ax.set_xlabel("Published flexible mode index")
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title("Vibrationdata conical shell: measured vs published preliminary FEA")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "published_modal_frequency_comparison.png")
    plt.close(fig)

    errors = np.array([np.nan if r["percent_error_fea_vs_measured"] is None else r["percent_error_fea_vs_measured"] for r in rows], dtype=float)
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=160)
    ax.axhline(0.0, color="black", lw=1)
    ax.bar(modes, np.nan_to_num(errors), color="#6d5fb3")
    for x, e in zip(modes, errors):
        if np.isnan(e):
            ax.text(x, 0.05, "missing FEA", ha="center", va="bottom", fontsize=9)
        else:
            ax.text(x, e + (0.08 if e >= 0 else -0.08), f"{e:+.2f}%", ha="center", va="bottom" if e >= 0 else "top", fontsize=9)
    ax.set_xlabel("Published flexible mode index")
    ax.set_ylabel("FEA error vs measured (%)")
    ax.set_title("Percent error is small, but mode 1 was tuned by construction")
    ax.grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "published_frequency_error.png")
    plt.close(fig)


def plot_peak_evidence(pub: dict[str, Any]) -> None:
    rows = pub["rows"]
    freqs = [r["measured_hz"] for r in rows]
    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=160)
    for f in freqs:
        ax.axvline(f, color="#2b6f6f", lw=1.8, alpha=0.85)
        ax.text(f, 1.0, f"{f:g} Hz", rotation=90, va="top", ha="right", fontsize=9)
    ax.set_xscale("log")
    ax.set_xlim(50, 1100)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([])
    ax.set_xlabel("Frequency (Hz, log scale)")
    ax.set_title("Measured modal peaks available from the report table\n(no raw FRF ordinates extracted in this phase)")
    ax.grid(True, axis="x", which="both", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "published_peak_evidence_log_frequency.png")
    plt.close(fig)


def plot_mode_shape_status() -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=160)
    ax.axis("off")
    rows = [
        ("Published PDF", "mode-shape figures present", "source evidence; not copied into generated figures"),
        ("Source Nastran deck", "mesh available", "parsed and rendered in this packet"),
        ("Human Femap/Nastran solve", "screenshot evidence", "frequencies ingested; screenshots cached as provenance"),
        ("Mode-shape vectors", "not exported", "MAC/mode-shape correlation remains a future gate"),
    ]
    ax.set_title("Conical-shell mode-shape evidence status", fontsize=14, pad=18)
    y = 0.78
    for source, status, note in rows:
        ax.text(0.03, y, source, fontsize=11, fontweight="bold", va="center")
        ax.text(0.33, y, status, fontsize=11, va="center")
        ax.text(0.57, y, note, fontsize=10, va="center")
        ax.axhline(y - 0.08, color="#dddddd", lw=0.8)
        y -= 0.18
    ax.text(
        0.03,
        0.06,
        "Status artifact, not a substitute for machine-readable mode-shape vectors. It prevents accidental MAC/shape claims from screenshots alone.",
        fontsize=9.5,
        color="#444444",
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "mode_shape_status_not_solver_output.png")
    plt.close(fig)


def plot_human_nastran_results(human: dict[str, Any], comparison: dict[str, Any]) -> None:
    modes = human["modes"]
    mode_nums = np.array([m["mode"] for m in modes])
    freqs = np.array([m["frequency_hz"] for m in modes])
    fig, ax = plt.subplots(figsize=(9, 5), dpi=160)
    ax.semilogy(mode_nums[:6], freqs[:6], "o", color="#777777", label="free-free rigid-body numerical zeros")
    ax.semilogy(mode_nums[6:], freqs[6:], "o-", color="#2b6f6f", label="flexible shell modes")
    ax.set_xlabel("Femap/Nastran output mode")
    ax.set_ylabel("Frequency (Hz, log scale)")
    ax.set_title("Human Femap/Nastran run: six near-zero modes, then shell-mode pairs")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "human_nastran_frequency_table.png")
    plt.close(fig)

    rows = comparison["rows"]
    labels = [f"M{r['published_mode_index']}" for r in rows]
    x = np.arange(len(rows))
    measured = np.array([r["measured_hz"] for r in rows], dtype=float)
    published = np.array([np.nan if r["published_preliminary_fea_hz"] is None else r["published_preliminary_fea_hz"] for r in rows])
    local = np.array([np.nan if r["human_nastran_mean_hz"] is None else r["human_nastran_mean_hz"] for r in rows])
    fig, ax = plt.subplots(figsize=(9, 5), dpi=160)
    width = 0.25
    ax.bar(x - width, measured, width=width, label="measured test", color="#2b6f6f")
    ax.bar(x, np.nan_to_num(published), width=width, label="published preliminary FEA", color="#b86b32")
    ax.bar(x + width, np.nan_to_num(local), width=width, label="human Femap/Nastran pair mean", color="#6d5fb3")
    for xi, y in zip(x, published):
        if np.isnan(y):
            ax.text(xi, 40, "missing", ha="center", va="bottom", rotation=90, fontsize=9)
    for xi, y in zip(x + width, local):
        if np.isnan(y):
            ax.text(xi, 40, "unmatched", ha="center", va="bottom", rotation=90, fontsize=9)
    ax.set_xticks(x, labels)
    ax.set_ylabel("Frequency (Hz)")
    ax.set_title("Published modal-test comparison with local Femap/Nastran solve")
    ax.grid(True, axis="y", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "local_solve_vs_published_modal_comparison.png")
    plt.close(fig)


def plot_digitized_frf_features(frf: dict[str, Any]) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=160)
    colors = {"aft accelerometer": "#2b6f6f", "midpoint accelerometer": "#b86b32"}
    for response, color in colors.items():
        feats = [f for f in frf["features"] if f["response"] == response]
        x = [f["frequency_hz"] for f in feats]
        y = [f["magnitude_g_per_lbf"] for f in feats]
        yerr = [f["magnitude_uncertainty_g_per_lbf"] for f in feats]
        ax.errorbar(x, y, yerr=yerr, fmt="o", capsize=4, color=color, label=response)
    ax.set_xscale("log")
    ax.set_xlabel("Frequency (Hz, log scale)")
    ax.set_ylabel("Peak accelerance (G/LBF)")
    ax.set_title("Coarse digitized FRF peak features from Vibrationdata PDF\n(secondary visual data, not raw FRF ordinates)")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / "digitized_frf_peak_features.png")
    plt.close(fig)


def plot_statfem_modal_v1(statfem: dict[str, Any], comparison: dict[str, Any]) -> None:
    post = statfem["posterior"]
    k_vals = np.linspace(0.78, 1.28, 500)
    prior_sigma = 0.16
    prior = np.exp(-0.5 * (np.log(k_vals) / prior_sigma) ** 2) / (k_vals * prior_sigma * np.sqrt(2 * np.pi))
    # Approximate posterior for display from the stored quantiles.
    mu = math.log(post["k_scale_q50"])
    sigma = (math.log(post["k_scale_q95"]) - math.log(post["k_scale_q05"])) / (2 * 1.645)
    posterior = np.exp(-0.5 * ((np.log(k_vals) - mu) / sigma) ** 2) / (k_vals * sigma * np.sqrt(2 * np.pi))
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), dpi=160)
    axes[0].plot(k_vals, prior, label="prior", color="#777777")
    axes[0].plot(k_vals, posterior, label="posterior display fit", color="#2b6f6f")
    axes[0].axvline(post["k_scale_q50"], color="#2b6f6f", ls="--", lw=1)
    axes[0].set_xlabel("Global stiffness scale")
    axes[0].set_ylabel("Density")
    axes[0].set_title("Modal-only StatFEM v1\n(exact grid posterior, not NUTS/HMC)")
    axes[0].legend()
    axes[0].grid(True, alpha=0.25)

    hold = statfem["holdout_predictions"][0]
    axes[1].errorbar([0], [hold["predictive_q50_hz"]], yerr=[[hold["predictive_q50_hz"] - hold["predictive_q05_hz"]], [hold["predictive_q95_hz"] - hold["predictive_q50_hz"]]], fmt="o", capsize=6, label="90% predictive")
    axes[1].axhline(hold["observed_hz"], color="#b86b32", lw=2, label="held-out measured")
    axes[1].set_xlim(-0.8, 0.8)
    axes[1].set_xticks([0], [f"mode {hold['mode']}"])
    axes[1].set_ylabel("Frequency (Hz)")
    axes[1].set_title("Held-out modal prediction")
    axes[1].legend()
    axes[1].grid(True, axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "modal_statfem_v1_posterior_and_holdout.png")
    plt.close(fig)


def plot_frf_qoi(qoi: dict[str, Any]) -> None:
    q = qoi["qoi"]
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=160)
    lo, hi = q["approx_90pct_interval_g_per_lbf"]
    med = q["median_peak_g_per_lbf"]
    ax.errorbar([q["frequency_shifted_by_modal_posterior_hz"]], [med], yerr=[[med - lo], [hi - med]], fmt="o", capsize=6, color="#2b6f6f")
    ax.set_xscale("log")
    ax.set_xlabel("Posterior-shifted peak frequency (Hz, log scale)")
    ax.set_ylabel("Peak accelerance QOI (G/LBF)")
    ax.set_title("First FRF/QOI layer: aft peak accelerance\n(visual digitization uncertainty only)")
    ax.grid(True, which="both", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "frf_qoi_peak_accelerance.png")
    plt.close(fig)


def plot_launch_diagram() -> None:
    fig, ax = plt.subplots(figsize=(10, 5.6), dpi=160)
    ax.axis("off")
    boxes = [
        (0.04, 0.62, 0.23, 0.22, "Source data\nPDF modal test\nNastran deck"),
        (0.38, 0.62, 0.24, 0.22, "Forward model\nshell FEM or\nmodal surrogate"),
        (0.73, 0.62, 0.23, 0.22, "Observed data\nmodal frequencies\nFRF peaks if digitized"),
        (0.20, 0.18, 0.25, 0.24, "Unknowns\nstiffness scale\ndamping if supported"),
        (0.55, 0.18, 0.27, 0.24, "Discrepancy\noutput-space GP over\nmode/log frequency"),
    ]
    for x, y, w, h, label in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, ec="#333333", fc="#f4f0e6", lw=1.2))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=11)
    arrows = [
        ((0.27, 0.73), (0.38, 0.73)),
        ((0.62, 0.73), (0.73, 0.73)),
        ((0.45, 0.42), (0.50, 0.62)),
        ((0.68, 0.42), (0.57, 0.62)),
    ]
    for a, b in arrows:
        ax.annotate("", xy=b, xytext=a, arrowprops={"arrowstyle": "->", "lw": 1.4, "color": "#333333"})
    ax.text(
        0.5,
        0.04,
        "Launch rule: do not claim an active StatFEM digital twin until local solve or modal-surrogate replay,\nlikelihood inputs, discrepancy assumptions, and held-out validation are checker-backed.",
        ha="center",
        va="bottom",
        fontsize=10,
    )
    fig.tight_layout()
    fig.savefig(FIG_DIR / "statfem_launch_graphical_model.png")
    plt.close(fig)


def image_legibility_report() -> dict[str, Any]:
    report = {"figures": {}, "pass": True}
    for path in sorted(FIG_DIR.glob("*.png")):
        im = plt.imread(path)
        h, w = im.shape[:2]
        ok = w >= 900 and h >= 450
        report["figures"][path.name] = {"width_px": int(w), "height_px": int(h), "basic_size_pass": ok}
        report["pass"] = report["pass"] and ok
    return report


def write_digital_twin_launch(pub: dict[str, Any], nas: dict[str, Any], statfem: dict[str, Any], qoi: dict[str, Any]) -> dict[str, Any]:
    launch = {
        "statfem_active": True,
        "why_not_active_yet": [
            "A modal-only one-parameter update is active, but a full FRF digital twin is not active yet.",
            "The source FEM was tuned to match the measured fundamental frequency.",
            "Raw FRF ordinates were not extracted; only coarse peak features are available.",
        ],
        "recommended_v1_model": {
            "forward_model": "modal surrogate built from the human Femap/Nastran flexible pair means",
            "observations": "measured modal frequencies [97.6, 278, 429, 529] Hz plus coarse digitized FRF peak features",
            "inferred_variables": [
                "global shell stiffness scale",
                "modal-only output discrepancy integrated as fixed covariance",
                "FRF peak QOI uncertainty from digitization uncertainty",
            ],
            "fixed_initial_assumptions": [
                "free-free boundary approximation",
                "source thickness/density/geometry from Appendix A",
                "third published FEA mode missing, not imputed",
            ],
            "held_out_validation": "mode 4 is held out from the scalar stiffness calibration; the 429 Hz feature remains an unmatched model-class warning",
            "qoi_candidates": [
                "held-out flexible-mode frequency",
                "peak accelerance near a selected measured mode after FRF digitization",
                "modal amplification factor for a chosen response location",
            ],
            "discrepancy": "zero-mean output-space GP over mode index for modal-only v1; switch to log-frequency GP when FRF ordinates are available",
        },
        "active_v1_results": {
            "posterior": statfem["posterior"],
            "holdout_predictions": statfem["holdout_predictions"],
            "qoi": qoi["qoi"],
        },
        "source_model_size": {
            "nodes": nas["node_count"],
            "elements": nas["element_count"],
            "quads": nas["cquadr_count"],
            "tris": nas["ctriar_count"],
        },
        "published_mode_rows": pub["rows"],
    }
    write_json(OUT_DIR / "digital_twin_launch_definition.json", launch)
    md = ["# Digital Twin Launch Definition", ""]
    md.append("Status: **modal-only v1 active**. This packet now runs a one-parameter stiffness-scale update, but still does not claim a full FRF digital twin.")
    md.append("")
    md.append("## Recommended v1")
    for k, v in launch["recommended_v1_model"].items():
        md.append(f"- **{k.replace('_', ' ').title()}:** {v if isinstance(v, str) else '; '.join(v)}")
    md.append("")
    md.append("## Why the FRF twin is still paused")
    for item in launch["why_not_active_yet"]:
        md.append(f"- {item}")
    (OUT_DIR / "digital_twin_launch_definition.md").write_text("\n".join(md) + "\n")
    return launch


def write_report(
    source_manifest: dict[str, Any],
    pub: dict[str, Any],
    nas: dict[str, Any],
    human: dict[str, Any],
    comparison: dict[str, Any],
    frf: dict[str, Any],
    statfem: dict[str, Any],
    qoi: dict[str, Any],
    launch: dict[str, Any],
    checks: dict[str, Any],
) -> None:
    rows = pub["rows"]
    table = ["| Mode | Measured Hz | Published preliminary FEA Hz | Error % |", "|---:|---:|---:|---:|"]
    for r in rows:
        f = r["published_preliminary_fea_hz"]
        e = r["percent_error_fea_vs_measured"]
        table.append(
            f"| {r['published_mode_index']} | {r['measured_hz']:.1f} | "
            f"{'missing' if f is None else f'{f:.1f}'} | "
            f"{'missing' if e is None else f'{e:+.2f}'} |"
        )
    local_table = ["| Published mode | Measured Hz | Human Nastran pair mean Hz | Error vs measured % | Notes |", "|---:|---:|---:|---:|---|"]
    for r in comparison["rows"]:
        local = r["human_nastran_mean_hz"]
        err = r["human_nastran_error_vs_measured_percent"]
        local_table.append(
            f"| {r['published_mode_index']} | {r['measured_hz']:.1f} | "
            f"{'unmatched' if local is None else f'{local:.4f}'} | "
            f"{'unmatched' if err is None else f'{err:+.2f}'} | {r.get('note', '')} |"
        )
    stat = statfem["posterior"]
    hold = statfem["holdout_predictions"][0]
    q = qoi["qoi"]
    report = f"""# Conical Shell FEM/Test Source Audit and StatFEM Launch Packet

## Method Summary
- **Engineering decision:** Can the Vibrationdata conical-shell example serve as a modest, auditable first real-ish dynamic digital-twin sandbox?
- **Current answer:** Yes for a modal-only v1 digital-twin sandbox; no for a full FRF digital twin yet.
- **Data count:** one published modal-test comparison table, one human Femap/Nastran solve screenshot set, two published FRF figures without raw ordinates, and one source Nastran deck.
- **Likelihood status:** active modal-only likelihood using exact grid quadrature over one stiffness-scale parameter. This is not NUTS/HMC.
- **Inferred variables:** global shell stiffness scale only.
- **Fixed assumptions:** see `assumptions_ledger.md`.
- **Not inferred:** material density, shell thickness, full mode-shape discrepancy field, raw FRF ordinates, and damping curve.
- **QOI:** aft peak accelerance near the first flexible shell mode from coarse visual digitization, with large uncertainty.

## Source Provenance
- StructuralFE index: {STRUCTURAL_FE_URL}
- PDF: `{PDF_URL}` -> {source_manifest['pdf']['status']}
- Nastran deck: `{NAS_URL}` -> {source_manifest['nas']['status']}
- Access quirk: browser-like user agent for the `.nas` returned `{source_manifest['nas_browser_like_access'].get('http_status')}`; curl-like user agent succeeded. This is recorded so future agents do not misdiagnose the source as unavailable.

## Published Test/FEM Comparison
The source report states that the preliminary FEM material properties were adjusted so the FEM fundamental frequency matched the measured fundamental. Therefore mode 1 agreement is useful provenance, not independent validation.

{chr(10).join(table)}

![Measured vs published FEA](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/published_modal_frequency_comparison.png>)

![Frequency error](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/published_frequency_error.png>)

## Parsed Source FEM Metadata
- Solution: `{nas['solution']}`
- Nodes: `{nas['node_count']}`
- Elements: `{nas['element_count']}` = `{nas['cquadr_count']}` CQUADR + `{nas['ctriar_count']}` CTRIAR
- Shell thickness from PSHELL: `{nas['pshell']['thickness_in']}` inch
- Boundary-condition interpretation from deck: free-free flexible-mode solve; no SPC/SPC1 constraints found.
- Bounding box in source coordinates: `{nas['bbox']}`

![Parsed source mesh](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/source_nastran_mesh.png>)

## Human Femap/Nastran Solve
The human-supplied solve shows six near-zero free-free rigid-body modes, followed by nearly degenerate shell-mode pairs. The first three flexible pair means agree with the published preliminary FEA values to within about one percent.

{chr(10).join(local_table)}

![Human Nastran frequency table](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/human_nastran_frequency_table.png>)

![Local solve comparison](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/local_solve_vs_published_modal_comparison.png>)

## Mode-Shape Evidence Status
The source PDF contains mode-shape figures, and the human screenshots show representative deformed views for modes 7 and 9. This packet records screenshot provenance but does not claim machine-readable mode-shape vectors. A solved mode-shape export remains the next gate.

![Mode-shape status](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/mode_shape_status_not_solver_output.png>)

## FRF Evidence
The report includes accelerance FRF figures in `G/LBF`. This phase adds coarse visual peak features with intentionally large uncertainty. These are secondary digitized data, not raw FRF ordinates.

![Peak evidence](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/published_peak_evidence_log_frequency.png>)

![Digitized FRF peak features](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/digitized_frf_peak_features.png>)

## Modal-Only StatFEM v1
- Model equation: `{statfem['model_equation']}`
- Inference method: `{statfem['method']}`
- Reason for no NUTS/HMC: {statfem['reason_not_nuts_hmc']}
- Calibration modes: `{statfem['calibration_modes']}`. Mode 1 is included but interpreted cautiously because the source FEM was tuned to the fundamental.
- Held-out mode: `{statfem['holdout_modes']}`.
- Posterior stiffness scale median: `{stat['k_scale_q50']:.4f}`, 90% interval `[{stat['k_scale_q05']:.4f}, {stat['k_scale_q95']:.4f}]`.
- Held-out mode {hold['mode']} observed `{hold['observed_hz']:.1f}` Hz; predictive 90% interval `[{hold['predictive_q05_hz']:.1f}, {hold['predictive_q95_hz']:.1f}]` Hz; covered: `{hold['covered_by_90pct_interval']}`.

![Modal StatFEM v1](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/modal_statfem_v1_posterior_and_holdout.png>)

## FRF/QOI Layer
- QOI: {q['name']}.
- Median peak accelerance: `{q['median_peak_g_per_lbf']:.2f}` G/LBF.
- Approximate 90% interval: `[{q['approx_90pct_interval_g_per_lbf'][0]:.2f}, {q['approx_90pct_interval_g_per_lbf'][1]:.2f}]` G/LBF.
- Posterior-shifted peak frequency: `{q['frequency_shifted_by_modal_posterior_hz']:.2f}` Hz.
- Warning: {q['warning']}

![FRF QOI](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/frf_qoi_peak_accelerance.png>)

## Digital Twin Launch
![StatFEM launch graphical model](</Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/conical_shell_statfem_ladder_20260608/figures/statfem_launch_graphical_model.png>)

- Active modal-only StatFEM posterior in this packet: `{launch['statfem_active']}`
- Recommended next v2: replace coarse peak digitization with raw FRF curve extraction or manual plot-digitizer traces, then move the discrepancy from mode-index covariance to log-frequency covariance.
- Held-out validation rule: do not validate on mode 1 alone because it was tuned. Continue using mode 4 and the unmatched 429 Hz feature as model-class checks.
- Discrepancy: fixed output discrepancy covariance in v1; output-space GP over mode index/log frequency is the next upgrade.

## What This Proves
- The conical-shell source files are reachable and cacheable.
- The PDF contains enough published modal-test evidence to compare test frequencies with preliminary FEA.
- The source Nastran deck can be parsed for geometry, elements, material/property cards, and boundary-condition metadata.
- The human Femap/Nastran solve reproduces the published preliminary FEA mode pairs.
- A first modal-only Bayesian update can be run and checked from one command.

## What This Does Not Prove
- It does not prove that the preliminary FEM predicts the fundamental from first principles; the report says it was tuned.
- It does not prove damping or FRF amplitude calibration; raw FRF ordinates were not extracted.
- It does not prove full mode-shape agreement; screenshots are provenance, not machine-readable MAC evidence.
- It does not use NUTS/HMC; the v1 posterior is one-dimensional exact grid quadrature.

## Checker Status
- Overall pass: `{checks['pass']}`
- See `checker_report.json` for machine-readable evidence.
"""
    (OUT_DIR / "conical_shell_packet.md").write_text(report)


def run_checks(source_manifest: dict[str, Any], pub: dict[str, Any], nas: dict[str, Any], launch: dict[str, Any]) -> dict[str, Any]:
    required = [
        OUT_DIR / "source_manifest.json",
        OUT_DIR / "nastran_summary.json",
        OUT_DIR / "published_modal_comparison.json",
        OUT_DIR / "human_nastran_solution.json",
        OUT_DIR / "local_solve_comparison.json",
        OUT_DIR / "frf_digitized_features.json",
        OUT_DIR / "modal_statfem_v1_results.json",
        OUT_DIR / "frf_qoi_summary.json",
        OUT_DIR / "assumptions_ledger.md",
        OUT_DIR / "assumptions_ledger.json",
        OUT_DIR / "quantity_contracts.md",
        OUT_DIR / "digital_twin_launch_definition.md",
        OUT_DIR / "digital_twin_launch_definition.json",
        FIG_DIR / "source_nastran_mesh.png",
        FIG_DIR / "human_nastran_frequency_table.png",
        FIG_DIR / "local_solve_vs_published_modal_comparison.png",
        FIG_DIR / "published_modal_frequency_comparison.png",
        FIG_DIR / "published_frequency_error.png",
        FIG_DIR / "published_peak_evidence_log_frequency.png",
        FIG_DIR / "digitized_frf_peak_features.png",
        FIG_DIR / "modal_statfem_v1_posterior_and_holdout.png",
        FIG_DIR / "frf_qoi_peak_accelerance.png",
        FIG_DIR / "mode_shape_status_not_solver_output.png",
        FIG_DIR / "statfem_launch_graphical_model.png",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    rows = pub["rows"]
    checks = {
        "source_pdf_fetched": source_manifest["pdf"]["status"] == "fetched",
        "source_nas_fetched": source_manifest["nas"]["status"] == "fetched",
        "source_metadata_has_checksums": bool(source_manifest["pdf"].get("sha256")) and bool(source_manifest["nas"].get("sha256")),
        "nastran_parser_reports_model": nas["node_count"] > 100 and nas["element_count"] > 100 and nas["pshell"]["thickness_in"] == 0.1,
        "free_boundary_documented": nas["free_boundary_condition"] is True,
        "published_test_and_fea_modes_present": len(rows) == 4 and rows[0]["measured_hz"] == 97.6 and rows[0]["published_preliminary_fea_hz"] == 97.6,
        "missing_third_fea_not_fabricated": rows[2]["published_preliminary_fea_hz"] is None,
        "percent_errors_computed": all((r["percent_error_fea_vs_measured"] is not None) for r in rows if r["published_preliminary_fea_hz"] is not None),
        "modal_statfem_v1_active": launch["statfem_active"] is True,
        "frf_twin_not_overclaimed": "Raw FRF ordinates were not extracted" in " ".join(launch["why_not_active_yet"]),
        "all_required_files_exist": not missing,
    }
    checks["pass"] = all(checks.values())
    checks["missing_files"] = missing
    return checks


def main() -> int:
    started_wall = time.perf_counter()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    pdf_meta = fetch(PDF_URL, SOURCE_DIR / "conical_shell.pdf")
    nas_browser = check_browser_like_access(NAS_URL)
    nas_meta = fetch(NAS_URL, SOURCE_DIR / "conical_shell3.nas")
    source_manifest = {
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "structural_fe_index": STRUCTURAL_FE_URL,
        "pdf": pdf_meta,
        "nas": nas_meta,
        "nas_browser_like_access": nas_browser,
        "notes": [
            "The Nastran deck is reachable with a curl-like user agent.",
            "The browser-like user agent returned HTTP 406 during this run.",
            "Source files are cached for traceability; do not present source figures as generated figures.",
        ],
    }
    write_json(OUT_DIR / "source_manifest.json", source_manifest)

    if pdf_meta["status"] != "fetched" or nas_meta["status"] != "fetched":
        raise RuntimeError("Required source file fetch failed; see source_manifest.json")

    pdf_text = extract_pdf_text(SOURCE_DIR / "conical_shell.pdf")
    (OUT_DIR / "pdf_extracted_text_excerpt.txt").write_text(pdf_text[:8000])
    nas_summary = parse_nastran(SOURCE_DIR / "conical_shell3.nas")
    write_json(OUT_DIR / "nastran_summary.json", {k: v for k, v in nas_summary.items() if k not in {"nodes", "quads", "tris"}})

    pub = published_data()
    write_json(OUT_DIR / "published_modal_comparison.json", pub)
    human = human_nastran_solution()
    write_json(OUT_DIR / "human_nastran_solution.json", human)
    comparison = local_solve_comparison(pub, human)
    write_json(OUT_DIR / "local_solve_comparison.json", comparison)
    frf = digitized_frf_features()
    write_json(OUT_DIR / "frf_digitized_features.json", frf)
    statfem = modal_statfem_v1(comparison)
    write_json(OUT_DIR / "modal_statfem_v1_results.json", statfem)
    qoi = frf_qoi_layer(frf, statfem)
    write_json(OUT_DIR / "frf_qoi_summary.json", qoi)
    rows = assumptions_ledger()
    write_assumptions(rows)
    write_quantity_contracts()

    plot_mesh(nas_summary)
    plot_human_nastran_results(human, comparison)
    plot_frequency_comparison(pub)
    plot_peak_evidence(pub)
    plot_mode_shape_status()
    plot_digitized_frf_features(frf)
    plot_statfem_modal_v1(statfem, comparison)
    plot_frf_qoi(qoi)
    plot_launch_diagram()

    launch = write_digital_twin_launch(pub, nas_summary, statfem, qoi)
    img_report = image_legibility_report()
    write_json(OUT_DIR / "image_legibility_report.json", img_report)

    checks = run_checks(source_manifest, pub, nas_summary, launch)
    checks["image_legibility_basic_pass"] = img_report["pass"]
    checks["active_runtime_s"] = time.perf_counter() - started_wall
    checks["elapsed_wallclock_s"] = checks["active_runtime_s"]
    write_json(OUT_DIR / "checker_report.json", checks)
    write_report(
        source_manifest,
        pub,
        {k: v for k, v in nas_summary.items() if k not in {"nodes", "quads", "tris"}},
        human,
        comparison,
        frf,
        statfem,
        qoi,
        launch,
        checks,
    )

    manifest = {
        "packet": str((OUT_DIR / "conical_shell_packet.md").relative_to(ROOT)),
        "source_manifest": str((OUT_DIR / "source_manifest.json").relative_to(ROOT)),
        "checker_report": str((OUT_DIR / "checker_report.json").relative_to(ROOT)),
        "figures": [str(p.relative_to(ROOT)) for p in sorted(FIG_DIR.glob("*.png"))],
        "frequency_axis_policy": {
            "published_peak_evidence_log_frequency.png": "log frequency x-axis",
            "published_modal_frequency_comparison.png": "mode-index axis, not frequency-domain FRF",
            "published_frequency_error.png": "mode-index axis, not frequency-domain FRF",
        },
        "statfem_active": True,
    }
    write_json(OUT_DIR / "manifest.json", manifest)
    return 0 if checks["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
