#!/bin/bash
# One-command replay: MPL stand parametric FEM rebuild (FABLE, 2026-06-11).
# BLAS pinned per AGENTS.md compute rules. Total ~8-10 min on a laptop.
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
T0=$(date +%s)
declare -a STEPS=()
run () {  # run <label> <cmd...>
  local label=$1; shift
  local t=$(date +%s)
  echo "=== $label ==="
  "$@"
  STEPS+=("{\"step\": \"$label\", \"seconds\": $(( $(date +%s) - t ))}")
}

run parse            python3 src/parse_deck.py
run validate_elems   python3 src/validate_elements.py
run assemble         python3 src/assemble.py
run modal            python3 src/modal.py
run drill_arm_asm    env DRILL_SCALE=1e-2 OUT_SUBDIR=model_drillx100 python3 src/assemble.py
run drill_arm_modal  env OUT_SUBDIR=model_drillx100 MODE_SUFFIX=_drillx100 NOMINAL_ONLY=1 python3 src/modal.py
run refine_arm_asm   env SHIELD_REFINE=2 OUT_SUBDIR=model_refined python3 src/assemble.py
run refine_arm_modal env OUT_SUBDIR=model_refined MODE_SUFFIX=_refined NOMINAL_ONLY=1 python3 src/modal.py
run discretization   python3 src/discretization_check.py
run interface        python3 src/interface_points.py
run priors           python3 src/priors.py
run prior_predictive python3 src/prior_predictive.py
run ledger           python3 src/make_ledger.py
run figures          python3 src/make_figures.py
run pseudo_frf       python3 src/pseudo_frf.py
run pseudo_frf_fig   python3 src/make_pseudo_frf_fig.py
run finalize_tuning  python3 src/finalize_tuning.py
# NOTE: src/tune_correlation.py (the ~25-min coordinate-descent search) is run
# ON DEMAND, not in the standard replay; finalize_tuning re-derives the result
# from the recorded FINAL config (2 solves).
run gifs             python3 src/make_gifs.py
run image_qa         python3 src/image_qa.py

ACTIVE=0
for s in "${STEPS[@]}"; do
  ACTIVE=$(( ACTIVE + $(echo "$s" | sed -E 's/.*"seconds": ([0-9]+).*/\1/') ))
done
WALL=$(( $(date +%s) - T0 ))
python3 - "$ACTIVE" "$WALL" "${STEPS[@]}" <<'EOF'
import json, sys
active, wall = int(sys.argv[1]), int(sys.argv[2])
steps = [json.loads(s) for s in sys.argv[3:]]
json.dump(dict(active_runtime_s=active, elapsed_wallclock_s=wall,
               note="replay timing (runner authoring time tracked separately "
                    "in runtime.json history)", steps=steps),
          open("runtime.json", "w"), indent=1)
EOF
run checker          python3 check.py
echo "REPLAY COMPLETE (active ${ACTIVE}s, wall ${WALL}s)"
