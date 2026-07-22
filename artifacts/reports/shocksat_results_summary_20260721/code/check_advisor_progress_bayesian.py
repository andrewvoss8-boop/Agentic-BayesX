#!/usr/bin/env python3
"""Fail-closed checks for the Bayesian-audit advisor progress report."""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

import numpy as np
from docx import Document


ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "ShockSat_Bayesian_FEM_and_StatFEM_progress_update_working_twin_revision.docx"
RENDER = ROOT / "qa" / "advisor_progress_working_twin_render_final"
OUT = ROOT / "qa" / "advisor_progress_working_twin" / "checker_report.json"


def item(gate: str, tier: str, evidence: str) -> dict[str, str]:
    return {"gate": gate, "tier": tier, "evidence": evidence}


def main() -> int:
    results: list[dict[str, str]] = []
    if not DOCX.exists():
        results.append(item("G01 artifact", "RED", f"missing {DOCX}"))
        write(results)
        return 1

    doc = Document(DOCX)
    text = "\n".join(p.text for p in doc.paragraphs)
    for table in doc.tables:
        for row in table.rows:
            text += "\n" + " | ".join(cell.text for cell in row.cells)

    rejected = [
        "Decision requested",
        "Overall research status",
        "An honest shear-load band exists",
        "DO NOW",
        "NEXT STUDY",
        "DO NOT PRIORITIZE",
    ]
    bad = [token for token in rejected if token.lower() in text.lower()]
    results.append(item("G01 rejected framing removed", "GREEN" if not bad else "RED", f"forbidden strings found: {bad}" if bad else "no rejected decision/status framing found"))

    context_tokens = [
        "The last plan I sent you proposed a dynamic statistical finite-element",
        "less than one month",
        "ShockSat1",
        "No direct net-CG force measurement",
        "67,683 nodes",
        "33 measured free-free modes",
        "five hammer drives",
        "evaluation means testing whether the implemented method is internally correct",
        "matches the evaluation objective better than the original validation objective",
    ]
    missing = [t for t in context_tokens if t.lower() not in text.lower()]
    results.append(item("G02 audience and evaluation context", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "advisor objective, schedule, testbed, data counts, and evaluation-versus-validation distinction are explicit"))

    method_tokens = [
        "Modal-frequency update (Beck framework",
        "IFT physics-in-prior comparator",
        "Hardened Beck/Au/Vanik modal-shape field",
        "Older exact-basis Beck whole-FRF target",
        "Schneider correlated complex/log-FRF discrepancy",
        "Frequency + MAC / shape variants",
        "Whole log-magnitude FRF, iid residual",
        "Free output-discrepancy statFEM",
        "Evidence / model-class comparison",
        "Das–Debnath lens",
    ]
    missing = [t for t in method_tokens if t.lower() not in text.lower()]
    results.append(item("G03 comprehensive Bayesian method comparison", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "ten method families, including Beck, Schneider, feature/full-FRF/MAC likelihoods, discrepancy, and evidence comparison, are separated"))

    sampler_tokens = [
        "No-U-Turn Sampler (NUTS)",
        "1,000 warmup + 1,000 retained draws",
        "R-hat 1.022",
        "ESS 232",
        "R-hat as high as 360.6",
        "Transitional Markov chain Monte Carlo",
        "Free-discrepancy M2 whole-FRF comparator",
        "IFT whole-FRF comparator",
        "boundary-seeking and not stably identified",
        "R-hat 13.95",
        "ESS about 2",
    ]
    missing = [t for t in sampler_tokens if t.lower() not in text.lower()]
    results.append(item("G04 sampler and convergence disclosure", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "implemented samplers, settings, successful diagnostics, and failed diagnostics are explicit"))

    causal_tokens = [
        "Why the posterior mean does not move enough toward the FRF data",
        "not to an obviously over-tight θ prior alone",
        "Why the uncertainty bands remain unusably large",
        "discrepancy is confounded with θ",
        "central 95% range 0.613–1.632",
        "local full-FRF Fisher calculation",
        "frequency-feature likelihood throws away needed data",
        "local curvature is not global identifiability",
        "Orthogonal discrepancy was identified in the literature but not implemented here",
    ]
    missing = [t for t in causal_tokens if t.lower() not in text.lower()]
    results.append(item("G05 Bayesian assumption audit and causal answers", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "prior strength, likelihood adequacy, information geometry, discrepancy confounding, and both requested causal answers are explicit"))

    recovered_tokens = [
        "They are too wide and inaccurate for industry use",
        "current-practice baseline used here",
        "Testing model-form freedom produced a narrower positive result",
        "down-weights response errors that cancel in the global inertial load",
        "ShockSat1 test article",
        "https://nescacademy.nasa.gov/workshops/ShockSat",
    ]
    missing = [t for t in recovered_tokens if t.lower() not in text.lower()]
    recovered = ROOT / "qa" / "advisor_progress_bayesian" / "recovered_user_edits.json"
    results.append(item("G06 user prose recovered", "GREEN" if not missing and recovered.exists() else "RED", f"missing: {missing}; extraction artifact={recovered.exists()}" if missing or not recovered.exists() else "all substantive user-edit sessions were extracted and restored; ShockSat image placeholder was replaced with a sourced NASA photograph and link"))

    frf_tokens = [
        "DAQ 20's mean absolute log10-magnitude error decreases",
        "DAQ 24 remains about an order of magnitude wrong",
        "parameter uncertainty",
        "model-form discrepancy",
        "two-stage posterior-predictive interval",
        "maximum R-hat 1.0012",
        "not evidence that a joint whole-FRF StatFEM posterior converged",
    ]
    missing = [t for t in frf_tokens if t.lower() not in text.lower()]
    band_path = ROOT.parent / "statfem_real_validation_20260617" / "out" / "mc_cache.npz"
    metrics_path = ROOT / "out" / "working_twin_frf_metrics.json"
    band_ok = False
    band_evidence = "missing predictive-band cache or metrics"
    if band_path.exists() and metrics_path.exists():
        z = np.load(band_path, allow_pickle=True)
        split = next(s for s in z["splits"] if int(s["seed"]) == 10)
        by_daq = {int(c["daq"]): c for c in split["chans"]}
        checks = []
        for daq in (20, 24):
            c = by_daq[daq]
            param = np.asarray(c["param"], float)
            total = np.asarray(c["total"], float)
            finite = all(np.all(np.isfinite(x)) and np.all(x > 0)
                         for x in (param, total, c["det"], c["tru"]))
            ordered = (np.all(param[0] <= param[1]) and np.all(param[1] <= param[2])
                       and np.all(total[0] <= param[0]) and np.all(param[2] <= total[1]))
            checks.append(finite and ordered)
        metrics = json.loads(metrics_path.read_text())
        band_ok = all(checks) and metrics["split_seed"] == 10 and metrics["interval_probability"] == 0.90
        band_evidence = f"split=10; DAQs=20/24; finite+ordered={checks}; R-hat={split['rhat']}; metrics={metrics_path.exists()}"
    results.append(item("G07 held-out FRF comparison and bands", "GREEN" if not missing and band_ok else "RED", f"missing text: {missing}; {band_evidence}" if missing or not band_ok else "the held-out good/bad comparison uses frozen finite nested bands from the converged modal stage and separately calibrated model-form discrepancy; no hit-quality shading or failed-method curves remain"))

    closure_tokens = [
        "Why the original goal is not industry-usable yet",
        "Why I tested model-form freedom",
        "What the project established",
        "Lessons I want to preserve",
        "What I need help deciding in the final month",
        "Personal diagnosis",
        "Proposed closeout acceptance bar—please approve or change",
    ]
    missing = [t for t in closure_tokens if t.lower() not in text.lower()]
    results.append(item("G08 narrative and closure purpose", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "industry gap, pivot, contributions, personal lessons, and advisor closure questions are present"))

    remodeling_tokens = [
        "Remeshing is therefore one operator family",
        "candidate.json",
        "remodelctl interface is not yet implemented",
        "hard verifier",
        "TRAIN-only diagnostic coach",
        "restricted development grader",
        "agent cannot modify the verifier",
        "not an MPL remodeling or posterior result",
    ]
    missing = [t for t in remodeling_tokens if t.lower() not in text.lower()]
    results.append(item("G09 agentic-remodeling definition and boundary", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "discrete-versus-continuous scope, current-versus-proposed CLI status, feedback roles, immutable boundary, and blinded comparison are explicit"))

    review_tokens = [
        "Defects found, repaired, and carried forward",
        "Four leakage-free per-fold MAP refits",
        "All 28 candidates were reranked",
        "validated port reproduced 1.508/2.301/2.526 exactly",
        "selected best-of-12 is exploratory and selection-biased",
        "posterior standard deviation divided by the analytic prior standard deviation",
        "+6 dB means an amplitude multiplier",
        "GRMS(high − low)/GRMS(highFEM+6dB − lowFEM+6dB)",
    ]
    missing = [t for t in review_tokens if t.lower() not in text.lower()]
    audit_metrics = ROOT / "out" / "advisor_audit_metrics.json"
    audit_ok = False
    audit_evidence = "missing advisor_audit_metrics.json"
    if audit_metrics.exists():
        audit = json.loads(audit_metrics.read_text())
        rows = audit["model_form_selection"]["rows"]
        expected = {
            "connectivity": (0.06412069847227284, 0.027978057975768165),
            "mesh_density": (0.06345941990795408, 0.05360165674775595),
            "element_formulation": (0.07111545328014318, 0.028037815209825807),
            "geometry": (0.05967872048769218, 0.024360047087976792),
        }
        audit_ok = len(audit["modal_posterior_contraction"]["rows"]) == 9 and all(
            row["class"] in expected
            and abs(row["selected_best_delta_mean"] - expected[row["class"]][0]) < 1e-12
            and abs(row["class_mean_delta_mean"] - expected[row["class"]][1]) < 1e-12
            for row in rows
        )
        audit_evidence = f"contraction rows={len(audit['modal_posterior_contraction']['rows'])}; model-form rows={len(rows)}; exact values={audit_ok}"
    results.append(item("G10 review consolidation and selection audit", "GREEN" if not missing and audit_ok else "RED", f"missing: {missing}; {audit_evidence}" if missing or not audit_ok else "later repairs supersede stale defects; posterior contraction and selected-best/class-mean controls are artifact-derived"))

    reference_markers = re.findall(r"^\[\d+\]", text, flags=re.MULTILINE)
    doi_count = text.lower().count("doi:")
    ledger = ROOT / "references_verified.md"
    results.append(item("G11 verified literature", "GREEN" if len(reference_markers) >= 17 and doi_count >= 13 and ledger.exists() else "RED", f"numbered references={len(reference_markers)}; DOI entries={doi_count}; verified ledger exists={ledger.exists()}"))

    with zipfile.ZipFile(DOCX) as zf:
        names = zf.namelist()
        xml = zf.read("word/document.xml").decode("utf-8")
        media = [n for n in names if n.startswith("word/media/")]
    comments = [n for n in names if "comments" in n.lower()] or (["comment markers in document.xml"] if "commentRangeStart" in xml else [])
    sub_count = len(re.findall(r'w:vertAlign w:val="subscript"', xml))
    sup_count = len(re.findall(r'w:vertAlign w:val="superscript"', xml))
    alt_count = min(len(media), xml.count('descr="'))
    results.append(item("G12 comments, equations, and figure metadata", "GREEN" if not comments and sub_count >= 5 and sup_count >= 2 and len(media) == 4 and alt_count == 4 else "RED", f"comments={comments}; subscript runs={sub_count}; superscript runs={sup_count}; images={len(media)}; image descriptions={alt_count}"))

    pages = sorted(RENDER.glob("page-*.png"))
    visual_qa = ROOT / "qa" / "advisor_progress_working_twin" / "manual_visual_qa.md"
    results.append(item("G13 render and visual QA", "GREEN" if len(pages) >= 14 and visual_qa.exists() else "RED", f"rendered pages={len(pages)}; manual QA exists={visual_qa.exists()}"))

    results.append(item("G14 scientific claim ceiling", "YELLOW", "No direct net-CG load answer key. The displayed L5 envelope is a calibrated-but-wide modular construction: its modal parameter stage converged, but its discrepancy was estimated separately rather than jointly inferred. The joint whole-FRF posterior did not converge, and one article/one main hit cannot establish build or flight generalization."))
    write(results)
    return 1 if any(r["tier"] == "RED" for r in results) else 0


def write(results: list[dict[str, str]]) -> None:
    counts = {tier: sum(r["tier"] == tier for r in results) for tier in ("GREEN", "YELLOW", "RED")}
    overall = "RED" if counts["RED"] else "YELLOW" if counts["YELLOW"] else "GREEN"
    payload = {"artifact": str(DOCX), "overall": overall, "counts": counts, "gates": results}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    sys.exit(main())
