#!/usr/bin/env python3
"""Held-out FRF with the UNITS-BASED gain (no fitting): measured data vs original FEM (theta=1) vs L5 mean + 95%
predictive band, per held-out channel. Each panel's legend carries the band-GRMS = sqrt(integral |H|^2 df) over
45-260 Hz for: data, original FEM, L5 mean (median), L5 upper 95%. (tufte-data-graphics skill applied.)

No new inference: reuses the cached L5 posterior (out/frf_compare/l5_theta_0.npz) and the single fixed units gain
per method (frf_fixed_gain.fixed_units_gain -> one constant, NOT re-fit to the data). The L5 band = posterior theta
draws x an observed-only model-form level offset, all at the FIXED units gain -> the residual ~2x peak under-
prediction shows as honest BIAS (median below the measured peaks), not hidden by a fitted gain.

Q = accelerance |H| = |a/F| [g/lbf]; band-GRMS [g/lbf*sqrt(Hz)]. Measured = single-impact hit-001 (YELLOW: 1 hit).
Output: figures/fig_l5_units_frf.png
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq
import frf_compare as FC
import frf_fixed_gain as FG

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; FIG.mkdir(exist_ok=True)
C_DATA = "#222222"; C_FEM = "#ff7f0e"; C_L5 = "#1f77b4"; NAVY = "#13456e"
HARD = {4, 27, 40, 52, 69, 92, 98}
qoi_band = rf.core.qoi_band
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": False, "figure.dpi": 140, "savefig.bbox": "tight"})


def main(seed=0, n_draws=200, n_panels=6):
    U, cal, eta = FG.fixed_units_gain()                          # one fixed units constant per method (no fitting)
    R = rf.load_reduced(); meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    obs_pos, ho_pos = FC.setup_split(R, meas, ch, freqs, fb, didx, dr, seed)
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T   # (Nf,n_o)
    th_l5, _ = FC.l5_theta(R, meas, ch, fb, didx, obs_pos, seed, 600, 600, 4)
    sub = np.linspace(0, th_l5.shape[0] - 1, min(th_l5.shape[0], n_draws)).astype(int)

    # observed-only model-form level sigma at the FIXED units gain
    lm_obs = rf.fem_logmag_batch(R, freqs, th_l5[sub], obs_rows, ch.drive_row, zeta=rf.ZETA_NOM) + U["L5"]
    sig = float(np.std(tru_obs[None] - lm_obs))
    lvl = np.random.default_rng(seed + 50).normal(0, max(sig, 1e-3), len(sub))

    # held-out L5 band (theta + model-form), original FEM line, all at the fixed units gain
    lm_ho = rf.fem_logmag_batch(R, freqs, th_l5[sub], ho_rows, ch.drive_row, zeta=rf.ZETA_NOM) + U["L5"]
    tot = np.exp(lm_ho + lvl[:, None, None])                     # (M,Nf,n_ho)
    fem_line = np.exp(rf.fem_logmag(R, freqs, np.ones(9), ho_rows, ch.drive_row, zeta=rf.ZETA_NOM) + U["FEM"])    # (Nf,n_ho)

    # choose panels: hard channels first, then high-DR typical
    hard = [i for i, d in enumerate(ho_daqs) if d in HARD]
    rest = sorted([i for i in range(len(ho_daqs)) if i not in hard], key=lambda i: dr[ho_pos[i]], reverse=True)
    pick = (hard + rest)[:n_panels]
    meas_mag = {int(ho_daqs[i]): np.abs(meas["H"][didx[ho_daqs[i]]][fb]) for i in pick}
    ymax = max(meas_mag[ho_daqs[i]].max() for i in pick) * 3; ymin = min(meas_mag[ho_daqs[i]].min() for i in pick) / 3

    ncol = 3; nrow = int(np.ceil(len(pick) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(13.5, 3.4 * nrow), sharex=True, sharey=True)
    axes = np.atleast_1d(axes).ravel()
    for ax, i in zip(axes, pick):
        d = int(ho_daqs[i]); data = meas_mag[d]
        band = tot[:, :, i]
        lo = np.percentile(band, 2.5, 0); med = np.median(band, 0); hi = np.percentile(band, 97.5, 0)
        ax.fill_between(freqs, lo, hi, color=C_L5, alpha=0.18, lw=0)
        ax.plot(freqs, med, color=C_L5, lw=1.3)
        ax.plot(freqs, fem_line[:, i], color=C_FEM, lw=1.1, ls="--")
        ax.plot(freqs, data, color=C_DATA, lw=1.2)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(ymin, ymax)
        # band-GRMS per source
        g_data = qoi_band(data, freqs); g_fem = qoi_band(fem_line[:, i], freqs)
        g_l5 = np.array([qoi_band(band[j], freqs) for j in range(band.shape[0])])
        g_l5_med = float(np.median(g_l5)); g_l5_hi = float(np.percentile(g_l5, 97.5))
        tag = "HARD" if d in HARD else "typical"
        ax.set_title(f"DAQ {d} ({tag})", fontsize=10, color=NAVY)
        txt = (f"GRMS [g/lbf$\\cdot\\sqrt{{Hz}}$]\n"
               f"data        {g_data:6.1f}\n"
               f"FEM (θ=1)   {g_fem:6.1f}\n"
               f"L5 mean     {g_l5_med:6.1f}\n"
               f"L5 up 95%   {g_l5_hi:6.1f}")
        ax.text(0.025, 0.025, txt, transform=ax.transAxes, fontsize=6.6, family="monospace",
                va="bottom", ha="left", bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#cccccc", alpha=0.85))
    for ax in axes[len(pick):]:
        ax.set_visible(False)
    for ax in axes[:len(pick)]:
        ax.set_xlabel("frequency [Hz, log]", fontsize=8.5)
    for r in range(nrow):
        axes[r * ncol].set_ylabel("|H| [g/lbf, log]", fontsize=8.5)
    a0 = axes[0]
    a0.text(0.03, 0.97, "measured data", color=C_DATA, transform=a0.transAxes, fontsize=8, va="top")
    a0.text(0.03, 0.90, "original FEM (θ=1)", color=C_FEM, transform=a0.transAxes, fontsize=8, va="top")
    a0.text(0.03, 0.83, "L5 mean + 95% band", color=C_L5, transform=a0.transAxes, fontsize=8, va="top")
    fig.suptitle(f"Held-out FRF with the UNITS-BASED gain (fixed, no fitting): data vs original FEM vs L5  "
                 f"[units gain ×{np.exp(U['L5']):.0f} L5 / ×{np.exp(U['FEM']):.0f} FEM]", fontsize=11, color=NAVY, y=0.998)
    fig.text(0.5, -0.02, "Q = accelerance |H| [g/lbf]; band-GRMS = sqrt(∫|H|²df) over 45-260 Hz. Single fixed units "
             "gain per method (frf_fixed_gain.fixed_units_gain; NOT re-fit). L5 band = posterior θ × observed-only "
             "model-form level offset. With NO fitted per-channel gain, the FEM's energy MIS-DISTRIBUTION across "
             "sensors is fully visible: it OVER-predicts band-GRMS at the hard impact-face channels (DAQ 40/98) and "
             "UNDER-predicts elsewhere (DAQ 77) — mode-shape participation error. L5 ≈ FEM (θ barely changes broadband "
             "energy). Upper-95% is inflated by the whole-FRF spread (peak-frequency misalignment). No new inference.",
             ha="center", fontsize=7.0, wrap=True)
    p = FIG / "fig_l5_units_frf.png"
    fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {p}; panels {[int(ho_daqs[i]) for i in pick]}; units gain L5 x{np.exp(U['L5']):.0f} FEM x{np.exp(U['FEM']):.0f}")


if __name__ == "__main__":
    main()
