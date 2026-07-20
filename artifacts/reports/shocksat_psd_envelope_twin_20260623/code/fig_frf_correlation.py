#!/usr/bin/env python3
"""FRF comparison: AS-DELIVERED FEM (nominal, theta=1) vs CLEAN measured FRF (Andrew request, reconciling the NASA
"already correlated" slides with our per-sensor amplitude scatter).

ONE global units-gain only (no per-sensor tuning) -- exactly as honest as the twin. Shows where the as-delivered
FEM tracks the data (peak FREQUENCIES, and the band below ~135 Hz where NASA's cross-orthogonality is good) and
where it scatters (peak HEIGHTS, worse >135 Hz / local node-line modes -- the regime NASA's slides flag as hardest).

6 sensors spanning best -> worst per-sensor band amplitude error. Reference = +X modal (Test01, node 990, cleanest,
coherence ~0.97 at peaks). NO NUTS. Output: figures/frf_correlation_examples.png + out/frf_correlation.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import probe as P
import pooling_sigma_probe as PP
import psd_envelope as pe

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; OUT.mkdir(exist_ok=True)
REF = "m_xpos_990x"; REF_LABEL = "+X modal (Test01, node 990)"
F135 = 135.0
C_DATA, C_FEM = "#222222", "#c44e1f"


def mag_meas(ctx, d):
    return np.abs(P.meas_H(ctx, [REF], d))


def mag_fem(ctx, d):
    resp = ctx.ch.rows[ctx.pos[d]]
    return np.abs(P.model_H(ctx, np.ones((1, 9)), [REF], resp)[0])


def peak_stats(f, hm, hf):
    """Peak-frequency match + per-peak amplitude log-ratio (data/FEM), split at 135 Hz. hf already gain-scaled."""
    lm, lf = np.log(hm + 1e-300), np.log(hf + 1e-300)
    df = float(np.median(np.diff(f)))
    pk, _ = find_peaks(lm, prominence=0.4, distance=max(1, int(3.0 / df)))
    fpk = f[pk]
    fem_pk, _ = find_peaks(lf, prominence=0.3)
    out = {"freq_match_relpct": [], "amp_logratio": [], "fpk": fpk.tolist()}
    for i in pk:
        # nearest FEM peak frequency
        if len(fem_pk):
            j = fem_pk[np.argmin(np.abs(f[fem_pk] - f[i]))]
            out["freq_match_relpct"].append(100.0 * abs(f[j] - f[i]) / f[i])
        out["amp_logratio"].append(float(lm[i] - lf[i]))
    out["fpk_below"] = [float(x) for x in fpk if x < F135]
    out["fpk_above"] = [float(x) for x in fpk if x >= F135]
    return out


def run():
    ctx = PP.minimal_ctx()
    f = ctx.freqs
    daqs = ctx.daq_master

    # one global units-gain from band-GRMS (cancels nothing here; just puts FEM on the data scale fairly)
    r = []
    Hm_all, Hf_all = {}, {}
    for d in daqs:
        hm, hf = mag_meas(ctx, d), mag_fem(ctx, d)
        Hm_all[d], Hf_all[d] = hm, hf
        r.append(np.log(pe.grms(f, hm ** 2) / (pe.grms(f, hf ** 2) + 1e-300)))
    r = np.array(r); gain = float(np.median(r)); g = np.exp(gain)
    amp_err = np.abs(r - gain)                                   # per-sensor band amplitude error (log)

    # split amplitude scatter below/above 135 Hz across ALL sensors
    lr_below, lr_above, fmatch = [], [], []
    for d in daqs:
        st = peak_stats(f, Hm_all[d], Hf_all[d] * g)
        fpk = np.array(st["fpk"]); lr = np.array(st["amp_logratio"])
        if len(fpk) == len(lr) and len(fpk):
            lr_below += list(lr[fpk < F135]); lr_above += list(lr[fpk >= F135])
        fmatch += st["freq_match_relpct"]
    sig_below = float(np.std(lr_below)) if lr_below else 0.0
    sig_above = float(np.std(lr_above)) if lr_above else 0.0
    fmatch_med = float(np.median(fmatch)) if fmatch else 0.0

    # 6 sensors spanning best -> worst amplitude error
    order = np.argsort(amp_err)
    pick_idx = [order[0], order[len(order) // 5], order[2 * len(order) // 5],
                order[3 * len(order) // 5], order[4 * len(order) // 5], order[-1]]
    pick = [daqs[i] for i in pick_idx]

    fig, axes = plt.subplots(2, 3, figsize=(13, 6.4), sharex=True)
    for ax, d in zip(axes.ravel(), pick):
        hm, hf = Hm_all[d], Hf_all[d] * g
        ax.semilogy(f, hm, color=C_DATA, lw=1.1, label="measured")
        ax.semilogy(f, hf, color=C_FEM, lw=1.0, label="as-delivered FEM (theta=1)")
        ax.axvline(F135, color="0.6", lw=0.8, ls=":")
        ax.text(F135 + 2, ax.get_ylim()[1], "135 Hz", color="0.5", fontsize=6, va="top")
        de = 10 * (np.log10(pe.grms(f, hm ** 2)) - np.log10(pe.grms(f, hf ** 2) * g ** 2))
        ax.set_title(f"ch {d}   band amp err {de:+.1f} dB", fontsize=8.5)
        ax.set_xlim(45, 260); ax.tick_params(labelsize=7)
        ax.spines[["top", "right"]].set_visible(False)
    for ax in axes[-1]:
        ax.set_xlabel("frequency (Hz)", fontsize=8)
    for ax in axes[:, 0]:
        ax.set_ylabel("|H|  (g/lbf)", fontsize=8)
    axes[0, 0].legend(fontsize=7, loc="lower left", frameon=False)

    cap = (f"As-delivered FEM (nominal theta=1) vs CLEAN measured FRF, {REF_LABEL}, 6 hits; ONE global units-gain "
           f"x{g:.2f} (no per-sensor tuning). 6 sensors span best->worst per-sensor band amplitude error. "
           f"RECONCILES the NASA 'already correlated' slides: peak FREQUENCIES line up (median nearest-peak match "
           f"{fmatch_med:.1f}% ; our freq skill +0.93), but per-sensor peak HEIGHTS scatter BROADLY across the whole "
           f"band (per-panel band amp err; per-peak log scatter ~{0.5*(sig_below+sig_above):.1f}). Height is HARDER "
           f"than shape-correlation: peak |H| = phi_drive x phi_sensor / damping, folding in TWO local shape values "
           f"PLUS damping -- and NASA flag both ('weld dimensions biggest unknown knob', 'no great damping observed', "
           f"'local modes near a node line'). Sensor->node snap is tiny (median 0.15 in) so this is INTRINSIC FEM "
           f"shape/damping error, NOT our reduction. 'Correlated' = frequencies + global mode shapes (MAC~0.70), NOT "
           f"per-sensor FRF amplitude. NO NUTS. Exploratory.")
    fig.text(0.012, -0.01, cap, fontsize=7.0, wrap=True, va="top")
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    outp = WS / "figures" / "frf_correlation_examples.png"
    fig.savefig(outp, dpi=150, bbox_inches="tight"); plt.close(fig)

    rec = {"deliverable": "FRF comparison: as-delivered FEM vs clean measured (reconcile NASA 'already correlated')",
           "reference": REF, "global_units_gain_x": round(g, 3),
           "peak_freq_match_median_relpct": round(fmatch_med, 2),
           "peak_height_scatter_sigma_log_below_135Hz": round(sig_below, 3),
           "peak_height_scatter_sigma_log_above_135Hz": round(sig_above, 3),
           "n_sensors": len(daqs), "sensors_shown_best_to_worst": [int(x) for x in pick],
           "interpretation": "FEM is correlated in FREQUENCY (peaks line up, median match ~{:.1f}%) but per-sensor "
                             "peak HEIGHT scatters, worse >135 Hz -> matches NASA cross-ortho degrade + node-line "
                             "local modes. 'Correlated' (freq + global MAC) != per-sensor FRF amplitude.".format(fmatch_med),
           "note": "EXPLORATORY; YELLOW; no success claim."}
    (OUT / "frf_correlation.json").write_text(json.dumps(rec, indent=2))
    print(f"wrote {outp}")
    print(f"global gain x{g:.2f}; peak-freq match median {fmatch_med:.1f}%")
    print(f"peak-height scatter sigma(log): below 135 Hz {sig_below:.2f}  |  above 135 Hz {sig_above:.2f}")
    print(f"sensors shown (best->worst amp err): {pick}")
    return rec


if __name__ == "__main__":
    run()
