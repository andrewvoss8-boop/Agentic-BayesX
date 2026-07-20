#!/usr/bin/env python3
"""Card C Phase 5 -- .ash modal survey as a CROSS-DATASET observable. Calibrate the stiffness multipliers theta on
the INDEPENDENT .ash experimental-modal-analysis survey (measured eigenfrequencies +/- mode shapes, MAC-matched),
then PREDICT the impact-hammer held-out FRF QOI (peak |H| and band-GRMS). Does a SEPARATE measurement campaign
(.ash) calibrate a twin that generalizes to the impact-hammer test? Compare calibration SOURCES under ONE common
forward (FEM-shape modal superposition from the 12 matched modes, measured per-mode damping, observed-only gain +
QOI-discrepancy, same 25 splits):

  nominal       theta = 1 (no calibration)                 [baseline = Phase-1 FEM_const]
  ash_freq      theta from .ash eigenfrequencies only
  ash_freqMAC   theta from .ash eigenfrequencies + MAC shape term
  beck_infer    theta + inferred shape FIELD from .ash      [Phase-1 INFER, inferred shapes]
Reference: L5 = impact-FRF-derived frequency calibration (out/heldout_qoi_L5.json, peak IS 1661).

All .ash calibrations are split-independent (one global survey). Output: out/cross_dataset_summary.json.
"""
import json
import sys
import time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq
import modal_beck_full as M
import modal_ash_mac as am
import score as SC

WS = Path(__file__).resolve().parent.parent
qoi_peak = rf.core.qoi_peak; qoi_band = rf.core.qoi_band


def fem_forward(R, theta, fem_k, rows, drive, freqs, c, eta):
    """FEM mode shapes at theta: eigh(K(theta)) -> matched columns -> modal-superposition |H| (Nf, Ns)."""
    K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
    lam, Q = np.linalg.eigh(K)
    return M.reconstruct_mag(Q[:, fem_k], lam[fem_k], rows, drive, freqs, c, eta)


def score_source(cal, theta_post, seed, source, n_draws=120):
    """Held-out impact peak+band IS for a theta posterior (FEM shapes) or the Beck inferred shapes."""
    R = cal["R"]; fem_k = cal["fem_k"]; phi0 = cal["phi0"]; eta = M.per_mode_eta(cal, True)
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
    peak_tru_obs = np.array([qoi_peak(np.abs(meas["H"][didx[d]][fb])) for d in obs_daqs])
    tru_ho = [np.abs(meas["H"][didx[d]][fb]) for d in ho_daqs]
    peak_tru_ho = np.array([qoi_peak(m) for m in tru_ho]); band_tru_ho = np.array([qoi_band(m, freqs) for m in tru_ho])
    Nd = theta_post.shape[0]; sub = np.linspace(0, Nd - 1, min(Nd, n_draws)).astype(int)
    peak_o = np.zeros((len(sub), n_o)); peak_h = np.zeros((len(sub), n_ho)); band_h = np.zeros((len(sub), n_ho))
    raw = cal["raw"]
    for j, s in enumerate(sub):
        theta = theta_post[s]
        if source == "beck_infer":
            K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
            phi = phi0 + M.TAU * raw[s % raw.shape[0]]; Phi = phi / (np.linalg.norm(phi, axis=0, keepdims=True) + 1e-30)
            w2r = np.sum(phi * (K @ phi), 0) / (np.sum(phi * phi, 0) + 1e-30)
            mo0 = M.reconstruct_mag(Phi, w2r, obs_rows, ch.drive_row, freqs, 0.0, eta)
        else:
            mo0 = fem_forward(R, theta, fem_k, obs_rows, ch.drive_row, freqs, 0.0, eta)
        obs_pk = np.array([qoi_peak(mo0[:, k]) for k in range(n_o)])
        c = float(np.median(np.log(peak_tru_obs + 1e-30) - np.log(obs_pk + 1e-30)))
        if source == "beck_infer":
            mh = M.reconstruct_mag(Phi, w2r, ho_rows, ch.drive_row, freqs, c, eta)
        else:
            mh = fem_forward(R, theta, fem_k, ho_rows, ch.drive_row, freqs, c, eta)
        for k in range(n_o):
            peak_o[j, k] = obs_pk[k] * np.exp(c)
        for k in range(n_ho):
            peak_h[j, k] = qoi_peak(mh[:, k]); band_h[j, k] = qoi_band(mh[:, k], freqs)
    sig_pk = float(np.std(np.log(np.median(peak_o, 0) + 1e-300) - np.log(peak_tru_obs + 1e-300)))
    # band sigma reuse peak sigma scale (consistent observed-only treatment)
    drng = np.random.default_rng(seed + 9)
    peak_hd = peak_h * np.exp(drng.normal(0, max(sig_pk, 1e-3), peak_h.shape))
    band_hd = band_h * np.exp(drng.normal(0, max(sig_pk, 1e-3), band_h.shape))

    def agg(draws, truth):
        sc = [SC.score_qoi(draws[:, k], truth[k]) for k in range(draws.shape[1])]
        return {"coverage": float(np.mean([x["covered"] for x in sc])),
                "interval_score": float(np.mean([x["interval_score"] for x in sc])),
                "z_std": float(np.std([x["z"] for x in sc]))}
    return {"peak": agg(peak_hd, peak_tru_ho), "band": agg(band_hd, band_tru_ho)}


