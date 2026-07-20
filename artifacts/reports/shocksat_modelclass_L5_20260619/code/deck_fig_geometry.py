#!/usr/bin/env python3
"""Deck figures — FEM/sensor geometry + strain energy (Tufte gate). Side view of the stacked satellite:
horizontal = x (in), vertical = z (in, base->dish). Produces:
  fig_param_locations.png  - FEM node cloud colored by the 9 stiffness-calibration GROUPS (where the params live)
  fig_sensor_map.png       - sensors: 8 hard accels (red) vs easy (grey) + drive point
  fig_train_test_split.png - one held-out split: observed (blue) vs held-out (orange) channels
  fig_strain_energy.png    - matched-mode x group strain-energy fraction heatmap (joints are SE-diluted)
"""
from __future__ import annotations
import sys
from types import SimpleNamespace
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; FIG.mkdir(exist_ok=True)
HARD = {4, 27, 38, 40, 52, 69, 92, 98}
GNAMES = ["al_welds", "angle_brackets", "bottom_box", "contact", "cross_beam", "joints", "plates", "steel_welds", "top_box"]

gg = np.load(WS / "data" / "group_geometry.npz", allow_pickle=True)
xyz = gg["xyz"]; gidx = gg["group_idx"]; gn = [str(x) for x in gg["gnames"]]
R = rf.load_reduced()
meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
ch = rf.build_channels(R, meas["daq"])
didx = {d: i for i, d in enumerate(meas["daq"])}
dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
elig = np.where(dr >= hq.DR_MIN)[0]
coords = ch.coords[elig]; daqs = [ch.daq[p] for p in elig]
is_hard = np.array([d in HARD for d in daqs])

cols9 = cm.get_cmap("tab10")(np.linspace(0, 1, 10))


def backdrop(ax):
    ax.scatter(xyz[:, 0], xyz[:, 2], s=1, c="0.86", edgecolor="none", rasterized=True)
    ax.set_xlabel("x (in)"); ax.set_ylabel("z (in)  base → dish"); ax.set_aspect("equal")
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)


# --- fig_param_locations ---
fig, ax = plt.subplots(figsize=(5.2, 7.2))
for g in range(9):
    m = gidx == g
    ax.scatter(xyz[m, 0], xyz[m, 2], s=2, c=[cols9[g]], edgecolor="none", label=gn[g], rasterized=True)
ax.set_xlabel("x (in)"); ax.set_ylabel("z (in)  base → dish"); ax.set_aspect("equal")
for sp in ("top", "right"): ax.spines[sp].set_visible(False)
ax.legend(markerscale=4, fontsize=7, loc="upper left", framealpha=0.9, ncol=1)
ax.set_title("FEM stiffness-calibration parameters (9 groups)", fontsize=10, loc="left")
fig.text(0.5, 0.01, "Each θ_g scales one group's stiffness. Joints/contact = bolted-joint & contact CBUSHes. FEM node cloud, side view.",
         ha="center", fontsize=6.5, color="0.4")
fig.tight_layout(rect=[0, 0.03, 1, 1]); fig.savefig(FIG / "fig_param_locations.png", dpi=140); plt.close(fig)

# --- fig_sensor_map ---
fig, ax = plt.subplots(figsize=(5.2, 7.2)); backdrop(ax)
ax.scatter(coords[~is_hard, 0], coords[~is_hard, 2], s=26, c="0.45", edgecolor="k", linewidth=0.3, label=f"easy ({(~is_hard).sum()})")
ax.scatter(coords[is_hard, 0], coords[is_hard, 2], s=70, c="#b2182b", edgecolor="k", linewidth=0.5, marker="D", label=f"hard ({is_hard.sum()})")
ax.scatter([ch.drive_xyz[0]], [ch.drive_xyz[2]], s=180, c="#f1a340", edgecolor="k", marker="*", label="impact (drive)", zorder=5)
for i in np.where(is_hard)[0]:
    ax.annotate(f"ch{daqs[i]}", (coords[i, 0], coords[i, 2]), fontsize=6.5, xytext=(3, 2), textcoords="offset points")
ax.legend(fontsize=7.5, loc="upper left"); ax.set_title("Accelerometers: 8 hard vs easy", fontsize=10, loc="left")
fig.text(0.5, 0.01, "Hard = impact face / bulkheads / bolted joint / strut / dish (a-priori model-form hotspots, Card D). 77 high-DR channels.",
         ha="center", fontsize=6.5, color="0.4")
