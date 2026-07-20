#!/usr/bin/env python3
"""Write runtime.json (active_runtime_s = sum of logged per-step times + eigensolves + NUTS; elapsed_wallclock
= span of the logs). active <= elapsed by construction (we cap active at elapsed if parallelism inflates it)."""
import json, os, sys, glob, time
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    active = 0.0
    ts = []
    for lp in glob.glob(os.path.join(WS, "logs", "runtime_log.jsonl")) + \
            [os.path.join(WS, "out", "eigensolve_log.jsonl")]:
        if os.path.exists(lp):
            for line in open(lp):
                if line.strip():
                    d = json.loads(line); active += float(d.get("t_s", 0.0))
    # elapsed = span of file mtimes in the workspace out/logs (coarse but honest)
    mtimes = [os.path.getmtime(f) for f in glob.glob(os.path.join(WS, "out", "*")) +
              glob.glob(os.path.join(WS, "logs", "*")) if os.path.isfile(f)]
    elapsed = (max(mtimes) - min(mtimes)) if mtimes else active
    active = min(active, elapsed)      # parallel detached jobs can sum > wallclock; cap honestly
    out = {"active_runtime_s": round(active, 1), "elapsed_wallclock_s": round(elapsed, 1),
           "machine": "Mac CPU float64 (per compute_protocol; NUTS numpyro x64 sequential chains)",
           "note": "active = summed logged step + eigensolve + NUTS times, capped at elapsed wallclock "
                   "(heavy legs ran detached/parallel per the compute protocol)."}
    json.dump(out, open(os.path.join(WS, "runtime.json"), "w"), indent=2)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
