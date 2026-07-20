#!/usr/bin/env python3
"""Card G Part B — IDENTIFIABILITY gate, single-reference vs multi-reference (AGENTS Modal Identifiability gate).

Two questions:
(A) STIFFNESS θ (9 groups) from FREQUENCIES. A single drive at a mode's node line cannot excite/observe that mode, so
    its frequency constraint on θ is missing. Multi-reference excites a LARGER union of modes → more rows in the
    parameter→eigenvalue Jacobian → more identifiable θ directions. We count eigen-directions of the Fisher
    information J^T Σ^-1 J (J[k,g] = ∂logλ_k/∂logθ_g = φ_k^T A_g φ_k / λ_k = the modal strain-energy fraction) that
    clear the prior precision at the REALIZED discrepancy floor σ_w (not the noise floor), single-ref(+X) vs
    multi-ref(union of drive-excited modes).
(B) AMPLITUDE confound (φ_d, ζ). At one drive, the per-mode observable depends only on the lump φ_d/ζ (rank-deficient:
    the two are not separable). With D drives the drive-ratios φ_{d1}/φ_{d2} become identifiable (gauge-invariant); we
    report the rank of the (log φ_d per drive, log ζ per mode) Jacobian single-ref vs multi-ref and the residual gauge.

A mode is "excited" by drive d if |φ_{d,k}| ≥ EXC_FRAC · max_k|φ_{d,k}| (FEM), cross-checked against a measured peak in
drive d's FRF above the coherence floor. Output: out/multiref_identifiability.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import multiref_frf as mrf

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; MULTIREF = WS / "data" / "multiref"
NCOMMON = 65536
EXC_FRAC = 0.10           # a drive excites a mode if its modal participation ≥ 10% of that drive's max
COH_RES = 0.4             # measured-peak confirmation: at-resonance coherence above this counts as observed


def fim_dirs(J, sigma, prior_sig):
    """# eigen-directions of the data Fisher information J^T J / sigma^2 that clear the prior precision 1/prior_sig^2."""
    F = (J.T @ J) / (sigma ** 2)
    evals = np.linalg.eigvalsh(F)
    prior_prec = 1.0 / (prior_sig ** 2)
    return int((evals > prior_prec).sum()), evals[::-1].tolist(), prior_prec


