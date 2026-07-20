#!/usr/bin/env python3
"""Static figures for the MPL stand rebuild packet (FABLE, 2026-06-11).

Tufte skill applied (read .claude/skills/tufte-data-graphics/SKILL.md).
Declared deviations: the geometry/mode-shape renderings are 3-D wireframes —
required by the task card (these display SHAPES of a 3-D structure, not a
quantitative comparison); mode shapes are normalized (stated on-figure).

Figures:
  fig_geometry.png            3 orthographic views + interface points + items
  fig_mode_small_multiples.png  first 24 modes, deformed vs undeformed
  fig_freq_ladders.png        mode-frequency ladders: nominal vs variants
  fig_identifiability.png     strain-energy fractions (modes x K-groups) + KE region
  fig_interface_motion.png    panel-vs-frame motion at both mounts across modes
Every figure carries run/dataset stamp + estimated-values invalidity flag.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.sparse as sp
from mpl_toolkits.mplot3d.art3d import Line3DCollection, Poly3DCollection

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(WS, "figures")
os.makedirs(FIG, exist_ok=True)

STAMP = ("run: mpl_stand_fem_rebuild_20260611 | model: out/model nominal "
         "(shield 1.7mm steel, feet SPC) | FABLE")
FLAG = ("mounted masses/attachments + shield extents ESTIMATED from photos "
        "(ANDREW-CONFIRM-REQUIRED); no test data; prior model only")

arr = np.load(os.path.join(WS, "out", "model", "arrays.npz"))
grid_ids = arr["grid_ids"]
X = arr["X"]
region = arr["region"].astype(str)
gpos = {int(g): i for i, g in enumerate(grid_ids)}
d = json.load(open(os.path.join(WS, "out", "parsed_deck.json")))
meta = json.load(open(os.path.join(WS, "out", "model", "meta.json")))
iface = json.load(open(os.path.join(WS, "out", "interface_points.json")))

beam_pairs = [(gpos[c["ga"]], gpos[c["gb"]]) for c in d["cbeams"]]
vframe_pairs = [(gpos[a], gpos[b]) for a, b in meta["valve_frame"]["beams"]]
C_VFRAME = "#6a3d9a"  # 80/20 aluminum valve frame
quad_plate = [[gpos[g] for g in q["g"]] for q in d["cquads"]]
# shield quads: rebuild connectivity from mesh layout in meta? simpler: from
# shield grid lattice: regenerate via estimates (same code path as assemble)
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from estimates import ESTIMATES
mesh = ESTIMATES["shield_mesh"]["value"]


def shield_quads_for(ext, nx, nz, id0):
    ids = np.arange(id0, id0 + (nx + 1) * (nz + 1)).reshape(nz + 1, nx + 1).T
    qs = []
    for j in range(nz):
        for i in range(nx):
            qs.append([gpos[int(ids[i, j])], gpos[int(ids[i + 1, j])],
                       gpos[int(ids[i + 1, j + 1])], gpos[int(ids[i, j + 1])]])
    return qs


qs_u = shield_quads_for(ESTIMATES["shield_upper_extent"]["value"],
                        mesh["upper_nx"], mesh["upper_nz"], 800000)
n_u = (mesh["upper_nx"] + 1) * (mesh["upper_nz"] + 1)
qs_l = shield_quads_for(ESTIMATES["shield_lower_extent"]["value"],
                        mesh["lower_nx"], mesh["lower_nz"], 800000 + n_u)
quad_shield = qs_u + qs_l

feet = [1, 164, 692, 1212]
items = {k: v for k, v in meta["mount_log"].items()}
C_FRAME, C_PLATE, C_SHIELD = "0.55", "#d95f02", "#1f78b4"
C_ITEM, C_IFACE = "#33a02c", "#e31a1c"


def stamp(fig, extra=""):
    fig.text(0.005, 0.005, STAMP + (" | " + extra if extra else ""),
             fontsize=7, color="0.35")
    fig.text(0.005, 0.022, "FLAG: " + FLAG, fontsize=7, color="#b30000")


# ------------------------------------------------------------- fig_geometry
views = [("side view (x-z), thrust = -X", 0, 2, "x [in]", "z [in]"),
         ("front view (y-z), from +X logo side", 1, 2, "y [in]", "z [in]"),
         ("plan view (x-y)", 0, 1, "x [in]", "y [in]")]
fig, axes = plt.subplots(1, 3, figsize=(16, 6))
for ax, (title, i, j, xl, yl) in zip(axes, views):
    segs = [[(X[a][i], X[a][j]), (X[b][i], X[b][j])] for a, b in beam_pairs]
    from matplotlib.collections import LineCollection
    ax.add_collection(LineCollection(segs, colors=C_FRAME, lw=0.6))
    vsegs = [[(X[a][i], X[a][j]), (X[b][i], X[b][j])] for a, b in vframe_pairs]
    ax.add_collection(LineCollection(vsegs, colors=C_VFRAME, lw=1.4, zorder=4))
    for qs, col in ((quad_plate, C_PLATE), (quad_shield, C_SHIELD)):
        for q in qs:
            poly = plt.Polygon([(X[a][i], X[a][j]) for a in q], closed=True,
                               facecolor=col, alpha=0.35, edgecolor=col, lw=0.4)
            ax.add_patch(poly)
    for g in feet:
        ax.plot(X[gpos[g]][i], X[gpos[g]][j], "ks", ms=7, zorder=5)
    for name, it in items.items():
        gid = it.get("cg_grid", it.get("bare_conm2_on_grid"))
        p = X[gpos[gid]]
        ax.plot(p[i], p[j], "o", color=C_ITEM, ms=8, zorder=6)
        ax.annotate(name.replace("_", " "), (p[i], p[j]), fontsize=7,
                    textcoords="offset points", xytext=(4, 4), color=C_ITEM)
    for nm, dd, off in (("SHIELD MOUNT", iface["shield_mount"]["shield_xyz"],
                         (6, 6)),
                        ("BEAM MOUNT", iface["beam_mount"]["grid_xyz"],
                         (6, -16))):
        ax.plot(dd[i], dd[j], "*", color=C_IFACE, ms=15, zorder=7)
        ax.annotate(nm, (dd[i], dd[j]), fontsize=8, fontweight="bold",
                    textcoords="offset points", xytext=off, color=C_IFACE)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    ax.set_aspect("equal")
    ax.autoscale()
    ax.margins(0.08)
axes[0].annotate("feet = SPC 123456 (black squares)", (0.02, 0.98),
                 xycoords="axes fraction", fontsize=8, va="top")
fig.suptitle("MPL test stand rebuild: parsed deck + added shield (blue) + thrust "
             "plate (orange) + 80/20 valve frame (purple) + estimated boxes "
             "(green); units inches", fontsize=11)
stamp(fig, "geometry from Test Stand FEA.dat parse + estimates.py")
fig.tight_layout(rect=(0, 0.04, 1, 0.96))
fig.savefig(os.path.join(FIG, "fig_geometry.png"), dpi=160)
plt.close(fig)

# ------------------------------------------- mode shapes: shared machinery
shp = np.load(os.path.join(WS, "out", "modes_nominal_shapes.npz"))
freqs, Phi = shp["freqs"], shp["Phi"]
T = sp.load_npz(os.path.join(WS, "out", "model", "T_rbe2.npz"))
U = T @ Phi                     # full DOFs x modes
N = X.shape[0]
Ut = U.reshape(N, 6, -1)[:, :3, :]   # translations per grid per mode

span = np.array([X[:, k].ptp() for k in range(3)]).max()


def deformed(j, scale_frac=0.06):
    u = Ut[:, :, j]
    amp = np.abs(u).max()
    sc = scale_frac * span / amp
    return X + sc * u, sc


# ------------------------------------- fig_mode_small_multiples (first 24)
n_show = min(24, len(freqs))
fig = plt.figure(figsize=(16, 12))
for j in range(n_show):
    ax = fig.add_subplot(4, 6, j + 1, projection="3d")
    Xd, sc = deformed(j)
    segs0 = [[X[a], X[b]] for a, b in beam_pairs]
    ax.add_collection3d(Line3DCollection(segs0, colors="0.85", lw=0.4))
    segs = [[Xd[a], Xd[b]] for a, b in beam_pairs]
    ax.add_collection3d(Line3DCollection(segs, colors="0.3", lw=0.6))
    vsegs = [[Xd[a], Xd[b]] for a, b in vframe_pairs]
    ax.add_collection3d(Line3DCollection(vsegs, colors=C_VFRAME, lw=0.9))
    polys = [[Xd[a] for a in q] for q in quad_shield]
    ax.add_collection3d(Poly3DCollection(polys, facecolor=C_SHIELD, alpha=0.5,
                                         edgecolor=C_SHIELD, lw=0.2))
    polysp = [[Xd[a] for a in q] for q in quad_plate]
    ax.add_collection3d(Poly3DCollection(polysp, facecolor=C_PLATE, alpha=0.6,
                                         edgecolor=C_PLATE, lw=0.2))
    for g in feet:
        ax.scatter(*X[gpos[g]], color="k", s=12)
    ax.set_title(f"mode {j+1}: {freqs[j]:.1f} Hz", fontsize=8, pad=0)
    ax.set_axis_off()
    ax.set_box_aspect((X[:, 0].ptp(), X[:, 1].ptp(), X[:, 2].ptp()))
    ax.view_init(elev=18, azim=-50)
fig.suptitle("First 24 modes, nominal model (deformed dark vs undeformed light; "
             "displacement normalized per mode -- SHAPES, not amplitudes)",
             fontsize=12)
stamp(fig, "shapes from out/modes_nominal_shapes.npz")
fig.tight_layout(rect=(0, 0.03, 1, 0.97))
fig.savefig(os.path.join(FIG, "fig_mode_small_multiples.png"), dpi=140)
plt.close(fig)

# ---------------------------------------------------------- fig_freq_ladders
variants = [("nominal", "modes_nominal.json", None),
            ("no shield (deck as-given)", "modes_no_shield.json", None),
            ("shield t x0.5", "modes_shield_t_x0.5.json", None),
            ("shield t x2", "modes_shield_t_x2.json", None),
            ("screw k x0.01", "modes_screw_k_x0.01.json", None),
            ("screw k x100", "modes_screw_k_x100.json", None),
            ("aluminum shield", "modes_shield_aluminum.json", None),
            ("feet springs 1e8", "modes_feet_springs.json", None)]
fig, ax = plt.subplots(figsize=(12, 6.5))
for k, (name, fn, _) in enumerate(variants):
    dd = json.load(open(os.path.join(WS, "out", fn)))
    if "modes" in dd:
        fs = [m["freq_hz"] for m in dd["modes"]]
    else:
        fs = dd["freqs_hz"]
    fs = np.array([f for f in fs if f > 0.1])
    ax.vlines(fs, k + 0.12, k + 0.88, lw=0.8,
              color="#1f78b4" if k == 0 else "0.35")
    ax.text(6.3, k + 0.5, f"{name}  (n={fs.size})", va="center", fontsize=9)
ax.set_xscale("log")
ax.set_xlim(6, 520)
ax.set_yticks([])
ax.set_xlabel("frequency [Hz] (log axis; project rule for frequency plots)")
ax.set_title("Mode-frequency ladders to 500 Hz: nominal vs variants "
             "(each vertical tick = one mode)", fontsize=11)
for s in ("left", "right", "top"):
    ax.spines[s].set_visible(False)
stamp(fig, "data: out/modes_*.json")
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig(os.path.join(FIG, "fig_freq_ladders.png"), dpi=160)
plt.close(fig)

# -------------------------------------------------------- fig_identifiability
se = json.load(open(os.path.join(WS, "out", "strain_energy_nominal.json")))
groups = se["groups"]
nm = min(40, len(se["per_mode"]))
Mse = np.array([[row[g] for g in groups] for row in se["per_mode"][:nm]])
modes_f = [row["freq_hz"] for row in se["per_mode"][:nm]]
fig, ax = plt.subplots(figsize=(10.5, 9))
im = ax.imshow(Mse, aspect="auto", cmap="viridis", vmin=0, vmax=1)
ax.set_xticks(range(len(groups)))
ax.set_xticklabels([g.replace("_", "\n") for g in groups], fontsize=8)
ax.set_yticks(range(0, nm, 2))
ax.set_yticklabels([f"{j+1}: {modes_f[j]:.0f} Hz" for j in range(0, nm, 2)],
                   fontsize=7)
ax.set_ylabel("mode : frequency")
cb = fig.colorbar(im, ax=ax, shrink=0.8)
cb.set_label("strain-energy fraction  $f_{i,g} = \\phi_i^T K_g \\phi_i / \\lambda_i$")
ax.set_title("Which parameter group each mode 'feels' (first %d modes, nominal)\n"
             "Modal Identifiability Gate artifact: rows sum to 1" % nm,
             fontsize=11)
stamp(fig, "data: out/strain_energy_nominal.json")
fig.tight_layout(rect=(0, 0.045, 1, 1))
fig.savefig(os.path.join(FIG, "fig_identifiability.png"), dpi=160)
plt.close(fig)

# ------------------------------------------------------ fig_interface_motion
pm = iface["per_mode_motion"]
fm = np.array([r["freq_hz"] for r in pm])
panelX = np.array([r["shield_mount_panel_absXYZ"][0] for r in pm])
frameX = np.array([r["shield_mount_frame_absXYZ"][0] for r in pm])
beamA = np.array([np.linalg.norm(r["beam_mount_absXYZ"]) for r in pm])
fig, axs = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
axs[0].plot(fm, panelX, "o", ms=3.5, color="#1f78b4")
axs[0].plot(fm, frameX, "o", ms=3.5, color="0.45")
axs[0].set_yscale("log")
axs[0].set_ylabel("|X motion| (mass-norm., shapes)")
axs[0].text(fm[3], panelX.max() * 0.5, "shield-mount PANEL node (blue) vs "
            "nearest FRAME grid (grey)", fontsize=9)
axs[0].set_title("Interface-point motion across the nominal mode set "
                 "(mass-normalized shapes; relative comparisons only)",
                 fontsize=11)
axs[1].plot(fm, beamA, "o", ms=3.5, color="#33a02c")
axs[1].set_yscale("log")
axs[1].set_ylabel("|motion| at BEAM MOUNT grid 670")
axs[1].set_xlabel("mode frequency [Hz] (log axis)")
axs[1].set_xscale("log")
for ax in axs:
    for s in ("right", "top"):
        ax.spines[s].set_visible(False)
stamp(fig, "data: out/interface_points.json")
fig.tight_layout(rect=(0, 0.05, 1, 1))
fig.savefig(os.path.join(FIG, "fig_interface_motion.png"), dpi=160)
plt.close(fig)

# ------------------------------------------------------ fig_prior_predictive
pp = json.load(open(os.path.join(WS, "out", "prior_predictive.json")))
mass = np.array(pp["samples_for_fig"]["mass"])
f1d = np.array(pp["samples_for_fig"]["f1"])
fig, axs = plt.subplots(1, 3, figsize=(15, 4.6))
# (a) prior on mass
axs[0].hist(mass, bins=60, color="#1f78b4", alpha=0.85)
axs[0].axvline(2.0, color="0.4", ls="--", lw=1)
axs[0].axvline(4.0, color="0.4", ls="--", lw=1)
axs[0].set_xlabel("electronics-box mass [lbm]")
axs[0].set_ylabel("prior draws (200k MC)")
axs[0].set_title("(a) ELICITED PRIOR\nLogNormal, 95% = [2,4] lbm (Andrew)",
                 fontsize=10)
# (b) forward map f1(m)
mg = np.array(pp["f1_grid"]["mass_lbm"])
fg = np.array(pp["f1_grid"]["f1_hz"])
axs[1].plot(mg, fg, "o-", color="#d95f02")
axs[1].set_xlabel("box mass [lbm]")
axs[1].set_ylabel("fundamental $f_1$ [Hz]")
axs[1].set_title("(b) forward model $f_1(m)$ (monotone interp)\n(box mode "
                 "crosses f1 near 2-2.5 lb; box/valve confounded)", fontsize=10)
for x, y in zip(mg, fg):
    axs[1].annotate(f"{y:.2f}", (x, y), fontsize=7, textcoords="offset points",
                    xytext=(0, 5))
# (c) prior-predictive on f1
axs[2].hist(f1d, bins=60, color="#33a02c", alpha=0.85)
ppf = pp["prior_predictive_f1_hz"]
axs[2].axvline(ppf["p2_5"], color="0.4", ls="--", lw=1)
axs[2].axvline(ppf["p97_5"], color="0.4", ls="--", lw=1)
axs[2].set_xlabel("fundamental $f_1$ [Hz]")
axs[2].set_ylabel("prior-predictive draws")
axs[2].set_title("(c) PRIOR-PREDICTIVE $f_1$\nmedian %.2f, 95%% [%.2f, %.2f] Hz"
                 % (ppf["median"], ppf["p2_5"], ppf["p97_5"]), fontsize=10)
for ax in axs:
    for s in ("right", "top"):
        ax.spines[s].set_visible(False)
fig.suptitle("Prior-predictive: box-mass prior pushed FORWARD to the "
             "fundamental (NO sampler, NOT a posterior). Caveat: f1 is "
             "valve-dominated -> box mass only weakly observable here; the "
             "17-45 Hz box cluster is the real lever.", fontsize=10)
stamp(fig, "data: out/prior_predictive.json; prior out/priors.json")
fig.tight_layout(rect=(0, 0.05, 1, 0.93))
fig.savefig(os.path.join(FIG, "fig_prior_predictive.png"), dpi=160)
plt.close(fig)

print("figures written to", FIG)
