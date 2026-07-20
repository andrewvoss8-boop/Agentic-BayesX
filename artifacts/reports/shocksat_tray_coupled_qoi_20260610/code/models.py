"""Forward models for the ShockSat x tray coupled-QOI study.

Two physics blocks, both linear:

1) TRAY CHAIN ("load" side): the Opus hexapod tray (SI units), with all six
   feet rigidly condensed to ONE massless virtual base point at the tray-frame
   origin (single-point 6-DOF condensation, D38/A10), connected through an
   uncertain 6-DOF CBUSH (the mount, A1-A3) to the enforced-motion base DOFs
   `b` (the ShockSat side). Outputs: chain fixed-base modes, participation
   vectors, rigid mass, and the 6x6 LOAD apparent mass M_chain(omega)
   (quantity contract C2).

2) SHOCKSAT INTERFACE ("source" side): the predecessor's validated 74-mode
   ROM. K_r(theta_S) = A_fix + sum_g theta_g A_g (mass = identity). Mode-shape
   rows at the mount node P come from B_P = T[P_dofs,:] @ V_keep, converted
   snail-inch -> SI (contract C8). Output: 6x6 drive-point accelerance
   Y_S(omega) including the 6 rigid-body modes (contract C3).

Tray geometry/elements are REUSED READ-ONLY from
artifacts/reports/fim_identifiability_opus_20260609/inputs/ (spec.py,
fe_elements.py); the assembly below is adapted from that workspace's
fim_model.py (same element physics) with the grounded foot springs re-routed
to the condensation base point (this is the one structural change; verified
by reproducing the FIM nominal fixed-feet modes when the base point is
clamped and the mount is rigid -- verify.py gate V1).

Units: SI throughout this module's OUTPUTS (m, kg, N, s, Hz).
DOF order per node: [ux, uy, uz, rx, ry, rz].
"""
import json
import os
import sys
import numpy as np
import scipy.linalg as sla
import scipy.sparse as sp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
FIM_IN = os.path.join(ROOT, "artifacts", "reports",
                      "fim_identifiability_opus_20260609", "inputs")
SHK = os.path.join(ROOT, "artifacts", "reports",
                   "shocksat_fem_modal_twin_20260609")
sys.path.insert(0, FIM_IN)
import spec            # noqa: E402  (read-only shared tray inputs)
import fe_elements as fe  # noqa: E402

SNAIL2KG = 175.126835          # 1 lbf*s^2/in in kg
IN2M = 0.0254

TRAY_PARAMS = ["tray_E", "strut_EA", "strut_EI", "joint_axial", "joint_lateral"]
MOUNT_PARAMS = ["k_tx", "k_ty", "k_tz", "k_rx", "k_ry", "k_rz"]
MOUNT_NOMINAL = dict(k_tx=2.0e6, k_ty=2.0e6, k_tz=2.0e6,    # N/m   (A1)
                     k_rx=2.0e4, k_ry=2.0e4, k_rz=2.0e4)    # N*m/rad


def _skew(r):
    return np.array([[0, -r[2], r[1]], [r[2], 0, -r[0]], [-r[1], r[0], 0.0]])


# --------------------------------------------------------------------------
# beam split helpers (axial vs bending+torsion), same physics as fim_model.py
# --------------------------------------------------------------------------
def _beam_axial_local(E, A, L):
    k = np.zeros((12, 12))
    EA_L = E * A / L
    k[0, 0] = k[6, 6] = EA_L
    k[0, 6] = k[6, 0] = -EA_L
    return k


