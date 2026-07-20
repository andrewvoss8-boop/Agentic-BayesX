#!/usr/bin/env python3
"""Enrich the reduction basis so the reduced surrogate stays accurate across
the FULL prior support (not just near theta=1).

Why: a fixed nominal-mode basis reproduces nominal exactly, but when the soft
hand-tuned joint springs are scaled to the prior edge their mode SHAPES move
out of the nominal span, giving up to ~2.7% reduced-vs-full frequency error
(comparable to the ~1% measurement noise floor). That would bias the joints
posterior. Fix = add off-nominal full-solve SNAPSHOTS at the joint/contact
prior edges and POD/mass-orthonormalize the union.

Snapshots (full sparse eigsh, ~5 min each):
  S1 joints+contact = 0.6   (prior ~2.5th percentile)
  S2 joints+contact = 1.6   (prior ~97.5th percentile)
Boxes/plates need no enrichment (modulus changes keep shapes; <0.6% error).

Outputs (overwrite): matrices/reduced_blocks.npz with enriched Phi,
                     matrices/Phi_keep.npy, enrich_report.json
Re-probe is done by reduce_model-style comparison appended here.
"""
import json
import os
import time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

SNAPSHOTS = [
    {"joints": 0.6, "contact": 0.6},
    {"joints": 1.6, "contact": 1.6},
]
PROBES = {                              # re-validate after enrichment
    "joints_soft":  {"joints": 0.5, "contact": 0.5},   # beyond prior (stress)
    "joints_edge":  {"joints": 0.6, "contact": 0.6},   # at prior edge
    "box_split":    {"bottom_box": 0.8, "top_box": 1.2},
    "mixed":        {"joints": 0.7, "top_box": 1.15, "plates": 0.85},
}
K_FULL = 80
F_REPORT = 280.0
SIGMA = -1.0e3

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
FIXED = ["bush_99"]

t0 = time.time()
def log(m): print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)

T = sp.load_npz("matrices/T.npz")
M = sp.load_npz("matrices/M.npz")
Mr = (T.T @ M @ T).tocsc()
gnames = sorted(GROUPS)

# group full-space blocks and their keep-space reductions
Kfull, Kr_g = {}, {}
for g in gnames + ["__fix__"]:
    pids = FIXED if g == "__fix__" else GROUPS[g]
    Kg = None
    for p in pids:
        Kp = sp.load_npz(f"matrices/K_{p}.npz")
        Kg = Kp if Kg is None else Kg + Kp
    Kfull[g] = Kg
    Kr_g[g] = (T.T @ Kg @ T).tocsc()
log("group blocks reduced to keep-space")

def Kr_at(theta):
    K = Kr_g["__fix__"].copy()
    for g in gnames:
        K = K + theta.get(g, 1.0) * Kr_g[g]
    return K.tocsc()

# nominal elastic basis (keep-space)
V = np.load("matrices/V_keep.npy")[:, 6:]          # (n_keep, 74)
snaps = [V]
for i, th in enumerate(SNAPSHOTS):
    log(f"snapshot {i+1} {th}: full eigsh ...")
    lam, vec = eigsh(Kr_at(th), k=K_FULL, M=Mr, sigma=SIGMA, which='LM')
    vec = vec[:, np.argsort(lam)][:, 6:]           # elastic only
    snaps.append(vec)
    log(f"  snapshot {i+1} done")

U = np.concatenate(snaps, axis=1)                  # (n_keep, ~222)
log(f"union basis {U.shape}; POD mass-orthonormalize ...")
G = U.T @ (Mr @ U)
w, S = np.linalg.eigh(G)
tol = w.max() * 1e-9
keep = w > tol
Phi = U @ (S[:, keep] / np.sqrt(w[keep]))          # (n_keep, r), Phi'MrPhi=I
r = Phi.shape[1]
orth = float(np.abs(Phi.T @ (Mr @ Phi) - np.eye(r)).max())
log(f"enriched basis r={r}, M-orthonormality residual {orth:.2e}")

A = {g: Phi.T @ (Kr_g[g] @ Phi) for g in gnames}
A_fix = Phi.T @ (Kr_g["__fix__"] @ Phi)

# observation operator on enriched basis
obs_dofs = np.load("matrices/obs_dofs.npy")
T_obs = T[obs_dofs, :]
obs_Phi = np.asarray(T_obs @ Phi)                  # (228, r)

# nominal eigenvalues from enriched reduced model (sanity)
K1 = A_fix + sum(A.values())
nom = np.sort(np.linalg.eigvalsh(K1))
vals_full = np.load("matrices/eigvals.npy")[6:]
nom_err = np.abs(nom[:len(vals_full)] - vals_full) / vals_full

np.save("matrices/Phi_keep.npy", Phi)
np.savez_compressed(
    "matrices/reduced_blocks.npz",
    gnames=np.array(gnames),
    A=np.stack([A[g] for g in gnames]),
    A_fix=A_fix, obs_V=obs_Phi,
    nominal_eigvals=vals_full, basis_r=r)

# ----- re-probe reduced vs full across prior support
def reduced_freqs(theta):
    K = A_fix + sum(theta.get(g, 1.0) * A[g] for g in gnames)
    lam = np.linalg.eigvalsh(K)
    return np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)

report = {"basis_r": int(r), "snapshots": SNAPSHOTS,
          "M_orthonormality_resid": orth,
          "nominal_max_rel_eigval_err": float(nom_err.max()),
          "probes": {}}
for pname, th in PROBES.items():
    fr = reduced_freqs(th)
    lam_f, _ = eigsh(Kr_at(th), k=60, M=Mr, sigma=SIGMA, which='LM')
    ff = np.sqrt(np.clip(np.sort(lam_f), 0, None)) / (2 * np.pi)
    ff_el = ff[6:]
    n = int(np.sum(ff_el < F_REPORT))
    derr = (fr[:n] - ff_el[:n]) / ff_el[:n]
    report["probes"][pname] = dict(
        theta=th, n=n, max_abs_rel_err=float(np.abs(derr).max()),
        median_abs_rel_err=float(np.median(np.abs(derr))))
    log(f"probe {pname}: n={n} max {np.abs(derr).max()*100:.3f}% "
        f"median {np.median(np.abs(derr))*100:.3f}%")
json.dump(report, open("enrich_report.json", "w"), indent=1)
log("done")
