#!/usr/bin/env python3
"""Vectorized flat-facet shell FE core for the ShockSat parametric twin.

Formulations (documented in fem_assembly_report.md):
- CQUAD4: QM6 incompatible-mode membrane (Taylor-corrected, passes patch test
  on distorted meshes) + MITC4 (Dvorkin-Bathe) Mindlin bending, flat-facet,
  small-warp projection onto the element mean plane. Drilling DOF gets a
  penalty stiffness mimicking PARAM,K6ROT (NX Nastran): k_drill =
  K6ROT*1e-6*G*t*A per node.
- CTRIA3: CST membrane + DKT bending (thin-plate; trias are a small minority).
- Mass: lumped translational (NX Nastran default "mass" lumping) plus lumped
  rotary inertia rho*t^3/12*A_node (tiny for these thin shells; sensitivity
  checked) so M is positive definite for shift-invert Lanczos.
- CBUSH: 6x6 generalized spring in CID frame at the midpoint (S=0.5) with
  rigid arms to GA/GB (exact for the coincident pairs that dominate here).
- CONM2: offset point mass -> 6x6 nodal matrix via rigid-offset transform.
- RBE2: exact MPC elimination u_full = T u_indep (CM=123 spiders tie
  translations to the independent grid's rigid motion; CM=123456 ties all 6).

Everything is float64 numpy, batched over elements with einsum.
"""
import numpy as np
import scipy.sparse as sp

# ---------------------------------------------------------------- geometry

def quad_local_frames(X):
    """X: (ne,4,3) node coords. Returns origin (ne,3), R (ne,3,3) rows=e1,e2,e3,
    local 2D coords (ne,4,2) after mean-plane projection, and max warp (ne,)."""
    d1 = X[:, 2] - X[:, 0]
    d2 = X[:, 3] - X[:, 1]
    e3 = np.cross(d1, d2)
    e3 /= np.linalg.norm(e3, axis=1, keepdims=True)
    # x-axis: bisector convention approximated by side 1-2 projected to plane
    s12 = X[:, 1] - X[:, 0]
    e1 = s12 - (s12 * e3).sum(1, keepdims=True) * e3
    e1 /= np.linalg.norm(e1, axis=1, keepdims=True)
    e2 = np.cross(e3, e1)
    R = np.stack([e1, e2, e3], axis=1)          # (ne,3,3)
    O = X.mean(axis=1)                           # mean-plane origin
    Xl = np.einsum('eij,enj->eni', R, X - O[:, None, :])
    warp = np.abs(Xl[..., 2]).max(axis=1)
    return O, R, Xl[..., :2], warp

# ------------------------------------------------------------ QM6 membrane

GP2 = np.array([[-1, -1], [1, -1], [1, 1], [-1, 1]]) / np.sqrt(3.0)

def _q4_dN(xi, eta):
    """dN/dxi, dN/deta for bilinear quad: returns (2,4)."""
    return 0.25 * np.array([
        [-(1 - eta),  (1 - eta), (1 + eta), -(1 + eta)],
        [-(1 - xi), -(1 + xi),  (1 + xi),  (1 - xi)]])

