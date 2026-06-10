#!/usr/bin/env python3
"""Reduced-vs-full validation at the POSTERIOR-MEAN theta (decision D18).

The 74-mode reduced surrogate was proven exact at nominal and probed at
synthetic theta corners (reduction_report.json). This script closes the
Discretization-Resolution loop where it matters: at the theta the posterior
actually concentrates on, run ONE full sparse eigensolve and compare every
mode below 280 Hz against the reduced eigh.

Input: theta_full.json (theta_median; D29 — the converged 18-mode posterior,
the region the deployed twin uses; band design is non-converged so its
6-mode theta_median is not the right validation point).
Output: posterior_validation.json
"""
import json
import time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

F_REPORT = 280.0
t0 = time.time()
def log(m): print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)

groups = json.load(open("groups.json"))["groups"]
theta = json.load(open("theta_full.json"))["theta_median"]   # D29
log(f"posterior-median theta: { {k: round(v,4) for k,v in theta.items()} }")

# reduced
rb = np.load("matrices/reduced_blocks.npz")
gnames = [str(g) for g in rb["gnames"]]
K_red = np.asarray(rb["A_fix"]) + sum(
    theta[g] * np.asarray(rb["A"][i]) for i, g in enumerate(gnames))
lam_r = np.linalg.eigvalsh(K_red)
f_red = np.sqrt(np.clip(lam_r, 0, None)) / (2 * np.pi)

# full
T = sp.load_npz("matrices/T.npz")
M = sp.load_npz("matrices/M.npz")
Ktot = None
for g, members in groups.items():
    for m in members:
        Kp = sp.load_npz(f"matrices/K_{m}.npz") * theta[g]
        Ktot = Kp if Ktot is None else Ktot + Kp
for m in ("bush_99",):
    Ktot = Ktot + sp.load_npz(f"matrices/K_{m}.npz")
Kr = (T.T @ Ktot @ T).tocsc()
Mr = (T.T @ M @ T).tocsc()
log("full eigsh ...")
lam_f, _ = eigsh(Kr, k=60, M=Mr, sigma=-1.0e3, which='LM')
lam_f = np.sort(lam_f)
f_full = np.sqrt(np.clip(lam_f, 0, None)) / (2 * np.pi)
f_full_el = f_full[6:]

n = int(np.sum(f_full_el < F_REPORT))
err = (f_red[:n] - f_full_el[:n]) / f_full_el[:n]
out = dict(theta=theta, n_modes=n,
           full_hz=[round(float(x), 3) for x in f_full_el[:n]],
           reduced_hz=[round(float(x), 3) for x in f_red[:n]],
           rel_err=[float(x) for x in err],
           max_abs_rel_err=float(np.abs(err).max()),
           median_abs_rel_err=float(np.median(np.abs(err))),
           note="reduced-vs-full at posterior-median theta (full 18-mode "
                "converged posterior, D29)")
json.dump(out, open("posterior_validation.json", "w"), indent=1)
log(f"{n} modes < {F_REPORT} Hz: max |df|/f {np.abs(err).max():.2e}, "
    f"median {np.median(np.abs(err)):.2e}")
