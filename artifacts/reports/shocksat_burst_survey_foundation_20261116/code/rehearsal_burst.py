#!/usr/bin/env python3
"""Synthetic rehearsal: what could NASA's burst-random survey resolve on ShockSat?

Truth system: the project's nominal FEM (80 modes to 321.7 Hz, mass-normalised shapes at
the 76 survey nodes) with per-mode damping interpolated from NASA's impact-survey
fits (0.12 % to 0.89 % of critical). Three shakers drive it with independent burst
random force (Gaussian noise band-limited to 400 Hz, on for the first half of every
frame, off for the second half, frames back to back so tails carry over). NASA's shaker
grids (5105, 8109, 9206) are not FEM grids, so STAND-IN drive points are used:
5201 Z (aluminium bulkhead centre), 8102 X (steel flange corner), 9201 Z (steel bulkhead
centre). Noise: 1 % of each output's RMS and 0.5 % of each force's RMS, white.

Simulation is exact for the discretised system: every mode is converted to a
discrete-time filter with a zero-order hold at 2048 samples/s, and the truth FRF is the
same filters' frequency response, so any error is the estimator's (leakage, noise, finite
averages), not the simulator's.

Scenarios: frame length 2, 4, 8, 16 s (line spacing 0.5, 0.25, 0.125, 0.0625 Hz),
16 frames each; plus the project's shock-cache condition (2.03 Hz lines) emulated by
power-averaging the 8 s estimate over 2.03 Hz blocks.

Outputs: out/rehearsal_burst.json, out/rehearsal_frf_examples.npz (for the figure).
"""
import json
import os
import sys
import time

import numpy as np
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fem_frf  # noqa: E402
import mimo_frf  # noqa: E402

FS = 2048.0
INPUTS = [(5201, "Z"), (8102, "X"), (9201, "Z")]
OUTPUTS = INPUTS + [(1101, "Z"), (11101, "X"), (11110, "Y"), (2101, "X"), (4101, "X"), (6102, "Y"), (10101, "X"), (3201, "Z"), (7102, "Y")]
FRAMES_S = [2.0, 4.0, 8.0, 16.0]
N_FRAMES = 16
BAND = (45.0, 200.0)
SEED = 20261117


def modal_filters(fem, zeta):
    """Discrete-time filters from modal force to modal acceleration (exact ZOH)."""
    T = 1.0 / FS
    out = []
    for m, (w, z) in enumerate(zip(fem.wn, zeta)):
        if fem.fn[m] < 5.0:
            out.append(None)          # rigid-body mode: acceleration = modal force
            continue
        A = np.array([[0.0, 1.0], [-w * w, -2 * z * w]])
        B = np.array([[0.0], [1.0]])
        C = np.array([[-w * w, -2 * z * w]])
        D = np.array([[1.0]])
        Ad, Bd, Cd, Dd, _ = signal.cont2discrete((A, B, C, D), T, method="zoh")
        b, a = signal.ss2tf(Ad, Bd, Cd, Dd)
        out.append((b[0], a))
    return out


def simulate(fem, filt, u):
    """u: (n_in, n) forces in lbf -> accelerations (n_out, n) in g."""
    rows_in = [fem.row(*d) for d in INPUTS]
    rows_out = [fem.row(*r) for r in OUTPUTS]
    y = np.zeros((len(OUTPUTS), u.shape[1]))
    for m, fl in enumerate(filt):
        p = fem.V[rows_in, m] @ u
        qdd = p if fl is None else signal.lfilter(fl[0], fl[1], p)
        y += np.outer(fem.V[rows_out, m], qdd)
    return y / fem_frf.G


def truth_frf(fem, filt, f):
    z = np.exp(1j * 2 * np.pi * f / FS)
    rows_in = [fem.row(*d) for d in INPUTS]
    rows_out = [fem.row(*r) for r in OUTPUTS]
    H = np.zeros((len(OUTPUTS), len(INPUTS), len(f)), complex)
    for m, fl in enumerate(filt):
        hm = np.ones_like(z) if fl is None else np.polyval(fl[0], z) / np.polyval(fl[1], z)
        H += np.einsum("o,i,f->oif", fem.V[rows_out, m], fem.V[rows_in, m], hm)
    return H / fem_frf.G


