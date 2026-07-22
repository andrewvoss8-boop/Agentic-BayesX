#!/usr/bin/env python3
"""Run the preregistered S0-S3 exact-Gaussian synthetic gates."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve

from common import (DB_PER_LN, REPO, RANK_TOL, SIGMA_E, TAU_BETA, WS,
                    constrained_basis, crps_normal, orthogonalize, point_kernel,
                    raw_basis, read_json, region_labels, success, write_json)


FG = [2, 4, 6, 8]


def metrics(obs, mean, var):
    sd = np.sqrt(np.maximum(var, 1e-12))
    z = 1.6448536269514722
    return {
        "median_abs_error_db": float(np.median(np.abs(obs - mean)) * DB_PER_LN),
        "mean_crps_db": float(np.mean(crps_normal(obs, mean, sd)) * DB_PER_LN),
        "coverage90": float(np.mean(np.abs(obs - mean) <= z * sd)),
        "mean_width90_db": float(np.mean(2 * z * sd) * DB_PER_LN),
    }


def arm_batch(y, k, train, test, ht=None, hs=None, cross=True):
    kt = k[np.ix_(train, train)] + SIGMA_E**2 * np.eye(len(train))
    ks = k[np.ix_(test, train)] if cross else np.zeros((len(test), len(train)))
    yd = y[:, train].T
    if ht is None:
        cf = cho_factor(kt, lower=True, check_finite=False)
        alpha = cho_solve(cf, yd, check_finite=False)
        mu_u = (ks @ alpha).T
        sk = cho_solve(cf, ks.T, check_finite=False)
        vu = np.diag(k)[test] - np.sum(ks * sk.T, axis=1)
        vt = np.maximum(vu + SIGMA_E**2, 1e-12)
        return {"mean": mu_u, "mean_beta": np.zeros_like(mu_u), "mean_u": mu_u,
                "var_beta": np.zeros(len(test)), "var_u": np.maximum(vu, 0),
                "cov_beta_u": np.zeros(len(test)), "var_total": vt}
    lam = TAU_BETA**2 * np.eye(ht.shape[1])
    s = kt + ht @ lam @ ht.T
    cf = cho_factor(s, lower=True, check_finite=False)
    alpha = cho_solve(cf, yd, check_finite=False)
    bc = hs @ lam @ ht.T
    mb = (bc @ alpha).T
    mu = (ks @ alpha).T
    sb = cho_solve(cf, bc.T, check_finite=False)
    sk = cho_solve(cf, ks.T, check_finite=False)
    vb = np.sum((hs @ lam) * hs, axis=1) - np.sum(bc * sb.T, axis=1)
    vu = np.diag(k)[test] - np.sum(ks * sk.T, axis=1)
    cov = -np.sum(bc * sk.T, axis=1)
    vt = np.maximum(vb + vu + 2 * cov + SIGMA_E**2, 1e-12)
    return {"mean": mb + mu, "mean_beta": mb, "mean_u": mu,
            "var_beta": np.maximum(vb, 0), "var_u": np.maximum(vu, 0),
            "cov_beta_u": cov, "var_total": vt}


def main() -> None:
    t0 = time.time()
    reg = read_json(WS / "mean_basis_registry.json")
    split = read_json(WS / "split_registry.json")
    freqs = np.asarray(split["frequency_grid_hz"], float)
    coords = np.asarray(reg["selected_coords_in"], float)
    axes = reg["selected_axes"]
    nf, nx = len(freqs), len(coords)
    n = nf * nx
    fi = np.repeat(np.arange(nf), nx)
    xi = np.tile(np.arange(nx), nf)
    hraw, hmeta = raw_basis(freqs, coords, axes, reg)

    # Actual FEM sensitivity grid at the modal posterior median, first frozen drive.
    src_code = REPO / "artifacts/reports/shocksat_modelclass_L5_20260619/code"
    sys.path.insert(0, str(src_code))
    import realfrf as rf  # type: ignore
    rm = rf.load_reduced()
    rows = np.array([rm.reduced_row(c, a)[0] for c, a in zip(coords, axes)])
    d0 = split["drives"][0]
    drive_row = rm.reduced_row(d0["drive_xyz_in"], d0["drive_axis"])[0]
    theta_summary = read_json(REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609/theta_full.json")
    theta0 = np.array([theta_summary["theta_median"][g] for g in rf.GNAMES])
    eps = 2e-4
    jcols = []
    for gi in FG:
        tp, tm = theta0.copy(), theta0.copy()
        tp[gi] *= np.exp(eps); tm[gi] *= np.exp(-eps)
        qp = rf.fem_logmag(rm, freqs, tp, rows, drive_row).reshape(-1)
        qm = rf.fem_logmag(rm, freqs, tm, rows, drive_row).reshape(-1)
        jcols.append((qp - qm) / (2 * eps))
    jfull = np.column_stack(jcols)
    post = np.load(REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609/nuts_full_samples.npz", allow_pickle=True)
    prior_eta = np.cov(np.log(np.asarray(post["theta"])[:, FG]), rowvar=False)

    kunit = point_kernel(freqs, coords, axes, 1.0)
    sigma_syn = 0.60
    k = sigma_syn**2 * kunit
    cf_full = cho_factor(k + 1e-10 * np.eye(n), lower=True, check_finite=False)
    # Stable GP draws from the same covariance.
    lfull = np.tril(cf_full[0])
    regions = region_labels(coords)
    fmat = np.repeat(freqs[:, None], nx, axis=1)
    dish = np.tile((regions == "dish")[None, :], (nf, 1))
    target_s1_raw = ((3.0 / DB_PER_LN) * dish * ((fmat >= 80) & (fmat <= 140))
                     - (2.0 / DB_PER_LN) * np.clip((110.0 - fmat) / 65.0, 0, 1)).reshape(-1)
    # Project S1 to the full raw basis so coefficient coverage has a defined truth.
    b_s1, *_ = np.linalg.lstsq(hraw, target_s1_raw, rcond=RANK_TOL)
    target_s1 = hraw @ b_s1
    zc = (coords - coords.mean(axis=0)) / np.maximum(coords.std(axis=0), 1e-12)
    target_s2 = ((2.2 / DB_PER_LN) * np.tile(zc[:, 0], nf)
                 + (2.0 / DB_PER_LN) * np.repeat(np.exp(-0.5 * ((freqs - 173.0) / 8.0) ** 2), nx))

    ys = {"S0": [], "S1": [], "S2": []}
    truth = {"S0": np.zeros(n), "S1": target_s1, "S2": target_s2}
    for seed in range(20):
        rng = np.random.default_rng(seed)
        u = lfull @ rng.normal(size=n)
        e = rng.normal(0, SIGMA_E, n)
        for case in ys:
            ys[case].append(truth[case] + u + e)
    ys = {k_: np.asarray(v) for k_, v in ys.items()}

    folds = []
    for rec in split["spatial"]:
        xhold = np.asarray(rec["heldout_selected_rows"], int)
        test = np.where(np.isin(xi, xhold))[0]
        train = np.where(~np.isin(xi, xhold))[0]
        folds.append(("spatial", rec["fold"], train, test))
    for rec in split["frequency"]:
        ftest = np.asarray(rec["score_frequency_indices"], int)
        ftrain = np.asarray(rec["train_frequency_indices"], int)
        test = np.where(np.isin(fi, ftest))[0]
        train = np.where(np.isin(fi, ftrain))[0]
        folds.append(("frequency", rec["fold"], train, test))

    case_fold = {c: [] for c in ys}
    example = {}
    max_constraint = 0.0
    max_ortho = 0.0
    canonical = []
    learned_mean_cover = [[] for _ in range(20)]
    coefficient_cover = [[] for _ in range(20)]
    training_fingerprints = []
    for family, fold_id, train, test in folds:
        ht, hs, bi = constrained_basis(hraw, hmeta, train, test, fi, xi)
        max_constraint = max(max_constraint, bi["max_constraint_residual"])
        ctrain = k[np.ix_(train, train)] + SIGMA_E**2 * np.eye(len(train))
        htp, hsp, oi = orthogonalize(ht, hs, jfull[train], jfull[test], ctrain)
        max_ortho = max(max_ortho, oi["normalized_orthogonality_residual"])
        # Canonical correlations between whitened J and H subspaces.
        qj, _ = np.linalg.qr(jfull[train])
        qh, _ = np.linalg.qr(ht)
        canonical.append(np.linalg.svd(qj.T @ qh, compute_uv=False).tolist())
        for case in ys:
            e0 = arm_batch(ys[case], k, train, test, cross=False)
            e1 = arm_batch(ys[case], k, train, test, cross=True)
            e2 = arm_batch(ys[case], k, train, test, ht, hs, cross=True)
            e3 = arm_batch(ys[case], k, train, test, htp, hsp, cross=True)
            training_fingerprints.append({"case": case, "family": family, "fold": fold_id,
                                          "e0": float(np.sum(k[np.ix_(train, train)])),
                                          "e1": float(np.sum(k[np.ix_(train, train)]))})
            fold_rows = []
            for seed in range(20):
                obs = truth[case][test]
                row = {"seed": seed, "family": family, "fold": fold_id,
                       "E0": metrics(obs, e0["mean"][seed], e0["var_total"]),
                       "E1": metrics(obs, e1["mean"][seed], e1["var_total"]),
                       "E2": metrics(obs, e2["mean"][seed], e2["var_total"]),
                       "E3": metrics(obs, e3["mean"][seed], e3["var_total"])}
                row["E3_vs_E1"] = success(row["E1"], row["E3"])
                fold_rows.append(row)
                if case == "S1":
                    sdmean = np.sqrt(np.maximum(e3["var_beta"], 1e-12))
                    learned_mean_cover[seed].append(float(np.mean(np.abs(target_s1[test] - e3["mean_beta"][seed]) <= 1.6448536 * sdmean)))
                    # Conditional beta posterior and projection-defined coefficient truth.
                    lam = TAU_BETA**2 * np.eye(htp.shape[1])
                    ss = ctrain + htp @ lam @ htp.T
                    cf = cho_factor(ss, lower=True, check_finite=False)
                    vbeta = lam - lam @ htp.T @ cho_solve(cf, htp @ lam, check_finite=False)
                    bmean = lam @ htp.T @ cho_solve(cf, ys[case][seed, train], check_finite=False)
                    btruth, *_ = np.linalg.lstsq(np.vstack([htp, hsp]), target_s1[np.r_[train, test]], rcond=RANK_TOL)
                    coefficient_cover[seed].append(float(np.mean(np.abs(btruth - bmean) <= 1.6448536 * np.sqrt(np.maximum(np.diag(vbeta), 0)))))
            case_fold[case].append({"family": family, "fold": fold_id, "basis": bi, "orthogonality": oi, "seeds": fold_rows})
            if case == "S1" and family == "spatial" and fold_id == 0:
                example = {"test": test, "truth": truth[case][test], "E1": e1, "E2": e2, "E3": e3}

    # Aggregate fold-level independent units for each seed.
    cases_out = {}
    for case in ["S0", "S1", "S2"]:
        seed_rows = []
        for seed in range(20):
            rows_seed = [f["seeds"][seed] for f in case_fold[case]]
            agg = {}
            for arm in ["E0", "E1", "E2", "E3"]:
                agg[arm] = {k_: float(np.median([r[arm][k_] for r in rows_seed]))
                            for k_ in ["median_abs_error_db", "mean_crps_db", "coverage90", "mean_width90_db"]}
            agg["seed"] = seed
            agg["E3_vs_E1"] = success(agg["E1"], agg["E3"])
            if case == "S1":
                agg["learned_mean_coverage90_heldout"] = float(np.mean(learned_mean_cover[seed]))
                agg["coefficient_coverage90"] = float(np.mean(coefficient_cover[seed]))
            seed_rows.append(agg)
        cases_out[case] = {"seeds": seed_rows, "fold_detail": case_fold[case]}

    # S3: joint linear-Gaussian posterior on one full-grid realization per seed.
    c = k + SIGMA_E**2 * np.eye(n)
    cf_c = cho_factor(c, lower=True, check_finite=False)
    # Full-grid constrained basis and local orthogonal version.
    all_idx = np.arange(n)
    ht, _, bi = constrained_basis(hraw, hmeta, all_idx, np.array([], int), fi, xi)
    # Empty-test call cannot extrapolate offsets; only training H is needed here.
    wj = cho_solve(cf_c, jfull, check_finite=False)
    wh = cho_solve(cf_c, ht, check_finite=False)
    aorth = np.linalg.pinv(jfull.T @ wj, rcond=RANK_TOL) @ (jfull.T @ wh)
    hp = ht - jfull @ aorth
    ortho_resid = np.linalg.norm(jfull.T @ cho_solve(cf_c, hp, check_finite=False))
    ortho_denom = np.linalg.norm(jfull) * np.linalg.norm(cho_solve(cf_c, hp, check_finite=False))
    ortho_norm = float(ortho_resid / ortho_denom)
    max_ortho = max(max_ortho, ortho_norm)
    # Inject an explicitly theta-aligned discrepancy plus an orthogonal mean component.
    u1, s1, _ = np.linalg.svd(np.linalg.solve(np.linalg.cholesky(c), jfull), full_matrices=False)
    aligned = jfull @ (np.linalg.eigh(prior_eta)[1][:, -1])
    aligned *= (1.0 / DB_PER_LN) / (np.std(aligned) + 1e-30)
    rng0 = np.random.default_rng(20260722)
    b0 = rng0.normal(0, 0.18, hp.shape[1])
    orthcomp = hp @ b0
    orthcomp *= (1.0 / DB_PER_LN) / (np.std(orthcomp) + 1e-30)
    s3_truth = aligned + orthcomp

    def joint_posterior(h, y):
        x = np.column_stack([jfull, h])
        p = np.zeros((x.shape[1], x.shape[1]))
        p[:4, :4] = prior_eta
        p[4:, 4:] = TAU_BETA**2 * np.eye(h.shape[1])
        cinvx = cho_solve(cf_c, x, check_finite=False)
        v = np.linalg.inv(np.linalg.inv(p) + x.T @ cinvx)
        m = v @ x.T @ cho_solve(cf_c, y, check_finite=False)
        return m[:4], v[:4, :4]

    s3rows = []
    cover2 = np.zeros(4); cover3 = np.zeros(4)
    for seed in range(20):
        rng = np.random.default_rng(1000 + seed)
        u = lfull @ rng.normal(size=n)
        y = s3_truth + u + rng.normal(0, SIGMA_E, n)
        m2, v2 = joint_posterior(ht, y)
        m3, v3 = joint_posterior(hp, y)
        c2 = np.abs(m2) <= 1.6448536 * np.sqrt(np.diag(v2))
        c3 = np.abs(m3) <= 1.6448536 * np.sqrt(np.diag(v3))
        cover2 += c2; cover3 += c3
        s3rows.append({"seed": seed, "E2_median_abs_delta_eta_bias": float(np.median(np.abs(m2))),
                       "E3_median_abs_delta_eta_bias": float(np.median(np.abs(m3))),
                       "E2_eta_mean": m2.tolist(), "E3_eta_mean": m3.tolist(),
                       "E2_coverage": c2.tolist(), "E3_coverage": c3.tolist()})
    cases_out["S3"] = {"seeds": s3rows, "theta_coverage_E2": (cover2 / 20).tolist(),
                         "theta_coverage_E3": (cover3 / 20).tolist(),
                         "normalized_orthogonality_residual": ortho_norm,
                         "injection": "1 dB RMS aligned with strongest modal-prior theta direction plus 1 dB RMS H_perp component"}

    # Frozen gate evaluation.
    fp = sum(r["E3_vs_E1"]["crosses_2db_or_20pct_rule"] for r in cases_out["S0"]["seeds"])
    s1_success = sum(r["E3_vs_E1"]["crosses_2db_or_20pct_rule"] and r["E3"]["coverage90"] >= 0.85
                     for r in cases_out["S1"]["seeds"])
    s1_mean_cov = float(np.mean([r["learned_mean_coverage90_heldout"] for r in cases_out["S1"]["seeds"]]))
    s2_change = [r["E3_vs_E1"]["error_reduction_db"] for r in cases_out["S2"]["seeds"]]
    s2_bad = int(np.sum(np.asarray(s2_change) < -2.0))
    b2 = np.median([r["E2_median_abs_delta_eta_bias"] for r in s3rows])
    b3 = np.median([r["E3_median_abs_delta_eta_bias"] for r in s3rows])
    s3_reduction = float(1 - b3 / b2) if b2 else 0.0
    s3_cov = np.asarray(cases_out["S3"]["theta_coverage_E3"])
    gates = {
        "S0": {"threshold": "false positives <=1/20", "observed_false_positives": fp, "pass": fp <= 1},
        "S1": {"threshold": "success >=16/20 and learned-mean coverage >=0.85", "observed_successes": s1_success,
               "observed_learned_mean_coverage": s1_mean_cov, "pass": s1_success >= 16 and s1_mean_cov >= 0.85},
        "S2": {"threshold": "median favorable and <=2 seeds worsen >2 dB", "observed_median_error_reduction_db": float(np.median(s2_change)),
               "observed_worse_than_minus2db_count": s2_bad, "pass": bool(np.median(s2_change) > 0 and s2_bad <= 2)},
        "S3": {"threshold": "theta bias reduction >=0.50, every coverage >=0.80, orthogonality <=1e-8",
               "observed_bias_reduction_fraction": s3_reduction, "observed_theta_coverage": s3_cov.tolist(),
               "observed_orthogonality": ortho_norm,
               "pass": bool(s3_reduction >= 0.50 and np.all(s3_cov >= 0.80) and ortho_norm <= 1e-8)},
    }
    all_pass = all(v["pass"] for v in gates.values())

    # Retain one auditable conditional with contributions separated.
    np.savez_compressed(WS / "out/synthetic_conditionals.npz", test_index=example["test"], truth=example["truth"],
                        e1_mean=example["E1"]["mean"][0], e1_var=example["E1"]["var_total"],
                        e2_mean_beta=example["E2"]["mean_beta"][0], e2_mean_u=example["E2"]["mean_u"][0],
                        e2_var_beta=example["E2"]["var_beta"], e2_var_u=example["E2"]["var_u"],
                        e2_cov_beta_u=example["E2"]["cov_beta_u"], e2_var_total=example["E2"]["var_total"],
                        e3_mean_beta=example["E3"]["mean_beta"][0], e3_mean_u=example["E3"]["mean_u"][0],
                        e3_var_beta=example["E3"]["var_beta"], e3_var_u=example["E3"]["var_u"],
                        e3_cov_beta_u=example["E3"]["cov_beta_u"], e3_var_total=example["E3"]["var_total"])
    out = {
        "model": "exact Gaussian conditionals; analytic beta posterior; no sampler",
        "geometry": {"n_frequency": nf, "n_channel": nx, "n_points": n, "folds": len(folds)},
        "cases": cases_out,
        "gates": gates,
        "all_synthetic_gates_pass": all_pass,
        "e0_e1_training_fit_identical": all(x["e0"] == x["e1"] for x in training_fingerprints),
        "separate_posterior_contributions_stored": (WS / "out/synthetic_conditionals.npz").exists(),
        "max_constraint_residual": max_constraint,
        "max_normalized_orthogonality_residual": max_ortho,
        "canonical_correlations_theta_mean_basis": canonical,
        "s1_projection_max_abs_error_db": float(np.max(np.abs(target_s1 - target_s1_raw)) * DB_PER_LN),
        "runtime_s": time.time() - t0,
    }
    write_json(WS / "out/synthetic_results.json", out)
    print("SYNTHETIC", "PASS" if all_pass else "STOP", json.dumps(gates, indent=2))


if __name__ == "__main__":
    main()
