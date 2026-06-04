#!/usr/bin/env python3
"""Round-3 MDOF forward model (Claude Code Opus 4.8 runner).

Two MDOF components coupled at ONE interface DOF by frequency-based substructuring (FBS),
plus the netCG QOI. Built in JAX (differentiable -> NUTS-compatible), extending the validated
spike Euler-Bernoulli beam FEM (runs/round3/spike/code/beam_fem_spike.py).

Architecture (see report/packet.md and known_failures.md):
  * A real assembled beam FEM (K, M, geometric Kg) provides the MODE BASIS of each component:
    mode-frequency ratios, interface participation, effective masses, and mode shapes. Pressure
    (stress) stiffening enters the dome via the geometric stiffness Kg from internal-pressure
    membrane tension; its effect on the RAW modes is shown (p=0 vs p_op).
  * The coupled interface dynamics use a MODAL series anchored to the staged-data effective interface
    modal masses (dome m1=1.0 kg, tray m2=0.6 kg) so the model reduces EXACTLY to the round-2 2DOF at
    the first mode (verified) and stays consistent with the staged 2DOF data; higher FEM modes are added.
  * netCG = F_interface / m_load (physical load mass) is a derived prediction (see netcg_psd()).

FBS single-interface coupling (derived in packet, verified == round-2 2DOF for single-mode):
  Source (dome) free-interface accelerance Y_s(w) = a_iface/F (tray removed).
  Load (tray) interface apparent mass M_L(w) = F/a_iface ; load accelerance Y_L = 1/M_L.
  Coupled interface force into load:  F_iface = Y_s/(Y_s+Y_L) * F_ext = Y_s*M_L/(1+Y_s*M_L) * F_ext.
  Coupled interface accelerance:      H_iface = a_iface/F_ext = Y_s/(1 + Y_s*M_L).

Units: strict SI (m, kg, s, Pa, N); frequency in Hz; PSD g^2/Hz with g0=9.80665.
Coordinate frame: x = beam axis (m), transverse displacement w, rotation theta (right-handed).
"""
from __future__ import annotations

import math
import numpy as np
import jax
import jax.numpy as jnp

jax.config.update("jax_enable_x64", True)

G0 = 9.80665

# ---------------------------------------------------------------------------
# Effective interface modal masses (data layer; consistent with staged 2DOF data)
# ---------------------------------------------------------------------------
M1_EFF = 1.0   # dome effective interface modal mass [kg] (local mount-region mode; small, by design)
M2_EFF = 0.6   # tray effective interface modal mass [kg] (staged-data effective mass)

# Anchors (round-2 structural truth; HARD constraint)
DOME_F1_HZ = 93.50
TRAY_F1_HZ = 86.25
DOME_ZETA1 = 0.0225
TRAY_ZETA1 = 0.0195

# Physical load mass for netCG (tray total = isogrid panel + avionics)
M_AVIONICS = 136.0          # kg (~300 lbm)
# isogrid panel mass from the FEM mass-thickness: rho*W*t_mass*L = 2700*0.70*0.0045*0.70
M_PANEL = 2700.0 * 0.70 * 0.0045 * 0.70   # ~5.95 kg (isogrid is stiff but light)
M_LOAD_PHYS = M_AVIONICS + M_PANEL        # ~141.95 kg (tray total for netCG)

# ---------------------------------------------------------------------------
# Beam element matrices (Euler-Bernoulli, Hermite cubic) -- from the spike, in JAX.
# DOF order per element [w1, th1, w2, th2].
# ---------------------------------------------------------------------------
def beam_element_K(EI, le):
    le2 = le * le; le3 = le2 * le
    k = jnp.array([
        [12.0, 6.0*le, -12.0, 6.0*le],
        [6.0*le, 4.0*le2, -6.0*le, 2.0*le2],
        [-12.0, -6.0*le, 12.0, -6.0*le],
        [6.0*le, 2.0*le2, -6.0*le, 4.0*le2]])
    return (EI/le3)*k

