#!/usr/bin/env python3
"""fig_schematic: where the physics and the discrepancy live (method/construction diagram).

Pure schematic (no numeric data): the plain-ShockSat forward chain, the TWO injected error layers
(parametric theta bias in stiffness space; Schneider discrepancy in output space), the 4 arms (where the
discrepancy lives), and the held-out-QOI trust test. Boxes spaced to avoid text overlap (save-time auditor).
"""
from __future__ import annotations

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

import viz

fig, ax = plt.subplots(figsize=(12.5, 6.2))
ax.set_xlim(0, 100); ax.set_ylim(0, 62); ax.axis("off")


def box(x, y, w, h, text, fc="#eef2ff", ec="#3b5bdb", fs=8.6, bold=False):
    ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                         fc=fc, ec=ec, lw=1.3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal")


def arrow(x0, y0, x1, y1):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", color="#444", lw=1.4))


# top row: forward chain
box(1, 46, 20, 12, "Plain ShockSat FEM\n(9 groups, NO tray)\n$K_{red}(\\theta)=A_{fix}+\\sum_g\\theta_g A_g$", bold=True)
box(26, 46, 19, 12, "eigh -> modal\nsuperposition FRF\n$H_s(\\omega;\\theta,\\zeta)$\nhysteretic $\\eta=2\\zeta$")
box(50, 46, 17, 12, "Observe a FEW\nchannels (6)\n-> calibrate $\\theta$, $\\sigma_d$")
box(72, 46, 26, 12, "TRUST TEST: predict QOI at\nHELD-OUT sensors (14)\npeak |H| + band-GRMS\n-> 95% coverage?", fc="#fff4e6", ec="#e8590c", bold=True)
arrow(21, 52, 26, 52); arrow(45, 52, 50, 52); arrow(67, 52, 72, 52)

# truth-side injected error (two layers)
box(1, 28, 30, 12, "TRUTH = model($\\theta_{truth}$) x Schneider field\nLAYER 1 parametric bias: $\\theta_{truth}$ offsets\n(5 combos, +10-20%)\nLAYER 2 discrepancy: complex, correlated\nover freq AND space (NOT a $\\theta$ scaling)",
    fc="#f3f0ff", ec="#7048e8", fs=8.0)
arrow(16, 40, 11, 46)

# the four arms (where the discrepancy lives)
box(36, 24, 62, 16,
    "FOUR ARMS (same data per combo) -- where does the discrepancy live?\n"
    "  M0 naive       : none ($\\sigma_d\\equiv 0$)  -> confidently wrong?\n"
    "  M1 StatFEM-iid : additive iid $\\sigma_d$ (no spatial transfer)\n"
    "  M2 Schneider   : correlated over freq AND space -> krige to held-out\n"
    "  M3 orthogonal  : Schneider $d$ projected OUT of the $\\theta$->FRF span\n"
    "                   ('do not put discrepancy in the stiffness space')",
    fc="#ebfbee", ec="#2f9e44", fs=8.2)
arrow(80, 46, 72, 40)

# bottom: identifiability + verdict
box(1, 8, 46, 12,
    "Identifiability gate (BEFORE any 'recovered' claim):\n"
    "modal strain energy -> only ~4/9 groups carry signal\n"
    "(bottom_box, top_box, plates, cross_beam);\n"
    "FRF-FIM at the realized $\\sigma_d$ floor; finite perturbation",
    fc="#fff9db", ec="#f08c00", fs=8.0)
box(52, 8, 46, 12,
    "VERDICT = held-out QOI coverage (distribution over 5 combos)\n"
    "+ theta recovery (identifiable vs not)\n"
    "+ iid/Schneider/orthogonal comparison\n"
    "Either direction is the science (StatFEM may fail here).",
    fc="#fff4e6", ec="#e8590c", fs=8.0)

ax.text(50, 60.5, "StatFEM ShockSat held-out-QOI evaluation -- method / construction",
        ha="center", fontsize=12, fontweight="bold")
viz.save(fig, "fig_schematic", extra="schematic (no numeric data)")
print("fig_schematic done")
