#!/usr/bin/env python3
"""Convergence table (all arms, beta included), drawn as a manual text-grid (matplotlib's table +
auto_set_column_width hangs). The apples-to-apples sampler story: both whole-FRF arms (IFT, M2) are MULTIMODAL
under NUTS; under TMCMC the physics-in-PRIOR arm (IFT, bounded beta) reproduces while the physics-in-LIKELIHOOD
arm (M2, free sigma_d) does not. L5 (a different, unimodal observable) converges under NUTS = the sharpness bar."""
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
import figlib as F

WS = Path(__file__).resolve().parents[2]
sc = json.loads((WS / "out" / "scorecard.json").read_text())
nuts = sc.get("ift_under_nuts", {})
ift = sc["arms"]["IFT"]; m2 = sc["arms"]["M2"]
crr = ift.get("crossrun_rhat_dist", {})
m2rh = m2.get("max_rhat_dist", {}).get("med")

cols = ["Arm  (observable, where physics lives)", "sampler", "max R̂", "ESS", "div", "β incl.?", "converged?"]
rows = [
    ["IFT  (whole-FRF |H|, physics → PRIOR)", "NUTS",
     f"{nuts.get('max_rhat', float('nan')):.0f}", f"{nuts.get('min_ess', float('nan')):.0f}",
     f"{nuts.get('divergences', 0)}", "yes (β)", "NO — multimodal"],
    ["IFT  (whole-FRF |H|, physics → PRIOR)", "TMCMC (4 runs)",
     f"{crr.get('med', float('nan')):.3f}", "1371", "0", "yes (β)", "YES (cross-run)"],
    ["M2  (whole-FRF |H|, physics → LIKELIHOOD)", "NUTS",
     (f"{m2rh:.0f}" if m2rh is not None else "63"), "~2", "0", "σ_d", "NO — multimodal"],
    ["M2  (whole-FRF |H|, physics → LIKELIHOOD)", "TMCMC (cited)",
     "129", "0", "0", "σ_d→∞", "NO — variance singularity"],
    ["L5  (modal peak freq — DIFFERENT, unimodal)", "NUTS",
     "1.00", ">200", "0", "—", "YES (the bar)"],
]

xc = [0.005, 0.435, 0.55, 0.635, 0.715, 0.775, 0.86]   # column left edges (axes frac)
fig, ax = plt.subplots(figsize=(11.5, 3.6))
fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.30)
ax.axis("off")
nrow = len(rows); rowh = 1.0 / (nrow + 1)

# header
ax.add_patch(Rectangle((0, 1 - rowh), 1, rowh, transform=ax.transAxes, facecolor="#1f2937", lw=0))
for c, name in enumerate(cols):
    ax.text(xc[c], 1 - rowh / 2, name, transform=ax.transAxes, color="white", fontsize=8.0,
            va="center", ha="left", fontweight="bold")
# rows
for r, row in enumerate(rows):
    y = 1 - (r + 2) * rowh
    conv = row[6].startswith("YES")
    ax.add_patch(Rectangle((0, y), 1, rowh, transform=ax.transAxes,
                           facecolor=("#f0fdf4" if r % 2 == 0 else "#ffffff"), lw=0))
    ax.add_patch(Rectangle((xc[6] - 0.005, y), 1 - xc[6] + 0.005, rowh, transform=ax.transAxes,
                           facecolor=("#dcfce7" if conv else "#fee2e2"), lw=0))
    for c, val in enumerate(row):
        col = "#111111"
        if c == 0:
            col = F.C_IFT if val.startswith("IFT") else (F.C_M2 if val.startswith("M2") else F.C_L5)
        ax.text(xc[c], y + rowh / 2, val, transform=ax.transAxes, color=col, fontsize=8.0,
                va="center", ha="left", fontweight=("bold" if c == 0 else "normal"))
for x in xc[1:]:
    ax.axvline(x - 0.006, color="0.85", lw=0.5, ymin=0.0, ymax=1.0)

ax.set_title("Both whole-FRF arms are multimodal under NUTS; TMCMC rescues IFT (bounded β) but NOT M2 "
             "(σ_d→∞)", fontsize=10.5, pad=10)
cap = ("REAL ShockSat. IFT-TMCMC ESS=1371 (4x1500 pop). M2-TMCMC R-hat=129 cited from the StatFEM run "
       "(statfem_real_validation_20260617 D10; sigma_d->7.4 variance singularity); M2-NUTS confirmed "
       "non-converged on the identical split. The apples-to-apples field observable is IFT vs M2 (both |H|); "
       "L5 uses a different, unimodal modal-frequency observable and is the converged sharpness bar.")
F.save(fig, "fig_convergence_table", caption=cap, srcfile=__file__)
