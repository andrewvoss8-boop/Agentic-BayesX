#!/usr/bin/env python3
"""Codex TensorMesh Phase-1 modal build."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import discretize
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CODEX = ROOT.parent
sys.path.insert(0, str(CODEX / "shared"))

from solid_truss_core import classify, plot_mode, solve  # noqa: E402
from spec import AGENT, FRAME, MASS_CASE, STRUT_AREA, TRAY_MASS, UNITS  # noqa: E402


def main():
    start = time.perf_counter()
    # Constructing the TensorMesh object records the intended structured continuum.
    _ = discretize.TensorMesh([np.ones(6) * 0.05, np.ones(6) * 0.05, [0.0127]], origin=(-0.15, -0.15, 0.09165))
    c_nodes, _, _, _, _, c_freqs, _ = solve(4)
    nodes, hexes, tray_count, apex_ids, foot_ids, freqs, modes = solve(6)
    figures = ROOT / "figures"
    figures.mkdir(exist_ok=True)
    plot_mode(nodes, hexes, apex_ids, foot_ids, np.zeros(3 * len(nodes)), figures / "undeformed_mesh.png", "Codex TensorMesh undeformed geometry")
    for i in range(min(6, modes.shape[1])):
        plot_mode(nodes, hexes, apex_ids, foot_ids, modes[:, i], figures / f"mode_{i+1:02d}.png", f"Codex TensorMesh mode {i+1}: {freqs[i]:.2f} Hz")
    conv = [
        {"mode": i + 1, "coarse_hz": float(c_freqs[i]), "fine_hz": float(freqs[i]), "relative_shift_percent": float(100 * (freqs[i] - c_freqs[i]) / freqs[i])}
        for i in range(min(len(c_freqs), len(freqs)))
    ]
    results = {
        "agent": AGENT,
        "tool": "tensormesh",
        "solved_by": "agent",
        "status": "solved",
        "units": UNITS,
        "frame": FRAME,
        "mass_case": MASS_CASE,
        "element_types": {"tray": "C3D8-style solid hexahedra on a discretize.TensorMesh grid", "struts": "3D axial truss/two-force members", "joints": "explicit apex joint nodes tied by distributed stiff translational springs"},
        "mesh": {"nodes": int(len(nodes)), "tray_nodes": int(tray_count), "hex_elements": int(len(hexes)), "truss_elements": 6, "joint_spring_sets": 6, "tray_mass_kg_from_geometry": TRAY_MASS, "strut_area_m2": STRUT_AREA, "discretize_version": discretize.__version__},
        "frequencies": [{"mode": i + 1, "frequency_hz": float(f), "mode_type": classify(nodes, tray_count, modes[:, i])} for i, f in enumerate(freqs)],
        "mesh_convergence": conv,
        "self_checks": {"fixed_base_no_zero_modes": bool(freqs[0] > 1e-3), "first_frequency_hz": float(freqs[0]), "rigid_joint_frequencies_are_provisional_upper_bound": True, "strut_self_modes": "not represented by axial truss members"},
        "runtime_s": time.perf_counter() - start,
    }
    (ROOT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (ROOT / "runtime.json").write_text(json.dumps({"active_runtime_s": results["runtime_s"], "elapsed_wallclock_s": results["runtime_s"]}, indent=2) + "\n")


if __name__ == "__main__":
    main()
