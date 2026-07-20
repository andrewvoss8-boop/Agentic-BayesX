#!/usr/bin/env python3
"""Held-out-sensor QOI scoring of the whole-FRF arms M0/M1/M2/M3 (Card A next-action #2, decisions_log D14).

Calibrate each whole-FRF-magnitude arm on OBSERVED channels via the faithful TMCMC (draws kept), predict the
HELD-OUT channels' peak-|H| and band-GRMS [g/lbf] from forward(theta)+gain plus a QOI-level marginal discrepancy
exp(N(0, sigma_w)) (sigma_w = the arm's fitted discrepancy std), and score with score.py. Writes the checker's
out/scores_summary.json (headline = interval/Winkler score; peak- + quality-weighted; arms M0/M1/M2/M3 + the
CONVERGED L5+marginal reference from heldout_qoi_L5.json).

The arms are YELLOW (non-converged, ESS 1-17, D13) -- labeled. The honest expectation: M2/M3 sigma_w ~= 12 makes
held-out QOI uselessly WIDE (~e^12); M0 (no discrepancy) is overconfident; only the converged L5+marginal
(sigma_QOI ~= 0.98, next-action #1) is calibrated AND usable. Spatial-kriging transfer is deferred (noted): with
sigma_w ~= 12 and non-convergence it would not rescue the whole-FRF arms.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import score as SC
import schneider_faithful as sf
import tmcmc as T

WS = Path(__file__).resolve().parent.parent
DR_MIN = 30.0
qoi_peak = rf.core.qoi_peak
qoi_band = rf.core.qoi_band


def calibrate(arm, R, freqs, tgt_obs, resp_obs, drive, coords_obs, fg, n, runs):
    pieces = sf.build_arm_pieces(arm, R, freqs, coords_obs, resp_obs, drive, fg)
    loglike = sf.make_loglike(arm, R, freqs, tgt_obs, resp_obs, drive, fg, pieces)
    logprior, sample_prior, d = sf.make_prior(arm, len(fg))
    runs_, diag = T.run_independent(loglike, logprior, sample_prior, n=n, n_runs=runs)
    S = np.concatenate([r["samples"] for r in runs_])
    return S, diag


def heldout_scores(arm, R, freqs, S, fg, resp_ho, drive, tru_ho, n_draws=300, seed=0):
    """Predict held-out-channel QOI + score. forward(theta)+gain, then QOI-level marginal exp(N(0,sigma_w))."""
    nfree = len(fg)
    theta = np.ones((S.shape[0], 9)); theta[:, fg] = np.exp(S[:, :nfree])
    c = S[:, nfree]
    sw = np.exp(S[:, nfree + 1]) if arm != "M0" else np.zeros(S.shape[0])
    n_ho = resp_ho.shape[0]
    sub = np.linspace(0, S.shape[0] - 1, min(S.shape[0], n_draws)).astype(int)
    lm = rf.fem_logmag_batch(R, freqs, theta[sub], resp_ho, drive, zeta=sf.ZETA)   # (M, Nf, n_ho)
    rng = np.random.default_rng(seed)
    sw_med = float(np.median(sw[sub]))
    peak = np.zeros((len(sub), n_ho)); band = np.zeros((len(sub), n_ho))
    for j in range(len(sub)):
        ph = np.exp(lm[j] + c[sub][j])                       # (Nf, n_ho), theta+gain
        infl = np.exp(rng.normal(0.0, sw_med, n_ho)) if arm != "M0" else np.ones(n_ho)  # QOI-level discrepancy
        for k in range(n_ho):
            peak[j, k] = qoi_peak(ph[:, k]) * infl[k]
            band[j, k] = qoi_band(ph[:, k], freqs) * infl[k]
    pk, bd = [], []
    for k in range(n_ho):
        pk_t = qoi_peak(np.exp(tru_ho[:, k])); bd_t = qoi_band(np.exp(tru_ho[:, k]), freqs)
        pk.append(SC.score_qoi(peak[:, k], pk_t)); bd.append(SC.score_qoi(band[:, k], bd_t))
    return pk, bd, sw_med


def agg(scores):
    keys = ("interval_score", "crps", "logpd")
    out = {k: float(np.mean([s[k] for s in scores])) for k in keys}
    out["coverage_frac"] = float(np.mean([s["covered"] for s in scores]))
    out["mean_width_db"] = float(np.mean([s["width_db"] for s in scores]))
    out.update(SC.aggregate_pit_z([s["pit"] for s in scores], [s["z"] for s in scores]))
    out["pit"] = out["pit_mean"]; out["z"] = out["z_mean"]; out["z_stats"] = {"mean": out["z_mean"], "std": out["z_std"]}
    return out


def run(seed=0, n_obs=10, n_ho_max=14, n=1500, runs=4, arms=("M0", "M1", "M2", "M3"), force=False):
    outp = WS / "out" / "scores_summary.json"
    if outp.exists() and not force:
        print(f"[skip] {outp.name} exists"); return json.loads(outp.read_text())
    t0 = time.time()
    fg = sf.IDENT4
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    didx = {d: i for i, d in enumerate(meas["daq"])}
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:n_obs + n_ho_max])
    tgt_obs = np.log(np.abs(np.array([meas["H"][didx[ch.daq[p]]][fb] for p in obs_pos])) + 1e-300).T
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[ch.daq[p]]][fb] for p in ho_pos])) + 1e-300).T
    resp_obs = ch.rows[obs_pos]; resp_ho = ch.rows[ho_pos]; coords_obs = ch.coords[obs_pos]

    arms_out = {}
    for arm in arms:
        ta = time.time()
        S, diag = calibrate(arm, R, freqs, tgt_obs, resp_obs, ch.drive_row, coords_obs, fg, n, runs)
        pk, bd, sw_med = heldout_scores(arm, R, freqs, S, fg, resp_ho, ch.drive_row, tru_ho, seed=seed)
        conv = diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02
        a_pk, a_bd = agg(pk), agg(bd)
        arms_out[arm] = {**a_pk, "peak": a_pk, "band": a_bd, "sigma_w": sw_med,
                         "calib_diag": diag, "converged": bool(conv),
                         "not_yet_converged": bool(not conv),
                         "log_evidence": diag.get("log_evidence_mean")}
        print(f"[{arm}] R-hat {diag['max_rhat']:.2f} ESS {diag['min_ess']:.0f} | sigma_w {sw_med:.2f} | "
              f"PEAK cover {a_pk['coverage_frac']:.2f} IS {a_pk['interval_score']:.3g} | "
              f"BAND cover {a_bd['coverage_frac']:.2f} IS {a_bd['interval_score']:.3g} | {time.time()-ta:.0f}s",
              flush=True)

    # converged L5 + marginal-discrepancy reference (next-action #1)
    l5 = None
    p = WS / "out" / "heldout_qoi_L5.json"
    if p.exists():
        d = json.loads(p.read_text())
        a = d["scores_theta_plus_qoi_discrepancy"]["peak"]
        l5 = {"interval_score": a["interval_score_mean"], "crps": a["crps_mean"], "logpd": a["logpd_mean"],
              "coverage_frac": a["coverage_frac"], "z_std": a["z_std"], "converged": True,
              "note": "L5 modal-feature calibrated + marginal QOI-discrepancy (next-action #1, CONVERGED)"}

    rec = {"study": "statfem_real_validation_20260617", "deliverable": "arm_heldout_QOI_scores",
           "headline": "interval_score", "peak_weighted": True, "coherence_weighted": True,
           "qoi": ["peak_accelerance_g_per_lbf", "band_GRMS_g_per_lbf"],
           "split_seed": seed, "n_observed": int(len(obs_pos)), "n_heldout": int(len(ho_pos)),
           "free_groups": [rf.GNAMES[i] for i in fg], "tmcmc": {"n": n, "n_runs": runs},
           "arms": arms_out, "L5_reference_converged": l5, "runtime_s": time.time() - t0,
           "note": "arms are whole-FRF-magnitude (YELLOW, non-converged ESS 1-17); QOI-level marginal discrepancy "
                   "transfer (spatial kriging deferred). Headline proper score; coverage secondary."}
    (WS / "out").mkdir(exist_ok=True)
    outp.write_text(json.dumps(rec, indent=2))
    print(f"-> {outp} ({rec['runtime_s']:.0f}s)")
    return rec


if __name__ == "__main__":
    kw = {}
    for a in sys.argv[1:]:
        if a.startswith("--n="): kw["n"] = int(a.split("=")[1])
        elif a == "--force": kw["force"] = True
    run(**kw)
