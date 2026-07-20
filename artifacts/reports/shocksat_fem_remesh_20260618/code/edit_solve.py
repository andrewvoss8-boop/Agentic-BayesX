#!/usr/bin/env python3
"""Card D — apply ONE correlated FEM-update edit, re-solve, measure correlation.

Reuses the assembled per-PID stiffness blocks (matrices/K_*.npz), mass M, RBE2
operator T. An edit modifies one or more PID stiffness blocks (joint/contact
CBUSH stiffness, shell modulus) WITHOUT re-meshing, OR rebuilds a CBUSH block
with custom 6-term stiffness. Mesh-topology edits are handled by remesh_*.py
(separate, they regenerate K blocks).

Metrics (vs the measured .ash survey, 33 modes / 76 nodes):
  - global matched MAC  = mean best-MAC over well-paired test modes (>0.3)
  - mean |df%|          = mean abs frequency error over paired calib modes
  - region MAC          = best-MAC restricted to a hard region's measured DOFs
Improvement = MAC up AND/OR |df%| down at the hard regions WITHOUT degrading
the global numbers.

Usage:  python3 edit_solve.py <edit_id>
  edit specs live in EDITS below; baseline is edit_id 'baseline_reuse'.
"""
import json, os, sys, time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)
K_EIG, SIGMA = int(os.environ.get("K_EIG", 80)), -1.0e3
t0 = time.time()
def log(m): print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)

# ----------------------------------------------------------- bush rebuild
def bush_block(pid, kvals):
    """Rebuild a CBUSH PID stiffness block with custom 6-term kvals (numpy)."""
    z = np.load("fem_model.npz", allow_pickle=True)
    gids, xyz = z["gids"], z["xyz"]
    g2i = {int(g): i for i, g in enumerate(gids)}
    cords = json.loads(str(z["cords"]))
    NDOF = 6 * len(gids)
    def skew(v):
        s = np.zeros((3, 3)); s[0,1],s[0,2]=-v[2],v[1]; s[1,0],s[1,2]=v[2],-v[0]
        s[2,0],s[2,1]=-v[1],v[0]; return s
    sel = z["cbush"][:, 1] == pid
    rows, cols, vals = [], [], []
    for eid, _, ga, gb, cid in z["cbush"][sel]:
        ia, ib = g2i[ga], g2i[gb]; xa, xb = xyz[ia], xyz[ib]
        P = 0.5*(xa+xb); ra, rb = P-xa, P-xb
        R = np.eye(3) if cid == 0 else np.array(cords[str(cid)]['R'])
        B = np.zeros((6,12))
        B[0:3,0:3]=-R; B[0:3,3:6]=R@skew(ra); B[0:3,6:9]=R; B[0:3,9:12]=-R@skew(rb)
        B[3:6,3:6]=-R; B[3:6,9:12]=R
        Ke = B.T @ np.diag(kvals) @ B
        d = np.concatenate([6*ia+np.arange(6), 6*ib+np.arange(6)])
        rows.append(np.repeat(d,12)); cols.append(np.tile(d,12)); vals.append(Ke.ravel())
    return sp.coo_matrix((np.concatenate(vals),
        (np.concatenate(rows), np.concatenate(cols))), shape=(NDOF,NDOF)).tocsr()

# ----------------------------------------------------------- assemble K with edit
def build_K(edit):
    """edit = dict with optional:
       scale: {pid_name: factor}  multiply that K_<pid> block
       bush_k: {pid: [6 kvals]}   replace CBUSH pid block with custom k
    """
    scale = edit.get("scale", {})
    bush_k = edit.get("bush_k", {})
    Ktot = None
    for f in sorted(os.listdir("matrices")):
        if not f.startswith("K_"): continue
        name = f[2:-4]                      # e.g. 'bush_801' or 'shell_101'
        pidnum = name.split("_")[1]
        if name.startswith("bush_") and pidnum in {str(k) for k in bush_k}:
            Kp = bush_block(int(pidnum), np.array(bush_k[int(pidnum)] if int(pidnum) in bush_k else bush_k[pidnum], float))
        else:
            Kp = sp.load_npz(f"matrices/{f}")
            if name in scale:
                Kp = Kp * float(scale[name])
        Ktot = Kp if Ktot is None else Ktot + Kp
    return Ktot.tocsr()

