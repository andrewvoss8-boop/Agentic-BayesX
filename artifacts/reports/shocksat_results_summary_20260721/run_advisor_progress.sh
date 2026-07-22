#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PY="/Users/avoss/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
PLOT_PY="/usr/bin/python3"
DOC_SKILL="/Users/avoss/.codex/plugins/cache/openai-primary-runtime/documents/26.715.12143/skills/documents"

cd "$ROOT_DIR"
"$PLOT_PY" code/make_agentic_remodeling_flowchart.py
"$PY" code/make_advisor_progress_report.py
"$PY" "$DOC_SKILL/render_docx.py" ShockSat_StatFEM_progress_and_closure_update.docx \
  --output_dir qa/advisor_progress_render_v5 --emit_pdf --verbose
"$PY" "$DOC_SKILL/scripts/a11y_audit.py" ShockSat_StatFEM_progress_and_closure_update.docx \
  --out_json qa/advisor_progress/a11y_audit.json
"$PY" "$DOC_SKILL/scripts/style_lint.py" ShockSat_StatFEM_progress_and_closure_update.docx \
  --json qa/advisor_progress/style_lint.json
"$PY" "$DOC_SKILL/scripts/images_audit.py" ShockSat_StatFEM_progress_and_closure_update.docx \
  > qa/advisor_progress/images_audit.txt
"$PY" "$DOC_SKILL/scripts/heading_audit.py" ShockSat_StatFEM_progress_and_closure_update.docx \
  > qa/advisor_progress/heading_audit.txt
"$PY" code/check_advisor_progress.py
