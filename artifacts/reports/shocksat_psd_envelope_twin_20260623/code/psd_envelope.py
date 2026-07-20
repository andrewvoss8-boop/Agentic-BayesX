#!/usr/bin/env python3
"""Smoothline envelope + GRMS + energy-weighted exceedance for the PSD-envelope twin (NEW; Q-C/Q-D/Q-E).

ENVELOPE (Q-C, Andrew Q2 default): peak-pick local maxima of the PSD in (log10 f, dB=10·log10 PSD) space, then
connect the peak tops with straight segments in (log f, dB) — the classic MPE / qualification-spec straight-line
log–log envelope drawn OVER the peaks. The SAME function is applied to FEM+6 dB and to the twin's 97.5th-pct PSD.
Band edges are anchored at the local signal level so the envelope spans the full band.

GRMS (Q-D): sqrt(∫ envelope df) over the band.  Lower GRMS = less conservative test level.
EXCEEDANCE (Q-E, Andrew Q3): where the measured data pokes ABOVE the envelope, in dB, plus the FRACTION of the data's
band energy carried by the exceeding frequencies (a big poke where the data is already low ≈ negligible energy).
"""
from __future__ import annotations
import numpy as np
from scipy.signal import find_peaks


def smoothline_envelope(freqs, psd, prominence_db=1.0, min_sep_hz=3.0, floor_frac=1e-6):
    """Piecewise-linear (in log f, dB) envelope through the PSD peak tops. Returns envelope on the same grid."""
    f = np.asarray(freqs, float); s = np.asarray(psd, float)
    s = np.maximum(s, s.max() * floor_frac + 1e-300)          # guard log of deep antiresonances
    dB = 10.0 * np.log10(s); logf = np.log10(f)
    df = np.median(np.diff(f))
    pk, _ = find_peaks(dB, prominence=prominence_db, distance=max(1, int(min_sep_hz / df)))
    # anchors = band edges (at local signal level) + peak tops, sorted by frequency
    idx = np.unique(np.concatenate([[0], pk, [len(f) - 1]]))
    env_dB = np.interp(logf, logf[idx], dB[idx])
    # never let the envelope fall below the underlying peaks it is meant to cover
    env_dB = np.maximum(env_dB, np.interp(logf, logf[idx], dB[idx]))
    return 10.0 ** (env_dB / 10.0)


def grms(freqs, psd):
    """sqrt(area under PSD) over the given band. Units g (with S_F0 = 1 lbf^2/Hz)."""
    return float(np.sqrt(np.trapz(np.asarray(psd, float), np.asarray(freqs, float))))


def exceedance(freqs, data_psd, env_psd):
    """How far the measured data pokes above an envelope, energy-weighted (Q-E)."""
    f = np.asarray(freqs, float); d = np.asarray(data_psd, float); e = np.asarray(env_psd, float)
    exc_db = 10.0 * np.log10(np.maximum(d, 1e-300) / np.maximum(e, 1e-300))
    over = d > e
    tot = np.trapz(d, f)
    exc_energy = float(np.trapz(np.where(over, d, 0.0), f) / (tot + 1e-300))
    return {"max_exceedance_db": float(exc_db.max()) if exc_db.size else 0.0,
            "max_exceedance_db_positive": float(max(0.0, exc_db.max())),
            "exceeding_energy_fraction": exc_energy,                       # fraction of data band-energy above env
            "n_exceeding_bins": int(over.sum()),
            "freq_of_max_exc_hz": float(f[int(np.argmax(exc_db))]) if exc_db.size else 0.0}


def add_db_psd(psd, db):
    """Add a dB margin to a PSD (g^2/Hz). +6 dB = x10^0.6 = x3.98 in PSD = x2 in GRMS."""
    return np.asarray(psd, float) * (10.0 ** (db / 10.0))


# ----------------------------------------------------------------------------- self-test
if __name__ == "__main__":
    f = np.linspace(45, 260, 600)
    rng = np.random.default_rng(0)
    psd = np.full_like(f, 1e-4)
    for f0, amp, q in [(75, 1.0, 0.01), (120, 0.5, 0.012), (190, 0.8, 0.008), (240, 0.3, 0.01)]:
        psd += amp / ((1 - (f / f0) ** 2) ** 2 + (2 * q * f / f0) ** 2)
    env = smoothline_envelope(f, psd)
    g_sig, g_env = grms(f, psd), grms(f, env)
    exc = exceedance(f, psd, env)            # signal vs its OWN envelope -> minimal exceedance
    env6 = smoothline_envelope(f, add_db_psd(psd, 6.0))
    print(f"GRMS signal {g_sig:.4f}, envelope {g_env:.4f} (env>=signal: {g_env >= g_sig})")
    print(f"+6 dB envelope GRMS {grms(f, env6):.4f} (ratio to env {grms(f, env6)/g_env:.2f}, expect ~2.0)")
    print(f"self-exceedance: max {exc['max_exceedance_db']:.2f} dB, energy frac {exc['exceeding_energy_fraction']:.4f}")
    assert g_env >= g_sig, "envelope GRMS must be >= signal GRMS"
    assert abs(grms(f, env6) / g_env - 2.0) < 0.05, "+6 dB must double GRMS"
    print("psd_envelope self-test PASS")