fig.tight_layout(rect=[0, 0.03, 1, 1]); fig.savefig(FIG / "fig_sensor_map.png", dpi=140); plt.close(fig)

# --- fig_train_test_split (seed 0, same protocol as held-out QOI) ---
rng = np.random.default_rng(0); perm = rng.permutation(elig)
n_obs = int(round(0.6 * len(perm))); obs = set(perm[:n_obs].tolist()); hoa = set(perm[n_obs:].tolist())
obsm = np.array([elig[i] in obs for i in range(len(elig))])
fig, ax = plt.subplots(figsize=(5.2, 7.2)); backdrop(ax)
ax.scatter(coords[obsm, 0], coords[obsm, 2], s=34, c="#2166ac", edgecolor="k", linewidth=0.3, label=f"observed / train ({obsm.sum()})")
ax.scatter(coords[~obsm, 0], coords[~obsm, 2], s=34, c="#f1a340", edgecolor="k", linewidth=0.3, marker="s", label=f"held-out / test ({(~obsm).sum()})")
ax.legend(fontsize=7.5, loc="upper left"); ax.set_title("One held-out split (seed 0): observe 60%, predict 40%", fontsize=10, loc="left")
fig.text(0.5, 0.01, "θ calibrated on observed-channel modal frequencies; QOI predicted at held-out channels (their |H| never used in fitting). ≥3 random splits scored.",
         ha="center", fontsize=6.5, color="0.4")
fig.tight_layout(rect=[0, 0.03, 1, 1]); fig.savefig(FIG / "fig_train_test_split.png", dpi=140); plt.close(fig)

# --- fig_strain_energy (matched-mode x group SE fraction) ---
meas_f, _ = mf.extract_measured_modes(meas, ch); pairs, _ = mf.match(R, meas_f)
idx = np.array([p[0] for p in pairs]); hz = np.array([p[1] for p in pairs])
import json
tm = json.loads((WS.parent / "statfem_real_validation_20260617" / "out" / "modal_feature.json").read_text())["theta_post"]
theta = np.array([tm[g]["med"] for g in GNAMES])
K = R.A_fix + np.einsum("g,gij->ij", theta, R.A); lam, Q = np.linalg.eigh(K)
SE = np.zeros((len(idx), 9))
for r, mode in enumerate(idx):
    phi = Q[:, mode]
    for g in range(9):
        SE[r, g] = theta[g] * (phi @ R.A[g] @ phi) / lam[mode]
order = np.argsort(hz)
fig, ax = plt.subplots(figsize=(7.6, 6.2))
im = ax.imshow(SE[order], aspect="auto", cmap="viridis", vmin=0, vmax=min(1, SE.max()))
ax.set_xticks(range(9)); ax.set_xticklabels(GNAMES, rotation=40, ha="right", fontsize=8)
ax.set_yticks(range(len(idx))); ax.set_yticklabels([f"{h:.0f}" for h in hz[order]], fontsize=6)
ax.set_ylabel("matched mode frequency (Hz)"); ax.set_title("Modal strain-energy fraction per calibration group", fontsize=10, loc="left")
ax.axvline(GNAMES.index("joints") - 0.5, color="w", lw=0);
gi = GNAMES.index("joints")
ax.add_patch(plt.Rectangle((gi - 0.5, -0.5), 1, len(idx), fill=False, edgecolor="#d7301f", lw=2))
ax.text(gi, -1.2, "joints\nSE-diluted", color="#d7301f", ha="center", fontsize=7.5)
cb = fig.colorbar(im, ax=ax, fraction=0.04); cb.set_label("SE fraction  f = φᵀ(θ A_g)φ / λ", fontsize=8)
fig.text(0.5, 0.005, "Modes load bottom/top box + cross-beam + plates; joints store ~3% (peak ~20% at 151 Hz) → joint stiffness & damping weakly identifiable.",
         ha="center", fontsize=6.5, color="0.4")
fig.tight_layout(rect=[0, 0.02, 1, 1]); fig.savefig(FIG / "fig_strain_energy.png", dpi=140); plt.close(fig)
print("wrote: fig_param_locations, fig_sensor_map, fig_train_test_split, fig_strain_energy")
