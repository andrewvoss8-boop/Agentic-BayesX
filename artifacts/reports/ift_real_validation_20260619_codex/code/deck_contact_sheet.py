#!/usr/bin/env python3
"""Create an all-slide contact sheet from deck preview PNGs for visual QA."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

WS = Path(__file__).resolve().parent.parent
PREVIEW = WS / "slides" / "preview"
OUT = PREVIEW / "contact_sheet.png"
MANIFEST = WS / "slides" / "deck_manifest.json"
QA = WS / "slides" / "visual_qa.txt"


def main():
    files = sorted(PREVIEW.glob("slide-*.png"))
    if not files:
        raise SystemExit("no slide previews found")
    thumbs = []
    for i, p in enumerate(files, 1):
        img = Image.open(p).convert("RGB")
        t = ImageOps.contain(img, (400, 225))
        canvas = Image.new("RGB", (400, 250), "white")
        canvas.paste(t, (0, 0))
        d = ImageDraw.Draw(canvas)
        d.text((8, 230), f"slide {i}", fill=(0, 0, 0))
        thumbs.append(canvas)
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 400, rows * 250), (240, 240, 240))
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % cols) * 400, (i // cols) * 250))
    sheet.save(OUT)
    if MANIFEST.exists():
        m = json.loads(MANIFEST.read_text())
        m["contact_sheet"] = "slides/preview/contact_sheet.png"
        MANIFEST.write_text(json.dumps(m, indent=2))
    if QA.exists():
        txt = QA.read_text()
        if "Contact sheet generated:" not in txt:
            QA.write_text(txt.rstrip() + f"\nContact sheet generated: {OUT.relative_to(WS)}\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
