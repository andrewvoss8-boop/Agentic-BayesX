#!/usr/bin/env python3
"""Interface-point identification (Deliverable 5, decisions D22/D26).

(a) SHIELD MOUNT: middle of the shield panel at its TOP edge. Model shield top
    edge = z=48.5 (the top front rail line; the ~1.5 in physical overhang above
    the rail is ignored in the coarse mesh, D24). Mid-width y=-24.
(b) BEAM MOUNT: viewed from the logo/shield (+X) side looking -X with Z up,
    viewer-left = -y. "Top-left region, on the BACK wall of the top steel
    beam" = the z=48.5 / x=60.75 full-width rail, back (-X) face, near the
    y=-48 end. Interpreted clamp station ~6 in inboard of the left post;
    ANDREW-CONFIRM-REQUIRED.

Reports grid IDs + coordinates + back-wall surface offset (from the rail's
section orientation) + per-mode panel-vs-frame motion at both stations.
Output: out/interface_points.json
"""
import json
import os

import numpy as np

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
arr = np.load(os.path.join(WS, "out", "model", "arrays.npz"))
grid_ids = arr["grid_ids"]
X = arr["X"]
region = arr["region"].astype(str)
gpos = {int(g): i for i, g in enumerate(grid_ids)}

shp = np.load(os.path.join(WS, "out", "modes_nominal_shapes.npz"))
freqs, Phi = shp["freqs"], shp["Phi"]
master_dofs = shp["master_dofs"]
# map master rows -> (grid row, dof); Phi rows are master DOFs
full_from_master = master_dofs  # full dof id of each master row

d = json.load(open(os.path.join(WS, "out", "parsed_deck.json")))
xyzd = {int(k): np.array([v["x"], v["y"], v["z"]]) for k, v in d["grids"].items()}


def trans_at(gid):
    """3 x nmodes translation of a grid from master-space Phi (grid must be a
    master grid: all shield/frame grids used here are)."""
    i = gpos[gid]
    rows = []
    for k in range(3):
        full_dof = 6 * i + k
        m = np.where(full_from_master == full_dof)[0]
        assert m.size == 1, f"grid {gid} dof {k} not a master DOF"
        rows.append(Phi[m[0]])
    return np.vstack(rows)


# ---------------- (a) shield mount ----------------
shield_rows = np.where(region == "shield")[0]
target_a = np.array([61.5, -24.0, 48.5])
ia = shield_rows[np.argmin(np.linalg.norm(X[shield_rows] - target_a, axis=1))]
gid_shield = int(grid_ids[ia])
# nearest frame grid to the same station
frame_rows = np.where(region == "frame")[0]
ifr = frame_rows[np.argmin(np.linalg.norm(X[frame_rows] - target_a, axis=1))]
gid_shield_frame = int(grid_ids[ifr])

# ---------------- (b) beam mount ----------------
# Andrew round 3 (D33): "the top left beam is all the way on the leftmost,
# VERTICAL beam, not the top crossbeam" -> the y=-48 wall post (x=60.25),
# top region, back (-X) wall.
post = [(g, xyzd[g]) for g in xyzd
        if abs(xyzd[g][0] - 60.25) < 0.01 and abs(xyzd[g][1] + 48.0) < 0.05]
target_z = 47.0  # near the top of the post, just below the top-rail joint
gid_beam = int(min(post, key=lambda t: abs(t[1][2] - target_z))[0])
beam_xyz = xyzd[gid_beam]
# section orientation of the post at that grid: find a CBEAM on the post
rail_ids = {g for g, _ in post}
elem = next(c for c in d["cbeams"] if c["ga"] in rail_ids and c["gb"] in rail_ids)
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elements import beam_axes
R, _ = beam_axes(xyzd[elem["ga"]], xyzd[elem["gb"]], elem["v"])
# stress points are (y_local +-0.75, z_local +-1.25); which local axis points
# along global X tells the back-wall offset
ey, ez = R[1], R[2]
off_y = 0.75 * abs(ey[0])   # x-extent of local-y half-dim
off_z = 1.25 * abs(ez[0])   # x-extent of local-z half-dim
back_off = max(off_y, off_z)
back_wall_point = [float(beam_xyz[0] - back_off), float(beam_xyz[1]),
                   float(beam_xyz[2])]

# ---------------- per-mode motion ----------------
ua = trans_at(gid_shield)        # shield node at mount (panel motion)
uaf = trans_at(gid_shield_frame)  # nearest frame grid (frame motion)
ub = trans_at(gid_beam)          # rail grid at beam mount (frame)
n500 = int(np.sum(freqs <= 500.0))
per_mode = []
for j in range(min(len(freqs), n500)):
    per_mode.append(dict(
        mode=j + 1, freq_hz=round(float(freqs[j]), 2),
        shield_mount_panel_absXYZ=[round(float(abs(v)), 4) for v in ua[:, j]],
        shield_mount_frame_absXYZ=[round(float(abs(v)), 4) for v in uaf[:, j]],
        panel_to_frame_ratio_X=round(float(abs(ua[0, j])
                                           / max(abs(uaf[0, j]), 1e-12)), 2),
        beam_mount_absXYZ=[round(float(abs(v)), 4) for v in ub[:, j]]))

out = dict(
    shield_mount=dict(
        shield_grid=gid_shield, shield_xyz=[float(x) for x in X[ia]],
        nearest_frame_grid=gid_shield_frame,
        frame_xyz=[float(x) for x in X[ifr]],
        interpretation="top-center of shield mesh top edge (= z=48.5 top rail "
                       "line; physical shield overhangs ~1.5 in above, ignored "
                       "in coarse mesh)",
        flag="ANDREW-CONFIRM-REQUIRED (clamp station on shield top edge)"),
    beam_mount=dict(
        grid=gid_beam, grid_xyz=[float(x) for x in beam_xyz],
        back_wall_surface_point=back_wall_point,
        back_wall_offset_in=float(back_off),
        rail="leftmost VERTICAL post (y=-48, x=60.25), top region (Andrew "
             "round 3, D33: 'all the way on the leftmost, vertical beam, "
             "not the top crossbeam')",
        interpretation="viewed from logo (+X) side: left = -y; clamp near "
                       "the post top (z~47), back (-X) wall",
        flag="ANDREW-CONFIRM-REQUIRED (exact height on the post)"),
    f_clamp_mass_lbm=0.91557,
    f_clamp_note="CONFIRMED 415.3 g (Andrew 2026-06-11); NOT modeled this "
                 "task; ledgered for the coupling task",
    per_mode_motion=per_mode,
)
with open(os.path.join(WS, "out", "interface_points.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print(json.dumps({k: out[k] for k in ("shield_mount", "beam_mount")}, indent=1))
print(f"per-mode motion table: {len(per_mode)} modes")
