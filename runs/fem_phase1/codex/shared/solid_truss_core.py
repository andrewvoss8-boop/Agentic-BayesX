"""Small solid-tray + truss-strut modal builder for Codex Phase 1."""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import scipy.linalg

from spec import APEX, E_AL, FOOT, JOINT_K, NU_AL, RHO_AL, STRUT_AREA, STRUT_NAMES, TRAY_L, TRAY_MASS, TRAY_T, TRAY_Z


def _dmat():
    lam = E_AL * NU_AL / ((1 + NU_AL) * (1 - 2 * NU_AL))
    mu = E_AL / (2 * (1 + NU_AL))
    d = np.zeros((6, 6))
    d[:3, :3] = lam
    np.fill_diagonal(d[:3, :3], lam + 2 * mu)
    np.fill_diagonal(d[3:, 3:], mu)
    return d


def _shape(xi, eta, zeta):
    s = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1], [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)
    n = 0.125 * np.prod(1 + s * np.array([xi, eta, zeta]), axis=1)
    dn = np.column_stack(
        [
            0.125 * s[:, 0] * (1 + s[:, 1] * eta) * (1 + s[:, 2] * zeta),
            0.125 * s[:, 1] * (1 + s[:, 0] * xi) * (1 + s[:, 2] * zeta),
            0.125 * s[:, 2] * (1 + s[:, 0] * xi) * (1 + s[:, 1] * eta),
        ]
    )
    return n, dn


def hex8(xe):
    d = _dmat()
    ke = np.zeros((24, 24))
    me = np.zeros((24, 24))
    gp = 1 / math.sqrt(3)
    for xi in (-gp, gp):
        for eta in (-gp, gp):
            for zeta in (-gp, gp):
                n, dn = _shape(xi, eta, zeta)
                jac = dn.T @ xe
                detj = np.linalg.det(jac)
                dxyz = dn @ np.linalg.inv(jac)
                b = np.zeros((6, 24))
                for a, (dx, dy, dz) in enumerate(dxyz):
                    j = 3 * a
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
                    for c in range(8):
                        me[3 * a : 3 * a + 3, 3 * c : 3 * c + 3] += RHO_AL * n[a] * n[c] * detj * np.eye(3)
    return ke, me


def tray_mesh(nxy):
    xs = np.linspace(-TRAY_L / 2, TRAY_L / 2, nxy + 1)
    ys = np.linspace(-TRAY_L / 2, TRAY_L / 2, nxy + 1)
    zs = np.array([TRAY_Z - TRAY_T / 2, TRAY_Z + TRAY_T / 2])
    nodes, ids = [], {}
    for k, z in enumerate(zs):
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                ids[(i, j, k)] = len(nodes)
                nodes.append((x, y, z))
    hexes = []
    for j in range(nxy):
        for i in range(nxy):
            hexes.append([ids[(i, j, 0)], ids[(i + 1, j, 0)], ids[(i + 1, j + 1, 0)], ids[(i, j + 1, 0)], ids[(i, j, 1)], ids[(i + 1, j, 1)], ids[(i + 1, j + 1, 1)], ids[(i, j + 1, 1)]])
    tray_count = len(nodes)
    apex_ids, foot_ids = [], []
    for p in APEX:
        apex_ids.append(len(nodes))
        nodes.append(tuple(p))
    for p in FOOT:
        foot_ids.append(len(nodes))
        nodes.append(tuple(p))
    return np.array(nodes, float), hexes, tray_count, apex_ids, foot_ids


