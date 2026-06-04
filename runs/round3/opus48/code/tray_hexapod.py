#!/usr/bin/env python3
"""6-strut (hexapod-style) minimally-constrained tray, RBE'd to a single interface node.

Round-3 follow-up (Claude Code Opus 4.8 runner), per human direction:
- Richer LOAD model: a rigid isogrid tray + 136 kg avionics, minimally constrained by 6 two-force-member
  (axial-only) struts to a base that is RBE'd into a SINGLE interface node to the tank (keeps FBS single
  interface). Genuinely MDOF: 6 mount modes (3 translation + 3 rotation on the strut stiffnesses).
- TWO distinct model-form errors for the ground truth:
   (A) SPATIAL: per-strut stiffness varies across azimuth (preload/roughness gradient) -> breaks the
       6-fold symmetry -> splits/shifts mount modes. The BU model (6 IDENTICAL struts, one k_j) CANNOT
       represent this -> it biases k_j. (statFEM 'stochastic forward / field' error, in the physics.)
   (B) FREQUENCY: an additive output discrepancy d(w) on the interface apparent-mass FRF (GP over
       frequency). (statFEM output 'model inadequacy' term.)
- Struts are REAL constant axial springs (no complex/frequency-dependent joint impedance yet).

Learned parameter (BU): the nominal strut/interface axial stiffness k_j (ONE scalar; all struts equal).
Observed channel: axial driving-point apparent mass at the interface node, M_app,zz(w).
Units SI. Coordinate frame: z = launch axis (up), x-y = tray plane.
"""
from __future__ import annotations
import sys, math, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parents[1]
FIG = HERE/"report"/"figures"

# ---- tray (rigid) properties ----
M_AVIONICS = 136.0
M_PANEL = 6.0
M_TRAY = M_AVIONICS + M_PANEL          # 142 kg
R_TRAY = 0.50                          # m, tray radius (strut attach circle)
# rigid disk inertia about CG (+ avionics treated as part of disk, conservative)
IXX = IYY = 0.25*M_TRAY*R_TRAY**2
IZZ = 0.50*M_TRAY*R_TRAY**2
M_MAT = np.diag([M_TRAY, M_TRAY, M_TRAY, IXX, IYY, IZZ])

# ---- 6-strut hexapod geometry ----
R_BASE = 0.35                          # m, base ring radius
H_STRUT = 0.35                         # m, strut height (tray z=0 -> base z=-H)
SKEW_DEG = 30.0                        # base azimuth offset (hexapod skew -> constrains theta_z)
TRAY_CG = np.array([0.0, 0.0, 0.0])
BASE_CG = np.array([0.0, 0.0, -H_STRUT])


def _skew(r):
    return np.array([[0, -r[2], r[1]], [r[2], 0, -r[0]], [-r[1], r[0], 0]])


def strut_geometry():
    """OCTAHEDRAL hexapod (full 6-DOF minimal constraint): 3 tray nodes (0,120,240 deg) and 3 base nodes
    (60,180,300 deg); each tray node connects to its TWO neighbouring base nodes -> 6 struts forming the
    standard octahedral pattern (non-singular wrench system -> 6 non-zero mount modes)."""
    tray_ang = [0.0, 120.0, 240.0]
    base_ang = [60.0, 180.0, 300.0]
    Tn = [np.array([R_TRAY*math.cos(math.radians(a)), R_TRAY*math.sin(math.radians(a)), 0.0]) for a in tray_ang]
    Bn = [np.array([R_BASE*math.cos(math.radians(a)), R_BASE*math.sin(math.radians(a)), -H_STRUT]) for a in base_ang]
    pairs = [(0, 0), (0, 2), (1, 1), (1, 0), (2, 2), (2, 1)]   # tray->two neighbouring base nodes
    P, B, n, L = [], [], [], []
    for ti, bi in pairs:
        Pi = Tn[ti]; Bi = Bn[bi]
        di = Bi - Pi; Li = np.linalg.norm(di)
        P.append(Pi); B.append(Bi); n.append(di/Li); L.append(Li)
    return np.array(P), np.array(B), np.array(n), np.array(L)


