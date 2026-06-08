#!/usr/bin/env python3
"""Codex Femap/Nastran SOL 103 deck generator."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
CODEX = ROOT.parent
sys.path.insert(0, str(CODEX / "shared"))

from solid_truss_core import plot_mode, tray_mesh  # noqa: E402
from spec import AGENT, E_AL, FRAME, MASS_CASE, NU_AL, RHO_AL, STRUT_AREA, TRAY_MASS, UNITS  # noqa: E402


def main():
    start = time.perf_counter()
    nodes, hexes, tray_count, apex_ids, foot_ids = tray_mesh(6)
    model = ROOT / "model"
    model.mkdir(exist_ok=True)
    bdf = model / "model.bdf"
    with bdf.open("w") as f:
        f.write("$ Codex Phase-1 hexapod FEM deck. SI units m, kg, N.\nSOL 103\nCEND\n")
        f.write("TITLE = CODEX PHASE 1 HEXAPOD NORMAL MODES\nSUBCASE 1\n  METHOD = 10\n  SPC = 20\n  DISPLACEMENT(PLOT) = ALL\nBEGIN BULK\n")
        f.write("PARAM,POST,-1\nPARAM,GRDPNT,0\nEIGRL,10,,,10\n")
        f.write(f"MAT1,1,{E_AL:.9E},,{NU_AL:.9E},{RHO_AL:.9E}\nPSOLID,1,1\nPROD,2,1,{STRUT_AREA:.9E}\n")
        for i, p in enumerate(nodes, start=1):
            f.write(f"GRID,{i},,{p[0]:.9E},{p[1]:.9E},{p[2]:.9E}\n")
        for eid, e in enumerate(hexes, start=1):
            f.write(f"CHEXA,{eid},1," + ",".join(str(v + 1) for v in e) + "\n")
        eid0 = len(hexes) + 1
        for eid, (a, b) in enumerate(zip(apex_ids, foot_ids), start=eid0):
            f.write(f"CROD,{eid},2,{a + 1},{b + 1}\n")
        top = np.array([i for i in range(tray_count) if nodes[i, 2] > 0.098])
        spring_id = eid0 + 6
        for aid in apex_ids:
            near = int(top[np.argmin(np.linalg.norm(nodes[top, :2] - nodes[aid, :2], axis=1))])
            for dof in (1, 2, 3):
                f.write(f"CELAS2,{spring_id},{1.0e9:.9E},{aid + 1},{dof},{near + 1},{dof}\n")
                spring_id += 1
        f.write("SPC1,20,123," + ",".join(str(f + 1) for f in foot_ids) + "\nENDDATA\n")
    fig = ROOT / "figures"
    fig.mkdir(exist_ok=True)
    plot_mode(nodes, hexes, apex_ids, foot_ids, np.zeros(3 * len(nodes)), fig / "undeformed_mesh.png", "Codex Nastran deck geometry")
    elapsed = time.perf_counter() - start
    results = {
        "agent": AGENT,
        "tool": "nastran_deck",
        "solved_by": "human",
        "status": "deck_generated_not_solved",
        "units": UNITS,
        "frame": FRAME,
        "mass_case": MASS_CASE,
        "element_types": {"tray": "Nastran CHEXA solid tray", "struts": "CROD axial rods", "joints": "explicit apex GRID tied to nearest tray solid node by three stiff CELAS2 translational springs"},
        "mesh": {"nodes": int(len(nodes)), "hex_elements": int(len(hexes)), "crod_elements": 6, "celas2_joint_springs": 18, "tray_mass_kg_from_geometry": TRAY_MASS, "strut_area_m2": STRUT_AREA},
        "frequencies": [{"mode": i, "frequency_hz": None, "mode_type": None} for i in range(1, 11)],
        "mesh_convergence": [],
        "self_checks": {"fixed_base_no_zero_modes": None, "rigid_joint_frequencies_are_provisional_upper_bound": True, "human_check": "Run SOL 103 in Femap/Nastran and update frequencies/mode types from shapes."},
        "deck_file": "model/model.bdf",
        "runtime_s": elapsed,
    }
    (ROOT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (ROOT / "runtime.json").write_text(json.dumps({"active_runtime_s": elapsed, "elapsed_wallclock_s": elapsed}, indent=2) + "\n")


if __name__ == "__main__":
    main()
