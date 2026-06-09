#!/usr/bin/env python3
"""Acceptance checks for the Vibrationdata conical-shell packet."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "reports" / "conical_shell_statfem_ladder_20260608"


def load_json(name: str) -> dict:
    return json.loads((OUT_DIR / name).read_text())


def main() -> int:
    required = [
        "conical_shell_packet.md",
        "source_manifest.json",
        "nastran_summary.json",
        "published_modal_comparison.json",
        "human_nastran_solution.json",
        "local_solve_comparison.json",
        "frf_digitized_features.json",
        "modal_statfem_v1_results.json",
        "frf_qoi_summary.json",
        "assumptions_ledger.md",
        "assumptions_ledger.json",
        "quantity_contracts.md",
        "digital_twin_launch_definition.md",
        "digital_twin_launch_definition.json",
        "image_legibility_report.json",
        "manifest.json",
        "checker_report.json",
        "figures/source_nastran_mesh.png",
        "figures/human_nastran_frequency_table.png",
        "figures/local_solve_vs_published_modal_comparison.png",
        "figures/published_modal_frequency_comparison.png",
        "figures/published_frequency_error.png",
        "figures/published_peak_evidence_log_frequency.png",
        "figures/digitized_frf_peak_features.png",
        "figures/modal_statfem_v1_posterior_and_holdout.png",
        "figures/frf_qoi_peak_accelerance.png",
        "figures/mode_shape_status_not_solver_output.png",
        "figures/statfem_launch_graphical_model.png",
    ]
    missing = [p for p in required if not (OUT_DIR / p).exists()]

    report = (OUT_DIR / "conical_shell_packet.md").read_text() if (OUT_DIR / "conical_shell_packet.md").exists() else ""
    snippets = [
        "## Method Summary",
        "## Source Provenance",
        "## Published Test/FEM Comparison",
        "## Parsed Source FEM Metadata",
        "## Mode-Shape Evidence Status",
        "## FRF Evidence",
        "## Modal-Only StatFEM v1",
        "## FRF/QOI Layer",
        "## Digital Twin Launch",
        "What This Does Not Prove",
        "modal-only v1 digital-twin sandbox",
        "mode 1 agreement is useful provenance, not independent validation",
        "not NUTS/HMC",
    ]
    missing_snippets = [s for s in snippets if s not in report]

    source = load_json("source_manifest.json") if not missing else {}
    nas = load_json("nastran_summary.json") if not missing else {}
    published = load_json("published_modal_comparison.json") if not missing else {}
    launch = load_json("digital_twin_launch_definition.json") if not missing else {}
    human = load_json("human_nastran_solution.json") if not missing else {}
    local = load_json("local_solve_comparison.json") if not missing else {}
    statfem = load_json("modal_statfem_v1_results.json") if not missing else {}
    qoi = load_json("frf_qoi_summary.json") if not missing else {}
    assumptions = load_json("assumptions_ledger.json") if not missing else {"rows": []}
    image = load_json("image_legibility_report.json") if not missing else {}

    rows = published.get("rows", [])
    checks = {
        "missing_files": missing,
        "missing_snippets": missing_snippets,
        "source_pdf_fetched": source.get("pdf", {}).get("status") == "fetched",
        "source_nas_fetched": source.get("nas", {}).get("status") == "fetched",
        "browser_access_quirk_recorded": source.get("nas_browser_like_access", {}).get("http_status") == 406,
        "checksums_recorded": bool(source.get("pdf", {}).get("sha256")) and bool(source.get("nas", {}).get("sha256")),
        "nastran_metadata_present": nas.get("node_count", 0) > 900
        and nas.get("element_count", 0) > 800
        and nas.get("pshell", {}).get("thickness_in") == 0.1,
        "free_boundary_recorded": nas.get("free_boundary_condition") is True,
        "published_modes_present": len(rows) == 4
        and rows[0].get("measured_hz") == 97.6
        and rows[3].get("published_preliminary_fea_hz") == 523.0,
        "missing_fea_mode_preserved": len(rows) >= 3 and rows[2].get("published_preliminary_fea_hz") is None,
        "assumptions_include_tuning_warning": any(
            row.get("assumption") == "Source FEM tuning" for row in assumptions.get("rows", [])
        ),
        "human_nastran_modes_ingested": len(human.get("modes", [])) == 20
        and len(human.get("flexible_pairs", [])) == 7
        and len(human.get("screenshots", [])) >= 3,
        "local_solve_comparison_present": len(local.get("rows", [])) == 4
        and local["rows"][0].get("human_nastran_mean_hz", 0) > 97.0,
        "modal_statfem_active": statfem.get("statfem_active") is True
        and statfem.get("method", "").startswith("exact grid")
        and statfem.get("holdout_predictions", [{}])[0].get("covered_by_90pct_interval") is True,
        "frf_qoi_present_and_labeled": "coarse visual" in json.dumps(qoi).lower()
        and qoi.get("qoi", {}).get("median_peak_g_per_lbf", 0) > 0,
        "statfem_not_overclaimed": launch.get("statfem_active") is True
        and "Raw FRF ordinates were not extracted" in " ".join(launch.get("why_not_active_yet", [])),
        "image_legibility_basic_pass": image.get("pass") is True,
    }
    checks["pass"] = (
        not checks["missing_files"]
        and not checks["missing_snippets"]
        and all(v is True for k, v in checks.items() if k not in {"missing_files", "missing_snippets", "pass"})
    )

    external_path = OUT_DIR / "checker_report_external.json"
    external_path.write_text(json.dumps(checks, indent=2, sort_keys=True))
    print(json.dumps(checks, indent=2, sort_keys=True))
    return 0 if checks["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
