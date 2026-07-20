#!/usr/bin/env python3
"""Checker for the ShockSat sequential statFEM PSD-envelope pilot.

Exit code is non-zero only on RED. YELLOW is an honest documented result.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent
OUT = WS / "out"


def gate(gates: list[dict], name: str, status: str, msg: str):
    gates.append({"gate": name, "status": status, "msg": msg})


def load_json(path: Path):
    return json.loads(path.read_text())


def summarize_counts(gates: list[dict]) -> dict:
    return {
        "green": sum(g["status"] == "GREEN" for g in gates),
        "yellow": sum(g["status"] == "YELLOW" for g in gates),
        "red": sum(g["status"] == "RED" for g in gates),
    }


def overall_from_counts(counts: dict) -> str:
    if counts["red"]:
        return "RED"
    if counts["yellow"]:
        return "YELLOW"
    return "GREEN"


def write_packet(results: dict, report: dict):
    overall = report["overall"]
    counts = report["counts"]
    variants = results["overall_by_variant"]
    best_variant = min(variants, key=lambda k: variants[k]["median_grms_ratio"])
    best = variants[best_variant]
    stiff = results["stiffness_update"]
    l5 = results["l5_probe_reused"]
    lines = []
    lines.append("# Packet - ShockSat sequential statFEM PSD-envelope pilot")
    lines.append("")
    lines.append(f"**Overall checker result: {overall} {counts['green']}/{counts['yellow']}/{counts['red']}.**")
    if overall == "YELLOW":
        lines.append("This is a documented validity-probe result, not a green replacement claim.")
    elif overall == "GREEN":
        lines.append("The checker found a PSD-envelope improvement under the stated gates.")
    else:
        lines.append("The checker found a blocking issue; withdraw any result claim until fixed.")
    lines.append("")
    lines.append("## First-pass method summary")
    lines.append("")
    lines.append("Plain-English statistical terms: a Bayesian filter updates the current state estimate each time a new measurement arrives. Here the state is modal displacement and modal velocity. For replayability this pilot uses a fixed-prior sequential MAP update rather than a full covariance-recursion Kalman filter. NUTS/HMC is used only for the small stiffness-subset calibration; the time-domain filter itself is not NUTS.")
    lines.append("")
    lines.append("- Model form: reduced ShockSat modal dynamics with state `x=[q, qdot]`, measured hammer force input `F_d(t)` in lbf, and sensor acceleration output in g.")
    lines.append("- Observation model: `a_obs(t) = C_obs x(t) + D_obs F_d(t) + e(t)`, with fixed Gaussian observation noise `e(t)`.")
    lines.append("- Data count: 4 clean modal-hammer references, 6 hits per reference, 84 mapped sensors, 76 observed sensors, 8 held-out sensors for the seed-0 90% split.")
    lines.append("- Data usage: whole time-history acceleration samples are assimilated for observed sensors; held-out acceptance uses only PSD-envelope metrics after FRF reconstruction.")
    lines.append("- Inferred variables: modal state through the filter; selected stiffness groups by NUTS for the stiffness-updated variant.")
    lines.append("- Fixed assumptions: damping ratio 1%, filter rate 2000 Hz, fixed process/observation hyperparameters, flat `S_F0=1 lbf^2/Hz`.")
    lines.append("- Non-inferred latent variables/hyperparameters: forcing uncertainty GP, process-noise scale, measurement-noise scale, build/test variability, and a full material field.")
    lines.append("")
    lines.append("## Decision metric")
    lines.append("")
    lines.append("| Variant | Median GRMS ratio vs FEM+6 dB | Clean-win rate | Median exceed-energy | Interpretation |")
    lines.append("|---|---:|---:|---:|---|")
    for variant, row in variants.items():
        interp = "candidate" if row["median_grms_ratio"] < 1.0 and row["clean_win_rate"] > 0 else "no PSD-envelope win"
        lines.append(f"| `{variant}` | {row['median_grms_ratio']:.3g} | {100*row['clean_win_rate']:.1f}% | {row['median_seq_exc_energy_frac']:.3g} | {interp} |")
    lines.append("")
    lines.append(f"Best median ratio: `{best_variant}` = {best['median_grms_ratio']:.3g}. The acceptance threshold is `< 1` with low held-out exceedance.")
    lines.append("")
    lines.append("## Baselines")
    lines.append("")
    lines.append("- FEM+6 dB was recomputed on the same split and smoothline convention.")
    if l5["available"]:
        med = l5["overall"]["median_grms_ratio"] if l5["overall"] else None
        lines.append(f"- Existing L5/modal-frequency PSD-envelope probe was reused from `{l5['path']}`; combined-correlated median GRMS ratio there was {med:.3g}.")
    else:
        lines.append("- Existing L5/modal-frequency probe was not available for reuse.")
    lines.append("")
    lines.append("## Discrepancy and identifiability")
    lines.append("")
    lines.append(f"Selected stiffness groups from observed-mode sensitivity/FIM: {', '.join(results['identifiability']['selected_group_names'])}.")
    if stiff.get("available"):
        diag = stiff["diag"]
        lines.append(f"Small-subset NUTS diagnostics: max R-hat {diag['max_rhat']:.3f}, min ESS {diag['min_ess']:.0f}, divergences {diag['divergences']}.")
    else:
        lines.append(f"Small-subset stiffness update was unavailable: {stiff.get('error', 'unknown error')}.")
    worst_db = max(
        r["psd_975_multiplier_db"]
        for by_ref in results["residual_calibration"].values()
        for r in by_ref.values()
    )
    lines.append(f"Worst training residual band multiplier for the sequential 97.5% PSD envelope: {worst_db:.1f} dB. Large values mean model discrepancy is doing real work and the result should stay YELLOW.")
    lines.append("")
    lines.append("## Figures")
    lines.append("")
    lines.append("- `figures/fig_method_graph.png`: run-specific filter/likelihood diagram.")
    lines.append("- `figures/fig_grms_summary.png`: median GRMS ratio by reference and variant.")
    lines.append("- `figures/fig_example_envelope.png`: one held-out PSD/envelope example with the inherited units and smoothline convention.")
    lines.append("")
    lines.append("## Checker gates")
    lines.append("")
    for g in report["gates"]:
        lines.append(f"- **{g['status']}** `{g['gate']}`: {g['msg']}")
    lines.append("")
    lines.append("## Replay")
    lines.append("")
    lines.append("Run `bash run_all.sh` from this workspace.")
    lines.append("")
    (WS / "packet.md").write_text("\n".join(lines))


def main() -> int:
    gates: list[dict] = []
    required = [
        "priority_deliverables.md",
        "decisions_log.md",
        "question_framing.md",
        "quantity_contracts.md",
        "assumptions_ledger.md",
        "run_all.sh",
        "check.py",
        "runtime.json",
        "out/results.json",
    ]
    for rel in required:
        gate(gates, f"file.{rel}", "GREEN" if (WS / rel).exists() else "RED", "present" if (WS / rel).exists() else "missing")
    if not (OUT / "results.json").exists():
        report = {"overall": "RED", "counts": summarize_counts(gates), "gates": gates}
        (WS / "checker_report.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return 1

    results = load_json(OUT / "results.json")
    runtime = load_json(WS / "runtime.json") if (WS / "runtime.json").exists() else {}

    split = results["split"]
    obs = set(split["observed_daqs"])
    held = set(split["heldout_daqs"])
    if obs & held:
        gate(gates, "split.no_leakage", "RED", "observed and held-out DAQs overlap")
    else:
        gate(gates, "split.no_leakage", "GREEN", f"{len(obs)} observed / {len(held)} held-out; disjoint")

    units = results["data"]["units"]
    unit_ok = units.get("force") == "lbf" and units.get("acceleration") == "g" and units.get("psd") == "g^2/Hz"
    gate(gates, "quantity.units", "GREEN" if unit_ok else "RED", str(units))

    details = results["detail"]
    n_rows = sum(len(rows) for by_ref in details.values() for rows in by_ref.values())
    has_metrics = n_rows > 0 and all("grms_ratio" in r and "seq_exc_energy_frac" in r for by_ref in details.values() for rows in by_ref.values() for r in rows)
    gate(gates, "psd.metrics_present", "GREEN" if has_metrics else "RED", f"{n_rows} held-out sensor-reference rows")

    best_variant = min(results["overall_by_variant"], key=lambda k: results["overall_by_variant"][k]["median_grms_ratio"])
    best = results["overall_by_variant"][best_variant]
    if best["median_grms_ratio"] < 1.0 and best["clean_win_rate"] > 0:
        gate(gates, "result.psd_improvement", "GREEN", f"{best_variant} median ratio {best['median_grms_ratio']:.3g}, clean-win {best['clean_win_rate']:.2f}")
    else:
        gate(gates, "result.psd_improvement", "YELLOW", f"no green PSD-envelope win: best {best_variant} median ratio {best['median_grms_ratio']:.3g}, clean-win {best['clean_win_rate']:.2f}")

    gate(gates, "filter.hyperparameters", "YELLOW", "process and observation noise scales are fixed validity-probe assumptions, not inferred/posterior")

    stiff = results["stiffness_update"]
    if stiff.get("available") and stiff["diag"].get("converged"):
        d = stiff["diag"]
        gate(gates, "stiffness.nuts_subset", "GREEN", f"small-subset NUTS converged: R-hat {d['max_rhat']:.3f}, ESS {d['min_ess']:.0f}, div {d['divergences']}")
    elif stiff.get("available"):
        d = stiff["diag"]
        gate(gates, "stiffness.nuts_subset", "YELLOW", f"small-subset NUTS not converged: R-hat {d['max_rhat']:.3f}, ESS {d['min_ess']:.0f}, div {d['divergences']}")
    else:
        gate(gates, "stiffness.nuts_subset", "YELLOW", f"stiffness update unavailable: {stiff.get('error', 'unknown error')}")

    worst_db = max(
        r["psd_975_multiplier_db"]
        for by_ref in results["residual_calibration"].values()
        for r in by_ref.values()
    )
    status = "YELLOW" if worst_db > 12.0 else "GREEN"
    gate(gates, "discrepancy.residual_band", status, f"worst training residual 97.5% PSD multiplier {worst_db:.1f} dB")

    if results["l5_probe_reused"]["available"]:
        gate(gates, "baseline.l5_reused", "GREEN", "existing L5/modal-frequency probe reused by path")
    else:
        gate(gates, "baseline.l5_reused", "YELLOW", "existing L5/modal-frequency probe not available")

    if runtime:
        rt_ok = runtime.get("active_runtime_s", 1e9) <= runtime.get("elapsed_wallclock_s", -1)
        gate(gates, "runtime.accounting", "GREEN" if rt_ok else "RED", f"active={runtime.get('active_runtime_s')} elapsed={runtime.get('elapsed_wallclock_s')}")
    else:
        gate(gates, "runtime.accounting", "RED", "runtime.json missing or unreadable")

    fig_paths = ["figures/fig_method_graph.png", "figures/fig_grms_summary.png", "figures/fig_example_envelope.png"]
    figs_ok = all((WS / p).exists() for p in fig_paths)
    gate(gates, "figures.present", "GREEN" if figs_ok else "RED", ", ".join(fig_paths))
    qa_path = OUT / "image_qa.json"
    if qa_path.exists():
        qa = load_json(qa_path)
        qa_ok = all(v.get("legible_min_size_px") for v in qa.values())
        gate(gates, "figures.image_qa", "GREEN" if qa_ok else "RED", json.dumps(qa))
    else:
        gate(gates, "figures.image_qa", "RED", "image_qa.json missing")
    lint_path = OUT / "tufte_lint.txt"
    gate(gates, "figures.tufte_lint", "GREEN" if lint_path.exists() else "RED", "lint output present" if lint_path.exists() else "missing lint output")

    counts = summarize_counts(gates)
    overall = overall_from_counts(counts)
    report = {
        "task": "ShockSat sequential statFEM PSD-envelope pilot",
        "overall": overall,
        "counts": counts,
        "gates": gates,
        "headline": f"{overall}: best variant {best_variant} median GRMS ratio {best['median_grms_ratio']:.3g}; clean-win rate {best['clean_win_rate']:.2f}",
    }
    (WS / "checker_report.json").write_text(json.dumps(report, indent=2))
    write_packet(results, report)
    print(json.dumps(report, indent=2))
    return 1 if overall == "RED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
