#!/bin/bash
# One-command replay — shocksat_closure_analyses_20260722 (Task Card A).
# Deterministic; A2 NUTS variants resume-skip on existing out/a2_draws/<name>.npz
# (delete out/a2_draws/ for a full ~75-min recompute; everything else is < 1 min).
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

python3 code/init_hash.py init          # source_manifest.json (57 frozen inputs)
python3 code/a1_subspace.py             # A1 subspace + known-answer gate
python3 code/a5_phase.py                # A5 provenance (found artifact)
python3 code/a3_calibration.py          # A3 known-answer reproduction + CRPS
python3 code/a4_profile.py              # A4 profiled-nuisance whole-FRF profiles
python3 code/a2_sweep.py                # A2 sigma_f 5-prior NUTS sweep (resumable)

python3 code/fig_a1.py
python3 code/fig_a3.py
python3 code/fig_a4.py
python3 code/fig_a2.py
: > out/tufte_lint.txt
for f in code/fig_a1.py code/fig_a3.py code/fig_a4.py code/fig_a2.py; do
  python3 "../../../.claude/skills/tufte-data-graphics/scripts/tufte_lint.py" "$f" >> out/tufte_lint.txt
done
python3 code/fig_qa.py                  # legibility QA -> out/fig_qa.json
python3 code/finalize_runtime.py        # runtime.json (sums logged step runtimes)
python3 code/init_hash.py verify        # end-of-run hash verify (exit 1 on mismatch)
python3 check.py                        # immutable checker (exit 1 only on RED)
