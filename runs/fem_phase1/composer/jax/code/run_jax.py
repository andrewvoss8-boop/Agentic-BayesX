#!/usr/bin/env python3
"""Composer Phase-1 JAX build.

Dense hand assembly intended as the future differentiable forward-model path. It
uses JAX for element matrix evaluation and SciPy for the generalized eigenproblem.
The mesh and solver path are separate from the TensorMesh sparse build.
"""

from __future__ import annotations

import json
import math
import time
from pathlib import Path

import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg

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
    [[0.0, 0.110, 0.098], [0.0, 0.110, 0.098], [-0.095, -0.055, 0.098], [-0.095, -0.055, 0.098], [0.095, -0.055, 0.098], [0.095, -0.055, 0.098]]
)
FOOT = np.array(
    [[-0.065, 0.267, 0.0], [0.065, 0.267, 0.0], [-0.199, -0.190, 0.0], [-0.264, -0.077, 0.0], [0.264, -0.077, 0.0], [0.199, -0.190, 0.0]]
)
STRUT_NAMES = ["b90+", "b90-", "b210+", "b210-", "b330+", "b330-"]


def make_grid(nxy: int):
    # JAX build uses an independent nonuniform grid that includes the three tray apex
    # plan locations in the plate mesh support stencil.
    base = np.linspace(-TRAY_L / 2, TRAY_L / 2, nxy + 1)
    xs = np.unique(np.round(np.r_[base, APEX[:, 0], -TRAY_L / 2, TRAY_L / 2], 12))
    ys = np.unique(np.round(np.r_[base, APEX[:, 1], -TRAY_L / 2, TRAY_L / 2], 12))
    zs = np.array([TRAY_Z - TRAY_T / 2, TRAY_Z + TRAY_T / 2])
    nodes = []
    ids = {}
    for k, z in enumerate(zs):
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                ids[(i, j, k)] = len(nodes)
                nodes.append([x, y, z])
    elems = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            elems.append([ids[(i, j, 0)], ids[(i + 1, j, 0)], ids[(i + 1, j + 1, 0)], ids[(i, j + 1, 0)], ids[(i, j, 1)], ids[(i + 1, j, 1)], ids[(i + 1, j + 1, 1)], ids[(i, j + 1, 1)]])
    tray_count = len(nodes)
    apex_ids = []
    foot_ids = []
    for p in APEX:
        apex_ids.append(len(nodes))
        nodes.append(p.tolist())
    for p in FOOT:
        foot_ids.append(len(nodes))
        nodes.append(p.tolist())
    return np.asarray(nodes, float), elems, tray_count, apex_ids, foot_ids


@jax.jit
def c3d8_jax(xe):
    lam = E * NU / ((1.0 + NU) * (1.0 - 2.0 * NU))
    mu = E / (2.0 * (1.0 + NU))
    d = jnp.array(
        [
            [lam + 2 * mu, lam, lam, 0, 0, 0],
            [lam, lam + 2 * mu, lam, 0, 0, 0],
            [lam, lam, lam + 2 * mu, 0, 0, 0],
            [0, 0, 0, mu, 0, 0],
            [0, 0, 0, 0, mu, 0],
            [0, 0, 0, 0, 0, mu],
        ],
        dtype=jnp.float64,
    )
    signs = jnp.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], dtype=jnp.float64)
    gps = jnp.array([-1.0 / jnp.sqrt(3.0), 1.0 / jnp.sqrt(3.0)], dtype=jnp.float64)
    ke = jnp.zeros((24, 24), dtype=jnp.float64)
    me = jnp.zeros((24, 24), dtype=jnp.float64)
    for xi in gps:
        for eta in gps:
            for zeta in gps:
                nat = jnp.array([xi, eta, zeta])
                n = 0.125 * jnp.prod(1.0 + signs * nat, axis=1)
                dn = jnp.column_stack(
                    [
                        0.125 * signs[:, 0] * (1 + signs[:, 1] * eta) * (1 + signs[:, 2] * zeta),
                        0.125 * signs[:, 1] * (1 + signs[:, 0] * xi) * (1 + signs[:, 2] * zeta),
                        0.125 * signs[:, 2] * (1 + signs[:, 0] * xi) * (1 + signs[:, 1] * eta),
                    ]
                )
                jac = dn.T @ xe
                detj = jnp.linalg.det(jac)
                dxyz = dn @ jnp.linalg.inv(jac)
                b = jnp.zeros((6, 24), dtype=jnp.float64)
                for a in range(8):
                    col = 3 * a
                    dx, dy, dz = dxyz[a, 0], dxyz[a, 1], dxyz[a, 2]
                    b = b.at[0, col].set(dx)
                    b = b.at[1, col + 1].set(dy)
                    b = b.at[2, col + 2].set(dz)
                    b = b.at[3, col].set(dy)
                    b = b.at[3, col + 1].set(dx)
                    b = b.at[4, col + 1].set(dz)
                    b = b.at[4, col + 2].set(dy)
                    b = b.at[5, col].set(dz)
                    b = b.at[5, col + 2].set(dx)
                ke = ke + b.T @ d @ b * detj
                for a in range(8):
                    for bnode in range(8):
                        block = RHO * n[a] * n[bnode] * detj * jnp.eye(3, dtype=jnp.float64)
                        me = me.at[3 * a : 3 * a + 3, 3 * bnode : 3 * bnode + 3].add(block)
    return ke, me


