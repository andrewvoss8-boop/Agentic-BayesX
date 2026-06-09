#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
python3 artifacts/reports/shocksat_statfem_runner_20260609/scripts/shocksat_runner.py
