#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

python3 code/sequential_modal_filter.py
python3 code/make_figures.py
python3 ../../../.agents/skills/tufte-data-graphics/scripts/tufte_lint.py code/make_figures.py > out/tufte_lint.txt
python3 check.py