def assemble(nxy, distributed_nodes=4):
    nodes, hexes, tray_count, apex_ids, foot_ids = tray_mesh(nxy)
    nd = 3 * len(nodes)
    k = np.zeros((nd, nd))
    m = np.zeros((nd, nd))
    for e in hexes:
        ke, me = hex8(nodes[e])
        dofs = [3 * n + c for n in e for c in range(3)]
        k[np.ix_(dofs, dofs)] += ke
        m[np.ix_(dofs, dofs)] += me
    top = np.array([i for i in range(tray_count) if abs(nodes[i, 2] - (TRAY_Z + TRAY_T / 2)) < 1e-12])
    for aid, fid in zip(apex_ids, foot_ids):
        v = nodes[aid] - nodes[fid]
        length = np.linalg.norm(v)
        n = v / length
        kt = E_AL * STRUT_AREA / length * np.outer(n, n)
        da = [3 * aid + c for c in range(3)]
        df = [3 * fid + c for c in range(3)]
        k[np.ix_(da, da)] += kt
        k[np.ix_(da, df)] -= kt
        k[np.ix_(df, da)] -= kt
        k[np.ix_(df, df)] += kt
        mass = RHO_AL * STRUT_AREA * length
        for node in (aid, fid):
            for c in range(3):
                m[3 * node + c, 3 * node + c] += 0.5 * mass
        near = top[np.argsort(np.linalg.norm(nodes[top, :2] - nodes[aid, :2], axis=1))[:distributed_nodes]]
        for tid in near:
            for c in range(3):
                ia, it, kk = 3 * aid + c, 3 * tid + c, JOINT_K / len(near)
                k[ia, ia] += kk
                k[ia, it] -= kk
                k[it, ia] -= kk
                k[it, it] += kk
    fixed = np.array([3 * f + c for f in foot_ids for c in range(3)])
    free = np.setdiff1d(np.arange(nd), fixed)
    return nodes, hexes, tray_count, apex_ids, foot_ids, k, m, free


def solve(nxy):
    nodes, hexes, tray_count, apex_ids, foot_ids, k, m, free = assemble(nxy)
    vals, vecs = scipy.linalg.eigh(k[np.ix_(free, free)], m[np.ix_(free, free)])
    keep = vals > 1e-6
    vals, vecs = vals[keep][:10], vecs[:, keep][:, :10]
    full = np.zeros((3 * len(nodes), len(vals)))
    full[free] = vecs
    return nodes, hexes, tray_count, apex_ids, foot_ids, np.sqrt(vals) / (2 * np.pi), full


def classify(nodes, tray_count, u):
    ids = np.arange(tray_count)
    r = nodes[ids] - np.array([0, 0, TRAY_Z])
    uu = u.reshape((-1, 3))[ids]
    a = np.zeros((3 * len(ids), 6))
    for i, rr in enumerate(r):
        a[3 * i : 3 * i + 3] = [[1, 0, 0, 0, rr[2], -rr[1]], [0, 1, 0, -rr[2], 0, rr[0]], [0, 0, 1, rr[1], -rr[0], 0]]
    q, *_ = np.linalg.lstsq(a, uu.reshape(-1), rcond=None)
    return "suspension" if np.linalg.norm(uu - (a @ q).reshape((-1, 3))) / (np.linalg.norm(uu) + 1e-30) < 0.35 else "tray-flex"


def plot_mode(nodes, hexes, apex_ids, foot_ids, u, path: Path, title):
    disp = u.reshape((-1, 3))
    scale = 0.035 / (np.max(np.linalg.norm(disp, axis=1)) + 1e-30)
    x = nodes + scale * disp
    fig = plt.figure(figsize=(7, 5.8))
    ax = fig.add_subplot(111, projection="3d")
    edges = set()
    for e in hexes:
        for a, b in [(0, 1), (1, 2), (2, 3), (3, 0), (4, 5), (5, 6), (6, 7), (7, 4), (0, 4), (1, 5), (2, 6), (3, 7)]:
            edges.add(tuple(sorted((e[a], e[b]))))
    for a, b in edges:
        ax.plot(*zip(x[a], x[b]), color="0.6", lw=0.4)
    for a, f, name in zip(apex_ids, foot_ids, STRUT_NAMES):
        ax.plot(*zip(x[a], x[f]), color="tab:blue", lw=1.5)
        ax.text(*x[a], name, fontsize=7)
    ax.scatter(x[foot_ids, 0], x[foot_ids, 1], x[foot_ids, 2], color="black", s=12)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_zlabel("z (m)")
    ax.set_box_aspect((1, 1, 0.45))
    ax.view_init(elev=24, azim=-52)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)
