"""
Parametric hexapod-tray FEM + EXACT analytic modal sensitivities for the
pre-test Fisher-Information (FIM) identifiability analysis.

What this module is (plain English):
  - A "forward model" maps a small vector of physical parameters theta to the
    things a vibration test can observe (natural frequencies in Hz, and mode-
    shape components at sensor locations). theta here are DIMENSIONLESS MULTIPLIERS
    on physical stiffnesses, nominal value 1.0 (e.g. theta_strutEA = 1.10 means
    "the struts are 10% axially stiffer than the nominal CAD value").
  - Because the global stiffness K(theta) is LINEAR in each theta (scaling a
    Young's modulus or a spring constant scales that block of K proportionally),
    we can split K into physically-labelled groups:
        K(theta) = sum_g theta_g * K_g  +  K_fixed
    and the derivative dK/dtheta_g is just K_g (no finite differences needed).
  - That makes the eigenvalue sensitivities EXACT (Fox-Kapoor / Nelson formulas),
    which is what the FIM needs.

Model provenance: this reuses ONLY the read-only raw inputs (inputs/spec.py) and
the element library (inputs/fe_elements.py) from the Opus Phase-1 JAX build
(runs/fem_phase1/opus/). The assembly here is re-expressed to track per-group
contributions; at theta = 1 it must reproduce that build's nominal modes
(checked in run_fim.py against runs/fem_phase1/opus/jax/results.json).

Units: SI (m, kg, N, Pa, Hz). DOF order per node: [ux, uy, uz, rx, ry, rz].
"""
import os
import sys
import numpy as np
import scipy.linalg as sla

HERE = os.path.dirname(os.path.abspath(__file__))
INPUTS = os.path.abspath(os.path.join(HERE, "..", "inputs"))
sys.path.insert(0, INPUTS)
import spec          # noqa: E402  raw shared inputs only
import fe_elements as fe  # noqa: E402

# Parameter menu (order is fixed and used everywhere downstream).
# Each is a dimensionless multiplier on a physically distinct stiffness, nominal 1.0.
PARAM_NAMES = [
    "tray_E",        # tray plate bending+membrane stiffness (scales tray Young's modulus)
    "strut_EA",      # strut AXIAL stiffness (E*A) -- the load path of a hexapod suspension
    "strut_EI",      # strut BENDING+torsion stiffness (E*I, G*J)
    "joint_axial",   # joint translational stiffness ALONG the strut axis
    "joint_lateral", # joint translational stiffness PERPENDICULAR to the strut axis
]
NP = len(PARAM_NAMES)


# ---------------------------------------------------------------------------
# Beam group-stiffness helpers (axial-only vs bending+torsion-only), reusing the
# SAME local-stiffness physics as fe_elements._beam_local_k, transformed by the
# SAME triad. Splitting lets us treat strut axial and strut bending as separate
# identifiable parameters (a thin tube can be axially observable but laterally sloppy).
# ---------------------------------------------------------------------------
def _beam_axial_local(E, A, L):
    k = np.zeros((12, 12))
    EA_L = E * A / L
    k[0, 0] += EA_L; k[6, 6] += EA_L
    k[0, 6] += -EA_L; k[6, 0] += -EA_L
    return k


def _beam_bend_local(E, Iy, Iz, J, G, L):
    k = np.zeros((12, 12))
    GJ_L = G * J / L
    k[3, 3] += GJ_L; k[9, 9] += GJ_L
    k[3, 9] += -GJ_L; k[9, 3] += -GJ_L
    a = E * Iz; c = a / L**3
    vals = {(1, 1): 12*c, (1, 7): -12*c, (7, 7): 12*c,
            (1, 5): 6*L*c, (1, 11): 6*L*c, (5, 7): -6*L*c, (7, 11): -6*L*c,
            (5, 5): 4*L*L*c, (11, 11): 4*L*L*c, (5, 11): 2*L*L*c}
    for (i, j), v in vals.items():
        k[i, j] += v
        if i != j:
            k[j, i] += v
    b = E * Iy; d = b / L**3
    valsy = {(2, 2): 12*d, (2, 8): -12*d, (8, 8): 12*d,
             (2, 4): -6*L*d, (2, 10): -6*L*d, (4, 8): 6*L*d, (8, 10): 6*L*d,
             (4, 4): 4*L*L*d, (10, 10): 4*L*L*d, (4, 10): 2*L*L*d}
    for (i, j), v in valsy.items():
        k[i, j] += v
        if i != j:
            k[j, i] += v
    return k


