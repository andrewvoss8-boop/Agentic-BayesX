#!/usr/bin/env python3
"""Element library for the MPL stand parametric FEM rebuild (FABLE, 2026-06-11).

Units: inch-lbf-second (E in psi, rho in lbf*s^2/in^4, lengths in inches).
DOF order per node: [ux, uy, uz, rx, ry, rz] in the GLOBAL (basic) frame.

Formulations (decisions D8-D11, D16, D24 in decisions_log.md):
  - CBEAM : 2-node Timoshenko beam (shear-deformable), deck PBEAM shear factors
            K1/K2; Nastran convention I1 = bending in plane 1 (local x-y, about
            local z), I2 = plane 2 (local x-z, about local y). Lumped mass:
            translational rho*A*L/2 per node + torsional rotary inertia
            rho*(I1+I2)*L/2 about the local x axis; no bending rotary inertia.
  - CQUAD4: flat shell = isoparametric Q4 plane-stress membrane (2x2 Gauss)
            + 12-DOF ACM (non-conforming Kirchhoff) rectangle bending plate,
            + small artificial drilling stiffness (K6ROT-style, D16).
            Requires near-rectangular elements (checked; this deck's quads and
            the generated shield mesh are rectangles). Lumped mass m/4 per node
            on translations. Thin-plate theory: fine for the 1.7 mm shield; the
            0.5 in thrust plate is quasi-rigid below 500 Hz (first local mode
            ~1.4 kHz) so Kirchhoff overstiffness there is irrelevant in-band.
  - CBUSH : 6-DOF spring located at the GA-GB midpoint with rigid arms to both
            grids (Nastran S=0.5 default), element frame = basic (deck CID=0).
  - CONM2 : concentrated mass with diagonal rotary inertia at its grid.
  - RBE2  : rigid-arm MPC transformation (dependent DOFs eliminated).
"""
import numpy as np

GAUSS2 = (np.array([-1.0, 1.0]) / np.sqrt(3.0), np.array([1.0, 1.0]))
GAUSS3 = (np.array([-np.sqrt(0.6), 0.0, np.sqrt(0.6)]),
          np.array([5.0, 8.0, 5.0]) / 9.0)


def skew(r):
    return np.array([[0.0, -r[2], r[1]], [r[2], 0.0, -r[0]], [-r[1], r[0], 0.0]])


# ----------------------------------------------------------------------------- beam
def beam_axes(xa, xb, v):
    """Local triad: x along A->B; plane 1 contains v; returns rows [xh; yh; zh]."""
    dx = xb - xa
    L = np.linalg.norm(dx)
    xh = dx / L
    y0 = np.asarray(v, float) - np.dot(v, xh) * xh
    ny = np.linalg.norm(y0)
    if ny < 1e-8:
        raise ValueError("orientation vector parallel to beam axis")
    yh = y0 / ny
    zh = np.cross(xh, yh)
    return np.vstack([xh, yh, zh]), L


def beam_K_local(E, G, A, I1, I2, J, K1, K2, L):
    """12x12 Timoshenko beam stiffness, local frame, DOFs [u v w rx ry rz] x2."""
    K = np.zeros((12, 12))
    # axial
    ka = E * A / L
    for i, j, s in ((0, 0, 1), (6, 6, 1), (0, 6, -1)):
        K[i, j] += s * ka
        if i != j:
            K[j, i] += s * ka
    # torsion
    kt = G * J / L
    for i, j, s in ((3, 3, 1), (9, 9, 1), (3, 9, -1)):
        K[i, j] += s * kt
        if i != j:
            K[j, i] += s * kt

    def bend(I, kshear, idx_t, idx_r, sgn):
        """Bending block. idx_t = transverse dofs (a,b), idx_r = rotations.
        sgn=+1 for plane 1 (v, rz), sgn=-1 for plane 2 (w, ry)."""
        phi = 12.0 * E * I / (kshear * A * G * L * L) if kshear > 0 else 0.0
        c = E * I / (L ** 3 * (1.0 + phi))
        k11 = 12.0 * c
        k12 = sgn * 6.0 * L * c
        k22 = (4.0 + phi) * L * L * c
        k22b = (2.0 - phi) * L * L * c
        ta, tb = idx_t
        ra, rb = idx_r
        K[ta, ta] += k11; K[tb, tb] += k11
        K[ta, tb] += -k11; K[tb, ta] += -k11
        K[ra, ra] += k22; K[rb, rb] += k22
        K[ra, rb] += k22b; K[rb, ra] += k22b
        K[ta, ra] += k12; K[ra, ta] += k12
        K[ta, rb] += k12; K[rb, ta] += k12
        K[tb, ra] += -k12; K[ra, tb] += -k12
        K[tb, rb] += -k12; K[rb, tb] += -k12

    bend(I1, K1, (1, 7), (5, 11), +1.0)   # plane 1: v displacement, rz rotation
    bend(I2, K2, (2, 8), (4, 10), -1.0)   # plane 2: w displacement, ry rotation
    return K