def qm6_membrane(Xl2, E, nu, t):
    """Batched QM6 membrane stiffness. Xl2: (ne,4,2). Returns (ne,8,8) for
    DOFs [u1,v1,...,u4,v4]."""
    ne = Xl2.shape[0]
    Dm = (E / (1 - nu ** 2))[:, None, None] * \
        np.array([[1, 0, 0], [0, 1, 0], [0, 0, 0]])[None]
    Dm = Dm + (E / (1 - nu ** 2) * nu)[:, None, None] * \
        np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]])[None]
    Dm = Dm + (E / (2 * (1 + nu)))[:, None, None] * \
        np.array([[0, 0, 0], [0, 0, 0], [0, 0, 1]])[None]

    nGP = 4
    B_u = np.zeros((ne, nGP, 3, 8))
    B_a = np.zeros((ne, nGP, 3, 4))     # incompatible modes: a1..a4
    detJ = np.zeros((ne, nGP))
    J0 = None
    # Jacobian at center for incompatible-mode correction
    dN0 = _q4_dN(0.0, 0.0)
    J0 = np.einsum('in,enj->eij', dN0, Xl2)      # (ne,2,2)
    detJ0 = np.linalg.det(J0)
    invJ0 = np.linalg.inv(J0)
    area = np.zeros(ne)
    for g, (xi, eta) in enumerate(GP2):
        dN = _q4_dN(xi, eta)                      # (2,4)
        J = np.einsum('in,enj->eij', dN, Xl2)     # (ne,2,2)
        dJ = np.linalg.det(J)
        invJ = np.linalg.inv(J)
        dNxy = np.einsum('eij,jn->ein', invJ, dN)
        detJ[:, g] = dJ
        area += dJ  # weight=1
        for a in range(4):
            B_u[:, g, 0, 2 * a] = dNxy[:, 0, a]
            B_u[:, g, 1, 2 * a + 1] = dNxy[:, 1, a]
            B_u[:, g, 2, 2 * a] = dNxy[:, 1, a]
            B_u[:, g, 2, 2 * a + 1] = dNxy[:, 0, a]
        # incompatible modes N5 = 1-xi^2 (u,v), N6 = 1-eta^2 (u,v)
        # Taylor correction: evaluate with center Jacobian scaled by detJ0/detJ
        dM = np.array([[-2 * xi, 0.0], [0.0, -2 * eta]])  # d/dxi of [N5,N6]
        # map with modified Jacobian (Taylor 1976): use invJ0 * detJ0/detJ
        scale = (detJ0 / dJ)[:, None, None]
        dMxy = scale * np.einsum('eij,jm->eim', invJ0, dM)  # (ne,2,2)
        # modes: a1: u += N5*a1 ; a2: u += N6*a2 ; a3: v += N5*a3 ; a4: v += N6*a4
        B_a[:, g, 0, 0] = dMxy[:, 0, 0]
        B_a[:, g, 0, 1] = dMxy[:, 0, 1]
        B_a[:, g, 1, 2] = dMxy[:, 1, 0]
        B_a[:, g, 1, 3] = dMxy[:, 1, 1]
        B_a[:, g, 2, 0] = dMxy[:, 1, 0]
        B_a[:, g, 2, 1] = dMxy[:, 1, 1]
        B_a[:, g, 2, 2] = dMxy[:, 0, 0]
        B_a[:, g, 2, 3] = dMxy[:, 0, 1]

    w = detJ * t[:, None]                        # weights x thickness
    Kuu = np.einsum('egki,ekl,eglj,eg->eij', B_u, Dm, B_u, w)
    Kua = np.einsum('egki,ekl,eglj,eg->eij', B_u, Dm, B_a, w)
    Kaa = np.einsum('egki,ekl,eglj,eg->eij', B_a, Dm, B_a, w)
    Kaa_inv = np.linalg.inv(Kaa)
    K = Kuu - np.einsum('eik,ekl,ejl->eij', Kua, Kaa_inv, Kua)
    return K, area

# ------------------------------------------------------------ MITC4 bending

