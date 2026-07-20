#!/usr/bin/env python3
"""2-node 3D Euler-Bernoulli frame element + axial bar, for struts and the
load-introduction ring. Consistent mass. ADDED for this study (D10) — validated
to the same standard as the reused ShockSat shell library (validate_beam.py).

Local DOF order per node: [u, v, w, rx, ry, rz] (x = element axis).
- axial:   u   (EA/L)
- torsion: rx  (GJ/L)
- bending in x-y plane: v, rz
- bending in x-z plane: w, ry
Sign conventions follow the standard frame-element stiffness (e.g. Cook,
Concepts and Applications of FEA; Przemieniecki). Consistent mass per
Archer/Przemieniecki.

bar3d: axial-only two-force member (struts with spherical end releases carry
axial load only). Translational consistent mass on both ends; no bending/torsion.
"""
import numpy as np


def _T_3d(x1, x2, vref):
    """12x12 transform local<-global. Rows of R = local axes in global coords.
    vref = approximate orientation of local y (any vector not parallel to axis)."""
    ex = np.asarray(x2, float) - np.asarray(x1, float)
    L = np.linalg.norm(ex)
    ex = ex / L
    vref = np.asarray(vref, float)
    if abs(np.dot(ex, vref)) > 0.99 * np.linalg.norm(vref):
        vref = np.array([0.0, 0.0, 1.0])
        if abs(np.dot(ex, vref)) > 0.99:
            vref = np.array([0.0, 1.0, 0.0])
    ez = np.cross(ex, vref); ez /= np.linalg.norm(ez)
    ey = np.cross(ez, ex)
    R = np.vstack([ex, ey, ez])                 # 3x3, local-from-global
    T = np.zeros((12, 12))
    for b in range(4):
        T[3 * b:3 * b + 3, 3 * b:3 * b + 3] = R
    return T, L


def beam3d(x1, x2, E, nu, A, Iy, Iz, J, rho, vref=(0, 0, 1)):
    """Return (Ke, Me) 12x12 in GLOBAL coords for an Euler-Bernoulli frame
    element. Iy bends about local y (x-z plane), Iz about local z (x-y plane)."""
    T, L = _T_3d(x1, x2, vref)
    G = E / (2.0 * (1.0 + nu))
    k = np.zeros((12, 12))
    # axial u: dofs 0,6
    ea = E * A / L
    for a, b, s in [(0, 0, 1), (6, 6, 1), (0, 6, -1), (6, 0, -1)]:
        k[a, b] += s * ea
    # torsion rx: dofs 3,9
    gj = G * J / L
    for a, b, s in [(3, 3, 1), (9, 9, 1), (3, 9, -1), (9, 3, -1)]:
        k[a, b] += s * gj
    # bending x-y plane: v(1,7), rz(5,11), uses Iz
    ez = E * Iz / L**3
    idx = [1, 5, 7, 11]
    Kb = ez * np.array([[12, 6 * L, -12, 6 * L],
                        [6 * L, 4 * L**2, -6 * L, 2 * L**2],
                        [-12, -6 * L, 12, -6 * L],
                        [6 * L, 2 * L**2, -6 * L, 4 * L**2]])
    for i, ii in enumerate(idx):
        for j, jj in enumerate(idx):
            k[ii, jj] += Kb[i, j]
    # bending x-z plane: w(2,8), ry(4,10), uses Iy. In x-z the rotation-
    # displacement coupling sign flips relative to x-y (ry = -dw/dx).
    ey = E * Iy / L**3
    idx2 = [2, 4, 8, 10]
    Kb2 = ey * np.array([[12, -6 * L, -12, -6 * L],
                         [-6 * L, 4 * L**2, 6 * L, 2 * L**2],
                         [-12, 6 * L, 12, 6 * L],
                         [-6 * L, 2 * L**2, 6 * L, 4 * L**2]])
    for i, ii in enumerate(idx2):
        for j, jj in enumerate(idx2):
            k[ii, jj] += Kb2[i, j]

    # consistent mass
    m = np.zeros((12, 12))
    ma = rho * A * L / 6.0
    for a, b, s in [(0, 0, 2), (6, 6, 2), (0, 6, 1), (6, 0, 1)]:
        m[a, b] += s * ma
    # torsional (rotary about axis): rho*J consistent
    mt = rho * J * L / 6.0
    for a, b, s in [(3, 3, 2), (9, 9, 2), (3, 9, 1), (9, 3, 1)]:
        m[a, b] += s * mt
    Mb = (rho * A * L / 420.0) * np.array(
        [[156, 22 * L, 54, -13 * L],
         [22 * L, 4 * L**2, 13 * L, -3 * L**2],
         [54, 13 * L, 156, -22 * L],
         [-13 * L, -3 * L**2, -22 * L, 4 * L**2]])
    for i, ii in enumerate(idx):
        for j, jj in enumerate(idx):
            m[ii, jj] += Mb[i, j]
    Mb2 = (rho * A * L / 420.0) * np.array(
        [[156, -22 * L, 54, 13 * L],
         [-22 * L, 4 * L**2, -13 * L, -3 * L**2],
         [54, -13 * L, 156, 22 * L],
         [13 * L, -3 * L**2, 22 * L, 4 * L**2]])
    for i, ii in enumerate(idx2):
        for j, jj in enumerate(idx2):
            m[ii, jj] += Mb2[i, j]

    Ke = T.T @ k @ T
    Me = T.T @ m @ T
    return Ke, Me


def bar3d(x1, x2, E, A, rho):
    """Axial-only two-force member (strut with spherical end releases).
    Returns (Ke, Me) 6x6 in GLOBAL coords on translational DOFs of the two
    nodes [u1,v1,w1, u2,v2,w2]."""
    ex = np.asarray(x2, float) - np.asarray(x1, float)
    L = np.linalg.norm(ex); ex = ex / L
    R = np.outer(ex, ex)                          # 3x3 axial projector
    Ke = np.zeros((6, 6)); Me = np.zeros((6, 6))
    ea = E * A / L
    Ke[:3, :3] = ea * R; Ke[3:, 3:] = ea * R
    Ke[:3, 3:] = -ea * R; Ke[3:, :3] = -ea * R
    # consistent axial mass distributed on translations (full 3D so lateral
    # inertia of the strut mass is represented, even though no lateral stiffness)
    ma = rho * A * L / 6.0
    I3 = np.eye(3)
    Me[:3, :3] = 2 * ma * I3; Me[3:, 3:] = 2 * ma * I3
    Me[:3, 3:] = ma * I3; Me[3:, :3] = ma * I3
    return Ke, Me
