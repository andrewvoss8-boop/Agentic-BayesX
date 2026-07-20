#!/usr/bin/env python3
"""Agentic bottom_box REMODELING campaign (D9/D10). Full-FEM architectural edits → re-solve → score on the
clean .ash MAC (global + the bottom_box TARGET modes 70/75/151/158/190/196 Hz) + |df%|. Extends Card D's
edit_solve with MASS edits (cable harness — the gap Andrew flagged: deck has 84 accel CONM2 masses but NO
cable mass). Reuses the modal-twin matrices (read-only); writes to THIS workspace. Resumable (skips done edits).

Edit dict keys:  scale {Kpid_name: factor} · bush_k {pid:[6 k]} · cable_mass_factor f (adds f·m_accel at the
.ash sensor nodes, translational) · damp_mass_factor f (adds mass on the cross_beam nodes = damping material).
Usage: python3 remodel.py <edit_id|all>
"""
import json, os, sys, time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MT = os.path.normpath(os.path.join(WS, "..", "shocksat_fem_modal_twin_20260609"))
MAT = os.path.join(MT, "matrices"); FEM = os.path.join(MT, "fem_model.npz")
MM = os.path.join(WS, "data", "measured_modes.npz")
K_EIG, SIGMA = 80, -1.0e3
TARGET_HZ = [70.0, 75.0, 151.0, 158.0, 190.0, 196.0]
t0 = time.time()
def log(m): print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)

_Z = np.load(FEM, allow_pickle=True)
GIDS = _Z["gids"]; G2I = {int(g): i for i, g in enumerate(GIDS)}
CORDS = json.loads(str(_Z["cords"])); CBUSH = _Z["cbush"]; XYZ = _Z["xyz"]
NDOF = 6 * len(GIDS)
M_ACCEL = 3.882e-5                                   # per-accel CONM2 mass from the deck (lbf·s²/in)
ASH_NODES = [int(n) for n in np.load(MM, allow_pickle=True)["nodes"]]


def bush_block(pid, kvals):
    def skew(v):
        s = np.zeros((3, 3)); s[0,1],s[0,2]=-v[2],v[1]; s[1,0],s[1,2]=v[2],-v[0]; s[2,0],s[2,1]=-v[1],v[0]; return s
    sel = CBUSH[:, 1] == pid; rows, cols, vals = [], [], []
    for eid, _, ga, gb, cid in CBUSH[sel]:
        ia, ib = G2I[ga], G2I[gb]; xa, xb = XYZ[ia], XYZ[ib]; P = 0.5*(xa+xb); ra, rb = P-xa, P-xb
        R = np.eye(3) if cid == 0 else np.array(CORDS[str(cid)]['R'])
        B = np.zeros((6,12)); B[0:3,0:3]=-R; B[0:3,3:6]=R@skew(ra); B[0:3,6:9]=R; B[0:3,9:12]=-R@skew(rb)
        B[3:6,3:6]=-R; B[3:6,9:12]=R
        Ke = B.T @ np.diag(kvals) @ B; d = np.concatenate([6*ia+np.arange(6), 6*ib+np.arange(6)])
        rows.append(np.repeat(d,12)); cols.append(np.tile(d,12)); vals.append(Ke.ravel())
    return sp.coo_matrix((np.concatenate(vals),(np.concatenate(rows),np.concatenate(cols))),shape=(NDOF,NDOF)).tocsr()


def build_couple_K(pairs, kvec):
    """Add a 6-DOF spring between each (ga,gb) coincident node pair (connectivity surgery: weld/bolt the cross to
    the walls along their coincident edges). kvec = 6 stiffnesses; coincident nodes ⇒ ra=rb=0 (pure DOF coupling)."""
    rows, cols, vals = [], [], []
    for ga, gb in pairs:
        ia, ib = G2I[int(ga)], G2I[int(gb)]
        for cc in range(6):
            da, db = 6*ia+cc, 6*ib+cc
            rows += [da, db, da, db]; cols += [da, db, db, da]; vals += [kvec[cc], kvec[cc], -kvec[cc], -kvec[cc]]
    return sp.coo_matrix((vals, (rows, cols)), shape=(NDOF, NDOF)).tocsr()


def build_K(edit):
    scale = edit.get("scale", {}); bush_k = {int(k): v for k, v in edit.get("bush_k", {}).items()}
    Ktot = None
    for f in sorted(os.listdir(MAT)):
        if not f.startswith("K_"): continue
        name = f[2:-4]; pidnum = name.split("_")[1]
        if name.startswith("bush_") and int(pidnum) in bush_k:
            Kp = bush_block(int(pidnum), np.array(bush_k[int(pidnum)], float))
        else:
            Kp = sp.load_npz(os.path.join(MAT, f))
            if name in scale: Kp = Kp * float(scale[name])
        Ktot = Kp if Ktot is None else Ktot + Kp
    cpl = edit.get("couple")
    if cpl:
        Ktot = Ktot + build_couple_K(cpl["pairs"], cpl["k"])
    return Ktot.tocsr()


# region -> shell PIDs (steel = bottom_box, aluminum = top_box, dish = thick top plates; from MAT1/PSHELL)
REGION_PIDS = {"steel": [101, 102, 103], "aluminum": [201, 202, 203], "dish": [501, 601, 701],
               "steelwelds": [104, 105, 106], "alwelds": [204, 205, 206], "cross": [401]}
_CQ = _Z["cquad4"]; _CT = _Z["ctria3"]


def region_nodes(pids):
    pids = set(pids)
    nq = _CQ[np.isin(_CQ[:, 1], list(pids))][:, 2:6].ravel()
    nt = _CT[np.isin(_CT[:, 1], list(pids))][:, 2:5].ravel() if _CT.size else np.array([], int)
    return {int(x) for x in np.concatenate([nq, nt]).tolist() if x > 0}