def _triad_np(p1, p2):
    x = np.asarray(p2) - np.asarray(p1)
    L = np.linalg.norm(x); x = x / L
    ref = np.array([1.0, 0.0, 0.0]) if abs(x[2]) > 0.99 else np.array([0.0, 0.0, 1.0])
    y = np.cross(ref, x); y = y / np.linalg.norm(y)
    z = np.cross(x, y)
    R = np.stack([x, y, z], axis=1)
    return R, L


def _beam_global(local12, R):
    T = np.zeros((12, 12))
    Rt = R.T
    for bk in range(4):
        T[3*bk:3*bk+3, 3*bk:3*bk+3] = Rt
    return T.T @ local12 @ T


# ---------------------------------------------------------------------------
def build_groups(target_h_mm=30.0):
    """Assemble M and the per-group stiffness matrices K_g (full ndof x ndof,
    numpy) plus K_fixed. Mirrors runs/fem_phase1/opus/jax build_model geometry."""
    T = spec.TRAY
    z = T["z_mid"]
    apex = spec.apex_m(); foot = spec.foot_m()

    # tray tensor grid (reuse build_jax grid logic)
    def grid1d(required, target_h):
        req = sorted(set(required)); out = [req[0]]
        for lo, hi in zip(req[:-1], req[1:]):
            n = max(1, int(round((hi - lo) / target_h)))
            for k in range(1, n + 1):
                out.append(lo + (hi - lo) * k / n)
        return np.array(sorted(set(np.round(out, 9))))

    ax = [a[0] for a in apex.values()]; ay = [a[1] for a in apex.values()]
    xs = grid1d([-T["Lx"]/2, *ax, T["Lx"]/2], target_h_mm*1e-3)
    ys = grid1d([-T["Ly"]/2, *ay, T["Ly"]/2], target_h_mm*1e-3)
    NX, NY = len(xs), len(ys)

    coords = []; nid = {}
    for j in range(NY):
        for i in range(NX):
            nid[("t", i, j)] = len(coords)
            coords.append([xs[i], ys[j], z])
    strut_nodes = {}
    for name, ak, fk in spec.STRUTS:
        nt = len(coords); coords.append(list(apex[ak])); strut_nodes[(name, "top")] = nt
        nb = len(coords); coords.append(list(foot[fk])); strut_nodes[(name, "bot")] = nb
    coords = np.array(coords)
    nn = len(coords); ndof = 6 * nn

    K_tray = np.zeros((ndof, ndof))
    K_strutAx = np.zeros((ndof, ndof))
    K_strutBend = np.zeros((ndof, ndof))
    K_jAx = np.zeros((ndof, ndof))
    K_jLat = np.zeros((ndof, ndof))
    K_fixed = np.zeros((ndof, ndof))
    M = np.zeros((ndof, ndof))

    def add(dst, Ke, node_list):
        dofs = []
        for n_ in node_list:
            dofs += list(range(6*n_, 6*n_+6))
        idx = np.array(dofs)
        dst[np.ix_(idx, idx)] += np.asarray(Ke)

    # tray shell (scales with tray_E); mass into M
    nelem_tray = 0
    for j in range(NY-1):
        for i in range(NX-1):
            a_half = (xs[i+1]-xs[i])/2.0; b_half = (ys[j+1]-ys[j])/2.0
            Ke, Me = fe.shell4(a_half, b_half, T["E"], T["nu"], T["t"], T["rho"])
            ns = [nid[("t", i, j)], nid[("t", i+1, j)],
                  nid[("t", i+1, j+1)], nid[("t", i, j+1)]]
            add(K_tray, Ke, ns); add(M, Me, ns)
            nelem_tray += 1

    # struts: split axial vs bending+torsion; mass from full consistent beam
    S = spec.STRUT
    for name, ak, fk in spec.STRUTS:
        nt = strut_nodes[(name, "top")]; nb = strut_nodes[(name, "bot")]
        R, L = _triad_np(coords[nt], coords[nb])
        Kax = _beam_global(_beam_axial_local(S["E"], S["A"], L), R)
        Kbe = _beam_global(_beam_bend_local(S["E"], S["I"], S["I"], S["J"], S["G"], L), R)
        add(K_strutAx, Kax, [nt, nb])
        add(K_strutBend, Kbe, [nt, nb])
        _, Me, _ = fe.beam3d(coords[nt], coords[nb], S["E"], S["A"],
                             S["I"], S["I"], S["J"], S["G"], S["rho"])
        add(M, np.asarray(Me), [nt, nb])

    # joint springs: split into axial (along strut) and lateral (perp) projectors
    kj = spec.JOINT["k_trans"]
    for name, ak, fk in spec.STRUTS:
        nt = strut_nodes[(name, "top")]; nb = strut_nodes[(name, "bot")]
        d = (coords[nt] - coords[nb]); d = d / np.linalg.norm(d)
        Pax = np.outer(d, d)            # axial projector (3x3)
        Plat = np.eye(3) - Pax          # lateral projector
        apex_node = nid[("t", int(np.where(xs == apex[ak][0])[0][0]),
                              int(np.where(ys == apex[ak][1])[0][0]))]
        # apex-node <-> strut-top coupling: k*[[P,-P],[-P,P]] on translational dofs
        for (Pmat, dst) in ((Pax, K_jAx), (Plat, K_jLat)):
            ai = 6*apex_node; ti = 6*nt
            dst[ai:ai+3, ai:ai+3] += kj*Pmat
            dst[ti:ti+3, ti:ti+3] += kj*Pmat
            dst[ai:ai+3, ti:ti+3] += -kj*Pmat
            dst[ti:ti+3, ai:ai+3] += -kj*Pmat
            # grounded strut-bottom translational spring (foot fixed)
            bi = 6*nb
            dst[bi:bi+3, bi:bi+3] += kj*Pmat
        # fixed tiny torsional ground about strut axis (anti-spin); NOT a parameter
        k_spin = 1.0e2
        bi3 = 6*nb+3
        K_fixed[bi3:bi3+3, bi3:bi3+3] += k_spin*np.outer(d, d)

    groups = {
        "tray_E": K_tray,
        "strut_EA": K_strutAx,
        "strut_EI": K_strutBend,
        "joint_axial": K_jAx,
        "joint_lateral": K_jLat,
    }
    meta = dict(coords=coords, nid=nid, strut_nodes=strut_nodes, xs=xs, ys=ys,
                NX=NX, NY=NY, nn=nn, ndof=ndof, nelem_tray=nelem_tray,
                apex=apex, foot=foot)
    return groups, K_fixed, M, meta


