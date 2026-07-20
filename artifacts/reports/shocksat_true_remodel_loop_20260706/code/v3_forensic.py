#!/usr/bin/env python3
"""Forensic for the V3 failure: rebuild the refined-dish model, solve a few modes AROUND 62.7 Hz with
eigenvectors, and report where they live (per-region kinetic-energy fractions)."""
import json, os, sys, time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F


def expand_csr(K, n):
    K = K.tocoo()
    return sp.coo_matrix((K.data, (K.row, K.col)), shape=(n, n)).tocsr()


t0 = time.time()
m0 = F.load_model()
mr, info = F.refine_region(m0, [701], note="forensic")
print("refine info:", info, flush=True)
N = 6 * len(mr["gids"])
K701_old, Md_old, _ = F.assemble_shell(m0, 701)
K701_new, Md_new, _ = F.assemble_shell(mr, 701)
Ktot = None
for pref in [f"shell_{p}" for p in (101, 102, 103, 104, 105, 106, 201, 202, 203, 204, 205, 206,
                                    301, 302, 401, 501, 601)] + \
        [f"bush_{b}" for b in (801, 802, 803, 804, 805, 806, 807, 902, 99)]:
    Kp = expand_csr(sp.load_npz(os.path.join(F.MATD, f"K_{pref}.npz")), N)
    Ktot = Kp if Ktot is None else Ktot + Kp
Ktot = Ktot + K701_new
M = expand_csr(sp.load_npz(os.path.join(F.MATD, "M.npz")), N)
pad = np.zeros(N); pad[:len(Md_old)] = Md_old
M = M - sp.diags(pad).tocsr() + sp.diags(Md_new).tocsr()
T, keep = F.build_T(mr)
Kr = (T.T @ (Ktot @ T)).tocsc()
Mr = (T.T @ (M @ T)).tocsc()
print(f"assembled in {time.time()-t0:.0f}s; solving near 62.7 Hz", flush=True)
sig = (2 * np.pi * 62.7) ** 2
lam, V = eigsh(Kr, k=8, M=Mr, sigma=sig, which="LM", tol=1e-8, ncv=48)
idx = np.argsort(lam); lam = lam[idx]; V = V[:, idx]
print("freqs found:", np.round(np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi), 3), flush=True)
# map to full space and compute per-region kinetic-energy fractions
W = T @ V                                        # (N, 8)
Mdiag_full = np.asarray(M.diagonal())
tags = np.asarray(mr["gfile"]).astype(str)
node_of = np.arange(N) // 6
regs = sorted(set(tags))
new_node_start = len(m0["gids"])
for j in range(8):
    f = np.sqrt(max(lam[j], 0)) / (2 * np.pi)
    ke = Mdiag_full * np.asarray(W[:, j]).ravel() ** 2
    tot = ke.sum()
    fr = {g: round(float(ke[tags[node_of] == g].sum() / tot), 3) for g in regs}
    fr = {k: v for k, v in fr.items() if v > 0.01}
    new_frac = float(ke[node_of >= new_node_start].sum() / tot)
    print(f"f={f:8.3f} Hz | new-node KE frac {new_frac:.3f} | regions {fr}", flush=True)
print(f"done {time.time()-t0:.0f}s")
