#!/usr/bin/env python3
"""Figures for the plate-test rehearsal (Tufte: direct labels, data-ink, log-f axes, sources on
figure, synthetic-data + convergence status stated on every numeric figure)."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WS / "code"))
from rehearsal import Setup, simulate_data, ARMS, NOISE_FRAC   # noqa: E402
import netcg_qoi as NC                                          # noqa: E402

FIG = WS / "figures"; FIG.mkdir(exist_ok=True)
GREY, BLUE, RED, GREEN, ORANGE = "#5a5a5a", "#3a66b0", "#b2182b", "#1b7837", "#b55e0c"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

runs = [json.loads(p.read_text()) for p in sorted((WS / "out" / "runs").glob("*.json"))]
summary = json.loads((WS / "out" / "summary.json").read_text())
arms = summary["arms"]; ref = summary["analytic_reference"]
worst_rhat = max(r["nuts"]["max_rhat"] for r in runs)
min_ess = min(r["nuts"]["min_ess"] for r in runs)
conv_note = f"NUTS 4 chains x64; worst R-hat {worst_rhat:.3f}, min ESS {min_ess:.0f} across {len(runs)} runs"
SRC = "src: plate_test_rehearsal_20260701/out/runs/*.json (SYNTHETIC truth; seeds per arm) · analytic ref: netcg pretest_design.json"


def by_arm(key, arm):
    return [r[key] for r in runs if r["arm"] == arm and r["nuts"]["converged"]]


# ---------------- fig 1: the money figure — analytic curve vs REHEARSED band factors ----------
fig, ax = plt.subplots(figsize=(7.6, 4.6))
fz = np.load(WS.parent / "shocksat_netcg_method_selection_20260701" / "out" / "pretest_figdata.npz")
ax.plot(fz["ns"], fz["band"], "-o", color=GREY, ms=3, lw=1,
        label=None)
ax.text(fz["ns"][-1] - 3.4, fz["band"][-1] + 0.25, "analytic design curve\n(no inference)", color=GREY, fontsize=8)
ax.axhline(float(fz["floor"]), color=GREEN, lw=0.8, ls=":")
ax.text(0.2, float(fz["floor"]) - 0.28, f"fully-resolved floor {float(fz['floor']):.1f}x", color=GREEN, fontsize=8)
pos = {"A0_1sensor": 1, "A1_12sensor": 12, "A2_20sensor": 20, "A3_12jitter": 12.6}
cols = {"A0_1sensor": GREY, "A1_12sensor": BLUE, "A2_20sensor": BLUE, "A3_12jitter": ORANGE}
labs = {"A0_1sensor": "1 sensor (current)", "A1_12sensor": "12 sensors", "A2_20sensor": "20 sensors",
        "A3_12jitter": "12 + 1.5-in jitter"}
for a, x in pos.items():
    bf = by_arm("band_factor", a)
    if not bf:
        continue
    ax.scatter([x] * len(bf), bf, s=14, color=cols[a], alpha=0.55, zorder=3)
    med = float(np.median(bf))
    ax.scatter([x], [med], s=90, color=cols[a], marker="_", lw=2.5, zorder=4)
    ax.annotate(f"{labs[a]}\nmedian {med:.1f}x", (x, med), xytext=(x + 0.5, med + 0.45),
                fontsize=8, color=cols[a])
ax.axhline(3.5, color=RED, lw=0.8, ls="--")
ax.text(15.5, 3.55, "pre-registered S1 target 3.5x", color=RED, fontsize=8)
ax.set_xlabel("number of plate Z-accelerometers"); ax.set_ylabel("normal-Z 95% band factor (x)")
ax.set_title("REHEARSED buy-down (full NUTS pipeline, synthetic truth) vs the analytic design curve",
             fontsize=10)
fig.text(0.01, 0.015, f"{SRC} · {conv_note} · dots = converged seeds, dash = median · band factor = "
         "97.5/2.5 pct of 1-oct-smoothed GRMS", fontsize=6.5, color=GREY)
fig.tight_layout(rect=(0, 0.05, 1, 1)); fig.savefig(FIG / "fig_buydown_rehearsed.png", dpi=160)
plt.close(fig)

# ---------------- fig 2: delivered band vs truth, small multiples (seed 0 per arm) -------------
show = ["A0_1sensor", "A1_12sensor", "A3_12jitter"]
fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
for ax, a in zip(axes, show):
    rs = [r for r in runs if r["arm"] == a and r["seed"] == 0]
    if not rs:
        continue
    r = rs[0]
    lo, hi, tr = np.array(r["lo"]), np.array(r["hi"]), np.array(r["truth_spec"])
    ls, hs = NC.octave_smooth(NC.FGRID, lo), NC.octave_smooth(NC.FGRID, hi)
    ts = NC.octave_smooth(NC.FGRID, tr)
    ax.fill_between(NC.FGRID, ls, hs, color=BLUE, alpha=0.25, lw=0)
    ax.plot(NC.FGRID, ts, color=RED, lw=1.2)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_title(f"{labs[a]} — band {r['band_factor']:.1f}x, cov {r['coverage']['weighted_coverage']:.2f}",
                 fontsize=9)
    ax.set_xlabel("frequency [Hz, log]")
    ax.axvspan(228, 260, color=ORANGE, alpha=0.08)
    if a == show[0]:
        ax.set_ylabel("net-CG normal-Z force (1-oct smoothed, arb.)")
        ax.text(230, ts.max() * 1.6, "drumhead\nband", fontsize=7, color=ORANGE)
    ax.text(50, ts.min() * 1.2, "truth", color=RED, fontsize=8)
fig.suptitle("Delivered 95% band (blue) vs the SYNTHETIC truth spectrum (red) — seed 0", fontsize=10)
fig.text(0.01, 0.01, f"{SRC} · {conv_note} · 1-octave smoothed, 45-260 Hz, log-log", fontsize=6.5, color=GREY)
fig.tight_layout(rect=(0, 0.05, 1, 0.93)); fig.savefig(FIG / "fig_bands_vs_truth.png", dpi=160)
plt.close(fig)

# ---------------- fig 3: amplitude recovery per target mode --------------------------------
fig, ax = plt.subplots(figsize=(7.2, 4.2))
tgt_hz = summary["target_modes_hz"]
x0 = 0
for a, col in [("A0_1sensor", GREY), ("A1_12sensor", BLUE)]:
    rs = [r for r in runs if r["arm"] == a and r["nuts"]["converged"]]
    for ti in range(len(tgt_hz)):
        xt = x0 + ti
        et = [r["eta_true"][ti] for r in rs]
        em = [r["eta_post_mean"][ti] for r in rs]
        es = [r["eta_post_sd"][ti] for r in rs]
        ax.errorbar([xt + 0.12] * len(em), em, yerr=es, fmt="o", ms=3, color=col,
                    alpha=0.6, lw=0.8, capsize=0)
        ax.scatter([xt - 0.12] * len(et), et, s=16, color=RED, marker="x")
    x0 += len(tgt_hz) + 1
ax.axhline(0, color=GREY, lw=0.6)
ax.set_xticks(list(range(len(tgt_hz))) + [len(tgt_hz) + 1 + i for i in range(len(tgt_hz))])
ax.set_xticklabels([f"{h:.0f}" for h in tgt_hz] * 2, fontsize=8)
ax.text(1.5, ax.get_ylim()[1] * 0.9, "1 sensor (current)", color=GREY, fontsize=9, ha="center")
ax.text(len(tgt_hz) + 2.5, ax.get_ylim()[1] * 0.9, "12 sensors", color=BLUE, fontsize=9, ha="center")
ax.set_xlabel("target drumhead mode [Hz]"); ax.set_ylabel("net-amplitude log-ratio  ln|g_true / g_model|")
ax.set_title("Amplitude recovery: truth (red x) vs posterior mean +/- sd (dots), converged seeds", fontsize=10)
fig.text(0.01, 0.01, f"{SRC} · {conv_note} · prior sd 0.80 (tier-2); posterior sd is the S6 metric",
         fontsize=6.5, color=GREY)
fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(FIG / "fig_amp_recovery.png", dpi=160)
plt.close(fig)

# ---------------- fig 4: clean truth vs observed sensor data (gate: show the data) ----------
S = Setup()
d = simulate_data(S, "A1_12sensor", 0, 0.8)
fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.0))
t0 = int(S.tgt[0])
ph = None
import rehearsal as RH
_, _, phi_true, _, _ = RH.make_truth(S, 0, 0.8)
ph = phi_true[t0]
sc = axes[0].scatter(S.coords[:, 0], S.coords[:, 1], c=ph, s=6, cmap="RdBu_r")
axes[0].scatter(S.coords[d["nodes_used"], 0], S.coords[d["nodes_used"], 1], s=70,
                facecolor="none", edgecolor="k", lw=1.2)
axes[0].set_title(f"TRUE (synthetic) {summary['target_modes_hz'][0]:.0f} Hz drumhead shape + 12 sensors (circles)",
                  fontsize=9)
axes[0].set_xlabel("x [in]"); axes[0].set_ylabel("y [in]"); axes[0].set_aspect("equal")
fig.colorbar(sc, ax=axes[0], shrink=0.8, label="modal Z [arb.]")
ii = np.argsort(np.asarray(d["nodes_used"]))
clean = ph[np.asarray(d["nodes_used"])[ii]]
obs = d["Y"][ii, 0]
axes[1].plot(clean, "o-", color=RED, ms=4, lw=0.8)
axes[1].plot(obs, "s", color=BLUE, ms=4)
axes[1].text(0.4, max(clean.max(), obs.max()) * 0.9, "clean truth (red), observed +10% RMS noise (blue)",
             fontsize=8)
axes[1].set_xlabel("sensor # (sorted by node index)"); axes[1].set_ylabel("modal Z sample [arb.]")
axes[1].set_title("Clean truth vs observed sensor samples (seed 0, mode 1)", fontsize=9)
fig.text(0.01, 0.01, f"{SRC} · SYNTHETIC data, seed 0 · noise sigma = {NOISE_FRAC:.0%} of per-mode plate-field RMS (A7)",
         fontsize=6.5, color=GREY)
fig.tight_layout(rect=(0, 0.04, 1, 1)); fig.savefig(FIG / "fig_sensor_data.png", dpi=160)
plt.close(fig)

# ---------------- fig 5: run-specific graphical model (schematic) ---------------------------
fig, ax = plt.subplots(figsize=(8.4, 4.4)); ax.axis("off")
boxes = [
    (0.06, 0.72, "theta (9)\nlog-stiffness\nN(0, 0.25)", BLUE),
    (0.06, 0.30, "c (4 x 12)\nshape coeffs\nN(e_i, kappa)", BLUE),
    (0.30, 0.72, "eigvalsh K(theta)\n-> mode freqs", GREY),
    (0.30, 0.30, "Phi_s @ c\nshape at sensors\n(basis @ theta_MAP, A9)", GREY),
    (0.56, 0.72, "freq lik (Kiran Eq 25)\n20 measured + 4 target modes\nsigma_w2 ~ HalfNormal", RED),
    (0.56, 0.30, "sensor lik\ny ~ N(Phi_s c, sigma_y)\nsigma_y ~ HalfNormal", RED),
    (0.82, 0.51, "DELIVERY\ntheta x c draws\n+ d ~ N(0,kappa) out-of-basis\n+ non-target tiers\n-> 95% band", GREEN),
]
for x, y, txt, col in boxes:
    ax.add_patch(plt.Rectangle((x, y - 0.11), 0.21, 0.24, fill=True, facecolor="white",
                               edgecolor=col, lw=1.4, transform=ax.transAxes))
    ax.text(x + 0.105, y + 0.01, txt, ha="center", va="center", fontsize=7.5,
            transform=ax.transAxes, color="#202020")
for (x0, y0), (x1, y1) in [((0.27, 0.83), (0.30, 0.83)), ((0.27, 0.41), (0.30, 0.41)),
                           ((0.51, 0.83), (0.56, 0.83)), ((0.51, 0.41), (0.56, 0.41)),
                           ((0.77, 0.83), (0.82, 0.60)), ((0.77, 0.41), (0.82, 0.48))]:
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="->", color=GREY, lw=1))
ax.set_title("Plate-test rehearsal: joint NUTS model (run-specific; schematic — no numeric data)",
             fontsize=10)
fig.text(0.01, 0.02, "Inferred: theta, sigma_w2, c, sigma_y. Fixed: zeta=1%, tiers, basis@theta_MAP, "
         "kappa. Latent not inferred: out-of-basis d (carried in delivery). Truth generator does NOT "
         "share the frozen-basis simplification (D4/D5).", fontsize=6.8, color=GREY)
fig.tight_layout(); fig.savefig(FIG / "fig_graphical_model.png", dpi=160)
plt.close(fig)
print("figures written:", sorted(p.name for p in FIG.glob("*.png")))