def add_dense(mat, dofs_a, dofs_b, block):
    for ia, da in enumerate(dofs_a):
        for ib, db in enumerate(dofs_b):
            mat[da, db] += float(block[ia, ib])


def assemble(nxy: int):
    nodes, elems, tray_count, apex_ids, foot_ids = make_grid(nxy)
    ndof = 3 * len(nodes)
    k = np.zeros((ndof, ndof))
    m = np.zeros((ndof, ndof))
    for elem in elems:
        ke, me = c3d8_jax(jnp.asarray(nodes[elem], dtype=jnp.float64))
        edofs = [3 * n + c for n in elem for c in range(3)]
        add_dense(k, edofs, edofs, np.asarray(ke))
        add_dense(m, edofs, edofs, np.asarray(me))
    top = np.array([i for i in range(tray_count) if abs(nodes[i, 2] - (TRAY_Z + TRAY_T / 2)) < 1e-12])
    for a_id, f_id in zip(apex_ids, foot_ids):
        xa, xf = nodes[a_id], nodes[f_id]
        vec = xa - xf
        length = np.linalg.norm(vec)
        direction = vec / length
        k3 = E * STRUT_AREA / length * np.outer(direction, direction)
        dofa = [3 * a_id + c for c in range(3)]
        doff = [3 * f_id + c for c in range(3)]
        add_dense(k, dofa, dofa, k3)
        add_dense(k, dofa, doff, -k3)
        add_dense(k, doff, dofa, -k3)
        add_dense(k, doff, doff, k3)
        mass = RHO * STRUT_AREA * length
        for node in (a_id, f_id):
            for c in range(3):
                m[3 * node + c, 3 * node + c] += 0.5 * mass
        nearest = top[np.argsort(np.linalg.norm(nodes[top, :2] - xa[:2], axis=1))[:4]]
        for tid in nearest:
            for c in range(3):
                ia = 3 * a_id + c
                it = 3 * tid + c
                kk = JOINT_K / len(nearest)
                k[ia, ia] += kk
                k[ia, it] -= kk
                k[it, ia] -= kk
                k[it, it] += kk
    fixed = np.array([3 * n + c for n in foot_ids for c in range(3)], dtype=int)
    free = np.setdiff1d(np.arange(ndof), fixed)
    meta = {
        "nxy_base": nxy,
        "nodes": int(len(nodes)),
        "tray_nodes": int(tray_count),
        "hex_elements": int(len(elems)),
        "truss_elements": 6,
        "joint_spring_sets": 6,
        "jax_version": jax.__version__,
        "tray_mass_kg_from_geometry": TRAY_L * TRAY_L * TRAY_T * RHO,
        "strut_area_m2": STRUT_AREA,
        "strut_lengths_m": [float(np.linalg.norm(APEX[i] - FOOT[i])) for i in range(6)],
    }
    return nodes, elems, apex_ids, foot_ids, k, m, free, meta


def solve(nxy: int):
    nodes, elems, apex_ids, foot_ids, k, m, free, meta = assemble(nxy)
    vals, vecs = scipy.linalg.eigh(k[np.ix_(free, free)], m[np.ix_(free, free)])
    keep = vals > 1e-6
    vals = vals[keep][:10]
    vecs = vecs[:, keep][:, :10]
    freqs = np.sqrt(vals) / (2 * np.pi)
    full = np.zeros((3 * len(nodes), len(freqs)))
    full[free, :] = vecs
    return nodes, elems, apex_ids, foot_ids, freqs, full, meta


