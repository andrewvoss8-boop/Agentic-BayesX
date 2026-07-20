#!/usr/bin/env python3
"""Shared figure styling + the two image gates for this study (Tufte skill applied):
  - save(): a generation-time TEXT-OVERLAP AUDITOR (bbox-collision check at save time, as in the
    buffet-dome thread) that pixel QA misses; accumulates hits into out/text_overlap.json.
  - run pixel image-legibility QA separately via image_qa.py.

Project figure rules: log-frequency axes; linear magnitude unless dB justified; direct labels over
legends; provenance stamp + flags on every numeric figure.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"
OUT = WS / "out"

# Color discipline: few, distinguishable hues; truth/observed neutral, arms by method.
C_TRUTH = "#111111"
C_OBS = "#6b7280"
C_DET = "#7c3aed"     # A0 deterministic (purple)
C_NAIVE = "#dc2626"   # A1 naive-no-discrepancy (red = the confidently-wrong arm)
C_IID = "#2563eb"     # A2 disc-aware iid (blue)
C_CORR = "#059669"    # A3 disc-aware correlated (green)
C_NOMINAL = "#9ca3af"

plt.rcParams.update({
    "font.size": 9.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.4,
    "figure.dpi": 110, "savefig.dpi": 200, "legend.frameon": False,
})

RUN = "run confidently_wrong_modelform_20260616"


def stamp(fig, extra=""):
    txt = f"{RUN} | synthetic, one realization per cell | NUTS 4-chain converged | {extra}".rstrip(" |")
    fig.text(0.005, 0.004, txt, fontsize=6.3, color="0.5", ha="left")


def style(ax, logx=True):
    if logx:
        ax.set_xscale("log")
    ax.grid(True, which="both", alpha=0.2, lw=0.4)


def _audit_overlaps(fig, name):
    """Bbox-collision audit of Text artists within each axes; record overlaps cumulatively."""
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    hits = []
    for ax in fig.get_axes():
        boxes = []
        for t in ax.texts:
            if not t.get_text().strip():
                continue
            try:
                boxes.append((t.get_text()[:24], t.get_window_extent(rend)))
            except Exception:
                pass
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                inter = boxes[i][1].intersection(boxes[i][1], boxes[j][1])
                if inter is not None and inter.width > 2 and inter.height > 2:
                    hits.append([boxes[i][0], boxes[j][0]])
    OUT.mkdir(exist_ok=True)
    p = OUT / "text_overlap.json"
    data = json.load(open(p)) if p.exists() else {}
    if hits:
        data[name] = hits
        print(f"  [WARN] {name}: {len(hits)} text-overlap pair(s): {hits[:3]}")
    else:
        data.pop(name, None)
    json.dump(data, open(p, "w"), indent=1)
    return hits


def save(fig, name, extra=""):
    """Stamp, audit text overlaps, save to figures/<name>.png."""
    stamp(fig, extra)
    fig.canvas.draw()
    _audit_overlaps(fig, name)
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight")
    plt.close(fig)
    print(f"saved {name}.png")
