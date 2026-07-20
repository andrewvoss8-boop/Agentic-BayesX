#!/usr/bin/env python3
"""Grade the pre-registered S1/S2/S3 success criteria (question_framing §4.3) from artifacts ONLY.
Writes out/verdicts.json. Never claims more than the numbers support; the checker validates labeling.
"""
import json, os, sys
import numpy as np

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def qlog():
    recs = []
    with open(os.path.join(WS, "out", "query_log.jsonl")) as f:
        for line in f:
            if line.strip():
                recs.append(json.loads(line))
    return recs


def main():
    recs = qlog()
    a0 = [r for r in recs if r["track"] == "baseline"][-1]   # LAST baseline record (D19/D21: A0_enr bar)
    a0_cid = a0["cid"]
    def last_per_cid(track):
        out = {}
        for r in recs:
            if r["track"] == track:
                out[r["cid"]] = r          # later records supersede (append-only convention, D19)
        # D22: a cid with a scored *_enr successor is superseded by it (exact-basis rule)
        return [r for c, r in out.items() if f"{c}_enr" not in out]
    agent = last_per_cid("agent")
    rand = last_per_cid("random")

    def is_shape(cid):
        """D20: parametric-only (all-scale) candidates are controls, not remodeling candidates."""
        p = os.path.join(WS, "out", "candidate_specs", f"{cid}.json")
        if not os.path.exists(p):
            return False
        ops = json.load(open(p)).get("ops", [])
        return bool(ops) and any(o["op"] != "scale" for o in ops)

    # D23: winner selection restricted to the exact-basis FREEZE set (vault-graded, comparable evaluation);
    # raw whole-track bests reported alongside with the basis-bias caveat.
    frozen = set(json.load(open(os.path.join(WS, "out", "finalists.json")))["freeze"])
    agent_frozen = [r for r in agent if r["cid"] in frozen]
    rand_frozen = [r for r in rand if r["cid"] in frozen]
    best_agent_any = max(agent_frozen, key=lambda r: r["P1_mean"]) if agent_frozen else None
    agent_shape = [r for r in agent_frozen if is_shape(r["cid"].replace("_enr", ""))
                   or is_shape(r["cid"])]
    best_agent = max(agent_shape, key=lambda r: r["P1_mean"]) if agent_shape else None   # S1 winner (shape)
    best_rand = max(rand_frozen, key=lambda r: r["P1_mean"]) if rand_frozen else None
    raw_bests = {"agent_raw_best": max(agent, key=lambda r: r["P1_mean"])["cid"] if agent else None,
                 "agent_raw_best_P1": max(r["P1_mean"] for r in agent) if agent else None,
                 "random_raw_best": max(rand, key=lambda r: r["P1_mean"])["cid"] if rand else None,
                 "random_raw_best_P1": max(r["P1_mean"] for r in rand) if rand else None,
                 "caveat": "raw records mix biased inherited-basis + single-start evaluations (D18/D19); "
                           "gates use the exact-basis freeze set (D23)"}
    vault = json.load(open(os.path.join(WS, "out", "vault_scores.json")))
    out = {"A0_dev_P1": a0["P1_mean"], "A0_P1_folds": a0["P1_folds"], "A0_P1_se": a0["P1_se"],
           "n_agent_queries": len(agent), "n_random_queries": len(rand),
           "winners_curse_N": {"agent": len(agent), "random": len(rand)}}
    v = {}
    # ---- S1 improvement (agent winner vs A0): dev margin >= +0.05, margin >= 2x SE, vault positive
    if best_agent:
        d_a = np.array(best_agent["P1_folds"]) - np.array(a0["P1_folds"])
        margin = float(np.mean(d_a))
        se = float(np.std(d_a, ddof=1) / np.sqrt(len(d_a)))          # SE of the paired fold differences
        va = vault["models"].get(best_agent["cid"], {}).get("P1_vault")
        v0 = vault["models"].get(a0_cid, vault["models"].get("A0", {})).get("P1_vault")
        s1 = {"winner": best_agent["cid"], "dev_margin": round(margin, 4),
              "dev_margin_se_paired": round(se, 4), "needs": ">=0.05 and >=2x SE and vault>A0",
              "vault_winner": va, "vault_A0": v0,
              "vault_positive": bool(va is not None and v0 is not None and va > v0),
              "pass": bool(margin >= 0.05 and margin >= 2 * se
                           and va is not None and v0 is not None and va > v0)}
    else:
        s1 = {"pass": False, "note": "no agent-track candidates scored"}
    v["S1"] = s1
    # ---- S2 intelligence (agent > random at equal budget)
    # D20: the gate follows the pre-registered LETTER (raw track best-vs-best, no family exclusion);
    # the capability-relevant SHAPE-ONLY comparison is reported alongside and in the packet.
    if best_agent_any and best_rand:
        s2 = {"agent_best_dev_P1_raw": best_agent_any["P1_mean"], "agent_cid_raw": best_agent_any["cid"],
              "random_best_dev_P1": best_rand["P1_mean"], "random_cid": best_rand["cid"],
              "pass": bool(best_agent_any["P1_mean"] > best_rand["P1_mean"]),
              "shape_only_comparison": {
                  "agent_shape_best": best_agent["P1_mean"] if best_agent else None,
                  "agent_shape_cid": best_agent["cid"] if best_agent else None,
                  "agent_shape_beats_random": bool(best_agent and
                                                   best_agent["P1_mean"] > best_rand["P1_mean"])}}
    else:
        s2 = {"pass": False, "note": "missing track"}
    v["S2"] = s2
    # ---- S3 honesty (finalists pass H and Q coverage)
    s3 = {"finalists": {}, "pass": True}
    import glob
    for hp in glob.glob(os.path.join(WS, "out", "honesty_*.json")):
        h = json.load(open(hp))
        cid = h["cid"]
        qp = os.path.join(WS, "out", f"qoi_{cid}.json")
        q = json.load(open(qp)) if os.path.exists(qp) else None
        cov_ok = None
        if q:
            cov_ok = all(ax["min_coverage"] >= 0.95 and ax["max_exceed_dB"] <= 0.5
                         for ax in q["axes"].values())
        lmo_ok = h["lmo_widen_ratio"] > 1.0
        s3["finalists"][cid] = {"lmo_widen_ratio": h["lmo_widen_ratio"], "lmo_ok": lmo_ok,
                                "q_coverage_ok": cov_ok}
        if not lmo_ok or cov_ok is False:
            s3["pass"] = False
    v["S3"] = s3
    win = v["S1"]["pass"] and v["S2"]["pass"] and v["S3"]["pass"]
    v["overall_claim"] = ("WIN: closed-loop shape-changing agent beat A0 (dev+vault) and random search, "
                          "honesty gates passed") if win else \
        "pre-registered claim FALSIFIED (see S1/S2/S3 details; honest reportable outcome)"
    out.update(v)
    # dev-vs-vault gap for every frozen model
    gaps = {}
    for cid, mv in vault["models"].items():
        dev = next((r["P1_mean"] for r in recs if r["cid"] == cid and r["track"] in
                    ("agent", "random", "baseline")), None)
        if dev is not None and mv.get("P1_vault") is not None:
            gaps[cid] = {"dev_P1": round(dev, 4), "vault_P1": round(mv["P1_vault"], 4),
                         "gap": round(dev - mv["P1_vault"], 4)}
    out["dev_vs_vault_gap"] = gaps
    out["raw_track_bests_caveated"] = raw_bests
    json.dump(out, open(os.path.join(WS, "out", "verdicts.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
