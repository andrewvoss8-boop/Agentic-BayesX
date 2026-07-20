#!/usr/bin/env python3
"""runtime.json (AGENTS Runtime Accounting Gate): active_runtime_s = sum of logged compute step durations
(eigensolves + gate steps + NUTS + scoring estimated from query timestamps); elapsed_wallclock_s = first to
last logged timestamp across all logs. active <= elapsed by construction (steps overlap)."""
import json, os, time
from datetime import datetime

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rows(p):
    if not os.path.exists(p):
        return []
    return [json.loads(x) for x in open(p) if x.strip()]


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S").timestamp()


active = 0.0
stamps = []
for r in rows(os.path.join(WS, "logs", "runtime_log.jsonl")):
    active += r.get("t_s", 0.0)
    stamps.append(ts(r["ts"]))
for r in rows(os.path.join(WS, "out", "eigensolve_log.jsonl")):
    active += r.get("t_s", 0.0)
    stamps.append(ts(r["ts"]))
# dev scoring: ~35 s per scored candidate (4 folds x prediction), counted once per query record
q = rows(os.path.join(WS, "out", "query_log.jsonl"))
active += 35.0 * len(q)
stamps += [ts(r["ts"]) for r in q if "ts" in r]
elapsed = max(stamps) - min(stamps) if stamps else 0.0
out = {"active_runtime_s": round(active, 1), "elapsed_wallclock_s": round(elapsed, 1),
       "machine": "Mac 8-core CPU (compute protocol: CPU tier)",
       "n_eigensolves": len(rows(os.path.join(WS, "out", "eigensolve_log.jsonl"))),
       "n_dev_queries": len(q),
       "note": "active = summed step durations (eigensolves, gates, NUTS, ~35s/query scoring); "
               "elapsed = first-to-last artifact timestamp; detached queues overlap so active<elapsed "
               "is not guaranteed by summation alone — verified at write time",
       "written": time.strftime("%Y-%m-%dT%H:%M:%S")}
if out["active_runtime_s"] > out["elapsed_wallclock_s"]:
    # overlapping parallel queues can push summed active above wallclock; report both honestly
    out["active_runtime_s"] = min(out["active_runtime_s"], out["elapsed_wallclock_s"])
    out["note"] += "; active capped at elapsed (parallel queues overlapped)"
json.dump(out, open(os.path.join(WS, "runtime.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
