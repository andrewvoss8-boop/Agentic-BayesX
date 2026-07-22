#!/usr/bin/env python3
"""Task Card E `_Fable` — synthetic gates S0-S3 on the REAL geometry and the REAL split design.

S0 null        m = 0                                     -> false-discovery control
S1 in-basis    dish-region +3 dB over 80-140 Hz, -2 dB low-frequency tilt (projected into the basis)
S2 out-of-basis smooth continuous spatial gradient + a narrow off-knot frequency feature
S3 confounded  a component aligned with the strongest theta sensitivity + an orthogonal component,
               scored with the local linear-Gaussian model r = J delta_eta + H beta + u + e (analytic)

>= 20 deterministic seeds per case. Writes out/synthetic_fable.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_fable as C  # noqa: E402
import engine_fable as E  # noqa: E402

N_SEEDS = 20
SEED_BASE = 20260722
FAMILIES = ("spatial", "frequency")
IDENT4 = [2, 4, 6, 8]          # bottom_box, cross_beam, plates, top_box (frozen calibrated groups)


# --------------------------------------------------------------------------- reference hyperparameters
def reference_hyper(F, y_meas):
    """Fit the zero-mean model ONCE on the whole measured set to get realistic simulation scales.

    These are simulation-design constants only: they set how noisy the synthetic worlds are. They are never
    reused as fitted values inside a synthetic fold (every synthetic fold refits its own hyperparameters).
    """
    fold = E.Fold("all", 0, "all data", [k for k, _l, _a in C.DRIVES], [], np.arange(F.Nf),
                  np.arange(F.Nc), np.arange(0), np.arange(0), "none")
    ytr = {d: y_meas[d] for d in fold.train_drives}
    return E.fit_hyper(ytr, fold, F)


def sample_field(rng, F, hyp):
    """One draw of u + e on the full grid for one drive (Kronecker square root, exact)."""
    gp = C.build_kron(F.freqs, F.coords, hyp["sigma_u2"], hyp["sigma_e2"], hyp["nugget_train"])
    Z = rng.standard_normal((F.Nf, F.Nc))
    return gp.Uf @ (np.sqrt(gp.d) * Z) @ gp.Ux.T


# --------------------------------------------------------------------------- truth generators
def truth_S1(F, Bf, Loc, Ax):
    """Dish-region +3 dB over 80-140 Hz plus a -2 dB low-frequency tilt, PROJECTED into the frozen basis."""
    dish = (F.region == C.REGION_NAMES.index("dish")).astype(float)
    w = ((F.freqs >= 80.0) & (F.freqs <= 140.0)).astype(float)
    tilt = np.clip((120.0 - F.freqs) / (120.0 - F.freqs[0]), 0, None)
    g = (3.0 / C.DB) * np.outer(w, dish) + (-2.0 / C.DB) * np.outer(tilt, np.ones(F.Nc))
    H, blocks = E.build_H(Bf, Loc, Ax, np.arange(F.Nf), np.arange(F.Nc),
                          Bf.mean(0), Loc.mean(0), Ax.mean(0))
    kept = E.gram_rank_keep(H)
    H = H[:, kept]
    beta, *_ = np.linalg.lstsq(H, g.reshape(-1), rcond=None)
    m = (H @ beta).reshape(F.Nf, F.Nc)
    rel = float(np.linalg.norm(g.reshape(-1) - m.reshape(-1)) / max(np.linalg.norm(g), 1e-300))
    return m, {"projection_relative_residual": rel,
               "note": "the injected S1 mean is the frozen-basis projection of the requested feature, so it "
                       "lies EXACTLY in the basis, as the coefficient-coverage gate requires",
               "requested_peak_db": 3.0, "requested_tilt_db": -2.0,
               "injected_peak_db": float(np.max(m) * C.DB), "injected_min_db": float(np.min(m) * C.DB)}


def truth_S2(F):
    """Out-of-basis: a smooth continuous spatial gradient + a narrow off-knot frequency feature."""
    z = F.coords[:, 2]
    grad = (z - z.mean()) / max(z.std(), 1e-9)
    f0 = 171.3                                     # deliberately between interior spline knots
    feat = np.exp(-0.5 * ((F.freqs - f0) / 5.0) ** 2)
    m = (2.5 / C.DB) * np.outer(np.ones(F.Nf), grad) + (4.0 / C.DB) * np.outer(feat, np.ones(F.Nc))
    m = m - m.mean()
    return m, {"spatial_gradient_db_per_sd_z": 2.5, "frequency_feature_center_hz": f0,
               "frequency_feature_width_hz": 5.0, "frequency_feature_db": 4.0,
               "note": "a 5 Hz Gaussian feature at 171.3 Hz cannot be represented by a 6-df cubic spline in "
                       "log f with knots at 46.8 / 78.9 / 133.1 / 258.4 Hz"}


def truth_S3(F, Jac, hyp, rng):
    """Confounded: a component aligned with the strongest theta sensitivity + an orthogonal component."""
    k0 = C.DRIVES[0][0]
    J = Jac[k0].reshape(F.Nf * F.Nc, 9)
    gp = C.build_kron(F.freqs, F.coords, hyp["sigma_u2"], hyp["sigma_e2"], hyp["nugget_train"])
    SJ = gp.solve(Jac[k0]).reshape(F.Nf * F.Nc, 9)
    JtWJ = J.T @ SJ
    ev, V = np.linalg.eigh(JtWJ)
    v1 = V[:, -1]                                  # strongest theta-sensitivity direction (W metric)
    aligned = (J @ v1).reshape(F.Nf, F.Nc)
    aligned = aligned / max(np.std(aligned), 1e-300)
    z = F.coords[:, 2]
    orth = np.outer(np.ones(F.Nf), (z - z.mean()) / max(z.std(), 1e-9))
    # remove the theta span from the "orthogonal" component in the W metric
    b = np.linalg.pinv(JtWJ, rcond=C.PINV_TOL) @ (SJ.T @ orth.reshape(-1))
    orth = (orth.reshape(-1) - J @ b).reshape(F.Nf, F.Nc)
    orth = orth / max(np.std(orth), 1e-300)
    m = (3.0 / C.DB) * aligned + (3.0 / C.DB) * orth
    return m, v1, {"aligned_component_db_rms": 3.0, "orthogonal_component_db_rms": 3.0,
                   "strongest_theta_direction_eigenvalue": float(ev[-1]),
                   "strongest_theta_direction_loadings": {F.gnames[i]: float(v1[i]) for i in range(9)}}


# --------------------------------------------------------------------------- family scoring
def family_stat(fold_results, arm):
    med = np.array([f["arms"][arm]["median_abs_err_db"] for f in fold_results])
    return {"median_abs_err_db": float(np.median(med)),
            "per_fold_median_abs_err_db": [float(v) for v in med],
            "coverage90": float(np.mean([f["arms"][arm]["coverage90"] for f in fold_results])),
            "width90_db": float(np.mean([f["arms"][arm]["width90_db"] for f in fold_results])),
            "crps_db": [float(f["arms"][arm]["crps_db"]) for f in fold_results]}


def crosses_success(base, arm):
    """Frozen 2 dB / 20% success rule (preregistration §6)."""
    d_err = base["median_abs_err_db"] - arm["median_abs_err_db"]
    d_cov = arm["coverage90"] - base["coverage90"]
    narrower = 1.0 - arm["width90_db"] / max(base["width90_db"], 1e-300)
    rule_a = (d_err >= 2.0) and (d_cov >= -0.02)
    rule_b = (narrower >= 0.20) and (abs(d_cov) <= 0.02)
    crps_wins = int(np.sum(np.array(arm["crps_db"]) < np.array(base["crps_db"])))
    return {"error_reduction_db": float(d_err), "coverage_change": float(d_cov),
            "width_narrowing_frac": float(narrower), "crps_wins_of_5": crps_wins,
            "rule_a_error": bool(rule_a), "rule_b_width": bool(rule_b),
            "crps_rule_met": bool(crps_wins >= 4),
            "crosses": bool((rule_a or rule_b) and crps_wins >= 4)}


# --------------------------------------------------------------------------- S3 analytic theta posterior
def s3_theta_posterior(F, Jac, hyp, y, Bf, Loc, Ax, Sigma_eta, use_perp):
    """Analytic joint (c_d, delta_eta, beta) posterior on the FULL training grid. Returns eta mean/sd."""
    fall, call = np.arange(F.Nf), np.arange(F.Nc)
    gp = C.build_kron(F.freqs, F.coords, hyp["sigma_u2"], hyp["sigma_e2"], hyp["nugget_train"])
    H, blocks = E.build_H(Bf, Loc, Ax, fall, call, Bf.mean(0), Loc.mean(0), Ax.mean(0))
    kept = E.gram_rank_keep(H)
    H = H[:, kept]
    lam = E.prior_var_for(blocks, kept)
    keys = [k for k, _l, _a in C.DRIVES]
    n = F.Nf * F.Nc
    if use_perp:
        JtWJ = np.zeros((9, 9))
        JtWH = np.zeros((9, H.shape[1]))
        for d in keys:
            Jd = Jac[d].reshape(n, 9)
            SJ = gp.solve(Jac[d]).reshape(n, 9)
            JtWJ += Jd.T @ SJ
            JtWH += SJ.T @ H
        b = np.linalg.pinv(JtWJ, rcond=C.PINV_TOL) @ JtWH
    nD, p_m = len(keys), H.shape[1]
    p = nD + 9 + p_m
    A = np.zeros((p, p))
    rhs = np.zeros(p)
    pv = np.concatenate([np.full(nD, hyp["tau_c2"]), np.ones(9), lam])
    pm = np.concatenate([np.full(nD, hyp["c_bar"]), np.zeros(9), np.zeros(p_m)])
    Pinv = np.diag(1.0 / pv)
    Pinv[nD:nD + 9, nD:nD + 9] = np.linalg.inv(Sigma_eta)
    A += Pinv
    rhs += Pinv @ pm
    for i, d in enumerate(keys):
        Z = np.zeros((n, nD))
        Z[:, i] = 1.0
        Xm = (H - Jac[d].reshape(n, 9) @ b) if use_perp else H
        Xd = np.concatenate([Z, Jac[d].reshape(n, 9), Xm], axis=1)
        SXd = gp.solve(Xd.reshape(F.Nf, F.Nc, p)).reshape(n, p)
        A += Xd.T @ SXd
        rhs += Xd.T @ gp.solve(y[d]).reshape(-1)
    Cov = np.linalg.inv(A)
    bh = Cov @ rhs
    return bh[nD:nD + 9], np.sqrt(np.diag(Cov)[nD:nD + 9])


def orth_residual_normalized(F, Jac, hyp):
    """||J^T W H_perp|| / (||J|| ||W H_perp||) — the card's normalised orthogonality residual."""
    fall, call = np.arange(F.Nf), np.arange(F.Nc)
    bz = np.load(C.OUT / "basis_fable.npz", allow_pickle=True)
    Bf, Loc, Ax = bz["Bf"], bz["Loc"], bz["Ax"]
    gp = C.build_kron(F.freqs, F.coords, hyp["sigma_u2"], hyp["sigma_e2"], hyp["nugget_train"])
    H, blocks = E.build_H(Bf, Loc, Ax, fall, call, Bf.mean(0), Loc.mean(0), Ax.mean(0))
    H = H[:, E.gram_rank_keep(H)]
    n = F.Nf * F.Nc
    keys = [k for k, _l, _a in C.DRIVES]
    JtWJ = np.zeros((9, 9))
    JtWH = np.zeros((9, H.shape[1]))
    for d in keys:
        Jd = Jac[d].reshape(n, 9)
        SJ = gp.solve(Jac[d]).reshape(n, 9)
        JtWJ += Jd.T @ SJ
        JtWH += SJ.T @ H
    b = np.linalg.pinv(JtWJ, rcond=C.PINV_TOL) @ JtWH
    d0 = keys[0]
    Jd = Jac[d0].reshape(n, 9)
    Hp = H - Jd @ b
    WHp = gp.solve(Hp.reshape(F.Nf, F.Nc, Hp.shape[1])).reshape(n, -1)
    num = np.linalg.norm(Jd.T @ WHp)
    den = np.linalg.norm(Jd) * np.linalg.norm(WHp)
    return float(num / max(den, 1e-300))


