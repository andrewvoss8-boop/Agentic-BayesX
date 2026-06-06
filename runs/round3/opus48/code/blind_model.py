#!/usr/bin/env python3
"""Clean engineering forward model for the BLIND round-3 inference (vs Codex independent truth).

I (the inference runner) consume ONLY runs/round3/codex_truth/dataset/observations.npz +
data_contract.md. I must NOT read the sealed truth or Codex's generator code. This module builds a
COARSE, LINEAR, SYMMETRIC design model of the SAME NOMINAL SYSTEM (dome bounce ~93.5 Hz, tray ~86.25 Hz,
6 equal struts, single interface) as a real engineer would from the nominal design -- NOT a reverse
engineering of the hidden as-built structure.

Modelled quantity: the published per-build 6-DOF DIAGONAL interface APPARENT MASS (kg / kg*m^2).
The published channel is the COUPLED interface apparent mass (its low-frequency asymptote is large:
~520-760 because the interface drives the dome's large effective bounce mass + the load + interface
hardware together). So:

    M_diag(w) = M_base6_rigid            (lumped dome+interface effective mass/inertia; low-f asymptote)
              + hexapod_condensed(w; k_strut, M_tray6)   (the 6 mount-mode resonances)
              + dome_axial_resonator(w; m_dome, f_dome)  (axial dome bounce, on z only)

Reading the rigid-body mass off the measured low-f apparent-mass asymptote is STANDARD apparent-mass
practice (a direct measurement), not peeking at hidden structure. The rest is the nominal design model;
its coarseness (6 equal struts, single axial dome mode, fixed damping, magnitude-only) is the source of
the model-form error we expect to bias us -- reported honestly.

Units SI. Frame: x,y transverse (tray plane); z axial (dome->tray, +up); rotations RH about x,y,z.
DOF order = [x,y,z,rx,ry,rz].
"""
from __future__ import annotations
import math
from pathlib import Path
import numpy as np
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

import tray_hexapod as hx   # geometry + 6x6 condensation blocks (shared nominal hexapod)

HERE = Path(__file__).resolve().parents[1]
DATASET = HERE.parent / "codex_truth" / "dataset" / "observations.npz"

DOF = ["x", "y", "z", "rx", "ry", "rz"]
NDOF = 6
ETA = 0.04            # fixed structural loss (finite FRF peaks; magnitude-only -> weakly identified; FIXED)
M_DOME_FRAC = 0.45    # fraction of the axial base mass that resonates as the dome bounce (nominal)

# ----- nominal tray rigid-body properties (design estimate, NOT read from the hidden truth) -----
# Load = 170 kg (data_contract load_mass_kg) on the hexapod; radius of gyration ~0.6 m.
M_TRAY = 170.0
R_TRAY = 0.60
IXX = IYY = 0.25 * M_TRAY * R_TRAY**2
IZZ = 0.50 * M_TRAY * R_TRAY**2
M_TRAY6 = np.array([M_TRAY, M_TRAY, M_TRAY, IXX, IYY, IZZ])

# unit-stiffness condensation blocks for the 6-strut hexapod (k_strut scales these linearly)
KTT_U, KTB_U, KBB_U = hx.assemble(np.ones(6))


def load_observations(path=DATASET):
    d = np.load(path, allow_pickle=True)
    AM = d["apparent_mass_real"] + 1j * d["apparent_mass_imag"]   # (8,6,nf)
    return dict(
        f=d["frequency_hz"], dof=[str(x) for x in d["dof_order"]],
        AM=AM, mag=np.abs(AM),                                    # (8,6,nf)
        logmag=np.log(np.abs(AM)),                               # (8,6,nf) log|apparent mass|
        resp_psd=d["response_psd_g2_per_Hz"], netcg=d["netcg_3grms_g"],
        design_force=d["design_force_psd_N2_per_Hz"], flight_force=d["flight_force_psd_N2_per_Hz"],
        load_mass=float(d["load_mass_kg"]), g0=float(d["g0_m_per_s2"]),
        build_ids=d["build_ids"], flight_ids=d["flight_ids"],
    )


def rigid_base_from_asymptote(obs, n_low=8):
    """M_base6_rigid set so the model low-f asymptote matches the MEASURED low-f apparent-mass asymptote
    (build-averaged over the lowest n_low grid points). Standard rigid-body read-off, per DOF. The axial
    (z) entry has the dome-resonator low-f mass removed so the total z low-f still equals the measurement.
    Returns (M_base6, m_dome) where m_dome = M_DOME_FRAC * (measured_z_lowf - tray_z)."""
    lf = obs["mag"][:, :, :n_low].mean(axis=(0, 2))   # (6,) measured low-f asymptote per DOF
    M_base6 = lf - M_TRAY6                              # remove tray rigid contribution
    M_base6 = np.clip(M_base6, 1.0, None)              # keep positive (coarse)
    m_dome = M_DOME_FRAC * max(lf[2] - M_TRAY6[2], 1.0)
    M_base6 = M_base6.copy()
    M_base6[2] = M_base6[2] - m_dome                    # take the dome-resonator mass out of the z rigid part
    M_base6[2] = max(M_base6[2], 1.0)
    return M_base6, float(m_dome), lf


