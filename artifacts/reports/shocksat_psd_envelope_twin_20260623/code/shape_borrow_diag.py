#!/usr/bin/env python3
"""DECISIVE CHEAP DIAGNOSTIC (validity-before-rigor gate, Andrew request): is the per-mode FEM mode-shape ERROR
SPATIALLY BORROWABLE to a held-out sensor? This is the single property that Beck (shape-field inference), Schneider
(space-correlated discrepancy), and a non-overfit heteroscedastic likelihood all live or die on.

Setup (no NUTS, pure linear algebra on the CLEAN .ash modal survey = "all the data" in shape form):
  - For each measured .ash mode r, MAC-match to its best FEM mode k (theta=1) over the instrumented DOFs.
  - Align FEM shape to measured by best least-squares scale/sign s: e_r = phi_meas - s*phi_fem  (the shape-error field).
  - LEAVE-ONE-SENSOR-OUT: at each instrumented DOF j, predict e_r(j) from e_r at the OTHER, SAME-AXIS DOFs by
    distance-weighted interpolation on 3-D node coords (Gaussian kernel, length swept). e_hat_r(j).
  - Compare held-out shape prediction: FEM-only error |e_r(j)| vs FEM+interp error |e_r(j)-e_hat_r(j)|.

Headline = borrow_R2 = 1 - Var(e - e_hat)/Var(e)  (fraction of the per-mode shape error that is spatially
predictable). High => shape-field transfer works => run multi-ref Beck. ~0 => capped => pivot (regional/pooled QOI).
Generalizes the old spatial_reanalysis R2=0.04 (AGGREGATE amplitude, NOISY Test07) to PER-MODE on CLEAN .ash.
Includes a coord-shuffle null (should give borrow_R2 ~ 0) and a held-out log-amplitude sigma (compare D9 oracle 0.70,
current broadband sigma ~0.97). EXPLORATORY; no success claim; YELLOW by default. Output: out/shape_borrow_diag.json.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; OUT.mkdir(exist_ok=True)
MEAS = WS / "data" / "measured_modes.npz"
FEMM = WS.parent / "shocksat_fem_modal_twin_20260609" / "fem_model.npz"
AXES = ["X", "Y", "Z"]
MAC_MIN = 0.3
N_MAX = 20
MIN_AXIS_DOF = 6                  # need enough same-axis sensors to interpolate
AMP_FLOOR_FRAC = 0.10            # for the log-amplitude sigma, only DOFs with |phi|>floor*max (avoid nodal lines)


def build_dofs(R):
    """Instrumented DOFs shared by .ash measured shapes and the reduced FEM basis, with coords/axis/node."""
    z = np.load(MEAS, allow_pickle=True)
    sh = np.asarray(z["shapes"], float)            # (33, 76, 3)
    mfr = np.asarray(z["freqs"], float)            # (33,)
    nodes = np.asarray(z["nodes"]); msk = np.asarray(z["measured"])  # (76,), (76,3)
    fm = np.load(FEMM); gids = np.asarray(fm["gids"]); xyz = np.asarray(fm["xyz"])
    gid2xyz = {int(g): xyz[i] for i, g in enumerate(gids)}
    Grows, meas_cols, coord, axis, node = [], [], [], [], []
    for ni, g in enumerate(nodes):
        for a in range(3):
            if not msk[ni, a]:
                continue
            try:
                r, _, _ = R.reduced_row(gid2xyz[int(g)], AXES[a])
            except Exception:
                continue
            Grows.append(r); meas_cols.append(sh[:, ni, a]); coord.append(gid2xyz[int(g)])
            axis.append(a); node.append(int(g))
    G = np.array(Grows)                              # (ndof, 74)
    MEASs = np.array(meas_cols).T                    # (33, ndof) -> per mode rows below use .T
    return dict(G=G, MEAS=np.array(meas_cols),       # (ndof, 33)
                mfr=mfr, coord=np.array(coord, float), axis=np.array(axis), node=np.array(node))


def mac(a, b):
    return float((a @ b) ** 2 / ((a @ a) * (b @ b) + 1e-30))


def match_modes(D, Q1):
    """MAC-match each measured mode to its best (unique) FEM mode over the instrumented DOFs."""
    FemAll = D["G"] @ Q1                              # (ndof, 74)
    pairs, used = [], set()
    for r in range(D["MEAS"].shape[1]):
        m = D["MEAS"][:, r]
        macs = np.array([mac(FemAll[:, k], m) for k in range(FemAll.shape[1])])
        k = int(np.argmax(macs))
        if macs[k] >= MAC_MIN and k not in used:
            pairs.append((r, k, float(macs[k]))); used.add(k)
    pairs = sorted(pairs, key=lambda p: D["mfr"][p[0]])[:N_MAX]
    return FemAll, pairs


def loo_interp(resid, coord, axis, length, shuffle_rng=None):
    """Leave-one-out same-axis Gaussian-kernel interpolation of a residual field. Returns e_hat (ndof,)."""
    c = coord.copy()
    if shuffle_rng is not None:                      # null: break the spatial signal
        c = c[shuffle_rng.permutation(len(c))]
    ehat = np.full(len(resid), np.nan)
    for j in range(len(resid)):
        same = np.where((axis == axis[j]) & (np.arange(len(resid)) != j))[0]
        if len(same) < 2:
            continue
        d = np.linalg.norm(c[same] - c[j], axis=1)
        w = np.exp(-0.5 * (d / length) ** 2)
        if w.sum() < 1e-9:
            continue
        ehat[j] = float(np.sum(w * resid[same]) / np.sum(w))
    return ehat


def run(write=True):
    R = rf.load_reduced()
    K1 = R.A_fix + R.A.sum(0); _, Q1 = np.linalg.eigh(K1)
    D = build_dofs(R)
    FemAll, pairs = match_modes(D, Q1)
    coord, axis = D["coord"], D["axis"]
    # median same-axis nearest-neighbour distance -> interpolation length scale
    nnd = []
    for j in range(len(coord)):
        same = np.where((axis == axis[j]) & (np.arange(len(coord)) != j))[0]
        if len(same):
            nnd.append(np.min(np.linalg.norm(coord[same] - coord[j], axis=1)))
    nn_med = float(np.median(nnd))

    lengths = {f"{c:g}x_nn": c * nn_med for c in (0.5, 1.0, 2.0, 4.0)}
    rng = np.random.default_rng(0)

    # accumulate per-DOF residuals across all matched modes (held-out shape error)
    def accumulate(length, shuffle=False):
        e_all, eint_all, ax_all, logfem, loginterp = [], [], [], [], []
        for (r, k, mc) in pairs:
            m = D["MEAS"][:, r].copy(); f = FemAll[:, k].copy()
            m = m / (np.linalg.norm(m) + 1e-30)                  # unit-norm measured mode
            s = float((m @ f) / (f @ f + 1e-30)); fa = s * f      # least-squares scale+sign aligned FEM
            e = m - fa
            sr = np.random.default_rng(r) if shuffle else None
            ehat = loo_interp(e, coord, axis, length, shuffle_rng=sr)
            ok = ~np.isnan(ehat)
            e_all.append(e[ok]); eint_all.append((e - ehat)[ok]); ax_all.append(axis[ok])
            # log-amplitude held-out sigma on non-nodal DOFs (QOI proxy: peak|H| ~ |phi_sensor|)
            mx = np.max(np.abs(m))
            big = ok & (np.abs(m) > AMP_FLOOR_FRAC * mx) & (np.abs(fa) > 1e-12)
            pred_interp = fa + ehat
            big = big & (np.abs(pred_interp) > 1e-12)
            logfem.append(np.log(np.abs(m[big])) - np.log(np.abs(fa[big])))
            loginterp.append(np.log(np.abs(m[big])) - np.log(np.abs(pred_interp[big])))
        e_all = np.concatenate(e_all); eint_all = np.concatenate(eint_all); ax_all = np.concatenate(ax_all)
        logfem = np.concatenate(logfem); loginterp = np.concatenate(loginterp)
        r2 = 1.0 - np.var(eint_all) / (np.var(e_all) + 1e-30)
        r2_ax = {AXES[a]: (1.0 - np.var(eint_all[ax_all == a]) / (np.var(e_all[ax_all == a]) + 1e-30))
                 if np.sum(ax_all == a) > 3 else None for a in range(3)}
        return {"borrow_R2": float(r2), "borrow_R2_per_axis": r2_ax,
                "sigma_log_fem_only": float(np.std(logfem)), "sigma_log_fem_interp": float(np.std(loginterp)),
                "n_heldout_dof": int(len(e_all)), "n_logamp_dof": int(len(logfem))}

    by_length = {name: accumulate(L) for name, L in lengths.items()}
    best_name = max(by_length, key=lambda n: by_length[n]["borrow_R2"])
    null = accumulate(lengths[best_name], shuffle=True)            # coord-shuffle null at the best length

    rec = {
        "deliverable": "DECISIVE DIAGNOSTIC: is the per-mode FEM mode-shape error spatially borrowable to a held-out sensor?",
        "data": "clean .ash modal survey (33 modes x 76 nodes x 3 axes) + reduced FEM basis; NO NUTS",
        "n_matched_modes": len(pairs), "mac_min": MAC_MIN,
        "matched_pairs_freq_mac": [{"meas_mode": int(r), "fem_mode": int(k), "mac": round(mc, 3),
                                     "freq_hz": round(float(D["mfr"][r]), 1)} for (r, k, mc) in pairs],
        "n_instrumented_dof": int(len(coord)), "nn_median_in": round(nn_med, 2),
        "by_length": by_length, "best_length": best_name,
        "coord_shuffle_null_at_best": null,
        "reference_marks": {"old_spatial_reanalysis_R2_aggregate_noisy": 0.04,
                            "D9_oracle_sigma_log_measured_shapes": 0.70,
                            "current_broadband_sigma_log": 0.97,
                            "FEM_shape_sigma_log_D9": 1.26},
        "interpretation_rule": "borrow_R2 high (>~0.4) AND sigma_log_fem_interp << fem_only => shape-field transfer "
                               "works => run multi-ref Beck. borrow_R2 ~ null => capped => pivot to regional/pooled QOI.",
        "note": "EXPLORATORY validity gate; YELLOW by default; no success claim.",
    }
    if write:
        (OUT / "shape_borrow_diag.json").write_text(json.dumps(rec, indent=2))
    b = by_length[best_name]
    print(f"matched modes: {len(pairs)} (MAC>={MAC_MIN}); instrumented DOFs: {len(coord)}; nn_med {nn_med:.1f} in")
    print(f"BEST length {best_name}:  borrow_R2 = {b['borrow_R2']:+.3f}  per-axis {b['borrow_R2_per_axis']}")
    print(f"  held-out shape log-amp sigma:  FEM-only {b['sigma_log_fem_only']:.2f}  ->  FEM+interp "
          f"{b['sigma_log_fem_interp']:.2f}   (D9 oracle 0.70, current broadband 0.97)")
    print(f"  coord-shuffle NULL borrow_R2 = {null['borrow_R2']:+.3f}  (should be ~0)")
    print("  all lengths:", {n: round(by_length[n]["borrow_R2"], 3) for n in by_length})
    return rec


if __name__ == "__main__":
    run()
