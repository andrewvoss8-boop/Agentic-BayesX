#!/usr/bin/env python3
"""wforward — resolution-consistent (window-matched) FRF forward paths for the 20260713 study.

Reuses (read-only) the damping run's femdamp + the true-remodel femlib. Adds:
  * the EXACT measurement-window operator W (quantity_contracts.md; decisions D1): closed-form DFT of the
    sampled, exponentially-windowed, frame-truncated modal impulse response (finite geometric sums). Recovered
    processing constants from modal_multiref.py / multiref_frf.py / realfrf.py: N=122880 @ 250 kHz, exp
    response window end=0.05, impact at pre_gap=200, H1 band bins 45-260 Hz.
  * damping kind 'permode_survey_interp': per-mode zeta from the 33-mode .ash survey by frequency
    interpolation (fixed measured DATA — zero free parameters).

NO-PER-MODE-LSQ: nothing in this module or its callers fits damping or amplitude; damping is a fixed
pre-registered spec; theta is the reused multi-start theta_MAP. LOW-DIM-PHYSICAL-DAMPING-ONLY.
All arms are viscous-only: structural eta is asserted ZERO (assumptions A6).
"""
from __future__ import annotations
import os, sys
import numpy as np

_MY = os.path.dirname(os.path.abspath(__file__))
_DWS = os.path.abspath(os.path.join(_MY, "..", "..", "shocksat_frf_damping_updating_20260710", "code"))
sys.path.insert(0, _DWS)                     # damping run code (femdamp chains femlib + package IO paths)
import femdamp as D                          # noqa: E402  (sets femlib WS -> damping run's data/packages)
import femlib as F                           # noqa: E402

WS = os.path.abspath(os.path.join(_MY, ".."))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
BAND = D.BAND
G_IN_S2 = D.G_IN_S2

# ---- recovered distillation constants (assumptions A1; sources hashed in REUSED_code.sha256) ----
FS = 250000.0
NFRAME = 122880
PRE_GAP = 200
EXP_END = 0.05
DT = 1.0 / FS
T_FRAME = NFRAME / FS                                    # 0.49152 s
RHO_WIN = float(np.exp(np.log(EXP_END) / (NFRAME - 1)))  # per-sample window ratio
W_N0 = RHO_WIN ** PRE_GAP                                # window value at the impact sample (~0.99512)
TAU_WIN = -(NFRAME - 1) / (FS * np.log(EXP_END))         # 0.164066 s
SIGMA_W = 1.0 / TAU_WIN                                  # 6.0951 1/s added decay rate
M_SUM = NFRAME - PRE_GAP                                 # samples of decay inside the frame


def zeta_w(f_hz):
    """Window-added apparent damping ratio at frequency f (realfrf.measured_zeta_w, recomputed here)."""
    return SIGMA_W / (2.0 * np.pi * np.asarray(f_hz, float))


# ------------------------------------------------------------------ survey per-mode damping (fixed data)
_SURVEY = None


def survey_table():
    global _SURVEY
    if _SURVEY is None:
        mm = np.load(os.path.join(ROOT, "artifacts/reports/shocksat_fem_remesh_20260618/measured_modes.npz"))
        fr = np.asarray(mm["freqs"], float)
        zt = np.asarray(mm["damp"], float) / 100.0       # percent critical -> ratio (damping run D7)
        order = np.argsort(fr)
        _SURVEY = (fr[order], zt[order])
    return _SURVEY


def per_mode_zeta(damping, fi):
    """Per-mode viscous zeta for the pre-registered damping kinds. fi = in-band mode freqs [Hz]."""
    kind = damping.get("kind", "fixed")
    if kind == "fixed":
        return np.full(len(fi), float(damping["zeta"]))
    if kind == "band":
        return D.band_zeta(fi, damping["zeta"], damping.get("edges", D.BAND_EDGES))
    if kind == "permode_survey_interp":
        fs_, zs_ = survey_table()
        return np.interp(np.asarray(fi, float), fs_, zs_)     # end-clamped; zero free parameters
    if kind == "permode_survey_nearest":                      # A3 sensitivity variant ONLY (not an arm)
        fs_, zs_ = survey_table()
        j = np.argmin(np.abs(np.asarray(fi, float)[:, None] - fs_[None, :]), axis=1)
        return zs_[j]
    raise ValueError(f"unknown damping kind {kind}")


