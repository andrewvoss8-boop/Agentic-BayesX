#!/usr/bin/env python3
"""Card D — THE tradeoff figure (one multivariate panel, the clearest honest telling).

Three variables per edit, all "better" pointing a consistent way:
  x = frequency improvement   = -Δ mean|freq error|%   (right = better)
  y = hard-region shape gain  = Δ box_column MAC        (up = better)
  color = global shape change = Δ global matched MAC    (blue = better, red = worse)
A clean win = upper-right AND blue. The figure shows the upper-right is reached
ONLY by red points (e10, e01) -> improving hard-region shape + frequency still
costs GLOBAL shape; no edit wins on all three. Tufte-applied; baseline = origin.
Reads out/before_after.json.
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ba = json.load(open(f"{HERE}/out/before_after.json"))
b = ba["baseline"]; edits = ba["edits"]
x = [-e["d_df_pct"] for e in edits]                       # freq improvement
y = [e["d_region_macs"]["box_column"] for e in edits]     # hard-region shape gain
c = [e["d_global_mac"] for e in edits]                    # global shape change
lab = [e["edit_id"].replace("_", " ") for e in edits]

fig, ax = plt.subplots(figsize=(10.4, 7.0))
xmax = max(abs(v) for v in x) * 1.18
ymax = max(abs(v) for v in y) * 1.18
ymin = -0.035
ax.axhspan(0, ymax, xmin=0.5, xmax=1.0, color="#eef6ee", zorder=0)   # win region
ax.axhline(0, color="0.6", lw=0.8); ax.axvline(0, color="0.6", lw=0.8)

cmax = max(abs(v) for v in c)
norm = TwoSlopeNorm(vmin=-cmax, vcenter=0, vmax=cmax)
sc = ax.scatter(x, y, c=c, cmap="RdBu", norm=norm, s=95, edgecolor="0.3", lw=0.6, zorder=3)
# manual label offsets to avoid the upper-left overlaps (e07/e05, e03/e06)
off = {"e07_topbox_soft": (7, 7), "e05_bottombox_stiff": (7, -13),
       "e03_joints_stiff": (-4, -14), "e06_topbox_stiff": (7, 6),
       "e09_strut807_soft": (8, 8)}
for xi, yi, e in zip(x, y, edits):
    dx, dy = off.get(e["edit_id"], (7, 5))
    ax.annotate(e["edit_id"].replace("_", " "), (xi, yi), textcoords="offset points",
                xytext=(dx, dy), fontsize=8, color="0.2")
ax.annotate("as-received NASA FEM", (0, 0), textcoords="offset points", xytext=(10, -20),
            fontsize=8.5, color="#7a3b3b",
            arrowprops=dict(arrowstyle="-", color="#7a3b3b", lw=0.8))
ax.text(xmax*0.97, ymax*0.95, "clean win =\nhere AND blue", ha="right", va="top",
        fontsize=9, color="#3a6b35")

ax.set_xlim(-xmax, xmax); ax.set_ylim(ymin, ymax)
ax.set_xlabel("frequency improvement   (−Δ mean |freq error| %,  right = closer to test)", fontsize=10)
ax.set_ylabel("hard-region shape gain   (Δ box_column MAC,  up = closer to test)", fontsize=10)
cb = fig.colorbar(sc, ax=ax, pad=0.02)
cb.set_label("global shape change  (Δ matched MAC; blue = better, red = worse)", fontsize=9)
ax.set_title("Card D — no correlated FEM update improves hard-region shape, frequency, AND global shape together",
             fontsize=10.5)
ax.spines[["top", "right"]].set_visible(False)
cap = ("One dot per data-motivated edit (re-solved, 80 modes, vs the 33-mode .ash survey). Origin = the as-received\n"
       f"FEM (baseline box_column MAC {b['region_macs']['box_column']:.2f}, global {b['global_mac']:.2f}, "
       f"|freq err| {b['mean_abs_df_pct']:.1f}%). The only edits reaching the upper-right (hard-region shape + frequency\n"
       "both better) are RED (global shape worse) -> the FEM sits at a 3-way shape/frequency compromise. n=10 edits.")
fig.text(0.5, 0.02, cap, ha="center", va="bottom", fontsize=8)
fig.tight_layout(rect=[0, 0.10, 1, 0.97])
out = f"{HERE}/figures/fig_tradeoff.png"
fig.savefig(out, dpi=150)
print("wrote", out)
