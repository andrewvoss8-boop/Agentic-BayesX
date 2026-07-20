#!/usr/bin/env python3
"""Example held-out-sensor figures (Andrew request): data + UNSMOOTHED fem/twin + SMOOTHED fem+6dB / twin-97.5%
envelopes. Small multiples: rows = 3 held-out sensors chosen to span the FEM bias (over- / near- / under-predict),
columns = [unsmoothed | smoothed]. Reference = +X modal (Test01, node 990, cleanest). Reuses probe.fit_context
(identical numbers to the probe). Tufte: log–log, direct labels, data-ink, caption carries units/source/takeaway.
PSD = |H|²·S_F0 (S_F0=1 lbf²/Hz flat); axes log–log (the standard MPE / qualification-spec view)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe as P
import psd_envelope as pe

WS = Path(__file__).resolve().parent.parent
REF = "m_xpos_990x"; REF_LABEL = "+X modal (Test01, node 990)"
C_DATA, C_FEM, C_TWIN = "#222222", "#1f77b4", "#d2691e"


def main(seed=0, obs_frac=0.9):
    ctx = P.fit_context(seed=seed, obs_frac=obs_frac)
    f = ctx.freqs
    # choose 3 held-out sensors spanning the FEM band-GRMS bias (data/FEM)
    bias = {}
    for d in ctx.ho_daqs:
        bias[d] = pe.grms(f, P.data_psd(ctx, [REF], d)) / (pe.grms(f, P.fem_psd(ctx, [REF], d)) + 1e-300)
    order = sorted(ctx.ho_daqs, key=lambda d: bias[d])
    pick = [order[0], order[len(order) // 2], order[-1]]            # FEM over- / near- / under-predicts
    tags = ["FEM over-predicts", "FEM ~matches", "FEM under-predicts"]

    # consistent y-range across panels
    allv = []
    for d in pick:
        allv += [P.data_psd(ctx, [REF], d), P.fem_psd(ctx, [REF], d),
                 np.percentile(P.twin_psd_draws(ctx, [REF], d), 97.5, axis=0)]
    lo = max(np.min([v[v > 0].min() for v in allv]) * 0.3, 1e-9)
    hi = np.max([v.max() for v in allv]) * 3

    fig, axes = plt.subplots(len(pick), 2, figsize=(11.5, 2.7 * len(pick)), sharex=True, sharey=True)
    for r, (d, tag) in enumerate(zip(pick, tags)):
        dp = P.data_psd(ctx, [REF], d); fp = P.fem_psd(ctx, [REF], d)
        draws = P.twin_psd_draws(ctx, [REF], d)
        tmed = np.median(draws, axis=0); t975 = np.percentile(draws, 97.5, axis=0); t025 = np.percentile(draws, 2.5, axis=0)
        env_t = pe.smoothline_envelope(f, t975); env_f6 = pe.smoothline_envelope(f, pe.add_db_psd(fp, 6.0))
        gt, gf = pe.grms(f, env_t), pe.grms(f, env_f6)
        et = pe.exceedance(f, dp, env_t)["exceeding_energy_fraction"]
        ef = pe.exceedance(f, dp, env_f6)["exceeding_energy_fraction"]

        axL, axR = axes[r, 0], axes[r, 1]
        # left: unsmoothed
        axL.fill_between(f, t025, t975, color=C_TWIN, alpha=0.18, lw=0, label="twin 2.5–97.5% band")
        axL.plot(f, tmed, color=C_TWIN, lw=1.1, label="twin median")
        axL.plot(f, fp, color=C_FEM, lw=1.0, ls="--", label="FEM (θ=1)")
        axL.plot(f, dp, color=C_DATA, lw=1.2, label="measured data")
        axL.set_ylabel(f"ch {d}  ({tag})\nPSD  g²/Hz", fontsize=8)
        # right: smoothed envelopes + data
        axR.plot(f, dp, color=C_DATA, lw=1.0, alpha=0.7, label="measured data")
        axR.plot(f, env_f6, color=C_FEM, lw=1.7, label="FEM + 6 dB envelope")
        axR.plot(f, env_t, color=C_TWIN, lw=1.7, label="twin 97.5% envelope")
        axR.text(0.03, 0.06, f"GRMS  twin {gt:.2g} | FEM+6dB {gf:.2g}  (ratio {gt/gf:.1f}×)\n"
                 f"data above: twin {et*100:.0f}% | FEM+6dB {ef*100:.0f}% of energy",
                 transform=axR.transAxes, fontsize=7.0, va="bottom",
                 bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.8", lw=0.5))
        for ax in (axL, axR):
            ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(45, 260); ax.set_ylim(lo, hi)
            ax.spines[["top", "right"]].set_visible(False)
            ax.tick_params(labelsize=7)
        if r == 0:
            axL.set_title("unsmoothed:  data · FEM · twin median + 2.5–97.5% band", fontsize=8.5)
            axR.set_title("smoothed envelopes:  data · FEM+6 dB · twin 97.5%", fontsize=8.5)
            axL.legend(fontsize=6.6, loc="upper left", frameon=False, handlelength=1.4, labelspacing=0.3)
            axR.legend(fontsize=6.6, loc="upper left", frameon=False, handlelength=1.4, labelspacing=0.3)
    for c in range(2):
        axes[-1, c].set_xlabel("frequency  (Hz, log)", fontsize=8)

    cap = (f"ShockSat held-out-SENSOR response PSD = |H|²·S_F0 (S_F0=1 lbf²/Hz flat), {REF_LABEL}, 6 hits; "
           f"MEASURED data (modal hammer, coherence ~0.97 at peaks) vs FEM (θ=1) and the calibrated twin "
           f"(97.5% = top of 2-sided 95% band). Split seed {seed}, {int(obs_frac*100)}% training "
           f"({len(ctx.obs_daqs)} obs / {len(ctx.ho_daqs)} held-out sensors); calib converged R-hat "
           f"{ctx.diag['max_rhat']:.3f}. ONE training-global units-gain ×{np.exp(ctx.gain):.2f}; amplitude "
           f"discrepancy σ={ctx.sig:.2f} (log) → twin band ~+{10*np.log10(np.exp(2*1.96*ctx.sig)):.0f} dB. "
           f"TAKEAWAY: the twin's honest covering band is far wider than FEM+6 dB (loses on GRMS), AND FEM+6 dB "
           f"does not envelope the data — both limited by per-node FEM mode-shape error. Exploratory probe.")
    fig.text(0.012, -0.02 / len(pick), cap, fontsize=7.0, wrap=True, va="top")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    out = WS / "figures" / "heldout_psd_examples.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {out}  (held-out sensors {pick}, biases {[round(bias[d],2) for d in pick]})")


if __name__ == "__main__":
    main()
