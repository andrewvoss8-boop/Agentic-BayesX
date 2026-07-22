#!/usr/bin/env python3
"""Deterministic source, covariance, and modal-identifiability known answers."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

from common import REPO, WS, LF_HZ, LX_IN, R_SPLIT, SIGMA_E, read_json, write_json


def close(a, b, atol=1e-9, rtol=1e-8):
    return bool(np.isclose(a, b, atol=atol, rtol=rtol))


def main() -> None:
    t0 = time.time()
    legacy_root = REPO / "artifacts/reports/statfem_real_validation_20260617/out"
    expected = {
        "M0": {"rhat": 1.0001740560416237, "ess": 4716.189286380408, "gain": 5.915704023183557, "sigma_w": None},
        "M1": {"rhat": 1.0413275806963551, "ess": 47.13472134444741, "gain": 5.9155664355024244, "sigma_w": 1.864858922227092},
        "M2": {"rhat": 2.576851908501521, "ess": 0.7091361501220279, "gain": 6.044700417108461, "sigma_w": 12.374862353468146},
        "M3": {"rhat": 1.1115389438280825, "ess": 16.947800765213163, "gain": 6.680415782580342, "sigma_w": 12.597528699848802},
    }
    parsed, checks = {}, []
    for arm, exp in expected.items():
        d = read_json(legacy_root / f"tmcmc_faithful_{arm}_ident4_n8.json")
        rec = {"converged": d["converged"], "max_rhat": d["diag"]["max_rhat"],
               "min_ess": d["diag"]["min_ess"], "gain_c_median": d["gain_c"]["med"],
               "sigma_w_median": None if d["sigma_w"] is None else d["sigma_w"]["med"],
               "log_evidence_mean_legacy_tmcmc": d["diag"]["log_evidence_mean"]}
        parsed[arm] = rec
        ok = close(rec["max_rhat"], exp["rhat"]) and close(rec["min_ess"], exp["ess"])
        ok &= close(rec["gain_c_median"], exp["gain"])
        ok &= (rec["sigma_w_median"] is None if exp["sigma_w"] is None else close(rec["sigma_w_median"], exp["sigma_w"]))
        checks.append({"name": f"parse_{arm}", "pass": ok})

    dd = read_json(REPO / "artifacts/reports/shocksat_modelclass_L5_20260619/out/discrepancy_diagnostic.json")
    sp = read_json(REPO / "artifacts/reports/shocksat_modelclass_L5_20260619/out/spatial_reanalysis.json")
    diag_ok = dd["n_eligible"] == 77 and close(dd["gain_c"], 6.350241699172241)
    diag_ok &= close(dd["residual_db"]["median_abs"], 6.596152094410286)
    diag_ok &= close(dd["hard_accels"]["mean_abs_res_hard_db"], 17.452205490645362)
    diag_ok &= close(dd["hard_accels"]["mean_abs_res_rest_db"], 6.535379707426281)
    spatial_ok = sp["n"] == 77 and close(sp["region_categorical_R2_(nearest_feature)"], 0.036)
    spatial_ok &= close(sp["region_mean_abs_res_db"]["bolted_joint"], 12.3)
    checks += [{"name": "discrepancy_diagnostic", "pass": diag_ok}, {"name": "spatial_reanalysis", "pass": spatial_ok}]

    # Recompute covariance eigenvalues on the exact legacy M2 8-channel x 173-frequency geometry.
    src_code = REPO / "artifacts/reports/shocksat_modelclass_L5_20260619/code"
    sys.path.insert(0, str(src_code))
    import realfrf as rf  # type: ignore
    import schneider_faithful as sf  # type: ignore
    rmodel = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(rmodel, meas["daq"])
    _, freq_legacy, _, coord_legacy, _ = sf.select_observed(rmodel, meas, ch, 8)
    rff = sf.corr_freq_linear(freq_legacy, LF_HZ)
    rzz = sf.corr_space(coord_legacy, LX_IN)
    direct = R_SPLIT * np.kron(rff, np.eye(len(coord_legacy))) + (1 - R_SPLIT) * np.kron(np.eye(len(freq_legacy)), rzz)
    ev_direct = np.linalg.eigvalsh(direct)
    ef = np.linalg.eigvalsh(rff)
    ex = np.linalg.eigvalsh(rzz)
    ev_formula = np.sort((R_SPLIT * ef[:, None] + (1 - R_SPLIT) * ex[None, :]).ravel())
    probes = [0, len(ev_direct) // 2, len(ev_direct) - 1]
    recomps = []
    for idx, label in zip(probes, ["minimum", "median_order", "maximum"]):
        recomps.append({"label": label, "direct_eigh": float(ev_direct[idx]),
                        "independent_kronecker_formula": float(ev_formula[idx]),
                        "abs_difference": float(abs(ev_direct[idx] - ev_formula[idx])),
                        "pass": close(ev_direct[idx], ev_formula[idx], atol=2e-10, rtol=2e-10)})
    checks.append({"name": "three_covariance_eigenvalues", "pass": all(r["pass"] for r in recomps)})

    # Reproduce modal strain-energy fractions directly from reduced stiffness blocks.
    modal = REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609"
    rb = np.load(modal / "matrices/reduced_blocks.npz", allow_pickle=True)
    gnames = [str(x) for x in rb["gnames"]]
    a = np.asarray(rb["A"])
    afix = np.asarray(rb["A_fix"])
    lam = np.asarray(rb["nominal_eigvals"])
    frac = np.stack([np.diag(a[i]) for i in range(len(gnames))]) / lam[None, :]
    fix_frac = np.diag(afix) / lam
    pairing = read_json(modal / "pairing.json")
    pairs = {p["test_mode"]: p for p in pairing["pairs"]}
    calib = pairing["calib_test_modes"]
    midx = [pairs[t]["model_mode"] for t in calib]
    summary = {}
    for gi, name in enumerate(gnames):
        q = 100 * frac[gi, midx]
        summary[name] = {"mean_se_pct": float(q.mean()), "max_se_pct": float(q.max()),
                         "n_modes_gt1pct": int(np.sum(q > 1)), "n_modes_gt5pct": int(np.sum(q > 5))}
    stored_se = read_json(modal / "joint_strain_energy.json")
    max_dev = max(abs(summary[g]["mean_se_pct"] - stored_se["group_summary"][g]["mean_se_pct"]) for g in gnames)
    closure = float(np.mean(frac[:, midx].sum(axis=0) + fix_frac[midx]))
    strain_ok = max_dev < 1e-10 and abs(closure - 1.0) < 1e-8
    checks.append({"name": "modal_strain_energy_reproduction", "pass": strain_ok})

    # FIM in log-frequency space at the realized modal discrepancy floor.
    samples = np.load(modal / "nuts_full_samples.npz", allow_pickle=True)
    theta_draws = np.asarray(samples["theta"])
    log_cov = np.cov(np.log(theta_draws), rowvar=False)
    jf = 0.5 * frac[:, midx].T  # d log(f_i) / d log(theta_g)
    sigma_floor = float(read_json(modal / "theta_full.json")["sigma_f_median"])
    fim = jf.T @ jf / sigma_floor**2
    eval_c, evec_c = np.linalg.eigh(log_cov)
    sqrt_c = (evec_c * np.sqrt(np.clip(eval_c, 0, None))) @ evec_c.T
    info = sqrt_c @ fim @ sqrt_c
    val, vec = np.linalg.eigh(info)
    order = np.argsort(val)[::-1]
    val, vec = val[order], vec[:, order]
    raw = sqrt_c @ vec
    mixes = []
    for j in range(len(val)):
        w = raw[:, j]
        w = w / (np.max(np.abs(w)) + 1e-30)
        mixes.append({"eigenvalue_vs_prior_precision": float(val[j]),
                      "raw_parameter_mix": {g: float(w[i]) for i, g in enumerate(gnames)}})
    n_clear = int(np.sum(val > 1.0))
    checks.append({"name": "realized_floor_fim", "pass": np.all(np.isfinite(val)) and n_clear >= 1})

    # Finite contact perturbation distinguishes low sensitivity in-path from out-of-path.
    knom = afix + a.sum(axis=0)
    t = np.ones(len(gnames)); t[gnames.index("contact")] = 0.5
    ksoft = afix + np.einsum("g,gij->ij", t, a)
    l0 = np.linalg.eigvalsh(knom)
    l1 = np.linalg.eigvalsh(ksoft)
    fshift = np.abs(np.sqrt(np.clip(l1, 0, None)) / np.sqrt(np.clip(l0, 1e-30, None)) - 1.0)
    finite = {"parameter": "contact", "theta_from": 1.0, "theta_to": 0.5,
              "median_abs_frequency_shift_fraction": float(np.median(fshift)),
              "max_abs_frequency_shift_fraction": float(np.max(fshift)),
              "cause": "in load path but low sensitivity" if np.max(fshift) > 1e-5 else "out of load path candidate"}

    out = {
        "all_pass": all(c["pass"] for c in checks),
        "checks": checks,
        "legacy_M0_M3": parsed,
        "legacy_status_note": "M0 converged; M1-M3 are legacy TMCMC and non-converged, so their intervals remain not trustworthy",
        "frozen_residual_known_answers": {"discrepancy": dd, "spatial": sp},
        "deterministic_recomputations": {"count": len(recomps), "covariance_eigenvalues": recomps,
                                          "geometry": {"n_frequency": len(freq_legacy), "n_location": len(coord_legacy)}},
        "modal_identifiability": {
            "strain_energy_present": strain_ok,
            "closure_mean": closure,
            "max_mean_fraction_deviation_vs_stored": max_dev,
            "group_summary": summary,
            "realized_floor_fim_present": True,
            "sigma_f_floor": sigma_floor,
            "n_parameter_combinations_clearing_prior_precision": n_clear,
            "fim_eigenvalues_vs_prior_precision": val.tolist(),
            "strong_weak_parameter_mixes": mixes,
            "finite_perturbation": finite,
        },
        "runtime_s": time.time() - t0,
    }
    write_json(WS / "out/known_answers.json", out)
    print(f"KNOWN ANSWERS: {'PASS' if out['all_pass'] else 'FAIL'}; covariance eigen max diff "
          f"{max(r['abs_difference'] for r in recomps):.3e}; modal combinations > prior {n_clear}")


if __name__ == "__main__":
    main()
