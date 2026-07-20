#!/usr/bin/env python3
"""Definitive gain-protocol figure (tufte skill): held-out peak |H| interval score for L5 vs Beck under THREE gain
treatments — fixed units gain (no free knob), whole-FRF gain, peak gain. Shows Beck beats L5 ONLY under a per-split
peak-tuned gain; under any non-peak-tuned gain L5 is at least as good. Reads out/frf_compare_summary.json +
out/frf_fixed_gain_summary.json. Output: figures/fig_gain_protocols.png
"""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"
C_L5 = "#2ca02c"; C_BECK = "#1f77b4"; NAVY = "#13456e"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": False, "figure.dpi": 140, "savefig.bbox": "tight"})


def main():
    cmp = json.load(open(WS / "out" / "frf_compare_summary.json"))
    fix = json.load(open(WS / "out" / "frf_fixed_gain_summary.json"))
    labels = ["fixed units gain\n(no free knob)", "whole-FRF gain\n(per-split fit)", "peak gain\n(fit TO the peaks)"]
    l5 = [fix["methods"]["L5"]["peak_IS_med"],
          cmp["methods"]["L5"]["gains"]["wholeFRF"]["peak_interval_score"]["median"],
          cmp["methods"]["L5"]["gains"]["peak"]["peak_interval_score"]["median"]]
    bk = [fix["methods"]["Beck"]["peak_IS_med"],
          cmp["methods"]["Beck"]["gains"]["wholeFRF"]["peak_interval_score"]["median"],
          cmp["methods"]["Beck"]["gains"]["peak"]["peak_interval_score"]["median"]]
    x = np.arange(3); w = 0.36
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    ax.bar(x - w / 2, l5, w, color=C_L5, label="L5 (best previous)")
    ax.bar(x + w / 2, bk, w, color=C_BECK, label="Beck (inferred shapes)")
    for xi, (a, b) in enumerate(zip(l5, bk)):
        ax.text(xi - w / 2, a + 40, f"{a:.0f}", ha="center", fontsize=9)
        ax.text(xi + w / 2, b + 40, f"{b:.0f}", ha="center", fontsize=9)
        win = "L5 wins" if a < b else "Beck wins"
        ax.text(xi, max(a, b) + 230, win, ha="center", fontsize=9, fontweight="bold",
                color=(C_L5 if a < b else C_BECK))
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=9.5); ax.set_ylim(bottom=0, top=max(l5 + bk) * 1.18)
    ax.set_ylabel("held-out peak |H| interval score (lower = sharper)")
    ax.set_title("Beck beats L5 ONLY when the gain is fit TO the peaks (25-split medians)", color=NAVY, fontsize=11.5)
    ax.legend(fontsize=9, frameon=False, loc="upper left")
    fig.text(0.5, -0.04, "out/frf_fixed_gain_summary.json + out/frf_compare_summary.json. Under a fixed units gain "
             "(no fitting) or a broadband whole-FRF gain, L5 is better on all 25 splits; only a per-split gain fit to "
             "the peaks makes Beck ~1.4× sharper. All methods under-predict held-out peaks ~2× under the fixed gain "
             "(FEM amplitude model-form error). The shape-field MECHANISM (inferred>FEM within Beck) is unaffected.",
             ha="center", fontsize=7.3, wrap=True)
    fig.savefig(FIG / "fig_gain_protocols.png", bbox_inches="tight"); plt.close(fig)
    print("wrote", FIG / "fig_gain_protocols.png")


if __name__ == "__main__":
    main()
