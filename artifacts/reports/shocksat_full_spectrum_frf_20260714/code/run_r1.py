import json, sys, time
sys.path.insert(0, "code")
import loop_wide as L
t0=time.time()
for s in json.load(open("out/agent_specs_r1.json"))["specs"]:
    try: L.score_candidate(s, "agent", 1)
    except Exception as e: print("AGENT ERR", s["cid"], e, flush=True)
L.random_round(1, 6, 20260715)
print("ROUND1_DONE %.0fs"%(time.time()-t0))
