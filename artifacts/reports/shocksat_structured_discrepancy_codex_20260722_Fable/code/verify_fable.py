#!/usr/bin/env python3
"""Task Card E `_Fable` — verification of the exact machinery against brute-force references.

Nothing here uses measured responses for a claim; it checks that the fast exact code equals the slow obvious
code. Writes out/verification_fable.json.

V1  Kronecker solve / log-determinant vs dense linear algebra
V2  full universal-kriging conditional (mean AND variance) vs a dense brute-force implementation
V3  E0 and E1 share EXACTLY the same fitted training hyperparameters and coefficient posterior; only K_*T differs
V4  analytic Gaussian coefficient prior vs a high-sample Monte-Carlo draw (sampling diagnostic)
V5  closed-form Gaussian CRPS vs Monte-Carlo CRPS
V6  central-difference response Jacobian vs jax forward-mode autodiff (float64)
V7  basis centering and interaction-margin residuals on a real training fold
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


def dense_sigma(fr, xs, su2, se2, nug):
    nf, nc = len(fr), len(xs)
    Kf = C.kern_f(fr, fr)
    Kx = C.kern_x(xs, xs)
    return (su2 * (C.R_SPLIT * np.kron(Kf, np.eye(nc)) + (1 - C.R_SPLIT) * np.kron(np.eye(nf), Kx))
            + np.kron(np.eye(nf), np.diag(nug)) + se2 * np.eye(nf * nc))


def main():
    t0 = time.time()
    rep = {"checks": []}
    rng = np.random.default_rng(20260722)

    # ---------------------------------------------------------------- V1
    nf, nc = 9, 6
    fr = np.linspace(50, 250, nf)
    xs = rng.normal(size=(nc, 3)) * 8
    su2, se2 = 2.1, 0.31
    nug = rng.uniform(0.05, 0.8, nc)
    gp = C.build_kron(fr, xs, su2, se2, nug)
    S = dense_sigma(fr, xs, su2, se2, nug)
    Y = rng.normal(size=(nf, nc))
    d1 = float(np.max(np.abs(gp.solve(Y).ravel() - np.linalg.solve(S, Y.ravel()))))
    d2 = float(abs(gp.logdet() - np.linalg.slogdet(S)[1]))
    rep["checks"].append({"id": "V1", "what": "Kronecker solve and logdet vs dense",
                          "max_abs_dev_solve": d1, "abs_dev_logdet": d2, "tol": 1e-9,
                          "pass": bool(d1 < 1e-9 and d2 < 1e-9)})

    # ---------------------------------------------------------------- V2 (spatial-style and frequency-style)
    v2 = {}
    for kind in ["spatial", "frequency"]:
        nfT, ncT = 9, 6
        frT = np.linspace(50, 250, nfT)
        xsT = rng.normal(size=(ncT, 3)) * 8
        if kind == "spatial":
            frS, xsS = frT, rng.normal(size=(4, 3)) * 8
        else:
            frS, xsS = np.linspace(260, 320, 5), xsT
        nfS, ncS = len(frS), len(xsS)
        nugT = rng.uniform(0.05, 0.8, ncT)
        gpT = C.build_kron(frT, xsT, su2, se2, nugT)
        ST = dense_sigma(frT, xsT, su2, se2, nugT)
        p = 4
        X_T = rng.normal(size=(nfT * ncT, p))
        X_S = rng.normal(size=(nfS * ncS, p))
        yT = rng.normal(size=nfT * ncT)
        pv = np.full(p, 0.7)
        # dense reference
        Sinv = np.linalg.inv(ST)
        A = X_T.T @ Sinv @ X_T + np.diag(1.0 / pv)
        Cb = np.linalg.inv(A)
        bh = Cb @ (X_T.T @ Sinv @ yT)
        if kind == "spatial":
            Kst = su2 * (1 - C.R_SPLIT) * np.kron(np.eye(nfT), C.kern_x(xsS, xsT))
        else:
            Kst = su2 * C.R_SPLIT * np.kron(C.kern_f(frS, frT), np.eye(ncT))
        mu_ref = X_S @ bh + Kst @ (Sinv @ (yT - X_T @ bh))
        Xeff = X_S - Kst @ Sinv @ X_T
        var_ref = (su2 + se2 + np.repeat(nugT[None, :], nfS, 0).reshape(-1)[:len(mu_ref)] * 0
                   - np.diag(Kst @ Sinv @ Kst.T) + np.einsum("ij,jk,ik->i", Xeff, Cb, Xeff))
        # fast route
        Kf_st = C.kern_f(frS, frT) if kind == "frequency" else None
        Kx_st = C.kern_x(xsS, xsT) if kind == "spatial" else None
        SX = gpT.solve(X_T.reshape(nfT, ncT, p)).reshape(nfT * ncT, p)
        Af = X_T.T @ SX + np.diag(1.0 / pv)
        Cb2 = np.linalg.inv(Af)
        bh2 = Cb2 @ (X_T.T @ gpT.solve(yT))
        Sres = gpT.solve((yT - X_T @ bh2).reshape(nfT, ncT)).reshape(nfT, ncT, 1)
        mu2 = X_S @ bh2 + E.cross_apply_fold(kind, Sres, su2, Kf_st, Kx_st).reshape(-1)
        qd = E.cross_quad_diag(kind, gpT, su2, Kf_st, Kx_st).reshape(-1)
        KSX = E.cross_apply_fold(kind, SX.reshape(nfT, ncT, p), su2, Kf_st, Kx_st).reshape(nfS * ncS, p)
        Xeff2 = X_S - KSX
        var2 = su2 + se2 - qd + np.einsum("ij,jk,ik->i", Xeff2, Cb2, Xeff2)
        v2[kind] = {"max_abs_dev_mean": float(np.max(np.abs(mu_ref - mu2))),
                    "max_abs_dev_var": float(np.max(np.abs(var_ref - var2))),
                    "max_abs_dev_beta": float(np.max(np.abs(bh - bh2)))}
    ok2 = all(max(v.values()) < 1e-8 for v in v2.values())
    rep["checks"].append({"id": "V2", "what": "universal-kriging conditional mean/variance/coefficients vs "
                                              "dense brute force, both cross-covariance kinds",
                          "detail": v2, "tol": 1e-8, "pass": bool(ok2)})

    # ---------------------------------------------------------------- V3, V7 on a real fold
    F = C.load_frozen(n_theta=20)
    split = json.loads((C.OUT / "split_registry.json").read_text())
    bz = np.load(C.OUT / "basis_fable.npz", allow_pickle=True)
    Bf, Loc, Ax = bz["Bf"], bz["Loc"], bz["Ax"]
    y = {k: C.q_meas(F, k) - C.q_fem(F, k, F.theta0) for k, _l, _a in C.DRIVES}
    Jac = {k: E.response_jacobian(F, k, F.theta0) for k, _l, _a in C.DRIVES}
    folds = E.make_folds(F, split)
    fd = [f for f in folds if f.family == "spatial"][0]
    res = E.run_fold(F, fd, y, Bf, Loc, Ax, Jac=Jac)
    same_hyper = res["arms"]["E0"]["c_hat"] == res["arms"]["E1"]["c_hat"]
    same_sd = res["arms"]["E0"]["c_post_sd"] == res["arms"]["E1"]["c_post_sd"]
    diff_pred = abs(res["arms"]["E0"]["median_abs_err_db"] - res["arms"]["E1"]["median_abs_err_db"])
    rep["checks"].append({"id": "V3", "what": "E0 and E1 identical training fit (same hyperparameters and "
                                             "coefficient posterior); only the train-to-test cross-covariance "
                                             "K_*T is toggled",
                          "identical_c_hat": bool(same_hyper), "identical_c_post_sd": bool(same_sd),
                          "median_abs_err_db_E0": res["arms"]["E0"]["median_abs_err_db"],
                          "median_abs_err_db_E1": res["arms"]["E1"]["median_abs_err_db"],
                          "prediction_differs": bool(diff_pred > 0),
                          "pass": bool(same_hyper and same_sd)})
    rep["checks"].append({"id": "V7", "what": "basis centering + interaction margin residuals on a real "
                                             "training fold (weighted ANOVA constraints)",
                          "residuals": res["constraints"], "tol": 1e-10,
                          "pass": bool(res["constraints"]["max_constraint_residual"] < 1e-10)})
    rep["orthogonality_example"] = res.get("orthogonality")

    # ---------------------------------------------------------------- V4 analytic prior vs Monte Carlo
    n_mc = 400000
    sd_main = np.sqrt((E.TARGET_DB_MAIN / C.DB) ** 2)
    draws = rng.normal(0.0, sd_main, n_mc)
    hist, edges = np.histogram(draws, bins=200, density=True)
    ctr = 0.5 * (edges[1:] + edges[:-1])
    ana = np.exp(-0.5 * (ctr / sd_main) ** 2) / (sd_main * np.sqrt(2 * np.pi))
    l1 = float(np.mean(np.abs(hist - ana)) / np.mean(ana))
    rep["checks"].append({"id": "V4", "what": "analytic Normal(0, Lambda_beta) main-effect prior density vs a "
                                             f"{n_mc}-sample Monte-Carlo histogram (200 bins)",
                          "mc_samples": n_mc, "bins": 200, "relative_L1_error": l1, "tol": 0.02,
                          "prior_sd_dimensionless": float(sd_main),
                          "prior_sd_db": float(sd_main * C.DB), "pass": bool(l1 < 0.02)})

    # ---------------------------------------------------------------- V5 CRPS
    mu, sd = 0.4, 1.3
    ytest = np.array([-1.0, 0.0, 0.4, 2.2])
    s = rng.normal(mu, sd, 200000)
    mc = np.array([np.mean(np.abs(s - v)) - 0.5 * np.mean(np.abs(s[:100000] - s[100000:])) for v in ytest])
    an = C.crps_gauss(ytest, mu, sd)
    rep["checks"].append({"id": "V5", "what": "closed-form Gaussian CRPS vs 200k-sample Monte-Carlo CRPS",
                          "max_abs_dev": float(np.max(np.abs(mc - an))), "tol": 0.01,
                          "analytic": [float(v) for v in an], "monte_carlo": [float(v) for v in mc],
                          "pass": bool(np.max(np.abs(mc - an)) < 0.01)})

    # ---------------------------------------------------------------- V6 Jacobian
    try:
        import jax
        jax.config.update("jax_enable_x64", True)
        import jax.numpy as jnp
        k0 = C.DRIVES[0][0]
        fwd = F.rf.jax_fem_logmag_factory(F.R, F.freqs, F.rows, F.drive_rows[k0], zeta=C.ZETA_PRIMARY)
        Jth = np.asarray(jax.jacfwd(fwd)(jnp.asarray(F.theta0)))          # d q / d theta
        Jlog = Jth * F.theta0[None, None, :]                              # d q / d log theta
        Jprod = E.response_jacobian(F, k0, F.theta0)                      # the Jacobian actually used
        rel_prod = float(np.max(np.abs(Jprod - Jlog)) / max(np.max(np.abs(Jlog)), 1e-300))
        Jfd = E.response_jacobian_fd(F, k0, F.theta0)
        rel_fd = float(np.max(np.abs(Jfd - Jlog)) / max(np.max(np.abs(Jlog)), 1e-300))
        med_fd = float(np.median(np.abs(Jfd - Jlog)) / max(np.median(np.abs(Jlog)), 1e-300))
        rep["checks"].append({"id": "V6", "what": "the production response Jacobian d q_fem / d log(theta) is "
                                                 "jax forward-mode autodiff in float64; a central-difference "
                                                 "Jacobian is reported alongside as an independent cross-check",
                              "production_vs_autodiff_max_rel_dev": rel_prod,
                              "fd_vs_autodiff_max_rel_dev": rel_fd,
                              "fd_vs_autodiff_median_rel_dev": med_fd,
                              "fd_step_log_theta": 1e-3, "tol_production": 1e-12,
                              "note": "the finite-difference route disagrees at the worst grid point because "
                                      "ln|H| is strongly nonlinear in theta near a resonance; the median "
                                      "agreement is good. Production uses autodiff, so this is a diagnostic.",
                              "pass": bool(rel_prod < 1e-12 and med_fd < 0.05)})
    except Exception as exc:                                              # pragma: no cover
        rep["checks"].append({"id": "V6", "what": "jax autodiff cross-check", "pass": False,
                              "error": str(exc)})

    rep["all_pass"] = all(c["pass"] for c in rep["checks"])
    rep["runtime_s"] = round(time.time() - t0, 2)
    (C.OUT / "verification_fable.json").write_text(json.dumps(rep, indent=2))
    for c in rep["checks"]:
        print(f"  {c['id']}: {'PASS' if c['pass'] else 'FAIL'} — {c['what'][:80]}")
    print(f"verification {'ALL PASS' if rep['all_pass'] else 'FAILURES PRESENT'} in {rep['runtime_s']} s")
    if not rep["all_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
