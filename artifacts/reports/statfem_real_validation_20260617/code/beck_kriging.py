#!/usr/bin/env python3
"""Card C Phase 2 -- spatial-kriging held-out discrepancy for the hardened Beck twin (the deferred Schneider transfer).

Phase 1 transferred the held-out model-form discrepancy as a MARGINAL scalar log-normal level offset per channel
(independent of where the channel sits). Here we replace that marginal with the freq x space GP-CONDITIONAL transfer
used in the synthetic predict.py (PredCtx.krige): condition each held-out channel's discrepancy FIELD d_h(f) on the
OBSERVED channels' residual field R_o(f) via the Schneider covariance sigma_d^2 (C_f kron C_z) + sigma_meas^2 I.
A held-out channel spatially near observed channels then inherits a conditional-MEAN correction and a SHRUNKEN
conditional variance -> potentially sharper while staying calibrated. Question (at FIXED Beck calibration): does the
correlated transfer SHARPEN vs the marginal? Compare on the 25-split MC.

C_f = SE over log-frequency (length DISC_LEN_LOGF); C_z = exponential over 3-D sensor distance (length len_z,
swept). Decoupled over the frequency eigenbasis (U_f preserves iid noise) -> vectorised over frequency.

Output: out/mc_beck_kriging_summary.json. Beck/Au/Vanik (2001) CACIE 16:1-11; Schneider et al. (2022) MSSP 166:108407.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq
import modal_beck_full as M
import nuts_arms as na
import core
import score as SC

WS = Path(__file__).resolve().parent.parent
qoi_peak = rf.core.qoi_peak
qoi_band = rf.core.qoi_band


class KrigeCtx:
    """Fixed (draw-independent) freq + space eigenbases for one channel split."""
    def __init__(self, freqs, coords_obs, coords_ho, len_logf=core.DISC_LEN_LOGF, len_z=core.DISC_LEN_Z,
                 sigma_meas=core.SIGMA_MEAS):
        self.freqs = freqs; self.sigma_meas = sigma_meas; self.Ns_h = len(coords_ho)
        Cf = na.corr_freq(freqs, len_logf)
        self.lam_f, self.U_f = np.linalg.eigh(Cf); self.lam_f = np.clip(self.lam_f, 0.0, None)
        Czoo = na.corr_space(coords_obs, len_z); self.Czhh = na.corr_space(coords_ho, len_z)
        d = np.sqrt(((coords_ho[:, None, :] - coords_obs[None, :, :]) ** 2).sum(-1))
        self.Czho = np.exp(-np.abs(d) / len_z)
        self.lam_o, self.U_o = np.linalg.eigh(Czoo); self.lam_o = np.clip(self.lam_o, 0.0, None)

    def krige(self, R_o, sigma_d, rng):
        """Conditional mean + one field sample of d_h (Nf, Ns_h) given observed residual R_o (Nf, Ns_o)."""
        sd2 = sigma_d ** 2
        if sd2 <= 0:
            z = np.zeros((len(self.freqs), self.Ns_h)); return z, z
        Czoh = self.Czho.T
        At = (self.U_f.T @ R_o) @ self.U_o
        denom = sd2 * self.lam_f[:, None] * self.lam_o[None, :] + self.sigma_meas ** 2
        w = (At / denom) @ self.U_o.T
        mean_t = (sd2 * self.lam_f[:, None]) * (w @ self.Czho.T)
        Soo_inv = np.einsum("oi,mi,pi->mop", self.U_o, 1.0 / denom, self.U_o)
        term = np.einsum("hi,mij,jk->mhk", self.Czho, Soo_inv, Czoh)
        s = sd2 * self.lam_f
        cov = s[:, None, None] * self.Czhh[None] - (s ** 2)[:, None, None] * term
        cov = 0.5 * (cov + np.swapaxes(cov, 1, 2)) + 1e-9 * np.eye(self.Ns_h)[None]
        try:
            L = np.linalg.cholesky(cov)
        except np.linalg.LinAlgError:
            ev, eV = np.linalg.eigh(cov)
            L = eV @ (np.sqrt(np.clip(ev, 0, None))[:, None, :] * np.eye(self.Ns_h)[None])
        smp_t = mean_t + np.einsum("mhk,mk->mh", L, rng.standard_normal(mean_t.shape))
        return self.U_f @ mean_t, self.U_f @ smp_t


def score_split(cal, seed, len_z=core.DISC_LEN_Z, n_draws=100):
    """Compare MARGINAL vs KRIGED held-out discrepancy at FIXED Beck (inferred shapes + measured damping)."""
    R = cal["R"]; phi0 = cal["phi0"]
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(0.6 * len(perm))); obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    n_o = len(obs_pos); n_ho = len(ho_pos)
    tru_obs_lm = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T  # (Nf, n_o)
    tru_ho = [np.abs(meas["H"][didx[d]][fb]) for d in ho_daqs]
    peak_tru_ho = np.array([qoi_peak(m) for m in tru_ho]); band_tru_ho = np.array([qoi_band(m, freqs) for m in tru_ho])
    peak_tru_obs = np.array([qoi_peak(np.exp(tru_obs_lm[:, k])) for k in range(n_o)])
    ctx = KrigeCtx(freqs, ch.coords[obs_pos], ch.coords[ho_pos], len_z=len_z)
    eta = M.per_mode_eta(cal, True)
    log_theta = cal["log_theta"]; raw = cal["raw"]
    sub = np.linspace(0, raw.shape[0] - 1, min(raw.shape[0], n_draws)).astype(int)
    theta_post = np.ones((log_theta.shape[0], 9)); theta_post[:, [2, 4, 6, 8]] = np.exp(log_theta)
    krng = np.random.default_rng(seed + 31)
    peak_m = np.zeros((len(sub), n_ho)); band_m = np.zeros((len(sub), n_ho))   # marginal
    peak_k = np.zeros((len(sub), n_ho)); band_k = np.zeros((len(sub), n_ho))   # kriged
    sig_qoi_acc = []
    for j, s in enumerate(sub):
        theta = theta_post[s]; K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
        phi = phi0 + M.TAU * raw[s]; Phi = phi / (np.linalg.norm(phi, axis=0, keepdims=True) + 1e-30)
        w2r = np.sum(phi * (K @ phi), 0) / (np.sum(phi * phi, 0) + 1e-30)
        mag_o0 = M.reconstruct_mag(Phi, w2r, obs_rows, ch.drive_row, freqs, 0.0, eta)
        obs_pk = np.array([qoi_peak(mag_o0[:, k]) for k in range(n_o)])
        c = float(np.median(np.log(peak_tru_obs + 1e-30) - np.log(obs_pk + 1e-30)))
        lm_o = np.log(mag_o0 + 1e-300) + c                       # (Nf, n_o)
        lm_h = np.log(M.reconstruct_mag(Phi, w2r, ho_rows, ch.drive_row, freqs, c, eta) + 1e-300)  # (Nf, n_ho)
        R_o = tru_obs_lm - lm_o                                  # observed residual field
        sig_d = float(np.std(R_o))                               # per-freq log-mag discrepancy scale (this draw)
        sig_qoi_acc.append(sig_d)
        # MARGINAL: scalar log-normal level offset per held-out channel (Phase-1 style, observed-only sigma)
        off = krng.normal(0, max(sig_d, 1e-3), n_ho)
        mag_hm = np.exp(lm_h + off[None, :])
        # KRIGED: freq x space conditional field
        _, d_h = ctx.krige(R_o, sig_d, krng)
        mag_hk = np.exp(lm_h + d_h)
        for k in range(n_ho):
            peak_m[j, k] = qoi_peak(mag_hm[:, k]); band_m[j, k] = qoi_band(mag_hm[:, k], freqs)
            peak_k[j, k] = qoi_peak(mag_hk[:, k]); band_k[j, k] = qoi_band(mag_hk[:, k], freqs)

    def agg(draws, truth):
        sc = [SC.score_qoi(draws[:, k], truth[k]) for k in range(draws.shape[1])]
        return {"coverage": float(np.mean([x["covered"] for x in sc])),
                "interval_score": float(np.mean([x["interval_score"] for x in sc])),
                "crps": float(np.mean([x["crps"] for x in sc])), "z_std": float(np.std([x["z"] for x in sc]))}
    return {"marginal": {"peak": agg(peak_m, peak_tru_ho), "band": agg(band_m, band_tru_ho)},
            "kriged": {"peak": agg(peak_k, peak_tru_ho), "band": agg(band_k, band_tru_ho)},
            "sigma_d_median": float(np.median(sig_qoi_acc)), "n_obs": n_o, "n_ho": n_ho}


def run_mc(n_splits=25, len_z_list=(12.0, 60.0), n_draws=100):
    t0 = time.time(); cal = M.calibrate(n_modes=12)
    print(f"calib conv {cal['diag']['converged']} R-hat {cal['diag']['max_rhat']:.3f}", flush=True)
    blocks = {}
    for len_z in len_z_list:
        rows = []
        for s in range(n_splits):
            r = score_split(cal, s, len_z=len_z, n_draws=n_draws); rows.append(r)
            print(f"  len_z {len_z:5.0f} split {s:2d}: peak IS marg {r['marginal']['peak']['interval_score']:7.0f} "
                  f"-> krig {r['kriged']['peak']['interval_score']:7.0f} (cov {r['kriged']['peak']['coverage']:.2f})",
                  flush=True)

        def med(kind, qoi, key):
            return float(np.median([x[kind][qoi][key] for x in rows]))
        nshp = {q: int(np.sum([rows[i]["kriged"][q]["interval_score"] < rows[i]["marginal"][q]["interval_score"]
                               for i in range(n_splits)])) for q in ("peak", "band")}
        blocks[f"len_z_{int(len_z)}_in"] = {
            "n_splits": n_splits, "sigma_d_median": float(np.median([x["sigma_d_median"] for x in rows])),
            "peak": {k: {"marginal": med("marginal", "peak", k), "kriged": med("kriged", "peak", k)}
                     for k in ("interval_score", "coverage", "z_std")},
            "band": {k: {"marginal": med("marginal", "band", k), "kriged": med("kriged", "band", k)}
                     for k in ("interval_score", "coverage", "z_std")},
            "n_splits_kriged_sharper": nshp, "per_split": rows}
        (WS / "out").mkdir(exist_ok=True)
        (WS / "out" / "mc_beck_kriging_summary.json").write_text(json.dumps(
            {"method": "L8b_Beck_on_ash + spatial-kriging held-out discrepancy (Schneider freq x space transfer)",
             "calib_diag": cal["diag"], "blocks": blocks, "runtime_s": time.time() - t0}, indent=2))
    print("\nKRIGING MC DONE.")
    for nm, b in blocks.items():
        print(f" {nm}: PEAK IS marg {b['peak']['interval_score']['marginal']:.0f} -> "
              f"krig {b['peak']['interval_score']['kriged']:.0f} (sharper {b['n_splits_kriged_sharper']['peak']}/"
              f"{b['n_splits']}, cov {b['peak']['coverage']['kriged']:.2f}) | BAND IS marg "
              f"{b['band']['interval_score']['marginal']:.0f} -> krig {b['band']['interval_score']['kriged']:.0f}")
    return blocks


if __name__ == "__main__":
    run_mc(int(sys.argv[1]) if len(sys.argv) > 1 else 25)