def K_of_theta(groups, K_fixed, theta):
    K = K_fixed.copy()
    for g, name in enumerate(PARAM_NAMES):
        K = K + theta[g] * groups[name]
    return K


def prune_dead(K_full, M):
    """Return free-DOF index list (drop drilling DOFs with no stiffness & no mass)."""
    ndof = K_full.shape[0]
    dK = np.abs(np.diag(K_full)); dM = np.abs(np.diag(M))
    dead = (dK < 1e-9*dK.max()) & (dM < 1e-9*dM.max())
    return np.array([d for d in range(ndof) if not dead[d]])


# ---------------------------------------------------------------------------
def solve_modes(groups, K_fixed, M, free, theta, nmodes):
    """Fixed-base modes at theta. Returns (freqs_Hz, lambda=omega^2, Phi) with Phi
    MASS-NORMALIZED (Phi^T M Phi = I), restricted to the free DOFs, shape (nfree, nmodes)."""
    K = K_of_theta(groups, K_fixed, theta)
    Kf = K[np.ix_(free, free)]; Mf = M[np.ix_(free, free)]
    # M is singular (rotational/drilling DOFs carry stiffness but no mass), so we
    # solve the equivalent problem  M v = mu K v  with the POSITIVE-DEFINITE K as the
    # "B" matrix (mirrors the Opus build_jax solver). mu = 1/omega^2; largest mu =
    # lowest frequency. scipy returns v with v^T K v = 1; rescale to mass-normalize.
    mu, V = sla.eigh(Mf, Kf)
    order = np.argsort(mu)[::-1]
    mu = mu[order]; V = V[:, order]
    good = mu > 1e-13*mu.max()
    mu = mu[good]; V = V[:, good]
    w2 = 1.0 / mu
    Phi = V * np.sqrt(w2)[None, :]      # now Phi^T M Phi = I (mass-normalized)
    f = np.sqrt(w2) / (2*np.pi)
    return f[:nmodes], w2[:nmodes], Phi[:, :nmodes]


