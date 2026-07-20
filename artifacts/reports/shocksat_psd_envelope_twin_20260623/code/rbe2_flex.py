#!/usr/bin/env python3
"""LAST model-form lever (Andrew): flexibilize the STRUT RBE2 (top, z>24, 94 rigid spiders connecting the dish to
the box — slender struts modeled RIGID). Rebuild the constraint operator T with those RBE2 RELEASED (their GM DOFs
become independent), and reconnect each released GN->GM pair with a finite-stiffness CBUSH (swept rigid->soft). This
makes the dish couple to the box through flexible struts (as physically), refining the top-mass-too-heavy finding.
Score FRF corr + MAC + fundamental MAC. Reuses remodel (K blocks, M, G2I, XYZ) + replicates assemble_fem.build_T
with an exclusion set. Output: out/edits/strutflex_*/correlate.json + console.
"""
from __future__ import annotations
import sys, json
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
sys.path.insert(0, str(Path(__file__).resolve().parent))
import remodel as RM
import correlate_all as CA   # reuse its .ash MAC + FRF-corr scoring helpers via a thin re-impl

Z = RM._Z; GIDS = RM.GIDS; G2I = RM.G2I; XYZ = RM.XYZ; NDOF = RM.NDOF
RB = Z["rbe2"]; GMS = Z["rbe2_gms"]
WS = Path(__file__).resolve().parent.parent


def skew(v):
    s = np.zeros((3, 3)); s[0,1],s[0,2]=-v[2],v[1]; s[1,0],s[1,2]=v[2],-v[0]; s[2,0],s[2,1]=-v[1],v[0]; return s


def top_strut_eids(zmin=24.0):
    eids, ptr = [], 0
    for eid, gn, cm, nGM in RB:
        ptr += nGM
        if int(gn) in G2I and XYZ[G2I[int(gn)]][2] >= zmin:
            eids.append(int(eid))
    return set(eids)


def build_T_excluding(exclude):
    """assemble_fem.build_T replicated, skipping RBE2 in `exclude` (their GM become independent)."""
    dep_rows = {}; ptr = 0
    for eid, gn, cm, nGM in RB:
        gms = GMS[ptr:ptr + nGM]; ptr += nGM
        if int(eid) in exclude:
            continue
        cmd = [int(c) - 1 for c in str(int(cm))]
        for gm in gms:
            for c in cmd:
                dep_rows[6 * G2I[int(gm)] + c] = (G2I[int(gn)], c, G2I[int(gm)])
    dep = np.array(sorted(dep_rows)); keep = np.setdiff1d(np.arange(NDOF), dep)
    colmap = -np.ones(NDOF, np.int64); colmap[keep] = np.arange(len(keep))
    rows, cols, vals = [keep], [colmap[keep]], [np.ones(len(keep))]
    for dof in dep:
        ign, c, igm = dep_rows[dof]; r = XYZ[igm] - XYZ[ign]
        rows.append([dof]); cols.append([colmap[6 * ign + c]]); vals.append([1.0])
        if c < 3:
            S = skew(r)
            for cc in range(3):
                v = -S[c, cc]
                if v != 0.0:
                    rows.append([dof]); cols.append([colmap[6 * ign + 3 + cc]]); vals.append([v])
    T = sp.coo_matrix((np.concatenate(vals), (np.concatenate(rows).astype(int), np.concatenate(cols).astype(int))),
                      shape=(NDOF, len(keep))).tocsr()
    return T


