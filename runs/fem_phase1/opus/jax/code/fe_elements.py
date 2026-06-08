"""
Hand-assembled finite-element building blocks for the JAX Phase-1 hexapod model.

Everything is written in jax.numpy so the map (material/section/joint parameters)
-> (stiffness K, mass M) -> (natural frequencies) is differentiable. This is the
"future differentiable forward model" required by the task card; in Phase 1 we only
run the eigensolve (no NUTS).

Elements implemented from standard texts (independent re-derivation, nothing ported
from the CalculiX or TensorMesh builds):
  - beam3d  : 3-D Euler-Bernoulli 2-node frame element, 12 DOF, consistent mass
              (Przemieniecki, "Theory of Matrix Structural Analysis").
  - shell4  : flat rectangular shell = ACM/MZC non-conforming plate-bending (12 DOF)
              + Q4 bilinear plane-stress membrane (8 DOF), per-node DOF [u v w rx ry rz];
              drilling DOF rz carries no stiffness/mass (pruned later).
DOF convention per node: [ux, uy, uz, rx, ry, rz].
"""

import jax.numpy as jnp
import numpy as np

# ---------------------------------------------------------------------------
# 3-D Euler-Bernoulli beam (frame) element, 12 DOF, in GLOBAL coordinates.
# ---------------------------------------------------------------------------

def _beam_local_k(E, A, Iy, Iz, J, G, L):
    """12x12 local stiffness, local x along the axis."""
    k = jnp.zeros((12, 12))
    EA_L = E * A / L
    GJ_L = G * J / L
    a = E * Iz
    b = E * Iy
    # axial (ux at 0 and 6)
    k = k.at[0, 0].add(EA_L); k = k.at[6, 6].add(EA_L)
    k = k.at[0, 6].add(-EA_L); k = k.at[6, 0].add(-EA_L)
    # torsion (rx at 3 and 9)
    k = k.at[3, 3].add(GJ_L); k = k.at[9, 9].add(GJ_L)
    k = k.at[3, 9].add(-GJ_L); k = k.at[9, 3].add(-GJ_L)
    # bending about z (uy=1,7 ; rz=5,11) -> uses Iz
    c = a / L**3
    vals = {
        (1, 1): 12*c, (1, 7): -12*c, (7, 7): 12*c,
        (1, 5): 6*L*c, (1, 11): 6*L*c, (5, 7): -6*L*c, (7, 11): -6*L*c,
        (5, 5): 4*L*L*c, (11, 11): 4*L*L*c, (5, 11): 2*L*L*c,
    }
    for (i, j), v in vals.items():
        k = k.at[i, j].add(v)
        if i != j:
            k = k.at[j, i].add(v)
    # bending about y (uz=2,8 ; ry=4,10) -> uses Iy ; note sign coupling for ry
    d = b / L**3
    valsy = {
        (2, 2): 12*d, (2, 8): -12*d, (8, 8): 12*d,
        (2, 4): -6*L*d, (2, 10): -6*L*d, (4, 8): 6*L*d, (8, 10): 6*L*d,
        (4, 4): 4*L*L*d, (10, 10): 4*L*L*d, (4, 10): 2*L*L*d,
    }
    for (i, j), v in valsy.items():
        k = k.at[i, j].add(v)
        if i != j:
            k = k.at[j, i].add(v)
    return k


def _beam_local_m(rho, A, J, L):
    """12x12 consistent mass (translational + torsional rotary inertia).
    Bending rotary inertia of the slender tube is small and the standard
    consistent translational mass already couples rotations; we use the
    classic Przemieniecki consistent mass matrix."""
    m = jnp.zeros((12, 12))
    mL = rho * A * L
    # axial
    for i, j, v in [(0, 0, 1/3), (6, 6, 1/3), (0, 6, 1/6)]:
        m = m.at[i, j].add(mL*v)
        if i != j:
            m = m.at[j, i].add(mL*v)
    # torsion (polar radius of gyration r^2 = J/A)
    rx2 = J / A
    for i, j, v in [(3, 3, rx2/3), (9, 9, rx2/3), (3, 9, rx2/6)]:
        m = m.at[i, j].add(mL*v)
        if i != j:
            m = m.at[j, i].add(mL*v)
    # bending about z (uy,rz : dofs 1,5,7,11)
    cz = mL / 420.0
    Bz = {
        (1, 1): 156, (1, 5): 22*L, (1, 7): 54, (1, 11): -13*L,
        (5, 5): 4*L*L, (5, 7): 13*L, (5, 11): -3*L*L,
        (7, 7): 156, (7, 11): -22*L, (11, 11): 4*L*L,
    }
    for (i, j), v in Bz.items():
        m = m.at[i, j].add(cz*v)
        if i != j:
            m = m.at[j, i].add(cz*v)
    # bending about y (uz,ry : dofs 2,4,8,10) -- sign pattern mirrors bending-z
    cy = mL / 420.0
    By = {
        (2, 2): 156, (2, 4): -22*L, (2, 8): 54, (2, 10): 13*L,
        (4, 4): 4*L*L, (4, 8): -13*L, (4, 10): -3*L*L,
        (8, 8): 156, (8, 10): 22*L, (10, 10): 4*L*L,
    }
    for (i, j), v in By.items():
        m = m.at[i, j].add(cy*v)
        if i != j:
            m = m.at[j, i].add(cy*v)
    return m


