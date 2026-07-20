#!/usr/bin/env python3
"""finalists — per-fold amplitude-trained theta_MAP refits for the top-2 candidates per track
(card §3; REINFORCEMENT test — the HQ verdicts come from the main fold-independent table).

The C6 lesson encoded: NO cross-fold reuse of ANY fitted object. Per finalist x fold:
  1. fit theta' on the candidate's ENRICHED basis using ONLY the 3 train drives' log10|H1|
     (windowed forward + measured survey zeta; ONE global gain per drive, profiled; lognormal prior
     sigma=0.25 on theta_total = theta_MAP_survey * theta'; sigma_e = 0.5 dex, fixed, declared);
     deterministic multi-start L-BFGS (5 starts, seed 20260716).
  2. EXACT enrichment of the spec at theta_total (own-space solve) — a per-fold exact basis.
  3. score ONLY the excluded drive.
Fold provenance (train_keys) recorded per refit; checker G05 verifies. Resumable per (cid, fold).
"""
from __future__ import annotations
import json
import os
import sys
import time

import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                  # noqa: E402
import pipeline as PL                                # noqa: E402
import collect as CL                                 # noqa: E402

SW, WFW, WP = C.SW, C.WFW, C.WP
SIG_E = 0.5                                          # dex, fixed output-error scale (declared)
SIG_TH = 0.25                                        # lognormal prior sd on theta_total
N_STARTS = 5
FDIR = os.path.join(C.MY_OUT, "finalist_partials")
os.makedirs(FDIR, exist_ok=True)


def fit_fold_theta(pkg, train_keys, theta_map_survey):
    """theta' MAP on the enriched basis from train drives only. Returns (theta_total, nlp, n_starts)."""
    caches = SW.load_caches()
    data = []
    for tk in train_keys:
        c = caches[tk]
        band = c["band"]
        rows, cols = SW._usable(pkg, c, band)
        ym = np.log10(np.abs(c["H1"][cols][:, band]) + 1e-300)
        data.append((tk, rows, c["freqs"][band], ym))
    lg_map = np.log(np.asarray(theta_map_survey, float))

    def nlp(lt):
        tot = 0.0
        th = np.exp(lt)
        for tk, rows, fc, ym in data:
            H = WFW.predict_H(pkg, th, tk, fc, windowed=True)
            lp = np.log10(np.abs(H[rows]) + 1e-300)
            g = float(np.mean(ym - lp))               # ONE global gain per drive, profiled
            r = ym - lp - g
            tot += 0.5 * float(np.sum(r ** 2)) / SIG_E ** 2
        tot += 0.5 * float(np.sum((lt + lg_map) ** 2)) / SIG_TH ** 2   # prior on theta_total
        return tot

    rng = np.random.default_rng(20260716)
    starts = [np.zeros(len(pkg.free_names))] + \
             [rng.normal(0, 0.1, len(pkg.free_names)) for _ in range(N_STARTS - 1)]
    best = None
    for x0 in starts:
        res = minimize(nlp, x0, method="L-BFGS-B", options=dict(maxiter=100))
        if best is None or res.fun < best.fun:
            best = res
    theta_prime = np.exp(best.x)
    theta_total = np.asarray(theta_map_survey, float) * theta_prime
    return theta_total, float(best.fun)


def score_single_fold(pkg, fold):
    """Exact score of ONE held-out drive at theta=ones (train-side warp from the other 3)."""
    caches = SW.load_caches()
    one = np.ones(len(pkg.free_names))
    tks = [k for k in C.DEV_KEYS if k != fold]
    rho, bm = SW._train_warp(pkg, one, tks, caches, True, None, None)
    fmask = None
    if bm:
        fm = np.zeros(len(caches[fold]["freqs"]), bool)
        for tk, mmask in bm.items():
            if mmask.shape[0] == fm.shape[0]:
                fm |= mmask
        fmask = fm if fm.sum() >= SW.MIN_BAND else None
    graded = SW._grade_bands(pkg, one, fold, caches[fold], rho, fmask, True, None, None, None)
    return graded["sub200"].get("P1p"), graded["b200_500"].get("P1p")


