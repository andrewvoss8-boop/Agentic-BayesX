#!/usr/bin/env python3
"""STAGE-3 human-review figures: posterior-predictive AM overlay (train + held-out, per DOF, log-f),
with/without structure-based discrepancy mode-split comparison, hyperparameter posteriors.
Reads report/blind3_posterior.npz (+ _nodisc). Writes report/figures/blind3_*.png."""
from __future__ import annotations
from pathlib import Path
import numpy as np
import jax, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import blind3_model as bm
import blind3_infer as bi

REP = Path(__file__).resolve().parents[1] / "report"; FIG = REP / "figures"; FIG.mkdir(parents=True, exist_ok=True)
DOF = bm.DOF


def predict_mag(P, build_factor, grid):
    k_pop = np.exp(P["log_k_pop"]); d0 = P["d0"]; f_dome = P["f_dome"]
    gj = jnp.asarray(grid); nd = len(k_pop)
    out = np.empty((nd, 6, len(grid)))
    for i in range(nd):
        k = k_pop[i] * build_factor[i] * np.exp(d0[i])
        M = np.asarray(bm.forward_complex(jnp.asarray(k), float(f_dome[i]), P["M_src6"], float(P["m_dome"]), gj))
        out[i] = np.abs(M)
    return out


def main():
    obs = bm.load_observations(); f = obs["f"]
    P = np.load(REP / "blind3_posterior.npz"); grid = P["grid"]
    rng = np.random.default_rng(3); nd = len(P["log_k_pop"])
    sb = P["sigma_build"]

    # ---- FIG A: posterior-predictive |AM| overlay vs data, train build 0 + held-out build 6 ----
    for tag, b in [("train_b0", 0), ("heldout_b6", 6)]:
        bf = np.exp(sb * rng.standard_normal(nd))
        pm = predict_mag(P, bf, grid)                    # (nd,6,ng)
        lo, md, hi = np.percentile(pm, [2.5, 50, 97.5], axis=0)
        fig, axes = plt.subplots(2, 3, figsize=(15, 8))
        for j, ax in enumerate(axes.ravel()):
            ax.loglog(f, obs["mag"][b, j], color="#d62728", lw=1.1, alpha=0.8, label="data |AM|")
            ax.loglog(grid, md[j], color="#1f77b4", lw=1.8, label="post. pred. median")
            ax.fill_between(grid, lo[j], hi[j], color="#1f77b4", alpha=0.18, label="95% band")
            ax.set_title(f"DOF {DOF[j]}", fontsize=10); ax.grid(True, which="both", alpha=0.3)
            ax.set_xlim(30, 200); ax.set_xlabel("freq [Hz] (log)"); ax.set_ylabel("|AM|")
            if j == 0:
                ax.legend(fontsize=8)
        fig.suptitle(f"Posterior-predictive interface apparent mass vs data — {tag} "
                     f"(model is coarse above the first mode cluster: missing higher modes -> residual)",
                     fontsize=11)
        fig.tight_layout(); fig.savefig(FIG / f"blind3_ppc_{tag}.png", dpi=130); plt.close(fig)

    # ---- FIG B: WITH vs WITHOUT structure-based discrepancy — lateral split x vs y (build-avg) ----
    nd_path = REP / "blind3_posterior_nodisc.npz"
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.2))
    bf1 = np.exp(sb * 0.0 * np.ones(nd))                 # population (no build offset)
    pm_w = predict_mag(P, bf1, grid); mdw = np.median(pm_w, axis=0)
    data = obs["mag"].mean(axis=0)
    for ax, (jx, jy, nm) in zip(axes, [(0, 1, "x vs y (lateral)"), (3, 4, "rx vs ry (rocking)")]):
        ax.loglog(f, data[jx], color="#d62728", lw=1.2, label=f"data {DOF[jx]}")
        ax.loglog(f, data[jy], color="#ff7f0e", lw=1.2, label=f"data {DOF[jy]}")
        ax.loglog(grid, mdw[jx], color="#1f77b4", lw=1.8, ls="-", label=f"with-d {DOF[jx]}")
        ax.loglog(grid, mdw[jy], color="#2ca02c", lw=1.8, ls="--", label=f"with-d {DOF[jy]}")
        ax.set_xlim(35, 160); ax.set_title(f"Structure-based discrepancy splits {nm}", fontsize=10)
        ax.grid(True, which="both", alpha=0.3); ax.set_xlabel("freq [Hz] (log)"); ax.set_ylabel("|AM|")
        ax.legend(fontsize=8)
    fig.suptitle("Does the per-strut feature-space discrepancy represent the x≠y / rx≠ry mode SPLITS "
                 "a frequency-only kernel could not?", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "blind3_split_with_d.png", dpi=130); plt.close(fig)

    # ---- FIG C: hyperparameter posteriors (sigma_e, sigma_d, sigma_build) + with/without sigma_e ----
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.4))
    for ax, key, ttl in zip(axes, ["sigma_e", "sigma_d", "sigma_build"],
                            ["σ_e (noise / misfit)", "σ_d (structure-based discrepancy)", "σ_build"]):
        if key in P.files:
            ax.hist(P[key], bins=40, color="#9ecae1", density=True)
            ax.axvline(np.median(P[key]), color="#1f77b4", lw=2, label=f"median {np.median(P[key]):.3f}")
        if key == "sigma_e" and nd_path.exists():
            P0 = np.load(nd_path)
            ax.hist(P0["sigma_e"], bins=40, color="#fdbe85", density=True, alpha=0.6, label="without-d")
        ax.set_title(ttl, fontsize=10); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    fig.suptitle("Hyperparameter posteriors — headline: does the structure-based discrepancy lower σ_e "
                 "and is σ_d identified (ridge resolved)?", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "blind3_hyperparams.png", dpi=130); plt.close(fig)
    print("wrote blind3 figures")


if __name__ == "__main__":
    main()
