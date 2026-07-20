#!/usr/bin/env python3
"""Headline figure: the VALUE of the L5 ShockSat twin, scored as CRPS-skill vs climatology (the no-skill calibrated
baseline that guesses a held-out channel/mode from the observed population). Skill>0 = the model carries
information beyond the population; skill<0 = worse than guessing. (Tufte gate.)
  A. value by DOMAIN: modal frequency (positive) vs per-channel single-impact amplitude (negative).
  B. every AMPLITUDE lever tried (non-hard sensors) — all <=0 -> no lever gives amplitude skill.
Loads out/{freq_value,value_eval,gap_closure}_seed*.json.
"""
from __future__ import annotations
import json, glob
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
fv = json.loads((OUT / "freq_value_seed00.json").read_text())["twin_vs_climatology"]["crps_skill"]
ve = [json.loads(Path(f).read_text())["NON_HARD"]["crps_skill_vs_clim"] for f in sorted(glob.glob(str(OUT / "value_eval_seed0[012].json")))]
amp_peak = float(np.mean(ve))
gc = json.loads((OUT / "gap_closure_seed00.json").read_text())["arms"]
amp_band = gc["baseline_band"]["nonhard_crps_skill_vs_clim"]

# Panel A: domain value
domA = [("modal frequency\n(held-out modes)", fv, "#1b7837"),
        ("per-channel amplitude\n(peak)", amp_peak, "#b2182b"),
        ("per-channel amplitude\n(band GRMS)", amp_band, "#b2182b")]
# Panel B: amplitude levers (non-hard CRPS-skill vs climatology)
levers = [("baseline (L5 freq, ζ=1%+window)", gc["baseline_peak"]["nonhard_crps_skill_vs_clim"]),
          ("+ fitted damping (best ζ×2, band)", gc["band_zeta_x2.0"]["nonhard_crps_skill_vs_clim"]),
          ("+ joint topology released (bush_801)", gc["topo_joint_soften0.0_peak"]["nonhard_crps_skill_vs_clim"]),
          ("peak, mean over 3 splits", amp_peak),
          ("band GRMS", amp_band)]

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(11, 4.6))

a = ax[0]
y = np.arange(len(domA))[::-1]
a.barh(y, [d[1] for d in domA], color=[d[2] for d in domA], height=0.6)
a.axvline(0, color="0.4", lw=1)
a.set_yticks(y); a.set_yticklabels([d[0] for d in domA], fontsize=8.5)
for yi, d in zip(y, domA):
    a.text(d[1] + (0.04 if d[1] >= 0 else -0.04), yi, f"{d[1]:+.2f}", va="center",
           ha="left" if d[1] >= 0 else "right", fontsize=8.5, fontweight="bold")
a.set_xlim(-1.6, 1.2); a.set_xlabel("CRPS-skill vs climatology")
a.text(0.02, 1.0, "skill > 0 = beats guessing the population", transform=a.transAxes, fontsize=7.2, color="#1b7837")
a.text(0.02, -0.0, "skill < 0 = worse than guessing", transform=a.transAxes, fontsize=7.2, color="#b2182b")
a.set_title("A. Twin value is real for FREQUENCY, negative for AMPLITUDE", fontsize=9.5, loc="left")

b = ax[1]
yb = np.arange(len(levers))[::-1]
b.barh(yb, [l[1] for l in levers], color="#b2182b", height=0.6)
b.axvline(0, color="0.4", lw=1)
b.set_yticks(yb); b.set_yticklabels([l[0] for l in levers], fontsize=8)
for yi, l in zip(yb, levers):
    b.text(l[1] - 0.03, yi, f"{l[1]:+.2f}", va="center", ha="right", fontsize=8)
b.set_xlim(-1.7, 0.4); b.set_xlabel("non-hard amplitude CRPS-skill vs climatology")
b.set_title("B. Every amplitude lever tried stays ≤ 0 (no skill)", fontsize=9.5, loc="left")

fig.suptitle("Value of the calibrated ShockSat L5 twin (held-out skill vs a no-skill calibrated baseline)",
             fontsize=10.5, y=0.995)
fig.text(0.5, 0.005, "Real single-impact ShockSat, held-out channels/modes (≥3 splits where shown); CRPS-skill = "
         "1 − CRPS_twin/CRPS_climatology. Frequency value also halves the as-received FEM error (2.10%→1.07%). "
         "MEASURED data. Amplitude levers: damping, FEM & measured shapes, richer/local stiffness, joint topology, "
         "discrepancy structure — none give per-channel single-impact amplitude positive skill.",
         ha="center", fontsize=6.6, color="0.4", wrap=True)
fig.tight_layout(rect=[0, 0.05, 1, 0.95])
out = WS / "figures" / "fig_value_summary.png"
out.parent.mkdir(exist_ok=True); fig.savefig(out, dpi=150)
print(f"wrote {out}  | freq skill {fv:+.2f} | amp peak {amp_peak:+.2f} | amp band {amp_band:+.2f}")
