#!/usr/bin/env python3
"""Checker for the sequential vibe/modal/flight setup packet."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "reports" / "sequential_vibe_modal_flight_20260602"
REPORT = ROOT / "artifacts" / "tests" / "sequential_vibe_modal_flight_setup_report.json"


REQUIRED_FILES = [
    "task.md",
    "db_conventions.md",
    "assumptions_ledger.md",
    "assumptions_ledger.json",
    "quantity_contracts.md",
    "sources.md",
    "experiment_schema.md",
    "experiment_schema.json",
    "nuts_backend_choice.md",
    "sequential_dataset.json",
    "summary.json",
    "manifest.json",
    "sequential_research_packet.md",
    "figures/smoothline_vs_dome_fem_psd.png",
    "figures/staged_test_observations.png",
    "figures/flight_forcing_matern_gp_samples.png",
    "figures/flight_qoi_interface_sequence.png",
    "figures/cumulative_flight_ci_preview.png",
]


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (OUT_DIR / path).exists()]
    failures: list[str] = [f"missing required file: {path}" for path in missing]

    summary = json.loads((OUT_DIR / "summary.json").read_text()) if (OUT_DIR / "summary.json").exists() else {}
    schema = json.loads((OUT_DIR / "experiment_schema.json").read_text()) if (OUT_DIR / "experiment_schema.json").exists() else {}
    dataset = json.loads((OUT_DIR / "sequential_dataset.json").read_text()) if (OUT_DIR / "sequential_dataset.json").exists() else {}
    packet = (OUT_DIR / "sequential_research_packet.md").read_text() if (OUT_DIR / "sequential_research_packet.md").exists() else ""
    db_text = (OUT_DIR / "db_conventions.md").read_text() if (OUT_DIR / "db_conventions.md").exists() else ""
    nuts_text = (OUT_DIR / "nuts_backend_choice.md").read_text() if (OUT_DIR / "nuts_backend_choice.md").exists() else ""
    quantities_text = (OUT_DIR / "quantity_contracts.md").read_text() if (OUT_DIR / "quantity_contracts.md").exists() else ""
    assumptions = json.loads((OUT_DIR / "assumptions_ledger.json").read_text()) if (OUT_DIR / "assumptions_ledger.json").exists() else {"rows": []}

    if "factor = 10 ** (dB / 10)" not in db_text:
        failures.append("PSD-space dB conversion is not documented")
    if len(assumptions.get("rows", [])) < 8:
        failures.append("assumptions ledger is missing required rows")
    for quantity in [
        "Smoothline PSD",
        "Dome FEM Response PSD",
        "Tray Vibe Response PSD",
        "Dome-Only Modal FRF",
        "Coupled Modal FRFs",
        "Flight Forcing PSD",
        "Interface Acceleration Spectrum",
        "Tray `3*GRMS` QOI",
    ]:
        if quantity not in quantities_text:
            failures.append(f"quantity contract missing: {quantity}")
    if summary.get("flight_to_flight_sigma_db_psd_known_not_learned") != 3.0:
        failures.append("3 dB flight-to-flight variability is missing or not fixed")
    if summary.get("build_to_build_sigma_db_psd_initial_to_be_learned") != 1.5:
        failures.append("1.5 dB build-to-build initial variability missing")
    if summary.get("nuts_active") is not False:
        failures.append("summary must not claim NUTS is active")
    if "Status: NUTS/HMC is not implemented" not in nuts_text:
        failures.append("NUTS note must state that NUTS/HMC is not implemented")
    forcing = summary.get("forcing_covariance", {})
    if forcing.get("type") != "Matern" or forcing.get("nu") != "3/2":
        failures.append("forcing covariance is not recorded as Matérn-3/2")
    if summary.get("flight_count") != 11 or summary.get("later_builds") != 10:
        failures.append("expected first flight plus 10 later builds/flights")

    stages = schema.get("stages", [])
    for stage in [
        "pre_data_dome_fem",
        "tray_vibe_test",
        "dome_modal_test",
        "coupled_modal_test",
        "first_build_flight",
        "later_builds_and_flights",
    ]:
        if stage not in stages:
            failures.append(f"schema missing stage: {stage}")

    fixed = schema.get("fixed_not_learned", {})
    if fixed.get("flight_to_flight_variability_sigma_db_psd") != 3.0:
        failures.append("schema does not mark flight-to-flight variability as fixed")
    targets = schema.get("learning_targets_future_nuts", [])
    for target in ["build-to-build variability scale", "sensor-noise scale", "tray 3*GRMS response QOI"]:
        if target not in targets:
            failures.append(f"schema missing future learning target: {target}")

    if dataset:
        spec_freqs = np.asarray(dataset.get("freqs_hz", []), dtype=float)
        smoothline = np.asarray(dataset.get("smoothline_psd_g2_per_hz", []), dtype=float)
        dome = np.asarray(dataset.get("dome_fem_response_psd_g2_per_hz", []), dtype=float)
        if len(spec_freqs) < 100 or not np.all(np.diff(spec_freqs) > 0):
            failures.append("frequency grid missing or not increasing")
        if not np.isclose(np.max(dome), 0.1, rtol=0.02):
            failures.append("dome FEM response peak is not scaled to 0.1 g^2/Hz")
        if np.any(smoothline <= 0):
            failures.append("smoothline PSD must be positive")
        if len(dataset.get("build_samples", [])) != 11:
            failures.append("dataset must include 11 build samples")
        if len(dataset.get("flight_summaries", [])) != 11:
            failures.append("dataset must include 11 flight summaries")
        qoi_ci = dataset.get("qoi_prior_predictive_ci_3grms_g", {})
        if not (qoi_ci.get("q005", 0.0) < qoi_ci.get("q025", 0.0) < qoi_ci.get("q975", 0.0) < qoi_ci.get("q995", 0.0)):
            failures.append("QOI prior predictive intervals are not ordered")

    for snippet in [
        "dB values are PSD-space dB",
        "Matérn-3/2 GP",
        "does not perform posterior inference",
        "Implement the NumPyro NUTS model",
    ]:
        if snippet not in packet:
            failures.append(f"packet missing snippet: {snippet}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "pass": not failures,
        "failures": failures,
        "summary": summary,
        "packet": str(OUT_DIR / "sequential_research_packet.md"),
    }
    REPORT.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if not failures else 2


if __name__ == "__main__":
    raise SystemExit(main())
