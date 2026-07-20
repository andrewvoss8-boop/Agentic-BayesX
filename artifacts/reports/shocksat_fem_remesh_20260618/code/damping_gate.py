#!/usr/bin/env python3
"""Card D / L-damp GATE (a) — damping-dissipation-fraction identifiability gate.

The damping analog of the strain-energy identifiability table. For
stiffness-proportional localized dampers C_g = beta_g * K_g, the modal damping of
mode m is
    zeta_{m,g} = (beta_g * omega_m / 2) * f_{m,g},   f_{m,g} = phi_m^T K_g phi_m / lambda_m
(f = strain-energy fraction; phi mass-normalized). Adding Rayleigh (alpha0 M +
alpha1 K) the model for the measured per-mode damping is the LINEAR system
    zeta_m = alpha0/(2 omega_m) + alpha1 omega_m/2 + sum_g (beta_g omega_m/2) f_{m,g}.

This script (NO eigensolve; reuses V_keep + per-PID K blocks):
  1. computes f_{m,g} for the FEM modes paired to the 33 measured modes,
  2. builds the design matrix A (columns = Rayleigh + per-group dampers),
  3. reports IDENTIFIABILITY: SVD/condition number + how many damper combinations
     clear (effective rank), which raw groups each strong combination mixes,
  4. fits the measured zeta (NNLS, damping>=0) and reports per-group damping share
     and the fit residual (does interface-localized damping reproduce the spread?).
Identifiability (conditioning) is UNIT-INDEPENDENT of zeta; only the fitted beta
magnitudes and 'reproduces-the-spread' depend on the zeta values/units.
"""
import json, os
import numpy as np
import scipy.sparse as sp

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)
groups = json.load(open("groups.json"))["groups"]   # group -> [block names]
GNAMES = list(groups.keys())

V = np.load("matrices/V_keep.npy")          # (n_keep, 80) mass-normalized
vals = np.load("matrices/eigvals.npy")      # (80,)
T = sp.load_npz("matrices/T.npz")
U = T @ V                                    # (NDOF, 80) full-space modes
freqs = np.sqrt(np.clip(vals, 0, None)) / (2*np.pi)

# per-group reduced strain energy phi^T K_g phi  for all modes
def group_K(g):
    Ksum = None
    for blk in groups[g]:
        Kp = sp.load_npz(f"matrices/K_{blk}.npz")
        Ksum = Kp if Ksum is None else Ksum + Kp
    return Ksum

SE = np.zeros((80, len(GNAMES)))            # phi^T K_g phi
for j, g in enumerate(GNAMES):
    Kg = group_K(g)
    KU = Kg @ U                              # (NDOF,80)
    SE[:, j] = np.einsum("ij,ij->j", U, KU)  # diag(U^T Kg U)
# strain-energy fraction f_{m,g} = (phi^T K_g phi)/lambda
f_mg = SE / vals[:, None]
# sanity: rows sum to ~1 for elastic modes
row_sum = f_mg[6:].sum(1)

# measured damping per mode, MAC-paired (test_mode -> fem elastic mode)
pairs = json.load(open("nominal_mac_table.json"))["mac_pairs"]
mm = np.load("measured_modes.npz", allow_pickle=True)
zeta_ash = mm["damp"]                        # (33,) — flagged: interpret as PERCENT -> /100
rows = []
for p in pairs:
    if p["mac"] < 0.3:
        continue
    tm = p["test_mode"]; fem_el = p["fem_mode"]   # 1-based elastic index
    k = fem_el + 5                                  # column in V (6 RBM first)
    w = 2*np.pi*freqs[k]
    rows.append(dict(test_mode=tm, fem_col=k, f_hz=float(freqs[k]),
                     omega=float(w), zeta_meas=float(zeta_ash[tm-1]/100.0),
                     f_mg=f_mg[k].tolist()))

om = np.array([r["omega"] for r in rows])
zeta = np.array([r["zeta_meas"] for r in rows])
F = np.array([r["f_mg"] for r in rows])             # (Nmodes, Ngroups)

