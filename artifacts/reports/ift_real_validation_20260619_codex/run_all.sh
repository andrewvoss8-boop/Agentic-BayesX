#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
START=$(date +%s)
PY="${PYTHON:-../../../.venv_nuts/bin/python}"
if [ ! -x "$PY" ]; then
  PY="python3"
fi
NODE="${NODE:-/Users/avoss/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node}"
"$PY" code/scorecard.py
"$PY" code/discretization_sensitivity.py
"$PY" code/make_figures.py
python3 ../../../.claude/skills/tufte-data-graphics/scripts/tufte_lint.py code/make_figures.py > logs/tufte_make_figures.txt
"$PY" code/image_qa.py > logs/image_qa.txt
"$NODE" code/make_deck.mjs
"$PY" code/deck_contact_sheet.py
"$PY" code/write_packet.py
"$PY" check.py
END=$(date +%s)
"$PY" - <<PY
import json, pathlib
p=pathlib.Path("runtime.json")
old={}
if p.exists():
    try:
        old=json.loads(p.read_text())
    except Exception:
        old={}
active=float(old.get("active_runtime_s", 0.0))
wall=float($END - $START)
old.update({"active_runtime_s": active + wall, "elapsed_wallclock_s": max(active + wall, wall), "last_replay_s": wall})
p.write_text(json.dumps(old, indent=2))
PY
