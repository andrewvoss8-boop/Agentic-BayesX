#!/usr/bin/env python3
"""Apples-to-apples FRF figure (tufte skill): full predictive |H| bands for L5 (best previous) vs Beck (inferred
shape field) at held-out channels, under BOTH gain protocols, vs measured. Same forward/scoring machinery as
frf_compare.py. Columns = held-out channels (hard + typical); rows = gain protocol (whole-FRF gain = original L5
protocol; peak gain = QOI-appropriate). Shows that the L5-vs-Beck ranking is GAIN-DEPENDENT.

Q = accelerance |H| [g/lbf]; measured = single-impact hit-001 (YELLOW: 1 hit), 45-260 Hz; bands = 95% predictive
(posterior forward x observed-only model-form level offset). Source: out/frf_compare_summary.json + cached
out/frf_compare/l5_theta_0.npz. Output: figures/fig_frf_compare.png
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
import modal_beck_full as M
import frf_compare as FC

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; FIG.mkdir(exist_ok=True)
C_MEAS = "#222222"; C_L5 = "#2ca02c"; C_BECK = "#1f77b4"; NAVY = "#13456e"
HARD = {4, 27, 40, 52, 69, 92, 98}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": False, "figure.dpi": 140, "savefig.bbox": "tight"})


def bands(seed=0, n_draws=120):
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    obs_pos, ho_pos = FC.setup_split(R, meas, ch, freqs, fb, didx, dr, seed)
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]; drive = ch.drive_row
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    n_o = len(obs_pos)
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).transpose(1, 0)
    wq_obs = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).transpose(1, 0)
    cal = M.calibrate(n_modes=12); eta = M.per_mode_eta(cal, True)
    th_l5, _ = FC.l5_theta(R, meas, ch, fb, didx, obs_pos, seed, 600, 600, 4)
    th_beck = np.ones((cal["log_theta"].shape[0], 9)); th_beck[:, [2, 4, 6, 8]] = np.exp(cal["log_theta"])
    TH = {"L5": th_l5, "Beck": th_beck}
    out = {}
    for m in ("L5", "Beck"):
        thp = TH[m]; sub = np.linspace(0, thp.shape[0] - 1, min(thp.shape[0], n_draws)).astype(int)
        lm_obs, lm_ho = FC.ho_obs_logmag(m, R, freqs, thp, sub, obs_rows, ho_rows, drive,
                                         cal=(cal if m == "Beck" else None), eta=(eta if m == "Beck" else None))
        ptru_o = np.array([rf.core.qoi_peak(np.exp(tru_obs[:, k])) for k in range(n_o)])
        c_whole = np.array([hq.wmedian((tru_obs - lm_obs[j]).ravel(), wq_obs.ravel()) for j in range(len(sub))])
        pk0 = np.array([[rf.core.qoi_peak(np.exp(lm_obs[j, :, k])) for k in range(n_o)] for j in range(len(sub))])
        c_peak = np.array([float(np.median(np.log(ptru_o + 1e-300) - np.log(pk0[j] + 1e-300))) for j in range(len(sub))])
        for gname, c in (("wholeFRF", c_whole), ("peak", c_peak)):
            lm_ho_g = lm_ho + c[:, None, None]
            sig = float(np.std(tru_obs[None] - (lm_obs + c[:, None, None])))
            lvl = np.random.default_rng(seed + 1000).normal(0, max(sig, 1e-3), len(sub))
            tot = np.exp(lm_ho_g + lvl[:, None, None])           # (M, Nf, n_ho)
            out[(m, gname)] = (np.percentile(tot, 2.5, 0), np.median(tot, 0), np.percentile(tot, 97.5, 0))
    measured = {int(ch.daq[p]): np.abs(meas["H"][didx[ch.daq[p]]][fb]) for p in ho_pos}
    return freqs, ho_daqs, out, measured, ho_pos, ch, dr


def fig_bars():
    import json
    d = json.load(open(WS / "out" / "frf_compare_summary.json"))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.3))
    labels = ["whole-FRF gain\n(original L5 protocol)", "peak gain\n(matched, QOI-appropriate)"]
    for ax, q, ttl in ((a1, "peak_interval_score", "Held-out PEAK |H| interval score"),
                       (a2, "band_interval_score", "Held-out BAND-GRMS interval score")):
        x = np.arange(2); w = 0.35
        l5 = [d["methods"]["L5"]["gains"][g][q]["median"] for g in ("wholeFRF", "peak")]
        bk = [d["methods"]["Beck"]["gains"][g][q]["median"] for g in ("wholeFRF", "peak")]
        ax.bar(x - w / 2, l5, w, color=C_L5, label="L5 (best previous)")
        ax.bar(x + w / 2, bk, w, color=C_BECK, label="Beck (inferred shapes)")
        for xi, (a, b) in enumerate(zip(l5, bk)):
            ax.text(xi - w / 2, a + max(l5 + bk) * 0.01, f"{a:.0f}", ha="center", fontsize=8.5)
            ax.text(xi + w / 2, b + max(l5 + bk) * 0.01, f"{b:.0f}", ha="center", fontsize=8.5)
        ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5); ax.set_ylim(bottom=0)
        ax.set_title(ttl, fontsize=10.5, color=NAVY); ax.set_ylabel("interval score (lower = sharper)")
    a1.legend(fontsize=8.5, frameon=False, loc="upper right")
    a1.annotate("ranking FLIPS\nwith the gain", xy=(1, 790), xytext=(0.45, 1500), fontsize=8.5, color="#aa3333",
                arrowprops=dict(arrowstyle="->", color="#aa3333"))
    fig.suptitle("Apples-to-apples: L5 vs Beck is GAIN-DEPENDENT (25-split medians)", fontsize=12, color=NAVY, y=1.0)
    fig.text(0.5, -0.04, "out/frf_compare_summary.json. whole-FRF gain → L5 better (Beck 0/25); matched peak gain → "
             "Beck ~1.4× sharper (peak 25/25, band 23/25, cov 0.97). On the whole FRF, L5 is better under both gains.",
             ha="center", fontsize=7.4, wrap=True)
    fig.savefig(FIG / "fig_frf_compare_bars.png", bbox_inches="tight"); plt.close(fig)
    print("wrote", FIG / "fig_frf_compare_bars.png")


def main():
    fig_bars()
    freqs, ho_daqs, out, measured, ho_pos, ch, dr = bands(0)
    hard = [i for i, d in enumerate(ho_daqs) if d in HARD]
    rest = sorted([i for i in range(len(ho_daqs)) if i not in hard], key=lambda i: dr[ho_pos[i]], reverse=True)
    pick = (hard + rest)[:4]
    ymax = max(measured[ho_daqs[i]].max() for i in pick) * 3; ymin = min(measured[ho_daqs[i]].min() for i in pick) / 3
    fig, axes = plt.subplots(2, 4, figsize=(13.5, 6.4), sharex=True, sharey=True)
    rows = [("wholeFRF", "whole-FRF gain (original L5 protocol) — L5 better; Beck's 12-mode FRF over-leveled"),
            ("peak", "peak gain (QOI-appropriate, SAME for both) — L5 ≈ Beck on the peak")]
    for ri, (gname, rlab) in enumerate(rows):
        for ci, i in enumerate(pick):
            ax = axes[ri, ci]; d = ho_daqs[i]
            lo5, m5, h5 = (a[:, i] for a in out[("L5", gname)])
            lob, mb, hb = (a[:, i] for a in out[("Beck", gname)])
            ax.fill_between(freqs, lo5, h5, color=C_L5, alpha=0.16, lw=0)
            ax.fill_between(freqs, lob, hb, color=C_BECK, alpha=0.18, lw=0)
            ax.plot(freqs, m5, color=C_L5, lw=1.1); ax.plot(freqs, mb, color=C_BECK, lw=1.1)
            ax.plot(freqs, measured[d], color=C_MEAS, lw=1.1)
            ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(ymin, ymax)
            if ri == 0:
                tag = "HARD" if d in HARD else "typical"
                ax.set_title(f"DAQ {d} ({tag})", fontsize=9.5, color=NAVY)
            if ci == 0:
                ax.set_ylabel(f"|H| [g/lbf, log]\n{gname} gain", fontsize=8.5)
        axes[ri, 0].text(0.02, 0.04, rlab, transform=axes[ri, 0].transAxes, fontsize=7.4, color="#333333")
    for ax in axes[1]:
        ax.set_xlabel("frequency [Hz, log]", fontsize=8.5)
    a0 = axes[0, 0]
    a0.text(0.02, 0.96, "measured", color=C_MEAS, transform=a0.transAxes, fontsize=8, va="top")
    a0.text(0.02, 0.88, "L5 (best previous) 95%", color=C_L5, transform=a0.transAxes, fontsize=8, va="top")
    a0.text(0.02, 0.80, "Beck inferred shapes 95%", color=C_BECK, transform=a0.transAxes, fontsize=8, va="top")
    fig.suptitle("Apples-to-apples held-out FRF: L5 vs Beck under TWO gain protocols (the ranking is gain-dependent)",
                 fontsize=11.5, color=NAVY, y=0.995)
    fig.text(0.5, -0.02, "Same splits, same observed-only model-form level offset, same forward/scoring machinery "
             "(frf_compare.py). TOP: the original whole-FRF gain over-levels Beck's sparse 12-mode FRF (L5 better). "
             "BOTTOM: with a shared peak gain, L5 and Beck are comparable on the peak. Full-MC numbers: "
             "out/frf_compare_summary.json.", ha="center", fontsize=7.3, wrap=True)
    fig.savefig(FIG / "fig_frf_compare.png", bbox_inches="tight"); plt.close(fig)
    print("wrote", FIG / "fig_frf_compare.png", "channels", [ho_daqs[i] for i in pick])


if __name__ == "__main__":
    main()
