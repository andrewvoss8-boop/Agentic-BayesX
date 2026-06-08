#!/usr/bin/env python3
"""Phase-1 hexapod — scipy.sparse eigsh (TensorMesh-style continuum + bar assembly)."""
from __future__ import annotations

import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.linalg import eigsh

from geometry_spec import (
    APEX,
    E_AL,
    FEET,
    NU_AL,
    RHO_AL,
    STRUTS,
    STRUT_A,
    TRAY_LX,
    TRAY_LY,
    TRAY_Z_BOT,
    TRAY_Z_TOP,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIG = ROOT / "figures"


def tet4_ke_me(coords: np.ndarray, E: float, nu: float, rho: float):
    """4-node constant-strain tetrahedron, 3 DOF/node."""
    x = coords[:, 0]
    y = coords[:, 1]
    z = coords[:, 2]
    v6 = np.array([
        [1, x[0], y[0], z[0]],
        [1, x[1], y[1], z[1]],
        [1, x[2], y[2], z[2]],
        [1, x[3], y[3], z[3]],
    ])
    det6 = np.linalg.det(v6)
    vol = abs(det6) / 6.0
    beta = np.zeros((4, 3))
    for i in range(4):
        j = [(i + 1) % 4, (i + 2) % 4, (i + 3) % 4]
        m = np.array([[1, y[j[0]], z[j[0]]], [1, y[j[1]], z[j[1]]], [1, y[j[2]], z[j[2]]]])
        beta[i, 0] = (-1) ** i * np.linalg.det(m)
        m = np.array([[1, x[j[0]], z[j[0]]], [1, x[j[1]], z[j[1]]], [1, x[j[2]], z[j[2]]]])
        beta[i, 1] = (-1) ** (i + 1) * np.linalg.det(m)
        m = np.array([[1, x[j[0]], y[j[0]]], [1, x[j[1]], y[j[1]]], [1, x[j[2]], y[j[2]]]])
        beta[i, 2] = (-1) ** (i + 2) * np.linalg.det(m)
    beta /= det6
    b = np.zeros((6, 12))
    for i in range(4):
        bi = beta[i]
        b[0, 3 * i] = bi[0]
        b[1, 3 * i + 1] = bi[1]
        b[2, 3 * i + 2] = bi[2]
        b[3, 3 * i] = bi[1]
        b[3, 3 * i + 1] = bi[0]
        b[4, 3 * i + 1] = bi[2]
        b[4, 3 * i + 2] = bi[1]
        b[5, 3 * i] = bi[2]
        b[5, 3 * i + 2] = bi[0]
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    c = np.array([
        [lam + 2 * mu, lam, lam, 0, 0, 0],
        [lam, lam + 2 * mu, lam, 0, 0, 0],
        [lam, lam, lam + 2 * mu, 0, 0, 0],
        [0, 0, 0, mu, 0, 0],
        [0, 0, 0, 0, mu, 0],
        [0, 0, 0, 0, 0, mu],
    ])
    ke = vol * (b.T @ c @ b)
    me = (rho * vol / 10.0) * np.eye(12)
    for i in range(4):
        for j in range(4):
            me[3 * i: 3 * i + 3, 3 * j: 3 * j + 3] += (rho * vol / 20.0) * (1.0 + (i == j))
    return ke, me


def build_tray_tet_mesh(n_div: int):
    xs = np.linspace(-TRAY_LX / 2, TRAY_LX / 2, n_div + 1)
    ys = np.linspace(-TRAY_LY / 2, TRAY_LY / 2, n_div + 1)
    for pt in APEX.values():
        xs = np.unique(np.append(xs, pt[0]))
        ys = np.unique(np.append(ys, pt[1]))
    zs = [TRAY_Z_BOT, TRAY_Z_TOP]
    nodes = []
    idx = {}
    for k, z in enumerate(zs):
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                nid = len(nodes)
                nodes.append([x, y, z])
                idx[(i, j, k)] = nid
    elems = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            n0 = idx[(i, j, 0)]
            n1 = idx[(i + 1, j, 0)]
            n2 = idx[(i + 1, j + 1, 0)]
            n3 = idx[(i, j + 1, 0)]
            n4 = idx[(i, j, 1)]
            n5 = idx[(i + 1, j, 1)]
            n6 = idx[(i + 1, j + 1, 1)]
            n7 = idx[(i, j + 1, 1)]
            # five tets per brick layer
            elems += [
                [n0, n1, n3, n4], [n1, n2, n3, n6], [n1, n4, n5, n6],
                [n3, n4, n6, n7], [n1, n3, n4, n6],
            ]
    return np.array(nodes), elems


def apex_node_map(nodes: np.ndarray) -> dict[str, int]:
    top = np.where(np.isclose(nodes[:, 2], TRAY_Z_TOP))[0]
    out = {}
    for key, pt in APEX.items():
        d = np.linalg.norm(nodes[top] - np.array(pt), axis=1)
        out[key] = int(top[np.argmin(d)])
    return out


def assemble_sparse(n_div: int):
    nodes, elems = build_tray_tet_mesh(n_div)
    foot_nodes = [nodes.shape[0] + i for i in range(6)]
    nodes = np.vstack([nodes, np.array([FEET[k] for k in ["F0", "F1", "F2", "F3", "F4", "F5"]])])
    apex_map = apex_node_map(nodes[: len(nodes) - 6])
    nnode = nodes.shape[0]
    ndof = 3 * nnode
    k_rows, k_cols, k_data = [], [], []
    m_rows, m_cols, m_data = [], [], []

    def add_mat(rows, cols, data, ke, conn):
        for a, na in enumerate(conn):
            for b, nb in enumerate(conn):
                for d1 in range(3):
                    for d2 in range(3):
                        ii = 3 * na + d1
                        jj = 3 * nb + d2
                        val = ke[3 * a + d1, 3 * b + d2]
                        if val != 0:
                            rows.append(ii)
                            cols.append(jj)
                            data.append(val)

    for conn in elems:
        ke, me = tet4_ke_me(nodes[conn], E_AL, NU_AL, RHO_AL)
        add_mat(k_rows, k_cols, k_data, ke, conn)
        add_mat(m_rows, m_cols, m_data, me, conn)

    for akey, fkey in STRUTS:
        ni = apex_map[akey]
        fj = ["F0", "F1", "F2", "F3", "F4", "F5"].index(fkey)
        nj = foot_nodes[fj]
        d = nodes[nj] - nodes[ni]
        L = np.linalg.norm(d)
        c = E_AL * STRUT_A / L
        e = d / L
        ke = c * np.block([[np.outer(e, e), -np.outer(e, e)], [-np.outer(e, e), np.outer(e, e)]])
        me = (RHO_AL * STRUT_A * L / 2.0) * np.eye(6)
        add_mat(k_rows, k_cols, k_data, ke, [ni, nj])
        add_mat(m_rows, m_cols, m_data, me, [ni, nj])

    fixed = []
    for fn in foot_nodes:
        fixed.extend([3 * fn, 3 * fn + 1, 3 * fn + 2])
    free = np.array([i for i in range(ndof) if i not in fixed], dtype=int)

    K = csr_matrix((k_data, (k_rows, k_cols)), shape=(ndof, ndof))
    M = csr_matrix((m_data, (m_rows, m_cols)), shape=(ndof, ndof))
    Kff = K[free][:, free]
    Mff = M[free][:, free]
    return nodes, free, Kff, Mff, apex_map, {"n_div": n_div, "nnode": nnode, "nelem_tet": len(elems)}


def solve_sparse(Kff, Mff, k: int = 12):
    w2, vec = eigsh(Kff, k=k, M=Mff, sigma=0.0, which="LM")
    order = np.argsort(w2)
    w2 = w2[order]
    vec = vec[:, order]
    f = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)
    return f, vec


