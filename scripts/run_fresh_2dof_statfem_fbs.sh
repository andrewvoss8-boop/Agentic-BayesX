#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=.
export PYTHONPYCACHEPREFIX=/private/tmp/agentic_bayesx_pycache
python3 scripts/fresh_2dof_statfem_fbs.py
python3 tests/test_fresh_2dof_rerun.py
