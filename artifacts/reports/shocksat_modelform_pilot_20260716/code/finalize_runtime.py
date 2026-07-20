#!/usr/bin/env python3
"""finalize_runtime — Runtime Accounting Gate. active_runtime_s = sum of per-command execution time
(candidate wall_s incl. their eigensolves + finalist fold wall_s + logged steps + standalone
eigensolves not inside a candidate); elapsed_wallclock_s = first-to-last artifact timestamp.
All on the 16 GB Mac CPU (float64, BLAS pinned to 1 thread)."""
from __future__ import annotations
import json
import os
import time

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(WS, "out")


def jlines(p):
    if not os.path.exists(p):
        return []
    return [json.loads(x) for x in open(p) if x.strip()]


def main():
    active = 0.0
    stamps = []

    def stamp(ts):
        if ts:
            stamps.append(time.mktime(time.strptime(ts, "%Y-%m-%dT%H:%M:%S")))

    # candidate + dud partials (wall_s includes their 2 eigensolves + scoring)
    pd = os.path.join(OUT, "partials")
    for fn in sorted(os.listdir(pd)) if os.path.isdir(pd) else []:
        if not fn.endswith(".json") or fn.endswith(".build.json"):
            continue
        r = json.load(open(os.path.join(pd, fn)))
        active += float(r.get("wall_s", 0.0))
        stamp(r.get("ts"))
    # finalist fold partials
    fd = os.path.join(OUT, "finalist_partials")
    for fn in sorted(os.listdir(fd)) if os.path.isdir(fd) else []:
        r = json.load(open(os.path.join(fd, fn)))
        active += float(r.get("wall_s", 0.0))
        stamp(r.get("ts"))
    # logged steps (baseline, vgates, diagnosis, collect, figures)
    for r in jlines(os.path.join(OUT, "runtime_log.jsonl")):
        active += float(r.get("active_s", 0.0))
        stamp(r.get("ts"))
    # standalone eigensolves NOT inside a candidate/vgate step already counted:
    # vgate + repro solves are inside logged steps only if logged; count tags explicitly
    counted_tags = ("own_theta1", "enrich_at_thetaMAP")
    for r in jlines(os.path.join(OUT, "eigensolve_log.jsonl")):
        stamp(r.get("ts"))
        if r.get("tag", "").startswith(counted_tags):
            continue                       # inside candidate wall_s
        if r.get("tag") == "baseline_ref_k200":
            continue                       # inside baseline_ref runtime_log step
        active += float(r.get("t_s", 0.0))
    # repro
    rp = os.path.join(OUT, "repro_check.json")
    if os.path.exists(rp):
        r = json.load(open(rp))
        active += float(r.get("wall_s", 0.0))
        stamp(r.get("ts"))
    elapsed = (max(stamps) - min(stamps)) if len(stamps) > 1 else active
    out = {"active_runtime_s": round(active, 1),
           "elapsed_wallclock_s": round(max(elapsed, active), 1),
           "machine": "16 GB Mac CPU (float64, OMP/VECLIB threads=1); serial eigensolves, "
                      "1 candidate per process",
           "note": "active = sum of per-command execution time (candidate/finalist wall_s incl. "
                   "eigensolves + logged steps + standalone solves); wallclock = first-to-last "
                   "artifact timestamp (detached run survives sleep/relaunch)",
           "generated": time.strftime("%Y-%m-%dT%H:%M:%S")}
    json.dump(out, open(os.path.join(WS, "runtime.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
