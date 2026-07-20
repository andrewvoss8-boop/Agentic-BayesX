#!/usr/bin/env python3
"""Sharpness-aware held-out-QOI scoring (NEW file; imports the copied predict/core, does NOT edit them).

The companion's `lenmis` arm scored coverage 1.00 purely by widening σ_d toward the prior (a wide-band FALSE
win). Coverage alone is foolable by width. This module adds scores that PENALISE width, so a plateau/cure
cannot be faked by inflating bands:

  - Interval score IS_α (Gneiting & Raftery 2007), central (1-α)=95% interval [l,u], α=0.05, in dB:
        IS = (u-l) + (2/α)(l-y)·1{y<l} + (2/α)(y-u)·1{y>u}        (lower = better; width + miscoverage)
  - CRPS (continuous ranked probability score), empirical from m predictive draws x and truth y, in dB:
        CRPS = mean_i|x_i - y| - 0.5 * mean_{i,j}|x_i - x_j|       (lower = better)
  - PIT (probability integral transform) = fraction of predictive draws ≤ truth, per held-out sensor;
        a calibrated predictive has PITs ~ Uniform(0,1). We report the KS distance from uniform.

QOI scored = the held-out PEAK accelerance, in dB (20·log10|H|), the decision-relevant quantity; the band-GRMS
QOI is reported alongside. Held-out discrepancy draws come from the copied `predict.PredCtx.krige` (M2/M3),
marginal iid (M1), or zero (M0) — IDENTICAL mechanism to predict.py, just retained so we can score the draws.
"""
from __future__ import annotations

import numpy as np

import core
import predict as pr

ALPHA = 0.05   # 95% central interval


def _interval_score(draws_db, y_db, alpha=ALPHA):
    lo, hi = np.percentile(draws_db, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    s = (hi - lo)
    if y_db < lo:
        s += (2.0 / alpha) * (lo - y_db)
    elif y_db > hi:
        s += (2.0 / alpha) * (y_db - hi)
    return s, (hi - lo), bool(lo <= y_db <= hi)


def _crps(draws_db, y_db):
    x = np.sort(np.asarray(draws_db))
    m = len(x)
    term1 = np.mean(np.abs(x - y_db))
    # E|X - X'| via sorted-array identity: mean_{i,j}|x_i-x_j| = (2/m^2) Σ_i (2i-m+1) x_i  (i 0-based)
    i = np.arange(m)
    ex = (2.0 / (m * m)) * np.sum((2 * i - m + 1) * x)
    return term1 - 0.5 * ex


def _pit(draws_db, y_db):
    return float(np.mean(np.asarray(draws_db) <= y_db))


def _ks_uniform(pits):
    p = np.sort(np.asarray(pits))
    n = len(p)
    if n == 0:
        return None
    cdf_lo = np.arange(n) / n
    cdf_hi = np.arange(1, n + 1) / n
    return float(np.max(np.maximum(np.abs(p - cdf_lo), np.abs(p - cdf_hi))))


def score_cell(ctx: pr.PredCtx, samples, truth_logmag_ho, truth_logmag_obs, n_draws=400, seed=7):
    """Generate held-out PEAK/BAND QOI predictive draws (same mechanism as predict.predict_cell) and score
    them with interval-score / CRPS / PIT (in dB), plus coverage + mean 95% width.

    truth_logmag_ho/obs: clean-truth log|H| on held-out / observed channels (Nf, Ns)."""
    rng = np.random.default_rng(seed)
    model, freqs = ctx.model, ctx.freqs
    th_all = samples["log_theta"]
    n = th_all.shape[0]
    idx = np.linspace(0, n - 1, min(n, n_draws)).astype(int)
    sd_all = np.asarray(samples.get("sigma_d", np.zeros(n)))
    arm = ctx.arm
    Ns_h = ctx.Ns_h

    peak_db = np.zeros((len(idx), Ns_h))
    band_db = np.zeros((len(idx), Ns_h))
    for j, s in enumerate(idx):
        theta = np.exp(th_all[s])
        sd = float(sd_all[s])
        lm_obs = np.log(np.abs(core.frf_np(model, freqs, theta, ctx.observed, ctx.drive, zeta=ctx.zeta)))
        lm_ho = np.log(np.abs(core.frf_np(model, freqs, theta, ctx.heldout, ctx.drive, zeta=ctx.zeta)))
        R_o = truth_logmag_obs - lm_obs
        if arm == "M0":
            d_h = np.zeros_like(lm_ho)
        elif arm == "M1":
            d_h = rng.normal(0, sd, lm_ho.shape)
        else:
            _, d_h = ctx.krige(R_o, sd, rng)
        pred = lm_ho + d_h
        for c in range(Ns_h):
            mag = np.exp(pred[:, c])
            peak_db[j, c] = core.db(core.qoi_peak(mag))
            band_db[j, c] = core.db(core.qoi_band(mag, freqs))

    truth_mag = np.exp(truth_logmag_ho)
    out = {}
    for label, draws in (("peak", peak_db), ("band", band_db)):
        IS = []; CR = []; W = []; COV = []; PIT = []
        for c in range(Ns_h):
            if label == "peak":
                y = core.db(core.qoi_peak(truth_mag[:, c]))
            else:
                y = core.db(core.qoi_band(truth_mag[:, c], freqs))
            isc, w, cov = _interval_score(draws[:, c], y)
            IS.append(isc); W.append(w); COV.append(cov)
            CR.append(_crps(draws[:, c], y)); PIT.append(_pit(draws[:, c], y))
        out[label] = {"interval_score_db": float(np.mean(IS)), "crps_db": float(np.mean(CR)),
                      "coverage": float(np.mean(COV)), "width_db": float(np.mean(W)),
                      "pit_ks": _ks_uniform(PIT), "n_heldout": Ns_h}
    # top-level SCORE_FIELDS = the decision-relevant PEAK QOI; band kept under out["band"]
    top = dict(out["peak"]); top["band"] = out["band"]
    return top
