#!/usr/bin/env python3
"""wide_candidates — candidate builder for the arm-D remodel loop (card §6 D), wide-band study.

Reuses the true-remodel action grammar READ-ONLY (actions.build_candidate(..., blocks_only=True) returns
(model_dict, full-space blocks) without writing to that workspace). Solve rule (inherited from the prior
loop, D2/D7 there; runtime tradeoff documented in decisions D7 here):
  * refine / thickness / rbe2_soften  -> OWN-SPACE sparse eigensolve, sigma=-1e3, k=K_OWN modes
    (covers ~>650 Hz; the LOOP scores sub-500 bands; the b500_ceiling cell for loop candidates is filled
    only for the FREEZE SET via an extended own-space solve).
  * split / scale-only                -> projection onto the A0_wide exact theta=1 basis (same DOF space),
    full-order spot-check (<=0.3%) required before freeze-set trust (G04).
Every eigensolve is logged to out/eigensolve_log.jsonl (>=40 across the loop is a card requirement).
Packages saved in THIS workspace (data/packages_wide/<cid>.npz), same schema as wide_package.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                        # noqa: E402
F = WP.F                                          # femlib, read-only
sys.path.insert(0, os.path.abspath(os.path.join(WS, "..", "shocksat_true_remodel_loop_20260706", "code")))
import actions as ACT                             # noqa: E402  (read-only reuse)

PKGD = os.path.join(WS, "data", "packages_wide")
K_OWN = 200          # own-space modes (D11: covers ~500 Hz credible; matches scoring cap)
SPECD = os.path.join(WS, "out", "candidate_specs")
os.makedirs(SPECD, exist_ok=True)


def log_eig(tag, cid, n_dof, t_s):
    with open(os.path.join(WS, "out", "eigensolve_log.jsonl"), "a") as f:
        f.write(json.dumps({"tag": tag, "cid": cid, "n_dof": int(n_dof), "t_s": round(t_s, 1),
                            "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")


def _package_from_W(m, blocks, W, lam_el, cid, note, extra_meta=None):
    """Common packaging: project blocks on W (NDOF_full x r, M-orthonormal), build rows, frozen pairing."""
    A, A_fix = {}, None
    for name, Kb in blocks.items():
        Ab = W.T @ (Kb @ W)
        if name == "_fixed_bush99":
            A_fix = Ab
        else:
            A[name] = Ab
    free_names = sorted(A)
    freqs_el = np.sqrt(np.clip(lam_el, 0, None)) / (2 * np.pi)
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
    pairs, _ = F.hungarian_pairing(freqs_el, ash_rows, live, mfreqs, msh, allowed=allowed)
    node_z = np.asarray(m["xyz"], float)[:, 2]
    tray_nodes = np.where(node_z >= 55.0)[0]
    tray = np.zeros((3, W.shape[1]))
    for a in range(3):
        tray[a] = W[6 * tray_nodes + a, :].sum(0)
    meta = dict(note=note, r=int(W.shape[1]))
    if extra_meta:
        meta.update(extra_meta)
    d = dict(cid=cid, free_names=free_names,
             A=np.stack([A[g] for g in free_names]), A_fix=A_fix,
             freqs_el=freqs_el, n_rbm=0, lam_all=lam_el,
             ash_rows=ash_rows, live=live, mfreqs=mfreqs,
             pairs=np.array([[p[0], p[1], p[2]] for p in pairs]),
             sens_daq=sens_daq, sens_rows=np.array(sens_rows), tray=tray,
             meta=json.dumps(meta))
    for k in F.DRIVE_KEYS + [F.VAULT_KEY]:
        d[f"drive_{k}"] = F.drive_row(m, W, cmeta[k]["xyz"], cmeta[k]["axis"])
    np.savez_compressed(os.path.join(PKGD, f"{cid}.npz"), **d)
    return WP.load(cid)


def build_own_space(spec, track):
    """Own-space eigensolve candidate (refine/thickness/rbe2)."""
    cid = spec["cid"]
    if os.path.exists(os.path.join(PKGD, f"{cid}.npz")):
        return WP.load(cid)
    json.dump(spec, open(os.path.join(SPECD, f"{cid}.json"), "w"), indent=1)
    m, blocks = ACT.build_candidate(dict(spec), tag_track=track, blocks_only=True)
    M = blocks.pop("__M__")
    Ktot = None
    for name, Kb in blocks.items():
        Ktot = Kb if Ktot is None else Ktot + Kb
    T, keep = F.build_T(m)
    t0 = time.time()
    Kr = (T.T @ (Ktot @ T)).tocsc()
    Mr = (T.T @ (M @ T)).tocsc()
    lam, V = eigsh(Kr, k=K_OWN, M=Mr, sigma=F.SIGMA_SHIFT, which="LM")
    idx = np.argsort(lam); lam, V = lam[idx], V[:, idx]
    dt = time.time() - t0
    log_eig("own_space_k%d" % K_OWN, cid, Kr.shape[0], dt)
    n_rbm = int((lam < (2 * np.pi * 10.0) ** 2).sum())
    Ve = V[:, n_rbm:]
    W = np.asarray(T @ Ve)
    ftop = float(np.sqrt(lam[-1]) / (2 * np.pi))
    pkg = _package_from_W(m, blocks, W, lam[n_rbm:], cid,
                          note=f"own-space k={K_OWN} solve ({track})",
                          extra_meta={"basis_top_hz": ftop, "solve_s": round(dt, 1),
                                      "family": spec.get("family", "?"), "track": track})
    print(f"{cid}: own-space r={W.shape[1]}, top {ftop:.0f} Hz, {dt:.0f}s", flush=True)
    return pkg


_A0W_CACHE = {}


def a0_wide_W():
    """(m, W, lam_el) of the inherited wide basis (cached; W rebuilt from full_eig outputs)."""
    if "W" not in _A0W_CACHE:
        z = np.load(os.path.join(WS, "out", "full_eig_theta1.npz"))
        V = np.load(os.path.join(WS, "out", "full_eig_V.npy"))
        n_rbm = int(z["n_rbm"])
        m = F.load_model()
        T, keep = F.build_T(m)
        _A0W_CACHE["m"] = m
        _A0W_CACHE["W"] = np.asarray(T @ V[:, n_rbm:])
        _A0W_CACHE["lam"] = (2 * np.pi * np.asarray(z["freqs"])[n_rbm:]) ** 2
    return _A0W_CACHE["m"], _A0W_CACHE["W"], _A0W_CACHE["lam"]


def build_projected(spec, track):
    """Same-DOF-space candidate (split / scale-only) projected onto the A0_wide basis.
    NOTE: uses the CANDIDATE's blocks (split regions get their own theta block) but the inherited basis;
    freeze-set trust requires the G04 spot check."""
    cid = spec["cid"]
    if os.path.exists(os.path.join(PKGD, f"{cid}.npz")):
        return WP.load(cid)
    json.dump(spec, open(os.path.join(SPECD, f"{cid}.json"), "w"), indent=1)
    m, blocks = ACT.build_candidate(dict(spec), tag_track=track, blocks_only=True)
    blocks.pop("__M__")
    m0, W, lam_el = a0_wide_W()
    assert 6 * len(m["gids"]) == W.shape[0], f"{cid}: DOF space changed; must use build_own_space"
    pkg = _package_from_W(m, blocks, W, lam_el, cid,
                          note=f"projected onto A0_wide basis ({track}; needs G04 spot check for freeze)",
                          extra_meta={"family": spec.get("family", "?"), "track": track,
                                      "projected": True})
    print(f"{cid}: projected (r={W.shape[1]})", flush=True)
    return pkg


def build(spec, track):
    fam, needs_full = ACT.classify(spec)
    spec = dict(spec); spec["family"] = fam
    if needs_full:
        return build_own_space(spec, track)
    return build_projected(spec, track)