def mitc4_bending(Xl2, E, nu, G3, t, bend_ratio, ts_t):
    """Batched MITC4 plate bending. DOFs [w1,thx1,thy1, ..., w4,thx4,thy4]
    with thx = rotation about x (NASTRAN convention: w,x = +thy ; w,y = -thx).
    We use beta notation: beta_x = -thy? -- To avoid sign tangles we build with
    engineering rotations (phi_x = dw/dx, phi_y = dw/dy convention via
    beta = [bx,by] where bx,by are section rotations s.t. shear = grad w - beta)
    and map to NASTRAN at the end: bx = thy, by = -thx.
    Returns (ne,12,12) in [w,thx,thy] per node ordering."""
    ne = Xl2.shape[0]
    Db = (E * t ** 3 * bend_ratio / (12 * (1 - nu ** 2)))
    kshear = ts_t  # NASTRAN TS/T default 5/6
    Ds = G3 * kshear * t

    Kb = np.zeros((ne, 12, 12))
    # bending part: standard 2x2 on curvature from rotations
    for xi, eta in GP2:
        dN = _q4_dN(xi, eta)
        J = np.einsum('in,enj->eij', dN, Xl2)
        dJ = np.linalg.det(J)
        invJ = np.linalg.inv(J)
        dNxy = np.einsum('eij,jn->ein', invJ, dN)
        # DOF order per node: [w, bx, by] (beta system)
        Bb = np.zeros((ne, 3, 12))
        for a in range(4):
            Bb[:, 0, 3 * a + 1] = dNxy[:, 0, a]                 # kx = bx,x
            Bb[:, 1, 3 * a + 2] = dNxy[:, 1, a]                 # ky = by,y
            Bb[:, 2, 3 * a + 1] = dNxy[:, 1, a]                 # kxy
            Bb[:, 2, 3 * a + 2] = dNxy[:, 0, a]
        Dmat = np.zeros((ne, 3, 3))
        Dmat[:, 0, 0] = Dmat[:, 1, 1] = Db
        Dmat[:, 0, 1] = Dmat[:, 1, 0] = nu * Db
        Dmat[:, 2, 2] = (1 - nu) / 2 * Db
        Kb += np.einsum('eki,ekl,elj,e->eij', Bb, Dmat, Bb, dJ)

    # MITC4 assumed transverse shear: tying points at side midpoints
    N4 = lambda xi, eta: 0.25 * np.array([(1 - xi) * (1 - eta),
                                          (1 + xi) * (1 - eta),
                                          (1 + xi) * (1 + eta),
                                          (1 - xi) * (1 + eta)])
    ties = {'A': (0.0, -1.0), 'B': (1.0, 0.0), 'C': (0.0, 1.0), 'D': (-1.0, 0.0)}
    Bt = {}
    for key, (xi, eta) in ties.items():
        dN = _q4_dN(xi, eta)
        J = np.einsum('in,enj->eij', dN, Xl2)
        Nf = N4(xi, eta)
        # covariant shear strain g_xi = dw/dxi - (J row1 . beta) etc.
        B = np.zeros((ne, 2, 12))
        for a in range(4):
            B[:, 0, 3 * a] = dN[0, a]
            B[:, 0, 3 * a + 1] = -Nf[a] * J[:, 0, 0]
            B[:, 0, 3 * a + 2] = -Nf[a] * J[:, 0, 1]
            B[:, 1, 3 * a] = dN[1, a]
            B[:, 1, 3 * a + 1] = -Nf[a] * J[:, 1, 0]
            B[:, 1, 3 * a + 2] = -Nf[a] * J[:, 1, 1]
        Bt[key] = B
    Ks = np.zeros((ne, 12, 12))
    for xi, eta in GP2:
        dN = _q4_dN(xi, eta)
        J = np.einsum('in,enj->eij', dN, Xl2)
        dJ = np.linalg.det(J)
        invJ = np.linalg.inv(J)
        # interpolated covariant strains
        Bcov = np.zeros((ne, 2, 12))
        Bcov[:, 0] = 0.5 * ((1 - eta) * Bt['A'][:, 0] + (1 + eta) * Bt['C'][:, 0])
        Bcov[:, 1] = 0.5 * ((1 - xi) * Bt['D'][:, 1] + (1 + xi) * Bt['B'][:, 1])
        # to cartesian: gamma_xyz = invJ^T? gamma_cart = invJ @ gamma_cov? strains
        # covariant components relate via J^{-1}: gamma_cart_i = invJ[i,j] g_cov_j
        Bcart = np.einsum('eij,ejk->eik', invJ, Bcov)
        Ks += np.einsum('eki,e,ekj,e->eij', Bcart, Ds, Bcart, dJ)

    K = Kb + Ks
    # map beta -> NASTRAN rotations. Derivation (rigid-tilt checks in
    # fe_validate.py V3b): rotation thx about x gives w=+y*thx, section
    # rotation by=+thx; rotation thy about y gives w=-x*thy, bx=-thy.
    Tmap = np.zeros((12, 12))
    for a in range(4):
        Tmap[3 * a, 3 * a] = 1.0           # w
        Tmap[3 * a + 1, 3 * a + 2] = -1.0  # bx <- -thy
        Tmap[3 * a + 2, 3 * a + 1] = 1.0   # by <- +thx
    K = np.einsum('ki,ekl,lj->eij', Tmap, K, Tmap)
    return K

