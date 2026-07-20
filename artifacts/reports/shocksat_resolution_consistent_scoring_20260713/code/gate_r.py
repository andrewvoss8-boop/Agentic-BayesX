#!/usr/bin/env python3
"""Gate R — reproduction / pipeline-drift guard. Scores arms B0 (naive + flat 1% on A0_enr) and B1 (naive +
survey per-mode zeta) through THIS study's scorer; B0 must reproduce the damping run's A0_enr dev
P1' = 0.196949 +/- 0.002 (frozen query_log reference) and B1 must be BELOW B0 (the addendum's naive-physical
deficit direction). These two scores ARE the B0/B1 dev entries in score_log.jsonl (no duplication).
Resumable: skips arms already logged."""
import json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wscore as SC

t0 = time.time()
OUT = os.path.join(SC.WS, "out")
REF = 0.196949

done = SC.existing("dev")
if "B0" not in done:
    print("scoring B0 (naive, flat 1%, A0_enr) ...", flush=True)
    done["B0"] = SC.score_dev("B0", "A0_enr", {"kind": "fixed", "zeta": 0.01}, windowed=False,
                              note="incumbent convention; Gate R reproduction target")
if "B1" not in done:
    print("scoring B1 (naive, survey per-mode zeta, A0_enr) ...", flush=True)
    done["B1"] = SC.score_dev("B1", "A0_enr", {"kind": "permode_survey_interp"}, windowed=False,
                              note="control: physically-correct light damping, naive forward")

b0, b1 = done["B0"]["P1p_mean"], done["B1"]["P1p_mean"]
res = {"B0_P1p_mean": b0, "B0_ref": REF, "B0_abs_err": abs(b0 - REF),
       "B0_P1p_folds": done["B0"]["P1p_folds"],
       "B1_P1p_mean": b1, "B1_lt_B0": bool(b1 < b0),
       "pass": bool(abs(b0 - REF) <= 0.002 and b1 < b0),
       "runtime_s": round(time.time() - t0, 1)}
with open(os.path.join(OUT, "gate_R.json"), "w") as f:
    json.dump(res, f, indent=1)
with open(os.path.join(OUT, "runtime_log.jsonl"), "a") as f:
    f.write(json.dumps({"step": "gate_R", "active_s": res["runtime_s"]}) + "\n")
print(json.dumps(res, indent=1))
print("GATE R:", "PASS" if res["pass"] else "FAIL")
