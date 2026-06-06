#!/usr/bin/env python3
"""STAGE-3 structure-aware forward model for the BLIND round-3 inference (vs Codex independent truth).

BLINDNESS: consumes ONLY runs/round3/codex_truth/dataset/observations.npz + data_contract.md. Does NOT
read sealed_truth/, codex code, or codex report. The master scores against the sealed truth.

The three coupled fixes the Stage-0/1 blind failure pointed to (see report/blind_known_failures.md,
review.md). This module implements fix #1 (asymmetric per-strut forward) and #2's forward propagation
(structure/property-based per-strut discrepancy in PARAMETER space). The complex likelihood (fix #3) and
the structured-discrepancy PRIOR live in blind3_infer.py. The netCG QOI (canonical contract) lives here.

Modelled quantity = published per-build 6-DOF DIAGONAL complex interface apparent mass M_pub(w):

    M_pub(w) = M_S(w)            SOURCE (dome): rigid per-DOF effective mass/inertia + axial bounce
             + M_L(w; k_struts)  LOAD  (tray): rigid body on 6 PER-STRUT axial struts, condensed to the
                                       single interface node. PER-STRUT k breaks 6-fold symmetry ->
                                       represents x!=y and rx!=ry mode SPLITS the one-equal-strut model
                                       could not.

Apparent masses ADD at a shared driven interface DOF (impedances in parallel), so M_pub = M_S + M_L is the
right, differentiable combination. Reading the rigid-body mass off the measured low-f apparent-mass
asymptote is standard apparent-mass practice, not peeking at hidden structure.

netCG QOI (canonical, netcg_quantity_contract.md): F_iface from DYNAMIC FBS coupling of source+load:
    a_iface(w) = F(w) / (M_S(w) + M_L(w))           coupled interface acceleration (single z DOF)
    F_iface(w) = M_L(w) * a_iface(w)                force flowing INTO the load
    netCG(w)   = F_iface(w) / m_load = [M_L/(M_S+M_L)] * F / m_load
  f->0 rigid limit: netCG -> F/(m_source+m_load) (sanity check). Resonates at coupled modes.
  FORBIDDEN (per contract): rigid mass-ratio constant transmission; drive-point accelerance F/M_zz.

Units SI. Frame: x,y transverse; z axial (dome->tray, +up); rotations RH. DOF=[x,y,z,rx,ry,rz].
"""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

import tray_hexapod as hx   # nominal hexapod geometry (per-strut assemble, modes)

HERE = Path(__file__).resolve().parents[1]
DATASET = HERE.parent / "codex_truth" / "dataset" / "observations.npz"

DOF = ["x", "y", "z", "rx", "ry", "rz"]
NDOF = 6
ETA = 0.04            # fixed structural loss (finite FRF peaks); magnitude+phase weakly identifies it -> FIXED
M_DOME_FRAC = 0.45    # fraction of axial source rigid mass that resonates as the dome bounce (nominal)

# ----- nominal LOAD (tray) rigid-body mass matrix; m_load=170 kg from data_contract -----
M_LOAD = 170.0
R_TRAY = 0.55
IXX = IYY = 0.25 * M_LOAD * R_TRAY**2
IZZ = 0.50 * M_LOAD * R_TRAY**2
M_LOAD6 = np.array([M_LOAD, M_LOAD, M_LOAD, IXX, IYY, IZZ])
M_LOAD_MAT = np.diag(M_LOAD6)

# ----- precompute the per-strut rank-1 geometry vectors so K(k) is LINEAR in per-strut k (JAX-friendly) ---
def _strut_rank1():
    """Return aP (6,6) and aB (6,6): column i is strut i's 6-vector at tray (aP) / base (aB).
    K_tt = sum_i k_i aP_i aP_i^T ; K_tb = -sum_i k_i aP_i aB_i^T ; K_bb = sum_i k_i aB_i aB_i^T."""
    P, B, n, L = hx.strut_geometry()
    aP = np.zeros((6, 6)); aB = np.zeros((6, 6))
    for i in range(6):
        rP = P[i] - hx.TRAY_CG; rB = B[i] - hx.BASE_CG
        BP = np.hstack([np.eye(3), -hx._skew(rP)])   # 3x6
        BB = np.hstack([np.eye(3), -hx._skew(rB)])
        ni = n[i].reshape(3, 1)
        aP[:, i] = (BP.T @ ni).ravel()
        aB[:, i] = (BB.T @ ni).ravel()
    return aP, aB

_AP, _AB = _strut_rank1()
_AP_J = jnp.asarray(_AP); _AB_J = jnp.asarray(_AB)
# strut azimuths (deg) for the discrepancy feature space (azimuthal position of each strut)
STRUT_AZIM_DEG = np.array([0.0, 120.0, 240.0, 60.0, 180.0, 300.0])  # tray->base pairing azimuths


