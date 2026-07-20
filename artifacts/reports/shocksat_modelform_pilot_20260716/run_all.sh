#!/bin/bash
# One-command replay — MODEL-FORM PILOT (Card C, 2026-07-16).
#
# Every stage is RESUMABLE (baseline/vgate/repro artifacts skip-load; per-candidate partials in
# out/partials/; per-(finalist,fold) partials in out/finalist_partials/; packages in
# data/packages_mf/). Exits non-zero only on checker RED.
#
# ISOLATION: writes ONLY inside this workspace (code/_common.py rebinds every reused-module write
# target; study packages reached via symlinks). REUSED_code.sha256 hashes the read-only inputs.
#
# PROVENANCE OF PROPOSALS: the RANDOM track is fully seeded (out/seeds.json). The AGENT track's specs
# were authored per round by the runner from out/diagnosis_mf_r*.json (links in
# out/round_summary_r*.md) and are preserved VERBATIM in out/pending_specs/ — replay re-scores the
# same 60 candidates; it does not re-author proposals.
#
# RUNTIME: ~120 serial k=200 eigensolves at ~400k DOF (~8-16 min each on the 16 GB Mac) => plan for
# a 20-32 h detached run. SERIAL ONLY — parallel eigensolves thrash to swap.
# NO SAMPLER (deterministic MAPs + exact eigensolves; pre-registered). NO VAULT (+XY never read;
# runtime guard in logs/vault_opens.jsonl).
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

echo "== stage 0: baseline reference (1 eigensolve) =="
python3 code/pipeline.py baseline

echo "== stage 1: operator V-gates (BEFORE any scored use; checker G04) =="
python3 code/vgates.py

echo "== stage 2: pipeline reproduction check (contract Q4; 2 eigensolves) =="
python3 code/pipeline.py repro

echo "== stage 3: the loop — drain the candidate queue (~120 eigensolves, SERIAL, detached-safe) =="
bash code/run_queue.sh

echo "== stage 4: finalists (per-fold amplitude refits + exact per-fold enrichments) =="
python3 code/finalists.py

echo "== stage 5: collect + verdicts =="
python3 code/collect.py

echo "== stage 6: figures (tufte skill; lint + legibility QA) =="
python3 "../../../.claude/skills/tufte-data-graphics/scripts/tufte_lint.py" code/make_figs.py \
  > out/tufte_lint.txt 2>&1 || true
python3 code/make_figs.py

echo "== stage 7: runtime accounting =="
python3 code/finalize_runtime.py

echo "== stage 8: immutable checker (SHA-locked BEFORE science; RED-on-empty proven) =="
python3 check.py
