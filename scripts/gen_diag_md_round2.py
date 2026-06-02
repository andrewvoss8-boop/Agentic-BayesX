#!/usr/bin/env python3
"""Render nuts_diagnostics.md and manifest.json from the pipeline JSON outputs."""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "artifacts/reports/runner_claude_opus48_round2_20260602"


def main():
    d = json.loads((OUT / "nuts_diagnostics.json").read_text())
    pv = d["per_variable"]
    gate = d["gate_thresholds"]
    conv = d["converged"]
    div = d["divergences"]
    lines = []
    lines.append("# NUTS Diagnostics — Round 2 (Claude Opus 4.8)\n")
    verdict = "PASS — converged; NUTS active" if conv else "NOT CONVERGED — do not treat as final"
    lines.append(f"**Verdict: {verdict}.**\n")
    if conv and div > 0:
        lines.append(f"> HARD-WARN: {div} divergence(s) observed. Even a few divergences cannot be "
                     "safely ignored (Stan); treat as a minor bias risk and confirm by eye.\n")
    elif conv and div == 0:
        lines.append("> 0 divergences — ideal (no divergence-related bias risk flagged).\n")
    lines.append("## Sampler\n")
    lines.append(f"- Sampler: {d['sampler']}; chains: {d['n_chains']}; warmup: {d['n_warmup']}; "
                 f"draws/chain: {d['n_draws_per_chain']}; total post-warmup draws: {d['total_post_warmup_draws']}.")
    lines.append(f"- target_accept_prob: {d['target_accept_prob']}; max_tree_depth setting: "
                 f"{d['max_tree_depth_setting']} (observed max {d['max_tree_depth_observed']:.2f}); "
                 f"mean leapfrog steps/iter: {d['mean_num_steps']:.1f}.")
    lines.append(f"- Parameterization: non-centered hierarchical build effects (build = sigma_build * z).")
    lines.append(f"- Fit runtime (sampling only, excludes compile): {d['fit_runtime_s']:.1f} s.\n")
    lines.append("## Source-backed gate (Stan Reference Manual / Vehtari et al. 2021)\n")
    lines.append(f"- rank-normalized split-R-hat < {gate['rank_split_rhat_max']} "
                 f"(1.05 only as labeled early-workflow fallback — NOT used as the pass bar).")
    lines.append(f"- bulk-ESS AND tail-ESS >= {gate['ess_bulk_min']} (= 100 x {d['n_chains']} chains).")
    lines.append(f"- divergence fraction < {gate['divergence_fraction_fail']} to avoid FAIL; 0 ideal.\n")
    lines.append("## Worst-case over ALL sampled variables (incl raw latents)\n")
    lines.append(f"- worst rank-split-R-hat = **{d['worst_rank_split_rhat']['value']:.4f}** "
                 f"({d['worst_rank_split_rhat']['variable']}) — {'PASS' if d['gate_rhat_pass'] else 'FAIL'}")
    lines.append(f"- min bulk-ESS = **{d['min_ess_bulk']['value']:.0f}** "
                 f"({d['min_ess_bulk']['variable']}) — {'PASS' if d['gate_ess_pass'] else 'FAIL'}")
    lines.append(f"- min tail-ESS = **{d['min_ess_tail']['value']:.0f}** "
                 f"({d['min_ess_tail']['variable']})")
    lines.append(f"- divergences = **{div}** (fraction {d['divergence_fraction']:.2e}) — "
                 f"{'PASS' if d['gate_divergence_pass'] else 'FAIL'}")
    lines.append(f"- monitored scalar quantities (incl every raw z): **{d['n_monitored_scalar_quantities']}**\n")
    lines.append("## Per-variable table (rank-split-R-hat / bulk-ESS / tail-ESS)\n")
    lines.append("| variable | R-hat | ESS bulk | ESS tail |")
    lines.append("|---|---:|---:|---:|")
    for name, m in pv.items():
        lines.append(f"| {name} | {m['rank_split_rhat']:.4f} | {m['ess_bulk']:.0f} | {m['ess_tail']:.0f} |")
    fc = d["forcing_constants_fixed"]
    lines.append("\n## Fixed forcing constants (flight-to-flight 3 dB is KNOWN, not learned)\n")
    lines.append(f"- sigma_q (log-3GRMS scatter from forcing): tray {fc['sigma_q_tray']:.3f}, "
                 f"interface {fc['sigma_q_iface']:.3f}; bias_tray {fc['bias_tray']:.3f}, "
                 f"bias_iface {fc['bias_iface']:.3f}; MC samples {fc['n_mc']}.")
    (OUT / "nuts_diagnostics.md").write_text("\n".join(lines) + "\n")

    # manifest
    manifest = {
        "trial_id": "runner_claude_opus48_round2_20260602",
        "runner": "Claude Code Opus 4.8",
        "date": "2026-06-02",
        "one_command_replay": "bash scripts/run_runner_claude_opus48_round2.sh",
        "pipeline": "scripts/runner_claude_opus48_round2.py",
        "forward_model": "scripts/r2_forward.py",
        "checker": "scripts/check_round2_artifacts.py (runner-local, non-immutable)",
        "dataset_consumed": "artifacts/reports/sequential_vibe_modal_flight_20260602/sequential_dataset.json",
        "sampler": d["sampler"], "n_chains": d["n_chains"],
        "converged": conv, "nuts_active": d["nuts_active"], "divergences": div,
        "worst_rank_split_rhat": d["worst_rank_split_rhat"],
        "min_ess_bulk": d["min_ess_bulk"], "min_ess_tail": d["min_ess_tail"],
        "key_deliverable": "figures/interface_response_psd_vs_spec.gif",
        "figures": [
            "figures/interface_response_psd_vs_spec.gif",
            "figures/flight_forcing_overlay.png",
            "figures/flight_qoi_vs_vibe_reference.png",
            "figures/resolution_sensitivity.png",
            "figures/posterior_recovery.png",
            "figures/sequential_assimilation_qoi.png",
        ],
        "docs": [
            "priority_deliverables.md", "quantity_contracts_round2.md", "assumptions_ledger.md",
            "resolution_analysis.md", "nuts_diagnostics.md", "commands.md", "files_changed.md",
            "known_failures.md", "review_request.md", "packet.md",
        ],
        "machine_readable": [
            "nuts_diagnostics.json", "interface_psd_bands.json", "resolution_metrics.json",
            "checks.json", "runtime.json", "posterior_samples.npz",
        ],
        "immutable_checkers_unchanged": True,
        "status": "complete" if conv else "complete_not_converged",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("wrote nuts_diagnostics.md and manifest.json; converged=", conv, "div=", div)


if __name__ == "__main__":
    main()
