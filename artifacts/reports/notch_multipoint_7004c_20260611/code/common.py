"""
Shared models for the 7004C multi-point/6-DOF teaching study.

Workspace: artifacts/reports/notch_multipoint_7004c_20260611/
All parameter values trace to assumptions_ledger.md (A*, B*, C*, D* tags).
Quantity conventions trace to quantity_contracts.md (Q1..Q9).
No randomness anywhere: deterministic frequency-domain linear dynamics.
"""
import json
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
FIG = os.path.join(WS, "figures")
RES = os.path.join(WS, "results")

# ----------------------------------------------------------------------------
# EX-A : nondimensional TDOF system of 7004C Figure 7/9 (ledger A1-A5)
# ----------------------------------------------------------------------------
QA = 50.0          # A3
M1 = M2 = 1.0      # A1
K1 = K2 = 1.0      # A2  -> omega0 = 1


def sdof_free_acceleration(r, Q=QA):
    """Q3/Fig 9a: source base-driven transmissibility As/Ao, load disconnected.
    r = omega/omega0."""
    return (1 + 1j * r / Q) / (1 - r**2 + 1j * r / Q)


def source_apparent_mass(r, m=M1, Q=QA):
    """Q1/Fig 9b: F/a at interface, base fixed, load off: m*(1-r^2+ir/Q)/(-r^2)
    (complex; magnitude has min ~ m/Q at r=1, stiffness line ~1/r^2 below)."""
    return m * (1 - r**2 + 1j * r / Q) / (-(r**2))


def load_apparent_mass(r, m=M2, Q=QA):
    """Q2/Fig 9c: F/a at the moving base of a fixed-base SDOF load:
    m*(1+ir/Q)/(1-r^2+ir/Q). Peak ~ m*Q at r=1; -> m as r->0."""
    return m * (1 + 1j * r / Q) / (1 - r**2 + 1j * r / Q)


def coupled_interface(r, Q=QA):
    """Q3 (7004C Eq 3/4): A = As*Ms/(Ms+Ml), F = As*Ms*Ml/(Ms+Ml)."""
    As = sdof_free_acceleration(r, Q)
    Ms = source_apparent_mass(r, M1, Q)
    Ml = load_apparent_mass(r, M2, Q)
    A = As * Ms / (Ms + Ml)
    F = As * Ms * Ml / (Ms + Ml)
    return As, Ms, Ml, A, F


def simple_tdfl_normalized_force(mass_ratio, Q2):
    """7004C Appendix B (Eq B1+B2): max normalized force PSD SFF/(SAA*m2^2)
    evaluated at the LOWER coupled resonance of the tuned (omega1=omega2) system."""
    mr = np.asarray(mass_ratio, dtype=float)
    r2_low = 1 + mr / 2 - np.sqrt(mr + mr**2 / 4)          # Eq B1, lower root of (w/w0)^2
    return (1 + r2_low / Q2**2) / ((1 - r2_low) ** 2 + r2_low / Q2**2)  # Eq B2


# ----------------------------------------------------------------------------
# EX-B : rigid box payload on 4 feet (ledger B1-B8). SI units.
# DOF order (payload, about CG): [x, y, z, thx, thy, thz]
# Interface reference point O = foot-plan centroid AT THE FOOT PLANE (Q4).
# ----------------------------------------------------------------------------
M_PAY = 6.0                      # B1, kg
LBOX = (0.30, 0.24, 0.20)        # B2, m
H_CG = 0.08                      # B3, m (CG height above foot plane)
AX, AY = 0.09, 0.07              # B4, m (foot plan half-spacing rel. centroid)
KZ_FOOT = 8.52e5                 # B5, N/m
KXY_FOOT = 6.0e5                 # B6, N/m
ETA = 0.04                       # B7, hysteretic loss factor (Q=25)


