#!/usr/bin/env python3
"""L5 -> held-out-SENSOR QOI (Card A next-action #1, decisions_log D12).

The CONVERGED modal-frequency twin (D11, modal_feature.py) calibrates the 9-group stiffness multipliers theta
from MEASURED modal peak frequencies. Here we push that calibrated twin onto the card's PRIMARY quantity of
interest (QOI): peak accelerance |H| and band-GRMS [g/lbf] at channels we did NOT use to fit -- the held-out-
SENSOR trust test.

Held-out is the SENSOR:
  - split the dynamic-range-eligible mapped channels into OBSERVED / HELD-OUT (seeded);
  - extract consensus modal frequencies from the OBSERVED channels ONLY (frequencies are a global structural
    feature; a held-out channel's magnitude is never seen in fitting), match to FEM modes, calibrate theta with
    the L5 NUTS modal-frequency likelihood (modal_feature.calibrate_modal -- proven converged);
  - amplitude calibration = ONE global units-gain c per posterior draw, fit on the OBSERVED channels only
    (quality-weighted median of log|H_meas_obs| - log|H_fem_obs(theta)|; the ~x100 offset, D4). A held-out
    channel's predicted level is then a GENUINE prediction from the FEM mode shape Q(theta) at that node +
    damping zeta + the global c -- none of which used held-out data. So this tests FEM mode-shape + frequency
    accuracy at UNSEEN sensors.

Two predictive variants (honest width):
  (i)  theta-only -- sharp; expected to UNDER-cover magnitude because L5 calibrated frequencies, not amplitudes;
  (ii) theta + QOI-discrepancy -- multiplies the predicted QOI by a log-normal exp(N(0, sigma_QOI)) whose scale
       sigma_QOI is estimated from the OBSERVED channels' QOI residual scatter (predicted vs measured peak/band,
       log scale) and transferred to held-out channels. This is an M1-style marginal model-form discrepancy at
       the QOI level (NOT iid per-frequency noise -- white per-bin noise then max() would inflate the peak).
Both reported; neither dressed up as the other. NO spatial Schneider discrepancy here (that is next-action #2).

Scoring (score.py): interval(Winkler)/CRPS/log-predictive-density HEADLINE + PIT/z + coverage SECONDARY.

Output: out/heldout_qoi_L5.json  (resumable: skips if present unless --force).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import score as SC
import modal_feature as mf

WS = Path(__file__).resolve().parent.parent
DR_MIN = 30.0          # only score channels whose in-band peak/floor dynamic range supports a real QOI
ZETA = rf.ZETA_NOM     # 0.01 nominal modal damping; window zeta_w(f) added by the measurement (D5); sweep later


def wmedian(x, w):
    x = np.asarray(x, float); w = np.asarray(w, float)
    if x.size == 0:
        return 0.0
    idx = np.argsort(x); x = x[idx]; w = w[idx]
    cw = np.cumsum(w)
    if cw[-1] <= 0:
        return float(np.median(x))
    return float(x[np.searchsorted(cw, 0.5 * cw[-1])])


def aggregate(scores):
    """Mean headline proper scores + calibration summary over a list of per-channel score_qoi dicts."""
    if not scores:
        return {}
    keys = ("interval_score", "crps", "logpd")
    out = {k + "_mean": float(np.mean([s[k] for s in scores])) for k in keys}
    out["coverage_frac"] = float(np.mean([s["covered"] for s in scores]))
    out["mean_width_db"] = float(np.mean([s["width_db"] for s in scores]))
    out.update(SC.aggregate_pit_z([s["pit"] for s in scores], [s["z"] for s in scores]))
    out["n_channels"] = len(scores)
    return out


def run(seed=0, obs_frac=0.6, n_draws=400, warmup=1000, samples=1000, chains=4, force=False, write=True):
    outp = WS / "out" / "heldout_qoi_L5.json"
    if write and outp.exists() and not force:
        print(f"[skip] {outp.name} exists (use force=True to recompute)")
        return json.loads(outp.read_text())
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}

    # eligible channels (positions in ch) with enough dynamic range for a meaningful QOI
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= DR_MIN)[0]
    rng = np.random.default_rng(seed)
    perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]

    # ---- calibrate theta from modal frequencies extracted from OBSERVED channels only ----
    meas_f, support = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    obs_mode_idx = np.array([p[0] for p in pairs]); obs_w_hz = np.array([p[1] for p in pairs])
    theta_post, sigw2, cdiag = mf.calibrate_modal(
        R, obs_mode_idx, obs_w_hz, seed=20260617, warmup=warmup, samples=samples, chains=chains)

    # ---- forward model log|H g/lbf| over the posterior, observed + held-out channels in one batched eigh ----
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    all_rows = np.vstack([obs_rows, ho_rows]); n_o = len(obs_pos)
    Nd = theta_post.shape[0]
    sub = np.linspace(0, Nd - 1, min(Nd, n_draws)).astype(int)
    lm = rf.fem_logmag_batch(R, freqs, theta_post[sub], all_rows, ch.drive_row, zeta=ZETA)  # (M, Nf, Ns)
    lm_obs = lm[:, :, :n_o]; lm_ho = lm[:, :, n_o:]

    # measured truth log|H| + quality weight, in band
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T  # (Nf, n_o)
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T   # (Nf, n_ho)
    wq_obs = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T                       # (Nf, n_o)
    n_ho = len(ho_pos)

    # ---- per-draw global gain c (observed-only), then peak/band QOI on observed + held-out channels ----
    peak_ho = np.zeros((len(sub), n_ho)); band_ho = np.zeros((len(sub), n_ho))    # held-out, theta-only
    peak_ob = np.zeros((len(sub), n_o)); band_ob = np.zeros((len(sub), n_o))      # observed (for sigma_QOI)
    c_draws = np.zeros(len(sub))
    wflat = wq_obs.ravel()
    for j in range(len(sub)):
        c = wmedian((tru_obs - lm_obs[j]).ravel(), wflat)    # global units-gain (1 scalar/draw, observed-only)
        c_draws[j] = c
        po = np.exp(lm_obs[j] + c); ph = np.exp(lm_ho[j] + c)
        for c2 in range(n_o):
            peak_ob[j, c2] = SC_qoi_peak(po[:, c2]); band_ob[j, c2] = SC_qoi_band(po[:, c2], freqs)
        for c2 in range(n_ho):
            peak_ho[j, c2] = SC_qoi_peak(ph[:, c2]); band_ho[j, c2] = SC_qoi_band(ph[:, c2], freqs)

    # truth QOI per channel
    peak_tru_ob = np.array([SC_qoi_peak(np.exp(tru_obs[:, c2])) for c2 in range(n_o)])
    band_tru_ob = np.array([SC_qoi_band(np.exp(tru_obs[:, c2]), freqs) for c2 in range(n_o)])
    peak_tru_ho = np.array([SC_qoi_peak(np.exp(tru_ho[:, c2])) for c2 in range(n_ho)])
    band_tru_ho = np.array([SC_qoi_band(np.exp(tru_ho[:, c2]), freqs) for c2 in range(n_ho)])

    # QOI-level model-form discrepancy estimated on OBSERVED channels (log scale, predictive-median vs measured):
    #   scatter sigma_QOI (transferred to held-out as a log-normal multiplier) + bias (gain mis-level diagnostic).
    def qoi_disc(pred_obs, tru_obs_qoi):
        r = np.log(np.median(pred_obs, axis=0) + 1e-300) - np.log(tru_obs_qoi + 1e-300)   # per observed channel
        return float(np.std(r)), float(np.median(r))
    sig_pk, bias_pk = qoi_disc(peak_ob, peak_tru_ob)
    sig_bd, bias_bd = qoi_disc(band_ob, band_tru_ob)
    drng = np.random.default_rng(seed + 2)
    peak_ho_d = peak_ho * np.exp(drng.normal(0.0, sig_pk, peak_ho.shape))
    band_ho_d = band_ho * np.exp(drng.normal(0.0, sig_bd, band_ho.shape))

    # ---- score each held-out channel (both variants) ----
    def score_block(peak_draws, band_draws):
        pk, bd, per_ch = [], [], {}
        for c2 in range(n_ho):
            sp = SC.score_qoi(peak_draws[:, c2], peak_tru_ho[c2])
            sb = SC.score_qoi(band_draws[:, c2], band_tru_ho[c2])
            pk.append(sp); bd.append(sb)
            per_ch[str(int(ho_daqs[c2]))] = {
                "z_in": float(ch.coords[ho_pos[c2], 2]), "dyn_range": float(dr[ho_pos[c2]]),
                "peak_truth": float(peak_tru_ho[c2]), "peak_med": float(np.median(peak_draws[:, c2])),
                "peak_covered": sp["covered"], "peak_interval_score": sp["interval_score"],
                "band_truth": float(band_tru_ho[c2]), "band_med": float(np.median(band_draws[:, c2])),
                "band_covered": sb["covered"], "band_interval_score": sb["interval_score"]}
        return {"peak": aggregate(pk), "band": aggregate(bd)}, per_ch

    agg_t, per_t = score_block(peak_ho, band_ho)
    agg_i, per_i = score_block(peak_ho_d, band_ho_d)

    rec = {
        "deliverable": "L5_heldout_sensor_QOI", "qoi": ["peak_accelerance_g_per_lbf", "band_GRMS_g_per_lbf"],
        "split_seed": seed, "obs_frac": obs_frac,
        "n_channels_eligible": int(len(elig)), "n_observed": int(n_o), "n_heldout": int(n_ho),
        "observed_daqs": [int(d) for d in obs_daqs], "heldout_daqs": [int(d) for d in ho_daqs],
        "calibration": {"likelihood": "L5_modal_peak_frequency_observed_channels",
                        "n_measured_modes_obs": int(len(meas_f)), "n_matched_to_fem": int(len(pairs)),
                        "diag": cdiag, "sigma_w2_rel_med": float(np.median(sigw2))},
        "gain_c": {"med": float(np.median(c_draws)), "lo": float(np.percentile(c_draws, 2.5)),
                   "hi": float(np.percentile(c_draws, 97.5)), "note": "natural-log units-gain; e^c = |H| ratio"},
        "qoi_discrepancy_logscale": {
            "peak": {"sigma": sig_pk, "bias": bias_pk}, "band": {"sigma": sig_bd, "bias": bias_bd},
            "note": "log-scale scatter (sigma, transferred to held-out) + bias (gain mis-level), est. on observed channels"},
        "zeta": ZETA, "n_draws_used": int(len(sub)), "runtime_s": time.time() - t0,
        "scores_theta_only": agg_t, "scores_theta_plus_qoi_discrepancy": agg_i,
        "per_channel_theta_plus_qoi_discrepancy": per_i, "per_channel_theta_only": per_t,
    }
    if not write:
        return rec
    (WS / "out").mkdir(exist_ok=True)
    outp.write_text(json.dumps(rec, indent=2))
    print(f"L5 -> held-out-sensor QOI: observe {n_o} ch, hold out {n_ho} ch "
          f"(eligible {len(elig)}, DR>={DR_MIN:.0f}); calib converged={cdiag['converged']} "
          f"R-hat {cdiag['max_rhat']:.3f} ESS {cdiag['min_ess']:.0f}")
    print(f"  global gain c med {rec['gain_c']['med']:.2f}; QOI-discrepancy sigma "
          f"peak {sig_pk:.2f}/band {sig_bd:.2f} (log), bias peak {bias_pk:+.2f}/band {bias_bd:+.2f}")
    for tag, agg in (("theta-only", agg_t), ("theta+qoi-disc", agg_i)):
        print(f"  [{tag}] PEAK cover {agg['peak']['coverage_frac']:.2f} interval {agg['peak']['interval_score_mean']:.3g} "
              f"CRPS {agg['peak']['crps_mean']:.3g} | BAND cover {agg['band']['coverage_frac']:.2f} "
              f"interval {agg['band']['interval_score_mean']:.3g}")
    print(f"  runtime {rec['runtime_s']:.0f}s -> {outp}")
    return rec


# QOI helpers (reuse core's definitions: peak = max|H|, band = GRMS = sqrt(int |H|^2 df))
SC_qoi_peak = rf.core.qoi_peak
SC_qoi_band = rf.core.qoi_band


if __name__ == "__main__":
    force = "--force" in sys.argv
    run(force=force)
