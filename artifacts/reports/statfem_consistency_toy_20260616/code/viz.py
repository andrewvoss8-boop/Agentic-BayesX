#!/usr/bin/env python3
"""Shared figure styling + the save-time TEXT-OVERLAP AUDITOR for this study (Tufte skill applied).

save() stamps provenance, runs a bbox-collision audit of Text artists (accumulated into
out/text_overlap.json), and saves to figures/<name>.png. The auditor logic mirrors the buffet-dome /
confidently-wrong thread (reuse-by-copy of the pattern); pixel legibility is checked separately by
image_qa.py. Project figure rules: log-frequency axes where frequency is plotted; direct labels over
legends; provenance stamp + flags on every numeric figure; colour encodes data only.
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

# Colour discipline: one hue per construction; truth/reference neutral.
C_TRUTH = "#111111"
C_LIK = "#dc2626"     # M-lik   (physics in likelihood) red
C_STATFEM = "#2563eb"  # M-statfem               blue
C_IFT = "#059669"     # M-ift   (physics in prior) green
C_REF = "#9ca3af"
CC = {"M-lik": C_LIK, "M-statfem": C_STATFEM, "M-ift": C_IFT}

plt.rcParams.update({
    "font.size": 9.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.4,
    "figure.dpi": 110, "savefig.dpi": 200, "legend.frameon": False,
})

RUN = "run statfem_consistency_toy_20260616"


def stamp(fig, extra=""):
    txt = (f"{RUN} | synthetic 1-D axial-rod toy | NUTS 4-chain | theta_true=1.15 | " + extra).rstrip(" |")
    fig.text(0.005, 0.004, txt, fontsize=6.2, color="0.5", ha="left")


def _audit_overlaps(fig, name):
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
    stamp(fig, extra)
    fig.canvas.draw()
    _audit_overlaps(fig, name)
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight")
    plt.close(fig)
    print(f"saved {name}.png")
