#!/usr/bin/env python3
"""Phase-1 hexapod — scipy.sparse eigsh (TET4 continuum + bar struts)."""
from __future__ import annotations

import json
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh

from geometry_spec import (
    APEX, E_AL, FEET, NU_AL, RHO_AL, STRUTS, STRUT_A,
    TRAY_LX, TRAY_LY, TRAY_Z_BOT, TRAY_Z_TOP,
)

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"


def tet4_ke_me(coords, E, nu, rho):
    x, y, z = coords[:, 0], coords[:, 1], coords[:, 2]
    v6 = np.array([[1, x[i], y[i], z[i]] for i in range(4)])
    det6 = np.linalg.det(v6)
    vol = abs(det6) / 6.0
    beta = np.zeros((4, 3))
    for i in range(4):
        j = [(i + 1) % 4, (i + 2) % 4, (i + 3) % 4]
        beta[i, 0] = (-1) ** i * np.linalg.det(np.array([[1, y[j[0]], z[j[0]]], [1, y[j[1]], z[j[1]]], [1, y[j[2]], z[j[2]]]]))
        beta[i, 1] = (-1) ** (i + 1) * np.linalg.det(np.array([[1, x[j[0]], z[j[0]]], [1, x[j[1]], z[j[1]]], [1, x[j[2]], z[j[2]]]]))
        beta[i, 2] = (-1) ** (i + 2) * np.linalg.det(np.array([[1, x[j[0]], y[j[0]]], [1, x[j[1]], y[j[1]]], [1, x[j[2]], y[j[2]]]]))
    beta /= det6
    b = np.zeros((6, 12))
    for i in range(4):
        bi = beta[i]
        b[0, 3 * i] = bi[0]; b[1, 3 * i + 1] = bi[1]; b[2, 3 * i + 2] = bi[2]
        b[3, 3 * i] = bi[1]; b[3, 3 * i + 1] = bi[0]
        b[4, 3 * i + 1] = bi[2]; b[4, 3 * i + 2] = bi[1]
        b[5, 3 * i] = bi[2]; b[5, 3 * i + 2] = bi[0]
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    c = np.diag([lam + 2 * mu, lam + 2 * mu, lam + 2 * mu, mu, mu, mu])
    c[0, 1] = c[0, 2] = c[1, 0] = c[1, 2] = c[2, 0] = c[2, 1] = lam
    ke = vol * (b.T @ c @ b)
    me = np.zeros((12, 12))
    for i in range(4):
        for j in range(4):
            me[3 * i: 3 * i + 3, 3 * j: 3 * j + 3] += (rho * vol / 20.0) * (1.0 + (i == j)) * np.eye(3)
    return ke, me


def build_tray_tet_mesh(n_div):
    xs = np.unique(np.concatenate([np.linspace(-TRAY_LX / 2, TRAY_LX / 2, n_div + 1), [p[0] for p in APEX.values()]]))
    ys = np.unique(np.concatenate([np.linspace(-TRAY_LY / 2, TRAY_LY / 2, n_div + 1), [p[1] for p in APEX.values()]]))
    zs = [TRAY_Z_BOT, TRAY_Z_TOP]
    nodes, idx = [], {}
    for k, z in enumerate(zs):
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                idx[(i, j, k)] = len(nodes)
                nodes.append([x, y, z])
    elems = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            n = [idx[(i, j, 0)], idx[(i + 1, j, 0)], idx[(i + 1, j + 1, 0)], idx[(i, j + 1, 0)],
                 idx[(i, j, 1)], idx[(i + 1, j, 1)], idx[(i + 1, j + 1, 1)], idx[(i, j + 1, 1)]]
            elems += [[n[0], n[1], n[3], n[4]], [n[1], n[2], n[3], n[6]], [n[1], n[4], n[5], n[6]],
                      [n[3], n[4], n[6], n[7]], [n[1], n[3], n[4], n[6]]]
    return np.array(nodes), elems


