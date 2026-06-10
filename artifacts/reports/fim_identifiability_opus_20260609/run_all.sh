#!/usr/bin/env bash
# One-command replay: build -> FIM -> profile-likelihood -> figures -> checker.
# Uses the isolated Opus Phase-1 venv (jax 0.4.30 / numpy 1.26.4 / scipy 1.10.1).
set -euo pipefail
cd "$(dirname "$0")"
PY="../../../runs/fem_phase1/opus/.venv/bin/python"
export OMP_NUM_THREADS=2

start=$(date +%s)
echo "== assert CWD is the analysis workspace, not master repo root =="
case "$(pwd)" in
  *artifacts/reports/fim_identifiability_opus_20260609) echo "CWD OK: $(pwd)";;
  *) echo "REFUSE: run from the analysis workspace"; exit 2;;
esac

echo "== 1. FIM + sensitivity + experiment design ==";  $PY code/run_fim.py
echo "== 2. profile-likelihood confirmation ==";        $PY code/profile_likelihood.py
echo "== 3. figures (Tufte) ==";                        $PY code/make_figures.py
echo "== 4. checker ==";                                $PY check.py || true   # checker sets exit code; keep replay going to write runtime
end=$(date +%s)

$PY - "$start" "$end" <<'PYEOF'
import json, sys, os
start, end = int(sys.argv[1]), int(sys.argv[2])
fr = json.load(open("fim_results.json")); pr = json.load(open("profile_likelihood.json"))
active = round(float(fr.get("runtime_s", 0)) + float(pr.get("runtime_s", 0)), 3)
json.dump({"active_runtime_s": active, "elapsed_wallclock_s": float(end - start),
           "note": "active = summed per-script runtimes; figures+checker excluded (fast)"},
          open("runtime.json", "w"), indent=2)
print("runtime.json:", active, "s active")
PYEOF
echo "== done; see packet.md, checker_report.json, figures/ =="