def hexapod_appmass_diag_jax(k_strut, freqs):
    """Diagonal condensed interface apparent mass of the rigid tray on 6 equal axial struts (JAX,
    differentiable in k_strut). Complex structural damping eta. Returns (nf,6) complex."""
    w = 2 * jnp.pi * freqs
    s = k_strut * (1 + 1j * ETA)
    Ktt = s * jnp.asarray(KTT_U); Ktb = s * jnp.asarray(KTB_U); Kbb = s * jnp.asarray(KBB_U)
    Mm = jnp.asarray(np.diag(M_TRAY6))

    def one(wj):
        D = Ktt - (wj**2) * Mm
        Zb = Kbb - Ktb.T @ jnp.linalg.solve(D, Ktb)
        return jnp.diag(-Zb / (wj**2))
    return jax.vmap(one)(w)   # (nf,6) complex


def dome_resonator_zz(m_dome, f_dome, freqs):
    """Driving-point apparent mass of the axial dome bounce as a free SDOF resonator (JAX):
    M(w) = m_dome * wd^2 (1+i eta) / (wd^2 (1+i eta) - w^2). Low-f -> m_dome; peaks at f_dome; ->0 above."""
    w = 2 * jnp.pi * freqs
    wd2 = (2 * jnp.pi * f_dome) ** 2 * (1 + 1j * ETA)
    return m_dome * wd2 / (wd2 - w**2)   # (nf,) complex


def forward_logmag(k_strut, f_dome, M_base6, m_dome, freqs):
    """Full model: diagonal interface apparent mass magnitude (log), shape (6, nf). JAX-differentiable in
    k_strut and f_dome (M_base6, m_dome fixed from the asymptote)."""
    hexa = hexapod_appmass_diag_jax(k_strut, freqs)              # (nf,6)
    base = jnp.asarray(M_base6)[None, :]                          # (1,6) rigid
    M = hexa + base                                              # (nf,6)
    # add the dome axial resonator to z (index 2)
    dz = dome_resonator_zz(m_dome, f_dome, freqs)                # (nf,)
    M = M.at[:, 2].add(dz)
    return jnp.log(jnp.abs(M)).T                                 # (6, nf)


def nominal_k_strut(target_axial_hz=86.25):
    """Calibrate the uniform strut stiffness so the AXIAL mount mode = nominal design 86.25 Hz."""
    kj, _ = hx.calibrate_kj(target_axial_hz)
    return float(kj)


# ---------------------------------------------------------------------------------------------------
def _validate():
    """Quick sanity check vs the published data gross features (NOT the inference)."""
    import json
    from scipy.signal import find_peaks
    obs = load_observations()
    f = obs["f"]
    M_base6, m_dome, lf = rigid_base_from_asymptote(obs)
    k0 = nominal_k_strut(86.25)
    f_dome0 = 93.5
    print("nominal k_strut=%.3e N/m  m_dome=%.1f kg  f_dome=%.1f Hz" % (k0, m_dome, f_dome0))
    print("measured low-f asymptote per DOF:", np.round(lf, 1))
    print("M_base6 rigid (after tray+dome removal):", np.round(M_base6, 1))
    print("nominal hexapod modes (Hz):", np.round(hx.modes(np.full(6, k0)), 2))
    mu = np.asarray(forward_logmag(k0, f_dome0, M_base6, m_dome, jnp.asarray(f)))  # (6,nf)
    model_mag = np.exp(mu)
    data_mag = obs["mag"].mean(axis=0)   # (6,nf)
    print("\nDOF | model_lf | data_lf | model peaks (Hz) | data peaks (Hz)")
    for i, nm in enumerate(DOF):
        mp, _ = find_peaks(model_mag[i], prominence=model_mag[i].max() * 0.05)
        mp = np.sort(mp[np.argsort(model_mag[i][mp])[::-1][:4]])
        dp, _ = find_peaks(data_mag[i], prominence=data_mag[i].max() * 0.05)
        dp = np.sort(dp[np.argsort(data_mag[i][dp])[::-1][:4]])
        print(f"{nm}: {model_mag[i,0]:7.0f} {data_mag[i,0]:7.0f} | {np.round(f[mp],1)} | {np.round(f[dp],1)}")


if __name__ == "__main__":
    _validate()
