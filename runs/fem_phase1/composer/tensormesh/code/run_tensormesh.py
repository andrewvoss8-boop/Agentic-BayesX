#!/usr/bin/env python3
"""Composer Phase-1 TensorMesh build.

Modeling choice: C3D8-style solid tray on a structured TensorMesh plus axial truss
struts. Rod ends are spherical, so the struts are two-force members in this build.
Rigid joints are explicit joint nodes tied to the tray through stiff translational
springs; this keeps the later joint-compliance parameter location visible.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg
import scipy.sparse as sp
import scipy.sparse.linalg as spla

try:
    import discretize
except Exception:  # pragma: no cover - recorded in results
    discretize = None


ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

E = 68.9e9
NU = 0.33
RHO = 2700.0
TRAY_L = 0.300
TRAY_T = 0.0127
TRAY_Z = 0.098
STRUT_OD = 0.008
STRUT_WALL = 0.001
STRUT_AREA = math.pi / 4.0 * (STRUT_OD**2 - (STRUT_OD - 2.0 * STRUT_WALL) ** 2)
JOINT_K = 1.0e9

APEX = np.array(
    [
        [0.000, 0.110, 0.098],
        [0.000, 0.110, 0.098],
        [-0.095, -0.055, 0.098],
        [-0.095, -0.055, 0.098],
        [0.095, -0.055, 0.098],
        [0.095, -0.055, 0.098],
    ],
    dtype=float,
)
FOOT = np.array(
    [
        [-0.065, 0.267, 0.0],
        [0.065, 0.267, 0.0],
        [-0.199, -0.190, 0.0],
        [-0.264, -0.077, 0.0],
        [0.264, -0.077, 0.0],
        [0.199, -0.190, 0.0],
    ],
    dtype=float,
)
STRUT_NAMES = ["b90+", "b90-", "b210+", "b210-", "b330+", "b330-"]


def elasticity_matrix() -> np.ndarray:
    lam = E * NU / ((1.0 + NU) * (1.0 - 2.0 * NU))
    mu = E / (2.0 * (1.0 + NU))
    d = np.zeros((6, 6), dtype=float)
    d[:3, :3] = lam
    np.fill_diagonal(d[:3, :3], lam + 2.0 * mu)
    np.fill_diagonal(d[3:, 3:], mu)
    return d


def shape_derivatives(xi: float, eta: float, zeta: float) -> tuple[np.ndarray, np.ndarray]:
    signs = np.array(
        [
            [-1, -1, -1],
            [1, -1, -1],
            [1, 1, -1],
            [-1, 1, -1],
            [-1, -1, 1],
            [1, -1, 1],
            [1, 1, 1],
            [-1, 1, 1],
        ],
        dtype=float,
    )
    n = 0.125 * np.prod(1.0 + signs * np.array([xi, eta, zeta]), axis=1)
    d_nat = np.column_stack(
        [
            0.125 * signs[:, 0] * (1.0 + signs[:, 1] * eta) * (1.0 + signs[:, 2] * zeta),
            0.125 * signs[:, 1] * (1.0 + signs[:, 0] * xi) * (1.0 + signs[:, 2] * zeta),
            0.125 * signs[:, 2] * (1.0 + signs[:, 0] * xi) * (1.0 + signs[:, 1] * eta),
        ]
    )
    return n, d_nat


def c3d8_matrices(xe: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d = elasticity_matrix()
    ke = np.zeros((24, 24), dtype=float)
    me = np.zeros((24, 24), dtype=float)
    gp = 1.0 / math.sqrt(3.0)
    for xi in (-gp, gp):
        for eta in (-gp, gp):
            for zeta in (-gp, gp):
                n, d_nat = shape_derivatives(xi, eta, zeta)
                jac = d_nat.T @ xe
                detj = float(np.linalg.det(jac))
                if detj <= 0:
                    raise ValueError(f"Non-positive Jacobian {detj}")
                d_xyz = d_nat @ np.linalg.inv(jac)
                b = np.zeros((6, 24), dtype=float)
                for a in range(8):
                    j = 3 * a
                    dx, dy, dz = d_xyz[a]
                    b[0, j] = dx
                    b[1, j + 1] = dy
                    b[2, j + 2] = dz
                    b[3, j] = dy
                    b[3, j + 1] = dx
                    b[4, j + 1] = dz
                    b[4, j + 2] = dy
                    b[5, j] = dz
                    b[5, j + 2] = dx
                ke += b.T @ d @ b * detj
                for a in range(8):
                    for bnode in range(8):
                        block = RHO * n[a] * n[bnode] * detj * np.eye(3)
                        me[3 * a : 3 * a + 3, 3 * bnode : 3 * bnode + 3] += block
    return ke, me


def build_mesh(nxy: int):
    xs = np.linspace(-TRAY_L / 2.0, TRAY_L / 2.0, nxy + 1)
    ys = np.linspace(-TRAY_L / 2.0, TRAY_L / 2.0, nxy + 1)
    zs = np.array([TRAY_Z - TRAY_T / 2.0, TRAY_Z + TRAY_T / 2.0])
    if discretize is not None:
        _ = discretize.TensorMesh([np.diff(xs), np.diff(ys), np.diff(zs)], origin=(xs[0], ys[0], zs[0]))
    nodes = []
    node_id = {}
    for k, z in enumerate(zs):
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                node_id[(i, j, k)] = len(nodes)
                nodes.append((x, y, z))
    hexes = []
    for j in range(nxy):
        for i in range(nxy):
            hexes.append(
                [
                    node_id[(i, j, 0)],
                    node_id[(i + 1, j, 0)],
                    node_id[(i + 1, j + 1, 0)],
                    node_id[(i, j + 1, 0)],
                    node_id[(i, j, 1)],
                    node_id[(i + 1, j, 1)],
                    node_id[(i + 1, j + 1, 1)],
                    node_id[(i, j + 1, 1)],
                ]
            )
    tray_node_count = len(nodes)
    apex_ids = []
    foot_ids = []
    for p in APEX:
        apex_ids.append(len(nodes))
        nodes.append(tuple(p))
    for p in FOOT:
        foot_ids.append(len(nodes))
        nodes.append(tuple(p))
    return np.array(nodes, dtype=float), hexes, tray_node_count, apex_ids, foot_ids, xs, ys


def add_block(rows, cols, vals, dofs_a, dofs_b, block):
    for ia, da in enumerate(dofs_a):
        for ib, db in enumerate(dofs_b):
            rows.append(da)
            cols.append(db)
            vals.append(float(block[ia, ib]))


def assemble(nxy: int):
    nodes, hexes, tray_node_count, apex_ids, foot_ids, xs, ys = build_mesh(nxy)
    ndof = 3 * len(nodes)
    kr: list[int] = []
    kc: list[int] = []
    kv: list[float] = []
    mr: list[int] = []
    mc: list[int] = []
    mv: list[float] = []
    for elem in hexes:
        xe = nodes[np.array(elem)]
        ke, me = c3d8_matrices(xe)
        edofs = [3 * n + c for n in elem for c in range(3)]
        add_block(kr, kc, kv, edofs, edofs, ke)
        add_block(mr, mc, mv, edofs, edofs, me)
    for sid, (a_id, f_id) in enumerate(zip(apex_ids, foot_ids)):
        xa, xf = nodes[a_id], nodes[f_id]
        vec = xa - xf
        length = float(np.linalg.norm(vec))
        direction = vec / length
        k3 = E * STRUT_AREA / length * np.outer(direction, direction)
        dofa = [3 * a_id + c for c in range(3)]
        doff = [3 * f_id + c for c in range(3)]
        add_block(kr, kc, kv, dofa, dofa, k3)
        add_block(kr, kc, kv, dofa, doff, -k3)
        add_block(kr, kc, kv, doff, dofa, -k3)
        add_block(kr, kc, kv, doff, doff, k3)
        mass = RHO * STRUT_AREA * length
        for node in (a_id, f_id):
            for c in range(3):
                mr.append(3 * node + c)
                mc.append(3 * node + c)
                mv.append(0.5 * mass)
        top_nodes = np.array([idx for idx in range(tray_node_count) if abs(nodes[idx, 2] - (TRAY_Z + TRAY_T / 2.0)) < 1e-12])
        dist = np.linalg.norm(nodes[top_nodes, :2] - xa[:2], axis=1)
        nearest = top_nodes[np.argsort(dist)[:4]]
        for tid in nearest:
            for c in range(3):
                ia = 3 * a_id + c
                it = 3 * tid + c
                k = JOINT_K / len(nearest)
                kr += [ia, ia, it, it]
                kc += [ia, it, ia, it]
                kv += [k, -k, -k, k]
    k = sp.coo_matrix((kv, (kr, kc)), shape=(ndof, ndof)).tocsr()
    m = sp.coo_matrix((mv, (mr, mc)), shape=(ndof, ndof)).tocsr()
    fixed = sorted([3 * n + c for n in foot_ids for c in range(3)])
    free = np.setdiff1d(np.arange(ndof), np.array(fixed, dtype=int))
    metadata = {
        "nxy": nxy,
        "nodes": len(nodes),
        "tray_nodes": tray_node_count,
        "hex_elements": len(hexes),
        "truss_elements": len(STRUT_NAMES),
        "joint_spring_sets": len(STRUT_NAMES),
        "strut_lengths_m": [float(np.linalg.norm(APEX[i] - FOOT[i])) for i in range(6)],
        "tray_mass_kg_from_geometry": TRAY_L * TRAY_L * TRAY_T * RHO,
        "strut_area_m2": STRUT_AREA,
        "discretize_version": getattr(discretize, "__version__", None),
    }
    return nodes, hexes, apex_ids, foot_ids, k, m, free, metadata


def solve(nxy: int, modes: int = 10):
    nodes, hexes, apex_ids, foot_ids, k, m, free, metadata = assemble(nxy)
    kf = k[free][:, free]
    mf = m[free][:, free]
    try:
        vals, vecs = spla.eigsh(kf, k=modes + 4, M=mf, sigma=0.0, which="LM", tol=1e-8)
    except Exception:
        vals, vecs = scipy.linalg.eigh(kf.toarray(), mf.toarray())
    order = np.argsort(vals)
    vals = np.asarray(vals)[order]
    vecs = np.asarray(vecs)[:, order]
    keep = vals > 1.0e-6
    vals = vals[keep][:modes]
    vecs = vecs[:, keep][:, :modes]
    freqs = np.sqrt(vals) / (2.0 * np.pi)
    full_vecs = np.zeros((3 * len(nodes), len(freqs)), dtype=float)
    full_vecs[free, :] = vecs
    return nodes, hexes, apex_ids, foot_ids, freqs, full_vecs, metadata


def classify_mode(nodes: np.ndarray, tray_node_count: int, u: np.ndarray) -> str:
    tray_ids = np.arange(tray_node_count)
    x = nodes[tray_ids] - np.array([0.0, 0.0, TRAY_Z])
    uu = u.reshape((-1, 3))[tray_ids]
    a = np.zeros((3 * len(tray_ids), 6))
    b = uu.reshape(-1)
    for row, r in enumerate(x):
        block = np.array(
            [
                [1, 0, 0, 0, r[2], -r[1]],
                [0, 1, 0, -r[2], 0, r[0]],
                [0, 0, 1, r[1], -r[0], 0],
            ]
        )
        a[3 * row : 3 * row + 3, :] = block
    q, *_ = np.linalg.lstsq(a, b, rcond=None)
    rigid = (a @ q).reshape((-1, 3))
    residual = np.linalg.norm(uu - rigid)
    total = np.linalg.norm(uu) + 1e-30
    return "suspension" if residual / total < 0.35 else "tray-flex"


def draw_mode(nodes, hexes, apex_ids, foot_ids, vec, filename, title):
    disp = vec.reshape((-1, 3))
    scale = 0.035 / (np.max(np.linalg.norm(disp, axis=1)) + 1e-30)
    deformed = nodes + scale * disp
    fig = plt.figure(figsize=(7.0, 5.8))
    ax = fig.add_subplot(111, projection="3d")
    edges = set()
    for e in hexes:
        for a, b in [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]:
            edges.add(tuple(sorted((e[a], e[b]))))
    for a, b in edges:
        ax.plot(*zip(deformed[a], deformed[b]), color="0.55", lw=0.45)
    for a, f, name in zip(apex_ids, foot_ids, STRUT_NAMES):
        ax.plot(*zip(deformed[a], deformed[f]), color="tab:blue", lw=1.5)
        ax.text(*deformed[a], name, fontsize=7)
    ax.scatter(deformed[foot_ids, 0], deformed[foot_ids, 1], deformed[foot_ids, 2], color="black", s=12)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    ax.set_title(title)
    ax.set_box_aspect((1.0, 1.0, 0.45))
    ax.view_init(elev=24, azim=-52)
    fig.tight_layout()
    fig.savefig(filename, dpi=180)
    plt.close(fig)


def main():
    start = time.perf_counter()
    coarse_nodes, _, _, _, coarse_f, _, coarse_meta = solve(4)
    nodes, hexes, apex_ids, foot_ids, freqs, modes, meta = solve(6)
    tray_node_count = meta["tray_nodes"]
    mode_rows = []
    for i, f in enumerate(freqs):
        label = classify_mode(nodes, tray_node_count, modes[:, i])
        mode_rows.append({"mode": i + 1, "frequency_hz": float(f), "mode_type": label})
    shifts = []
    for i in range(min(len(freqs), len(coarse_f))):
        shifts.append(
            {
                "mode": i + 1,
                "coarse_hz": float(coarse_f[i]),
                "fine_hz": float(freqs[i]),
                "relative_shift_percent": float(100.0 * (freqs[i] - coarse_f[i]) / freqs[i]),
            }
        )
    zero_check_hz = float(freqs[0]) if len(freqs) else None
    pair_gaps = [
        {"modes": [i, i + 1], "gap_percent": float(100.0 * abs(freqs[i] - freqs[i - 1]) / freqs[i])}
        for i in range(1, min(10, len(freqs)), 2)
    ]
    draw_mode(nodes, hexes, apex_ids, foot_ids, np.zeros(3 * len(nodes)), FIG / "undeformed_mesh.png", "TensorMesh undeformed geometry")
    for i in range(min(6, modes.shape[1])):
        draw_mode(nodes, hexes, apex_ids, foot_ids, modes[:, i], FIG / f"mode_{i+1:02d}.png", f"TensorMesh mode {i+1}: {freqs[i]:.2f} Hz")
    elapsed = time.perf_counter() - start
    results = {
        "agent": "composer",
        "tool": "tensormesh",
        "solved_by": "agent",
        "status": "solved",
        "units": "SI: m, kg, N, Hz",
        "frame": "Origin at tray center; +z up; tray mid-plane at z=0.098 m; base feet at z=0 fixed.",
        "mass_case": "bare tray, no ballast",
        "element_types": {
            "tray": "C3D8-style linear solid hexahedra on discretize.TensorMesh",
            "struts": "3D axial truss/two-force members for spherical rod ends",
            "joints": "explicit joint nodes tied to tray by k=1e9 N/m translational springs",
        },
        "mesh": meta,
        "coarse_mesh": coarse_meta,
        "frequencies": mode_rows,
        "mesh_convergence": shifts,
        "self_checks": {
            "fixed_base_no_zero_modes": bool(zero_check_hz and zero_check_hz > 1e-3),
            "first_frequency_hz": zero_check_hz,
            "near_degenerate_pair_gaps_percent": pair_gaps,
            "strut_self_modes": "not represented by axial truss members; this build uses the bar-member option.",
            "rigid_joint_frequencies_are_provisional_upper_bound": True,
        },
        "limitations": [
            "Linear C3D8 solids with one element through thickness can shear-lock tray bending; mesh-convergence shifts are reported.",
            "Axial truss struts match spherical two-force behavior but do not capture strut bending self-modes.",
        ],
        "runtime_s": elapsed,
    }
    (ROOT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (ROOT / "runtime.json").write_text(json.dumps({"active_runtime_s": elapsed, "elapsed_wallclock_s": elapsed}, indent=2) + "\n")


if __name__ == "__main__":
    main()
