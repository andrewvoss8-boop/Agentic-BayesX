#!/usr/bin/env python3
"""exact_rerank — T2: exact-basis re-rank of ALL 28 remodel-loop candidates (card §2 T2).

WHY THIS EXISTS
The study's exact-basis S2 (agent D - random R = -0.0017 +/- 0.0094) re-scored only the TWO screening
winners out of 28 loop candidates (review C1). That is circular in a specific way: the whole point of study
D15 is that the theta=1 SCREENING basis inflates candidates living in/near the theta-parametrization span
(thickness/scale/split) -- but screening is exactly what CHOSE those two winners. If screening mis-ordered
the field, the "winner" of each track is the wrong candidate to re-score.

WHAT THIS DOES
For each of the 28 candidates in the study's out/query_log.jsonl (14 agent + 14 random):
  1. enrich at its own multi-start theta_MAP (out/theta_maps.json, reused verbatim -- NOT re-optimized, so
     this card cannot flatter any candidate by re-tuning it): solve K(theta_MAP) with a k=200 own-space
     sparse shift-invert eigensolve and fold theta_MAP into the projected blocks  -> scoring at theta=ones
     reproduces the full solve (study D14/D22);
  2. score exactly on the 4 dev folds, both bands, with the same warp + one-global-gain machinery as every
     other arm.
Then S2 is computed BOTH ways:
  (a) screening-selected winners, exact-scored  -- the study's convention (reproduction target -0.0017);
  (b) EXACT-selected winners (best exact per track) -- the winner's-curse-honest reading.
plus the per-track Spearman rank correlation between the screening and exact orderings (the mechanism: how
badly did the theta=1 basis re-order the field?) and the top-3 per track under each ranking.

Resumable per candidate (out/rerank_partial/<cid>.json). Every eigensolve is logged to
out/eigensolve_log.jsonl. A candidate whose enrichment fails is recorded EXCLUDED-WITH-REASON, never
substituted. NO SAMPLER: deterministic eigensolves + scoring only.
"""
from __future__ import annotations
import json, os, sys, time, traceback

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                # noqa: E402  (redirects all writes into this workspace)

PARTD = os.path.join(C.MY_OUT, "rerank_partial")
os.makedirs(PARTD, exist_ok=True)
BANDS = ("sub200", "b200_500")
# the study's two screening winners (arm D = agent, arm R = random) -- see rescore_freeze.py:58
STUDY_D_CID, STUDY_R_CID = "wa2_brackets_soft", "wr2_rnd001"


def score_exact(pkg):
    """Exact-basis LODO score at theta=ones. Mirrors rescore_freeze.score_exact (windowed + measured zeta)."""
    caches = C.SW.load_caches()
    one = np.ones(len(pkg.free_names))
    folds = {}
    for fold in C.DEV_KEYS:
        tks = [k for k in C.DEV_KEYS if k != fold]
        rho, bm = C.SW._train_warp(pkg, one, tks, caches, True, None, None)
        fmask = None
        if bm:
            fm = np.zeros(len(caches[fold]["freqs"]), bool)
            for tk, mmask in bm.items():
                if mmask.shape[0] == fm.shape[0]:
                    fm |= mmask
            fmask = fm if fm.sum() >= C.SW.MIN_BAND else None
        bands = C.SW._grade_bands(pkg, one, fold, caches[fold], rho, fmask, True, None, None, None)
        folds[fold] = {b: bands[b].get("P1p") for b in BANDS}
    agg = {}
    for b in BANDS:
        vals = [folds[f][b] for f in C.DEV_KEYS if folds[f][b] is not None]
        agg[b] = float(np.mean(vals)) if len(vals) == len(C.DEV_KEYS) else None
    return agg, folds