def load_observations(path=DATASET):
    d = np.load(path, allow_pickle=True)
    re = d["apparent_mass_real"]; im = d["apparent_mass_imag"]
    AM = re + 1j * im   # (8,6,nf)
    return dict(
        f=np.asarray(d["frequency_hz"]), dof=[str(x) for x in d["dof_order"]],
        AM=AM, re=re, im=im, mag=np.abs(AM),
        resp_psd=d["response_psd_g2_per_Hz"], netcg=d["netcg_3grms_g"],
        design_force=np.asarray(d["design_force_psd_N2_per_Hz"]),
        flight_force=np.asarray(d["flight_force_psd_N2_per_Hz"]),
        load_mass=float(d["load_mass_kg"]), g0=float(d["g0_m_per_s2"]),
        build_ids=np.asarray(d["build_ids"]), flight_ids=np.asarray(d["flight_ids"]),
    )


def source_rigid_from_asymptote(obs, n_low=8):
    """SOURCE (dome) per-DOF rigid effective mass/inertia = measured low-f asymptote - LOAD rigid body.
    The axial (z) entry has the bounce-resonator low-f mass split out so the total z low-f is preserved.
    Returns (M_src6, m_dome, lf). m_source(z) = M_src6[2] + m_dome (used as the f->0 source mass)."""
    lf = obs["mag"][:, :, :n_low].mean(axis=(0, 2))   # (6,) build-averaged measured asymptote
    M_src6 = np.clip(lf - M_LOAD6, 1.0, None)
    m_dome = M_DOME_FRAC * max(lf[2] - M_LOAD6[2], 1.0)
    M_src6 = M_src6.copy(); M_src6[2] = max(M_src6[2] - m_dome, 1.0)
    return M_src6, float(m_dome), lf


# --------------------------------------------------------------------------------------------------- JAX
def load_AM_diag(k_struts, freqs):
    """LOAD interface apparent mass, diagonal (nf,6) complex. Rigid load body on 6 PER-STRUT axial
    struts, condensed to the interface (base) node. JAX-differentiable in the 6 per-strut k.
    Z_b(w)=K_bb-K_bt(K_tt-w^2 M)^-1 K_tb ; M_app = -Z_b/w^2 ; -> M_LOAD6 at low f."""
    s = k_struts * (1 + 1j * ETA)                       # (6,) complex per-strut
    Ktt = (_AP_J * s) @ _AP_J.T                          # 6x6 complex
    Ktb = -(_AP_J * s) @ _AB_J.T
    Kbb = (_AB_J * s) @ _AB_J.T
    Mm = jnp.asarray(M_LOAD_MAT).astype(jnp.complex128)
    w2 = (2 * jnp.pi * freqs) ** 2                       # (nf,)
    # batched complex solve over all frequencies at once: D_f = Ktt - w2_f * M  (nf,6,6)
    D = Ktt[None, :, :] - w2[:, None, None] * Mm[None, :, :]
    X = jnp.linalg.solve(D, jnp.broadcast_to(Ktb, (freqs.shape[0], 6, 6)))   # (nf,6,6)
    Zb = Kbb[None, :, :] - jnp.einsum("ij,fjk->fik", Ktb.T, X)               # (nf,6,6)
    diagZ = jnp.diagonal(Zb, axis1=1, axis2=2)                               # (nf,6)
    return -diagZ / w2[:, None]                                             # (nf,6) complex


def source_AM_diag(M_src6, m_dome, f_dome, freqs):
    """SOURCE (dome) interface apparent mass, diagonal (nf,6) complex: rigid per-DOF + axial bounce SDOF
    on z. M_z(w) = M_src6[z] + m_dome*wd^2(1+ieta)/(wd^2(1+ieta)-w^2)."""
    w = 2 * jnp.pi * freqs
    base = jnp.asarray(M_src6).astype(jnp.complex128)[None, :] * jnp.ones((freqs.shape[0], 1))
    wd2 = (2 * jnp.pi * f_dome) ** 2 * (1 + 1j * ETA)
    dz = m_dome * wd2 / (wd2 - w**2)                     # (nf,)
    base = base.at[:, 2].add(dz)
    return base                                         # (nf,6) complex


def forward_complex(k_struts, f_dome, M_src6, m_dome, freqs):
    """Total published interface apparent mass M_pub = M_S + M_L, diagonal. Returns (6,nf) complex."""
    ML = load_AM_diag(k_struts, freqs)                  # (nf,6)
    MS = source_AM_diag(M_src6, m_dome, f_dome, freqs)  # (nf,6)
    return (MS + ML).T                                  # (6,nf)


# --- discrepancy in PARAMETER (strut-feature) space: per-strut multiplicative log-k field d_j ---
def feature_corr(azim_deg=STRUT_AZIM_DEG, ell_deg=70.0, same_type=0.30):
    """Structure/property-based correlation in STRUT FEATURE space (azimuth). Same element-type (all are
    axial struts) -> moderate baseline `same_type`; azimuthal proximity -> high correlation (Gaussian in
    angular distance, length ell_deg). This is the kernel that lets the discrepancy carry an AZIMUTHAL
    (spatial) error a frequency-only kernel cannot. Returns 6x6 correlation (unit diagonal)."""
    th = np.radians(azim_deg)
    d = np.angle(np.exp(1j * (th[:, None] - th[None, :])))   # wrapped angular distance [rad]
    az = np.exp(-0.5 * (np.degrees(np.abs(d)) / ell_deg) ** 2)
    R = same_type + (1.0 - same_type) * az
    R = 0.5 * (R + R.T)
    R[np.diag_indices(6)] = 1.0
    return R


