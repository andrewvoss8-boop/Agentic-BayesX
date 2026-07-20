#!/usr/bin/env python3
"""L5 mode-matching sensitivity (tufte skill): held-out peak |H| interval score vs number of modes kept, for
MAC-informed vs nearest-frequency matching, on the apples-to-apples peak gain. Reads
out/l5_matching_sensitivity_summary.json. Output: figures/fig_l5_matching.png
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"
C_MAC = "#1f77b4"; C_FREQ = "#ff7f0e"; C_ORIG = "#2ca02c"; NAVY = "#13456e"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": False, "figure.dpi": 140, "savefig.bbox": "tight"})


def main():
    d = json.load(open(WS / "out" / "l5_matching_sensitivity_summary.json"))["configs"]

    def series(prefix):
        pts = []
        for name, c in d.items():
            if name.startswith(prefix) and "keep" in name:
                pts.append((c["n_modes_med"], c["peak_IS_med"]))
        return sorted(pts)
    mac = series("mac15"); frq = series("freq12")
    fig, ax = plt.subplots(figsize=(8.2, 4.6))
    if mac:
        xm, ym = zip(*mac); ax.plot(xm, ym, "-o", color=C_MAC, lw=1.8, ms=7, label="MAC-informed match")
    if frq:
        xf, yf = zip(*frq); ax.plot(xf, yf, "-s", color=C_FREQ, lw=1.6, ms=6, label="nearest-frequency match (12%)")
    orig = d.get("orig12_keepall")
    if orig:
        ax.plot(orig["n_modes_med"], orig["peak_IS_med"], marker="*", ms=18, color=C_ORIG, ls="none",
                label="deployed L5 (orig, 26 modes)")
    f5 = d.get("freq5_keepall")
    if f5:
        ax.plot(f5["n_modes_med"], f5["peak_IS_med"], marker="D", ms=7, mfc="none", mec="#aa3333", ls="none",
                label="nearest-freq 5% (tight)")
    pk = [c["peak_IS_med"] for c in d.values()]
    ax.axhspan(min(pk), max(pk), color="#eeeeee", zorder=0)
    ax.set_xlabel("number of modes kept (by MAC / support rank)")
    ax.set_ylabel("held-out peak |H| interval score (lower = sharper)")
    ax.set_title("L5 is largely INSENSITIVE to matching & mode count (full spread ≈20%)", color=NAVY, fontsize=11.5)
    ax.legend(fontsize=8.5, frameon=False, loc="upper left")
    ax.annotate("MAC-ranked, small clean set\n(~6-8 modes) is marginally best",
                xy=(6, min(pk)), xytext=(13, min(pk) - 0), fontsize=8.5, color=C_MAC, va="center",
                arrowprops=dict(arrowstyle="->", color=C_MAC))
    fig.text(0.5, -0.04, "10-split medians, apples-to-apples peak gain (out/l5_matching_sensitivity_summary.json). "
             "Single-impact ODS-MAC is only 0.10-0.25 (noisy shapes, D20), so MAC barely informs the MATCH; its small "
             "value is in SELECTING a clean mode subset. Coverage steady ~0.92-0.94 across all configs. The ~34 dB "
             "amplitude width is FEM model-form error, NOT a matching artifact.", ha="center", fontsize=7.3, wrap=True)
    fig.savefig(FIG / "fig_l5_matching.png", bbox_inches="tight"); plt.close(fig)
    print("wrote", FIG / "fig_l5_matching.png")


if __name__ == "__main__":
    main()
