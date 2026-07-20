#!/bin/bash
# One-command replay: notch_multipoint_7004c_20260611
# Regenerates all results, figures, GIFs, the PPTX, and runs the checker.
# Exit code nonzero ONLY on checker RED (AGENTS.md Result Status Standard).
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
mkdir -p logs results figures

START=$(date +%s)
declare -a STEPS=(
  "code/ex_a_tdof_baseline.py"
  "code/ex_b_sixdof.py"
  "code/ex_c_notch_distance.py"
  "code/ex_d_force_limits.py"
  "code/ex_e_empirical_reconstruction.py"
  "code/make_gifs.py"
  "code/make_pptx.py"
)
: > logs/step_times.txt
for s in "${STEPS[@]}"; do
  echo "=== $s"
  T0=$(date +%s)
  (cd code && python3 "$(basename "$s")") 2>&1 | tee "logs/$(basename "$s" .py).log" | tail -3
  T1=$(date +%s)
  echo "$(basename "$s") $((T1-T0))" >> logs/step_times.txt
done
T0=$(date +%s)
python3 check.py | tee logs/check.log
RC=${PIPESTATUS[0]}
T1=$(date +%s)
echo "check.py $((T1-T0))" >> logs/step_times.txt
END=$(date +%s)
echo "total_active_s $((END-START))" >> logs/step_times.txt
echo "run_all.sh finished in $((END-START)) s (checker exit $RC)"
exit $RC
