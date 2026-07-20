#!/usr/bin/env python3
"""Exact-at-θ_MAP rebuild for an OWN-SPACE candidate (D22; e.g. a04 thickness): rebuild its full blocks
(same deterministic path as build_candidate), solve ITS K(θ_MAP) full-order once, and package in that basis
(exact at the evaluated θ_MAP by construction; validation reported). Usage: enrich_own.py <cid>"""
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
th_of = dict(zip(pkg.free_names, theta))
m, blocks = ACT.build_candidate(dict(spec), tag_track="enrich", blocks_only=True)
M = blocks.pop("__M__")
Ktheta = blocks["_fixed_bush99"].copy()
for g, Kb in blocks.items():
    if g != "_fixed_bush99":
        Ktheta = Ktheta + th_of[g] * Kb
T, keep = F.build_T(m)
t0 = time.time()
Kr = (T.T @ (Ktheta @ T)).tocsc()
Mr = (T.T @ (M @ T)).tocsc()
lam, V = eigsh(Kr, k=F.NMODES, M=Mr, sigma=F.SIGMA_SHIFT, which="LM")
idx = np.argsort(lam); lam = lam[idx]; V = V[:, idx]
F.log_eigensolve("vgate_spot", f"{cid}_enrich", Kr.shape[0], time.time() - t0)
Ve = V[:, 6:]
W = np.asarray(T @ Ve)
A = {}
A_fix = None
for g, Kb in blocks.items():
    Ab = W.T @ (Kb @ W)
    if g == "_fixed_bush99":
        A_fix = Ab
    else:
        A[g] = Ab
free_names = sorted(A)
# validation at θ_MAP (exact by construction)
K_at = A_fix + sum(th_of[g] * A[g] for g in free_names)
lam_red = np.sort(np.linalg.eigvalsh(K_at))
f_full = np.sqrt(np.clip(lam[6:], 0, None)) / (2 * np.pi)
f_red = np.sqrt(np.clip(lam_red, 1e-9, None)) / (2 * np.pi)
n = int(np.sum(f_full <= 300.0))
rel = np.abs(f_red[:n] / f_full[:n] - 1.0)
val = {"cid": f"{cid}_enr", "basis": "theta_MAP eigenbasis (74)", "n_modes": n,
       "max_rel_err": float(rel.max()), "pass_0p3pct": bool(rel.max() <= 0.003)}
json.dump(val, open(os.path.join(F.WS, "out", f"spot_check_{cid}_enr.json"), "w"), indent=1)
print(json.dumps(val), flush=True)
# package (basis exact at θ_MAP; θ=1 frequencies for pairing come from within-basis eigh — labeled)
K1 = A_fix + sum(A.values())
lam1, Q1 = np.linalg.eigh(K1)
freqs_el = np.sqrt(np.clip(lam1, 1e-9, None)) / (2 * np.pi)
mm = np.load(os.path.join(F.REMESH, "measured_modes.npz"), allow_pickle=True)
live = np.asarray(mm["measured"]).reshape(-1)
mfreqs = np.asarray(mm["freqs"], float)
msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
obs_dofs = np.load(os.path.join(F.MATD, "obs_dofs.npy"))
ash_rows = W[obs_dofs, :] @ Q1
chmap = F.channels_map(); cmeta = F.cache_meta()
all_daq = sorted(set(d for k in cmeta for d in cmeta[k]["daq"]) - F.BAD_DAQ)
sens_daq, sens_rows = [], []
for dq in all_daq:
    if dq not in chmap:
        continue
    pt, ax = chmap[dq]
    try:
        sens_rows.append(F.nearest_dof_row(m, W, pt, ax) @ Q1)
        sens_daq.append(dq)
    except KeyError:
        pass
allowed = F.participation_mask(np.array(sens_rows))
pairs, _ = F.hungarian_pairing(freqs_el, ash_rows, live, mfreqs, msh, allowed=allowed)
node_z = np.asarray(m["xyz"], float)[:, 2]
tray_nodes = np.where(node_z >= 55.0)[0]
r = Ve.shape[1]
tray = np.zeros((3, r))
for a in range(3):
    tray[a] = W[6 * tray_nodes + a, :].sum(0) @ Q1
d = dict(cid=f"{cid}_enr", free_names=free_names,
         A=np.stack([Q1.T @ A[g] @ Q1 for g in free_names]), A_fix=Q1.T @ A_fix @ Q1,
         freqs_el=freqs_el, n_rbm=6, lam_all=np.concatenate([np.zeros(6), lam1]),
         ash_rows=ash_rows, live=live, mfreqs=mfreqs,
         pairs=np.array([[p[0], p[1], p[2]] for p in pairs]),
         sens_daq=sens_daq, sens_rows=np.array(sens_rows), tray=tray,
         meta=json.dumps(dict(note=f"exact-at-theta_MAP rebuild of {cid} (D22)", tag="enriched_own",
                              spot=val)))
for k in F.DRIVE_KEYS + [F.VAULT_KEY]:
    d[f"drive_{k}"] = F.drive_row(m, W, cmeta[k]["xyz"], cmeta[k]["axis"]) @ Q1
np.savez_compressed(os.path.join(F.WS, "data", "packages", f"{cid}_enr.npz"), **d)
json.dump({**spec, "cid": f"{cid}_enr", "enriched_from": cid},
          open(os.path.join(F.WS, "out", "candidate_specs", f"{cid}_enr.json"), "w"), indent=1)
print(f"package {cid}_enr saved", flush=True)
