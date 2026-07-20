#!/usr/bin/env python3
"""Card D — the JOINT-space Pareto frontier figure (the decisive answer).

Tufte-applied: hard-region shape (MAC) vs frequency error, the Pareto frontier of
the FULL 9-parameter stiffness space (re-pairing-robust tracked metric). The
nominal FEM sits ON the frontier and the 'win' quadrant (better shape AND better
frequency) is empty -> no stiffness update improves both = a model-form limit.
Reads out/joint_frontier.json.
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(f"{HERE}/out/joint_frontier.json"))
n = d["nominal"]; pf = d["pareto_front"]
fx = [p["mean_abs_df_pct"] for p in pf]
fy = [p["hard_region_mac"] for p in pf]

fig, ax = plt.subplots(figsize=(9.0, 6.2))
xlo = min(fx)-0.2
ax.set_xlim(xlo, max(fx)+0.3); ax.set_ylim(min(fy)-0.004, max(fy)+0.012)
# win quadrant (data coords): x < nominal freq error AND y > nominal hard MAC
from matplotlib.patches import Rectangle
ax.add_patch(Rectangle((xlo, n["hard_region_mac"]), n["mean_abs_df_pct"]-xlo,
                        max(fy)+0.012-n["hard_region_mac"], color="#e8f3e8", zorder=0))
ax.plot(fx, fy, "-o", color="#1f4e79", ms=4, lw=1.4, zorder=3, label="Pareto frontier (9 params free)")
ax.scatter([n["mean_abs_df_pct"]], [n["hard_region_mac"]], color="#7a3b3b", s=90, zorder=4)
ax.annotate("as-received NASA FEM\n(already on the frontier)",
            (n["mean_abs_df_pct"], n["hard_region_mac"]),
            textcoords="offset points", xytext=(12, -4), fontsize=9, color="#7a3b3b",
            arrowprops=dict(arrowstyle="-", color="#7a3b3b", lw=0.8))
ax.axvline(n["mean_abs_df_pct"], color="0.7", lw=0.8, ls=":")
ax.axhline(n["hard_region_mac"], color="0.7", lw=0.8, ls=":")
ax.text(n["mean_abs_df_pct"]-0.12, max(fy)+0.006, "WIN quadrant: better shape\nAND better frequency  —  EMPTY",
        ha="right", va="top", fontsize=9.5, color="#3a6b35")
ax.set_xlabel("mean |natural-frequency error| %  (left = better)", fontsize=10)
ax.set_ylabel("hard-region mode-shape MAC  (up = better)", fontsize=10)
ax.set_title("Card D — hard-region shape vs frequency: the as-received FEM is already Pareto-optimal\n"
             "(full 9-parameter joint scan, re-pairing-robust tracked metric) → no stiffness update wins on both",
             fontsize=10)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(fontsize=8, loc="lower right", frameon=False)
fig.text(0.5, 0.01,
         f"{d['n_samples']} samples of theta in [0.6,1.4]^9, reduced 74-DOF model, {d['n_calib_modes']} calibrated "
         f"modes; each test mode keeps its tracked physical FEM partner (no greedy re-pairing). "
         f"Points improving hard-region shape without a frequency penalty: {d['n_both_improve']} of {d['n_samples']}.",
         ha="center", fontsize=7.8)
fig.tight_layout(rect=[0, 0.03, 1, 0.96])
out = f"{HERE}/figures/fig_joint_frontier.png"
os.makedirs(f"{HERE}/figures", exist_ok=True)
fig.savefig(out, dpi=150)
print("wrote", out)
