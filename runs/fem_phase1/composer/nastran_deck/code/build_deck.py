#!/usr/bin/env python3
"""Generate Nastran SOL 103 bulk deck for human Femap solve."""
from __future__ import annotations

import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
MODEL = ROOT / "model"
FIG = ROOT / "figures"

E, NU, RHO = 68.9e9, 0.33, 2700.0
A_STRUT = 22e-6
TRAY_Z_TOP = 0.098
TRAY_Z_BOT = TRAY_Z_TOP - 0.0127
APEX = {"A0": (0, 0.110, TRAY_Z_TOP), "A1": (-0.095, -0.055, TRAY_Z_TOP), "A2": (0.095, -0.055, TRAY_Z_TOP)}
FEET = {
    "F0": (-0.065, 0.267, 0), "F1": (0.065, 0.267, 0),
    "F2": (-0.199, -0.190, 0), "F3": (-0.264, -0.077, 0),
    "F4": (0.264, -0.077, 0), "F5": (0.199, -0.190, 0),
}
STRUTS = [("A0", "F0"), ("A0", "F1"), ("A1", "F2"), ("A1", "F3"), ("A2", "F4"), ("A2", "F5")]


def build_mesh(n):
    xs = np.unique(np.concatenate([np.linspace(-0.15, 0.15, n + 1), [p[0] for p in APEX.values()]]))
    ys = np.unique(np.concatenate([np.linspace(-0.15, 0.15, n + 1), [p[1] for p in APEX.values()]]))
    zs = [TRAY_Z_BOT, TRAY_Z_TOP]
    nodes, grid, nid = {}, {}, 1
    for k, z in enumerate(zs):
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                grid[(i, j, k)] = nid
                nodes[nid] = (x, y, z)
                nid += 1
    hexes, eid = [], 1
    for k in range(len(zs) - 1):
        for j in range(len(ys) - 1):
            for i in range(len(xs) - 1):
                hexes.append((eid, [
                    grid[(i, j, k)], grid[(i + 1, j, k)], grid[(i + 1, j + 1, k)], grid[(i, j + 1, k)],
                    grid[(i, j, k + 1)], grid[(i + 1, j, k + 1)], grid[(i + 1, j + 1, k + 1)], grid[(i, j + 1, k + 1)],
                ]))
                eid += 1
    foot_start = nid
    for key in ["F0", "F1", "F2", "F3", "F4", "F5"]:
        nodes[nid] = FEET[key]
        nid += 1
    return nodes, hexes, foot_start, eid


def write_bdf(nodes, hexes, foot_start, next_eid):
    lines = [
        "SOL 103", "CEND", "  ECHO = NONE", "  SUBCASE 1", "    LABEL = NORMAL MODES",
        "    METHOD = 10", "    SPC = 1", "    DISPLACEMENT(PLOT) = ALL",
        "BEGIN BULK", "EIGRL,10,,,,10,,,,MASS", f"MAT1,1,{E:.4E},,{NU:.4f},{RHO:.4E}",
    ]
    for nid, (x, y, z) in sorted(nodes.items()):
        lines.append(f"GRID,{nid},,{x:.6f},{y:.6f},{z:.6f}")
    for eid, conn in hexes:
        lines.append("CHEXA," + ",".join([str(eid), "1"] + [str(c) for c in conn]))
    top = [nid for nid, (_, _, z) in nodes.items() if abs(z - TRAY_Z_TOP) < 1e-9 and nid < foot_start]
    apex = {k: min(top, key=lambda nid: np.linalg.norm(np.array(nodes[nid]) - np.array(pt))) for k, pt in APEX.items()}
    foot = {k: foot_start + i for i, k in enumerate(["F0", "F1", "F2", "F3", "F4", "F5"])}
    pid = 2
    lines.append(f"PROD,{pid},1,{A_STRUT}")
    eid = next_eid
    for akey, fkey in STRUTS:
        lines.append(f"CROD,{eid},{pid},{apex[akey]},{foot[fkey]}")
        eid += 1
    for key in foot:
        lines.append(f"SPC1,1,{foot[key]},123")
    lines.append("ENDDATA")
    return "\n".join(lines) + "\n"


def main():
    t0 = time.time()
    MODEL.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    nodes, hexes, foot_start, next_eid = build_mesh(8)
    (MODEL / "model.bdf").write_text(write_bdf(nodes, hexes, foot_start, next_eid))
    (ROOT / "RUN_IN_FEMAP.md").write_text("""# Run in Femap / Nastran

1. Open `model/model.bdf` in Femap (or MSC/NX Nastran).
2. Verify SOL 103, EIGRL requests 10 modes, SPC1 fixes translations at foot nodes.
3. Run normal modes; plot first ~6 mode shapes.
4. Record solved frequencies in `results.json` (`solved_by: human`).

Units: SI (m, kg, N). Frame: tray center origin, +z up, tray top z = 0.098 m.
""")
    arr = np.array(list(nodes.values()))
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(arr[:, 0], arr[:, 1], arr[:, 2], s=4)
    fig.savefig(FIG / "undeformed_geometry.png", dpi=150); plt.close(fig)
    out = {
        "agent": "composer", "tool": "nastran_deck",
        "units": "SI (m, kg, N, Hz)",
        "coordinate_frame": "origin at tray center; +z up",
        "mass_case": "bare tray CHEXA solid",
        "provisional_upper_bound_note": "rigid joints; CROD struts",
        "solved_by": "human",
        "element_types": {"tray": "CHEXA", "struts": "CROD"},
        "mesh": {"n_div": 8, "nelem_hex": len(hexes), "nnode": len(nodes)},
        "modes": [{"index": i + 1, "frequency_hz": None, "mode_type": None} for i in range(10)],
        "runtime_s": time.time() - t0,
    }
    (ROOT / "results.json").write_text(json.dumps(out, indent=2))
    print("wrote model.bdf")


if __name__ == "__main__":
    main()