def assemble(k_struts):
    """Assemble K_tt, K_tb, K_bb (6x6 each) for the rigid tray on 6 axial struts to the rigid base.
    k_struts: array(6) of per-strut axial stiffness [N/m]."""
    P, B, n, L = strut_geometry()
    Ktt = np.zeros((6, 6)); Ktb = np.zeros((6, 6)); Kbb = np.zeros((6, 6))
    for i in range(6):
        rP = P[i] - TRAY_CG; rB = B[i] - BASE_CG
        BP = np.hstack([np.eye(3), -_skew(rP)])   # 3x6 tray CG -> tray point
        BB = np.hstack([np.eye(3), -_skew(rB)])   # 3x6 base CG -> base point
        ni = n[i].reshape(3, 1)
        aP = (BP.T @ ni)                          # 6x1
        aB = (BB.T @ ni)
        Ktt += k_struts[i]*(aP @ aP.T)
        Ktb += -k_struts[i]*(aP @ aB.T)
        Kbb += k_struts[i]*(aB @ aB.T)
    return Ktt, Ktb, Kbb


def modes(k_struts, return_shapes=False):
    Ktt, _, _ = assemble(k_struts)
    Lc = np.linalg.cholesky(M_MAT); Li = np.linalg.inv(Lc)
    A = Li @ Ktt @ Li.T; A = 0.5*(A+A.T)
    ev, evec = np.linalg.eigh(A)
    order = np.argsort(ev)
    f = np.sqrt(np.clip(ev[order], 0, None))/(2*np.pi)
    phi = Li.T @ evec[:, order]    # physical mass-normalized shapes (6x6)
    if return_shapes:
        return f, phi
    return f


def apparent_mass_axial(k_struts, freqs, dof=2):
    """Axial driving-point apparent mass M_app[dof,dof](w) at the interface (base) node.
    Z_b(w) = K_bb - K_bt (K_tt - w^2 M)^-1 K_tb ; M_app = -Z_b / w^2."""
    Ktt, Ktb, Kbb = assemble(k_struts)
    Kbt = Ktb.T
    w = 2*np.pi*freqs
    out = np.empty(len(freqs), dtype=complex)
    for j, wj in enumerate(w):
        D = Ktt - (wj**2)*M_MAT
        Zb = Kbb - Kbt @ np.linalg.solve(D, Ktb)
        out[j] = -Zb[dof, dof]/(wj**2)
    return out


def calibrate_kj(target_hz=86.25):
    """Scale the uniform per-strut stiffness k_j so the AXIAL (z-dominant) mount mode = target_hz.
    f ~ sqrt(k), so kj = (target/f_z_at_unit_k)^2 using the z-dominant mode at unit stiffness."""
    f, phi = modes(np.ones(6), return_shapes=True)
    zpart = np.abs(phi[2, :])              # |z-translation| participation of each mode
    iz = int(np.argmax(zpart))
    fz_unit = f[iz]
    return (target_hz/fz_unit)**2, iz