def beam_M_local_lumped(rho, A, I1, I2, L, nsm=0.0):
    """Translational-only lumped mass (Nastran CBAR/CBEAM lumped default):
    rho*A*L/2 per node, NO rotary inertia (D8: member torsion/rotary modes of
    the stocky welded tubes sit far above the 500 Hz band; keeps the massless
    rotational DOF set exactly condensable)."""
    m = (rho * A + nsm) * L
    d = np.zeros(12)
    d[[0, 1, 2]] = m / 2.0
    d[[6, 7, 8]] = m / 2.0
    return np.diag(d)


def beam_KM_global(xa, xb, v, E, G, rho, prop):
    R, L = beam_axes(xa, xb, v)
    T = np.zeros((12, 12))
    for b in range(4):
        T[3 * b:3 * b + 3, 3 * b:3 * b + 3] = R
    Kl = beam_K_local(E, G, prop["A"], prop["I1"], prop["I2"], prop["J"],
                      prop["K1"], prop["K2"], L)
    Ml = beam_M_local_lumped(rho, prop["A"], prop["I1"], prop["I2"], L,
                             prop.get("nsm", 0.0))
    return T.T @ Kl @ T, T.T @ Ml @ T


# ----------------------------------------------------------------------------- shell
def shell_local_frame(xyz):
    """Best-fit local frame for a flat quad. xyz: 4x3 corner coords (G1..G4).
    Returns R (rows xh,yh,zh), corner coords in local 2-D (4x2), max out-of-plane."""
    n = np.cross(xyz[2] - xyz[0], xyz[3] - xyz[1])
    n = n / np.linalg.norm(n)
    xh = xyz[1] - xyz[0]
    xh = xh - np.dot(xh, n) * n
    xh = xh / np.linalg.norm(xh)
    yh = np.cross(n, xh)
    R = np.vstack([xh, yh, n])
    c = xyz - xyz.mean(axis=0)
    loc = c @ R.T
    return R, loc[:, :2], np.abs(loc[:, 2]).max()


def quad_membrane_K(loc, E, nu, t):
    """8x8 isoparametric Q4 plane-stress membrane (dofs ux,uy per node, local)."""
    C = E / (1.0 - nu ** 2) * np.array([[1.0, nu, 0.0],
                                        [nu, 1.0, 0.0],
                                        [0.0, 0.0, (1.0 - nu) / 2.0]])
    K = np.zeros((8, 8))
    gp, gw = GAUSS2
    for xi, wi in zip(gp, gw):
        for eta, wj in zip(gp, gw):
            dN = 0.25 * np.array([[-(1 - eta), (1 - eta), (1 + eta), -(1 + eta)],
                                  [-(1 - xi), -(1 + xi), (1 + xi), (1 - xi)]])
            Jm = dN @ loc                      # 2x2 jacobian
            detJ = np.linalg.det(Jm)
            dNxy = np.linalg.solve(Jm, dN)     # 2x4 derivatives wrt x,y
            B = np.zeros((3, 8))
            B[0, 0::2] = dNxy[0]
            B[1, 1::2] = dNxy[1]
            B[2, 0::2] = dNxy[1]
            B[2, 1::2] = dNxy[0]
            K += B.T @ C @ B * detJ * wi * wj * t
    return K