def beam_element_M(rhoA, le):
    le2 = le*le
    m = jnp.array([
        [156.0, 22.0*le, 54.0, -13.0*le],
        [22.0*le, 4.0*le2, 13.0*le, -3.0*le2],
        [54.0, 13.0*le, 156.0, -22.0*le],
        [-13.0*le, -3.0*le2, -22.0*le, 4.0*le2]])
    return (rhoA*le/420.0)*m

def beam_element_Kg(T, le):
    """Geometric (stress) stiffness for axial tension T>0 (stiffening). Standard cubic-beam Kg."""
    le2 = le*le
    g = jnp.array([
        [36.0, 3.0*le, -36.0, 3.0*le],
        [3.0*le, 4.0*le2, -3.0*le, -1.0*le2],
        [-36.0, -3.0*le, 36.0, -3.0*le],
        [3.0*le, -1.0*le2, -3.0*le, 4.0*le2]])
    return (T/(30.0*le))*g


def assemble_beam(E, rho, L, A, I, nele, tension=0.0, lumped=None, bc="clamped-free"):
    """Assemble global K (+geometric), M for a 2-node Hermite beam.

    lumped: dict {node_index: mass_kg} added to translational DOF.
    bc: 'clamped-free' (node0 w,theta fixed) or 'free-free' (no constraint).
    Returns reduced Kr, Mr (numpy), and the mapping free->global DOF index list.
    """
    nnode = nele + 1
    ndof = 2 * nnode
    le = L / nele
    EI = E * I
    rhoA = rho * A
    Ke = np.asarray(beam_element_K(EI, le))
    Me = np.asarray(beam_element_M(rhoA, le))
    Kge = np.asarray(beam_element_Kg(tension, le)) if tension != 0.0 else np.zeros((4, 4))
    K = np.zeros((ndof, ndof)); M = np.zeros((ndof, ndof))
    for e in range(nele):
        d = [2*e, 2*e+1, 2*e+2, 2*e+3]
        K[np.ix_(d, d)] += Ke + Kge
        M[np.ix_(d, d)] += Me
    if lumped:
        for node, mass in lumped.items():
            M[2*node, 2*node] += mass
    if bc == "clamped-free":
        free = list(range(2, ndof))
    elif bc == "free-free":
        free = list(range(ndof))
    else:
        raise ValueError(bc)
    Kr = K[np.ix_(free, free)]; Mr = M[np.ix_(free, free)]
    return Kr, Mr, free


def solve_modes(Kr, Mr, n=6):
    """Generalized symmetric eigensolve K phi = w^2 M phi via Cholesky whitening (numpy).
    Returns f_hz (ascending), and mass-normalized mode matrix phi (cols), phi^T M phi = I."""
    Lc = np.linalg.cholesky(Mr)
    Linv = np.linalg.inv(Lc)
    Asym = Linv @ Kr @ Linv.T
    Asym = 0.5 * (Asym + Asym.T)
    evals, evecs = np.linalg.eigh(Asym)
    evals = np.clip(evals, 0.0, None)
    omega = np.sqrt(evals)
    f = omega / (2*np.pi)
    phi = Linv.T @ evecs   # mass-normalized
    order = np.argsort(f)
    return f[order][:n], phi[:, order][:, :n]


def effective_modal_mass(phi_row, Mr, phi):
    """Effective modal mass for a unit-direction drive at a DOF, using participation factors.
    For mass-normalized modes, modal participation L_r = phi_r^T M r (r = influence vector).
    Here we use the DRIVE-DOF residue (phi_r[dof]^2) -> apparent modal mass 1/phi_r[dof]^2."""
    raise NotImplementedError  # not used; see drive-point residues below


# ---------------------------------------------------------------------------
# Aluminum dome (source) -- spin-formed 2:1 ellipsoidal cap, internal pressure.
# Meridional strip beam-FEM with internal-pressure membrane tension -> geometric stiffening.
# ---------------------------------------------------------------------------
# Material: Al 2219 (state in ledger): E=73.1 GPa, rho=2840 kg/m^3, nu=0.33
DOME_E = 73.1e9
DOME_RHO = 2840.0
DOME_R = 2.75            # m, equatorial radius (5.5 m dia)
DOME_HEIGHT = 1.40       # m, 2:1 ellipsoidal cap height (~R/2)
DOME_MERIDIAN_L = 2.50   # m, quarter-meridian arc length (strip length)
DOME_T = 0.0060          # m, wall thickness (tuning knob; reported)
DOME_STRIP_W = 0.10      # m, representative meridional strip width
DOME_P_OP = 3.5e5        # Pa, operating ullage pressure (~3.5 bar, F9-like)
DOME_NELE = 24


