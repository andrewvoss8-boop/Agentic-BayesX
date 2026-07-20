#!/usr/bin/env python3
"""Nominal (theta=1) full-order modal solve of the assembled ShockSat FEM.

Steps:
 1. K0 = sum of all per-PID stiffness blocks; M; RBE2 elimination T.
 2. Generalized eigensolve on the reduced (independent-DOF) space:
    K_r q = lam M_r q, shift-invert at sigma = -1e3 (rad/s)^2 so the six
    near-zero rigid-body eigenvalues are well separated from the shift.
 3. Checks: 6 rigid-body modes near 0 Hz; elastic frequencies vs NASA's
    published FINAL-FEM (Oct 2021) frequencies; MAC of our modes vs the
    MEASURED test shapes (.ash) at the 76 accelerometer nodes.

Outputs: matrices/V_keep.npy (mass-orthonormal eigenvectors, keep-space),
         matrices/obs_V.npy (observation matrix at accel nodes, 228 x k),
         nominal_modes.json, nominal_mac_table.json
"""
import json
import os
import time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

K_EIG = 80          # eigenpairs to extract (6 RBM + ~74 elastic, > 300 Hz)
SIGMA = -1.0e3      # shift (rad/s)^2

# NASA published frequencies, Final_Summary_Documentation_101521_rev1.pptx
# slides 21-45: measured test mode <-> FINAL (Oct 2021) FEM mode pairing.
# None = NASA reported no FEM partner for test mode 24 (213.9 Hz).
NASA_TEST = [54.19, 69.98, 74.98, 85.78, 107.03, 117.63, 118.53, 125.0,
             137.2, 142.4, 151.2, 158.2, 165.9, 168.0, 172.3, 174.8, 184.4,
             188.6, 190.2, 195.7, 197.8, 198.9, 203.0, 213.9, 222.1]
NASA_FEM = [54.67, 73.51, 73.09, 87.94, 102.23, 108.17, 113.43, 116.9,
            137.9, 154.5, 151.8, 135.9, 160.4, 183.4, 185.0, 164.5, 182.7,
            189.3, 191.0, 192.6, 191.9, 193.5, 191.4, None, 211.1]

t0 = time.time()

def log(msg):
    print(f"[{time.time()-t0:7.1f}s] {msg}", flush=True)

# ---------------------------------------------------------------- assemble
Ktot = None
for f in sorted(os.listdir("matrices")):
    if f.startswith("K_"):
        Kp = sp.load_npz(f"matrices/{f}")
        Ktot = Kp if Ktot is None else Ktot + Kp
M = sp.load_npz("matrices/M.npz")
T = sp.load_npz("matrices/T.npz")
log(f"loaded K (nnz {Ktot.nnz}), M, T {T.shape}")

Kr = (T.T @ Ktot @ T).tocsc()
Mr = (T.T @ M @ T).tocsc()
log(f"reduced: Kr nnz {Kr.nnz}, Mr nnz {Mr.nnz}, n {Kr.shape[0]}")

# ---------------------------------------------------------------- eigsh
vals, vecs = eigsh(Kr, k=K_EIG, M=Mr, sigma=SIGMA, which='LM')
order = np.argsort(vals)
vals, vecs = vals[order], vecs[:, order]
freqs = np.sqrt(np.clip(vals, 0, None)) / (2 * np.pi)
log(f"eigsh done: f[0:8] = {np.round(freqs[:8], 3)}")
log(f"elastic f[6:31] = {np.round(freqs[6:31], 2)}")

n_rbm = int(np.sum(freqs < 5.0))
assert n_rbm == 6, f"expected 6 RBMs < 5 Hz, got {n_rbm}"

np.save("matrices/V_keep.npy", vecs)
np.save("matrices/eigvals.npy", vals)

# ------------------------------------------------- observation operator
mm = np.load("measured_modes.npz", allow_pickle=True)
nodes, mfreqs, mshapes, mmask = (mm["nodes"], mm["freqs"], mm["shapes"],
                                 mm["measured"])
z = np.load("fem_model.npz", allow_pickle=True)
g2i = {int(g): i for i, g in enumerate(z["gids"])}
obs_dofs = np.array([6 * g2i[int(n)] + c for n in nodes for c in range(3)])
T_obs = T[obs_dofs, :]                      # (228, n_keep) sparse
obs_V = np.asarray(T_obs @ vecs)            # (228, K_EIG) translations x,y,z
np.save("matrices/obs_V.npy", obs_V)
np.save("matrices/obs_dofs.npy", obs_dofs)

# MAC on the 132 measured DOFs only
live = mmask.reshape(-1)                    # (228,) True where measured
phi_fem = obs_V[live, :]                    # (132, K_EIG)
phi_tst = mshapes.reshape(33, -1)[:, live]  # (33, 132)

num = (phi_tst @ phi_fem) ** 2
den = (np.sum(phi_tst ** 2, axis=1)[:, None] *
       np.sum(phi_fem ** 2, axis=0)[None, :])
MAC = num / den                             # (33 test, K_EIG fem)

pairs = []
for it in range(33):
    jf = int(np.argmax(MAC[it, 6:]) + 6)    # elastic modes only
    pairs.append(dict(
        test_mode=it + 1, f_test=float(mfreqs[it]),
        fem_mode=jf - 5, f_fem=float(freqs[jf]),
        mac=float(MAC[it, jf]),
        df_pct=float(100 * (freqs[jf] / mfreqs[it] - 1))))

# NASA comparison: our ascending elastic frequencies vs NASA FEM ascending
ours_el = freqs[6:]
nasa_fem_sorted = sorted(x for x in NASA_FEM if x is not None)
cmp_rows = []
for i, nf in enumerate(nasa_fem_sorted):
    cmp_rows.append(dict(nasa_fem_sorted_i=i + 1, f_nasa_fem=nf,
                         f_ours=float(ours_el[i]) if i < len(ours_el) else None,
                         d_pct=float(100 * (ours_el[i] / nf - 1))
                         if i < len(ours_el) else None))

out = dict(
    k_eig=K_EIG, sigma=SIGMA, n_keep=int(Kr.shape[0]),
    rbm_freqs_hz=[float(f) for f in freqs[:6]],
    elastic_freqs_hz=[float(f) for f in freqs[6:]],
    nasa_test=NASA_TEST, nasa_fem=NASA_FEM,
    ours_vs_nasa_fem_ascending=cmp_rows,
    eigsh_seconds=round(time.time() - t0, 1))
json.dump(out, open("nominal_modes.json", "w"), indent=1)
json.dump(dict(mac_pairs=pairs), open("nominal_mac_table.json", "w"), indent=1)

log("MAC pairing (test -> our elastic mode):")
for p in pairs[:25]:
    log(f"  test {p['test_mode']:2d} {p['f_test']:7.2f} Hz -> "
        f"fem {p['fem_mode']:2d} {p['f_fem']:7.2f} Hz  "
        f"MAC {p['mac']:.3f}  df {p['df_pct']:+.2f}%")
log("done")
