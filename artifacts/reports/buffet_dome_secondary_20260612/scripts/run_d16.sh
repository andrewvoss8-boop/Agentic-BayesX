#!/usr/bin/env bash
# D16 full re-run on the flight-realistic mount model (detached, resumable).
# Order: modes(bcA,bcB) -> QOI both -> coupling + proxy -> CI both -> variants
# -> figures/image-QA/variant-summary -> checker. Each step guarded by its
# output so a relaunch resumes. ~5-7 hr active.
set -uo pipefail
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

step () { echo "[d16 $(date +%H:%M:%S)] $*"; }

# model already built by hand (build_model.py with D16 defaults); rebuild to be safe
[ -f out/model_meta.json ] || python3 scripts/build_model.py > logs/build_d16.log 2>&1

step "modes bcA"; [ -f out/modes_bcA_meta.json ] || python3 scripts/solve_modes.py bcA > logs/solve_bcA_d16.log 2>&1
step "modes bcB"; [ -f out/modes_bcB_meta.json ] || python3 scripts/solve_modes.py bcB > logs/solve_bcB_d16.log 2>&1
step "qoi bcA";   [ -f out/qoi_bcA_summary.json ] || python3 scripts/forcing_qoi.py bcA > logs/qoi_bcA_d16.log 2>&1
step "qoi bcB";   [ -f out/qoi_bcB_summary.json ] || python3 scripts/forcing_qoi.py bcB > logs/qoi_bcB_d16.log 2>&1
step "coupling";  [ -f out/coupling_validation.json ] || python3 scripts/validate_coupling.py > logs/coupling_d16.log 2>&1
step "proxy";     [ -f out/response_limit_proxy.json ] || python3 scripts/response_limit_proxy.py > logs/proxy_d16.log 2>&1
step "ci bcA";    [ -f out/ci_bcA_summary.json ] || python3 scripts/ci_mc.py bcA > logs/ci_bcA_d16.log 2>&1
step "ci bcB";    [ -f out/ci_bcB_summary.json ] || python3 scripts/ci_mc.py bcB > logs/ci_bcB_d16.log 2>&1
step "variants";  python3 scripts/resolve_variants.py > logs/variants_d16.log 2>&1
step "figures";   python3 scripts/make_figures.py > logs/figures_d16.log 2>&1
step "image qa";  python3 scripts/image_qa.py > logs/image_qa_d16.log 2>&1
step "variant summary"; python3 scripts/make_variant_summary.py > logs/variant_summary_d16.log 2>&1
step "checker";   python3 check.py > /dev/null 2>&1
step "DONE"