def dome_fem(thickness=DOME_T, pressure=DOME_P_OP, nele=DOME_NELE, n=6):
    """Dome meridional-strip beam FEM with internal-pressure geometric stiffening.
    Returns (f_hz, phi, free, interface_node, x_nodes, geom)."""
    b = DOME_STRIP_W; h = thickness
    A = b * h
    I = b * h**3 / 12.0
    # internal-pressure membrane tension on the strip: sphere membrane stress N = p R / 2 [N/m];
    # tension carried by the strip T = N * width  (tensile -> stiffening)
    N_membrane = pressure * DOME_R / 2.0
    T = N_membrane * b
    Kr, Mr, free = assemble_beam(DOME_E, DOME_RHO, DOME_MERIDIAN_L, A, I, nele,
                                 tension=T, lumped=None, bc="clamped-free")
    f, phi = solve_modes(Kr, Mr, n=n)
    x = np.linspace(0.0, DOME_MERIDIAN_L, nele + 1)
    interface_node = nele  # tip (apex / strut attach)
    geom = dict(E=DOME_E, rho=DOME_RHO, t=thickness, width=b, A=A, I=I, L=DOME_MERIDIAN_L,
                R=DOME_R, height=DOME_HEIGHT, pressure=pressure, membrane_tension_N_per_m=N_membrane,
                strip_tension_N=T, nele=nele, material="Al 2219")
    return f, phi, free, interface_node, x, geom


def dome_drivepoint_residue_ratios(thickness=DOME_T, pressure=DOME_P_OP, nele=DOME_NELE, n=6):
    """Mode-frequency ratios (f_r/f_1) and drive-point residue ratios (phi_r[iface]^2/phi_1[iface]^2)
    at the interface DOF, from the dome FEM. These FEM-derived ratios are the fixed mode basis used
    by the modal forward model; the absolute f_1 and amplitude are anchored downstream."""
    f, phi, free, inode, x, geom = dome_fem(thickness, pressure, nele, n=n)
    # reduced index of transverse DOF at interface node:
    # clamped-free removes DOFs 0,1 -> reduced index of w at node k is 2k-2
    ired = 2*inode - 2
    res = phi[ired, :]**2
    freq_ratio = f / f[0]
    res_ratio = res / res[0]
    return freq_ratio, res_ratio, f, geom


# ---------------------------------------------------------------------------
# Aluminum isogrid tray (load) -- free panel beam carrying lumped avionics,
# attached to the interface through soft joint spring+damper (sets fundamental + damping).
# ---------------------------------------------------------------------------
TRAY_E = 70.0e9          # Al-Li 2198 ~ 70 GPa (state in ledger)
TRAY_RHO = 2700.0
TRAY_L = 0.70            # m, panel strip length
TRAY_W = 0.70           # m, panel width
# Isogrid: high BENDING stiffness, low MASS (the point of isogrid). Decouple the two equivalent
# thicknesses so the panel flex modes sit WELL ABOVE the soft joint fundamental (joint = softest spring).
TRAY_T_BEND = 0.024     # m, equivalent BENDING thickness (-> I)
TRAY_T_MASS = 0.0045    # m, equivalent MASS/membrane thickness (-> areal mass)
TRAY_NELE = 20


