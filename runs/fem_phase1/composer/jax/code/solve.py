#!/usr/bin/env python3
"""Phase-1 hexapod normal modes — JAX hand assembly (solid tray + truss struts)."""
from __future__ import annotations

import json
import math
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
    JOINT_K,
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIG = ROOT / "figures"


def build_tray_mesh(nx: int, ny: int, nz: int):
    # Include apex attach coordinates so joint nodes land on the top surface mesh.
    x_extra = sorted({round(x, 6) for x, _, _ in APEX.values()} | {-TRAY_LX / 2, TRAY_LX / 2})
    y_extra = sorted({round(y, 6) for _, y, _ in APEX.values()} | {-TRAY_LY / 2, TRAY_LY / 2})
    xs = np.unique(np.concatenate([
        np.linspace(-TRAY_LX / 2, TRAY_LX / 2, nx + 1),
        np.array(x_extra),
    ]))
    ys = np.unique(np.concatenate([
        np.linspace(-TRAY_LY / 2, TRAY_LY / 2, ny + 1),
        np.array(y_extra),
    ]))
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
                n000 = idx[(i, j, k)]
                n100 = idx[(i + 1, j, k)]
                n110 = idx[(i + 1, j + 1, k)]
                n010 = idx[(i, j + 1, k)]
                n001 = idx[(i, j, k + 1)]
                n101 = idx[(i + 1, j, k + 1)]
                n111 = idx[(i + 1, j + 1, k + 1)]
                n011 = idx[(i, j + 1, k + 1)]
                elems.append([n000, n100, n110, n010, n001, n101, n111, n011])
    return np.array(nodes, float), elems, len(xs) - 1, len(ys) - 1, len(zs) - 1


def nearest_node(nodes: np.ndarray, target: tuple[float, float, float], tol: float = 1e-4) -> int:
    d = np.linalg.norm(nodes - np.array(target), axis=1)
    i = int(np.argmin(d))
    if d[i] > tol:
        raise RuntimeError(f"No node within {tol} m of {target}; nearest {d[i]:.4e}")
    return i


def truss_ke(coords_i: np.ndarray, coords_j: np.ndarray, E: float, A: float) -> np.ndarray:
    d = coords_j - coords_i
    L = np.linalg.norm(d)
    e = d / L
    k = E * A / L
    ee = np.outer(e, e)
    top = np.hstack([ee, -ee])
    bot = np.hstack([-ee, ee])
    return k * np.vstack([top, bot])


def truss_me(L: float, rho: float, A: float) -> np.ndarray:
    m = rho * A * L / 2.0
    me = np.zeros((6, 6))
    for i in range(2):
        me[3 * i: 3 * i + 3, 3 * i: 3 * i + 3] = np.eye(3) * m
    return me


def spring_ke(k: float) -> np.ndarray:
    k3 = k * np.eye(3)
    return np.block([[k3, -k3], [-k3, k3]])


def apex_top_node_ids(tray_nodes: np.ndarray) -> dict[str, int]:
    top_mask = np.isclose(tray_nodes[:, 2], TRAY_Z_TOP)
    top_nodes = tray_nodes[top_mask]
    top_ids = np.where(top_mask)[0]
    out = {}
    for key in ["A0", "A1", "A2"]:
        local = nearest_node(top_nodes, APEX[key])
        out[key] = int(top_ids[local])
    return out