def burst(n_in, nfft, n_frames, rng, frac=0.5):
    lp = signal.firwin(255, 400.0, fs=FS)
    u = np.zeros((n_in, nfft * n_frames))
    on = int(frac * nfft)
    for k in range(n_frames):
        seg = rng.standard_normal((n_in, on + 254))
        u[:, k * nfft:k * nfft + on] = signal.lfilter(lp, 1.0, seg, axis=1)[:, 254:]
    return u * 10.0       # about 10 lbf RMS while on


def coarse(f, Hmag, width):
    """Power average over blocks of `width` Hz (emulates the 2.03 Hz shock caches)."""
    edges = np.arange(f[0], f[-1], width)
    fc, out = [], []
    for a in edges:
        s = (f >= a) & (f < a + width)
        if s.any():
            fc.append(a + width / 2)
            out.append(np.sqrt(np.mean(Hmag[..., s] ** 2, axis=-1)))
    return np.array(fc), np.stack(out, axis=-1)


def main():
    t0 = time.time()
    fem = fem_frf.FEM()
    zeta = fem.zeta("measured_interp")
    filt = modal_filters(fem, zeta)
    rng = np.random.default_rng(SEED)
    el = np.where((fem.fn >= BAND[0]) & (fem.fn <= BAND[1]))[0]
    # which input excites each mode best (largest |phi_d|^2), and which output to read
    rows_in = [fem.row(*d) for d in INPUTS]
    best_in = {int(m): int(np.argmax(np.abs(fem.V[rows_in, m]))) for m in el}
    # isolation: no other mode within 10 half-power widths (or 2 Hz, whichever is larger)
    iso = {}
    for m in el:
        width = 2 * zeta[m] * fem.fn[m]
        gap = np.min(np.abs(np.delete(fem.fn, m) - fem.fn[m]))
        iso[int(m)] = bool(gap > max(10 * width, 2.0))
    res = {"settings": {"fs_hz": FS, "inputs_stand_in": INPUTS, "outputs": OUTPUTS, "n_frames": N_FRAMES, "burst_fraction": 0.5,
                        "noise": {"output_rms_fraction": 0.01, "input_rms_fraction": 0.005}, "seed": SEED,
                        "zeta_range": [float(zeta[el].min()), float(zeta[el].max())]},
           "modes_in_band": len(el), "isolated_modes_in_band": int(sum(iso.values())), "scenarios": {}}
    examples = {}
    for T in FRAMES_S:
        nfft = int(T * FS)
        u = burst(len(INPUTS), nfft, N_FRAMES + 1, rng)
        y = simulate(fem, filt, u)
        y = y + 0.01 * y.std(axis=1, keepdims=True) * rng.standard_normal(y.shape)
        um = u + 0.005 * u.std(axis=1, keepdims=True) * rng.standard_normal(u.shape)
        X = mimo_frf.frame_spectra(um[:, nfft:], nfft)       # drop the first frame (no previous tail)
        Y = mimo_frf.frame_spectra(y[:, nfft:], nfft)
        H, coh, cond = mimo_frf.h1(X, Y)
        f = np.fft.rfftfreq(nfft, 1 / FS)
        Ht = truth_frf(fem, filt, f)
        b = (f >= BAND[0]) & (f <= BAND[1])
        err = 20 * np.log10(np.abs(H[..., b]) / np.abs(Ht[..., b]))
        # tail energy left at the end of each frame relative to the burst part (leakage driver)
        tail = []
        for k in range(1, N_FRAMES):
            seg = y[:, k * nfft:(k + 1) * nfft]
            tail.append(np.sqrt(np.mean(seg[:, -nfft // 16:] ** 2, 1)) / np.sqrt(np.mean(seg[:, : nfft // 2] ** 2, 1)))
        z_rec, details = [], []
        for m in el:
            if not iso[int(m)]:
                continue
            i = best_in[int(m)]
            o = i                                   # the drive point of that shaker
            hp = mimo_frf.half_power_zeta(f, np.abs(H[o, i]), fem.fn[m], max(1.0, 6 * zeta[m] * fem.fn[m]))
            ok = hp is not None and abs(hp[0] / zeta[m] - 1) <= 0.25
            z_rec.append(ok)
            details.append({"f_hz": float(fem.fn[m]), "zeta_true": float(zeta[m]), "zeta_est": None if hp is None else float(hp[0]),
                            "lines_across_half_power": None if hp is None else hp[2], "recovered_within_25pct": bool(ok)})
        peak_err = []
        for m in el:
            i = best_in[int(m)]
            s = (f >= fem.fn[m] - 0.6) & (f <= fem.fn[m] + 0.6)
            if s.any():
                peak_err.append(20 * np.log10(np.abs(H[i, i, s]).max() / np.abs(Ht[i, i, s]).max()))
        res["scenarios"][f"T{T:g}s"] = {
            "line_spacing_hz": 1 / T, "median_abs_err_db": float(np.median(np.abs(err))), "p95_abs_err_db": float(np.percentile(np.abs(err), 95)),
            "peak_err_db_median": float(np.median(peak_err)), "peak_err_db_min": float(np.min(peak_err)),
            "coherence_median": float(np.nanmedian(coh[:, b])), "coherence_p05": float(np.nanpercentile(coh[:, b], 5)),
            "cond_gxx_median": float(np.median(cond[b])),
            "tail_to_burst_rms_median": float(np.median(tail)), "tail_to_burst_rms_max": float(np.max(tail)),
            "damping_recovered_fraction": float(np.mean(z_rec)) if z_rec else None, "n_isolated_modes": len(z_rec),
            "damping_details": details}
        if T in (2.0, 8.0):
            o = OUTPUTS.index((5201, "Z"))
            examples[f"T{T:g}"] = (f[b], np.abs(H[o, 0, b]), np.abs(Ht[o, 0, b]))
        if T == 8.0:
            fc, Hc = coarse(f[b], np.abs(H[..., b]), 2.0345)
            zc = []
            for m in el:
                if not iso[int(m)]:
                    continue
                i = best_in[int(m)]
                hp = mimo_frf.half_power_zeta(fc, Hc[i, i], fem.fn[m], 4.0)
                zc.append(hp is not None and abs(hp[0] / zeta[m] - 1) <= 0.25)
            res["scenarios"]["cache_2p03hz_from_T8s"] = {"line_spacing_hz": 2.0345, "damping_recovered_fraction": float(np.mean(zc)),
                                                        "n_isolated_modes": len(zc)}
            examples["cache"] = (fc, Hc[0, 0], None)
    # Estimator-free resolvability: frequency lines across each mode's half-power width
    # (2 zeta f). Fewer than about 3 lines cannot support a damping estimate from FRFs.
    widths = 2 * zeta[el] * fem.fn[el]
    test_w = 2 * fem.test_zeta * fem.test_f
    tb = (fem.test_f >= BAND[0]) & (fem.test_f <= BAND[1])
    res["lines_across_half_power"] = {}
    for df in (0.0625, 0.125, 0.25, 0.5, 2.0345):
        lw = widths / df
        lt = test_w[tb] / df
        res["lines_across_half_power"][f"{df:g}Hz"] = {
            "fem_modes_45_200": {"n": int(len(lw)), "min": float(lw.min()), "median": float(np.median(lw)), "n_ge_3": int((lw >= 3).sum())},
            "nasa_test_modes_45_200": {"n": int(len(lt)), "min": float(lt.min()), "median": float(np.median(lt)), "n_ge_3": int((lt >= 3).sum())}}
    res["runtime_s"] = time.time() - t0
    json.dump(res, open(os.path.join(WS, "out", "rehearsal_burst.json"), "w"), indent=1)
    np.savez_compressed(os.path.join(WS, "out", "rehearsal_frf_examples.npz"),
                        **{f"{k}_{n}": v for k, tup in examples.items() for n, v in zip(("f", "est", "true"), tup) if v is not None})
    for k, v in res["scenarios"].items():
        print(k, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk != "damping_details"})
    for k, v in res["lines_across_half_power"].items():
        print("lines across half-power", k, v)
    print("isolated modes in band", res["isolated_modes_in_band"], "of", res["modes_in_band"], "| runtime", round(res["runtime_s"], 1), "s")


if __name__ == "__main__":
    main()