# design matrix columns: [alpha0: 1/(2w)] [alpha1: w/2] [beta_g: (w/2) f_{m,g}]
A = np.column_stack([1.0/(2*om), om/2.0, (om/2.0)[:, None]*F])
colnames = ["rayleigh_alpha0", "rayleigh_alpha1"] + [f"beta_{g}" for g in GNAMES]

# scale columns to unit norm for conditioning (identifiability is about shape)
cn = np.linalg.norm(A, axis=0); cn[cn == 0] = 1.0
As = A / cn
sv = np.linalg.svd(As, compute_uv=False)
cond = float(sv[0]/sv[-1])
# effective rank: singular values within 1e3 of the top (combos that clear)
eff_rank = int(np.sum(sv > sv[0]/1e3))
# which raw params each leading right-singular vector mixes
_, _, Vt = np.linalg.svd(As, full_matrices=False)

# NNLS fit (damping >= 0) of measured zeta
from scipy.optimize import nnls
coef, rnorm = nnls(A, zeta)
zeta_fit = A @ coef
# per-group damping share of each mode (only the beta part)
beta = coef[2:]
contrib_g = (om[:, None]/2.0) * F * beta[None, :]    # (Nmodes, Ngroups) zeta from each group
ray = coef[0]/(2*om) + coef[1]*om/2.0

out = dict(
    note="L-damp gate (a): damping-dissipation-fraction identifiability. zeta_ash interpreted as PERCENT/100 (unit caveat).",
    n_modes=len(rows), groups=GNAMES,
    se_rowsum_min=float(row_sum.min()), se_rowsum_max=float(row_sum.max()),
    design_condition_number=cond, design_singular_values=sv.tolist(),
    effective_rank_of_design=eff_rank, n_params=A.shape[1],
    leading_combo_mix={colnames[i]: round(float(Vt[0, i]), 3) for i in range(len(colnames))},
    nnls_coef={colnames[i]: float(coef[i]) for i in range(len(colnames))},
    nnls_residual_norm=float(rnorm),
    zeta_meas_pct=[round(z*100, 3) for z in zeta],
    zeta_fit_pct=[round(z*100, 3) for z in zeta_fit],
    rayleigh_share_pct=[round(r*100, 3) for r in ray],
    per_group_damping_share=  # which group dominates each mode's damping
        {GNAMES[j]: round(float(contrib_g[:, j].sum()/contrib_g.sum()), 3) for j in range(len(GNAMES))}
        if contrib_g.sum() > 0 else {},
)
json.dump(out, open("out/damping_gate.json", "w"), indent=1)

print(f"n_modes={out['n_modes']}  SE rowsum [{row_sum.min():.3f},{row_sum.max():.3f}] (≈1 ok)")
print(f"\nIDENTIFIABILITY (unit-independent): design condition number = {cond:.2e}")
print(f"  singular values: {np.array2string(sv, precision=2, max_line_width=120)}")
print(f"  effective rank = {eff_rank} of {A.shape[1]} params  -> ~{eff_rank} damping combinations clear")
print(f"\nMeasured zeta spread: {zeta.min()*100:.3f}% - {zeta.max()*100:.3f}%  (n={len(rows)} modes)")
print(f"NNLS fit residual norm = {rnorm:.4e}  (fit zeta spread {zeta_fit.min()*100:.3f}-{zeta_fit.max()*100:.3f}%)")
print("\nNNLS coefficients (damping>=0):")
for i, c in enumerate(colnames):
    flag = "  <-- carries damping" if (i >= 2 and coef[i] > 0 and beta.max() > 0 and coef[i] > 0.05*beta.max()) else ""
    print(f"  {c:22s} {coef[i]:.4e}{flag}")
print("\nper-group share of total non-Rayleigh damping:")
for g, s in out["per_group_damping_share"].items():
    print(f"  {g:16s} {s*100:5.1f}%")
print("\n-> out/damping_gate.json")
