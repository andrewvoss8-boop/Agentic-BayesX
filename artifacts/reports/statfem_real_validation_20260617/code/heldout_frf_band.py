#!/usr/bin/env python3
"""Predicted |H| band at a HELD-OUT channel vs the real measured FRF (for fig_heldout_frf; decisions_log D16).

Reuses the L5 modal-feature calibration (modal_feature.calibrate_modal) on OBSERVED-channel modes, then forwards
the theta posterior + per-draw global gain through the matched-path forward at one UNSEEN (held-out) channel to
get a per-frequency predictive band. Overlays the measured |H1| truth + single-hit quality weight. Saves
out/heldout_frf_band.json. This visualizes WHERE the modal-calibrated twin predicts the FRF (frequencies align)
and where it is off (amplitudes) -- the real model-form story.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq

WS = Path(__file__).resolve().parent.parent


def run(seed=0, obs_frac=0.6, n_draws=250, warmup=1000, samples=1000, chains=4):
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]
    # held-out channel = REPRESENTATIVE (median dynamic range among held-out), not the extreme.
    # (every held-out channel is shown in out/heldout_report.pdf; this single figure is one typical example.)
    hsel = ho_pos[int(np.argsort(dr[ho_pos])[len(ho_pos) // 2])]

    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    theta_post, _, diag = mf.calibrate_modal(R, np.array([p[0] for p in pairs]),
                                             np.array([p[1] for p in pairs]),
                                             warmup=warmup, samples=samples, chains=chains)
    sub = np.linspace(0, theta_post.shape[0] - 1, min(theta_post.shape[0], n_draws)).astype(int)

    obs_rows = ch.rows[obs_pos]; ho_row = ch.rows[hsel][None, :]
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T   # (Nf, n_obs)
    wq_obs = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T
    lm_obs = rf.fem_logmag_batch(R, freqs, theta_post[sub], obs_rows, ch.drive_row, zeta=hq.ZETA)
    lm_ho = rf.fem_logmag_batch(R, freqs, theta_post[sub], ho_row, ch.drive_row, zeta=hq.ZETA)[:, :, 0]
    wflat = wq_obs.ravel()
    pred = np.zeros((len(sub), len(freqs))); c_draws = np.zeros(len(sub))
    peak_ob = np.zeros((len(sub), len(obs_pos)))
    for j in range(len(sub)):
        c = hq.wmedian((tru_obs - lm_obs[j]).ravel(), wflat)     # per-draw global gain on observed
        c_draws[j] = c; pred[j] = lm_ho[j] + c
        po = np.exp(lm_obs[j] + c)
        for k in range(len(obs_pos)):
            peak_ob[j, k] = float(np.max(po[:, k]))
    # amplitude QOI discrepancy (log) from OBSERVED peaks -> the calibrated total band
    peak_tru_ob = np.array([float(np.max(np.exp(tru_obs[:, k]))) for k in range(len(obs_pos))])
    sig_qoi = float(np.std(np.log(np.median(peak_ob, 0) + 1e-300) - np.log(peak_tru_ob + 1e-300)))
    c_med = float(np.median(c_draws))
    band = np.exp(np.percentile(pred, [5, 50, 95], axis=0))      # PARAM band (theta posterior) at the channel
    # deterministic as-received NASA-correlated FEM = prior mean theta=1 (our matched-path forward; NASA SOL111
    # NOT used = mismatched path, study constraint; our reduced model reproduces the NASA FEM eigenfreqs to 3e-10)
    det = np.exp(rf.fem_logmag(R, freqs, np.ones(9), ho_row, ch.drive_row, zeta=hq.ZETA)[:, 0] + c_med)
    tru = np.abs(meas["H"][didx[ch.daq[hsel]]][fb])
    wq = meas["weight"][didx[ch.daq[hsel]]][fb]
    rec = {"channel_daq": int(ch.daq[hsel]), "dyn_range": float(dr[hsel]), "split_seed": seed,
           "calib_converged": bool(diag["converged"]), "calib_rhat": diag["max_rhat"],
           "n_observed": int(n_obs), "freqs_hz": freqs.tolist(), "sigma_qoi": sig_qoi,
           "measured_absH": tru.tolist(), "quality_weight": wq.tolist(),
           "deterministic_nasa_absH": det.tolist(),
           "pred_lo": band[0].tolist(), "pred_med": band[1].tolist(), "pred_hi": band[2].tolist()}
    (WS / "out").mkdir(exist_ok=True)
    (WS / "out" / "heldout_frf_band.json").write_text(json.dumps(rec))
    print(f"held-out FRF band: channel {ch.daq[hsel]} (DR {dr[hsel]:.0f}), calib converged {diag['converged']} "
          f"R-hat {diag['max_rhat']:.3f}; saved out/heldout_frf_band.json")
    return rec


if __name__ == "__main__":
    run()
