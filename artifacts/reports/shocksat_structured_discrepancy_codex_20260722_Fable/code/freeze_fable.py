#!/usr/bin/env python3
"""Task Card E `_Fable` — FREEZE: split registry and mean-basis registry.

Both are built from DESIGN INFORMATION ONLY (sensor coordinates, response-axis labels, the frequency grid).
No response residual is read anywhere in this file. Run before any fitting.

Writes:
  out/split_registry.json
  out/mean_basis_registry.json
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_fable as C  # noqa: E402

HASH_SEED = "shocksat_structured_discrepancy_codex_20260722_Fable/joint_transfer/v1"


# ------------------------------------------------------------------ deterministic k-medoids (PAM-style)
def kmedoids(X, k, max_iter=200):
    """Fully deterministic k-medoids. Init = farthest-point traversal from the point nearest the centroid.

    Returns (medoid_indices sorted, labels).
    """
    X = np.asarray(X, float)
    n = len(X)
    D = np.linalg.norm(X[:, None, :] - X[None, :, :], axis=2)
    start = int(np.argmin(np.linalg.norm(X - X.mean(0), axis=1)))
    med = [start]
    while len(med) < k:
        dmin = D[:, med].min(axis=1)
        cand = np.flatnonzero(dmin == dmin.max())
        med.append(int(cand[0]))                       # ties broken by lowest index -> deterministic
    med = list(med)
    for _ in range(max_iter):
        lab = np.argmin(D[:, med], axis=1)
        new = []
        for j in range(k):
            idx = np.flatnonzero(lab == j)
            if len(idx) == 0:
                new.append(med[j])
                continue
            costs = D[np.ix_(idx, idx)].sum(axis=1)
            best = idx[int(np.argmin(costs))]
            tie = idx[costs == costs.min()]
            new.append(int(tie.min()))
        if new == med:
            break
        med = new
    lab = np.argmin(D[:, med], axis=1)
    order = np.argsort(med)
    remap = {int(o): i for i, o in enumerate(order)}
    lab = np.array([remap[int(v)] for v in lab])
    return [int(med[o]) for o in order], lab


# ------------------------------------------------------------------ cubic B-spline basis in log f
def bspline_basis(x, knots_interior, lo, hi, degree=3):
    """Cubic B-spline design with the given interior knots and boundary knots (lo, hi). Returns (n, df)."""
    from scipy.interpolate import BSpline
    t = np.concatenate([[lo] * (degree + 1), knots_interior, [hi] * (degree + 1)])
    n_basis = len(t) - degree - 1
    cols = []
    for i in range(n_basis):
        c = np.zeros(n_basis)
        c[i] = 1.0
        cols.append(BSpline(t, c, degree, extrapolate=True)(x))
    return np.stack(cols, axis=1)


def main():
    t0 = time.time()
    F = C.load_frozen(n_theta=5)
    C.OUT.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- SPLIT FAMILY 2: spatial clusters
    med_sp, lab_sp = kmedoids(F.coords, C.N_SPATIAL_CLUSTERS)
    clusters = []
    for j in range(C.N_SPATIAL_CLUSTERS):
        idx = np.flatnonzero(lab_sp == j)
        ax = {a: int(np.sum([F.axes[i] == a for i in idx])) for a in ["X", "Y", "Z"]}
        rg = {C.REGION_NAMES[k]: int(np.sum(F.region[idx] == k)) for k in range(len(C.REGION_NAMES))}
        clusters.append({"cluster": j, "medoid_daq": int(F.daq[med_sp[j]]),
                         "medoid_xyz_in": [float(v) for v in F.coords[med_sp[j]]],
                         "n_channels": int(len(idx)), "daq": [int(F.daq[i]) for i in idx],
                         "axis_counts": ax, "region_counts": {k: v for k, v in rg.items() if v},
                         "n_unique_locations": int(len(np.unique(np.round(F.coords[idx], 6), axis=0)))})
    impossible = []
    for cl in clusters:
        for a in ["X", "Y", "Z"]:
            if cl["axis_counts"][a] == 0:
                impossible.append(f"spatial cluster {cl['cluster']} contains no {a}-axis channel")
        if len(cl["region_counts"]) < 2:
            impossible.append(f"spatial cluster {cl['cluster']} spans only region(s) "
                              f"{list(cl['region_counts'])} — region/axis balance not achievable")

    # ---------------------------------------------------------------- SPLIT FAMILY 3: frequency cores
    nf = F.Nf
    edges = np.linspace(0, nf, C.N_FREQ_CORES + 1).astype(int)
    cores = []
    for j in range(C.N_FREQ_CORES):
        core = np.arange(edges[j], edges[j + 1])
        f_lo, f_hi = float(F.freqs[core[0]]), float(F.freqs[core[-1]])
        guard = np.flatnonzero((F.freqs >= f_lo - C.GUARD_HZ) & (F.freqs <= f_hi + C.GUARD_HZ))
        train = np.setdiff1d(np.arange(nf), guard)
        cores.append({"core": j, "core_line_idx": [int(v) for v in core],
                      "core_hz": [f_lo, f_hi], "n_core_lines": int(len(core)),
                      "guard_hz": C.GUARD_HZ,
                      "excluded_from_training_line_idx": [int(v) for v in guard],
                      "n_excluded": int(len(guard)), "n_train_lines": int(len(train)),
                      "min_gap_to_nearest_training_line_hz":
                          float(np.min(np.abs(F.freqs[train][:, None] - F.freqs[core][None, :])))})

    # ---------------------------------------------------------------- SPLIT FAMILY 4: joint (hash permutation)
    h = hashlib.sha256(HASH_SEED.encode()).digest()
    order = sorted(range(C.N_FREQ_CORES), key=lambda i: h[i])
    joint = [{"pair": j, "spatial_cluster": j, "frequency_core": int(order[j])}
             for j in range(C.N_SPATIAL_CLUSTERS)]

    split = {
        "frozen_before_any_residual_was_inspected": True,
        "built_from": "sensor coordinates (in), response-axis labels, frequency grid — no response data",
        "family_1_drive": {"folds": [{"fold": i, "held_out_drive": k, "label": lab}
                                     for i, (k, lab, _a) in enumerate(C.DRIVES)],
                           "note": "leave-one-drive-out; the held-out drive's log-gain c_d is integrated over "
                                   "its prior-predictive N(c_bar, tau_c^2) fitted on training drives only. "
                                   "Because the residual GP is an independent realisation per drive "
                                   "(decisions_log F2), K_*T = 0 here and arm E1 is identical to E0 by "
                                   "construction in this family."},
        "family_2_spatial": {"method": "deterministic k-medoids on RAW physical coordinates (inches); ties "
                                       "broken by lowest index; farthest-point init from the point nearest the "
                                       "centroid",
                             "n_clusters": C.N_SPATIAL_CLUSTERS, "clusters": clusters,
                             "impossible_strata": impossible},
        "family_3_frequency": {"method": "5 contiguous cores spanning the analysis band; a 10 Hz guard on both "
                                         "sides of each core is removed from TRAINING; scoring uses core lines only",
                               "cores": cores},
        "family_4_joint": {"method": "spatial cluster x frequency core, pairing = permutation derived from "
                                     f"SHA-256('{HASH_SEED}')",
                           "sha256_seed_hex": hashlib.sha256(HASH_SEED.encode()).hexdigest(),
                           "pairs": joint, "stage": "Stage 1 only; Stage 2 may not expand this budget"},
        "no_outer_test_tuning": "All covariance and mean hyperparameters are either fixed a priori (l_f, l_x, r) "
                                "or fitted INSIDE the training portion of each fold. No held-out response is "
                                "used to choose knots, length scales, shrinkage, interval width or calibration.",
    }
    (C.OUT / "split_registry.json").write_text(json.dumps(split, indent=2))

    # ---------------------------------------------------------------- MEAN BASIS REGISTRY
    logf = np.log(F.freqs)
    lo, hi = float(np.log(C.BAND[0])), float(np.log(C.BAND[1]))
    df_freq = 6
    n_interior = df_freq - 4                                # cubic: df = n_interior + degree + 1
    interior = list(np.linspace(lo, hi, n_interior + 2)[1:-1])
    Bf = bspline_basis(logf, interior, lo, hi)
    assert Bf.shape[1] == df_freq, Bf.shape

    Xs = (F.coords - F.coords.mean(0)) / F.coords.std(0)
    med_rbf, _lab_rbf = kmedoids(Xs, 5)
    centers = Xs[med_rbf]
    Dc = np.linalg.norm(centers[:, None, :] - centers[None, :, :], axis=2)
    scale = float(np.median(Dc[Dc > 0]))
    Rbf = np.exp(-0.5 * (np.linalg.norm(Xs[:, None, :] - centers[None, :, :], axis=2) / scale) ** 2)
    Reg = np.zeros((F.Nc, len(C.REGION_NAMES)))
    Reg[np.arange(F.Nc), F.region] = 1.0
    Loc = np.concatenate([Reg, Rbf], axis=1)               # (Nc, 10)
    axlist = ["X", "Y", "Z"]
    Ax = np.zeros((F.Nc, len(axlist)))
    for i, a in enumerate(F.axes):
        Ax[i, axlist.index(a)] = 1.0

    basis = {
        "frozen_before_any_residual_was_inspected": True,
        "frequency_main_effect": {
            "form": "cubic B-spline in log(f)", "df": df_freq, "degree": 3,
            "boundary_knots_log_f": [lo, hi],
            "boundary_knots_hz": [float(C.BAND[0]), float(C.BAND[1])],
            "interior_knots_log_f": [float(v) for v in interior],
            "interior_knots_hz": [float(np.exp(v)) for v in interior],
            "spacing_rule": "interior knots equally spaced in log f"},
        "location_main_effect": {
            "region_indicators": C.REGION_NAMES,
            "region_assignment": "nearest frozen physical feature (decisions_log F4)",
            "n_rbf": 5,
            "rbf_center_method": "deterministic k-medoids on standardized sensor coordinates (per-axis "
                                 "mean 0 / sd 1); coordinates only",
            "rbf_center_daq": [int(F.daq[i]) for i in med_rbf],
            "rbf_center_xyz_in": [[float(v) for v in F.coords[i]] for i in med_rbf],
            "rbf_center_standardized": [[float(v) for v in centers[j]] for j in range(len(centers))],
            "rbf_scale_standardized": scale,
            "rbf_scale_rule": "median nonzero pairwise distance between centers",
            "coord_mean_in": [float(v) for v in F.coords.mean(0)],
            "coord_sd_in": [float(v) for v in F.coords.std(0)]},
        "response_axis_main_effect": {"labels": axlist, "form": "frozen one-hot",
                                      "counts": {a: int(Ax[:, i].sum()) for i, a in enumerate(axlist)}},
        "interaction": {"form": "tensor product of the frequency basis with the location basis",
                        "n_columns": int(df_freq * Loc.shape[1]),
                        "explicitly_excluded": "channel identity — a per-channel random effect has ZERO "
                                               "predictive mean at an unseen channel and may not be credited "
                                               "as spatial transfer"},
        "column_counts": {"frequency": df_freq, "location": int(Loc.shape[1]), "axis": len(axlist),
                          "interaction": int(df_freq * Loc.shape[1]),
                          "total_before_constraints": int(df_freq + Loc.shape[1] + len(axlist)
                                                          + df_freq * Loc.shape[1])},
        "constraints": {
            "main_effects": "weighted mean zero within each training drive, per main-effect block",
            "interaction": "zero weighted frequency margin AND zero weighted location margin",
            "rank_deficiency": f"deterministic SVD tolerance {C.RANK_TOL:g} on column-normalised blocks, "
                               "columns kept left-to-right",
            "note": "a single grand sum-to-zero constraint is explicitly NOT sufficient and is not used"},
        "coefficient_prior": {"form": "beta ~ Normal(0, Lambda_beta)",
                              "Lambda_beta_rule": "per-block variance = (target dB scale / 20*log10(e))^2 with "
                                                  "target 6 dB for main effects and 3 dB for interactions; "
                                                  "frozen here, never tuned on held-out responses",
                              "target_db_main": 6.0, "target_db_interaction": 3.0},
        "channel_variation": "handled by a per-channel nugget in the covariance, never by a mean column",
    }
    (C.OUT / "mean_basis_registry.json").write_text(json.dumps(basis, indent=2))

    np.savez_compressed(C.OUT / "basis_fable.npz", Bf=Bf, Loc=Loc, Ax=Ax, Reg=Reg, Rbf=Rbf,
                        region=F.region, cluster=lab_sp, freqs=F.freqs, coords=F.coords,
                        daq=F.daq, axes=np.array(F.axes))

    print(f"split_registry.json: 5 drive folds, {C.N_SPATIAL_CLUSTERS} spatial clusters "
          f"(sizes {[c['n_channels'] for c in clusters]}), {C.N_FREQ_CORES} frequency cores "
          f"(sizes {[c['n_core_lines'] for c in cores]}), {len(joint)} joint pairs")
    if impossible:
        print(f"  impossible strata documented: {len(impossible)}")
        for s in impossible:
            print("   -", s)
    print(f"mean_basis_registry.json: {basis['column_counts']['total_before_constraints']} raw columns "
          f"(freq {df_freq}, loc {Loc.shape[1]}, axis {len(axlist)}, interaction {df_freq*Loc.shape[1]})")
    print(f"FREEZE ok in {time.time()-t0:.2f} s")


if __name__ == "__main__":
    main()