def _beam_bend_local(E, Iy, Iz, J, G, L):
    k = np.zeros((12, 12))
    GJ_L = G * J / L
    k[3, 3] = k[9, 9] = GJ_L
    k[3, 9] = k[9, 3] = -GJ_L
    c = E * Iz / L**3
    for (i, j), v in {(1, 1): 12*c, (1, 7): -12*c, (7, 7): 12*c,
                      (1, 5): 6*L*c, (1, 11): 6*L*c, (5, 7): -6*L*c,
                      (7, 11): -6*L*c, (5, 5): 4*L*L*c, (11, 11): 4*L*L*c,
                      (5, 11): 2*L*L*c}.items():
        k[i, j] += v
        if i != j:
            k[j, i] += v
    d = E * Iy / L**3
    for (i, j), v in {(2, 2): 12*d, (2, 8): -12*d, (8, 8): 12*d,
                      (2, 4): -6*L*d, (2, 10): -6*L*d, (4, 8): 6*L*d,
                      (8, 10): 6*L*d, (4, 4): 4*L*L*d, (10, 10): 4*L*L*d,
                      (4, 10): 2*L*L*d}.items():
        k[i, j] += v
        if i != j:
            k[j, i] += v
    return k


def _triad_np(p1, p2):
    x = np.asarray(p2) - np.asarray(p1)
    L = np.linalg.norm(x)
    x = x / L
    ref = np.array([1.0, 0, 0]) if abs(x[2]) > 0.99 else np.array([0.0, 0, 1])
    y = np.cross(ref, x)
    y /= np.linalg.norm(y)
    z = np.cross(x, y)
    return np.stack([x, y, z], axis=1), L


def _beam_global(local12, R):
    T = np.zeros((12, 12))
    for bk in range(4):
        T[3*bk:3*bk+3, 3*bk:3*bk+3] = R.T
    return T.T @ local12 @ T


