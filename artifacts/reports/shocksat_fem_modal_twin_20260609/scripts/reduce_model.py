#!/usr/bin/env python3
"""Parametric model-order reduction for the ShockSat modal twin.

Basis: the 74 mass-orthonormal ELASTIC eigenvectors of the nominal model
(rigid-body modes excluded). In that basis the reduced stiffness is
    K_red(theta) = sum_g theta_g * A_g,    A_g = V' (T' K_g T) V   (74x74)
and the reduced mass is exactly the identity, so
    modes(theta) = eigh(K_red(theta))  -- small, dense, differentiable.

Reduction error (Discretization-Resolution gate): a NON-UNIFORM theta is
required for an honest probe — under uniform scaling theta_g = c both the
full and reduced frequencies scale exactly by sqrt(c), so the error is
identically zero and proves nothing. Probes:
  P1 "joints_soft":  joints x0.5, contact x0.5      (the hand-tuned part)
  P2 "box_split":    bottom_box x0.8, top_box x1.2  (shell modulus split)
Each probe re-solves the FULL sparse model (eigsh, ~6 min) and compares
per-mode frequencies against the reduced eigh.

Outputs: matrices/reduced_blocks.npz (A_g per group + obs basis),
         groups.json, reduction_report.json
"""
import json
import os
import time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

GROUPS = {
    "bottom_box":     ["shell_101", "shell_102", "shell_103"],
    "steel_welds":    ["shell_104", "shell_105", "shell_106"],
    "top_box":        ["shell_201", "shell_202", "shell_203"],
    "al_welds":       ["shell_204", "shell_205", "shell_206"],
    "angle_brackets": ["shell_301", "shell_302"],
    "cross_beam":     ["shell_401"],
    "plates":         ["shell_501", "shell_601", "shell_701"],
    "joints":         ["bush_801", "bush_802", "bush_803", "bush_804",
                       "bush_805", "bush_806", "bush_807"],
    "contact":        ["bush_902"],
}
FIXED = ["bush_99"]          # accelerometer mounts: theta fixed at 1
PROBES = {
    "joints_soft": {"joints": 0.5, "contact": 0.5},
    "box_split":   {"bottom_box": 0.8, "top_box": 1.2},
}
F_REPORT = 280.0             # report reduction error for modes below this (Hz)

t0 = time.time()
def log(m): print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)

T = sp.load_npz("matrices/T.npz")
M = sp.load_npz("matrices/M.npz")
V = np.load("matrices/V_keep.npy")          # (n_keep, 80) M-orthonormal
vals = np.load("matrices/eigvals.npy")
Ve = V[:, 6:]                                # elastic basis, 74 cols
W = np.asarray(T @ Ve)                       # full-space basis (n_full, 74)
log(f"basis W {W.shape}")

def load_block(name):
    return sp.load_npz(f"matrices/K_{name}.npz")

A = {}                                       # group -> (74,74)
Kfull = {}                                   # group -> sparse full block
for g, pids in GROUPS.items():
    Kg = None
    for p in pids:
        Kp = load_block(p)
        Kg = Kp if Kg is None else Kg + Kp
    Kfull[g] = Kg
    A[g] = W.T @ (Kg @ W)
    log(f"A[{g}] done, fro {np.linalg.norm(A[g]):.3e}")
Kfix = None
for p in FIXED:
    Kp = load_block(p)
    Kfix = Kp if Kfix is None else Kfix + Kp
A_fix = W.T @ (Kfix @ W)

# consistency: sum of all blocks at theta=1 must reproduce nominal eigvals
K1 = A_fix + sum(A.values())
nom_err = np.abs(np.sort(np.linalg.eigvalsh(K1)) - vals[6:]) / vals[6:]
log(f"nominal consistency: max rel eigval err {nom_err.max():.2e}")

gnames = sorted(GROUPS)
np.savez_compressed(
    "matrices/reduced_blocks.npz",
    gnames=np.array(gnames),
    A=np.stack([A[g] for g in gnames]),      # (9,74,74)
    A_fix=A_fix,
    nominal_eigvals=vals[6:],
    obs_V=np.load("matrices/obs_V.npy")[:, 6:])   # (228,74) elastic only
json.dump(dict(groups=GROUPS, fixed=FIXED,
               note="theta_g scales the stiffness blocks of these PIDs; "
                    "exact modulus scaling (K linear in E, k)"),
          open("groups.json", "w"), indent=1)

# ---------------------------------------------------- reduction-error probes
def reduced_freqs(theta):
    K = A_fix + sum(theta.get(g, 1.0) * A[g] for g in gnames)
    lam = np.linalg.eigvalsh(K)
    return np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)

report = {"nominal_consistency_max_rel_eigval_err": float(nom_err.max()),
          "basis_size": int(Ve.shape[1]),
          "basis_fmax_hz": float(np.sqrt(vals[-1]) / (2 * np.pi)),
          "f_report_hz": F_REPORT, "probes": {}}

Mr_cache = None
for pname, th in PROBES.items():
    fr = reduced_freqs(th)
    # full model at this theta
    Ktheta = Kfix.copy()
    for g in gnames:
        Ktheta = Ktheta + th.get(g, 1.0) * Kfull[g]
    Kr = (T.T @ Ktheta @ T).tocsc()
    if Mr_cache is None:
        Mr_cache = (T.T @ M @ T).tocsc()
    log(f"probe {pname}: full eigsh ...")
    lam_f, _ = eigsh(Kr, k=60, M=Mr_cache, sigma=-1.0e3, which='LM')
    lam_f = np.sort(lam_f)
    ff = np.sqrt(np.clip(lam_f, 0, None)) / (2 * np.pi)
    ff_el = ff[6:]                                   # drop RBMs
    n = int(np.sum(ff_el < F_REPORT))
    derr = (fr[:n] - ff_el[:n]) / ff_el[:n]
    report["probes"][pname] = dict(
        theta=th, n_modes_compared=n,
        full_freqs_hz=[round(float(x), 3) for x in ff_el[:n]],
        reduced_freqs_hz=[round(float(x), 3) for x in fr[:n]],
        rel_err=[float(x) for x in derr],
        max_abs_rel_err=float(np.abs(derr).max()),
        median_abs_rel_err=float(np.median(np.abs(derr))))
    log(f"probe {pname}: {n} modes < {F_REPORT} Hz, "
        f"max |df|/f = {np.abs(derr).max():.2e}, "
        f"median = {np.median(np.abs(derr)):.2e}")

json.dump(report, open("reduction_report.json", "w"), indent=1)
log("done")
