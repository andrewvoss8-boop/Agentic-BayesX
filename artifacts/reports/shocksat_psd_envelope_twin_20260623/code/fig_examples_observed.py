#!/usr/bin/env python3
"""Example OBSERVED (NOT-held-out / training) sensor figures (Andrew request): same layout as fig_examples.py but
the 3 example sensors are drawn from ctx.obs_daqs (the training sensors) instead of ctx.ho_daqs (held-out).

HONEST FRAMING (this is the whole point of the contrast):
  - Observed sensors are IN-SAMPLE. Their measured modal FREQUENCIES were used to calibrate theta, AND the single
    training-global units-gain c and the broadband amplitude-discrepancy band-width sigma were fit from the OBSERVED
    channels' peak heights. So by construction these sensors should be covered BETTER than the held-out ones.
  - This is a diagnostic CONTRAST to heldout_psd_examples.png, NOT a held-out generalization result and NOT any
    metric-improvement claim. Same calibration context (seed 0, 90% train) as the held-out figure.

Everything else (PSD = |H|^2 * S_F0, smoothline envelope, FEM+6 dB bar, twin 97.5% band, scoring numbers) is reused
byte-identical from probe.fit_context / psd_envelope, so numbers are directly comparable to the held-out figure."""
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
    # choose 3 OBSERVED (training) sensors spanning the FEM band-GRMS bias (data/FEM)
    bias = {}
    for d in ctx.obs_daqs:
        bias[d] = pe.grms(f, P.data_psd(ctx, [REF], d)) / (pe.grms(f, P.fem_psd(ctx, [REF], d)) + 1e-300)
    order = sorted(ctx.obs_daqs, key=lambda d: bias[d])
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
        axL.fill_between(f, t025, t975, color=C_TWIN, alpha=0.18, lw=0, label="twin 2.5-97.5% band")
        axL.plot(f, tmed, color=C_TWIN, lw=1.1, label="twin median")
        axL.plot(f, fp, color=C_FEM, lw=1.0, ls="--", label="FEM (theta=1)")
        axL.plot(f, dp, color=C_DATA, lw=1.2, label="measured data")
        axL.set_ylabel(f"ch {d}  ({tag})\nPSD  g2/Hz", fontsize=8)
        # right: smoothed envelopes + data
        axR.plot(f, dp, color=C_DATA, lw=1.0, alpha=0.7, label="measured data")
        axR.plot(f, env_f6, color=C_FEM, lw=1.7, label="FEM + 6 dB envelope")
        axR.plot(f, env_t, color=C_TWIN, lw=1.7, label="twin 97.5% envelope")
        axR.text(0.03, 0.06, f"GRMS  twin {gt:.2g} | FEM+6dB {gf:.2g}  (ratio {gt/gf:.1f}x)\n"
                 f"data above: twin {et*100:.0f}% | FEM+6dB {ef*100:.0f}% of energy",
                 transform=axR.transAxes, fontsize=7.0, va="bottom",
                 bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.8", lw=0.5))
        for ax in (axL, axR):
            ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(45, 260); ax.set_ylim(lo, hi)
            ax.spines[["top", "right"]].set_visible(False)
            ax.tick_params(labelsize=7)
        if r == 0:
            axL.set_title("unsmoothed:  data . FEM . twin median + 2.5-97.5% band  (OBSERVED sensors)", fontsize=8.5)
            axR.set_title("smoothed envelopes:  data . FEM+6 dB . twin 97.5%  (OBSERVED sensors)", fontsize=8.5)
            axL.legend(fontsize=6.6, loc="upper left", frameon=False, handlelength=1.4, labelspacing=0.3)
            axR.legend(fontsize=6.6, loc="upper left", frameon=False, handlelength=1.4, labelspacing=0.3)
    for c in range(2):
        axes[-1, c].set_xlabel("frequency  (Hz, log)", fontsize=8)

    cap = (f"ShockSat OBSERVED (NOT-held-out / training) SENSOR response PSD = |H|^2*S_F0 (S_F0=1 lbf^2/Hz flat), "
           f"{REF_LABEL}, 6 hits; MEASURED data (modal hammer, coherence ~0.97 at peaks) vs FEM (theta=1) and the "
           f"calibrated twin (97.5% = top of 2-sided 95% band). Split seed {seed}, {int(obs_frac*100)}% training "
           f"({len(ctx.obs_daqs)} observed / {len(ctx.ho_daqs)} held-out); calib converged R-hat "
           f"{ctx.diag['max_rhat']:.3f}. ONE training-global units-gain x{np.exp(ctx.gain):.2f}; amplitude "
           f"discrepancy sigma={ctx.sig:.2f} (log) -> twin band ~+{10*np.log10(np.exp(2*1.96*ctx.sig)):.0f} dB. "
           f"IN-SAMPLE CAVEAT: these sensors' modal frequencies were used to calibrate theta AND the gain + sigma band "
           f"were fit from observed-channel peak heights, so they are expected to be covered better than the held-out "
           f"sensors (compare heldout_psd_examples.png). Diagnostic contrast, not a held-out result. Exploratory probe.")
    fig.text(0.012, -0.02 / len(pick), cap, fontsize=7.0, wrap=True, va="top")
    fig.tight_layout(rect=[0, 0.04, 1, 1])
    out = WS / "figures" / "observed_psd_examples.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {out}  (observed sensors {pick}, biases {[round(bias[d],2) for d in pick]})")


if __name__ == "__main__":
    main()
