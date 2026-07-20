#!/usr/bin/env python3
"""collect — partials -> query_log.jsonl, complexity.json, results_table.json, verdicts.json,
vault_guard.json. Finiteness-hardened (assert_finite before every write; the D17/C8 lesson).
Decision rules recomputed EXACTLY as pre-registered (question_framing §4); the locked checker G12
re-verifies them independently. Falsification is a valid outcome — this script records, never tunes.
"""
from __future__ import annotations
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                  # noqa: E402

GENUINE = ["connectivity", "mesh_density", "element_formulation", "geometry"]


def load_partials():
    rows = []
    for fn in sorted(os.listdir(C.PARTD)):
        if not fn.endswith(".json") or fn.endswith(".build.json"):
            continue
        r = json.load(open(os.path.join(C.PARTD, fn)))
        if r.get("dud"):
            continue
        if r.get("track") not in ("agent", "random"):
            continue
        rows.append(r)
    return sorted(rows, key=lambda r: r.get("ts", ""))


def write_query_log(rows):
    p = os.path.join(C.MY_OUT, "query_log.jsonl")
    with open(p, "w") as f:
        for r in rows:
            C.assert_finite({k: r[k] for k in ("exact_sub200", "exact_b200_500")}, r["cid"])
            C.assert_finite(r["exact_folds"], f"{r['cid']}.folds")
            f.write(json.dumps(r) + "\n")
    return p


def write_complexity(rows):
    ref = json.load(open(os.path.join(C.MY_OUT, "complexity_ref.json")))
    comp = {}
    for r in rows:
        deltas = [r["exact_folds"][f] - C.A1_FOLDS[f] for f in C.DEV_KEYS]
        m, se, _ = C.paired_stats(deltas)
        nwi = bool(m < se and r["delta_dof_pct"] > 10.0)
        comp[r["cid"]] = {"n_dof": r["n_dof"], "delta_dof_pct": r["delta_dof_pct"],
                          "n_params": r["n_params"], "delta_n_params": r["n_params"] - 9,
                          "solve_s": r["solve_s_theta1"],
                          "solve_ratio": round(r["solve_s_theta1"] / ref["solve_s_ref"], 3),
                          "exact_sub200": r["exact_sub200"],
                          "gain_vs_A1_mean": m, "gain_vs_A1_se": se,
                          "not_worth_it": nwi,
                          "rule": "not_worth_it iff gain < 1xSE AND dDOF > +10% (pre-registered)"}
    C.assert_finite(comp, "complexity")
    json.dump(comp, open(os.path.join(C.MY_OUT, "complexity.json"), "w"), indent=1)
    return comp


def write_results_table(rows):
    tab = {"A1_reference": {"exact_sub200": float(np.mean(list(C.A1_FOLDS.values()))),
                            "folds": C.A1_FOLDS,
                            "source": "study exact_freeze_scores.json (pinned, read-only)"},
           "cells": {}, "tracks": {}}
    for cls in C.CLASSES:
        for tr in ("agent", "random"):
            sel = [r for r in rows if r["cls"] == cls and r["track"] == tr]
            if not sel:
                continue
            best = max(sel, key=lambda r: r["exact_sub200"])
            scores = [r["exact_sub200"] for r in sel]
            cell = {"n": len(sel),
                    "mean_exact_sub200": float(np.mean(scores)),
                    "sd_over_candidates": float(np.std(scores, ddof=1)) if len(scores) > 1 else 0.0,
                    "best_cid": best["cid"], "best_exact_sub200": best["exact_sub200"],
                    "best_folds": best["exact_folds"],
                    "mean_b200_500": float(np.mean([r["exact_b200_500"] for r in sel])),
                    "mean_delta_dof_pct": float(np.mean([r["delta_dof_pct"] for r in sel]))}
            db = [best["exact_folds"][f] - C.A1_FOLDS[f] for f in C.DEV_KEYS]
            m, se, pf = C.paired_stats(db)
            cell["best_vs_A1"] = {"delta_mean": m, "delta_se": se, "per_fold": pf}
            tab["cells"][f"{cls}|{tr}"] = cell
    for tr in ("agent", "random"):
        sel = [r for r in rows if r["track"] == tr]
        if sel:
            best = max(sel, key=lambda r: r["exact_sub200"])
            tab["tracks"][tr] = {"n": len(sel),
                                 "mean_exact_sub200": float(np.mean([r["exact_sub200"]
                                                                     for r in sel])),
                                 "best_cid": best["cid"],
                                 "best_exact_sub200": best["exact_sub200"]}
    C.assert_finite(tab, "results_table")
    json.dump(tab, open(os.path.join(C.MY_OUT, "results_table.json"), "w"), indent=1)
    return tab


