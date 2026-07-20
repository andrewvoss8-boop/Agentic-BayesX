#!/usr/bin/env python3
"""Tier-2 FULL EIGENSOLVES (card §3): top ~30 tier-1 candidates + the M0 baseline through the SAME path.

Per candidate: assemble full-order K,M (remodel.py, read-only), reduce by T (RBE2), eigsh k=80 shift-invert
(A12 proven path), then SAVE the candidate-basis reduced package for tiers 3+4 (so M0 and M1 run through
IDENTICAL downstream code):
  vals(80) | per-block K projections Kblk (9 groups + candidate extras) | .ash live-DOF shapes | sensor rows
  (115 ch) | per-drive rows (5 drives) | tray uniform-mass selectors (3 axes, netcg kept-node set) | Hungarian
  .ash pairing at theta=1 (frozen for scoring; trap-2).
Resumable (skips finished). Detached launch. Output: out/tier2/<id>.npz + out/tier2_full.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
from scipy.optimize import linear_sum_assignment

WS = Path(__file__).resolve().parent.parent
BASE = WS.parent / "shocksat_psd_envelope_twin_20260623"
NETCG = WS.parent / "shocksat_netcg_method_selection_20260701"
sys.path.insert(0, str(BASE / "code"))
import remodel as RM
import realfrf as rf

BAND = (45.0, 260.0); MAC_MIN = 0.3; K_EIG, SIGMA = 80, -1.0e3
TRAY_Z = 55.0
N_TOP = 30
AX = {"X": 0, "Y": 1, "Z": 2}
GROUPS = json.loads((WS.parent / "shocksat_fem_remesh_20260618" / "groups.json").read_text())["groups"]
CACHE_DIR = NETCG / "data" / "multiref_modal"
DRIVES = {"m_xpos_990x": "X", "m_zpos_990z": "Z", "m_xy_990xy": "XY", "m_zpos_900z": "Z", "m_ypos_990y": "Y"}
t0 = time.time()


def log(m):
    print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)


def pick_top():
    sc = json.loads((WS / "out" / "tier1_screen.json").read_text())["scores"]
    ranked = sorted(((v["screen_score"], k) for k, v in sc.items()
                     if "error" not in v and k != "baseline"), reverse=True)
    top = [k for _, k in ranked[:N_TOP - 3]]
    # family-diversity hedge (D6): ensure every family with a viable candidate has >=1 in tier-2
    fams_in = {sc[k]["family"] for k in top}
    for fam in ["joint_compliance", "connectivity", "weld_contact", "thickness_offset_proxy",
                "mass_distribution", "random_tranche"]:
        if fam not in fams_in:
            best = max((v["screen_score"], k) for k, v in sc.items()
                       if v.get("family") == fam and "error" not in v)
            top.append(best[1]); fams_in.add(fam)
    return (["baseline"] + top)[:N_TOP + 1]


def main():
    cands = {c["id"]: c for c in json.loads((WS / "out" / "candidates.json").read_text())["candidates"]}
    top = pick_top()
    (WS / "out" / "tier2").mkdir(parents=True, exist_ok=True)

    T = sp.load_npz(Path(RM.MAT) / "T.npz").tocsr()
    mm = np.load(RM.MM, allow_pickle=True)
    nodes, mfreqs, mshapes, mmask = mm["nodes"], mm["freqs"], mm["shapes"], mm["measured"]
    obs_dofs = np.array([6 * RM.G2I[int(n)] + c for n in nodes for c in range(3)])
    live = mmask.reshape(-1)
    pht = mshapes.reshape(33, -1)[:, live]

    # sensor channel DOFs (rescore_sigma convention: ch.nodes = node INDEX; dof = 6*idx + axis)
    R = rf.load_reduced()
    ch = rf.build_channels(R, [d for d in range(1, 116) if d not in rf.BAD_DAQ])
    sens_dofs = np.array([6 * int(n) + AX[a] for n, a in zip(ch.nodes, ch.axes)])
    sens_daq = np.array(ch.daq)
    # tray selector: SAME kept-node set as the netcg QOIModel (quantity contract)
    keep = np.load(BASE / "data" / "keep_dofs.npy")
    xyz = R.xyz
    tray_dofs = {a: keep[(xyz[keep // 6, 2] >= TRAY_Z) & (keep % 6 == a)] for a in (0, 1, 2)}
    # drive points from the 5 caches
    drv = {}
    for key in DRIVES:
        c = np.load(CACHE_DIR / f"{key}.npz", allow_pickle=True)
        dxyz = np.array([float(x) for x in c["xyz"]])
        nn = int(np.argmin(np.linalg.norm(RM.XYZ - dxyz, axis=1)))
        drv[key] = (nn, DRIVES[key])

    # candidate-specific K blocks: 9 groups (edited blocks folded in) + extras (couple / rebuilt bush)
    def blocks_for(edit):
        blks = {}
        for gname, members in GROUPS.items():
            Kg = None
            for mem in members:
                pid = int(mem.split("_")[1])
                if mem.startswith("bush_") and str(pid) in {str(k) for k in edit.get("bush_k", {})}:
                    kv = edit["bush_k"][str(pid)] if str(pid) in edit.get("bush_k", {}) else edit["bush_k"][pid]
                    Kp = RM.bush_block(pid, np.array(kv, float))
                else:
                    Kp = sp.load_npz(Path(RM.MAT) / f"K_{mem}.npz")
                    if mem in edit.get("scale", {}):
                        Kp = Kp * float(edit["scale"][mem])
                Kg = Kp if Kg is None else Kg + Kp
            blks[gname] = Kg.tocsr()
        blks["_fixed_bush99"] = sp.load_npz(Path(RM.MAT) / "K_bush_99.npz").tocsr()
        cpl = edit.get("couple")
        if cpl:
            blks["couple_x"] = RM.build_couple_K(cpl["pairs"], cpl["k"]).tocsr()
        return blks

    import os
    budget = float(os.environ.get("TIER2_BUDGET_S", "1e18"))   # clean exit after budget (foreground chunking, D10)
    summary = {}
    outp = WS / "out" / "tier2_full.json"
    if outp.exists():
        summary = json.loads(outp.read_text()).get("results", {})
    for cid in top:
        if time.time() - t0 > budget:
            log(f"budget {budget:.0f}s reached — clean exit ({len(summary)}/{len(top)} done, resumable)")
            return
        f_npz = WS / "out" / "tier2" / f"{cid}.npz"
        if f_npz.exists() and cid in summary:
            log(f"[{cid}] done — skip"); continue
        edit = cands[cid]["edit"]
        log(f"[{cid}] assembling K,M ...")
        blks = blocks_for(edit)
        K = None
        for b in blks.values():
            K = b if K is None else K + b
        Mfull = RM.build_M(edit)
        Kr = (T.T @ K @ T).tocsc(); Mr = (T.T @ Mfull @ T).tocsc()
        log(f"[{cid}] eigsh k={K_EIG} on n={Kr.shape[0]} ...")
        vals, vecs = eigsh(Kr, k=K_EIG, M=Mr, sigma=SIGMA, which="LM")
        o = np.argsort(vals); vals, vecs = vals[o], vecs[:, o]
        f = np.sqrt(np.clip(vals, 0, None)) / (2 * np.pi)
        # candidate-basis projections (vecs are Mr-orthonormal)
        Uc = T @ vecs                                        # full-space modes (406098, 80)
        Kblk = {n: Uc.T @ (b @ Uc) for n, b in blks.items()}
        ash = np.asarray(T[obs_dofs, :] @ vecs)[live]        # (n_live, 80)
        sens = np.asarray(Uc[sens_dofs])                     # (n_ch, 80)
        tray = np.stack([Uc[tray_dofs[a]].sum(0) for a in (0, 1, 2)])   # (3, 80)
        drows = {}
        for key, (nn, dax) in drv.items():
            if dax == "XY":
                drows[key] = Uc[6 * nn + 0] + Uc[6 * nn + 1]
            else:
                drows[key] = Uc[6 * nn + AX[dax]]
        # frozen Hungarian pairing at theta=1 (trap-2)
        inb = np.where((f >= BAND[0]) & (f <= BAND[1]))[0]
        ash_c = ash[:, inb]
        MAC = (pht @ ash_c) ** 2 / (np.sum(pht ** 2, 1)[:, None] * np.sum(ash_c ** 2, 0)[None, :] + 1e-300)
        ri, ci = linear_sum_assignment(1.0 - MAC)
        keep_p = MAC[ri, ci] >= MAC_MIN
        pairs = [[int(a), int(inb[b]), round(float(MAC[a, b2]), 4)]
                 for a, b, b2 in zip(ri[keep_p], ci[keep_p], ci[keep_p])]
        macs = MAC[ri[keep_p], ci[keep_p]]
        ferr = (f[inb][ci[keep_p]] - mfreqs[ri[keep_p]]) / mfreqs[ri[keep_p]]
        np.savez_compressed(f_npz, vals=vals, ash=ash, sens=sens, sens_daq=sens_daq, tray=tray,
                            pairs=np.array(pairs, float), mfreqs=mfreqs,
                            blk_names=np.array(list(Kblk.keys())),
                            Kblk=np.stack([Kblk[n] for n in Kblk]),
                            **{f"drive_{k}": v for k, v in drows.items()})
        summary[cid] = {"n_matched": int(keep_p.sum()), "mac_mean": round(float(np.mean(macs)), 4),
                        "freq_rms_pct": round(100 * float(np.sqrt(np.mean(ferr ** 2))), 3),
                        "full_score": round(float(np.mean(macs) - 3 * np.sqrt(np.mean(ferr ** 2))), 4),
                        "family": cands[cid]["family"], "runtime_s": round(time.time() - t0, 1)}
        outp.write_text(json.dumps({"design": "full eigsh k=80 (A12); frozen Hungarian .ash pairing; "
                                    "shape-inclusive full score (no amplitude fitting)",
                                    "n_planned": len(top), "results": summary}, indent=1))
        log(f"[{cid}] full: n={summary[cid]['n_matched']} MAC {summary[cid]['mac_mean']} "
            f"fRMS {summary[cid]['freq_rms_pct']}% score {summary[cid]['full_score']:+.4f}")
    ranked = sorted(((v["full_score"], k) for k, v in summary.items() if k != "baseline"), reverse=True)
    log("TIER-2 ranking (baseline={}): ".format(summary.get("baseline", {}).get("full_score"))
        + ", ".join(f"{k}({s:+.3f})" for s, k in ranked[:12]))


if __name__ == "__main__":
    main()
