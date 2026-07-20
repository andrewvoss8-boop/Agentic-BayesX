#!/usr/bin/env python3
"""Fig (testbed): the FRF testbed and the model-form error we inject.
Left: an observed channel -- the best modal fit (what alpha/beta/gamma CAN represent) vs the truth
(modal x un-modeled discrepancy) vs the noisy observation. Right: the ABSOLUTE injected discrepancy
(log-amplitude), correlated over log-frequency and growing toward high frequency -- NOT representable
by any modal scaling. Shown at a representative delta=0.20. Channels Ch1/Ch2 observed (fit), Ch3/Ch4
masked (held out).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import core
import run_sweep as rs
import viz

DELTA = 0.20
SEED_BASE = 20260616  # matches run_sweep.gen_data seeding so this is the SAME data the arms saw
modes = rs.modes3()
freqs = core.freq_grid()
rng_t = np.random.default_rng(SEED_BASE + int(round(DELTA * 1000)))
td = core.make_truth(freqs, modes, rs.ALPHA_TRUE, rs.BETA_TRUE, rs.GAMMA_TRUE, rng_t,
                     disc_std_lo=DELTA / 6.0, disc_std_hi=DELTA)
rng_m = np.random.default_rng(20260616 + 99 + int(round(DELTA * 1000)))
measured = core.measure(td["truth"], core.MASKED, rng_m, sigma_meas=rs.SIGMA_MEAS, sigma_phase=rs.SIGMA_MEAS)

fig, axs = plt.subplots(1, 2, figsize=(12.2, 4.9))

# ---- Left: observed channel Ch1 ----
ax = axs[0]
c = 0
ax.plot(freqs, core.db(measured[:, c]), ".", color=viz.C_OBS, ms=3.0, alpha=0.7, zorder=1)
ax.plot(freqs, core.db(td["truth_modal"][:, c]), color=viz.C_IID, lw=1.6, zorder=3)
ax.plot(freqs, core.db(td["truth"][:, c]), color=viz.C_TRUTH, lw=2.0, zorder=4)
ax.annotate("truth = modal x discrepancy", (freqs[80], core.db(td["truth"][:, c])[80]),
            textcoords="offset points", xytext=(6, 12), fontsize=8, color=viz.C_TRUTH)
ax.annotate("best modal fit\n(what alpha,beta,gamma can represent)", (freqs[40], core.db(td["truth_modal"][:, c])[40]),
            textcoords="offset points", xytext=(6, -28), fontsize=7.8, color=viz.C_IID)
ax.annotate("noisy observation", (freqs[120], core.db(measured[:, c])[120]),
            textcoords="offset points", xytext=(4, 14), fontsize=7.8, color="0.4")
ax.set_xlabel("frequency [Hz], log scale")
ax.set_ylabel("Ch1 (observed) |H|  [dB]")
ax.set_title("Observed channel: the truth carries error the modal model cannot fit", fontsize=9.4)
viz.style(ax, logx=True)

# ---- Right: absolute injected discrepancy ----
ax = axs[1]
logdisc = np.log(np.abs(td["discrepancy"]))  # additive error in log-amplitude space
labels = ["Ch1 (obs)", "Ch2 (obs)", "Ch3 (masked)", "Ch4 (masked)"]
cols = [viz.C_OBS, "#94a3b8", viz.C_CORR, "#10b981"]
for cc in range(4):
    ax.plot(freqs, logdisc[:, cc], color=cols[cc], lw=1.3, alpha=0.9)
    ax.annotate(labels[cc], (freqs[-1], logdisc[-1, cc]), textcoords="offset points",
                xytext=(4, 0), fontsize=7.4, color=cols[cc], va="center")
# injected std envelope (grows delta/6 -> delta)
logf = np.log(freqs); g = (logf - logf.min()) / (logf.max() - logf.min())
std = DELTA / 6.0 + (DELTA - DELTA / 6.0) * g
ax.plot(freqs, 2 * std, color="0.3", ls="--", lw=1.0)
ax.plot(freqs, -2 * std, color="0.3", ls="--", lw=1.0)
ax.annotate("+/-2 x injected std\n(grows with frequency)", (freqs[70], 2 * std[70]),
            textcoords="offset points", xytext=(2, 8), fontsize=7.6, color="0.3")
ax.axhline(0, color="0.7", lw=0.7)
ax.set_xlabel("frequency [Hz], log scale")
ax.set_ylabel("injected discrepancy  ln|disc|  (log-amplitude)")
ax.set_title(f"Absolute injected model-form error (delta={DELTA}): correlated, HF-growing, non-modal", fontsize=9.4)
viz.style(ax, logx=True)

fig.suptitle("Testbed: a modal-ROM FRF twin fit to 2 observed channels, truth corrupted by an "
             "un-modeled correlated discrepancy", fontsize=10.2, y=1.0)
fig.subplots_adjust(right=0.90, wspace=0.22)
viz.save(fig, "fig_testbed", extra=f"testbed | delta={DELTA}")
print("fig_testbed done")
