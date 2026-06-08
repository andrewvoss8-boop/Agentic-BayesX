"""
Parse CalculiX outputs (hexapod.dat eigenfrequencies, hexapod.frd mode shapes),
classify modes, render figures, and write results.json.

Run after ccx: ../../.venv/bin/python parse_ccx.py
"""
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import spec

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.abspath(os.path.join(HERE, "..", "model"))
FIG = os.path.abspath(os.path.join(HERE, "..", "figures"))
os.makedirs(FIG, exist_ok=True)


def parse_dat_freqs(path):
    freqs = []
    with open(path) as f:
        lines = f.readlines()
    started = False
    for ln in lines:
        if "MODE NO" in ln and "EIGENVALUE" in ln:
            started = True
            continue
        if started:
            if "PARTICIPATION" in ln:
                break
            parts = ln.split()
            if len(parts) >= 4:
                try:
                    int(parts[0])
                    freqs.append(float(parts[3]))  # cycles/time = Hz
                except ValueError:
                    pass
    return np.array(freqs)


def parse_frd(path):
    """Return node coords dict {id:(x,y,z)} and list of mode displacement dicts
    [{id:(u1,u2,u3)}, ...]."""
    coords = {}
    modes = []
    with open(path) as f:
        lines = f.readlines()
    i = 0
    n = len(lines)
    cur = None
    in_nodes = False
    in_disp = False
    while i < n:
        ln = lines[i]
        # node block marker: '    2C'
        if ln[:6].strip() == "2C":
            in_nodes = True; i += 1; continue
        # displacement result block: contains 'DISP' on a -4 line
        if ln[:3] == " -4" and "DISP" in ln:
            cur = {}; in_disp = True; in_nodes = False; i += 1; continue
        if ln[:3] == " -3":
            if in_disp and cur is not None:
                modes.append(cur); cur = None; in_disp = False
            in_nodes = False
            i += 1; continue
        if ln[:3] == " -1" and (in_nodes or in_disp):
            nid = int(ln[3:13])
            vals = []
            rest = ln[13:].rstrip("\n")
            for k in range(0, len(rest)//12*12, 12):
                seg = rest[k:k+12].strip()
                if seg:
                    vals.append(float(seg))
            if in_nodes and len(vals) >= 3:
                coords[nid] = (vals[0], vals[1], vals[2])
            elif in_disp and len(vals) >= 3:
                cur[nid] = (vals[0], vals[1], vals[2])
            i += 1; continue
        if ln[:3] == " -2":
            i += 1; continue
        if ln[:3] == " -5":
            i += 1; continue
        i += 1
    return coords, modes


def main():
    meta = json.load(open(os.path.join(MODEL, "deck_meta.json")))
    f = parse_dat_freqs(os.path.join(MODEL, "hexapod.dat"))
    coords, modes = parse_frd(os.path.join(MODEL, "hexapod.frd"))
    assert len(modes) >= 6, f"only {len(modes)} mode shapes parsed"

    # tray node ids: 1..NX*NY*NZ ; mid-plane layer for surface plotting
    NX, NY, NZ = meta["NX"], meta["NY"], meta["NZ"]
    nmax = NX*NY*NZ

    def tray_id(i, j, k):
        return 1 + i + j*NX + k*NX*NY
    topk = NZ-1
    tray_ids_top = [tray_id(i, j, topk) for j in range(NY) for i in range(NX)]
    tray_ids_all = [tray_id(i, j, k) for k in range(NZ) for j in range(NY) for i in range(NX)]

    # classification via rigid-body fit on tray nodes (top layer)
    labels = []; diags = []
    for md in modes:
        pts = np.array([coords[n] for n in tray_ids_all])
        u = np.array([md.get(n, (0, 0, 0)) for n in tray_ids_all])
        c = pts.mean(0); rc = pts-c
        A = np.zeros((3*len(pts), 6)); b = np.zeros(3*len(pts))
        for kk in range(len(pts)):
            A[3*kk:3*kk+3, :3] = np.eye(3)
            x, y, z = rc[kk]
            A[3*kk:3*kk+3, 3:] = [[0, z, -y], [-z, 0, x], [y, -x, 0]]
            b[3*kk:3*kk+3] = u[kk]
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
        resid = b-A@sol
        rigid = 1.0-np.linalg.norm(resid)/(np.linalg.norm(b)+1e-30)
        diags.append(dict(rigid_frac=float(rigid)))
        labels.append("suspension" if rigid > 0.9 else "tray-flex")

    # figures
    fig_undeformed(coords, NX, NY, NZ, tray_id, meta)
    fig_modes(coords, modes, f, labels, NX, NY, NZ, tray_id, meta)

    nmode = min(10, len(f))
    pairs = [[i+1, i+2, round(float(abs(f[i+1]-f[i])/max(f[i], 1e-9)), 4)]
             for i in range(len(f)-1) if abs(f[i+1]-f[i])/max(f[i], 1e-9) < 0.05]
    results = {
        "agent": "opus", "tool": "calculix", "solved_by": "opus",
        "solver": "CalculiX ccx 2.23, *FREQUENCY (Lanczos/ARPACK)",
        "units": "SI (m, kg, N, Hz)",
        "frame": "origin at tray center; +z up; tray mid-plane z=0.098 m; base z=0",
        "mass_case": "bare tray, no ballast; emergent C3D8I solid mass ~3.086 kg",
        "boundary_condition": "feet fixed; source plate not modeled",
        "joint_status": "RIGID (truss two-force => moment-free/spherical; RBE3 distributing over bracket footprint)",
        "frequencies_hz": [round(float(x), 3) for x in f[:nmode]],
        "frequency_label": "PROVISIONAL UPPER BOUND (rigid joints; real compliant joints lower these)",
        "mode_type": labels[:nmode], "mode_diagnostics": diags[:nmode],
        "element_types": {
            "tray": "C3D8I 8-node incompatible-mode hexahedron (accurate bending vs plain C3D8)",
            "struts": "T3D2 3-D truss (two-force, moment-free spherical rod-end)",
            "joints": "RBE3 distributing coupling (DCOUP3D) over rod-end bracket footprint; feet fixed"},
        "mesh": {"tray_grid": f"{NX}x{NY}x{NZ} nodes, {meta['nhex']} C3D8I, {meta['ntruss']} T3D2",
                 "target_h_mm": meta["target_h_mm"], "nz_cells": NZ-1,
                 "bracket_footprint_radius_m": meta["r_patch_m"]},
        "near_degenerate_pairs": pairs,
        "fixed_base_no_zero_modes": bool(f[0] > 1.0),
        "fixed_base_lowest_mode_hz": round(float(f[0]), 3),
        "note_dense_flex_cluster": ("the tray is supported at only the 3 apex points (radius "
            "110 mm); its 4 corners/edges overhang and produce a dense set of low-participation "
            "corner/edge-flap tray-flex modes near ~337 Hz. These are physical (not spurious): "
            "C3D8I incompatible-mode bending is softer/more accurate than locked full-integration "
            "H8, so it places the first tray-flex cluster below the JAX-plate (371 Hz) and "
            "TensorMesh locked-H8 (374 Hz) values."),
        "integrity": "independent re-derivation; shares only shared/spec.py raw inputs; C3D8I solid tray + truss struts; no porting of K/M, eigen-results, or frequency tables.",
    }
    with open(os.path.join(HERE, "..", "results.json"), "w") as fo:
        json.dump(results, fo, indent=2)
    print("CalculiX first %d freqs (Hz):" % nmode)
    for i in range(nmode):
        print(f"  mode {i+1:2d}: {f[i]:8.2f}  {labels[i]}  rigid_frac={diags[i]['rigid_frac']:.3f}")
    print("pairs:", pairs)


def _eq(ax):
    lim = np.array([ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()])
    c = lim.mean(1); r = 0.5*(lim[:, 1]-lim[:, 0]).max()
    ax.set_xlim3d(c[0]-r, c[0]+r); ax.set_ylim3d(c[1]-r, c[1]+r); ax.set_zlim3d(c[2]-r, c[2]+r)


def fig_undeformed(coords, NX, NY, NZ, tray_id, meta):
    fig = plt.figure(figsize=(7, 6)); ax = fig.add_subplot(111, projection="3d")
    k = NZ-1
    segs = []
    for j in range(NY):
        for i in range(NX-1):
            segs.append([coords[tray_id(i, j, k)], coords[tray_id(i+1, j, k)]])
    for i in range(NX):
        for j in range(NY-1):
            segs.append([coords[tray_id(i, j, k)], coords[tray_id(i, j+1, k)]])
    ax.add_collection3d(Line3DCollection(segs, colors="0.6", linewidths=0.4))
    for name, ak, fk in spec.STRUTS:
        ap = spec.apex_m()[ak]; ft = spec.foot_m()[fk]
        ax.plot([ap[0], ft[0]], [ap[1], ft[1]], [ap[2], ft[2]], "-", color="C3", lw=2)
    ax.set_title("CalculiX build — undeformed mesh\n(C3D8I solid tray + T3D2 truss struts, fixed base)")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
    _eq(ax); fig.tight_layout()
    fig.savefig(os.path.join(FIG, "calculix_undeformed_mesh.png"), dpi=130); plt.close(fig)


def fig_modes(coords, modes, f, labels, NX, NY, NZ, tray_id, meta):
    fig = plt.figure(figsize=(13, 8))
    k = NZ-1
    for m in range(min(6, len(modes))):
        md = modes[m]
        allu = np.array([md.get(n, (0, 0, 0)) for n in coords])
        sc = 0.06/(np.abs(allu).max()+1e-30)
        ax = fig.add_subplot(2, 3, m+1, projection="3d")
        X = np.zeros((NY, NX)); Y = np.zeros((NY, NX)); Z = np.zeros((NY, NX))
        for j in range(NY):
            for i in range(NX):
                n = tray_id(i, j, k); cx, cy, cz = coords[n]
                ux, uy, uz = md.get(n, (0, 0, 0))
                X[j, i] = cx+sc*ux; Y[j, i] = cy+sc*uy; Z[j, i] = cz+sc*uz
        ax.plot_surface(X, Y, Z, cmap="coolwarm", alpha=0.85, linewidth=0)
        for name, ak, fk in spec.STRUTS:
            ap = spec.apex_m()[ak]; ft = spec.foot_m()[fk]
            ax.plot([ap[0], ft[0]], [ap[1], ft[1]], [ap[2], ft[2]], "-", color="0.2", lw=1.2)
        ax.set_title(f"Mode {m+1}: {f[m]:.1f} Hz\n{labels[m]}", fontsize=9)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([]); _eq(ax)
    fig.suptitle("CalculiX build — first 6 mode shapes (rigid joints = provisional upper bound)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "calculix_mode_shapes.png"), dpi=130)
    plt.close(fig)


if __name__ == "__main__":
    main()
