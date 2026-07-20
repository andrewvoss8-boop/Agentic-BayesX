#!/usr/bin/env python3
"""figD: naive vs StatFEM held-out-sensor FRF predictive bands (the visual of "confidently wrong").

For one combo and one held-out sensor: the clean truth accelerance, the naive (M0) 95% predictive band
(tight, misses), and the Schneider (M2) 95% band (kriged discrepancy). Log-frequency, linear magnitude;
the held-out peak QOI marked. Recomputed from saved posterior samples (no re-run of NUTS).
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

import core
import predict as pr
import run_sweep as rs
import viz

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"


def predictive_band(model, freqs, ch, combo_idx, arm, sensor_col, n_draws=300, seed=11):
    observed, heldout, drive = ch["observed"], ch["heldout"], ch["drive"]
    tt = core.theta_vector(core.COMBOS[combo_idx]["theta"])
    meas, _, tho = rs.gen_truth(model, freqs, observed, heldout, drive, tt, combo_idx)
    z = np.load(OUT / f"samples_{combo_idx}_{arm}.npz")
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
        elif arm == "M1":
            d_h = rng.normal(0, float(sd[s]), lm_ho.shape)
        else:
            _, d_h = ctx.krige(meas - lm_obs, float(sd[s]), rng)
        preds[j] = (lm_ho + d_h)[:, sensor_col]
    lo, med, hi = np.percentile(np.exp(preds), [2.5, 50, 97.5], axis=0)
    truth = np.exp(tho[:, sensor_col])
    return lo, med, hi, truth


def main():
    model = core.load_model(); ch = core.select_channels(model); freqs = core.freq_grid()
    COMBO = 4  # "large" bias -- most dramatic
    # choose the held-out sensor where M0 misses worst (read its cell)
    cM0 = json.load(open(OUT / f"cell_{COMBO}_M0.json"))
    qoi = cM0["heldout_qoi"]
    # find held-out sensor (by dof id) with worst peak miss; map to column index
    worst = max(qoi.items(), key=lambda kv: abs(np.log(kv[1]["peak"]["med"] / max(kv[1]["peak"]["truth"], 1e-9))))
    worst_dof = int(worst[0])
    sensor_col = list(ch["heldout"]).index(worst_dof)
    z_in = model.dof_xyz[worst_dof, 2]

    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    lo0, med0, hi0, truth = predictive_band(model, freqs, ch, COMBO, "M0", sensor_col)
    lo2, med2, hi2, _ = predictive_band(model, freqs, ch, COMBO, "M2", sensor_col)
    ax.fill_between(freqs, lo0, hi0, color=viz.C_M0, alpha=0.18)
    ax.fill_between(freqs, lo2, hi2, color=viz.C_M2, alpha=0.18)
    ax.plot(freqs, med0, color=viz.C_M0, lw=1.3)
    ax.plot(freqs, med2, color=viz.C_M2, lw=1.3)
    ax.plot(freqs, truth, color=viz.C_TRUTH, lw=1.6)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("frequency [Hz]  (log)")
    ax.set_ylabel("accelerance |H| [ (in/s$^2$)/lbf ]  (log)")
    # direct labels at staggered axis-fraction y positions (avoid end-of-line collisions)
    ax.annotate("truth", (0.985, 0.93), xycoords="axes fraction", color=viz.C_TRUTH, fontsize=9,
                ha="right", va="center")
    ax.annotate("M0 naive 95%", (0.985, 0.84), xycoords="axes fraction", color=viz.C_M0, fontsize=8.5,
                ha="right", va="center")
    ax.annotate("M2 Schneider 95%", (0.985, 0.75), xycoords="axes fraction", color=viz.C_M2, fontsize=8.5,
                ha="right", va="center")
    # mark peak QOI truth
    pk = freqs[np.argmax(truth)]
    ax.axvline(pk, color="0.85", lw=0.8)
    cP = "covered" if qoi[str(worst_dof)]["peak"]["covered"] else "MISSED"
    ax.set_title(f"Held-out sensor z={z_in:.0f} in (combo {COMBO} 'large'): naive band {cP} the truth peak; "
                 f"Schneider band kriged from observed", fontsize=9.5)
    viz.save(fig, "figD_heldout_frf_bands",
             extra=f"combo {COMBO}, held-out DOF {worst_dof}; black=truth, shaded=95% predictive")
    print(f"figD done (combo {COMBO}, held-out dof {worst_dof}, z={z_in:.1f})")


if __name__ == "__main__":
    main()
