#!/usr/bin/env python3
"""Deck figures — the scoring system + scores at hard vs easy locations (Tufte gate)."""
from __future__ import annotations
import json, glob
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; OUT = WS / "out"

# --- fig_scoring_schematic: how we score a held-out QOI (didactic, illustrative) ---
fig, ax = plt.subplots(figsize=(8.0, 4.6))
x = np.linspace(-1, 4, 600)
def logndens(x, m, s): return np.exp(-0.5 * ((x - m) / s) ** 2) / s
twin = logndens(x, 1.6, 0.55); clim = logndens(x, 1.2, 1.0)
ax.fill_between(x, 0, twin, color="#9ecae1", alpha=0.8, label="twin predictive (held-out channel)")
ax.plot(x, clim, color="#f1a340", lw=1.6, label="climatology baseline (population)")
truth = 2.2
ax.axvline(truth, color="k", lw=1.6); ax.text(truth + 0.05, twin.max() * 1.02, "truth", fontsize=9)
lo, hi = 1.6 - 1.96 * 0.55, 1.6 + 1.96 * 0.55
ax.annotate("", (lo, -0.04), (hi, -0.04), arrowprops=dict(arrowstyle="<->", color="#2166ac"))
ax.text((lo + hi) / 2, -0.10, "95% interval", color="#2166ac", ha="center", fontsize=8)
ax.set_xlabel("log peak accelerance (held-out channel)"); ax.set_yticks([])
ax.set_title("Scoring: each held-out channel gets a predictive distribution scored against the measured truth", fontsize=10, loc="left")
ax.legend(fontsize=8, loc="upper right")
fig.text(0.5, 0.005, "Coverage = is truth inside the 95% interval. Interval score / CRPS reward sharp AND calibrated. "
         "SKILL = 1 − CRPS_twin/CRPS_climatology (>0 only if the model beats guessing the population). MEASURED data; schematic shapes.",
         ha="center", fontsize=6.6, color="0.4")
for sp in ("top", "right", "left"): ax.spines[sp].set_visible(False)
fig.tight_layout(rect=[0, 0.04, 1, 1]); fig.savefig(FIG / "fig_scoring_schematic.png", dpi=140); plt.close(fig)

# --- fig_scores_hard_easy: real scores, hard vs easy (value_eval seed 0) ---
d = json.loads((OUT / "value_eval_seed00.json").read_text())
ve = [json.loads(Path(f).read_text()) for f in sorted(glob.glob(str(OUT / "value_eval_seed0[012].json")))]
nh_skill = float(np.mean([v["NON_HARD"]["crps_skill_vs_clim"] for v in ve]))
hd = d["HARD"]; nh = d["NON_HARD"]
fig, ax = plt.subplots(1, 3, figsize=(12.0, 4.0))
cats = ["easy\n(non-hard)", "hard"]; cols = ["#1b7837", "#b2182b"]
# coverage
ax[0].bar(cats, [nh["twin_coverage"], hd["twin_coverage"]], color=cols, width=0.6)
ax[0].axhline(0.95, color="0.4", ls="--", lw=0.8); ax[0].text(1.4, 0.96, "95% target", fontsize=7, color="0.4", ha="right")
ax[0].set_ylim(0, 1.08); ax[0].set_ylabel("held-out coverage"); ax[0].set_title("A. Coverage (both honest)", fontsize=9.5, loc="left")
for i, v in enumerate([nh["twin_coverage"], hd["twin_coverage"]]): ax[0].text(i, v + 0.01, f"{v:.2f}", ha="center", fontsize=9)
# FEM-point miss (dB)
ax[1].bar(cats, [nh["fem_point_median_abs_db"], hd["fem_point_median_abs_db"]], color=cols, width=0.6)
ax[1].set_ylabel("original-FEM point miss (dB)"); ax[1].set_title("B. As-received FEM error", fontsize=9.5, loc="left")
for i, v in enumerate([nh["fem_point_median_abs_db"], hd["fem_point_median_abs_db"]]): ax[1].text(i, v + 0.3, f"{v:.1f}", ha="center", fontsize=9)
# CRPS-skill vs climatology
ax[2].bar(cats, [nh_skill, hd["crps_skill_vs_clim"]], color=cols, width=0.6)
ax[2].axhline(0, color="0.3", lw=1); ax[2].set_ylabel("CRPS-skill vs climatology")
ax[2].set_title("C. Amplitude SKILL (both < 0)", fontsize=9.5, loc="left")
for i, v in enumerate([nh_skill, hd["crps_skill_vs_clim"]]): ax[2].text(i, v - 0.12, f"{v:+.2f}", ha="center", fontsize=9)
ax[2].set_ylim(min(hd["crps_skill_vs_clim"], nh_skill) * 1.25, 0.3)
for a in ax:
    for sp in ("top", "right"): a.spines[sp].set_visible(False)
fig.suptitle("Held-out AMPLITUDE scores: hard vs easy sensors — covered (honest) but the FEM misses and skill is negative for both",
             fontsize=10, y=0.99)
fig.text(0.5, 0.005, "ShockSat held-out peak accelerance. Coverage = twin band covers truth; FEM miss = as-received deterministic error; "
         "skill<0 = worse than guessing the population. Easy-skill = mean of 3 splits.", ha="center", fontsize=6.5, color="0.4")
fig.tight_layout(rect=[0, 0.03, 1, 0.95]); fig.savefig(FIG / "fig_scores_hard_easy.png", dpi=140); plt.close(fig)
print("wrote fig_scoring_schematic, fig_scores_hard_easy")
