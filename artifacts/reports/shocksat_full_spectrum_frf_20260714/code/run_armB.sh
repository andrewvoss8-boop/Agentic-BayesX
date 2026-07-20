#!/bin/bash
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=4 VECLIB_MAXIMUM_THREADS=4
for FOLD in m_xpos_990x m_zpos_990z m_ypos_990y m_zpos_900z; do
  python3 code/arm_b_nuts.py "$FOLD"            || exit 1
  python3 code/arm_b_nuts.py "$FOLD" --theta-only || exit 1
done
echo "ARMB_ALL_DONE"
