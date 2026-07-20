#!/usr/bin/env python3
"""Core time-domain decay estimator (Layer 1): band-pass + analytic-signal log-decrement.

Intuition (plain English): a lightly-damped mode rung by a hammer impact decays like a fading sine wave,
  a(t) = A * exp(-zeta * 2*pi*f0 * t) * cos(2*pi*f_d*t + phi).
The "envelope" A*exp(-zeta*2*pi*f0*t) is a straight line on a log scale; its slope gives the damping ratio
  zeta = -slope / (2*pi*f0).
This is a TIME-DOMAIN decay rate and does NOT depend on the FFT frequency bin width df: a sub-bin half-power
width (the thing that defeated D22's windowed FRF) is still many cycles of visible decay in the ring-down.

Method: 4th-order Butterworth band-pass (zero-phase filtfilt) isolates the mode; scipy Hilbert gives the
analytic envelope; a weighted linear fit of log-envelope vs time over the clean window gives the decay slope.
Noise floor = same band-pass applied to the PRE-impact baseline (t<0). The fit window runs from a small
post-impact skip to where the envelope falls to k*noise_floor. Returns zeta, fit quality, and resolvability
diagnostics (cycles of decay, dB of decay, SNR, decay time-constant tau, half-power df vs FFT df).
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
from scipy.signal import butter, filtfilt, hilbert

WS = Path(__file__).resolve().parent.parent
CACHE = WS / "data" / "ringdown"
DF_FFT = 2.0345052083333335   # the inherited modal-cache FFT bin width (Hz) we are dodging (modal_cache_summary)


def load_ring(key):
    z = np.load(CACHE / f"{key}.npz", allow_pickle=True)
    return {k: z[k] for k in z.files}


def bandpass(x, f0, W, fs, order=4):
    lo, hi = max(1.0, f0 - W), f0 + W
    b, a = butter(order, [lo / (fs / 2), hi / (fs / 2)], btype="band")
    return filtfilt(b, a, x, axis=-1)


def decay_fit(sig, t, ip, f0, fs, neighbors=(), skip_ms=6.0, k_floor=4.0, min_cycles=8.0, return_trace=False):
    """Estimate zeta from one ring-down trace `sig` (1-D, decimated, full record incl. pre-impact).
    `t` = time relative to impact (s); `ip` = impact index. Returns dict (zeta + diagnostics) or None."""
    # band half-width: half the distance to the nearest neighbouring mode, capped; >= 3 Hz
    gaps = [abs(nb - f0) for nb in neighbors if abs(nb - f0) > 0.5]
    W = min((min(gaps) * 0.5 if gaps else 7.0), 7.0); W = max(W, 3.0)
    xb = bandpass(sig, f0, W, fs)
    env = np.abs(hilbert(xb))
    # noise floor from the band-passed PRE-impact baseline (t < -10 ms)
    pre = env[t < -0.010]
    floor = np.median(pre) + 1e-12 if pre.size > 50 else np.percentile(env, 5)
    # fit window: from skip_ms after impact, to where env first drops below k*floor (or record end)
    i0 = ip + int(skip_ms * 1e-3 * fs)
    peak_env = env[i0:i0 + int(0.02 * fs)].max() if i0 + 10 < len(env) else env[i0:].max()
    thr = max(k_floor * floor, 0.02 * peak_env)
    seg = env[i0:]
    below = np.where(seg < thr)[0]
    i1 = i0 + (below[0] if below.size else len(seg))
    if i1 - i0 < 20:
        return None
    tw = t[i0:i1]; ew = env[i0:i1]
    n_cycles = float(f0 * (tw[-1] - tw[0]))
    if n_cycles < min_cycles:
        return None
    # weighted linear fit of log-envelope (weight by envelope amplitude -> down-weight the noisy tail)
    y = np.log(ew); w = ew / ew.max()
    A = np.vstack([tw, np.ones_like(tw)]).T
    WA = A * w[:, None]; Wy = y * w
    coef, *_ = np.linalg.lstsq(WA, Wy, rcond=None)
    slope, intercept = coef
    yhat = A @ coef
    ss_res = float(np.sum((w * (y - yhat)) ** 2)); ss_tot = float(np.sum((w * (y - np.average(y, weights=w))) ** 2))
    r2 = 1.0 - ss_res / (ss_tot + 1e-30)
    zeta = float(-slope / (2 * np.pi * f0))
    tau = float(-1.0 / slope) if slope < 0 else np.inf       # decay time constant (s)
    db_decay = float(20 * np.log10(ew[0] / (ew[-1] + 1e-30)))
    snr = float(peak_env / floor)
    half_power_df = 2.0 * zeta * f0                           # Hz; compare to DF_FFT
    out = dict(zeta=zeta, zeta_pct=zeta * 100, slope=float(slope), r2=float(r2), tau_s=tau,
               W_hz=float(W), n_cycles=n_cycles, db_decay=db_decay, snr=snr,
               T_fit_ms=float((tw[-1] - tw[0]) * 1000), half_power_df_hz=float(half_power_df),
               df_fft_hz=DF_FFT, subbin=bool(half_power_df < DF_FFT), peak_env=float(peak_env), floor=float(floor))
    if return_trace:
        out["tw"] = tw - tw[0]    # time from fit-window start (s)
        out["ew"] = ew            # envelope over the fit window
    return out


if __name__ == "__main__":
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else "m_xpos_990x"
    f0 = float(sys.argv[2]) if len(sys.argv) > 2 else 138.3
    r = load_ring(key)
    fs = float(r["fs_dec"]); t = r["t"]; ipv = int(np.median(r["impact_idx_dec"]))
    daq = list(r["daq"]); A = r["A"]
    print(f"{key} mode {f0} Hz | fs_dec {fs:.0f} | impact idx {ipv} | {A.shape[0]} hits x {A.shape[1]} ch")
    # rank channels by post-impact band SNR (hit 0) and fit the top few
    results = []
    for ci, d in enumerate(daq):
        fits = []
        for h in range(A.shape[0]):
            f = decay_fit(A[h, ci], t, ipv, f0, fs)
            if f and f["r2"] > 0.9 and f["snr"] > 8:
                fits.append(f)
        if len(fits) >= 3:
            zs = [f["zeta_pct"] for f in fits]
            results.append((d, np.median(zs), np.std(zs), len(fits), np.median([f["snr"] for f in fits]),
                            np.median([f["n_cycles"] for f in fits]), np.median([f["r2"] for f in fits])))
    results.sort(key=lambda x: -x[4])
    print(f"{'ch':>4} {'zeta%':>7} {'std':>6} {'nfit':>4} {'snr':>7} {'cyc':>6} {'r2':>6}")
    for d, zmed, zstd, nf, snr, cyc, r2 in results[:15]:
        print(f"{d:>4} {zmed:>7.3f} {zstd:>6.3f} {nf:>4} {snr:>7.0f} {cyc:>6.0f} {r2:>6.3f}")
    if results:
        allz = [r[1] for r in results]
        print(f"\nmode {f0} Hz: across {len(results)} good channels, zeta median {np.median(allz):.3f}% "
              f"[{np.percentile(allz,25):.3f}, {np.percentile(allz,75):.3f}]  (ash ~0.35%, FEM nominal 1.00%)")
