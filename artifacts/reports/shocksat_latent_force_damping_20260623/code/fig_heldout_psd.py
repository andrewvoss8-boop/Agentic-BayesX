#!/usr/bin/env python3
"""Held-out-sensor PSD examples in the style of the live program's heldout_psd_examples.png, but showing THIS
study's posterior FRF: the MEASURED-zeta-corrected twin vs the original FEM vs the measured data.

Rows = 3 held-out sensors spanning the FEM band bias (over- / near- / under-predict). Columns:
  left  (unsmoothed): measured data | FEM (theta=1, nominal zeta=1%) | twin median + 2.5-97.5% band (measured-zeta)
  right (smoothed):   measured data | FEM smoothed envelope | twin 97.5% smoothed envelope NOMINAL-zeta (dashed)
                      | twin 97.5% smoothed envelope MEASURED-zeta (solid)
The nominal-vs-measured-zeta twin contrast is the point: the time-domain measured zeta (~0.4%) is LIGHTER than the
FEM nominal 1%, so it RAISES the modal peaks (the FEM is over-damped) -- visible as the solid twin envelope sitting
ABOVE the dashed one. Reuses probe.fit_context + layer3 measured_eta BYTE-IDENTICAL (same numbers as the probe/L3).
PSD = |H|^2 * S_F0 (S_F0 = 1 lbf^2/Hz flat); log-log axes (the standard MPE / qualification-spec view)."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "shocksat_psd_envelope_twin_20260623" / "code"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe as P
import psd_envelope as pe
from layer3_value import measured_eta

WS = Path(__file__).resolve().parent.parent
REF = "m_xpos_990x"; REF_LABEL = "+X modal (Test01, node 990)"
C_DATA, C_FEM, C_TWIN, C_TWIN_NOM = "#222222", "#1f77b4", "#d2691e", "#c8c8c8"


def main(seed=0, obs_frac=0.9):
    ctx = P.fit_context(seed=seed, obs_frac=obs_frac)
    f = ctx.freqs
    eta_nom = 2.0 * P.zeta_eff(f)            # FEM/twin nominal damping (1% structural + window)
    eta_meas = measured_eta(f)              # time-domain measured zeta per mode (+ window)

    def twin975(d, eta):
        ctx.eta = eta
        return np.percentile(P.twin_psd_draws(ctx, [REF], d), 97.5, axis=0)

    def twin_draws_meas(d):
        ctx.eta = eta_meas
        return P.twin_psd_draws(ctx, [REF], d)

    def fem(d):
        ctx.eta = eta_nom
        return P.fem_psd(ctx, [REF], d)

    def data(d):
        ctx.eta = eta_nom
        return P.data_psd(ctx, [REF], d)

    # pick 3 held-out sensors spanning the FEM band-GRMS bias (data/FEM)
    bias = {d: pe.grms(f, data(d)) / (pe.grms(f, fem(d)) + 1e-300) for d in ctx.ho_daqs}
    order = sorted(ctx.ho_daqs, key=lambda d: bias[d])
    pick = [order[0], order[len(order) // 2], order[-1]]
    tags = ["FEM over-predicts", "FEM ~matches", "FEM under-predicts"]

    allv = []
    for d in pick:
        allv += [data(d), fem(d), np.percentile(twin_draws_meas(d), 97.5, axis=0)]
    lo = max(np.min([v[v > 0].min() for v in allv]) * 0.3, 1e-9)
    hi = np.max([v.max() for v in allv]) * 3

    fig, axes = plt.subplots(len(pick), 2, figsize=(11.5, 2.7 * len(pick)), sharex=True, sharey=True)
    for r, (d, tag) in enumerate(zip(pick, tags)):
        dp, fp = data(d), fem(d)
        draws = twin_draws_meas(d)
        tmed = np.median(draws, axis=0); t975 = np.percentile(draws, 97.5, axis=0); t025 = np.percentile(draws, 2.5, axis=0)
        env_fem = pe.smoothline_envelope(f, fp)
        env_t_nom = pe.smoothline_envelope(f, twin975(d, eta_nom))
        env_t_meas = pe.smoothline_envelope(f, t975)
        g_fem, g_nom, g_meas = pe.grms(f, env_fem), pe.grms(f, env_t_nom), pe.grms(f, env_t_meas)

        axL, axR = axes[r, 0], axes[r, 1]
        axL.fill_between(f, t025, t975, color=C_TWIN, alpha=0.16, lw=0, label="twin 2.5–97.5% band (meas-ζ)")
        axL.plot(f, tmed, color=C_TWIN, lw=1.1, label="twin median (meas-ζ)")
        axL.plot(f, fp, color=C_FEM, lw=1.0, ls="--", label="FEM (θ=1, ζ=1%)")
        axL.plot(f, dp, color=C_DATA, lw=1.2, label="measured data")
        axL.set_ylabel(f"ch {d}  ({tag})\nPSD  g²/Hz", fontsize=8)

        axR.plot(f, dp, color=C_DATA, lw=1.0, alpha=0.7, label="measured data")
        axR.plot(f, env_fem, color=C_FEM, lw=1.5, label="FEM smoothed (ζ=1%)")
        axR.plot(f, env_t_nom, color=C_TWIN_NOM, lw=1.6, ls="--", label="twin 97.5% smoothed (nominal ζ=1%)")
        axR.plot(f, env_t_meas, color=C_TWIN, lw=1.8, label="twin 97.5% smoothed (measured ζ~0.4%)")
        axR.text(0.03, 0.05, f"smoothed GRMS  FEM {g_fem:.2g} | twin nom-ζ {g_nom:.2g} | twin meas-ζ {g_meas:.2g}\n"
                 f"measured ζ is LIGHTER → peaks & GRMS RISE (meas/nom {g_meas/g_nom:.2f}×): FEM is over-damped",
                 transform=axR.transAxes, fontsize=7.0, va="bottom",
                 bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="0.8", lw=0.5))
        print(f"  ch {d:3d} ({tag:18s}): smoothed GRMS FEM {g_fem:.3g} | twin nom-ζ {g_nom:.3g} | "
              f"twin meas-ζ {g_meas:.3g} (meas/nom {g_meas/g_nom:.2f}×, twin/FEM {g_meas/g_fem:.1f}×)")
        for ax in (axL, axR):
            ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(45, 260); ax.set_ylim(lo, hi)
            ax.spines[["top", "right"]].set_visible(False); ax.tick_params(labelsize=7)
        if r == 0:
            axL.set_title("unsmoothed:  data · FEM · twin median + 2.5–97.5% band (measured-ζ posterior)", fontsize=8.3)
            axR.set_title("smoothed:  data · FEM · twin 97.5% (nominal-ζ vs measured-ζ)", fontsize=8.3)
            axL.legend(fontsize=6.4, loc="upper left", frameon=False, handlelength=1.4, labelspacing=0.3)
            axR.legend(fontsize=6.2, loc="upper left", frameon=False, handlelength=1.4, labelspacing=0.3)
    for c in range(2):
        axes[-1, c].set_xlabel("frequency  (Hz, log)", fontsize=8)

    cap = (f"ShockSat held-out-SENSOR response PSD = |H|²·S_F0 (S_F0=1 lbf²/Hz flat), {REF_LABEL}, 6 hits; MEASURED "
           f"data (modal hammer) vs FEM (θ=1) and the calibrated twin. The TWIN POSTERIOR here uses the TIME-DOMAIN "
           f"MEASURED per-mode damping ζ~0.4% (Layer-1 NUTS); the dashed twin uses the FEM nominal ζ=1%. Split seed "
           f"{seed}, {int(obs_frac*100)}% training ({len(ctx.obs_daqs)} obs / {len(ctx.ho_daqs)} held-out); calib "
           f"converged R-hat {ctx.diag['max_rhat']:.3f}; units-gain ×{np.exp(ctx.gain):.2f}; twin band σ={ctx.sig:.2f} "
           f"(log) → ~+{10*np.log10(np.exp(2*1.96*ctx.sig)):.0f} dB. TAKEAWAY: injecting the MEASURED (lighter) ζ "
           f"RAISES the posterior FRF peaks (the FEM at 1% is over-damped), so the smoothed twin sits ABOVE the "
           f"nominal-ζ twin — a measured-ζ correction makes the envelope MORE conservative, not less; the twin's honest "
           f"covering band is still set by per-node FEM mode-shape error, not damping. Exploratory; reuses probe/L3.")
    fig.text(0.012, -0.02 / len(pick), cap, fontsize=6.8, wrap=True, va="top")
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    out = WS / "figures" / "fig6_heldout_psd_examples.png"
    fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
    print(f"wrote {out}  (held-out sensors {pick}, biases {[round(bias[d],2) for d in pick]})")


if __name__ == "__main__":
    main()
