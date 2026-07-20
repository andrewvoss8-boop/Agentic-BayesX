#!/usr/bin/env python3
"""Card D — before/after correlation figure for the correlated-update campaign.

Tufte-applied (skill read 2026-06-18): deviation dot plots vs the as-received
baseline (zero reference line = baseline), direct labels, shared edit axis,
small multiples for the three quantities, captions carry baseline numbers and
units. Shows comparisons (each edit vs baseline) and structure (which lever
moves shape vs frequency). Reads out/before_after.json.
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ba = json.load(open(f"{HERE}/out/before_after.json"))
base = ba["baseline"]; edits = ba["edits"]
labels = [e["edit_id"].replace("_", " ") for e in edits]
y = list(range(len(edits)))[::-1]            # top-to-bottom in listed order

fig, ax = plt.subplots(1, 3, figsize=(13, 0.5*len(edits)+2.2), sharey=True)

# Panel 1: change in global matched MAC (right = better)
d_mac = [e["d_global_mac"] for e in edits]
ax[0].axvline(0, color="0.6", lw=0.8)
ax[0].scatter(d_mac, y, color="#1f4e79", zorder=3)
for v, yy in zip(d_mac, y):
    ax[0].annotate(f"{v:+.3f}", (v, yy), textcoords="offset points",
                   xytext=(6 if v >= 0 else -6, 0), va="center",
                   ha="left" if v >= 0 else "right", fontsize=8)
ax[0].set_title(f"Δ global matched MAC\n(baseline {base['global_mac']:.3f}; right = better)", fontsize=9)
ax[0].set_yticks(y); ax[0].set_yticklabels(labels, fontsize=8)

# Panel 2: change in mean |df%| (left = better, frequency closer)
d_df = [e["d_df_pct"] for e in edits]
ax[1].axvline(0, color="0.6", lw=0.8)
ax[1].scatter(d_df, y, color="#7a3b3b", zorder=3)
for v, yy in zip(d_df, y):
    ax[1].annotate(f"{v:+.2f}", (v, yy), textcoords="offset points",
                   xytext=(6 if v >= 0 else -6, 0), va="center",
                   ha="left" if v >= 0 else "right", fontsize=8)
ax[1].set_title(f"Δ mean |freq error| %\n(baseline {base['mean_abs_df_pct']:.2f}%; left = better)", fontsize=9)

# Panel 3: change in hard-region MAC (small multiples by region marker)
regions = [r for r in base["region_macs"] if base["region_macs"][r] is not None]
colors = {"source_face": "#2c7", "box_column": "#27a", "strut_base": "#b73"}
ax[2].axvline(0, color="0.6", lw=0.8)
for r in regions:
    xs = [e["d_region_macs"].get(r) for e in edits]
    xs = [(v if v is not None else float("nan")) for v in xs]
    ax[2].scatter(xs, y, label=f"{r} (base {base['region_macs'][r]:.2f})",
                  color=colors.get(r, "0.3"), s=28, zorder=3)
ax[2].set_title("Δ hard-region MAC\n(right = better)", fontsize=9)
ax[2].legend(fontsize=7, loc="lower right", frameon=False)

for a in ax:
    a.spines[["top", "right"]].set_visible(False)
fig.suptitle("Card D — correlated FEM-update attempts vs the as-received baseline "
             "(eigen-MAC + frequency, vs the .ash modal survey)", fontsize=10)
fig.text(0.5, 0.005,
         f"Each row = one data-motivated edit re-solved (eigsh, 80 modes) and re-correlated to the 33-mode .ash survey. "
         f"Baseline reproduces the inherited FEM to 3.6e-10. n_improved (region up, global not worse) = {ba['n_improved']}/{ba['n_edits']}.",
         ha="center", fontsize=7.5)
fig.tight_layout(rect=[0, 0.02, 1, 0.96])
out = f"{HERE}/figures/fig_before_after.png"
os.makedirs(f"{HERE}/figures", exist_ok=True)
fig.savefig(out, dpi=150)
print("wrote", out)
