#!/usr/bin/env python3
"""Finish the terminal packet, figures, QA, runtime, and checker report."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from common import REPO, WS, read_json, write_json


def table_row(cols):
    return "| " + " | ".join(str(x) for x in cols) + " |"


def main() -> None:
    t0 = time.time()
    subprocess.run([sys.executable, str(WS / "code/figures.py")], cwd=WS, check=True)
    lint = subprocess.run([sys.executable, str(REPO / ".claude/skills/tufte-data-graphics/scripts/tufte_lint.py"),
                           str(WS / "code/figures.py")], cwd=REPO, text=True, capture_output=True)
    (WS / "out/tufte_lint.txt").write_text(lint.stdout + lint.stderr + f"\nexit_code={lint.returncode}\n")
    subprocess.run([sys.executable, str(WS / "code/fig_qa.py")], cwd=WS, check=True)

    syn = read_json(WS / "out/synthetic_results.json")
    known = read_json(WS / "out/known_answers.json")
    decision = read_json(WS / "automatic_decision.json")
    inv = read_json(WS / "data_inventory.json")
    measured = read_json(WS / "out/stage1_results.json") if (WS / "out/stage1_results.json").exists() else None
    runtime = read_json(WS / "runtime.json")
    active = float(decision["stage1_active_runtime_s"]) + (time.time() - t0)
    start = float(read_json(WS / "source_manifest.json")["created_unix"])
    elapsed = max(time.time() - start, active)
    runtime.update({"active_runtime_s": active, "elapsed_wallclock_s": elapsed})
    runtime.setdefault("commands", []).append({"name": "finalize", "active_s": time.time() - t0})
    write_json(WS / "runtime.json", runtime)

    checkpoint = ["# Stage 1 checkpoint", "", f"Automatic path: **{decision['chosen_terminal_path']}**", "",
                  decision["reason"], "", "## Synthetic transition gates", "",
                  "| Case | Frozen threshold | Observed | Result |", "|---|---|---|---|"]
    for case, rec in syn["gates"].items():
        observed = ", ".join(f"{k}={v}" for k, v in rec.items() if k not in {"threshold", "pass"})
        checkpoint.append(table_row([case, rec["threshold"], observed, "GREEN" if rec["pass"] else "YELLOW miss"]))
    checkpoint += ["", f"Stage 1 active runtime: {active:.2f} s of 7,200 s cap.",
                   "The checkpoint is terminal when the path is a STOP path; no approval pause is requested."]
    (WS / "stage1_checkpoint.md").write_text("\n".join(checkpoint) + "\n")

    packet = [
        "# ShockSat structured-discrepancy Card E — review packet",
        "",
        f"**Terminal path: {decision['chosen_terminal_path']}. Overall scientific status: YELLOW unless the immutable checker reports RED.**",
        "",
        "## First-pass method summary",
        "",
        "Model: `r(d,i,s;theta) = H(f_s,x_i,a_i) beta + u(f_s,x_i,a_i) + e`, with `beta ~ Normal(0,Lambda_beta)`, `u ~ GP(0,K_fx)`, and `e ~ Normal(0,sigma_e^2)`. The likelihood uses whole natural-log H1 magnitude curves, not peaks or selected resonance features.",
        "",
        f"Data inventory: {inv['measured_vs_synthetic']['measured_drive_caches']} measured drive caches; {inv['eligible_common_response_channels']} common mapped eligible response channels; the exact primary study freezes {inv['selected_response_channels']} design/axis-balanced channels × {inv['analysis_frequency_lines']} frequency lines from {inv['analysis_range_hz'][0]:.0f}–{inv['analysis_range_hz'][1]:.0f} Hz. The synthetic gate uses 4 cases × 20 deterministic seeds. Source H1 curves average retained impacts, but repeat-level variability is not modeled.",
        "",
        "Inferred/conditioned in Stage 1: per-drive gain on retained data, training-only GP amplitude, conditional beta, and conditional GP. Fixed: FEM model form, damping, basis rules, primary length scales and split, observation scale, and all outer folds. Not inferred: channel-identity effects, drive×frequency forcing, axis misorientation, build variability, and repeat-to-repeat impact variability. Modal parameter uncertainty is modular: retained draws from the converged modal posterior are not response-updated.",
        "",
        "Split families: five leave-drive-out, five coordinate-only spatial clusters, five contiguous frequency cores with 10 Hz guards, and five hash-frozen joint spatial×frequency cells. Fold—not frequency line—is the independent unit.",
        "",
        "Mechanism separation: E0 and E1 share one training covariance fit; E0 suppresses train-to-test covariance while E1 conditions the zero-mean GP. E2 adds a learned conditional mean. E3 projects that basis locally away from theta sensitivities. Every retained conditional stores `E[H_* beta|train]`, `E[u_*|train]`, their variance terms, cross-covariance, and total variance separately.",
        "",
        "## Result",
        "",
        decision["reason"],
        "",
        "### Synthetic gates",
        "",
        "| Case | Key observed value | Threshold | Status |", "|---|---:|---|---|",
    ]
    for case, rec in syn["gates"].items():
        obs = "; ".join(f"{k}={v}" for k, v in rec.items() if k not in {"threshold", "pass"})
        packet.append(table_row([case, obs, rec["threshold"], "GREEN" if rec["pass"] else "YELLOW — gate missed"]))
    packet += [
        "",
        "A missed synthetic gate is not a measured negative-transfer result. It means the preregistered procedure could not establish the required false-positive, recovery, robustness, or confounding behavior on known truth; Card E therefore forbids interpreting measured arms.",
        "",
        "## Frozen known-answer and integrity evidence",
        "",
        f"The frozen M0–M3 summaries parsed exactly. M0 is the only converged legacy TMCMC result. M1–M3 remain non-converged; worst M2 R-hat/ESS are {known['legacy_M0_M3']['M2']['max_rhat']:.3f}/{known['legacy_M0_M3']['M2']['min_ess']:.3f}, and M3 are {known['legacy_M0_M3']['M3']['max_rhat']:.3f}/{known['legacy_M0_M3']['M3']['min_ess']:.2f}. Their intervals are not trustworthy.",
        "",
        f"Three additive-kernel covariance eigenvalues were independently reproduced by dense eigendecomposition and the Kronecker eigenvalue formula; maximum absolute difference was {max(x['abs_difference'] for x in known['deterministic_recomputations']['covariance_eigenvalues']):.3e}. The legacy residual and spatial values also reproduced: n=77, median absolute residual 6.596 dB, hard channels 17.452 dB versus 6.535 dB for the rest, and region R²=0.036.",
        "",
        "The immutable checker was proven RED before science output. Source hashes include the task card, two papers, legacy summaries/code, modal posterior, FEM/reduced-model inputs, measured H1 caches, preregistration, split registry, basis registry, quantity contract, and checker.",
        "",
        "## Modal identifiability and physical mechanism",
        "",
        f"Modal strain-energy fractions were recomputed from the reduced stiffness blocks with mean closure {known['modal_identifiability']['closure_mean']:.12f}. At the realized modal discrepancy floor sigma_f={known['modal_identifiability']['sigma_f_floor']:.4f}, {known['modal_identifiability']['n_parameter_combinations_clearing_prior_precision']} prior-whitened parameter combinations exceed prior precision. The contact finite perturbation is classified as `{known['modal_identifiability']['finite_perturbation']['cause']}`; this prevents an unsupported out-of-load-path claim.",
        "",
        "## Assumptions, sensitivity, and limits",
        "",
        "The selected 15-channel geometry is a bounded exact-Gaussian feasibility study, not evidence for every one of the 111 cached channels. Axis/region balance impossibilities are stored in the split registry. With only five folds per family, even a crossed measured threshold would carry weak uncertainty.",
        "",
        "The primary 2.5 Hz grid gives four lines per 10 Hz covariance length but cannot certify sharp individual resonance amplitudes. Because the automatic synthetic stop occurs before measured fitting, the preregistered 1.25 Hz measured resolution refinement and training-only learned-length sensitivity are logged gaps rather than silently inferred results. This limits the result to the synthetic procedure gate.",
        "",
        "The two-paper literature claim is narrow: the requested learned frequency×location mean is absent from Febrianto et al. (2022) and Schneider et al. (2022). No literature-wide novelty claim is made.",
        "",
        "## Figures and replay",
        "",
        "Figures are generated by `code/figures.py`; numeric figures state run provenance and terminal validity in their footers. Tufte heuristic lint and pixel/legibility QA are stored under `out/`. Replay command: `bash run_all.sh` (resumable; frozen registries are not regenerated once `source_manifest.json` exists).",
        "",
        "## Closure-brief wording",
        "",
        "The proposed Schneider correction is in `closure_brief_correction.md`. This run does not revise the delivered brief.",
        "",
        f"Runtime: active {active:.2f} s; elapsed wall clock {elapsed:.2f} s; active <= elapsed and below the 8 h hard cap.",
    ]
    if measured:
        packet += ["", "## Measured Stage 1", "", "Measured fitting ran because all synthetic gates passed. See `out/stage1_results.json` for paired fold effects and the automatic decision for the permitted terminal path."]
    (WS / "packet.md").write_text("\n".join(packet) + "\n")

    # Produce checker report, then append its exact status to the packet.
    subprocess.run([sys.executable, str(WS / "check.py"), "--report", str(WS / "out/checker_report.json")], cwd=WS, check=False)
    report = read_json(WS / "out/checker_report.json")
    with (WS / "packet.md").open("a") as f:
        f.write(f"\n## Immutable checker\n\n**OVERALL {report['overall_status']} {report['counts']}**\n")
    print("FINALIZED", decision["chosen_terminal_path"], report["overall_status"], report["counts"])


if __name__ == "__main__":
    main()
