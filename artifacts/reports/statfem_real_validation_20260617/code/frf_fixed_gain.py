#!/usr/bin/env python3
"""Card C follow-up (Andrew 2026-06-19): can we pin the units gain from physics instead of fitting it?

FINDINGS (units forensics, documented in apples_to_apples_frf_summary update):
  - The FEM deck is in CONSISTENT English units (MAT1 densities 2.59e-4 / 7.77e-4 lbf*s^2/in^4 = slinch/in^3 for
    Al/steel; NO WTMASS) and the code already divides accelerance by g = 386.0886 in/s^2 -> g/lbf. So the
    deterministic units conversions are ALREADY handled.
  - The residual model-vs-measured offset is NOT a clean units factor: x496 broadband but x789 at the peaks, with
    ~x2.4 channel-to-channel scatter. The x496 part is the inherited reduced basis's normalization (V_keep column
    norms 219-1490, NOT mass-normalized) -- a fixed but provenance-dependent constant, not derivable from sensor
    calibration. The x789/x496 = x1.6 PEAK-vs-broadband gap and the x2.4 scatter are genuine MODEL-FORM error
    (FEM under-predicts peak amplitude; damping/mode-shape). So the gain cannot be fully pinned from units/sensor
    info, and the whole-vs-peak ambiguity is a SYMPTOM of model-form error, not units.

This script does the most honest 'no free knob' comparison: fix ONE units gain per method, calibrated ONCE on a
reference split's BROADBAND observed data (geometric-mean; no per-target, per-split, or per-draw fitting), then
predict + score held-out peak/band across all 25 splits and report each method's residual BIAS (how far the
held-out peak prediction sits from measured, after the fixed gain). No gain is allowed to absorb model-form error.

Reuses cached calibrations (out/frf_compare/l5_theta_*.npz + the global Beck calib) -> fast, no new NUTS.
Output: out/frf_fixed_gain_summary.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq
import modal_beck_full as M
import frf_compare as FC
import score as SC

WS = Path(__file__).resolve().parent.parent
qoi_peak = rf.core.qoi_peak; qoi_band = rf.core.qoi_band
METHODS = ("L5", "FEM", "Beck")


def fixed_units_gain(ref_seed=0, n_draws=120):
    """ONE broadband units constant per method, from the reference split's observed channels (median over freq x
    observed channel of log|H_meas| - log|H_model_raw|), using the median posterior forward. Single scalar/method."""
    R = rf.load_reduced(); meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    obs_pos, _ = FC.setup_split(R, meas, ch, freqs, fb, didx, dr, ref_seed)
    obs_rows = ch.rows[obs_pos]; obs_daqs = [ch.daq[p] for p in obs_pos]
    tru = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T   # (Nf,n_o)
    cal = M.calibrate(n_modes=12); eta = M.per_mode_eta(cal, True)
    th_l5, _ = FC.l5_theta(R, meas, ch, fb, didx, obs_pos, ref_seed, 600, 600, 4)
    th_beck = np.ones((cal["log_theta"].shape[0], 9)); th_beck[:, [2, 4, 6, 8]] = np.exp(cal["log_theta"])
    TH = {"L5": th_l5, "FEM": np.ones((50, 9)), "Beck": th_beck}
    U = {}
    for m in METHODS:
        thp = TH[m]; sub = np.linspace(0, thp.shape[0] - 1, min(thp.shape[0], n_draws)).astype(int)
        lm_obs, _ = FC.ho_obs_logmag(m, R, freqs, thp, sub, obs_rows, obs_rows[:1], ch.drive_row,
                                     cal=(cal if m == "Beck" else None), eta=(eta if m == "Beck" else None))
        lm_med = np.median(lm_obs, 0)                                   # (Nf,n_o), median forward (no gain)
        U[m] = float(np.median(tru - lm_med))                          # single broadband units constant [nat log]
    return U, cal, eta


def score_split(seed, U, cal, eta, n_draws=120):
    R = rf.load_reduced(); meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    obs_pos, ho_pos = FC.setup_split(R, meas, ch, freqs, fb, didx, dr, seed)
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    n_o, n_ho = len(obs_pos), len(ho_pos)
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    tru_ho = [np.abs(meas["H"][didx[d]][fb]) for d in ho_daqs]
    peak_tru = np.array([qoi_peak(m) for m in tru_ho]); band_tru = np.array([qoi_band(m, freqs) for m in tru_ho])
    th_l5, _ = FC.l5_theta(R, meas, ch, fb, didx, obs_pos, seed, 600, 600, 4)
    th_beck = np.ones((cal["log_theta"].shape[0], 9)); th_beck[:, [2, 4, 6, 8]] = np.exp(cal["log_theta"])
    TH = {"L5": th_l5, "FEM": np.ones((50, 9)), "Beck": th_beck}
    out = {}
    for m in METHODS:
        thp = TH[m]; sub = np.linspace(0, thp.shape[0] - 1, min(thp.shape[0], n_draws)).astype(int)
        lm_obs, lm_ho = FC.ho_obs_logmag(m, R, freqs, thp, sub, obs_rows, ho_rows, ch.drive_row,
                                         cal=(cal if m == "Beck" else None), eta=(eta if m == "Beck" else None))
        lm_obs_g = lm_obs + U[m]; lm_ho_g = lm_ho + U[m]               # FIXED units gain, no fitting
        peak_h = np.array([[qoi_peak(np.exp(lm_ho_g[j, :, k])) for k in range(n_ho)] for j in range(len(sub))])
        band_h = np.array([[qoi_band(np.exp(lm_ho_g[j, :, k]), freqs) for k in range(n_ho)] for j in range(len(sub))])
        # observed-only model-form discrepancy spread (NOT re-centering the bias away)
        peak_o = np.array([[qoi_peak(np.exp(lm_obs_g[j, :, k])) for k in range(n_o)] for j in range(len(sub))])
        ptru_o = np.array([qoi_peak(np.exp(tru_obs[:, k])) for k in range(n_o)])
        resid = np.log(np.median(peak_o, 0) + 1e-300) - np.log(ptru_o + 1e-300)
        sig = float(np.std(resid)); bias_obs = float(np.median(resid))
        dr2 = np.random.default_rng(seed + 3)
        peak_hd = peak_h * np.exp(dr2.normal(0, max(sig, 1e-3), peak_h.shape))
        band_hd = band_h * np.exp(dr2.normal(0, max(sig, 1e-3), band_h.shape))
        sc_pk = [SC.score_qoi(peak_hd[:, k], peak_tru[k]) for k in range(n_ho)]
        sc_bd = [SC.score_qoi(band_hd[:, k], band_tru[k]) for k in range(n_ho)]
        bias_ho = float(np.median(np.log(np.median(peak_h, 0) + 1e-300) - np.log(peak_tru + 1e-300)))
        out[m] = {"peak_IS": float(np.mean([x["interval_score"] for x in sc_pk])),
                  "peak_cov": float(np.mean([x["covered"] for x in sc_pk])),
                  "band_IS": float(np.mean([x["interval_score"] for x in sc_bd])),
                  "peak_bias_log10_obs": bias_obs / np.log(10), "peak_bias_log10_heldout": bias_ho / np.log(10)}
    return out


def run(n_splits=25, n_draws=120):
    t0 = time.time(); U, cal, eta = fixed_units_gain()
    print(f"FIXED units gain per method (nat-log / x): " +
          " | ".join(f"{m} {U[m]:.2f} (x{np.exp(U[m]):.0f})" for m in METHODS), flush=True)
    rows = [score_split(s, U, cal, eta, n_draws) for s in range(n_splits)]

    def D(m, k):
        return float(np.median([r[m][k] for r in rows]))
    agg = {m: {"peak_IS_med": D(m, "peak_IS"), "peak_cov_med": D(m, "peak_cov"), "band_IS_med": D(m, "band_IS"),
               "peak_bias_x_med": float(10 ** D(m, "peak_bias_log10_heldout"))} for m in METHODS}
    beck_lt_l5 = int(np.sum([rows[i]["Beck"]["peak_IS"] < rows[i]["L5"]["peak_IS"] for i in range(n_splits)]))
    out = {"deliverable": "fixed_single_units_gain_no_free_knob", "n_splits": n_splits,
           "units_gain_per_method_natlog": U,
           "note": ("ONE broadband units constant per method, calibrated once on split-0 observed channels; NO "
                    "per-target/per-split/per-draw gain fitting. Residual peak BIAS reported (model-form, not hidden)."),
           "methods": agg, "beck_peakIS_lt_L5_/N": beck_lt_l5, "runtime_s": time.time() - t0}
    (WS / "out" / "frf_fixed_gain_summary.json").write_text(json.dumps(out, indent=2))
    print(f"\nFIXED-GAIN (no free knob, {n_splits} splits):")
    for m in METHODS:
        a = agg[m]
        print(f"  {m:5s}: peak IS {a['peak_IS_med']:.0f} cov {a['peak_cov_med']:.2f} | band IS {a['band_IS_med']:.0f} "
              f"| held-out peak BIAS x{a['peak_bias_x_med']:.2f} (1.0=unbiased)")
    print(f"  Beck peak IS < L5 in {beck_lt_l5}/{n_splits} splits")
    return out


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 25)
