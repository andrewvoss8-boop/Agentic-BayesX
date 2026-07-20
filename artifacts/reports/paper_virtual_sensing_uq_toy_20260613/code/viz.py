#!/usr/bin/env python3
"""Shared plotting style + image-QA proxy. Log-frequency axes; minimal chartjunk."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from PIL import Image  # noqa: E402

C_TRUTH = "#1a1a1a"
C_BASE = "#9aa0a6"
C_DET = "#c0392b"
C_BAYES = "#1f6feb"
C_OBS = "#2d3748"


def style(ax, logx=True):
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(True, which="major", color="0.9", linewidth=0.6)
    if logx:
        ax.set_xscale("log")


def save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=170)
    plt.close(fig)
    return Path(path)


def image_qa(paths, out_json):
    failures, details = [], []
    for p in paths:
        p = Path(p)
        im = Image.open(p)
        w, h = im.size
        ok = w >= 1100 and h >= 700 and p.stat().st_size > 18_000
        if not ok:
            failures.append(p.name)
        details.append({"file": p.name, "w": w, "h": h, "bytes": p.stat().st_size, "pass": ok})
    rep = {"pass": not failures, "failures": failures, "n_figures": len(paths), "figures": details}
    json.dump(rep, open(out_json, "w"), indent=2)
    return rep
