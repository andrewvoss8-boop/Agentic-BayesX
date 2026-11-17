#!/usr/bin/env python3
"""Multiple-input frequency response estimation (the H1 estimator) for burst-random
modal test data.

Plain English: each frame of the record is Fourier transformed; for every frequency
line the cross-spectra between outputs and inputs (Gyx) and among the inputs (Gxx) are
summed over frames, and H1 = Gyx Gxx^-1. Averaging over frames suppresses noise on the
outputs. "Multiple coherence" (0 to 1) is the fraction of an output's power explained
by all inputs together; values well below 1 flag noise, leakage or nonlinearity. The
condition number of Gxx flags correlated shaker forces (inputs that cannot be separated).

Burst random uses a rectangular window (no taper): the excitation stops part-way through
each frame so the response can decay before the frame ends. If it does not decay, the
leftover response leaks into neighbouring lines; the rehearsal measures that.
"""
import numpy as np


def frame_spectra(x, nfft):
    """x: (n_channels, n_samples). Returns (n_frames, n_channels, nfft//2+1), rectangular window."""
    n_frames = x.shape[1] // nfft
    xf = x[:, : n_frames * nfft].reshape(x.shape[0], n_frames, nfft).transpose(1, 0, 2)
    return np.fft.rfft(xf, axis=2)


def h1(X, Y):
    """X: (frames, n_in, n_f) input spectra; Y: (frames, n_out, n_f). Returns H (n_out, n_in, n_f),
    multiple coherence (n_out, n_f) and condition number of Gxx (n_f)."""
    Gxx = np.einsum("kif,kjf->fij", X, np.conj(X))
    Gyx = np.einsum("kof,kjf->foj", Y, np.conj(X))
    Gyy = np.einsum("kof,kof->of", Y, np.conj(Y)).real
    Ginv = np.linalg.inv(Gxx)
    H = np.einsum("foj,fji->foi", Gyx, Ginv)
    expl = np.einsum("foi,fij,foj->of", H, Gxx, np.conj(H)).real
    coh = np.clip(expl / np.where(Gyy > 0, Gyy, np.nan), 0, 1)
    cond = np.linalg.cond(Gxx)
    return H.transpose(1, 2, 0), coh, cond


def half_power_zeta(f, mag, f_guess, search_hz):
    """Damping ratio from the half-power width of the peak nearest f_guess:
    zeta = (f_hi - f_lo) / (2 f_peak), with linear interpolation of |H|^2 at the
    -3 dB crossings. Returns (zeta, f_peak, n_lines_across_width) or None."""
    s = (f >= f_guess - search_hz) & (f <= f_guess + search_hz)
    if s.sum() < 3:
        return None
    idx = np.where(s)[0]
    k = idx[np.argmax(mag[idx])]
    p = mag ** 2
    half = p[k] / 2.0
    i = k
    while i > 0 and p[i] > half:
        i -= 1
    j = k
    while j < len(p) - 1 and p[j] > half:
        j += 1
    if i == 0 or j == len(p) - 1 or i == k or j == k:
        return None
    flo = f[i] + (half - p[i]) * (f[i + 1] - f[i]) / (p[i + 1] - p[i])
    fhi = f[j - 1] + (p[j - 1] - half) * (f[j] - f[j - 1]) / (p[j - 1] - p[j])
    return (fhi - flo) / (2 * f[k]), float(f[k]), int(j - i - 1)
