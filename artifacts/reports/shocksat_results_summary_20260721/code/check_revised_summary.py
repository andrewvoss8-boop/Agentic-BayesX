#!/usr/bin/env python3
"""Fail-closed QA checker for the revised ShockSat advisor memo.

Exit non-zero only on RED. YELLOW is reserved for accurately surfaced science
limitations and does not make the presentation artifact unusable.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

from docx import Document
from lxml import etree


HERE = Path(__file__).resolve()
ROOT = HERE.parent.parent
DOCX = ROOT / "ShockSat_results_summary_revised.docx"
ORIGINAL = ROOT / "ShockSat_results_summary.docx"
MANIFEST = ROOT / "out_revised" / "figure_source_manifest.json"
REPORT = ROOT / "qa" / "revised" / "checker_report.json"
VISUAL_QA = ROOT / "qa" / "revised" / "manual_visual_qa.md"
RENDER_DIR = ROOT / "qa" / "revised" / "render_final"

ORIGINAL_SHA256 = "8650c8e6634d06421d57c478b2ed4dae0c0a301bf8112f6b2793c15cd31c77cf"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def gate(name: str, status: str, evidence: str) -> dict:
    return {"name": name, "status": status, "evidence": evidence}


def main() -> int:
    gates: list[dict] = []

    if not DOCX.exists():
        gates.append(gate("revised_docx_exists", "RED", f"missing {DOCX}"))
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        result = {"overall": "RED", "gates": gates}
        REPORT.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return 1

    original_ok = ORIGINAL.exists() and sha256(ORIGINAL) == ORIGINAL_SHA256
    gates.append(gate(
        "original_preserved",
        "GREEN" if original_ok else "RED",
        f"expected {ORIGINAL_SHA256}; observed {sha256(ORIGINAL) if ORIGINAL.exists() else 'missing'}",
    ))

    document = Document(DOCX)
    body_text = [p.text for p in document.paragraphs]
    table_text = [cell.text for table in document.tables for row in table.rows for cell in row.cells]
    text = "\n".join(body_text + table_text)
    text_lower = text.lower()
    headings = [p.text for p in document.paragraphs if p.style.name.startswith("Heading")]
    tables = len(document.tables)
    required_text = [
        "decision requested",
        "recommendation. yes.",
        "overall research status: yellow",
        "no direct force answer key",
        "0.269 to 0.338",
        "worst r-hat 360.6",
        "no trustworthy posterior intervals",
        "agent minus random",
        "evidence provenance and status",
    ]
    missing = [item for item in required_text if item not in text_lower]
    narrative_ok = not missing and len(headings) >= 8 and tables >= 8
    gates.append(gate(
        "advisor_narrative_and_caveats",
        "GREEN" if narrative_ok else "RED",
        f"missing={missing}; headings={len(headings)}; tables={tables}",
    ))

    reference_tokens = [
        "10.1006/jsvi.1993.1340",
        "10.1016/j.ymssp.2010.10.012",
        "10.1061/(ASCE)0733-9399(1998)124:4(455)",
        "10.1016/j.cma.2020.113533",
        "10.1088/0266-5611/30/11/114007",
        "10.1016/j.ymssp.2011.04.001",
        "10.1007/s11222-016-9696-4",
        "ASME V&V 10-2019",
        "nescacademy.nasa.gov/workshops/ShockSat",
    ]
    missing_refs = [token for token in reference_tokens if token not in text]
    gates.append(gate(
        "verified_literature_present",
        "GREEN" if not missing_refs else "RED",
        f"9 verified source identifiers; missing={missing_refs}",
    ))

    with zipfile.ZipFile(DOCX) as archive:
        media = sorted(name for name in archive.namelist() if name.startswith("word/media/"))
        xml = etree.fromstring(archive.read("word/document.xml"))
        doc_props = xml.xpath(".//wp:docPr", namespaces={"wp": WP_NS})
        missing_alt = [node.get("name") for node in doc_props
                       if not (node.get("descr") or node.get("title"))]
        rows = xml.xpath(".//w:tbl/w:tr[1]", namespaces={"w": W_NS})
        unmarked_headers = [index for index, row in enumerate(rows)
                            if not row.xpath("./w:trPr/w:tblHeader", namespaces={"w": W_NS})]
    manifest_data = json.loads(MANIFEST.read_text()) if MANIFEST.exists() else {}
    stories = [item.get("story") for item in manifest_data.get("figures", [])]
    visual_budget_ok = len(media) == 2 and len(stories) == 2
    gates.append(gate(
        "two_figure_visual_budget",
        "GREEN" if visual_budget_ok else "RED",
        f"embedded_media={media}; stories={stories}",
    ))
    a11y_ok = not missing_alt and not unmarked_headers
    gates.append(gate(
        "structural_accessibility",
        "GREEN" if a11y_ok else "RED",
        f"missing_alt={missing_alt}; unmarked_table_headers={unmarked_headers}",
    ))

    pages = sorted(RENDER_DIR.glob("page-*.png"))
    visual_text = VISUAL_QA.read_text() if VISUAL_QA.exists() else ""
    visual_ok = len(pages) == 6 and "Overall visual QA: **GREEN**" in visual_text
    gates.append(gate(
        "render_and_manual_legibility",
        "GREEN" if visual_ok else "RED",
        f"rendered_pages={len(pages)}; manual_visual_qa={VISUAL_QA.exists()}",
    ))

    # An honest limitation gate: usable for the advisor decision, not scientific GREEN.
    gates.append(gate(
        "science_claim_ceiling",
        "YELLOW",
        "normal force has no direct answer key; full-spectrum NUTS worst R-hat 360.6/min ESS about 2; evidence winner did not earn held-out delivery",
    ))

    statuses = [item["status"] for item in gates]
    overall = "RED" if "RED" in statuses else "YELLOW" if "YELLOW" in statuses else "GREEN"
    result = {
        "artifact": str(DOCX),
        "overall": overall,
        "green": statuses.count("GREEN"),
        "yellow": statuses.count("YELLOW"),
        "red": statuses.count("RED"),
        "gates": gates,
        "interpretation": "YELLOW is the scientific claim ceiling, not a document-layout defect.",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 1 if overall == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())
