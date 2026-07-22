#!/usr/bin/env python3
"""Shared exact-Gaussian machinery for Card E.

All arrays use point order `(frequency first, channel second)` after flattening a
`(n_frequency, n_channel)` matrix in C order.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy.interpolate import BSpline
from scipy.linalg import cho_factor, cho_solve
from scipy.special import ndtr


WS = Path(__file__).resolve().parent.parent
REPO = WS.parents[2]
DB_PER_LN = 20.0 / np.log(10.0)
SIGMA_E = 0.15
TAU_BETA = 0.35
LF_HZ = 10.0
LX_IN = 2000.0
R_SPLIT = 0.82
RANK_TOL = 1e-10
SIGMA_U_GRID = np.array([0.30, 0.60, 1.00, 1.50])


def read_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def region_labels(coords: np.ndarray) -> np.ndarray:
    features = {
        "impact": np.array([9.0, 8.0, 1.0]),
        "bolted_joint": np.array([9.0, -0.4, 19.1]),
        "strut": np.array([8.7, 0.0, 49.6]),
        "dish": np.array([1.9, 0.0, 57.0]),
    }
    names = list(features) + ["bulkhead"]
    d = [np.linalg.norm(coords - features[k][None, :], axis=1) for k in features]
    bulkhead_z = np.array([12.4, 18.4, 30.4])
    d.append(np.min(np.abs(coords[:, 2, None] - bulkhead_z[None, :]), axis=1))
    return np.asarray(names)[np.argmin(np.stack(d), axis=0)]


def kmedoids(x: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic PAM-like k-medoids with farthest-first initialization."""
    x = np.asarray(x, float)
    dist = np.linalg.norm(x[:, None, :] - x[None, :, :], axis=2)
    med = [int(np.argmin(dist.sum(axis=1)))]
    while len(med) < k:
        nearest = dist[:, med].min(axis=1)
        nearest[med] = -1.0
        med.append(int(np.argmax(nearest)))
    med = np.array(med, int)
    for _ in range(100):
        labels = np.argmin(dist[:, med], axis=1)
        new = med.copy()
        for j in range(k):
            idx = np.where(labels == j)[0]
            if len(idx):
                new[j] = idx[np.argmin(dist[np.ix_(idx, idx)].sum(axis=1))]
        if np.array_equal(new, med):
            break
        med = new
    labels = np.argmin(dist[:, med], axis=1)
    order = np.argsort(med)
    remap = np.empty(k, int)
    remap[order] = np.arange(k)
    return med[order], remap[labels]


def spline_basis(freqs: np.ndarray, registry: dict) -> np.ndarray:
    x = np.log(np.asarray(freqs, float))
    knots = np.asarray(registry["frequency"]["full_knot_vector_log_hz"], float)
    return BSpline.design_matrix(x, knots, 3, extrapolate=False).toarray()


def raw_basis(freqs: np.ndarray, coords: np.ndarray, axes: list[str], registry: dict) -> tuple[np.ndarray, dict]:
    bf = spline_basis(freqs, registry)
    regions = region_labels(coords)
    region_order = registry["location"]["region_order"]
    ind = np.column_stack([(regions == r).astype(float) for r in region_order])
    mu = np.asarray(registry["location"]["standardize_mean_in"], float)
    sd = np.asarray(registry["location"]["standardize_sd_in"], float)
    z = (coords - mu) / sd
    centers = np.asarray(registry["location"]["rbf_centers_standardized"], float)
    scale = float(registry["location"]["rbf_scale_standardized"])
    rbf = np.exp(-0.5 * np.sum((z[:, None, :] - centers[None, :, :]) ** 2, axis=2) / scale**2)
    bx = np.column_stack([ind, rbf])
    axis_order = registry["axis"]["labels"]
    ba = np.column_stack([(np.asarray(axes) == a).astype(float) for a in axis_order])
    # Point ordering: frequency-major, channel-minor.
    fmain = np.repeat(bf, len(coords), axis=0)
    xmain = np.tile(bx, (len(freqs), 1))
    amain = np.tile(ba, (len(freqs), 1)) if len(axis_order) > 1 else np.empty((len(freqs) * len(coords), 0))
    inter = np.einsum("fi,xj->fxij", bf, bx).reshape(len(freqs) * len(coords), -1)
    h = np.column_stack([fmain, xmain, amain, inter])
    meta = {
        "freq": list(range(0, fmain.shape[1])),
        "loc": list(range(fmain.shape[1], fmain.shape[1] + xmain.shape[1])),
        "axis": list(range(fmain.shape[1] + xmain.shape[1], fmain.shape[1] + xmain.shape[1] + amain.shape[1])),
        "interaction": list(range(fmain.shape[1] + xmain.shape[1] + amain.shape[1], h.shape[1])),
        "n_freq_raw": bf.shape[1],
        "n_loc_raw": bx.shape[1],
    }
    return h, meta