def box_inertia(m=M_PAY, dims=LBOX):
    Lx, Ly, Lz = dims
    return np.diag([m / 12 * (Ly**2 + Lz**2),
                    m / 12 * (Lx**2 + Lz**2),
                    m / 12 * (Lx**2 + Ly**2)])


def skew(v):
    x, y, z = v
    return np.array([[0., -z, y], [z, 0., -x], [-y, x, 0.]])


def payload_6dof_matrices(ex=0.0, hysteretic=True):
    """Mass (about CG) and foot-spring stiffness mapped to CG DOFs, plus the
    per-foot Jacobians. ex = CG plan offset (D1, EX-D): feet keep plan positions
    about the FOOT CENTROID; CG sits at (+ex, 0, +H_CG) relative to O.

    Returns dict with M (6x6), K (6x6 complex if hysteretic), feet (list of
    dicts: r_cg (vector CG->foot), J (3x6 foot displacement = J @ q_cg),
    k_diag (3,)), and O->CG offset r_ocg.
    """
    Mrb = np.zeros((6, 6))
    Mrb[:3, :3] = M_PAY * np.eye(3)
    Mrb[3:, 3:] = box_inertia()
    kdiag = np.array([KXY_FOOT, KXY_FOOT, KZ_FOOT])
    kfac = (1 + 1j * ETA) if hysteretic else 1.0
    feet = []
    K = np.zeros((6, 6), dtype=complex)
    for sx in (+1, -1):
        for sy in (+1, -1):
            r_o = np.array([sx * AX, sy * AY, 0.0])          # foot rel O
            r_cg = r_o - np.array([ex, 0.0, H_CG])           # foot rel CG
            J = np.hstack([np.eye(3), -skew(r_cg)])          # u_foot = u_cg + th x r
            Kf = J.T @ np.diag(kdiag * kfac) @ J
            K += Kf
            feet.append(dict(r_o=r_o, r_cg=r_cg, J=J, k_diag=kdiag))
    return dict(M=Mrb, K=K, feet=feet, r_ocg=np.array([ex, 0.0, H_CG]))


def transform_O_from_CG(r_ocg):
    """6x6 rigid kinematic transform T: u_CG = T @ u_O (O = interface ref point).
    u_CG = u_O + th x r_ocg ; th_CG = th_O."""
    T = np.eye(6)
    T[:3, 3:] = -skew(r_ocg)
    return T


def apparent_mass_matrix_6dof(freqs_hz, ex=0.0):
    """Q4: 6x6 interface apparent mass about O for uniform base motion.
    Base motion u_b (6, about O) -> foot base displacement via foot Jacobians
    about O. Payload eq: (-w^2 M_cg + K_cg) u = Kc u_b ; foot spring forces ->
    resultant about O. Returns (nf, 6, 6) complex array (units kg / kg*m / kg*m^2)."""
    p = payload_6dof_matrices(ex=ex)
    M, K, feet = p["M"], p["K"], p["feet"]
    # coupling: base DOFs about O move feet rigidly: u_foot_base = JO @ u_b
    out = np.zeros((len(freqs_hz), 6, 6), dtype=complex)
    JOs, Js, kfs = [], [], []
    kfac = (1 + 1j * ETA)
    for f in feet:
        JO = np.hstack([np.eye(3), -skew(f["r_o"])])
        JOs.append(JO); Js.append(f["J"]); kfs.append(np.diag(f["k_diag"] * kfac))
    Kc = sum(J.T @ kf @ JO for J, kf, JO in zip(Js, kfs, JOs))   # CG <- base
    for i, fh in enumerate(freqs_hz):
        w = 2 * np.pi * fh
        u = np.linalg.solve(K - w**2 * M, Kc @ np.eye(6))        # u_cg per unit u_b
        # interface force on payload from feet springs, resolved about O
        F = np.zeros((6, 6), dtype=complex)
        for J, kf, JO in zip(Js, kfs, JOs):
            df = kf @ (JO @ np.eye(6) - J @ u)                   # spring force on payload
            F[:3, :] += df
            F[3:, :] += skew_apply_moment(JO, df)
        # F = force on payload per unit base displacement; apparent mass = F / a_b
        # a_b = -w^2 u_b  -> M_app = F / (-w^2)
        out[i] = F / (-(w**2))
    return out