def apply_discrepancy(k_pop, d_field):
    """Actual per-strut stiffness = k_pop * exp(d_j), with d_j the zero-mean structure-based discrepancy
    field (feature-correlated). k_pop is the population calibration scalar; d carries the asymmetry."""
    d0 = d_field - jnp.mean(d_field)                    # zero-mean -> separates k_pop (mean) from d (shape)
    return k_pop * jnp.exp(d0)


# --- netCG QOI (canonical contract; axial z) ---
def netcg_transfer_z(k_struts, f_dome, M_src6, m_dome, freqs):
    """H(w) such that netCG(w) = H(w) * F(w):  H = M_L_z/((M_S_z+M_L_z) * m_load * g0).
    Uses the z-DOF source & load apparent masses (FBS impedance sharing). Returns complex (nf,)."""
    MLz = load_AM_diag(k_struts, freqs)[:, 2]           # (nf,)
    MSz = source_AM_diag(M_src6, m_dome, f_dome, freqs)[:, 2]
    return MLz, MSz


def netcg_psd(k_struts, f_dome, M_src6, m_dome, force_psd, freqs, m_load, g0):
    """PSD_netCG(f) [g^2/Hz] = |H|^2 * force_psd, H=M_L/((M_S+M_L) m_load g0). Returns (nf,) real."""
    MLz, MSz = netcg_transfer_z(k_struts, f_dome, M_src6, m_dome, freqs)
    H = MLz / ((MSz + MLz) * m_load * g0)
    return (jnp.abs(H) ** 2) * force_psd


def grms3(psd, freqs):
    """3 * sqrt(integral psd df) using trapezoid on the (possibly non-uniform) grid."""
    return 3.0 * jnp.sqrt(jnp.trapezoid(psd, freqs))


# --------------------------------------------------------------------------------------------------- check
def _validate():
    from scipy.signal import find_peaks
    obs = load_observations()
    f = obs["f"]
    M_src6, m_dome, lf = source_rigid_from_asymptote(obs)
    kj, _ = hx.calibrate_kj(86.25)
    print("nominal k_strut=%.3e  m_dome=%.1f  m_source(z)=%.1f  m_load=%.1f" %
          (kj, m_dome, M_src6[2] + m_dome, M_LOAD))
    print("measured low-f asymptote:", np.round(lf, 1))
    print("M_src6 rigid (asymptote - load):", np.round(M_src6, 1))
    # symmetric vs per-strut split
    print("symmetric modes:", np.round(hx.modes(np.full(6, kj)), 2))
    kper = kj * hx.spatial_error_pattern(0.25, 20.0)
    print("per-strut(0.25) modes:", np.round(hx.modes(kper), 2))
    # forward vs data peaks
    Mc = np.asarray(forward_complex(jnp.asarray(np.full(6, kj)), 93.5, M_src6, m_dome, jnp.asarray(f)))
    mag = np.abs(Mc); data = obs["mag"].mean(axis=0)
    print("\nDOF | model_lf data_lf | model peaks | data peaks")
    for i, nm in enumerate(DOF):
        mp, _ = find_peaks(mag[i], prominence=mag[i].max() * 0.05)
        mp = np.sort(mp[np.argsort(mag[i][mp])[::-1][:4]])
        dp, _ = find_peaks(data[i], prominence=data[i].max() * 0.05)
        dp = np.sort(dp[np.argsort(data[i][dp])[::-1][:4]])
        print(f"{nm}: {mag[i,0]:6.0f} {data[i,0]:6.0f} | {np.round(f[mp],1)} | {np.round(f[dp],1)}")
    # netCG sanity: f->0 limit and a GRMS estimate
    H_MLz, H_MSz = netcg_transfer_z(jnp.asarray(np.full(6, kj)), 93.5, M_src6, m_dome, jnp.asarray(f))
    H_MLz = np.asarray(H_MLz); H_MSz = np.asarray(H_MSz)
    ms = M_src6[2] + m_dome
    print("\nnetCG f->0: H*m_load*g0 = M_L/(M_S+M_L) ->", float(np.abs(H_MLz[0] / (H_MSz[0] + H_MLz[0]))),
          " expected m_load/(m_source+m_load)=", M_LOAD / (ms + M_LOAD))
    fpsd = obs["flight_force"].mean(axis=0)
    psd = np.asarray(netcg_psd(jnp.asarray(np.full(6, kj)), 93.5, M_src6, m_dome,
                               jnp.asarray(fpsd), jnp.asarray(f), M_LOAD, obs["g0"]))
    print("nominal netCG 3*GRMS = %.3f g   (published mean %.3f g)" %
          (float(grms3(jnp.asarray(psd), jnp.asarray(f))), float(obs["netcg"].mean())))
    print("feature_corr:\n", np.round(feature_corr(), 2))


if __name__ == "__main__":
    _validate()
