#!/bin/bash
set -e
cd "$(dirname "$0")"

python3 collect_fixed.py
python3 check.py
