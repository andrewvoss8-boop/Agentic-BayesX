#!/usr/bin/env python3
"""run_baseline_arms — dev-score the baseline rows of the arms×bands table (decisions D5):
  A0  (wide): naive forward + flat 1% zeta      (historical convention, wide-band restatement)
  A1  (wide): windowed forward + survey zeta    (THE bar to beat, wide-band restatement)
Both at A0_wide's own deterministic multi-start theta_MAP (D19). Resumable via score_log."""
import json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402
import wscore_wide as SW                       # noqa: E402

t0 = time.time()
qoi_w = None
qp = os.path.join(WS, "out", "qoi_sensor_weights.json")
if os.path.exists(qp):
    qoi_w = {int(k): v for k, v in json.load(open(qp))["weights"].items()}

pkg = WP.load("A0_wide")
theta, nlp, ok = pkg.theta_map()
json.dump({"theta_map": dict(zip(pkg.free_names, np.round(theta, 4).tolist())),
           "theta_map_vec": np.asarray(theta, float).tolist(), "free_names": pkg.free_names, "nlp": nlp,
           "multistart_ok": bool(ok)}, open(os.path.join(WS, "out", "theta_map_wide.json"), "w"), indent=1)
print("theta_MAP:", dict(zip(pkg.free_names, np.round(theta, 3).tolist())), flush=True)

done = SW.existing("dev")
ARMS = [
    ("A0", dict(windowed=False, flat_zeta=0.01), "historical convention restated on wide caches"),
    ("A1", dict(windowed=True, flat_zeta=None), "window-matched + survey zeta: THE bar to beat (wide)"),
]
for arm, kw, note in ARMS:
    if arm in done:
        print(f"{arm} already scored (resume-skip)"); continue
    r = SW.score_dev_wide(arm, pkg, theta, note=note, qoi_w=qoi_w, **kw)
    print(arm, json.dumps(r["bands_agg"], indent=1), flush=True)
with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
    f.write(json.dumps({"step": "baseline_arms", "active_s": round(time.time() - t0, 1)}) + "\n")
