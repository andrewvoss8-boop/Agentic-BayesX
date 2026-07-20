#!/usr/bin/env python3
"""Mode-shape GIFs (Deliverable 6): first 15 flexible modes of the nominal
model. 3-D wireframe (card requirement; declared Tufte deviation -- this
renders 3-D SHAPES, not a quantitative chart): beams as lines, quads as
patches, CONM2 markers, fixed feet marked, undeformed overlay light.
Frequency + mode number + run stamp + per-mode normalized scale factor ON
the figure ("shapes, not amplitudes").
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.sparse as sp
from matplotlib.animation import FuncAnimation, PillowWriter
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIFD = os.path.join(WS, "gifs")
os.makedirs(GIFD, exist_ok=True)
# wipe stale GIFs: filenames embed frequency, so a re-run with shifted modes
# would otherwise ACCUMULATE stale-named copies (D35).
for _f in os.listdir(GIFD):
    if _f.endswith(".gif"):
        os.remove(os.path.join(GIFD, _f))
N_MODES = int(os.environ.get("N_GIF_MODES", "15"))
N_FRAMES = 24

STAMP = ("run mpl_stand_fem_rebuild_20260611 | nominal model (shield 1.7mm "
         "steel; masses ESTIMATED unconfirmed) | FABLE")

arr = np.load(os.path.join(WS, "out", "model", "arrays.npz"))
grid_ids = arr["grid_ids"]
X = arr["X"]
gpos = {int(g): i for i, g in enumerate(grid_ids)}
d = json.load(open(os.path.join(WS, "out", "parsed_deck.json")))
meta = json.load(open(os.path.join(WS, "out", "model", "meta.json")))

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estimates import ESTIMATES
mesh = ESTIMATES["shield_mesh"]["value"]

beam_pairs = [(gpos[c["ga"]], gpos[c["gb"]]) for c in d["cbeams"]]
vframe_pairs = [(gpos[a], gpos[b]) for a, b in meta["valve_frame"]["beams"]]
quad_plate = [[gpos[g] for g in q["g"]] for q in d["cquads"]]


def shield_quads_for(nx, nz, id0):
    ids = np.arange(id0, id0 + (nx + 1) * (nz + 1)).reshape(nz + 1, nx + 1).T
    qs = []
    for j in range(nz):
        for i in range(nx):
            qs.append([gpos[int(ids[i, j])], gpos[int(ids[i + 1, j])],
                       gpos[int(ids[i + 1, j + 1])], gpos[int(ids[i, j + 1])]])
    return qs


n_u = (mesh["upper_nx"] + 1) * (mesh["upper_nz"] + 1)
quad_shield = (shield_quads_for(mesh["upper_nx"], mesh["upper_nz"], 800000)
               + shield_quads_for(mesh["lower_nx"], mesh["lower_nz"],
                                  800000 + n_u))
feet = [1, 164, 692, 1212]
item_grids = [v.get("cg_grid", v.get("bare_conm2_on_grid"))
              for v in meta["mount_log"].values()]

shp = np.load(os.path.join(WS, "out", "modes_nominal_shapes.npz"))
freqs, Phi = shp["freqs"], shp["Phi"]
T = sp.load_npz(os.path.join(WS, "out", "model", "T_rbe2.npz"))
U = (T @ Phi).reshape(X.shape[0], 6, -1)[:, :3, :]
span = max(X[:, k].ptp() for k in range(3))

for j in range(min(N_MODES, len(freqs))):
    u = U[:, :, j]
    sc = 0.06 * span / np.abs(u).max()
    fig = plt.figure(figsize=(7.5, 6.5))
    ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Line3DCollection([[X[a], X[b]] for a, b in beam_pairs],
                                         colors="0.88", lw=0.5))
    beams_art = Line3DCollection([[X[a], X[b]] for a, b in beam_pairs],
                                 colors="0.25", lw=0.8)
    ax.add_collection3d(beams_art)
    vframe_art = Line3DCollection([[X[a], X[b]] for a, b in vframe_pairs],
                                  colors="#6a3d9a", lw=1.2)
    ax.add_collection3d(vframe_art)
    shield_art = Poly3DCollection([[X[a] for a in q] for q in quad_shield],
                                  facecolor="#1f78b4", alpha=0.55,
                                  edgecolor="#1f78b4", lw=0.3)
    ax.add_collection3d(shield_art)
    plate_art = Poly3DCollection([[X[a] for a in q] for q in quad_plate],
                                 facecolor="#d95f02", alpha=0.65,
                                 edgecolor="#d95f02", lw=0.3)
    ax.add_collection3d(plate_art)
    items_art = ax.scatter(*np.array([X[gpos[g]] for g in item_grids]).T,
                           color="#33a02c", s=40, depthshade=False)
    for g in feet:
        ax.scatter(*X[gpos[g]], color="k", s=30, marker="s", depthshade=False)
    ax.set_box_aspect((X[:, 0].ptp(), X[:, 1].ptp(), X[:, 2].ptp()))
    ax.view_init(elev=18, azim=-50)
    ax.set_axis_off()
    ax.set_title(f"Mode {j+1}: {freqs[j]:.2f} Hz (nominal)", fontsize=13)
    fig.text(0.02, 0.060, f"displacement scale x{sc:.1f} (normalized) -- "
             "SHAPE, not amplitude; feet (black squares) SPC-fixed",
             fontsize=8)
    fig.text(0.02, 0.018, STAMP, fontsize=7, color="0.35")

    def update(fr, u=u, sc=sc, beams_art=beams_art, shield_art=shield_art,
               plate_art=plate_art, items_art=items_art, vframe_art=vframe_art):
        a = np.sin(2 * np.pi * fr / N_FRAMES)
        Xd = X + a * sc * u
        beams_art.set_segments([[Xd[p], Xd[q]] for p, q in beam_pairs])
        vframe_art.set_segments([[Xd[p], Xd[q]] for p, q in vframe_pairs])
        shield_art.set_verts([[Xd[i] for i in q] for q in quad_shield])
        plate_art.set_verts([[Xd[i] for i in q] for q in quad_plate])
        items_art._offsets3d = tuple(
            np.array([Xd[gpos[g]] for g in item_grids]).T)
        return []

    anim = FuncAnimation(fig, update, frames=N_FRAMES, blit=False)
    out = os.path.join(GIFD, f"mode_{j+1:02d}_{freqs[j]:.1f}Hz.gif")
    anim.save(out, writer=PillowWriter(fps=12), dpi=90)
    plt.close(fig)
    print("wrote", os.path.basename(out), flush=True)

print("done:", min(N_MODES, len(freqs)), "GIFs")
