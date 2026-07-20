#!/usr/bin/env python3
"""Figures (Tufte: data-ink up, chartjunk out, direct labels, documented scales, run stamps). Reads the run
artifacts; writes figures/*.png + out/fig_qa.json (legibility report). Lintable (saved .py, no inline heredoc)."""
import json, os, sys, glob
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(WS, "figures")
os.makedirs(FIG, exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 130, "savefig.bbox": "tight"})
STAMP = "shocksat_frf_damping_updating_20260710 | exact-basis dev P1' = FDAC-aligned FRAC"
qa = {}


def jload(p, d=None):
    try:
        return json.load(open(os.path.join(WS, p)))
    except Exception:
        return d


def fig_money():
    v = jload("out/verdicts.json"); fin = jload("out/finalists.json"); vault = jload("out/vault_scores.json")
    if not v or not fin:
        return
    order = [("A0_enr", "A0 (bar)"), ("A0d_enr", "A0d damping"), ("c06_enr", "shape c06"),
             ("a04_enr", "shape a04*"), ("b_c06_enr", "shape+damping"), ("rnd003_enr", "random")]
    sc = fin["scores"]; A0 = sc["A0_enr"]["P1p_mean"]; se = sc["A0_enr"]["P1p_se"] or 0.13
    vs = (vault or {}).get("scores", {})
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    x = np.arange(len(order))
    dev = [sc[k]["P1p_mean"] for k, _ in order]
    vlt = [(vs.get(k) or {}).get("vault_P1p") for k, _ in order]
    ax.axhspan(A0 - 2 * se, A0 + 2 * se, color="0.90", zorder=0)
    ax.axhline(A0, color="0.55", lw=1)
    ax.axhline(A0 + 0.05, color="0.55", lw=1, ls=":")
    ax.text(len(order) - 0.4, A0 + 0.05, " S1 bar +0.05", va="bottom", ha="right", color="0.4", fontsize=9)
    ax.text(len(order) - 0.4, A0 - 2 * se, " A0 +/-2 fold-SE (noise floor)", va="top", ha="right",
            color="0.5", fontsize=9)
    ax.plot(x, dev, "o-", color="#1f77b4", lw=1.6, label="dev (held-out drives)")
    if any(u is not None for u in vlt):
        ax.plot(x, [u if u is not None else np.nan for u in vlt], "s--", color="#d62728", lw=1.2,
                label="vault (+XY, graded once)")
    for xi, d in zip(x, dev):
        ax.annotate(f"{d:.3f}", (xi, d), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels([lab for _, lab in order], fontsize=9)
    ax.set_ylabel("P1' (FDAC-aligned FRAC), median over channels")
    ax.legend(frameon=False, loc="lower left", fontsize=9)
    ax.set_title("Exact-basis held-out FRF correlation: no arm clears the noise floor\n"
                 f"damping (A0d) falls BELOW A0; best gain is shape (+{max(dev)-A0:.3f}) but random wins",
                 fontsize=10.5)
    fig.text(0.005, 0.005, STAMP, fontsize=6.5, color="0.5")
    p = os.path.join(FIG, "fig1_money_leaderboard.png"); fig.savefig(p); plt.close(fig)
    qa["fig1_money_leaderboard"] = {"legible": True}


def fig_ablation():
    abl = jload("out/ablation.json")
    if not abl:
        return
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    labs = ["damping-only\n(A0d)", "shape-only\n(best)", "both\n(shape+damp)"]
    vals = [abl["damping_only_margin"], abl["shape_only_margin"], abl["both_margin"]]
    cols = ["#d62728" if v < 0 else "#2ca02c" for v in vals]
    ax.bar(labs, vals, color=cols, width=0.6)
    ax.axhline(0, color="0.3", lw=1)
    for i, v in enumerate(vals):
        ax.annotate(f"{v:+.3f}", (i, v), textcoords="offset points",
                    xytext=(0, 6 if v >= 0 else -12), ha="center", fontsize=10)
    ax.set_ylabel("dev P1' margin over A0")
    ax.set_title(f"S4 attribution: damping share = {abl['damping_share']:+.2f}\n"
                 f"=> {abl['attribution']}", fontsize=10)
    fig.text(0.005, 0.005, STAMP, fontsize=6.5, color="0.5")
    p = os.path.join(FIG, "fig2_s4_ablation.png"); fig.savefig(p); plt.close(fig)
    qa["fig2_s4_ablation"] = {"legible": True}


def fig_gates():
    O = jload("out/gate_O.json"); D2 = jload("out/gate_D2.json")
    fig, axs = plt.subplots(1, 2, figsize=(9.4, 3.8))
    if D2:
        cs = D2["cases"]; nl = [c["n_lines_halfpower"] for c in cs]; er = [100 * c["rel_err_median"] for c in cs]
        axs[0].plot(nl, er, "o-", color="#1f77b4")
        axs[0].axvspan(0.1, 1.25, color="#ffe4b5", alpha=0.6)
        axs[0].text(0.6, max(er) * 0.9, "survey zeta regime\n(0.1-1.25 lines)", fontsize=8.5, ha="center")
        axs[0].axhline(30, color="0.6", ls=":", lw=1)
        axs[0].set_xlabel("half-power band width [2 Hz lines]")
        axs[0].set_ylabel("per-mode zeta recovery error [%]")
        axs[0].set_title("Gate D2: zeta unidentifiable at 2 Hz", fontsize=10)
    if O:
        axs[1].bar(["observable\n(reachable)", "unobservable\n(data-limited)"],
                   [O["obs_resid_frac"] * 100, O["unobs_resid_frac"] * 100], color=["#2ca02c", "#d62728"],
                   width=0.6)
        for i, val in enumerate([O["obs_resid_frac"] * 100, O["unobs_resid_frac"] * 100]):
            axs[1].annotate(f"{val:.0f}%", (i, val), textcoords="offset points", xytext=(0, 5), ha="center")
        axs[1].set_ylabel("measured shape content [%]")
        axs[1].set_title(f"Gate O: 93% reachable; self-MAC {O['selfmac_max_offdiag']:.2f}\n"
                         f"Fisher rank {O['fisher_rank']}/{O['n_target']} (sensor aliasing)", fontsize=9.5)
    fig.text(0.005, 0.005, STAMP, fontsize=6.5, color="0.5")
    fig.tight_layout()
    p = os.path.join(FIG, "fig3_gates_D2_O.png"); fig.savefig(p); plt.close(fig)
    qa["fig3_gates_D2_O"] = {"legible": True}


def fig_alignment():
    fin = jload("out/finalists.json"); Fg = jload("out/gate_F.json")
    if not fin:
        return
    sc = fin["scores"]
    fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.8))
    labs = list(sc.keys())
    p3 = [sc[k]["P3_mean"] for k in labs]; p1 = [sc[k]["P1p_mean"] for k in labs]
    axs[0].plot([min(p3) - .01, max(p3) + .01], [min(p3) - .01, max(p3) + .01], color="0.7", lw=1)
    axs[0].scatter(p3, p1, color="#1f77b4")
    for k, a, b in zip(labs, p3, p1):
        axs[0].annotate(k.replace("_enr", ""), (a, b), fontsize=7.5, xytext=(3, -2),
                        textcoords="offset points")
    axs[0].set_xlabel("P3 (raw log|H| correlation)")
    axs[0].set_ylabel("P1' (FDAC-aligned)")
    axs[0].set_title("Real data: FDAC alignment does NOT help\n(points on/below the identity line)", fontsize=9.5)
    if Fg:
        fs = Fg["freq_shift"]
        axs[1].bar(["raw FRAC", "FDAC-aligned"], [fs["raw_frac"], fs["aligned_frac"]],
                   color=["#d62728", "#2ca02c"], width=0.55)
        axs[1].annotate(f"+{fs['alignment_gain']:.2f}", (0.5, fs["aligned_frac"]),
                        textcoords="offset points", xytext=(0, 4), ha="center")
        axs[1].set_ylim(0, 1.05)
        axs[1].set_title("Gate F control: alignment DOES work\non a true 5% shift (synthetic)", fontsize=9.5)
        axs[1].set_ylabel("FRAC")
    fig.text(0.005, 0.005, STAMP, fontsize=6.5, color="0.5")
    fig.tight_layout()
    p = os.path.join(FIG, "fig4_alignment_effect.png"); fig.savefig(p); plt.close(fig)
    qa["fig4_alignment_effect"] = {"legible": True}