# --------------------------------------------------------------------------
def build_tray_chain(target_h_mm=30.0):
    """Assemble the tray + base-point model ONCE (theta enters as multipliers
    on the returned per-group stiffness blocks; mount k enters via the
    base-point/b coupling pattern returned separately).

    Returns dict with:
      Kg   : {name: (nf, nf)} per-tray-group stiffness on FREE dofs
      Kfix : (nf, nf) fixed stiffness (anti-spin springs to base point)
      M    : (nf, nf) mass on free dofs
      ibase: indices (6,) of the base-point DOFs WITHIN the free-dof vector
      free : free-dof index array into the full model
      meta : geometry bookkeeping
    The mount CBUSH is NOT in these blocks; it couples ibase <-> enforced b.
    """
    T = spec.TRAY
    z = T["z_mid"]
    apex = spec.apex_m()
    foot = spec.foot_m()

    def grid1d(required, target_h):
        req = sorted(set(required))
        out = [req[0]]
        for lo, hi in zip(req[:-1], req[1:]):
            n = max(1, int(round((hi - lo) / target_h)))
            for k in range(1, n + 1):
                out.append(lo + (hi - lo) * k / n)
        return np.array(sorted(set(np.round(out, 9))))

    ax = [a[0] for a in apex.values()]
    ay = [a[1] for a in apex.values()]
    xs = grid1d([-T["Lx"]/2, *ax, T["Lx"]/2], target_h_mm*1e-3)
    ys = grid1d([-T["Ly"]/2, *ay, T["Ly"]/2], target_h_mm*1e-3)
    NX, NY = len(xs), len(ys)

    coords, nid = [], {}
    for j in range(NY):
        for i in range(NX):
            nid[("t", i, j)] = len(coords)
            coords.append([xs[i], ys[j], z])
    strut_nodes = {}
    for name, ak, fk in spec.STRUTS:
        nt = len(coords); coords.append(list(apex[ak])); strut_nodes[(name, "top")] = nt
        nb = len(coords); coords.append(list(foot[fk])); strut_nodes[(name, "bot")] = nb
    BASE = len(coords)
    coords.append([0.0, 0.0, 0.0])            # condensation base point (A10)
    coords = np.array(coords)
    nn = len(coords)
    ndof = 6 * nn

    K = {g: np.zeros((ndof, ndof)) for g in TRAY_PARAMS}
    Kfix = np.zeros((ndof, ndof))
    M = np.zeros((ndof, ndof))

    def add(dst, Ke, node_list):
        dofs = np.concatenate([np.arange(6*n_, 6*n_+6) for n_ in node_list])
        dst[np.ix_(dofs, dofs)] += np.asarray(Ke)

    # tray shells
    for j in range(NY-1):
        for i in range(NX-1):
            a_half = (xs[i+1]-xs[i])/2
            b_half = (ys[j+1]-ys[j])/2
            Ke, Me = fe.shell4(a_half, b_half, T["E"], T["nu"], T["t"], T["rho"])
            ns = [nid[("t", i, j)], nid[("t", i+1, j)],
                  nid[("t", i+1, j+1)], nid[("t", i, j+1)]]
            add(K["tray_E"], Ke, ns)
            add(M, Me, ns)

    # struts (axial / bending split) + consistent beam mass
    S = spec.STRUT
    for name, ak, fk in spec.STRUTS:
        nt = strut_nodes[(name, "top")]
        nb = strut_nodes[(name, "bot")]
        R, L = _triad_np(coords[nt], coords[nb])
        add(K["strut_EA"], _beam_global(_beam_axial_local(S["E"], S["A"], L), R), [nt, nb])
        add(K["strut_EI"], _beam_global(
            _beam_bend_local(S["E"], S["I"], S["I"], S["J"], S["G"], L), R), [nt, nb])
        _, Me, _ = fe.beam3d(coords[nt], coords[nb], S["E"], S["A"],
                             S["I"], S["I"], S["J"], S["G"], S["rho"])
        add(M, np.asarray(Me), [nt, nb])

    # joint springs: apex<->strut-top exactly as fim_model;
    # strut-bottom<->BASE POINT (rigid offset map) replaces the grounding.
    kj = spec.JOINT["k_trans"]
    for name, ak, fk in spec.STRUTS:
        nt = strut_nodes[(name, "top")]
        nb = strut_nodes[(name, "bot")]
        d = coords[nt] - coords[nb]
        d /= np.linalg.norm(d)
        Pax = np.outer(d, d)
        Plat = np.eye(3) - Pax
        apex_node = nid[("t", int(np.where(xs == apex[ak][0])[0][0]),
                              int(np.where(ys == apex[ak][1])[0][0]))]
        r_f = coords[nb] - coords[BASE]       # foot position rel. base point
        Rf = np.hstack([np.eye(3), -_skew(r_f)])     # u_foot = Rf @ u_base6
        for Pmat, dst in ((Pax, K["joint_axial"]), (Plat, K["joint_lateral"])):
            ai, ti, bi, gi = 6*apex_node, 6*nt, 6*nb, 6*BASE
            kP = kj * Pmat
            # apex <-> strut top
            dst[ai:ai+3, ai:ai+3] += kP
            dst[ti:ti+3, ti:ti+3] += kP
            dst[ai:ai+3, ti:ti+3] -= kP
            dst[ti:ti+3, ai:ai+3] -= kP
            # strut bottom <-> base point (through rigid offset)
            dst[bi:bi+3, bi:bi+3] += kP
            dst[bi:bi+3, gi:gi+6] -= kP @ Rf
            dst[gi:gi+6, bi:bi+3] -= Rf.T @ kP
            dst[gi:gi+6, gi:gi+6] += Rf.T @ kP @ Rf
        # tiny anti-spin about strut axis: bottom rotation vs base rotation
        k_spin = 1.0e2
        bi3, gi3 = 6*nb+3, 6*BASE+3
        kS = k_spin * np.outer(d, d)
        Kfix[bi3:bi3+3, bi3:bi3+3] += kS
        Kfix[bi3:bi3+3, gi3:gi3+3] -= kS
        Kfix[gi3:gi3+3, bi3:bi3+3] -= kS
        Kfix[gi3:gi3+3, gi3:gi3+3] += kS

    # prune dead DOFs (no stiffness, no mass) -- base-point dofs all have
    # stiffness (joint springs + later the mount), so they survive.
    Kall = Kfix + sum(K.values())
    dK = np.abs(np.diag(Kall))
    dM = np.abs(np.diag(M))
    alive = ~((dK < 1e-9*dK.max()) & (dM < 1e-9*dM.max()))
    free = np.where(alive)[0]
    ibase = np.searchsorted(free, np.arange(6*BASE, 6*BASE+6))
    assert np.all(free[ibase] == np.arange(6*BASE, 6*BASE+6))

    out = dict(
        Kg={g: K[g][np.ix_(free, free)] for g in TRAY_PARAMS},
        Kfix=Kfix[np.ix_(free, free)],
        M=M[np.ix_(free, free)],
        ibase=ibase, free=free,
        meta=dict(coords=coords, nid=nid, strut_nodes=strut_nodes,
                  xs=xs, ys=ys, NX=NX, NY=NY, BASE=BASE,
                  # rigid-body mass = 1^T M_xx 1 (consistent mass: NOT the trace)
                  mass_total=float(np.sum(M[0::6, 0::6]))),
    )
    return out


