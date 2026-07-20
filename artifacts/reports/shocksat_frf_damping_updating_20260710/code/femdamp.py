#!/usr/bin/env python3
"""femdamp — damping-augmented FRF forward model for the FRF-domain damping updating loop (20260710).

Reuses the completed run's femlib (read-only) for the FE layer / Package; REPLACES only the fixed-zeta
resolvent in predict_logH with the DAMPING action space (card §5):
  1. band modal zeta  : zeta_i = zeta(band containing f_i)                       (<=4 params)
  2. Rayleigh         : zeta_i = alpha/(2 w_i) + beta w_i/2                        (2 params)
  3. structural eta   : composite per-mode loss factor eta_i = sum_g eta_g SE_{i,g},
                        SE_{i,g} = theta_g (Q_i^T A[g] Q_i)/lambda_i  (modal strain-energy fraction),
                        resolvent D = w_i^2 (1 + i eta_i) - w^2                    (<=2 joint groups)
All families are LOW-DIM + PHYSICAL; there is NO per-mode or per-channel free damping (anti-LSQ). A candidate
may combine viscous (band|rayleigh) + structural but total damping dim <= 10.

Damping is differentiable in its parameters (smooth resolvent) -> usable by NUTS.
"""
from __future__ import annotations
import os, sys
import numpy as np

# reuse the completed FE layer read-only; redirect its workspace to OURS for package IO.
# IMPORTANT: put OUR code dir FIRST and the reused dir LAST so our modules (esp. score.py) win any name
# collision with the completed run's code (which also has a score.py).
_MYCODE = os.path.dirname(os.path.abspath(__file__))
_TRL = os.path.abspath(os.path.join(_MYCODE, "..", "..",
                                    "shocksat_true_remodel_loop_20260706", "code"))
sys.path.insert(0, _MYCODE)
sys.path.append(_TRL)
import femlib as F  # noqa: E402
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))    # our workspace
F.WS = WS                                                          # redirect femlib IO (data/packages) to ours

BAND = F.BAND
G_IN_S2 = F.G_IN_S2
BAND_EDGES = np.array([45.0, 69.8, 108.2, 167.7, 260.0])   # D8: 4 geometric bands
JOINT_GROUPS = ("joints", "contact")                       # structural-eta groups (CBUSH)

# hard physical-damping gate bounds (quantity_contracts / assumptions_ledger)
ZETA_LO, ZETA_HI = 0.002, 0.05
ETA_HI = 0.20


# ------------------------------------------------------------- damping spec -> per-mode zeta / eta
def band_zeta(freqs_hz, zeta_bands, edges=BAND_EDGES):
    """Piecewise-constant zeta over `edges`; freqs outside clamp to nearest band."""
    zeta_bands = np.asarray(zeta_bands, float)
    idx = np.clip(np.digitize(np.asarray(freqs_hz, float), edges) - 1, 0, len(zeta_bands) - 1)
    return zeta_bands[idx]


def rayleigh_zeta(freqs_hz, alpha, beta):
    w = 2 * np.pi * np.asarray(freqs_hz, float)
    return alpha / (2 * w) + beta * w / 2.0


def strain_energy_fractions(pkg, theta, Q, lam, inb):
    """SE_{i,g} = theta_g (Q_i^T A[g] Q_i)/lambda_i for each free group g, in-band modes only.
    Returns dict group -> array over in-band modes. A[g], A_fix stored on the package."""
    A = np.asarray(pkg.A)                      # (n_free, n, n)
    theta = np.asarray(theta, float)
    Qi = Q[:, inb]                             # (n, n_inb)
    lam_i = np.asarray(lam)[inb]               # (n_inb,)  == (2 pi f_i)^2
    out = {}
    for gi, gname in enumerate(pkg.free_names):
        # quadratic form Q_i^T A_g Q_i per in-band mode
        qf = np.einsum("mi,mn,ni->i", Qi, A[gi], Qi)
        out[gname] = theta[gi] * qf / np.clip(lam_i, 1e-30, None)
    return out


def structural_eta(pkg, theta, Q, lam, inb, eta_groups):
    """Composite per-mode loss factor eta_i = sum_{g in eta_groups} eta_g SE_{i,g}."""
    if not eta_groups:
        return np.zeros(len(inb))
    SE = strain_energy_fractions(pkg, theta, Q, lam, inb)
    eta_i = np.zeros(np.size(inb))
    for g, val in eta_groups.items():
        if g in SE:
            eta_i = eta_i + float(val) * SE[g]
    return eta_i