def do_candidate(row, tmaps):
    """Enrich one candidate at its theta_MAP and score it exactly. Resumable; returns a partial record."""
    cid, track = row["cid"], row["track"]
    pp = os.path.join(PARTD, f"{cid}.json")
    if os.path.exists(pp):
        with open(pp) as f:
            r = json.load(f)
        print(f"  [{cid}] resume-skip ({'EXCLUDED' if r.get('excluded') else 'ok'})", flush=True)
        return r
    t0 = time.time()
    rec = {"cid": cid, "track": track, "round": row.get("round"), "family": row.get("family"),
           "screening_sub200": row["sub200_P1p"], "screening_b200_500": row["b200_500_P1p"]}
    try:
        theta = tmaps[cid]["theta"]
        print(f"  [{cid}] ({track}, {row.get('family')}) enriching at theta_MAP ...", flush=True)
        pkg = C.EW.enrich(cid, theta, f"{cid}__xenr")
        agg, folds = score_exact(pkg)
        if any(agg[b] is None for b in BANDS):
            raise ValueError(f"scorer returned a null band aggregate: {agg} (folds {folds})")
        rec.update({"exact_sub200": agg["sub200"], "exact_b200_500": agg["b200_500"],
                    "exact_folds": {f: folds[f]["sub200"] for f in C.DEV_KEYS},
                    "exact_folds_b200_500": {f: folds[f]["b200_500"] for f in C.DEV_KEYS},
                    "theta_map": theta, "enriched_pkg": f"{cid}__xenr",
                    "spot_max_pct": pkg.meta.get("spot_max_pct"),
                    "wall_s": round(time.time() - t0, 1)})
        C.assert_finite({k: rec[k] for k in ("exact_sub200", "exact_b200_500")}, f"rerank.{cid}")
        C.assert_finite(rec["exact_folds"], f"rerank.{cid}.folds")
        print(f"  [{cid}] screening {rec['screening_sub200']:+.4f} -> exact {rec['exact_sub200']:+.4f}  "
              f"({rec['wall_s']:.0f}s, self-consistency {rec['spot_max_pct']:.4f}%)", flush=True)
    except Exception as ex:
        rec.update({"excluded": True, "reason": f"{type(ex).__name__}: {ex}",
                    "traceback": traceback.format_exc()[-800:], "wall_s": round(time.time() - t0, 1)})
        print(f"  [{cid}] EXCLUDED-WITH-REASON: {rec['reason']}", flush=True)
    with open(pp, "w") as f:
        json.dump(rec, f, indent=1)
    return rec


def spearman(a, b):
    """Spearman rank correlation, computed directly (no scipy dependency in the scoring path)."""
    def ranks(x):
        order = np.argsort(np.asarray(x, float))
        r = np.empty(len(x), float)
        r[order] = np.arange(len(x), dtype=float)
        # average ties
        x = np.asarray(x, float)
        for v in np.unique(x):
            m = x == v
            if m.sum() > 1:
                r[m] = r[m].mean()
        return r
    ra, rb = ranks(a), ranks(b)
    ra = ra - ra.mean(); rb = rb - rb.mean()
    den = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def s2_for(rows_by_cid, a_cid, r_cid, convention, note):
    """Paired per-fold S2 = agent - random on the exact sub-200 folds."""
    a, r = rows_by_cid[a_cid], rows_by_cid[r_cid]
    deltas = [a["exact_folds"][f] - r["exact_folds"][f] for f in C.DEV_KEYS]
    dm, se, pf = C.paired_stats(deltas)
    rec = {"convention": convention, "note": note,
           "agent_cid": a_cid, "random_cid": r_cid,
           "agent_exact_sub200": a["exact_sub200"], "random_exact_sub200": r["exact_sub200"],
           "delta_mean": dm, "delta_se": se, "per_fold": pf,
           "S2_rule_met": bool(dm >= se), "rule": "agent beats random by >= 1x paired-fold SE"}
    C.assert_finite({k: rec[k] for k in ("delta_mean", "delta_se")}, f"S2.{convention}")
    return rec