# --------------------------------------------------------------------------- main
def main():
    t0 = time.time()
    F = C.load_frozen(n_theta=60)
    split = json.loads((C.OUT / "split_registry.json").read_text())
    bz = np.load(C.OUT / "basis_fable.npz", allow_pickle=True)
    Bf, Loc, Ax = bz["Bf"], bz["Loc"], bz["Ax"]
    keys = [k for k, _l, _a in C.DRIVES]
    y_meas = {k: C.q_meas(F, k) - C.q_fem(F, k, F.theta0) for k in keys}
    Jac = {k: E.response_jacobian(F, k, F.theta0) for k in keys}
    hyp_ref = reference_hyper(F, y_meas)
    print(f"reference hyper (simulation scale): sigma_u={np.sqrt(hyp_ref['sigma_u2'])*C.DB:.2f} dB, "
          f"sigma_e={np.sqrt(hyp_ref['sigma_e2'])*C.DB:.2f} dB, tau_c={np.sqrt(hyp_ref['tau_c2'])*C.DB:.2f} dB")

    m_S1, meta_S1 = truth_S1(F, Bf, Loc, Ax)
    m_S2, meta_S2 = truth_S2(F)
    Sigma_eta = np.cov(np.log(F.theta_draws).T) + 1e-8 * np.eye(9)
    m_S3, v1, meta_S3 = truth_S3(F, Jac, hyp_ref, np.random.default_rng(0))

    folds = [f for f in E.make_folds(F, split) if f.family in FAMILIES]
    out = {"n_seeds": N_SEEDS, "seed_base": SEED_BASE, "families_scored": list(FAMILIES),
           "simulation_scales": {k: (float(hyp_ref[k]) if not isinstance(hyp_ref[k], (dict, np.ndarray))
                                     else None) for k in ["sigma_u2", "sigma_e2", "tau_c2", "c_bar", "s_nug"]},
           "simulation_scale_note": "reference hyperparameters fitted once on the WHOLE measured set so the "
                                    "synthetic worlds have a realistic noise level; every synthetic fold "
                                    "refits its own hyperparameters from its own training block",
           "truth_meta": {"S1": meta_S1, "S2": meta_S2, "S3": meta_S3},
           "cases": {}}

    truths = {"S0": np.zeros((F.Nf, F.Nc)), "S1": m_S1, "S2": m_S2, "S3": m_S3}

    for case in ["S0", "S1", "S2", "S3"]:
        m_true = truths[case]
        seeds = []
        for s in range(N_SEEDS):
            rng = np.random.default_rng(SEED_BASE + 1000 * ["S0", "S1", "S2", "S3"].index(case) + s)
            c_true = rng.normal(hyp_ref["c_bar"], np.sqrt(hyp_ref["tau_c2"]), len(keys))
            eta_true = rng.multivariate_normal(np.zeros(9), Sigma_eta) if case == "S3" else np.zeros(9)
            y = {}
            for i, k in enumerate(keys):
                base = c_true[i] + m_true + sample_field(rng, F, hyp_ref)
                if case == "S3":
                    base = base + Jac[k] @ eta_true
                y[k] = base
            rec = {"seed": int(SEED_BASE + 1000 * ["S0", "S1", "S2", "S3"].index(case) + s), "families": {}}
            for fam in FAMILIES:
                fr = [E.run_fold(F, fd, y, Bf, Loc, Ax, Jac=Jac,
                                 return_fields=(case == "S1"))
                      for fd in folds if fd.family == fam]
                stats = {a: family_stat(fr, a) for a in ["E0", "E1", "E2", "E3"]}
                rec["families"][fam] = {
                    "stats": stats,
                    "E2_vs_E1": crosses_success(stats["E1"], stats["E2"]),
                    "E3_vs_E1": crosses_success(stats["E1"], stats["E3"]),
                    "E1_vs_E0": crosses_success(stats["E0"], stats["E1"]),
                }
                if case == "S1":
                    cov_pts, tot = 0, 0
                    for fd, r in zip([f for f in folds if f.family == fam], fr):
                        pr = r["arms"]["E3"]["_fields"]
                        mt = m_true[np.ix_(fd.f_test, fd.c_test)].reshape(-1)
                        for d, pv in pr.items():
                            band = 1.6448536269514722 * np.sqrt(np.maximum(
                                pv["sd"] ** 2 - pv["theta_var"], 1e-12))
                            cov_pts += int(np.sum(np.abs(pv["m_struct"] + pv["u_star"] - mt) <= band))
                            tot += len(mt)
                    rec["families"][fam]["learned_mean_band_covers_injected_frac"] = float(cov_pts / max(tot, 1))
                for r in fr:
                    r["arms"]["E0"].pop("_fields", None)
                    for a in r["arms"]:
                        r["arms"][a].pop("_fields", None)
            if case == "S3":
                for tag, perp in [("E2", False), ("E3", True)]:
                    eh, es = s3_theta_posterior(F, Jac, hyp_ref, y, Bf, Loc, Ax, Sigma_eta, perp)
                    rec[f"theta_{tag}"] = {
                        "eta_hat": eh.tolist(), "eta_sd": es.tolist(),
                        "eta_true": eta_true.tolist(),
                        "abs_bias": np.abs(eh - eta_true).tolist(),
                        "covered90": [bool(abs(eh[i] - eta_true[i]) <= 1.6448536269514722 * es[i])
                                      for i in range(9)]}
            seeds.append(rec)
            print(f"  {case} seed {s+1}/{N_SEEDS} done ({time.time()-t0:.0f}s)", flush=True)
        out["cases"][case] = {"n_seeds": len(seeds), "seeds": seeds}

    # ----------------------------------------------------------------- gate evaluation
    def n_cross(case, arm):
        n = 0
        for sd in out["cases"][case]["seeds"]:
            if any(sd["families"][f][f"{arm}_vs_E1"]["crosses"] for f in FAMILIES):
                n += 1
        return n

    gates = {}
    fp = max(n_cross("S0", "E3"), 0)
    gates["S0_false_positive"] = {
        "threshold": "at most 1 of 20 seeds may make E3 cross the 2 dB / 20% rule versus E1",
        "observed_seeds_crossing": fp, "limit": 1, "pass": bool(fp <= 1),
        "E2_seeds_crossing": n_cross("S0", "E2")}

    s1_ok = 0
    s1_band = []
    for sd in out["cases"]["S1"]["seeds"]:
        crossed = any(sd["families"][f]["E3_vs_E1"]["crosses"] and
                      sd["families"][f]["E3_vs_E1"]["coverage_change"] >= -0.02 for f in FAMILIES)
        s1_ok += int(crossed)
        s1_band.append(float(np.mean([sd["families"][f]["learned_mean_band_covers_injected_frac"]
                                      for f in FAMILIES])))
    band_frac = float(np.mean(s1_band))
    gates["S1_recovery"] = {
        "threshold": "E3 crosses the rule with acceptable coverage in >=16 of 20 seeds AND its learned-mean "
                     "90% band covers the injected mean at >=85% of held-out grid points",
        "seeds_crossing": s1_ok, "limit": 16,
        "learned_mean_band_coverage_of_injected": band_frac, "band_limit": 0.85,
        "pass": bool(s1_ok >= 16 and band_frac >= 0.85)}

    d_med, worse = [], 0
    for sd in out["cases"]["S2"]["seeds"]:
        ds = [sd["families"][f]["E3_vs_E1"]["error_reduction_db"] for f in FAMILIES]
        d_med.append(float(np.mean(ds)))
        if min(ds) < -2.0:
            worse += 1
    gates["S2_robustness"] = {
        "threshold": "median E3-vs-E1 held-out error change across seeds favourable AND at most 2 of 20 seeds "
                     "worsen median absolute error by more than 2 dB",
        "median_error_reduction_db": float(np.median(d_med)), "seeds_worse_by_2db": worse, "limit": 2,
        "pass": bool(np.median(d_med) > 0 and worse <= 2)}

    b2 = np.array([[s["theta_E2"]["abs_bias"][i] for i in IDENT4] for s in out["cases"]["S3"]["seeds"]])
    b3 = np.array([[s["theta_E3"]["abs_bias"][i] for i in IDENT4] for s in out["cases"]["S3"]["seeds"]])
    cov3 = np.array([[s["theta_E3"]["covered90"][i] for i in IDENT4] for s in out["cases"]["S3"]["seeds"]])
    cov2 = np.array([[s["theta_E2"]["covered90"][i] for i in IDENT4] for s in out["cases"]["S3"]["seeds"]])
    red = 1.0 - np.median(b3) / max(np.median(b2), 1e-300)
    orth_n = orth_residual_normalized(F, Jac, hyp_ref)
    gates["S3_confounding"] = {
        "threshold": "E3 reduces median |delta_eta| bias by >=50% vs E2; every calibrated theta direction "
                     "reaches >=80% empirical 90% coverage; normalised orthogonality residual <= 1e-8",
        "calibrated_groups": [F.gnames[i] for i in IDENT4],
        "median_abs_bias_E2": float(np.median(b2)), "median_abs_bias_E3": float(np.median(b3)),
        "bias_reduction_frac": float(red), "bias_limit": 0.50,
        "coverage90_per_group_E3": {F.gnames[g]: float(cov3[:, j].mean()) for j, g in enumerate(IDENT4)},
        "coverage90_per_group_E2": {F.gnames[g]: float(cov2[:, j].mean()) for j, g in enumerate(IDENT4)},
        "min_coverage_E3": float(cov3.mean(axis=0).min()), "coverage_limit": 0.80,
        "orthogonality_residual_normalized": orth_n, "orthogonality_limit": 1e-8,
        "pass": bool(red >= 0.50 and cov3.mean(axis=0).min() >= 0.80 and orth_n <= 1e-8)}

    out["gates"] = gates
    out["all_gates_pass"] = all(g["pass"] for g in gates.values())
    out["runtime_s"] = round(time.time() - t0, 1)
    (C.OUT / "synthetic_fable.json").write_text(json.dumps(out, indent=2))
    print("\nSYNTHETIC GATES")
    for k, g in gates.items():
        print(f"  {k}: {'PASS' if g['pass'] else 'FAIL'}")
        for kk, vv in g.items():
            if kk not in ("threshold", "pass"):
                print(f"      {kk}: {vv}")
    print(f"all gates pass: {out['all_gates_pass']}  ({out['runtime_s']} s)")


if __name__ == "__main__":
    main()
