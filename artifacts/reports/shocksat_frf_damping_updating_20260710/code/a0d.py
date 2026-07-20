#!/usr/bin/env python3
"""A0d — damping-updated baseline (card §4.2). Inherited FEM (A0 package, theta=theta_MAP), damping fit on
TRAIN amplitude match (median |FRSF-1|) within the physical gate zeta in [0.2%,5%], eta<=0.2. Deterministic
multi-start. Fits four low-dim physical families and keeps the best by the TRAIN objective; then dev-scores.
This isolates 'what does damping alone buy the baseline' and is the reference the agent must EXCEED to claim
shape value. NO per-mode/per-channel damping (LOW-DIM-PHYSICAL only)."""
import json, os, sys, time
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femdamp as D
import femlib as F
import score as SC

WS = D.WS
Z_LO, Z_HI, ETA_HI = D.ZETA_LO, D.ZETA_HI, D.ETA_HI


def _amp_obj(damping, theta):
    p = SC.train_proxy("A0", damping=damping, theta_override=theta)
    return p["proxy_P2p"] if p["proxy_P2p"] is not None else 1e6


def fit_global(theta):
    def obj(lz): return _amp_obj({"kind": "band", "zeta": [float(np.exp(lz[0]))] * 4}, theta)
    best = None
    for z0 in np.log([0.003, 0.01, 0.03]):
        r = minimize(obj, [z0], method="Nelder-Mead",
                     options=dict(xatol=1e-3, fatol=1e-4, maxiter=60))
        if best is None or r.fun < best.fun:
            best = r
    z = float(np.clip(np.exp(best.x[0]), Z_LO, Z_HI))
    return {"kind": "band", "zeta": [z] * 4}, float(best.fun)


def fit_band(theta, z0):
    def obj(lz):
        zb = np.clip(np.exp(lz), Z_LO, Z_HI)
        return _amp_obj({"kind": "band", "zeta": zb.tolist()}, theta)
    r = minimize(obj, np.log([z0] * 4), method="Nelder-Mead",
                 options=dict(xatol=1e-3, fatol=1e-4, maxiter=200))
    zb = np.clip(np.exp(r.x), Z_LO, Z_HI)
    return {"kind": "band", "zeta": zb.tolist()}, float(r.fun)


def fit_rayleigh(theta):
    def obj(p):
        a, b = np.exp(p)
        return _amp_obj({"kind": "rayleigh", "alpha": float(a), "beta": float(b)}, theta)
    best = None
    for a0, b0 in [(0.5, 2e-6), (2.0, 5e-7), (0.1, 5e-6)]:
        r = minimize(obj, np.log([a0, b0]), method="Nelder-Mead",
                     options=dict(xatol=1e-2, fatol=1e-4, maxiter=120))
        if best is None or r.fun < best.fun:
            best = r
    a, b = np.exp(best.x)
    return {"kind": "rayleigh", "alpha": float(a), "beta": float(b)}, float(best.fun)


def fit_joint_eta(theta):
    """Structural loss factor on joints+contact (viscous fixed at survey median 0.32%)."""
    def obj(le):
        eta = {g: float(np.clip(np.exp(le[i]), 1e-4, ETA_HI)) for i, g in enumerate(D.JOINT_GROUPS)}
        return _amp_obj({"kind": "band", "zeta": [0.0032] * 4, "eta": eta}, theta)
    r = minimize(obj, np.log([0.02, 0.02]), method="Nelder-Mead",
                 options=dict(xatol=1e-2, fatol=1e-4, maxiter=120))
    eta = {g: float(np.clip(np.exp(r.x[i]), 1e-4, ETA_HI)) for i, g in enumerate(D.JOINT_GROUPS)}
    return {"kind": "band", "zeta": [0.0032] * 4, "eta": eta}, float(r.fun)


def main():
    t0 = time.time()
    pkg = F.Package.load("A0")
    theta = np.asarray(pkg.theta_map()[0], float)
    fits = {}
    print("fitting global zeta...", flush=True)
    dg, og = fit_global(theta); fits["global"] = (dg, og)
    print("  global:", dg, "obj", round(og, 4), flush=True)
    z0 = dg["zeta"][0]
    print("fitting 4-band zeta...", flush=True)
    db, ob = fit_band(theta, z0); fits["band4"] = (db, ob)
    print("  band4:", np.round(db["zeta"], 4).tolist(), "obj", round(ob, 4), flush=True)
    print("fitting rayleigh...", flush=True)
    dr, orr = fit_rayleigh(theta); fits["rayleigh"] = (dr, orr)
    print("  rayleigh:", {k: round(dr[k], 3 if k == 'alpha' else 8) for k in ('alpha', 'beta')},
          "obj", round(orr, 4), flush=True)
    print("fitting joint eta...", flush=True)
    de, oe = fit_joint_eta(theta); fits["joint_eta"] = (de, oe)
    print("  joint_eta:", {k: round(v, 4) for k, v in de["eta"].items()}, "obj", round(oe, 4), flush=True)
    best_family = min(fits, key=lambda k: fits[k][1])
    best_damping = fits[best_family][0]
    print(f"\nbest A0d family by TRAIN amplitude match: {best_family}", flush=True)
    # dev-score every fitted family (off-budget baseline) + record which is A0d
    recs = {}
    for fam, (dmp, obj) in fits.items():
        rec = SC.score_candidate("A0", "baseline", damping=dmp, theta_override=theta,
                                 family=f"A0d_{fam}", ablation="damping_only",
                                 rationale=f"A0 + fitted {fam} damping (train amplitude match {obj:.4f})",
                                 enforce_budget=False)
        recs[fam] = {"damping": dmp, "train_obj": obj, "P1p_mean": rec["P1p_mean"],
                     "P3_mean": rec["P3_mean"], "P2p_mean": rec["P2p_mean"],
                     "alignment_gain": rec["alignment_gain"], "P1p_folds": rec["P1p_folds"],
                     "damping_dim": rec["damping_dim"]}
    out = {"best_family": best_family, "best_damping": best_damping, "A0d": recs[best_family],
           "all_families": recs, "theta_map": theta.tolist(), "free_names": list(pkg.free_names),
           "runtime_s": round(time.time() - t0, 1)}
    json.dump(out, open(os.path.join(WS, "out", "a0d.json"), "w"), indent=2)
    print("\n=== A0d (best family) ===", flush=True)
    print(json.dumps(recs[best_family], indent=1), flush=True)
    print(f"\na0d done in {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
