#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=.
export PYTHONPYCACHEPREFIX=/private/tmp/agentic_bayesx_pycache
python3 scripts/sequential_vibe_modal_flight_setup.py
python3 tests/test_sequential_vibe_modal_flight_setup.py