def per_mode_damping(pkg, theta, damping, f, Q, lam, inb):
    """Return (zeta_i, eta_i) arrays over in-band modes for a damping spec dict.
    damping kinds: 'fixed'|'band'|'rayleigh' (viscous) optionally + 'eta' (structural, per joint group)."""
    fi = f[inb]
    kind = damping.get("kind", "fixed")
    if kind == "fixed":
        zeta_i = np.full(len(fi), float(damping.get("zeta", 0.01)))
    elif kind == "band":
        zeta_i = band_zeta(fi, damping["zeta"], damping.get("edges", BAND_EDGES))
    elif kind == "rayleigh":
        zeta_i = rayleigh_zeta(fi, float(damping["alpha"]), float(damping["beta"]))
    else:
        raise ValueError(f"unknown viscous damping kind {kind}")
    eta_groups = damping.get("eta", {})       # {group: eta_g}
    eta_i = structural_eta(pkg, theta, Q, lam, inb, eta_groups)
    return zeta_i, eta_i


# ------------------------------------------------------------- damped modal FRF
def frf_from_modes(residues, wi, zeta_i, eta_i, fc):
    """Complex accelerance H (n_chan, n_freq) from modal residues R_{c,i}=U_s,i U_d,i and per-mode damping.
    Viscous+structural combined resolvent: D_i = w_i^2 (1 + i eta_i) - w^2 + 2 i zeta_i w_i w."""
    w = 2 * np.pi * np.asarray(fc, float)
    wi = np.asarray(wi, float)
    D = (wi[None, :] ** 2) * (1.0 + 1j * np.asarray(eta_i)[None, :]) \
        - (w ** 2)[:, None] + 2j * np.asarray(zeta_i)[None, :] * wi[None, :] * w[:, None]
    # H(f, chan) = -w^2 * sum_i residues[chan,i]/D[f,i]
    H = -(w ** 2)[None, :] * (np.asarray(residues)[:, None, :] / D[None, :, :]).sum(-1)
    return H  # (n_chan, n_freq)


def predict_H_damped(pkg, theta, damping, dkey, fc):
    """COMPLEX accelerance H (n_sens, n_freq) in g/lbf BEFORE global gain, with the damping action space.
    NO per-mode/per-channel fitting. Mirrors femlib.predict_logH math but with variable damping."""
    f, Q = pkg.modes(theta)
    lam = (2 * np.pi * f) ** 2
    inb = np.where((f >= BAND[0] - 10) & (f <= BAND[1] + 40))[0]
    Us = np.asarray(pkg.sens_rows) @ Q[:, inb]          # (n_sens, n_inb)
    Ud = np.asarray(pkg.drives[dkey]) @ Q[:, inb]       # (n_inb,)
    residues = Us * Ud[None, :]                         # (n_sens, n_inb)
    wi = 2 * np.pi * f[inb]
    zeta_i, eta_i = per_mode_damping(pkg, theta, damping, f, Q, lam, inb)
    return frf_from_modes(residues, wi, zeta_i, eta_i, fc) / G_IN_S2


def predict_logH_damped(pkg, theta, damping, dkey, fc):
    """log10|H| (n_sens, n_freq) accelerance g/lbf BEFORE global gain, with the damping action space."""
    return np.log10(np.abs(predict_H_damped(pkg, theta, damping, dkey, fc)) + 1e-300)


def damping_dim(damping):
    """Number of free damping parameters in a spec (checker: <=10)."""
    kind = damping.get("kind", "fixed")
    n = {"fixed": 0, "band": len(np.atleast_1d(damping.get("zeta", []))), "rayleigh": 2}.get(kind, 0)
    n += len(damping.get("eta", {}))
    return int(n)


# ------------------------------------------------------------- analytic reference FRFs (Gate D1)
def analytic_sdof_accelerance(fn_hz, zeta, fc):
    """1-DOF unit-modal accelerance: H = -w^2/(wn^2 - w^2 + 2 i zeta wn w). Peak |H|(wn)=1/(2 zeta)."""
    return frf_from_modes(np.array([[1.0]]), np.array([2 * np.pi * fn_hz]),
                          np.array([zeta]), np.array([0.0]), fc)[0]


def analytic_sdof_structural(fn_hz, eta, fc):
    """1-DOF structural: H = -w^2/(wn^2(1+i eta) - w^2). Peak |H|(wn)=1/eta."""
    return frf_from_modes(np.array([[1.0]]), np.array([2 * np.pi * fn_hz]),
                          np.array([0.0]), np.array([eta]), fc)[0]
