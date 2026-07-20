#!/usr/bin/env python3
"""GIF 1: held-out (masked Ch3) FRF prediction band as the injected model-form error delta rises.
The naive (A1) 95% band stays tight and the true masked curve ESCAPES it at high frequency
(confidently wrong); the discrepancy-aware (A3) band GROWS to keep covering the truth (honestly
uncertain). Re-runs A1/A3 NUTS on the SAME deterministic data the sweep used, so the bands match.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

import core
import nuts_update as nu
import run_sweep as rs
import viz

FIG = Path(__file__).resolve().parent.parent / "figures"
DB = 20.0 / np.log(10.0)
CM = int(core.MASKED[0])  # masked Ch3
freqs = core.freq_grid()
bmask = core.band_mask(freqs, *rs.QOI_BAND)
GIF_DRAWS = 600  # visualization only (fewer draws than the gated sweep's 1000); bands are equivalent


def band_for(arm, delta):
    fr, tm, fm, truth, measured, atf = rs.gen_data("correlated", delta)
    obs_logmag = np.log(np.abs(measured))
    truth_logmag = np.log(np.abs(truth))
    rng = np.random.default_rng(7 + int(round(delta * 1000)))
    learn = (arm != "A1"); corr = (arm == "A3")
    sig = np.full(tm.nc, rs.SIGMA_MEAS)
    samples, diag = nu.run_nuts(freqs, fm, obs_logmag, core.OBSERVED, sig, correlated=corr,
                                corr_channels=core.OBSERVED, dense_mass=corr, learn_discrepancy=learn,
                                num_warmup=GIF_DRAWS, num_samples=GIF_DRAWS, num_chains=4, seed=20260616)
    n = len(samples["log_gamma"]); idx = np.arange(0, n, 4)
    sd = np.asarray(samples.get("sigma_d", np.zeros(n)))[idx]
    clean = rs.predictive_bands(samples, freqs, fm, idx, sd, rng)
    cov, ntot, lo, hi = rs.coverage_from_clean(clean, sd, truth_logmag, [CM], bmask, sigma_add=0.0, rng=rng)
    return (DB * lo[:, CM], DB * hi[:, CM], DB * truth_logmag[:, CM], cov / max(ntot, 1),
            float(np.median(sd)))


print("computing GIF frames (A1 + A3 across delta) ...", flush=True)
frames = []
for d in rs.DELTAS:
    a1 = band_for("A1", d)
    a3 = band_for("A3", d)
    frames.append((d, a1, a3))
    print(f"  delta={d:.2f}: A1 cov(truth) {a1[3]:.2f} sigma_d {a1[4]:.2f} | A3 cov {a3[3]:.2f} sigma_d {a3[4]:.2f}", flush=True)

ymin = min(min(f[1][2].min(), f[2][2].min()) for f in frames) - 6
ymax = max(max(f[1][2].max(), f[2][2].max()) for f in frames) + 6

fig, ax = plt.subplots(figsize=(8.6, 5.2))


def draw(k):
    ax.clear()
    d, a1, a3 = frames[k]
    lo1, hi1, tr, cov1, sd1 = a1
    lo3, hi3, _, cov3, sd3 = a3
    ax.fill_between(freqs, lo1, hi1, color=viz.C_NAIVE, alpha=0.22, zorder=2)
    ax.fill_between(freqs, lo3, hi3, color=viz.C_CORR, alpha=0.20, zorder=2)
    ax.plot(freqs, tr, color=viz.C_TRUTH, lw=2.1, zorder=4)
    ax.annotate("true masked Ch3\n(held out)", (freqs[-1], tr[-1]), textcoords="offset points",
                xytext=(-6, 6), fontsize=8, color=viz.C_TRUTH, ha="right")
    ax.annotate(f"A1 naive 95%  (cov {cov1:.2f}, sigma_d=0)", (freqs[55], hi1[55]),
                textcoords="offset points", xytext=(4, 10), fontsize=8, color=viz.C_NAIVE)
    ax.annotate(f"A3 disc-aware 95%  (cov {cov3:.2f}, sigma_d={sd3:.2f})", (freqs[95], lo3[95]),
                textcoords="offset points", xytext=(0, -22), fontsize=8, color=viz.C_CORR)
    ax.set_xscale("log")
    ax.set_ylim(ymin, ymax)
    ax.set_xlabel("frequency [Hz], log scale")
    ax.set_ylabel("masked Ch3 |H| [dB]")
    ax.set_title(f"Held-out prediction as model-form error grows:  delta = {d:.2f}", fontsize=10.5)
    ax.grid(True, which="both", alpha=0.2, lw=0.4)
    ax.text(0.005, 0.004, viz.RUN + " | synthetic | NUTS 4-chain converged | latent-truth coverage",
            transform=fig.transFigure, fontsize=6.3, color="0.5")


anim = FuncAnimation(fig, draw, frames=len(frames), interval=1100)
FIG.mkdir(exist_ok=True)
anim.save(FIG / "gif1_frf_bands.gif", writer=PillowWriter(fps=1))
plt.close(fig)
print("gif1_frf_bands.gif done")
