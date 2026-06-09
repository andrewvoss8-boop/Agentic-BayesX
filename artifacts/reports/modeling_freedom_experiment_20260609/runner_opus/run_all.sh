#!/usr/bin/env bash
# One-command replay of the SEARCH RUNNER's whole pipeline (synthetic + ShockSat).
# Writes ONLY under runner_opus/. Does NOT touch the vault. Asserts CWD.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$HERE"

# --- CWD guard (contract S9) ---
case "$HERE" in
  *modeling_freedom_experiment_20260609/runner_opus) : ;;
  *) echo "REFUSING: not in runner_opus workspace ($HERE)"; exit 1 ;;
esac

export JAX_ENABLE_X64=1
PY=python3

t0=$(date +%s)

echo "== [1/4] verifying frozen inputs against manifest =="
( cd .. && shasum -c manifest.sha256 >/dev/null && echo "manifest OK" )

echo "== [2/4] synthetic search (MAIN + ablations + overfit probe) =="
ts=$(date +%s); $PY src/search.py;        a_search=$(( $(date +%s) - ts ))

echo "== [3/4] ShockSat modal correlation + committed OOD prediction =="
ts=$(date +%s); $PY src/shocksat.py >/dev/null; a_shock=$(( $(date +%s) - ts ))

echo "== [4/4] figures =="
ts=$(date +%s); $PY src/figures.py;        a_fig=$(( $(date +%s) - ts ))

active=$(( a_search + a_shock + a_fig ))
wall=$(( $(date +%s) - t0 ))
cat > runtime.json <<JSON
{
  "active_runtime_s": ${active},
  "elapsed_wallclock_s": ${wall},
  "breakdown_s": {"search": ${a_search}, "shocksat": ${a_shock}, "figures": ${a_fig}},
  "note": "active = sum of per-stage execution time; <= wallclock. See runtime_search.json for per-NUTS-fit sum."
}
JSON
echo "active=${active}s wall=${wall}s -> runtime.json"

echo "== lock finalists hash =="
shasum -a 256 finalists.json shocksat_predictions.json > finalists.sha256
cat finalists.sha256
echo "DONE. Vault NOT accessed. Human runs ../scripts/score_vault.py next."
