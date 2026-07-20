#!/usr/bin/env python3
"""Stage-3 delivery figure (Tufte-linted). Net-CG force bands per QOI (SELECTED method) + full N=18 scorecard +
leave-modes-out proof. Recomputes bands from the SAME cached L5 theta posterior -> traceable to the scorecard run."""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

WS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WS / "code"))
import netcg_qoi as NC

sc = json.load(open(WS / "out" / "bakeoff_scorecard.json"))
lmo = json.load(open(WS / "out" / "leave_modes_out.json"))
hod = json.load(open(WS / "out" / "heldout_drive.json")) if (WS / "out" / "heldout_drive.json").exists() else None
z = np.load(WS / "out" / "theta_post_L5.npz", allow_pickle=True)
theta_post = z["theta_post"]; theta_map = np.median(theta_post, axis=0)
conv = sc["convergence"]
model = NC.QOIModel()
FEM6 = 10 ** (6 / 20)
# delivered method per QOI = the assumption-light conservative winner (statFEM F(k) everywhere here)
DELIV = {name: sc["selection"][name]["conservative_assumption_light_winner"] for name in ["shear_X", "shear_Y", "normal_Z"]}
KIND = {"L5_freq_discrep": "freq_discrep", "statfem_Fk": "statfem_fk", "feature_space": "feature_space",
        "hier_pooled": "hier_pooled", "L5_theta_only": "theta_only"}
AX = [(0, "shear_X", "tray net-CG SHEAR X"), (1, "shear_Y", "tray net-CG SHEAR Y"), (2, "normal_Z", "tray net-CG NORMAL Z")]
METH = ["L5_theta_only", "L5_freq_discrep", "feature_space", "statfem_Fk", "hier_pooled"]
MSHORT = {"L5_theta_only": "theta-only", "L5_freq_discrep": "freq+discrep", "feature_space": "feature",
          "statfem_Fk": "statFEM F(k)", "hier_pooled": "hier-pool"}
C_WIN, C_FEM, C_TO, C_TRUTH, C_OTH = "#1f4e79", "#888888", "#b03030", "#2b7a2b", "#5b9bd5"

fig = plt.figure(figsize=(14, 9.6))
gs = GridSpec(2, 3, figure=fig, height_ratios=[1.15, 1.0], hspace=0.36, wspace=0.26)

for col, (axis, key, title) in enumerate(AX):
    ax = fig.add_subplot(gs[0, col])
    nom = model.spectrum(theta_map, axis)
    win = NC.Method(model, axis, theta_post, kind=KIND[DELIV[key]], seed=0)
    lo, med, hi = win.band()
    tmed = np.median(NC.truth_ensemble(model, axis, theta_map, n=200), 0)
    ax.fill_between(NC.FGRID, lo, hi, color=C_WIN, alpha=0.22, lw=0)
    ax.plot(NC.FGRID, med, color=C_WIN, lw=1.6)
    ax.plot(NC.FGRID, nom * FEM6, color=C_FEM, lw=1.0, ls="--")
    ax.plot(NC.FGRID, nom / FEM6, color=C_FEM, lw=1.0, ls="--")
    ax.plot(NC.FGRID, tmed, color=C_TRUTH, lw=1.0, alpha=0.9)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(45, 260); ax.set_xticks([45, 90, 150, 260]); ax.set_xticklabels([45, 90, 150, 260])
    ax.set_title(title, fontsize=10, loc="left")
    if col == 0:
        ax.set_ylabel("net-CG force |G|  (∝√PSD, arb.)")
    ax.set_xlabel("frequency [Hz, log]")
    r = sc["qois"][key][DELIV[key]]
    txt = f"delivered: {MSHORT[DELIV[key]]}\nband {r['sharpness_band_grms_ratio_vs_fem6db']:.2f}x FEM+6dB, cov {r['weighted_coverage']:.2f}"
    if hod and key in hod["summary"]:
        s = hod["summary"][key]
        txt += f"\nheld-out-drive cov {s['n_strong_drives']} drives: min {s['min_covered_frac_strong_drives']:.2f}"
    ax.text(0.03, 0.055, txt, transform=ax.transAxes, fontsize=7.2, va="bottom", color=C_WIN)
    ax.spines[["top", "right"]].set_visible(False)
axl = fig.axes[-1]
axl.text(0.97, 0.95, "delivered 95% band", color=C_WIN, fontsize=7.3, ha="right", transform=axl.transAxes)
axl.text(0.97, 0.885, "FEM+6dB (incumbent)", color=C_FEM, fontsize=7.3, ha="right", transform=axl.transAxes)
axl.text(0.97, 0.82, "epistemic-truth median", color=C_TRUTH, fontsize=7.3, ha="right", transform=axl.transAxes)

