#!/usr/bin/env python3
"""Apples-to-apples held-out FRF comparison: Beck inferred-shape twin vs our BEST PREVIOUS method (L5) vs the
FEM-nominal floor, with FULL predictive |H| bands, scored with the SAME protocol as the original runs in this
folder (score.py: score_qoi on peak |H| + band-GRMS exactly as heldout_qoi/mc_heldout; PLUS the whole-FRF
peak-weighted frf_score), comprehensively across the full 25-split Monte-Carlo.

Apples-to-apples controls (held identical across methods):
  - SAME channel splits (DR>=30 eligibility, rng(seed), 60% observed) -> identical observed/held-out sets;
  - SAME measured truth (single-impact hit-001 |H1| [g/lbf], 45-260 Hz);
  - SAME whole-FRF quality-weighted global gain c (the original L5 gain, score.wmedian on observed) for EVERY method;
  - SAME held-out hygiene: gain + every discrepancy sigma estimated on OBSERVED channels ONLY;
  - SAME scorer: score.score_qoi (peak/band, original marginal QOI discrepancy sigma_peak/sigma_band) +
    score.frf_score (whole-FRF, peak+quality weighted). The METHOD = the forward model (which mode shapes, which
    modes, which calibration), nothing else.

Methods:
  L5   = modal peak-FREQUENCY calibration (per split, observed modes) -> full FEM FRF (all modes, FEM shapes, zeta=0.01)
  FEM  = nominal theta=1 -> same full FEM FRF forward (floor)
  Beck = inferred shape FIELD + measured per-mode damping, .ash-calibrated (global) -> 12-mode modal superposition

Note (labeled): Beck uses the whole-FRF gain here (not its native peak gain) for strict apples-to-apples, so its
numbers differ slightly from the Phase-1 table (which used a peak gain). L5 is recalibrated PER SPLIT (its native
protocol). Resumable: per-split JSON in out/frf_compare/, L5 theta cached. Output: out/frf_compare_summary.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
from types import SimpleNamespace
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import heldout_qoi as hq
import modal_feature as mf
import modal_beck_full as M
import score as SC

WS = Path(__file__).resolve().parent.parent
CD = WS / "out" / "frf_compare"; CD.mkdir(parents=True, exist_ok=True)
qoi_peak = rf.core.qoi_peak; qoi_band = rf.core.qoi_band
METHODS = ("L5", "FEM", "Beck")


def setup_split(R, meas, ch, freqs, fb, didx, dr, seed):
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(0.6 * len(perm)))
    return np.sort(perm[:n_obs]), np.sort(perm[n_obs:])


def l5_theta(R, meas, ch, fb, didx, obs_pos, seed, warmup, samples, chains):
    cache = CD / f"l5_theta_{seed}.npz"
    if cache.exists():
        z = np.load(cache); return z["theta"], json.loads(str(z["diag"]))
    obs_daqs = [ch.daq[p] for p in obs_pos]
    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    omi = np.array([p[0] for p in pairs]); owh = np.array([p[1] for p in pairs])
    theta, sigw2, cdiag = mf.calibrate_modal(R, omi, owh, seed=20260617, warmup=warmup, samples=samples, chains=chains)
    np.savez(cache, theta=theta, diag=json.dumps(cdiag))
    return theta, cdiag


def ho_obs_logmag(method, R, freqs, theta_post, sub, obs_rows, ho_rows, drive, cal=None, eta=None):
    """Return (lm_obs, lm_ho) log|H| WITHOUT gain, shape (M, Nf, n)."""
    if method in ("L5", "FEM"):
        all_rows = np.vstack([obs_rows, ho_rows]); n_o = obs_rows.shape[0]
        lm = rf.fem_logmag_batch(R, freqs, theta_post[sub], all_rows, drive, zeta=rf.ZETA_NOM)
        return lm[:, :, :n_o], lm[:, :, n_o:]
    phi0 = cal["phi0"]; raw = cal["raw"]
    lo = np.zeros((len(sub), len(freqs), obs_rows.shape[0])); lh = np.zeros((len(sub), len(freqs), ho_rows.shape[0]))
    for j, s in enumerate(sub):
        theta = theta_post[s]; K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
        phi = phi0 + M.TAU * raw[s % raw.shape[0]]; Phi = phi / (np.linalg.norm(phi, axis=0, keepdims=True) + 1e-30)
        w2r = np.sum(phi * (K @ phi), 0) / (np.sum(phi * phi, 0) + 1e-30)
        lo[j] = np.log(M.reconstruct_mag(Phi, w2r, obs_rows, drive, freqs, 0.0, eta) + 1e-300)
        lh[j] = np.log(M.reconstruct_mag(Phi, w2r, ho_rows, drive, freqs, 0.0, eta) + 1e-300)
    return lo, lh


def score_one(seed, warmup, samples, chains, n_draws):
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    obs_pos, ho_pos = setup_split(R, meas, ch, freqs, fb, didx, dr, seed)
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]; drive = ch.drive_row
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    n_o = len(obs_pos); n_ho = len(ho_pos)
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).transpose(1, 0)  # (Nf,n_o)
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).transpose(1, 0)    # (Nf,n_ho)
    wq_obs = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).transpose(1, 0)                        # (Nf,n_o)
    wq_ho = np.array([meas["weight"][didx[d]][fb] for d in ho_daqs]).transpose(1, 0)
    peak_tru = np.array([qoi_peak(np.exp(tru_ho[:, k])) for k in range(n_ho)])
    band_tru = np.array([qoi_band(np.exp(tru_ho[:, k]), freqs) for k in range(n_ho)])

    cal = M.calibrate(n_modes=12); eta = M.per_mode_eta(cal, True)
    th_l5, d_l5 = l5_theta(R, meas, ch, fb, didx, obs_pos, seed, warmup, samples, chains)
    th_beck = np.ones((cal["log_theta"].shape[0], 9)); th_beck[:, [2, 4, 6, 8]] = np.exp(cal["log_theta"])
    th_fem = np.ones((200, 9))
    TH = {"L5": th_l5, "FEM": th_fem, "Beck": th_beck}
    diag = {"L5": d_l5, "FEM": {"converged": True, "max_rhat": 1.0}, "Beck": cal["diag"]}

    ptru_o = None  # set per method
    res = {"seed": seed, "n_obs": n_o, "n_ho": n_ho, "ho_daqs": [int(d) for d in ho_daqs], "methods": {}}

    def agg_qoi(draws, truth):
        sc = [SC.score_qoi(draws[:, k], truth[k]) for k in range(draws.shape[1])]
        return {"interval_score": float(np.mean([x["interval_score"] for x in sc])),
                "crps": float(np.mean([x["crps"] for x in sc])), "logpd": float(np.mean([x["logpd"] for x in sc])),
                "coverage": float(np.mean([x["covered"] for x in sc])), "z_std": float(np.std([x["z"] for x in sc]))}

    for m in METHODS:
        thp = TH[m]; Nd = thp.shape[0]; sub = np.linspace(0, Nd - 1, min(Nd, n_draws)).astype(int)
        lm_obs, lm_ho = ho_obs_logmag(m, R, freqs, thp, sub, obs_rows, ho_rows, drive,
                                      cal=(cal if m == "Beck" else None), eta=(eta if m == "Beck" else None))
        ptru_o = np.array([qoi_peak(np.exp(tru_obs[:, k])) for k in range(n_o)])
        btru_o = np.array([qoi_band(np.exp(tru_obs[:, k]), freqs) for k in range(n_o)])
        # TWO gain protocols, both observed-only: whole-FRF quality-weighted (the ORIGINAL L5 gain) and PEAK gain
        c_whole = np.array([hq.wmedian((tru_obs - lm_obs[j]).ravel(), wq_obs.ravel()) for j in range(len(sub))])
        pk_obs0 = np.array([[qoi_peak(np.exp(lm_obs[j, :, k])) for k in range(n_o)] for j in range(len(sub))])
        c_peak = np.array([float(np.median(np.log(ptru_o + 1e-300) - np.log(pk_obs0[j] + 1e-300))) for j in range(len(sub))])
        mrec = {"converged": bool(diag[m].get("converged", False)), "rhat": float(diag[m].get("max_rhat", np.nan)),
                "gains": {}}
        for gname, c in (("wholeFRF", c_whole), ("peak", c_peak)):
            lm_obs_g = lm_obs + c[:, None, None]; lm_ho_g = lm_ho + c[:, None, None]
            sig_frf = float(np.std(tru_obs[None] - lm_obs_g))
            lvl = np.random.default_rng(seed + 1000).normal(0, max(sig_frf, 1e-3), len(sub))
            frf_ens = lm_ho_g + lvl[:, None, None]
            peak_o = np.array([[qoi_peak(np.exp(lm_obs_g[j, :, k])) for k in range(n_o)] for j in range(len(sub))])
            band_o = np.array([[qoi_band(np.exp(lm_obs_g[j, :, k]), freqs) for k in range(n_o)] for j in range(len(sub))])
            peak_h = np.array([[qoi_peak(np.exp(lm_ho_g[j, :, k])) for k in range(n_ho)] for j in range(len(sub))])
            band_h = np.array([[qoi_band(np.exp(lm_ho_g[j, :, k]), freqs) for k in range(n_ho)] for j in range(len(sub))])
            sig_pk = float(np.std(np.log(np.median(peak_o, 0) + 1e-300) - np.log(ptru_o + 1e-300)))
            sig_bd = float(np.std(np.log(np.median(band_o, 0) + 1e-300) - np.log(btru_o + 1e-300)))
            dr2 = np.random.default_rng(seed + 2)
            peak_hd = peak_h * np.exp(dr2.normal(0, max(sig_pk, 1e-3), peak_h.shape))
            band_hd = band_h * np.exp(dr2.normal(0, max(sig_bd, 1e-3), band_h.shape))
            frf_sc = [SC.frf_score(frf_ens[:, :, k], tru_ho[:, k], freqs, qual_weight=wq_ho[:, k]) for k in range(n_ho)]
            mrec["gains"][gname] = {
                "sigma_frf": sig_frf, "sigma_peak": sig_pk, "sigma_band": sig_bd,
                "peak": agg_qoi(peak_hd, peak_tru), "band": agg_qoi(band_hd, band_tru),
                "frf_weighted_interval_score": float(np.mean([x["weighted_interval_score"] for x in frf_sc])),
                "frf_grms_rel_err_med": float(np.median([x["grms_rel_err"] for x in frf_sc])),
                "frf_peak_freq_err_hz_med": float(np.median([x["peak_freq_err_hz"] for x in frf_sc]))}
        res["methods"][m] = mrec
    (CD / f"split_{seed}.json").write_text(json.dumps(res, indent=2))
    return res


def run(n_splits=25, warmup=600, samples=600, chains=4, n_draws=200, force=False):
    t0 = time.time(); rows = []
    for s in range(n_splits):
        f = CD / f"split_{s}.json"
        if f.exists() and not force:
            rows.append(json.loads(f.read_text())); print(f"  [skip] split {s}", flush=True); continue
        r = score_one(s, warmup, samples, chains, n_draws); rows.append(r)
        ln = " | ".join(f"{m}[pk-gain] peakIS {r['methods'][m]['gains']['peak']['peak']['interval_score']:.0f}"
                        for m in METHODS)
        print(f"  split {s:2d}: {ln}", flush=True)

    def D(vals):
        v = np.asarray(vals, float)
        return {"median": float(np.median(v)), "mean": float(np.mean(v)),
                "p5": float(np.percentile(v, 5)), "p95": float(np.percentile(v, 95))}

    def G(m, gain, *path):
        out = []
        for r in rows:
            d = r["methods"][m]["gains"][gain]
            for p in path:
                d = d[p]
            out.append(d)
        return out
    agg = {}
    for m in METHODS:
        agg[m] = {"calib_converged_frac": float(np.mean([r["methods"][m]["converged"] for r in rows])), "gains": {}}
        for gain in ("wholeFRF", "peak"):
            agg[m]["gains"][gain] = {
                "peak_interval_score": D(G(m, gain, "peak", "interval_score")),
                "peak_coverage": D(G(m, gain, "peak", "coverage")),
                "peak_crps": D(G(m, gain, "peak", "crps")), "peak_z_std": D(G(m, gain, "peak", "z_std")),
                "band_interval_score": D(G(m, gain, "band", "interval_score")),
                "band_coverage": D(G(m, gain, "band", "coverage")),
                "frf_weighted_interval_score": D(G(m, gain, "frf_weighted_interval_score")),
                "frf_peak_freq_err_hz_med": D(G(m, gain, "frf_peak_freq_err_hz_med"))}

    def sharper(gain, q):
        return int(np.sum([rows[i]["methods"]["Beck"]["gains"][gain][q[0]][q[1]]
                           < rows[i]["methods"]["L5"]["gains"][gain][q[0]][q[1]] for i in range(len(rows))]))
    h2h = {gain: {"peak_IS": sharper(gain, ("peak", "interval_score")),
                  "band_IS": sharper(gain, ("band", "interval_score")),
                  "frf_IS": int(np.sum([rows[i]["methods"]["Beck"]["gains"][gain]["frf_weighted_interval_score"]
                                        < rows[i]["methods"]["L5"]["gains"][gain]["frf_weighted_interval_score"]
                                        for i in range(len(rows))]))}
           for gain in ("wholeFRF", "peak")}
    out = {"deliverable": "apples_to_apples_FRF_comparison_full_MC",
           "scoring": "score.py original protocol: score_qoi(peak,band) + frf_score(whole-FRF, peak+quality weighted)",
           "controls": "same splits, observed-only sigmas, same scorer; method = forward model. TWO gain protocols "
                       "reported: wholeFRF (the ORIGINAL L5 gain) and peak (QOI-appropriate). Ranking is gain-dependent.",
           "n_splits": len(rows), "methods": agg, "beck_vs_L5_sharper_per_split_/N": h2h, "runtime_s": time.time() - t0}
    (WS / "out" / "frf_compare_summary.json").write_text(json.dumps(out, indent=2))
    print("\nFRF-COMPARE DONE (apples-to-apples, full MC; N=%d):" % len(rows))
    for gain in ("wholeFRF", "peak"):
        print(f"  --- gain = {gain} ---")
        for m in METHODS:
            a = agg[m]["gains"][gain]
            print(f"    {m:5s}: peak IS {a['peak_interval_score']['median']:.0f} cov {a['peak_coverage']['median']:.2f}"
                  f" | band IS {a['band_interval_score']['median']:.0f} | whole-FRF IS "
                  f"{a['frf_weighted_interval_score']['median']:.2f} | pk-freq err "
                  f"{a['frf_peak_freq_err_hz_med']['median']:.0f}Hz")
        print(f"    Beck<L5 sharper: peak {h2h[gain]['peak_IS']}/{len(rows)}, band {h2h[gain]['band_IS']}/{len(rows)}, "
              f"whole-FRF {h2h[gain]['frf_IS']}/{len(rows)}")
    return out


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 25, force="--force" in sys.argv)
