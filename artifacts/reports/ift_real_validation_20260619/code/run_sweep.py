#!/usr/bin/env python3
"""Resumable ≥25-split apples-to-apples sweep -> out/scorecard.json (checker reads this).

Three arms on the SAME seeds / SAME split RNG / SAME scorer (score.py):
  IFT  = physics-in-prior, learned beta (ift_arm.run_split)            -- all N seeds (resumable cells)
  L5   = StatFEM modal-feature + marginal QOI discrepancy (heldout_qoi) -- all N seeds (the bar)
  M2   = StatFEM whole-FRF Schneider (real_arms) field LIKELIHOOD       -- labeled subset (expected NON-converged;
         the divergence IS the comparison result, D3; scoring it on all 25 is meaningless)

Each per-split result is cached (out/{ift,l5,m2}_cells/) so a killed/relaunched run skips finished work.
Aggregates per-arm per-QOI proper-score DISTRIBUTIONS (med/p5/p95 over seeds) + convergence + beta.
The verdict is NOT computed here -- check.py generates it from this scorecard (no hand-set win).
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ift_arm
import heldout_qoi as hq
import realfrf as rf
import real_arms as ra
import m2_arm
import score as SC

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
DR_MIN = ift_arm.DR_MIN


def dist(vals):
    v = np.asarray([x for x in vals if x is not None and np.isfinite(x)], float)
    if v.size == 0:
        return {"med": None, "p5": None, "p95": None, "n": 0}
    return {"med": float(np.median(v)), "p5": float(np.percentile(v, 5)),
            "p95": float(np.percentile(v, 95)), "min": float(v.min()), "max": float(v.max()), "n": int(v.size)}


def _arm_block(per_split, converged_flags, extra=None):
    """per_split: list of {'peak':agg,'band':agg} dicts (agg has *_mean/coverage_frac/z_std)."""
    block = {"converged_frac": float(np.mean(converged_flags)) if converged_flags else 0.0,
             "n_splits": len(per_split)}
    for q in ("peak", "band"):
        block[q] = {
            "interval": dist([s[q].get("interval_score_mean") for s in per_split]),
            "crps": dist([s[q].get("crps_mean") for s in per_split]),
            "logpd": dist([s[q].get("logpd_mean") for s in per_split]),
            "coverage": dist([s[q].get("coverage_frac") for s in per_split]),
            "zstd": dist([s[q].get("z_std") for s in per_split]),
        }
    if extra:
        block.update(extra)
    return block


# ---------------------------------------------------------------- IFT
def ift_split(seed, warmup, samples, chains, n_draws, beta_prior_sd, sigma_meas, force):
    rec = ift_arm.run_split(seed=seed, beta_prior_sd=beta_prior_sd, sigma_meas=sigma_meas,
                            warmup=warmup, samples=samples, chains=chains, n_draws=n_draws,
                            write=True, force=force)
    return rec


# ---------------------------------------------------------------- L5 (cached per seed)
def l5_split(seed, warmup, samples, chains, n_draws, force):
    cell = OUT / "l5_cells" / f"l5_seed{seed:02d}.json"
    if cell.exists() and not force:
        return json.loads(cell.read_text())
    rec = hq.run(seed=seed, n_draws=n_draws, warmup=warmup, samples=samples, chains=chains, write=False)
    # store the comparable block (theta+QOI-discrepancy = the working L5 predictive)
    out = {"seed": seed, "scores": rec["scores_theta_plus_qoi_discrepancy"],
           "converged": bool(rec["calibration"]["diag"]["converged"]),
           "calib_rhat": rec["calibration"]["diag"]["max_rhat"]}
    cell.parent.mkdir(parents=True, exist_ok=True); cell.write_text(json.dumps(out, indent=2))
    return out


# ---------------------------------------------------------------- M2 whole-FRF (cached per seed; expected non-converged)
def m2_split(seed, warmup, samples, chains, n_draws, force):
    cell = OUT / "m2_cells" / f"m2_seed{seed:02d}.json"
    if cell.exists() and not force:
        return json.loads(cell.read_text())
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= DR_MIN)[0]
    perm = np.random.default_rng(seed).permutation(elig)
    n_obs = int(round(0.6 * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T
    wq_obs = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T
    coords_obs = ch.coords[obs_pos]
    lm0 = rf.fem_logmag(R, freqs, np.ones(9), obs_rows, ch.drive_row, zeta=rf.ZETA_NOM)
    c0 = ift_arm.wmedian((tru_obs - lm0).ravel(), wq_obs.ravel())
    # whole-FRF Schneider field LIKELIHOOD arm (Kronecker-efficient; == dense real_arms.M2 to ~2e-15, m2_verify)
    flat, diag = m2_arm.run_m2(R, freqs, tru_obs, obs_rows, ch.drive_row, coords_obs, c0,
                               num_warmup=warmup, num_samples=samples, num_chains=chains)
    # held-out QOI from the (NON-converged) theta posterior + per-draw gain (parametric predictive, flagged)
    log_theta = flat["log_theta"]; nsamp = log_theta.shape[0]
    sub = np.linspace(0, nsamp - 1, min(nsamp, n_draws)).astype(int)
    theta_b = np.exp(log_theta[sub])                                     # (M,9) all 9 free in M2
    gain_b = flat["gain"][sub]
    lm_ho = rf.fem_logmag_batch(R, freqs, theta_b, ho_rows, ch.drive_row, zeta=rf.ZETA_NOM)   # (M,Nf,Nho)
    n_ho = ho_rows.shape[0]
    peak_pred = np.zeros((len(sub), n_ho)); band_pred = np.zeros((len(sub), n_ho))
    for j in range(len(sub)):
        Hmag = np.exp(lm_ho[j] + gain_b[j])
        for k in range(n_ho):
            peak_pred[j, k] = Hmag[:, k].max()
            band_pred[j, k] = np.sqrt(np.trapz(Hmag[:, k] ** 2, freqs))
    peak_tru = np.array([np.exp(tru_ho[:, k]).max() for k in range(n_ho)])
    band_tru = np.array([np.sqrt(np.trapz(np.exp(tru_ho[:, k]) ** 2, freqs)) for k in range(n_ho)])
    pk = [SC.score_qoi(peak_pred[:, k], peak_tru[k]) for k in range(n_ho)]
    bd = [SC.score_qoi(band_pred[:, k], band_tru[k]) for k in range(n_ho)]
    scores = {"peak": ift_arm._agg(pk), "band": ift_arm._agg(bd)}
    out = {"seed": seed, "scores": scores, "converged": bool(diag.get("converged",
           diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02)),
           "diag": {k: diag[k] for k in ("max_rhat", "min_ess", "divergences", "div_frac")},
           "note": "whole-FRF Schneider field LIKELIHOOD; expected NON-converged (StatFEM D7/D10); QOI flagged"}
    cell.parent.mkdir(parents=True, exist_ok=True); cell.write_text(json.dumps(out, indent=2))
    return out


def run(n_splits=25, m2_splits=5, warmup=1000, samples=1000, chains=4, n_draws=300,
        beta_prior_sd=ift_arm.BETA_PRIOR_SD, sigma_meas=ift_arm.SIGMA_MEAS, force=False):
    t0 = time.time()
    seeds = list(range(n_splits))
    ift_ps, ift_conv, ift_beta_med, ift_beta_weak = [], [], [], []
    l5_ps, l5_conv = [], []
    m2_ps, m2_conv = [], []
    for s in seeds:
        r = ift_split(s, warmup, samples, chains, n_draws, beta_prior_sd, sigma_meas, force)
        ift_ps.append(r["scores"]); ift_conv.append(bool(r["convergence"]["converged"]))
        ift_beta_med.append(r["beta_posterior"].get("beta_med"))
        ift_beta_weak.append(bool(r["beta_posterior"].get("weakly_identified", False)))
        l = l5_split(s, warmup, samples, chains, n_draws, force)
        l5_ps.append(l["scores"]); l5_conv.append(l["converged"])
        print(f"[sweep] seed {s}: IFT conv {ift_conv[-1]} | L5 conv {l5_conv[-1]}", flush=True)
    for s in seeds[:m2_splits]:
        m = m2_split(s, warmup, samples, chains, n_draws, force)
        m2_ps.append(m["scores"]); m2_conv.append(m["converged"])
        print(f"[sweep] M2 seed {s}: conv {m2_conv[-1]} (R-hat {m['diag']['max_rhat']:.1f})", flush=True)

    bstar = None
    try:
        bstar = json.loads((OUT / "ift_cells" / f"ift_seed{seeds[0]:02d}.json").read_text())["beta_posterior"]["beta_star"]
    except Exception:
        pass
    beta_collapsed = bool(bstar and np.nanmedian([b for b in ift_beta_med if b]) < bstar / 100.0)
    ift_extra = {"seeds": seeds, "beta": {
        "beta_med_dist": dist(ift_beta_med), "beta_star": bstar,
        "weakly_identified_frac": float(np.mean(ift_beta_weak)) if ift_beta_weak else None,
        "collapsed": beta_collapsed}}

    scorecard = {"study": "ift_real_validation_20260619", "deliverable": "head_to_head_heldout_QOI_scorecard",
                 "seeds": seeds, "n_splits": n_splits,
                 "mc_axis": "channel train/held-out split ONLY (1 impact, 1 hit; labeled reduction)",
                 "headline_scores": ["interval", "crps", "logpd"], "secondary": ["coverage", "zstd"],
                 "scorer": "score.py (byte-identical, manifest)", "sampler": "NUTS 4-chain (TMCMC if escalated)",
                 "arms": {
                     "IFT": _arm_block(ift_ps, ift_conv, ift_extra),
                     "L5": _arm_block(l5_ps, l5_conv),
                     "M2": _arm_block(m2_ps, m2_conv, {"seeds": seeds[:m2_splits],
                            "note": "whole-FRF field LIKELIHOOD; expected non-converged; QOI flagged"}),
                 },
                 "runtime_s": time.time() - t0}
    OUT.mkdir(exist_ok=True)
    (OUT / "scorecard.json").write_text(json.dumps(scorecard, indent=2))
    print(f"\nSCORECARD written: IFT conv {scorecard['arms']['IFT']['converged_frac']*100:.0f}% | "
          f"L5 conv {scorecard['arms']['L5']['converged_frac']*100:.0f}% | "
          f"M2 conv {scorecard['arms']['M2']['converged_frac']*100:.0f}% | runtime {scorecard['runtime_s']:.0f}s")
    return scorecard


if __name__ == "__main__":
    kw = {}
    for a in sys.argv[1:]:
        if a.startswith("--n="): kw["n_splits"] = int(a.split("=")[1])
        elif a.startswith("--m2="): kw["m2_splits"] = int(a.split("=")[1])
        elif a.startswith("--warmup="): kw["warmup"] = int(a.split("=")[1])
        elif a.startswith("--samples="): kw["samples"] = int(a.split("=")[1])
        elif a == "--force": kw["force"] = True
    run(**kw)
