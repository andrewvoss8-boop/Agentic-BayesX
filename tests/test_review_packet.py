#!/usr/bin/env python3
"""Check the human-review packet has the expected audit content."""

from __future__ import annotations

import json
import re
from pathlib import Path


REQUIRED_MARKDOWN_SNIPPETS = [
    "# Agentic BayesX Synthetic StatFEM Packet",
    "## Scope: 2DOF, Not Two MDOFs",
    "## Question Framing",
    "## Assumptions and Units",
    "## Experimental Setup and Workflow",
    "## Measurement Channels",
    "## Key Transfer Functions (Linear Units)",
    "## Error and Uncertainty Taxonomy",
    "## Sensitivity to Assumptions",
    "## Checker Status",
    "## Diagnostics",
    "## QOI Summary",
    "## Agentic Workflow Lesson",
    "## Human Reflection",
    "channel 2 and channel 3 now use different coordinates",
    "BOED can optimize",
    "linear magnitudes, not dB",
    "NASA-HDBK-7004C source and load conventions",
    "source apparent mass has a notch",
    "load apparent mass has a peak",
    "Reference lines added to the apparent-mass panel",
    "m1 + m2 total mass",
    "Actual error hyperparameters used in this run",
    "Primary measurement view",
    "Primary error-injection view",
    "Secondary diagnostic: normalized error",
    "small `|truth|` in the denominator",
    "zero-mean squared-exponential Gaussian process over natural log frequency",
    "frequency ratio rather than an absolute Hz gap",
    "Frequency-axis note: packet frequency-domain plots use log-scaled frequency axes",
    "agent workflow miss",
    "log-frequency plot and GP coordinate postmortem",
    "GP discrepancy sample paths",
    "Retained QOI samples",
    "Posterior mean bias",
    "Fraction of retained samples above truth",
    "residual panel",
    "QOI posterior samples",
    "first-pass sensitivity artifact",
    "k12 = k2",
    "reciprocal inertance",
    "apparent mass convention postmortem",
    "2DOF machine-readable results",
    "Separate MDOF prototype result",
]

REQUIRED_FIGURES = [
    "artifacts/reports/figures/model_schematic.png",
    "artifacts/reports/figures/experimental_workflow.png",
    "artifacts/reports/figures/error_taxonomy.png",
    "artifacts/reports/figures/error_hyperparameters.png",
    "artifacts/reports/figures/channel_truth_vs_observed.png",
    "artifacts/reports/figures/channel_absolute_error.png",
    "artifacts/reports/figures/channel_error_vs_truth.png",
    "artifacts/reports/figures/gp_discrepancy_samples.png",
    "artifacts/reports/figures/parameter_error_summary.png",
    "artifacts/reports/figures/question_framing.png",
    "artifacts/reports/figures/qoi_uncertainty.png",
    "artifacts/reports/figures/qoi_samples.png",
    "artifacts/reports/figures/sampler_diagnostics.png",
]

REQUIRED_SOURCE_PLOTS = [
    "artifacts/plots/key_2dof_transfer_functions_linear.png",
]

REQUIRED_DATA_ARTIFACTS = [
    "artifacts/reports/key_frf_summary.json",
    "artifacts/reports/sensitivity_assumptions/sensitivity_assumptions.json",
    "artifacts/tests/key_transfer_functions_report.json",
    "artifacts/tests/tied_coupling_and_errors_report.json",
    "artifacts/tests/sensitivity_artifact_report.json",
]


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report_path = root / "artifacts" / "reports" / "synthetic_statfem_packet.md"
    manifest_path = root / "artifacts" / "reports" / "manifest.json"

    missing_files = [
        str(path.relative_to(root))
        for path in [
            report_path,
            manifest_path,
            *(root / f for f in REQUIRED_FIGURES),
            *(root / f for f in REQUIRED_SOURCE_PLOTS),
            *(root / f for f in REQUIRED_DATA_ARTIFACTS),
        ]
        if not path.exists()
    ]
    missing_snippets: list[str] = []
    missing_embedded_images: list[str] = []
    if report_path.exists():
        text = report_path.read_text()
        missing_snippets = [snippet for snippet in REQUIRED_MARKDOWN_SNIPPETS if snippet not in text]
        image_targets = re.findall(r"!\[[^\]]*\]\(<([^>]+)>\)", text)
        missing_embedded_images = [target for target in image_targets if not Path(target).exists()]

    manifest_ok = False
    axis_metadata_ok = False
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        manifest_ok = manifest.get("report") == "artifacts/reports/synthetic_statfem_packet.md" and all(
            fig in manifest.get("figures", []) for fig in REQUIRED_FIGURES
        ) and all(
            plot in manifest.get("source_plots", []) for plot in REQUIRED_SOURCE_PLOTS
        )
        axis_meta = manifest.get("frequency_axis_scale", {})
        axis_metadata_ok = all(
            axis_meta.get(path) == "log"
            for path in [
                "artifacts/reports/figures/channel_truth_vs_observed.png",
                "artifacts/reports/figures/channel_absolute_error.png",
                "artifacts/reports/figures/channel_error_vs_truth.png",
                "artifacts/reports/figures/gp_discrepancy_samples.png",
            ]
        )

    report = {
        "missing_files": missing_files,
        "missing_snippets": missing_snippets,
        "missing_embedded_images": missing_embedded_images,
        "manifest_ok": manifest_ok,
        "axis_metadata_ok": axis_metadata_ok,
        "pass": not missing_files and not missing_snippets and not missing_embedded_images and manifest_ok and axis_metadata_ok,
    }
    out = root / "artifacts" / "tests" / "review_packet_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
