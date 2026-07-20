#!/usr/bin/env python3
"""metrics — FRF-domain correlation metrics for the damping updating loop (20260710).

FRAC (correlation form), FDAC (improved cosine, phase-sensitive), FRSF (amplitude scale factor), and the
train-side frequency-alignment warp built from the FDAC ridge. Definitions per quantity_contracts.md.

Conventions:
  * FRAC/P1'/P3 use the SIGNED Pearson correlation of mean-removed log10|H| (matches the completed run's P1,
    so P1'-P3 is a clean alignment-gain; FRAC_squared = corr^2 also available).
  * FDAC surface aggregates over sensors (vector at a frequency) -> ridge = frequency-shift map. cosine form
    in [-1,1] so a 180-deg phase flip scores -1 (not +1).
  * The alignment warp is a LOW-DIM (global or per-band scale rho, fe = rho*fa) train-side field; it is NEVER
    fit per channel to the dev/vault data (no overfitting).
"""
from __future__ import annotations
import numpy as np

EPS = 1e-300


def logmag(H):
    return np.log10(np.abs(np.asarray(H)) + EPS)


# ---------------------------------------------------------------- FRAC (correlation form)
def frac_corr(yp, ym):
    """Signed Pearson correlation of two real log-magnitude curves (mean-removed). [-1,1]."""
    yp = np.asarray(yp, float); ym = np.asarray(ym, float)
    if yp.std() < 1e-12 or ym.std() < 1e-12:
        return np.nan
    return float(np.corrcoef(yp, ym)[0, 1])


def frac_squared(yp, ym):
    c = frac_corr(yp, ym)
    return np.nan if np.isnan(c) else c * c


# ---------------------------------------------------------------- FDAC (improved cosine)
def fdac_surface(Hp, Hm, cosine=True):
    """FDAC over (analysis freq fa index, test freq fe index).
    Hp, Hm: (n_sens, n_freq) complex. cosine=True -> real inner product / norms in [-1,1]."""
    Hp = np.asarray(Hp); Hm = np.asarray(Hm)
    np_ = np.linalg.norm(Hp, axis=0)            # (n_fa,)
    nm_ = np.linalg.norm(Hm, axis=0)            # (n_fe,)
    cross = Hp.conj().T @ Hm                     # (n_fa, n_fe) complex
    denom = np.outer(np_, nm_) + EPS
    if cosine:
        return np.real(cross) / denom            # phase-sensitive, [-1,1]
    return (np.abs(cross) ** 2) / (denom ** 2)   # classic MAC-like, [0,1]


def fdac_ridge(FDAC, fa, fe, max_shift=None):
    """Ridge fe*(fa) = argmax_fe FDAC(fa,fe), restricted to a PHYSICAL shift window |fe/fa-1|<=max_shift so
    the ridge cannot collapse onto a distant dominant resonance (the degeneracy that gave nonphysical rho on
    real data). Returns (fa, fe_star, ridge_value); ridge_value=0 where no fe lies in the window."""
    fa = np.asarray(fa, float); fe = np.asarray(fe, float)
    if max_shift is not None:
        win = np.abs(fe[None, :] / fa[:, None] - 1.0) <= max_shift
        F2 = np.where(win, FDAC, -np.inf)
    else:
        F2 = FDAC
    j = np.argmax(F2, axis=1)
    val = F2[np.arange(F2.shape[0]), j]
    val = np.where(np.isfinite(val), val, 0.0)
    return fa, fe[j], val


# ---------------------------------------------------------------- alignment warp (train-side)
def _weighted_median(x, w):
    idx = np.argsort(x); x, w = np.asarray(x)[idx], np.asarray(w)[idx]
    cw = np.cumsum(w)
    return float(x[np.searchsorted(cw, 0.5 * cw[-1])])


def estimate_scale_warp(fa, fe_star, ridge_val, vmin=0.3, max_shift=0.06):
    """Robust scale rho (fe=rho*fa) = weighted MEDIAN of fe/fa over clean ridge points (ridge_val>=vmin),
    clipped to the physical window [1-max_shift, 1+max_shift]. Median (not mean) resists the dominant-peak
    pull; the clip guards residual degeneracy. Returns 1.0 if too few clean points."""
    m = (ridge_val >= vmin) & (fa > 0)
    if m.sum() < 5:
        return 1.0
    ratios = fe_star[m] / fa[m]
    rho = _weighted_median(ratios, np.clip(ridge_val[m], 1e-6, None))
    return float(np.clip(rho, 1.0 - max_shift, 1.0 + max_shift))


def apply_scale_warp(logHp, fc, rho):
    """Align predicted log|H| onto the measured grid: warped(fe) = logHp(fe/rho) via linear interp.
    logHp: (..., n_freq) evaluated at fc. Returns same shape, resampled."""
    fc = np.asarray(fc, float)
    src = fc / max(rho, 1e-6)
    lo, hi = fc[0], fc[-1]
    out = np.empty_like(np.asarray(logHp, float))
    L = np.atleast_2d(logHp)
    O = np.atleast_2d(out)
    for i in range(L.shape[0]):
        O[i] = np.interp(src, fc, L[i], left=L[i, 0], right=L[i, -1])
    return O.reshape(np.asarray(logHp).shape)


def fdac_band_select(fa, fe_star, ridge_val, vmin=0.5):
    """Boolean mask over analysis frequencies where the ridge is clean (value>=vmin) -> updating band."""
    return np.asarray(ridge_val, float) >= vmin


# ---------------------------------------------------------------- FRSF (amplitude scale factor)
def frsf(Hp, Hm, peak_idx=None):
    """Amplitude scale factor measured/predicted at (matched) peaks. If Hp = c*Hm elementwise, FRSF = 1/c.
    Returns (frsf_median, frsf_db_median, abs_err=|frsf-1|)."""
    Hp = np.abs(np.asarray(Hp)); Hm = np.abs(np.asarray(Hm))
    if peak_idx is not None and len(peak_idx):
        Hp = Hp[..., peak_idx]; Hm = Hm[..., peak_idx]
    ratio = (Hm + EPS) / (Hp + EPS)
    r = float(np.median(ratio))
    return r, float(20.0 * np.log10(r)), float(abs(r - 1.0))
