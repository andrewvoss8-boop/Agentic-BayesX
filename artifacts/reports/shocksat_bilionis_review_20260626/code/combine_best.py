#!/usr/bin/env python3
"""
BEST agentic remesh (al_rho_lo) + BEST Bayesian updating (modal-feature NUTS), on ONE consistent metric.
Andrew's request: actually run our best Bayesian updating on our best remeshed FEM.

Best remesh  = al_rho_lo  (aluminium mass x0.8) — top FRF-corr in modelform_sweep.json (0.379, generous metric).
               It is a PURE MASS edit, so stiffness K (and the per-group K blocks theta scales) are unchanged.
Best Bayes   = the converged modal-feature NUTS that calibrates the 9 stiffness groups theta to the pooled clean
               multi-reference measured modal frequencies (the bayes_update.py procedure), but on the REMESHED FEM.

What it produces (out/combine_best.json + figures/combine_best.png):
  1. Self-check: reproduce the inherited-FEM honest metric (fig_frf_comparison "updated" = 0.338) — proves the pipeline.
  2. Honest FRF log|H| correlation on the al_rho_lo SHAPES with calibration (deterministic participations phi_s*phi_d
     + ONE global gain — the SAME honest metric as #1), using (a) measured/oracle freq+damping and (b) the Bayesian
     theta-posterior frequencies. This is the literal best-remesh + best-Bayes number on the honest metric.
  3. The Bayesian updating result on the remeshed FEM: theta posterior, NUTS convergence, held-out modal-freq error.

Reuses validated primitives byte-for-byte where possible (rescore_sigma.sigma_from_vecs for Phi/pd; modal_feature
.calibrate_modal for the NUTS; reduce_model recipe for the reduced blocks). Resumable: caches the eigensolve.
"""
from __future__ import annotations
import json, os, sys, time
from types import SimpleNamespace
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

PSD = Path("/Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/shocksat_psd_envelope_twin_20260623")
sys.path.insert(0, str(PSD / "code"))
import remodel as RM
import realfrf as rf
import modal_feature as mf
import rescore_sigma as RSC               # module-level: T, SENSOR_DOF, common, DRIVE_DOF, mfreqs, ash_damp, tau, w, mm
from modal_multiref import MODAL_REFS, CACHE

HERE = Path(__file__).resolve().parent.parent
OUT = HERE / "out"; FIG = HERE / "figures"; OUT.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
EDIT_ID = "al_rho_lo"; EDIT = {"mass_scale": {"aluminum": 0.8}}
GROUPS = {  # reduce_model.py order; sorted(GROUPS) == GNAMES
    "bottom_box": ["shell_101", "shell_102", "shell_103"], "steel_welds": ["shell_104", "shell_105", "shell_106"],
    "top_box": ["shell_201", "shell_202", "shell_203"], "al_welds": ["shell_204", "shell_205", "shell_206"],
    "angle_brackets": ["shell_301", "shell_302"], "cross_beam": ["shell_401"],
    "plates": ["shell_501", "shell_601", "shell_701"],
    "joints": ["bush_801", "bush_802", "bush_803", "bush_804", "bush_805", "bush_806", "bush_807"],
    "contact": ["bush_902"]}
GNAMES = sorted(GROUPS)
t0 = time.time()
def log(m): print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)


def solve_edit():
    """Generalized eigensolve of (baseline K, al_rho_lo M). In-memory (avoid a 256MB cache write). Returns vals, vecs."""
    T = RSC.T
    Kr = (T.T @ RM.build_K({}) @ T).tocsc()              # al_rho_lo has NO stiffness edit
    Mr = (T.T @ RM.build_M(EDIT) @ T).tocsc()
    log("eigsh (al_rho_lo) ...")
    vals, vecs = eigsh(Kr, k=80, M=Mr, sigma=-1.0e3, which="LM")
    o = np.argsort(vals); vals, vecs = vals[o], vecs[:, o]
    log(f"eigsh done; elastic f[0:6] = {np.round(np.sqrt(np.clip(vals[6:12],0,None))/2/np.pi,2)}")
    return vals, vecs


def mac_match(vecs):
    mm = RSC.mm; T = RSC.T
    obs_dofs = np.array([6 * RM.G2I[int(n)] + cc for n in mm["nodes"] for cc in range(3)])
    obs_V = np.asarray(T[obs_dofs, :] @ vecs); live = mm["measured"].reshape(-1)
    pf_, pt = obs_V[live, :], mm["shapes"].reshape(33, -1)[:, live]
    return (pt @ pf_) ** 2 / (np.sum(pt ** 2, 1)[:, None] * np.sum(pf_ ** 2, 0)[None, :] + 1e-300)


def reduced_blocks(vecs):
    """al_rho_lo reduced blocks A_fix, A_g (mass=I in this basis since vecs are M_edit-orthonormal)."""
    T = RSC.T; W = np.asarray(T @ vecs[:, 6:80])                  # (n_full, 74) elastic basis
    def Kg(pids):
        K = None
        for p in pids:
            Kp = sp.load_npz(os.path.join(RM.MAT, f"K_{p}.npz"))
            K = Kp if K is None else K + Kp
        return K
    A = np.stack([W.T @ (Kg(GROUPS[g]) @ W) for g in GNAMES])      # (9,74,74)
    A_fix = W.T @ (Kg(["bush_99"]) @ W)
    return A_fix, A


