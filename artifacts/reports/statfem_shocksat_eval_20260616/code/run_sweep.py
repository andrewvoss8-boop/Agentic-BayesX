#!/usr/bin/env python3
"""Main sweep: 5 bias combos x 4 arms (M0/M1/M2/M3). Resumable (skips finished cells).

Per combo a single synthetic truth is generated (theta_truth offsets + ONE Schneider field realization,
combo-specific seed) and SHARED by all 4 arms (same data). Each arm: NUTS calibration on observed channels
-> posterior predictive held-out QOI coverage. Float64; BLAS threads pinned by run_all.sh; launch detached.

Cell JSON schema (out/cell_<combo>_<arm>.json): combo/combo_idx/arm, nuts{max_rhat,min_ess,div_frac,...},
converged, heldout_coverage{peak,band,combined}, heldout_qoi{sensor:{peak,band}}, theta[9 rows w/
covered+informed], sigma_d, mean_band_width_db, runtime_s.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WS = HERE.parent
OUT = WS / "out"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))

import core            # noqa: E402
import nuts_arms as na  # noqa: E402
import predict as pr   # noqa: E402

ARMS = ["M0", "M1", "M2", "M3"]
# strain-energy/FIM identifiable set (authoritative version in identifiability.py); FRF carries more
# box signal than freq-only, so we expect these to be informable when biased.
INFORMED_GROUPS = ["bottom_box", "top_box", "plates", "cross_beam"]
SEED_BASE = 20260616


def gen_truth(model, freqs, observed, heldout, drive, theta_truth, combo_idx, zeta=core.ZETA_NOM):
    """One synthetic truth: model(theta_truth) * Schneider field (combo seed), + measurement noise on obs."""
    all_ch = list(observed) + list(heldout)
    coords_all = model.dof_xyz[np.asarray(all_ch)]
    rng_f = np.random.default_rng(SEED_BASE + 100 * combo_idx)
    H = core.frf_np(model, freqs, theta_truth, all_ch, drive, zeta=zeta)        # (Nf, Nall)
    field = core.schneider_field(freqs, coords_all, rng_f)                      # (Nf, Nall) complex mult
    truth = H * field
    logmag_all = np.log(np.abs(truth))
    no = len(observed)
    truth_obs = logmag_all[:, :no]
    truth_ho = logmag_all[:, no:]
    rng_m = np.random.default_rng(SEED_BASE + 100 * combo_idx + 1)
    meas_obs = truth_obs + rng_m.normal(0, core.SIGMA_MEAS, truth_obs.shape)
    return meas_obs, truth_obs, truth_ho


def run_cell(model, freqs, ch, combo_idx, arm, nwarm, nsamp, nchain, zeta=core.ZETA_NOM,
             tag="", observed=None, heldout=None):
    observed = ch["observed"] if observed is None else observed
    heldout = ch["heldout"] if heldout is None else heldout
    drive = ch["drive"]
    combo = core.COMBOS[combo_idx]
    theta_truth = core.theta_vector(combo["theta"])
    meas_obs, truth_obs, truth_ho = gen_truth(model, freqs, observed, heldout, drive,
                                              theta_truth, combo_idx, zeta=zeta)
    t0 = time.time()
    samples, diag, _ = na.run_arm(arm, model, freqs, meas_obs, observed, drive, zeta=zeta,
                                  num_warmup=nwarm, num_samples=nsamp, num_chains=nchain,
                                  seed=SEED_BASE + combo_idx)
    ctx = pr.PredCtx(model, freqs, observed, heldout, drive, arm, zeta=zeta)
    # krige/predict conditions on the SAME observed target the sampler saw (meas_obs)
    res = pr.predict_cell(ctx, samples, truth_ho, meas_obs, core.GNAMES, theta_truth, INFORMED_GROUPS)
    # save posterior samples (small) so figures can recompute predictive FRF bands without re-running NUTS
    np.savez_compressed(OUT / f"samples_{tag}{combo_idx}_{arm}.npz",
                        log_theta=samples["log_theta"].astype(np.float32),
                        sigma_d=np.asarray(samples.get("sigma_d", np.zeros(len(samples["log_theta"])))).astype(np.float32))
    rec = {"combo": combo["name"], "combo_idx": combo_idx, "arm": arm, "tag": tag,
           "zeta": zeta, "theta_truth": {g: float(theta_truth[i]) for i, g in enumerate(core.GNAMES)},
           "nuts": diag,
           "converged": bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02),
           "runtime_s": round(time.time() - t0, 2)}
    rec.update(res)
    return rec


def cell_path(combo_idx, arm, tag=""):
    return OUT / f"cell_{tag}{combo_idx}_{arm}.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--combos", default="1,2,3,4,5")
    ap.add_argument("--arms", default="M0,M1,M2,M3")
    args = ap.parse_args()

    nwarm, nsamp, nchain = (300, 300, 4) if args.smoke else (1000, 1000, 4)
    combos = [int(x) for x in args.combos.split(",")]
    arms = args.arms.split(",")

    model = core.load_model()
    ch = core.select_channels(model)
    freqs = core.freq_grid()
    cfg_path = OUT / "config.json"
    if not cfg_path.exists():
        core.write_config(cfg_path, model, ch,
                          extra={"informed_groups_expected": INFORMED_GROUPS,
                                 "n_observed": len(ch["observed"]), "n_heldout": len(ch["heldout"]),
                                 "inference_uses_true_corr_lengths": True,
                                 "note": "M2/M3 inference uses the injected Schneider correlation lengths "
                                         "(favorable to the correlated arm; mismatch tested in sensitivity)"})

    t_all = time.time()
    for ci in combos:
        for arm in arms:
            p = cell_path(ci, arm)
            if p.exists():
                print(f"[skip] {p.name}", flush=True)
                continue
            print(f"[run ] combo={ci} ({core.COMBOS[ci]['name']}) arm={arm} ...", flush=True)
            rec = run_cell(model, freqs, ch, ci, arm, nwarm, nsamp, nchain)
            json.dump(rec, open(p, "w"), indent=1)
            hc = rec["heldout_coverage"]
            print(f"       done {p.name}  rhat={rec['nuts']['max_rhat']:.3f} ess={rec['nuts']['min_ess']:.0f} "
                  f"div={rec['nuts']['div_frac']:.3f} cov[peak/band]={hc['peak']['frac']:.2f}/"
                  f"{hc['band']['frac']:.2f} sigd={rec['sigma_d']['med']:.3f} t={rec['runtime_s']}s",
                  flush=True)
    print(f"ALL CELLS in {time.time()-t_all:.1f}s", flush=True)


if __name__ == "__main__":
    main()
