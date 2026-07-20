import json, sys, time
sys.path.insert(0, "code")
import loop_wide as L
t0=time.time()
for s in json.load(open("out/agent_specs_r3.json"))["specs"]:
    try: L.score_candidate(s, "agent", 3)
    except Exception as e: print("AGENT ERR", s["cid"], e, flush=True)
L.random_round(3, 4, 20260717)
print("ROUND3_DONE %.0fs"%(time.time()-t0))