# --------------------------------------------------------------- CST + DKT

def cst_membrane(Xl2, E, nu, t):
    """CST membrane, Xl2 (ne,3,2) -> (ne,6,6) [u1,v1,u2,v2,u3,v3]."""
    x = Xl2[..., 0]; y = Xl2[..., 1]
    b = np.stack([y[:, 1] - y[:, 2], y[:, 2] - y[:, 0], y[:, 0] - y[:, 1]], 1)
    c = np.stack([x[:, 2] - x[:, 1], x[:, 0] - x[:, 2], x[:, 1] - x[:, 0]], 1)
    A2 = (x[:, 1] - x[:, 0]) * (y[:, 2] - y[:, 0]) - \
         (x[:, 2] - x[:, 0]) * (y[:, 1] - y[:, 0])   # 2*area
    ne = Xl2.shape[0]
    B = np.zeros((ne, 3, 6))
    for a in range(3):
        B[:, 0, 2 * a] = b[:, a]
        B[:, 1, 2 * a + 1] = c[:, a]
        B[:, 2, 2 * a] = c[:, a]
        B[:, 2, 2 * a + 1] = b[:, a]
    B /= A2[:, None, None]
    D = np.zeros((ne, 3, 3))
    f = E / (1 - nu ** 2)
    D[:, 0, 0] = D[:, 1, 1] = f
    D[:, 0, 1] = D[:, 1, 0] = f * nu
    D[:, 2, 2] = E / (2 * (1 + nu))
    K = np.einsum('eki,ekl,elj,e->eij', B, D, B, 0.5 * A2 * t)
    return K, 0.5 * A2

