#!/usr/bin/env python3
"""E2 - baselines + reconstruction-error sweep.

Reproduces the paper's deterministic baseline ranking (Meas-Up discard / Interp-Up spatial
interpolation / FAU-Up virtual target) on masked channels, AND sweeps the reconstruction
error level. Adds the discrepancy-aware Bayesian update and its masked-channel coverage.

Paper-consistent finding we quantify: FAU-Up beats simply discarding the channel (Meas-Up)
ONLY when the reconstruction error falls below the physics-prediction floor; Interp-Up can
be worse than discarding. The Bayesian update keeps masked-channel coverage across levels.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import core
import nuts_update as nu
import viz
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "out"
FIG = ROOT / "figures"
SEED = 20260613
SIGMA_MEAS = 0.05
SIGMA_VIRTUAL = 0.30

# Reconstruction-error levels: one fixed correlated error field scaled by these multipliers,
# so the realized error rises monotonically and reproducibly (no tail-draw noise).
LEVELS = [("good", 0.4), ("fair", 0.9), ("poor", 1.6), ("bad", 2.6), ("severe", 3.8)]


def masked_peak_db_err(Hpred, truth, freqs, qoi_mask):
    errs = []
    hf_idx = np.where(qoi_mask)[0]
    for c in core.MASKED:
        pb = hf_idx[np.argmax(np.abs(truth[hf_idx, c]))]
        errs.append(abs(core.db(Hpred[pb, c]) - core.db(truth[pb, c])))
    return float(np.mean(errs)), errs


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    modes = core.default_modes()
    freqs = core.freq_grid(160)
    qoi_mask = core.band_mask(freqs, 450.0, 900.0)

    alpha_truth = np.array([0.97, 0.90, 0.85, 0.80])
    beta_truth = np.array([1.2, 1.3, 1.4, 1.5])
    gamma_truth = 1.05 * core.GAMMA0
    T = core.make_truth(freqs, modes, alpha_truth, beta_truth, gamma_truth, rng,
                        disc_std_lo=0.04, disc_std_hi=0.45)
    truth = T["truth"]
    measured = core.measure(truth, core.MASKED, rng, SIGMA_MEAS, SIGMA_MEAS)

    sig_ch = np.array([SIGMA_MEAS, SIGMA_MEAS, SIGMA_VIRTUAL, SIGMA_VIRTUAL])
    hf_idx = np.where(qoi_mask)[0]

    # Recon-independent baselines (computed once on the fixed measurement realization):
    #  Meas-Up = discard masked, fit observed, predict masked from shared physics.
    #  Interp-Up = recover masked by spatial interpolation across healthy channels (data only).
    det_meas = core.deterministic_update(freqs, modes, measured, np.array([1.0, 1.0, 0.0, 0.0]), rng)
    meas_err, _ = masked_peak_db_err(det_meas["H"], truth, freqs, qoi_mask)
    interp = core.interp_fill(measured, core.OBSERVED, core.MASKED)
    interp_err, _ = masked_peak_db_err(interp, truth, freqs, qoi_mask)

    # One fixed correlated reconstruction-error field (log units), scaled per level.
    g0 = np.log(core.correlated_logfield(freqs, modes.nc, np.random.default_rng(SEED + 7),
                                         std_lo=0.06, std_hi=0.50))

    rows = []
    for name, lam in LEVELS:
        virtual = truth * np.exp(lam * g0)
        realized = masked_peak_db_err(virtual, truth, freqs, qoi_mask)[0]
        tgt = measured.copy()
        tgt[:, core.MASKED] = virtual[:, core.MASKED]
        det_fau = core.deterministic_update(freqs, modes, tgt, np.ones(modes.nc), rng)
        fau_err = masked_peak_db_err(det_fau["H"], truth, freqs, qoi_mask)[0]

        samples, diag = nu.run_nuts(freqs, modes, np.log(np.abs(tgt)), np.arange(modes.nc),
                                    sig_ch, num_warmup=700, num_samples=700, seed=SEED)
        _, noisy, _ = nu.posterior_predict(samples, freqs, modes, sig_ch, rng, thin=4)
        cov, ntot, bayes_e = 0, 0, []
        for c in core.MASKED:
            pb = hf_idx[np.argmax(np.abs(truth[hf_idx, c]))]
            qp = np.exp(noisy[:, pb, c])
            lo, med, hi = np.percentile(qp, [2.5, 50, 97.5])
            cov += int(lo <= np.abs(truth[pb, c]) <= hi); ntot += 1
            bayes_e.append(abs(20 * np.log10(med / np.abs(truth[pb, c]))))
        rows.append({
            "level": name, "scale_lambda": lam,
            "realized_recon_peak_err_db": realized,
            "interp_up_err_db": interp_err,
            "meas_up_err_db": meas_err,
            "fau_up_err_db": fau_err,
            "bayes_median_err_db": float(np.mean(bayes_e)),
            "bayes_masked_qoi_covered": cov, "bayes_masked_qoi_n": ntot,
            "nuts": diag,
            "nuts_converged": bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02),
        })

    summary = {
        "experiment": "E2_baselines_sweep",
        "runtime_s": round(time.time() - t0, 2),
        "meas_up_floor_db": meas_err,
        "note": "Meas-Up predicts masked channels from shared physics (discard). Interp-Up "
                "interpolates across channels. FAU-Up trusts the surrogate virtual target. "
                "Bayes down-weights the virtual target and reports an interval.",
        "levels": rows,
        "all_nuts_converged": bool(all(r["nuts_converged"] for r in rows)),
    }
    json.dump(summary, open(OUT / "exp2_summary.json", "w"), indent=2)

    # ---- Figure: masked-channel peak error vs reconstruction error, with coverage ----
    x = [r["realized_recon_peak_err_db"] for r in rows]
    fig, ax = plt.subplots(figsize=(9.0, 5.8))
    ax.axhline(meas_err, color="#6b7280", lw=1.4, ls="--")
    ax.text(x[0], meas_err * 1.03, "Meas-Up (discard + physics) floor", color="#6b7280", fontsize=8.5, va="bottom")
    ax.plot([x[0], x[-1]], [interp_err, interp_err], "s--", color="#8e44ad", label="Interp-Up (spatial interp)")
    ax.plot(x, [r["fau_up_err_db"] for r in rows], "o-", color=viz.C_DET, label="FAU-Up (trust surrogate)")
    ax.plot(x, [r["bayes_median_err_db"] for r in rows], "D-", color=viz.C_BAYES, label="Bayes posterior median")
    for r, xi in zip(rows, x):
        conv = r["nuts_converged"]
        ax.annotate(f"{r['bayes_masked_qoi_covered']}/{r['bayes_masked_qoi_n']} cov",
                    (xi, r["bayes_median_err_db"]), textcoords="offset points", xytext=(0, -15),
                    fontsize=7.5, color=viz.C_BAYES if conv else "#b91c1c", ha="center")
        if not conv:
            ax.plot(xi, r["bayes_median_err_db"], "o", mfc="none", mec="#b91c1c", ms=15, mew=2)
            ax.annotate(f"NOT converged\n(ESS {r['nuts']['min_ess']:.0f}<200)", (xi, r["bayes_median_err_db"]),
                        textcoords="offset points", xytext=(-6, 16), fontsize=7.5, color="#b91c1c", ha="right")
    ax.plot([0, max(x)], [0, max(x)], color="0.8", lw=1.0, zorder=0)
    ax.text(max(x) * 0.60, max(x) * 0.64, "reference: error = recon error", color="0.6", fontsize=8, rotation=30)
    ax.text(max(x) * 0.30, 4.95, "FAU-Up peels off the diagonal at high error:\nobserved channels + box constraints partly reject a grossly-wrong surrogate",
            color=viz.C_DET, fontsize=7.0, ha="left", va="bottom")
    ax.set_xlabel("realized reconstruction main-peak error [dB]")
    ax.set_ylabel("masked-channel main-peak error [dB]")
    viz.style(ax, logx=False)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.set_title("E2: deterministic baselines vs reconstruction error (Bayes coverage annotated)")
    p = viz.save(fig, FIG / "exp2_baselines_sweep.png")
    viz.image_qa([p], ROOT / "image_qa_exp2.json")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
