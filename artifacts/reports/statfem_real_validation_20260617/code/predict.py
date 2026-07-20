#!/usr/bin/env python3
"""Held-out-sensor QOI posterior predictive + coverage (the trust test).

For each posterior draw (theta, sigma_d):
  - model FRF at observed + held-out sensors (eigh-resolvent, numpy);
  - observed residual r_o = log|H_meas_obs| - log|H_model_obs(theta)|;
  - held-out discrepancy d_h:
      M0  : none (sigma_d = 0)                                  -> confidently wrong if theta misses
      M1  : marginal iid N(0, sigma_d^2) (NO spatial transfer)  -> wide, uninformed
      M2/3: GP-CONDITIONAL on r_o using the Schneider freq x space covariance (kriging) -> informed
  - predicted held-out log|H| = log|H_model_h| + d_h; QOI(peak, band) per held-out sensor.

Spatial conditioning is decoupled over the FREQUENCY eigenbasis (C_f shared across sensors; U_f^T preserves
iid measurement noise), so each freq-eigenmode is a small Ns x Ns spatial GP -> fully vectorised over freq.

Coverage = fraction of held-out CLEAN-truth QOI values inside the 95% predictive interval (latent-QOI
coverage, the structural-property trust metric); a noisy-observation coverage is also reported.
"""
from __future__ import annotations

import numpy as np

import core
import nuts_arms as na


class PredCtx:
    """Fixed (theta-independent) pieces for held-out prediction."""

    def __init__(self, model, freqs, observed, heldout, drive, arm,
                 zeta=core.ZETA_NOM, sigma_meas=core.SIGMA_MEAS,
                 len_logf=core.DISC_LEN_LOGF, len_z=core.DISC_LEN_Z):
        self.model = model
        self.freqs = freqs
        self.observed = np.asarray(observed)
        self.heldout = np.asarray(heldout)
        self.drive = drive
        self.arm = arm
        self.zeta = zeta
        self.sigma_meas = sigma_meas
        # frequency correlation eigenbasis (shared)
        Cf = na.corr_freq(freqs, len_logf)
        self.lam_f, self.U_f = np.linalg.eigh(Cf)
        self.lam_f = np.clip(self.lam_f, 0.0, None)
        # spatial correlation blocks over observed/held-out
        co = model.dof_xyz[self.observed]
        ch = model.dof_xyz[self.heldout]
        self.Czoo = na.corr_space(co, len_z)
        self.Czhh = na.corr_space(ch, len_z)
        # C_z_ho (held x obs)
        d = np.sqrt(((ch[:, None, :] - co[None, :, :]) ** 2).sum(-1))
        self.Czho = np.exp(-np.abs(d) / len_z)
        self.lam_o, self.U_o = np.linalg.eigh(self.Czoo)
        self.lam_o = np.clip(self.lam_o, 0.0, None)
        self.Ns_h = len(self.heldout)

    def krige(self, R_o, sigma_d, rng):
        """Return (d_h_mean, d_h_sample) each (Nf, Ns_h): conditional mean + one field sample of the
        held-out discrepancy given observed residual R_o (Nf, Ns_o), Schneider freq x space covariance.
        Decoupled over the frequency eigenbasis (U_f preserves iid noise); vectorised over freq."""
        sd2 = sigma_d ** 2
        if sd2 <= 0:
            z = np.zeros((len(self.freqs), self.Ns_h))
            return z, z
        Czoh = self.Czho.T                                   # (Ns_o, Ns_h)
        # whiten frequency, then work in the observed spatial eigenbasis Czoo = U_o Lam_o U_o^T
        At = (self.U_f.T @ R_o) @ self.U_o                   # (Nf, Ns_o), freq- & space-eigenbasis
        denom = sd2 * self.lam_f[:, None] * self.lam_o[None, :] + self.sigma_meas ** 2  # (Nf, Ns_o)
        w = (At / denom) @ self.U_o.T                        # Sigma_oo^-1 r_o in sensor basis, (Nf, Ns_o)
        mean_t = (sd2 * self.lam_f[:, None]) * (w @ self.Czho.T)   # (Nf, Ns_h), freq-eigenbasis
        # batched conditional spatial covariance per freq-eigenmode m:
        #   Soo_inv[m] = U_o diag(1/denom[m]) U_o^T
        #   cov[m] = sd2 lam_f[m] Czhh - (sd2 lam_f[m])^2 Czho Soo_inv[m] Czoh
        Soo_inv = np.einsum("oi,mi,pi->mop", self.U_o, 1.0 / denom, self.U_o)          # (Nf, Ns_o, Ns_o)
        term = np.einsum("hi,mij,jk->mhk", self.Czho, Soo_inv, Czoh)                   # (Nf, Ns_h, Ns_h)
        s = (sd2 * self.lam_f)                                                          # (Nf,)
        cov = s[:, None, None] * self.Czhh[None] - (s ** 2)[:, None, None] * term       # (Nf, Ns_h, Ns_h)
        cov = 0.5 * (cov + np.swapaxes(cov, 1, 2)) + 1e-9 * np.eye(self.Ns_h)[None]
        try:
            L = np.linalg.cholesky(cov)
        except np.linalg.LinAlgError:
            ev, eV = np.linalg.eigh(cov)
            L = eV @ (np.sqrt(np.clip(ev, 0, None))[:, None, :] * np.eye(self.Ns_h)[None])
        smp_t = mean_t + np.einsum("mhk,mk->mh", L, rng.standard_normal(mean_t.shape))
        return self.U_f @ mean_t, self.U_f @ smp_t