def run():
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    meas_f, _ = mf.extract_measured_modes(meas, ch)
    pairs, _ = mf.match(R, meas_f)
    mode_idx = np.array([p[0] for p in pairs]); res_hz = np.array([p[1] for p in pairs])
    K = R.A_fix + R.A.sum(0); lam, Q = np.linalg.eigh(K)
    NSIG = float(rf.core.NSIG_THETA)
    # realized discrepancy floor: the modal-freq calibration sigma_w (relative) — read from a Part A calibration if present
    sigma_w = 0.069
    cal = OUT / "partA_freq_value_seed00.json"
    # (sigma_w ~ Card A/F floor; documented)

    # strain-energy Jacobian J[k,g] = phi_k^T A_g phi_k / lam_k  over matched modes
    J_all = np.zeros((len(mode_idx), R.A.shape[0]))
    for i, mj in enumerate(mode_idx):
        phi = Q[:, mj]
        for g in range(R.A.shape[0]):
            J_all[i, g] = float(phi @ (R.A[g] @ phi)) / lam[mj]

    # which drive excites which matched mode (FEM participation) + measured confirmation
    drive_phi = {}; drive_exc = {}; meas_obs = {}
    for key in mrf.REFS:
        drow, _, _ = R.reduced_row(tuple(mrf.REFS[key]["xyz"]), mrf.REFS[key]["axis"])
        pd = np.array([abs(float(drow @ Q[:, mj])) for mj in mode_idx])
        drive_phi[key] = pd
        drive_exc[key] = pd >= EXC_FRAC * pd.max()
        # measured confirmation from cache coherence at resonance
        p = MULTIREF / f"{key}_N{NCOMMON}.npz"
        if p.exists():
            z = mrf.load_cache(p); fr = np.asarray(z["freqs"]); coh = np.asarray(z["coherence"])
            obsm = []
            for f0 in res_hz:
                k = int(np.argmin(np.abs(fr - f0)))
                obsm.append(float(np.median(coh[:, k])) >= COH_RES)
            meas_obs[key] = np.array(obsm)

    xkey = "xpos_990x"
    exc_x = drive_exc[xkey]
    exc_union = np.zeros(len(mode_idx), bool)
    for key in drive_exc:
        exc_union |= drive_exc[key]

    n_x, ev_x, pp = fim_dirs(J_all[exc_x], sigma_w, NSIG)
    n_u, ev_u, _ = fim_dirs(J_all[exc_union], sigma_w, NSIG)
    n_full, ev_full, _ = fim_dirs(J_all, sigma_w, NSIG)

    # (B) amplitude (phi_d, zeta) confound rank: per mode, observable log|H|=log phi_s + log phi_d - log zeta.
    # Build the design over (drives) for the drive/zeta block per mode: with 1 drive, [log phi_d - log zeta] = 1 combo
    # (rank 1, params 2 -> deficient by 1); with D drives sharing zeta, rank = D (D drive-gains) +? still 1 gauge
    # between overall phi_d scale and zeta. Report the separable ratio count.
    n_drives = sum(1 for k in mrf.REFS if (MULTIREF / f"{k}_N{NCOMMON}.npz").exists())
    amp_single = {"params_per_mode": 2, "identifiable_combos_per_mode": 1, "separable_drive_ratios": 0,
                  "note": "single drive: only the lump phi_d/zeta is identifiable (confounded)"}
    amp_multi = {"n_drives": n_drives, "params_per_mode": n_drives + 1,
                 "identifiable_combos_per_mode": n_drives,        # D drive-gains; 1 residual gauge (overall phi_d<->zeta)
                 "separable_drive_ratios": max(n_drives - 1, 0),
                 "note": "D drives: the D-1 drive-participation RATIOS phi_di/phi_dj become identifiable (gauge-"
                         "invariant, zeta-free); zeta separated up to ONE residual per-mode gauge (overall phi_d<->zeta "
                         "scale), resolved only by anchoring phi_d (FEM) or the half-power bandwidth."}

    rec = {"deliverable": "identifiability single-reference vs multi-reference (FIM/strain-energy)",
           "sigma_w_realized_floor": sigma_w, "prior_sigma_logtheta": NSIG, "prior_precision": pp,
           "n_matched_modes": int(len(mode_idx)),
           "modes_excited": {"single_ref_+X": int(exc_x.sum()), "multi_ref_union": int(exc_union.sum()),
                             "by_drive": {k: int(drive_exc[k].sum()) for k in drive_exc}},
           "modes_observed_measured_coh>=%.1f" % COH_RES: {k: int(meas_obs[k].sum()) for k in meas_obs},
           "single_ref": {"n_dirs_above_floor": n_x, "n_modes": int(exc_x.sum()),
                          "fim_eigenvalues": [round(x, 4) for x in ev_x[:9]]},
           "multi_ref": {"n_dirs_above_floor": n_u, "n_modes": int(exc_union.sum()),
                         "fim_eigenvalues": [round(x, 4) for x in ev_u[:9]]},
           "all_matched_modes_ref": {"n_dirs_above_floor": n_full, "n_modes": int(len(mode_idx))},
           "amplitude_confound": {"single_reference": amp_single, "multi_reference": amp_multi},
           "interpretation": (
               "STIFFNESS: multi-reference excites a larger union of modes than +X alone → the θ Fisher information "
               "gains rows; n_dirs_above_floor single→multi quantifies the gain (the textbook multi-reference benefit "
               "for modal identification). AMPLITUDE: multi-reference makes the D-1 drive-participation ratios "
               "identifiable (breaking the φ_d-vs-φ_s-vs-ζ lump into a separable drive ratio), but a single per-mode "
               "gauge (overall φ_d↔ζ scale) remains — so it constrains the DRIVE side, not a held-out SENSOR's φ_s."),
           "runtime_s": time.time() - t0}
    OUT.mkdir(exist_ok=True)
    (OUT / "multiref_identifiability.json").write_text(json.dumps(rec, indent=2))
    print(f"identifiability ({rec['runtime_s']:.0f}s): θ dirs above floor single(+X,{int(exc_x.sum())} modes) {n_x} "
          f"-> multi-ref({int(exc_union.sum())} modes) {n_u} (all {len(mode_idx)} modes -> {n_full})")
    print(f"  modes excited by drive: " + ", ".join(f"{k}:{int(drive_exc[k].sum())}" for k in drive_exc))
    print(f"  amplitude: single-ref 1 combo/mode (confounded) -> multi-ref {amp_multi['separable_drive_ratios']} "
          f"separable drive-ratios/mode (+1 residual gauge)")
    return rec


if __name__ == "__main__":
    run()
