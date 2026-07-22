#!/usr/bin/env python3
"""Immutable checker for the structured-discrepancy Card E run."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


DEFAULT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


def load(path: Path):
    return json.loads(path.read_text())


def gate(name, status, evidence):
    return {"name": name, "status": status, "evidence": evidence}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", type=Path, default=DEFAULT)
    ap.add_argument("--report", type=Path)
    args = ap.parse_args()
    ws = args.workspace.resolve()
    g = []

    required_freeze = ["priority_deliverables.md", "question_framing.md", "assumptions_ledger.md",
                       "quantity_contracts.md", "data_inventory.json", "split_registry.json",
                       "mean_basis_registry.json", "preregistration.md", "decisions_log.md",
                       "source_manifest.json", "check.py", "CHECKER.sha256", "run_all.sh", "runtime.json"]
    missing = [p for p in required_freeze if not (ws / p).exists()]
    g.append(gate("freeze_artifacts", "RED" if missing else "GREEN", {"missing": missing}))

    manifest_path = ws / "source_manifest.json"
    hash_bad = []
    if manifest_path.exists():
        repo = ws.parents[2]
        for rec in load(manifest_path).get("files", []):
            p = Path(rec["path"])
            p = p if p.is_absolute() else repo / p
            if not p.exists() or digest(p) != rec["sha256"] or p.stat().st_size != rec["size"]:
                hash_bad.append(rec["path"])
    else:
        hash_bad.append("source_manifest.json missing")
    g.append(gate("source_and_predecessor_hashes", "RED" if hash_bad else "GREEN", {"mismatches": hash_bad}))

    canary = ws / "qa/checker_empty_report.json"
    canary_ok = False
    if canary.exists():
        try:
            c = load(canary)
            canary_ok = c.get("overall_status") == "RED" and c.get("canary", False)
        except Exception:
            pass
    g.append(gate("red_on_empty_canary", "GREEN" if canary_ok else "RED", {"path": str(canary)}))

    q = (ws / "quantity_contracts.md").read_text() if (ws / "quantity_contracts.md").exists() else ""
    qok = "ln(|H1_meas" in q and "H_ref = 1 g/lbf" in q and "20/log(10) * q" in q
    g.append(gate("quantity_contract_and_db", "GREEN" if qok else "RED", {}))

    splits_ok = False
    if (ws / "split_registry.json").exists():
        s = load(ws / "split_registry.json")
        splits_ok = len(s.get("drives", [])) == 5 and len(s.get("spatial", [])) == 5 and len(s.get("frequency", [])) == 5
        splits_ok &= all(x.get("guard_hz") == 10.0 for x in s.get("frequency", []))
    g.append(gate("split_registry_and_guards", "GREEN" if splits_ok else "RED", {}))

    known_path = ws / "out/known_answers.json"
    known_ok = False
    if known_path.exists():
        k = load(known_path)
        known_ok = k.get("all_pass", False) and k.get("deterministic_recomputations", {}).get("count", 0) >= 3
        known_ok &= k.get("modal_identifiability", {}).get("strain_energy_present", False)
        known_ok &= k.get("modal_identifiability", {}).get("realized_floor_fim_present", False)
    g.append(gate("known_answers_and_modal_identifiability", "GREEN" if known_ok else "RED", {}))

    syn_path = ws / "out/synthetic_results.json"
    syn_ok = False
    syn_gate_pass = False
    eq_ok = False
    contrib_ok = False
    constraint_ok = False
    if syn_path.exists():
        s = load(syn_path)
        syn_ok = all(len(s.get("cases", {}).get(c, {}).get("seeds", [])) >= 20 for c in ["S0", "S1", "S2", "S3"])
        syn_gate_pass = s.get("all_synthetic_gates_pass", False)
        eq_ok = s.get("e0_e1_training_fit_identical", False)
        contrib_ok = s.get("separate_posterior_contributions_stored", False)
        constraint_ok = s.get("max_constraint_residual", 1.0) <= 1e-8 and s.get("max_normalized_orthogonality_residual", 1.0) <= 1e-8
    g.append(gate("synthetic_s0_s3_20_seeds", "GREEN" if syn_ok else "RED", {}))
    g.append(gate("e0_e1_identical_training_fit", "GREEN" if eq_ok else "RED", {}))
    g.append(gate("mean_gp_contributions_separate", "GREEN" if contrib_ok else "RED", {}))
    g.append(gate("basis_constraints_and_orthogonality", "GREEN" if constraint_ok else "RED", {}))

    decision_path = ws / "automatic_decision.json"
    decision = load(decision_path) if decision_path.exists() else {}
    path = decision.get("chosen_terminal_path")
    decision_ok = path in {"STOP_SYNTHETIC", "STOP_CONFOUNDED", "PROCEED_JOINT", "STOP_PARTIAL_MEAN",
                           "STOP_PROPAGATION_ONLY", "STOP_NEGATIVE"}
    decision_ok &= "thresholds" in decision and "observed" in decision and "stage1_active_runtime_s" in decision
    g.append(gate("automatic_decision_complete", "GREEN" if decision_ok else "RED", {"path": path}))

    measured_needed = syn_gate_pass and path != "STOP_SYNTHETIC"
    measured_path = ws / "out/stage1_results.json"
    measured_ok = measured_path.exists() if measured_needed else True
    if measured_path.exists():
        m = load(measured_path)
        measured_ok &= m.get("outer_test_tuning", True) is False
        measured_ok &= m.get("separate_posterior_contributions_stored", False)
        measured_ok &= m.get("e0_e1_training_fit_identical", False)
    g.append(gate("measured_stage1_when_permitted", "GREEN" if measured_ok else "RED", {"required": measured_needed}))

    stage2_required = path == "PROCEED_JOINT"
    stage2_path = ws / "out/stage2_results.json"
    if stage2_required:
        stage2_ok = stage2_path.exists()
        if stage2_ok:
            j = load(stage2_path)
            diag = j.get("all_variable_diagnostics", {})
            stage2_ok &= diag.get("n_chains", 0) >= 4 and "worst_rhat" in diag and "min_ess" in diag and "divergence_fraction" in diag
    else:
        stage2_ok = True
    g.append(gate("stage2_nuts_diagnostics_if_run", "GREEN" if stage2_ok else "RED", {"required": stage2_required}))

    figure_req = ["fig_graphical_model.png", "fig_synthetic_recovery.png", "fig_fold_effects.png",
                  "fig_identifiability.png", "fig_beta_prior_check.png"]
    if measured_path.exists():
        figure_req.append("fig_heldout_frf.png")
    fig_missing = [p for p in figure_req if not (ws / "figures" / p).exists()]
    lint = ws / "out/tufte_lint.txt"
    qa = ws / "out/fig_qa.json"
    fig_ok = not fig_missing and lint.exists() and qa.exists() and load(qa).get("all_legible", False)
    g.append(gate("figures_lint_legibility_and_labels", "GREEN" if fig_ok else "RED", {"missing": fig_missing}))

    finals = ["packet.md", "stage1_checkpoint.md", "automatic_decision.json", "closure_brief_correction.md",
              "runtime.json"]
    fm = [p for p in finals if not (ws / p).exists()]
    g.append(gate("completion_packet", "RED" if fm else "GREEN", {"missing": fm}))

    runtime_ok = False
    if (ws / "runtime.json").exists():
        r = load(ws / "runtime.json")
        runtime_ok = 0 <= r.get("active_runtime_s", -1) <= r.get("elapsed_wallclock_s", -2)
        runtime_ok &= r.get("active_runtime_s", 1e99) <= 28800
    g.append(gate("runtime_accounting", "GREEN" if runtime_ok else "RED", {}))

    # A scientifically failed but completely documented synthetic gate is YELLOW, not RED.
    if syn_ok and not syn_gate_pass and decision_ok and path == "STOP_SYNTHETIC":
        g.append(gate("scientific_result", "YELLOW", {"caveat": "one or more preregistered synthetic gates missed; measured fitting prohibited"}))
    elif decision_ok:
        g.append(gate("scientific_result", "YELLOW", {"caveat": "five-fold transfer uncertainty is weak; status cannot exceed evidence"}))
    else:
        g.append(gate("scientific_result", "RED", {"caveat": "no valid terminal decision"}))

    counts = {s: sum(x["status"] == s for x in g) for s in ["GREEN", "YELLOW", "RED"]}
    overall = "RED" if counts["RED"] else ("YELLOW" if counts["YELLOW"] else "GREEN")
    report = {"overall_status": overall, "counts": counts, "gates": g,
              "canary": bool(args.report and args.report.name == "checker_empty_report.json")}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(f"OVERALL {overall} {counts}")
    for x in g:
        print(f"{x['status']:6s} {x['name']}")
    return 1 if overall == "RED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
