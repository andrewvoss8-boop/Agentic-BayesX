#!/usr/bin/env python3
"""repro_continuity — pinned continuity bars (card §3.4) for the full-spectrum study.

A0 (historical convention)            == resolution run's B0: A0_enr pkg, naive forward, flat 1% zeta.
A1 (window-matched + measured zeta)   == resolution run's B2: A0_enr pkg, windowed forward, survey-interp zeta.

REUSES the resolution run's wscore/wforward UNEDITED (imported read-only). wscore.score_dev is always called
with log=False so NOTHING is written into the resolution workspace; records are appended to THIS workspace's
out/score_log.jsonl instead. HARD GATE: A0 dev P1' must be 0.1969±0.002 or the study stops.
Resumable: skips arms already in this workspace's score_log.
"""
import json, os, sys, time

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RES_CODE = os.path.abspath(os.path.join(WS, "..", "shocksat_resolution_consistent_scoring_20260713", "code"))
sys.path.insert(0, RES_CODE)
import wscore as SC                                    # noqa: E402  (read-only reuse)

SLOG = os.path.join(WS, "out", "score_log.jsonl")
t0 = time.time()

ARMS = [
    ("A0", "A0_enr", {"kind": "fixed", "zeta": 0.01}, False,
     "continuity bar 0.1969±0.002 (HARD): historical convention = resolution run B0"),
    ("A1", "A0_enr", {"kind": "permode_survey_interp"}, True,
     "continuity bar 0.2371±0.005: window-matched + measured zeta = resolution run B2; THE bar to beat"),
]

done = {}
if os.path.exists(SLOG):
    for line in open(SLOG):
        if line.strip():
            r = json.loads(line)
            if r.get("stage") == "dev":
                done[r["arm"]] = r

recs = {}
for arm, cid, dmp, win, note in ARMS:
    if arm in done:
        print(f"{arm} already scored (resume-skip): P1'={done[arm]['P1p_mean']:.4f}")
        recs[arm] = done[arm]
        continue
    print(f"scoring {arm} ({cid}, {dmp['kind']}, windowed={win}) ...", flush=True)
    r = SC.score_dev(arm, cid, dmp, windowed=win, log=False, note=note)   # log=False: never touch the
    r["train_keys_note"] = "LODO: per-fold train = other 3 dev drives (wscore convention)"  # other workspace
    with open(SLOG, "a") as f:
        f.write(json.dumps(r) + "\n")
    recs[arm] = r
    print(f"  {arm}: P1'={r['P1p_mean']:.4f} folds={r['P1p_folds']}", flush=True)

cont = {"A0_dev_P1p": recs["A0"]["P1p_mean"], "A1_dev_P1p": recs["A1"]["P1p_mean"],
        "A0_folds": recs["A0"]["P1p_folds"], "A1_folds": recs["A1"]["P1p_folds"],
        "A1_fold_se": recs["A1"]["P1p_se"],
        "bars": {"A0": [0.1969, 0.002], "A1": [0.2371, 0.005]},
        "A0_pass": abs(recs["A0"]["P1p_mean"] - 0.1969) <= 0.002,
        "A1_pass": abs(recs["A1"]["P1p_mean"] - 0.2371) <= 0.005}
json.dump(cont, open(os.path.join(WS, "out", "continuity.json"), "w"), indent=1)
with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
    f.write(json.dumps({"step": "repro_continuity", "active_s": round(time.time() - t0, 1)}) + "\n")
print(json.dumps(cont, indent=1))
if not (cont["A0_pass"] and cont["A1_pass"]):
    print("CONTINUITY FAILURE — HARD GATE", file=sys.stderr)
    sys.exit(1)
print("continuity bars reproduced")