# ------------------------------------------------------------------ modal layer (mirrors femdamp exactly)
def modal_quantities(pkg, theta, dkey):
    """(residues (n_sens,n_inb), fi (n_inb,)) exactly as femdamp.predict_H_damped builds them."""
    f, Q = pkg.modes(theta)
    inb = np.where((f >= BAND[0] - 10) & (f <= BAND[1] + 40))[0]
    Us = np.asarray(pkg.sens_rows) @ Q[:, inb]
    Ud = np.asarray(pkg.drives[dkey]) @ Q[:, inb]
    return Us * Ud[None, :], f[inb]


# ------------------------------------------------------------------ the two forward paths
def predict_H(pkg, theta, damping, dkey, fc, windowed):
    """Complex accelerance H (n_sens, n_freq) in g/lbf BEFORE global gain.
    windowed=False -> naive analytic modal FRF (bit-identical math to femdamp.frf_from_modes);
    windowed=True  -> the exact measurement-window operator W (quantity_contracts.md)."""
    residues, fi = modal_quantities(pkg, theta, dkey)
    zi = per_mode_zeta(damping, fi)
    if not windowed:
        wi = 2 * np.pi * fi
        return D.frf_from_modes(residues, wi, zi, np.zeros(len(fi)), fc) / G_IN_S2
    return _windowed_H(residues, fi, zi, fc) / G_IN_S2


def predict_logH(pkg, theta, damping, dkey, fc, windowed):
    return np.log10(np.abs(predict_H(pkg, theta, damping, dkey, fc, windowed)) + 1e-300)


def _windowed_H(residues, fi, zi, fc):
    """W[H](f_k) = sum_i R_i [ -w[n0] + dt (r+ S(z+,k) + r- S(z-,k)) ],  S(z)=(1-z^M)/(1-z).
    Exact closed form of the distillation processing applied to the modal model (D1). fc must be (a subset
    of) the frame's rfft bins; each f is snapped to its exact bin k=round(f*NFRAME/FS) (cache freqs ARE bins).
    """
    fc = np.asarray(fc, float)
    k = np.round(fc * NFRAME / FS).astype(int)                # exact DFT bins (max snap err < 1e-9 Hz)
    wn = 2 * np.pi * np.asarray(fi, float)                    # (nm,)
    zi = np.clip(np.asarray(zi, float), 1e-8, 0.999)
    sig = zi * wn
    wd = wn * np.sqrt(1.0 - zi ** 2)
    p_pl = -sig + 1j * wd                                     # (nm,) upper pole
    # residue of the proper part (2 zeta wn s + wn^2)/(s^2+2 zeta wn s + wn^2) at p+ ; r- = conj(r+)
    r_pl = (2.0 * sig * p_pl + wn ** 2) / (2j * wd)
    ephi = np.exp(-2j * np.pi * k / NFRAME)                   # (nk,)
    zp = (RHO_WIN * np.exp(p_pl * DT))[:, None] * ephi[None, :]          # (nm, nk)
    zm = (RHO_WIN * np.exp(np.conj(p_pl) * DT))[:, None] * ephi[None, :]
    Sp = (1.0 - zp ** M_SUM) / (1.0 - zp)
    Sm = (1.0 - zm ** M_SUM) / (1.0 - zm)
    term = -W_N0 + DT * (r_pl[:, None] * Sp + np.conj(r_pl)[:, None] * Sm)   # (nm, nk)
    return np.asarray(residues) @ term                        # (n_sens, nk)


# ------------------------------------------------------------------ synthetic single-mode helper (Gate K)
def sdof_windowed(fn_hz, zeta, fc):
    """Windowed unit-residue 1-DOF accelerance (physical units, no /G)."""
    return _windowed_H(np.array([[1.0]]), np.array([fn_hz]), np.array([zeta]), fc)[0]


def sdof_naive(fn_hz, zeta, fc):
    return D.analytic_sdof_accelerance(fn_hz, zeta, fc)
