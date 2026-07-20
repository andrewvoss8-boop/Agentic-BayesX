#!/usr/bin/env python3
"""Run-specific graphical model / likelihood diagram for the WINNING method (L5 freq + unmeasured-mode
discrepancy). Schematic (no numeric data) -> Tufte numeric-lint N/A; kept legible + labeled. NOT a copied
paper figure. Shows: what is inferred (NUTS), what is fixed, what is a non-inferred latent (drumhead shapes),
and how the honest net-CG force band is formed."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

WS = Path(__file__).resolve().parent.parent
fig, ax = plt.subplots(figsize=(13.5, 6.6)); ax.axis("off"); ax.set_xlim(0, 100); ax.set_ylim(0, 62)

C_INF, C_FIX, C_LAT, C_DATA, C_OUT = "#1f4e79", "#555555", "#b03030", "#2b7a2b", "#7a5c00"


def box(x, y, w, h, text, fc, ec=None, fs=8.6, tc="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3,rounding_size=1.2",
                                fc=fc, ec=ec or fc, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, wrap=True)


def arrow(x1, y1, x2, y2, text="", tc="#333"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
                                 lw=1.3, color="#444"))
    if text:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.4, text, ha="center", fontsize=7.4, color=tc)


# nodes
box(2, 46, 20, 9, "PRIOR\ntheta_g ~ LogNormal(0, NSIG)\n9 stiffness-group multipliers", C_INF)
box(2, 30, 20, 9, "DATA (measured)\nmodal frequencies from\n5-drive modal-hammer FRFs", C_DATA)
box(30, 38, 22, 9, "LIKELIHOOD (Kiran Eq25, L5)\n-0.5*sum (w_hat^2 - w^2(theta))^2/sig^2\nsig ~ HalfNormal  [NUTS, 4 chains]", C_INF)
box(60, 38, 16, 9, "POSTERIOR\ntheta | data\n(R-hat 1.001)", C_INF)
box(30, 20, 22, 10, "FIXED / ASSUMED\ninput PSD (flat), zeta=1%,\ntray mass proxy, mode-match MAC", C_FIX)
box(2, 8, 24, 10, "NON-INFERRED LATENT\ndrumhead mode SHAPES 234-254 Hz\n= UNMEASURED (sensors miss\nplate center) -> discrepancy tier", C_LAT)
box(60, 20, 22, 12, "net-CG FORCE FORWARD\nS_F(w)=|sum_i g_i(theta) w^2/D_i|^2 S_in\n+ per-mode tier discrepancy:\nmeasured tight / UNMEASURED wide", C_OUT, tc="white")
box(84, 30, 14, 12, "QOI BAND\nshear: 1.9-3.2x\nnormal: 2.55x\n(covers + humble)", C_OUT, tc="white")

# edges
arrow(22, 50, 30, 45, "")
arrow(22, 34, 30, 42, "")
arrow(52, 42.5, 60, 42.5)
arrow(68, 38, 68, 32, "propagate")
arrow(41, 30, 62, 30, "fix")
arrow(26, 13, 60, 22, "widen where\nshape unknown", C_LAT)
arrow(82, 26, 84, 34)

# legend
ax.text(2, 60, "L5 freq + unmeasured-mode discrepancy  (the selected method, both QOIs)", fontsize=11, fontweight="bold")
for i, (c, t) in enumerate([(C_INF, "inferred (NUTS)"), (C_DATA, "measured data"), (C_FIX, "fixed/assumed"),
                            (C_LAT, "non-inferred latent (unmeasured)"), (C_OUT, "forward / QOI output")]):
    ax.add_patch(plt.Rectangle((55 + i * 0, 57 - i * 0), 0, 0))
ax.text(2, 57.4, "  ".join(""), fontsize=7)
xleg = 2
for c, t in [(C_INF, "inferred (NUTS)"), (C_DATA, "measured data"), (C_FIX, "fixed/assumed"),
             (C_LAT, "non-inferred latent"), (C_OUT, "forward/QOI")]:
    ax.add_patch(FancyBboxPatch((xleg, 57), 2.2, 1.6, boxstyle="round,pad=0.1", fc=c, ec=c))
    ax.text(xleg + 2.6, 57.8, t, fontsize=7.6, va="center"); xleg += 15

cap = ("Graphical model of the WINNING net-CG force method (run shocksat_netcg_method_selection_20260701). The "
       "theta posterior (9 stiffness groups) is inferred by NUTS from MEASURED modal frequencies (converged). It "
       "moves mode FREQUENCIES but does NOT resolve the drumhead SHAPES (234-254 Hz), which are a non-inferred "
       "latent (unmeasured) carried as an amplitude discrepancy tier. The honest net-CG force band = theta "
       "posterior x per-mode tier discrepancy (measured tight / unmeasured wide). Schematic, not a copied figure.")
fig.text(0.01, 0.01, cap, fontsize=7.4, va="bottom", wrap=True)
fig.tight_layout(rect=[0, 0.04, 1, 1])
outp = WS / "figures" / "fig_graphical_model.png"
fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)
print(f"wrote {outp}")
