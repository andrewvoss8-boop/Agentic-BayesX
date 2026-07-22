#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY="/Users/avoss/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
PLOT_PY="/usr/bin/python3"
DOC_SKILL="/Users/avoss/.codex/plugins/cache/openai-primary-runtime/documents/26.715.12143/skills/documents"
TUFTE_LINT="/Users/avoss/Downloads/bayesX/Agentic BayesX/.agents/skills/tufte-data-graphics/scripts/tufte_lint.py"
DOCX="ShockSat_Bayesian_FEM_and_StatFEM_progress_update_working_twin_revision.docx"

cd "$ROOT_DIR"
"$PLOT_PY" code/make_agentic_remodeling_flowchart.py
"$PLOT_PY" code/make_working_twin_frf_comparison.py
"$PY" code/make_advisor_audit_metrics.py
mkdir -p qa/advisor_progress_working_twin
"$PY" "$TUFTE_LINT" code/make_working_twin_frf_comparison.py \
  > qa/advisor_progress_working_twin/tufte_lint_predictive_bands.txt
"$PY" code/make_advisor_progress_report.py
"$PY" "$DOC_SKILL/render_docx.py" "$DOCX" \
  --output_dir qa/advisor_progress_working_twin_render_final --emit_pdf --verbose
"$PY" "$DOC_SKILL/scripts/a11y_audit.py" "$DOCX" \
  --out_json qa/advisor_progress_working_twin/a11y_audit.json
"$PY" "$DOC_SKILL/scripts/style_lint.py" "$DOCX" \
  --json qa/advisor_progress_working_twin/style_lint.json
"$PY" "$DOC_SKILL/scripts/images_audit.py" "$DOCX" \
  > qa/advisor_progress_working_twin/images_audit.txt
"$PY" "$DOC_SKILL/scripts/heading_audit.py" "$DOCX" \
  > qa/advisor_progress_working_twin/heading_audit.txt
"$PY" code/check_advisor_progress_bayesian.py
