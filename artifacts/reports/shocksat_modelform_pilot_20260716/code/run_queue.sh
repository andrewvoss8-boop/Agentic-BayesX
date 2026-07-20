#!/bin/bash
# run_queue — drain out/pending_specs/ SERIALLY, ONE candidate per python process (Card A D4 memory
# lesson). Fully resumable: partials skip finished work.
# FIX (r2): the completion check now inspects ONLY the current iteration's output — the original
# `tail -5 logs/queue.log` caught a PREVIOUS round's "ALL DONE" line and exited after one candidate.
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
while true; do
  out=$(python3 code/pipeline.py one 2>&1)
  echo "$out" >> logs/queue.log
  echo "$out" | tail -2
  if echo "$out" | grep -q "ALL DONE"; then
    break
  fi
done
echo "queue drained"
