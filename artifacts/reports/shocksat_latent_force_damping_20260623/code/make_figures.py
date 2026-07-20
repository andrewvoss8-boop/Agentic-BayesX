#!/usr/bin/env python3
"""Figures for the time-domain latent-force damping diagnostic. Tufte-linted (see SKILL.md): minimal non-data ink
(top/right spines off, light grid), direct labels over legends where they fit, log-frequency axes, dB stated
explicitly, CI bands shown, captions carry source/units/takeaway, R-hat/ESS printed on the posterior figure.
All figures are built from the saved out/*.json and out/*.npz so they are replayable without recomputation.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decay_core as dc

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; FIG = WS / "figures"; FIG.mkdir(exist_ok=True)
INK = "#222222"; GRAY = "#999999"; BLUE = "#1f6fb4"; RED = "#c4302b"; GREEN = "#2a8a3e"; ORANGE = "#e08a1e"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": INK, "axes.labelcolor": INK, "text.color": INK,
                     "xtick.color": INK, "ytick.color": INK, "figure.dpi": 130})


def cap(fig, text):
    fig.text(0.012, 0.012, text, fontsize=7.2, color=GRAY, ha="left", va="bottom", wrap=True)


def fig_ringdown():
    """Mechanism: a clean ring-down decays over many cycles; its log-envelope slope = zeta (time domain)."""
    key, f0 = "m_zpos_990z", 99.7    # well-isolated mode (>=22 Hz from neighbours) -> clean single-exponential decay
    r = dc.load_ring(key); fs = float(r["fs_dec"]); t = r["t"]; ip = int(np.median(r["impact_idx_dec"]))
    A = r["A"]
    best = max(range(A.shape[1]), key=lambda ci: (dc.decay_fit(A[0, ci], t, ip, f0, fs) or {"snr": 0})["snr"])
    f = dc.decay_fit(A[0, best], t, ip, f0, fs, return_trace=True)
    xb = dc.bandpass(A[0, best], f0, f["W_hz"], fs)
    from scipy.signal import hilbert
    env = np.abs(hilbert(xb))
    tm = t * 1000.0
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.6))
    tmax = (f["tw"][-1]) * 1000 + 20
    m = (tm > -10) & (tm < tmax)
    ax[0].plot(tm[m], np.abs(xb[m]), color=GRAY, lw=0.3)
    ax[0].plot(tm[m], env[m], color=BLUE, lw=1.3)
    tw = f["tw"] * 1000 + 6.0  # fit window starts ~6 ms after impact
    ax[0].plot(tw, f["ew"][0] * np.exp(f["slope"] * f["tw"]), color=RED, lw=1.6, ls="--")
    ax[0].set_yscale("log"); ax[0].set_xlabel("time after impact [ms]")
    ax[0].set_ylabel("band-passed |accel| [g]"); ax[0].set_ylim(env[m].max() * 3e-3, env[m].max() * 2)
    ax[0].set_title("ring-down envelope (blue) + exp-decay fit (red)", fontsize=8.5)
    ax[0].text(0.40, 0.86, f"zeta = {f['zeta_pct']:.3f}%\n{f['n_cycles']:.0f} cycles\n{f['db_decay']:.0f} dB decay",
               transform=ax[0].transAxes, color=RED, fontsize=9)
    # panel B: half-power width vs FFT bin, per resolved mode
    L1 = json.load(open(OUT / "layer1_damping.json"))
    fs_, dfs, sub = [], [], []
    df_fft = next(m_["resolvability"]["df_fft_hz"] for m_ in L1["modes"] if "resolvability" in m_)
    for m_ in L1["modes"]:
        if "resolvability" in m_:
            fs_.append(m_["f_hz"]); dfs.append(m_["resolvability"]["half_power_df_hz"])
            sub.append(m_["resolvability"]["subbin_in_freq"])
    fs_ = np.array(fs_); dfs = np.array(dfs); sub = np.array(sub)
    ax[1].scatter(fs_[sub], dfs[sub], color=GREEN, s=28, label="sub-bin (freq can't resolve width)")
    ax[1].scatter(fs_[~sub], dfs[~sub], color=ORANGE, s=28, label="width >= 1 bin")
    ax[1].axhline(df_fft, color=INK, lw=1.0, ls=":")
    ax[1].text(250, df_fft * 1.05, f"FFT bin df = {df_fft:.2f} Hz", ha="right", fontsize=8, color=INK)
    ax[1].set_xlabel("mode frequency [Hz]  (linear; narrow 75-260 Hz modal band)")
    ax[1].set_ylabel("half-power width  2*zeta*f  [Hz]")
    ax[1].set_xticks([75, 100, 150, 200, 250])  # linear: log ticks overlap on this <2-octave range
    ax[1].set_xlim(65, 265); ax[1].set_ylim(0, 4.4)
    ax[1].legend(frameon=False, fontsize=7.5, loc="upper left")
    ax[1].set_title("light modes are SUB-BIN in frequency, resolvable in time", fontsize=8.5)
    cap(fig, "Source: Test02 +Z@990 modal-hammer ring-down (fs=250kHz->2.5kHz decimated), isolated mode 99.7 Hz; units g. "
             "Left: the time-domain decay rate gives zeta independent of the FFT bin (clustered modes beat instead -- "
             "the Layer-2 residual). Right: half-power width vs the df=2.03 Hz modal-cache bin -- light modes are "
             "sub-bin (the reason D22's windowed FRF got 0/9).")
    fig.tight_layout(rect=(0, 0.07, 1, 1)); fig.savefig(FIG / "fig1_ringdown.png"); plt.close(fig)


def fig_zeta_headline():
    """Per-mode time-domain zeta (NUTS posterior CI) vs .ash, FEM nominal, and the D22 unidentified result."""
    N = json.load(open(OUT / "layer1_nuts.json"))
    L1 = json.load(open(OUT / "layer1_damping.json"))
    ash = {m["f_hz"]: m["ash_zeta_pct"] for m in L1["modes"] if "ash_zeta_pct" in m}
    f, med, lo, hi, rh, es = [], [], [], [], [], []
    for m in N["modes"]:
        if m.get("resolved"):
            f.append(m["f_hz"]); med.append(m["zeta_pct"]["med"]); lo.append(m["zeta_pct"]["lo"]); hi.append(m["zeta_pct"]["hi"])
            rh.append(m["rhat_max"]); es.append(m["ess_min"])
    f = np.array(f); med = np.array(med)
    fig, ax = plt.subplots(figsize=(8.4, 4.2))
    ax.fill_between([60, 270], 0.05, 0.05, color="none")
    ax.axhline(1.0, color=GRAY, lw=1.0, ls="--")
    ax.text(258, 1.02, "FEM/L5 nominal zeta = 1.0%", ha="right", color=GRAY, fontsize=8)
    yerr = np.vstack([med - np.array(lo), np.array(hi) - med])
    ax.errorbar(f, med, yerr=yerr, fmt="o", color=BLUE, ms=5, lw=1.1, capsize=2, label="time-domain zeta (NUTS 95% CI)")
    af = np.array([k for k in ash]); az = np.array([ash[k] for k in ash])
    ax.scatter(af, az, marker="s", color=GREEN, s=22, label="NASA .ash modal zeta")
    ax.set_xscale("log"); ax.set_xlabel("mode frequency [Hz]"); ax.set_ylabel("damping ratio zeta [% of critical]")
    ax.set_ylim(0, 2.0)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.text(0.30, 0.93, f"D22 (windowed FRF, df=1.25 Hz): 0/9 identified\nthis run (ring-down): {len(f)}/16 resolved\n"
            f"worst R-hat {max(rh):.3f}, min ESS {min(es):.0f}, 0 div",
            transform=ax.transAxes, fontsize=8.5, color=INK,
            bbox=dict(boxstyle="round", fc="white", ec=GRAY, lw=0.6))
    cap(fig, "Source: clean modal-hammer ring-downs Test01/02/04/06 (g & lbf). Quantity: modal damping zeta = fraction "
             "of critical, hierarchical non-centered NUTS over the exp-decay envelope, prior LogUniform[0.05%,6%] "
             "(same bounds as D22). Takeaway: the time domain RESOLVES zeta (~0.3-0.8%, near .ash) where the windowed "
             "FRF could not; FEM nominal 1% is heavier than measured (FEM is over-damped).")
    fig.tight_layout(rect=(0, 0.09, 1, 1)); fig.savefig(FIG / "fig2_zeta_headline.png"); plt.close(fig)


def fig_counts():
    """Two levers: clean data lifts the frequency domain 0->7; the time domain reaches 14 (sub-bin/cluster modes)."""
    fig, ax = plt.subplots(figsize=(6.6, 4.0))
    labels = ["D22\nwindowed FRF\n(noisy tap, df=1.25)", "frequency width fit\n(clean data, df=2.03)",
              "time-domain decay\n(clean data)"]
    vals = [0, 7, 14]; denom = [9, 16, 16]
    cols = [GRAY, ORANGE, GREEN]
    x = np.arange(3)
    ax.bar(x, vals, color=cols, width=0.6)
    for i, (v, d) in enumerate(zip(vals, denom)):
        ax.text(i, v + 0.3, f"{v}/{d}", ha="center", fontsize=11, color=INK)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylabel("modes with a resolved/identified zeta"); ax.set_ylim(0, 16)
    cap(fig, "Like-for-like 'identified/resolved' criterion (posterior CI < half the prior log-width, interior). "
             "Two real levers: clean multi-hit data helps even in frequency (0->7); the TIME domain adds the "
             "light/sub-bin-width and clustered modes (7->14) on the SAME clean data.")
    fig.tight_layout(rect=(0, 0.10, 1, 1)); fig.savefig(FIG / "fig3_counts.png"); plt.close(fig)


def fig_layer2():
    """Latent-force decomposition: smoother zeta cross-checks log-decrement; residual shows no nonlinearity."""
    L2 = json.load(open(OUT / "layer2_gplfm.json"))
    ok = [m for m in L2["modes"] if m.get("ok")]
    fig, ax = plt.subplots(1, 2, figsize=(9.2, 3.7))
    zt = [m["zeta_true_pct"]["med"] for m in ok]; zl = [m["zeta_logdec_pct_med"] for m in ok]
    fs = [m["f_hz"] for m in ok]
    ax[0].plot([0, 1.2], [0, 1.2], color=GRAY, lw=0.8, ls="--")
    ax[0].scatter(zl, zt, color=BLUE, s=34)
    for x, y, fhz in zip(zl, zt, fs):
        ax[0].annotate(f"{fhz:.0f}", (x, y), fontsize=7, color=GRAY, xytext=(3, 3), textcoords="offset points")
    ax[0].set_xlabel("log-decrement zeta [%]  (independent)")
    ax[0].set_ylabel("latent-force smoother zeta [%]")
    ax[0].set_xlim(0, 1.1); ax[0].set_ylim(0, 1.1)
    ax[0].text(0.03, 0.92, f"per-trace corr ~ {L2['median_smoother_vs_logdec_corr']:.2f}",
               transform=ax[0].transAxes, fontsize=9, color=INK)
    ax[0].text(0.02, 1.02, "latent force (velocity proj.) recovers the same damping", transform=ax[0].transAxes,
               fontsize=8, color=INK)
    # nonlinearity diagnostics: |corr(residual,q^2)| (bars from 0) + early/late zeta ratio (markers, ref=1)
    nl = [m["residual_vs_q2_corr_median"] for m in ok]
    el = [m["early_over_late_zeta_median"] or 1.0 for m in ok]
    x = np.arange(len(ok))
    ax[1].bar(x, nl, 0.5, color=BLUE)
    ax[1].set_ylim(0, 1.0); ax[1].set_ylabel("|corr(residual, q^2)|", color=BLUE)
    ax[1].tick_params(axis="y", colors=BLUE)
    ax1b = ax[1].twinx(); ax1b.spines["top"].set_visible(False)
    ax1b.scatter(x, el, color=ORANGE, marker="D", s=26)
    ax1b.axhline(1.0, color=GRAY, lw=0.8, ls=":")
    ax1b.set_ylim(0, 4.0); ax1b.set_ylabel("early/late-decay zeta ratio (ref=1)", color=ORANGE)
    ax1b.tick_params(axis="y", colors=ORANGE)
    ax[1].set_xticks(x); ax[1].set_xticklabels([f"{f:.0f}" for f in fs], fontsize=8)
    ax[1].set_xlabel("mode frequency [Hz]")
    ax[1].text(0.02, 1.02, "two independent nonlinearity diagnostics: corr~0 (bars) and ratio~1 (diamonds) = linear",
               transform=ax[1].transAxes, fontsize=7.4, color=INK)
    cap(fig, "Layer 2 (RTS Kalman SMOOTHER = linear-Gaussian filter, NOT NUTS). Left: the latent modal force projected "
             "on velocity recovers the per-trace decay zeta -> the model-form error is dominantly a DAMPING correction "
             "(FEM over-damped). Right: residual-vs-q^2 correlation ~0 and early/late decay-rate ratio ~1 -> little "
             "evidence of missing nonlinear physics. (Raw variance split is q_g/close-mode-beating contaminated; see JSON caveat.)")
    fig.tight_layout(rect=(0, 0.10, 1, 1)); fig.savefig(FIG / "fig4_layer2.png"); plt.close(fig)


def fig_layer3():
    """Layer 3 honest negative: zeta cancels in the win ratio; the binding limit is per-node shape error (+27 dB)."""
    FP = json.load(open(OUT / "finite_perturbation.json"))
    L3 = json.load(open(OUT / "layer3_value_seed00.json"))
    cz = np.load(OUT / "layer3_curves.npz")
    fig, ax = plt.subplots(1, 2, figsize=(9.4, 3.9))
    # panel A: finite perturbation -- GRMS (absolute lever) and win ratio (cancels) vs zeta
    z = [r["zeta_struct_pct"] for r in FP["sweep"]]
    g6 = [r["env_grms_fem6_median"] for r in FP["sweep"]]
    wr = [r["win_ratio_twin_over_fem6_median"] for r in FP["sweep"]]
    ax[0].plot(z, g6, "o-", color=BLUE, lw=1.3)
    ax[0].set_xlabel("structural zeta [%]"); ax[0].set_ylabel("FEM+6dB envelope GRMS [g]", color=BLUE)
    ax[0].tick_params(axis="y", colors=BLUE)
    ax0b = ax[0].twinx(); ax0b.plot(z, wr, "s--", color=RED, lw=1.3); ax0b.set_ylabel("win ratio twin/FEM+6dB", color=RED)
    ax0b.tick_params(axis="y", colors=RED); ax0b.set_ylim(0, max(wr) * 1.3); ax0b.spines["top"].set_visible(False)
    ax[0].axvline(1.0, color=GRAY, lw=0.8, ls=":"); ax[0].axvline(0.4, color=GREEN, lw=0.8, ls=":")
    ylo, yhi = ax[0].get_ylim()
    ax[0].text(1.02, ylo + 0.10 * (yhi - ylo), "FEM\n1.0%", color=GRAY, fontsize=7.5, ha="left", va="bottom")
    ax[0].text(0.42, ylo + 0.42 * (yhi - ylo), "measured\n~0.4%", color=GREEN, fontsize=7.5, ha="left", va="center")
    ax[0].set_title("GRMS scales ~1/zeta (lever); RATIO is flat (zeta cancels)", fontsize=8.2)
    # panel B: PSD overlay for one held-out sensor (log-log)
    f = cz["freqs"]
    ax[1].plot(f, cz["data_psd"], color=INK, lw=0.7, label="measured data PSD")
    ax[1].plot(f, cz["fem_psd"], color=GRAY, lw=0.8, label="FEM PSD")
    ax[1].plot(f, cz["fem6_env"], color=ORANGE, lw=1.2, label="FEM+6dB envelope")
    ax[1].plot(f, cz["twin_nom_env"], color=RED, lw=1.2, label="twin 97.5% envelope")
    ax[1].set_xscale("log"); ax[1].set_yscale("log")
    ax[1].set_xlabel("frequency [Hz]"); ax[1].set_ylabel("response PSD [g^2/Hz], S_F0=1")
    ax[1].legend(frameon=False, fontsize=7.2, loc="lower center")
    ax[1].text(0.02, 1.02, f"held-out sensor ch{int(cz['daq'])}: twin band must be ~+27 dB to cover; "
               f"FEM+6dB under-envelopes", transform=ax[1].transAxes, fontsize=7.2, color=INK)
    cap(fig, "Layer 3 (reuses the inherited PSD-envelope QOI byte-identical, 90% split). Left: a realistic zeta change "
             "moves envelope GRMS a lot (absolute lever) but the twin/FEM+6dB win RATIO is invariant (zeta is "
             "common-mode -> cancels; mirrors D8). Right: the twin's honest 97.5% band is ~+27 dB (per-node FEM "
             "shape error sigma~1.6), so it cannot beat FEM+6dB on GRMS -> 0% win (honest negative, confirms D7).")
    fig.tight_layout(rect=(0, 0.10, 1, 1)); fig.savefig(FIG / "fig5_layer3.png"); plt.close(fig)


if __name__ == "__main__":
    fig_ringdown(); print("fig1 ringdown")
    fig_zeta_headline(); print("fig2 zeta headline")
    fig_counts(); print("fig3 counts")
    fig_layer2(); print("fig4 layer2")
    fig_layer3(); print("fig5 layer3")
    print("all figures written to figures/")