def group_blocks(groups, free):
    """K_g restricted to free DOFs, in PARAM_NAMES order."""
    return [groups[name][np.ix_(free, free)] for name in PARAM_NAMES]


def freq_sensitivity(Kg_free, w2, Phi):
    """EXACT eigen-frequency sensitivity matrix dF[i,g] = d f_i / d theta_g  (Hz/unit).
    Eigenvalue derivative (mass-normalized modes): d(w2_i)/d theta_g = phi_i^T K_g phi_i.
    f_i = sqrt(w2_i)/(2 pi)  =>  d f_i = d(w2_i) / (4 pi sqrt(w2_i)).
    """
    nm = Phi.shape[1]; ng = len(Kg_free)
    dF = np.zeros((nm, ng))
    for g in range(ng):
        KgP = Kg_free[g] @ Phi
        for i in range(nm):
            dlam = Phi[:, i] @ KgP[:, i]
            dF[i, g] = dlam / (4*np.pi*np.sqrt(max(w2[i], 1e-30)))
    return dF


def shape_sensitivity(Kg_free, w2, Phi):
    """Modal-vector sensitivity dPhi[:, i, g] = d phi_i / d theta_g (Fox-Kapoor).
    d phi_i = sum_{k != i} [ (phi_k^T K_g phi_i) / (w2_i - w2_k) ] phi_k.
    Returns array (nfree, nmodes, nparam)."""
    nf, nm = Phi.shape; ng = len(Kg_free)
    dPhi = np.zeros((nf, nm, ng))
    for g in range(ng):
        KgP = Kg_free[g] @ Phi          # (nf, nm)
        C = Phi.T @ KgP                 # C[k,i] = phi_k^T K_g phi_i
        for i in range(nm):
            coef = np.zeros(nm)
            for k in range(nm):
                if k == i:
                    continue
                denom = w2[i] - w2[k]
                if abs(denom) < 1e-6*max(abs(w2[i]), 1.0):
                    continue            # near-degenerate: skip (documented limitation)
                coef[k] = C[k, i] / denom
            dPhi[:, i, g] = Phi @ coef
    return dPhi


def dof_index(meta, free, node, comp):
    """Position within the FREE-DOF vector of (global node, component 0..5), or None."""
    gdof = 6*node + comp
    hit = np.where(free == gdof)[0]
    return int(hit[0]) if len(hit) else None


def tray_node(meta, i, j):
    return meta["nid"][("t", i, j)]
