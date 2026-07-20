#!/usr/bin/env python3
"""Q + H legs for a finalist package: reuse the completed run's qoi.py (net-CG statFEM F(k) coverage + the
leave-modes-out honesty audit) in OUR workspace. Aliases our post_<cid>.npz -> theta_post_<cid>.npz (the name
qoi expects). The Q-leg spectra use the netcg convention zeta=1% (secondary QOI; labeled).
Usage: python3 code/run_qoi.py <package_cid>"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femdamp as D           # sets F.WS -> ours, path order
import femlib as F            # noqa: F401
WS = D.WS
cid = sys.argv[1]
p = np.load(os.path.join(WS, "data", f"post_{cid}.npz"), allow_pickle=True)
np.savez(os.path.join(WS, "data", f"theta_post_{cid}.npz"),
         theta_post=np.asarray(p["theta_post"]), free_names=np.asarray(p["free_names"]))
import qoi  # noqa: E402  (executes Q+H, writes out/qoi_<cid>.json + out/honesty_<cid>.json)
qoi.run_q_h(cid)
