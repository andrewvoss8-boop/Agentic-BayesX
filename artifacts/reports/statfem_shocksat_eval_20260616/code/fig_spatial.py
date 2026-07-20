#!/usr/bin/env python3
"""Spatial figures on the actual ShockSat geometry (front X-Z projection from the FEM).

figF_spatial_error: one panel per bias combo -- structure (grey) with the BIASED property groups colored by the
  magnitude of their injected prior error |theta_truth - 1| [%]; observed sensors (filled green), held-out
  sensors (open orange), drive (black star). Shows WHERE the error lives vs WHERE we measure.
figG_spatial_ident: same geometry + sensors, property groups colored by their modal strain-energy
  identifiability [% mean SE]. Shows WHERE the data can/can't see the structure.

Geometry = subsampled per-group element centroids (data/group_geometry.npz, from the FEM). Sensor positions =
the 76 accelerometer node coordinates. (FEM-based and exact; the _ShockSat_Overview_20220606.pdf is the
external context document but registration to it is avoided in favor of exact FEM coordinates.)
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.colors import Normalize
import numpy as np

import core
import viz

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
DATA = WS / "data"

geo = np.load(DATA / "group_geometry.npz", allow_pickle=True)
GX = geo["xyz"].astype(float)            # (N,3)
GIDX = geo["group_idx"]                  # (N,) index into gnames
GN = [str(g) for g in geo["gnames"]]     # alphabetical, == core.GNAMES
assert GN == core.GNAMES

model = core.load_model()
ch = core.select_channels(model)
obs_xyz = model.dof_xyz[ch["observed"]]
ho_xyz = model.dof_xyz[ch["heldout"]]
dr_xyz = model.dof_xyz[ch["drive"]]

COMBO_NAME = {1: "identifiable", 2: "unidentifiable", 3: "mixed", 4: "large", 5: "broad small"}


def draw_structure(ax, value_per_group, cmap, norm, color_all=False):
    """Scatter element centroids in the X-Z plane. If color_all, colour every group by value;
    else grey backdrop + colour only groups with value>0."""
    x, z = GX[:, 0], GX[:, 2]
    if color_all:
        vals = np.array([value_per_group[GN[g]] for g in GIDX])
        o = np.argsort(vals)                      # draw high-value (identifiable) groups ON TOP (no occlusion)
        ax.scatter(x[o], z[o], c=vals[o], cmap=cmap, norm=norm, s=2.0, linewidths=0, rasterized=True)
    else:
        ax.scatter(x, z, c="0.85", s=1.5, linewidths=0, rasterized=True)
        m = np.array([value_per_group[GN[g]] > 1e-9 for g in GIDX])
        vals = np.array([value_per_group[GN[g]] for g in GIDX])[m]
        ax.scatter(x[m], z[m], c=vals, cmap=cmap, norm=norm, s=4.0, linewidths=0, rasterized=True)


def draw_sensors(ax, legend=False):
    ax.scatter(ho_xyz[:, 0], ho_xyz[:, 2], facecolors="none", edgecolors="#e8590c", s=46, lw=1.4,
               label="held-out sensor", zorder=5)
    ax.scatter(obs_xyz[:, 0], obs_xyz[:, 2], c="#1b7a3d", s=42, lw=0, label="observed sensor", zorder=6)
    ax.scatter([dr_xyz[0]], [dr_xyz[2]], marker="*", c="k", s=160, label="drive", zorder=7)
    ax.set_aspect("equal")
    ax.set_xlim(-13, 13); ax.set_ylim(-2, 60)
    ax.set_xticks([-10, 0, 10])
    if legend:
        ax.legend(loc="upper left", fontsize=7, framealpha=0.9, handletextpad=0.3, borderpad=0.3)


# ---------------- figF: prior-error map across the 5 combos ----------------
emax = 0.20
norm_e = Normalize(vmin=0, vmax=emax * 100)
cmap_e = cm.get_cmap("YlOrRd")
fig, axs = plt.subplots(1, 5, figsize=(13.5, 5.4), sharey=True)
for k, ci in enumerate([1, 2, 3, 4, 5]):
    ax = axs[k]
    tt = core.COMBOS[ci]["theta"]
    err = {g: abs(tt.get(g, 1.0) - 1.0) * 100 for g in GN}      # |theta_truth-1| in %
    draw_structure(ax, err, cmap_e, norm_e, color_all=False)
    draw_sensors(ax, legend=(k == 0))
    biased = ", ".join(f"{g.split('_')[0]} {('+' if tt[g]>1 else '')}{(tt[g]-1)*100:.0f}%" for g in tt)
    ax.set_title(f"combo {ci}: {COMBO_NAME[ci]}", fontsize=9)
    ax.set_xlabel(biased, fontsize=6.6)
    if k == 0:
        ax.set_ylabel("height  z  [in]")
sm = cm.ScalarMappable(norm=norm_e, cmap=cmap_e); sm.set_array([])
cb = fig.colorbar(sm, ax=axs, fraction=0.025, pad=0.02)
cb.set_label("injected prior error |theta_truth - 1|  [%]", fontsize=8)
fig.suptitle("ShockSat (front X-Z view): observed vs held-out sensors, property groups coloured by injected "
             "PRIOR ERROR per combo", fontsize=11, y=1.0)
viz.save(fig, "figF_spatial_error", extra="FEM geometry; grey = un-biased groups; 6 observed / 14 held-out")
print("figF done")

# ---------------- figG: identifiability map --------------------------------
idf = json.load(open(OUT / "identifiability.json"))
se = {r["group"]: r["mean_se_pct"] for r in idf["strain_energy"]}
informed = set(idf["informed_groups_strain_energy"])
norm_i = Normalize(vmin=0, vmax=max(se.values()))
cmap_i = cm.get_cmap("viridis")
fig2, ax2 = plt.subplots(1, 2, figsize=(8.2, 6.0), sharey=True)
# left: identifiability heat; right: same with group labels
draw_structure(ax2[0], se, cmap_i, norm_i, color_all=True)
draw_sensors(ax2[0], legend=True)
ax2[0].set_ylabel("height  z  [in]"); ax2[0].set_xlabel("x [in]")
ax2[0].set_title("coloured by modal strain energy", fontsize=9)
# right panel: grey structure + STAGGERED side-labels with leader lines (no overlap)
draw_structure(ax2[1], {g: 0.0 for g in GN}, cmap_i, norm_i, color_all=False)
cents = {g: (GX[GIDX == gi, 0].mean(), GX[GIDX == gi, 2].mean()) for gi, g in enumerate(GN)}
order = sorted(GN, key=lambda g: cents[g][1], reverse=True)        # top to bottom by height
label_z = np.linspace(56, 4, len(order))                          # evenly spaced label rows (no collision)
for g, lz in zip(order, label_z):
    cx, cz = cents[g]
    dark = g in informed
    col = "#111" if dark else "#aaa"
    ax2[1].plot([cx, 14.2], [cz, lz], "-", color=col, lw=0.5, alpha=0.6, zorder=2)
    ax2[1].annotate(f"{g} {se[g]:.0f}%", (14.5, lz), fontsize=6.8, ha="left", va="center",
                    color=col, fontweight=("bold" if dark else "normal"), zorder=8)
ax2[1].set_xlabel("x [in]"); ax2[1].set_title("group strain-energy %\n(dark = identifiable, >5%)", fontsize=9)
ax2[1].set_aspect("equal"); ax2[1].set_xlim(-13, 24); ax2[1].set_ylim(-2, 60); ax2[1].set_xticks([-10, 0, 10])
sm2 = cm.ScalarMappable(norm=norm_i, cmap=cmap_i); sm2.set_array([])
cb2 = fig2.colorbar(sm2, ax=ax2, fraction=0.04, pad=0.02)
cb2.set_label("modal strain-energy fraction (mean over in-band modes)  [%]", fontsize=8)
fig2.suptitle("ShockSat identifiability map: only ~4/9 groups (boxes, plates, cross-beam) carry signal",
              fontsize=10.5, y=1.0)
viz.save(fig2, "figG_spatial_ident", extra="FEM geometry; same sensors as figF; strain-energy gate")
print("figG done")
