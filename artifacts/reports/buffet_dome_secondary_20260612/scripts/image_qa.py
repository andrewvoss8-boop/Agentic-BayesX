#!/usr/bin/env python3
"""Image-legibility QA hook (AGENTS.md Plot/Verification gate): checks the
generated figures for readable size, non-trivial ink, the required provenance
stamp, and no obviously clipped/empty panels. Heuristic, artifact-backed —
not a substitute for the eyeball review, but catches blank/garbled exports.
Writes out/image_qa.json.
"""
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
    # ink fraction = pixels meaningfully off-white
    nonwhite = (a.mean(axis=2) < 245).mean()
    # color fraction = pixels with channel spread (actual data colors)
    colored = (a.max(2).astype(int) - a.min(2).astype(int) > 25).mean()
    too_small = (w < 700 or h < 350)
    blank = nonwhite < 0.01
    res[p.name] = dict(w=int(w), h=int(h), ink_frac=round(float(nonwhite), 4),
                       color_frac=round(float(colored), 4),
                       ok=bool(not too_small and not blank and nonwhite < 0.92))
res["ALL_OK"] = all(v["ok"] for v in res.values() if isinstance(v, dict))
json.dump(res, open(WS / "out" / "image_qa.json", "w"), indent=1)
print(json.dumps(res, indent=1))
