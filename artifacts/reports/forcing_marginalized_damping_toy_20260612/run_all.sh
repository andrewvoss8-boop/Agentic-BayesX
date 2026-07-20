#!/usr/bin/env bash
# One-command replay - forcing-marginalized amplitude-dependent damping toy.
set -euo pipefail
cd "$(dirname "$0")"
WALL0=$(date +%s)

export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

PY="../../../.venv_nuts/bin/python"
if [ ! -x "$PY" ]; then
  PY="python3"
fi

mkdir -p logs out figures

"$PY" code/run_toy.py > logs/run_toy.log 2>&1
python3 ../../../.claude/skills/tufte-data-graphics/scripts/tufte_lint.py code/run_toy.py > logs/tufte_lint.txt 2>&1 || true
python3 check.py

WALL1=$(date +%s)
ACTIVE=$("$PY" - <<'PY'
import json
print(round(json.load(open("out/summary.json"))["runtime_s"], 2))
PY
)
python3 - <<EOF
import json
json.dump({"active_runtime_s": $ACTIVE,
           "elapsed_wallclock_s": $((WALL1-WALL0)),
           "stages": {"toy_generation_and_nuts_s": $ACTIVE}},
          open("runtime.json", "w"), indent=1)
EOF
echo "run_all complete; see packet.md checker_report.json runtime.json"
