#!/usr/bin/env python3
"""figC3: held-out coverage + where the model-form error lives. Panel A: held-out drive-point-FRF 95%
coverage per construction at eps=0 and eps=0.3 (nominal 0.95). Panel B: the analytic RMS-over-sensors
forced response vs frequency for the true rod with/without the omitted foundation, with the fit and
held-out drive frequencies marked -- showing the foundation shifts the LOW mode strongly and higher
modes barely (so a single theta cannot absorb it)."""
import json
from pathlib import Path

import numpy as np

import core
import viz
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
SS = json.load(open(WS / "out" / "sweep_summary.json"))
cons = SS["constructions"]
ORDER = ["M-lik", "M-statfem", "M-ift"]
PRIMARY = {"M-lik": "N_c", "M-statfem": "h", "M-ift": "N_c"}

fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.6))

# Panel A: coverage bars (finest discretization)
ax = axes[0]
xpos = np.arange(len(ORDER))
w = 0.36
for k, (eps, off, hatch) in enumerate([("0.0", -w / 2, None), ("0.3", w / 2, "////")]):
    vals = [cons[cn]["knobs"][PRIMARY[cn]]["eps"][eps]["coverage_finest"] for cn in ORDER]
    bars = ax.bar(xpos + off, vals, w, color=[viz.CC[cn] for cn in ORDER],
                  alpha=(0.95 if eps == "0.0" else 0.5), hatch=hatch, edgecolor="white")
    for x, v in zip(xpos + off, vals):
        ax.text(x, v + 0.01, f"{v:.2f}", ha="center", fontsize=7.5, color="0.3")
ax.axhline(0.95, color=viz.C_TRUTH, ls="--", lw=1.0)
ax.text(len(ORDER) - 0.5, 0.955, "nominal 0.95", fontsize=7.5, color=viz.C_TRUTH, ha="right", va="bottom")
ax.set_xticks(xpos); ax.set_xticklabels(ORDER)
ax.set_ylim(0, 1.12); ax.set_ylabel("held-out FRF 95% coverage")
ax.set_title("Held-out coverage  (solid eps=0,  hatched eps=0.3)", fontsize=10)

# Panel B: analytic FRF (RMS over sensors) vs frequency, truth with/without foundation
ax = axes[1]
fgrid = np.linspace(0.3, 9.0, 1400)
for i, (eps, col, lab) in enumerate([(0.0, viz.C_REF, "truth, no foundation (eps=0)"),
                                     (0.3, viz.C_TRUTH, "truth + foundation (eps=0.3)")]):
    rms = np.array([np.sqrt(np.mean(core.analytic_response(core.THETA_TRUE, eps, w, core.SENSORS) ** 2))
                    for w in fgrid])
    rms = np.clip(rms, None, 50)  # clip resonance spikes for display
    ax.loglog(fgrid, rms, color=col, lw=1.4, ls=("-" if eps == 0.3 else "--"))
    # staggered colour legend (curves nearly coincide except near the shifted low mode)
    ax.text(0.035, 0.96 - 0.07 * i, lab, transform=ax.transAxes, color=col, fontsize=7.8,
            ha="left", va="top", fontweight="bold")
for w in core.DRIVE_FREQS_FIT:
    ax.axvline(w, color="#2563eb", lw=0.8, alpha=0.5)
for w in core.DRIVE_FREQS_HELDOUT:
    ax.axvline(w, color="#b45309", lw=0.9, ls=":", alpha=0.8)
ax.text(0.02, 0.06, "blue = fit drive freqs\nbrown dotted = held-out", transform=ax.transAxes,
        fontsize=7.5, va="bottom", color="0.35")
ax.set_xlabel("drive frequency  omega  (rad/s, log)")
ax.set_ylabel("RMS sensor response (display-clipped)")
ax.set_title("Where the model-form error lives (foundation shifts low mode)", fontsize=10)
fig.tight_layout()
viz.save(fig, "figC3_coverage", extra="coverage at finest discretization, n=8")
