#!/usr/bin/env python3
"""
Does the held-out-SENSOR CV FRF correlation (al_rho_lo best remesh = 0.441 at oracle freq) SURVIVE Bayesian updating?
Andrew: score with FRF CORRELATION only (NOT held-out frequency).

Everything is the held-out-sensor CV metric (fit one complex amplitude+phase per mode on 90% of sensors, predict the
held-out 10%, 5-fold, median log|H| correlation on the held-out sensors). The ONLY thing that changes across rows is
where the resonance peaks are placed:
  * oracle      = measured per-mode frequencies (upper bound; "we know the true poles")
  * Bayes-median= theta-posterior MEDIAN frequencies from the modal-feature NUTS on the al_rho_lo reduced model
  * Bayes-post  = full theta posterior (per-draw frequencies) -> posterior-predictive CV correlation distribution
Damping for peak width = measured per-mode (same as the 0.441 run). Mode shapes Phi, pd = al_rho_lo (fixed; theta
scales stiffness -> moves frequencies, not the saved shapes). Baseline oracle CV printed for reference.

Reuses: combine_best.solve_edit/reduced_blocks (eigensolve + reduced blocks), heldout_sensor_cv.build_basis/_fit,
modal_feature.calibrate_modal (same NUTS, seed=0). ~5 min eigensolve + ~90 s NUTS.
"""
from __future__ import annotations
import json, sys, time
from types import SimpleNamespace
from pathlib import Path
import numpy as np

PSD = Path("/Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/shocksat_psd_envelope_twin_20260623")
sys.path.insert(0, str(PSD / "code"))
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "code"))
import rescore_sigma as RSC
import realfrf as rf
import modal_feature as mf
from modal_multiref import MODAL_REFS, CACHE
import combine_best as CB
from heldout_sensor_cv import build_basis, _fit, load_measured

OUT = HERE / "out"; OUT.mkdir(exist_ok=True)
t0 = time.time()
def log(m): print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)


def cv_from_B(B, Hdata, K=5, seed=0):
    """Held-out-sensor CV: fit per-mode amp on 90% cols, predict held-out 10%, median log|H| corr on held-out."""
    Nc, nm = B.shape[1], B.shape[2]; logHd = np.log(np.abs(Hdata) + 1e-30)
    rng = np.random.default_rng(seed); cors = []
    for fold in np.array_split(rng.permutation(Nc), K):
        ho = np.array(sorted(fold)); obs = np.array(sorted(set(range(Nc)) - set(ho.tolist())))
        a = _fit(B, Hdata, obs, nm); Hp = B[:, ho, :] @ a
        for k in range(len(ho)):
            cors.append(np.corrcoef(np.log(np.abs(Hp[:, k]) + 1e-30), logHd[:, ho[k]])[0, 1])
    return float(np.median(cors))


def cv_corr(Phi, pd, kidx, w, Hdata, wr_hz, eta_extra):
    return cv_from_B(build_basis(Phi, pd, kidx, w, wr_hz, eta_extra), Hdata)


