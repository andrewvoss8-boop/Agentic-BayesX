#!/usr/bin/env python3
"""Fail-closed checks for the self-contained advisor progress report."""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "ShockSat_StatFEM_progress_and_closure_update.docx"
RENDER = ROOT / "qa" / "advisor_progress_render_v5"
OUT = ROOT / "qa" / "advisor_progress" / "checker_report.json"


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
        "Your objective should be to evaluate the StatFEM approach",
        "less than one month",
        "ShockSat1",
        "No direct net-CG force measurement",
        "67,683 nodes",
        "33 measured free-free modes",
        "five hammer drives",
    ]
    missing = [t for t in context_tokens if t.lower() not in text.lower()]
    results.append(item("G02 audience and testbed context", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "original advisor objective, schedule, ShockSat, data counts, and missing load observation are explicit"))

    method_tokens = [
        "y(ω) = P u(ω; θ) + δ(ω) + ε(ω)",
        "p(θ, ηδ | y)",
        "Nine stiffness multipliers",
        "LogNormal(0, 0.25)",
        "HalfNormal(0.05)",
        "18 paired modal frequencies",
        "Mass, geometry, mesh, element formulation",
    ]
    missing = [t for t in method_tokens if t.lower() not in text.lower()]
    results.append(item("G03 mathematical and Bayesian specification", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "intended statFEM hierarchy and implemented modal model, priors, inferred/fixed quantities, and likelihood are present"))

    sampler_tokens = [
        "No-U-Turn Sampler",
        "1,000 warmup + 1,000 retained draws",
        "R-hat 1.022",
        "ESS 232",
        "R-hat as high as 360.6",
        "Transitional Markov chain Monte Carlo",
        "no completed ShockSat TMCMC posterior",
    ]
    missing = [t for t in sampler_tokens if t.lower() not in text.lower()]
    results.append(item("G04 sampler disclosure", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "NUTS settings/diagnostics and the non-implemented ShockSat TMCMC boundary are explicit"))

    science_tokens = [
        "frequency-residual scale was 4.6%",
        "best residual ground-response root-mean-square (GRMS) ratio was 2.07",
        "1.508",
        "2.301",
        "2.526",
        "0.269 to 0.338",
        "Agent minus random = −0.0077 ± 0.0177",
        "+0.0711 ± 0.0120",
        "planned follow-on formulation-calibration study is incomplete",
    ]
    missing = [t for t in science_tokens if t.lower() not in text.lower()]
    results.append(item("G05 results and limits", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "modal, response, load, FRF, model-form, comparator, and unfinished-study results are reported with limits"))

    closure_tokens = [
        "Why the original goal is not industry-usable yet",
        "Why I pivoted to agentic model-form remodeling",
        "What I think the work contributed",
        "Lessons I want to preserve",
        "What I need help deciding in the final month",
        "Personal diagnosis",
        "A proposed closure plan for discussion",
    ]
    missing = [t for t in closure_tokens if t.lower() not in text.lower()]
    results.append(item("G06 narrative and closure purpose", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "industry gap, pivot, contributions, personal lessons, and advisor closure questions are present"))

    remodeling_tokens = [
        "Remeshing is therefore one operator family",
        "candidate.json",
        "remodelctl interface is not yet implemented",
        "hard verifier",
        "TRAIN-only diagnostic coach",
        "restricted development grader",
        "no feedback",
        "pass/fail feedback",
        "structured diagnostics",
        "agent cannot modify the verifier",
        "not an MPL remodeling or posterior result",
    ]
    missing = [t for t in remodeling_tokens if t.lower() not in text.lower()]
    results.append(item("G07 agentic-remodeling definition and boundary", "GREEN" if not missing else "RED", f"missing: {missing}" if missing else "discrete-versus-continuous scope, current-versus-proposed CLI status, feedback roles, immutable boundary, and blinded training comparison are explicit"))

    reference_markers = re.findall(r"^\[\d+\]", text, flags=re.MULTILINE)
    doi_count = text.lower().count("doi:")
    results.append(item("G08 verified literature", "GREEN" if len(reference_markers) >= 14 and doi_count >= 12 else "RED", f"numbered references={len(reference_markers)}; DOI entries={doi_count}; verified ledger exists={((ROOT / 'references_verified.md').exists())}"))

    with zipfile.ZipFile(DOCX) as zf:
        xml = zf.read("word/document.xml").decode("utf-8")
        media = [n for n in zf.namelist() if n.startswith("word/media/")]
    color_coded_fills = [c for c in ("EAF4EA", "FFF4CE", "FCE8E6") if c in xml]
    alt_count = len(re.findall(r'w:docPr[^>]+descr="[^"]+"', xml)) + len(re.findall(r'wp:docPr[^>]+descr="[^"]+"', xml))
    # docPr has no w namespace in standard OOXML; count descriptions directly and cap at image count.
    alt_count = min(len(media), xml.count('descr="'))
    results.append(item("G09 figures and neutral status presentation", "GREEN" if len(media) == 3 and alt_count == 3 and not color_coded_fills else "RED", f"embedded images={len(media)}; images with descriptions={alt_count}; traffic-light fills={color_coded_fills}"))

    pages = sorted(RENDER.glob("page-*.png"))
    visual_qa = ROOT / "qa" / "advisor_progress" / "manual_visual_qa.md"
    results.append(item("G10 render and visual QA", "GREEN" if len(pages) >= 12 and visual_qa.exists() else "RED", f"rendered pages={len(pages)}; manual QA exists={visual_qa.exists()}"))

    # Science ceiling is intentionally not a document defect.
    results.append(item("G11 scientific claim ceiling", "YELLOW", "No direct net-CG load answer key; held-out modal/full-FRF posterior families did not converge; agent did not beat random. Report limits the claims accordingly."))
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