def assemble_model(nx: int, ny: int, nz: int):
    tray_nodes, tray_elems, nxa, nya, nza = build_tray_mesh(nx, ny, nz)
    apex_ids = apex_top_node_ids(tray_nodes)
    extra_nodes = []
    foot_ids = []
    for key in ["F0", "F1", "F2", "F3", "F4", "F5"]:
        extra_nodes.append(FEET[key])
        foot_ids.append(len(tray_nodes) + len(extra_nodes) - 1)

    nodes = np.vstack([tray_nodes, np.array(extra_nodes, float)])
    nnode = nodes.shape[0]
    ndof = 3 * nnode
    K = np.zeros((ndof, ndof))
    M = np.zeros((ndof, ndof))

    for conn in tray_elems:
        coords = nodes[conn]
        ke, me = hex8_ke_me(coords, E_AL, NU_AL, RHO_AL)
        dofs = []
        for n in conn:
            dofs.extend([3 * n, 3 * n + 1, 3 * n + 2])
        for a, da in enumerate(dofs):
            for b, db in enumerate(dofs):
                K[da, db] += ke[a, b]
                M[da, db] += me[a, b]

    # Explicit joint nodes coincide with tagged top-surface tray nodes (apex_ids).

    for akey, fkey, _ in STRUTS:
        ai = apex_ids[akey]
        fi = foot_ids[["F0", "F1", "F2", "F3", "F4", "F5"].index(fkey)]
        ci = nodes[ai]
        cj = nodes[fi]
        ke = truss_ke(ci, cj, E_AL, STRUT_A)
        me = truss_me(np.linalg.norm(cj - ci), RHO_AL, STRUT_A)
        for a, na in enumerate([ai, fi]):
            for b, nb in enumerate([ai, fi]):
                ia = 3 * na
                ib = 3 * nb
                K[ia: ia + 3, ib: ib + 3] += ke[3 * a: 3 * a + 3, 3 * b: 3 * b + 3]
                M[ia: ia + 3, ib: ib + 3] += me[3 * a: 3 * a + 3, 3 * b: 3 * b + 3]

    fixed = []
    for fi in foot_ids:
        fixed.extend([3 * fi, 3 * fi + 1, 3 * fi + 2])
    fixed = sorted(set(fixed))
    free = [i for i in range(ndof) if i not in fixed]

    Kff = K[np.ix_(free, free)]
    Mff = M[np.ix_(free, free)]
    # Consistent-mass total: sum of element rho*V (not sum(M) entries).
    tray_mass = RHO_AL * TRAY_LX * TRAY_LY * (TRAY_Z_TOP - TRAY_Z_BOT)
    return nodes, free, Kff, Mff, tray_mass, {
        "nx_target": nx,
        "ny_target": ny,
        "nz": nz,
        "nx_actual": nxa,
        "ny_actual": nya,
        "nz_actual": nza,
        "nnode": nnode,
        "nelem_hex": len(tray_elems),
    }


def solve_modes(Kff: np.ndarray, Mff: np.ndarray, n_modes: int = 12):
    Kj = jnp.array(Kff)
    Mj = jnp.array(Mff)
    Lc = jnp.linalg.cholesky(Mj)
    Li = jnp.linalg.inv(Lc)
    A = Li @ Kj @ Li.T
    A = 0.5 * (A + A.T)
    w2, vec = jnp.linalg.eigh(A)
    w2 = np.array(w2)
    vec = np.array(vec)
    order = np.argsort(w2)
    w2 = w2[order]
    vec = vec[:, order]
    freqs = np.sqrt(np.clip(w2, 0.0, None)) / (2 * np.pi)
    shapes = Li.T @ vec
    return freqs[:n_modes], shapes[:, :n_modes]


def classify_mode(nodes: np.ndarray, free: list[int], shape: np.ndarray, tray_n: int) -> str:
    full = np.zeros(3 * nodes.shape[0])
    for i, fd in enumerate(free):
        full[fd] = shape[i]
    tray_disp = full[: 3 * tray_n].reshape(-1, 3)
    foot_slice = full[3 * tray_n:]
    tray_rms = float(np.sqrt(np.mean(tray_disp**2)))
    foot_rms = float(np.sqrt(np.mean(foot_slice**2))) if foot_slice.size else 0.0
    bend = float(np.std(tray_disp[:, 2]))
    if foot_rms > 0.25 * tray_rms and tray_rms > 1e-12:
        return "strut-self"
    if bend > 0.35 * np.max(np.abs(tray_disp)):
        return "tray-flex"
    return "suspension"


