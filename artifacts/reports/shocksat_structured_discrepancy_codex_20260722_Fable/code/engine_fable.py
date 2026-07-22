#!/usr/bin/env python3
"""Task Card E `_Fable` — the exact Stage-1 arm engine (E0/E1/E2/E3).

Everything here is an EXACT Gaussian conditional. No sampler is used (card: "Do not invoke NUTS in Stage 1").

Model on the raw residual  y(d,f,c) = q_meas - q_fem(theta_0):

    y = c_d + H(f,x,a) beta + u_d(f,x,a) + e
    c_d  ~ N(c_bar, tau_c^2)      per-drive log-gain, learned from TRAINING drives only
    beta ~ N(0, Lambda_beta)      structured-mean coefficients, zero-centred PRIOR (the fitted CONDITIONAL
                                  mean E[H beta | train] is generally non-zero and is stored separately)
    u_d  ~ GP(0, K_fx)            independent realisation per drive (decisions_log F2)
    e    ~ N(0, sigma_e^2)        + per-channel excess nugget

K_fx = sigma_u^2 [ r K_f(df; l_f) (x) I_x + (1-r) I_f (x) K_x(dx; l_x) ]  (frozen Schneider-style additive form)

Arms
----
E0  zero mean, K_*T forced to zero      -> current-style marginal discrepancy
E1  zero mean, exact Gaussian conditional with K_*T
E2  H beta + u, universal kriging, SAME covariance as E1
E3  as E2 with the locally theta-orthogonal basis H_perp = P_perp H

E0/E1 share the fitted training hyperparameters exactly; E2/E3 reuse them unchanged.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_fable as C  # noqa: E402

# frozen coefficient-prior scales (mean_basis_registry.json)
TARGET_DB_MAIN = 6.0
TARGET_DB_INT = 3.0
TAU_C_FLOOR = 1e-4
NUG_FLOOR = 1e-8


# ------------------------------------------------------------------------------ design construction
def build_H(Bf, Loc, Ax, f_idx, c_idx, center_f=None, center_l=None, center_a=None):
    """Mean-basis design on the complete grid f_idx x c_idx, C-order (f outer, c inner).

    Returns (H, blocks) with blocks = list of (name, slice). Centering vectors, if given, are SUBTRACTED
    (these come from the TRAINING grid; the same vectors are reused at held-out points so the constrained
    basis is a single fixed function, not a re-fit).
    """
    B = Bf[f_idx]                                   # (nf, kf)
    L = Loc[c_idx]                                  # (nc, kl)
    A = Ax[c_idx]                                   # (nc, ka)
    if center_f is not None:
        B = B - center_f[None, :]
    if center_l is not None:
        L = L - center_l[None, :]
    if center_a is not None:
        A = A - center_a[None, :]
    nf, nc = len(f_idx), len(c_idx)
    kf, kl, ka = B.shape[1], L.shape[1], A.shape[1]
    cols = []
    cols.append(np.repeat(B, nc, axis=0))                                   # frequency main
    cols.append(np.tile(L, (nf, 1)))                                        # location main
    cols.append(np.tile(A, (nf, 1)))                                        # axis main
    inter = (np.repeat(B, nc, axis=0)[:, :, None] * np.tile(L, (nf, 1))[:, None, :]).reshape(nf * nc, kf * kl)
    cols.append(inter)                                                      # frequency x location tensor
    H = np.concatenate(cols, axis=1)
    blocks = [("frequency", slice(0, kf)), ("location", slice(kf, kf + kl)),
              ("axis", slice(kf + kl, kf + kl + ka)),
              ("interaction", slice(kf + kl + ka, kf + kl + ka + kf * kl))]
    return H, blocks


def gram_rank_keep(H, tol=C.RANK_TOL):
    """Deterministic left-to-right column keep-set using the column-normalised Gram matrix."""
    p = H.shape[1]
    if p == 0:
        return np.arange(0)
    s = np.maximum(np.linalg.norm(H, axis=0), 1e-300)
    G = (H / s).T @ (H / s)
    kept = []
    for j in range(p):
        trial = kept + [j]
        ev = np.linalg.eigvalsh(G[np.ix_(trial, trial)])
        if ev[0] / max(ev[-1], 1e-300) > tol:
            kept = trial
    return np.array(kept, dtype=int)


def prior_var_for(blocks, kept):
    """Lambda_beta diagonal, frozen: 6 dB scale on main effects, 3 dB on the interaction."""
    v = np.zeros(sum(b.stop - b.start for _n, b in blocks))
    for name, sl in blocks:
        tgt = TARGET_DB_INT if name == "interaction" else TARGET_DB_MAIN
        v[sl] = (tgt / C.DB) ** 2
    return v[kept]


# ------------------------------------------------------------------------------ fold specification
@dataclass
class Fold:
    family: str
    fold: int
    name: str
    train_drives: list      # drive keys with training data
    test_drives: list       # drive keys scored
    f_train: np.ndarray
    c_train: np.ndarray
    f_test: np.ndarray
    c_test: np.ndarray
    cross_kind: str         # 'none' | 'spatial' | 'frequency'


def make_folds(F, split):
    folds = []
    allf = np.arange(F.Nf)
    allc = np.arange(F.Nc)
    keys = [k for k, _l, _a in C.DRIVES]

    for i, k in enumerate(keys):
        folds.append(Fold("drive", i, f"leave-out {k}", [x for x in keys if x != k], [k],
                          allf, allc, allf, allc, "none"))

    cl = np.asarray(np.load(C.OUT / "basis_fable.npz")["cluster"])
    for j in range(C.N_SPATIAL_CLUSTERS):
        cte = np.flatnonzero(cl == j)
        ctr = np.flatnonzero(cl != j)
        folds.append(Fold("spatial", j, f"leave-out spatial cluster {j}", keys, keys,
                          allf, ctr, allf, cte, "spatial"))

    for j, core in enumerate(split["family_3_frequency"]["cores"]):
        fte = np.array(core["core_line_idx"])
        ftr = np.setdiff1d(allf, np.array(core["excluded_from_training_line_idx"]))
        folds.append(Fold("frequency", j, f"leave-out frequency core {j} "
                                          f"({core['core_hz'][0]:.0f}-{core['core_hz'][1]:.0f} Hz)",
                          keys, keys, ftr, allc, fte, allc, "frequency"))

    for pr in split["family_4_joint"]["pairs"]:
        j_s, j_f = pr["spatial_cluster"], pr["frequency_core"]
        core = split["family_3_frequency"]["cores"][j_f]
        fte = np.array(core["core_line_idx"])
        ftr = np.setdiff1d(allf, np.array(core["excluded_from_training_line_idx"]))
        cte = np.flatnonzero(cl == j_s)
        ctr = np.flatnonzero(cl != j_s)
        folds.append(Fold("joint", pr["pair"], f"leave-out cluster {j_s} x core {j_f}", keys, keys,
                          ftr, ctr, fte, cte, "none"))
    return folds


# ------------------------------------------------------------------------------ hyperparameter fit (training only)
def fit_hyper(y_tr, fold: Fold, F, verbose=False):
    """Exact restricted-ML fit of (sigma_u^2, s_nug) on the TRAINING block only, frozen r/l_f/l_x.

    y_tr: dict drive -> (nf, nc) training residual grid.
    Returns dict of hyperparameters + the per-channel variance profile.
    """
    fr = F.freqs[fold.f_train]
    xs = F.coords[fold.c_train]
    D = list(y_tr)
    # per-drive log-gain (robust) -> c_bar, tau_c
    c_hat = np.array([np.median(y_tr[d]) for d in D])
    c_bar = float(np.mean(c_hat))
    tau_c2 = float(max(np.var(c_hat, ddof=1) if len(c_hat) > 1 else 0.0, TAU_C_FLOOR))
    Yc = {d: y_tr[d] - c_hat[i] for i, d in enumerate(D)}

    # per-channel variance profile from training residuals of THIS fold (mean 1)
    v = np.mean([np.mean(Yc[d] ** 2, axis=0) for d in D], axis=0)
    p = v / max(np.mean(v), 1e-300)
    p_min = float(p.min())

    def nll(par):
        su2 = float(np.exp(par[0]))
        snug = float(np.exp(par[1]))
        se2 = snug * p_min
        nug = snug * (p - p_min) + NUG_FLOOR
        gp = C.build_kron(fr, xs, su2, se2, nug)
        ld = gp.logdet()
        tot = 0.0
        for d in D:
            Y = Yc[d]
            tot += float(np.sum(Y * gp.solve(Y))) + ld
        return 0.5 * tot

    x0 = np.array([np.log(max(np.mean(v), 1e-6)), np.log(max(np.mean(v), 1e-6))])
    res = minimize(nll, x0, method="Nelder-Mead",
                   options={"xatol": 1e-3, "fatol": 1e-2, "maxiter": 200})
    su2 = float(np.exp(res.x[0]))
    snug = float(np.exp(res.x[1]))
    hyp = {"sigma_u2": su2, "s_nug": snug, "sigma_e2": snug * p_min,
           "nugget_train": snug * (p - p_min) + NUG_FLOOR,
           "nugget_heldout": float(snug * (np.median(p) - p_min) + NUG_FLOOR),
           "p_profile_mean1": p, "p_min": p_min,
           "c_bar": c_bar, "tau_c2": tau_c2, "c_hat_train": {d: float(c_hat[i]) for i, d in enumerate(D)},
           "r": C.R_SPLIT, "l_f_hz": C.L_F_HZ, "l_x_in": C.L_X_IN,
           "nll": float(res.fun), "opt_success": bool(res.success), "opt_nit": int(res.nit)}
    if verbose:
        print(f"    hyper: su2={su2:.4g} se2={hyp['sigma_e2']:.4g} snug={snug:.4g} "
              f"c_bar={c_bar:+.3f} tau_c={np.sqrt(tau_c2):.3f} nll={res.fun:.1f}")
    return hyp


# ------------------------------------------------------------------------------ cross-covariance application
def cross_apply_fold(kind, V, su2, Kf_st=None, Kx_st=None):
    """Apply K_*T to a training-grid field V (nf_T, nc_T, k) -> (nf_*, nc_*, k).

    'spatial'   : test lines == training lines, test channels disjoint -> K_*T = su2(1-r) I_f (x) Kx_st
    'frequency' : test channels == training channels, test lines disjoint -> K_*T = su2 r Kf_st (x) I_x
    'none'      : zero
    """
    if kind == "none":
        return None
    if kind == "spatial":
        return su2 * (1 - C.R_SPLIT) * np.einsum("sc,fck->fsk", Kx_st, V)
    if kind == "frequency":
        return su2 * C.R_SPLIT * np.einsum("sf,fck->sck", Kf_st, V)
    raise ValueError(kind)


def cross_quad_diag(kind, gp: C.KronGP, su2, Kf_st=None, Kx_st=None):
    """diag(K_*T Sigma_T^{-1} K_T*) on the test grid, computed in the product eigenbasis (exact)."""
    if kind == "none":
        return None
    d = gp.d                                             # (nf_T, nc_T) eigenvalues
    if kind == "spatial":
        A = su2 * (1 - C.R_SPLIT)
        M = gp.Ux.T @ Kx_st.T                            # (nc_T, nc_*)
        S = (M ** 2).T @ (1.0 / d).T                     # (nc_*, nf_T)  = sum_b M[b,c*]^2 / d[a,b]
        return (A ** 2) * ((gp.Uf ** 2) @ S.T)           # (nf_T==nf_*, nc_*)
    A = su2 * C.R_SPLIT
    N = gp.Uf.T @ Kf_st.T                                # (nf_T, nf_*)
    S = (N ** 2).T @ (1.0 / d)                           # (nf_*, nc_T)
    return (A ** 2) * (S @ (gp.Ux ** 2).T)               # (nf_*, nc_*)


# ------------------------------------------------------------------------------ the arm fit
def run_fold(F, fold: Fold, y_raw, Bf, Loc, Ax, Jac=None, hyp=None, arms=("E0", "E1", "E2", "E3"),
             theta_var=None, return_fields=False):
    """Fit all arms on one fold.

    y_raw     : dict drive -> (Nf, Nc) raw residual grid (full grid; the fold slices it)
    Jac       : dict drive -> (Nf, Nc, 9) response Jacobian d q_fem / d log theta at theta_0 (E3 only)
    theta_var : dict drive -> (Nf, Nc) variance of q_fem across retained modal-posterior draws
    Returns dict of per-arm results with predictive mean/sd at the test points and stored contributions.
    """
    ftr, ctr, fte, cte = fold.f_train, fold.c_train, fold.f_test, fold.c_test
    fr_tr, fr_te = F.freqs[ftr], F.freqs[fte]
    xs_tr, xs_te = F.coords[ctr], F.coords[cte]
    Dtr, Dte = fold.train_drives, fold.test_drives
    ytr = {d: y_raw[d][np.ix_(ftr, ctr)] for d in Dtr}
    yte = {d: y_raw[d][np.ix_(fte, cte)] for d in Dte}

    if hyp is None:
        hyp = fit_hyper(ytr, fold, F)
    su2, se2 = hyp["sigma_u2"], hyp["sigma_e2"]
    gp = C.build_kron(fr_tr, xs_tr, su2, se2, hyp["nugget_train"][ctr] if
                      len(hyp["nugget_train"]) == F.Nc else hyp["nugget_train"])

    # --- constrained mean basis (centering vectors from the TRAINING grid only)
    cf = Bf[ftr].mean(0)
    clv = Loc[ctr].mean(0)
    ca = Ax[ctr].mean(0)
    H_tr, blocks = build_H(Bf, Loc, Ax, ftr, ctr, cf, clv, ca)
    kept = gram_rank_keep(H_tr)
    H_tr = H_tr[:, kept]
    H_te, _ = build_H(Bf, Loc, Ax, fte, cte, cf, clv, ca)
    H_te = H_te[:, kept]
    lam_beta = prior_var_for(blocks, kept)
    nf_tr, nc_tr = len(ftr), len(ctr)
    nf_te, nc_te = len(fte), len(cte)

    # constraint residuals (reported, card requirement)
    H_grid = H_tr.reshape(nf_tr, nc_tr, -1)
    kf_n = Bf.shape[1]
    kl_n = Loc.shape[1]
    ka_n = Ax.shape[1]
    names = np.array([n for n, sl in blocks for _ in range(sl.stop - sl.start)])[kept]
    cons = {}
    for nm in ["frequency", "location", "axis", "interaction"]:
        sel = names == nm
        if not sel.any():
            continue
        cons[f"{nm}_grand_mean_abs"] = float(np.max(np.abs(H_tr[:, sel].mean(0))))
    sel_i = names == "interaction"
    if sel_i.any():
        Bl = H_grid[:, :, sel_i]
        cons["interaction_freq_margin_abs"] = float(np.max(np.abs(Bl.mean(axis=1))))
        cons["interaction_loc_margin_abs"] = float(np.max(np.abs(Bl.mean(axis=0))))
    scale = float(np.max(np.abs(H_tr))) if H_tr.size else 1.0
    cons["max_constraint_residual"] = float(max(v for v in cons.values())) if cons else 0.0
    cons["max_constraint_residual_normalized"] = cons["max_constraint_residual"] / max(scale, 1e-300)

    # --- drive-indicator design (log-gain), prior N(c_bar, tau_c^2)
    Dall = list(dict.fromkeys(Dtr + Dte))
    zi = {d: i for i, d in enumerate(Dall)}
    nD = len(Dall)

    # --- precomputed Sigma^{-1} products per training drive
    Sy = {d: gp.solve(ytr[d]) for d in Dtr}

    # cross-covariance helper matrices
    Kf_st = C.kern_f(fr_te, fr_tr) if fold.cross_kind == "frequency" else None
    Kx_st = C.kern_x(xs_te, xs_tr) if fold.cross_kind == "spatial" else None
    qd = cross_quad_diag(fold.cross_kind, gp, su2, Kf_st, Kx_st)

    # theta-induced predictive variance at test points (modular: propagated, NOT conditioned)
    tv = {d: (theta_var[d][np.ix_(fte, cte)] if theta_var is not None else np.zeros((nf_te, nc_te)))
          for d in Dte}

    # per-channel nugget at test points
    if len(cte) and np.all(np.isin(cte, ctr)):
        nug_te = hyp["nugget_train"][cte] if len(hyp["nugget_train"]) == F.Nc else \
            hyp["nugget_train"][[list(ctr).index(c) for c in cte]]
    else:
        nug_te = np.full(nc_te, hyp["nugget_heldout"])

    out = {"fold": {"family": fold.family, "fold": fold.fold, "name": fold.name,
                    "n_train_points": int(len(Dtr) * nf_tr * nc_tr),
                    "n_test_points": int(len(Dte) * nf_te * nc_te),
                    "cross_kind": fold.cross_kind},
           "hyper": {k: (v if not isinstance(v, np.ndarray) else None) for k, v in hyp.items()},
           "constraints": cons, "n_basis_kept": int(H_tr.shape[1]), "n_basis_raw": int(len(names)),
           "arms": {}}

    for arm in arms:
        use_cross = arm != "E0"
        use_mean = arm in ("E2", "E3")
        perp = arm == "E3"

        # design blocks per drive
        Xd_tr, Xd_te = {}, {}
        if perp:
            # locally theta-orthogonal basis: H_perp = H - J b, b = (J^T W J)^+ (J^T W H) using the
            # realized covariance metric W = Sigma_train^{-1}, stacked over training drives
            JtWJ = np.zeros((9, 9))
            JtWH = np.zeros((9, H_tr.shape[1]))
            SJ = {}
            for d in Dtr:
                Jd = Jac[d][np.ix_(ftr, ctr)].reshape(nf_tr * nc_tr, 9)
                SJd = gp.solve(Jd.reshape(nf_tr, nc_tr, 9)).reshape(nf_tr * nc_tr, 9)
                SJ[d] = SJd
                JtWJ += Jd.T @ SJd
                JtWH += SJd.T @ H_tr
            b = np.linalg.pinv(JtWJ, rcond=C.PINV_TOL) @ JtWH
            resid = JtWH - JtWJ @ b
            nrm = np.linalg.norm(resid) / max(np.linalg.norm(JtWH), 1e-300)
            out["orthogonality"] = {
                "normalized_residual": float(nrm),
                "abs_residual": float(np.linalg.norm(resid)),
                "JtWH_norm": float(np.linalg.norm(JtWH)),
                "pinv_rcond": C.PINV_TOL,
                "JtWJ_cond": float(np.linalg.cond(JtWJ)),
                "definition": "P_perp = I - J (J^T W J)^+ J^T W at the modal-posterior median theta_0 on the "
                              "TRAINING grid, W = Sigma_train^{-1} (realized covariance metric)"}
            for d in Dtr:
                Jd = Jac[d][np.ix_(ftr, ctr)].reshape(nf_tr * nc_tr, 9)
                Xd_tr[d] = H_tr - Jd @ b
            for d in Dte:
                Jd = Jac[d][np.ix_(fte, cte)].reshape(nf_te * nc_te, 9)
                Xd_te[d] = H_te - Jd @ b
        else:
            for d in Dtr:
                Xd_tr[d] = H_tr
            for d in Dte:
                Xd_te[d] = H_te

        # full design = [drive indicators | mean basis]
        p_mean = H_tr.shape[1] if use_mean else 0
        p = nD + p_mean
        A = np.zeros((p, p))
        rhs = np.zeros(p)
        prior_mu = np.zeros(p)
        prior_var = np.zeros(p)
        prior_mu[:nD] = hyp["c_bar"]
        prior_var[:nD] = hyp["tau_c2"]
        if use_mean:
            prior_var[nD:] = lam_beta
        A += np.diag(1.0 / prior_var)
        rhs += prior_mu / prior_var

        SX_cache = {}
        for d in Dtr:
            cols = [np.zeros((nf_tr * nc_tr, nD))]
            cols[0][:, zi[d]] = 1.0
            if use_mean:
                cols.append(Xd_tr[d])
            Xd = np.concatenate(cols, axis=1)
            SXd = gp.solve(Xd.reshape(nf_tr, nc_tr, p)).reshape(nf_tr * nc_tr, p)
            SX_cache[d] = (Xd, SXd)
            A += Xd.T @ SXd
            rhs += Xd.T @ Sy[d].reshape(-1)
        Cov_b = np.linalg.inv(A)
        b_hat = Cov_b @ rhs

        # --- prediction
        preds = {}
        for d in Dte:
            Zte = np.zeros((nf_te * nc_te, nD))
            Zte[:, zi[d]] = 1.0
            cols = [Zte] + ([Xd_te[d]] if use_mean else [])
            Xte = np.concatenate(cols, axis=1)
            mean_gain_basis = Xte @ b_hat
            # split the mean into the log-gain part and the learned structured-mean part
            m_gain = Zte @ b_hat[:nD]
            m_struct = (Xd_te[d] @ b_hat[nD:]) if use_mean else np.zeros(nf_te * nc_te)

            # GP conditional term  E[u_* | train] = K_*T Sigma^{-1} (y - X b_hat), summed over training
            # drives that share the SAME drive (rho = 0 -> only drive d contributes)
            u_star = np.zeros(nf_te * nc_te)
            if use_cross and fold.cross_kind != "none" and d in Dtr:
                Xd, _ = SX_cache[d]
                res_d = ytr[d].reshape(-1) - Xd @ b_hat
                Sres = gp.solve(res_d.reshape(nf_tr, nc_tr)).reshape(nf_tr, nc_tr, 1)
                u_star = cross_apply_fold(fold.cross_kind, Sres, su2, Kf_st, Kx_st).reshape(-1)

            mu = m_gain + m_struct + u_star

            # --- predictive variance (diagonal)
            var = np.full(nf_te * nc_te, su2) + np.repeat(nug_te[None, :], nf_te, 0).reshape(-1) + se2
            if use_cross and fold.cross_kind != "none" and d in Dtr:
                var = var - qd.reshape(-1)
            # coefficient uncertainty, propagated through (X_* - K_*T Sigma^{-1} X_T)
            if use_cross and fold.cross_kind != "none" and d in Dtr:
                Xd, SXd = SX_cache[d]
                KSX = cross_apply_fold(fold.cross_kind, SXd.reshape(nf_tr, nc_tr, p),
                                       su2, Kf_st, Kx_st).reshape(nf_te * nc_te, p)
                Xeff = Xte - KSX
            else:
                Xeff = Xte
            var = var + np.einsum("ij,jk,ik->i", Xeff, Cov_b, Xeff)
            var = var + tv[d].reshape(-1)
            var = np.maximum(var, 1e-12)

            preds[d] = {"mu": mu, "sd": np.sqrt(var), "y": yte[d].reshape(-1),
                        "m_gain": m_gain, "m_struct": m_struct, "u_star": u_star,
                        "theta_var": tv[d].reshape(-1)}

        y_all = np.concatenate([preds[d]["y"] for d in Dte])
        mu_all = np.concatenate([preds[d]["mu"] for d in Dte])
        sd_all = np.concatenate([preds[d]["sd"] for d in Dte])
        rec = {
            "median_abs_err_db": C.median_abs_db(y_all, mu_all),
            "mean_abs_err_db": float(np.mean(np.abs(y_all - mu_all)) * C.DB),
            "crps_db": float(np.mean(C.crps_gauss(y_all, mu_all, sd_all)) * C.DB),
            "coverage90": C.coverage(y_all, mu_all, sd_all),
            "width90_db": float(np.mean(C.interval_width(sd_all)) * C.DB),
            "mean_abs_struct_mean_db": float(np.mean(np.abs(np.concatenate(
                [preds[d]["m_struct"] for d in Dte]))) * C.DB),
            "mean_abs_gp_mean_db": float(np.mean(np.abs(np.concatenate(
                [preds[d]["u_star"] for d in Dte]))) * C.DB),
            "mean_theta_sd_db": float(np.mean(np.sqrt(np.concatenate(
                [preds[d]["theta_var"] for d in Dte]))) * C.DB),
            "n_test": int(len(y_all)),
        }
        if use_mean:
            rec["beta_hat"] = b_hat[nD:].tolist()
            rec["beta_post_sd"] = np.sqrt(np.diag(Cov_b)[nD:]).tolist()
        rec["c_hat"] = {d: float(b_hat[zi[d]]) for d in Dall}
        rec["c_post_sd"] = {d: float(np.sqrt(Cov_b[zi[d], zi[d]])) for d in Dall}
        out["arms"][arm] = rec
        if return_fields:
            out["arms"][arm]["_fields"] = preds
    return out


# ------------------------------------------------------------------------------ Jacobian / theta variance
def response_jacobian_fd(F, drive_key, theta0, h=1e-3):
    """d q_fem / d log(theta_g) at theta_0 by central differences in log theta. Shape (Nf, Nc, 9).

    FALLBACK ONLY. Near a resonance ln|H| is strongly nonlinear in theta, so a finite step of 1e-3 in
    log theta disagrees with autodiff by ~13% at the worst grid point (verification V6). Use the exact
    autodiff route below whenever jax is available.
    """
    J = np.empty((F.Nf, F.Nc, 9))
    lt = np.log(theta0)
    for g in range(9):
        lp, lm = lt.copy(), lt.copy()
        lp[g] += h
        lm[g] -= h
        J[:, :, g] = (C.q_fem(F, drive_key, np.exp(lp)) - C.q_fem(F, drive_key, np.exp(lm))) / (2 * h)
    return J


def response_jacobian(F, drive_key, theta0, zeta=C.ZETA_PRIMARY):
    """EXACT d q_fem / d log(theta_g) at theta_0 by jax forward-mode autodiff in float64. (Nf, Nc, 9)."""
    import jax
    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    fwd = F.rf.jax_fem_logmag_factory(F.R, F.freqs, F.rows, F.drive_rows[drive_key], zeta=zeta)
    Jth = np.asarray(jax.jacfwd(fwd)(jnp.asarray(theta0)))
    assert Jth.dtype == np.float64, f"Jacobian not float64 ({Jth.dtype}) — x64 not enabled"
    return Jth * np.asarray(theta0)[None, None, :]


def theta_variance(F, drive_key, theta_draws):
    """Var over retained modal-posterior draws of q_fem, and the mean field. Returns (var, mean)."""
    acc = np.empty((len(theta_draws), F.Nf, F.Nc))
    for i, t in enumerate(theta_draws):
        acc[i] = C.q_fem(F, drive_key, t)
    return acc.var(axis=0), acc.mean(axis=0)