def build_M(edit):
    M = sp.load_npz(os.path.join(MAT, "M.npz")).tocsr()
    ms = edit.get("mass_scale", {})                  # density/mass distribution: {region: factor} (NEW model-form lever)
    if ms:
        D = np.ones(NDOF)
        for region, fac in ms.items():
            sq = float(fac) ** 0.5
            pids = REGION_PIDS.get(region) or [int(region)]
            for n in region_nodes(pids):
                if n in G2I:
                    D[6 * G2I[n]:6 * G2I[n] + 6] *= sq     # scale region node DOFs -> M_region *= fac (D M D)
        Dm = sp.diags(D); M = (Dm @ M @ Dm).tocsr()
    add = np.zeros(NDOF)
    f = edit.get("cable_mass_factor", 0.0)
    if f:
        for n in ASH_NODES:
            for c in range(3): add[6 * G2I[n] + c] += f * M_ACCEL
    if add.any():
        M = M.tolil()
        for i in np.nonzero(add)[0]: M[i, i] += add[i]
        M = M.tocsr()
    return M


def solve_and_measure(edit_id, edit):
    od = os.path.join(WS, "out", "edits", edit_id)
    if os.path.exists(os.path.join(od, "result.json")):
        log(f"[{edit_id}] already done — skip"); return json.load(open(os.path.join(od, "result.json")))["summary"]
    T = sp.load_npz(os.path.join(MAT, "T.npz"))
    Kr = (T.T @ build_K(edit) @ T).tocsc(); Mr = (T.T @ build_M(edit) @ T).tocsc()
    log(f"[{edit_id}] reduced n={Kr.shape[0]}; eigsh k={K_EIG}...")
    vals, vecs = eigsh(Kr, k=K_EIG, M=Mr, sigma=SIGMA, which='LM')
    order = np.argsort(vals); vals, vecs = vals[order], vecs[:, order]
    freqs = np.sqrt(np.clip(vals, 0, None)) / (2*np.pi); n_rbm = int(np.sum(freqs < 5.0))

    mm = np.load(MM, allow_pickle=True)
    nodes, mfreqs, mshapes, mmask = mm["nodes"], mm["freqs"], mm["shapes"], mm["measured"]
    obs_dofs = np.array([6*G2I[int(n)]+c for n in nodes for c in range(3)])
    obs_V = np.asarray(T[obs_dofs, :] @ vecs); live = mmask.reshape(-1)
    phi_fem = obs_V[live, :]; phi_tst = mshapes.reshape(33, -1)[:, live]
    MAC = (phi_tst @ phi_fem)**2 / (np.sum(phi_tst**2,1)[:,None]*np.sum(phi_fem**2,0)[None,:] + 1e-300)
    pairs = []
    for it in range(33):
        jf = int(np.argmax(MAC[it, 6:]) + 6)
        pairs.append(dict(f_test=float(mfreqs[it]), mac=float(MAC[it, jf]),
                          df_pct=float(100*(freqs[jf]/mfreqs[it]-1))))
    well = [p for p in pairs if p["mac"] > 0.3]; calib = [p for p in pairs if p["mac"] > 0.5]
    def target_mac(hz, tol=6.0):
        cand = [p for p in pairs if abs(p["f_test"]-hz) <= tol]
        return max((p["mac"] for p in cand), default=None)
    tgt = {f"{hz:.0f}Hz": target_mac(hz) for hz in TARGET_HZ}
    tgt_vals = [v for v in tgt.values() if v is not None]
    summary = dict(edit_id=edit_id, edit=edit, n_well=len(well),
        global_mac_well=float(np.mean([p["mac"] for p in well])),
        global_mac_calib=float(np.mean([p["mac"] for p in calib])),
        mean_abs_df_pct_calib=float(np.mean([abs(p["df_pct"]) for p in calib])),
        target_mode_mac=tgt, target_mode_mac_mean=float(np.mean(tgt_vals)) if tgt_vals else None,
        f_mode1_hz=float(freqs[6]), n_rbm=n_rbm, runtime_s=round(time.time()-t0,1))
    os.makedirs(od, exist_ok=True)
    json.dump(dict(summary=summary, pairs=pairs), open(os.path.join(od,"result.json"),"w"), indent=1)
    log(f"[{edit_id}] global MAC(well)={summary['global_mac_well']:.4f} |df%|={summary['mean_abs_df_pct_calib']:.3f} "
        f"TARGET-mode MAC mean={summary['target_mode_mac_mean']} {tgt}")
    return summary


JV = [round(1.e6,0)]  # noqa (kept for readability of joint vals below)
EDITS = {
  "baseline":        {},
  "cable_mass_lo":   {"cable_mass_factor": 0.5},
  "cable_mass_med":  {"cable_mass_factor": 1.0},
  "cable_mass_hi":   {"cable_mass_factor": 2.0},
  "joint_soft":      {"scale": {f"bush_{p}": 0.5 for p in range(801,808)}},
  "joint_stiff":     {"scale": {f"bush_{p}": 2.0 for p in range(801,808)}},
  "cross_soft":      {"scale": {"shell_401": 0.7}},
  "cross_stiff":     {"scale": {"shell_401": 1.5}},
  "cable_med+joint_soft": {"cable_mass_factor": 1.0, "scale": {f"bush_{p}": 0.5 for p in range(801,808)}},
}

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    ids = list(EDITS) if which == "all" else [which]
    for eid in ids:
        try:
            solve_and_measure(eid, EDITS[eid])
        except Exception as e:
            log(f"[{eid}] FAILED: {e}")
    log("campaign done")