def constrained_basis(h_full: np.ndarray, meta: dict, train: np.ndarray, test: np.ndarray,
                      f_index: np.ndarray, x_index: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """Training-fold ANOVA centering and deterministic rank removal.

    Two-way interaction columns are residualized against training frequency and
    location margins by alternating projections. The same learned offsets are
    applied to test rows.
    """
    ht = h_full[train].copy()
    hs = h_full[test].copy()
    fit = f_index[train]
    xit = x_index[train]
    fis = f_index[test]
    xis = x_index[test]
    max_res = 0.0

    # Main-effect blocks: training mean zero.
    for block in (meta["freq"], meta["loc"], meta["axis"]):
        if not block:
            continue
        m = ht[:, block].mean(axis=0)
        ht[:, block] -= m
        hs[:, block] -= m
        max_res = max(max_res, float(np.max(np.abs(ht[:, block].mean(axis=0)))))

    # Interaction: learn row/column effects on training rows and apply by labels.
    cols = meta["interaction"]
    zt = ht[:, cols]
    zs = hs[:, cols]
    grand = zt.mean(axis=0)
    zt -= grand
    zs -= grand
    uf = np.unique(f_index)
    ux = np.unique(x_index)
    foff = np.zeros((len(uf), zt.shape[1]))
    xoff = np.zeros((len(ux), zt.shape[1]))
    for _ in range(200):
        change = 0.0
        for f in np.unique(fit):
            m = zt[fit == f].mean(axis=0)
            zt[fit == f] -= m
            zs[fis == f] -= m
            foff[f] += m
            change = max(change, float(np.max(np.abs(m))))
        for x in np.unique(xit):
            m = zt[xit == x].mean(axis=0)
            zt[xit == x] -= m
            zs[xis == x] -= m
            xoff[x] += m
            change = max(change, float(np.max(np.abs(m))))
        if change < 1e-13:
            break
    ht[:, cols] = zt
    hs[:, cols] = zs
    for f in np.unique(fit):
        max_res = max(max_res, float(np.max(np.abs(zt[fit == f].mean(axis=0)))))
    for x in np.unique(xit):
        max_res = max(max_res, float(np.max(np.abs(zt[xit == x].mean(axis=0)))))

    # Remove rank-deficient directions using training SVD; normalize retained columns to RMS 1.
    u, s, vt = np.linalg.svd(ht, full_matrices=False)
    keep = s > (RANK_TOL * s[0] if len(s) and s[0] else RANK_TOL)
    v = vt[keep].T
    ht = ht @ v
    hs = hs @ v
    rms = np.sqrt(np.mean(ht**2, axis=0))
    good = rms > 1e-14
    ht = ht[:, good] / rms[good]
    hs = hs[:, good] / rms[good]
    info = {
        "raw_columns": int(h_full.shape[1]),
        "retained_rank": int(good.sum()),
        "rank_tolerance": RANK_TOL,
        "max_constraint_residual": max_res,
    }
    return ht, hs, info


def point_kernel(freqs: np.ndarray, coords: np.ndarray, axes: list[str], sigma_u: float) -> np.ndarray:
    f = np.repeat(freqs, len(coords))
    x = np.tile(coords, (len(freqs), 1))
    a = np.tile(np.asarray(axes), len(freqs))
    df = np.abs(f[:, None] - f[None, :])
    dx = np.linalg.norm(x[:, None, :] - x[None, :, :], axis=2)
    same_axis = (a[:, None] == a[None, :]).astype(float)
    kf = np.exp(-df / LF_HZ) * same_axis
    kx = np.exp(-dx / LX_IN) * same_axis
    return sigma_u**2 * (R_SPLIT * kf + (1.0 - R_SPLIT) * kx)


def select_sigma(y: np.ndarray, k_unit: np.ndarray, train: np.ndarray) -> tuple[float, list[dict]]:
    records = []
    yt = np.asarray(y)[train]
    for sig in SIGMA_U_GRID:
        c = sig**2 * k_unit[np.ix_(train, train)] + SIGMA_E**2 * np.eye(len(train))
        cf = cho_factor(c, lower=True, check_finite=False)
        alpha = cho_solve(cf, yt, check_finite=False)
        logdet = 2.0 * np.log(np.diag(cf[0])).sum()
        nll = 0.5 * (yt @ alpha + logdet + len(train) * np.log(2 * np.pi))
        records.append({"sigma_u": float(sig), "training_nll": float(nll)})
    best = min(records, key=lambda r: r["training_nll"])["sigma_u"]
    return float(best), records


def orthogonalize(ht: np.ndarray, hs: np.ndarray, jt: np.ndarray, js: np.ndarray,
                  c_train: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    cf = cho_factor(c_train, lower=True, check_finite=False)
    wj = cho_solve(cf, jt, check_finite=False)
    wh = cho_solve(cf, ht, check_finite=False)
    gram = jt.T @ wj
    a = np.linalg.pinv(gram, rcond=RANK_TOL) @ (jt.T @ wh)
    htp = ht - jt @ a
    hsp = hs - js @ a
    resid = jt.T @ cho_solve(cf, htp, check_finite=False)
    denom = np.linalg.norm(jt) * np.linalg.norm(cho_solve(cf, htp, check_finite=False))
    normalized = float(np.linalg.norm(resid) / denom) if denom else 0.0
    return htp, hsp, {
        "pseudoinverse_tolerance": RANK_TOL,
        "jt_w_hperp_norm": float(np.linalg.norm(resid)),
        "normalized_orthogonality_residual": normalized,
    }


def predict(y: np.ndarray, k: np.ndarray, train: np.ndarray, test: np.ndarray,
            htrain: np.ndarray | None = None, htest: np.ndarray | None = None,
            cross: bool = True) -> dict:
    kt = k[np.ix_(train, train)] + SIGMA_E**2 * np.eye(len(train))
    ks = k[np.ix_(test, train)] if cross else np.zeros((len(test), len(train)))
    kss_diag = np.diag(k)[test]
    if htrain is None:
        s = kt
        cf = cho_factor(s, lower=True, check_finite=False)
        alpha = cho_solve(cf, np.asarray(y)[train], check_finite=False)
        mean_u = ks @ alpha
        var_u = kss_diag - np.sum(ks * cho_solve(cf, ks.T, check_finite=False).T, axis=1)
        return {
            "mean": mean_u,
            "mean_beta": np.zeros(len(test)),
            "mean_u": mean_u,
            "var_beta": np.zeros(len(test)),
            "var_u": np.clip(var_u, 0, None),
            "cov_beta_u": np.zeros(len(test)),
            "var_total": np.clip(var_u + SIGMA_E**2, 1e-12, None),
        }
    lam = TAU_BETA**2 * np.eye(htrain.shape[1])
    s = kt + htrain @ lam @ htrain.T
    cf = cho_factor(s, lower=True, check_finite=False)
    alpha = cho_solve(cf, np.asarray(y)[train], check_finite=False)
    b_cross = htest @ lam @ htrain.T
    mean_beta = b_cross @ alpha
    mean_u = ks @ alpha
    sinv_bt = cho_solve(cf, b_cross.T, check_finite=False)
    sinv_kt = cho_solve(cf, ks.T, check_finite=False)
    var_beta = np.sum((htest @ lam) * htest, axis=1) - np.sum(b_cross * sinv_bt.T, axis=1)
    var_u = kss_diag - np.sum(ks * sinv_kt.T, axis=1)
    cov_bu = -np.sum(b_cross * sinv_kt.T, axis=1)
    var_total = var_beta + var_u + 2.0 * cov_bu + SIGMA_E**2
    return {
        "mean": mean_beta + mean_u,
        "mean_beta": mean_beta,
        "mean_u": mean_u,
        "var_beta": np.clip(var_beta, 0, None),
        "var_u": np.clip(var_u, 0, None),
        "cov_beta_u": cov_bu,
        "var_total": np.clip(var_total, 1e-12, None),
    }


def crps_normal(obs: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> np.ndarray:
    sd = np.maximum(sd, 1e-12)
    z = (obs - mu) / sd
    phi = np.exp(-0.5 * z**2) / np.sqrt(2 * np.pi)
    return sd * (z * (2 * ndtr(z) - 1) + 2 * phi - 1 / np.sqrt(np.pi))


def score(obs: np.ndarray, pred: dict) -> dict:
    mu = np.asarray(pred["mean"])
    sd = np.sqrt(np.asarray(pred["var_total"]))
    z90 = 1.6448536269514722
    err_db = np.abs(obs - mu) * DB_PER_LN
    return {
        "median_abs_error_db": float(np.median(err_db)),
        "mean_crps_db": float(np.mean(crps_normal(obs, mu, sd)) * DB_PER_LN),
        "coverage90": float(np.mean((obs >= mu - z90 * sd) & (obs <= mu + z90 * sd))),
        "mean_width90_db": float(np.mean(2 * z90 * sd) * DB_PER_LN),
        "n_points": int(len(obs)),
    }


def success(e1: dict, e3: dict) -> dict:
    err_reduction = e1["median_abs_error_db"] - e3["median_abs_error_db"]
    width_reduction = 1.0 - e3["mean_width90_db"] / e1["mean_width90_db"]
    cov_delta = e3["coverage90"] - e1["coverage90"]
    crossed = (err_reduction >= 2.0 and cov_delta >= -0.02) or (width_reduction >= 0.20 and abs(cov_delta) <= 0.02)
    return {
        "error_reduction_db": float(err_reduction),
        "width_reduction_fraction": float(width_reduction),
        "coverage_delta": float(cov_delta),
        "crosses_2db_or_20pct_rule": bool(crossed),
    }
