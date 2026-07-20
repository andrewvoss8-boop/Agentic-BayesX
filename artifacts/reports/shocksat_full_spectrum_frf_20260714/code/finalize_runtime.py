#!/usr/bin/env python3
"""finalize_runtime — Runtime Accounting Gate: runtime.json with active_runtime_s (sum of logged step
times) and elapsed_wallclock_s (since out/.wallclock_start). All CPU (Mac); no GPU used."""
import json, os, time

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
active = 0.0
p = os.path.join(WS, "out", "runtime_log.jsonl")
steps = []
if os.path.exists(p):
    for line in open(p):
        if line.strip():
            r = json.loads(line)
            active += float(r.get("active_s", 0))
            steps.append(r)
start = float(open(os.path.join(WS, "out", ".wallclock_start")).read().strip())
elapsed = time.time() - start
out = {"active_runtime_s": round(active, 1), "elapsed_wallclock_s": round(elapsed, 1),
       "machine": "CPU (Mac, float64); no GPU", "n_steps": len(steps)}
assert out["active_runtime_s"] <= out["elapsed_wallclock_s"], "active > elapsed?"
json.dump(out, open(os.path.join(WS, "runtime.json"), "w"), indent=1)
print(json.dumps(out))
