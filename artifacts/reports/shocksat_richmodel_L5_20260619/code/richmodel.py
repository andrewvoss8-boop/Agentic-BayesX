#!/usr/bin/env python3
"""Card E core: build a RICHER LOCAL stiffness parameterization (per-PID reduced blocks regrouped) and run the
AGENTS Modal/Eigenproblem Identifiability gate on it BEFORE any sharpen/no-sharpen conclusion.

Recipe (modal-twin scripts/reduce_model.py): reduced basis W = T @ V_keep[:, 6:] (full -> 74 elastic modes,
6 rigid-body removed). Per-PID reduced block  B_pid = W^T K_pid W  (K_pid = per-PID full-order sparse stiffness).
A richer parameterization REGROUPS the 26 per-PID blocks into finer sub-groups; theta=1 reconstructs the
nominal K EXACTLY (Sum_pid B_pid == A_g of reduced_blocks; A_fix + Sum all == nominal eigvals).

Why the gate is cheap + decisive: for the L5 eigenvalue likelihood, d lambda_r / d theta_g = phi_r^T A_g phi_r
= lambda_r * f_{r,g} (Hellmann-Feynman, mass-normalized) -> the modal strain-energy fraction f_{r,g} IS the FIM
sensitivity. A new local param whose SE fraction sits below the realized discrepancy floor (sigma_w2 from L5)
is NOT identifiable from frequencies and can only WIDEN the held-out prediction, not sharpen it.

Outputs:
  out/perpid_reduced.npz   (pids, B (n_pid,74,74), A_fix)
  out/integrity.json       (reconstruction errors -> checker Gate 1)
  out/param_variants.json  (the richer parameterization variants + rationale)
  out/identifiability_rich.json (strain-energy table + FIM eigen view -> checker Gate 2)
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
import scipy.sparse as sp

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
MT = WS.parent / "shocksat_fem_modal_twin_20260609"      # read-only source of per-PID blocks + reduction
MATR = MT / "matrices"

# group -> PIDs (from modal-twin reduce_model.py / groups.json)
GROUPS = {
    "bottom_box":     ["shell_101", "shell_102", "shell_103"],
    "steel_welds":    ["shell_104", "shell_105", "shell_106"],
    "top_box":        ["shell_201", "shell_202", "shell_203"],
    "al_welds":       ["shell_204", "shell_205", "shell_206"],
    "angle_brackets": ["shell_301", "shell_302"],
    "cross_beam":     ["shell_401"],
    "plates":         ["shell_501", "shell_601", "shell_701"],
    "joints":         ["bush_801", "bush_802", "bush_803", "bush_804",
                       "bush_805", "bush_806", "bush_807"],
    "contact":        ["bush_902"],
}
FIXED = ["bush_99"]
ALL_PIDS = [p for g in GROUPS for p in GROUPS[g]]
PID2GROUP = {p: g for g in GROUPS for p in GROUPS[g]}


# ----------------------------------------------------------------- per-PID reduced blocks
def build_W():
    T = sp.load_npz(MATR / "T.npz")
    V = np.load(MATR / "V_keep.npy")          # (n_keep, 80) M-orthonormal
    Ve = V[:, 6:]                              # 74 elastic columns
    W = np.asarray(T @ Ve)                     # (n_full, 74)
    return W


def build_perpid(force=False):
    outp = OUT / "perpid_reduced.npz"
    OUT.mkdir(exist_ok=True)
    if outp.exists() and not force:
        z = np.load(outp, allow_pickle=True)
        return {"pids": [str(p) for p in z["pids"]], "B": z["B"], "A_fix": z["A_fix"]}
    t0 = time.time()
    W = build_W()
    print(f"[{time.time()-t0:.0f}s] basis W {W.shape}", flush=True)
    pids = ALL_PIDS + FIXED
    B = np.zeros((len(pids), W.shape[1], W.shape[1]))
    for i, p in enumerate(pids):
        Kp = sp.load_npz(MATR / f"K_{p}.npz")
        B[i] = W.T @ (Kp @ W)
        print(f"[{time.time()-t0:.0f}s] B[{p}] fro {np.linalg.norm(B[i]):.3e}", flush=True)
    A_fix = B[pids.index("bush_99")].copy()
    np.savez_compressed(outp, pids=np.array(pids), B=B, A_fix=A_fix)
    print(f"[{time.time()-t0:.0f}s] saved {outp.name}", flush=True)
    return {"pids": pids, "B": B, "A_fix": A_fix}


def block_of(pp, pid):
    return pp["B"][pp["pids"].index(pid)]


def group_block(pp, group):
    return sum(block_of(pp, p) for p in GROUPS[group])


def verify_integrity(pp):
    """Sum_{pid in g} B_pid == A_g (reduced_blocks); A_fix + Sum all == nominal eigvals."""
    rb = np.load(WS / "data" / "reduced_blocks.npz", allow_pickle=True)
    gnames = [str(x) for x in rb["gnames"]]
    A = rb["A"]; nom = rb["nominal_eigvals"]
    grp_err = 0.0
    for gi, gname in enumerate(gnames):
        Ag_ref = A[gi]
        Ag_built = group_block(pp, gname)
        denom = max(np.linalg.norm(Ag_ref), 1e-30)
        grp_err = max(grp_err, np.linalg.norm(Ag_built - Ag_ref) / denom)
    K1 = pp["A_fix"] + sum(group_block(pp, g) for g in GROUPS)
    lam = np.sort(np.linalg.eigvalsh(K1))
    eig_err = float(np.max(np.abs(lam - nom) / nom))
    rec = {"n_pids": len(pp["pids"]), "recon_group_max_abs_rel": float(grp_err),
           "nominal_recon_max_rel_eigval_err": eig_err,
           "note": "per-PID reduced blocks B_pid=W^T K_pid W reconstruct the 9 group blocks and nominal eigvals"}
    (OUT / "integrity.json").write_text(json.dumps(rec, indent=2))
    print(f"INTEGRITY: group recon {grp_err:.2e}, nominal eigval {eig_err:.2e}")
    return rec


# ----------------------------------------------------------------- richer parameterization variants
def define_variants():
    """Each variant = ordered list of (param_name, [pids]). theta multiplies each param block. Baseline (9) +
    targeted local splits motivated by the hard-channel regions (Card D region_diagnosis):
      box column ch40/52/69 + source face -> high-SE steel/Al boxes; bolted joint ch52 -> bush_801."""
    base = [(g, GROUPS[g]) for g in sorted(GROUPS)]
    # box_split: split the two high-SE boxes (bottom 46.8%, top 34.9% SE) into per-shell params
    box_split = []
    for g in sorted(GROUPS):
        if g in ("bottom_box", "top_box"):
            for p in GROUPS[g]:
                box_split.append((f"{g}:{p}", [p]))
        else:
            box_split.append((g, GROUPS[g]))
    # joint_split: pull the bolted-joint bush_801 out of the 7-bush joints group
    joint_split = []
    for g in sorted(GROUPS):
        if g == "joints":
            joint_split.append(("joint_bolted_801", ["bush_801"]))
            joint_split.append(("joints_rest", [p for p in GROUPS[g] if p != "bush_801"]))
        else:
            joint_split.append((g, GROUPS[g]))
    # full_rich: box per-shell + bolted joint split + plates per-shell (dish ch98)
    full_rich = []
    for g in sorted(GROUPS):
        if g in ("bottom_box", "top_box", "plates"):
            for p in GROUPS[g]:
                full_rich.append((f"{g}:{p}", [p]))
        elif g == "joints":
            full_rich.append(("joint_bolted_801", ["bush_801"]))
            full_rich.append(("joints_rest", [p for p in GROUPS[g] if p != "bush_801"]))
        else:
            full_rich.append((g, GROUPS[g]))
    variants = {"base9": base, "box_split": box_split, "joint_split": joint_split, "full_rich": full_rich}
    rec = {name: {"n_params": len(v), "params": [{"name": n, "pids": p} for n, p in v]}
           for name, v in variants.items()}
    rec["rationale"] = ("box_split/full_rich split the two highest-SE substructures (steel+Al boxes) and the "
                        "dish plates per-shell so the update can change LOCAL interface kinematics (not just "
                        "whole-group level); joint_split pulls the steel<->Al bolted joint (CBUSH 801) out of "
                        "the 7-bush joints group. Hard channels: box column ch40/52/69, source face ch4/27/38, "
                        "bolted joint ch52, dish ch98.")
    (OUT / "param_variants.json").write_text(json.dumps(rec, indent=2))
    return variants


def variant_blocks(pp, variant):
    """Return (names, A_params (P,74,74), A_fix_eff). A_fix_eff = the projected fixed block (bush_99). The
    PARAM blocks together with A_fix_eff reconstruct nominal K at theta=1 (since every PID is in exactly one
    param and bush_99 is fixed)."""
    names = [n for n, _ in variant]
    A_params = np.stack([sum(block_of(pp, p) for p in pids) for _, pids in variant])
    return names, A_params, pp["A_fix"]


# ----------------------------------------------------------------- identifiability gate
def matched_modes():
    """Consensus measured modes (all channels) matched to FEM mode indices at theta=1 (re-pairing-robust:
    nearest-frequency match within tol, no greedy best-MAC). Returns (fem_mode_idx, measured_hz)."""
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    meas_f, support = mf.extract_measured_modes(meas, ch)
    pairs, femf = mf.match(R, meas_f)
    idx = np.array([p[0] for p in pairs]); wmeas = np.array([p[1] for p in pairs])
    return R, idx, wmeas, len(meas_f)


def strain_energy_and_fim(R, A_params, A_fix, names, idx, sigma_w2, prior_sigma_logtheta=rf.core.NSIG_THETA):
    """Strain-energy fractions f_{r,p} = phi_r^T A_p phi_r / lambda_r for matched modes r (mass-norm: M=I),
    plus the FIM eigen view in log-theta space.

    Observable = matched eigenvalues lambda_r (= omega_r^2). Relative discrepancy floor = sigma_w2 (L5).
    Sensitivity to log-theta_p: d lambda_r / d log theta_p = phi_r^T A_p phi_r = lambda_r * f_{r,p}.
    Normalized (per-sigma) sensitivity S_{r,p} = f_{r,p}/sigma_w2. FIM (log-theta) = S^T S. A param combination
    is data-identifiable when its FIM eigenvalue exceeds the prior precision 1/prior_sigma^2 (data > prior)."""
    K = A_fix + A_params.sum(0)
    lam, Q = np.linalg.eigh(K)
    lam = np.clip(lam, 1e-12, None)
    P = len(names)
    nmodes = len(idx)
    F = np.zeros((nmodes, P))          # strain-energy fraction per matched mode r, param p
    for ri, r in enumerate(idx):
        phi = Q[:, r]
        denom = lam[r]
        for p in range(P):
            F[ri, p] = float(phi @ (A_params[p] @ phi)) / denom
    S = F / sigma_w2                    # normalized sensitivity (per relative-sigma)
    FIM = S.T @ S
    evals, evecs = np.linalg.eigh(FIM)
    order = np.argsort(evals)[::-1]
    evals = evals[order]; evecs = evecs[:, order]
    sv = np.sqrt(np.clip(evals, 0, None))
    prior_prec = 1.0 / prior_sigma_logtheta ** 2
    n_above = int(np.sum(evals > prior_prec))
    # combo mixes for the strong combinations
    combos = []
    for k in range(min(P, max(n_above, 1) + 2)):
        w = evecs[:, k]
        mix = sorted([(names[p], float(w[p])) for p in range(P)], key=lambda t: -abs(t[1]))
        combos.append({"singular_value": float(sv[k]), "fim_eigenvalue": float(evals[k]),
                       "above_prior": bool(evals[k] > prior_prec),
                       "mix": [{"param": n, "weight": round(wt, 3)} for n, wt in mix[:4]]})
    se_typ = np.median(F, axis=0)
    se_peak = np.max(F, axis=0)
    return F, lam, Q, {"singular_values": [float(x) for x in sv], "fim_eigenvalues": [float(x) for x in evals],
                       "prior_precision": float(prior_prec), "n_combos_above_prior": n_above,
                       "combos": combos}, se_typ, se_peak


def finite_perturb(R, A_params, A_fix, idx, p_index, frac=0.10):
    """Finite-perturbation load-path check (AGENTS gate): scale param p by (1+frac), report max |df%| over the
    matched modes (re-pairing by index). Distinguishes 'in load path but low sensitivity' from 'out of path'."""
    def freqs(scale):
        Ap = A_params.copy()
        Ap[p_index] = Ap[p_index] * scale
        lam = np.linalg.eigvalsh(A_fix + Ap.sum(0))
        return np.sqrt(np.clip(np.sort(lam), 0, None)) / (2 * np.pi)
    f0 = freqs(1.0); f1 = freqs(1.0 + frac)
    df = np.abs(f1[idx] - f0[idx]) / np.maximum(f0[idx], 1e-9)
    return float(np.max(df)), float(np.median(df))


def run_identifiability(variants=("box_split", "joint_split", "full_rich"), sigma_w2=None):
    pp = build_perpid()
    verify_integrity(pp)
    vdefs = define_variants()
    # realized discrepancy floor: prefer the L5 baseline sigma_w2 if available, else nominal modal-twin value
    if sigma_w2 is None:
        try:
            base = json.loads((WS / "out" / "l5_baseline.json").read_text())
            sigma_w2 = base["calibration"]["sigma_w2_rel_med"]
        except Exception:
            sigma_w2 = 0.069   # Card A D11 L5 sigma_w2 (~7%); documented fallback
    R, idx, wmeas, n_meas = matched_modes()
    print(f"matched modes: {len(idx)} (of {n_meas} measured); sigma_w2 floor = {sigma_w2:.4f}")
    out = {"sigma_w2_discrepancy_floor_rel": float(sigma_w2), "n_matched_modes": int(len(idx)),
           "matched_fem_mode_idx": [int(i) for i in idx], "matched_measured_hz": [round(float(x), 1) for x in wmeas],
           "variants": {}}
    for vname in variants:
        names, A_params, A_fix = variant_blocks(pp, vdefs[vname])
        F, lam, Q, fim, se_typ, se_peak = strain_energy_and_fim(R, A_params, A_fix, names, idx, sigma_w2)
        params = []
        for p, nm in enumerate(names):
            mp, _ = finite_perturb(R, A_params, A_fix, idx, p)
            # identifiable iff this raw param has signal above the floor in at least one matched mode
            above = bool(se_peak[p] > sigma_w2)
            params.append({"name": nm, "group_origin": PID2GROUP.get(nm.split(":")[-1], nm),
                           "se_frac_typical": float(se_typ[p]), "se_frac_peak": float(se_peak[p]),
                           "se_over_floor_peak": float(se_peak[p] / sigma_w2),
                           "finite_perturb_max_df_pct": round(mp * 100, 4),
                           "in_load_path": bool(se_peak[p] > 1e-6),
                           "raw_above_floor": above})
        ident = [p["name"] for p in params if p["raw_above_floor"]]
        nonident = [p["name"] for p in params if not p["raw_above_floor"]]
        out["variants"][vname] = {
            "n_params": len(names), "params": params, "fim": {
                "discrepancy_floor_rel": float(sigma_w2),
                "n_combos_above_prior": fim["n_combos_above_prior"],
                "singular_values": fim["singular_values"], "fim_eigenvalues": fim["fim_eigenvalues"],
                "prior_precision": fim["prior_precision"], "combos": fim["combos"]},
            "verdict_identifiable_params": ident, "verdict_nonidentifiable_params": nonident}
        print(f"[{vname}] {len(names)} params; {fim['n_combos_above_prior']} combos clear prior; "
              f"raw-identifiable {len(ident)}/{len(names)}")
    # checker Gate 2 expects a flat top-level record for the HEADLINE variant (full_rich)
    head = out["variants"].get("full_rich") or out["variants"][list(out["variants"])[0]]
    flat = {"headline_variant": "full_rich" if "full_rich" in out["variants"] else list(out["variants"])[0],
            "params": head["params"], "fim": head["fim"], "n_matched_modes": out["n_matched_modes"],
            "verdict_identifiable_params": head["verdict_identifiable_params"],
            "verdict_nonidentifiable_params": head["verdict_nonidentifiable_params"],
            "pretest_lever": ("Params below the floor carry their signal in modes/bands not excited or not "
                              "frequency-sensitive at this single impact; the decisive lever is multi-reference / "
                              "roving-hammer data (a 2nd drive varies phi_d, breaks the participation/damping "
                              "confound) and/or mode-shape (eigenvector) observations, not more eigenfrequencies."),
            "all_variants": out}
    (OUT / "identifiability_rich.json").write_text(json.dumps(flat, indent=2))
    print(f"wrote out/identifiability_rich.json (headline {flat['headline_variant']})")
    return flat


if __name__ == "__main__":
    if "--build" in sys.argv:
        pp = build_perpid(force="--force" in sys.argv)
        verify_integrity(pp)
    else:
        run_identifiability()
