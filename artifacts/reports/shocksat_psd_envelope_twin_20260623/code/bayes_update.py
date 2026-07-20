#!/usr/bin/env python3
"""Best Bayesian updating on the updated FEM (Andrew): the converged modal-feature NUTS — calibrate the 9 stiffness
groups θ from the POOLED clean multi-reference modal frequencies, with held-out-MODE frequency coverage (leave 20%
of matched modes out, predict them). Reports θ posterior, convergence (R-hat/ESS/div, all variables), and held-out
modal-frequency skill vs the nominal FEM. Output: out/bayes_update.json + console."""
from __future__ import annotations
import json, sys
from types import SimpleNamespace
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import score as SC
from modal_multiref import MODAL_REFS, CACHE


def meas_dict(c):
    H = c["H1"]
    dr = [float(np.abs(H[k]).max() ** 2 / (np.percentile(np.abs(H[k]) ** 2, 25) + 1e-300)) for k in range(H.shape[0])]
    return {"freqs": c["freqs"], "H": H, "daq": [int(d) for d in c["daq"]], "dyn_range": np.array(dr)}


def run(seed=0):
    R = rf.load_reduced()
    ch = rf.build_channels(R, [d for d in range(1, rf.N_ACCEL_RECORDERS + 1) if d not in rf.BAD_DAQ])
    pooled = {}
    for key in MODAL_REFS:
        c = dict(np.load(CACHE / f"{key}.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
        fq, _ = mf.extract_measured_modes(meas_dict(c), SimpleNamespace(daq=ch.daq))
        for jm, hz in mf.match(R, fq)[0]:
            pooled.setdefault(int(jm), []).append(float(hz))
    idx = np.array(sorted(pooled)); wmeas = np.array([np.median(pooled[m]) for m in idx])
    # held-out modes: every 5th
    ho = np.arange(len(idx)) % 5 == 4; obs = ~ho
    tp, sw2, dg = mf.calibrate_modal(R, idx[obs], wmeas[obs], seed=seed, warmup=1000, samples=1000, chains=4)
    sub = np.linspace(0, len(tp) - 1, 300).astype(int)
    femf_nom = mf.fem_modes_np(R, np.ones(9))
    cov, skill_num, skill_den = [], [], []
    for m, wm in zip(idx[ho], wmeas[ho]):
        fpred = np.array([mf.fem_modes_np(R, tp[s])[m] for s in sub])
        sc = SC.score_qoi(fpred, wm); cov.append(sc["covered"])
        skill_num.append(abs(np.median(fpred) - wm)); skill_den.append(abs(femf_nom[m] - wm))
    theta = {rf.GNAMES[g]: [round(float(np.percentile(tp[:, g], q)), 3) for q in (2.5, 50, 97.5)] for g in range(9)}
    rec = {"deliverable": "best Bayesian updating (modal-feature NUTS) on the updated FEM, clean multi-reference",
           "n_pooled_modes": len(idx), "n_observed": int(obs.sum()), "n_heldout_modes": int(ho.sum()),
           "convergence": {"max_rhat": round(dg["max_rhat"], 4), "min_ESS": round(dg["min_ess"], 0),
                           "divergences": dg["divergences"], "converged": dg["converged"], "chains": dg["n_chains"]},
           "sigma_w2_rel_median": round(float(np.median(sw2)), 4),
           "heldout_mode_freq_coverage": round(float(np.mean(cov)), 2),
           "heldout_freq_err_pct_calibrated": round(float(100 * np.mean(skill_num) / np.mean(wmeas[ho])), 2),
           "heldout_freq_err_pct_nominal": round(float(100 * np.mean(skill_den) / np.mean(wmeas[ho])), 2),
           "theta_posterior_2.5_50_97.5": theta}
    (Path(__file__).resolve().parent.parent / "out" / "bayes_update.json").write_text(json.dumps(rec, indent=2))
    print(json.dumps(rec, indent=2))
    print(f"\nCONVERGED={rec['convergence']['converged']} (R-hat {rec['convergence']['max_rhat']}, "
          f"ESS {rec['convergence']['min_ESS']}, div {rec['convergence']['divergences']})")
    print(f"held-out modal-freq coverage {rec['heldout_mode_freq_coverage']}; freq err calibrated "
          f"{rec['heldout_freq_err_pct_calibrated']}% vs nominal {rec['heldout_freq_err_pct_nominal']}%")
    return rec


if __name__ == "__main__":
    run()
