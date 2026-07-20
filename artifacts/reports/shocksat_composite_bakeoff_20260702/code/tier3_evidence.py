#!/usr/bin/env python3
"""Tier-3 EVIDENCE (card §3): Bayesian model-class evidence on the SHAPE-INCLUSIVE observable (freq + MAC)
for the tier-2 survivors. Frequency-only evidence is FORBIDDEN as the selector (question_framing R4) — it is
computed ONLY as a labeled reference column to show what it would have (wrongly) crowned.

Per class (candidate): theta_MAP by L-BFGS on the freq+MAC log-posterior; analytic statFEM Eq-38 evidence at
theta_MAP (stage1_evidence pattern): Y=[omega_hat^2 ; MAC targets(=1)], Sigma = D I D + J Cprior J^T,
D = diag([sig_w2*Y_f ; sig_mac]), (sig_w2, sig_mac) type-II ML'd per class (k=2 BIC adj, equal across classes),
J = [Fox-Kapoor dlambda/dlntheta ; finite-diff dMAC/dlntheta]. Prior width swept {0.15,0.25,0.40}.
Output: out/tier3_evidence.json. Run AFTER tier2. Resumable at the JSON level (cheap enough to recompute).
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize, minimize_scalar

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rmodel as RMOD

WS = Path(__file__).resolve().parent.parent
SIG_PRIOR_GRID = [0.15, 0.25, 0.40]
N_TIER3 = 10
t0 = time.time()


def mac_of(model, theta):
    _, Q = model.modes(theta)
    gp = model.ash @ Q[:, model.femk]
    return np.sum(gp * model.phm, 0) ** 2 / (np.sum(gp * gp, 0) * np.sum(model.phm ** 2, 0) + 1e-30)


def theta_map(model, sw2=0.05, smac=0.3, prior=RMOD.NSIG_THETA):
    tgt = (model.mfreqs[model.ashr] * 2 * np.pi) ** 2

    def neg(lt):
        th = np.exp(lt)
        lam, Q = np.linalg.eigh(model.K(th))
        lam = np.clip(lam, 1e-9, None)
        rf = (tgt - lam[model.femk]) / (sw2 * tgt)
        gp = model.ash @ Q[:, model.femk]
        mac = np.sum(gp * model.phm, 0) ** 2 / (np.sum(gp * gp, 0) * np.sum(model.phm ** 2, 0) + 1e-30)
        rm = (1.0 - mac) / smac
        return 0.5 * (np.sum(rf ** 2) + np.sum(rm ** 2) + np.sum((lt / prior) ** 2))

    res = minimize(neg, np.zeros(model.np_), method="L-BFGS-B",
                   options={"maxiter": 300, "ftol": 1e-12})
    return np.exp(res.x), float(res.fun)


def jacobians(model, th):
    """J wrt ln(theta): freq rows (Fox-Kapoor, exact) + MAC rows (central finite diff)."""
    lam, Q = np.linalg.eigh(model.K(th))
    V = Q[:, model.femk]
    Jf = np.stack([th[p] * np.einsum("ir,ij,jr->r", V, model.A[p], V)
                   for p in range(model.np_)], 1)                        # (nm, np_)
    mac0 = mac_of(model, th)
    Jm = np.zeros((len(model.femk), model.np_))
    h = 0.02
    for p in range(model.np_):
        tp = th.copy(); tp[p] *= np.exp(h)
        tm = th.copy(); tm[p] *= np.exp(-h)
        Jm[:, p] = (mac_of(model, tp) - mac_of(model, tm)) / (2 * h)
    return Jf, Jm, lam, mac0


def class_logZ(model, th, Jf, Jm, lam, mac0, sig_prior):
    tgt = (model.mfreqs[model.ashr] * 2 * np.pi) ** 2
    rf = tgt - lam[model.femk]
    rm = 1.0 - mac0
    nf, nm_ = len(rf), len(rm)

    def neg(p):
        sw2, smac = np.exp(p)
        s = np.concatenate([sw2 * tgt, np.full(nm_, smac)])
        r = np.concatenate([rf, rm]) / s
        G = np.vstack([Jf, Jm]) / s[:, None]
        Mm = np.eye(nf + nm_) + sig_prior ** 2 * (G @ G.T)
        sign, ld = np.linalg.slogdet(Mm)
        if sign <= 0:
            return 1e18
        sol = np.linalg.solve(Mm, r)
        return 0.5 * (r @ sol + ld + 2 * np.sum(np.log(s)) + (nf + nm_) * np.log(2 * np.pi))

    best = None
    for x0 in ([np.log(0.05), np.log(0.3)], [np.log(0.02), np.log(0.15)], [np.log(0.1), np.log(0.5)]):
        r = minimize(neg, x0, method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-4})
        if best is None or r.fun < best.fun:
            best = r
    sw2, smac = np.exp(best.x)
    return {"logZ": float(-best.fun), "sigma_w2": float(sw2), "sigma_mac": float(smac),
            "n_params": int(model.np_)}


def freq_only_logZ(model, th, Jf, lam, sig_prior):
    """LABELED REFERENCE ONLY (forbidden as selector)."""
    tgt = (model.mfreqs[model.ashr] * 2 * np.pi) ** 2
    rf = tgt - lam[model.femk]

    def neg(lsw):
        sw2 = np.exp(lsw)
        s = sw2 * tgt
        r = rf / s
        G = Jf / s[:, None]
        Mm = np.eye(len(rf)) + sig_prior ** 2 * (G @ G.T)
        sign, ld = np.linalg.slogdet(Mm)
        if sign <= 0:
            return 1e18
        return 0.5 * (r @ np.linalg.solve(Mm, r) + ld + 2 * np.sum(np.log(s)) + len(rf) * np.log(2 * np.pi))

    r = minimize_scalar(neg, bounds=(np.log(1e-3), np.log(0.5)), method="bounded")
    return float(-r.fun)


def main():
    t2 = json.loads((WS / "out" / "tier2_full.json").read_text())["results"]
    ranked = sorted(((v["full_score"], k) for k, v in t2.items() if k != "baseline"), reverse=True)
    cids = ["baseline"] + [k for _, k in ranked[:N_TIER3]]
    out = {"observable": "shape-inclusive: matched .ash eigenvalues omega^2 + MAC (frozen Hungarian pairing)",
           "shape_inclusive": True, "n_classes": len(cids),
           "note": "each class at its own freq+MAC theta_MAP; type-II ML (sigma_w2, sigma_mac) k=2 all classes;"
                   " freq_only column = LABELED REFERENCE, forbidden as selector (R4).",
           "by_sigma_prior": {}, "freq_only_reference": {}}
    cache = {}
    for cid in cids:
        m = RMOD.CModel(cid)
        th, _ = theta_map(m)
        Jf, Jm, lam, mac0 = jacobians(m, th)
        cache[cid] = (m, th, Jf, Jm, lam, mac0)
        print(f"[{time.time()-t0:6.1f}s] {cid}: MAP done, nm={len(m.femk)}, np={m.np_}, "
              f"mac_mean {np.mean(mac0):.3f}", flush=True)
    for sp in SIG_PRIOR_GRID:
        rec = {}
        for cid in cids:
            m, th, Jf, Jm, lam, mac0 = cache[cid]
            rec[cid] = class_logZ(m, th, Jf, Jm, lam, mac0, sp)
        # BIC adj equal (k=2) -> ranking unchanged; report raw logZ + model probs
        mx = max(v["logZ"] for v in rec.values())
        w = {k: np.exp(v["logZ"] - mx) for k, v in rec.items()}
        Z = sum(w.values())
        for k in rec:
            rec[k]["post_prob"] = round(float(w[k] / Z), 4)
        rec["_ranking"] = sorted(rec, key=lambda k: -rec[k]["logZ"] if not k.startswith("_") else 1e9)
        out["by_sigma_prior"][f"{sp:.2f}"] = rec
    for cid in cids:
        m, th, Jf, Jm, lam, mac0 = cache[cid]
        out["freq_only_reference"][cid] = freq_only_logZ(m, th, Jf, lam, 0.25)
    ranks = [tuple(out["by_sigma_prior"][f"{sp:.2f}"]["_ranking"]) for sp in SIG_PRIOR_GRID]
    out["prior_robust_ranking"] = bool(all(r == ranks[0] for r in ranks))
    out["prior_robust_top"] = bool(len({r[0] for r in ranks}) == 1)
    h = out["by_sigma_prior"]["0.25"]
    out["headline"] = {"sigma_prior": 0.25, "ranking": h["_ranking"],
                       "winner": h["_ranking"][0],
                       "winner_beats_baseline": bool(h["_ranking"][0] != "baseline"),
                       "logZ_winner_minus_baseline": round(h[h["_ranking"][0]]["logZ"] - h["baseline"]["logZ"], 2)}
    fr = out["freq_only_reference"]
    out["freq_only_would_have_crowned"] = max(fr, key=fr.get)
    (WS / "out" / "tier3_evidence.json").write_text(json.dumps(out, indent=1))
    print("HEADLINE (0.25):", json.dumps(out["headline"]))
    print("prior-robust top:", out["prior_robust_top"], "| freq-only would crown:",
          out["freq_only_would_have_crowned"], "(reference only)")


if __name__ == "__main__":
    main()
