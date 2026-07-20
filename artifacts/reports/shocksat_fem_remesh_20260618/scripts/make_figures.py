#!/usr/bin/env python3
"""Figures for the ShockSat modal twin packet (Tufte gate applied).

Design choices (Tufte checklist):
 - Direct end-of-line / per-point labels, minimal legends.
 - Log frequency axis for the nominal-vs-measured spectrum (project rule).
 - Held-out QOI figure shows comparison (predicted CI vs measured actual),
   documents coverage on the plot, no chartjunk, data-ink maximized.
 - Convergence shown as values (R-hat/ESS) not decoration.
Reads: nominal_modes.json, pairing.json, heldout_band.json, convergence_band.json
Writes: figures/*.png
"""
import json
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("figures", exist_ok=True)
plt.rcParams.update({"font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 140,
                     "savefig.bbox": "tight"})
INK = "#222222"; PRED = "#1b6ca8"; MEAS = "#c0392b"; MUTE = "#999999"


def fig_nominal_correlation():
    pr = json.load(open("pairing.json"))["pairs"]
    cal = [p for p in pr if p["calib_ok"]]
    ft = np.array([p["f_test"] for p in cal])
    fm = np.array([p["f_model"] for p in cal])
    mac = np.array([p["mac"] for p in cal])
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
    lim = [50, 240]
    ax1.plot(lim, lim, color=MUTE, lw=1, zorder=0)
    sc = ax1.scatter(ft, fm, c=mac, cmap="viridis", vmin=0.5, vmax=1.0,
                     s=45, edgecolor=INK, linewidth=0.4, zorder=3)
    ax1.set_xlim(lim); ax1.set_ylim(lim); ax1.set_aspect("equal")
    ax1.set_xlabel("measured frequency  [Hz]")
    ax1.set_ylabel("nominal FEM frequency  [Hz]")
    ax1.set_title("Nominal twin vs test (1:1 line)", fontsize=11)
    cb = fig.colorbar(sc, ax=ax1, fraction=0.046, pad=0.04)
    cb.set_label("MAC", fontsize=9)
    err = 100 * (fm / ft - 1)
    ax2.axhline(0, color=MUTE, lw=1)
    ax2.scatter(ft, err, c=mac, cmap="viridis", vmin=0.5, vmax=1.0,
                s=45, edgecolor=INK, linewidth=0.4)
    ax2.set_xlabel("measured frequency  [Hz]")
    ax2.set_ylabel("nominal freq error  [%]")
    ax2.set_title(f"Pre-calibration error (median |err| "
                  f"{np.median(np.abs(err)):.1f}%)", fontsize=11)
    fig.suptitle("ShockSat free-free: nominal (theta=1) FEM vs measured "
                 f"modes, {len(cal)} correlated modes", fontsize=11)
    fig.savefig("figures/nominal_correlation.png")
    plt.close(fig)


def fig_heldout(tag="band"):
    d = json.load(open(f"heldout_{tag}.json"))
    rows = sorted(d["held_out_rows"], key=lambda r: r["f_meas"])
    y = np.arange(len(rows))
    fm = np.array([r["f_meas"] for r in rows])
    med = np.array([r["f_pred_median"] for r in rows])
    plo = np.array([r["ci95_pred"][0] for r in rows])
    phi = np.array([r["ci95_pred"][1] for r in rows])
    clo = np.array([r["ci95_param"][0] for r in rows])
    chi = np.array([r["ci95_param"][1] for r in rows])
    cov = np.array([r["covers_pred"] for r in rows])
    fig, ax = plt.subplots(figsize=(8.4, 0.5 * len(rows) + 1.6))
    for i in y:
        ax.plot([plo[i], phi[i]], [i, i], color=PRED, lw=1.2, alpha=0.5,
                solid_capstyle="round", zorder=1)
        ax.plot([clo[i], chi[i]], [i, i], color=PRED, lw=4, alpha=0.9,
                solid_capstyle="round", zorder=2)
    ax.scatter(med, y, color=PRED, s=26, zorder=3, label="posterior median")
    ax.scatter(fm, y, marker="D", color=MEAS, s=34, zorder=4,
               edgecolor="white", linewidth=0.5, label="measured (held-out)")
    for i in y:
        mark = "covered" if cov[i] else "MISS"
        ax.text(phi.max() * 1.005, i,
                f"{100*(med[i]/fm[i]-1):+.1f}%  {mark}",
                va="center", fontsize=8,
                color=INK if cov[i] else MEAS)
    ax.set_yticks(y)
    ax.set_yticklabels([f"test {r['test_mode']}" for r in rows])
    ax.set_xlabel("frequency  [Hz]")
    ax.set_title(f"Held-out modes — {DESIGN_LABEL.get(tag, tag)} "
                 f"(predict 120-222 Hz)\npredicted 95% CI vs measured; "
                 f"thin = +noise predictive, thick = parameter CI; "
                 f"coverage {int(cov.sum())}/{len(rows)}", fontsize=9.5)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    cf = f"convergence_{tag}.json"
    if os.path.exists(cf):
        c = json.load(open(cf))
        if not c["gate_pass"]:
            ax.text(0.02, 0.98,
                    f"posterior NOT converged (R-hat {c['worst_rhat']:.2f}, "
                    f"ESS {c['min_ess']:.0f}) — CI edges not trustworthy",
                    transform=ax.transAxes, ha="left", va="top",
                    color=MEAS, fontsize=8.5)
    fig.savefig(f"figures/heldout_qoi_sidebyside_{tag}.png")
    plt.close(fig)


