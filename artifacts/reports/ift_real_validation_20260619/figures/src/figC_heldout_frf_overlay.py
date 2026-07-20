#!/usr/bin/env python3
"""Fig C: a HELD-OUT-channel FRF overlay — measured |H| vs the IFT band vs the L5 band vs the M2 band. Shows who
places the resonances and who widens honestly. Log frequency, log magnitude (accelerance spans decades; not dB).
M2 (non-converged whole-FRF) drawn flagged."""
import sys
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt

CODE = Path(__file__).resolve().parents[2] / "code"
sys.path.insert(0, str(CODE))
import figlib as F

WS = Path(__file__).resolve().parents[2]
d = np.load(WS / "out" / "frf_overlay.npz")
f = d["freqs"]

fig, ax = plt.subplots(figsize=(10.0, 5.2))
fig.subplots_adjust(left=0.085, right=0.975, top=0.90, bottom=0.27)

# IFT band + median
ax.fill_between(f, d["ift_lo"], d["ift_hi"], color=F.C_IFT, alpha=0.18, lw=0)
ax.plot(f, d["ift_md"], color=F.C_IFT, lw=1.8)
# L5 band + median
ax.fill_between(f, d["l5_lo"], d["l5_hi"], color=F.C_L5, alpha=0.16, lw=0)
ax.plot(f, d["l5_md"], color=F.C_L5, lw=1.6, ls="--")
# M2 band (flagged)
ax.fill_between(f, d["m2_lo"], d["m2_hi"], color=F.C_M2, alpha=0.10, lw=0)
ax.plot(f, d["m2_md"], color=F.C_M2, lw=1.2, ls=":")
# measured truth
ax.plot(f, d["meas"], color=F.C_TRUTH, lw=2.2)

ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("frequency [Hz]  (log)")
ax.set_ylabel("|H| accelerance [g/lbf]  (log)")
ax.set_title(f"Held-out channel DAQ {int(d['channel_daq'])} — measured vs predictive bands", fontsize=11)

# direct labels (no legend)
ymax = max(d["meas"].max(), d["ift_hi"].max())
ax.text(0.015, 0.96, "measured", transform=ax.transAxes, color=F.C_TRUTH, fontsize=9.5, va="top", fontweight="bold")
ax.text(0.015, 0.90, "IFT 95% band (physics-in-prior, β)", transform=ax.transAxes, color=F.C_IFT, fontsize=9, va="top")
ax.text(0.015, 0.84, "L5 95% band (modal-feature bar)", transform=ax.transAxes, color=F.C_L5, fontsize=9, va="top")
ax.text(0.015, 0.78, f"M2 95% band (whole-FRF, NON-CONVERGED R̂≈{int(d['m2_rhat'])})", transform=ax.transAxes,
        color=F.C_M2, fontsize=9, va="top")
ax.grid(True, which="both", alpha=0.2)

cap = ("Predictive accelerance |H| at a sensor NOT used in fitting (REAL ShockSat, split seed "
       f"{int(d['seed'])}). IFT and L5 both bracket the measured resonance; M2 (same observable, physics in the "
       "likelihood) is non-converged and its band is not trustworthy. Bands = central 95% predictive.")
F.save(fig, "figC_heldout_frf_overlay", caption=cap, srcfile=__file__)