def honest_corr(Phi, pd, kidx, freqs_fem, wr_hz, eta_extra_damp):
    """fig_frf_comparison synth (deterministic participations + ONE global gain). Returns median per-ch log|H| corr.
    wr_hz: per-matched-mode frequencies (Hz) to place the peaks; eta_extra_damp: per-mode fractional damping."""
    c = dict(np.load(CACHE / "m_xpos_990x.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
    f = c["freqs"]; w = 2 * np.pi * f
    daq = RSC.common
    Hdata = np.array([c["H1"][c["daq"].index(d)] for d in daq]).T          # (Nf,Nc)
    wr = wr_hz * 2 * np.pi
    eta = 2.0 * (eta_extra_damp + 1.0 / (2 * np.pi * wr_hz * RSC.tau))     # measured damping + exp-window
    den = (1 + 1j * eta)[None, :] * (wr ** 2)[None, :] - (w ** 2)[:, None]
    H = ((-(w ** 2)[:, None, None]) * (Phi[None, :, :] * pd[None, None, :]) / den[:, None, :]).sum(2)
    g = np.median(np.log(np.abs(Hdata) + 1e-30) - np.log(np.abs(H) + 1e-30))
    H = H * np.exp(g)
    co = [np.corrcoef(np.log(np.abs(H[:, k]) + 1e-30), np.log(np.abs(Hdata[:, k]) + 1e-30))[0, 1] for k in range(len(daq))]
    return float(np.median(co)), float(np.mean(np.array(co) > 0.5)), np.array(co)


def load_modes_npz(path):
    z = np.load(path, allow_pickle=True)
    return z["Phi"], z["pd"], z["kidx"], z["freqs_fem"]


def meas_dict(c):
    H = c["H1"]
    dr = [float(np.abs(H[k]).max() ** 2 / (np.percentile(np.abs(H[k]) ** 2, 25) + 1e-300)) for k in range(H.shape[0])]
    return {"freqs": c["freqs"], "H": H, "daq": [int(d) for d in c["daq"]], "dyn_range": np.array(dr)}


def main():
    rec = {"deliverable": "best agentic remesh (al_rho_lo) + best Bayesian updating (modal-feature NUTS), honest metric",
           "best_remesh": EDIT_ID, "edit": EDIT}
    # ---- measured per-mode poles/damping (for placing peaks) -------------------------------------------------
    mm = RSC.mm; mfr = mm["freqs"]; mdp = mm["damp"] / 100.0

    # ---- (1) SELF-CHECK: reproduce the inherited-FEM honest "updated" metric (expect ~0.338) -----------------
    Phib, pdb, kib, ffb = load_modes_npz(PSD / "out" / "edits" / "baseline" / "modes.npz")
    jb = np.array([int(np.argmin(np.abs(mfr - x))) for x in ffb])
    base_med, base_frac, _ = honest_corr(Phib, pdb, kib, ffb, mfr[jb], mdp[jb])
    rec["selfcheck_baseline_updated_corr"] = round(base_med, 3)
    log(f"[selfcheck] inherited-FEM honest 'updated' corr = {base_med:.3f} (expect ~0.338)")

    # ---- solve al_rho_lo, build its matched modes.npz (same format/convention as baseline) -------------------
    vals, vecs = solve_edit()
    MAC = mac_match(vecs)
    sig, dbmed, nm, nmatch, Phi, pd, kidx = RSC.sigma_from_vecs(vecs, MAC)
    freqs_fem_all = np.sqrt(np.clip(vals, 0, None)) / (2 * np.pi)
    ff = freqs_fem_all[kidx]
    np.savez_compressed(PSD / "out" / "edits" / EDIT_ID / "modes.npz",
                        Phi=Phi, pd=pd, kidx=kidx, daq=np.array(RSC.common), freqs_fem=ff)
    rec["n_matched_modes"] = int(nmatch); rec["heldout_sigma_al_rho_lo"] = round(sig, 3)

    # ---- (2a) honest FRF corr on al_rho_lo SHAPES + ORACLE (measured) freq+damping ---------------------------
    j = np.array([int(np.argmin(np.abs(mfr - x))) for x in ff])
    o_med, o_frac, _ = honest_corr(Phi, pd, kidx, ff, mfr[j], mdp[j])
    rec["remesh_oracle_cal_corr"] = round(o_med, 3); rec["remesh_oracle_cal_frac_gt0.5"] = round(o_frac, 2)
    log(f"[remesh+oracle-cal, honest] corr = {o_med:.3f}")

    # ---- (3) BEST BAYESIAN UPDATING on the remeshed FEM: modal-feature NUTS on al_rho_lo reduced blocks ------
    A_fix, A = reduced_blocks(vecs)
    cons = np.abs(np.sort(np.linalg.eigvalsh(A_fix + A.sum(0))) - vals[6:80]) / vals[6:80]
    rec["reduced_blocks_consistency_max_rel_err"] = float(cons.max())
    log(f"[reduced blocks] nominal consistency max rel eigval err = {cons.max():.2e}")
    R2 = SimpleNamespace(A_fix=A_fix, A=A)
    # pooled clean multi-reference measured modes matched to THIS model (bayes_update.py procedure)
    ch = rf.build_channels(rf.load_reduced(), [d for d in range(1, rf.N_ACCEL_RECORDERS + 1) if d not in rf.BAD_DAQ])
    pooled = {}
    for key in MODAL_REFS:
        c = dict(np.load(CACHE / f"{key}.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
        fq, _ = mf.extract_measured_modes(meas_dict(c), SimpleNamespace(daq=ch.daq))
        for jm, hz in mf.match(R2, fq)[0]:
            pooled.setdefault(int(jm), []).append(float(hz))
    idx = np.array(sorted(pooled)); wmeas = np.array([np.median(pooled[m]) for m in idx])
    ho = np.arange(len(idx)) % 5 == 4; obs = ~ho
    tp, sw2, dg = mf.calibrate_modal(R2, idx[obs], wmeas[obs], fg=list(range(9)), seed=0,
                                     warmup=1000, samples=1000, chains=4)
    femf_nom = mf.fem_modes_np(R2, np.ones(9))
    sub = np.linspace(0, len(tp) - 1, 300).astype(int)
    skill_num, skill_den = [], []
    for m, wm in zip(idx[ho], wmeas[ho]):
        fpred = np.array([mf.fem_modes_np(R2, tp[s])[m] for s in sub])
        skill_num.append(abs(np.median(fpred) - wm)); skill_den.append(abs(femf_nom[m] - wm))
    rec["bayes_on_remesh"] = {
        "n_pooled_modes": int(len(idx)), "convergence": {
            "max_rhat": round(dg["max_rhat"], 4), "min_ESS": round(float(dg["min_ess"]), 0),
            "divergences": int(dg["divergences"]), "converged": bool(dg["converged"]), "chains": dg["n_chains"]},
        "sigma_w2_rel_median": round(float(np.median(sw2)), 4),
        "heldout_freq_err_pct_calibrated": round(float(100 * np.mean(skill_num) / np.mean(wmeas[ho])), 2),
        "heldout_freq_err_pct_nominal": round(float(100 * np.mean(skill_den) / np.mean(wmeas[ho])), 2),
        "theta_2.5_50_97.5": {GNAMES[g]: [round(float(np.percentile(tp[:, g], q)), 3) for q in (2.5, 50, 97.5)]
                              for g in range(9)}}
    log(f"[bayes on remesh] R-hat {dg['max_rhat']:.4f} ESS {dg['min_ess']:.0f} div {dg['divergences']} "
        f"conv={dg['converged']}; held-out freq err {rec['bayes_on_remesh']['heldout_freq_err_pct_calibrated']}% "
        f"vs nominal {rec['bayes_on_remesh']['heldout_freq_err_pct_nominal']}%")

    # ---- (2b) honest FRF corr on al_rho_lo SHAPES + BAYESIAN theta-posterior frequencies ---------------------
    # theta-model FEM frequencies for the matched elastic modes (kidx are full-mode idx; elastic idx = kidx-6)
    th_med = np.median(tp, axis=0)
    lam_th = np.sort(np.clip(np.linalg.eigvalsh(A_fix + np.einsum("g,gij->ij", th_med, A)), 1e-9, None))
    f_th_elastic = np.sqrt(lam_th) / (2 * np.pi)                  # (74,)
    el = np.array(kidx) - 6
    ok = (el >= 0) & (el < len(f_th_elastic))
    if ok.all():
        f_theta = f_th_elastic[el]
        b_med, b_frac, _ = honest_corr(Phi, pd, kidx, ff, f_theta, mdp[j])
        rec["remesh_bayes_cal_corr"] = round(b_med, 3); rec["remesh_bayes_cal_frac_gt0.5"] = round(b_frac, 2)
        log(f"[remesh+bayes-theta-cal, honest] corr = {b_med:.3f}")

    rec["summary"] = {
        "inherited_FEM_no_cal (fig)": 0.269, "inherited_FEM_calibrated_honest (selfcheck)": rec["selfcheck_baseline_updated_corr"],
        "best_remesh_calibrated_oracle_honest": rec["remesh_oracle_cal_corr"],
        "best_remesh_calibrated_BAYES_honest": rec.get("remesh_bayes_cal_corr"),
        "best_remesh_generous_LSQ_metric (modelform_sweep)": 0.379}
    (OUT / "combine_best.json").write_text(json.dumps(rec, indent=2))
    print("\n" + json.dumps(rec["summary"], indent=2))
    print(f"\nDONE in {time.time()-t0:.0f}s -> out/combine_best.json")
    return rec


if __name__ == "__main__":
    main()
