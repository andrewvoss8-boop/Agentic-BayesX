#!/usr/bin/env python3
"""
Grading figures, regenerated under the tufte-data-graphics skill checklist.
Writes ONLY under review/. Direct labels (no legends), zero-baseline bars,
log frequency axis, inter-channel spread bands, captions carry the numbers.

Two honesty notes baked into the pyro figure:
  - The runner committed NO predicted pyro MAGNITUDE (modal twin cannot supply absolute
    pyro levels). So we do NOT fabricate a predicted PSD curve. Instead we show the twin's
    real *coverage*: the cumulative fraction of measured energy that falls inside the twin's
    validated band (~152 Hz). That fraction (~0.07%) IS the honest predicted-vs-actual story.
  - Spread is shown as the 16-84th percentile band across the 128 measured channels.
"""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def tufte(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=3, labelsize=9)
    ax.grid(True, which="major", color="0.85", lw=0.5)
    ax.set_axisbelow(True)


# ----------------------------------------------------------------------------- pyro
d = np.load(os.path.join(HERE, "pyro_spectrum.npz"))
f = d["f"]; psd = d["psd_all"]; cum = d["cumfrac"]
lo, med, hi = (np.percentile(psd, q, axis=0) for q in (16, 50, 84))
clo, cmed, chi = (np.percentile(cum, q, axis=0) for q in (16, 50, 84))
TWIN = 152.27
i152 = np.searchsorted(f, TWIN)
cov152 = np.median(cum[:, i152])
fpk = f[np.argmax(med)]
m = f > 0

fig, (a0, a1) = plt.subplots(2, 1, figsize=(7.2, 7.4), sharex=True)

# Panel A: measured PSD, median + inter-channel band, twin band shaded
a0.fill_between(f[m], lo[m], hi[m], color="#4c72b0", alpha=0.20, lw=0)
a0.loglog(f[m], med[m], color="#1f3b73", lw=1.0)
a0.axvspan(f[1], TWIN, color="0.90", lw=0)
f95 = float(np.median([f[np.searchsorted(c, 0.95)] for c in cum]))
tufte(a0)
a0.set_ylabel("PSD  (g$^2$/Hz)", fontsize=9)
a0.text(TWIN*0.55, med[m].max()*0.5, "twin's validated\nband  ≤152 Hz",
        fontsize=8.5, ha="center", color="0.30")
a0.text(700, med[m].max()*0.6,
        f"broadband pyro energy,\n~10$^2$–10$^4$ Hz;\n95% of energy ≤ ~{f95/1000:.0f} kHz",
        fontsize=8.5, color="#c44e52")
a0.annotate("median of 128 channels;\nshaded = 16–84th pct across channels",
            xy=(f[m][-1], med[m][-1]), xytext=(f[m][-1]*0.06, med[m][-1]*0.02),
            fontsize=8, color="#1f3b73")
a0.set_title("a. Measured pyro-NSD acceleration spectrum (held-out truth)",
             fontsize=10, loc="left")

# Panel B: cumulative energy fraction = the twin's COVERAGE vs frequency
a1.fill_between(f[m], clo[m]*100, chi[m]*100, color="#55a868", alpha=0.20, lw=0)
a1.semilogx(f[m], cmed[m]*100, color="#1b5e20", lw=1.1)
a1.axvspan(f[1], TWIN, color="0.90", lw=0)
a1.plot([TWIN], [cov152*100], "o", color="#c44e52", ms=5)
a1.annotate(f"twin band edge: only {cov152*100:.2f}% of\nmeasured energy lies ≤152 Hz\n"
            f"→ twin can model ~0% of the regime",
            xy=(TWIN, cov152*100), xytext=(TWIN*1.4, 32),
            fontsize=8.5, color="#7a1f1a",
            arrowprops=dict(arrowstyle="->", color="#7a1f1a", lw=0.8))
tufte(a1)
a1.set_ylim(0, 100)
a1.set_ylabel("cumulative energy ≤ f  (%)", fontsize=9)
a1.set_xlabel("Frequency (Hz, log)", fontsize=9)
a1.set_title("b. Twin coverage: fraction of real energy the ≤152 Hz modal twin can reach",
             fontsize=10, loc="left")

fig.suptitle("Pyro OOD check: modal twin under-resolves the pyro regime (runner's committed DIRECTION confirmed)",
             fontsize=11, y=0.995, x=0.01, ha="left")
