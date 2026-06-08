#!/usr/bin/env python3
"""Generate the Composer Phase-1 Femap/Nastran deck and geometry figure."""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "model"
FIG = ROOT / "figures"
MODEL.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

E = 68.9e9
NU = 0.33
RHO = 2700.0
TRAY_L = 0.300
TRAY_T = 0.0127
TRAY_Z = 0.098
OD = 0.008
WALL = 0.001
AREA = math.pi / 4 * (OD**2 - (OD - 2 * WALL) ** 2)
APEX = np.array([[0.0, 0.110, 0.098], [0.0, 0.110, 0.098], [-0.095, -0.055, 0.098], [-0.095, -0.055, 0.098], [0.095, -0.055, 0.098], [0.095, -0.055, 0.098]])
FOOT = np.array([[-0.065, 0.267, 0.0], [0.065, 0.267, 0.0], [-0.199, -0.190, 0.0], [-0.264, -0.077, 0.0], [0.264, -0.077, 0.0], [0.199, -0.190, 0.0]])
NAMES = ["b90+", "b90-", "b210+", "b210-", "b330+", "b330-"]


def mesh(n=6):
    xs = np.linspace(-TRAY_L / 2, TRAY_L / 2, n + 1)
    ys = np.linspace(-TRAY_L / 2, TRAY_L / 2, n + 1)
    nodes = []
    ids = {}
    for j, y in enumerate(ys):
        for i, x in enumerate(xs):
            ids[(i, j)] = len(nodes) + 1
            nodes.append((x, y, TRAY_Z))
    quads = []
    for j in range(n):
        for i in range(n):
            quads.append((ids[(i, j)], ids[(i + 1, j)], ids[(i + 1, j + 1)], ids[(i, j + 1)]))
    tray_count = len(nodes)
    apex_ids = []
    foot_ids = []
    for p in APEX:
        apex_ids.append(len(nodes) + 1)
        nodes.append(tuple(p))
    for p in FOOT:
        foot_ids.append(len(nodes) + 1)
        nodes.append(tuple(p))
    return np.asarray(nodes), quads, tray_count, apex_ids, foot_ids


def nearest(nodes, tray_count, point, count=4):
    dist = np.linalg.norm(nodes[:tray_count, :2] - point[:2], axis=1)
    return [int(i + 1) for i in np.argsort(dist)[:count]]


def write_bdf():
    nodes, quads, tray_count, apex_ids, foot_ids = mesh()
    bdf = MODEL / "model.bdf"
    with bdf.open("w") as f:
        f.write("$ Composer Phase-1 hexapod FEM deck. SI units: m, kg, N.\n")
        f.write("SOL 103\nCEND\nTITLE = COMPOSER PHASE 1 HEXAPOD NORMAL MODES\nSUBCASE 1\n  METHOD = 10\n  SPC = 20\n  DISPLACEMENT(PLOT) = ALL\nBEGIN BULK\n")
        f.write("PARAM,POST,-1\nPARAM,GRDPNT,0\n")
        f.write("EIGRL,10,,,10\n")
        f.write(f"MAT1,1,{E:.9E},,{NU:.9E},{RHO:.9E}\n")
        f.write(f"PSHELL,1,1,{TRAY_T:.9E}\n")
        f.write(f"PROD,2,1,{AREA:.9E}\n")
        for i, (x, y, z) in enumerate(nodes, start=1):
            f.write(f"GRID,{i},,{x:.9E},{y:.9E},{z:.9E}\n")
        for eid, q in enumerate(quads, start=1):
            f.write(f"CQUAD4,{eid},1,{q[0]},{q[1]},{q[2]},{q[3]}\n")
        rod_start = len(quads) + 1
        for eid, (a, foot) in enumerate(zip(apex_ids, foot_ids), start=rod_start):
            f.write(f"CROD,{eid},2,{a},{foot}\n")
        rbe_start = rod_start + len(apex_ids)
        for eid, a in enumerate(apex_ids, start=rbe_start):
            deps = nearest(nodes, tray_count, nodes[a - 1], 4)
            f.write(f"RBE2,{eid},{a},123," + ",".join(str(d) for d in deps) + "\n")
        f.write("SPC1,20,123," + ",".join(str(v) for v in foot_ids) + "\n")
        f.write("ENDDATA\n")
    return bdf, nodes, quads, apex_ids, foot_ids, tray_count


def plot(nodes, quads, apex_ids, foot_ids):
    fig = plt.figure(figsize=(7, 5.8))
    ax = fig.add_subplot(111, projection="3d")
    for q in quads:
        pts = [nodes[i - 1] for i in q + (q[0],)]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], [p[2] for p in pts], color="0.65", lw=0.5)
    for a, f, name in zip(apex_ids, foot_ids, NAMES):
        ax.plot(*zip(nodes[a - 1], nodes[f - 1]), color="tab:orange", lw=1.5)
        ax.text(*nodes[a - 1], name, fontsize=7)
    ax.scatter(nodes[np.array(foot_ids) - 1, 0], nodes[np.array(foot_ids) - 1, 1], nodes[np.array(foot_ids) - 1, 2], color="black", s=12)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    ax.set_title("Nastran deck geometry, undeformed")
    ax.set_box_aspect((1, 1, 0.45))
    ax.view_init(elev=24, azim=-52)
    fig.tight_layout()
    fig.savefig(FIG / "undeformed_mesh.png", dpi=180)
    plt.close(fig)


def main():
    start = time.perf_counter()
    bdf, nodes, quads, apex_ids, foot_ids, tray_count = write_bdf()
    plot(nodes, quads, apex_ids, foot_ids)
    elapsed = time.perf_counter() - start
    results = {
        "agent": "composer",
        "tool": "nastran_deck",
        "solved_by": "human",
        "status": "deck_generated_not_solved",
        "units": "SI: m, kg, N, Hz",
        "frame": "Origin at tray center; +z up; tray mid-plane at z=0.098 m; base feet at z=0 fixed.",
        "mass_case": "bare tray, no ballast",
        "element_types": {
            "tray": "Nastran CQUAD4 shell plate with PSHELL thickness 12.7 mm",
            "struts": "CROD axial rods for spherical rod-end two-force behavior",
            "joints": "explicit apex joint GRID tied to nearest tray shell nodes by RBE2 translational components 123",
        },
        "mesh": {"nodes": int(len(nodes)), "tray_nodes": int(tray_count), "cquad4_elements": int(len(quads)), "crod_elements": 6, "rbe2_joint_ties": 6, "tray_mass_kg_from_geometry": TRAY_L * TRAY_L * TRAY_T * RHO, "strut_area_m2": AREA},
        "frequencies": [{"mode": i, "frequency_hz": None, "mode_type": None} for i in range(1, 11)],
        "mesh_convergence": [],
        "self_checks": {
            "fixed_base_no_zero_modes": None,
            "near_degenerate_pair_gaps_percent": [],
            "rigid_joint_frequencies_are_provisional_upper_bound": True,
            "human_check": "Run SOL 103 in Femap/Nastran; then check no zero modes, near-degenerate symmetry pairs, and first ~10 mode-shape labels.",
        },
        "deck_file": str(bdf.relative_to(ROOT)),
        "runtime_s": elapsed,
    }
    (ROOT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (ROOT / "runtime.json").write_text(json.dumps({"active_runtime_s": elapsed, "elapsed_wallclock_s": elapsed}, indent=2) + "\n")


if __name__ == "__main__":
    main()