def skew_apply_moment(JO, df):
    """Moment about O of foot force df applied at the foot position encoded in JO.
    JO[:3,3:] = -skew(r_o) -> recover r_o."""
    S = -JO[:3, 3:]
    r = np.array([S[2, 1], S[0, 2], S[1, 0]])
    return np.cross(r, df.T).T if df.ndim == 2 else np.cross(r, df)


# ----------------------------------------------------------------------------
# EX-C/D : simply supported plate source (ledger C1-C8)
# ----------------------------------------------------------------------------
E_PL, NU_PL, RHO_PL = 70e9, 0.3, 2700.0
LX, LY, TPL = 1.0, 0.8, 0.005
ZETA_PL = 0.02
FEET_CENTROID = (0.55, 0.45)     # C3
FORCE_PT = (0.18, 0.62)          # C5


def plate_modes(fmax_hz, lx=LX, ly=LY, t=TPL):
    """Analytic SS plate modes: shapes phi_mn(x,y)=sin(m pi x/lx) sin(n pi y/ly),
    unit-modal-mass normalization handled via Nmn = rho*t*lx*ly/4."""
    D = E_PL * t**3 / (12 * (1 - NU_PL**2))
    rt = RHO_PL * t
    modes = []
    m = 1
    while True:
        f_m1 = (np.pi / 2) * np.sqrt(D / rt) * ((m / lx) ** 2 + (1 / ly) ** 2)
        if f_m1 > fmax_hz and m > 1:
            break
        n = 1
        while True:
            f = (np.pi / 2) * np.sqrt(D / rt) * ((m / lx) ** 2 + (n / ly) ** 2)
            if f > fmax_hz:
                break
            modes.append((m, n, f))
            n += 1
        m += 1
    modes.sort(key=lambda t_: t_[2])
    return modes, D, rt


def phi(m, n, x, y, lx=LX, ly=LY):
    return np.sin(m * np.pi * x / lx) * np.sin(n * np.pi * y / ly)


def plate_modal_system(fmax_modes_hz, t=TPL):
    """Return modal data dict: freqs (rad/s), generalized mass (=rho t lx ly/4),
    and shape evaluators at arbitrary points."""
    modes, D, rt = plate_modes(fmax_modes_hz, t=t)
    mn = np.array([(m, n) for m, n, _ in modes])
    wn = 2 * np.pi * np.array([f for _, _, f in modes])
    mgen = rt * LX * LY / 4.0
    return dict(mn=mn, wn=wn, mgen=mgen, D=D, rt=rt, n_modes=len(modes))


def phi_matrix(sysd, pts):
    """(npts, n_modes) mode-shape matrix at pts [(x,y), ...] (vectorized)."""
    mn = np.asarray(sysd["mn"], dtype=float)
    pts = np.asarray(pts, dtype=float)
    x = pts[:, 0][:, None]
    y = pts[:, 1][:, None]
    return np.sin(x * mn[None, :, 0] * np.pi / LX) * \
           np.sin(y * mn[None, :, 1] * np.pi / LY)


def foot_points(centroid=FEET_CENTROID, ax=AX, ay=AY):
    cx, cy = centroid
    return [(cx + sx * ax, cy + sy * ay) for sx in (+1, -1) for sy in (+1, -1)]
    # order matches payload_6dof_matrices loop: (+,+), (+,-), (-,+), (-,-)