def dkt_bending(Xl2, E, nu, t, bend_ratio):
    """DKT thin-plate bending triangle (Batoz). (ne,9,9) [w,thx,thy]x3.
    Builds Bb at 3 mid-side Gauss points (exact for DKT)."""
    ne = Xl2.shape[0]
    x = Xl2[..., 0]; y = Xl2[..., 1]
    x12 = x[:, 0] - x[:, 1]; x23 = x[:, 1] - x[:, 2]; x31 = x[:, 2] - x[:, 0]
    y12 = y[:, 0] - y[:, 1]; y23 = y[:, 1] - y[:, 2]; y31 = y[:, 2] - y[:, 0]
    A2 = x31 * y12 - x12 * y31  # 2*area (positive for CCW)
    l12 = x12 ** 2 + y12 ** 2; l23 = x23 ** 2 + y23 ** 2; l31 = x31 ** 2 + y31 ** 2
    P4 = -6 * x23 / l23; P5 = -6 * x31 / l31; P6 = -6 * x12 / l12
    t4 = -6 * y23 / l23; t5 = -6 * y31 / l31; t6 = -6 * y12 / l12
    q4 = 3 * x23 * y23 / l23; q5 = 3 * x31 * y31 / l31; q6 = 3 * x12 * y12 / l12
    r4 = 3 * y23 ** 2 / l23; r5 = 3 * y31 ** 2 / l31; r6 = 3 * y12 ** 2 / l12

    def Hx_dxi(L2, L3):
        # derivatives of Hx wrt xi at point (Batoz 1980 standard expressions)
        return np.stack([
            P6 * (1 - 2 * L2) + (P5 - P6) * L3,
            q6 * (1 - 2 * L2) - (q5 + q6) * L3,
            -4 + 6 * (L2 + L3) + r6 * (1 - 2 * L2) - L3 * (r5 + r6),
            -P6 * (1 - 2 * L2) + L3 * (P4 + P6),
            q6 * (1 - 2 * L2) - L3 * (q6 - q4),
            -2 + 6 * L2 + r6 * (1 - 2 * L2) + L3 * (r4 - r6),
            -L3 * (P5 + P4),
            L3 * (q4 - q5),
            -L3 * (r5 - r4)], axis=1)

    def Hy_dxi(L2, L3):
        return np.stack([
            t6 * (1 - 2 * L2) + (t5 - t6) * L3,
            1 + r6 * (1 - 2 * L2) - L3 * (r5 + r6),
            -q6 * (1 - 2 * L2) + L3 * (q5 + q6),
            -t6 * (1 - 2 * L2) + L3 * (t4 + t6),
            -1 + r6 * (1 - 2 * L2) + L3 * (r4 - r6),
            -q6 * (1 - 2 * L2) - L3 * (q4 - q6),
            -L3 * (t4 + t5),
            L3 * (r4 - r5),
            -L3 * (q4 - q5)], axis=1)

    def Hx_deta(L2, L3):
        return np.stack([
            -P5 * (1 - 2 * L3) - L2 * (P6 - P5),
            q5 * (1 - 2 * L3) - L2 * (q5 + q6),
            -4 + 6 * (L2 + L3) + r5 * (1 - 2 * L3) - L2 * (r5 + r6),
            L2 * (P4 + P6),
            L2 * (q4 - q6),
            -L2 * (r6 - r4),
            P5 * (1 - 2 * L3) - L2 * (P4 + P5),
            q5 * (1 - 2 * L3) + L2 * (q4 - q5),
            -2 + 6 * L3 + r5 * (1 - 2 * L3) + L2 * (r4 - r5)], axis=1)

    def Hy_deta(L2, L3):
        return np.stack([
            -t5 * (1 - 2 * L3) - L2 * (t6 - t5),
            1 + r5 * (1 - 2 * L3) - L2 * (r5 + r6),
            -q5 * (1 - 2 * L3) + L2 * (q5 + q6),
            L2 * (t4 + t6),
            L2 * (r4 - r6),
            -L2 * (q4 - q6),
            t5 * (1 - 2 * L3) - L2 * (t4 + t5),
            -1 + r5 * (1 - 2 * L3) + L2 * (r4 - r5),
            -q5 * (1 - 2 * L3) - L2 * (q4 - q5)], axis=1)

    D = E * t ** 3 * bend_ratio / (12 * (1 - nu ** 2))
    gps = [(0.5, 0.0), (0.5, 0.5), (0.0, 0.5)]
    K = np.zeros((ne, 9, 9))
    for L2, L3 in gps:
        Bx_xi = Hx_dxi(L2, L3); Bx_eta = Hx_deta(L2, L3)
        By_xi = Hy_dxi(L2, L3); By_eta = Hy_deta(L2, L3)
        B = np.zeros((ne, 3, 9))
        B[:, 0] = (y31[:, None] * Bx_xi + y12[:, None] * Bx_eta)
        B[:, 1] = (-x31[:, None] * By_xi - x12[:, None] * By_eta)
        B[:, 2] = (-x31[:, None] * Bx_xi - x12[:, None] * Bx_eta
                   + y31[:, None] * By_xi + y12[:, None] * By_eta)
        B /= A2[:, None, None]
        Dm = np.zeros((ne, 3, 3))
        Dm[:, 0, 0] = Dm[:, 1, 1] = D
        Dm[:, 0, 1] = Dm[:, 1, 0] = nu * D
        Dm[:, 2, 2] = (1 - nu) / 2 * D
        K += np.einsum('eki,ekl,elj,e->eij', B, Dm, B, A2 / 6.0)
    # DKT DOF order is [w, thx, thy] already (Batoz convention)
    return K
