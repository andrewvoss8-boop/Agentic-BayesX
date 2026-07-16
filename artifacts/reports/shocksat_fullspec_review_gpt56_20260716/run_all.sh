#!/bin/bash
set -e
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

python3 audit_recompute.py
python3 fim_sensitivity.py
python3 ../shocksat_full_spectrum_frf_repair_20260716/collect_fixed.py
python3 ../shocksat_full_spectrum_frf_repair_20260716/check.py
python3 check_review.py
