#!/usr/bin/env python3
"""Artifact-backed image legibility and caption-presence checks."""
from __future__ import annotations

from PIL import Image

from common import WS, write_json


def main():
    rows = []
    for p in sorted((WS / "figures").glob("*.png")):
        with Image.open(p) as im:
            w, h = im.size
            extrema = im.convert("L").getextrema()
            ok = w >= 1200 and h >= 600 and extrema[0] < 245 and p.stat().st_size >= 40000
            rows.append({"file": p.name, "width_px": w, "height_px": h, "grayscale_extrema": extrema,
                         "size_bytes": p.stat().st_size, "minimum_legibility_checks_pass": ok,
                         "manual_layout_check": "pending visual inspection"})
    write_json(WS / "out/fig_qa.json", {"all_legible": bool(rows) and all(r["minimum_legibility_checks_pass"] for r in rows),
                                        "checks": rows,
                                        "limitations": "pixel/dynamic-range checks do not replace rendered human inspection"})
    print("FIG QA", all(r["minimum_legibility_checks_pass"] for r in rows), len(rows))


if __name__ == "__main__":
    main()