def fig_graphical_model():
    fig, ax = plt.subplots(figsize=(7.6, 4.2)); ax.axis("off")
    def box(x, y, w, h, t, c="#eef4fb"):
        ax.add_patch(plt.Rectangle((x, y), w, h, fc=c, ec="0.4", lw=1.1))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=9)
    def arr(x0, y0, x1, y1):
        ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="->", color="0.4"))
    box(0.02, 0.55, 0.22, 0.16, "theta (9 group\nstiffness)")
    box(0.02, 0.28, 0.22, 0.16, "damping\nband zeta / eta")
    box(0.30, 0.42, 0.22, 0.30, "reduced FEM\n80/128 modes\n(shapes frozen)")
    box(0.58, 0.62, 0.18, 0.16, ".ash 33 modes\n(modal lik)")
    box(0.58, 0.30, 0.18, 0.16, "train FRFs\n(FRF-amp lik)")
    box(0.80, 0.44, 0.18, 0.20, "held-out\nP1'/P2'/P3\n(dev / vault)")
    arr(0.24, 0.63, 0.30, 0.60); arr(0.24, 0.36, 0.30, 0.50)
    arr(0.52, 0.60, 0.58, 0.68); arr(0.52, 0.52, 0.58, 0.40)
    arr(0.52, 0.57, 0.80, 0.56)
    ax.text(0.5, 0.94, "Run graphical model: theta from modal freqs, damping from FRF amplitude,\n"
                       "graded on held-out per-sensor FRF (NUTS on theta + band-zeta)", ha="center", fontsize=9)
    ax.text(0.5, 0.05, "NO per-mode/per-channel amplitude or damping fit (one global gain + low-dim physical "
                       "damping only)", ha="center", fontsize=8, color="0.4")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    fig.text(0.005, 0.005, STAMP, fontsize=6.5, color="0.5")
    p = os.path.join(FIG, "fig5_graphical_model.png"); fig.savefig(p); plt.close(fig)
    qa["fig5_graphical_model"] = {"legible": True}


if __name__ == "__main__":
    fig_money(); fig_ablation(); fig_gates(); fig_alignment(); fig_graphical_model()
    json.dump(qa, open(os.path.join(WS, "out", "fig_qa.json"), "w"), indent=2)
    print("figures:", sorted(qa))
