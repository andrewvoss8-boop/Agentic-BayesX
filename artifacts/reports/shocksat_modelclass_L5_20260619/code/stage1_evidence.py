#!/usr/bin/env python3
"""Card F — STAGE 1: analytic statFEM evidence (Ockham-penalized) at FIXED-MAP theta, on the modal peak-
FREQUENCY observable, for competing STIFFNESS-parameterization model classes (M0 / M1 local splits) and a
correlated-discrepancy class (M4). Fast (reduced 74-DOF, closed form). Damping classes M2/M3 are ~blind to
this observable by physics (D3) and are reported as such here; they are judged on amplitude/held-out QOI.

Construction (statFEM Eq 38; Kiran Eq 43-44). Observable Y = matched measured eigenvalues omega_hat^2 (the L5
data). Mean mu0 = FEM eigenvalues lambda(theta_MAP) at the matched mode indices (SAME for every class — Stage 1
holds theta at its L5 MAP). A model class differs only in its predictive covariance C_u + discrepancy C:
  Sigma_M = D R D + J_M diag(sigma_prior^2) J_M^T,  D = diag(sigma_w2 * Y) (relative L5 discrepancy floor),
  R = I (iid) or the Schneider frequency-correlation matrix (M4),
  J_M[r,p] = d lambda_idx[r] / d ln(eta_p) = eta0_p * phi_r^T A_params[p] phi_r   (Fox-Kapoor; mass = I),
  eta0_p = theta_MAP of param p's origin group (so the nominal config reconstructs K_MAP exactly).
log p(Y|M) = -0.5 [ (Y-mu0)^T Sigma_M^-1 (Y-mu0) + logdet(2 pi Sigma_M) ]  (Kiran Eq 44: fit - complexity).
Hyperparameters (sigma_w2, and M4's length/ratio) are type-II ML'd per class (shared scale => fair Ockham on
the parameter granularity, which has NO extra optimized DOF). sigma_prior (new-param prior width) is swept.

theta is held FIXED at the L5 MAP so the richer classes can ONLY inflate the predictive covariance along their
new directions (they cannot move the mean). This is the CONSERVATIVE statFEM Eq-38 screen; Stage-2 TMCMC (theta
free) lets the mean move and is the rigorous re-rank. Output: out/stage1_evidence.json, out/evidence_sensitivity.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize_scalar, minimize

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import cardE_richmodel as rm

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
CARD_A_OUT = WS.parent / "statfem_real_validation_20260617" / "out"
TWO_PI = 2 * np.pi
SIG_PRIOR_GRID = [0.15, 0.25, 0.40]   # new-param log-normal prior width sweep (headline = 0.25 = NSIG_THETA)
SIG_W2_GRID = np.geomspace(3e-3, 0.4, 80)


def load_theta_map():
    """L5 MAP theta (group medians) from Card A modal_feature.json (read-only)."""
    d = json.loads((CARD_A_OUT / "modal_feature.json").read_text())
    return {g: v["med"] for g, v in d["theta_post"].items()}, float(d["sigma_w2_rel"]["med"])


def whitened_logZ(resid_w, lns_sum, n, M):
    """logZ for Sigma = D M D given whitened residual resid_w=D^-1 r, lns_sum=sum ln s_r.
    M = R + G Cprior G^T (PSD, well-conditioned)."""
    sign, ld = np.linalg.slogdet(M)
    if sign <= 0:
        return -np.inf, np.nan, np.nan
    sol = np.linalg.solve(M, resid_w)
    quad = float(resid_w @ sol)
    logdet = ld + 2.0 * lns_sum + n * np.log(2 * np.pi)
    logZ = -0.5 * (quad + logdet)
    return logZ, quad, logdet


def class_logZ(Y, mu0, J, sig_prior, R=None, sig_w2=None):
    """Maximize (type-II ML) logZ over sig_w2 (and use given R for correlation). J: (n,p) or None.
    Returns dict with best logZ, sig_w2*, fit (quad) and complexity (logdet) pieces."""
    n = len(Y)
    r = Y - mu0
    Cp = (sig_prior ** 2)
    Rm = np.eye(n) if R is None else R

    def neg(sw2):
        s = sw2 * Y                      # per-mode std (relative to omega^2)
        Dinv = 1.0 / s
        rw = Dinv * r
        if J is None or J.shape[1] == 0:
            M = Rm.copy()
        else:
            G = Dinv[:, None] * J        # D^-1 J
            M = Rm + Cp * (G @ G.T)
        lZ, _, _ = whitened_logZ(rw, float(np.sum(np.log(s))), n, M)
        return -lZ

    vals = [neg(sw2) for sw2 in SIG_W2_GRID]
    i0 = int(np.argmin(vals))
    lo = SIG_W2_GRID[max(0, i0 - 1)]; hi = SIG_W2_GRID[min(len(SIG_W2_GRID) - 1, i0 + 1)]
    res = minimize_scalar(neg, bounds=(lo, hi), method="bounded")
    sw2 = float(res.x);
    s = sw2 * Y; Dinv = 1.0 / s; rw = Dinv * r
    if J is None or J.shape[1] == 0:
        M = Rm.copy()
    else:
        G = Dinv[:, None] * J; M = Rm + Cp * (G @ G.T)
    lZ, quad, logdet = whitened_logZ(rw, float(np.sum(np.log(s))), n, M)
    return {"logZ": float(lZ), "sigma_w2": sw2, "fit_quad": float(quad), "logdet": float(logdet)}


def m4_logZ(Y, mu0, fhz, sig_prior):
    """M4: M0 mean + correlated (Schneider additive) discrepancy across modes. Optimize sig_w2, ell_f, rmix."""
    n = len(Y); r = Y - mu0
    dist = np.abs(fhz[:, None] - fhz[None, :])

    def neg(p):
        sw2, ellf, rmix = p
        if sw2 <= 0 or ellf <= 0 or not (0 <= rmix < 0.999):
            return 1e18
        R = (1 - rmix) * np.eye(n) + rmix * np.exp(-dist / ellf)
        s = sw2 * Y; Dinv = 1.0 / s; rw = Dinv * r
        lZ, _, _ = whitened_logZ(rw, float(np.sum(np.log(s))), n, R)
        return -lZ

    best = None
    for ellf0 in (5.0, 15.0, 40.0):
        for rmix0 in (0.3, 0.7):
            res = minimize(neg, x0=[0.06, ellf0, rmix0], method="Nelder-Mead",
                           options={"xatol": 1e-3, "fatol": 1e-3, "maxiter": 2000})
            if best is None or res.fun < best.fun:
                best = res
    sw2, ellf, rmix = best.x
    return {"logZ": float(-best.fun), "sigma_w2": float(sw2), "ell_f_hz": float(ellf),
            "rmix": float(rmix), "n_extra_hyperparams_vs_M0fixed": 2}


def build_J(pp, variant, theta_map, V, idx):
    names, A_params, _ = rm.variant_blocks(pp, variant)
    eta0 = np.array([theta_map[rm.PID2GROUP[pids[0]]] for _, pids in variant])  # origin-group MAP
    Vm = V[:, idx]                                  # (74, n) matched eigenvectors
    # phi^T A_p phi for each matched mode r and param p:
    quad = np.einsum("ir,pij,jr->rp", Vm, A_params, Vm)   # (n, p) = phi_r^T A_p phi_r
    J = eta0[None, :] * quad                        # d lambda_r / d ln eta_p
    return names, J, eta0


def main():
    t0 = time.time()
    theta_map, sig_w2_l5 = load_theta_map()
    pp = rm.build_perpid()
    vdefs = rm.define_variants()
    R, idx, wmeas, n_meas = rm.matched_modes()
    theta9 = rf.core.theta_vector(theta_map)
    K = R.A_fix + np.einsum("g,gij->ij", theta9, R.A)
    lam, V = np.linalg.eigh(K)
    mu0 = lam[idx]
    Y = (wmeas * TWO_PI) ** 2
    fhz = wmeas.copy()
    n = len(Y)
    print(f"matched modes n={n}; theta MAP loaded; sig_w2_L5={sig_w2_l5:.3f}; resid%% "
          f"median={np.median(np.abs(Y-mu0)/Y)*100:.2f}")

    variants = {"M0_base9": vdefs["base9"], "M1_box_split": vdefs["box_split"],
                "M1_joint_split": vdefs["joint_split"], "M1_full_rich": vdefs["full_rich"]}

    # damping (M2/M3) frequency-blindness check (D3): max damped-frequency shift
    zeta_pct = json.loads((OUT / "cardD_inputs" / "damping_gate.json").read_text())["zeta_meas_pct"]
    zmax = max(zeta_pct) / 100.0
    df_damp = 1.0 - np.sqrt(max(0.0, 1.0 - zmax ** 2))     # Delta f / f from damping
    damp_note = {"max_zeta": zmax, "max_damped_freq_shift_rel": float(df_damp),
                 "sig_w2_floor": sig_w2_l5,
                 "verdict": ("damping shifts modal frequency by ~%.1e << %.3f discrepancy floor => the FREQUENCY "
                             "observable cannot rank M2/M3 vs M0; evidence here Ockham-penalizes their extra "
                             "params. Damping is judged on amplitude/held-out QOI (confound-limited)."
                             % (df_damp, sig_w2_l5))}

    out = {"observable": "modal_peak_frequency_omega2 (matched, n=%d)" % n,
           "stage": "1_fixed_MAP_theta_analytic_evidence",
           "note": ("theta held at L5 MAP; richer classes can only inflate predictive covariance (conservative "
                    "statFEM Eq-38 screen). Stage-2 TMCMC (theta free) lets the mean move = rigorous re-rank."),
           "n_matched_modes": n, "theta_map": theta_map, "sig_w2_l5": sig_w2_l5,
           "damping_frequency_blindness": damp_note,
           "by_sigma_prior": {}}

    # precompute J per variant (independent of sig_prior)
    Js = {}
    for cls, vv in variants.items():
        names, J, eta0 = build_J(pp, vv, theta_map, V, idx)
        Js[cls] = (names, J)

    rankings = {}
    for sp in SIG_PRIOR_GRID:
        rec = {}
        # as-received deterministic reference: theta fixed, no param uncertainty
        rec["M0_fixed_thetaMAP"] = class_logZ(Y, mu0, None, sp)
        for cls, (names, J) in Js.items():
            rec[cls] = class_logZ(Y, mu0, J, sp)
            rec[cls]["n_params"] = J.shape[1]
        rec["M4_corr_discrepancy"] = m4_logZ(Y, mu0, fhz, sp)
        # type-II-ML'd hyperparameter count per class (marginalized stiffness params are NOT optimized -> they
        # are already Occam-penalized inside the marginal likelihood; only type-II-ML'd hyperparams need a BIC
        # correction): M0_fixed/M0_base9/M1_* optimize only sigma_w2 (k=1); M4 optimizes sigma_w2,ell_f,rmix (k=3).
        n_hyp = {"M0_fixed_thetaMAP": 1, "M0_base9": 1, "M1_box_split": 1, "M1_joint_split": 1,
                 "M1_full_rich": 1, "M4_corr_discrepancy": 3}
        bic_pen = {k: 0.5 * n_hyp[k] * np.log(n) for k in n_hyp}
        for k in n_hyp:
            rec[k]["n_typeII_hyperparams"] = n_hyp[k]
            rec[k]["bic_adjusted_logZ"] = float(rec[k]["logZ"] - bic_pen[k])
        # Bayes factors + posterior model probs over the comparable classes (incl. as-received M0_fixed)
        comp = ["M0_fixed_thetaMAP", "M0_base9", "M1_box_split", "M1_joint_split", "M1_full_rich",
                "M4_corr_discrepancy"]
        lzb = {k: rec[k]["bic_adjusted_logZ"] for k in comp}
        base = rec["M0_base9"]["bic_adjusted_logZ"]
        bf = {k: float(lzb[k] - base) for k in comp}            # log Bayes factor vs M0(base9), BIC-adjusted
        m = max(lzb.values()); w = {k: np.exp(lzb[k] - m) for k in comp}; Z = sum(w.values())
        pmp = {k: float(w[k] / Z) for k in comp}
        order = sorted(comp, key=lambda k: -lzb[k])
        order_raw = sorted(comp, key=lambda k: -rec[k]["logZ"])
        rec["_log_bayes_factor_vs_M0base9_bicadj"] = bf
        rec["_posterior_model_prob_bicadj"] = pmp
        rec["_ranking_best_to_worst_bicadj"] = order
        rec["_ranking_best_to_worst_raw"] = order_raw
        out["by_sigma_prior"][f"{sp:.2f}"] = rec
        rankings[f"{sp:.2f}"] = order

    # headline = sig_prior 0.25 (BIC-adjusted ranking = the honest decision ranking)
    h = out["by_sigma_prior"]["0.25"]
    out["headline_sigma_prior"] = "0.25"
    out["headline_ranking_bicadj"] = rankings["0.25"]
    out["headline_ranking_raw"] = h["_ranking_best_to_worst_raw"]
    # top-level summary (checker schema): BIC-adjusted log-evidence + Bayes factors at the headline prior width
    out["log_evidence"] = {k: h[k].get("bic_adjusted_logZ", h[k]["logZ"]) for k in
                           ["M0_fixed_thetaMAP", "M0_base9", "M1_box_split", "M1_joint_split",
                            "M1_full_rich", "M4_corr_discrepancy"]}
    out["bayes_factors"] = h["_log_bayes_factor_vs_M0base9_bicadj"]
    out["posterior_model_prob"] = h["_posterior_model_prob_bicadj"]
    out["runtime_s"] = time.time() - t0
    (OUT / "stage1_evidence.json").write_text(json.dumps(out, indent=2))

    # evidence-sensitivity gate (P6): does the ranking flip across prior widths?
    ranks = list(rankings.values())
    flips = any(r != ranks[0] for r in ranks[1:])
    top_flips = len({r[0] for r in ranks}) > 1
    sens = {"prior_widths": SIG_PRIOR_GRID, "ranking_per_width": rankings,
            "ranking_flips": bool(flips), "top_model_flips": bool(top_flips),
            "headline_winner": ranks[1][0],
            "note": ("ranking_flips = full order changes with prior width (Kiran §5 prior-sensitivity); "
                     "top_model_flips = the BEST class changes (the decision-relevant flip).")}
    (OUT / "evidence_sensitivity.json").write_text(json.dumps(sens, indent=2))

    h = out["by_sigma_prior"]["0.25"]
    print(f"\nSTAGE-1 evidence (headline sig_prior=0.25), BIC-adjusted best->worst:")
    for k in rankings["0.25"]:
        r = h[k]
        print(f"  {k:24s} logZ_raw={r['logZ']:.2f}  logZ_bicadj={r['bic_adjusted_logZ']:.2f}  "
              f"BF_vs_M0base9={h['_log_bayes_factor_vs_M0base9_bicadj'][k]:+.2f}  "
              f"P(M|Y)={h['_posterior_model_prob_bicadj'][k]:.3f}")
    print(f"  (raw-logZ ranking: {h['_ranking_best_to_worst_raw']})")
    print(f"ranking_flips={flips} top_model_flips={top_flips} | {out['runtime_s']:.1f}s")
    print(f"damping freq-shift {df_damp:.1e} vs floor {sig_w2_l5:.3f} -> M2/M3 frequency-blind (D3)")


if __name__ == "__main__":
    main()