def tray_panel_fem(nele=TRAY_NELE, n=6):
    """Free-free isogrid panel strip beam-FEM carrying lumped avionics (center node).
    Returns panel (free-free) mode freqs & shapes; first two are rigid-body (~0).
    Isogrid: bending I from t_bend, mass from t_mass (separate, since isogrid is stiff yet light)."""
    b = TRAY_W
    A = b * TRAY_T_MASS                 # mass area
    I = b * TRAY_T_BEND**3 / 12.0       # bending second moment
    center = nele // 2
    # lump avionics at center node (state: lumped, conservative for first flexible mode)
    lumped = {center: M_AVIONICS}
    Kr, Mr, free = assemble_beam(TRAY_E, TRAY_RHO, TRAY_L, A, I, nele,
                                 tension=0.0, lumped=lumped, bc="free-free")
    f, phi = solve_modes(Kr, Mr, n=n + 2)
    x = np.linspace(0.0, TRAY_L, nele + 1)
    panel_mass = TRAY_RHO * A * TRAY_L
    geom = dict(E=TRAY_E, rho=TRAY_RHO, t_bend=TRAY_T_BEND, t_mass=TRAY_T_MASS, width=b,
                L=TRAY_L, A=A, I=I, nele=nele,
                panel_mass_kg=panel_mass, avionics_kg=M_AVIONICS, m_load_phys=M_LOAD_PHYS,
                material="Al-Li 2198 isogrid (equivalent)")
    return f, phi, free, center, x, geom


def tray_flex_mode_ratios(nele=TRAY_NELE, n=4):
    """Return the panel FLEXIBLE-mode frequencies (Hz, free-free, excluding the 2 rigid modes)
    and their effective-mass fractions relative to the total tray mass. Used to add higher tray
    modes (above the joint-bounce fundamental) to the load apparent mass."""
    f, phi, free, center, x, geom = tray_panel_fem(nele=nele, n=n + 4)
    # free-free: first 2 modes are rigid-body (~0 Hz); flexible modes follow
    flex_f = f[f > 1.0][:n]
    return flex_f, geom


# ---------------------------------------------------------------------------
# Modal forward model (JAX, differentiable over f1, zeta) -- anchored amplitudes.
# ---------------------------------------------------------------------------
def _modal_accelerance(freqs_hz, mode_f_hz, residues, zetas):
    """Driving-point accelerance Y(w)=sum_r res_r * (-w^2)/(wr^2 - w^2 + 2 i zr wr w)  [(m/s^2)/N]."""
    w = 2.0*jnp.pi*freqs_hz
    wr = 2.0*jnp.pi*mode_f_hz
    Y = jnp.zeros_like(w, dtype=jnp.complex128)
    for r in range(len(mode_f_hz)):
        denom = wr[r]**2 - w**2 + 2j*zetas[r]*wr[r]*w
        Y = Y + residues[r] * (-(w**2)) / denom
    return Y


def source_accelerance(f1_dome, zeta_dome, freqs_hz, freq_ratio, res_ratio, m1_eff=M1_EFF,
                       n_modes=None):
    """Dome free-interface driving-point accelerance Y_s(w). First-mode effective interface mass=m1_eff
    => first residue = 1/m1_eff; higher residues scaled by FEM res_ratio. Higher modes share zeta_dome."""
    nm = len(freq_ratio) if n_modes is None else n_modes
    mode_f = f1_dome * jnp.asarray(freq_ratio[:nm])
    res = (1.0/m1_eff) * jnp.asarray(res_ratio[:nm])
    zetas = jnp.asarray([zeta_dome]*nm)
    return _modal_accelerance(freqs_hz, mode_f, res, zetas)


def load_apparent_mass(f1_tray, zeta_tray, freqs_hz, flex_f_hz, m_load=M2_EFF,
                       flex_mass_frac=0.04, zeta_flex=0.03):
    """Tray interface apparent mass M_L(w). Low-freq limit M_L -> m_load.

    Mode 1 = the JOINT bounce: tray mass on the joint SPRING+DAMPER (k_j + i w c_j) in series.
    For a mass m behind a series spring+damper, the exact driving-point apparent mass is
        M_L1 = m * (wr^2 + 2 i z wr w) / (wr^2 - w^2 + 2 i z wr w),  wr = 2 pi f1_tray,
    where the damper sits in the NUMERATOR too (joint = dominant damping source). This reduces the
    coupled interface accelerance EXACTLY to the round-2 2DOF (verified, tests/validate_fem.py).
    Higher panel-flex modes (structural/modal damping) use the standard modal numerator."""
    w = 2.0*jnp.pi*freqs_hz
    nf = len(flex_f_hz)
    frac = flex_mass_frac
    m1 = (1.0 - nf*frac) * m_load
    wr1 = 2.0*jnp.pi*f1_tray
    num1 = wr1**2 + 2j*zeta_tray*wr1*w           # joint spring+damper (k_j + i w c_j)/m
    M = m1 * num1 / (wr1**2 - w**2 + 2j*zeta_tray*wr1*w)
    for j in range(nf):
        wrj = 2.0*jnp.pi*flex_f_hz[j]
        M = M + (frac*m_load) * wrj**2 / (wrj**2 - w**2 + 2j*zeta_flex*wrj*w)
    return M