def assemble_sparse(n_div):
    nodes, elems = build_tray_tet_mesh(n_div)
    n_tray = nodes.shape[0]
    foot_keys = ["F0", "F1", "F2", "F3", "F4", "F5"]
    nodes = np.vstack([nodes, np.array([FEET[k] for k in foot_keys])])
    foot_nodes = list(range(n_tray, n_tray + 6))
    top = np.where(np.isclose(nodes[:n_tray, 2], TRAY_Z_TOP))[0]
    apex = {k: top[np.argmin(np.linalg.norm(nodes[top] - np.array(APEX[k]), axis=1))] for k in APEX}

    ndof = 3 * nodes.shape[0]
    kr, kc, kd, mr, mc, md = [], [], [], [], [], []

    def add(ke, me, conn):
        for a, na in enumerate(conn):
            for b, nb in enumerate(conn):
                for d1 in range(3):
                    for d2 in range(3):
                        v = ke[3 * a + d1, 3 * b + d2]
                        if v:
                            kr.append(3 * na + d1); kc.append(3 * nb + d2); kd.append(v)
                        m = me[3 * a + d1, 3 * b + d2]
                        if m:
                            mr.append(3 * na + d1); mc.append(3 * nb + d2); md.append(m)

    for conn in elems:
        add(*tet4_ke_me(nodes[conn], E_AL, NU_AL, RHO_AL), conn)

    for akey, fkey in STRUTS:
        ni = apex[akey]
        nj = foot_nodes[foot_keys.index(fkey)]
        d = nodes[nj] - nodes[ni]
        L = np.linalg.norm(d)
        e = d / L
        c = E_AL * STRUT_A / L
        ke = c * np.block([[np.outer(e, e), -np.outer(e, e)], [-np.outer(e, e), np.outer(e, e)]])
        me = (RHO_AL * STRUT_A * L / 2.0) * np.eye(6)
        add(ke, me, [ni, nj])

    fixed = sorted({3 * fn + d for fn in foot_nodes for d in range(3)})
    free = np.array([i for i in range(ndof) if i not in fixed], dtype=int)
    Kff = csr_matrix((kd, (kr, kc)), shape=(ndof, ndof))[free][:, free]
    Mff = csr_matrix((md, (mr, mc)), shape=(ndof, ndof))[free][:, free]
    return nodes, free, Kff, Mff, n_tray, {"n_div": n_div, "nnode": nodes.shape[0], "nelem_tet": len(elems)}


def solve_sparse(Kff, Mff, k=12):
    w2, vec = eigsh(Kff, k=k, M=Mff, sigma=0.0, which="LM")
    order = np.argsort(w2)
    return np.sqrt(np.clip(w2[order], 0, None)) / (2 * np.pi), vec[:, order]


def main():
    t0 = time.time()
    FIG.mkdir(parents=True, exist_ok=True)
    nodes, free, Kc, Mc, n_tray, mesh_c = assemble_sparse(8)
    _, free_f, Kf, Mf, _, mesh_f = assemble_sparse(14)
    freqs, vecs = solve_sparse(Kc, Mc)
    freqs_f, _ = solve_sparse(Kf, Mf)
    pairs = [(float(freqs[i]), float(freqs[i + 1]))
             for i in range(len(freqs) - 1)
             if abs(freqs[i + 1] - freqs[i]) / max(freqs[i], 1e-9) < 0.02]

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(nodes[:, 0], nodes[:, 1], nodes[:, 2], s=3)
    fig.savefig(FIG / "undeformed_geometry.png", dpi=150); plt.close(fig)

    for i in range(6):
        full = np.zeros((nodes.shape[0], 3))
        for j, fd in enumerate(free):
            full[fd // 3, fd % 3] = vecs[j, i]
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111, projection="3d")
        ax.quiver(nodes[:, 0], nodes[:, 1], nodes[:, 2], 0.02 * full[:, 0], 0.02 * full[:, 1], 0.02 * full[:, 2], lw=0.4)
        ax.set_title(f"TensorMesh/scipy mode {i + 1}: {freqs[i]:.2f} Hz")
        fig.savefig(FIG / f"mode_{i + 1}.png", dpi=150); plt.close(fig)

    out = {
        "agent": "composer", "tool": "tensormesh",
        "units": "SI (m, kg, N, Hz)",
        "coordinate_frame": "origin at tray center; +z up; tray top z=0.098 m",
        "mass_case": "bare tray; tet solid mesh emergent mass",
        "provisional_upper_bound_note": "rigid apex joints on top-surface nodes",
        "solved_by": "agent",
        "element_types": {"tray": "TET4 constant-strain tetrahedra", "struts": "3D bar (axial)"},
        "mesh": mesh_c,
        "mesh_convergence": {"refined": mesh_f, "shift_hz_first10": [float(b - a) for a, b in zip(freqs[:10], freqs_f[:10])]},
        "symmetry_degenerate_pairs_hz": pairs,
        "modes": [{"index": i + 1, "frequency_hz": float(freqs[i]),
                   "mode_type": "tray-flex" if float(np.std((np.zeros((nodes.shape[0], 3)))) ) else "suspension"}
                  for i in range(min(10, len(freqs)))],
        "runtime_s": time.time() - t0,
    }
    # classify modes
    for i in range(min(10, len(freqs))):
        full = np.zeros(3 * nodes.shape[0])
        for j, fd in enumerate(free):
            full[fd] = vecs[j, i]
        tray = full[: 3 * n_tray].reshape(-1, 3)
        out["modes"][i]["mode_type"] = "tray-flex" if float(np.std(tray[:, 2])) > 0.3 * np.max(np.abs(tray)) else "suspension"

    (ROOT / "results.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"first10_hz": [round(float(f), 2) for f in freqs[:10]]}, indent=2))


if __name__ == "__main__":
    main()
