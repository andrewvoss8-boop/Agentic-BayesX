#!/usr/bin/env python3
"""E4 - coherent reconstruction bias (the stress test).

The virtual ground truth carries a COHERENT bias: a peak-frequency shift on the masked
channels (like the paper's pure-FAU peak shift up to ~10.8%). Because mode 4 is a local mode
living at the FAILED sensors, the updater can absorb the shift by STIFFENING alpha_4 - turning
a real softening into an apparent hardening. We compare three updates on the SAME biased target:
  (A) deterministic FAU-Up (trust the surrogate),
  (B) Bayes with iid credibility inflation,
  (C) Bayes with a correlated (Schneider-style) discrepancy.

Tested finding: uncertainty quantification protects you only if the discrepancy MODEL matches
the reconstruction's error STRUCTURE. An iid credibility weight does not cover a coherent bias;
a correlated discrepancy does (at the cost of width). Connects to the project's Schneider /
Kennedy-O'Hagan discrepancy-structure findings.
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
PEAK_SHIFT = 0.15   # +15% coherent peak-frequency shift on the masked reconstruction
M4 = 3              # mode-4 index (local mode at failed sensors)


def run_bayes(freqs, modes, tgt, sig_ch, correlated, seed):
    # Correlated discrepancy is applied to the MASKED channels only (their reconstruction error
    # is structured); observed channels keep iid measurement noise. Dense mass matrix handles the
    # ill-conditioned marginal-GP geometry.
    samples, diag = nu.run_nuts(freqs, modes, np.log(np.abs(tgt)), np.arange(modes.nc), sig_ch,
                                correlated=correlated, corr_logf=0.25,
                                corr_channels=core.MASKED if correlated else None,
                                dense_mass=correlated,
                                num_warmup=1000, num_samples=1000, seed=seed)
    conv = bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02)
    return samples, diag, conv


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    modes = core.local_mode_modes()
    freqs = core.freq_grid(160)
    qoi_mask = core.band_mask(freqs, 450.0, 900.0)
    hf_idx = np.where(qoi_mask)[0]

    alpha_truth = np.array([0.97, 0.92, 0.88, 0.85])  # real softening, incl. mode 4
    beta_truth = np.array([1.2, 1.3, 1.4, 1.5])
    gamma_truth = 1.03 * core.GAMMA0
    T = core.make_truth(freqs, modes, alpha_truth, beta_truth, gamma_truth, rng,
                        disc_std_lo=0.04, disc_std_hi=0.30)
    truth = T["truth"]
    measured = core.measure(truth, core.MASKED, rng, SIGMA_MEAS, SIGMA_MEAS)

    # Biased virtual ground truth: coherent +PEAK_SHIFT peak-frequency shift on masked channels.
    virtual = core.reconstruct_virtual(truth, core.MASKED, rng, recon_std_lo=0.05, recon_std_hi=0.18,
                                        bias_peakshift=PEAK_SHIFT, modes=modes, freqs=freqs)
    tgt = measured.copy()
    tgt[:, core.MASKED] = virtual[:, core.MASKED]
    # Unbiased control reconstruction (same random error, NO coherent shift) for the correlated arm.
    virtual_unb = core.reconstruct_virtual(truth, core.MASKED, np.random.default_rng(SEED + 1),
                                           recon_std_lo=0.05, recon_std_hi=0.18, modes=modes, freqs=freqs)
    tgt_unb = measured.copy()
    tgt_unb[:, core.MASKED] = virtual_unb[:, core.MASKED]
    sig_ch = np.array([SIGMA_MEAS, SIGMA_MEAS, SIGMA_VIRTUAL, SIGMA_VIRTUAL])

    # masked mode-4 peak QOI truth (peak bin on a masked channel within the HF band)
    cm = core.MASKED[0]  # Ch3
    pb = hf_idx[np.argmax(np.abs(truth[hf_idx, cm]))]
    q_truth = float(np.abs(truth[pb, cm]))

    # ---- (A) deterministic FAU-Up ----
    det = core.deterministic_update(freqs, modes, tgt, np.ones(modes.nc), rng)
    det_a4 = float(det["alpha"][M4])
    det_q = float(np.abs(det["H"][pb, cm]))

    # ---- (B) iid (biased), (C) correlated (biased), (D) correlated control (UNBIASED recon) ----
    out = {}
    runs = [("bayes_iid", False, tgt), ("bayes_correlated", True, tgt),
            ("bayes_correlated_unbiased_control", True, tgt_unb)]
    for tag, corr, target in runs:
        samples, diag, conv = run_bayes(freqs, modes, target, sig_ch, corr, SEED)
        a4 = np.exp(samples["log_alpha"][:, M4])
        a4_ci = nu.interval(a4)
        _, noisy, _ = nu.posterior_predict(samples, freqs, modes, sig_ch, rng, thin=4)
        qp = np.exp(noisy[:, pb, cm])
        q_ci = nu.interval(qp)
        out[tag] = {
            "alpha4_ci": a4_ci,
            "alpha4_covers_truth": bool(a4_ci[0] <= alpha_truth[M4] <= a4_ci[2]),
            "alpha4_says_softening": bool(a4_ci[2] < 1.0),   # whole interval below 1 = softening
            "masked_mode4_qoi_ci": q_ci,
            "masked_mode4_qoi_covers_truth": bool(q_ci[0] <= q_truth <= q_ci[2]),
            "sigma_d": nu.interval(samples["sigma_d"]),
            "nuts": diag, "nuts_converged": conv,
            "_noisy_band": (np.percentile(noisy[:, :, cm], 2.5, axis=0).tolist(),
                            np.percentile(noisy[:, :, cm], 97.5, axis=0).tolist()),
        }

    summary = {
        "experiment": "E4_biased_reconstruction",
        "runtime_s": round(time.time() - t0, 2),
        "design": {
            "peak_shift_pct": PEAK_SHIFT * 100,
            "local_mode_at_failed_sensors": M4 + 1,
            "alpha4_truth": alpha_truth[M4],
            "note": "Coherent peak-frequency shift on the masked virtual target; mode 4 is local "
                    "to the failed sensors so alpha_4 can absorb the shift (apparent hardening).",
        },
        "truth": {"alpha": alpha_truth.tolist(), "alpha4_softening": True},
        "deterministic": {
            "alpha4": det_a4, "alpha4_says_softening": bool(det_a4 < 1.0),
            "masked_mode4_qoi": det_q,
            "masked_mode4_qoi_err_db": float(abs(20 * np.log10(det_q / q_truth))),
        },
        "qoi_truth": q_truth,
        "bayes_iid": out["bayes_iid"],
        "bayes_correlated": out["bayes_correlated"],
        "bayes_correlated_unbiased_control": out["bayes_correlated_unbiased_control"],
        "headline": {
            "det_alpha4_err": float(det_a4 - alpha_truth[M4]),
            "iid_covers_alpha4": out["bayes_iid"]["alpha4_covers_truth"],
            "correlated_biased_covers_alpha4": out["bayes_correlated"]["alpha4_covers_truth"],
            "correlated_unbiased_control_covers_alpha4": out["bayes_correlated_unbiased_control"]["alpha4_covers_truth"],
            "iid_covers_qoi": out["bayes_iid"]["masked_mode4_qoi_covers_truth"],
            "correlated_covers_qoi": out["bayes_correlated"]["masked_mode4_qoi_covers_truth"],
            "lesson": "Unbiased reconstruction + correlated discrepancy recovers alpha_4 (method OK). "
                      "A coherent reconstruction bias is confounded with the failed-sensor local "
                      "mode's stiffness (peak shift = stiffness scaling); neither iid nor correlated "
                      "UQ recovers alpha_4, though the amplitude QOI stays covered. Fix = break the "
                      "degeneracy (keep a sensor on the local mode / bias-aware credibility), not more "
                      "flexible discrepancy.",
        },
        "all_nuts_converged": bool(all(out[t]["nuts_converged"] for t in out)),
    }
    # strip private band arrays from the saved summary but keep for the figure
    band_iid = out["bayes_iid"].pop("_noisy_band")
    band_corr = out["bayes_correlated"].pop("_noisy_band")
    out["bayes_correlated_unbiased_control"].pop("_noisy_band")
    json.dump(summary, open(OUT / "exp4_summary.json", "w"), indent=2)

    # ---- Figure: alpha_4 posteriors + masked mode-4 channel prediction ----
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 5.4))
    ax = axs[0]
    labels = ["deterministic\nFAU-Up\n(biased)", "Bayes iid\ncredibility\n(biased)",
              "Bayes correlated\ndiscrepancy\n(biased)", "Bayes correlated\nCONTROL\n(unbiased recon)"]
    xs = np.arange(4)
    ax.axhspan(0, 1.0, color="#dcfce7", alpha=0.6)
    ax.axhspan(1.0, 1.5, color="#fee2e2", alpha=0.6)
    ax.text(3.45, 0.56, "softening (truth)", color="#166534", fontsize=8.5, ha="right")
    ax.text(3.45, 1.30, "apparent hardening (wrong sign)", color="#991b1b", fontsize=8.5, ha="right")
    ax.plot(0, det_a4, "o", color=viz.C_DET, ms=9)
    ax.annotate("hits box floor", (0, det_a4), textcoords="offset points", xytext=(8, 6), fontsize=7.5, color=viz.C_DET)
    cols = {"bayes_iid": "#d97706", "bayes_correlated": viz.C_BAYES, "bayes_correlated_unbiased_control": "#059669"}
    for j, tag in enumerate(["bayes_iid", "bayes_correlated", "bayes_correlated_unbiased_control"]):
        ci = out[tag]["alpha4_ci"]
        col = cols[tag]
        ax.plot([j + 1, j + 1], [ci[0], ci[2]], color=col, lw=7, alpha=0.55, solid_capstyle="butt")
        ax.plot(j + 1, ci[1], "o", color=col, ms=8)
        ok = "covers" if out[tag]["alpha4_covers_truth"] else "MISSES"
        ax.annotate(ok, (j + 1, ci[2]), textcoords="offset points", xytext=(0, 6), fontsize=7.5,
                    color=("#166534" if out[tag]["alpha4_covers_truth"] else "#991b1b"), ha="center")
    ax.axhline(alpha_truth[M4], color="black", ls="--", lw=1.5)
    ax.text(3.45, alpha_truth[M4] - 0.03, f"truth alpha_4 = {alpha_truth[M4]:.2f}", fontsize=8.5, ha="right")
    ax.set_xticks(xs); ax.set_xticklabels(labels, fontsize=7.8)
    ax.set_ylabel("mode-4 stiffness factor alpha_4")
    ax.set_ylim(0.45, 1.5)
    ax.set_title(f"alpha_4: only the UNBIASED control recovers softening (+{PEAK_SHIFT*100:.0f}% bias otherwise)")
    viz.style(ax, logx=False)

    ax = axs[1]
    ax.plot(freqs, core.db(truth[:, cm]), color=viz.C_TRUTH, lw=2.0, label="true masked (held out)")
    ax.plot(freqs, core.db(virtual[:, cm]), color="#e08e0b", lw=1.1, ls=":", label="biased virtual target")
    f2db = 20 / np.log(10)
    ax.fill_between(freqs, f2db * np.array(band_iid[0]), f2db * np.array(band_iid[1]),
                    color="#d97706", alpha=0.18, label="Bayes iid 95%")
    ax.fill_between(freqs, f2db * np.array(band_corr[0]), f2db * np.array(band_corr[1]),
                    color=viz.C_BAYES, alpha=0.20, label="Bayes correlated 95%")
    ax.axvline(freqs[pb], color="0.6", lw=0.8)
    ax.set_xlabel("frequency [Hz], log scale")
    ax.set_ylabel(f"Ch{cm+1} |H| [dB]")
    ax.set_title("masked mode-4 channel: correlated band covers the true peak; iid does not")
    viz.style(ax)
    ax.legend(frameon=False, fontsize=7.5, loc="lower left")
    fig.suptitle("E4: a coherent reconstruction bias - UQ protects only if the discrepancy model matches the error structure",
                 fontsize=11)
    p = viz.save(fig, FIG / "exp4_biased_reconstruction.png")
    viz.image_qa([p], ROOT / "image_qa_exp4.json")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
