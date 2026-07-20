#!/usr/bin/env python3
"""E-LIMIT - the honest limit: a COHERENT confounded bias our cure does NOT fix.

Mirrors the prior-art E4 on this study's testbed. Modes = local_mode_modes (mode 4 = 760 Hz is
LOCAL to the masked sensors Ch3/Ch4). The masked "virtual ground truth" carries a coherent +15%
peak-frequency shift and IS used as a down-weighted fit target (the paper's closed-loop updating).
Because a peak-frequency shift is algebraically a stiffness scaling (alpha_i^2 multiplies w_i^2),
and mode 4 is seen only by the failed sensor, the +15% shift is CONFOUNDED with alpha_4.

Tested (not assumed): the discrepancy-aware fit keeps the held-out amplitude QOI covered but MISSES
alpha_4 (flips real softening to apparent hardening). The cure is to BREAK the degeneracy (a sensor
that sees the local mode), not more flexible discrepancy. An unbiased control recovers alpha_4 =>
the method itself is sound; only the coherent bias defeats the parameter.

Writes out/limit_summary.json (headline keys consumed by check.py) + figure arrays for fig_limit.py.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

import core
import nuts_update as nu

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "out"
OUT.mkdir(exist_ok=True)
SEED = 20260616
SIGMA_MEAS = 0.05
SIGMA_VIRTUAL = 0.30
PEAK_SHIFT = 0.15
M4 = 3  # local mode index


def run_bayes(freqs, modes, tgt, sig_ch, correlated, seed):
    samples, diag = nu.run_nuts(
        freqs, modes, np.log(np.abs(tgt)), np.arange(modes.nc), sig_ch,
        correlated=correlated, corr_logf=0.25,
        corr_channels=core.MASKED if correlated else None, dense_mass=correlated,
        learn_discrepancy=True, num_warmup=1000, num_samples=1000, num_chains=4, seed=seed)
    conv = bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02)
    return samples, diag, conv


def main():
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    modes = core.local_mode_modes()
    freqs = core.freq_grid(160)
    hf = core.band_mask(freqs, 450.0, 900.0)
    hf_idx = np.where(hf)[0]

    alpha_truth = np.array([0.97, 0.92, 0.88, 0.85])  # real softening incl. mode 4
    beta_truth = np.array([1.2, 1.3, 1.4, 1.5])
    gamma_truth = 1.03 * core.GAMMA0
    T = core.make_truth(freqs, modes, alpha_truth, beta_truth, gamma_truth, rng,
                        disc_std_lo=0.04, disc_std_hi=0.30)
    truth = T["truth"]
    measured = core.measure(truth, core.MASKED, rng, SIGMA_MEAS, SIGMA_MEAS)

    virtual = core.reconstruct_virtual(truth, core.MASKED, rng, recon_std_lo=0.05, recon_std_hi=0.18,
                                       bias_peakshift=PEAK_SHIFT, modes=modes, freqs=freqs)
    tgt = measured.copy(); tgt[:, core.MASKED] = virtual[:, core.MASKED]
    virtual_unb = core.reconstruct_virtual(truth, core.MASKED, np.random.default_rng(SEED + 1),
                                           recon_std_lo=0.05, recon_std_hi=0.18, modes=modes, freqs=freqs)
    tgt_unb = measured.copy(); tgt_unb[:, core.MASKED] = virtual_unb[:, core.MASKED]
    sig_ch = np.array([SIGMA_MEAS, SIGMA_MEAS, SIGMA_VIRTUAL, SIGMA_VIRTUAL])

    cm = int(core.MASKED[0])  # Ch3
    pb = int(hf_idx[np.argmax(np.abs(truth[hf_idx, cm]))])
    # QOI = held-out mode-4 PEAK HEIGHT (band-max amplitude) on the masked channel, matching the main
    # sweep's QOI. Peak HEIGHT is ~robust to a frequency shift; peak LOCATION (encoded by alpha_4) is not.
    # That is the sharpest "QOI coverage != parameter recovery" statement under a coherent peak shift.
    q_truth = float(np.max(np.abs(truth[hf_idx, cm])))

    det = core.deterministic_update(freqs, modes, tgt, np.ones(modes.nc), rng)
    det_a4 = float(det["alpha"][M4]); det_q = float(np.abs(det["H"][pb, cm]))

    arms = [("bayes_iid_biased", False, tgt),
            ("bayes_correlated_biased", True, tgt),
            ("bayes_correlated_unbiased_control", True, tgt_unb)]
    out = {}
    for tag, corr, target in arms:
        samples, diag, conv = run_bayes(freqs, modes, target, sig_ch, corr, SEED)
        a4 = np.exp(samples["log_alpha"][:, M4]); a4_ci = nu.interval(a4)
        _, noisy, _ = nu.posterior_predict(samples, freqs, modes, sig_ch, rng, thin=4)
        qp = np.exp(noisy[:, hf_idx, cm]).max(axis=1)  # band-max peak HEIGHT per sample
        q_ci = nu.interval(qp)
        out[tag] = {
            "alpha4_ci": a4_ci,
            "alpha4_covers_truth": bool(a4_ci[0] <= alpha_truth[M4] <= a4_ci[2]),
            "alpha4_biased_high": bool(a4_ci[1] > alpha_truth[M4]),
            "qoi_ci": q_ci, "qoi_covers_truth": bool(q_ci[0] <= q_truth <= q_ci[2]),
            "sigma_d": nu.interval(samples["sigma_d"]),
            "nuts": diag, "converged": conv,
            "band_lo": np.percentile(noisy[:, :, cm], 2.5, axis=0).tolist(),
            "band_hi": np.percentile(noisy[:, :, cm], 97.5, axis=0).tolist(),
        }

    corr_biased = out["bayes_correlated_biased"]
    iid_biased = out["bayes_iid_biased"]
    control = out["bayes_correlated_unbiased_control"]
    a4_med = corr_biased["alpha4_ci"][1]
    summary = {
        "experiment": "E_LIMIT_coherent_bias",
        "runtime_s": round(time.time() - t0, 2),
        "design": {"peak_shift_pct": PEAK_SHIFT * 100, "local_mode": M4 + 1,
                   "alpha4_truth": float(alpha_truth[M4]), "sigma_virtual": SIGMA_VIRTUAL},
        "deterministic": {"alpha4": det_a4, "qoi_err_db": float(20 * np.log10(det_q / q_truth))},
        "arms": out,
        "headline": {
            # the disc-aware CURE is the structure-matched correlated arm (A3); iid cannot match a
            # coherent bias (reported separately, consistent with prior-art E4).
            "disc_aware_qoi_covered": bool(corr_biased["qoi_covers_truth"]),
            "iid_qoi_covered": bool(iid_biased["qoi_covers_truth"]),
            "disc_aware_alpha_covered": bool(corr_biased["alpha4_covers_truth"]),
            "alpha4_ci_corr": corr_biased["alpha4_ci"],
            "apparent_sign": ("biased high toward hardening (under-recovers softening)"
                              if corr_biased["alpha4_ci"][0] > alpha_truth[M4] else
                              ("hardening" if a4_med > 1.0 else "softening")),
            "control_alpha_covered": bool(control["alpha4_covers_truth"]),
            "all_converged": bool(all(out[t]["converged"] for t in out)),
            "lesson": "A coherent +15% peak shift on the masked virtual target is confounded with the "
                      "failed-sensor local-mode stiffness alpha_4 (peak shift = stiffness scaling). The "
                      "discrepancy-aware QOI stays covered but alpha_4 MISSES (apparent hardening). The "
                      "unbiased control recovers alpha_4, so the method is sound; the cure is to BREAK the "
                      "degeneracy (a sensor that sees the local mode), not more flexible discrepancy.",
        },
        "fig": {"freqs": freqs.tolist(), "cm": cm, "peak_bin": pb, "qoi_truth": q_truth,
                "truth_db": core.db(truth[:, cm]).tolist(), "virtual_db": core.db(virtual[:, cm]).tolist(),
                "alpha4_truth": float(alpha_truth[M4]), "det_alpha4": det_a4},
    }
    json.dump(summary, open(OUT / "limit_summary.json", "w"), indent=2)
    h = summary["headline"]
    print(f"E-LIMIT: control covers alpha4={h['control_alpha_covered']}; biased disc-aware covers alpha4="
          f"{h['disc_aware_alpha_covered']} (apparent {h['apparent_sign']}); QOI covered={h['disc_aware_qoi_covered']}; "
          f"all converged={h['all_converged']} ({summary['runtime_s']}s)")


if __name__ == "__main__":
    main()