def main():
    w, Hdata = load_measured()
    mfr = RSC.mm["freqs"]; mdp = RSC.mm["damp"] / 100.0
    rec = {"deliverable": "held-out-SENSOR CV FRF correlation: does the remesh gain survive Bayesian updating?",
           "metric": "fit per-mode amp on 90% sensors -> predict held-out 10%, median log|H| corr; peaks moved by theta"}

    # ---- baseline oracle CV (reference) ----
    zb = np.load(PSD / "out" / "edits" / "baseline" / "modes.npz", allow_pickle=True)
    jb = np.array([int(np.argmin(np.abs(mfr - x))) for x in zb["freqs_fem"]])
    rec["baseline_oracle_cv"] = round(cv_corr(zb["Phi"], zb["pd"], zb["kidx"], w, Hdata, mfr[jb], mdp[jb]), 3)
    log(f"baseline oracle CV = {rec['baseline_oracle_cv']}")

    # ---- al_rho_lo shapes (fixed) ----
    z = np.load(PSD / "out" / "edits" / CB.EDIT_ID / "modes.npz", allow_pickle=True)
    Phi, pd, kidx, ff = z["Phi"], z["pd"], z["kidx"], z["freqs_fem"]
    j = np.array([int(np.argmin(np.abs(mfr - x))) for x in ff])
    rec["remesh_oracle_cv"] = round(cv_corr(Phi, pd, kidx, w, Hdata, mfr[j], mdp[j]), 3)   # expect ~0.441
    log(f"al_rho_lo oracle CV = {rec['remesh_oracle_cv']}  (expect ~0.441)")

    # ---- eigensolve + reduced blocks (needed to turn theta -> frequencies) ----
    vals, vecs = CB.solve_edit()
    A_fix, A = CB.reduced_blocks(vecs); R2 = SimpleNamespace(A_fix=A_fix, A=A)
    el = np.array(kidx) - 6
    def f_of_theta(theta):
        lam = np.sort(np.clip(np.linalg.eigvalsh(A_fix + np.einsum("g,gij->ij", theta, A)), 1e-9, None))
        return (np.sqrt(lam) / (2 * np.pi))[el]

    # ---- re-run the SAME modal-feature NUTS on the al_rho_lo reduced model (seed=0) ----
    ch = rf.build_channels(rf.load_reduced(), [d for d in range(1, rf.N_ACCEL_RECORDERS + 1) if d not in rf.BAD_DAQ])
    pooled = {}
    for key in MODAL_REFS:
        c = dict(np.load(CACHE / f"{key}.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
        fq, _ = mf.extract_measured_modes(CB.meas_dict(c), SimpleNamespace(daq=ch.daq))
        for jm, hz in mf.match(R2, fq)[0]:
            pooled.setdefault(int(jm), []).append(float(hz))
    idx = np.array(sorted(pooled)); wmeas = np.array([np.median(pooled[m]) for m in idx])
    obs = ~(np.arange(len(idx)) % 5 == 4)
    tp, sw2, dg = mf.calibrate_modal(R2, idx[obs], wmeas[obs], fg=list(range(9)), seed=0,
                                     warmup=1000, samples=1000, chains=4)
    rec["nuts_convergence"] = {"max_rhat": round(dg["max_rhat"], 4), "min_ESS": round(float(dg["min_ess"]), 0),
                               "divergences": int(dg["divergences"]), "converged": bool(dg["converged"])}
    log(f"NUTS R-hat {dg['max_rhat']:.4f} ESS {dg['min_ess']:.0f} div {dg['divergences']}")

    # ---- Bayes-median CV ----
    rec["remesh_bayes_median_cv"] = round(cv_corr(Phi, pd, kidx, w, Hdata, f_of_theta(np.median(tp, 0)), mdp[j]), 3)
    log(f"al_rho_lo Bayes-median CV = {rec['remesh_bayes_median_cv']}")

    # ---- Bayes-posterior-predictive CV (per-draw frequencies) ----
    sub = np.linspace(0, len(tp) - 1, 60).astype(int)
    post = np.array([cv_corr(Phi, pd, kidx, w, Hdata, f_of_theta(tp[s]), mdp[j]) for s in sub])
    rec["remesh_bayes_posterior_cv"] = {"median": round(float(np.median(post)), 3),
                                        "p2.5": round(float(np.percentile(post, 2.5)), 3),
                                        "p97.5": round(float(np.percentile(post, 97.5)), 3), "n_draws": len(sub)}
    log(f"al_rho_lo Bayes-posterior CV = {rec['remesh_bayes_posterior_cv']}")

    rec["summary_FRF_corr_heldout_sensor_CV"] = {
        "baseline_oracle": rec["baseline_oracle_cv"], "remesh_oracle": rec["remesh_oracle_cv"],
        "remesh_bayes_median": rec["remesh_bayes_median_cv"],
        "remesh_bayes_posterior_median": rec["remesh_bayes_posterior_cv"]["median"]}
    (OUT / "combine_best_cv.json").write_text(json.dumps(rec, indent=2))
    print("\n" + json.dumps(rec["summary_FRF_corr_heldout_sensor_CV"], indent=2))
    print(f"\nDONE in {time.time()-t0:.0f}s -> out/combine_best_cv.json")


if __name__ == "__main__":
    main()