def _triad(p1, p2):
    """local->global 3x3 rotation; columns are local x',y',z' in global."""
    x = p2 - p1
    L = jnp.linalg.norm(x)
    x = x / L
    # reference vector to build y'; use global Z unless beam ~ vertical
    ref = jnp.where(jnp.abs(x[2]) > 0.99, jnp.array([1.0, 0.0, 0.0]),
                    jnp.array([0.0, 0.0, 1.0]))
    y = jnp.cross(ref, x)
    y = y / jnp.linalg.norm(y)
    z = jnp.cross(x, y)
    R = jnp.stack([x, y, z], axis=1)  # 3x3, columns local axes in global
    return R, L


def beam3d(p1, p2, E, A, Iy, Iz, J, G, rho):
    """Return (Ke, Me) 12x12 in GLOBAL coords for a beam from p1 to p2."""
    R, L = _triad(p1, p2)
    kl = _beam_local_k(E, A, Iy, Iz, J, G, L)
    ml = _beam_local_m(rho, A, J, L)
    # 12x12 transform T (block diagonal of R^T mapping global->local)
    T = jnp.zeros((12, 12))
    Rt = R.T
    for b in range(4):
        T = T.at[3*b:3*b+3, 3*b:3*b+3].add(Rt)
    Ke = T.T @ kl @ T
    Me = T.T @ ml @ T
    return Ke, Me, L


# ---------------------------------------------------------------------------
# Flat rectangular shell = ACM plate bending (12 DOF) + Q4 membrane (8 DOF).
# Element lies in the global z = const plane; local axes == global x,y.
# Node ordering CCW: (-,-),(+,-),(+,+),(-,+). DOF per node [u v w rx ry rz].
# ---------------------------------------------------------------------------

def _acm_plate(a, b, D, nu):
    """ACM/MZC non-conforming rectangular plate-bending stiffness.
    a,b are HALF side lengths (element is 2a x 2b). Returns 12x12 in dof order
    [w1,thx1,thy1, w2,..., w4,thx4,thy4] with thx=dw/dy, thy=-dw/dx.
    Built by numeric integration of the 12-term ACM polynomial."""
    # nodal natural coords
    xn = np.array([-a, a, a, -a])
    yn = np.array([-b, -b, b, b])

    def pvec(x, y):
        return np.array([1, x, y, x*x, x*y, y*y, x**3, x*x*y, x*y*y, y**3,
                         x**3*y, x*y**3])

    def pvec_x(x, y):
        return np.array([0, 1, 0, 2*x, y, 0, 3*x*x, 2*x*y, y*y, 0,
                         3*x*x*y, y**3])

    def pvec_y(x, y):
        return np.array([0, 0, 1, 0, x, 2*y, 0, x*x, 2*x*y, 3*y*y,
                         x**3, 3*x*y*y])

    # second derivatives for curvature
    def pvec_xx(x, y):
        return np.array([0, 0, 0, 2, 0, 0, 6*x, 2*y, 0, 0, 6*x*y, 0])

    def pvec_yy(x, y):
        return np.array([0, 0, 0, 0, 0, 2, 0, 0, 2*x, 6*y, 0, 6*x*y])

    def pvec_xy(x, y):
        return np.array([0, 0, 0, 0, 1, 0, 0, 2*x, 2*y, 0, 3*x*x, 3*y*y])

    # C maps polynomial coeffs -> nodal dof [w, thx=dw/dy, thy=-dw/dx]
    C = np.zeros((12, 12))
    for i in range(4):
        C[3*i + 0, :] = pvec(xn[i], yn[i])
        C[3*i + 1, :] = pvec_y(xn[i], yn[i])      # thx = dw/dy
        C[3*i + 2, :] = -pvec_x(xn[i], yn[i])     # thy = -dw/dx
    Cinv = np.linalg.inv(C)

    # 2x2 Gauss
    g = 1.0/np.sqrt(3.0)
    gp = [(-g, -g), (g, -g), (g, g), (-g, g)]
    K = np.zeros((12, 12))
    Dm = np.array([[D, nu*D, 0], [nu*D, D, 0], [0, 0, D*(1-nu)/2.0]])
    for (xi, eta) in gp:
        x = a*xi; y = b*eta
        # curvature kappa = [-w_xx, -w_yy, -2 w_xy] = Bp * coeffs
        Bp = np.vstack([-pvec_xx(x, y), -pvec_yy(x, y), -2*pvec_xy(x, y)])
        B = Bp @ Cinv
        K += (a*b) * (B.T @ Dm @ B)   # Jacobian a*b per Gauss weight 1
    return K, Cinv


