#!/usr/bin/env python3
"""Select finalists from the query log (card §6): <=3 agent-track candidates by dev P1, plus the random-best
and A0 in the freeze set. Enforces that finalists are NOT reduced-basis unless spot-check-validated (D7).
Writes out/finalists.json = {"cids": [nuts targets incl A0], "freeze": [vault-freeze set]}.
"""
import glob
import json
import os
import sys

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def last_per(recs, track):
    out = {}
    for r in recs:
        if r["track"] == track:
            out[r["cid"]] = r
    return list(out.values())


def spot_ok(cid):
    """A reduced-basis candidate is eligible only if its spot check passed; own-space candidates always ok."""
    pkg_meta = json.load(open(os.path.join(WS, "out", "candidate_specs", f"{cid}.json"))) \
        if os.path.exists(os.path.join(WS, "out", "candidate_specs", f"{cid}.json")) else {}
    sc = os.path.join(WS, "out", f"spot_check_{cid}.json")
    # own-space families (refine/thickness/connect) need no spot check
    ops = pkg_meta.get("ops", [])
    if any(o["op"] in ("refine", "thickness", "rbe2_soften") for o in ops):
        return True
    if os.path.exists(sc):
        return json.load(open(sc))["pass_0p3pct"]
    return False


def main(n_finalists=3):
    recs = [json.loads(x) for x in open(os.path.join(WS, "out", "query_log.jsonl")) if x.strip()]
    agent = sorted(last_per(recs, "agent"), key=lambda r: -r["P1_mean"])
    rand = sorted(last_per(recs, "random"), key=lambda r: -r["P1_mean"])
    fins = []
    for r in agent:
        if len(fins) >= n_finalists:
            break
        if spot_ok(r["cid"]):
            fins.append(r["cid"])
        else:
            print(f"[pick] {r['cid']} P1 {r['P1_mean']:.4f} SKIPPED — reduced-basis spot check not passed")
    rand_best = rand[0]["cid"] if rand else None
    freeze = list(dict.fromkeys(fins + ([rand_best] if rand_best else []) + ["A0"]))
    nuts_targets = list(dict.fromkeys(fins + ([rand_best] if rand_best else []) + ["A0"]))
    out = {"cids": nuts_targets, "freeze": freeze,
           "agent_finalists": fins, "random_best": rand_best,
           "agent_finalist_P1": {r["cid"]: r["P1_mean"] for r in agent[:n_finalists]},
           "random_best_P1": rand[0]["P1_mean"] if rand else None}
    json.dump(out, open(os.path.join(WS, "out", "finalists.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 3)
