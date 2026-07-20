#!/bin/bash
# Driver for T2: ONE candidate per python process, strictly SERIAL.
#
# WHY (decisions_log D4): the single long-lived process thrashed a 16 GB box into swap by candidate ~18
# (10.8/12.3 GB swap; a 530 s eigensolve took 11,198 s = 21x). A fresh interpreter per candidate bounds
# memory to one candidate's working set and returns it to the OS on exit. Resumable: each candidate's
# record is skip-loaded if present, so this can be re-run any number of times.
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
for i in $(seq 1 40); do
  OUT=$(python3 code/exact_rerank.py --one 2>&1)
  echo "$OUT"
  if echo "$OUT" | grep -q "ALL DONE"; then
    echo "=== all candidates have records; running aggregation ==="
    python3 code/exact_rerank.py            # full pass: skip-loads all 28, then aggregates S2/ranks
    exit $?
  fi
done
echo "ERROR: still pending after 40 iterations" >&2
exit 1