def payload_vertical_3dof(ex=0.0):
    """EX-C/D payload subset: q_p = [z, thx, thy] about CG; feet transmit vertical
    force only (ledger C4). Foot vertical displacement = z + thx*(y_f) - thy*(x_f)
    with (x_f, y_f) = foot position relative CG plan position.
    Returns Mp (3x3), foot lever matrix Lp (4x3): w_foot_top = Lp @ q_p."""
    Mp = np.diag([M_PAY, box_inertia()[0, 0], box_inertia()[1, 1]])
    Lp = np.zeros((4, 3))
    for i, (sx, sy) in enumerate([(+1, +1), (+1, -1), (-1, +1), (-1, -1)]):
        xf = sx * AX - ex          # foot rel CG (plan)
        yf = sy * AY
        Lp[i] = [1.0, yf, -xf]
    return Mp, Lp


def coupled_plate_payload_frf(freqs_hz, sysd, ex=0.0, drive="force",
                              kz=KZ_FOOT, eta=ETA, zeta_pl=ZETA_PL):
    """Assemble coupled (plate modal + 3-DOF payload) FRFs.

    drive="force": unit point force at FORCE_PT on the plate (flight-like, C5).
    drive="base": unit base acceleration shaking the plate? not used; EX-D test
                  case uses payload_on_shaker() instead.

    Returns dict of complex responses per frequency:
      qm   (nf, n_modes) plate modal displacement
      qp   (nf, 3)       payload [z, thx, thy] about CG
      Ffoot(nf, 4)       vertical spring force ON PAYLOAD (+up) per foot
      wfeet(nf, 4)       plate displacement at feet
    """
    wn, mgen = sysd["wn"], sysd["mgen"]
    nm = len(wn)
    fp = foot_points()
    Phi_f = phi_matrix(sysd, fp)                 # (4, nm)
    Phi_d = phi_matrix(sysd, [FORCE_PT])         # (1, nm)
    Mp, Lp = payload_vertical_3dof(ex=ex)
    kc = kz * (1 + 1j * eta)
    nf = len(freqs_hz)
    qm = np.zeros((nf, nm), dtype=complex)
    qp = np.zeros((nf, 3), dtype=complex)
    Ff = np.zeros((nf, 4), dtype=complex)
    wf = np.zeros((nf, 4), dtype=complex)
    Kpp = kc * (Lp.T @ Lp)                       # payload-side spring stiffness
    for i, fh in enumerate(freqs_hz):
        w = 2 * np.pi * fh
        Dm = mgen * (wn**2 - w**2 + 2j * zeta_pl * wn * w)   # plate modal dynamic stiffness
        # coupled system in [qm (nm), qp (3)]:
        A = np.zeros((nm + 3, nm + 3), dtype=complex)
        A[:nm, :nm] = np.diag(Dm) + kc * (Phi_f.T @ Phi_f)
        A[:nm, nm:] = -kc * (Phi_f.T @ Lp)
        A[nm:, :nm] = -kc * (Lp.T @ Phi_f)
        A[nm:, nm:] = -w**2 * Mp + Kpp
        b = np.zeros(nm + 3, dtype=complex)
        b[:nm] = Phi_d[0]                        # unit point force projection
        sol = np.linalg.solve(A, b)
        qm[i], qp[i] = sol[:nm], sol[nm:]
        wf[i] = Phi_f @ qm[i]
        Ff[i] = kc * (wf[i] - Lp @ qp[i])        # + = pushes payload up
    return dict(qm=qm, qp=qp, Ffoot=Ff, wfeet=wf, Phi_f=Phi_f, Lp=Lp, fp=fp)


def bare_plate_field(freqs_hz, sysd, pts, zeta_pl=ZETA_PL):
    """Plate-only acceleration field per unit point force at FORCE_PT: (nf, npts)."""
    wn, mgen = sysd["wn"], sysd["mgen"]
    Phi_p = phi_matrix(sysd, pts)
    Phi_d = phi_matrix(sysd, [FORCE_PT])[0]
    out = np.zeros((len(freqs_hz), len(pts)), dtype=complex)
    for i, fh in enumerate(freqs_hz):
        w = 2 * np.pi * fh
        Dm = mgen * (wn**2 - w**2 + 2j * zeta_pl * wn * w)
        qm = Phi_d / Dm
        out[i] = -(w**2) * (Phi_p @ qm)
    return out


