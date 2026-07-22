#!/usr/bin/env python3
"""Apply Card E's ordered automatic transition rules."""
from __future__ import annotations

import time

from common import WS, read_json, write_json


def main() -> None:
    if (WS / "out/stage2_results.json").exists() and (WS / "automatic_decision.json").exists():
        print("automatic_decision.json immutable because Stage 2 output exists")
        return
    syn = read_json(WS / "out/synthetic_results.json")
    runtime = read_json(WS / "runtime.json")
    active = float(runtime.get("active_runtime_s", 0)) + float(read_json(WS / "out/known_answers.json").get("runtime_s", 0)) + float(syn.get("runtime_s", 0))
    measured = read_json(WS / "out/stage1_results.json") if (WS / "out/stage1_results.json").exists() else None
    if measured:
        active += float(measured.get("runtime_s", 0))

    threshold = {
        "S0_false_positive_max": 1,
        "S1_success_min": 16,
        "S1_mean_coverage_min": 0.85,
        "S2_worse_than_2db_max": 2,
        "S3_bias_reduction_min": 0.50,
        "S3_each_theta_coverage_min": 0.80,
        "orthogonality_max": 1e-8,
        "measured_error_reduction_db_min": 2.0,
        "measured_width_reduction_fraction_min": 0.20,
        "coverage_loss_max": 0.02,
        "crps_fold_wins_min": 4,
        "E3_retained_E2_gain_min": 0.80,
        "stage1_active_runtime_cap_s": 7200,
        "stage2_additional_cap_s": 21600,
    }
    observed = {"synthetic_gates": syn["gates"]}
    if not syn["all_synthetic_gates_pass"]:
        path = "STOP_SYNTHETIC"
        reason = "At least one preregistered S0-S3 gate missed; measured responses are prohibited."
    elif measured is None:
        path = "STOP_NEGATIVE"
        reason = "Synthetic gates passed but measured evidence is not yet present; conservative provisional stop."
    else:
        fam = measured["family_decisions"]
        observed["measured_family_decisions"] = fam
        spatial = fam["spatial"]["E3_vs_E1_success"] and fam["spatial"]["lower_crps_fold_count"] >= 4
        frequency = fam["frequency"]["E3_vs_E1_success"] and fam["frequency"]["lower_crps_fold_count"] >= 4
        e2gain = measured["confounding"]["E3_retained_fraction_of_E2_error_gain"]
        s3ok = syn["gates"]["S3"]["pass"]
        if measured["confounding"]["E2_succeeds_any"] and (e2gain < 0.80 or not s3ok):
            path, reason = "STOP_CONFOUNDED", "E2 gain was not retained by protected E3 or S3 protection failed."
        elif (spatial and frequency and e2gain >= 0.80 and not measured.get("any_red_gate", False)
              and active <= 7200 and measured.get("stage2_projected_runtime_s", 1e99) <= 21600):
            path, reason = "PROCEED_JOINT", "Every synthetic, spatial, frequency, CRPS, protection, status, and runtime gate permits Stage 2."
        elif spatial ^ frequency:
            path, reason = "STOP_PARTIAL_MEAN", "Protected mean crossed the bar in exactly one of spatial/frequency transfer."
        elif measured["family_decisions"]["propagation_any_primary_family"]:
            path, reason = "STOP_PROPAGATION_ONLY", "GP conditioning transferred in at least one primary family; protected mean did not satisfy preceding rules."
        else:
            path, reason = "STOP_NEGATIVE", "Neither conditioning nor structured mean crossed the frozen transfer bar."
    out = {
        "written_unix": time.time(),
        "chosen_terminal_path": path,
        "reason": reason,
        "thresholds": threshold,
        "observed": observed,
        "all_synthetic_gates_pass": syn["all_synthetic_gates_pass"],
        "stage1_active_runtime_s": active,
        "stage1_cap_s": 7200,
        "projected_stage2_runtime_s": None if measured is None else measured.get("stage2_projected_runtime_s"),
        "remaining_stage2_cap_s": 21600,
        "missing_evidence_resolves_conservatively": True,
    }
    write_json(WS / "automatic_decision.json", out)
    print(path, reason)


if __name__ == "__main__":
    main()
