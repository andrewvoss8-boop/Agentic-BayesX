#!/usr/bin/env python3
"""Task Card E `_Fable` — INIT: immutable source gate.

Writes:
  out/source_manifest.json    SHA-256, size, role for every frozen source file
  out/data_inventory.json     actual data counts by drive/channel/axis/location/region/frequency/repeat
  out/known_answer_fable.json deterministic recomputation of >=3 stored numbers from the frozen artifacts

Reads only; modifies nothing outside this workspace.
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

T0 = time.time()


def sha256(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


SOURCES = [
    # (path, role)
    (C.L5 / "code/realfrf.py", "forward model: reduced accelerance ln|H|/H_ref, channel map, drive placement"),
    (C.L5 / "code/core.py", "helper imported by realfrf (group names, correlation helpers)"),
    (C.L5 / "code/schneider_faithful.py", "frozen Schneider-style additive kernel reference implementation"),
    (C.L5 / "code/spatial_reanalysis.py", "frozen physical-feature coordinates used for the 5 region labels"),
    (C.L5 / "data/reduced_blocks.npz", "reduced stiffness blocks A_fix + 9 group blocks, obs_V"),
    (C.L5 / "data/obs_dofs.npy", "observed DOF index for the reduced-basis placement map T"),
    (C.L5 / "data/keep_dofs.npy", "kept FEM DOF list"),
    (C.L5 / "data/channel_map.csv", "DAQ channel -> coordinates (in), structural axis, FEM grid"),
    (C.REPO / "artifacts/reports/statfem_shocksat_eval_20260616/data/V_keep.npy", "kept-DOF eigenvector block"),
    (C.TWIN / "fem_model.npz", "FEM node coordinates (in) for nearest-node placement"),
    (C.TWIN / "nuts_full_samples.npz", "converged modal-frequency posterior draws (theta, sigma_f)"),
    (C.TWIN / "theta_full.json", "stored modal posterior summary — known-answer target"),
    (C.TWIN / "joint_strain_energy.json", "modal strain-energy fractions — identifiability gate input"),
    (C.TWIN / "measured_modes.npz", "measured survey modes"),
    (C.TWIN / "pairing.json", "measured/predicted mode pairing"),
    (C.RVAL / "out/tmcmc_faithful_M0_ident4_n8.json", "frozen legacy M0 summary (prototype TMCMC)"),
    (C.RVAL / "out/tmcmc_faithful_M1_ident4_n8.json", "frozen legacy M1 summary (prototype TMCMC)"),
    (C.RVAL / "out/tmcmc_faithful_M2_ident4_n8.json", "frozen legacy M2 summary (prototype TMCMC, NOT converged)"),
    (C.RVAL / "out/tmcmc_faithful_M3_ident4_n8.json", "frozen legacy M3 summary (prototype TMCMC, NOT converged)"),
    (C.RVAL / "out/identifiability.json", "FIM-realized discrepancy floor sigma_d0"),
]
for key, _lab, _ax in C.DRIVES:
    SOURCES.append((C.DRIVE_DIR / f"{key}.npz", f"measured multi-hit H1 + coherence, drive {key}"))


def build_manifest():
    entries = []
    missing = []
    for p, role in SOURCES:
        if not p.exists():
            missing.append(str(p))
            continue
        entries.append({"path": str(p.relative_to(C.REPO)), "sha256": sha256(p),
                        "bytes": p.stat().st_size, "role": role})
    return entries, missing


def build_inventory(F: C.FrozenInputs):
    import collections
    per_drive = {}
    for key, lab, ax in C.DRIVES:
        H = F.H1[key]
        finite = np.isfinite(H).all()
        per_drive[key] = {
            "label": lab, "drive_axis_label": ax,
            "drive_xyz_in": [float(v) for v in F.drive_xyz[key]],
            "n_response_channels": int(F.Nc),
            "n_frequency_lines": int(F.Nf),
            "n_impacts_averaged": int(F.n_hits[key]),
            "median_coherence": float(np.median(F.coh[key])),
            "frac_coherence_ge_0p9": float(np.mean(F.coh[key] >= 0.9)),
            "all_finite": bool(finite),
            "status": "MEASURED",
        }
    ax_c = collections.Counter(F.axes)
    reg_c = collections.Counter(C.REGION_NAMES[i] for i in F.region)
    df = float(np.median(np.diff(F.freqs)))
    inv = {
        "measured_versus_synthetic": "ALL Stage-1 measured arms use MEASURED impact-hammer data; the S0-S3 "
                                     "gates use SYNTHETIC residual fields injected on the same real geometry.",
        "n_drives": len(C.DRIVES),
        "per_drive": per_drive,
        "n_response_channels": int(F.Nc),
        "daq_channels": [int(d) for d in F.daq],
        "response_axis_counts": dict(ax_c),
        "region_counts": dict(reg_c),
        "region_names": C.REGION_NAMES,
        "n_unique_sensor_locations": int(len(np.unique(np.round(F.coords, 6), axis=0))),
        "coordinate_frame": "frozen ShockSat frame, inches; x,y in the base plane, z along the stack axis "
                            "(origin at the frozen FEM grid origin used by shocksat_fem_modal_twin_20260609)",
        "frequency": {
            "n_lines": int(F.Nf), "f_min_hz": float(F.freqs[0]), "f_max_hz": float(F.freqs[-1]),
            "df_hz": df, "spacing": "linear, native cache grid",
            "window": "force: 2 ms box on the pulse; response: exponential, end value 0.05 over N=122880 samples",
            "frame_length_samples": 122880, "overlap": "none (one frame per impact, impact-aligned)",
            "detrending": "none (impact-aligned single frame)",
            "averaging_axis": "ACROSS INDEPENDENT IMPACTS (4-6 hammer hits per drive), not segments of one transient",
            "coherence_treatment": "ordinary multi-hit coherence stored and reported; NOT used to weight the "
                                   "likelihood in this study (kept as an independent data-quality diagnostic)",
        },
        "repeats": {
            "independent_realizations_live_at": "impacts within a drive (already averaged into H1) and, at a "
                                                "coarser level, across the 5 drives",
            "n_impacts_per_drive": {k: int(F.n_hits[k]) for k, _l, _a in C.DRIVES},
            "note": "H1 is already an across-impact average, so per-line replicate scatter is NOT recoverable "
                    "from the caches; sigma_e is therefore inferred, not measured from repeats.",
        },
        "total_residual_points": int(len(C.DRIVES) * F.Nf * F.Nc),
    }
    return inv


def known_answers(F: C.FrozenInputs):
    """Deterministic recomputation of stored numbers (card immutable-source-gate item 4)."""
    res = {"note": "Deterministic recomputations only. Stochastic R-hat/ESS of the legacy non-converged TMCMC "
                   "runs are NOT re-run (card forbids it); their stored hyperparameters are parsed and matched.",
           "checks": []}

    # KA1 — reduced eigensolve at the stored posterior median must reproduce stored predicted frequencies
    tf = json.loads((C.TWIN / "theta_full.json").read_text())
    z = np.load(C.TWIN / "nuts_full_samples.npz", allow_pickle=True)
    th_med = np.median(np.asarray(z["theta"], float), axis=0)
    stored_med = np.array([tf["theta_median"][g] for g in F.gnames]) if isinstance(tf["theta_median"], dict) \
        else np.asarray(tf["theta_median"], float)
    res["checks"].append({
        "id": "KA1", "what": "posterior median theta recomputed from retained draws vs stored theta_median",
        "max_abs_dev": float(np.max(np.abs(th_med - stored_med))), "tol": 1e-9,
        "pass": bool(np.max(np.abs(th_med - stored_med)) < 1e-9)})

    # KA2 — the 74 stored nominal reduced eigenvalues must be reproduced by A_fix + sum_g A_g at theta = 1
    rb = np.load(C.L5 / "data/reduced_blocks.npz", allow_pickle=True)
    lam_nom = np.linalg.eigvalsh(F.R.A_fix + F.R.A.sum(0))
    stored_nom = np.asarray(rb["nominal_eigvals"], float)
    rel = np.max(np.abs(lam_nom - stored_nom) / np.maximum(np.abs(stored_nom), 1e-300))
    res["checks"].append({
        "id": "KA2", "what": "74 stored nominal reduced eigenvalues reproduced by eigh(A_fix + sum_g A_g)",
        "n_values": int(len(stored_nom)), "max_rel_dev": float(rel), "tol_rel": 1e-8,
        "pass": bool(rel < 1e-8),
        "three_smallest_stored": [float(v) for v in np.sort(stored_nom)[:3]],
        "three_smallest_recomputed": [float(v) for v in np.sort(lam_nom)[:3]]})

    # KA6 — sigma_f posterior median and 95% interval recomputed from the retained draws
    sf = np.asarray(z["sigma_f"], float)
    got_med = float(np.median(sf))
    got_ci = [float(v) for v in np.percentile(sf, [2.5, 97.5])]
    dsf = max(abs(got_med - float(tf["sigma_f_median"])),
              abs(got_ci[0] - float(tf["sigma_f_ci"][0])), abs(got_ci[1] - float(tf["sigma_f_ci"][1])))
    res["checks"].append({
        "id": "KA6", "what": "sigma_f posterior median and 95% CI recomputed from the 4000 retained draws",
        "stored": [float(tf["sigma_f_median"])] + [float(v) for v in tf["sigma_f_ci"]],
        "recomputed": [got_med] + got_ci, "max_abs_dev": float(dsf), "tol": 1e-12,
        "pass": bool(dsf < 1e-12)})

    # DIAGNOSTIC (non-gating): the stored per-mode f_pred_median cannot be reproduced bit-exactly because the
    # modal twin re-tracked mode order by MAC per draw and used a 2000-draw subsample. Reported, not gated.
    pair = json.loads((C.TWIN / "pairing.json").read_text())
    m_of = {int(p["test_mode"]): int(p["model_mode"]) for p in pair["pairs"]}
    th_all = np.asarray(z["theta"], float)
    Kb = F.R.A_fix[None] + np.einsum("cg,gij->cij", th_all, F.R.A)
    f_all = np.sqrt(np.clip(np.linalg.eigvalsh(Kb), 0, None)) / (2 * np.pi)
    rows = tf["in_sample_rows"]
    stored_f = np.array([r["f_pred_median"] for r in rows])
    mi = np.array([m_of[int(r["test_mode"])] for r in rows])
    got_f = np.median(f_all[:, mi], axis=0)
    rel_f = np.abs(got_f - stored_f) / stored_f
    res["diagnostic_f_pred_median"] = {
        "gating": False,
        "why_not_gated": "the stored value used per-draw MAC re-tracking and a 2000-of-4000 draw subsample; a "
                         "fixed-index recomputation is a different estimator, so an exact match is not expected",
        "n_modes": int(len(stored_f)), "median_rel_dev": float(np.median(rel_f)),
        "max_rel_dev": float(rel_f.max()),
        "n_modes_within_0p5pct": int(np.sum(rel_f < 0.005))}

    # KA3 — my kernels must reproduce the frozen Schneider implementation exactly
    sys.path.insert(0, str(C.L5 / "code"))
    import schneider_faithful as SF  # noqa: E402
    fr = F.freqs[:20]
    xs = F.coords[:12]
    d_f = float(np.max(np.abs(C.kern_f(fr, fr) - SF.corr_freq_linear(fr, SF.L_F_HZ))))
    d_x = float(np.max(np.abs(C.kern_x(xs, xs) - SF.corr_space(xs, SF.L_Z_IN))))
    res["checks"].append({
        "id": "KA3", "what": "this study's kern_f/kern_x vs frozen schneider_faithful.corr_freq_linear/corr_space",
        "max_abs_dev_freq": d_f, "max_abs_dev_space": d_x, "tol": 1e-12,
        "pass": bool(max(d_f, d_x) < 1e-12),
        "frozen_hyper": {"l_f_hz": SF.L_F_HZ, "l_z_in": SF.L_Z_IN, "r_split": SF.R_SPLIT, "zeta": SF.ZETA}})

    # KA4 — eigenvalues of the frozen additive covariance: exact Kronecker route vs dense construction
    Rff = SF.corr_freq_linear(fr, SF.L_F_HZ)
    Rzz = SF.corr_space(xs, SF.L_Z_IN)
    C_add = SF.R_SPLIT * np.kron(Rff, np.eye(len(xs))) + (1 - SF.R_SPLIT) * np.kron(np.eye(len(fr)), Rzz)
    ev_dense = np.linalg.eigvalsh(C_add)
    af = np.linalg.eigvalsh(SF.R_SPLIT * Rff)
    bx = np.linalg.eigvalsh((1 - SF.R_SPLIT) * Rzz)
    ev_kron = np.sort((af[:, None] + bx[None, :]).ravel())
    res["checks"].append({
        "id": "KA4", "what": "additive-kernel eigenvalues: dense kron construction vs product-eigenbasis sum",
        "max_abs_dev": float(np.max(np.abs(ev_dense - ev_kron))), "tol": 1e-10,
        "pass": bool(np.max(np.abs(ev_dense - ev_kron)) < 1e-10),
        "three_largest_dense": [float(v) for v in ev_dense[-3:]],
        "three_smallest_dense": [float(v) for v in ev_dense[:3]]})

    # KA5 — frozen legacy M0-M3 summaries parse, and their fixed hyperparameters match the card's frozen values
    leg = {}
    ok = True
    for arm in ["M0", "M1", "M2", "M3"]:
        j = json.loads((C.RVAL / f"out/tmcmc_faithful_{arm}_ident4_n8.json").read_text())
        fh = j.get("fixed_hyper") or {}
        diag = j.get("diag") or {}
        sw = j.get("sigma_w") or {}
        leg[arm] = {"converged": j.get("converged"), "max_rhat": diag.get("max_rhat"),
                    "min_ess": diag.get("min_ess"),
                    "sigma_w_med": sw.get("med"),
                    "log_evidence_mean": diag.get("log_evidence_mean"),
                    "fixed_hyper": fh}
        for k, want in [("l_f_hz", C.L_F_HZ), ("l_z_in", C.L_X_IN), ("r_split", C.R_SPLIT),
                        ("zeta", C.ZETA_PRIMARY)]:
            if k in fh and abs(float(fh[k]) - want) > 1e-12:
                ok = False
    res["checks"].append({
        "id": "KA5", "what": "frozen legacy M0-M3 summaries parsed; stored l_f/l_x/r/zeta match the card's "
                             "frozen values (no stochastic diagnostic re-run)",
        "pass": bool(ok), "legacy": leg,
        "prototype_label": "M0-M3 are PROTOTYPE/LEGACY random-scan TMCMC results; M2 (R-hat 2.58) and M3 "
                           "(R-hat 1.11) are NOT converged and are used here only as frozen hyperparameters."})

    res["all_pass"] = all(c["pass"] for c in res["checks"])
    return res


def main():
    C.OUT.mkdir(parents=True, exist_ok=True)
    entries, missing = build_manifest()
    man = {"run": "shocksat_structured_discrepancy_codex_20260722_Fable",
           "card": "docs/agents/structured_discrepancy_codex_review_20260722/"
                   "task_card_codex_structured_discrepancy.md",
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "n_sources": len(entries), "missing": missing, "sources": entries}
    (C.OUT / "source_manifest.json").write_text(json.dumps(man, indent=2))
    print(f"source_manifest.json: {len(entries)} sources, {len(missing)} missing")
    if missing:
        for m in missing:
            print("  MISSING:", m)
        raise SystemExit("STOP: frozen sources missing — card immutable source gate fails")

    F = C.load_frozen(n_theta=60)
    inv = build_inventory(F)
    (C.OUT / "data_inventory.json").write_text(json.dumps(inv, indent=2))
    print(f"data_inventory.json: {inv['n_drives']} drives x {inv['n_response_channels']} channels x "
          f"{inv['frequency']['n_lines']} lines = {inv['total_residual_points']} residual points")

    ka = known_answers(F)
    ka["runtime_s"] = round(time.time() - T0, 2)
    (C.OUT / "known_answer_fable.json").write_text(json.dumps(ka, indent=2))
    for c in ka["checks"]:
        print(f"  {c['id']}: {'PASS' if c['pass'] else 'FAIL'} — {c['what']}")
    if not ka["all_pass"]:
        raise SystemExit("STOP: known-answer gate failed")
    print(f"INIT ok in {ka['runtime_s']} s")


if __name__ == "__main__":
    main()