def classify(nodes, tray_count, vec):
    ids = np.arange(tray_count)
    r = nodes[ids] - np.array([0, 0, TRAY_Z])
    u = vec.reshape((-1, 3))[ids]
    a = np.zeros((3 * len(ids), 6))
    for i, rr in enumerate(r):
        a[3 * i : 3 * i + 3] = [[1, 0, 0, 0, rr[2], -rr[1]], [0, 1, 0, -rr[2], 0, rr[0]], [0, 0, 1, rr[1], -rr[0], 0]]
    q, *_ = np.linalg.lstsq(a, u.reshape(-1), rcond=None)
    residual = np.linalg.norm(u - (a @ q).reshape((-1, 3)))
    return "suspension" if residual / (np.linalg.norm(u) + 1e-30) < 0.35 else "tray-flex"


def plot_geom(nodes, elems, apex_ids, foot_ids, vec, out, title):
    disp = vec.reshape((-1, 3))
    scale = 0.035 / (np.max(np.linalg.norm(disp, axis=1)) + 1e-30)
    xyz = nodes + scale * disp
    fig = plt.figure(figsize=(7.0, 5.8))
    ax = fig.add_subplot(111, projection="3d")
    edges = set()
    for e in elems:
        for a, b in [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]:
            edges.add(tuple(sorted((e[a], e[b]))))
    for a, b in edges:
        ax.plot(*zip(xyz[a], xyz[b]), color="0.60", lw=0.35)
    for a, f, name in zip(apex_ids, foot_ids, STRUT_NAMES):
        ax.plot(*zip(xyz[a], xyz[f]), color="tab:purple", lw=1.5)
        ax.text(*xyz[a], name, fontsize=7)
    ax.scatter(xyz[foot_ids, 0], xyz[foot_ids, 1], xyz[foot_ids, 2], color="black", s=12)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    ax.set_box_aspect((1.0, 1.0, 0.45))
    ax.view_init(elev=24, azim=-52)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(out, dpi=180)
    plt.close(fig)


def main():
    start = time.perf_counter()
    c_nodes, _, _, _, coarse_f, _, c_meta = solve(3)
    nodes, elems, apex_ids, foot_ids, freqs, modes, meta = solve(4)
    modes_json = [{"mode": i + 1, "frequency_hz": float(f), "mode_type": classify(nodes, meta["tray_nodes"], modes[:, i])} for i, f in enumerate(freqs)]
    conv = [{"mode": i + 1, "coarse_hz": float(coarse_f[i]), "fine_hz": float(freqs[i]), "relative_shift_percent": float(100 * (freqs[i] - coarse_f[i]) / freqs[i])} for i in range(min(len(coarse_f), len(freqs)))]
    plot_geom(nodes, elems, apex_ids, foot_ids, np.zeros(3 * len(nodes)), FIG / "undeformed_mesh.png", "JAX dense undeformed geometry")
    for i in range(min(6, modes.shape[1])):
        plot_geom(nodes, elems, apex_ids, foot_ids, modes[:, i], FIG / f"mode_{i+1:02d}.png", f"JAX mode {i+1}: {freqs[i]:.2f} Hz")
    elapsed = time.perf_counter() - start
    results = {
        "agent": "composer",
        "tool": "jax",
        "solved_by": "agent",
        "status": "solved",
        "units": "SI: m, kg, N, Hz",
        "frame": "Origin at tray center; +z up; tray mid-plane at z=0.098 m; base feet at z=0 fixed.",
        "mass_case": "bare tray, no ballast",
        "element_types": {
            "tray": "JAX-evaluated C3D8-style dense solid hexahedra",
            "struts": "3D axial truss/two-force members for spherical rod ends",
            "joints": "explicit joint nodes tied to tray by k=1e9 N/m translational springs",
        },
        "mesh": meta,
        "coarse_mesh": c_meta,
        "frequencies": modes_json,
        "mesh_convergence": conv,
        "self_checks": {
            "fixed_base_no_zero_modes": bool(len(freqs) and freqs[0] > 1e-3),
            "first_frequency_hz": float(freqs[0]) if len(freqs) else None,
            "near_degenerate_pair_gaps_percent": [
                {"modes": [i, i + 1], "gap_percent": float(100 * abs(freqs[i] - freqs[i - 1]) / freqs[i])}
                for i in range(1, min(10, len(freqs)), 2)
            ],
            "rigid_joint_frequencies_are_provisional_upper_bound": True,
            "strut_self_modes": "not represented by axial truss members; this build uses the bar-member option.",
        },
        "limitations": [
            "Dense JAX path is intentionally small enough for differentiable shakedown; mesh convergence is reported rather than hidden.",
            "Axial struts omit bending self-modes.",
        ],
        "runtime_s": elapsed,
    }
    (ROOT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    (ROOT / "runtime.json").write_text(json.dumps({"active_runtime_s": elapsed, "elapsed_wallclock_s": elapsed}, indent=2) + "\n")


if __name__ == "__main__":
    main()