# ----------------------------------------------------------- solve + measure
def solve_and_measure(edit_id, edit):
    M = sp.load_npz("matrices/M.npz"); T = sp.load_npz("matrices/T.npz")
    Ktot = build_K(edit)
    Kr = (T.T @ Ktot @ T).tocsc(); Mr = (T.T @ M @ T).tocsc()
    log(f"[{edit_id}] reduced n={Kr.shape[0]}; eigsh k={K_EIG}...")
    vals, vecs = eigsh(Kr, k=K_EIG, M=Mr, sigma=SIGMA, which='LM')
    order = np.argsort(vals); vals, vecs = vals[order], vecs[:, order]
    freqs = np.sqrt(np.clip(vals, 0, None)) / (2*np.pi)
    n_rbm = int(np.sum(freqs < 5.0))
    log(f"[{edit_id}] f[6:12]={np.round(freqs[6:12],2)} n_rbm={n_rbm}")

    mm = np.load("measured_modes.npz", allow_pickle=True)
    nodes, mfreqs, mshapes, mmask = mm["nodes"], mm["freqs"], mm["shapes"], mm["measured"]
    z = np.load("fem_model.npz", allow_pickle=True)
    g2i = {int(g): i for i, g in enumerate(z["gids"])}
    obs_dofs = np.array([6*g2i[int(n)]+c for n in nodes for c in range(3)])
    obs_V = np.asarray(T[obs_dofs, :] @ vecs)      # (228, K)
    live = mmask.reshape(-1)
    phi_fem = obs_V[live, :]; phi_tst = mshapes.reshape(33, -1)[:, live]
    num = (phi_tst @ phi_fem)**2
    den = (np.sum(phi_tst**2,1)[:,None]*np.sum(phi_fem**2,0)[None,:])
    MAC = num/den                                   # (33, K)

    # greedy best-MAC pairing (elastic modes only), per test mode
    pairs = []
    for it in range(33):
        jf = int(np.argmax(MAC[it, 6:]) + 6)
        pairs.append(dict(test_mode=it+1, f_test=float(mfreqs[it]),
            fem_mode=jf-5, f_fem=float(freqs[jf]), mac=float(MAC[it, jf]),
            df_pct=float(100*(freqs[jf]/mfreqs[it]-1))))

    # region MAC (restricted to each hard region's nearest .ash nodes/axes)
    REG = json.load(open("out/region_diagnosis.json"))["regions"]
    mm_n = mmask  # (76,3)
    obs_n = obs_V.reshape(76,3,-1); tst_n = np.transpose(mshapes,(1,2,0))
    def region_mac(idxs):
        # best-MAC per test mode over the region DOFs, then mean over well-paired
        a_idx=[(j,ax) for j in idxs for ax in range(3) if mm_n[j,ax]]
        if len(a_idx)<2: return None
        rmacs=[]
        for it in range(33):
            if pairs[it]["mac"]<0.3: continue
            jf=pairs[it]["fem_mode"]+5
            a=np.array([obs_n[j,ax,jf] for j,ax in a_idx])
            b=np.array([tst_n[j,ax,it] for j,ax in a_idx])
            if np.dot(a,a)>0 and np.dot(b,b)>0:
                rmacs.append(np.dot(a,b)**2/(np.dot(a,a)*np.dot(b,b)))
        return float(np.mean(rmacs)) if rmacs else None
    region_macs={r: region_mac(idx) for r,idx in REG.items()}

    well=[p for p in pairs if p["mac"]>0.3]
    calib=[p for p in pairs if p["mac"]>0.5]   # the cleaner calibration set
    summary=dict(edit_id=edit_id, edit=edit,
        n_well=len(well),
        global_mac_matched_mean=float(np.mean([p["mac"] for p in well])),
        global_mac_calib_mean=float(np.mean([p["mac"] for p in calib])),
        mean_abs_df_pct_calib=float(np.mean([abs(p["df_pct"]) for p in calib])),
        f_mode1_hz=float(freqs[6]), n_rbm=n_rbm,
        region_macs=region_macs, runtime_s=round(time.time()-t0,1))
    od=f"out/edits/{edit_id}"; os.makedirs(od, exist_ok=True)
    json.dump(dict(summary=summary, pairs=pairs), open(f"{od}/result.json","w"), indent=1)
    log(f"[{edit_id}] global MAC(well)={summary['global_mac_matched_mean']:.4f} "
        f"calib={summary['global_mac_calib_mean']:.4f} |df%|={summary['mean_abs_df_pct_calib']:.3f} "
        f"regions={ {k:(round(v,3) if v else None) for k,v in region_macs.items()} }")
    return summary

# ----------------------------------------------------------- edit catalog
EDITS = {
  "baseline_reuse": {},
}

if __name__ == "__main__":
    eid = sys.argv[1]
    spec = EDITS.get(eid)
    if spec is None and len(sys.argv) > 2:
        spec = json.load(open(sys.argv[2]))
    if spec is None and os.path.exists(f"out/edit_specs/{eid}.json"):
        spec = json.load(open(f"out/edit_specs/{eid}.json"))
    if spec is None: raise SystemExit(f"unknown edit_id {eid}")
    solve_and_measure(eid, spec)
