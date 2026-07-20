#!/usr/bin/env python3
"""Card D — LOCAL interface parameter + RE-PAIRING-ROBUST (tracked) shape metric.

Fixes the two flaws that muddied the group-multiplier campaign:
  1. LOCAL parameter: scale a single discrete joint CBUSH (PBUSH 801 bolted joint
     at ch52, 807 strut base at ch92, 902 contact) -> changes interface FLEXIBILITY
     without changing whole-panel modulus. Joints store ~3% strain energy, so
     frequency should barely move -> if SHAPE moves, the lever is decoupled.
  2. TRACKED pairing (re-pairing-robust): MAC-track each baseline FEM mode to its
     shape-CONTINUATION in the edited model, so each test mode keeps the SAME
     PHYSICAL FEM partner. Then ask: did THAT mode's shape get closer to the test
     (genuine dMAC), at what frequency cost? No greedy re-pairing churn.

Usage: python3 local_interface.py <pid> <scale>   (e.g. 801 0.3)
"""
import json, os, sys, time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import edit_solve  # reuse build_K

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)
K_EIG, SIGMA = 80, -1.0e3
t0 = time.time()
HARD = {  # hard channel -> nearest .ash node idx (from region_diagnosis)
    "ch4": 0, "ch27": 0, "ch38": 0, "ch40": 0, "ch52": 0, "ch69": 0, "ch92": 0, "ch98": 0}

def mac(a, b):
    na, nb = a @ a, b @ b
    return float((a @ b) ** 2 / (na * nb)) if na > 0 and nb > 0 else 0.0

def solve_obs(edit):
    M = sp.load_npz("matrices/M.npz"); T = sp.load_npz("matrices/T.npz")
    Ktot = edit_solve.build_K(edit)
    Kr = (T.T @ Ktot @ T).tocsc(); Mr = (T.T @ M @ T).tocsc()
    vals, vecs = eigsh(Kr, k=K_EIG, M=Mr, sigma=SIGMA, which='LM')
    o = np.argsort(vals); vals, vecs = vals[o], vecs[:, o]
    z = np.load("fem_model.npz", allow_pickle=True)
    mm = np.load("measured_modes.npz", allow_pickle=True)
    g2i = {int(g): i for i, g in enumerate(z["gids"])}
    obs_dofs = np.array([6*g2i[int(n)]+c for n in mm["nodes"] for c in range(3)])
    obs_V = np.asarray(T[obs_dofs, :] @ vecs)        # (228, 80)
    freqs = np.sqrt(np.clip(vals, 0, None))/(2*np.pi)
    return obs_V, freqs

def run(pid, scale):
    eid = f"loc_{pid}_{scale}"
    obs_E, fE = solve_obs({"scale": {f"bush_{pid}": float(scale)},
                           "note": f"local bolted/strut joint PID {pid} x{scale}"})
    obs_B = np.load("matrices/obs_V.npy")
    fB = np.sqrt(np.clip(np.load("matrices/eigvals.npy"), 0, None))/(2*np.pi)
    mm = np.load("measured_modes.npz", allow_pickle=True)
    nodes = mm["nodes"]; mshapes = mm["shapes"]; mmask = mm["measured"]
    live = mmask.reshape(-1)
    Bel, Eel = obs_B[:, 6:], obs_E[:, 6:]            # elastic
    phi_tst = mshapes.reshape(33, -1)
    # baseline test->FEM pairing (greedy best-MAC on live DOFs)
    def macv(fem_col, t):
        a = fem_col[live]; b = phi_tst[t][live]; return mac(a, b)
    pair = [int(np.argmax([macv(Bel[:, j], t) for j in range(Bel.shape[1])])) for t in range(33)]
    # TRACK each baseline FEM mode j -> its shape continuation in edited model (full 228 DOFs)
    track = []
    for j in range(Bel.shape[1]):
        macs = [mac(Bel[:, j], Eel[:, k]) for k in range(Eel.shape[1])]
        k = int(np.argmax(macs)); track.append((k, macs[k]))
    # hard-region .ash node indices (nearest to each hard channel) from region_diagnosis
    rd = json.load(open("out/region_diagnosis.json"))
    hard_idx = sorted({i for reg in rd["regions"].values() for i in reg})
    def region_mac(fem_col, t):
        a, b = [], []
        for jn in hard_idx:
            for ax in range(3):
                if mmask[jn, ax]:
                    a.append(fem_col.reshape(76, 3)[jn, ax]); b.append(mshapes[t, jn, ax])
        a, b = np.array(a), np.array(b)
        return mac(a, b) if a.size >= 2 else None
    rows = []
    for t in range(33):
        jb = pair[t]; macB = macv(Bel[:, jb], t)
        if macB < 0.3: continue
        ke, tq = track[jb]                       # tracked continuation + track quality
        macT = macv(Eel[:, ke], t)               # SAME physical mode, edited
        rB, rT = region_mac(Bel[:, jb], t), region_mac(Eel[:, ke], t)
        rows.append(dict(test=t+1, fem_base=jb+1, fem_track=ke+1, track_mac=round(tq, 3),
            mac_base=round(macB, 3), mac_tracked=round(macT, 3), dmac=round(macT-macB, 3),
            f_base=round(fB[jb+6], 2), f_track=round(fE[ke+6], 2),
            df_pct=round(100*(fE[ke+6]/fB[jb+6]-1), 2),
            region_mac_base=None if rB is None else round(rB, 3),
            region_mac_tracked=None if rT is None else round(rT, 3)))
    clean = [r for r in rows if r["track_mac"] > 0.7]
    dmac = np.array([r["dmac"] for r in clean])
    dfreq = np.array([abs(r["df_pct"]) for r in clean])
    reg = [(r["region_mac_base"], r["region_mac_tracked"]) for r in clean
           if r["region_mac_base"] is not None and r["region_mac_tracked"] is not None]
    dreg = np.array([b - a for a, b in [(x[0], x[1]) for x in reg]])
    out = dict(pid=pid, scale=scale, n_clean_tracked=len(clean),
        genuine_dmac_mean=float(dmac.mean()), genuine_dmac_max=float(dmac.max()),
        genuine_dmac_min=float(dmac.min()),
        mean_abs_dfreq_pct=float(dfreq.mean()),
        region_dmac_mean=float(dreg.mean()) if len(dreg) else None,
        region_dmac_max=float(dreg.max()) if len(dreg) else None,
        n_modes_shape_improved=int(np.sum(dmac > 0.02)),
        n_modes_shape_worsened=int(np.sum(dmac < -0.02)),
        rows=rows, runtime_s=round(time.time()-t0, 1))
    od = f"out/local/{eid}"; os.makedirs(od, exist_ok=True)
    json.dump(out, open(f"{od}/result.json", "w"), indent=1)
    print(f"[{eid}] tracked {len(clean)} modes | GENUINE dMAC mean {dmac.mean():+.3f} "
          f"(max {dmac.max():+.3f}, min {dmac.min():+.3f}) | |dfreq| {dfreq.mean():.3f}% "
          f"| region dMAC mean {out['region_dmac_mean']} | improved {out['n_modes_shape_improved']} "
          f"worsened {out['n_modes_shape_worsened']}")
    return out

if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2])
