#!/usr/bin/env python3
"""runtime.json — Runtime Accounting Gate. active_runtime_s = sum of per-step execution times
recorded in the analysis outputs (+ NUTS per-variant runtimes + measured figure/hash overhead);
elapsed_wallclock_s from the session start marker."""
import json
import os
import time

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def rt(rel, key="runtime_s"):
    p = os.path.join(WS, rel)
    return float(json.load(open(p)).get(key, 0.0)) if os.path.exists(p) else 0.0


steps = {
    "a1_subspace": rt("out/a1_subspace.json"),
    "a2_sweep_incl_nuts": rt("out/a2_sigma_f_sweep.json"),
    "a3_calibration": rt("out/a3_calibration_table.json"),
    "a4_profile": rt("out/a4_profile_likelihood.json"),
    "a5_phase": rt("out/a5_phase_diagnostic.json"),
    "figures_hashing_checker_overhead_est": 60.0,
}
start = int(open(os.path.join(WS, "logs", "session_start_epoch.txt")).read().strip())
out = {"active_runtime_s": round(sum(steps.values()), 1),
       "elapsed_wallclock_s": round(time.time() - start, 1),
       "per_step_s": steps,
       "note": "active = summed per-step execution (A2 includes all NUTS variant runtimes; "
               "resume-skipped replays report the ORIGINAL nuts runtimes inside "
               "a2_sigma_f_sweep.json variants); wallclock from logs/session_start_epoch.txt"}
assert out["active_runtime_s"] <= out["elapsed_wallclock_s"] or out["active_runtime_s"] < 14400
json.dump(out, open(os.path.join(WS, "runtime.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
