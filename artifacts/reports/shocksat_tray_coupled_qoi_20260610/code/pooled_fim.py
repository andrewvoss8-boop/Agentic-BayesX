#!/usr/bin/env python3
"""Pooled-mount FIM analysis (D15, Andrew: 'could get 6 stiffnesses down to 3
without too much trouble').

Pooling = tying mount axes together (one multiplier scales the tied set), so
the pooled log-sensitivity column is the SUM of the tied columns:
J_pooled = J @ B. Evaluated at the REALIZED discrepancy floor (sigma=3.7%)
per the extended Identifiability Gate (D12): how many pooled COMBINATIONS
clear the prior precision, and is the pooled parameterization fully separable
(all eigenvalues above prior) -- the precondition for a unimodal posterior.

Honesty note: the TRUTH is NOT symmetric (mult_true = [1.22,0.82,1.48,0.85,
0.84,0.41] + off-diagonal coupling), so pooling adds deliberate model-form
error; sigma_f must absorb the x/y asymmetry. That is the realistic trade:
fewer, identifiable, slightly-wrong knobs vs many, unidentifiable ones.

Output: out/pooled_fim.json
"""
import json
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(WS, "out")
sys.path.insert(0, HERE)

rom = np.load(os.path.join(OUT, "coupled_rom.npz"))
pairing = json.load(open(os.path.join(OUT, "pairing_coupled.json")))
calib = [p for p in pairing["pairs"] if p["calib_ok"]]
m_idx = np.array([p["anchor_mode"] for p in calib])
f_data = np.array([p["f_data"] for p in calib])
B_fix, B_mount, B_tray = rom["B_fix"], rom["B_mount"], rom["B_tray"]
Qa = rom[f"anchorQ_x{pairing['anchor_mult']}"]
NAMES = ["k_tx", "k_ty", "k_tz", "k_rx", "k_ry", "k_rz"]
SIG_REAL, SIG_NOISE = 0.037, 0.003
PRIOR_PREC = 1/1.15**2


def freqs(theta_m, theta_T=np.ones(5)):
    K = (B_fix + np.einsum("j,jab->ab", theta_m, B_mount)
         + np.einsum("g,gab->ab", theta_T, B_tray))
    lam, Q = np.linalg.eigh(K)
    f = np.sqrt(np.clip(lam, 1e-12, None))/(2*np.pi)
    k = np.argmax(np.abs(Qa.T @ Q)[m_idx, :], axis=1)
    return f[k]


# full 6-param log-Jacobian at nominal
th0 = np.ones(6)
f0 = freqs(th0)
J = np.zeros((len(f_data), 6))
h = 1e-4
for j in range(6):
    tp = th0.copy()
    tp[j] = np.exp(h)
    J[:, j] = (np.log(freqs(tp)) - np.log(f0))/h

POOLINGS = {
    "P6_full (baseline)": [["k_tx"], ["k_ty"], ["k_tz"], ["k_rx"], ["k_ry"],
                           ["k_rz"]],
    "P4_symmetric (t_lat, t_z, r_lat, r_z)": [["k_tx", "k_ty"], ["k_tz"],
                                              ["k_rx", "k_ry"], ["k_rz"]],
    "P3_A (t_lat, t_z, r_all)": [["k_tx", "k_ty"], ["k_tz"],
                                 ["k_rx", "k_ry", "k_rz"]],
    "P3_B (t_all, r_lat, r_z)": [["k_tx", "k_ty", "k_tz"],
                                 ["k_rx", "k_ry"], ["k_rz"]],
    "P2 (t_all, r_all)": [["k_tx", "k_ty", "k_tz"],
                          ["k_rx", "k_ry", "k_rz"]],
}

out = dict(note=__doc__.strip().split("\n")[0], sigma_levels={},
           prior_precision=round(PRIOR_PREC, 3))
for label, groups in POOLINGS.items():
    Bmat = np.zeros((6, len(groups)))
    for gi, g in enumerate(groups):
        for nm in g:
            Bmat[NAMES.index(nm), gi] = 1.0
    Jp = J @ Bmat
    rows = {}
    for slab, sig in (("real_3.7pct", SIG_REAL), ("noise_0.3pct", SIG_NOISE)):
        ev, evec = np.linalg.eigh(Jp.T @ Jp / sig**2)
        n_id = int(np.sum(ev > PRIOR_PREC))
        rows[slab] = dict(eigenvalues=[round(float(e), 2) for e in ev],
                          n_identifiable=n_id,
                          fully_separable=bool(n_id == len(groups)))
    out["sigma_levels"][label] = dict(
        n_params=len(groups),
        groups=[" + ".join(g) for g in groups], **rows)
    r = rows["real_3.7pct"]
    print(f"{label:42s} n={len(groups)}  eig={r['eigenvalues']}  "
          f"identifiable {r['n_identifiable']}/{len(groups)}"
          f"{'  <-- FULLY SEPARABLE' if r['fully_separable'] else ''}")

json.dump(out, open(os.path.join(OUT, "pooled_fim.json"), "w"), indent=1)
print("written out/pooled_fim.json")