def chain_modal(tray, theta_T=None, kmount=None, zeta_struct=0.01,
                zeta_mount_ref=0.05, n_keep=None, fmax_keep=np.inf):
    """Fixed-base (enforced-motion) modal data of the CBUSH+tray chain.

    Base `b` = the source-side CBUSH end (6 enforced DOFs). The CBUSH couples
    b to the base point: K_m = diag(kmount). Returns dict with chain
    frequencies f_k [Hz], participation Gamma (nm,6) [phi^T M Psi], rigid mass
    M_rb (6x6) about b, modal damping zeta_k, and the completeness defect.

    M_chain(omega) = M_rb + sum_k Gamma_k Gamma_k^T w^2/(wk^2-w^2+2i z wk w)
    (contract C2).
    """
    theta_T = theta_T or {}
    km = dict(MOUNT_NOMINAL)
    km.update(kmount or {})
    kdiag = np.array([km[p] for p in MOUNT_PARAMS])

    Kff = tray["Kfix"].copy()
    for g in TRAY_PARAMS:
        Kff = Kff + float(theta_T.get(g, 1.0)) * tray["Kg"][g]
    ib = tray["ibase"]
    Kff[ib, ib] += kdiag                      # mount spring, b clamped
    Kfb = np.zeros((Kff.shape[0], 6))
    Kfb[ib, np.arange(6)] = -kdiag
    Mff = tray["M"]

    # static constraint modes and rigid mass about b
    Psi = -sla.solve(Kff, Kfb, assume_a="pos")
    M_rb = Psi.T @ Mff @ Psi

    # modes: solve M v = mu K v (K positive definite with b clamped; M singular
    # because rotational/drilling dofs carry no mass) -- same trick as the
    # predecessor FIM model.
    mu, V = sla.eigh(Mff, Kff)
    order = np.argsort(mu)[::-1]
    mu, V = mu[order], V[:, order]
    good = mu > 1e-12 * mu.max()
    mu, V = mu[good], V[:, good]
    w2 = 1.0 / mu
    Phi = V * np.sqrt(w2)[None, :]            # mass-normalized
    f = np.sqrt(w2) / (2*np.pi)

    Gamma = Phi.T @ (Mff @ Psi)               # (nm, 6)
    completeness = np.linalg.norm(Gamma.T @ Gamma - M_rb) / np.linalg.norm(M_rb)

    # damping model (A3/D5): PHYSICAL viscous dashpot across the mount (rank-6,
    # handled EXACTLY in apparent_mass via a Woodbury identity -- no diagonal
    # modal-damping approximation) + diagonal structural modal damping
    # zeta_struct on the chain modes. Dashpot sized on NOMINAL mount + tray
    # rigid properties (documented; damping-sweep arm varies it).
    m_t = M_rb[2, 2]
    I_eq = np.mean(np.diag(M_rb)[3:])
    c_t = 2*zeta_mount_ref*np.sqrt(np.array([MOUNT_NOMINAL[p] for p in MOUNT_PARAMS[:3]])*m_t)
    c_r = 2*zeta_mount_ref*np.sqrt(np.array([MOUNT_NOMINAL[p] for p in MOUNT_PARAMS[3:]])*I_eq)
    cdiag = np.concatenate([c_t, c_r])
    phi_b = Phi[ib, :]                        # (6, nm) base-point rows
    # EFFECTIVE per-mode zeta (diagonal projection) -- used only as the
    # "informed analyst" Q for the SRS/Miles methods and for reporting:
    zeta_k = zeta_struct + np.einsum("ik,i,ik->k", phi_b, cdiag, phi_b)/(2*np.sqrt(w2))

    keep = f <= fmax_keep
    if n_keep:
        keep[np.cumsum(keep) > n_keep] = False
    return dict(f=f[keep], w2=w2[keep], Gamma=Gamma[keep], zeta=zeta_k[keep],
                M_rb=M_rb, completeness=float(completeness),
                Phi=Phi[:, keep], Psi=Psi, ibase=ib, cdiag=cdiag,
                U=phi_b.T[keep],              # (nm, 6) dashpot coupling rows
                zeta_struct=float(zeta_struct),
                f_all=f, Gamma_all=Gamma)


