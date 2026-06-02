#!/usr/bin/env python3
"""Checker for the Codex GPT-5.5 full sequential runner outputs."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "reports" / "runner_codex_gpt55_20260602"
REPORT = OUT_DIR / "runner_checker_report.json"

REQUIRED_FILES = [
    "commands.md",
    "files_changed.md",
    "assumptions_ledger.md",
    "assumptions_ledger.json",
    "nuts_diagnostics.md",
    "nuts_diagnostics.json",
    "figures/sequential_observations_truth_vs_observed.png",
    "figures/absolute_error_and_normalized_diagnostics.png",
    "figures/posterior_full_vs_peak_parameters.png",
    "figures/input_spectra_and_tray_qoi_intervals_after_flights.png",
    "figures/full_vs_peak_likelihood_qoi_differences.png",
    "figures/hmc_diagnostics.png",
    "figures/peak_feature_mapping_sensitivity.png",
    "figures/graphical_model_likelihood.png",
    "checks.json",
    "known_failures.md",
    "review_request.md",
    "manifest.json",
    "packet.md",
    "posterior_results.json",
    "sequential_full_dataset.json",
    "quantity_contracts.md",
    "feature_sensitivity.json",
]


def main() -> int:
    failures: list[str] = []
    missing = [path for path in REQUIRED_FILES if not (OUT_DIR / path).exists()]
    failures.extend([f"missing required file: {path}" for path in missing])

    data = {}
    results = {}
    diagnostics = {}
    checks = {}
    manifest = {}
    packet = ""
    if (OUT_DIR / "sequential_full_dataset.json").exists():
        data = json.loads((OUT_DIR / "sequential_full_dataset.json").read_text())
    if (OUT_DIR / "posterior_results.json").exists():
        results = json.loads((OUT_DIR / "posterior_results.json").read_text())
    if (OUT_DIR / "nuts_diagnostics.json").exists():
        diagnostics = json.loads((OUT_DIR / "nuts_diagnostics.json").read_text())
    if (OUT_DIR / "checks.json").exists():
        checks = json.loads((OUT_DIR / "checks.json").read_text())
    if (OUT_DIR / "manifest.json").exists():
        manifest = json.loads((OUT_DIR / "manifest.json").read_text())
    if (OUT_DIR / "packet.md").exists():
        packet = (OUT_DIR / "packet.md").read_text()

    if data:
        if data.get("data_count", {}).get("flights") != 11:
            failures.append("dataset must contain first flight plus 10 later flights")
        if data.get("data_count", {}).get("tray_vibe_tests") != 11:
            failures.append("dataset must contain tray vibe tests for all 11 builds")
        fixed = data.get("fixed_not_inferred", {})
        if fixed.get("flight_to_flight_sigma_db_psd") != 3.0:
            failures.append("flight-to-flight forcing sigma must remain fixed at 3 dB")
        if "Matern-3/2" not in fixed.get("forcing_covariance", ""):
            failures.append("forcing covariance must be recorded as Matern-3/2")

    if diagnostics:
        for mode in ["full", "peak_feature"]:
            if mode not in diagnostics:
                failures.append(f"diagnostics missing mode: {mode}")
                continue
            d = diagnostics[mode]
            if d.get("hmc_active") is not True:
                failures.append(f"{mode} must mark HMC active")
            if d.get("nuts_active") is not False:
                failures.append(f"{mode} must not claim NUTS active")
            for key in ["divergences", "step_size_final_by_chain", "tree_depth", "ess_bulk_approx", "r_hat"]:
                if key not in d:
                    failures.append(f"{mode} diagnostics missing {key}")
            if "fixed_leapfrog_steps" not in d.get("tree_depth", {}):
                failures.append(f"{mode} tree-depth entry must state fixed leapfrog steps")

    if results:
        if "likelihood_comparison" not in results:
            failures.append("posterior results missing likelihood comparison")
        else:
            ratios = results["likelihood_comparison"].get("interval_width_ratio_peak_over_full", {})
            for key in ["dome_hz", "tray_hz", "build_sigma_db_psd", "sensor_sigma_db_psd", "tray_3grms_g"]:
                if key not in ratios:
                    failures.append(f"missing interval-width ratio: {key}")
        for mode in ["full", "peak_feature"]:
            summary = results.get(mode, {}).get("posterior_summary", {})
            qoi = summary.get("tray_3grms_g", {})
            if not (qoi.get("q005", 0.0) < qoi.get("q025", 0.0) < qoi.get("q975", 0.0) < qoi.get("q995", 0.0)):
                failures.append(f"{mode} tray 3*GRMS intervals are missing or unordered")
            pred = results.get(mode, {}).get("posterior_predictive", {})
            input_psd = pred.get("input_force_psd_n2_per_hz", {})
            if not all(key in input_psd for key in ["q005", "q025", "q500", "q975", "q995"]):
                failures.append(f"{mode} missing 95/99 input PSD intervals")

    if checks:
        if checks.get("self_check_pass") is not True:
            failures.append("runner self-check did not pass")
        image = checks.get("image_legibility", [])
        if not image or not all(item.get("pass") for item in image):
            failures.append("image legibility check missing or failed")

    if manifest:
        sampler = manifest.get("sampler", {})
        if sampler.get("random_walk_metropolis_used") is not False:
            failures.append("manifest must state random-walk Metropolis was not used")
        if sampler.get("nuts_active") is not False or sampler.get("hmc_active") is not True:
            failures.append("manifest sampler status must honestly mark HMC active and NUTS inactive")

    for snippet in [
        "PSD-space dB uses `factor = 10 ** (dB / 10)`",
        "This is real gradient-based HMC, not random-walk Metropolis.",
        "It is not NUTS",
        "Full-data likelihood uses every generated log PSD",
        "Peak-feature likelihood uses observed hard peak/notch summaries",
        "A checker pass is not proof of physical correctness.",
    ]:
        if snippet not in packet:
            failures.append(f"packet missing snippet: {snippet}")

    report = {
        "pass": not failures,
        "failures": failures,
        "output_dir": str(OUT_DIR),
        "checked_files": REQUIRED_FILES,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))

    if (OUT_DIR / "checks.json").exists():
        checks["runner_checker"] = {
            "command": "PYTHONPATH=. python3 tests/test_runner_codex_gpt55_full_experiment.py",
            "pass": report["pass"],
            "report": "runner_checker_report.json",
            "failures": failures,
        }
        (OUT_DIR / "checks.json").write_text(json.dumps(checks, indent=2))

    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
