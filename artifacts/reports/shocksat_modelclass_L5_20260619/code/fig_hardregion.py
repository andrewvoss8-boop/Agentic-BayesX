#!/usr/bin/env python3
"""Figure: what is a 'hard region', and is it a GENERALIZABLE concept or over-fit? (Tufte gate.)
Reads out/hardregion_map.json. 2x2 small multiples, all about the per-channel held-out peak-amplitude residual
|20 log10(pred/meas)| (dB; amplitude-ratio error, standard in vibration: 6 dB = x2):
  A  residual vs structural height z  -> WHERE the hard regions are (source face / box column / strut / dish).
  B  residual vs drive-point distance (a-priori near-field feature)   -> does it predict 'hard'?  (rho~0)
  C  residual vs high-mode fraction   (a-priori locality feature)      -> does it predict 'hard'?  (rho~0)
  D  semivariogram of the residual    -> is it spatially correlated?   (flat/high nugget = no)
Takeaway: hard (17.5 dB) vs rest (6.5 dB) is REAL but NOT predictable from a-priori FEM features nor spatial
structure -> keying a discrepancy to the hand-labeled hard list is ShockSat-specific (over-fit), not transferable.
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
d = json.loads((WS / "out" / "hardregion_map.json").read_text())
pc = d["per_channel"]
z = np.array([c["z"] for c in pc]); res = np.array([c["res_db"] for c in pc])
dd = np.array([c["drive_dist"] for c in pc]); hm = np.array([c["highmode_frac"] for c in pc])
hard = np.array([c["hard"] for c in pc]); region = [c["region"] for c in pc]
rho = d["spearman_resdb_vs"]; nn = d["spatial_correlation"]["nn4_moran_like_corr"]
mh, mr = d["mean_res_db_hard"], d["mean_res_db_rest"]

REG_COL = {"source_face": "#d7301f", "box_column": "#fc8d59", "box_column(bolted joint)": "#b30000",
           "strut_base": "#7b3294", "dish": "#1b7837"}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(2, 2, figsize=(10, 7.4))

# ---- A: residual vs height z, hard colored by region, rest gray ----
a = ax[0, 0]
rest = hard == 0
a.scatter(z[rest], res[rest], s=18, c="0.7", edgecolor="none", label="rest (well-modeled)", zorder=2)
seen = set()
for i in np.where(hard == 1)[0]:
    reg = region[i]; col = REG_COL.get(reg, "k")
    a.scatter(z[i], res[i], s=55, c=col, edgecolor="k", linewidth=0.5, zorder=4,
              label=reg if reg not in seen else None)
    seen.add(reg)
a.axhline(mr, color="0.5", ls="--", lw=0.8); a.axhline(mh, color="#b30000", ls="--", lw=0.8)
a.text(58, mr + 0.4, f"rest mean {mr:.1f} dB", color="0.4", ha="right", fontsize=7.5)
a.text(58, mh + 0.4, f"hard mean {mh:.1f} dB", color="#b30000", ha="right", fontsize=7.5)
a.set_xlabel("sensor height  z  (in)  — base → dish"); a.set_ylabel("|held-out peak error|  (dB)")
a.set_title("A. The 8 hard accels by structural region", fontsize=9.5, loc="left")
a.legend(fontsize=6.6, loc="upper center", ncol=2, frameon=False)

# ---- B: residual vs drive distance (a-priori near-field feature) ----
b = ax[0, 1]
b.scatter(dd[rest], res[rest], s=18, c="0.7", edgecolor="none")
b.scatter(dd[hard == 1], res[hard == 1], s=45, c="#b30000", edgecolor="k", linewidth=0.4)
b.set_xlabel("drive-point distance (in)  [a-priori near-field feature]")
b.set_ylabel("|held-out peak error| (dB)")
b.set_title(f"B. a-priori feature does NOT predict hard  (Spearman ρ={rho['drive_dist']:+.2f})",
            fontsize=9.5, loc="left")

# ---- C: residual vs high-mode fraction (a-priori locality feature) ----
c = ax[1, 0]
c.scatter(hm[rest], res[rest], s=18, c="0.7", edgecolor="none")
c.scatter(hm[hard == 1], res[hard == 1], s=45, c="#b30000", edgecolor="k", linewidth=0.4)
c.set_xlabel("fraction of response from un-validated modes  [a-priori locality feature]")
c.set_ylabel("|held-out peak error| (dB)")
c.set_title(f"C. locality feature does NOT predict hard  (ρ={rho['highmode_frac']:+.2f})", fontsize=9.5, loc="left")

# ---- D: semivariogram (is residual spatially correlated?) ----
e = ax[1, 1]
vg = d["spatial_correlation"]["variogram"]
dm = [0.5 * (v["d_lo"] + v["d_hi"]) for v in vg]; sv = [v["semivariance"] for v in vg]
e.plot(dm, sv, "o-", color="#2166ac", ms=5, lw=1.2)
e.set_ylim(0, max(sv) * 1.15)
e.set_xlabel("pair separation distance (in)"); e.set_ylabel("semivariance of |error|  (dB²)")
e.set_title(f"D. residual ~spatially flat (nugget)  → nn-corr {nn:.2f} = weak", fontsize=9.5, loc="left")
e.text(0.5, 0.06, "flat from d→0 = high nugget = channel-specific error,\nnot spatially smooth → spatial-GP won't transfer either",
       transform=e.transAxes, fontsize=7, color="0.35", ha="left", va="bottom")

fig.suptitle("'Hard region' is real (17.5 vs 6.5 dB) but NOT predictable a-priori → hand-labeled split is "
             "over-fit, not transferable", fontsize=10.5, y=0.99)
fig.text(0.5, 0.005, "ShockSat single-impact held-out peak |H| (g/lbf), seed 0, θ at L5 MAP, ζ=1%+window; "
         "error = |20·log10(pred/measured)| (dB). MEASURED data. "
         "Generalizable tightening needs more/better data (multi-reference), not a discrepancy reparameterization.",
         ha="center", fontsize=6.8, color="0.4")
fig.tight_layout(rect=[0, 0.022, 1, 0.965])
out = WS / "figures" / "fig_hardregion.png"
out.parent.mkdir(exist_ok=True)
fig.savefig(out, dpi=150)
print(f"wrote {out}")
