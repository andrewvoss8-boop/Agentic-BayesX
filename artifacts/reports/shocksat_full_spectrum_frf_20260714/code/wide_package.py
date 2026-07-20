#!/usr/bin/env python3
"""wide_package — build the wide-band exact-basis package for the INHERITED model from the full_eig
theta=1 eigenbasis (card §5). Same package format as femlib.Package (A blocks, sens/drive/tray/ash rows,
FROZEN Hungarian pairing vs the 33 survey modes) but saved in THIS workspace (data/packages_wide/).

Basis = ALL full-order modes to 1600 Hz at theta=1 (from out/full_eig_V.npy). Within-basis eigh at any
theta gives the candidate modes; the exact-basis rule (Gate 4) is enforced separately by spot_check_wide
(full solve at each freeze-set candidate's theta_MAP, <=0.3%). Reuses femlib helpers READ-ONLY; nothing is
written outside this workspace.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.abspath(os.path.join(WS, "..", "shocksat_true_remodel_loop_20260706", "code")))
import femlib as F                                  # noqa: E402  (read-only reuse)

PKGD = os.path.join(WS, "data", "packages_wide")
os.makedirs(PKGD, exist_ok=True)


def build(cid="A0_wide"):
    t0 = time.time()
    z = np.load(os.path.join(WS, "out", "full_eig_theta1.npz"))
    V = np.load(os.path.join(WS, "out", "full_eig_V.npy"))
    freqs, n_rbm = np.asarray(z["freqs"]), int(z["n_rbm"])
    Ve = V[:, n_rbm:]                                # drop rigid-body modes
    print(f"basis: {Ve.shape[1]} elastic modes to {freqs.max():.0f} Hz (n_rbm={n_rbm})", flush=True)
    m = F.load_model()
    blocks = F.baseline_blocks(m)
    blocks.pop("__M__")                              # basis is M-orthonormal already
    T, keep = F.build_T(m)
    W = np.asarray(T @ Ve)                           # (NDOF_full, r)
    A, A_fix = {}, None
    for name, Kb in blocks.items():
        Ab = W.T @ (Kb @ W)
        if name == "_fixed_bush99":
            A_fix = Ab
        else:
            A[name] = Ab
    free_names = sorted(A)
    lam1 = (2 * np.pi * freqs[n_rbm:]) ** 2
    # observation rows (survey pairing, femlib conventions)
    mm = np.load(os.path.join(F.REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1)
    mfreqs = np.asarray(mm["freqs"], float)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
    obs_dofs = np.load(os.path.join(F.MATD, "obs_dofs.npy"))
    ash_rows = W[obs_dofs, :]
    chmap = F.channels_map(); cmeta = F.cache_meta()
    all_daq = sorted(set(d for k in cmeta for d in cmeta[k]["daq"]) - F.BAD_DAQ)
    sens_daq, sens_rows = [], []
    for dq in all_daq:
        if dq not in chmap:
            continue
        pt, ax = chmap[dq]
        try:
            sens_rows.append(F.nearest_dof_row(m, W, pt, ax))
            sens_daq.append(dq)
        except KeyError:
            pass
    allowed = F.participation_mask(np.array(sens_rows))
    freqs_el = freqs[n_rbm:]
    pairs, _ = F.hungarian_pairing(freqs_el, ash_rows, live, mfreqs, msh, allowed=allowed)
    node_z = np.asarray(m["xyz"], float)[:, 2]
    tray_nodes = np.where(node_z >= 55.0)[0]
    tray = np.zeros((3, Ve.shape[1]))
    for a in range(3):
        tray[a] = W[6 * tray_nodes + a, :].sum(0)
    d = dict(cid=cid, free_names=free_names,
             A=np.stack([A[g] for g in free_names]), A_fix=A_fix,
             freqs_el=freqs_el, n_rbm=n_rbm, lam_all=np.concatenate([np.zeros(n_rbm), lam1]),
             ash_rows=ash_rows, live=live, mfreqs=mfreqs,
             pairs=np.array([[p[0], p[1], p[2]] for p in pairs]),
             sens_daq=sens_daq, sens_rows=np.array(sens_rows), tray=tray,
             meta=json.dumps(dict(note="wide-band exact theta=1 basis from full_eig (full-spectrum card §5)",
                                  tag="wide_theta1", r=int(Ve.shape[1]))))
    for k in F.DRIVE_KEYS + [F.VAULT_KEY]:
        d[f"drive_{k}"] = F.drive_row(m, W, cmeta[k]["xyz"], cmeta[k]["axis"])
    np.savez_compressed(os.path.join(PKGD, f"{cid}.npz"), **d)
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": f"wide_package_{cid}", "active_s": round(time.time() - t0, 1)}) + "\n")
    print(f"package {cid}: r={Ve.shape[1]}, pairs={len(pairs)}, {time.time()-t0:.0f}s", flush=True)


def load(cid):
    """Local loader returning femlib.Package with drives dict (same field conventions)."""
    z = np.load(os.path.join(PKGD, f"{cid}.npz"), allow_pickle=True)
    d = {k: z[k] for k in z.files}
    d["free_names"] = [str(n) for n in d["free_names"]]
    d["cid"] = str(d["cid"])
    d["sens_daq"] = [int(x) for x in d["sens_daq"]]
    d["meta"] = json.loads(str(d["meta"]))
    d["drives"] = {k: d[f"drive_{k}"] for k in F.DRIVE_KEYS + [F.VAULT_KEY]}
    d["pairs"] = np.asarray(d["pairs"])
    return F.Package(d)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "A0_wide")