def couple_interface(Ys, ML):
    """FBS single-interface coupling.
    Returns (H_iface, force_ratio): H_iface = a_iface/F_ext, force_ratio = F_iface/F_ext."""
    H_iface = Ys / (1.0 + Ys * ML)
    force_ratio = (Ys * ML) / (1.0 + Ys * ML)   # = F_iface/F_ext
    return H_iface, force_ratio


def interface_accel_per_force_g(f1_dome, f1_tray, zeta_dome, zeta_tray, freqs_hz,
                                dome_basis, tray_flex_f, m1_eff=M1_EFF, m2_eff=M2_EFF):
    """Coupled interface accelerance (g per N) under force into the source interface DOF."""
    fr, rr = dome_basis
    Ys = source_accelerance(f1_dome, zeta_dome, freqs_hz, fr, rr, m1_eff=m1_eff)
    ML = load_apparent_mass(f1_tray, zeta_tray, freqs_hz, tray_flex_f, m_load=m2_eff)
    H, _ = couple_interface(Ys, ML)
    return H / G0


def interface_force_per_force(f1_dome, f1_tray, zeta_dome, zeta_tray, freqs_hz,
                             dome_basis, tray_flex_f, m1_eff=M1_EFF, m_load=M2_EFF):
    """Interface FORCE transfer F_iface/F_ext (dimensionless)."""
    fr, rr = dome_basis
    Ys = source_accelerance(f1_dome, zeta_dome, freqs_hz, fr, rr, m1_eff=m1_eff)
    ML = load_apparent_mass(f1_tray, zeta_tray, freqs_hz, tray_flex_f, m_load=m_load)
    _, frc = couple_interface(Ys, ML)
    return frc


def dome_only_recip_inertance(f1_dome, zeta_dome, freqs_hz, dome_basis, m1_eff=M1_EFF):
    fr, rr = dome_basis
    Ys = source_accelerance(f1_dome, zeta_dome, freqs_hz, fr, rr, m1_eff=m1_eff)
    return 1.0 / Ys


def tray_transmissibility(f1_tray, zeta_tray, freqs_hz):
    """Base-driven tray transmissibility (vibe test): mount/(mount - m w^2), single-mode joint."""
    w = 2.0*jnp.pi*freqs_hz
    wr = 2.0*jnp.pi*f1_tray
    # T = wr^2 + 2 i z wr w over (wr^2 - w^2 + 2 i z wr w)
    num = wr**2 + 2j*zeta_tray*wr*w
    den = wr**2 - w**2 + 2j*zeta_tray*wr*w
    return num/den


def netcg_psd(force_ratio_mag2, force_psd_n2, m_load=M_LOAD_PHYS):
    """netCG acceleration PSD [ (m/s^2)^2 / Hz ] = |F_iface/F_ext|^2 * S_F / m_load^2.
    Return also in g^2/Hz."""
    psd_acc = force_ratio_mag2 * force_psd_n2 / (m_load**2)   # (m/s^2)^2/Hz
    psd_g2 = psd_acc / (G0**2)
    return psd_acc, psd_g2


# ---------------------------------------------------------------------------
# Dome BOUNCE-mode PHYSICAL effective interface mass + forcing reverse-engineering.
# 93.5 Hz is the global axisymmetric bounce/breathing mode (whole top shell translating axially);
# its axial effective interface mass is a fraction of the dome cap mass (NOT the abstract 1 kg).
# ---------------------------------------------------------------------------
DOME_BOUNCE_PARTICIP = 0.40   # axial effective-mass fraction of the bounce mode (typical 0.3-0.5; sens.)


