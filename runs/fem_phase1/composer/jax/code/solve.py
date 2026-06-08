#!/usr/bin/env python3
"""Phase-1 hexapod normal modes — JAX hand assembly (solid tray + truss struts)."""
from __future__ import annotations

import json
import time
from pathlib import Path

import jax
import jax.numpy as jnp
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from geometry import (
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
    strut_length_m,
)
from solid_hex import hex8_ke_me

jax.config.update("jax_enable_x64", True)

ROOT = Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"


def build_tray_mesh(nx: int, ny: int, nz: int):
    x_extra = sorted({round(x, 6) for x, _, _ in APEX.values()} | {-TRAY_LX / 2, TRAY_LX / 2})
    y_extra = sorted({round(y, 6) for _, y, _ in APEX.values()} | {-TRAY_LY / 2, TRAY_LY / 2})
    xs = np.unique(np.concatenate([np.linspace(-TRAY_LX / 2, TRAY_LX / 2, nx + 1), np.array(x_extra)]))
    ys = np.unique(np.concatenate([np.linspace(-TRAY_LY / 2, TRAY_LY / 2, ny + 1), np.array(y_extra)]))
    zs = np.linspace(TRAY_Z_BOT, TRAY_Z_TOP, nz + 1)
    nodes = []
    idx = {}
    for k, z in enumerate(zs):
        for j, y in enumerate(ys):
            for i, x in enumerate(xs):
                nid = len(nodes)
                nodes.append((x, y, z))
                idx[(i, j, k)] = nid
    elems = []
    for k in range(len(zs) - 1):
        for j in range(len(ys) - 1):
            for i in range(len(xs) - 1):
                elems.append([
                    idx[(i, j, k)], idx[(i + 1, j, k)], idx[(i + 1, j + 1, k)], idx[(i, j + 1, k)],
                    idx[(i, j, k + 1)], idx[(i + 1, j, k + 1)], idx[(i + 1, j + 1, k + 1)], idx[(i, j + 1, k + 1)],
                ])
    return np.array(nodes, float), elems, len(xs) - 1, len(ys) - 1, len(zs) - 1


def nearest_node(nodes: np.ndarray, target: tuple[float, float, float], tol: float = 1e-4) -> int:
    d = np.linalg.norm(nodes - np.array(target), axis=1)
    i = int(np.argmin(d))
    if d[i] > tol:
        raise RuntimeError(f"No node within {tol} m of {target}; nearest {d[i]:.4e}")
    return i


def truss_ke(ci: np.ndarray, cj: np.ndarray, E: float, A: float) -> np.ndarray:
    d = cj - ci
    L = np.linalg.norm(d)
    e = d / L
    k = E * A / L
    ee = np.outer(e, e)
    return k * np.vstack([np.hstack([ee, -ee]), np.hstack([-ee, ee])])


def truss_me(L: float, rho: float, A: float) -> np.ndarray:
    m = rho * A * L / 2.0
    me = np.zeros((6, 6))
    for i in range(2):
        me[3 * i: 3 * i + 3, 3 * i: 3 * i + 3] = np.eye(3) * m
    return me


def apex_top_node_ids(tray_nodes: np.ndarray) -> dict[str, int]:
    top_mask = np.isclose(tray_nodes[:, 2], TRAY_Z_TOP)
    top_nodes = tray_nodes[top_mask]
    top_ids = np.where(top_mask)[0]
    return {key: int(top_ids[nearest_node(top_nodes, APEX[key])]) for key in ["A0", "A1", "A2"]}


def assemble_model(nx: int, ny: int, nz: int):
    tray_nodes, tray_elems, nxa, nya, nza = build_tray_mesh(nx, ny, nz)
    apex_ids = apex_top_node_ids(tray_nodes)
    extra = [FEET[k] for k in ["F0", "F1", "F2", "F3", "F4", "F5"]]
    foot_ids = [len(tray_nodes) + i for i in range(6)]
    nodes = np.vstack([tray_nodes, np.array(extra, float)])
    ndof = 3 * nodes.shape[0]
    K = np.zeros((ndof, ndof))
    M = np.zeros((ndof, ndof))

    for conn in tray_elems:
        ke, me = hex8_ke_me(nodes[conn], E_AL, NU_AL, RHO_AL)
        dofs = [3 * n + d for n in conn for d in range(3)]
        for a, da in enumerate(dofs):
            for b, db in enumerate(dofs):
                K[da, db] += ke[a, b]
                M[da, db] += me[a, b]

    foot_map = {k: i for i, k in enumerate(["F0", "F1", "F2", "F3", "F4", "F5"])}
    for akey, fkey, _ in STRUTS:
        ai = apex_ids[akey]
        fi = foot_ids[foot_map[fkey]]
        ke = truss_ke(nodes[ai], nodes[fi], E_AL, STRUT_A)
        me = truss_me(np.linalg.norm(nodes[fi] - nodes[ai]), RHO_AL, STRUT_A)
        for a, na in enumerate([ai, fi]):
            for b, nb in enumerate([ai, fi]):
                ia, ib = 3 * na, 3 * nb
                K[ia: ia + 3, ib: ib + 3] += ke[3 * a: 3 * a + 3, 3 * b: 3 * b + 3]
                M[ia: ia + 3, ib: ib + 3] += me[3 * a: 3 * a + 3, 3 * b: 3 * b + 3]

    fixed = sorted({3 * fn + d for fn in foot_ids for d in range(3)})
    free = [i for i in range(ndof) if i not in fixed]
    Kff = K[np.ix_(free, free)]
    Mff = M[np.ix_(free, free)]
    tray_mass = RHO_AL * TRAY_LX * TRAY_LY * (TRAY_Z_TOP - TRAY_Z_BOT)
    return nodes, free, Kff, Mff, tray_mass, {
        "nx_target": nx, "ny_target": ny, "nz": nz,
        "nx_actual": nxa, "ny_actual": nya, "nz_actual": nza,
        "nnode": nodes.shape[0], "nelem_hex": len(tray_elems),
    }


