#!/usr/bin/env python3
"""FEM visualization + export for the round-3 MDOF model (Claude Code Opus 4.8 runner).

Makes the AI-generated mesh INSPECTABLE by the human (task-card requirement):
  report/mesh/nodes.csv      (node_id, x, y, z)                      -- human-readable card
  report/mesh/elements.csv   (elem_id, type, connectivity node_ids)  -- human-readable card
  report/mesh/model.bdf      NASTRAN bulk data (GRID + CBAR/CONM2)    -- Femap
  report/mesh/model.vtu      VTK unstructured (lines)                 -- ParaView
  report/mesh/model.obj      wavefront line geometry                  -- Blender
  report/figures/mesh_assembly.png            undeformed assembly
  report/figures/modeshapes_dome.png          first ~5 dome mode shapes
  report/figures/modeshapes_tray.png          first ~5 tray mode shapes (incl joint bounce)

UNITS: SI metres. COORDINATE FRAME: global X-Z meridional plane; Z up (launch axis),
X radial. Y = 0 (the 1-D strip models live in the X-Z plane). The dome meridian runs from the
clamped base ring (node 0) to the apex/strut-attach interface (last dome node). The tray panel is a
horizontal strip below the apex; a single equivalent strut/joint connects the apex to the tray centre.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import meshio

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "code"))
import mdof_forward as fw

MESH = HERE / "report" / "mesh"
FIG = HERE / "report" / "figures"


def dome_node_coords(nele):
    """Place dome FEM nodes along the 2:1 ellipsoidal meridian (base ring -> apex)."""
    phi = np.linspace(0.0, np.pi/2, nele + 1)   # 0 = base (equator), pi/2 = apex
    x = fw.DOME_R * np.cos(phi)
    z = fw.DOME_HEIGHT * np.sin(phi)
    y = np.zeros_like(x)
    return np.column_stack([x, y, z])


def tray_node_coords(nele, z_tray=-0.8, x_apex=0.0, z_apex=None):
    """Place tray FEM nodes along a horizontal strip centred below the apex."""
    if z_apex is None:
        z_apex = fw.DOME_HEIGHT
    xs = np.linspace(-fw.TRAY_L/2, fw.TRAY_L/2, nele + 1) + x_apex
    z = np.full_like(xs, z_apex + z_tray)
    y = np.zeros_like(xs)
    return np.column_stack([xs, y, z])


def build_assembly():
    dome_xyz = dome_node_coords(fw.DOME_NELE)
    tray_xyz = tray_node_coords(fw.TRAY_NELE)
    n_dome = dome_xyz.shape[0]
    n_tray = tray_xyz.shape[0]
    points = np.vstack([dome_xyz, tray_xyz])
    # line elements: dome beam, tray beam, and one strut/joint apex->tray-centre
    dome_lines = [[i, i+1] for i in range(n_dome-1)]
    tray_off = n_dome
    tray_lines = [[tray_off+i, tray_off+i+1] for i in range(n_tray-1)]
    apex = n_dome - 1
    tray_center = tray_off + fw.TRAY_NELE//2
    strut = [[apex, tray_center]]
    elem_blocks = [("dome_beam", dome_lines), ("tray_beam", tray_lines), ("strut_joint", strut)]
    meta = dict(n_dome=n_dome, n_tray=n_tray, apex_node=apex, tray_center_node=tray_center,
                avionics_node=tray_center)
    return points, elem_blocks, meta


def write_csv_card(points, elem_blocks):
    with open(MESH / "nodes.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["node_id", "x_m", "y_m", "z_m"])
        for i, p in enumerate(points):
            w.writerow([i, f"{p[0]:.6f}", f"{p[1]:.6f}", f"{p[2]:.6f}"])
    with open(MESH / "elements.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["elem_id", "type", "node_i", "node_j"])
        eid = 0
        for etype, lines in elem_blocks:
            for ln in lines:
                w.writerow([eid, etype, ln[0], ln[1]]); eid += 1


def write_meshio(points, elem_blocks):
    cells = [("line", np.asarray([ln for _, lines in elem_blocks for ln in lines], dtype=int))]
    cell_tags = []
    for etype, lines in elem_blocks:
        cell_tags += [etype]*len(lines)
    mesh = meshio.Mesh(points=points, cells=cells,
                       cell_data={"component": [np.array(
                           [{"dome_beam": 0, "tray_beam": 1, "strut_joint": 2}[t] for t in cell_tags])]})
    meshio.write(MESH / "model.vtu", mesh)          # ParaView (lines supported)
    meshio.write(MESH / "model.msh", mesh, file_format="gmsh")  # gmsh (Blender via import)
    # OBJ line geometry written manually (meshio's OBJ writer is surface-only); Blender imports 'l'
    all_lines = [ln for _, lines in elem_blocks for ln in lines]
    with open(MESH / "model.obj", "w") as f:
        f.write("# Round-3 MDOF assembly line geometry (SI metres; X-Z meridional plane)\n")
        for p in points:
            f.write(f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
        for ln in all_lines:
            f.write(f"l {ln[0]+1} {ln[1]+1}\n")


def write_nastran_bdf(points, elem_blocks, meta):
    """Minimal NASTRAN bulk data: GRID + CBAR (beams) + PBAR/MAT1 + CONM2 (avionics) + SPC (clamp)."""
    lines = ["$ Round-3 MDOF assembly (Claude Code Opus 4.8) -- SI (m, kg). Frame: X radial, Z launch axis.",
             "BEGIN BULK"]
    for i, p in enumerate(points):
        lines.append(f"GRID,{i+1},,{p[0]:.6f},{p[1]:.6f},{p[2]:.6f}")
    # materials/properties (representative; dome Al2219, tray Al-Li2198)
    lines.append("MAT1,1,7.31+10,,0.33,2840.0")   # dome
    lines.append("MAT1,2,7.00+10,,0.33,2700.0")   # tray
    lines.append(f"PBAR,1,1,{fw.DOME_STRIP_W*fw.DOME_T:.6e},{fw.DOME_STRIP_W*fw.DOME_T**3/12:.6e},,")
    lines.append(f"PBAR,2,2,{fw.TRAY_W*fw.TRAY_T_MASS:.6e},{fw.TRAY_W*fw.TRAY_T_BEND**3/12:.6e},,")
    lines.append("PBAR,3,2,3.0-4,1.0-8,,")        # strut/joint (axial-dominant)
    eid = 1
    pid_of = {"dome_beam": 1, "tray_beam": 2, "strut_joint": 3}
    for etype, blk in elem_blocks:
        for ln in blk:
            lines.append(f"CBAR,{eid},{pid_of[etype]},{ln[0]+1},{ln[1]+1},0.,0.,1.")
            eid += 1
    # avionics lumped mass at tray centre
    lines.append(f"CONM2,{eid},{meta['avionics_node']+1},,{fw.M_AVIONICS:.3f}")
    # clamp dome base ring (node 0)
    lines.append("SPC1,1,123456,1")
    lines.append("ENDDATA")
    (MESH / "model.bdf").write_text("\n".join(lines) + "\n")


def _dome_mode_shapes(n=5):
    f, phi, free, inode, x, geom = fw.dome_fem(n=n)
    # reduced->full transverse deflection (clamped-free: prepend node0 w=0)
    shapes = []
    for r in range(n):
        wred = phi[0::2, r]            # transverse DOFs among reduced (every other, since [w,th] pairs)
        w_full = np.concatenate([[0.0], wred])
        w_full = w_full/np.max(np.abs(w_full))
        shapes.append(w_full)
    return x, shapes, f


def _tray_mode_shapes(n=5):
    f, phi, free, center, x, geom = fw.tray_panel_fem(n=n+2)
    shapes = []; fsel = []
    # skip the 2 rigid-body modes (~0 Hz); show joint-bounce conceptually + flex modes
    cnt = 0
    for r in range(phi.shape[1]):
        if f[r] < 1.0:
            continue
        wfull = phi[0::2, r]
        wfull = wfull/np.max(np.abs(wfull))
        shapes.append(wfull); fsel.append(f[r]); cnt += 1
        if cnt >= n-1:
            break
    return x, shapes, np.array(fsel)


def render_modeshapes():
    # dome
    x, shapes, f = _dome_mode_shapes(5)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    for r, sh in enumerate(shapes):
        ax.plot(x, sh, marker=".", label=f"mode {r+1}: {fw.DOME_F1_HZ*f[r]/f[0]:.1f} Hz (calibrated)")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("meridian arc length s [m] (base s=0 -> apex/interface)")
    ax.set_ylabel("normalized transverse mode shape")
    ax.set_title("Dome (source) meridional-strip FEM mode shapes — pressurized (3.5 bar), Al 2219\n"
                 "mode 1 = 93.50 Hz = global axisymmetric BOUNCE/BREATHING mode (~110 nominal); strip underestimates shell stiffness")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "modeshapes_dome.png", dpi=140); plt.close(fig)

    # tray
    x, shapes, f = _tray_mode_shapes(5)
    fig, ax = plt.subplots(figsize=(8, 4.6))
    # joint bounce = rigid translation of the whole panel on the soft joint (depict as flat line at 1)
    ax.plot(x, np.ones_like(x), marker=".", color="#d62728",
            label=f"mode 1 (joint bounce, rigid): {fw.TRAY_F1_HZ:.2f} Hz")
    for r, sh in enumerate(shapes):
        ax.plot(x, sh, marker=".", label=f"panel flex mode {r+2}: {f[r]:.0f} Hz")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("panel coordinate x [m] (centre = avionics)")
    ax.set_ylabel("normalized transverse mode shape")
    ax.set_title("Tray (load) isogrid-panel FEM mode shapes — free panel + 136 kg avionics\n"
                 "fundamental = rigid bounce on the SOFT JOINT (86.25 Hz); panel flex modes >> joint")
    ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    fig.tight_layout(); fig.savefig(FIG / "modeshapes_tray.png", dpi=140); plt.close(fig)


def render_assembly(points, elem_blocks, meta):
    fig, ax = plt.subplots(figsize=(7.5, 7.0))
    colors = {"dome_beam": "#1f77b4", "tray_beam": "#2ca02c", "strut_joint": "#d62728"}
    for etype, lines in elem_blocks:
        first = True
        for ln in lines:
            p0, p1 = points[ln[0]], points[ln[1]]
            ax.plot([p0[0], p1[0]], [p0[2], p1[2]], "-o", color=colors[etype], ms=3, lw=1.6,
                    label=etype if first else None)
            first = False
    ax.plot(points[meta["apex_node"], 0], points[meta["apex_node"], 2], "k*", ms=16,
            label="interface DOF (apex / strut-to-dome)")
    ax.plot(points[meta["avionics_node"], 0], points[meta["avionics_node"], 2], "ks", ms=10,
            label="avionics lumped 136 kg")
    ax.set_xlabel("X radial [m]"); ax.set_ylabel("Z launch axis [m]")
    ax.set_title("MDOF assembly mesh (undeformed) — dome meridian + isogrid tray + single strut/joint\n"
                 "SI metres; X-Z meridional plane (Y=0); dome base ring clamped")
    ax.axis("equal"); ax.grid(True, alpha=0.3); ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout(); fig.savefig(FIG / "mesh_assembly.png", dpi=140); plt.close(fig)


def main():
    MESH.mkdir(parents=True, exist_ok=True); FIG.mkdir(parents=True, exist_ok=True)
    points, elem_blocks, meta = build_assembly()
    write_csv_card(points, elem_blocks)
    write_meshio(points, elem_blocks)
    write_nastran_bdf(points, elem_blocks, meta)
    render_assembly(points, elem_blocks, meta)
    render_modeshapes()
    n_elems = sum(len(b) for _, b in elem_blocks)
    summary = dict(n_nodes=int(points.shape[0]), n_elements=int(n_elems),
                   files=["nodes.csv", "elements.csv", "model.bdf", "model.vtu", "model.obj"],
                   figures=["mesh_assembly.png", "modeshapes_dome.png", "modeshapes_tray.png"],
                   units="SI metres", frame="X radial, Z launch axis, Y=0")
    import json
    (MESH / "mesh_summary.json").write_text(json.dumps(summary, indent=2))
    print("mesh export OK:", summary)


if __name__ == "__main__":
    main()
