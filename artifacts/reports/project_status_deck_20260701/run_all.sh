#!/usr/bin/env bash
# Project status deck 2026-07-01 — consolidation only (NO new science).
# Copies telling figures from their source workspaces (reuse_* prefix = provenance
# label; these are NOT generated outputs of this workspace) and builds the deck.
set -euo pipefail
cd "$(dirname "$0")"
ROOT=".."

NETCG="$ROOT/shocksat_netcg_method_selection_20260701/figures"
BIL="$ROOT/shocksat_bilionis_review_20260626/figures"

mkdir -p figures slides

# --- reused figures (source workspace -> local provenance-prefixed copy) ---
cp "$NETCG/fig_delivery_netcg_bands.png"  figures/reuse_netcg_delivery_bands.png
cp "$NETCG/fig_stage0_qoi_trust.png"      figures/reuse_netcg_stage0_qoi_trust.png
cp "$NETCG/fig_pretest.png"               figures/reuse_netcg_pretest.png
cp "$NETCG/fig_learned_statfem.png"       figures/reuse_netcg_learned_statfem.png
cp "$BIL/fig_wide_ci.png"                 figures/reuse_bil_wide_ci.png
cp "$BIL/fig_combine_best.png"            figures/reuse_bil_combine_best.png
cp "$BIL/reuse_residual_map.png"          figures/reuse_bil_residual_map.png
cp "$BIL/reuse_consistency_money.png"     figures/reuse_bil_consistency_money.png

# 2026-07-02 revision: rehearsal money figure (supersedes the §9 analytic curve on slide 17)
cp "$ROOT/plate_test_rehearsal_20260701/figures/fig_buydown_rehearsed.png" figures/reuse_rehearsal_buydown.png

# --- build + QA ---
T0=$(date +%s)
python3 code/make_deck.py
python3 code/qa_deck.py
T1=$(date +%s)
python3 - "$T0" "$T1" <<'EOF'
import json, sys
json.dump({"task": "project_status_deck_20260701 (consolidation; no new science)",
           "active_seconds": int(sys.argv[2]) - int(sys.argv[1]),
           "detached_jobs": None, "samplers_run": "none (deck build only)"},
          open("runtime.json", "w"), indent=1)
EOF
echo "OK: slides/project_status_20260701.pptx"