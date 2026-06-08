#!/usr/bin/env python3
"""Generate CalculiX deck, run ccx if available, parse frequencies."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIG = ROOT / "figures"
MODEL = ROOT / "model"

E = 68.9e9
NU = 0.33
RHO = 2700.0
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


def tray_mesh(n: int):
    xs = np.unique(np.concatenate([np.linspace(-0.15, 0.15, n + 1), [p[0] for p in APEX.values()]]))
    ys = np.unique(np.concatenate([np.linspace(-0.15, 0.15, n + 1), [p[1] for p in APEX.values()]]))
    zs = [TRAY_Z_BOT, TRAY_Z_TOP]
    nodes = {}
    nid = 1
    grid = {}
    for k, z in enumerate(zs):
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                grid[(i, j, k)] = nid
                nodes[nid] = (float(x), float(y), float(z))
                nid += 1
    elems = []
    eid = 1
    for k in range(len(zs) - 1):
        for j in range(len(ys) - 1):
            for i in range(len(xs) - 1):
                n = [
                    grid[(i, j, k)], grid[(i + 1, j, k)], grid[(i + 1, j + 1, k)], grid[(i, j + 1, k)],
                    grid[(i, j, k + 1)], grid[(i + 1, j, k + 1)], grid[(i + 1, j + 1, k + 1)], grid[(i, j + 1, k + 1)],
                ]
                elems.append((eid, n))
                eid += 1
    return nodes, elems, nid


def write_inp(nodes: dict, elems: list, foot_start: int, n_mesh: int):
    lines = ["*HEADING", "Phase-1 hexapod normal modes (CalculiX)", "*NODE"]
    for nid, (x, y, z) in sorted(nodes.items()):
        lines.append(f"{nid},{x:.6f},{y:.6f},{z:.6f}")
    lines += ["*ELEMENT, TYPE=C3D8, ELSET=TRAY"]
    for eid, conn in elems:
        lines.append(f"{eid}," + ",".join(str(c) for c in conn))
    lines += [
        "*MATERIAL, NAME=AL6061",
        f"*ELASTIC", f"{E},{NU}",
        f"*DENSITY", f"{RHO}",
        "*SOLID SECTION, ELSET=TRAY, MATERIAL=AL6061",
    ]
    # apex map on top surface
    top_ids = [nid for nid, (_, _, z) in nodes.items() if abs(z - TRAY_Z_TOP) < 1e-9 and nid < foot_start]
    apex_ids = {}
    for key, pt in APEX.items():
        d = {nid: np.linalg.norm(np.array(nodes[nid]) - np.array(pt)) for nid in top_ids}
        apex_ids[key] = min(d, key=lambda k: d[k])
    foot_map = {}
    for i, key in enumerate(["F0", "F1", "F2", "F3", "F4", "F5"]):
        foot_map[key] = foot_start + i
    lines.append("*ELEMENT, TYPE=T3D2, ELSET=STRUTS")
    eid = len(elems) + 1
    strut_elems = []
    for akey, fkey in STRUTS:
        n1, n2 = apex_ids[akey], foot_map[fkey]
        lines.append(f"{eid},{n1},{n2}")
        strut_elems.append(eid)
        eid += 1
    lines += [
        "*SOLID SECTION, ELSET=STRUTS, MATERIAL=AL6061",
        f"{A_STRUT:.12e}",
        "*BOUNDARY",
    ]
    for key in ["F0", "F1", "F2", "F3", "F4", "F5"]:
        fn = foot_map[key]
        lines.append(f"{fn},1,3")
    lines += [
        "*STEP",
        "*FREQUENCY", "10",
        "*NODE PRINT",
        "NT",
        "*NODE FILE",
        "U",
        "*END STEP",
    ]
    return "\n".join(lines) + "\n", apex_ids, foot_map, {"n_div": n_mesh, "nelem_c3d8": len(elems), "nelem_strut": len(strut_elems)}


def parse_dat(dat_path: Path):
    text = dat_path.read_text(errors="ignore")
    freqs = []
    in_block = False
    for line in text.splitlines():
        if "E I G E N V A L U E" in line:
            in_block = True
            continue
        if in_block and "P A R T I C I P A T I O N" in line:
            break
        if not in_block:
            continue
        parts = line.split()
        if len(parts) >= 4 and parts[0].isdigit():
            try:
                f_hz = float(parts[3].replace("D", "E"))
                if 1.0 < f_hz < 1e6:
                    freqs.append(f_hz)
            except ValueError:
                pass
    if not freqs:
        for m in re.finditer(r"frequency\s*[=:]\s*(\d+\.?\d*(?:[Ee][+-]?\d+)?)", text, re.I):
            freqs.append(float(m.group(1)))
    return freqs[:10]


def main():
    t0 = time.time()
    MODEL.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    nodes, elems, next_id = tray_mesh(8)
    foot_start = next_id
    for key in ["F0", "F1", "F2", "F3", "F4", "F5"]:
        nodes[next_id] = FEET[key]
        next_id += 1
    inp_text, apex_ids, foot_map, mesh = write_inp(nodes, elems, foot_start, 8)
    inp_path = MODEL / "hexapod.inp"
    inp_path.write_text(inp_text)
    conda_ccx = Path(__file__).resolve().parents[5] / ".conda_calculix" / "bin" / "ccx"
    ccx = shutil.which("ccx") or shutil.which("ccx_2.23") or (str(conda_ccx) if conda_ccx.exists() else None)
    freqs = []
    solved_by = "agent"
    note = ""
    if ccx:
        subprocess.run([ccx, "-i", str(inp_path.with_suffix(""))], cwd=MODEL, check=False)
        dat = MODEL / "hexapod.dat"
        if dat.exists():
            freqs = parse_dat(dat)
        else:
            note = "ccx ran but hexapod.dat not found"
    else:
        solved_by = "not_run"
        note = "ccx not found on PATH; deck generated only"
    # geometry figure from nodes
    arr = np.array(list(nodes.values()))
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(arr[:, 0], arr[:, 1], arr[:, 2], s=4)
    for akey, fkey in STRUTS:
        p = np.array(APEX[akey])
        q = np.array(FEET[fkey])
        ax.plot([p[0], q[0]], [p[1], q[1]], [p[2], q[2]], "r-", lw=1)
    ax.set_title("CalculiX undeformed model")
    fig.savefig(FIG / "undeformed_geometry.png", dpi=150)
    plt.close(fig)
    out = {
        "agent": "composer",
        "tool": "calculix",
        "units": "SI (m, kg, N, Hz)",
        "coordinate_frame": "origin at tray center; +z up",
        "mass_case": "bare tray solid C3D8",
        "provisional_upper_bound_note": "rigid joints; T3D2 struts",
        "solved_by": solved_by,
        "run_note": note,
        "element_types": {"tray": "C3D8", "struts": "T3D2 beam/truss"},
        "mesh": mesh,
        "modes": [
            {
                "index": i + 1,
                "frequency_hz": float(freqs[i]) if i < len(freqs) else None,
                "mode_type": "unsolved" if i >= len(freqs) else "pending_shape_review",
            }
            for i in range(10)
        ],
        "runtime_s": time.time() - t0,
    }
    if freqs:
        pairs = []
        for i in range(len(freqs) - 1):
            if abs(freqs[i + 1] - freqs[i]) / max(freqs[i], 1e-9) < 0.02:
                pairs.append((freqs[i], freqs[i + 1]))
        out["symmetry_degenerate_pairs_hz"] = pairs
        for i, f in enumerate(freqs[:10]):
            out["modes"][i]["frequency_hz"] = float(f)
            out["modes"][i]["mode_type"] = "pending_shape_review"
    (ROOT / "results.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"ccx": ccx, "freqs": freqs[:10], "note": note}, indent=2))


if __name__ == "__main__":
    main()