def classify(nodes, free, vec_col, n_tray):
    full = np.zeros(3 * nodes.shape[0])
    for i, fd in enumerate(free):
        full[fd] = vec_col[i]
    tray = full[: 3 * n_tray].reshape(-1, 3)
    if float(np.std(tray[:, 2])) > 0.3 * np.max(np.abs(tray)):
        return "tray-flex"
    return "suspension"


def plot_modes(nodes, free, vec, freq, tag, path):
    full = np.zeros((nodes.shape[0], 3))
    for i, fd in enumerate(free):
        full[fd // 3, fd % 3] = vec[i]
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    s = 0.02
    ax.quiver(nodes[:, 0], nodes[:, 1], nodes[:, 2], s * full[:, 0], s * full[:, 1], s * full[:, 2], linewidth=0.4)
    ax.set_title(f"TensorMesh/scipy mode {tag}: {freq:.2f} Hz")
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    t0 = time.time()
    FIG.mkdir(parents=True, exist_ok=True)
    n_tray = len(build_tray_tet_mesh(8)[0])
    nodes_c, free_c, Kc, Mc, _, mesh_c = assemble_sparse(8)
    nodes_f, free_f, Kf, Mf, _, mesh_f = assemble_sparse(14)
    freqs, vecs = solve_sparse(Kc, Mc, 12)
    freqs_f, _ = solve_sparse(Kf, Mf, 12)
    conv = [float(b - a) for a, b in zip(freqs[:10], freqs_f[:10])]
    pairs = []
    for i in range(len(freqs) - 1):
        if abs(freqs[i + 1] - freqs[i]) / max(freqs[i], 1e-9) < 0.02:
            pairs.append((float(freqs[i]), float(freqs[i + 1])))
    for i in range(6):
        plot_modes(nodes_c, free_c, vecs[:, i], freqs[i], i + 1, FIG / f"mode_{i + 1}.png")
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(nodes_c[:, 0], nodes_c[:, 1], nodes_c[:, 2], s=3)
    fig.savefig(FIG / "undeformed_geometry.png", dpi=150)
    plt.close(fig)
    out = {
        "agent": "composer",
        "tool": "tensormesh",
        "units": "SI (m, kg, N, Hz)",
        "coordinate_frame": "origin at tray center; +z up; tray top z=0.098 m",
        "mass_case": "bare tray; tet solid mesh emergent mass",
        "provisional_upper_bound_note": "rigid apex joints on top-surface nodes",
        "solved_by": "agent",
        "element_types": {"tray": "TET4 constant-strain tetrahedra", "struts": "3D bar (axial)"},
        "mesh": mesh_c,
        "mesh_convergence": {"refined": mesh_f, "shift_hz_first10": conv},
        "symmetry_degenerate_pairs_hz": pairs,
        "modes": [
            {"index": i + 1, "frequency_hz": float(freqs[i]), "mode_type": classify(nodes_c, free_c, vecs[:, i], n_tray)}
            for i in range(min(10, len(freqs)))
        ],
        "runtime_s": time.time() - t0,
    }
    (ROOT / "results.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"first10_hz": [round(float(f), 2) for f in freqs[:10]]}, indent=2))


if __name__ == "__main__":
    main()