def run(n_splits=25, n_draws=120, warmup=1000, samples=1000, chains=4):
    t0 = time.time()
    cal = M.calibrate(n_modes=12)                                  # Beck calib (theta + inferred shapes), 12 modes
    R = cal["R"]
    ash12 = dict(cal["ash"]); ash12["pairs"] = cal["ash"]["pairs"][:12]   # match Beck's 12-mode subset
    # .ash freq-only and freq+MAC theta posteriors (split-independent)
    th_freq, d_freq, _ = am.calibrate(R, ash12, [2, 4, 6, 8], use_mac=False, warmup=warmup, samples=samples, chains=chains)
    th_mac, d_mac, smac = am.calibrate(R, ash12, [2, 4, 6, 8], use_mac=True, warmup=warmup, samples=samples, chains=chains)
    th_beck = np.ones((cal["log_theta"].shape[0], 9)); th_beck[:, [2, 4, 6, 8]] = np.exp(cal["log_theta"])
    th_nom = np.ones((200, 9))
    sources = {"nominal": (th_nom, "fem", {"converged": True, "max_rhat": 1.0}),
               "ash_freq": (th_freq, "fem", d_freq),
               "ash_freqMAC": (th_mac, "fem", d_mac),
               "beck_infer": (th_beck, "beck_infer", cal["diag"])}
    res = {}
    for name, (thp, src, diag) in sources.items():
        pk, bd, cp, cb, zz = [], [], [], [], []
        for s in range(n_splits):
            sc = score_source(cal, thp, s, src, n_draws=n_draws)
            pk.append(sc["peak"]["interval_score"]); bd.append(sc["band"]["interval_score"])
            cp.append(sc["peak"]["coverage"]); cb.append(sc["band"]["coverage"]); zz.append(sc["peak"]["z_std"])
        res[name] = {"calib_converged": bool(diag.get("converged", False)), "calib_rhat": float(diag.get("max_rhat", np.nan)),
                     "peak_IS_median": float(np.median(pk)), "peak_cov_median": float(np.median(cp)),
                     "peak_zstd_median": float(np.median(zz)),
                     "band_IS_median": float(np.median(bd)), "band_cov_median": float(np.median(cb))}
        print(f"  {name:12s} conv {res[name]['calib_converged']} R-hat {res[name]['calib_rhat']:.3f} | "
              f"peak IS {res[name]['peak_IS_median']:.0f} cov {res[name]['peak_cov_median']:.2f} | "
              f"band IS {res[name]['band_IS_median']:.0f}", flush=True)
    L5 = json.loads((WS / "out" / "heldout_qoi_L5.json").read_text())["scores_theta_plus_qoi_discrepancy"]
    (WS / "out").mkdir(exist_ok=True)
    (WS / "out" / "cross_dataset_summary.json").write_text(json.dumps(
        {"deliverable": "Phase5_cross_dataset (.ash-calibrated theta -> predict impact-hammer held-out FRF QOI)",
         "n_splits": n_splits, "sources": res,
         "L5_impact_FRF_reference": {"peak_IS": L5["peak"]["interval_score_mean"], "peak_cov": L5["peak"]["coverage_frac"],
                                     "band_IS": L5["band"]["interval_score_mean"]},
         "ash_freqMAC_sigma_mac": smac, "runtime_s": time.time() - t0}, indent=2))
    print(f"\nCROSS-DATASET DONE. L5 (impact-FRF) ref peak IS {L5['peak']['interval_score_mean']:.0f}.")
    return res


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 25)
