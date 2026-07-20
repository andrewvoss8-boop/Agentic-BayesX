#!/usr/bin/env python3
"""Pixel image-legibility QA (AGENTS.md Plot/Verification gate): readable size, non-trivial ink, not
blank, not over-saturated. Heuristic, artifact-backed; complements the save-time text-overlap auditor in
viz.py. Writes out/image_qa.json with ALL_OK."""
import json
from pathlib import Path

import numpy as np
from PIL import Image

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"
res = {}
for p in sorted(FIG.glob("*.png")):
    im = Image.open(p).convert("RGB")
    a = np.asarray(im)
    h, w, _ = a.shape
    nonwhite = float((a.mean(axis=2) < 245).mean())
    colored = float((a.max(2).astype(int) - a.min(2).astype(int) > 25).mean())
    too_small = (w < 700 or h < 350)
    blank = nonwhite < 0.01
    res[p.name] = dict(w=int(w), h=int(h), ink_frac=round(nonwhite, 4), color_frac=round(colored, 4),
                       ok=bool(not too_small and not blank and nonwhite < 0.92))
res["ALL_OK"] = all(v["ok"] for v in res.values() if isinstance(v, dict))
(WS / "out").mkdir(exist_ok=True)
json.dump(res, open(WS / "out" / "image_qa.json", "w"), indent=1)
print(json.dumps(res, indent=1))
print("ALL_OK:", res["ALL_OK"])
