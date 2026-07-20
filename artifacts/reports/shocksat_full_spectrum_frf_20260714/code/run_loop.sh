#!/bin/bash
# run_loop.sh — arm D remodel loop replay (agent + equal-budget random control).
# Agent proposals per round live in out/agent_specs_r{1,2,3}.json (written by the runner WITH the
# diagnosis→proposal link table in out/round_summary_r{N}.md). Random control: same grammar, seeded.
set -e
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1

for R in 1 2 3; do
  python3 code/diag_wide.py "$R" "$(python3 -c "
import json,os
p='out/loop_best.json'
print(json.load(open(p))['cid'] if os.path.exists(p) else 'A0_wide')")"
  # agent proposals for this round must exist (written from the diagnosis)
  test -f "out/agent_specs_r$R.json" || { echo "agent_specs_r$R.json missing (runner writes it from the diagnosis)"; exit 2; }
  python3 - "$R" <<'EOF'
import json, sys, os
sys.path.insert(0, "code")
import loop_wide as L
rnd = int(sys.argv[1])
specs = json.load(open(f"out/agent_specs_r{rnd}.json"))["specs"]
for s in specs:
    L.score_candidate(s, "agent", rnd)
# keep the running best for next round's diagnosis
recs = {}
for line in open("out/query_log.jsonl"):
    r = json.loads(line)
    if r.get("track") == "agent" and r.get("sub200_P1p") is not None:
        recs[r["cid"]] = r["sub200_P1p"]
if recs:
    best = max(recs, key=recs.get)
    json.dump({"cid": best, "sub200_P1p": recs[best]}, open("out/loop_best.json", "w"), indent=1)
EOF
  python3 code/loop_wide.py random_round "$R" "$(python3 -c "
import json;print(len(json.load(open('out/agent_specs_r$R.json'))['specs']))")" $((20260714 + R))
done
echo "loop complete"
