#!/usr/bin/env python3
"""Parametric 80/20 valve sub-frame generator (D38, FABLE 2026-06-11).

Builds a rectangular T-slot aluminum cage as a node/member list for the
higher-fidelity valve-assembly model that REPLACES the single rigid CONM2.
Pure geometry/topology here; assemble.py turns members into aluminum
Timoshenko beams (K_valveframe/M_valveframe), lumps the tank/valve masses on
frame nodes (M_valvemass), and bolts the bottom corners to the stand
(K_valve_mount).

Cage topology: 4 x-stations (n_bays+1) x 2 y-sides x 2 z-levels = corner
nodes; members = verticals + long rails (x) + transverse rails (y) at top and
bottom. Tanks lumped on bottom-rail nodes; manifold/valves on mid/upper nodes.
"""
import numpy as np


def build_valve_frame(spec, id0=910000):
    c = np.array(spec["center"], float)
    L, W, H = spec["L_x"], spec["W_y"], spec["H_z"]
    nb = spec["n_bays"]
    xs = c[0] + np.linspace(-L / 2, L / 2, nb + 1)
    ys = [c[1] - W / 2, c[1] + W / 2]
    zs = [c[2] - H / 2, c[2] + H / 2]          # bottom, top

    nodes = {}            # id -> xyz
    idx = {}              # (ix, iy, iz) -> id
    nid = id0
    for iz, z in enumerate(zs):
        for iy, y in enumerate(ys):
            for ix, x in enumerate(xs):
                nodes[nid] = np.array([x, y, z])
                idx[(ix, iy, iz)] = nid
                nid += 1

    beams = []            # (id_a, id_b)
    # verticals (each station, each side)
    for ix in range(nb + 1):
        for iy in range(2):
            beams.append((idx[(ix, iy, 0)], idx[(ix, iy, 1)]))
    # long rails along x (each side, each level)
    for iy in range(2):
        for iz in range(2):
            for ix in range(nb):
                beams.append((idx[(ix, iy, iz)], idx[(ix + 1, iy, iz)]))
    # transverse rails along y (each station, each level)
    for ix in range(nb + 1):
        for iz in range(2):
            beams.append((idx[(ix, 0, iz)], idx[(ix, 1, iz)]))

    # tank masses: lumped on bottom-level nodes (low, where the tanks sit)
    bottom_nodes = [idx[(ix, iy, 0)] for ix in range(nb + 1) for iy in range(2)]
    n_tanks = spec["n_tanks"]
    # spread tanks across the lowest interior nodes
    tank_nodes = bottom_nodes[:n_tanks] if len(bottom_nodes) >= n_tanks \
        else bottom_nodes
    lumped = {}           # node_id -> mass_lbm
    m_tank = spec["tank_mass_lbm_each"]
    for n in tank_nodes:
        lumped[n] = lumped.get(n, 0.0) + m_tank * n_tanks / len(tank_nodes)
    # manifold/valves: spread on TOP-level nodes (manifold runs up top)
    top_nodes = [idx[(ix, iy, 1)] for ix in range(nb + 1) for iy in range(2)]
    m_each = spec["valve_manifold_mass_lbm"] / len(top_nodes)
    for n in top_nodes:
        lumped[n] = lumped.get(n, 0.0) + m_each

    # mount nodes = the 4 bottom corners
    mount_nodes = [idx[(0, 0, 0)], idx[(nb, 0, 0)],
                   idx[(0, 1, 0)], idx[(nb, 1, 0)]]
    return dict(nodes=nodes, beams=beams, lumped=lumped,
                mount_nodes=mount_nodes,
                n_nodes=len(nodes), n_beams=len(beams))


def beam_orient(xa, xb):
    """An orientation vector not parallel to the member axis (local-y ref)."""
    d = np.asarray(xb) - np.asarray(xa)
    d = d / np.linalg.norm(d)
    ref = np.array([0.0, 0.0, 1.0])
    if abs(np.dot(d, ref)) > 0.9:             # member is vertical-ish
        ref = np.array([1.0, 0.0, 0.0])
    return ref.tolist()
