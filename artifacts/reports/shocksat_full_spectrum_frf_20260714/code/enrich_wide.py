#!/usr/bin/env python3
"""enrich_wide — exact-at-theta_MAP basis rebuild for a freeze-set candidate (D22; card §5 exact-basis rule).

theta_MAP is far from 1 (A0_wide: joints 0.47, cross_beam 1.46) so the theta=1 reduced basis mispredicts the
most-sensitive modes by up to ~3.7% -> the theta=1 reduced-basis DEV scores are SCREENING; vault/delivery
numbers must use a basis solved AT theta_MAP. This solves K(theta_MAP) fully (k=K_OWN) ONCE, projects the
group blocks onto that eigenbasis with theta_MAP FOLDED IN, so pkg.modes(ones) reproduces the exact solve
(self-consistency ~0%). Re-scoring is then done at theta = ones(9). Saved as <out_cid>.npz in packages_wide.

Usage: enrich_wide.py <base_cid> <theta_json_list> <out_cid>"""
import json, os, sys, time
import numpy as np
from scipy.sparse.linalg import eigsh

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402
import wide_candidates as WC                   # noqa: E402
F = WP.F
ACT = WC.ACT


def enrich(base_cid, theta, out_cid, k=WC.K_OWN):
    if os.path.exists(os.path.join(WC.PKGD, f"{out_cid}.npz")):
        return WP.load(out_cid)
    t0 = time.time()
    spec_p = os.path.join(WC.SPECD, f"{base_cid}.json")
    if os.path.exists(spec_p) and json.load(open(spec_p)).get("ops"):
        m, blocks = ACT.build_candidate(json.load(open(spec_p)), tag_track="enrich", blocks_only=True)
    else:
        m = F.load_model(); blocks = F.baseline_blocks(m)
    M = blocks.pop("__M__")
    pkg0 = WP.load(base_cid)
    th_of = dict(zip(pkg0.free_names, np.asarray(theta, float)))
    Kth = blocks["_fixed_bush99"].copy()
    for g, Kb in blocks.items():
        if g != "_fixed_bush99":
            Kth = Kth + th_of[g] * Kb
    T, keep = F.build_T(m)
    Kr = (T.T @ (Kth @ T)).tocsc(); Mr = (T.T @ (M @ T)).tocsc()
    lam, V = eigsh(Kr, k=k, M=Mr, sigma=F.SIGMA_SHIFT, which="LM")
    idx = np.argsort(lam); lam, V = lam[idx], V[:, idx]
    WC.log_eig("enrich_at_thetaMAP", out_cid, Kr.shape[0], time.time() - t0)
    n_rbm = int((lam < (2 * np.pi * 10.0) ** 2).sum())
    Ve = V[:, n_rbm:]; W = np.asarray(T @ Ve)
    freqs_el = np.sqrt(np.clip(lam[n_rbm:], 0, None)) / (2 * np.pi)
    A, A_fix = {}, None
    for name, Kb in blocks.items():
        Ab = W.T @ (Kb @ W)
        if name == "_fixed_bush99":
            A_fix = Ab
        else:
            A[name] = th_of[name] * Ab                       # fold theta_MAP in -> evaluate at ones(9)
    free_names = sorted(A)
    # self-consistency: eigh of the folded reduced K vs the full-solve freqs (exact by construction)
    Kchk = A_fix + sum(A.values())
    f_red = np.sort(np.sqrt(np.clip(np.linalg.eigvalsh(Kchk), 1e-9, None)) / (2 * np.pi))
    nn = int((freqs_el <= 500).sum())
    rel = np.abs(np.sort(freqs_el)[:nn] / f_red[:nn] - 1.0)
    mm = np.load(os.path.join(F.REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1); mfreqs = np.asarray(mm["freqs"], float)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
    obs_dofs = np.load(os.path.join(F.MATD, "obs_dofs.npy")); ash_rows = W[obs_dofs, :]
    chmap = F.channels_map(); cmeta = F.cache_meta()
    all_daq = sorted(set(d for kk in cmeta for d in cmeta[kk]["daq"]) - F.BAD_DAQ)
    sens_daq, sens_rows = [], []
    for dq in all_daq:
        if dq not in chmap:
            continue
        pt, ax = chmap[dq]
        try:
            sens_rows.append(F.nearest_dof_row(m, W, pt, ax)); sens_daq.append(dq)
        except KeyError:
            pass
    allowed = F.participation_mask(np.array(sens_rows))
    pairs, _ = F.hungarian_pairing(freqs_el, ash_rows, live, mfreqs, msh, allowed=allowed)
    node_z = np.asarray(m["xyz"], float)[:, 2]; tray_nodes = np.where(node_z >= 55.0)[0]
    tray = np.zeros((3, W.shape[1]))
    for a in range(3):
        tray[a] = W[6 * tray_nodes + a, :].sum(0)
    d = dict(cid=out_cid, free_names=free_names, A=np.stack([A[g] for g in free_names]), A_fix=A_fix,
             freqs_el=freqs_el, n_rbm=0, lam_all=lam[n_rbm:], ash_rows=ash_rows, live=live, mfreqs=mfreqs,
             pairs=np.array([[p[0], p[1], p[2]] for p in pairs]), sens_daq=sens_daq,
             sens_rows=np.array(sens_rows), tray=tray,
             meta=json.dumps(dict(note=f"exact-at-theta_MAP enrichment of {base_cid} (D22)", r=int(W.shape[1]),
                                  base=base_cid, theta_map=list(map(float, theta)),
                                  spot_max_pct=float(rel.max() * 100))))
    for kk in F.DRIVE_KEYS + [F.VAULT_KEY]:
        d[f"drive_{kk}"] = F.drive_row(m, W, cmeta[kk]["xyz"], cmeta[kk]["axis"])
    np.savez_compressed(os.path.join(WC.PKGD, f"{out_cid}.npz"), **d)
    print(f"{out_cid}: enriched at theta_MAP, r={W.shape[1]}, self-consistency {rel.max()*100:.4f}% "
          f"({time.time()-t0:.0f}s)", flush=True)
    return WP.load(out_cid)


if __name__ == "__main__":
    enrich(sys.argv[1], json.loads(sys.argv[2]), sys.argv[3])