def do_finalist(rec):
    cid = rec["cid"]
    spec = json.load(open(os.path.join(C.MY_SPECD, f"{cid}.json")))
    spec["cls"] = rec["cls"]
    per_fold = []
    for fold in C.DEV_KEYS:
        pp = os.path.join(FDIR, f"{cid}__{fold}.json")
        if os.path.exists(pp):
            per_fold.append(json.load(open(pp)))
            continue
        t0 = time.time()
        train_keys = [k for k in C.DEV_KEYS if k != fold]
        epkg = WP.load(rec["enriched_pkg"])
        th_total, nlp = fit_fold_theta(epkg, train_keys, rec["theta_map"])
        fpkg = PL.enrich_mf(spec, th_total, json.load(
            open(os.path.join(C.MY_OUT, "theta_maps.json")))[cid]["free_names"],
            f"{cid}__f_{fold}")
        s200, s25 = score_single_fold(fpkg, fold)
        C.assert_finite({"s200": s200}, f"{cid}.{fold}")
        fr = {"fold": fold, "train_keys": train_keys,
              "theta_refit": [float(t) for t in th_total], "nlp": nlp,
              "exact_sub200_fold": s200, "exact_b200_500_fold": s25,
              "spot_max_pct": float(fpkg.meta.get("spot_max_pct")),
              "wall_s": round(time.time() - t0, 1), "ts": C.now()}
        json.dump(fr, open(pp, "w"), indent=1)
        print(f"  [{cid}/{fold}] refit sub200 {s200:+.4f} ({fr['wall_s']:.0f}s)", flush=True)
        per_fold.append(fr)
        C.flush_vault_guard(f"finalist_{cid}_{fold}")
    return per_fold


def main():
    t0 = time.time()
    rows = CL.load_partials()
    fin = []
    for tr in ("agent", "random"):
        top2 = sorted([r for r in rows if r["track"] == tr],
                      key=lambda r: -r["exact_sub200"])[:2]
        for rec in top2:
            print(f"finalist {tr}: {rec['cid']} (main exact {rec['exact_sub200']:+.4f})",
                  flush=True)
            pf = do_finalist(rec)
            refit_scores = {x["fold"]: x["exact_sub200_fold"] for x in pf}
            dv = [refit_scores[f] - C.A1_FOLDS[f] for f in C.DEV_KEYS]
            m, se, pfd = C.paired_stats(dv)
            thetas = [tuple(round(t, 12) for t in x["theta_refit"]) for x in pf]
            frec = {"cid": rec["cid"], "track": tr, "cls": rec["cls"],
                    "main_exact_sub200": rec["exact_sub200"],
                    "refit_exact_sub200_mean": float(np.mean(list(refit_scores.values()))),
                    "per_fold": pf,
                    "refit_vs_A1": {"delta_mean": m, "delta_se": se, "per_fold": pfd}}
            if len(set(thetas)) == 1:
                frec["degenerate_reason"] = ("per-fold refits converged to identical theta "
                                             "(train-drive information insufficient to move the "
                                             "prior+survey MAP)")
            fin.append(frec)
    # paired S-test: top-1 agent refit vs top-1 random refit
    stest = None
    a1 = next((f for f in fin if f["track"] == "agent"), None)
    r1 = next((f for f in fin if f["track"] == "random"), None)
    if a1 and r1:
        sa = {x["fold"]: x["exact_sub200_fold"] for x in a1["per_fold"]}
        sr = {x["fold"]: x["exact_sub200_fold"] for x in r1["per_fold"]}
        m, se, pfd = C.paired_stats([sa[f] - sr[f] for f in C.DEV_KEYS])
        stest = {"agent_cid": a1["cid"], "random_cid": r1["cid"],
                 "delta_mean": m, "delta_se": se, "per_fold": pfd,
                 "met_1se": bool(m >= se)}
    out = {"finalists": fin, "agent_vs_random_refit": stest,
           "method": "per-fold amplitude-trained theta MAP (train drives only, 5 deterministic "
                     "starts, sigma_e=0.5 dex, lognormal prior 0.25 on theta_total) -> per-fold "
                     "EXACT enrichment -> held-out drive scored. REINFORCEMENT test; HQ verdicts "
                     "come from the main fold-independent exact table.",
           "generated": C.now()}
    json.dump(out, open(os.path.join(C.MY_OUT, "finalists.json"), "w"), indent=1)
    C.log_step("finalists", time.time() - t0, n=len(fin))
    print(json.dumps(stest, indent=1) if stest else "no s-test")


if __name__ == "__main__":
    main()
