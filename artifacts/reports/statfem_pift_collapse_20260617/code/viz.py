#!/usr/bin/env python3
"""Shared figure styling + the save-time TEXT-OVERLAP auditor (Tufte skill applied).

save(): stamps provenance + flags, audits text-artist bbox collisions (accumulates out/text_overlap.json),
saves to figures/<name>.png. Pixel legibility QA is separate (image_qa.py).
Project figure rules: log-frequency axes; linear magnitude unless dB justified; direct labels; provenance
+ not-yet-converged flags on every numeric figure.
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

# Color discipline: arms by method; truth/observed neutral.
C_TRUTH = "#111111"
C_OBS = "#6b7280"
C_M0 = "#dc2626"   # naive (red = confidently-wrong arm)
C_M1 = "#2563eb"   # StatFEM-iid (blue)
C_M2 = "#059669"   # Schneider (green)
C_M3 = "#d97706"   # orthogonal (amber)
ARM_COLOR = {"M0": C_M0, "M1": C_M1, "M2": C_M2, "M3": C_M3}
ARM_LABEL = {"M0": "M0 naive", "M1": "M1 StatFEM-iid", "M2": "M2 Schneider", "M3": "M3 orthogonal"}
C_NOMINAL = "#9ca3af"

plt.rcParams.update({
    "font.size": 9.5, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.alpha": 0.22, "grid.linewidth": 0.4,
    "figure.dpi": 110, "savefig.dpi": 200, "legend.frameon": False,
})

RUN = "run statfem_shocksat_eval_20260616"


def stamp(fig, extra=""):
    txt = f"{RUN} | plain ShockSat (9-group), synthetic | NUTS 4-chain | {extra}".rstrip(" |")
    fig.text(0.005, 0.004, txt, fontsize=6.2, color="0.5", ha="left")


def style(ax, logx=True):
    if logx:
        ax.set_xscale("log")
    ax.grid(True, which="both", alpha=0.2, lw=0.4)


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