def write_verdicts(rows):
    tracks = {t: [r for r in rows if r["track"] == t] for t in ("agent", "random")}
    best = {t: max(v, key=lambda r: r["exact_sub200"]) for t, v in tracks.items() if v}
    d1 = [best["agent"]["exact_folds"][f] - best["random"]["exact_folds"][f] for f in C.DEV_KEYS]
    m1, se1, pf1 = C.paired_stats(d1)
    dm = [(float(np.mean([r["exact_folds"][f] for r in tracks["agent"]]))
           - float(np.mean([r["exact_folds"][f] for r in tracks["random"]])))
          for f in C.DEV_KEYS]
    m2, se2, pf2 = C.paired_stats(dm)
    hq1 = {"statement": "agent beats seeded random on held-out sub-200 P1', exact bases, "
                        ">= 1x paired-fold SE",
           "primary": {"convention": "best-exact vs best-exact (winner's-curse-honest; both sides "
                                     "max over 30 noisy candidates — a sub-SE gap is a win for "
                                     "neither)",
                       "agent_cid": best["agent"]["cid"], "random_cid": best["random"]["cid"],
                       "agent_exact_sub200": best["agent"]["exact_sub200"],
                       "random_exact_sub200": best["random"]["exact_sub200"],
                       "delta_mean": m1, "delta_se": se1, "per_fold": pf1,
                       "met": bool(m1 >= se1)},
           "secondary": {"convention": "track mean over all candidates (distribution-level)",
                         "delta_mean": m2, "delta_se": se2, "per_fold": pf2,
                         "met_1se": bool(m2 >= se2)}}
    per_class = {}
    any_met = False
    for cls in C.CLASSES:
        sel = [r for r in rows if r["cls"] == cls]
        if not sel:
            continue
        b = max(sel, key=lambda r: r["exact_sub200"])
        db = [b["exact_folds"][f] - C.A1_FOLDS[f] for f in C.DEV_KEYS]
        mb, seb, pfb = C.paired_stats(db)
        mean_folds = {f: float(np.mean([r["exact_folds"][f] for r in sel])) for f in C.DEV_KEYS}
        dmn = [mean_folds[f] - C.A1_FOLDS[f] for f in C.DEV_KEYS]
        mm_, sem, pfm = C.paired_stats(dmn)
        met = bool(mb >= seb) and cls in GENUINE
        per_class[cls] = {"n_pooled": len(sel), "genuine": cls in GENUINE,
                          "best": {"cid": b["cid"], "track": b["track"],
                                   "exact_sub200": b["exact_sub200"],
                                   "delta_mean": mb, "delta_se": seb, "per_fold": pfb,
                                   "met": met},
                          "class_mean_vs_A1": {"delta_mean": mm_, "delta_se": sem,
                                               "per_fold": pfm},
                          "note": ("CONTROL class — cannot satisfy HQ2 by definition"
                                   if cls not in GENUINE else
                                   "best-of-12 carries selection noise; class mean is the control")}
        if met:
            any_met = True
    hq2 = {"statement": "at least one GENUINE model-form class beats A1 on exact-basis held-out "
                        "sub-200 by >= 1x paired-fold SE",
           "per_class": per_class, "met": any_met}
    # stop-condition report: per-fold sign stability of the HQ1 primary delta
    signs = [1 if x > 0 else (-1 if x < 0 else 0) for x in pf1]
    v = {"card": "shocksat_modelform_pilot_20260716",
         "HQ1": hq1, "HQ2": hq2,
         "fold_stability": {"hq1_primary_per_fold_signs": signs,
                            "consistent": bool(len(set(s for s in signs if s != 0)) <= 1)},
         "sampler": "NONE (deterministic multi-start MAPs + exact eigensolves; pre-registered)",
         "vault": "not read",
         "generated": C.now()}
    C.assert_finite({"hq1": [m1, se1, m2, se2]}, "verdicts.hq1")
    json.dump(v, open(os.path.join(C.MY_OUT, "verdicts.json"), "w"), indent=1)
    return v


def write_vault_guard():
    total_wide = 0
    meta = 0
    vp = os.path.join(C.MY_LOGS, "vault_opens.jsonl")
    if os.path.exists(vp):
        for line in open(vp):
            if line.strip():
                r = json.loads(line)
                total_wide += r.get("xy_wide_opens", 0)
                meta += r.get("xy_narrow_meta_opens", 0)
    hits = []
    for fn in ("query_log.jsonl", "score_log.jsonl", "finalists.json"):
        p = os.path.join(C.MY_OUT, fn)
        if os.path.exists(p) and "m_xy_990xy" in open(p).read():
            hits.append(fn)
    g = {"xy_files_opened": total_wide,
         "xy_narrow_meta_opens": meta,
         "narrow_meta_note": "femlib.cache_meta() metadata-only reads (daq/xyz/axis; H1 never "
                             "accessed) — the established validated-package convention; the +XY FRF "
                             "DATA (wide cache) was opened 0 times",
         "log_hits": hits, "checked_paths": ["logs/vault_opens.jsonl (runtime np.load guard)",
                                             "out/query_log.jsonl", "out/score_log.jsonl",
                                             "out/finalists.json"],
         "generated": C.now()}
    json.dump(g, open(os.path.join(C.MY_OUT, "vault_guard.json"), "w"), indent=1)
    if total_wide != 0 or hits:
        raise RuntimeError(f"VAULT GUARD TRIPPED: {g}")
    return g


def main():
    t0 = time.time()
    rows = load_partials()
    print(f"{len(rows)} scored candidates "
          f"({sum(1 for r in rows if r['track'] == 'agent')} agent / "
          f"{sum(1 for r in rows if r['track'] == 'random')} random)")
    write_query_log(rows)
    write_complexity(rows)
    write_results_table(rows)
    v = write_verdicts(rows)
    write_vault_guard()
    C.log_step("collect", time.time() - t0, n=len(rows))
    h1 = v["HQ1"]["primary"]
    print(f"HQ1 primary: {h1['delta_mean']:+.4f} +/- {h1['delta_se']:.4f} -> "
          f"{'MET' if h1['met'] else 'NOT MET'}")
    for cls, cc in v["HQ2"]["per_class"].items():
        b = cc["best"]
        print(f"HQ2 {cls:20s}: best {b['delta_mean']:+.4f} +/- {b['delta_se']:.4f} "
              f"[{'MET' if b['met'] else 'not met'}] ({b['cid']})")
    print(f"HQ2 overall: {'MET' if v['HQ2']['met'] else 'NOT MET'}")


if __name__ == "__main__":
    main()
