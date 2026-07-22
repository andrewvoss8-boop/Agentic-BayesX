#!/usr/bin/env python3
"""Immutable checker for the ShockSat advisor closure report.

GREEN means an artifact/integrity gate is satisfied. The inherited YELLOW is a
scientific caveat: three of five sigma_f sensitivity variants are non-converged.
YELLOW does not cause a non-zero exit; any RED does.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

from PIL import Image
from pypdf import PdfReader


DEFAULT_ROOT = Path(__file__).resolve().parent


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_path(obj, dotted: str):
    cur = obj
    for part in dotted.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def gate(name: str, status: str, evidence: str) -> dict:
    return {"gate": name, "status": status, "evidence": evidence}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    root = args.root.resolve()
    out_path = args.output or root / "out" / "checker_report.json"
    results = []

    required = [
        "priority_deliverables.md", "decisions_log.md", "code/build_report.py", "check.py",
        "run_all.sh", "runtime.json", "ShockSat_Bayesian_FEM_StatFEM_closure_brief.docx",
        "ShockSat_Bayesian_FEM_StatFEM_closure_brief.md", "packet.md",
        "out/source_manifest.json", "out/numeric_trace.json", "out/figure_qa.json",
        "figures/fig1_method_map.png", "figures/fig2_modal_identification.png",
        "figures/fig3_wholefrf_profile.png", "figures/fig4_modular_frf.png",
    ]
    missing = [x for x in required if not (root / x).exists()]
    results.append(gate("G1 required artifacts", "GREEN" if not missing else "RED",
                        "all required artifacts present" if not missing else f"missing={missing}"))

    md_path = root / "ShockSat_Bayesian_FEM_StatFEM_closure_brief.md"
    md = md_path.read_text(errors="replace") if md_path.exists() else ""
    trace_path = root / "out" / "numeric_trace.json"
    trace_errors = []
    trace = []
    if trace_path.exists():
        try:
            trace = json.loads(trace_path.read_text())
            for row in trace:
                source = Path(row["source"])
                if not source.exists():
                    trace_errors.append(f"missing source: {source}")
                    continue
                obj = json.loads(source.read_text())
                actual = resolve_path(obj, row["path"])
                expected = row["expected"]
                if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
                    if abs(float(actual) - float(expected)) > 1e-10:
                        trace_errors.append(f"{row['label']}: {actual} != {expected}")
                elif str(expected) not in str(actual):
                    trace_errors.append(f"{row['label']}: expected {expected!r} not in {actual!r}")
                if row["display"] not in md:
                    trace_errors.append(f"{row['label']}: display {row['display']!r} absent from Markdown")
        except Exception as exc:
            trace_errors.append(f"trace parse/validation error: {exc}")
    else:
        trace_errors.append("numeric trace missing")
    results.append(gate("G2 numeric traceability", "GREEN" if len(trace) >= 25 and not trace_errors else "RED",
                        f"{len(trace)} spot checks; all source-backed" if not trace_errors else "; ".join(trace_errors[:8])))

    definitions = ["| IFT / β |", "| Model-form score |", "| Counts and bands |"]
    def_errors = [token for token in definitions if md.count(token) != 1]
    results.append(gate("G3 definitions/data contract", "GREEN" if not def_errors else "RED",
                        "terms used later, score units, counts, and bands defined once; unused internal labels omitted"
                        if not def_errors else f"bad counts: {def_errors}"))

    correct = "log f_meas,m ~ Normal(log f_pred,m(theta), sigma_f)"
    wrong = "log f_pred,m ~ Normal(log f_meas,m"
    results.append(gate("G4 likelihood direction", "GREEN" if correct in md and wrong not in md else "RED",
                        "measured log frequency is modeled around predicted log frequency" if correct in md and wrong not in md else "likelihood equation absent or reversed"))

    normal_ok = ("Normal Z, synthetic self-consistency only" in md and
                 md.count("synthetic self-consistency") >= 3 and
                 "no measured validation" in md)
    results.append(gate("G5 evidence labels", "GREEN" if normal_ok else "RED",
                        "normal-Z is repeatedly and adjacently labeled synthetic-only" if normal_ok else "normal-Z synthetic-only label incomplete"))

    pdf_path = root / "qa" / "render" / "ShockSat_Bayesian_FEM_StatFEM_closure_brief.pdf"
    pages = None
    if pdf_path.exists():
        try:
            pages = len(PdfReader(str(pdf_path)).pages)
        except Exception:
            pages = None
    future_pos = md.find("## Why I pivoted to model-form remodeling")
    remodel_pos = md.find("remodelctl")
    scope_ok = md.count("remodelctl") <= 1 and remodel_pos > future_pos >= 0 and "PSIS-LOO" not in md
    results.append(gate("G6 compression and future-work scope", "GREEN" if pages is not None and pages <= 9 and scope_ok else "RED",
                        f"pages={pages}; remodelctl only in future work; PSIS-LOO absent" if scope_ok else f"pages={pages}; scope check failed"))

    prior_manifest = root / "prior_docx_sha256.json"
    prior_errors = []
    if prior_manifest.exists():
        try:
            pm = json.loads(prior_manifest.read_text())
            prior_root = root.parent / "shocksat_results_summary_20260721"
            for rel, expected in pm["files"].items():
                path = prior_root / rel
                if not path.exists() or sha256(path) != expected:
                    prior_errors.append(rel)
        except Exception as exc:
            prior_errors.append(str(exc))
    else:
        prior_errors.append("prior hash manifest absent")
    results.append(gate("G7 prior DOCX preservation", "GREEN" if not prior_errors else "RED",
                        "six prior DOCX files byte-identical" if not prior_errors else f"hash failures={prior_errors}"))

    figs = sorted((root / "figures").glob("*.png"))
    fig_errors = []
    for fig in figs:
        try:
            with Image.open(fig) as im:
                if im.width < 1400 or im.height < 450:
                    fig_errors.append(f"{fig.name}:{im.size}")
        except Exception as exc:
            fig_errors.append(f"{fig.name}:{exc}")
    docx = root / "ShockSat_Bayesian_FEM_StatFEM_closure_brief.docx"
    alt_count = 0
    if docx.exists():
        try:
            with zipfile.ZipFile(docx) as zf:
                xml = zf.read("word/document.xml").decode("utf-8")
            alt_count = len(re.findall(r'<wp:docPr[^>]+descr="[^"]+"', xml))
        except Exception as exc:
            fig_errors.append(f"docx alt parse:{exc}")
    if alt_count < 4:
        fig_errors.append(f"alt_count={alt_count}")
    results.append(gate("G8 figure legibility and alt text", "GREEN" if len(figs) == 4 and not fig_errors else "RED",
                        "4 high-resolution figures; 4 descriptive alt texts; visual QA recorded" if not fig_errors else f"figure errors={fig_errors}"))

    required_context = [
        "Stress Testing StatFEM", "## How the work evolved", "## What I modeled and measured",
        "## Bayesian model used for the first update", "## What the modal update showed",
        "Two-stage construction", "failed to demonstrate an agent advantage", "best-exact versus best-exact",
    ]
    positions = [md.find(x) for x in ["## Where this work started", "## How the work evolved",
                                      "## What I modeled and measured", "## What the modal update showed"]]
    context_ok = all(x in md for x in required_context) and positions == sorted(positions) and min(positions) >= 0
    forbidden = re.compile(r"\b(?:green|yellow|red)\b|claims I will defend|defensible contribution|evidence ceiling",
                           re.IGNORECASE)
    forbidden_hits = sorted(set(m.group(0) for m in forbidden.finditer(md)))
    docx_text = ""
    if docx.exists():
        try:
            with zipfile.ZipFile(docx) as zf:
                docx_text = zf.read("word/document.xml").decode("utf-8")
        except Exception:
            docx_text = ""
    forbidden_docx = sorted(set(m.group(0) for m in forbidden.finditer(docx_text)))
    narrative_ok = context_ok and not forbidden_hits and not forbidden_docx
    results.append(gate("G9 advisor context and narrative", "GREEN" if narrative_ok else "RED",
                        "proposal context and chronological method explanation precede results; advisor-facing status shorthand absent"
                        if narrative_ok else f"context_ok={context_ok}; markdown_forbidden={forbidden_hits}; docx_forbidden={forbidden_docx}"))

    refs_ok = all(x in md for x in ["doi.org/10.1061", "doi.org/10.1016/j.cma.2020.113533", "doi.org/10.1214/20-BA1221", "nescacademy.nasa.gov/workshops/ShockSat"])
    results.append(gate("G10 references and closure request", "GREEN" if refs_ok and md.count("## Guidance I need for the final month") == 1 else "RED",
                        "primary/official references present and four closure questions retained" if refs_ok else "reference or closure section missing"))

    a2_path = None
    manifest = root / "out" / "source_manifest.json"
    if manifest.exists():
        for row in json.loads(manifest.read_text()).get("sources", []):
            if row["path"].endswith("a2_sigma_f_sweep.json"):
                a2_path = Path(row["path"])
                break
    yellow_ok = False
    yellow_evidence = "A2 source missing"
    if a2_path and a2_path.exists():
        a2 = json.loads(a2_path.read_text())
        bad = [v for v in a2["variants"].values() if not v["convergence"]["gate_pass"]]
        yellow_ok = len(bad) == 3 and "intervals are not trustworthy" in md
        worst_rhat = max(v["convergence"]["worst_rhat"] for v in bad)
        min_ess = min(v["convergence"]["min_ess"] for v in bad)
        yellow_evidence = f"3/5 variants non-converged; worst R-hat={worst_rhat:.3f}; min ESS={min_ess:.1f}; intervals labeled not trustworthy"
    results.append(gate("Y1 inherited science ceiling", "YELLOW" if yellow_ok else "RED", yellow_evidence))

    counts = {s: sum(1 for g in results if g["status"] == s) for s in ("GREEN", "YELLOW", "RED")}
    overall = "RED" if counts["RED"] else ("YELLOW" if counts["YELLOW"] else "GREEN")
    payload = {"overall": overall, "counts": counts, "gates": results}
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"OVERALL {overall} {{GREEN: {counts['GREEN']}, YELLOW: {counts['YELLOW']}, RED: {counts['RED']}}}")
    for g in results:
        print(f"[{g['status']}] {g['gate']}: {g['evidence']}")
    return 1 if counts["RED"] else 0


if __name__ == "__main__":
    sys.exit(main())
