#!/usr/bin/env python3
"""Checker-backed acceptance conditions for the fresh 2DOF rerun."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "reports" / "fresh_2dof_statfem_fbs_20260601"


def main() -> int:
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
        "sensitivity_summary.json",
        "reference_comparison.json",
        "image_legibility_report.json",
        "fresh_vs_prior_comparison.json",
        "noise_qoi_7004c_lit_review.md",
        "manifest.json",
        "checker_report.json",
        *required_figures,
    ]
    missing_files = [path for path in required_files if not (OUT_DIR / path).exists()]

    report_path = OUT_DIR / "fresh_2dof_statfem_packet.md"
    report_text = report_path.read_text() if report_path.exists() else ""
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
        "Likelihood formulation",
        "not only resonance peak locations or magnitudes",
        "## Method Summary",
        "Whole FRF/PSD likelihood",
        "Inferred variables",
        "Fixed assumptions",
        "Not inferred",
        "Specific likelihood function",
        "Image legibility QA",
    ]
    missing_snippets = [snippet for snippet in required_snippets if snippet not in report_text]

    assumptions_path = OUT_DIR / "assumptions_ledger.json"
    assumptions = json.loads(assumptions_path.read_text()) if assumptions_path.exists() else {"rows": []}
    numeric_assumptions = [
        row
        for row in assumptions.get("rows", [])
        if isinstance(row.get("value"), (int, float)) and row.get("units") and row.get("rationale")
    ]
    assumption_values = {row.get("assumption"): row.get("value") for row in assumptions.get("rows", [])}
    model_error_assumptions_present = (
        abs(float(assumption_values.get("Dome frequency model error", 999.0)) + 0.15) < 1e-12
        and abs(float(assumption_values.get("Tray frequency model error", 999.0)) - 0.15) < 1e-12
        and abs(float(assumption_values.get("Dome damping model error", 999.0)) - 0.25) < 1e-12
        and abs(float(assumption_values.get("Tray damping model error", 999.0)) + 0.25) < 1e-12
    )

    dataset_path = OUT_DIR / "fresh_2dof_dataset.json"
    channel_2_3_relative_l2 = None
    if dataset_path.exists():
        dataset = json.loads(dataset_path.read_text())
        ch2 = np.asarray(
            dataset["channels_clean"]["ch2_coupled_primary_reciprocal_inertance"]["real"]
        ) + 1j * np.asarray(
            dataset["channels_clean"]["ch2_coupled_primary_reciprocal_inertance"]["imag"]
        )
        ch3 = np.asarray(
            dataset["channels_clean"]["ch3_coupled_tray_reciprocal_inertance"]["real"]
        ) + 1j * np.asarray(
            dataset["channels_clean"]["ch3_coupled_tray_reciprocal_inertance"]["imag"]
        )
        channel_2_3_relative_l2 = float(
            np.linalg.norm(ch2 - ch3) / max(np.linalg.norm(ch2), np.linalg.norm(ch3), 1e-12)
        )

    manifest_path = OUT_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
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
    axis_metadata_ok = (
        bool(frequency_axis_items)
        and all("log" in str(value) for value in frequency_axis_items.values())
        and declared_axis_exceptions_ok
    )

    posterior_path = OUT_DIR / "posterior_summary.json"
    posterior = json.loads(posterior_path.read_text()) if posterior_path.exists() else {}
    qoi_sample_summary_exists = bool(posterior.get("qoi_summary")) and len(
        posterior.get("qoi_samples_3grms_tray_accel_g", [])
    ) >= 100

    bayes_path = OUT_DIR / "bayes_update_summary.json"
    bayes = json.loads(bayes_path.read_text()) if bayes_path.exists() else {}
    parameter_ci_ok = all(
        name in bayes.get("parameter_summaries", {})
        and "q025" in bayes["parameter_summaries"][name].get("posterior", {})
        and "q975" in bayes["parameter_summaries"][name].get("posterior", {})
        for name in ["dome_hz", "tray_hz", "zeta1", "zeta2"]
    )

    sensitivity_path = OUT_DIR / "sensitivity_summary.json"
    sensitivity = json.loads(sensitivity_path.read_text()) if sensitivity_path.exists() else {}
    sensitivity_present = bool(sensitivity.get("qoi_scenarios")) and bool(
        sensitivity.get("synthetic_error_scenarios")
    )
    forbidden_sensitivity_text = [
        "Sensitivity labels:",
        "Decision threshold used only for sensitivity illustration",
        "1.10 x synthetic truth",
    ]
    no_arbitrary_threshold_language = (
        all(text not in report_text for text in forbidden_sensitivity_text)
        and sensitivity.get("decision_threshold") is None
        and "decision_threshold_110pct_truth_3grms_g" not in sensitivity
    )

    reference_path = OUT_DIR / "reference_comparison.json"
    reference = json.loads(reference_path.read_text()) if reference_path.exists() else {}
    reference_metrics = reference.get("metrics", {})
    reference_value_metrics_present = all(
        key in reference_metrics
        for key in [
            "ch4_low_frequency_median",
            "ch4_peak_frequency_hz",
            "nasa_7004c_load_at_r_0p62",
            "nasa_7004c_load_at_r_1",
            "nasa_7004c_source_at_r_1",
        ]
    )
    reference_present = (
        bool(reference.get("checks"))
        and "NASA-HDBK-7004C" in report_text
        and "vibrationdata.com" in report_text
        and reference.get("checks", {}).get("nasa_7004c_figure9_load_at_0p62_near_1p62") is True
    )
    simulation_replicates = {}
    if dataset_path.exists():
        dataset = json.loads(dataset_path.read_text())
        simulation_replicates = dataset.get("simulation_replicates", {})
    simulation_replicates_documented = (
        simulation_replicates.get("frequency_domain_realizations_per_channel") == 1
        and simulation_replicates.get("flight_like_response_psd_realizations") == 1
        and simulation_replicates.get("flight_time_history_realizations") == 1
        and simulation_replicates.get("flight_to_flight_variability_modeled") is False
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
        and "Likelihood formulation" in report_text
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
    image_legibility_path = OUT_DIR / "image_legibility_report.json"
    image_legibility = json.loads(image_legibility_path.read_text()) if image_legibility_path.exists() else {}
    image_legibility_pass = (
        image_legibility.get("pass") is True
        and "figures/statfem_likelihood_graphical_model_legible.png" in image_legibility.get("strict_text_heavy_figures", [])
        and "figures/reference_standards_comparison_cards.png" in image_legibility.get("strict_text_heavy_figures", [])
        and "Image legibility QA" in report_text
    )

    checks = {
        "required_report_exists": report_path.exists(),
        "required_figures_exist": not [fig for fig in required_figures if not (OUT_DIR / fig).exists()],
        "required_files_exist": not missing_files,
        "required_report_snippets_present": not missing_snippets,
        "numerical_assumptions_present": len(numeric_assumptions) >= 10,
        "model_error_assumptions_present": model_error_assumptions_present,
        "reference_standards_comparison_present": reference_present,
        "reference_value_metrics_present": reference_value_metrics_present,
        "sensitivity_artifact_present": sensitivity_present,
        "no_arbitrary_sensitivity_threshold_language": no_arbitrary_threshold_language,
        "channel_2_and_3_not_accidental_duplicates": channel_2_3_relative_l2 is not None
        and channel_2_3_relative_l2 > 0.05,
        "frequency_domain_plot_metadata_states_log_x_axis": axis_metadata_ok,
        "qoi_sample_summary_exists": qoi_sample_summary_exists,
        "bayes_parameter_update_artifact_present": bool(bayes.get("parameter_summaries")),
        "posterior_parameter_95_ci_exists": parameter_ci_ok,
        "simulation_replicate_count_reported": simulation_replicates_documented,
        "statfem_noise_model_documented": statfem_noise_documented,
        "prior_likelihood_methodology_documented": prior_likelihood_methodology_documented,
        "method_summary_documented": method_summary_documented,
        "image_legibility_report_pass": image_legibility_pass,
        "checker_status_and_limitations_included": "## Checker Status" in report_text
        and "## Limitations" in report_text,
    }
    result = {
        "missing_files": missing_files,
        "missing_snippets": missing_snippets,
        "numeric_assumption_count": len(numeric_assumptions),
        "channel_2_3_relative_l2": channel_2_3_relative_l2,
        "checks": checks,
        "pass": all(checks.values()),
    }
    out = OUT_DIR / "checker_report_external.json"
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
