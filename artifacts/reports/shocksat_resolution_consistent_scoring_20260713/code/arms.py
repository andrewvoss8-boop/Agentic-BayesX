#!/usr/bin/env python3
"""Dev scoring of the remaining pre-registered arms B2-B5 (B0/B1 are produced by gate_r.py). The arm set is
FIXED by the card; nothing is added, dropped, or tuned. Resumable: skips arms already in score_log.jsonl.
Also runs the A3 sensitivity variant (interp vs nearest survey-zeta map on B2) — logged to
out/sensitivity_A3.json ONLY (not score_log; it is not an arm)."""
import json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wscore as SC

t0 = time.time()
OUT = os.path.join(SC.WS, "out")
ERA_BZ = [0.00099, 0.00301, 0.00542, 0.00236]   # scratch_test07/era_result.npz band_zeta (pre-registered)

ARMS = [
    ("B2", "A0_enr", {"kind": "permode_survey_interp"}, True,
     "THE CLAIM: window-matched forward + physical survey zeta"),
    ("B3", "A0_enr", {"kind": "fixed", "zeta": 0.01}, True,
     "ablation: window alone (flat 1%)"),
    ("B4", "A0_enr", {"kind": "band", "zeta": ERA_BZ}, True,
     "validation: ERA 4-band zeta; CAVEAT: ERA derives from Test07 (+X drive) raw records -> "
     "labeled leakage caveat on the +X fold"),
    ("B5", "c06_tb_xface_enr", {"kind": "permode_survey_interp"}, True,
     "shape-edit comparator under resolution-consistency"),
]

done = SC.existing("dev")
for arm, cid, dmp, win, note in ARMS:
    if arm in done:
        print(f"{arm} already scored (resume-skip)"); continue
    print(f"scoring {arm} ({cid}, {dmp['kind']}, windowed={win}) ...", flush=True)
    r = SC.score_dev(arm, cid, dmp, windowed=win, note=note)
    print(f"  {arm}: P1'={r['P1p_mean']:.4f} folds={r['P1p_folds']} P2'={r['P2p_mean']:.4f} "
          f"P4={r['P4_mean']:.2f} dB", flush=True)

# A3 sensitivity (NOT an arm; not in score_log): survey-zeta map interp vs nearest on the claim arm
sens_p = os.path.join(OUT, "sensitivity_A3.json")
if not os.path.exists(sens_p):
    print("A3 sensitivity: B2 with nearest-mode survey-zeta map ...", flush=True)
    alt = SC.score_dev("B2_sens_nearest", "A0_enr", {"kind": "permode_survey_nearest"}, windowed=True,
                       log=False, note="A3 sensitivity variant (interp vs nearest); NOT an arm")
    b2 = SC.existing("dev")["B2"]
    json.dump({"B2_interp_P1p": b2["P1p_mean"], "B2_nearest_P1p": alt["P1p_mean"],
               "delta": alt["P1p_mean"] - b2["P1p_mean"],
               "note": "sensitivity of the claim arm to the survey-zeta mapping choice (assumptions A3)"},
              open(sens_p, "w"), indent=1)
with open(os.path.join(OUT, "runtime_log.jsonl"), "a") as f:
    f.write(json.dumps({"step": "arms_B2_B5", "active_s": round(time.time() - t0, 1)}) + "\n")
print("arms done")
