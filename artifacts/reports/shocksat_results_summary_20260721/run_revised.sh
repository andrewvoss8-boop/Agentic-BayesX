#!/usr/bin/env bash
set -euo pipefail

workspace="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$workspace/../../.." && pwd)"
system_python="/usr/bin/python3"
bundled_python="/Users/avoss/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
documents_root="/Users/avoss/.codex/plugins/cache/openai-primary-runtime/documents/26.715.12143/skills/documents"

cd "$repo"

"$system_python" "$workspace/code/make_summary_figures.py"
"$system_python" ".agents/skills/tufte-data-graphics/scripts/tufte_lint.py" \
  "$workspace/code/make_summary_figures.py" \
  > "$workspace/qa/revised/tufte_lint.txt"
"$bundled_python" "$workspace/code/make_report_revised.py"
"$bundled_python" "$documents_root/scripts/a11y_audit.py" \
  "$workspace/ShockSat_results_summary_revised.docx" \
  > "$workspace/qa/revised/a11y_audit.txt"
"$bundled_python" "$documents_root/scripts/images_audit.py" \
  "$workspace/ShockSat_results_summary_revised.docx" \
  > "$workspace/qa/revised/images_audit.txt"
"$bundled_python" "$documents_root/scripts/style_lint.py" \
  "$workspace/ShockSat_results_summary_revised.docx" \
  > "$workspace/qa/revised/style_lint.txt"
env TMPDIR=/private/tmp "$bundled_python" "$documents_root/render_docx.py" \
  "$workspace/ShockSat_results_summary_revised.docx" \
  --output_dir "$workspace/qa/revised/render_final" --emit_pdf
"$bundled_python" "$workspace/code/check_revised_summary.py"
