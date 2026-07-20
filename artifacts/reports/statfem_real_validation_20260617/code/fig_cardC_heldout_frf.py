#!/usr/bin/env python3
"""Card C Phase 1(d) figure (tufte-data-graphics skill applied): held-out impact-channel FRF at the HARD channels,
measured |H1| vs the inferred-shape-field Beck twin band vs the FEM-shape Beck band, with the L5 peak-QOI median
overlaid. Small multiples, same log-log scales across panels; direct labels; caption carries quantity/units/source.

Quantity (Q): accelerance |H| = |a_response / F_drive| [g / lbf], drive = the +X impact node, single-impact hit-001
(YELLOW: 1 hit). Bands = 95% predictive interval of |H|(f): posterior (theta, shape-field phi) draws of the modal
reconstruction x a per-draw log-normal level offset exp(N(0, sigma_QOI)) with sigma_QOI estimated on OBSERVED
channels only (same model-form discrepancy as L5; fair). x-axis log frequency (45-260 Hz band); y-axis log |H|.

Source: out/beck_calib_nm12.npz (cached Beck calibration, R-hat 1.004, 0 div), out/heldout_qoi_L5.json (L5 peak QOI).
Output: figures/fig_cardC_heldout_frf.png
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq
import modal_beck_full as M

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; FIG.mkdir(exist_ok=True)
HARD = {4, 27, 40, 52, 69, 92, 98}                 # the 7 consistent-fail channels (D20/D21: impact-face interfaces)
C_MEAS = "#222222"; C_INF = "#1f77b4"; C_FEM = "#d62728"
plt.rcParams.update({"font.size": 9.5, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": False, "figure.dpi": 140, "savefig.bbox": "tight"})


def frf_bands(cal, seed=0, n_draws=120, n_panels=6):
    """For one split, return per-channel measured |H|(f) and the INFER/FEM Beck 95% predictive |H| bands.
    Gain fit on OBSERVED peaks; level offset from observed-only sigma_QOI (fair). Picks hard held-out channels."""
    R = cal["R"]; phi0 = cal["phi0"]
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(0.6 * len(perm))); obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_rows = ch.rows[obs_pos]; obs_daqs = [ch.daq[p] for p in obs_pos]
    ho_daqs = [ch.daq[p] for p in ho_pos]
    peak_tru_obs = np.array([rf.core.qoi_peak(np.abs(meas["H"][didx[d]][fb])) for d in obs_daqs])
    eta = M.per_mode_eta(cal, True)
    log_theta = cal["log_theta"]; raw = cal["raw"]
    sub = np.linspace(0, raw.shape[0] - 1, min(raw.shape[0], n_draws)).astype(int)
    theta_post = np.ones((log_theta.shape[0], 9)); theta_post[:, [2, 4, 6, 8]] = np.exp(log_theta)

    def ensemble(rows, use_inferred):
        curves = np.zeros((len(sub), len(freqs), rows.shape[0]))
        peak_o = np.zeros((len(sub), len(obs_pos)))
        for j, s in enumerate(sub):
            theta = theta_post[s]; K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
            phi = (phi0 + M.TAU * raw[s]) if use_inferred else phi0
            Phi = phi / (np.linalg.norm(phi, axis=0, keepdims=True) + 1e-30)
            w2r = np.sum(phi * (K @ phi), 0) / (np.sum(phi * phi, 0) + 1e-30)
            mag_o0 = M.reconstruct_mag(Phi, w2r, obs_rows, ch.drive_row, freqs, 0.0, eta)
            obs_pk = np.array([rf.core.qoi_peak(mag_o0[:, k]) for k in range(len(obs_pos))])
            c = float(np.median(np.log(peak_tru_obs + 1e-30) - np.log(obs_pk + 1e-30)))
            curves[j] = M.reconstruct_mag(Phi, w2r, rows, ch.drive_row, freqs, c, eta)
            peak_o[j] = obs_pk * np.exp(c)
        sig = float(np.std(np.log(np.median(peak_o, 0) + 1e-300) - np.log(peak_tru_obs + 1e-300)))
        drng = np.random.default_rng(seed + 11)
        off = np.exp(drng.normal(0, max(sig, 1e-3), (len(sub), 1, rows.shape[0])))
        tot = curves * off                                          # total predictive (theta + model-form level)
        lo = np.percentile(tot, 2.5, axis=0); hi = np.percentile(tot, 97.5, axis=0)
        med = np.median(tot, axis=0)
        return lo, med, hi

    # choose held-out channels: hard ones first, then highest-DR held-out to fill
    hard_ho = [i for i, d in enumerate(ho_daqs) if d in HARD]
    rest = [i for i in range(len(ho_daqs)) if i not in hard_ho]
    rest.sort(key=lambda i: dr[ho_pos[i]], reverse=True)
    pick = (hard_ho + rest)[:n_panels]
    ho_rows = ch.rows[ho_pos[pick]]
    lo_i, med_i, hi_i = ensemble(ho_rows, True)
    lo_f, med_f, hi_f = ensemble(ho_rows, False)
    L5 = json.loads((WS / "out" / "heldout_qoi_L5.json").read_text())["per_channel_theta_plus_qoi_discrepancy"]
    panels = []
    for col, i in enumerate(pick):
        d = ho_daqs[i]
        meas_mag = np.abs(meas["H"][didx[d]][fb])
        l5 = L5.get(str(int(d)))
        panels.append(dict(daq=int(d), hard=(d in HARD), freqs=freqs, meas=meas_mag,
                           lo_i=lo_i[:, col], med_i=med_i[:, col], hi_i=hi_i[:, col],
                           lo_f=lo_f[:, col], med_f=med_f[:, col], hi_f=hi_f[:, col],
                           l5_peak_med=(l5["peak_med"] if l5 else None),
                           peak_freq=freqs[int(np.argmax(meas_mag))]))
    return panels


def main(seed=0):
    cal = M.calibrate(n_modes=12)
    panels = frf_bands(cal, seed=seed)
    n = len(panels); ncol = 3; nrow = int(np.ceil(n / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(11, 3.0 * nrow), sharex=True)
    axes = np.atleast_1d(axes).ravel()
    ymax = max(p["meas"].max() for p in panels) * 3
    ymin = min(p["meas"].min() for p in panels) / 3
    for ax, p in zip(axes, panels):
        f = p["freqs"]
        ax.fill_between(f, p["lo_f"], p["hi_f"], color=C_FEM, alpha=0.13, lw=0)
        ax.fill_between(f, p["lo_i"], p["hi_i"], color=C_INF, alpha=0.22, lw=0)
        ax.plot(f, p["med_f"], color=C_FEM, lw=1.0, ls="--")
        ax.plot(f, p["med_i"], color=C_INF, lw=1.3)
        ax.plot(f, p["meas"], color=C_MEAS, lw=1.2)
        if p["l5_peak_med"] is not None:
            ax.plot(p["peak_freq"], p["l5_peak_med"], marker="o", ms=5, mfc="none",
                    mec="#2ca02c", mew=1.4, ls="none")
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(ymin, ymax)
        tag = "HARD (impact-face interface)" if p["hard"] else "typical held-out"
        ax.set_title(f"DAQ {p['daq']} — {tag}", fontsize=9)
    for ax in axes[n:]:
        ax.set_visible(False)
    for ax in axes[:n]:
        ax.set_xlabel("frequency [Hz, log]", fontsize=8.5)
    for r in range(nrow):
        axes[r * ncol].set_ylabel("|H| [g/lbf, log]", fontsize=8.5)
    # direct labels in the first panel
    a0 = axes[0]
    a0.text(0.03, 0.94, "measured |H1|", color=C_MEAS, transform=a0.transAxes, fontsize=8, va="top")
    a0.text(0.03, 0.84, "inferred shape-field (95%)", color=C_INF, transform=a0.transAxes, fontsize=8, va="top")
    a0.text(0.03, 0.74, "FEM shapes (95%)", color=C_FEM, transform=a0.transAxes, fontsize=8, va="top")
    a0.text(0.03, 0.64, "L5 peak QOI (median) ○", color="#2ca02c", transform=a0.transAxes, fontsize=8, va="top")
    fig.suptitle("Held-out impact-channel FRF: inferring the mode-shape FIELD sharpens vs FEM shapes "
                 "(Beck/Au/Vanik 2001)", fontsize=10.5, y=0.995)
    fig.text(0.5, -0.02,
             "Q = accelerance |H| = |a_resp / F_drive| [g/lbf]; drive = +X impact node; measured = single-impact "
             "hit-001 (YELLOW: 1 hit, 45-260 Hz). Bands = 95% predictive (theta + shape-field posterior x observed-"
             "only model-form level offset). Held-out MC peak IS median: inferred 773 vs L5 1661 vs FEM 1252 "
             "(out/mc_beck_full_summary.json). Calibration split-independent (global .ash survey).",
             ha="center", fontsize=7.4, wrap=True)
    p = FIG / "fig_cardC_heldout_frf.png"
    fig.savefig(p, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {p} ({n} panels: {[pp['daq'] for pp in panels]})")
    return p


if __name__ == "__main__":
    main()