# bottom left: scorecard band-ratio, all 5 methods + FEM+6dB baseline line
axS = fig.add_subplot(gs[1, 0:2])
qkeys = ["shear_X", "shear_Y", "normal_Z"]
x = np.arange(len(qkeys)); wbar = 0.15
allm = ["baseline_fem+6dB"] + METH
for i, lab in enumerate(allm):
    vals = [sc["qois"][q][lab]["sharpness_band_grms_ratio_vs_fem6db"] for q in qkeys]
    covs = [sc["qois"][q][lab]["weighted_coverage"] for q in qkeys]
    color = C_FEM if lab == "baseline_fem+6dB" else (C_TO if lab == "L5_theta_only" else
            (C_WIN if lab == "statfem_Fk" else C_OTH))
    off = (i - len(allm) / 2 + 0.5) * wbar
    axS.bar(x + off, vals, wbar, color=color, alpha=0.9)
    for xi, v, c in zip(x + off, vals, covs):
        axS.text(xi, v + 0.03, f"{c:.2f}", ha="center", fontsize=5.6, rotation=90, va="bottom", color="#333")
axS.axhline(1.0, color="#000", lw=0.6, ls=":")
axS.set_xticks(x); axS.set_xticklabels(qkeys); axS.set_ylim(0, 3.75)
axS.set_ylabel("95% band GRMS ratio vs FEM+6dB")
axS.set_title("Bake-off (N=18): all 4 discrepancy methods cover+humble; winner = statFEM F(k); theta-only overconfident",
              fontsize=9.2, loc="left")
lg = [("FEM+6dB", C_FEM), ("theta-only (DISQ)", C_TO), ("statFEM F(k) (WIN)", C_WIN), ("freq/feature/hier-pool", C_OTH)]
for i, (t, c) in enumerate(lg):
    axS.text(0.008, 0.95 - i * 0.075, t, color=c, fontsize=7.4, transform=axS.transAxes)
axS.text(0.008, 0.62, "(bar top label = coverage)", fontsize=6.6, color="#555", transform=axS.transAxes)
axS.spines[["top", "right"]].set_visible(False)

# bottom right: leave-modes-out widen ratio, all 5 methods
axL = fig.add_subplot(gs[1, 2])
xw = np.arange(len(qkeys)); wb = 0.16
for i, lab in enumerate(METH):
    vals = [lmo["qois"][q][lab]["widen_ratio"] for q in qkeys]
    color = C_TO if lab == "L5_theta_only" else (C_WIN if lab == "statfem_Fk" else C_OTH)
    axL.bar(xw + (i - 2) * wb, vals, wb, color=color, alpha=0.9)
axL.axhline(1.0, color="#000", lw=0.6, ls=":")
axL.set_xticks(xw); axL.set_xticklabels(qkeys, fontsize=8); axL.set_ylim(0, 1.8)
axL.set_ylabel("band widen ratio when modes hidden")
axL.set_title("Leave-modes-out: theta-only=1.00 (blind);\ndiscrepancy methods widen (humble)", fontsize=8.8, loc="left")
axL.text(0.03, 0.93, "theta-only (red) never widens", color=C_TO, fontsize=7, transform=axL.transAxes)
axL.spines[["top", "right"]].set_visible(False)

cap = (f"ShockSat net-CG FORCE method selection (run shocksat_netcg_method_selection_20260701). L5 modal-frequency "
       f"NUTS CONVERGED R-hat {conv['max_rhat']:.3f} ESS {conv['min_ess']:.0f} div {conv['divergences']}. Bake-off "
       f"N=18: all four discrepancy methods COVER + are HUMBLE; only theta-only falsely sharpens (leave-modes-out "
       f"widen=1.00) -> DISQUALIFIED. SELECTED = statFEM F(k): SHEAR bands 1.51x(X)/2.30x(Y) FEM+6dB, held-out-DRIVE "
       f"validated (shear_X 5/5 drives cov 1.0; shear_Y 4/5, a real +Z@900 end-drive cross-axis gap). NORMAL band "
       f"2.53x (conservative); hier-pool reaches 2.00x but only via an unverifiable pooling assumption on the "
       f"UNMEASURED drumhead modes -> needs a >200 Hz plate test. Uniform-mass proxy, 45-260 Hz. |G| ∝ sqrt(PSD).")
fig.text(0.01, 0.005, cap, fontsize=7.2, va="bottom", wrap=True)
fig.tight_layout(rect=[0, 0.055, 1, 1])
outp = WS / "figures" / "fig_delivery_netcg_bands.png"
fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)
print(f"wrote {outp}")
