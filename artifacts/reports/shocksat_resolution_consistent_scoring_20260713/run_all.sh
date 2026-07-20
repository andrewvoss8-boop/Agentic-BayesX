#!/bin/bash
# One-command replay — ShockSat resolution-consistent FRF scoring (20260713).
# All steps are resumable (cached spectra / logged scores are skipped on rerun).
# NOTE: gate_w.py streams ~245 MB .mat extractions one at a time from Test07_ImpactHammer_990x.zip
# (repo root) and deletes each after processing (D7 disk protocol).
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1
python3 code/gate_k.py
python3 code/gate_w.py
python3 code/gate_r.py
python3 code/arms.py
python3 code/vaultrc.py freeze
python3 code/vaultrc.py grade
python3 code/verdicts.py
python3 code/make_figs.py
python3 check.py
