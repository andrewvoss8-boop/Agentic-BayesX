#!/usr/bin/env bash
# One-command replay for the time-domain latent-force damping diagnostic.
# Replays the ANALYSIS from the saved time-domain caches (data/ringdown/*.npz, ~24 MB) -- it does NOT rebuild
# caches from the raw .mat (that one-time data-prep step is code/cache_builder.py and needs the raw modal .mat).
# Pins BLAS threads for the small dense eigh/posterior math (AGENTS compute protocol). Writes runtime.json.
set -u
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
cd "$(dirname "$0")"
WS="$(pwd)"; PSD="$WS/../shocksat_psd_envelope_twin_20260623"
ACTIVE=0; T0=$(date +%s)
step() { local s=$(date +%s); "$@"; local rc=$?; local e=$(date +%s); ACTIVE=$((ACTIVE + e - s)); return $rc; }

echo "== [0] integrity: reproduce D22 (0/9) from the cached Test07 windowed FRF =="
step bash -c "cd '$PSD/code' && python3 damping_inference.py" && cp "$PSD/out/damping_inference.json" "$WS/out/d22_reproduction.json"

echo "== [1] Layer 1: time-domain decay re-test (band-pass + log-decrement) =="
step bash -c "cd '$WS/code' && python3 layer1_damping.py"

echo "== [2] Layer 1: hierarchical NUTS posterior over per-mode zeta (~10 min) =="
step bash -c "cd '$WS/code' && python3 layer1_nuts.py"

echo "== [3] frequency-domain control on the clean data =="
step bash -c "cd '$WS/code' && python3 freq_control.py"

echo "== [4] finite-perturbation: is zeta a lever on the envelope QOI? =="
step bash -c "cd '$WS/code' && python3 finite_perturbation.py"

echo "== [5] Layer 2: latent-force MFE smoother + damping-vs-residual decomposition =="
step bash -c "cd '$WS/code' && python3 layer2_gplfm.py"

echo "== [6] Layer 3: measured-zeta twin vs FEM+6dB envelope GRMS (held-out, 90% split) =="
step bash -c "cd '$WS/code' && python3 layer3_value.py"

echo "== [7] figures =="
step bash -c "cd '$WS/code' && python3 make_figures.py"
step bash -c "cd '$WS/code' && python3 fig_heldout_psd.py"   # held-out PSD examples (measured-zeta posterior vs FEM vs data)

echo "== [8] checker (exits non-zero only on RED) =="
step bash -c "cd '$WS' && python3 check.py"; CHECK_RC=$?

ELAPSED=$(( $(date +%s) - T0 ))
python3 -c "import json; json.dump({'active_runtime_s': $ACTIVE, 'elapsed_wallclock_s': $ELAPSED, 'note': 'active = sum of per-step seconds; replays analysis from saved caches (cache_builder.py is the one-time raw-.mat data prep, not in this replay)'}, open('$WS/runtime.json','w'), indent=2)"
echo "runtime: active ${ACTIVE}s, elapsed ${ELAPSED}s -> runtime.json"
exit $CHECK_RC