def run_one():
    """Process exactly ONE pending candidate, then exit — so the OS reclaims all memory.

    WHY (decisions_log D4): running all 28 in ONE long-lived process thrashed. Each candidate loads the
    full model + sparse blocks + a k=200 eigensolve; the heap never fully returned to the OS across
    iterations, so by candidate ~18 the 16 GB box was 10.8/12.3 GB into swap and a normally-530 s solve took
    11,198 s (21x). A fresh interpreter per candidate bounds memory to one candidate's working set. Driver:
    `until python3 code/exact_rerank.py --one | grep -q 'ALL DONE'; do :; done` (see run_all.sh).
    Exit 0 always; prints 'ALL DONE' when nothing is pending.
    """
    rows_in = C.loop_candidates()
    tmaps = C.theta_maps()
    pending = [r for r in rows_in if not os.path.exists(os.path.join(PARTD, f"{r['cid']}.json"))]
    if not pending:
        print(f"ALL DONE ({len(rows_in)}/{len(rows_in)} candidates have records)", flush=True)
        return
    row = pending[0]
    print(f"[{len(rows_in) - len(pending) + 1}/{len(rows_in)}] {row['cid']}", flush=True)
    do_candidate(row, tmaps)
    print(f"{len(pending) - 1} candidates still pending", flush=True)


