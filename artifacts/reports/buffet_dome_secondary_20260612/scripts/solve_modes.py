#!/usr/bin/env python3
"""Detached, resumable modal solve for the fine-region model (both BCs).

Marching shift-invert Lanczos: windows of k modes around increasing shifts
until coverage passes F_TOP Hz. Resumable: after each window the partial
result is written; on restart, finished work is skipped (compute gate,
AGENTS.md). Mass-normalized full-space shapes saved float32.

Usage: python3 scripts/solve_modes.py [bcA|bcB]
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

WS = Path(__file__).resolve().parent.parent
BC = sys.argv[1] if len(sys.argv) > 1 else "bcA"   # any model tag, e.g. bcA_kmlo
F_TOP = float(sys.argv[2]) if len(sys.argv) > 2 else 820.0  # Hz (2x band + margin)
K_WIN = 250
MAX_WIN = 40

d = np.load(WS / "out" / f"model_{BC}.npz")
n = int(d["shape"])
K = sp.csr_matrix((d["K_data"], d["K_indices"], d["K_indptr"]), shape=(n, n))
M = sp.csr_matrix((d["M_data"], d["M_indices"], d["M_indptr"]), shape=(n, n))
# variant models share the nominal node count unless they wrote their own xyz
xyz_p = WS / "out" / ("xyz_" + BC.split("_", 1)[1] + ".npy") if "_" in BC \
    else WS / "out" / "xyz.npy"
if not xyz_p.exists():
    xyz_p = WS / "out" / "xyz.npy"
NDOF_FULL = int(np.load(xyz_p).shape[0]) * 6

if "free" in d.files:                  # fixed-boundary reduction (BC-A style)
    free = d["free"]
    def expand(V):
        out = np.zeros((NDOF_FULL, V.shape[1]), dtype=np.float32)
        out[free] = V
        return out
else:                                  # RBE2/T reduction (BC-B style)
    T = sp.csr_matrix((d["T_data"], d["T_indices"], d["T_indptr"]),
                      shape=tuple(d["T_shape"]))
    def expand(V):
        return (T @ V).astype(np.float32)

out_path = WS / "out" / f"modes_{BC}.npz"
log = open(WS / "logs" / f"solve_{BC}.log", "a")
def say(msg):
    log.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n"); log.flush()
    print(msg, flush=True)

fs, Phi = np.zeros(0), np.zeros((NDOF_FULL, 0), dtype=np.float32)
if out_path.exists():
    z = np.load(out_path)
    fs, Phi = z["f"], z["Phi"]
    say(f"resume: {len(fs)} modes loaded, fmax {fs.max() if len(fs) else 0:.1f}")

t_all = time.time()
sigma_f = 5.0 if len(fs) == 0 else float(max(5.0, fs.max()))
for win in range(MAX_WIN):
    if len(fs) and fs.max() >= F_TOP:
        break
    sigma = -(2 * np.pi * 30) ** 2 if (BC.startswith("bcB") and len(fs) == 0) \
        else (2 * np.pi * sigma_f) ** 2
    t0 = time.time()
    say(f"window {win}: sigma_f={sigma_f:.1f} Hz k={K_WIN}")
    w, v = spla.eigsh(K, k=K_WIN, M=M, sigma=sigma, which="LM")
    fw = np.sqrt(np.clip(w, 0, None)) / (2 * np.pi)
    order = np.argsort(fw); fw, v = fw[order], v[:, order]
    # mass-normalize in reduced space
    nrm = np.sqrt(np.einsum("ij,ij->j", v, M @ v))
    v = v / nrm
    Vf = expand(v)
    # dedupe vs existing using MAC where frequencies are close
    keep = []
    for j in range(len(fw)):
        close = np.where(np.abs(fs - fw[j]) < max(0.5, 2e-3 * fw[j]))[0]
        dup = False
        for c in close:
            num = float(Phi[:, c].astype(np.float64) @ Vf[:, j].astype(np.float64))
            if num ** 2 > 0.98:          # both unit-M-norm -> MAC ~ (phi1.M.phi2)^2
                dup = True
                break
        if not dup:
            keep.append(j)
    fs = np.concatenate([fs, fw[keep]])
    Phi = np.concatenate([Phi, Vf[:, keep]], axis=1)
    order = np.argsort(fs); fs = fs[order]; Phi = Phi[:, order]
    np.savez_compressed(out_path, f=fs, Phi=Phi)
    say(f"  window done in {time.time()-t0:.0f}s: +{len(keep)} new "
        f"(total {len(fs)}), span {fw.min():.1f}-{fw.max():.1f} Hz")
    sigma_f = float(fw.max())

meta = dict(bc=BC, n_modes=int(len(fs)),
            n_below_400=int((fs < 400).sum()),
            n_below_820=int((fs < 820).sum()),
            fmax=float(fs.max()) if len(fs) else 0.0,
            runtime_s=time.time() - t_all)
json.dump(meta, open(WS / "out" / f"modes_{BC}_meta.json", "w"), indent=1)
say(json.dumps(meta))
