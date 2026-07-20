#!/usr/bin/env python3
"""Deck figure — per-mode damping INFERENCE result: posteriors are prior-dominated / railed to the resolution
floor (0/9 identified). Confirms by running that damping isn't recoverable from this single windowed FRF."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf

WS = Path(__file__).resolve().parent.parent
d = json.loads((WS / "out" / "damping_inference.json").read_text())
m = d["modes"]
f = np.array([x["f_hz"] for x in m]); med = np.array([x["zeta_apparent_pct"]["med"] for x in m])
lo = np.array([x["zeta_apparent_pct"]["lo"] for x in m]); hi = np.array([x["zeta_apparent_pct"]["hi"] for x in m])
ash_f = np.array([x["f_hz"] for x in m]); ash_z = np.array([x["ash_zeta_pct"] for x in m])
ff = np.linspace(45, 260, 200); zw = rf.measured_zeta_w(ff) * 100
zrange = d["prior_zeta_pct_range"]

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(9.5, 5.2))
ax.axhspan(zrange[0], zrange[1], color="0.92", label=f"prior range [{zrange[0]:.2f},{zrange[1]:.1f}]%")
ax.errorbar(f, med, yerr=[med - lo, hi - med], fmt="o", ms=6, color="#2166ac", ecolor="#2166ac",
            elinewidth=1.4, capsize=3, label="inferred apparent ζ (95% CI)")
ax.plot(ff, zw, color="#b2182b", lw=1.6, label="exp-window ζ_w(f)")
ax.scatter(ash_f, ash_z, marker="s", s=28, color="#1b7837", zorder=5, label="NASA .ash modal ζ")
ax.set_yscale("log"); ax.set_xscale("log")
ax.set_xlabel("frequency (Hz)"); ax.set_ylabel("damping ratio ζ (%)")
ax.set_title("Per-mode damping inference: 0/9 IDENTIFIED — posteriors prior-dominated / railed to the floor", fontsize=10, loc="left")
ax.legend(fontsize=8, loc="upper right")
ax.text(0.02, 0.04, "CIs span the prior or pile at the resolution floor:\nthe df=1.25 Hz windowed FRF cannot resolve the\nhalf-power width of these lightly-damped modes",
        transform=ax.transAxes, fontsize=7.5, color="0.3")
fig.text(0.5, 0.005, "Multi-channel SDOF resonance fit per matched mode (per-channel residues marginalized; exact 2-D (f,ζ) grid posterior). "
         "Closes the damping to-do by RUNNING: per-mode/complex damping is NOT identifiable from this single-impact FRF. MEASURED data.",
         ha="center", fontsize=6.6, color="0.4")
fig.tight_layout(rect=[0, 0.04, 1, 1]); fig.savefig(WS / "figures" / "fig_damping_inference.png", dpi=140); plt.close(fig)
print("wrote fig_damping_inference.png")