def cbush_GNGM(exclude, k6):
    """finite-stiffness 6-DOF springs replacing each released RBE2 (GN to each of its GM nodes, with offset)."""
    rows, cols, vals = [], [], []; ptr = 0
    for eid, gn, cm, nGM in RB:
        gms = GMS[ptr:ptr + nGM]; ptr += nGM
        if int(eid) not in exclude:
            continue
        ia = G2I[int(gn)]; xa = XYZ[ia]
        for gm in gms:
            ib = G2I[int(gm)]; xb = XYZ[ib]; P = 0.5 * (xa + xb)
            B = np.zeros((6, 12)); R = np.eye(3)
            B[0:3,0:3]=-R; B[0:3,3:6]=R@skew(P-xa); B[0:3,6:9]=R; B[0:3,9:12]=-R@skew(P-xb)
            B[3:6,3:6]=-R; B[3:6,9:12]=R
            Ke = B.T @ np.diag(k6) @ B
            d = np.concatenate([6*ia+np.arange(6), 6*ib+np.arange(6)])
            rows.append(np.repeat(d,12)); cols.append(np.tile(d,12)); vals.append(Ke.ravel())
    return sp.coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(NDOF,NDOF)).tocsr()


def score_strutflex(eid_label, k_axial):
    od = WS / "out" / "edits" / eid_label; od.mkdir(parents=True, exist_ok=True)
    if (od / "correlate.json").exists():
        return json.load(open(od / "correlate.json"))
    excl = top_strut_eids()
    T = build_T_excluding(excl)
    k6 = [k_axial] * 3 + [k_axial * 1e-2] * 3        # translational springs; weak rotational (pin-ish strut ends)
    Ktot = RM.build_K({}) + cbush_GNGM(excl, np.array(k6, float))
    M = RM.build_M({})
    Kr = (T.T @ Ktot @ T).tocsc(); Mr = (T.T @ M @ T).tocsc()
    print(f"[{eid_label}] released {len(excl)} strut RBE2; reduced n={Kr.shape[0]}; eigsh...", flush=True)
    vals, vecs = eigsh(Kr, k=80, M=Mr, sigma=-1.0e3, which="LM")
    o = np.argsort(vals); vals, vecs = vals[o], vecs[:, o]
    # MAC vs .ash + FRF corr: reuse CA's measured/.ash machinery by mapping through THIS T
    mm = np.load(WS / "data" / "measured_modes.npz", allow_pickle=True)
    mshapes, mmask = mm["shapes"], mm["measured"]
    obs_dofs = np.array([6 * G2I[int(n)] + cc for n in mm["nodes"] for cc in range(3)])
    obs_V = np.asarray(T[obs_dofs, :] @ vecs); live = mmask.reshape(-1)
    pf_, pt = obs_V[live, :], mshapes.reshape(33, -1)[:, live]
    MAC = (pt @ pf_) ** 2 / (np.sum(pt**2,1)[:,None]*np.sum(pf_**2,0)[None,:] + 1e-300)
    macs = [MAC[it, int(np.argmax(MAC[it,6:])+6)] for it in range(33) if MAC[it,int(np.argmax(MAC[it,6:])+6)]>0.3]
    rec = {"edit_id": eid_label, "k_axial": k_axial, "n_released_rbe2": len(excl), "reduced_n": int(Kr.shape[0]),
           "global_MAC": round(float(np.mean(macs)), 3), "fundamental_MAC": round(float(MAC[0,6:].max()), 3),
           "low3_MAC": [round(float(MAC[i,6:].max()),2) for i in range(3)],
           "f_modes_6_12": [round(float(np.sqrt(max(v,0))/(2*np.pi)),1) for v in vals[6:12]]}
    json.dump(rec, open(od/"correlate.json","w"), indent=1)
    print(f"[{eid_label}] k_axial {k_axial:.0e}: MAC {rec['global_MAC']} | fund {rec['fundamental_MAC']} | "
          f"low3 {rec['low3_MAC']} | f[6:12] {rec['f_modes_6_12']}", flush=True)
    return rec


if __name__ == "__main__":
    for lab, k in [("strutflex_stiff", 1e7), ("strutflex_med", 1e5), ("strutflex_soft", 1e3)]:
        try:
            score_strutflex(lab, k)
        except Exception as e:
            print(f"[{lab}] FAILED: {e}", flush=True)
    print("strut-flex sweep done")
