#!/usr/bin/env python3
"""Adaptive frequency grid for structural-dynamics FRF/PSD work (Claude Code Opus 4.8 runner).

Standard for this problem class: DO NOT hardcode the frequency vector. Because we have an FEM we KNOW
the modal frequencies (and damping) from the eigensolve, so we place DENSE points only where they matter
(around each resonance, within a few half-power bandwidths ~ zeta*fn) on top of a COARSE log-spaced
(octave-like) baseline everywhere else. This maximizes QOI/FRF accuracy for a given point budget and
keeps the cost low in the flat low/high-frequency regions. Nothing is hardcoded: the dense clusters are
derived from the solved modes and their damping.

Use: grid = adaptive_frequency_grid(modes_hz, zetas, fmin, fmax)
"""
from __future__ import annotations
import numpy as np


def adaptive_frequency_grid(modes_hz, zetas, fmin, fmax, base_per_decade=14,
                            pts_per_mode=25, n_halfwidths=6, min_halfwidth_frac=2e-3):
    """Log-spaced baseline + mode-local refinement.
    modes_hz, zetas : solved natural frequencies and modal damping ratios (zetas may be scalar).
    base_per_decade : coarse baseline density (octave-like).
    pts_per_mode    : points placed across each mode's +/- n_halfwidths*bandwidth window.
    Returns a sorted unique 1-D grid over [fmin, fmax]. No hardcoded frequencies."""
    modes = np.atleast_1d(np.asarray(modes_hz, float))
    z = np.atleast_1d(np.asarray(zetas, float))
    if z.size == 1:
        z = np.full(modes.shape, float(z))
    n_base = max(int(base_per_decade*np.log10(fmax/fmin)) + 1, 8)
    pts = [np.geomspace(fmin, fmax, n_base)]
    for fn, zn in zip(modes, z):
        if not (fmin < fn < fmax):
            continue
        hw = max(zn*fn, min_halfwidth_frac*fn)          # half-power half-bandwidth ~ zeta*fn
        lo = max(fn - n_halfwidths*hw, fmin)
        hi = min(fn + n_halfwidths*hw, fmax)
        pts.append(np.geomspace(lo, hi, pts_per_mode))
    return np.unique(np.concatenate(pts))


def points_in_halfpower_bands(grid, modes_hz, zetas):
    """Diagnostic: number of grid points inside each mode's half-power band [fn(1-zeta), fn(1+zeta)]."""
    modes = np.atleast_1d(np.asarray(modes_hz, float)); z = np.atleast_1d(np.asarray(zetas, float))
    if z.size == 1:
        z = np.full(modes.shape, float(z))
    return {float(round(fn, 2)): int(np.sum((grid >= fn*(1-zn)) & (grid <= fn*(1+zn))))
            for fn, zn in zip(modes, z)}