def apparent_mass(chain, freqs_hz):
    """LOAD apparent mass M_chain(omega) (nf,6,6) complex (contract C2).

    EXACT damped modal form: with D0 = diag(wk^2 - w^2 + 2i zeta_struct wk w)
    and the rank-6 mount dashpot C = U c U^T (U = mode rows at the base
    point), the enforced-motion solution gives
      M(w) = M_rb + w^2 [ G^T D0i G - (G^T D0i U)(c^-1/(iw) + U^T D0i U)^-1 (U^T D0i G) ]
    (Woodbury on (D0 + iw U c U^T)^-1). Verified against the direct
    dynamic-stiffness evaluation (verify.py V6)."""
    w = 2*np.pi*np.asarray(freqs_hz)
    nz = w > 0
    wnz = w[nz]
    wk2 = chain["w2"][:, None]
    wk = np.sqrt(chain["w2"])[:, None]
    zs = chain["zeta_struct"]
    G = chain["Gamma"]                        # (nm, 6)
    U = chain["U"]                            # (nm, 6)
    c = chain["cdiag"]
    # tiny zeta floor guards the zs=0 exact-resonance singularity of the
    # Woodbury SPLIT (the combined result is finite); production zs >= 0.005
    D0i = 1.0 / (wk2 - wnz**2 + 2j*(zs + 1e-9)*wk*wnz)   # (nm, nfnz)
    GtDG = np.einsum("kf,ki,kj->fij", D0i, G, G)
    GtDU = np.einsum("kf,ki,kj->fij", D0i, G, U)
    UtDU = np.einsum("kf,ki,kj->fij", D0i, U, U)
    inner = np.diag(1.0/c)[None]/(1j*wnz)[:, None, None] + UtDU
    corr = GtDU @ np.linalg.solve(inner, np.swapaxes(GtDU, 1, 2))
    Mc = np.empty((len(w), 6, 6), complex)
    Mc[nz] = chain["M_rb"][None] + (wnz**2)[:, None, None]*(GtDG - corr)
    Mc[~nz] = chain["M_rb"][None]
    return Mc


def apparent_mass_direct(tray, theta_T, kmount, freqs_hz, cdiag=None,
                         Km6=None):
    """Direct dynamic-stiffness evaluation of M_chain at a few frequencies
    (verification of the modal form; full C matrix for the mount dashpot,
    no structural damping). F_b = (D_bb - D_bf D_ff^-1 D_fb) u_b ; M = F/a.
    Km6: optional FULL 6x6 mount stiffness (overnight truth model with
    off-diagonal coupling, D10/A21); default = diagonal from kmount."""
    if Km6 is not None:
        Km = np.asarray(Km6, float)
    else:
        km = dict(MOUNT_NOMINAL)
        km.update(kmount or {})
        Km = np.diag([km[p] for p in MOUNT_PARAMS])
    theta_T = theta_T or {}
    Kff0 = tray["Kfix"].copy()
    for g in TRAY_PARAMS:
        Kff0 = Kff0 + float(theta_T.get(g, 1.0)) * tray["Kg"][g]
    ib = tray["ibase"]
    n = Kff0.shape[0]
    Kff0[np.ix_(ib, ib)] += Km
    Mff = tray["M"]
    if cdiag is None:
        cdiag = np.zeros(6)
    out = np.zeros((len(freqs_hz), 6, 6), complex)
    for q, fhz in enumerate(freqs_hz):
        w = 2*np.pi*fhz
        Sm = Km + 1j*w*np.diag(cdiag)
        Dff = (Kff0 - w**2*Mff).astype(complex)
        Dff[ib, ib] += 1j*w*cdiag
        Dfb = np.zeros((n, 6), complex)
        Dfb[ib, :] = -Sm
        uf = np.linalg.solve(Dff, Dfb)
        out[q] = (Sm - Dfb.T @ uf) / (-w**2)
    return out