def _acm_basis(x, y):
    """12-term ACM polynomial basis and second derivatives."""
    P = np.array([1, x, y, x * x, x * y, y * y, x ** 3, x * x * y, x * y * y,
                  y ** 3, x ** 3 * y, x * y ** 3])
    Pxx = np.array([0, 0, 0, 2, 0, 0, 6 * x, 2 * y, 0, 0, 6 * x * y, 0])
    Pyy = np.array([0, 0, 0, 0, 0, 2, 0, 0, 2 * x, 6 * y, 0, 6 * x * y])
    Pxy = np.array([0, 0, 0, 0, 1, 0, 0, 2 * x, 2 * y, 0, 3 * x * x, 3 * y * y])
    Px = np.array([0, 1, 0, 2 * x, y, 0, 3 * x * x, 2 * x * y, y * y, 0,
                   3 * x * x * y, y ** 3])
    Py = np.array([0, 0, 1, 0, x, 2 * y, 0, x * x, 2 * x * y, 3 * y * y,
                   x ** 3, 3 * x * y * y])
    return P, Px, Py, Pxx, Pyy, Pxy


def plate_bending_K(loc, E, nu, t):
    """12x12 ACM rectangle bending plate. Local dofs per node: (w, rx, ry) with
    rx = dw/dy (rotation about local x), ry = -dw/dx (rotation about local y).
    `loc` must be (close to) a rectangle; built on its axis-aligned bounding box."""
    D = E * t ** 3 / (12.0 * (1.0 - nu ** 2)) * np.array(
        [[1.0, nu, 0.0], [nu, 1.0, 0.0], [0.0, 0.0, (1.0 - nu) / 2.0]])
    Amat = np.zeros((12, 12))
    for i in range(4):
        x, y = loc[i]
        P, Px, Py, _, _, _ = _acm_basis(x, y)
        Amat[3 * i] = P
        Amat[3 * i + 1] = Py        # rx =  dw/dy
        Amat[3 * i + 2] = -Px       # ry = -dw/dx
    Ainv = np.linalg.inv(Amat)
    # integrate over the actual rectangle using 3x3 Gauss on the bounding box
    xmin, ymin = loc.min(axis=0)
    xmax, ymax = loc.max(axis=0)
    a, b = xmax - xmin, ymax - ymin
    Kq = np.zeros((12, 12))
    gp, gw = GAUSS3
    for xi, wi in zip(gp, gw):
        for eta, wj in zip(gp, gw):
            x = xmin + a * (xi + 1) / 2.0
            y = ymin + b * (eta + 1) / 2.0
            _, _, _, Pxx, Pyy, Pxy = _acm_basis(x, y)
            B = np.vstack([-Pxx, -Pyy, -2.0 * Pxy])  # curvature vector kappa
            Kq += B.T @ D @ B * wi * wj * (a * b / 4.0)
    return Ainv.T @ Kq @ Ainv


