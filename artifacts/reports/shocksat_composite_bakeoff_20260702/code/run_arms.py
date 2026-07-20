#!/usr/bin/env python3
"""Run NUTS for the six pre-registered arms (question_framing): {M0 baseline, M1 evidence winner} x {S0,S1,S2}.
Uniform retune policy (A15, parent-D9 style): any arm failing the convergence gate gets ONE retune
(warmup x2, target_accept 0.95, max_tree +1) applied identically; both attempts recorded. Resumable per arm.
Output: out/arms/<ARM>.npz + out/arms_diag.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rmodel as RMOD

WS = Path(__file__).resolve().parent.parent
t0 = time.time()


def main():
    ev = json.loads((WS / "out" / "tier3_evidence.json").read_text())
    rank = ev["headline"]["ranking"]
    m1 = next(c for c in rank if c != "baseline")     # best M1 by shape-inclusive evidence
    m1_flag = "beats_M0_on_evidence" if rank[0] == m1 else "does_NOT_beat_M0_on_evidence"
    (WS / "out" / "arms").mkdir(parents=True, exist_ok=True)
    diag_all = {}
    dpath = WS / "out" / "arms_diag.json"
    if dpath.exists():
        diag_all = json.loads(dpath.read_text())
    diag_all["m1_candidate"] = m1
    diag_all["m1_evidence_flag"] = m1_flag

    models = {"M0": RMOD.CModel("baseline"), "M1": RMOD.CModel(m1)}
    for mt in ["M0", "M1"]:
        for kind in ["S0", "S1", "S2"]:
            arm = f"{mt}{kind}"
            f_npz = WS / "out" / "arms" / f"{arm}.npz"
            if f_npz.exists() and arm in diag_all:
                print(f"[{arm}] done — skip", flush=True); continue
            m = models[mt]
            print(f"[{time.time()-t0:7.1f}s] [{arm}] NUTS ({m.cid}, nm={len(m.femk)}, np={m.np_}) ...", flush=True)
            res = RMOD.run_nuts(m, kind)
            attempts = [dict(res["diag"], attempt=1)]
            if not res["diag"]["converged"]:
                print(f"[{arm}] attempt 1 FAILED gate (R-hat {res['diag']['max_rhat']}) -> uniform retune",
                      flush=True)
                res = RMOD.run_nuts(m, kind, warmup=2000, samples=1000, target_accept=0.95,
                                    max_tree=10, seed=20260703)
                attempts.append(dict(res["diag"], attempt=2, retune="warmup2000_ta0.95_tree10"))
            save = {"theta_post": res["theta_post"]}
            for k in ("sigma_w2", "sigma_mac", "sigma_phi", "raw", "phi0"):
                if res.get(k) is not None:
                    save[k] = res[k]
            if kind == "S2":
                save["tau"] = res["tau"]
            np.savez_compressed(f_npz, **save)
            diag_all[arm] = {"cid": m.cid, "kind": kind, "attempts": attempts, "final": res["diag"],
                             "n_modes_used": int(len(m.femk)), "runtime_s": round(time.time() - t0, 1)}
            dpath.write_text(json.dumps(diag_all, indent=1))
            d = res["diag"]
            print(f"[{arm}] converged={d['converged']} R-hat {d['max_rhat']} ESS {d['min_ess']} "
                  f"div {d['divergences']}", flush=True)
    print("ALL ARMS DONE.", json.dumps({k: v["final"]["converged"] for k, v in diag_all.items()
                                        if isinstance(v, dict) and "final" in v}))


if __name__ == "__main__":
    main()
