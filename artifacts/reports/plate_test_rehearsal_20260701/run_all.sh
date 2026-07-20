#!/usr/bin/env bash
# Plate-test rehearsal — one-command replay.
# Phase 1 (science, resumable, ~3.5 h): per-(arm,seed) NUTS runs -> out/runs/*.json
# Phase 2: summary -> figures -> checker.
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T0=$(date +%s)

python3 code/rehearsal.py               # resumable: skips finished (arm,seed)
python3 code/figs.py
T1=$(date +%s)
python3 - "$T0" "$T1" <<'EOF'
import json, sys, glob
runs = [json.load(open(p)) for p in glob.glob("out/runs/*.json")]
act = sum(r.get("runtime_s", 0) for r in runs)
json.dump({"task": "plate_test_rehearsal_20260701",
           "active_runtime_s": round(act + 120, 1),   # + setup/figs overhead
           "elapsed_wallclock_s": int(sys.argv[2]) - int(sys.argv[1]),
           "n_nuts_runs": len(runs), "sampler": "NUTS (numpyro, 4 chains, x64)"},
          open("runtime.json", "w"), indent=1)
EOF
python3 check.py
