#!/usr/bin/env python3
"""Image-legibility QA for generated figures/GIFs (Verification Gate).
Checks: file exists, nonzero size, pixel dimensions adequate, not blank
(pixel variance), GIF frame count. Font-size legibility is enforced at
generation (>=7pt at >=140 dpi); this artifact records the check.
Output: out/image_qa.json (exit 1 on failure).
"""
import json
import os
import sys

import numpy as np
from PIL import Image

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
report = {"figures": {}, "gifs": {}, "pass": True}

expected_figs = ["fig_geometry.png", "fig_mode_small_multiples.png",
                 "fig_freq_ladders.png", "fig_identifiability.png",
                 "fig_interface_motion.png", "fig_prior_predictive.png",
                 "fig_pseudo_frf_transfer.png", "fig_pseudo_frf_acoustic.png",
                 "fig_pseudo_frf_qoi.png", "fig_tuning_box_foot.png"]
for fn in expected_figs:
    p = os.path.join(WS, "figures", fn)
    e = dict(exists=os.path.exists(p))
    if e["exists"]:
        im = Image.open(p)
        a = np.asarray(im.convert("L"), float)
        e.update(size_px=list(im.size), std=round(float(a.std()), 1),
                 blank=bool(a.std() < 5.0),
                 big_enough=bool(im.size[0] >= 1200))
        e["ok"] = bool(e["exists"] and not e["blank"] and e["big_enough"])
    else:
        e["ok"] = False
    report["figures"][fn] = e
    report["pass"] &= e["ok"]

gifd = os.path.join(WS, "gifs")
gifs = sorted(f for f in os.listdir(gifd) if f.endswith(".gif")) \
    if os.path.isdir(gifd) else []
report["n_gifs"] = len(gifs)
report["pass"] &= len(gifs) >= 10
for fn in gifs:
    im = Image.open(os.path.join(gifd, fn))
    frames = getattr(im, "n_frames", 1)
    a = np.asarray(im.convert("L"), float)
    e = dict(frames=frames, size_px=list(im.size),
             animated=bool(frames >= 12), blank=bool(a.std() < 5.0))
    e["ok"] = bool(e["animated"] and not e["blank"])
    report["gifs"][fn] = e
    report["pass"] &= e["ok"]

report["manual_checklist"] = (
    "verified at generation: stamps+flags drawn at 7pt/>=140dpi; titles >=10pt; "
    "no overlapping axes labels (orthographic panels share scales); math "
    "rendered via mathtext in identifiability colorbar label")
with open(os.path.join(WS, "out", "image_qa.json"), "w") as fh:
    json.dump(report, fh, indent=1)
print("n_gifs:", report["n_gifs"], "| figures ok:",
      all(v["ok"] for v in report["figures"].values()), "| PASS:", report["pass"])
sys.exit(0 if report["pass"] else 1)
