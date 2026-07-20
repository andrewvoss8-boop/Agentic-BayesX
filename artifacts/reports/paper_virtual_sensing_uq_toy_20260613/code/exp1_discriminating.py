#!/usr/bin/env python3
"""E1 - discriminating experiment.

Same imperfect virtual ground truth fed to:
  (A) deterministic constrained least-squares update (the paper's FAU-Up, point estimate);
  (B) discrepancy-aware NUTS update (the paper's deferred Future-Work #3 UQ).
Trust test = held-out TRUE masked-channel FRF + masked-channel peak QOI.

Headline being tested: UQ converts a possibly confidently-wrong point estimate into an
honest interval that covers the masked-channel truth. Value = coverage, not point precision.
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
for d in (OUT, FIG):
    d.mkdir(exist_ok=True)

SEED = 20260613
SIGMA_MEAS = 0.05         # observed-channel measurement noise (nat-log units)
SIGMA_VIRTUAL = 0.30      # credibility noise assigned to the reconstructed masked channels


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    modes = core.default_modes()
    freqs = core.freq_grid(160)
    bmask = core.band_mask(freqs)                       # broadband, held-out line coverage
    qoi_mask = core.band_mask(freqs, 450.0, 900.0)      # HIGH-frequency regime (paper's 800 Hz story)

    # Truth: joint softening (alpha<1, stronger at high modes) + extra damping + un-modeled
    # discrepancy that GROWS at high frequency (mimics micro-slip nonlinearity the paper blames).
    alpha_truth = np.array([0.97, 0.90, 0.85, 0.80])
    beta_truth = np.array([1.2, 1.3, 1.4, 1.5])
    gamma_truth = 1.05 * core.GAMMA0
    T = core.make_truth(freqs, modes, alpha_truth, beta_truth, gamma_truth, rng,
                        disc_std_lo=0.04, disc_std_hi=0.45)
    truth = T["truth"]

    measured = core.measure(truth, core.MASKED, rng, SIGMA_MEAS, SIGMA_MEAS)
    virtual = core.reconstruct_virtual(truth, core.MASKED, rng,
                                       recon_std_lo=0.08, recon_std_hi=0.60,
                                       modes=modes, freqs=freqs)

    # Reference target: observed channels = measured; masked channels = virtual ground truth.
    target = measured.copy()
    target[:, core.MASKED] = virtual[:, core.MASKED]

    # ---- (A) deterministic FAU-Up: trust all 4 channels equally (paper Wch=1) ----
    cw_det = np.ones(modes.nc)
    det = core.deterministic_update(freqs, modes, target, cw_det, rng)

    # ---- (B) discrepancy-aware NUTS: down-weight the virtual (masked) channels ----
    target_logmag = np.log(np.abs(target))
    sigma_per_channel = np.array([SIGMA_MEAS, SIGMA_MEAS, SIGMA_VIRTUAL, SIGMA_VIRTUAL])
    samples, diag = nu.run_nuts(freqs, modes, target_logmag, np.arange(modes.nc),
                                sigma_per_channel, correlated=False, seed=SEED)
    clean, noisy, _ = nu.posterior_predict(samples, freqs, modes, sigma_per_channel, rng, thin=4)

    # ---- Trust test on masked channels (post-hoc TRUE FRF) ----
    truth_logmag = np.log(np.abs(truth))
    results_masked = {}
    det_qoi_err_db, bayes_cov_qoi = [], []
    cover_lines, n_lines = 0, 0          # broadband
    cover_hf, n_hf = 0, 0                # high-frequency band
    for c in core.MASKED:
        # high-frequency QOI peak (paper's 800 Hz regime)
        hf_idx = np.where(qoi_mask)[0]
        peak_bin = hf_idx[np.argmax(np.abs(truth[hf_idx, c]))]
        det_peak_db_err = abs(core.db(det["H"][peak_bin, c]) - core.db(truth[peak_bin, c]))
        # masked-channel main-peak amplitude QOI at the peak bin (paper Eq. 18, single freq)
        q_truth = float(np.abs(truth[peak_bin, c]))
        q_det = float(np.abs(det["H"][peak_bin, c]))
        det_qoi_err = abs(20 * np.log10(q_det / q_truth))
        # Bayes predictive band on log-mag (held-out lines) and QOI
        lo = np.percentile(noisy[:, :, c], 2.5, axis=0)
        hi = np.percentile(noisy[:, :, c], 97.5, axis=0)
        in_band = (truth_logmag[bmask, c] >= lo[bmask]) & (truth_logmag[bmask, c] <= hi[bmask])
        cover_lines += int(in_band.sum())
        n_lines += int(bmask.sum())
        in_hf = (truth_logmag[qoi_mask, c] >= lo[qoi_mask]) & (truth_logmag[qoi_mask, c] <= hi[qoi_mask])
        cover_hf += int(in_hf.sum())
        n_hf += int(qoi_mask.sum())
        q_post = np.exp(noisy[:, peak_bin, c])
        q_lo, q_med, q_hi = np.percentile(q_post, [2.5, 50, 97.5])
        bayes_q_cov = bool(q_lo <= q_truth <= q_hi)
        det_qoi_err_db.append(float(det_qoi_err))
        bayes_cov_qoi.append(bayes_q_cov)
        # naive deterministic "interval" = point +- measurement-noise (the honest UQ a point fit can offer)
        det_q_lo = q_det * np.exp(-1.96 * SIGMA_MEAS)
        det_q_hi = q_det * np.exp(1.96 * SIGMA_MEAS)
        det_q_cov = bool(det_q_lo <= q_truth <= det_q_hi)
        results_masked[f"Ch{c+1}"] = {
            "peak_freq_hz": float(freqs[peak_bin]),
            "det_peak_amp_err_db": float(det_peak_db_err),
            "qoi_truth": q_truth,
            "qoi_det_point": q_det,
            "det_qoi_err_db": float(det_qoi_err),
            "det_qoi_interval_meas_noise": [float(det_q_lo), float(det_q_hi)],
            "det_qoi_covers_truth": det_q_cov,
            "bayes_qoi_interval": [float(q_lo), float(q_med), float(q_hi)],
            "bayes_qoi_covers_truth": bayes_q_cov,
        }

    hf_idx = np.where(qoi_mask)[0]
    realized_recon_peak_db = float(np.mean([
        abs(core.db(virtual[hf_idx[np.argmax(np.abs(truth[hf_idx, c]))], c])
            - core.db(truth[hf_idx[np.argmax(np.abs(truth[hf_idx, c]))], c])) for c in core.MASKED]))

    conv = diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02
    summary = {
        "experiment": "E1_discriminating",
        "runtime_s": round(time.time() - t0, 2),
        "design": {
            "n_modes": modes.nm, "n_channels": modes.nc,
            "observed_channels": ["Ch1", "Ch2"], "masked_channels": ["Ch3", "Ch4"],
            "sigma_meas": SIGMA_MEAS, "sigma_virtual_credibility": SIGMA_VIRTUAL,
            "realized_recon_peak_err_db_mean": realized_recon_peak_db,
            "note": "Virtual ground truth is a LABELED surrogate, not the FAU network.",
        },
        "truth": {"alpha": alpha_truth.tolist(), "beta": beta_truth.tolist(),
                  "gamma_over_gamma0": gamma_truth / core.GAMMA0},
        "deterministic": {"alpha": det["alpha"].tolist(), "beta": det["beta"].tolist(),
                          "gamma": det["gamma"], "cost": det["cost"]},
        "nuts_diagnostics": diag,
        "nuts_converged": bool(conv),
        "bayes_posterior": {
            "alpha": [nu.interval(np.exp(samples["log_alpha"][:, i])) for i in range(modes.nm)],
            "sigma_d": nu.interval(samples["sigma_d"]),
            "gamma": nu.interval(np.exp(samples["log_gamma"])),
        },
        "masked_channel_results": results_masked,
        "heldout_logmag_coverage": {
            "covered": cover_lines, "n": n_lines,
            "fraction": float(cover_lines / n_lines),
        },
        "heldout_hf_logmag_coverage": {
            "band_hz": [450.0, 900.0], "covered": cover_hf, "n": n_hf,
            "fraction": float(cover_hf / n_hf),
        },
        "det_masked_qoi_coverage": {
            "covered": int(sum(results_masked[c]["det_qoi_covers_truth"] for c in results_masked)),
            "n": len(results_masked),
        },
        "bayes_masked_qoi_coverage": {
            "covered": int(sum(bayes_cov_qoi)), "n": len(bayes_cov_qoi),
        },
    }
    json.dump(summary, open(OUT / "exp1_summary.json", "w"), indent=2)

    # ---- Figures ----
    paths = []
    # Fig 1: masked-channel reconstruction + the two updated predictions vs truth.
    fig, axs = plt.subplots(2, 1, figsize=(9.5, 7.6), sharex=True)
    for ax, c in zip(axs, core.MASKED):
        ax.plot(freqs, core.db(truth[:, c]), color=viz.C_TRUTH, lw=2.0, label="true masked (held out)")
        ax.plot(freqs, core.db(T["baseline"][:, c]), color=viz.C_BASE, lw=1.2, label="initial FEM baseline")
        ax.plot(freqs, core.db(virtual[:, c]), color="#e08e0b", lw=1.1, ls=":", label="virtual ground truth (surrogate)")
        ax.plot(freqs, core.db(det["H"][:, c]), color=viz.C_DET, lw=1.5, label="(A) deterministic update")
        lo = np.percentile(noisy[:, :, c], 2.5, axis=0)
        hi = np.percentile(noisy[:, :, c], 97.5, axis=0)
        ax.fill_between(freqs, 20 / np.log(10) * lo, 20 / np.log(10) * hi, color=viz.C_BAYES, alpha=0.20,
                        label="(B) Bayes 95% predictive")
        ax.set_ylabel(f"Ch{c+1} |H| [dB]")
        viz.style(ax)
    axs[0].legend(frameon=False, fontsize=7.5, ncol=2, loc="lower left")
    axs[1].set_xlabel("frequency [Hz], log scale")
    fig.suptitle("E1: masked-channel prediction - deterministic point vs discrepancy-aware band\n"
                 f"(NUTS R-hat {diag['max_rhat']:.3f}, ESS {diag['min_ess']:.0f}, div {diag['div_frac']:.3f})",
                 fontsize=11)
    paths.append(viz.save(fig, FIG / "exp1_masked_prediction.png"))

    # Fig 2: masked-channel peak QOI - deterministic point+meas-noise vs Bayes interval vs truth.
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    labels = list(results_masked.keys())
    x = np.arange(len(labels))
    for i, c in enumerate(labels):
        r = results_masked[c]
        ax.plot([x[i] - 0.12, x[i] - 0.12], r["det_qoi_interval_meas_noise"], color=viz.C_DET, lw=6, alpha=0.5,
                solid_capstyle="butt")
        ax.plot(x[i] - 0.12, r["qoi_det_point"], "o", color=viz.C_DET, ms=7)
        bi = r["bayes_qoi_interval"]
        ax.plot([x[i] + 0.12, x[i] + 0.12], [bi[0], bi[2]], color=viz.C_BAYES, lw=6, alpha=0.5, solid_capstyle="butt")
        ax.plot(x[i] + 0.12, bi[1], "o", color=viz.C_BAYES, ms=7)
        ax.plot(x[i], r["qoi_truth"], "x", color=viz.C_TRUTH, ms=12, mew=2.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("masked-channel peak |H| (QOI)")
    ax.set_yscale("log")
    viz.style(ax, logx=False)
    ax.text(0.02, 0.96, "red = (A) deterministic point +- meas noise   blue = (B) Bayes 95%   x = truth",
            transform=ax.transAxes, fontsize=8.5, va="top")
    ax.set_title("E1: held-out masked-channel peak QOI - does the interval cover truth?")
    paths.append(viz.save(fig, FIG / "exp1_qoi_coverage.png"))

    viz.image_qa(paths, ROOT / "image_qa_exp1.json")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
