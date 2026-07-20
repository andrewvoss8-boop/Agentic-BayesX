#!/usr/bin/env bash
# Card G — one-command replay. Reproduces Part A (Card F value program) then the multi-reference Part B.
# All analysis/figures replay from the kept band-limited FRF caches (data/multiref/*.npz). The cache-BUILD steps
# (coherence_diagnostic, multiref_build_caches) need the raw 256 MB .mat hits, which were DELETED for disk hygiene
# after caching — re-extract the NASA ShockSat1 Test07/08/10 (+impact) and Test03 (modal) hits to rebuild caches.
set -euo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=python3

echo "== check.py baseline =="; $PY check.py || true

echo "== Part A: reproduce Card F value program (+X) =="; $PY code/partA_reproduce.py

# Part B cache build (needs raw .mat; skip if caches present) ----------------------------------------------------
if ls data/multiref/*_N65536.npz >/dev/null 2>&1; then
  echo "== Part B caches present — skipping cache build (raw .mat deleted for hygiene) =="
else
  echo "== Part B: build multi-reference FRF caches (needs re-extracted raw .mat) =="
  $PY code/multiref_build_caches.py
  $PY code/coherence_diagnostic.py
fi

echo "== Part B: coherence diagnostic (if caches only) =="; [ -f out/coherence_by_reference.json ] || $PY code/coherence_diagnostic.py
echo "== Part B: mechanism (drive-shape ratio) =="; $PY code/drive_shape_ratio.py
echo "== Part B: identifiability single vs multi =="; $PY code/multiref_identifiability.py
echo "== Part B: HEADLINE held-out amplitude before/after (NUTS) =="; $PY code/multiref_value.py
echo "== Part B: frequency preservation =="; $PY code/multiref_freq.py
echo "== figures + image QA =="; $PY code/figs.py

echo "== check.py final =="; $PY check.py