def plot_geometry(nodes: np.ndarray, out: Path):
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(nodes[:, 0], nodes[:, 1], nodes[:, 2], s=4, c="#4c72b0", alpha=0.5)
    for akey, fkey, _ in STRUTS:
        pa = np.array(APEX[akey])
        pb = np.array(FEET[fkey])
        ax.plot([pa[0], pb[0]], [pa[1], pb[1]], [pa[2], pb[2]], "r-", lw=1.5)
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_zlabel("z [m]")
    ax.set_title("Hexapod undeformed geometry (JAX build)")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def plot_mode(nodes: np.ndarray, free: list[int], shape: np.ndarray, freq: float, tag: str, out: Path, scale: float = 0.02):
    full = np.zeros((nodes.shape[0], 3))
    for i, fd in enumerate(free):
        comp = fd % 3
        node = fd // 3
        full[node, comp] = shape[i]
    defo = nodes + scale * full
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    for akey, fkey, _ in STRUTS:
        pa = np.array(APEX[akey])
        pb = np.array(FEET[fkey])
        ax.plot([pa[0], pb[0]], [pa[1], pb[1]], [pa[2], pb[2]], "k-", lw=0.8, alpha=0.3)
    ax.quiver(
        nodes[:, 0], nodes[:, 1], nodes[:, 2],
        defo[:, 0] - nodes[:, 0], defo[:, 1] - nodes[:, 1], defo[:, 2] - nodes[:, 2],
        length=1.0, normalize=False, color="#d62728", linewidth=0.5,
    )
    ax.set_title(f"Mode {tag}: {freq:.2f} Hz (provisional upper bound, rigid joints)")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.set_zlabel("z [m]")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main():
    t0 = time.time()
    FIG.mkdir(parents=True, exist_ok=True)
    coarse = assemble_model(6, 6, 2)
    fine = assemble_model(12, 12, 3)

    nodes, free, Kff, Mff, tray_mass, mesh = coarse
    freqs, shapes = solve_modes(Kff, Mff, 12)

    _, _, Kf2, Mf2, _, mesh_f = fine
    freqs_f, _ = solve_modes(Kf2, Mf2, 12)
    conv = [float(f2 - f1) for f1, f2 in zip(freqs[:10], freqs_f[:10])]

    plot_geometry(nodes, FIG / "undeformed_geometry.png")
    labels = []
    for i in range(min(6, len(freqs))):
        tag = f"{i + 1}"
        labels.append(classify_mode(nodes, free, shapes[:, i], mesh["nnode"]))
        plot_mode(nodes, free, shapes[:, i], freqs[i], tag, FIG / f"mode_{tag}.png")

    pairs = []
    for i in range(len(freqs) - 1):
        if abs(freqs[i + 1] - freqs[i]) / max(freqs[i], 1e-6) < 0.02:
            pairs.append((float(freqs[i]), float(freqs[i + 1])))

    results = {
        "agent": "composer",
        "tool": "jax",
        "units": "SI (m, kg, N, Hz)",
        "coordinate_frame": "origin at tray center; +z up; tray top z=0.098 m; base z=0",
        "mass_case": "bare tray, no ballast; solid mesh emergent mass",
        "tray_mass_kg": tray_mass,
        "provisional_upper_bound_note": "rigid explicit joint nodes (k=1e9 N/m); compliant joints will lower frequencies",
        "solved_by": "agent",
        "element_types": {
            "tray": "C3D8 linear hexahedral solid",
            "struts": "3D truss (axial only, spherical end releases)",
            "joints": "explicit joint nodes at apex top-surface mesh nodes (rigid this phase)",
        },
        "mesh": mesh,
        "mesh_convergence": {
            "refined_mesh": mesh_f,
            "frequency_shift_hz_coarse_to_fine_first10": conv,
        },
        "symmetry_degenerate_pairs_hz": pairs,
        "modes": [
            {
                "index": i + 1,
                "frequency_hz": float(freqs[i]),
                "mode_type": labels[i] if i < len(labels) else classify_mode(nodes, free, shapes[:, i], mesh["nnode"]),
            }
            for i in range(min(10, len(freqs)))
        ],
        "runtime_s": time.time() - t0,
        "strut_lengths_m": {name: strut_length_m(a, f) for a, f, name in STRUTS},
    }
    (ROOT / "results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps({"first10_hz": [round(float(f), 3) for f in freqs[:10]], "tray_mass_kg": round(tray_mass, 4)}, indent=2))


if __name__ == "__main__":
    main()
