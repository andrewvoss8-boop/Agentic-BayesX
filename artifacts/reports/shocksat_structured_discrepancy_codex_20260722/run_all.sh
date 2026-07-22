#!/usr/bin/env bash
set -euo pipefail

WS="$(cd "$(dirname "$0")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
export OMP_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1

cd "$WS"
if [[ ! -f source_manifest.json ]]; then
  "$PYTHON_BIN" code/freeze.py
fi
"$PYTHON_BIN" code/known_answers.py
"$PYTHON_BIN" code/synthetic.py
"$PYTHON_BIN" code/decide.py
if "$PYTHON_BIN" -c 'import json; print(json.load(open("automatic_decision.json"))["chosen_terminal_path"] != "STOP_SYNTHETIC")' | grep -q True; then
  "$PYTHON_BIN" code/measured.py
  "$PYTHON_BIN" code/decide.py
fi
"$PYTHON_BIN" code/finalize.py
"$PYTHON_BIN" check.py --report out/checker_report.json