def loaded_plate_field(freqs_hz, sysd, pts, ex=0.0, **kw):
    """Acceleration field of the payload-loaded plate per unit point force."""
    cp = coupled_plate_payload_frf(freqs_hz, sysd, ex=ex, **kw)
    wn, mgen = sysd["wn"], sysd["mgen"]
    Phi_p = phi_matrix(sysd, pts)
    acc = np.zeros((len(freqs_hz), len(pts)), dtype=complex)
    for i, fh in enumerate(freqs_hz):
        w = 2 * np.pi * fh
        acc[i] = -(w**2) * (Phi_p @ cp["qm"][i])
    return acc, cp


def payload_on_shaker(freqs_hz, ex=0.0, kz=KZ_FOOT, eta=ETA):
    """EX-D test config: payload (3-DOF) on rigid base with unit vertical base
    acceleration (uniform at all feet). Returns per-foot forces, net Fz, My about
    foot centroid O, and payload CG acceleration (all per unit base accel a_b).
    Relative coordinates: q_rel about CG; M qr'' + K qr = -M T a_b, with rigid
    base influence T = [1,0,0] in [z,thx,thy] (uniform vertical)."""
    Mp, Lp = payload_vertical_3dof(ex=ex)
    kc = kz * (1 + 1j * eta)
    Kp = kc * (Lp.T @ Lp)
    Tinf = np.array([1.0, 0.0, 0.0])
    nf = len(freqs_hz)
    Ff = np.zeros((nf, 4), dtype=complex)
    acc_cg = np.zeros((nf, 3), dtype=complex)
    for i, fh in enumerate(freqs_hz):
        w = 2 * np.pi * fh
        qr = np.linalg.solve(Kp - w**2 * Mp, -(Mp @ Tinf))   # per unit a_b
        Ff[i] = -kc * (Lp @ qr)                              # foot top - base, vertical
        acc_cg[i] = -(w**2) * qr + Tinf                      # absolute accel
    # net force & moment about O (feet plan positions rel O)
    xfO = np.array([+AX, +AX, -AX, -AX])
    netF = Ff.sum(axis=1)
    My = -(Ff * xfO).sum(axis=1)     # My = sum(-x_i * Fz_i) (right-hand rule about +y)
    return dict(Ffoot=Ff, netF=netF, My=My, acc_cg=acc_cg, xfO=xfO)


def octave_band_envelope(freqs, psd, frac=1.0):
    """Peak-hold envelope in 1/1-octave (frac=1) bands, returned on the same
    frequency grid as a piecewise-constant (in log f) envelope. Simple, stated
    in ledger D2: this is a plain peak-hold, not a margin-added spec."""
    fmin, fmax = freqs[0], freqs[-1]
    edges = [fmin]
    while edges[-1] < fmax:
        edges.append(edges[-1] * 2 ** frac)
    env = np.zeros_like(psd)
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (freqs >= lo) & (freqs <= hi)
        if sel.any():
            env[sel] = psd[sel].max()
    return env


def stamp(fig, script, note=""):
    """AGENTS.md plot gate: every data figure states its run/data provenance."""
    txt = (f"{script} | notch_multipoint_7004c_20260611 | deterministic analytic model, "
           f"no measured data{' | ' + note if note else ''}")
    fig.text(0.005, 0.005, txt, fontsize=6.0, color="0.45", ha="left", va="bottom")


def save_json(path, obj):
    def cv(o):
        if isinstance(o, (np.floating, np.integer)):
            return o.item()
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o))
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=1, default=cv)
    print("wrote", os.path.relpath(path, WS))
