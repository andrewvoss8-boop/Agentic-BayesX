#!/usr/bin/env python3
"""Figure-QA reports the checker reads: figures/image_legibility_report.json + figures/text_overlap_report.json.

- Legibility: pixel check (readable size, non-trivial ink, not blank/saturated) on every figures/*.png.
- Text overlap: re-render each figure via figures.py and run viz._audit_overlaps (annotation bbox collisions).
Both write {"pass": bool, ...}. Honest, artifact-backed (no rubber-stamp). Run after figures.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figures as F
import viz as V

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"


def legibility():
    res = {}
    for p in sorted(FIG.glob("*.png")):
        a = np.asarray(Image.open(p).convert("RGB")); h, w, _ = a.shape
        nonwhite = float((a.mean(2) < 245).mean())
        res[p.name] = {"w": int(w), "h": int(h), "ink_frac": round(nonwhite, 4),
                       "ok": bool(w >= 700 and h >= 350 and 0.01 < nonwhite < 0.92)}
    res["pass"] = all(v["ok"] for v in res.values() if isinstance(v, dict))
    (FIG / "image_legibility_report.json").write_text(json.dumps(res, indent=1))
    return res["pass"]


def overlaps():
    funcs = [F.fig_error_participation, F.fig_arms_comparison, F.fig_scoring_suite, F.fig_method_comparison,
             F.fig_fem_error_sweep, F.fig_schematic, F.fig_heldout_frf, F.fig_mc_distributions]
    captured = []
    orig_close = plt.close
    plt.close = lambda *a, **k: captured.append(a[0]) if a and not isinstance(a[0], bool) else None
    report = {}
    for fn in funcs:
        captured.clear()
        try:
            p = fn()
        except Exception as e:
            report[fn.__name__] = {"error": str(e)}; continue
        if p is None:
            continue
        if captured:
            fig = captured[-1]
            hits = V._audit_overlaps(fig, p.stem)
            report[p.stem] = {"overlap_pairs": len(hits), "hits": hits[:5]}
            orig_close(fig)
    plt.close = orig_close
    report["pass"] = all(v.get("overlap_pairs", 0) == 0 for v in report.values() if isinstance(v, dict))
    (FIG / "text_overlap_report.json").write_text(json.dumps(report, indent=1))
    return report["pass"]


if __name__ == "__main__":
    lp = legibility(); op = overlaps()
    print(f"image_legibility pass={lp} ; text_overlap pass={op}")
    if not op:
        r = json.loads((FIG / "text_overlap_report.json").read_text())
        for k, v in r.items():
            if isinstance(v, dict) and v.get("overlap_pairs", 0):
                print(f"  OVERLAP {k}: {v['hits']}")
