#!/usr/bin/env python3
"""BRUTE-FORCE FEM correlation (Andrew pivot): no held-out / no Bayes — correlate the FEM against ALL the data
(4 clean modal references + .ash), with 100% per-mode damping freedom, scoring FRF correlation AND MAC jointly.

Objective per edit: solve FEM -> match modes to .ash -> for each reference synthesize the FRF at every sensor from
the FEM shapes + MEASURED per-mode frequency + MEASURED per-mode damping (full freedom) + per-mode complex
participation fit by LSQ to THAT reference's ALL-channel measured FRF; score:
  FRF_corr   = median over (channel x reference) of corr(log|H_synth|, log|H_meas|) in band   [-> 1 best]
  FRF_ampdB  = median |20 log10(peak_synth/peak_meas)|                                          [-> 0 best]
  MAC        = global matched-mode MAC vs .ash                                                  [-> 1 best]
Reuses rescore_sigma setup (R, ch, T, channels, .ash). Usage: python3 correlate_all.py <edit_id|all>.
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
sys.path.insert(0, str(Path(__file__).resolve().parent))
import rescore_sigma as RS          # reuses R, ch, T, common, SENSOR_DOF, AX, mm, tau, RM
import remodel as RM
import realfrf as rf
from modal_multiref import MODAL_REFS, CACHE, N_MODAL

WS = Path(__file__).resolve().parent.parent; OUT = WS / "out"
t0 = time.time()
def log(m): print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)

# per-reference measured FRF + drive node DOF (full per-mode damping uses .ash damp)
REFS = {}
for key, meta in MODAL_REFS.items():
    c = dict(np.load(CACHE / f"{key}.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
    xyz = tuple(float(x) for x in c["xyz"]); ax = str(c["axis"])
    dn = int(np.argmin(np.linalg.norm(RM.XYZ - np.array(xyz), axis=1)))
    axes = [RS.AX["X"], RS.AX["Y"]] if ax == "XY" else [RS.AX[ax]]
    REFS[key] = {"c": c, "drive_dofs": [6 * dn + a for a in axes], "label": meta["label"]}
FREQS = REFS["m_xpos_990x"]["c"]["freqs"]; W = 2 * np.pi * FREQS
COMMON = RS.common
RIDGE = 1e-3


def score(edit_id, edit):
    od = OUT / "edits" / edit_id; od.mkdir(parents=True, exist_ok=True)
    if (od / "correlate.json").exists():
        log(f"[{edit_id}] correlate already done — skip"); return json.load(open(od / "correlate.json"))
    Kr = (RS.T.T @ RM.build_K(edit) @ RS.T).tocsc(); Mr = (RS.T.T @ RM.build_M(edit) @ RS.T).tocsc()
    log(f"[{edit_id}] eigsh..."); vals, vecs = eigsh(Kr, k=80, M=Mr, sigma=-1.0e3, which="LM")
    o = np.argsort(vals); vals, vecs = vals[o], vecs[:, o]
    mshapes, mmask, mfreqs, mdamp = RS.mm["shapes"], RS.mm["measured"], RS.mm["freqs"], RS.mm["damp"] / 100.0
    obs_dofs = np.array([6 * RM.G2I[int(n)] + cc for n in RS.mm["nodes"] for cc in range(3)])
    obs_V = np.asarray(RS.T[obs_dofs, :] @ vecs); live = mmask.reshape(-1)
    pf_, pt = obs_V[live, :], mshapes.reshape(33, -1)[:, live]
    MAC = (pt @ pf_) ** 2 / (np.sum(pt ** 2, 1)[:, None] * np.sum(pf_ ** 2, 0)[None, :] + 1e-300)
    ridx, kidx = [], []
    for it in range(33):
        jf = int(np.argmax(MAC[it, 6:]) + 6)
        if MAC[it, jf] > 0.3: ridx.append(it); kidx.append(jf)
    macs = [MAC[it, int(np.argmax(MAC[it, 6:]) + 6)] for it in range(33) if MAC[it, int(np.argmax(MAC[it, 6:]) + 6)] > 0.3]
    wr = mfreqs[ridx] * 2 * np.pi
    eta = 2.0 * (mdamp[ridx] + 1.0 / (2 * np.pi * mfreqs[ridx] * RS.tau))   # FULL per-mode MEASURED damping + window
    dofs = np.array([RS.SENSOR_DOF[d] for d in COMMON])
    Phi = np.asarray(RS.T[dofs, :] @ vecs)[:, kidx]                          # (Nc, nmode) FEM shapes at sensors
    denom = (1 + 1j * eta)[None, :] * (wr ** 2)[None, :] - (W ** 2)[:, None]
    corrs, amps = [], []
    for key, R in REFS.items():
        c = R["c"]; cidx = {d: c["daq"].index(d) for d in COMMON}
        pd = sum(np.asarray(RS.T[dd, :] @ vecs).ravel()[kidx] for dd in R["drive_dofs"])   # drive participation
        basis = (-(W ** 2)[:, None, None]) * (Phi[None, :, :] * pd[None, None, :]) / denom[:, None, :]  # (Nf,Nc,nm)
        Hmeas = np.array([c["H1"][cidx[d]] for d in COMMON]).T               # (Nf,Nc)
        A = basis.reshape(-1, len(kidx)); b = Hmeas.reshape(-1)
        AhA = A.conj().T @ A + RIDGE * np.eye(len(kidx)) * np.real(np.trace(A.conj().T @ A)) / len(kidx)
        a = np.linalg.solve(AhA, A.conj().T @ b)
        Hsyn = basis @ a                                                     # (Nf,Nc) all-channel fit
        for k in range(len(COMMON)):
            corrs.append(np.corrcoef(np.log(np.abs(Hsyn[:, k]) + 1e-30), np.log(np.abs(Hmeas[:, k]) + 1e-30))[0, 1])
            amps.append(abs(20 * np.log10((np.abs(Hsyn[:, k]).max() + 1e-30) / (np.abs(Hmeas[:, k]).max() + 1e-30))))
    rec = {"edit_id": edit_id, "n_matched_modes": len(kidx), "global_MAC": round(float(np.mean(macs)), 3),
           "fundamental_MAC": round(float(MAC[0, 6:].max()), 3),                    # lowest measured mode (~54 Hz) best FEM-MAC
           "low3_MAC": [round(float(MAC[i, 6:].max()), 2) for i in range(3)],
           "FRF_logmag_corr_median": round(float(np.median(corrs)), 3),
           "FRF_logmag_corr_mean": round(float(np.mean(corrs)), 3),
           "FRF_corr_frac_above_0.5": round(float(np.mean(np.array(corrs) > 0.5)), 2),
           "FRF_peak_ampl_err_dB_median": round(float(np.median(amps)), 1),
           "n_channels": len(COMMON), "n_refs": len(REFS), "runtime_s": round(time.time() - t0, 1)}
    json.dump(rec, open(od / "correlate.json", "w"), indent=1)
    log(f"[{edit_id}] FRF log|H| corr median={rec['FRF_logmag_corr_median']} "
        f"(mean {rec['FRF_logmag_corr_mean']}, frac>0.5 {rec['FRF_corr_frac_above_0.5']}); "
        f"peak ampl err {rec['FRF_peak_ampl_err_dB_median']} dB; MAC {rec['global_MAC']}")
    return rec


# baseline PBUSH 6-term K (from the deck) for DIRECTIONAL joint rebuilds (the untried lever: which DOF is soft)
PBUSH0 = {801: [1e6,1e6,5e6,12240,1e7,1e7], 802: [813660,813660,1.91e7,7.7e5,1e7,1e7],
          803: [186000,186000,5e6,1e6,1e7,1e7], 804: [691000,5e6,691000,16660,1e7,1e7],
          805: [899790,5e6,899790,1e7,1e7,946000], 806: [5e6,100000,100000,1e7,32000,1e7],
          807: [5e6,324000,324000,1e7,1e7,869000]}
def jdir(transf, rotf):
    return {"bush_k": {p: [PBUSH0[p][i]*(rotf if i>=3 else transf) for i in range(6)] for p in PBUSH0}}
def eblock(pids, f): return {"scale": {f"shell_{p}": f for p in pids}}
def merge(*ds):
    out = {"scale": {}, "bush_k": {}}
    for d in ds:
        out["scale"].update(d.get("scale", {})); out["bush_k"].update(d.get("bush_k", {}))
    return {k: v for k, v in out.items() if v}
BB, TB, PL = [101,102,103], [201,202,203], [501,601,701]
# CONNECTIVITY SURGERY: couple the cross-edge nodes that sit coincident (<0.2in) on the walls but are left
# UNCONNECTED in the FEM (only ~13 of 68 attached). = densify the bolted-cross attachment toward reality.
import scipy.spatial as _spat
_zc = np.load(os.path.join(RM.MT, "fem_model.npz"), allow_pickle=True); _cq = _zc["cquad4"]
_cross = {int(x) for x in _cq[_cq[:, 1] == 401][:, 2:6].ravel().tolist() if x > 0}
_wall = {int(x) for x in _cq[np.isin(_cq[:, 1], [101,102,103,201,202,203])][:, 2:6].ravel().tolist() if x > 0}
_wl = list(_wall); _tree = _spat.cKDTree(np.array([RM.XYZ[RM.G2I[w]] for w in _wl]))
CROSS_PAIRS = []
for cnode in _cross:
    d, j = _tree.query(RM.XYZ[RM.G2I[cnode]], k=1)
    if d < 0.2: CROSS_PAIRS.append((cnode, _wl[int(j)]))
log(f"cross-attach surgery: {len(CROSS_PAIRS)} coincident cross<->wall pairs to couple")
def cross(k6): return {"couple": {"pairs": CROSS_PAIRS, "k": k6}}
CORR_EDITS = {
  "cross_bolt":       cross([1e6]*6),
  "cross_weld":       cross([1e8]*6),
  "cross_bolt_trans": cross([1e7, 1e7, 1e7, 0., 0., 0.]),   # translational attach, rotations free (bolted, no moment)
  "baseline": {},
  "joints_rot_soft":  jdir(1.0, 0.1), "joints_rot_stiff": jdir(1.0, 10.0),
  "joints_trans_soft": jdir(0.3, 1.0), "joints_trans_stiff": jdir(3.0, 1.0),
  "joints_all_soft":  jdir(0.3, 0.3),
  "bottombox_E_lo": eblock(BB, 0.85), "bottombox_E_hi": eblock(BB, 1.15),
  "topbox_E_lo": eblock(TB, 0.85), "topbox_E_hi": eblock(TB, 1.15),
  "plates_E_lo": eblock(PL, 0.7), "plates_E_hi": eblock(PL, 1.5),
  "bbLo_jrotSoft": merge(eblock(BB, 0.85), jdir(1.0, 0.1)),
  "platesHi_jrotSoft": merge(eblock(PL, 1.5), jdir(1.0, 0.1)),
}

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    cat = CORR_EDITS
    ids = list(cat) if arg == "all" else [arg]
    rows = [score(e, cat.get(e, RM.EDITS.get(e, {}))) for e in ids]
    (OUT / "correlate_all.json").write_text(json.dumps(rows, indent=2))
    log("=== all-data FRF correlation (full per-mode damping) ===")
    for r in sorted(rows, key=lambda x: -x["FRF_logmag_corr_median"]):
        log(f"  {r['edit_id']:22s} FRFcorr={r['FRF_logmag_corr_median']:.3f} ampErr={r['FRF_peak_ampl_err_dB_median']:.1f}dB MAC={r['global_MAC']:.3f}")
