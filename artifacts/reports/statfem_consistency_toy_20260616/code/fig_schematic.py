#!/usr/bin/env python3
"""figS: construction schematic. Three cards showing, for the SAME rod / forcing / data, WHERE the
physics is injected and WHAT plays the model-error role -- the difference that IS the experiment:
  M-lik     physics in the LIKELIHOOD   -> fixed residual noise sigma_r (arbitrary numerical knob)
  M-statfem FE prediction + discrepancy -> learned additive discrepancy sigma_d
  M-ift     physics in the PRIOR        -> learned inverse-temperature beta (self-calibrating)
Pure schematic (no numeric data); text placed on a coordinate grid so the save-time overlap auditor stays clean."""
from pathlib import Path

import viz
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

fig, ax = plt.subplots(figsize=(13.5, 6.4))
ax.set_xlim(0, 3); ax.set_ylim(0, 1); ax.axis("off")

CARDS = [
    (0, viz.C_LIK, "M-lik  -  physics in the LIKELIHOOD",
     ["chain:   theta  ->  field u  ->  data y",
      "PDE residual  A(theta) u - f  is treated as",
      "FICTITIOUS data:  'residual = 0' with noise sigma_r",
      "",
      "model-error knob:  sigma_r   (FIXED, arbitrary)",
      "likelihood:  N(0; Au-f, sigma_r^2) x N(y; Su, sigma_u^2)",
      "",
      "=> the answer DEPENDS on sigma_r,",
      "    a number that carries NO information"]),
    (1, viz.C_STATFEM, "M-statfem  -  FE prediction + discrepancy",
     ["chain:   theta  ->  FE(h)  -> (+ d)  ->  data y",
      "the FE model predicts the response; the data =",
      "FE prediction + additive zero-mean discrepancy d",
      "+ measurement noise  (Girolami et al. 2021)",
      "",
      "model-error knob:  sigma_d   (LEARNED discrepancy)",
      "likelihood:  N(y; S u_FE,  sigma_d^2 C + sigma_u^2)",
      "",
      "=> d can absorb model error -- or theta does"]),
    (2, viz.C_IFT, "M-ift  -  physics in the PRIOR (IFT/PIFT)",
     ["chain:   theta -> [prior with beta] -> u -> data y",
      "the field PRIOR weights the PDE residual:",
      "prior ~ exp(- beta/2 || A(theta) u - f ||^2)",
      "with inverse-temperature beta LEARNED from data",
      "",
      "model-error knob:  beta   (LEARNED, self-calibrating)",
      "likelihood:  N(y; Su, sigma_u^2)",
      "",
      "=> no arbitrary sigma_r knob"]),
]

for col, color, head, lines in CARDS:
    x0 = col + 0.05
    ax.add_patch(FancyBboxPatch((x0, 0.06), 0.90, 0.86, boxstyle="round,pad=0.012,rounding_size=0.02",
                                linewidth=1.4, edgecolor=color, facecolor=color, alpha=0.06))
    ax.text(x0 + 0.45, 0.86, head, color=color, fontsize=10.5, fontweight="bold", ha="center", va="center")
    y = 0.76
    for ln in lines:
        ax.text(x0 + 0.05, y, ln, color="0.18", fontsize=8.2, ha="left", va="center")
        y -= 0.072

ax.text(1.5, 0.012,
        "Same rod, same uniform forcing, same sensor data: ONLY the residual WEIGHT differs "
        "(fixed sigma_r in the likelihood  vs  additive d  vs  learned beta in the prior).",
        ha="center", va="bottom", fontsize=8.6, color="0.4")
viz.save(fig, "figS_schematic", extra="schematic (no numeric data)")