def predict_cell(ctx: PredCtx, samples, truth_logmag_ho, truth_logmag_obs, gnames, theta_truth,
                 informed_groups, n_draws=400, seed=7):
    """Compute held-out QOI intervals + coverage + theta recovery + sigma_d.
    truth_logmag_ho/obs: clean-truth log|H| on held-out / observed channels (Nf, Ns)."""
    rng = np.random.default_rng(seed)
    model, freqs = ctx.model, ctx.freqs
    bmask = np.ones(len(freqs), bool)
    th_all = samples["log_theta"]
    n = th_all.shape[0]
    idx = np.linspace(0, n - 1, min(n, n_draws)).astype(int)
    sd_all = samples.get("sigma_d", np.zeros(n))
    arm = ctx.arm

    truth_obs_meas = truth_logmag_obs  # observed target used in calibration was noisy; here we krige on the
    # SAME observed target the sampler saw (passed in as truth_logmag_obs = the measured observed log-mag)

    Ns_h = ctx.Ns_h
    # accumulators: predictive QOI samples per held-out sensor
    peak_draws = np.zeros((len(idx), Ns_h))
    band_draws = np.zeros((len(idx), Ns_h))
    peak_draws_noisy = np.zeros((len(idx), Ns_h))
    band_draws_noisy = np.zeros((len(idx), Ns_h))
    for j, s in enumerate(idx):
        theta = np.exp(th_all[s])
        sd = float(sd_all[s])
        lm_obs = np.log(np.abs(core.frf_np(model, freqs, theta, ctx.observed, ctx.drive, zeta=ctx.zeta)))
        lm_ho = np.log(np.abs(core.frf_np(model, freqs, theta, ctx.heldout, ctx.drive, zeta=ctx.zeta)))
        R_o = truth_obs_meas - lm_obs
        if arm == "M0":
            d_h = np.zeros_like(lm_ho)
        elif arm == "M1":
            d_h = rng.normal(0, sd, lm_ho.shape)             # marginal iid, no spatial transfer
        else:  # M2/M3 kriging
            _, d_h = ctx.krige(R_o, sd, rng)
        pred = lm_ho + d_h                                   # latent predicted log|H_ho|
        noisy = pred + rng.normal(0, ctx.sigma_meas, pred.shape)
        for c in range(Ns_h):
            mag = np.exp(pred[:, c])
            peak_draws[j, c] = core.qoi_peak(mag)
            band_draws[j, c] = core.qoi_band(mag, freqs)
            magn = np.exp(noisy[:, c])
            peak_draws_noisy[j, c] = core.qoi_peak(magn)
            band_draws_noisy[j, c] = core.qoi_band(magn, freqs)

    # truth QOI per held-out sensor
    truth_mag = np.exp(truth_logmag_ho)
    qoi = {}
    cov_peak = cov_band = cov_peak_n = cov_band_n = 0
    widths = []
    for c in range(Ns_h):
        pk_t = core.qoi_peak(truth_mag[:, c]); bd_t = core.qoi_band(truth_mag[:, c], freqs)
        plo, pmed, phi = np.percentile(peak_draws[:, c], [2.5, 50, 97.5])
        blo, bmed, bhi = np.percentile(band_draws[:, c], [2.5, 50, 97.5])
        pnl, _, pnh = np.percentile(peak_draws_noisy[:, c], [2.5, 50, 97.5])
        bnl, _, bnh = np.percentile(band_draws_noisy[:, c], [2.5, 50, 97.5])
        cp = bool(plo <= pk_t <= phi); cb = bool(blo <= bd_t <= bhi)
        cpn = bool(pnl <= pk_t <= pnh); cbn = bool(bnl <= bd_t <= bnh)
        cov_peak += cp; cov_band += cb; cov_peak_n += cpn; cov_band_n += cbn
        widths.append(core.db(phi) - core.db(plo))
        qoi[str(int(ctx.heldout[c]))] = {
            "z_in": float(model.dof_xyz[ctx.heldout[c], 2]),
            "peak": {"lo": float(plo), "med": float(pmed), "hi": float(phi), "truth": float(pk_t),
                     "covered": cp, "width_db": float(core.db(phi) - core.db(plo))},
            "band": {"lo": float(blo), "med": float(bmed), "hi": float(bhi), "truth": float(bd_t),
                     "covered": cb}}
    nh = Ns_h
    coverage = {
        "peak": {"covered": int(cov_peak), "n": nh, "frac": cov_peak / nh},
        "band": {"covered": int(cov_band), "n": nh, "frac": cov_band / nh},
        "combined": {"covered": int(cov_peak + cov_band), "n": 2 * nh, "frac": (cov_peak + cov_band) / (2 * nh)},
        "peak_noisy_frac": cov_peak_n / nh, "band_noisy_frac": cov_band_n / nh,
        "nominal": 0.95}

    # theta recovery
    theta_post = np.exp(th_all)
    theta_rows = []
    for i, g in enumerate(gnames):
        lo, med, hi = np.percentile(theta_post[:, i], [2.5, 50, 97.5])
        tr = float(theta_truth[i])
        # informed = posterior 95% width materially below prior 95% width (~1.02 for LogNormal(0,.25))
        prior_w = 1.632 - 0.613
        informed = (hi - lo) < 0.6 * prior_w
        theta_rows.append({"group": g, "median": float(med), "lo": float(lo), "hi": float(hi),
                           "truth": tr, "covered": bool(lo <= tr <= hi), "informed": bool(informed),
                           "in_identifiable_set": bool(g in informed_groups),
                           "bias_pct": float(100 * (med / tr - 1)) if tr else None})
    sdf = np.asarray(sd_all)
    sd_summary = ({"lo": float(np.percentile(sdf, 2.5)), "med": float(np.median(sdf)),
                   "hi": float(np.percentile(sdf, 97.5)), "fixed": False}
                  if arm != "M0" else {"lo": 0.0, "med": 0.0, "hi": 0.0, "fixed": True})
    return {"heldout_qoi": qoi, "heldout_coverage": coverage, "theta": theta_rows,
            "sigma_d": sd_summary, "mean_band_width_db": float(np.mean(widths))}
