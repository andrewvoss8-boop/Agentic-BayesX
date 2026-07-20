#!/usr/bin/env bash
# One-command replay — buffet/acoustic dome secondary-structure study.
# Grows by stage; exits non-zero only on checker RED (AGENTS.md standard).
set -euo pipefail
cd "$(dirname "$0")"
WALL0=$(date +%s)

export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

# Stage 1 — forcing-math plumbing validation (analytic SS plate)
python3 scripts/validate_forcing_math.py > logs/stage1.log 2>&1

# Stage 2 — added beam/bar element validation (struts + ring)
python3 scripts/validate_beam.py > logs/stage2.log 2>&1

# Stage 3 — fine-region model build + Donnell assembly validation
python3 scripts/build_model.py > logs/build.log 2>&1
python3 scripts/validate_assembly.py > logs/stage3.log 2>&1

# Heavy stages (HOURS; run detached — compute gate): modal solves, QOI sweeps,
# CI MC, variants. Replay them with:
#   bash scripts/run_pipeline_tonight.sh   (after: python3 scripts/solve_modes.py bcA; ... bcB)
#   bash scripts/run_d14_finalize.sh       (D14 model + variants)
# Light post-stages once modes_bcA.npz exists (each ~30s-10min):
#   python3 scripts/validate_coupling.py     # S6 truncation trust-test
#   python3 scripts/response_limit_proxy.py  # S8 response-limit proxy
#   python3 scripts/make_variant_summary.py  # S7 variant/mesh table
#   python3 scripts/make_figures.py && python3 scripts/image_qa.py
# This default replay validates foundations + checks whatever heavy artifacts exist.
if [ -f out/modes_bcA.npz ] && [ ! -f out/response_limit_proxy.json ]; then
  python3 scripts/response_limit_proxy.py > logs/proxy.log 2>&1 || true
fi

# Checker (immutable during trial)
python3 check.py

WALL1=$(date +%s)
python3 - <<EOF
import json
s1 = json.load(open('out/forcing_validation.json'))['runtime_s']
s2 = json.load(open('out/beam_validation.json'))['runtime_s']
json.dump({"active_runtime_s": round(s1 + s2, 1),
           "elapsed_wallclock_s": $((WALL1-WALL0)),
           "stages": {"S1_forcing_validation_s": round(s1, 1),
                      "S2_beam_validation_s": round(s2, 1)}},
          open("runtime.json", "w"), indent=1)
EOF
echo "run_all complete; see checker_report.json runtime.json"