def solve_modes(Kff, Mff, n_modes=12):
    Kj, Mj = jnp.array(Kff), jnp.array(Mff)
    Lc = jnp.linalg.cholesky(Mj)
    Li = jnp.linalg.inv(Lc)
    A = 0.5 * (Li @ Kj @ Li.T + (Li @ Kj @ Li.T).T)
    w2, vec = jnp.linalg.eigh(A)
    w2, vec = np.array(w2), np.array(vec)
    order = np.argsort(w2)
    freqs = np.sqrt(np.clip(w2[order], 0.0, None)) / (2 * np.pi)
    shapes = Li.T @ vec[:, order]
    return freqs[:n_modes], shapes[:, :n_modes]


def classify_mode(nodes, free, shape, tray_n):
    full = np.zeros(3 * nodes.shape[0])
    for i, fd in enumerate(free):
        full[fd] = shape[i]
    tray = full[: 3 * tray_n].reshape(-1, 3)
    if float(np.std(tray[:, 2])) > 0.35 * max(np.max(np.abs(tray)), 1e-12):
        return "tray-flex"
    return "suspension"


def plot_geometry(nodes, out):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(nodes[:, 0], nodes[:, 1], nodes[:, 2], s=4, c="#4c72b0", alpha=0.5)
    for akey, fkey, _ in STRUTS:
        pa, pb = np.array(APEX[akey]), np.array(FEET[fkey])
        ax.plot([pa[0], pb[0]], [pa[1], pb[1]], [pa[2], pb[2]], "r-", lw=1.5)
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
    ax.set_title("Hexapod undeformed geometry (JAX build)")
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)


def plot_mode(nodes, free, shape, freq, tag, out, scale=0.02):
    full = np.zeros((nodes.shape[0], 3))
    for i, fd in enumerate(free):
        full[fd // 3, fd % 3] = shape[i]
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.quiver(nodes[:, 0], nodes[:, 1], nodes[:, 2],
              scale * full[:, 0], scale * full[:, 1], scale * full[:, 2],
              linewidth=0.5, color="#d62728")
    ax.set_title(f"Mode {tag}: {freq:.2f} Hz (provisional upper bound, rigid joints)")
    fig.tight_layout(); fig.savefig(out, dpi=150); plt.close(fig)


def main():
    t0 = time.time()
    FIG.mkdir(parents=True, exist_ok=True)
    nodes, free, Kc, Mc, tray_mass, mesh_c = assemble_model(6, 6, 2)
    _, _, Kf, Mf, _, mesh_f = assemble_model(12, 12, 3)
    freqs, shapes = solve_modes(Kc, Mc, 12)
    freqs_f, _ = solve_modes(Kf, Mf, 12)
    conv = [float(b - a) for a, b in zip(freqs[:10], freqs_f[:10])]
    pairs = [(float(freqs[i]), float(freqs[i + 1]))
             for i in range(len(freqs) - 1)
             if abs(freqs[i + 1] - freqs[i]) / max(freqs[i], 1e-6) < 0.02]

    plot_geometry(nodes, FIG / "undeformed_geometry.png")
    labels = []
    for i in range(min(6, len(freqs))):
        labels.append(classify_mode(nodes, free, shapes[:, i], mesh_c["nnode"]))
        plot_mode(nodes, free, shapes[:, i], freqs[i], i + 1, FIG / f"mode_{i + 1}.png")

    out = {
        "agent": "composer",
        "tool": "jax",
        "units": "SI (m, kg, N, Hz)",
        "coordinate_frame": "origin at tray center; +z up; tray top z=0.098 m; base z=0",
        "mass_case": "bare tray, no ballast; solid mesh emergent mass",
        "tray_mass_kg": tray_mass,
        "provisional_upper_bound_note": "rigid apex joints on top-surface mesh nodes",
        "solved_by": "agent",
        "element_types": {
            "tray": "C3D8 linear hexahedral solid",
            "struts": "3D truss (axial only, spherical end releases)",
            "joints": "explicit joint nodes at apex top-surface mesh nodes (rigid this phase)",
        },
        "mesh": mesh_c,
        "mesh_convergence": {"refined_mesh": mesh_f, "frequency_shift_hz_coarse_to_fine_first10": conv},
        "symmetry_degenerate_pairs_hz": pairs,
        "modes": [
            {"index": i + 1, "frequency_hz": float(freqs[i]),
             "mode_type": labels[i] if i < len(labels) else classify_mode(nodes, free, shapes[:, i], mesh_c["nnode"])}
            for i in range(min(10, len(freqs)))
        ],
        "runtime_s": time.time() - t0,
        "strut_lengths_m": {name: strut_length_m(a, f) for a, f, name in STRUTS},
    }
    (ROOT / "results.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({"first10_hz": [round(float(f), 3) for f in freqs[:10]]}, indent=2))


if __name__ == "__main__":
    main()
