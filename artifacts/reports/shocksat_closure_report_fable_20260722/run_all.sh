#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
DOC_SKILL="/Users/avoss/.codex/plugins/cache/openai-primary-runtime/documents/26.715.12143/skills/documents"
START="$(date +%s)"

cd "$REPO"
shasum -a 256 -c "$HERE/CHECKER.sha256"
MPLCONFIGDIR="${TMPDIR:-/tmp}/shocksat_closure_fable_mpl" python3 "$HERE/code/build_report_fable.py"
python3 "$REPO/.agents/skills/tufte-data-graphics/scripts/tufte_lint.py" "$HERE/code/build_report_fable.py" > "$HERE/qa/tufte_lint.txt"
python3 "$DOC_SKILL/render_docx.py" "$HERE/ShockSat_Bayesian_FEM_StatFEM_closure_brief_fable.docx" --output_dir "$HERE/qa/render" --emit_pdf
python3 "$DOC_SKILL/scripts/a11y_audit.py" "$HERE/ShockSat_Bayesian_FEM_StatFEM_closure_brief_fable.docx" --out_json "$HERE/qa/a11y_audit.json"
python3 "$DOC_SKILL/scripts/style_lint.py" "$HERE/ShockSat_Bayesian_FEM_StatFEM_closure_brief_fable.docx" --json "$HERE/qa/style_lint.json"
python3 "$DOC_SKILL/scripts/images_audit.py" "$HERE/ShockSat_Bayesian_FEM_StatFEM_closure_brief_fable.docx" > "$HERE/qa/images_audit.txt"
python3 "$DOC_SKILL/scripts/heading_audit.py" "$HERE/ShockSat_Bayesian_FEM_StatFEM_closure_brief_fable.docx" > "$HERE/qa/heading_audit.txt"

END="$(date +%s)"
python3 -c 'import json,sys; s=int(sys.argv[1]); e=int(sys.argv[2]); p=sys.argv[3]; open(p,"w").write(json.dumps({"active_runtime_s":e-s,"elapsed_wallclock_s":e-s,"scope":"document build, render, and checks only"},indent=2)+"\n")' "$START" "$END" "$HERE/runtime.json"
python3 "$HERE/check.py"
