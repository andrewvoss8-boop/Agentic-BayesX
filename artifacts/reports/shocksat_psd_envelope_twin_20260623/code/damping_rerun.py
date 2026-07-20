#!/usr/bin/env python3
"""Damping lever experiment (Andrew): does giving the twin DATA-INFORMED damping lower its envelope GRMS vs an
under-damped FEM baseline? Two parts:
  (A) GLOBAL-damping absorption check: twin at global zeta in {1,3,5%} (FEM at 1%), gain re-fit each time. If the
      training-global units-gain absorbs a global zeta, the GRMS ratio is ~unchanged -> a global damping number is
      NOT the lever (motivates per-mode / elemental / complex damping, per Das-Debnath).
  (B) PER-MODE damping: extract zeta_r per consensus mode from the clean modal data (half-power on the multi-hit
      |H1|, now resolvable at zeta~3-4% / df~2 Hz), give the twin per-mode zeta(f), FEM baseline uniform nominal;
      re-run the GRMS comparison. Honest expectation: helps modestly; the dominant blocker stays the shape-error band.
Reuses probe.fit_context (theta, splits, gain/sigma machinery). Output: out/damping_rerun.json + console.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks
sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe as P
import psd_forward as pf
import psd_envelope as pe

WS = Path(__file__).resolve().parent.parent
REFS_SCORE = ["m_xpos_990x", "m_zpos_990z", "m_xy_990xy", "m_zpos_900z"]


def fit_gain_sigma(ctx, eta):
    """Peak-matched (misalignment-free) gain + scatter on observed channels at a GIVEN damping eta(f)."""
    thmed = np.median(ctx.theta_post, axis=0)[None, :]
    df = float(ctx.freqs[1] - ctx.freqs[0]); tol = max(1, int(round(5.0 / df)))
    pr = []
    for key in ctx.caches:
        for d in ctx.obs_daqs:
            lm = np.log(np.abs(P.meas_H(ctx, [key], d)) + 1e-300)
            H = pf.forward_H_batch(ctx.R, ctx.freqs, thmed, ctx.drows[key], ctx.ch.rows[ctx.pos[d]][None, :], eta)[0, :, 0]
            lf = np.log(np.abs(H) + 1e-300)
            pk, _ = find_peaks(lm, prominence=0.3, distance=tol)
            for i in pk:
                lo, hi = max(0, i - tol), min(len(ctx.freqs), i + tol + 1)
                pr.append(float(lm[i] - np.max(lf[lo:hi])))
    pr = np.array(pr); g = float(np.median(pr)); return g, float(np.std(pr - g))


def fwd_mag(ctx, theta_batch, key, daq, eta):
    return np.abs(pf.forward_H_batch(ctx.R, ctx.freqs, theta_batch, ctx.drows[key],
                                     ctx.ch.rows[ctx.pos[daq]][None, :], eta)[:, :, 0])


def score(ctx, eta_twin, eta_fem, g_twin, s_twin, g_fem):
    f = ctx.freqs; ratios, twin_exc, fem_exc = [], [], []
    for key in REFS_SCORE:
        for d in ctx.ho_daqs:
            eps = np.random.default_rng(ctx.seed + 1000 + d).normal(0, s_twin, len(ctx.thsub))
            tw = (fwd_mag(ctx, ctx.thsub, key, d, eta_twin) * np.exp(g_twin) * np.exp(eps)[:, None]) ** 2
            t975 = np.percentile(tw, 97.5, axis=0)
            fem = (fwd_mag(ctx, np.ones((1, 9)), key, d, eta_fem)[0] * np.exp(g_fem)) ** 2
            dp = np.abs(P.meas_H(ctx, [key], d)) ** 2
            et = pe.smoothline_envelope(f, t975); ef6 = pe.smoothline_envelope(f, pe.add_db_psd(fem, 6.0))
            ratios.append(pe.grms(f, et) / pe.grms(f, ef6))
            twin_exc.append(pe.exceedance(f, dp, et)["exceeding_energy_fraction"])
            fem_exc.append(pe.exceedance(f, dp, ef6)["exceeding_energy_fraction"])
    return (float(np.median(ratios)), float(np.mean(np.array(ratios) < 1)),
            float(np.median(twin_exc)), float(np.median(fem_exc)))


def extract_per_mode_zeta(ctx, ref="m_xpos_990x"):
    f = ctx.freqs; df = float(f[1] - f[0])
    c = ctx.caches[ref]; H = np.median(np.abs(c["H1"][[c["daq"].index(d) for d in ctx.daq_master]]), axis=0)
    pk, _ = find_peaks(np.log(H + 1e-30), prominence=0.3, distance=max(1, int(3.0 / df)))
    zr = {}
    for i in pk:
        fr = f[i]; half = H[i] / np.sqrt(2.0)
        l = i
        while l > 0 and H[l] > half:
            l -= 1
        r = i
        while r < len(f) - 1 and H[r] > half:
            r += 1
        fl = np.interp(half, [H[l], H[l + 1]], [f[l], f[l + 1]]) if H[l + 1] > H[l] else f[l]
        fr2 = np.interp(half, [H[r], H[r - 1]], [f[r], f[r - 1]]) if H[r - 1] > H[r] else f[r]
        z = max((fr2 - fl) / (2 * fr), df / (2 * fr))                       # resolution floor
        zr[float(fr)] = float(z)
    return zr


def zeta_profile(freqs, zr):
    fr = np.array(sorted(zr)); zv = np.array([zr[k] for k in fr])
    idx = np.argmin(np.abs(freqs[:, None] - fr[None, :]), axis=1)            # nearest-mode zeta
    return zv[idx]


def main(seed=0, obs_frac=0.9):
    ctx = P.fit_context(seed=seed, obs_frac=obs_frac)
    f = ctx.freqs
    win = 1.0 / (2 * np.pi * f * (-(122880 - 1) / (250000.0 * np.log(0.05))))  # window zeta_w(f)
    rec = {"seed": seed, "obs_frac": obs_frac, "baseline_sigma": ctx.sig, "note": "damping lever experiment"}

    # (A) global-damping absorption: twin global zeta z, FEM at 1% (both +window)
    A = {}
    for z in [0.01, 0.03, 0.05]:
        eta_t = 2 * (z + win); eta_f = 2 * (0.01 + win)
        gt, st = fit_gain_sigma(ctx, eta_t); gf, _ = fit_gain_sigma(ctx, eta_f)
        ratio, win_rate, te, fe = score(ctx, eta_t, eta_f, gt, st, gf)
        A[f"{z*100:.0f}pct"] = {"twin_gain": round(gt, 2), "twin_sigma": round(st, 2),
                                "median_grms_ratio": round(ratio, 2), "win_rate": win_rate}
        print(f"(A) twin global zeta {z*100:.0f}% (FEM 1%): gain {gt:+.2f} sigma {st:.2f} -> median GRMS ratio {ratio:.2f}")
    rec["A_global_absorption"] = A

    # (B) per-mode extracted damping for twin, FEM uniform nominal 1%
    zr = extract_per_mode_zeta(ctx)
    zvals = np.array(list(zr.values()))
    eta_t = 2 * zeta_profile(f, zr)                  # extracted already includes the window (measured peaks)
    eta_f = 2 * (0.01 + win)
    gt, st = fit_gain_sigma(ctx, eta_t); gf, _ = fit_gain_sigma(ctx, eta_f)
    ratio, win_rate, te, fe = score(ctx, eta_t, eta_f, gt, st, gf)
    rec["B_per_mode"] = {"n_modes": len(zr), "zeta_median": round(float(np.median(zvals)), 4),
                         "zeta_range": [round(float(zvals.min()), 4), round(float(zvals.max()), 4)],
                         "per_mode_zeta": {round(k, 1): round(v, 4) for k, v in zr.items()},
                         "twin_gain": round(gt, 2), "twin_sigma": round(st, 2),
                         "median_grms_ratio": round(ratio, 2), "win_rate": win_rate,
                         "twin_exc_energy": round(te, 3), "fem_exc_energy": round(fe, 3)}
    print(f"(B) per-mode zeta: {len(zr)} modes, median {np.median(zvals)*100:.1f}% "
          f"(range {zvals.min()*100:.1f}-{zvals.max()*100:.1f}%)")
    print(f"    twin per-mode-damped vs FEM(1%)+6dB: median GRMS ratio {ratio:.2f}, win {win_rate*100:.0f}%, "
          f"twin exceed-energy {te:.3f}, FEM+6 exceed {fe:.3f}")
    (WS / "out" / "damping_rerun.json").write_text(json.dumps(rec, indent=2))
    print("wrote out/damping_rerun.json")
    return rec


if __name__ == "__main__":
    main()
