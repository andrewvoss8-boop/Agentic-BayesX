#!/usr/bin/env bash
# One-command replay - virtual-sensing-target credibility toy (E1-E4).
set -euo pipefail
cd "$(dirname "$0")"
WALL0=$(date +%s)
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

PY="../../../.venv_nuts/bin/python"
[ -x "$PY" ] || PY="python3"

mkdir -p logs out figures
LINT="../../../.claude/skills/tufte-data-graphics/scripts/tufte_lint.py"

for exp in exp1_discriminating exp2_baselines_sweep exp3_config_trend_identifiability exp4_biased_reconstruction; do
  echo "== running ${exp} =="
  ( cd code && OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 "../$PY" "${exp}.py" > "../logs/${exp}.log" 2>&1 )
  python3 "$LINT" "code/${exp}.py" > "logs/tufte_${exp}.txt" 2>&1 || true
done

python3 check.py | tee logs/check.txt

WALL1=$(date +%s)
ACTIVE=$("$PY" - <<'PY'
import json
tot=0.0
for e in ["exp1","exp2","exp3","exp4"]:
    tot += json.load(open(f"out/{e}_summary.json"))["runtime_s"]
print(round(tot,2))
PY
)
python3 - <<EOF
import json
json.dump({"active_runtime_s": $ACTIVE, "elapsed_wallclock_s": $((WALL1-WALL0)),
           "stages": {"exp1_4_generation_and_nuts_s": $ACTIVE}},
          open("runtime.json","w"), indent=1)
EOF
echo "run_all complete; see packet.md checker_report.json runtime.json"
