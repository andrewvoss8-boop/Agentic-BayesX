#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=.
export PYTHONPYCACHEPREFIX=/private/tmp/agentic_bayesx_pycache

python3 scripts/conical_shell_statfem_ladder.py
python3 tests/test_conical_shell_statfem_ladder.py
