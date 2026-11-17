#!/usr/bin/env bash
# Network-gated continuation of the burst-survey foundation check.
#   bash gated_run.sh                      probe NASA; if reachable fetch tiers 0, 1, 2, 4 and run the
#                                          pre-registered tier-4 scoring plus first-look probes
#   WITH_TIME_HISTORIES=1 bash gated_run.sh  also fetch the three burst time-history files (589 MB)
# Downloaded NASA files go to BURST_DATA_DIR (default ~/.cache/shocksat_burst_survey), outside the
# repository, and are never committed. Exit codes: 0 done, 2 host not reachable (status written to
# logs/gate_status.json), 3 archive changed or a member failed its CRC check.
set -uo pipefail
WS=$(cd "$(dirname "$0")" && pwd)
PY=${PYTHON:-python3}
DATA=${BURST_DATA_DIR:-$HOME/.cache/shocksat_burst_survey}
URL=https://mediaex-server.larc.nasa.gov/shocksat/FEM_and_CAD.zip
mkdir -p "$WS/logs" "$DATA"
now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
"$PY" -I "$WS/code/zipfetch.py" probe "$URL" > "$WS/logs/gate_probe.json" 2> "$WS/logs/gate_probe.err"
rc=$?
if [ $rc -ne 0 ]; then
  printf '{"status": "BLOCKED", "host": "mediaex-server.larc.nasa.gov", "checked_utc": "%s", "exit_code": %d, "detail": %s}\n' \
    "$(now)" "$rc" "$("$PY" -c 'import json,sys;print(json.dumps(open(sys.argv[1]).read().strip()[:300]))' "$WS/logs/gate_probe.err")" > "$WS/logs/gate_status.json"
  cat "$WS/logs/gate_status.json"; exit 2
fi
"$PY" -I - "$WS/logs/gate_probe.json" <<'P' || exit 3
import json, sys
d = json.load(open(sys.argv[1]))
ok = d["content_length"] == 2025227962
print("archive bytes", d["content_length"], "etag", d["etag"], "unchanged since 2026-06-09" if ok else "CHANGED: rebuild the listing before fetching")
sys.exit(0 if ok else 3)
P
"$PY" -I "$WS/code/freeze_predictions.py" --verify || { echo "frozen predictions do not reproduce; stopping"; exit 3; }
TIERS="tier0_documents_and_shapes tier1_plans_and_reduced_models tier2_burst_frf_file tier4_frf_verification_plots"
[ "${WITH_TIME_HISTORIES:-0}" = 1 ] && TIERS="$TIERS tier3_burst_time_histories"
for t in $TIERS; do
  rx=$("$PY" -I -c "import json,sys;print([x['regex'] for x in json.load(open(sys.argv[1]))['tiers'] if x['tier']==sys.argv[2]][0])" "$WS/out/fetch_plan.json" "$t")
  "$PY" -I "$WS/code/zipfetch.py" fetch "$URL" --match "$rx" --dest "$DATA" --json "$WS/logs/fetch_$t.json" || exit 3
done
C="$DATA/FEM/Correlation"
"$PY" -I "$WS/code/tier4_study.py" --plots "$C/FRF_Verification" > "$WS/logs/tier4_stdout.txt" 2>&1
T4=$?
for f in "$C"/Modal_Test_Data_Use_in_Correlation2021/FINAL_FF/*.afu "$C"/Modal_Test_Data_Use_in_Correlation2021/TH/*.ati; do
  [ -f "$f" ] && "$PY" -I "$WS/code/adf_probe.py" "$f" --json "$WS/out/adf_probe_$(basename "$f" | tr ' ' '_').json" > /dev/null
done
find "$C" -name '*.xlsx' -print0 | while IFS= read -r -d '' x; do
  "$PY" -I "$WS/code/xlsx_dump.py" "$x" --out "$WS/out/xlsx_$(basename "$x" .xlsx | tr ' ' '_').json" > /dev/null
done
ST=FETCHED; [ $T4 -ne 0 ] && ST=FETCHED_SCORING_FAILED
printf '{"status": "%s", "checked_utc": "%s", "tiers": "%s", "data_dir": "%s", "tier4_exit": %d}\n' "$ST" "$(now)" "$TIERS" "$DATA" "$T4" > "$WS/logs/gate_status.json"
cat "$WS/logs/gate_status.json"
