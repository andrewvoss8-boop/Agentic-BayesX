#!/usr/bin/env bash
# One-command replay of the ShockSat modal twin pipeline.
# Refuses to run from the master repo root (workspace-isolation gate).
set -euo pipefail
cd "$(dirname "$0")"
HERE="$(pwd)"
case "$HERE" in
  *"/artifacts/reports/shocksat_fem_modal_twin_"*) : ;;
  *) echo "REFUSING: not in the runner workspace ($HERE)"; exit 2 ;;
esac

PY=python3                                   # system py: parse/assemble/solve
NUTS_PY="../../../.venv_nuts/bin/python"     # pinned jax/numpyro env (Sec.12)
[ -x "$NUTS_PY" ] || { echo "pinned .venv_nuts missing (Sec.12 gate)"; exit 3; }
export PYTHONPATH=scripts
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p matrices figures logs femap_handoff

echo "== 1. parse NASTRAN deck"
$PY scripts/parse_nastran.py
echo "== 2. parse measured .ash test modes"
$PY scripts/parse_ash.py
echo "== 3. validate element library"
( cd scripts && $PY fe_validate.py )
echo "== 4. assemble per-PID K blocks + M + RBE2 T"
$PY scripts/assemble_fem.py
echo "== 5. nominal full-order eigensolve + observation operator + MAC"
$PY scripts/solve_nominal.py
echo "== 6. Hungarian one-to-one mode pairing"
$PY scripts/pairing.py
echo "== 7. reduced basis + non-uniform probe report"
$PY scripts/reduce_model.py
echo "== (7b. OPTIONAL basis enrichment — abandoned on cost, decision D18;"
echo "==      replay manually: $PY scripts/enrich_basis.py)"
echo "== 8. replicate-test frequency noise floor"
$PY scripts/noise_floor.py
echo "== 9. NUTS band-extrapolation + held-out (D22 remedy config)"
NUTS_MTD=10 NUTS_WARMUP=2000 NUTS_DRAWS=2000 $NUTS_PY scripts/run_nuts.py band
echo "== 10. NUTS leave-one-mode-out held-out (4 parallel workers, D21)"
$NUTS_PY scripts/lomo_parallel.py --drive
echo "== 11. NUTS full-calibration run (theta posterior + FEMAP theta)"
$NUTS_PY scripts/run_full.py
echo "== 12. reduced-vs-full validation at posterior-median theta (D18)"
$PY scripts/validate_posterior.py
echo "== 13. sensitivity arms (prior width, MAC likelihood, band edge)"
$NUTS_PY scripts/sensitivity.py || echo "(sensitivity arm failed — labeled)"
echo "== 14. lock held-out predictions (hash before grading)"
$PY scripts/make_lock.py
echo "== 15. figures (Tufte gate)"
$PY scripts/make_figures.py
$PY scripts/make_figures2.py
echo "== 16. FEMAP cross-check decks (nominal + posterior-mean theta)"
$PY scripts/make_femap_deck.py nominal
$PY scripts/make_femap_deck.py posterior \
    --theta-json femap_handoff/theta_posterior_mean.json
echo "== 17. re-hash inputs (must equal start)"
$PY scripts/hash_inputs.py end
echo "== 18. checker"
$PY check.py
echo "== DONE"
