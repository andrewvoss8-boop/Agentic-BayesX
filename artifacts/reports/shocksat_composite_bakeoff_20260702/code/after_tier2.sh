#!/bin/bash
# Detached orchestrator: wait for the running tier-2, ensure completeness (resume if needed), then run the
# remaining pipeline. All stages resumable; no approvals needed (task card). Logs to logs/pipeline.log.
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=4 VECLIB_MAXIMUM_THREADS=4
echo "[orchestrator] waiting for running tier2 ($(date))"
while pgrep -f tier2_full.py > /dev/null; do sleep 120; done
N=$(python3 -c "import json;print(len(json.load(open('out/tier2_full.json'))['results']))" 2>/dev/null || echo 0)
echo "[orchestrator] tier2 process gone, n=$N ($(date))"
if [ "$N" -lt 29 ]; then
  echo "[orchestrator] resuming tier2 in-line"
  python3 code/tier2_full.py || exit 1
fi
echo "[orchestrator] tier3 evidence ($(date))"
python3 code/tier3_evidence.py || exit 1
echo "[orchestrator] arms NUTS ($(date))"
python3 code/run_arms.py || exit 1
echo "[orchestrator] score matrix ($(date))"
python3 code/score_matrix.py || exit 1
echo "[orchestrator] figures ($(date))"
python3 code/fig_matrix.py || exit 1
python3 code/fig_graphmodel.py || exit 1
echo "[orchestrator] locked checker ($(date))"
python3 check.py
echo "[orchestrator] DONE exit=$? ($(date))"
