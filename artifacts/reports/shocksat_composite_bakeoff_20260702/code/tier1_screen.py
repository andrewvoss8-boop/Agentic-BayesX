#!/usr/bin/env python3
"""Tier-1 CHEAP SCREEN (card §3 two-tier plan; decisions_log D4; assumptions A11 = IMPERFECT PROXY, labeled).

Rayleigh-Ritz in the nominal 80-mode basis: project each candidate's edited full-order K,M onto
U = T @ V_keep (mass-orthonormal at nominal), solve the dense 80x80 generalized eigenproblem, pair the
in-band Ritz modes to the 33 .ash survey modes by ONE-TO-ONE Hungarian assignment on the MAC matrix
(metric-trap #2: NOT greedy argmax), and score the SHAPE-INCLUSIVE proxy over the FULL matched in-band set:
    screen_score = mean(matched MAC) - 3 * RMS(rel freq err)          (mesh_screen convention)
NO amplitude fitting anywhere (metric-trap #1). Proxy limitation: cannot create modes outside the nominal
80-mode span -> hedge = top ~30 go to tier-2 FULL eigensolves. Output: out/tier1_screen.json. Resumable.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.linalg import eigh
from scipy.optimize import linear_sum_assignment

WS = Path(__file__).resolve().parent.parent
BASE = WS.parent / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(BASE / "code"))
import remodel as RM   # read-only: bush_block, build_couple_K, region_nodes, G2I, MAT, MM

BAND = (45.0, 260.0)
MAC_MIN = 0.3
t0 = time.time()


def log(m):
    print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)


def main():
    cand = json.loads((WS / "out" / "candidates.json").read_text())["candidates"]
    outp = WS / "out" / "tier1_screen.json"
    done = json.loads(outp.read_text())["scores"] if outp.exists() else {}

    log("loading T, V_keep, M, K blocks...")
    T = sp.load_npz(Path(RM.MAT) / "T.npz").tocsr()
    V = np.load(Path(RM.MAT) / "V_keep.npy")            # (399510, 80)
    U = T @ V                                            # (406098, 80) full-space nominal modes
    M = sp.load_npz(Path(RM.MAT) / "M.npz").tocsr()
    MU = M @ U
    Mt0 = U.T @ MU                                       # nominal projected mass (~I; mass-orthonormal check)
    dev = float(np.abs(Mt0 - np.eye(80)).max())
    log(f"mass-orthonormality max|M~ - I| = {dev:.2e}")
    Kt = {}
    import os
    for f in sorted(os.listdir(RM.MAT)):
        if f.startswith("K_"):
            Kp = sp.load_npz(Path(RM.MAT) / f)
            Kt[f[2:-4]] = U.T @ (Kp @ U)                 # (80,80) per-block projection
    Ksum = sum(Kt.values())

    # .ash survey observation rows in the nominal basis
    mm = np.load(RM.MM, allow_pickle=True)
    nodes, mfreqs, mshapes, mmask = mm["nodes"], mm["freqs"], mm["shapes"], mm["measured"]
    obs_dofs = np.array([6 * RM.G2I[int(n)] + c for n in nodes for c in range(3)])
    live = mmask.reshape(-1)
    ashU = np.asarray(T[obs_dofs, :] @ V)[live]          # (n_live_dof, 80)
    pht = mshapes.reshape(33, -1)[:, live]               # (33, n_live_dof) measured shapes

    # region DOF scaling vectors for mass_scale (precomputed once)
    reg_D = {}
    for region, pids in RM.REGION_PIDS.items():
        D = np.ones(RM.NDOF)
        for n in RM.region_nodes(pids):
            if n in RM.G2I:
                D[6 * RM.G2I[n]:6 * RM.G2I[n] + 6] = np.nan   # mark; factor applied per candidate
        reg_D[region] = np.isnan(D)

    def project_K(edit):
        Ke = Ksum.copy()
        for name, s in edit.get("scale", {}).items():
            Ke = Ke + (float(s) - 1.0) * Kt[name]
        for pid, kv in edit.get("bush_k", {}).items():
            Kb = RM.bush_block(int(pid), np.array(kv, float))
            Ke = Ke - Kt[f"bush_{pid}"] + U.T @ (Kb @ U)
        cpl = edit.get("couple")
        if cpl:
            Kc = RM.build_couple_K(cpl["pairs"], cpl["k"])
            Ke = Ke + U.T @ (Kc @ U)
        return Ke

    def project_M(edit):
        Me = Mt0.copy()
        ms = edit.get("mass_scale", {})
        if ms:
            D = np.ones(RM.NDOF)
            for region, fac in ms.items():
                mask = reg_D.get(region)
                if mask is None:
                    pids = [int(region)]
                    mask = np.zeros(RM.NDOF, bool)
                    for n in RM.region_nodes(pids):
                        if n in RM.G2I:
                            mask[6 * RM.G2I[n]:6 * RM.G2I[n] + 6] = True
                D[mask] *= float(fac) ** 0.5
            DU = D[:, None] * U
            Me = DU.T @ (M @ DU)
        f = edit.get("cable_mass_factor", 0.0)
        if f:
            add = np.zeros(RM.NDOF)
            for n in RM.ASH_NODES:
                for c in range(3):
                    add[6 * RM.G2I[n] + c] += f * RM.M_ACCEL
            idx = np.nonzero(add)[0]
            Me = Me + (U[idx] * add[idx][:, None]).T @ U[idx]
        return Me

    def score(edit):
        Ke, Me = project_K(edit), project_M(edit)
        vals, W = eigh(Ke, Me)
        f = np.sqrt(np.clip(vals, 0, None)) / (2 * np.pi)
        inb = np.where((f >= BAND[0]) & (f <= BAND[1]))[0]
        ash_c = ashU @ W[:, inb]                          # (n_live, n_inb) candidate shapes at .ash DOFs
        num = (pht @ ash_c) ** 2
        den = np.sum(pht ** 2, 1)[:, None] * np.sum(ash_c ** 2, 0)[None, :] + 1e-300
        MAC = num / den                                   # (33, n_inb)
        ri, ci = linear_sum_assignment(1.0 - MAC)         # one-to-one optimal assignment (trap-2 contract)
        keep = MAC[ri, ci] >= MAC_MIN
        ri, ci = ri[keep], ci[keep]
        if len(ri) == 0:
            return {"n_matched": 0, "screen_score": -9.9, "mac_mean": 0.0, "freq_rms_pct": 99.0}
        macs = MAC[ri, ci]
        ferr = (f[inb][ci] - mfreqs[ri]) / mfreqs[ri]
        return {"n_matched": int(len(ri)), "mac_mean": round(float(np.mean(macs)), 4),
                "freq_rms_pct": round(100 * float(np.sqrt(np.mean(ferr ** 2))), 3),
                "screen_score": round(float(np.mean(macs) - 3.0 * np.sqrt(np.mean(ferr ** 2))), 4),
                "n_inband": int(len(inb)),
                "matched_pairs": [[int(a), int(inb[b]), round(float(m), 3)] for a, b, m in zip(ri, ci, macs)]}

    scores = dict(done)
    for i, c in enumerate(cand):
        if c["id"] in scores:
            continue
        try:
            scores[c["id"]] = score(c["edit"]) | {"family": c["family"]}
        except Exception as e:
            scores[c["id"]] = {"error": str(e), "family": c["family"]}
        if (i + 1) % 20 == 0 or i == len(cand) - 1:
            outp.write_text(json.dumps({"proxy_note": "Rayleigh-Ritz nominal-80-mode subspace; IMPERFECT PROXY "
                                        "(A11): cannot create modes outside the nominal span; hedge = tier-2 "
                                        "full eigensolves on top ~30. Shape-inclusive score; Hungarian pairing; "
                                        "no amplitude fitting.", "mass_orthonormality_dev": dev,
                                        "scores": scores}, indent=1))
            log(f"scored {i+1}/{len(cand)}")
    ranked = sorted(((v.get("screen_score", -99), k) for k, v in scores.items()), reverse=True)
    log("top 15: " + ", ".join(f"{k}({s:+.3f})" for s, k in ranked[:15]))
    log(f"baseline: {scores['baseline']}")


if __name__ == "__main__":
    main()
