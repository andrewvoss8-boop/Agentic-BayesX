#!/usr/bin/env python3
"""gif_story: animate the held-out-sensor FRF prediction across the 5 bias combos.

Each frame = one combo: at a fixed held-out sensor, the clean truth accelerance (black), the NAIVE (M0) 95%
predictive band (red, tight -> misses), and the SCHNEIDER (M2) 95% band (green, kriged -> covers). The frame
annotates the per-combo held-out QOI coverage. Tells the 'confidently wrong vs covered' story in one loop.
Recomputed from saved posterior samples (no re-run of NUTS). Saved to figures/gif_story.gif.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

import core
import predict as pr
import run_sweep as rs
import viz

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
FIG = WS / "figures"
COMBO_NAME = {1: "identifiable", 2: "unidentifiable", 3: "mixed", 4: "large", 5: "broad small"}


def band_for(model, freqs, ch, combo, arm, sensor_col, n_draws=250, seed=3):
    observed, heldout, drive = ch["observed"], ch["heldout"], ch["drive"]
    tt = core.theta_vector(core.COMBOS[combo]["theta"])
    meas, _, tho = rs.gen_truth(model, freqs, observed, heldout, drive, tt, combo)
    z = np.load(OUT / f"samples_{combo}_{arm}.npz")
    lt = z["log_theta"].astype(float); sd = z["sigma_d"].astype(float)
    ctx = pr.PredCtx(model, freqs, observed, heldout, drive, arm)
    rng = np.random.default_rng(seed)
    idx = np.linspace(0, len(lt) - 1, min(len(lt), n_draws)).astype(int)
    preds = np.zeros((len(idx), len(freqs)))
    for j, s in enumerate(idx):
        theta = np.exp(lt[s])
        lm_obs = np.log(np.abs(core.frf_np(model, freqs, theta, observed, drive)))
        lm_ho = np.log(np.abs(core.frf_np(model, freqs, theta, heldout, drive)))
        if arm == "M0":
            d_h = np.zeros_like(lm_ho)
        else:
            _, d_h = ctx.krige(meas - lm_obs, float(sd[s]), rng)
        preds[j] = (lm_ho + d_h)[:, sensor_col]
    lo, med, hi = np.percentile(np.exp(preds), [2.5, 50, 97.5], axis=0)
    return lo, med, hi, np.exp(tho[:, sensor_col])


def main():
    model = core.load_model(); ch = core.select_channels(model); freqs = core.freq_grid()
    # fixed held-out sensor: a mid-height one present in all combos (same channel set across combos)
    sensor_col = len(ch["heldout"]) // 2
    dof = ch["heldout"][sensor_col]; z_in = model.dof_xyz[dof, 2]
    frames = []
    for combo in [1, 2, 3, 4, 5]:
        lo0, m0, hi0, truth = band_for(model, freqs, ch, combo, "M0", sensor_col)
        lo2, m2, hi2, _ = band_for(model, freqs, ch, combo, "M2", sensor_col)
        cell0 = json.load(open(OUT / f"cell_{combo}_M0.json"))
        cell2 = json.load(open(OUT / f"cell_{combo}_M2.json"))
        cov0 = cell0["heldout_coverage"]["combined"]["frac"]
        cov2 = cell2["heldout_coverage"]["combined"]["frac"]
        fig, ax = plt.subplots(figsize=(9.5, 5.2))
        ax.fill_between(freqs, lo0, hi0, color=viz.C_M0, alpha=0.18)
        ax.fill_between(freqs, lo2, hi2, color=viz.C_M2, alpha=0.20)
        ax.plot(freqs, m0, color=viz.C_M0, lw=1.1)
        ax.plot(freqs, m2, color=viz.C_M2, lw=1.1)
        ax.plot(freqs, truth, color=viz.C_TRUTH, lw=1.7)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("frequency [Hz]  (log)")
        ax.set_ylabel("accelerance |H|  [(in/s$^2$)/lbf]  (log)")
        ax.set_ylim(truth.min() * 0.25, truth.max() * 4)
        ax.annotate("truth", (0.985, 0.93), xycoords="axes fraction", ha="right", color=viz.C_TRUTH, fontsize=9)
        ax.annotate(f"M0 naive 95% (held-out cov {cov0:.0%})", (0.985, 0.85), xycoords="axes fraction",
                    ha="right", color=viz.C_M0, fontsize=8.5)
        ax.annotate(f"M2 Schneider 95% (held-out cov {cov2:.0%})", (0.985, 0.77), xycoords="axes fraction",
                    ha="right", color=viz.C_M2, fontsize=8.5)
        ax.set_title(f"Held-out sensor z={z_in:.0f} in | combo {combo}: {COMBO_NAME[combo]} bias "
                     f"| naive {'MISSES' if cov0 < 0.5 else 'partial'}, Schneider covers", fontsize=10)
        viz.stamp(fig, extra=f"combo {combo}; held-out DOF {dof}; black=truth, shaded=95% predictive")
        fig.canvas.draw()
        fr = FIG / f"_gifframe_{combo}.png"
        fig.savefig(fr, dpi=110, bbox_inches="tight")
        plt.close(fig)
        frames.append(Image.open(fr).convert("RGB"))
    # uniform size
    w = min(im.width for im in frames); h = min(im.height for im in frames)
    frames = [im.resize((w, h)) for im in frames]
    frames[0].save(FIG / "gif_story.gif", save_all=True, append_images=frames[1:],
                   duration=1700, loop=0)
    for combo in [1, 2, 3, 4, 5]:
        (FIG / f"_gifframe_{combo}.png").unlink(missing_ok=True)
    print(f"saved gif_story.gif ({len(frames)} frames)")


if __name__ == "__main__":
    main()
