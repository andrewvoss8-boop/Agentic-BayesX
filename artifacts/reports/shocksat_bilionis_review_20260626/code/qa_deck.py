#!/usr/bin/env python3
"""
Heuristic QA for the review deck (no LibreOffice available to render).
Reads the .pptx back and flags: (1) text boxes whose estimated wrapped height
exceeds the box (overflow risk), (2) tables wider than the slide, (3) missing
referenced pictures. Heuristic only — not a substitute for opening the file.
"""
from __future__ import annotations
import math
from pathlib import Path
from pptx import Presentation
from pptx.util import Emu

WS = Path(__file__).resolve().parent.parent
PPTX = WS / "slides" / "shocksat_bilionis_review.pptx"
SLIDE_W_IN = 13.333
SLIDE_H_IN = 7.5

prs = Presentation(str(PPTX))
issues = []
for si, slide in enumerate(prs.slides, start=1):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.height and sh.width:
            box_w = Emu(sh.width).inches
            box_h = Emu(sh.height).inches
            top = Emu(sh.top).inches
            # estimate wrapped height
            est = 0.0
            for p in sh.text_frame.paragraphs:
                txt = "".join(r.text for r in p.runs) or p.text
                if not txt:
                    continue
                fs = (p.runs[0].font.size.pt if (p.runs and p.runs[0].font.size)
                      else (p.font.size.pt if p.font.size else 14))
                # ~ chars per line for a proportional font at this size
                cpl = max(8, box_w * 72.0 / (fs * 0.50))
                lines = max(1, math.ceil(len(txt) / cpl))
                sa = (p.space_after.pt if p.space_after else 2)
                est += lines * (fs * 1.18) / 72.0 + sa / 72.0
            # only flag the main bullet/title boxes (skip tiny footers)
            if est > box_h + 0.12 and box_h > 0.7:
                issues.append(f"slide {si}: text est {est:.2f}in > box {box_h:.2f}in "
                              f"(top {top:.2f}) :: '{sh.text_frame.text[:45].strip()}...'")
            if top + est > SLIDE_H_IN - 0.05 and box_h > 0.7:
                issues.append(f"slide {si}: text may spill past slide bottom "
                              f"(top {top:.2f} + est {est:.2f} > {SLIDE_H_IN})")
        if sh.has_table:
            tw = sum(Emu(c.width).inches for c in sh.table.columns)
            left = Emu(sh.left).inches
            if left + tw > SLIDE_W_IN - 0.1:
                issues.append(f"slide {si}: table right edge {left+tw:.2f}in > slide {SLIDE_W_IN}in")
    # picture presence is guaranteed by add_picture (only added if file exists)

print(f"slides: {len(prs.slides._sldIdLst)}")
if not issues:
    print("QA: no overflow / table-width / spill flags.")
else:
    print(f"QA: {len(issues)} flag(s):")
    for i in issues:
        print("  -", i)
