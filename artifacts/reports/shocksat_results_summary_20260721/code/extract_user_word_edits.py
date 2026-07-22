#!/usr/bin/env python3
"""Extract paragraphs touched in the user-edited Word draft by revision-session ID."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
DOCX = ROOT / "archives" / "ShockSat_StatFEM_progress_and_closure_update_user_comments_20260721.docx"
OUT = ROOT / "qa" / "advisor_progress_bayesian" / "recovered_user_edits.json"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS = {"w": W}
RID = f"{{{W}}}rsidR"


def text_of(node: ET.Element) -> str:
    return "".join(t.text or "" for t in node.findall(".//w:t", NS))


def main() -> None:
    with zipfile.ZipFile(DOCX) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
        settings = ET.fromstring(zf.read("word/settings.xml"))

    rsids = [el.attrib.get(f"{{{W}}}val", "") for el in settings.findall(".//w:rsid", NS)]
    paragraphs = root.findall(".//w:p", NS)
    records = []
    for i, paragraph in enumerate(paragraphs):
        p_rsid = paragraph.attrib.get(RID, "")
        run_rsids = sorted({run.attrib.get(RID, "") for run in paragraph.findall(".//w:r", NS) if run.attrib.get(RID)})
        all_ids = sorted(set(([p_rsid] if p_rsid else []) + run_rsids))
        if not all_ids or all(rid in {"00000000", "001054EB"} for rid in all_ids):
            continue
        style = paragraph.find("./w:pPr/w:pStyle", NS)
        record = {
            "paragraph_index": i,
            "style": style.attrib.get(f"{{{W}}}val", "") if style is not None else "",
            "paragraph_rsid": p_rsid,
            "run_rsids": run_rsids,
            "text": text_of(paragraph),
            "previous_text": text_of(paragraphs[i - 1]) if i else "",
            "next_text": text_of(paragraphs[i + 1]) if i + 1 < len(paragraphs) else "",
        }
        records.append(record)

    payload = {
        "source": str(DOCX),
        "settings_rsids": rsids,
        "generated_session_rsid": "001054EB",
        "user_edit_session_rsids": sorted({rid for rec in records for rid in ([rec["paragraph_rsid"]] + rec["run_rsids"]) if rid not in {"", "00000000", "001054EB"}}),
        "touched_paragraphs": records,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
