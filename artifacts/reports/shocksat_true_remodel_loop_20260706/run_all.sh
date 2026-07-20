#!/bin/bash
# One-command replay — ShockSat TRUE agentic remodel loop (20260706).
# Everything is resumable: finished artifacts are skipped. Heavy eigensolves/NUTS run FOREGROUND here
# (replay semantics); during the original run they were launched detached per the compute protocol.
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=4 VECLIB_MAXIMUM_THREADS=4

echo "== 0. reused-source integrity =="
shasum -a 256 -c REUSED_code.sha256 --quiet && echo OK

echo "== 1. mechanics gates V1-V5 (+ A0 package) =="
python3 code/mech_gates.py

echo "== 2. A0 baseline + reference bar + round-0 diagnosis =="
python3 code/baseline.py

echo "== 3. agent rounds (proposals are stored artifacts; builds/screens/dev-scores resume) =="
for r in 1 2 3 4; do
  if [ -f "out/proposals_r${r}.json" ]; then
    python3 code/loop.py build  out/proposals_r${r}.json agent
    python3 code/loop.py screen out/proposals_r${r}.json agent ${r}
    ntop=$(python3 -c "import json;print(json.load(open('out/round_plan.json'))['r${r}_ntop'])" 2>/dev/null || echo 12)
    python3 code/loop.py dev    out/proposals_r${r}.json agent ${r} ${ntop}
    python3 code/diag.py $(python3 -c "import json;print(json.load(open('out/round_plan.json')).get('r${r}_diag','A0'))" 2>/dev/null || echo A0) ${r} || true
  fi
done

echo "== 4. random track (fixed seed 20260706) =="
if [ -f "out/proposals_random.json" ]; then
  python3 code/loop.py build  out/proposals_random.json random
  python3 code/loop.py screen out/proposals_random.json random 99
  python3 code/loop.py dev    out/proposals_random.json random 99 60
fi

echo "== 5. finalists: NUTS + Q/H legs =="
if [ -f "out/finalists.json" ]; then
  for cid in $(python3 -c "import json;print(' '.join(json.load(open('out/finalists.json'))['cids']))"); do
    [ -f "out/nuts_${cid}.json" ] || python3 code/nuts_finalist.py ${cid}
    [ -f "out/qoi_${cid}.json" ]  || python3 code/qoi.py ${cid}
  done
fi

echo "== 6. vault (freeze must precede grade; grade happens ONCE) =="
if [ -f "out/finalists.json" ] && [ ! -f "VAULT_FREEZE.sha256" ]; then
  python3 code/vault.py freeze "$(python3 -c "import json;print(','.join(json.load(open('out/finalists.json'))['freeze']))")"
fi
if [ -f "VAULT_FREEZE.sha256" ] && [ ! -f "out/vault_scores.json" ]; then
  python3 code/vault.py grade
fi

echo "== 7. verdicts + figures + checker =="
[ -f "out/vault_scores.json" ] && python3 code/verdicts.py
[ -f "code/make_figs.py" ] && python3 code/make_figs.py
python3 check.py