def spatial_error_pattern(a_spatial, phi0_deg=20.0):
    """Per-strut multiplicative stiffness error across azimuth (smooth, azimuthally correlated):
    k_i = k_j * (1 + a_spatial*cos(phi_i - phi0)). Represents a preload/roughness gradient (stiff side
    / soft side). Breaks 6-fold symmetry -> mode splitting the single-k_j BU model cannot represent."""
    phis = np.array([60*i for i in range(6)])
    return 1.0 + a_spatial*np.cos(np.radians(phis - phi0_deg))


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    kj, iz = calibrate_kj(86.25)
    f_sym = modes(np.full(6, kj))
    print("calibrated per-strut k_j = %.3e N/m  (axial mode index %d)" % (kj, iz))
    print("symmetric mount modes (Hz):", np.round(f_sym, 2))

    # spatial-error (truth) struts
    a_spatial = 0.20
    k_spatial = kj*spatial_error_pattern(a_spatial)
    f_spatial = modes(k_spatial)
    print("per-strut k (spatial err 20%%):", np.round(k_spatial/1e6, 3), "MN/m")
    print("spatial-error mount modes (Hz):", np.round(f_spatial, 2))

    freqs = np.geomspace(20.0, 2000.0, 1000)
    Msym = np.abs(apparent_mass_axial(np.full(6, kj), freqs))
    Mspa = np.abs(apparent_mass_axial(k_spatial, freqs))
    # frequency-error: smooth GP draw on log apparent mass
    eta = np.log(freqs); rng = np.random.default_rng(3)
    Kf = (0.12**2)*(1+math.sqrt(3)*np.abs(np.subtract.outer(eta, eta))/0.4)*np.exp(-math.sqrt(3)*np.abs(np.subtract.outer(eta, eta))/0.4)
    dfreq = np.linalg.cholesky(Kf+1e-10*np.eye(len(freqs))) @ rng.standard_normal(len(freqs))
    Mspa_freq = Mspa*np.exp(dfreq)

    # ---- geometry figure ----
    P, B, n, L = strut_geometry()
    fig = plt.figure(figsize=(7.6, 7.0)); ax = fig.add_subplot(111, projection="3d")
    th = np.linspace(0, 2*np.pi, 60)
    ax.plot(R_TRAY*np.cos(th), R_TRAY*np.sin(th), 0*th, color="#2ca02c", lw=2, label="tray (rigid)")
    for i in range(6):
        ax.plot([P[i,0],B[i,0]],[P[i,1],B[i,1]],[P[i,2],B[i,2]], color="#d62728", lw=2, label="6 struts (2-force)" if i==0 else None)
        ax.scatter(*P[i], color="#2ca02c", s=20); ax.scatter(*B[i], color="#1f77b4", s=20)
    ax.scatter(*BASE_CG, color="k", marker="*", s=200, label="interface node (RBE base)")
    ax.scatter(*TRAY_CG, color="#2ca02c", marker="s", s=80, label="tray CG + 136 kg avionics")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z (launch) [m]")
    ax.set_title("6-strut minimally-constrained tray, RBE'd to a single interface node\n(hexapod-style; 6 mount modes; single FBS interface to the tank)", fontsize=9.5)
    ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(FIG/"tray_hexapod_geometry.png", dpi=140); plt.close(fig)

    # ---- modes + apparent mass with the two errors ----
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))
    ax = axes[0]
    idx = np.arange(1, 7)
    ax.plot(idx, f_sym, "o-", color="#1f77b4", ms=8, label="symmetric (BU: 6 equal struts)")
    ax.plot(idx, f_spatial, "s--", color="#d62728", ms=7, label="spatial error (truth: per-strut k)")
    ax.axhline(86.25, color="gray", ls=":", label="axial anchor 86.25 Hz")
    ax.set_xlabel("mount mode #"); ax.set_ylabel("frequency [Hz]")
    ax.set_title("6 mount modes — spatial stiffness error SPLITS the symmetric modes", fontsize=9.5)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8.5)
    ax = axes[1]
    ax.loglog(freqs, Msym, color="#1f77b4", lw=2.0, label="BU symmetric |M_app,zz|")
    ax.loglog(freqs, Mspa, color="#d62728", lw=1.8, ls="--", label="+ SPATIAL model-form error")
    ax.loglog(freqs, Mspa_freq, color="#6a0dad", lw=1.2, alpha=0.8, label="+ SPATIAL + FREQUENCY error")
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("axial apparent mass |M_app,zz| [kg]")
    ax.set_title("Interface apparent mass: two distinct model-form errors\n(spatial = symmetry-breaking peaks; frequency = smooth FRF bias)", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/"tray_hexapod_modes_apparentmass.png", dpi=140); plt.close(fig)

    summary = {"k_j_per_strut_n_per_m": float(kj), "m_tray_kg": M_TRAY,
               "mount_modes_symmetric_hz": [float(x) for x in f_sym],
               "mount_modes_spatial_error_hz": [float(x) for x in f_spatial],
               "n_struts": 6, "skew_deg": SKEW_DEG, "spatial_error_amp": a_spatial,
               "note": "rigid tray on 6 axial struts, RBE'd to single interface node; struts = real "
                       "constant springs (no complex impedance yet); two model-form errors: spatial "
                       "(per-strut k, symmetry-breaking) + frequency (output GP on FRF)."}
    (HERE/"report"/"tray_hexapod_summary.json").write_text(json.dumps(summary, indent=2))
    print("wrote geometry + modes/apparent-mass figures and summary")


if __name__ == "__main__":
    main()
