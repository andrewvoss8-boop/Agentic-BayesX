#!/usr/bin/env python3
"""collect_results — arms×bands table (EXACT-basis trusted numbers; θ=1 dev = screening, D22) + S1-S5/H1-H5
verdicts. Reads exact_freeze_scores.json (primary), score_log (screening), netcg_results, arm_E, +
query_log. No new science."""
import json, os, sys
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
BANDS = ["sub200", "b200_500", "b500_ceiling"]
DEV = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]


def J(p):
    fp = os.path.join(WS, p)
    return json.load(open(fp)) if os.path.exists(fp) else None


def main():
    ex = J("out/exact_freeze_scores.json") or {}
    table = {"arms": {}, "basis": "EXACT (enriched at theta_MAP, D22); theta=1 dev scores are SCREENING",
             "note": "fold-averaged held-out per-channel log|H| corr (P1'). b500_ceiling not certified "
                     "(FEM basis credible ~640 Hz; scored <=500)."}
    for arm in ["A0", "A1", "B", "C", "D", "R", "F"]:
        if arm == "F":
            continue
        v = ex.get(arm)
        if not v:
            continue
        cell = {}
        for b in ("sub200", "b200_500"):
            val = v["exact"].get(b)
            fv = [(v["exact"]["folds"].get(k, {}) or {}).get("P1p") for k in DEV]
            fv = [x for x in fv if x is not None]
            cell[b] = {"mean": round(val, 4) if val is not None else None,
                       "se": round(float(np.std(fv, ddof=1) / np.sqrt(len(fv))), 4) if len(fv) > 1 else None,
                       "screening": round((v["screen"] or {}).get(b) or -9, 4) if v.get("screen") else None}
        cell["b500_ceiling"] = {"status": "not_certified",
                                "reason": "FEM basis credible ~640 Hz; scored freq cap 500 Hz (D11)"}
        table["arms"][arm] = cell
    # arm F = best-performing exact arm on sub-200 (delivery pick); tie -> A1
    best_arm = max([a for a in table["arms"]], key=lambda a: table["arms"][a]["sub200"]["mean"] or -9)
    table["arms"]["F"] = dict(table["arms"][best_arm]); table["arms"]["F"]["equals"] = best_arm
    json.dump(table, open(os.path.join(WS, "out", "arms_bands_table.json"), "w"), indent=1)

    def exfold(arm, band):
        return {k: (ex[arm]["exact"]["folds"].get(k, {}) or {}).get(band and "P1p")
                for k in DEV} if False else \
               {k: (ex[arm]["exact"]["folds"].get(k, {}) or {}).get("P1p") for k in DEV}

    def paired(a, b):
        fa, fb = exfold(a, "sub200"), exfold(b, "sub200")
        d = [fa[k] - fb[k] for k in DEV if fa.get(k) is not None and fb.get(k) is not None]
        return (float(np.mean(d)), float(np.std(d, ddof=1) / np.sqrt(len(d))), [round(x, 3) for x in d])

    v = {}
    # S1: best arm (B/C/D) vs A1, exact
    cands = {a: paired(a, "A1") for a in ("B", "C", "D") if a in ex}
    best = max(cands, key=lambda a: cands[a][0])
    dm, se, pf = cands[best]
    s1_pass = dm >= 0.05 and dm >= 2 * se
    v["S1"] = {"status": "GREEN" if s1_pass else "YELLOW", "claim": "some arm beats A1 sub-200 by >=+0.05 AND >=2xSE",
               "numbers": {"best_arm": best, "delta_mean": round(dm, 4), "delta_se": round(se, 4),
                           "2xSE": round(2 * se, 4), "per_fold": pf, "basis": "exact",
                           "screening_best_arm_C_delta": 0.044, "note": "screening leader C collapsed on "
                           "exact basis (0.189->0.157); no arm cleanly clears +0.05 AND 2xSE"}}
    # S2: agent D vs random R, exact
    dm2, se2, pf2 = paired("D", "R")
    s2_pass = dm2 >= se2
    v["S2"] = {"status": "GREEN" if s2_pass else "YELLOW", "claim": "agent beats equal-budget random by >=1xSE (sub-200)",
               "numbers": {"delta_mean": round(dm2, 4), "delta_se": round(se2, 4), "per_fold": pf2,
                           "basis": "exact", "screening_delta": 0.0138,
                           "note": "screening showed +0.0138 (agent ahead); the EXACT-basis re-eval OVERTURNS "
                           "it (agent ties/loses random) -> H2 impotence confirmed, screening lead was "
                           "reduced-basis inflation (D22)"}}
    ncg = J("out/netcg_results.json")
    if ncg:
        sx, sy, nz = ncg["shear_x"], ncg["shear_y"], ncg["normal_z"]
        v["S3"] = {"status": "GREEN" if ((sx["width_ratio"] < 1.51 or sy["width_ratio"] < 2.30)
                                         and min(sx["coverage"], sy["coverage"]) >= 0.95) else "YELLOW",
                   "claim": "narrows net-CG shear while keeping >=0.95 coverage",
                   "numbers": {"shear_x": sx, "shear_y": sy, "delivered": {"x": 1.51, "y": 2.30}}}
        v["S4"] = {"status": "GREEN" if (nz["width_ratio"] <= 1.90 and nz["coverage"] >= 0.95) else "YELLOW",
                   "claim": "normal band narrows >=25% (2.53->1.90) while covering",
                   "numbers": {"normal_z": nz, "delivered": 2.53}}
    e = J("out/arm_E.json")
    if e and e.get("spearman") is not None:
        v["S5"] = {"status": "GREEN" if e["spearman"] >= 0.5 else "YELLOW",
                   "claim": "amplitude-inclusive selection Spearman >= 0.5 vs held-out",
                   "numbers": {"spearman": e["spearman"], "by_prior": {k: e.get(k) for k in e if "spearman_sig" in k}}}
    H = {"H1": ("S1", "shape wall: amplitude-trained shape (C) dented sub-200 on screening (+0.044) but "
                "collapsed on exact basis; no lever cleanly clears the noise floor -> wall stands, dented"),
         "H2": ("S2", "remodeling impotence CONFIRMED with the amplitude compass: agent ties random on the "
                "trusted exact basis (screening lead was D22 inflation)"),
         "H3": ("S1", "window-matched + measured zeta is the standard convention for all arms; on exact bases "
                "the window's sub-200 benefit over A0 shrank to ~noise (0.114 vs 0.112)"),
         "H4": ("S4", "extended-band cluster (254-367 Hz) measured; normal-band tier update -> see S4/netcg"),
         "H5": ("S5", "amplitude-inclusive selection vs held-out ranking -> see S5")}
    for h, (src, summ) in H.items():
        s = v.get(src)
        v[h] = {"status": s["status"] if s else "RED", "summary": summ, "anchor": src}
    json.dump(v, open(os.path.join(WS, "out", "verdicts.json"), "w"), indent=1)
    # QOI-weighted (from screening folds; per-sensor qoiw)
    qw = {}
    for line in open(os.path.join(WS, "out", "score_log.jsonl")):
        r = json.loads(line)
        if r.get("stage") == "dev" and "bands_agg" in r:
            vals = [(r["folds"][k]["bands"]["sub200"] or {}).get("P1p_qoiw") for k in DEV
                    if r["folds"].get(k, {}).get("bands", {}).get("sub200", {}).get("P1p_qoiw") is not None]
            if vals:
                qw[r["arm"]] = round(float(np.mean(vals)), 4)
    json.dump({"sub200_P1p_qoiw_mean_by_arm": qw, "basis": "screening (theta=1)"},
              open(os.path.join(WS, "out", "qoi_weighted_scores.json"), "w"), indent=1)
    print(json.dumps({k: v[k]["status"] for k in ["S1", "S2", "S3", "S4", "S5"] if k in v}, indent=1))
    print("table arms:", list(table["arms"]))


if __name__ == "__main__":
    main()
