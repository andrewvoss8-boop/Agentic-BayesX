#!/usr/bin/env python3
"""Reduced-basis spot check (D2/D7): for a split/scale candidate scored in the inherited basis, solve the
FULL model at its θ_MAP and compare in-band frequencies vs the reduced prediction. Requirement: <=0.3%
max abs relative error on in-band modes, else the reduced dev scores are NOT trusted (candidate demoted).
Writes out/spot_check_<cid>.json. Usage: python3 code/spot_check.py <cid>
"""
import json, os, sys, time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F
import actions as ACT
import score as SC

cid = sys.argv[1]
spec = json.load(open(os.path.join(F.WS, "out", "candidate_specs", f"{cid}.json")))
pkg = F.Package.load(cid)
theta = SC.theta_map_cached(pkg)
names = list(pkg.free_names)

# rebuild the candidate's FULL-space blocks (same code path as build_candidate, stopping before packaging)
m = F.load_model()
ops = sorted(spec["ops"], key=lambda o: ACT.ORDER[o["op"]])
assert not any(o["op"] in ("refine", "thickness", "rbe2_soften") for o in ops), \
    "spot check is for reduced-basis (split/scale) candidates only"
NDOF = 6 * len(m["gids"])
pid_K = {p: sp.load_npz(os.path.join(F.MATD, f"K_shell_{p}.npz")) for p in ACT.SHELL_PIDS}
extra = {}
scale_f = {g: 1.0 for g in F.GNAMES}
for op in ops:
    if op["op"] == "split":
        p = op["pid"]
        qm, tm = ACT.rule_mask(m, p, op["rule"])
        Ksub, _, _ = F.assemble_shell(m, p, qmask=qm, tmask=tm)
        name = op.get("name", f"s_{p}")
        extra[name] = extra.get(name, sp.csr_matrix((NDOF, NDOF))) + Ksub
        pid_K[p] = pid_K[p] - Ksub
    elif op["op"] == "scale":
        scale_f[op["group"]] *= float(op["factor"])
blocks = {}
for g in F.GNAMES:
    Kg = None
    for pref in F.GROUPS[g]:
        Kp = pid_K[int(pref.split("_")[1])] if pref.startswith("shell_") else \
            sp.load_npz(os.path.join(F.MATD, f"K_{pref}.npz"))
        Kg = Kp if Kg is None else Kg + Kp
    blocks[g] = Kg * scale_f[g] if scale_f[g] != 1.0 else Kg
blocks.update(extra)
th_of = dict(zip(names, theta))
Ktheta = sp.load_npz(os.path.join(F.MATD, "K_bush_99.npz")).copy()
for gname, Kb in blocks.items():
    Ktheta = Ktheta + th_of[gname] * Kb
T = sp.load_npz(os.path.join(F.MATD, "T.npz"))
M = sp.load_npz(os.path.join(F.MATD, "M.npz"))
t0 = time.time()
Kr = (T.T @ (Ktheta @ T)).tocsc()
Mr = (T.T @ (M @ T)).tocsc()
lam, _ = eigsh(Kr, k=60, M=Mr, sigma=F.SIGMA_SHIFT, which="LM")
lam = np.sort(lam)
F.log_eigensolve("vgate_spot", cid, Kr.shape[0], time.time() - t0)
f_full = np.sqrt(np.clip(lam[6:], 0, None)) / (2 * np.pi)
f_red, _ = pkg.modes(theta)
n = min(len(f_full), int(np.sum(f_red <= 300.0)))
rel = np.abs(f_red[:n] / f_full[:n] - 1.0)
out = {"cid": cid, "theta_map": {g: round(float(t), 4) for g, t in th_of.items()},
       "n_modes": int(n), "max_rel_err": float(rel.max()), "median_rel_err": float(np.median(rel)),
       "pass_0p3pct": bool(rel.max() <= 0.003), "solve_s": round(time.time() - t0, 1)}
json.dump(out, open(os.path.join(F.WS, "out", f"spot_check_{cid}.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
