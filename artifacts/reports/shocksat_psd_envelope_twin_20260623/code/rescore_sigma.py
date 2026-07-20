#!/usr/bin/env python3
"""Re-score the wave-1 remodel variants on the REAL metric (held-out σ / local-FRF), NOT MAC (Andrew: MAC masks
local-FRF error). For each edit: re-solve the full FEM (reuse remodel.build_K/build_M), match modes to .ash, then
predict each held-out sensor's peak |H| from the EDITED FEM mode shapes at the sensor channels (measured .ash poles +
damping, complex LSQ on observed channels) — exactly the shape_diag construction but with the edited full-FEM modes.
σ_edit = std of held-out peak log-error. Compare to baseline σ (nominal=1.26) and the measured-shape oracle (0.70).
Saves channel modes per variant (out/edits/<id>/modes.npz) so future QOI re-scores are free. Resumable.
Output: out/rescore_sigma.json + console.
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
sys.path.insert(0, str(Path(__file__).resolve().parent))
import remodel as RM
import realfrf as rf
from modal_multiref import CACHE, N_MODAL
import multiref_frf as mr

WS = Path(__file__).resolve().parent.parent; OUT = WS / "out"
AX = {"X": 0, "Y": 1, "Z": 2}; K_EIG, SIGMA = 80, -1.0e3
t0 = time.time()
def log(m): print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)

R = rf.load_reduced()
ch = rf.build_channels(R, [d for d in range(1, 116) if d not in rf.BAD_DAQ])
c = dict(np.load(CACHE / "m_xpos_990x.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
freqs = c["freqs"]; w = 2 * np.pi * freqs
common = [d for d in ch.daq if d in c["daq"]]; pos = {d: i for i, d in enumerate(ch.daq)}; ci = {d: c["daq"].index(d) for d in common}
SENSOR_DOF = {d: 6 * int(ch.nodes[pos[d]]) + AX[ch.axes[pos[d]]] for d in common}  # ch.nodes = grid INDEX (not GID)
HMEAS = {d: c["H1"][ci[d]] for d in common}
mm = np.load(RM.MM, allow_pickle=True); mfreqs = mm["freqs"]; ash_damp = mm["damp"] / 100.0
tau = -(N_MODAL - 1) / (rf.FS * np.log(mr.PROC["exp_end"]))
rng = np.random.default_rng(0); perm = rng.permutation(len(common)); n_obs = int(round(0.9 * len(common)))
OBS = [common[i] for i in perm[:n_obs]]; HO = [common[i] for i in perm[n_obs:]]
dn = int(np.argmin(np.linalg.norm(RM.XYZ - np.array([9.0, 7.6, 0.6]), axis=1)))   # +X drive node (Test01)
DRIVE_DOF = 6 * dn + AX["X"]
T = sp.load_npz(os.path.join(RM.MAT, "T.npz"))
RIDGE = 1e-3


def sigma_from_vecs(vecs, MAC):
    ridx, kidx = [], []
    for it in range(33):
        jf = int(np.argmax(MAC[it, 6:]) + 6)
        if MAC[it, jf] > 0.3:
            ridx.append(it); kidx.append(jf)
    wr = mfreqs[ridx] * 2 * np.pi; eta = 2.0 * (ash_damp[ridx] + 1.0 / (2 * np.pi * mfreqs[ridx] * tau))
    dofs = np.array([SENSOR_DOF[d] for d in common])
    Phi = np.asarray(T[dofs, :] @ vecs)[:, kidx]                       # (Ncommon, nmode) edited FEM shapes at channels
    pd = np.asarray(T[DRIVE_DOF, :] @ vecs).ravel()[kidx]              # drive participation
    denom = (1 + 1j * eta)[None, :] * (wr ** 2)[None, :] - (w ** 2)[:, None]
    def basis(daqs):
        sc = np.array([Phi[common.index(d)] for d in daqs])            # (Ns,nmode)
        return (-(w ** 2)[:, None, None]) * (sc[None, :, :] * pd[None, None, :]) / denom[:, None, :]
    M_obs = basis(OBS); M_ho = basis(HO); nm = len(kidx)
    H_obs = np.array([HMEAS[d] for d in OBS]).T
    A = M_obs.reshape(-1, nm); b = H_obs.reshape(-1)
    AhA = A.conj().T @ A + RIDGE * np.eye(nm) * np.real(np.trace(A.conj().T @ A)) / nm
    a_r = np.linalg.solve(AhA, A.conj().T @ b)
    H_ho_pred = M_ho @ a_r; H_ho_tru = np.array([HMEAS[d] for d in HO]).T
    err = np.log(np.abs(H_ho_pred).max(0) + 1e-300) - np.log(np.abs(H_ho_tru).max(0) + 1e-300)
    return float(np.std(err)), float(np.median(np.abs(err)) * 20 / np.log(10)), nm, len(kidx), Phi, pd, np.array(kidx)


def run_edit(eid, edit):
    od = OUT / "edits" / eid; od.mkdir(parents=True, exist_ok=True)
    sj = od / "sigma.json"
    if sj.exists():
        log(f"[{eid}] sigma already done — skip"); return json.load(open(sj))
    Kr = (T.T @ RM.build_K(edit) @ T).tocsc(); Mr = (T.T @ RM.build_M(edit) @ T).tocsc()
    log(f"[{eid}] eigsh...")
    vals, vecs = eigsh(Kr, k=K_EIG, M=Mr, sigma=SIGMA, which="LM")
    order = np.argsort(vals); vals, vecs = vals[order], vecs[:, order]
    freqs_fem = np.sqrt(np.clip(vals, 0, None)) / (2 * np.pi)
    mshapes, mmask = mm["shapes"], mm["measured"]
    obs_dofs = np.array([6 * RM.G2I[int(n)] + cc for n in mm["nodes"] for cc in range(3)])
    obs_V = np.asarray(T[obs_dofs, :] @ vecs); live = mmask.reshape(-1)
    pf_, pt = obs_V[live, :], mshapes.reshape(33, -1)[:, live]
    MAC = (pt @ pf_) ** 2 / (np.sum(pt ** 2, 1)[:, None] * np.sum(pf_ ** 2, 0)[None, :] + 1e-300)
    sig, dbmed, nm, nmatch, Phi, pd, kidx = sigma_from_vecs(vecs, MAC)
    np.savez_compressed(od / "modes.npz", Phi=Phi, pd=pd, kidx=kidx, daq=np.array(common),
                        freqs_fem=freqs_fem[kidx])
    rec = {"edit_id": eid, "heldout_sigma": round(sig, 3), "heldout_median_abs_db": round(dbmed, 1),
           "n_matched_modes": nmatch, "runtime_s": round(time.time() - t0, 1)}
    json.dump(rec, open(sj, "w"), indent=1)
    log(f"[{eid}] held-out σ = {sig:.3f} (median |err| {dbmed:.1f} dB) [baseline 1.26, oracle 0.70]")
    return rec


if __name__ == "__main__":
    ids = list(RM.EDITS) if (len(sys.argv) < 2 or sys.argv[1] == "all") else [sys.argv[1]]
    rows = []
    for eid in ids:
        try:
            rows.append(run_edit(eid, RM.EDITS[eid]))
        except Exception as e:
            log(f"[{eid}] FAILED: {e}")
    base = next((r["heldout_sigma"] for r in rows if r["edit_id"] == "baseline"), None)
    summ = {"baseline_sigma": base, "oracle_sigma": 0.70, "variants": rows}
    (OUT / "rescore_sigma.json").write_text(json.dumps(summ, indent=2))
    log("=== held-out σ by variant (lower=better; baseline FEM 1.26, measured-shape oracle 0.70) ===")
    for r in sorted(rows, key=lambda x: x["heldout_sigma"]):
        log(f"  {r['edit_id']:22s} σ={r['heldout_sigma']:.3f}  (median |err| {r['heldout_median_abs_db']:.1f} dB)")
