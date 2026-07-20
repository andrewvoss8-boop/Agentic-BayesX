#!/usr/bin/env bash
# Card D — chain: wait for the campaign, then dish-refine solve, then aggregate+figure.
set -uo pipefail
cd "$(dirname "$0")"
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 OPENBLAS_NUM_THREADS=1
echo "== waiting for campaign to finish =="
while pgrep -f run_campaign.sh >/dev/null; do sleep 30; done
echo "== campaign done; running dish-refined assemble+solve =="
if [ ! -f out/dish_refined/nominal_mac_table.json ]; then
  bash run_dish_refined.sh || echo "DISH REFINE FAILED"
fi
echo "== aggregate before/after =="
python3 code/aggregate.py
echo "== figure =="
python3 code/make_figure.py
echo "== FINISH DONE =="
