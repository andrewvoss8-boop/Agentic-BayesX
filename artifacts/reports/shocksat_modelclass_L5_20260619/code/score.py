#!/usr/bin/env python3
"""Sharpness-aware scoring suite (Card A §5). The HEADLINE is a PROPER scoring rule (interval/Winkler score,
CRPS, log predictive density) that jointly rewards CALIBRATION and SHARPNESS, so a method cannot win by
inflating its bands. Coverage + width are kept as SECONDARY diagnostics. The whole-FRF score is PEAK-WEIGHTED
(missing a peak >> missing a valley) and coherence/quality-weighted.

All functions take an ensemble of predictive samples (draws of the predicted quantity) and the (real measured)
truth. Lower interval-score / CRPS = better; higher log-density = better. PIT≈Uniform and z≈N(0,1) = calibrated.
"""
from __future__ import annotations
import numpy as np


# ---------------------------------------------------------------- proper scores (per scalar QOI)
def interval_score(samples, truth, alpha=0.05):
    """Winkler interval score for the central (1-alpha) predictive interval. Penalizes width PLUS
    2/alpha * (how far truth falls outside). Lower = better (sharp AND calibrated)."""
    lo, hi = np.percentile(samples, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    s = (hi - lo)
    if truth < lo:
        s += (2.0 / alpha) * (lo - truth)
    elif truth > hi:
        s += (2.0 / alpha) * (truth - hi)
    return float(s)


def crps_sample(samples, truth):
    """Empirical CRPS = E|X - y| - 0.5 E|X - X'|  (proper; lower = better). O(n log n) via sorting."""
    x = np.sort(np.asarray(samples, float))
    n = len(x)
    e1 = np.mean(np.abs(x - truth))
    # E|X-X'| = 2/n^2 * sum_i (2i-n+1) x_i  (sorted)
    i = np.arange(1, n + 1)
    e2 = (2.0 / n ** 2) * np.sum((2 * i - n - 1) * x)
    return float(e1 - 0.5 * e2)


def log_predictive_density(samples, truth, bw=None):
    """Log predictive density at truth via a Gaussian kernel density estimate of the ensemble (higher=better).
    Robust to non-Gaussian / multimodal predictive (which we expect)."""
    x = np.asarray(samples, float)
    n = len(x); sd = x.std()
    if sd <= 0:
        sd = 1e-6
    h = bw if bw is not None else 1.06 * sd * n ** (-1 / 5)        # Silverman
    h = max(h, 1e-9)
    z = (truth - x) / h
    logk = -0.5 * z ** 2 - np.log(h) - 0.5 * np.log(2 * np.pi)
    m = logk.max()
    return float(m + np.log(np.mean(np.exp(logk - m))))


def pit(samples, truth):
    """Probability integral transform = predictive CDF at truth (~Uniform(0,1) if calibrated; near 0/1 = truth
    at an edge of the predictive)."""
    return float(np.mean(np.asarray(samples) <= truth))


def z_standardized(samples, truth):
    med = np.median(samples); sd = np.std(samples)
    return float((truth - med) / sd) if sd > 0 else np.nan


def coverage_width(samples, truth, alpha=0.05):
    lo, hi = np.percentile(samples, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"covered": bool(lo <= truth <= hi), "lo": float(lo), "hi": float(hi),
            "width": float(hi - lo), "width_db": float(20 * np.log10(max(hi, 1e-30) / max(lo, 1e-30)))}


def score_qoi(samples, truth, alpha=0.05):
    """Full per-QOI scorecard: proper scores (headline) + PIT/z + coverage/width (secondary)."""
    return {"interval_score": interval_score(samples, truth, alpha),
            "crps": crps_sample(samples, truth),
            "logpd": log_predictive_density(samples, truth),
            "pit": pit(samples, truth), "z": z_standardized(samples, truth),
            **coverage_width(samples, truth, alpha)}


# ---------------------------------------------------------------- whole-FRF peak-weighted score
def peak_weight(mag_truth, freqs, kind="peak", power=2.0):
    """Asymmetric weight over frequency: emphasize PEAKS (high |H|) so missing a peak costs far more than
    missing a valley. weight ∝ (|H|/max|H|)^power, normalized to mean 1."""
    m = np.abs(mag_truth)
    w = (m / max(m.max(), 1e-30)) ** power
    return w / max(w.mean(), 1e-30)


def frf_score(pred_logmag_samples, truth_logmag, freqs, qual_weight=None, peak_power=2.0, alpha=0.05):
    """Peak-weighted + quality-weighted whole-FRF proper score. pred_logmag_samples: (n_draws, Nf) predictive
    log|H| for ONE channel; truth_logmag: (Nf,) measured log|H|. Returns the per-frequency interval score
    averaged with peak+quality weights, plus band GRMS error and peak-frequency error."""
    nd, Nf = pred_logmag_samples.shape
    pw = peak_weight(np.exp(truth_logmag), freqs, power=peak_power)
    qw = np.ones(Nf) if qual_weight is None else np.asarray(qual_weight)
    w = pw * qw
    w = w / max(w.sum(), 1e-30)
    # per-frequency interval score on the magnitude (work in log to compress peaks, consistent w/ likelihood)
    per_f = np.array([interval_score(pred_logmag_samples[:, k], truth_logmag[k], alpha) for k in range(Nf)])
    weighted_is = float(np.sum(w * per_f))
    # band GRMS (energy) on the predictive median vs truth
    med = np.exp(np.median(pred_logmag_samples, axis=0))
    grms_pred = np.sqrt(np.trapz(med ** 2, freqs)); grms_truth = np.sqrt(np.trapz(np.exp(truth_logmag) ** 2, freqs))
    # peak-frequency error: argmax frequency of predictive-median vs truth
    pf_pred = freqs[int(np.argmax(med))]; pf_truth = freqs[int(np.argmax(np.exp(truth_logmag)))]
    return {"weighted_interval_score": weighted_is,
            "grms_pred": float(grms_pred), "grms_truth": float(grms_truth),
            "grms_rel_err": float(grms_pred / max(grms_truth, 1e-30) - 1),
            "peak_freq_pred_hz": float(pf_pred), "peak_freq_truth_hz": float(pf_truth),
            "peak_freq_err_hz": float(abs(pf_pred - pf_truth))}


def aggregate_pit_z(pits, zs):
    """Calibration summary over many held-out QOIs: PIT should be ~Uniform, z ~ N(0,1).
    Report KS-like deviation of PIT from uniform + mean/std of z."""
    pits = np.asarray(pits); zs = np.asarray(zs)
    p = np.sort(pits); n = len(p)
    ks = float(np.max(np.abs(p - (np.arange(1, n + 1) - 0.5) / n))) if n else np.nan
    return {"pit_ks_dev": ks, "pit_mean": float(np.mean(pits)) if n else np.nan,
            "z_mean": float(np.mean(zs)) if len(zs) else np.nan,
            "z_std": float(np.std(zs)) if len(zs) else np.nan}


def wideband_demo(seed=0, n_truth=3000, n_samp=4000):
    """Show the proper score is NOT foolable by width: averaged over truths drawn from the TRUE distribution
    N(1,0.2), a WIDE predictive N(1,2.0) wins COVERAGE but LOSES the proper score (interval + CRPS). Writes
    out/wideband_demo.json (checker gate). The held-out-QOI suite uses these same proper scores."""
    import json
    from pathlib import Path
    rng = np.random.default_rng(seed)
    truths = rng.normal(1.0, 0.2, n_truth)
    sharp = rng.normal(1.0, 0.2, n_samp)        # correctly calibrated
    wide = rng.normal(1.0, 2.0, n_samp)         # band-inflated
    b_cov = np.mean([coverage_width(sharp, t)["covered"] for t in truths])
    w_cov = np.mean([coverage_width(wide, t)["covered"] for t in truths])
    b_is = np.mean([interval_score(sharp, t) for t in truths])
    w_is = np.mean([interval_score(wide, t) for t in truths])
    b_crps = np.mean([crps_sample(sharp, t) for t in truths])
    w_crps = np.mean([crps_sample(wide, t) for t in truths])
    rec = {"base_coverage": float(b_cov), "wide_coverage": float(w_cov),
           "base_interval_score": float(b_is), "wide_interval_score": float(w_is),
           "base_crps": float(b_crps), "wide_crps": float(w_crps),
           "coverage_up_but_score_worse": bool(w_cov > b_cov and w_is > b_is and w_crps > b_crps),
           "note": "averaged over truths ~ N(1,0.2); wide N(1,2.0) covers more but scores worse (proper)."}
    p = Path(__file__).resolve().parent.parent / "out" / "wideband_demo.json"
    p.parent.mkdir(exist_ok=True); p.write_text(json.dumps(rec, indent=2))
    print(f"WIDE-DOESN'T-WIN: coverage {b_cov:.2f}->{w_cov:.2f} (up) but interval {b_is:.2f}->{w_is:.2f} and "
          f"CRPS {b_crps:.3f}->{w_crps:.3f} (worse) | coverage_up_but_score_worse={rec['coverage_up_but_score_worse']}")
    return rec


if __name__ == "__main__":
    wideband_demo()
