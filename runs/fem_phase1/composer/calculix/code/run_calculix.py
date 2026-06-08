#!/usr/bin/env python3
"""Generate and, if available, run the Composer Phase-1 CalculiX model."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
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
AREA = math.pi / 4.0 * (OD**2 - (OD - 2.0 * WALL) ** 2)
APEX = np.array([[0.0, 0.110, 0.098], [0.0, 0.110, 0.098], [-0.095, -0.055, 0.098], [-0.095, -0.055, 0.098], [0.095, -0.055, 0.098], [0.095, -0.055, 0.098]])
FOOT = np.array([[-0.065, 0.267, 0.0], [0.065, 0.267, 0.0], [-0.199, -0.190, 0.0], [-0.264, -0.077, 0.0], [0.264, -0.077, 0.0], [0.199, -0.190, 0.0]])
NAMES = ["b90+", "b90-", "b210+", "b210-", "b330+", "b330-"]


def mesh(n=6):
    xs = np.linspace(-TRAY_L / 2, TRAY_L / 2, n + 1)
    ys = np.linspace(-TRAY_L / 2, TRAY_L / 2, n + 1)
    zs = [TRAY_Z - TRAY_T / 2, TRAY_Z + TRAY_T / 2]
    nodes = []
    nid = {}
    for k, z in enumerate(zs):
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                nid[(i, j, k)] = len(nodes) + 1
                nodes.append((x, y, z))
    elems = []
    for j in range(n):
        for i in range(n):
            elems.append((nid[(i, j, 0)], nid[(i + 1, j, 0)], nid[(i + 1, j + 1, 0)], nid[(i, j + 1, 0)], nid[(i, j, 1)], nid[(i + 1, j, 1)], nid[(i + 1, j + 1, 1)], nid[(i, j + 1, 1)]))
    tray_count = len(nodes)
    apex_ids = []
    foot_ids = []
    for p in APEX:
        apex_ids.append(len(nodes) + 1)
        nodes.append(tuple(p))
    for p in FOOT:
        foot_ids.append(len(nodes) + 1)
        nodes.append(tuple(p))
    top_ids = [nid[(i, j, 1)] for j in range(n + 1) for i in range(n + 1)]
    return np.array(nodes), elems, tray_count, apex_ids, foot_ids, top_ids


def nearest_top(nodes, top_ids, point):
    coords = nodes[np.array(top_ids) - 1]
    return int(top_ids[int(np.argmin(np.linalg.norm(coords[:, :2] - point[:2], axis=1)))])


def write_inp():
    nodes, elems, tray_count, apex_ids, foot_ids, top_ids = mesh()
    path = MODEL / "composer_hexapod_phase1.inp"
    with path.open("w") as f:
        f.write("*HEADING\n")
        f.write("Composer Phase-1 hexapod, fixed base, bare tray, rigid joint ties\n")
        f.write("** Units: SI (m, kg, N). Origin tray center; +z up; tray mid-plane z=0.098 m.\n")
        f.write("*NODE\n")
        for i, (x, y, z) in enumerate(nodes, start=1):
            f.write(f"{i}, {x:.9e}, {y:.9e}, {z:.9e}\n")
        f.write("*ELEMENT, TYPE=C3D8, ELSET=TRAY_SOLID\n")
        for eid, elem in enumerate(elems, start=1):
            f.write(f"{eid}, " + ", ".join(str(v) for v in elem) + "\n")
        f.write("*ELEMENT, TYPE=T3D2, ELSET=STRUT_TRUSS\n")
        first = len(elems) + 1
        for i, (a, b) in enumerate(zip(apex_ids, foot_ids), start=first):
            f.write(f"{i}, {a}, {b}\n")
        f.write("*NSET, NSET=FIXED_FEET\n")
        f.write(", ".join(str(v) for v in foot_ids) + "\n")
        f.write("*MATERIAL, NAME=AL6061T6\n")
        f.write("*ELASTIC\n")
        f.write(f"{E:.9e}, {NU:.9e}\n")
        f.write("*DENSITY\n")
        f.write(f"{RHO:.9e}\n")
        f.write("*SOLID SECTION, ELSET=TRAY_SOLID, MATERIAL=AL6061T6\n")
        f.write("*SOLID SECTION, ELSET=STRUT_TRUSS, MATERIAL=AL6061T6\n")
        f.write(f"{AREA:.9e}\n")
        f.write("** Explicit joint-node rigid ties to nearest tray top-surface node.\n")
        for a in apex_ids:
            tied = nearest_top(nodes, top_ids, nodes[a - 1])
            for dof in (1, 2, 3):
                f.write("*EQUATION\n")
                f.write("2\n")
                f.write(f"{a}, {dof}, 1.0, {tied}, {dof}, -1.0\n")
        f.write("*BOUNDARY\n")
        for node in foot_ids:
            f.write(f"{node}, 1, 3, 0.0\n")
        f.write("*STEP\n")
        f.write("*FREQUENCY, EIGENSOLVER=LANCZOS\n")
        f.write("10\n")
        f.write("*NODE FILE\n")
        f.write("U\n")
        f.write("*END STEP\n")
    return path, nodes, elems, apex_ids, foot_ids


def plot_geometry(nodes, elems, apex_ids, foot_ids):
    fig = plt.figure(figsize=(7, 5.8))
    ax = fig.add_subplot(111, projection="3d")
    edges = set()
    for e in elems:
        for a, b in [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]:
            edges.add(tuple(sorted((e[a] - 1, e[b] - 1))))
    for a, b in edges:
        ax.plot(*zip(nodes[a], nodes[b]), color="0.60", lw=0.45)
    for a, f, name in zip(apex_ids, foot_ids, NAMES):
        ax.plot(*zip(nodes[a - 1], nodes[f - 1]), color="tab:green", lw=1.5)
        ax.text(*nodes[a - 1], name, fontsize=7)
    ax.scatter(nodes[np.array(foot_ids) - 1, 0], nodes[np.array(foot_ids) - 1, 1], nodes[np.array(foot_ids) - 1, 2], color="black", s=12)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    ax.set_title("CalculiX input geometry, undeformed")
    ax.set_box_aspect((1, 1, 0.45))
    ax.view_init(elev=24, azim=-52)
    fig.tight_layout()
    fig.savefig(FIG / "undeformed_mesh.png", dpi=180)
    plt.close(fig)


def main():
    start = time.perf_counter()
    inp, nodes, elems, apex_ids, foot_ids = write_inp()
    plot_geometry(nodes, elems, apex_ids, foot_ids)
    ccx = shutil.which("ccx") or shutil.which("ccx_2.21")
    status = "blocked_no_ccx"
    stdout = ""
    frequencies = []
    if ccx:
        run = subprocess.run([ccx, inp.with_suffix("").name], cwd=MODEL, text=True, capture_output=True, check=False)
        stdout = run.stdout + run.stderr
        status = "solver_returned" if run.returncode == 0 else "solver_failed"
        (ROOT / "ccx_stdout_stderr.txt").write_text(stdout)
        dat = inp.with_suffix(".dat")
        if dat.exists():
            for line in dat.read_text(errors="ignore").splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[0].isdigit():
                    try:
                        val = float(parts[-1])
                    except ValueError:
                        continue
                    if val > 0:
                        frequencies.append({"mode": len(frequencies) + 1, "frequency_hz": val, "mode_type": None})
                    if len(frequencies) == 10:
                        break
    elapsed = time.perf_counter() - start
    result = {
        "agent": "composer",
        "tool": "calculix",
        "solved_by": "agent" if frequencies else None,
        "status": "solved" if frequencies else status,
        "blocked_reason": None if frequencies else "CalculiX executable ccx/ccx_2.21 was not found on PATH in this environment.",
        "units": "SI: m, kg, N, Hz",
        "frame": "Origin at tray center; +z up; tray mid-plane at z=0.098 m; base feet at z=0 fixed.",
        "mass_case": "bare tray, no ballast",
        "element_types": {
            "tray": "CalculiX C3D8 solid hexahedra",
            "struts": "CalculiX T3D2 axial trusses for spherical rod ends",
            "joints": "explicit apex joint nodes constrained to nearest tray top node with *EQUATION rigid translation ties",
        },
        "mesh": {"nodes": int(len(nodes)), "hex_elements": int(len(elems)), "truss_elements": 6, "tray_mass_kg_from_geometry": TRAY_L * TRAY_L * TRAY_T * RHO, "strut_area_m2": AREA},
        "frequencies": frequencies,
        "mesh_convergence": [],
        "self_checks": {
            "fixed_base_no_zero_modes": None if not frequencies else frequencies[0]["frequency_hz"] > 1e-3,
            "rigid_joint_frequencies_are_provisional_upper_bound": True,
            "near_degenerate_pair_gaps_percent": [],
            "strut_self_modes": "T3D2 truss build does not represent bending self-modes.",
        },
        "input_file": str(inp.relative_to(ROOT)),
        "solver_stdout_excerpt": stdout[:2000],
        "runtime_s": elapsed,
    }
    (ROOT / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    (ROOT / "runtime.json").write_text(json.dumps({"active_runtime_s": elapsed, "elapsed_wallclock_s": elapsed}, indent=2) + "\n")


if __name__ == "__main__":
    main()
