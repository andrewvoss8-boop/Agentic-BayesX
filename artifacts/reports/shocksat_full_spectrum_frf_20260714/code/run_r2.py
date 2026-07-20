import json, sys, time
sys.path.insert(0, "code")
import loop_wide as L
t0=time.time()
for s in json.load(open("out/agent_specs_r2.json"))["specs"]:
    try: L.score_candidate(s, "agent", 2)
    except Exception as e: print("AGENT ERR", s["cid"], e, flush=True)
L.random_round(2, 4, 20260716)
# update loop_best
best,bv=None,-9
for line in open("out/query_log.jsonl"):
    r=json.loads(line)
    if r.get("track")=="agent" and (r.get("sub200_P1p") or -9)>bv: best,bv=r["cid"],r["sub200_P1p"]
json.dump({"cid":best,"sub200_P1p":bv}, open("out/loop_best.json","w"))
print("ROUND2_DONE %.0fs best=%s %.4f"%(time.time()-t0,best,bv))