def main():
    t_start = time.time()
    rows_in = C.loop_candidates()
    tmaps = C.theta_maps()
    print(f"exact re-rank: {len(rows_in)} loop candidates "
          f"({sum(1 for r in rows_in if r['track'] == 'agent')} agent + "
          f"{sum(1 for r in rows_in if r['track'] == 'random')} random)", flush=True)

    recs = [do_candidate(row, tmaps) for row in rows_in]
    rows = [r for r in recs if not r.get("excluded")]
    excluded = [{"cid": r["cid"], "track": r["track"], "reason": r["reason"]}
                for r in recs if r.get("excluded")]
    by_cid = {r["cid"]: r for r in rows}
    print(f"\n{len(rows)} candidates exact-scored, {len(excluded)} excluded-with-reason", flush=True)

    # ---------------- S2 under BOTH selection conventions
    s2 = {}
    tracks = {t: [r for r in rows if r["track"] == t] for t in ("agent", "random")}
    scr_win = {t: max(v, key=lambda r: r["screening_sub200"])["cid"] for t, v in tracks.items()}
    exa_win = {t: max(v, key=lambda r: r["exact_sub200"])["cid"] for t, v in tracks.items()}
    if scr_win["agent"] != STUDY_D_CID or scr_win["random"] != STUDY_R_CID:
        print(f"  NOTE: my screening winners {scr_win} differ from the study's arms D/R "
              f"({STUDY_D_CID}/{STUDY_R_CID}) — reporting mine and flagging the discrepancy", flush=True)
    s2["screening_selected"] = s2_for(
        by_cid, scr_win["agent"], scr_win["random"], "screening_selected",
        "the study's convention: each track's SCREENING (theta=1 basis) winner, re-scored on the exact "
        "basis. Reproduction target: the repair's D-R = -0.0017 +/- 0.0094.")
    s2["exact_selected"] = s2_for(
        by_cid, exa_win["agent"], exa_win["random"], "exact_selected",
        "winner's-curse-honest: each track's BEST EXACT candidate. Selection and reporting use the same "
        "trustworthy metric. NOTE: a per-track maximum over 14 noisy candidates carries selection noise in "
        "BOTH arms, so a sub-SE gap is not a win for either track.")

    # ---------------- rank agreement (the mechanism behind (a) vs (b))
    rank_agreement = {}
    for t, v in tracks.items():
        scr = [r["screening_sub200"] for r in v]
        exa = [r["exact_sub200"] for r in v]
        rho = spearman(scr, exa)
        top3s = [r["cid"] for r in sorted(v, key=lambda r: -r["screening_sub200"])[:3]]
        top3e = [r["cid"] for r in sorted(v, key=lambda r: -r["exact_sub200"])[:3]]
        rank_agreement[t] = {
            "n": len(v), "spearman_screening_vs_exact": rho,
            "top3_screening": top3s, "top3_exact": top3e,
            "top1_agrees": bool(top3s[0] == top3e[0]),
            "mean_screening_sub200": float(np.mean(scr)), "mean_exact_sub200": float(np.mean(exa)),
            "mean_inflation_screening_minus_exact": float(np.mean(np.asarray(scr) - np.asarray(exa)))}
        C.assert_finite({"spearman": rho}, f"rank_agreement.{t}")

    # ---------------- pipeline reproduction vs the study's exact freeze numbers
    ex = C.study_exact_freeze()
    reproduction_check = {}
    for arm, cid in (("D", STUDY_D_CID), ("R", STUDY_R_CID)):
        mine = by_cid[cid]["exact_sub200"] if cid in by_cid else None
        study = ex[arm]["exact"]["sub200"]
        reproduction_check[arm] = {
            "cid": cid, "mine_exact_sub200": mine, "study_exact_sub200": study,
            "abs_diff": abs(mine - study) if mine is not None else None,
            "note": "my independent re-enrichment + re-score of the same candidate at the same theta_MAP; "
                    "an ARPACK start-vector difference can perturb near-degenerate modes slightly, so "
                    "agreement to <0.01 is the pass bar (checker G07)."}
    C.assert_finite({k: v["mine_exact_sub200"] for k, v in reproduction_check.items()}, "reproduction")

    out = {"card": "T2 — exact re-rank of ALL 28 loop candidates",
           "method": "each candidate enriched at its own study theta_MAP (k=200 own-space sparse "
                     "shift-invert eigensolve, theta folded in) and scored at theta=ones on the 4 dev folds "
                     "with the study's warp + one-global-gain scorer. theta_MAPs reused verbatim, never "
                     "re-optimized. NO SAMPLER: deterministic eigensolves + scoring.",
           "n_candidates": len(rows_in), "n_scored": len(rows), "n_excluded": len(excluded),
           "screening_winners": scr_win, "exact_winners": exa_win,
           "rows": sorted(rows, key=lambda r: (r["track"], -r["exact_sub200"])),
           "excluded": excluded,
           "S2": s2, "rank_agreement": rank_agreement, "reproduction_check": reproduction_check,
           "generated": time.strftime("%Y-%m-%dT%H:%M:%S")}
    with open(os.path.join(C.MY_OUT, "exact_rerank.json"), "w") as f:
        json.dump(out, f, indent=1)
    C.log_step("exact_rerank", time.time() - t_start, n_scored=len(rows))

    print("\n=== T2 RESULT (exact re-rank, all 28) ===")
    for t in ("agent", "random"):
        ra = rank_agreement[t]
        print(f"  {t:7s}: screening->exact Spearman {ra['spearman_screening_vs_exact']:+.3f}; "
              f"top1 agrees: {ra['top1_agrees']}; mean inflation "
              f"{ra['mean_inflation_screening_minus_exact']:+.4f}")
        print(f"           top3 screening {ra['top3_screening']}")
        print(f"           top3 exact     {ra['top3_exact']}")
    for k, v in s2.items():
        print(f"  S2 [{k:18s}] {v['agent_cid']} vs {v['random_cid']}: "
              f"delta {v['delta_mean']:+.4f} +/- {v['delta_se']:.4f}  rule met: {v['S2_rule_met']}")
    for arm, v in reproduction_check.items():
        print(f"  reproduction {arm}: mine {v['mine_exact_sub200']:.4f} vs study "
              f"{v['study_exact_sub200']:.4f} (diff {v['abs_diff']:.4f})")


if __name__ == "__main__":
    if "--one" in sys.argv:
        run_one()                                   # one candidate per process (memory-bounded; D4)
    else:
        main()                                      # full loop + aggregation (aggregation needs all 28)