def dome_cap_geometry():
    """Surface area & mass of the 2:1 ellipsoidal dome cap (surface of revolution of the meridian)."""
    n = 4000
    phi = np.linspace(0.0, np.pi/2, n)
    x = DOME_R*np.cos(phi); z = DOME_HEIGHT*np.sin(phi)
    dx = np.gradient(x); dz = np.gradient(z)
    ds = np.sqrt(dx**2 + dz**2)
    area = float(np.sum(2*np.pi*np.abs(x)*ds))
    mass = area*DOME_T*DOME_RHO
    return area, mass


def dome_eff_interface_mass(particip=DOME_BOUNCE_PARTICIP):
    """Physical bounce-mode axial effective interface mass = particip * cap mass."""
    area, cap_mass = dome_cap_geometry()
    return particip*cap_mass, cap_mass, area


def reverse_engineer_force(dome_basis, m1_phys, f1_dome=DOME_F1_HZ, zeta_dome=DOME_ZETA1,
                           target_g2hz=0.1, freqs=None):
    """REVERSE-ENGINEER the flat ORIGINAL (+6 dB initial) force PSD [N^2/Hz] so the DOME-ONLY
    free-interface response PSD peaks at target_g2hz (=0.1 g^2/Hz) at the bounce mode. Same process
    that defined the round-2 original force, but applied to THIS (physical bounce-mode) dome.
    Returns (S_orig_n2_hz, peak_freq_hz, dome_resp_peak_per_unit_force_g2hz)."""
    if freqs is None:
        freqs = np.geomspace(20.0, 2000.0, 6000)
    Ys = np.asarray(source_accelerance(f1_dome, zeta_dome, jnp.asarray(freqs),
                                       dome_basis[0], dome_basis[1], m1_eff=m1_phys))
    Hg2 = np.abs(Ys/G0)**2                 # (g/N)^2 dome interface accelerance
    peak = float(Hg2.max()); fpk = float(freqs[np.argmax(Hg2)])
    S_orig = target_g2hz/peak              # flat original force PSD [N^2/Hz]
    return S_orig, fpk, peak


# Convenience: precompute FEM bases once (numpy constants for the JAX model)
def build_bases():
    fr, rr_fem, dome_f, dome_geom = dome_drivepoint_residue_ratios()
    flex_f, tray_geom = tray_flex_mode_ratios()
    # AXISYMMETRIC BOUNCE/BREATHING mode interface (CORRECTED, human review): 93.5 Hz (=0.85x110
    # nominal) is the dome's GLOBAL axisymmetric bounce mode (whole top shell translating axially), NOT
    # a local mount mode. Axial drive-point participation at the central apex concentrates in the bounce
    # mode; ovalling/lobar modes contribute ~0 axial response there -> drive-point residues decay
    # (~1/r^2). The free-tip strip FEM gives ~flat residues (rr_fem); we use the decay residues so the
    # bounce mode dominates the axial interface. NOTE: the physical bounce-mode EFFECTIVE MASS is large
    # (~150-250 kg), but m1_eff below is the ABSTRACT staged-2DOF value (1.0 kg) kept for
    # data-consistency. See known_failures.md sec.4 (re-run candidate). rr_fem retained for documentation.
    r_index = np.arange(1, len(fr) + 1, dtype=float)
    rr_local = 1.0 / r_index**2
    return dict(dome_freq_ratio=fr, dome_res_ratio=rr_local, dome_res_ratio_fem=rr_fem,
                dome_modes_raw=dome_f, dome_geom=dome_geom, tray_flex_f=flex_f, tray_geom=tray_geom)


if __name__ == "__main__":
    import json
    b = build_bases()
    print("dome FEM raw modes (Hz):", np.round(b["dome_modes_raw"], 2))
    print("dome freq ratios:", np.round(b["dome_freq_ratio"], 3))
    print("dome residue ratios:", np.round(b["dome_res_ratio"], 4))
    print("tray flex modes (Hz):", np.round(b["tray_flex_f"], 2))
    # show pressure effect
    f0, *_ = dome_fem(pressure=0.0)
    fp, *_ = dome_fem(pressure=DOME_P_OP)
    print("dome modes p=0   :", np.round(f0[:5], 2))
    print("dome modes p=3.5b:", np.round(fp[:5], 2))
