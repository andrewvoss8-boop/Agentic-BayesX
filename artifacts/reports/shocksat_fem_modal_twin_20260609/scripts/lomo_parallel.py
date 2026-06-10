#!/usr/bin/env python3
"""Parallel leave-one-mode-out (LOMO) driver (decision D21).

Reuses run_nuts.py functions UNCHANGED; only the orchestration differs:
each held-out mode runs as its own single-threaded process (4 at a time),
then partial results merge into heldout_lomo.json with the IDENTICAL schema
the sequential `run_nuts.py lomo` branch writes.

  python lomo_parallel.py --drive      # spawn workers, merge
  python lomo_parallel.py --worker 5   # one held-out mode (internal)
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
PY = os.path.abspath(os.path.join(WS, "../../../.venv_nuts/bin/python"))
NPAR = 4

ap = argparse.ArgumentParser()
ap.add_argument("--worker", type=int, default=None)
ap.add_argument("--drive", action="store_true")
ap.add_argument("--mac", action="store_true")
args = ap.parse_args()

os.chdir(WS)

if args.worker is not None:
    sys.path.insert(0, HERE)
    import numpy as np
    import run_nuts as RN
    held = args.worker
    hi = [t for t in RN.calib_modes if t != held]
    t0 = time.time()
    samples, div = RN.run_nuts(hi, args.mac, seed=held)
    conv = RN.convergence(samples, div, 1000, 4)
    row = RN.predict(samples, [held])[0]
    row.update(conv_rhat=conv["worst_rhat"], conv_ess=conv["min_ess"],
               conv_div=conv["divergences"])
    json.dump(dict(row=row, runtime_s=round(time.time() - t0, 1)),
              open(f"logs/lomo_partial_{held}{'_mac' if args.mac else ''}.json",
                   "w"), indent=1)
    print(f"worker {held}: err {row['err_pct']:+.2f}% covers_pred "
          f"{row['covers_pred']} rhat {conv['worst_rhat']:.3f} "
          f"({time.time()-t0:.0f}s)", flush=True)
    sys.exit(0)

assert args.drive
calib = json.load(open("pairing.json"))["calib_test_modes"]
suffix = "_mac" if args.mac else ""
env = dict(os.environ, OMP_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1",
           OPENBLAS_NUM_THREADS="1")
todo = [m for m in calib
        if not os.path.exists(f"logs/lomo_partial_{m}{suffix}.json")]
print(f"LOMO modes: {calib}; to run: {todo}", flush=True)
procs = {}
while todo or procs:
    while todo and len(procs) < NPAR:
        m = todo.pop(0)
        cmd = [PY, os.path.join(HERE, "lomo_parallel.py"), "--worker", str(m)]
        if args.mac:
            cmd.append("--mac")
        lf = open(f"logs/lomo_worker_{m}{suffix}.log", "w")
        procs[m] = (subprocess.Popen(cmd, env=env, stdout=lf, stderr=lf), lf)
        print(f"spawned worker {m}", flush=True)
    done = [m for m, (p, _) in procs.items() if p.poll() is not None]
    for m in done:
        p, lf = procs.pop(m)
        lf.close()
        print(f"worker {m} exited {p.returncode}", flush=True)
        if p.returncode != 0:
            print(f"WORKER {m} FAILED — see logs/lomo_worker_{m}{suffix}.log",
                  flush=True)
    time.sleep(5)

import numpy as np
rows, worst = [], {"rhat": 0.0, "ess": 1e18, "div": 0}
for m in calib:
    d = json.load(open(f"logs/lomo_partial_{m}{suffix}.json"))["row"]
    rows.append(d)
    worst["rhat"] = max(worst["rhat"], d["conv_rhat"])
    worst["ess"] = min(worst["ess"], d["conv_ess"])
    worst["div"] = max(worst["div"], d["conv_div"])
cov_pred = float(np.mean([r["covers_pred"] for r in rows]))
cov_param = float(np.mean([r["covers_param"] for r in rows]))
json.dump(dict(design="lomo", use_mac=args.mac, rows=rows,
               worst_convergence=worst, coverage_pred=cov_pred,
               coverage_param=cov_param),
          open(f"heldout_lomo{suffix}.json", "w"), indent=1)
print(f"LOMO merged: coverage_pred {cov_pred:.2f}, coverage_param "
      f"{cov_param:.2f}, worst rhat {worst['rhat']:.4f}, "
      f"min ess {worst['ess']:.0f}", flush=True)
