#!/usr/bin/env python3
"""Closed-loop orchestration (card §6). This file NEVER loads drive caches — diagnosis fields come from
diag.py (train-side), dev scores come from score.py (scalar returns only). Checker-audited.

Subcommands:
  python3 loop.py build  <specs.json> <track>     build candidate packages (own-space solves as required;
                                                  respects the D7 per-track full-solve allocation of 32)
  python3 loop.py screen <specs.json> <track> <r> NO-sampler train-side proxy rank -> out/screen_<track>_r<r>.json
  python3 loop.py dev    <specs.json> <track> <r> <n_top>   dev-score the top-n screened candidates (budgeted)
Resumable: existing packages/scores are skipped.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F
import actions as ACT
import score as SC

WS = F.WS
FULL_SOLVE_CAP = {"agent": 32, "random": 32}


def full_solves_used(track):
    p = os.path.join(WS, "out", "eigensolve_log.jsonl")
    if not os.path.exists(p):
        return 0
    return sum(1 for line in open(p) if line.strip() and json.loads(line).get("tag") == track)


def scored_cids():
    p = os.path.join(WS, "out", "query_log.jsonl")
    if not os.path.exists(p):
        return set()
    return set(json.loads(x)["cid"] for x in open(p) if x.strip())


def cmd_build(specs_path, track):
    specs = json.load(open(specs_path))
    for spec in specs:
        cid = spec["cid"]
        if os.path.exists(os.path.join(WS, "data", "packages", f"{cid}.npz")):
            print(f"[build] {cid}: exists, skip", flush=True)
            continue
        tag, needs_full = ACT.classify(spec)
        if needs_full and full_solves_used(track) >= FULL_SOLVE_CAP[track]:
            print(f"[build] {cid}: SKIPPED — full-solve cap {FULL_SOLVE_CAP[track]} reached for {track}",
                  flush=True)
            continue
        try:
            pkg, famtag = ACT.build_candidate(spec, tag_track=track)
            n_rbm = int(np.asarray(pkg.n_rbm))
            if n_rbm != 6:
                os.rename(os.path.join(WS, "data", "packages", f"{cid}.npz"),
                          os.path.join(WS, "data", "packages", f"BAD_{cid}.npz"))
                with open(os.path.join(WS, "out", "build_failures.jsonl"), "a") as f:
                    f.write(json.dumps({"cid": cid, "err": f"mechanism: n_rbm={n_rbm} != 6"}) + "\n")
                print(f"[build] {cid}: REJECTED — {n_rbm} rigid-body modes (mechanism)", flush=True)
                continue
            print(f"[build] {cid} ({famtag}): OK n_modes={len(pkg.freqs_el)} "
                  f"pairs={len(np.asarray(pkg.pairs))}", flush=True)
        except Exception as e:
            print(f"[build] {cid}: FAILED {type(e).__name__}: {e}", flush=True)
            with open(os.path.join(WS, "out", "build_failures.jsonl"), "a") as f:
                f.write(json.dumps({"cid": cid, "err": str(e)}) + "\n")


def screen_proxy(cid):
    """NO-sampler train-side proxy (D9): mean matched MAC - 2*mean|df| + 0.02*n_matched at θ_MAP."""
    pkg = F.Package.load(cid)
    theta = SC.theta_map_cached(pkg)
    f_el, Q = pkg.modes(theta)
    mfreqs = np.asarray(pkg.mfreqs, float)
    pairs = np.asarray(pkg.pairs)
    if len(pairs) == 0:
        return -9.9, {}
    # MAC at θ_MAP on ash DOFs (live), frozen pairs
    mm = np.load(os.path.join(F.REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
    ash_now = (np.asarray(pkg.ash_rows) @ Q)[live, :]
    macs, dfs = [], []
    for rr, k, _ in pairs:
        rr, k = int(rr), int(k)
        pm = ash_now[:, k]; tm = msh[rr]
        mac = float(np.dot(tm, pm)) ** 2 / (float(np.dot(tm, tm)) * float(np.dot(pm, pm)) + 1e-300)
        macs.append(mac)
        dfs.append(abs(f_el[k] / mfreqs[rr] - 1.0))
    proxy = float(np.mean(macs) - 2.0 * np.mean(dfs) + 0.02 * len(pairs))
    return proxy, {"mean_mac": round(float(np.mean(macs)), 4), "mean_abs_df": round(float(np.mean(dfs)), 5),
                   "n_matched": int(len(pairs))}


def cmd_screen(specs_path, track, r):
    specs = json.load(open(specs_path))
    rows = []
    for spec in specs:
        cid = spec["cid"]
        if not os.path.exists(os.path.join(WS, "data", "packages", f"{cid}.npz")):
            continue
        proxy, detail = screen_proxy(cid)
        rows.append({"cid": cid, "family": ACT.classify(spec)[0], "proxy": round(proxy, 4), **detail})
        print(f"[screen] {cid}: proxy {proxy:.4f} {detail}", flush=True)
    rows.sort(key=lambda x: -x["proxy"])
    p = os.path.join(WS, "out", f"screen_{track}_r{r}.json")
    json.dump({"note": "NO-sampler train-side proxy (D9); not a posterior, not the metric",
               "rank": rows}, open(p, "w"), indent=1)
    print(f"wrote {p}")


def cmd_dev(specs_path, track, r, n_top):
    specs = {s["cid"]: s for s in json.load(open(specs_path))}
    rank = json.load(open(os.path.join(WS, "out", f"screen_{track}_r{r}.json")))["rank"]
    done = scored_cids()
    n = 0
    for row in rank:
        if n >= n_top:
            break
        cid = row["cid"]
        if cid in done:
            n += 1
            continue
        s = specs[cid]
        rec = SC.score_candidate(cid, track, rationale=s.get("rationale", ""),
                                 family=row["family"], evidence=s.get("evidence", ""))
        print(f"[dev] {cid}: P1 {rec['P1_mean']:.4f} folds {rec['P1_folds']} "
              f"P2 {rec['P2_mean_dB']}", flush=True)
        n += 1


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        cmd_build(sys.argv[2], sys.argv[3])
    elif cmd == "screen":
        cmd_screen(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    elif cmd == "dev":
        cmd_dev(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
    else:
        raise SystemExit("build|screen|dev")
