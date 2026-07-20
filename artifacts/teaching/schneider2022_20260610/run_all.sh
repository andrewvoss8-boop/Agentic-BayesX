#!/usr/bin/env bash
# Reproduce the full Schneider et al. (2022) teaching deck from scratch.
# Regenerates all figures (figures/), animations (gifs/), and the PowerPoint.
# Requires: python3 with numpy, scipy, matplotlib, pillow, python-pptx.
set -euo pipefail
cd "$(dirname "$0")/scripts"

echo "[1/4] Part 1 - rational surrogate"
python3 part1_rational_surrogate.py
echo "[2/4] Part 2 - likelihood"
python3 part2_likelihood.py
echo "[3/4] Part 3 - BUS-SuS"
python3 part3_bus_sus.py
echo "[4/4] assembling PowerPoint"
python3 build_pptx.py

echo "DONE. Outputs:"
echo "  figures/  ($(ls -1 ../figures | wc -l | tr -d ' ') PNG)"
echo "  gifs/     ($(ls -1 ../gifs | wc -l | tr -d ' ') GIF)"
echo "  schneider2022_teaching.pptx"