# --------------------------- demonstration ---------------------------
def _demo():
    import sys, json, math
    from pathlib import Path
    HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE/"code"))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    import statfem_hexapod as hxs, tray_hexapod as hx, mdof_forward as mdof
    import jax.numpy as jnp

    kj, _ = hx.calibrate_kj(86.25)
    tray_modes = hx.modes(np.full(6, kj))                       # 6 mount modes
    dome_modes = mdof.DOME_F1_HZ*mdof.build_bases()["dome_freq_ratio"][:4]   # dome bounce + higher
    modes = np.unique(np.round(np.concatenate([tray_modes, dome_modes]), 2))
    ZETA = 0.015                                                # realistic LIGHT modal damping (Q~33)
    zetas = np.full(len(modes), ZETA)
    fmin, fmax = 20.0, 2000.0

    # PEAK-DOMINATED QOI: a modal-superposition accelerance response 3*GRMS (the resonances dominate the
    # variance for light damping -> resolving peaks matters). This is the regime where adaptive wins.
    def accel(fg):
        w = 2*np.pi*fg; A = np.zeros_like(fg, dtype=complex)
        for fr in modes:
            wr = 2*np.pi*fr
            A += (-(w**2))/(wr**2 - w**2 + 2j*ZETA*wr*w)        # unit-residue accelerance
        return np.abs(A)
    def grms(fg):
        return 3.0*np.sqrt(np.trapz(accel(fg)**2, fg))         # 3*GRMS of |A| (flat input)

    grid = adaptive_frequency_grid(modes, zetas, fmin, fmax)
    N = len(grid)
    uni = np.geomspace(fmin, fmax, N)                          # uniform-log with SAME point count
    ref = np.geomspace(fmin, fmax, 60000)                      # dense reference
    q_ref = grms(ref); q_ad = grms(grid); q_un = grms(uni)
    err_ad = abs(q_ad-q_ref)/q_ref; err_un = abs(q_un-q_ref)/q_ref

    # PEAK-HEIGHT fidelity (the 'no clipped peaks' / modal-ID / narrow-band-exceedance use case)
    def peak_err(fg):
        errs = []
        for fr in modes:
            win = (ref >= fr*(1-4*ZETA)) & (ref <= fr*(1+4*ZETA)); pref = accel(ref[win]).max()
            wg = (fg >= fr*(1-4*ZETA)) & (fg <= fr*(1+4*ZETA))
            pk = accel(fg[wg]).max() if wg.any() else 0.0
            errs.append(abs(pk-pref)/pref)
        return float(np.mean(errs)), float(np.max(errs))
    pkmean_ad, pkmax_ad = peak_err(grid); pkmean_un, pkmax_un = peak_err(uni)
    bands_ad = points_in_halfpower_bands(grid, modes, zetas)
    bands_un = points_in_halfpower_bands(uni, modes, zetas)
    summary = {"n_points": N, "modes_hz": [round(float(x), 2) for x in np.unique(np.round(modes, 1))],
               "PEAK_HEIGHT_mean_err_adaptive": pkmean_ad, "PEAK_HEIGHT_mean_err_uniform_log": pkmean_un,
               "PEAK_HEIGHT_max_err_adaptive": pkmax_ad, "PEAK_HEIGHT_max_err_uniform_log": pkmax_un,
               "peak_fidelity_improvement_x": float(pkmean_un/max(pkmean_ad, 1e-12)),
               "integrated_3grms_rel_err_adaptive": err_ad, "integrated_3grms_rel_err_uniform_log": err_un,
               "min_pts_in_halfpower_adaptive": int(min(bands_ad.values())),
               "min_pts_in_halfpower_uniform": int(min(bands_un.values())),
               "note": "Adaptive WINS on PEAK FIDELITY (peak height / no-clipped-peaks / narrow-band "
                       "exceedance) at matched cost. The INTEGRATED 3*GRMS is grid-robust either way; a "
                       "matched-N adaptive grid can even be slightly worse on the integral if its log "
                       "baseline is starved -> rule: keep an adequate log baseline AND add mode-local "
                       "refinement (use adaptive for peak-sensitive outputs; ensure baseline for integrals)."}
    (HERE/"report"/"adaptive_freq_summary.json").write_text(json.dumps(summary, indent=2))

    fig, axes = plt.subplots(2, 1, figsize=(11, 8))
    ax = axes[0]
    ax.loglog(ref, accel(ref), color="#bbbbbb", lw=1.0, label="reference FRF (60k pts)")
    ax.loglog(uni, accel(uni), "x", ms=4, color="#999999", alpha=0.6, label=f"uniform-log ({N} pts) — clips peaks")
    ax.loglog(grid, accel(grid), ".", ms=4, color="#1f77b4", label=f"adaptive grid ({N} pts)")
    for fn in np.unique(np.round(modes, 1)):
        ax.axvline(fn, color="#d62728", ls=":", lw=0.6)
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("|accelerance|")
    ax.set_title(f"Adaptive grid (dense at solved modes, coarse elsewhere): PEAK-HEIGHT err "
                 f"{pkmean_ad*100:.1f}% (adaptive) vs {pkmean_un*100:.1f}% (uniform-log, same {N} pts) -> "
                 f"{summary['peak_fidelity_improvement_x']:.0f}x better peak fidelity", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.25); ax.legend(fontsize=8)
    ax = axes[1]
    ax.semilogx(grid, np.gradient(np.arange(N), np.log10(grid)), color="#1f77b4", label="adaptive point density d(idx)/d(log f)")
    ax.semilogx(uni, np.gradient(np.arange(N), np.log10(uni)), color="#999999", ls="--", label="uniform-log density")
    for fn in np.unique(np.round(modes, 1)):
        ax.axvline(fn, color="#d62728", ls=":", lw=0.6)
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("local point density (pts per decade)")
    ax.set_title("Density concentrates at solved resonances (red), coarse in flat low/high-freq regions", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.25); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(HERE/"report"/"figures"/"adaptive_freq_demo.png", dpi=140); plt.close(fig)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    _demo()
