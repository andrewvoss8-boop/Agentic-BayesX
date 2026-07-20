#!/bin/bash
# One-command replay — ShockSat FRF-domain damping updating (20260710). Resumable: finished artifacts skipped.
# Heavy eigensolves/NUTS run FOREGROUND here (replay semantics); the original run launched them detached.
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=2 VECLIB_MAXIMUM_THREADS=2
P=python3

echo "== 0. reused-source integrity =="
shasum -a 256 -c REUSED_code.sha256 --quiet && echo OK

echo "== 1. validation gates D1/F/D2/O (compute-light) =="
[ -f out/gate_D1.json ] || $P code/gate_D1.py
[ -f out/gate_F.json ]  || $P code/gate_F.py
[ -f out/gate_D2.json ] || $P code/gate_D2.py
[ -f out/gate_O.json ]  || $P code/gate_O.py

echo "== 2. mechanics gates V1-V5 (+ A0 package; full eigensolves) =="
[ -f out/mech_gates.json ] || $P code/run_mech.py

echo "== 3. A0 baseline + A0d damping baseline =="
[ -f out/baseline_summary.json ] || $P code/baseline.py
[ -f out/a0d.json ] || $P code/a0d.py

echo "== 4. agent loop + random track (budgeted, resumable) =="
$P code/loop.py agent
$P code/loop.py random

echo "== 5. exact-basis finalists + S4 ablation =="
[ -f out/finalists.json ] || $P code/finalize.py

echo "== 6. NUTS finalists (theta + band-zeta) =="
for cid in A0_enr c06_tb_xface_enr a04_welds_t074_enr; do
  [ -f out/nuts_${cid}.json ] || $P code/nuts_damp.py ${cid}
done

echo "== 7. Q/H legs + physical-damping honesty =="
for cid in A0_enr c06_tb_xface_enr a04_welds_t074_enr; do
  [ -f out/qoi_${cid}.json ] || $P code/run_qoi.py ${cid}
done
$P code/augment_honesty.py

echo "== 8. vault (freeze must precede grade; grade ONCE) =="
[ -f VAULT_FREEZE.sha256 ] || $P code/vault.py freeze
[ -f out/vault_scores.json ] || $P code/vault.py grade

echo "== 9. verdicts + figures + runtime + checker =="
$P code/verdicts.py
$P code/make_figs.py
$P code/finalize_runtime.py
$P check.py
