#!/usr/bin/env python3
"""Enriched-reduction rebuild for a split/scale candidate that FAILED the 0.3% spot check (D18).
Basis = M-orthonormal POD of [inherited θ=1 elastic basis ∪ candidate θ_MAP elastic modes] (enrich_basis.py
pattern). Validation: enriched-basis eigenvalues at the OLD θ_MAP vs the full solve (must be <=0.3%).
Writes package <cid>_enr + out/spot_check_<cid>_enr.json. Usage: python3 code/enrich_candidate.py <cid>
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
theta_old = SC.theta_map_cached(pkg)
names = list(pkg.free_names)
th_of = dict(zip(names, theta_old))
m = F.load_model()
ops = sorted(spec["ops"], key=lambda o: ACT.ORDER[o["op"]])
assert not any(o["op"] in ("refine", "thickness", "rbe2_soften") for o in ops), "split/scale only"
NDOF = 6 * len(m["gids"])

# candidate FULL blocks (split/scale decomposition of the stored per-PID blocks)
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
blocks["_fixed_bush99"] = sp.load_npz(os.path.join(F.MATD, "K_bush_99.npz"))

T = sp.load_npz(os.path.join(F.MATD, "T.npz"))
M = sp.load_npz(os.path.join(F.MATD, "M.npz"))
Mr = (T.T @ (M @ T)).tocsc()
Ktheta = blocks["_fixed_bush99"].copy()
for gname, Kb in blocks.items():
    if gname != "_fixed_bush99":
        Ktheta = Ktheta + th_of[gname] * Kb
t0 = time.time()
Kr_map = (T.T @ (Ktheta @ T)).tocsc()
lam_map, V_map = eigsh(Kr_map, k=F.NMODES, M=Mr, sigma=F.SIGMA_SHIFT, which="LM")
idx = np.argsort(lam_map); lam_map = lam_map[idx]; V_map = V_map[:, idx]
F.log_eigensolve("vgate_spot", f"{cid}_enrich", Kr_map.shape[0], time.time() - t0)
print(f"full solve at old theta_MAP: {time.time()-t0:.0f}s", flush=True)

# union basis + POD (enrich_basis.py pattern)
Ve0 = np.asarray(np.load(os.path.join(F.MATD, "V_keep.npy"), mmap_mode="r")[:, 6:], float)
U = np.concatenate([Ve0, V_map[:, 6:]], axis=1)
G = U.T @ (Mr @ U)
w, S = np.linalg.eigh(G)
keep = w > w.max() * 1e-9
Phi = U @ (S[:, keep] / np.sqrt(w[keep]))
r = Phi.shape[1]
print(f"enriched basis r={r}, M-orth resid "
      f"{np.abs(Phi.T @ (Mr @ Phi) - np.eye(r)).max():.2e}", flush=True)

# project blocks + rows
W = np.asarray(T @ Phi)
A = {}
A_fix = None
for name, Kb in blocks.items():
    Ab = W.T @ (Kb @ W)
    if name == "_fixed_bush99":
        A_fix = Ab
    else:
        A[name] = Ab
free_names = sorted(A)
# VALIDATION at old theta_MAP (vs the full solve just computed)
K_at = A_fix + sum(th_of[g] * A[g] for g in free_names)
lam_red = np.sort(np.linalg.eigvalsh(K_at))
f_full = np.sqrt(np.clip(lam_map[6:], 0, None)) / (2 * np.pi)
f_red = np.sqrt(np.clip(lam_red, 1e-9, None)) / (2 * np.pi)
n = int(np.sum(f_full <= 300.0))
rel = np.abs(f_red[:n] / f_full[:n] - 1.0)
val = {"cid": f"{cid}_enr", "basis_r": int(r), "n_modes": n,
       "max_rel_err": float(rel.max()), "median_rel_err": float(np.median(rel)),
       "pass_0p3pct": bool(rel.max() <= 0.003)}
json.dump(val, open(os.path.join(F.WS, "out", f"spot_check_{cid}_enr.json"), "w"), indent=1)
print(json.dumps(val), flush=True)

# package at theta=1 in the enriched basis
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
for d in all_daq:
    if d not in chmap:
        continue
    pt, ax = chmap[d]
    try:
        row = F.nearest_dof_row(m, W, pt, ax) @ Q1
        sens_rows.append(row); sens_daq.append(d)
    except KeyError:
        pass
allowed = F.participation_mask(np.array(sens_rows))
pairs, _ = F.hungarian_pairing(freqs_el, ash_rows, live, mfreqs, msh, allowed=allowed)
node_z = np.asarray(m["xyz"], float)[:, 2]
tray_nodes = np.where(node_z >= 55.0)[0]
tray = np.zeros((3, r))
for a in range(3):
    tray[a] = W[6 * tray_nodes + a, :].sum(0) @ Q1
d = dict(cid=f"{cid}_enr", free_names=free_names,
         A=np.stack([Q1.T @ A[g] @ Q1 for g in free_names]), A_fix=Q1.T @ A_fix @ Q1,
         freqs_el=freqs_el, n_rbm=6, lam_all=np.concatenate([np.zeros(6), lam1]),
         ash_rows=ash_rows, live=live, mfreqs=mfreqs,
         pairs=np.array([[p[0], p[1], p[2]] for p in pairs]),
         sens_daq=sens_daq, sens_rows=np.array(sens_rows), tray=tray,
         meta=json.dumps(dict(note=f"enriched-reduction rebuild of {cid} (D18)", tag="enriched",
                              basis_r=int(r), spot=val)))
for k in F.DRIVE_KEYS + [F.VAULT_KEY]:
    d[f"drive_{k}"] = F.drive_row(m, W, cmeta[k]["xyz"], cmeta[k]["axis"]) @ Q1
np.savez_compressed(os.path.join(F.WS, "data", "packages", f"{cid}_enr.npz"), **d)
json.dump({**spec, "cid": f"{cid}_enr", "enriched_from": cid},
          open(os.path.join(F.WS, "out", "candidate_specs", f"{cid}_enr.json"), "w"), indent=1)
print(f"package {cid}_enr saved (basis {r})", flush=True)