fig.text(0.01, 0.005,
         "Source: Pyro_NSD_990x001_HELDOUT.mat (NASA/NESC ShockSat), 128 accel ch (g), fs=250 kHz, "
         "Welch nperseg=8192. Held-out (sealed) truth, SHA256 03e476fa…. No predicted MAGNITUDE was "
         "committed by the runner, so no predicted PSD curve is drawn; panel b is the honest coverage proxy.",
         fontsize=6.6, color="0.35", ha="left", va="bottom", wrap=True)
fig.tight_layout(rect=(0, 0.03, 1, 0.97))
fig.savefig(os.path.join(HERE, "fig_pyro_spectrum.png"), dpi=140)
print("wrote fig_pyro_spectrum.png  (twin coverage at 152 Hz = %.3f%%)" % (cov152*100))

# --------------------------------------------------------------------------- vault
rows = json.load(open(os.path.join(ROOT, "vault_grading_result.json")))["rows"]
ids = [r[0].split("_")[0] for r in rows]
disc = {"F1": "freq+shape disc.", "F2": "freq disc.", "F3": "no disc."}
dev = [r[5] for r in rows]; inreg = [r[3] for r in rows]; ood = [r[4] for r in rows]
col = {"F1": "#c44e52", "F2": "#dd8452", "F3": "#55a868"}

fig2, (b0, b1) = plt.subplots(1, 2, figsize=(11, 4.6))

# Panel A: dev score (what you see) vs OOD QOI error (the truth)
for x, y, i in zip(dev, ood, ids):
    b0.plot(x, y, "o", color=col[i], ms=11)
    b0.annotate(f"{i}  {disc[i]}", (x, y), xytext=(9, 4),
                textcoords="offset points", fontsize=9, color=col[i])
b0.annotate("", xy=(dev[0], ood[0]), xytext=(dev[2], ood[2]),
            arrowprops=dict(arrowstyle="->", color="0.5", ls=(0, (4, 3)), lw=1))
b0.text(np.mean([dev[0], dev[2]]), np.mean([ood[0], ood[2]])+0.45,
        "+246 nats of dev-LPD\nbought NO OOD-QOI gain", fontsize=8.5,
        ha="center", color="0.35")
tufte(b0)
b0.set_xlabel("dev-LPD  (higher = better in-distribution fit, nats)", fontsize=9)
b0.set_ylabel("VAULT held-out OOD QOI error  (%, lower better)", fontsize=9)
b0.set_title("a. dev winner F1 is NOT the OOD winner → dev was a leaky proxy",
             fontsize=10, loc="left")

# Panel B: in-regime vs OOD error per finalist, zero-baseline bars, direct labels
x = np.arange(3); w = 0.36
b1.bar(x - w/2, inreg, w, color="#bcc7d6")
b1.bar(x + w/2, ood, w, color="#c44e52")
for xi, v in zip(x - w/2, inreg):
    b1.text(xi, v + 0.6, f"{v:.0f}", ha="center", fontsize=8, color="#5a6b80")
for xi, v in zip(x + w/2, ood):
    b1.text(xi, v + 0.6, f"{v:.0f}", ha="center", fontsize=8, color="#c44e52")
b1.text(0.5 - w/2, max(inreg)+5, "in-regime\n(path 11←0)", ha="center",
        fontsize=8.5, color="#5a6b80")
b1.text(0.5 + w/2, max(ood)+3, "held-out OOD\n(path 5←8)", ha="center",
        fontsize=8.5, color="#c44e52")
tufte(b1)
b1.set_ylim(0, max(ood)+9)
b1.set_xticks(x); b1.set_xticklabels(ids, fontsize=9)
b1.set_ylabel("QOI relative error (%)", fontsize=9)
b1.set_title("b. OOD error (~40–44%) ≈ 4× in-regime error (~9–11%), every finalist",
             fontsize=10, loc="left")

fig2.text(0.005, 0.005,
          "Source: scripts/score_vault.py vs sealed vault/tray/truth.json (synthetic, SHA256 0cc799b4…). "
          "N=31 configs; finalists frozen pre-vault. QOI = peak receptance |H| over 10–600 Hz, m/N.",
          fontsize=6.6, color="0.35", ha="left")
fig2.tight_layout(rect=(0, 0.04, 1, 1))
fig2.savefig(os.path.join(HERE, "fig_dev_vs_vault.png"), dpi=140)
print("wrote fig_dev_vs_vault.png")