def _acm_mass(a, b, rho_t, Cinv):
    """Consistent translational mass for ACM plate (w only)."""
    g = 1.0/np.sqrt(3.0)
    gp = [(-g, -g), (g, -g), (g, g), (-g, g)]

    def pvec(x, y):
        return np.array([1, x, y, x*x, x*y, y*y, x**3, x*x*y, x*y*y, y**3,
                         x**3*y, x*y**3])

    M = np.zeros((12, 12))
    for (xi, eta) in gp:
        x = a*xi; y = b*eta
        N = (pvec(x, y) @ Cinv).reshape(1, 12)
        M += (a*b) * rho_t * (N.T @ N)
    return M


def _q4_membrane(a, b, E, nu, rho_t):
    """Q4 plane-stress membrane (u,v). a,b half-sides. Returns (K8,M8)."""
    xn = np.array([-a, a, a, -a]); yn = np.array([-b, -b, b, b])
    g = 1.0/np.sqrt(3.0)
    gp = [(-g, -g), (g, -g), (g, g), (-g, g)]
    Dm = E/(1-nu*nu)*np.array([[1, nu, 0], [nu, 1, 0], [0, 0, (1-nu)/2.0]])
    K = np.zeros((8, 8)); M = np.zeros((8, 8))
    for (xi, eta) in gp:
        dN_dxi = 0.25*np.array([-(1-eta), (1-eta), (1+eta), -(1+eta)])
        dN_deta = 0.25*np.array([-(1-xi), -(1+xi), (1+xi), (1-xi)])
        Nsh = 0.25*np.array([(1-xi)*(1-eta), (1+xi)*(1-eta),
                             (1+xi)*(1+eta), (1-xi)*(1+eta)])
        Jm = np.array([[dN_dxi @ xn, dN_dxi @ yn],
                       [dN_deta @ xn, dN_deta @ yn]])
        detJ = np.linalg.det(Jm)
        Jinv = np.linalg.inv(Jm)
        dN = Jinv @ np.vstack([dN_dxi, dN_deta])  # 2x4 -> d/dx,d/dy
        B = np.zeros((3, 8))
        for i in range(4):
            B[0, 2*i] = dN[0, i]
            B[1, 2*i+1] = dN[1, i]
            B[2, 2*i] = dN[1, i]
            B[2, 2*i+1] = dN[0, i]
        K += detJ * (B.T @ Dm @ B)
        Nmat = np.zeros((2, 8))
        for i in range(4):
            Nmat[0, 2*i] = Nsh[i]
            Nmat[1, 2*i+1] = Nsh[i]
        M += detJ * rho_t * (Nmat.T @ Nmat)
    return K, M


def shell4(a_half, b_half, E, nu, t, rho):
    """Flat rectangular shell, 24x24 (4 nodes x 6 dof [u v w rx ry rz]).
    Returns numpy (Ke, Me). rz (drilling) rows/cols are zero (pruned later).
    a_half,b_half are HALF side lengths in metres."""
    D = E*t**3/(12.0*(1-nu*nu))
    rho_t = rho*t
    Kp, Cinv = _acm_plate(a_half, b_half, D, nu)
    Mp = _acm_mass(a_half, b_half, rho_t, Cinv)
    Km, Mm = _q4_membrane(a_half, b_half, E, nu, rho_t)
    Ke = np.zeros((24, 24)); Me = np.zeros((24, 24))
    # plate dof local idx (per node): w->2, rx->3, ry->4
    pmap = [2, 3, 4]
    # membrane dof local idx: u->0, v->1
    mmap = [0, 1]
    for i in range(4):
        for j in range(4):
            for ii, pi in enumerate(pmap):
                for jj, pj in enumerate(pmap):
                    Ke[6*i+pi, 6*j+pj] += Kp[3*i+ii, 3*j+jj]
                    Me[6*i+pi, 6*j+pj] += Mp[3*i+ii, 3*j+jj]
            for ii, mi in enumerate(mmap):
                for jj, mj in enumerate(mmap):
                    Ke[6*i+mi, 6*j+mj] += Km[2*i+ii, 2*j+jj]
                    Me[6*i+mi, 6*j+mj] += Mm[2*i+ii, 2*j+jj]
    return Ke, Me
