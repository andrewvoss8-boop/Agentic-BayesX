#!/usr/bin/env python3
"""Codex CalculiX deck generation and solve if ccx is available."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CODEX = ROOT.parent
sys.path.insert(0, str(CODEX / "shared"))

from solid_truss_core import plot_mode, tray_mesh  # noqa: E402
from spec import AGENT, APEX, E_AL, FOOT, FRAME, MASS_CASE, NU_AL, RHO_AL, STRUT_AREA, TRAY_MASS, UNITS  # noqa: E402


def write_inp():
    model = ROOT / "model"
    model.mkdir(exist_ok=True)
    nodes, hexes, tray_count, apex_ids, foot_ids = tray_mesh(6)
    top = np.array([i for i in range(tray_count) if nodes[i, 2] > 0.098])
    inp = model / "hexapod_codex.inp"
    with inp.open("w") as f:
        f.write("*HEADING\nCodex Phase-1 hexapod, fixed feet, bare tray\n*NODE\n")
        for i, p in enumerate(nodes, start=1):
            f.write(f"{i}, {p[0]:.9e}, {p[1]:.9e}, {p[2]:.9e}\n")
        f.write("*ELEMENT, TYPE=C3D8, ELSET=TRAY\n")
        for eid, e in enumerate(hexes, start=1):
            f.write(f"{eid}, " + ", ".join(str(v + 1) for v in e) + "\n")
        first = len(hexes) + 1
        f.write("*ELEMENT, TYPE=T3D2, ELSET=STRUTS\n")
        for eid, (a, b) in enumerate(zip(apex_ids, foot_ids), start=first):
            f.write(f"{eid}, {a + 1}, {b + 1}\n")
        f.write("*MATERIAL, NAME=AL6061T6\n*ELASTIC\n")
        f.write(f"{E_AL:.9e}, {NU_AL:.9e}\n*DENSITY\n{RHO_AL:.9e}\n")
        f.write("*SOLID SECTION, ELSET=TRAY, MATERIAL=AL6061T6\n")
        f.write("*SOLID SECTION, ELSET=STRUTS, MATERIAL=AL6061T6\n")
        f.write(f"{STRUT_AREA:.9e}\n")
        for aid in apex_ids:
            near = top[np.argsort(np.linalg.norm(nodes[top, :2] - nodes[aid, :2], axis=1))[:4]]
            for dof in (1, 2, 3):
                f.write("*EQUATION\n")
                f.write("5\n")
                f.write(f"{aid + 1}, {dof}, 1.0")
                for tid in near:
                    f.write(f", {tid + 1}, {dof}, {-1/len(near):.9e}")
                f.write("\n")
        f.write("*BOUNDARY\n")
        for fid in foot_ids:
            f.write(f"{fid + 1}, 1, 3, 0.0\n")
        f.write("*STEP\n*FREQUENCY, EIGENSOLVER=LANCZOS\n10\n*NODE FILE\nU\n*END STEP\n")
    return inp, nodes, hexes, apex_ids, foot_ids


def parse_dat(dat: Path):
    freqs = []
    if not dat.exists():
        return freqs
    for line in dat.read_text(errors="ignore").splitlines():
        if re.search(r"^\s*\d+\s+", line):
            nums = re.findall(r"[-+]?\d+(?:\.\d*)?(?:[Ee][-+]?\d+)?", line)
            if len(nums) >= 5:
                # CalculiX frequency rows are:
                # mode, eigenvalue, rad/time, cycles/time, imaginary rad/time.
                val = float(nums[3])
                if val > 0:
                    freqs.append({"mode": len(freqs) + 1, "frequency_hz": val, "mode_type": None})
            if len(freqs) == 10:
                break
    return freqs


def main():
    start = time.perf_counter()
    inp, nodes, hexes, apex_ids, foot_ids = write_inp()
    fig = ROOT / "figures"
    fig.mkdir(exist_ok=True)
    plot_mode(nodes, hexes, apex_ids, foot_ids, np.zeros(3 * len(nodes)), fig / "undeformed_mesh.png", "Codex CalculiX undeformed input")
    ccx = shutil.which("ccx") or str(Path.home() / "miniforge3_bayesx_femphase1/envs/ccx/bin/ccx")
    stdout = ""
    status = "blocked_no_ccx"
    freqs = []
    if ccx and Path(ccx).exists():
        run = subprocess.run([ccx, inp.with_suffix("").name], cwd=inp.parent, text=True, capture_output=True, check=False)
        stdout = run.stdout + run.stderr
        (ROOT / "ccx_stdout_stderr.txt").write_text(stdout)
        status = "solver_returned" if run.returncode == 0 else "solver_failed"
        freqs = parse_dat(inp.with_suffix(".dat"))
        if freqs:
            status = "solved"
    elapsed = time.perf_counter() - start
    results = {
        "agent": AGENT,
        "tool": "calculix",
        "solved_by": "agent" if freqs else None,
        "status": status,
        "units": UNITS,
        "frame": FRAME,
        "mass_case": MASS_CASE,
        "element_types": {"tray": "CalculiX C3D8 solid hexahedra", "struts": "CalculiX T3D2 axial trusses", "joints": "explicit apex joint nodes constrained to distributed tray nodes by *EQUATION"},
        "mesh": {"nodes": int(len(nodes)), "hex_elements": int(len(hexes)), "truss_elements": 6, "tray_mass_kg_from_geometry": TRAY_MASS, "strut_area_m2": STRUT_AREA},
        "frequencies": freqs,
        "mesh_convergence": [],
        "self_checks": {"fixed_base_no_zero_modes": None if not freqs else freqs[0]["frequency_hz"] > 1e-3, "rigid_joint_frequencies_are_provisional_upper_bound": True, "strut_self_modes": "not represented by truss members"},
        "input_file": str(inp.relative_to(ROOT)),
        "blocked_reason": None if Path(ccx).exists() else "ccx not available",
        "solver_stdout_excerpt": stdout[:2000],
        "runtime_s": elapsed,
    }
    (ROOT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (ROOT / "runtime.json").write_text(json.dumps({"active_runtime_s": elapsed, "elapsed_wallclock_s": elapsed}, indent=2) + "\n")


if __name__ == "__main__":
    main()
