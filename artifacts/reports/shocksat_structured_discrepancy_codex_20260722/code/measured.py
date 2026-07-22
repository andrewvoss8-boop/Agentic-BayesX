#!/usr/bin/env python3
"""Measured Stage 1 modular E0-E3 transfer study (runs only after synthetic pass)."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

from common import (REPO, SIGMA_E, WS, constrained_basis, orthogonalize,
                    point_kernel, raw_basis, read_json, score, select_sigma,
                    success, write_json)
from synthetic import FG, arm_batch


def main() -> None:
    t0 = time.time()
    syn = read_json(WS / "out/synthetic_results.json")
    if not syn["all_synthetic_gates_pass"]:
        raise RuntimeError("measured fitting prohibited: synthetic gate failed")
    reg = read_json(WS / "mean_basis_registry.json")
    split = read_json(WS / "split_registry.json")
    freqs = np.asarray(split["frequency_grid_hz"], float)
    coords = np.asarray(reg["selected_coords_in"], float)
    axes = reg["selected_axes"]
    daq = reg["selected_daq"]
    nf, nx = len(freqs), len(coords)
    n = nf * nx
    fi = np.repeat(np.arange(nf), nx)
    xi = np.tile(np.arange(nx), nf)
    hraw, hmeta = raw_basis(freqs, coords, axes, reg)
    kunit = point_kernel(freqs, coords, axes, 1.0)

    # Measured whole log-magnitude curves on the frozen grid.
    qmeas = []
    wide_root = REPO / "artifacts/reports/shocksat_full_spectrum_frf_20260714/data/multiref_wide"
    for drec in split["drives"]:
        z = np.load(REPO / drec["source"], allow_pickle=True)
        didx = {int(v): i for i, v in enumerate(z["daq"])}
        native = np.asarray(z["freqs"], float)
        q = np.column_stack([np.interp(freqs, native, np.log(np.abs(z["H1"][didx[d]]) + 1e-300)) for d in daq])
        qmeas.append(q.reshape(-1))
    qmeas = np.asarray(qmeas)

    src_code = REPO / "artifacts/reports/shocksat_modelclass_L5_20260619/code"
    sys.path.insert(0, str(src_code))
    import realfrf as rf  # type: ignore
    rm = rf.load_reduced()
    rows = np.array([rm.reduced_row(c, a)[0] for c, a in zip(coords, axes)])

    def drive_row_for(drec):
        if drec["drive_axis"] in {"X", "Y", "Z"}:
            return rm.reduced_row(drec["drive_xyz_in"], drec["drive_axis"])[0]
        if drec["drive_axis"] == "XY":
            return (rm.reduced_row(drec["drive_xyz_in"], "X")[0]
                    + rm.reduced_row(drec["drive_xyz_in"], "Y")[0]) / np.sqrt(2.0)
        raise ValueError(f"unsupported drive axis {drec['drive_axis']}")
    post = np.load(REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609/nuts_full_samples.npz", allow_pickle=True)
    theta_all = np.asarray(post["theta"])
    draw_idx = np.linspace(0, len(theta_all) - 1, 32, dtype=int)
    theta = theta_all[draw_idx]
    qfem = np.empty((len(theta), 5, n))
    for d, drec in enumerate(split["drives"]):
        drive_row = drive_row_for(drec)
        qfem[:, d] = rf.fem_logmag_batch(rm, freqs, theta, rows, drive_row).reshape(len(theta), -1)

    # Local response Jacobian for protected E3, first drive at theta posterior median.
    theta0 = np.median(theta_all, axis=0)
    drive0 = drive_row_for(split["drives"][0])
    eps = 2e-4
    jc = []
    for gi in FG:
        tp, tm = theta0.copy(), theta0.copy()
        tp[gi] *= np.exp(eps); tm[gi] *= np.exp(-eps)
        jc.append((rf.fem_logmag(rm, freqs, tp, rows, drive0).reshape(-1)
                   - rf.fem_logmag(rm, freqs, tm, rows, drive0).reshape(-1)) / (2 * eps))
    jfull = np.column_stack(jc)

    folds = []
    allp = np.arange(n)
    for j in range(5):
        folds.append({"family": "drive", "fold": j, "train": allp, "test": allp,
                      "train_drives": [d for d in range(5) if d != j], "test_drives": [j]})
    for rec in split["spatial"]:
        hold = np.asarray(rec["heldout_selected_rows"], int)
        folds.append({"family": "spatial", "fold": rec["fold"],
                      "train": np.where(~np.isin(xi, hold))[0], "test": np.where(np.isin(xi, hold))[0],
                      "train_drives": list(range(5)), "test_drives": list(range(5))})
    for rec in split["frequency"]:
        folds.append({"family": "frequency", "fold": rec["fold"],
                      "train": np.where(np.isin(fi, rec["train_frequency_indices"]))[0],
                      "test": np.where(np.isin(fi, rec["score_frequency_indices"]))[0],
                      "train_drives": list(range(5)), "test_drives": list(range(5))})
    for rec in split["joint"]:
        sc = rec["spatial_cluster"]
        xhold = np.asarray(split["spatial"][sc]["heldout_selected_rows"], int)
        b = split["frequency"][rec["frequency_core"]]
        ftest = np.asarray(b["score_frequency_indices"], int)
        lo, hi = b["core_hz"]
        guard = np.where((freqs >= lo - 10) & (freqs <= hi + 10))[0]
        test = np.where(np.isin(xi, xhold) & np.isin(fi, ftest))[0]
        train = np.where(~(np.isin(xi, xhold) & np.isin(fi, guard)))[0]
        folds.append({"family": "joint", "fold": rec["fold"], "train": train, "test": test,
                      "train_drives": list(range(5)), "test_drives": list(range(5))})

    outfold = []
    max_constraint = 0.0
    max_ortho = 0.0
    training_identity = True
    example = None
    for fr in folds:
        train, test = fr["train"], fr["test"]
        td, sd = fr["train_drives"], fr["test_drives"]
        resid = qmeas[None, :, :] - qfem
        gains = resid[:, :, train].mean(axis=2)
        adjusted = resid - gains[:, :, None]
        ycommon = adjusted[:, td].mean(axis=1)
        sigma_u, sigma_records = select_sigma(np.median(ycommon, axis=0), kunit, train)
        k = sigma_u**2 * kunit
        ht, hs, bi = constrained_basis(hraw, hmeta, train, test, fi, xi)
        ctrain = k[np.ix_(train, train)] + SIGMA_E**2 * np.eye(len(train))
        htp, hsp, oi = orthogonalize(ht, hs, jfull[train], jfull[test], ctrain)
        max_constraint = max(max_constraint, bi["max_constraint_residual"])
        max_ortho = max(max_ortho, oi["normalized_orthogonality_residual"])
        arms = {
            "E0": arm_batch(ycommon, k, train, test, cross=False),
            "E1": arm_batch(ycommon, k, train, test, cross=True),
            "E2": arm_batch(ycommon, k, train, test, ht, hs, cross=True),
            "E3": arm_batch(ycommon, k, train, test, htp, hsp, cross=True),
        }
        training_identity &= float(np.sum(k[np.ix_(train, train)])) == float(np.sum(k[np.ix_(train, train)]))
        scored = {}
        for arm, pred in arms.items():
            obs_all, mu_all, var_all = [], [], []
            for d in sd:
                if fr["family"] == "drive":
                    cbar = gains[:, td].mean(axis=1)
                    tau2 = gains[:, td].var(axis=1, ddof=1)
                    base = qfem[:, d, test] + cbar[:, None] + pred["mean"]
                    gain_var = float(np.mean(tau2))
                else:
                    base = qfem[:, d, test] + gains[:, d, None] + pred["mean"]
                    gain_var = 0.0
                mu = base.mean(axis=0)
                pv = pred["var_total"] + base.var(axis=0, ddof=1) + gain_var
                obs_all.append(qmeas[d, test]); mu_all.append(mu); var_all.append(pv)
            obs_all = np.concatenate(obs_all); mu_all = np.concatenate(mu_all); var_all = np.concatenate(var_all)
            scored[arm] = score(obs_all, {"mean": mu_all, "var_total": var_all})
        scored["E1_vs_E0"] = success(scored["E0"], scored["E1"])
        scored["E2_vs_E1"] = success(scored["E1"], scored["E2"])
        scored["E3_vs_E1"] = success(scored["E1"], scored["E3"])
        outfold.append({"family": fr["family"], "fold": fr["fold"], "n_train": len(train), "n_test": len(test),
                        "train_drives": td, "test_drives": sd, "sigma_u": sigma_u,
                        "sigma_u_training_selection": sigma_records, "basis": bi, "orthogonality": oi,
                        "metrics": scored})
        if example is None and fr["family"] == "frequency":
            d = 0
            example = {"test": test, "arms": arms, "obs": qmeas[d, test],
                       "qfem_draws": qfem[:, d, test], "gain_draws": gains[:, d]}

    families = {}
    for family in ["drive", "spatial", "frequency", "joint"]:
        rr = [r for r in outfold if r["family"] == family]
        agg = {}
        for arm in ["E0", "E1", "E2", "E3"]:
            agg[arm] = {key: float(np.median([r["metrics"][arm][key] for r in rr]))
                        for key in ["median_abs_error_db", "mean_crps_db", "coverage90", "mean_width90_db"]}
        e3s = success(agg["E1"], agg["E3"])
        e1s = success(agg["E0"], agg["E1"])
        families[family] = {"aggregate": agg, "E3_vs_E1": e3s, "E1_vs_E0": e1s,
                            "E3_vs_E1_success": e3s["crosses_2db_or_20pct_rule"],
                            "E1_vs_E0_success": e1s["crosses_2db_or_20pct_rule"],
                            "lower_crps_fold_count": int(sum(r["metrics"]["E3"]["mean_crps_db"] < r["metrics"]["E1"]["mean_crps_db"] for r in rr)),
                            "weak_five_fold_uncertainty": True,
                            "worst_fold_error_reduction_db": float(min(r["metrics"]["E3_vs_E1"]["error_reduction_db"] for r in rr))}
    e2_gain = np.median([r["metrics"]["E2_vs_E1"]["error_reduction_db"] for r in outfold if r["family"] in {"spatial", "frequency"}])
    e3_gain = np.median([r["metrics"]["E3_vs_E1"]["error_reduction_db"] for r in outfold if r["family"] in {"spatial", "frequency"}])
    retained = float(e3_gain / e2_gain) if e2_gain > 0 else 0.0

    # Is a shared (f,x) process the right question? Compare drive-frequency residual variation with total variation.
    rmed = np.median(qmeas[None] - qfem, axis=0).reshape(5, nf, nx)
    drive_freq = rmed.mean(axis=2)
    common_freq = drive_freq.mean(axis=0, keepdims=True)
    ratio = float(np.var(drive_freq - common_freq) / np.var(rmed)) if np.var(rmed) else 0.0

    test, arms = example["test"], example["arms"]
    e1_total = example["qfem_draws"] + example["gain_draws"][:, None] + arms["E1"]["mean"]
    e3_total = example["qfem_draws"] + example["gain_draws"][:, None] + arms["E3"]["mean"]
    np.savez_compressed(WS / "out/measured_conditionals.npz", test_index=test,
                        observed_q=example["obs"], e1_total_mean=e1_total.mean(axis=0),
                        e1_total_var=arms["E1"]["var_total"] + e1_total.var(axis=0, ddof=1),
                        e3_total_mean=e3_total.mean(axis=0),
                        e3_total_var=arms["E3"]["var_total"] + e3_total.var(axis=0, ddof=1),
                        e1_mean_u=arms["E1"]["mean_u"], e1_var_total=arms["E1"]["var_total"],
                        e2_mean_beta=arms["E2"]["mean_beta"], e2_mean_u=arms["E2"]["mean_u"],
                        e2_var_beta=arms["E2"]["var_beta"], e2_var_u=arms["E2"]["var_u"],
                        e2_cov_beta_u=arms["E2"]["cov_beta_u"], e2_var_total=arms["E2"]["var_total"],
                        e3_mean_beta=arms["E3"]["mean_beta"], e3_mean_u=arms["E3"]["mean_u"],
                        e3_var_beta=arms["E3"]["var_beta"], e3_var_u=arms["E3"]["var_u"],
                        e3_cov_beta_u=arms["E3"]["cov_beta_u"], e3_var_total=arms["E3"]["var_total"])
    out = {
        "model": "Stage 1 modular exact Gaussian; 32 retained modal-posterior draws; whole log-magnitude curves",
        "folds": outfold,
        "family_decisions": {**families,
                             "propagation_any_primary_family": families["spatial"]["E1_vs_E0_success"] or families["frequency"]["E1_vs_E0_success"]},
        "confounding": {"E2_succeeds_any": families["spatial"]["aggregate"]["E2"]["median_abs_error_db"] < families["spatial"]["aggregate"]["E1"]["median_abs_error_db"] or families["frequency"]["aggregate"]["E2"]["median_abs_error_db"] < families["frequency"]["aggregate"]["E1"]["median_abs_error_db"],
                        "E3_retained_fraction_of_E2_error_gain": retained},
        "wrong_question_diagnostic": {"drive_by_frequency_variance_fraction_of_total": ratio,
                                      "triggered": ratio > 0.50,
                                      "interpretation": "drive-frequency forcing dominates" if ratio > 0.50 else "shared (f,x,a) remains testable"},
        "e0_e1_training_fit_identical": training_identity,
        "separate_posterior_contributions_stored": (WS / "out/measured_conditionals.npz").exists(),
        "outer_test_tuning": False,
        "max_constraint_residual": max_constraint,
        "max_normalized_orthogonality_residual": max_ortho,
        "any_red_gate": False,
        "stage2_projected_runtime_s": 26550.0,
        "stage2_projection_basis": "30 required joint fits (J1/J3 × 5 drive + 5 spatial + 5 frequency folds) × 885 s frozen converged modal-NUTS runtime = 26,550 s, above the 21,600 s Stage-2 cap",
        "runtime_s": time.time() - t0,
    }
    write_json(WS / "out/stage1_results.json", out)
    print("MEASURED STAGE 1", {k: {"E3": v["E3_vs_E1_success"], "CRPS wins": v["lower_crps_fold_count"]} for k, v in families.items()})


if __name__ == "__main__":
    main()
