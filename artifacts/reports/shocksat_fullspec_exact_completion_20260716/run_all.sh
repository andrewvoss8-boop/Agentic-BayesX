#!/bin/bash
# One-command replay — EXACT-EVIDENCE COMPLETION for the full-spectrum FRF study (20260716).
#
# Every stage is RESUMABLE: artifacts already present are skip-loaded, so a killed/relaunched run does not
# start over (per-fold MAPs in out/armC_exact_maps/, per-candidate records in out/rerank_partial/, enriched
# packages in data/packages_wide/). Exits non-zero only on RED (checker convention).
#
# ISOLATION: this card writes ONLY inside this workspace. The study/review/repair workspaces are read-only
# inputs; code/_common.py rebinds every study write target (PKGD, log_eig, score log) into here, and the
# study's base packages are reached through symlinks. check.py G02 re-verifies all 90 read-only inputs
# against REUSED_code.sha256 on every run.
#
# RUNTIME: T2 is the long pole — ~28 SERIAL sparse shift-invert eigensolves (k=200, 399510 DOF) at ~530 s
# each on the 16 GB Mac ≈ 4.1 h. Run them serially: parallel eigensolves thrash to swap (study D11).
# The original run executed T2 detached (nohup ... & disown, see logs/); it runs foreground here for
# replay fidelity.
#
# NO SAMPLER: deterministic MAP refits + exact eigensolves + scoring only (decisions_log D0). NUTS/HMC
# remains the project default for Bayesian updating; this card makes no posterior claim.
# NO VAULT: dev drives only (m_xpos_990x, m_zpos_990z, m_ypos_990y, m_zpos_900z). +XY is never read.
set -e
cd "$(dirname "$0")"
# Pin BLAS threads: small dense eigh/posterior math thrashes with multi-thread BLAS (compute protocol).
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

echo "== T1: honest arm-C exact score (4 per-fold shape-MAP refits, leakage-free) =="
python3 code/armC_exact.py

echo "== T2: exact re-rank of ALL 28 loop candidates (~28 eigensolves, ~4-5 h SERIAL) =="
# ONE candidate per python process (decisions_log D4). Running all 28 in a single long-lived process
# thrashed this 16 GB box into swap by candidate ~18 (a 530 s eigensolve took 11,198 s = 21x). A fresh
# interpreter per candidate bounds memory to one candidate's working set. The driver loops until every
# candidate has a record, then runs the aggregation pass. Fully resumable.
bash code/run_rerank_serial.sh

echo "== T3a: corrected, finiteness-hardened verdicts =="
python3 code/verdicts_final.py

echo "== T3b: corrected figures (tufte skill applied; lint + legibility QA) =="
python3 "../../../.claude/skills/tufte-data-graphics/scripts/tufte_lint.py" code/make_figs.py \
  > out/tufte_lint.txt 2>&1 || true
python3 code/make_figs.py

echo "== runtime accounting =="
python3 code/finalize_runtime.py

echo "== checker (immutable, SHA-locked before any science) =="
python3 check.py