def shell_parts_global(xyz, E, nu, rho, t, drill_scale=1e-4, nsm=0.0):
    """Global 24x24 flat-shell matrices for a (near-)rectangular CQUAD4, SPLIT
    for parametric thickness scaling: returns (K_mem_plus_drill, K_bend, M, oop).
    K_mem (+drilling) scales ~ t; K_bend scales ~ t^3; M scales ~ t."""
    R, loc, oop = shell_local_frame(xyz)
    Km = quad_membrane_K(loc, E, nu, t)       # ux,uy
    Kb = plate_bending_K(loc, E, nu, t)       # w, rx, ry
    Kl_m = np.zeros((24, 24))
    Kl_b = np.zeros((24, 24))
    mem_idx = []
    for i in range(4):
        mem_idx += [6 * i + 0, 6 * i + 1]
    bend_idx = []
    for i in range(4):
        bend_idx += [6 * i + 2, 6 * i + 3, 6 * i + 4]
    Kl_m[np.ix_(mem_idx, mem_idx)] += Km
    Kl_b[np.ix_(bend_idx, bend_idx)] += Kb
    # Drilling stiffness (K6ROT-style, D16): RELATIVE penalty tying each
    # node's normal rotation rz to the membrane in-plane rotation
    # omega = 0.5*(duy/dx - dux/dy) at the element center. A rigid-body
    # rotation gives rz == omega -> zero energy (preserves all 6 RBMs,
    # unlike an absolute diagonal spring). Grouped with the membrane part
    # (scales ~ t like the membrane).
    kd = drill_scale * np.mean(np.diag(Km))
    dN0 = 0.25 * np.array([[-1.0, 1.0, 1.0, -1.0],     # dN/dxi  at (0,0)
                           [-1.0, -1.0, 1.0, 1.0]])    # dN/deta at (0,0)
    J0 = dN0 @ loc
    dNxy0 = np.linalg.solve(J0, dN0)                   # dN/dx, dN/dy
    Gm = np.zeros(24)                                  # omega = Gm @ u_local
    for i in range(4):
        Gm[6 * i + 0] = -0.5 * dNxy0[1, i]             # -0.5 * dux/dy
        Gm[6 * i + 1] = +0.5 * dNxy0[0, i]             # +0.5 * duy/dx
    for i in range(4):
        Ri = -Gm.copy()
        Ri[6 * i + 5] += 1.0                           # rz_i - omega
        Kl_m += kd * np.outer(Ri, Ri)
    # area (shoelace on local coords)
    x, y = loc[:, 0], loc[:, 1]
    area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    m = (rho * t + nsm) * area
    Ml = np.zeros((24, 24))
    for i in range(4):
        for k in range(3):
            Ml[6 * i + k, 6 * i + k] = m / 4.0
    T = np.zeros((24, 24))
    for blk in range(8):
        T[3 * blk:3 * blk + 3, 3 * blk:3 * blk + 3] = R
    return T.T @ Kl_m @ T, T.T @ Kl_b @ T, T.T @ Ml @ T, oop


def shell_KM_global(xyz, E, nu, rho, t, drill_scale=1e-4, nsm=0.0):
    """Combined (K, M, shape_err) wrapper around shell_parts_global."""
    Km, Kb, M, oop = shell_parts_global(xyz, E, nu, rho, t, drill_scale, nsm)
    return Km + Kb, M, oop


# ----------------------------------------------------------------------------- bush
def bush_K_global(xa, xb, kdiag):
    """12x12 CBUSH: spring at the GA-GB midpoint with rigid arms (S=0.5),
    element/basic frame (CID=0). kdiag = [k1..k6]."""
    xm = 0.5 * (np.asarray(xa) + np.asarray(xb))
    ra = xm - xa
    rb = xm - xb
    B = np.zeros((6, 12))
    # delta_u = (u_B - skew(r_B) th_B) - (u_A - skew(r_A) th_A)
    B[0:3, 6:9] = np.eye(3)
    B[0:3, 9:12] = -skew(rb)
    B[0:3, 0:3] = -np.eye(3)
    B[0:3, 3:6] = skew(ra)
    # delta_theta = th_B - th_A
    B[3:6, 9:12] = np.eye(3)
    B[3:6, 3:6] = -np.eye(3)
    return B.T @ np.diag(kdiag) @ B


def conm2_M(mass, inertia_diag=(0.0, 0.0, 0.0)):
    d = np.array([mass, mass, mass, *inertia_diag], float)
    return np.diag(d)


# ----------------------------------------------------------------------------- rbe2
def rbe2_rows(xn, xg):
    """6x6 block expressing dependent grid DOFs from independent grid DOFs:
    u_g = u_n - skew(r) th_n ; th_g = th_n ; r = x_g - x_n."""
    r = np.asarray(xg, float) - np.asarray(xn, float)
    Tb = np.eye(6)
    Tb[0:3, 3:6] = -skew(r)
    return Tb