# --------------------------------------------------------------------------
# ShockSat source side
# --------------------------------------------------------------------------
class ShockSatInterface:
    """74-mode ROM drive-point accelerance at the mount node P (contract C3).

    All OUTPUT quantities SI. theta_S = dict or vector over the 9 sorted
    group names (gnames)."""

    def __init__(self, node_gid=None):
        rb = np.load(os.path.join(SHK, "matrices", "reduced_blocks.npz"))
        self.gnames = [str(g) for g in rb["gnames"]]
        self.A = rb["A"]                      # (9,74,74)
        self.A_fix = rb["A_fix"]
        fm = np.load(os.path.join(SHK, "fem_model.npz"), allow_pickle=True)
        self.gids = fm["gids"]
        self.xyz = fm["xyz"]                  # inches
        self.gfile = fm["gfile"]
        eig = np.load(os.path.join(SHK, "matrices", "eigvals.npy"))
        self.lam_rbm = eig[:6]                # (rad/s)^2, suspension-level
        if node_gid is None:
            node_gid = self.pick_top_center_node()
        self.node_gid = int(node_gid)
        self._load_rows()
        self._damping()

    def pick_top_center_node(self):
        m = self.gfile == "Top_Circular_Plate"
        xyz = self.xyz[m]
        zmax = xyz[:, 2].max()
        top = m & (self.xyz[:, 2] > zmax - 1e-3)
        idx = np.where(top)[0]
        r = np.hypot(self.xyz[idx, 0], self.xyz[idx, 1])
        return int(self.gids[idx[np.argmin(r)]])

    def pick_top_edge_node(self):
        m = self.gfile == "Top_Circular_Plate"
        zmax = self.xyz[m][:, 2].max()
        top = m & (self.xyz[:, 2] > zmax - 1e-3)
        idx = np.where(top)[0]
        r = np.hypot(self.xyz[idx, 0], self.xyz[idx, 1])
        return int(self.gids[idx[np.argmax(r)]])

    def _load_rows(self):
        T = sp.load_npz(os.path.join(SHK, "matrices", "T.npz")).tocsr()
        V = np.load(os.path.join(SHK, "matrices", "V_keep.npy"), mmap_mode="r")
        g2i = {int(g): i for i, g in enumerate(self.gids)}
        i = g2i[self.node_gid]
        rows = T[6*i:6*i+6, :]                # (6, n_keep) sparse
        B = np.asarray(rows @ V)              # (6, 80) snail-inch normalized
        # snail-inch -> SI (contract C8)
        s = np.ones(6) / np.sqrt(SNAIL2KG)
        s[3:] /= IN2M
        B = B * s[:, None]
        self.B_rbm = B[:, :6]                 # (6,6)  theta-independent
        self.B_el = B[:, 6:]                  # (6,74) nominal elastic basis
        self.node_xyz_in = self.xyz[i].copy()

    def _damping(self):
        mm = np.load(os.path.join(SHK, "measured_modes.npz"))
        pairing = json.load(open(os.path.join(SHK, "pairing.json")))
        damp = mm["damp"]                     # fraction of critical, per test mode
        med = float(np.median(damp))
        z = np.full(74, med)
        for p in pairing["pairs"]:
            mi = int(p["model_mode"])
            if 0 <= mi < 74:
                z[mi] = float(damp[int(p["test_mode"]) - 1])
        self.zeta_el = z                      # by NOMINAL mode index (A5)
        self.zeta_rbm = np.full(6, 0.02)
        self.zeta_med = med

    def modes(self, theta_S=None):
        """theta_S dict/vec -> (lam (74,), phi_P (6,74) SI)."""
        if theta_S is None:
            th = np.ones(9)
        elif isinstance(theta_S, dict):
            th = np.array([theta_S.get(g, 1.0) for g in self.gnames])
        else:
            th = np.asarray(theta_S, float)
        K = self.A_fix + np.einsum("g,gij->ij", th, self.A)
        lam, Q = np.linalg.eigh(K)
        return lam, self.B_el @ Q

    def accelerance(self, freqs_hz, theta_S=None, zeta_scale=1.0):
        """Y_S(omega) (nf,6,6) complex, (m/s^2)/N, free-free, contract C3.
        Damping is assigned by sorted mode index (A5 approximation)."""
        lam, phiP = self.modes(theta_S)
        lam_all = np.concatenate([self.lam_rbm, lam])
        phi_all = np.hstack([self.B_rbm, phiP])           # (6, 80)
        zet = np.concatenate([self.zeta_rbm, self.zeta_el]) * zeta_scale
        w = 2*np.pi*np.asarray(freqs_hz)
        wk = np.sqrt(np.clip(lam_all, 1e-12, None))[:, None]
        D = (-w**2) / (lam_all[:, None] - w**2 + 2j*zet[:, None]*wk*w)
        return np.einsum("kf,ik,jk->fij", D, phi_all, phi_all)

    def rigid_mass_check(self):
        """Verify Sum_RBM phi phi^T at P == rigid accelerance from geometry
        (gate V3). Returns dict of the two 6x6s (SI) and rel error."""
        Mfull = sp.load_npz(os.path.join(SHK, "matrices", "M.npz")).tocsr()
        n = len(self.gids)
        P = self.node_xyz_in
        r = self.xyz - P[None, :]             # (n,3) inches
        R = np.zeros((6*n, 6))
        for c in range(3):                    # translations
            R[c::6, c] = 1.0
            R[3+c::6, 3+c] = 1.0              # rotations
        # u_trans = u_P + theta x r  ->  -skew(r) block
        R[0::6, 4] = r[:, 2]; R[0::6, 5] = -r[:, 1]
        R[1::6, 3] = -r[:, 2]; R[1::6, 5] = r[:, 0]
        R[2::6, 3] = r[:, 1]; R[2::6, 4] = -r[:, 0]
        Mrb = R.T @ (Mfull @ R)               # snail-inch units
        # convert to SI: translations kg, coupling kg*m, rotary kg*m^2
        s = np.ones(6)
        s[3:] = IN2M
        Mrb_SI = Mrb * SNAIL2KG * np.outer(s, s)
        Y_rigid = np.linalg.inv(Mrb_SI)                   # = R_P Mrb^-1 R_P^T at P
        Y_rbm = self.B_rbm @ self.B_rbm.T
        err = np.linalg.norm(Y_rbm - Y_rigid) / np.linalg.norm(Y_rigid)
        return dict(Y_rigid=Y_rigid, Y_rbm=Y_rbm, rel_err=float(err),
                    mass_kg=float(Mrb_SI[0, 0]))


def couple_fbs(Mchain, Ys, a_free):
    """F_cpl(omega) = (I + M_chain Y_S)^-1 M_chain a_free  (contract C5).
    Mchain, Ys: (nf,6,6); a_free: (nf,6). Returns (F_unc, F_cpl) (nf,6)."""
    F_unc = np.einsum("fij,fj->fi", Mchain, a_free)
    n = Mchain.shape[-1]
    A = np.eye(n)[None] + Mchain @ Ys
    F_cpl = np.linalg.solve(A, F_unc[:, :, None])[:, :, 0]
    return F_unc, F_cpl
