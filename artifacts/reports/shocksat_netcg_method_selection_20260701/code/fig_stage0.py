#!/usr/bin/env python3
"""Stage-0 QOI trust / weight map (Tufte-linted). Reads out/stage0_*.json (no recompute -> traceable).

Small multiples:
  A: per-QOI SHAPE-trust (green=measured share) + band factor + top driving modes (* .ash-shape, o freq-observed
     only, ! prior). Shows shear high-trust, normal low.
  B: per-mode participation weight for tray_shear_X vs tray_normal_Z on a log-freq axis -> shear rides the
     measured global modes (114-197 Hz), normal rides the drumhead modes (234-254 Hz).
  C: drumhead-band (>=228 Hz) frequency observability by drive, isolating +Y's unique 230.6 Hz peak.
  D: normal-QOI band factor vs the assumed unmeasured-mode amplitude sigma SD_A_U (the load-bearing assumption).
All Stage 0 = NO NUTS (analytical MC over mode uncertainty). Linear axes labeled; log frequency in B.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
W = json.load(open(OUT / "stage0_qoi_weights.json"))
T = json.load(open(OUT / "stage0_trust.json"))
O = json.load(open(OUT / "stage0_observability.json"))
S = json.load(open(OUT / "stage0_sensitivity.json"))

C_MEAS, C_UNM, C_OBS = "#2b7a2b", "#b03030", "#c8862b"
qorder = ["tray_shear_X", "tray_shear_Y", "tray_normal_Z", "mount_response"]

fig, ax = plt.subplots(2, 2, figsize=(13.5, 9.2))

# --- A: trust bars + band factor + top modes
axA = ax[0, 0]
y = np.arange(len(qorder))[::-1]
for yi, q in zip(y, qorder):
    tr = T["trust"][q]["shape_only"]["trust_pct"]
    bx = T["trust"][q]["shape_only"]["band_factor"]; bxy = T["trust"][q]["freqobs_withY"]["band_factor"]
    axA.barh(yi, tr, color=C_MEAS)
    axA.barh(yi, 100 - tr, left=tr, color=C_UNM, alpha=0.55)
    tm = "  ".join(f"{m['hz']:.0f}{'*' if m['ash_measured'] else ('o' if m['coherently_observed'] else '!')}"
                  for m in W["qoi_participation"][q]["top_modes"][:4])
    axA.text(1.5, yi + 0.26, q, va="center", ha="left", fontsize=9, fontweight="bold")
    axA.text(1.5, yi - 0.02, f"top: {tm}", va="center", ha="left", fontsize=7.5, color="#333")
    axA.text(1.5, yi - 0.28, f"band {bx:.1f}x (shape) -> {bxy:.1f}x (+Y freq-obs)", va="center",
             ha="left", fontsize=7.5, color="#333")
    axA.text(98.5, yi + 0.28, f"{tr:.0f}%", va="center", ha="right", fontsize=10, color="#111", fontweight="bold")
axA.set_xlim(0, 100); axA.set_ylim(-0.6, len(qorder) - 0.4); axA.set_yticks([])
axA.set_xlabel("shape-trust = % of net-CG QOI on .ash-measured modes  (green=measured / red=unmeasured)")
axA.set_title("A. Which net-CG loads the twin can carry (shape-trust)", fontsize=10, loc="left")
axA.spines[["top", "right", "left"]].set_visible(False)

# --- B: per-mode participation, shear vs normal, log-freq
axB = ax[0, 1]
def modes_arr(q):
    tm = W["qoi_participation"][q]["top_modes"]
    return np.array([m["hz"] for m in tm]), np.array([m["weight_pct"] for m in tm]), \
           [("*" if m["ash_measured"] else ("o" if m["coherently_observed"] else "!")) for m in tm]
for q, col, mk, dy in [("tray_shear_X", "#1f4e79", "o", 1.0), ("tray_normal_Z", "#b03030", "s", -1.0)]:
    hz, wt, fl = modes_arr(q)
    axB.stem(hz, wt, linefmt=col, markerfmt=" ", basefmt=" ")
    for h, w, f in zip(hz, wt, fl):
        axB.plot(h, w, marker=mk, color=col, ms=5)
        axB.text(h, w + 0.8, f, ha="center", fontsize=7, color=col)
axB.axvspan(114, 197, color=C_MEAS, alpha=0.07); axB.axvspan(228, 258, color=C_UNM, alpha=0.07)
axB.text(150, axB.get_ylim()[1] * 0.92, "measured global\n(shear)", ha="center", fontsize=8, color=C_MEAS)
axB.text(243, axB.get_ylim()[1] * 0.92, "drumhead\n(normal)", ha="center", fontsize=8, color=C_UNM)
axB.set_xscale("log"); axB.set_xlabel("mode frequency [Hz, log]"); axB.set_ylabel("QOI participation weight [%]")
axB.set_title("B. shear (blue) rides measured modes; normal (red) rides drumhead", fontsize=10, loc="left")
axB.set_xticks([45, 60, 90, 120, 160, 200, 260]); axB.set_xticklabels([45, 60, 90, 120, 160, 200, 260])
axB.spines[["top", "right"]].set_visible(False)

# --- C: drumhead-band observability by drive (with vs without +Y)
axC = ax[1, 0]
rows = O["drumhead_band_observability_with_Y"]
freqs = [r["freq_hz"] for r in rows]
yy = np.arange(len(rows))[::-1]
for yi, r in zip(yy, rows):
    bys = r["by"]
    col = C_OBS if bys else "#bbbbbb"
    axC.barh(yi, 1, color=col, alpha=0.8 if bys else 0.3)
    lab = (", ".join(bys) if bys else "NOT observed")
    axC.text(0.02, yi, f"{r['freq_hz']:.0f} Hz", va="center", ha="left", fontsize=8, fontweight="bold")
    axC.text(0.30, yi, lab + ("  <-- +Y only" if bys == ["+Y"] else ""), va="center", ha="left",
             fontsize=8, color="#333")
axC.set_xlim(0, 1); axC.set_yticks([]); axC.set_xticks([])
axC.set_title("C. drumhead-band frequency observability by drive (+Y adds 230.6 Hz)", fontsize=10, loc="left")
axC.spines[["top", "right", "bottom", "left"]].set_visible(False)

# --- D: normal band factor vs SD_A_U (load-bearing assumption)
axD = ax[1, 1]
grid = S["grid"]["tray_normal_Z"]
sdau = sorted({g["SD_A_U"] for g in grid})
base_f = S["baseline"]["SD_F_U"]
sel = [g for g in grid if abs(g["SD_F_U"] - base_f) < 1e-9]
xa = [g["SD_A_U"] for g in sel]; ba = [g["band_factor"] for g in sel]
axD.plot(xa, ba, "-o", color="#1f4e79", ms=6)
for x, b in zip(xa, ba):
    axD.text(x, b + max(ba) * 0.03, f"{b:.1f}x", ha="center", fontsize=8, color="#1f4e79")
axD.axvline(S["baseline"]["SD_A_U"], color=C_UNM, ls="--", lw=1)
axD.text(S["baseline"]["SD_A_U"], max(ba) * 0.6, " assumed 0.80", color=C_UNM, fontsize=8, rotation=90, va="center")
axD.set_xlabel("assumed unmeasured-mode log-amplitude sigma  SD_A_U"); axD.set_ylabel("tray_normal_Z 95% band factor")
axD.set_title("D. normal band is set by the AMPLITUDE assumption (sensitivity)", fontsize=10, loc="left")
axD.spines[["top", "right"]].set_visible(False)

cap = ("ShockSat net-CG FORCE on the top tray (z>=55 in), uniform-mass proxy, band 45-260 Hz. Stage 0 = NO NUTS "
       "(analytical MC over mode uncertainty; meas freq 1%/amp 0.35, UNMEAS freq 6%/amp 0.80). Trust is SHAPE-based "
       "(.ash MAC>=0.3): shear_X/Y 96/94% (measured global modes), normal_Z 45% (drumhead shape unresolved). +Y "
       "adds FREQUENCY observability (230.6 Hz unique) not shape -> normal band 6.6x->5.7x. Run: "
       "shocksat_netcg_method_selection_20260701. * .ash-shape / o freq-observed only / ! prior.")
fig.text(0.01, 0.005, cap, fontsize=7.4, va="bottom", wrap=True)
fig.tight_layout(rect=[0, 0.055, 1, 1])
outp = WS / "figures" / "fig_stage0_qoi_trust.png"
fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)
print(f"wrote {outp}")