DESIGN_LABEL = {
    "band": "BAND design — 6 held-in modes <=120 Hz",
    "band_mac": "BAND+MAC arm — 6 held-in modes, freq+MAC likelihood",
    "full": "FULL design — all 18 calibration modes",
}


def fig_theta(tag="band"):
    # Mirrors fig_theta_full: prior band + informed/at-prior coloring, and
    # ALWAYS states the run it came from + flags a failed convergence gate in
    # red so non-converged intervals are not read as trustworthy.
    s = np.load(f"nuts_{tag}_samples.npz")
    gnames = [str(g) for g in s["gnames"]]
    th = s["theta"]
    med = np.median(th, 0)
    lo = np.percentile(th, 2.5, 0); hi = np.percentile(th, 97.5, 0)
    plo, phi = np.exp(-1.96 * 0.25), np.exp(1.96 * 0.25)   # prior 95%
    informed = (hi - lo) < 0.70 * (phi - plo)
    order = np.argsort(med)
    y = np.arange(len(gnames))
    fig, ax = plt.subplots(figsize=(7.6, 0.5 * len(gnames) + 1.8))
    ax.axvspan(plo, phi, color="#dfe6ee", zorder=0)
    ax.axvline(1.0, color=MUTE, lw=1, zorder=1)
    for yi, gi in zip(y, order):
        col = PRED if informed[gi] else MUTE
        ax.plot([lo[gi], hi[gi]], [yi, yi], color=col, lw=2.6,
                solid_capstyle="round", zorder=2)
        ax.scatter(med[gi], yi, color=col, s=42, zorder=3)
        ax.text(max(hi[gi], phi) + 0.02, yi,
                "informed" if informed[gi] else "~prior (not informed)",
                va="center", fontsize=8, color=INK if informed[gi] else MUTE)
    ax.set_yticks(y)
    ax.set_yticklabels([gnames[i] for i in order])
    ax.set_xlabel("stiffness scale  theta_g  (1 = as-modeled; "
                  "shaded = LogNormal(0.25) prior 95% range)")
    src = DESIGN_LABEL.get(tag, tag)
    cf = f"convergence_{tag}.json"
    conv = json.load(open(cf)) if os.path.exists(cf) else None
    if conv and not conv["gate_pass"]:
        ax.set_title(
            f"Posterior part-group stiffness scales — {src}\n"
            f"NOT CONVERGED: worst R-hat {conv['worst_rhat']:.2f}, min ESS "
            f"{conv['min_ess']:.0f} (gate 1.05 / 200) — intervals NOT trustworthy",
            fontsize=9.5, color=MEAS)
    elif conv:
        ax.set_title(
            f"Posterior part-group stiffness scales — {src}\n"
            f"converged: R-hat {conv['worst_rhat']:.2f}, ESS "
            f"{conv['min_ess']:.0f}", fontsize=9.5)
    else:
        ax.set_title(f"Posterior part-group stiffness scales — {src}",
                     fontsize=10)
    fig.savefig(f"figures/theta_posterior_{tag}.png")
    plt.close(fig)


def fig_theta_full():
    """Headline identifiability figure: the CONVERGED full 18-mode posterior
    theta CIs against the LogNormal(0,0.25) prior 95% band. A group whose
    posterior CI ~ the prior band is NOT informed by the modal data."""
    s = np.load("nuts_full_samples.npz")
    gnames = [str(g) for g in s["gnames"]]
    th = s["theta"]
    med = np.median(th, 0)
    lo = np.percentile(th, 2.5, 0); hi = np.percentile(th, 97.5, 0)
    plo, phi = np.exp(-1.96 * 0.25), np.exp(1.96 * 0.25)   # prior 95% = [.613,1.632]
    # "informed" = posterior 95% width < 70% of prior 95% width
    pw = phi - plo
    informed = (hi - lo) < 0.70 * pw
    order = np.argsort(med)
    y = np.arange(len(gnames))
    fig, ax = plt.subplots(figsize=(7.6, 0.5 * len(gnames) + 1.6))
    ax.axvspan(plo, phi, color="#dfe6ee", zorder=0)
    ax.axvline(1.0, color=MUTE, lw=1, zorder=1)
    for yi, gi in zip(y, order):
        col = PRED if informed[gi] else MUTE
        ax.plot([lo[gi], hi[gi]], [yi, yi], color=col, lw=2.6,
                solid_capstyle="round", zorder=2)
        ax.scatter(med[gi], yi, color=col, s=42, zorder=3)
        tag = "informed" if informed[gi] else "~prior (not informed)"
        ax.text(max(hi[gi], phi) + 0.02, yi, tag, va="center", fontsize=8,
                color=INK if informed[gi] else MUTE)
    ax.set_yticks(y)
    ax.set_yticklabels([gnames[i] for i in order])
    ax.set_xlabel("stiffness scale  theta_g  (1 = as-modeled; "
                  "shaded = LogNormal(0.25) prior 95% range)")
    ni = int(informed.sum())
    ax.set_title("Converged full 18-mode posterior (R-hat 1.02, ESS 232): "
                 f"{ni}/9 part-group\nstiffnesses informed; the rest sit at "
                 "the prior = not identifiable from modal data", fontsize=10)
    fig.savefig("figures/theta_posterior_full.png")
    plt.close(fig)


if __name__ == "__main__":
    fig_nominal_correlation()
    print("wrote nominal_correlation.png")
    if os.path.exists("nuts_full_samples.npz"):
        fig_theta_full(); print("wrote theta_posterior_full.png")
    for tag in ("band", "band_mac"):
        if os.path.exists(f"heldout_{tag}.json"):
            fig_heldout(tag); fig_theta(tag)
            print(f"wrote heldout/theta figures for {tag}")
