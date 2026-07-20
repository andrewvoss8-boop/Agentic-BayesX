#!/usr/bin/env python3
"""Modal solves + sanity gates for the MPL stand rebuild (FABLE, 2026-06-11).

SOL-103-equivalent: generalized eigensolve of the reduced (K, M).
Method: rotational DOFs without inertia are massless (translational lumping,
D8) -> they are condensed out EXACTLY (static condensation on zero-mass DOFs
is exact for eigenvalues), then a dense generalized eigensolve with
subset_by_value guarantees NO mode below the band edge is missed.

Configurations:
  nominal      : deck + shield@1.7mm steel, feet SPC (TABLE A)
  no_shield    : deck as-given (no shield groups)        (TABLE B)
  free_free    : nominal stiffness, no SPC -> exactly 6 rigid-body modes gate
  feet_springs : no SPC, stiff grounding springs (base-flexibility variant)
  sensitivity  : shield t x0.5/x2, screw k x0.01/x100, aluminum shield,
                 (drilling arm is run separately via DRILL_SCALE env)

Outputs: out/modes_<config>.json, out/modes_nominal_shapes.npz,
         out/modal_gates.json, out/strain_energy_nominal.json
BLAS pinned by run_all.sh (OMP/VECLIB=1).
"""
import json
import os
import sys
import time

import numpy as np
import scipy.linalg as sla
import scipy.sparse as sp
import scipy.sparse.linalg as spla

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(WS, "out", os.environ.get("OUT_SUBDIR", "model"))
SUFFIX = os.environ.get("MODE_SUFFIX", "")
FMAX = 500.0
FMARGIN = 620.0  # solve a little past the band edge
T0 = time.time()

meta = json.load(open(os.path.join(MODEL, "meta.json")))
arr = np.load(os.path.join(MODEL, "arrays.npz"), allow_pickle=False)
grid_ids = arr["grid_ids"]
X = arr["X"]
region = arr["region"].astype(str)
spc_idx = arr["spc_master_idx"]
NM = meta["ndof_master"]

KG = {n: sp.load_npz(os.path.join(MODEL, "groups", f"K_{n}.npz"))
      for n in meta["K_groups"]}
MG = {n: sp.load_npz(os.path.join(MODEL, "groups", f"M_{n}.npz"))
      for n in meta["M_groups"]}


def build(scal):
    K = None
    M = None
    for n, A in KG.items():
        s = scal.get(f"K_{n}", 1.0)
        if s == 0.0:
            continue
        K = s * A if K is None else K + s * A
    for n, A in MG.items():
        s = scal.get(f"M_{n}", 1.0)
        if s == 0.0:
            continue
        M = s * A if M is None else M + s * A
    return K.tocsr(), M.tocsr()


def solve_modes(K, M, fix_idx, fmax=FMARGIN, want_shapes=False):
    """Exact massless condensation + dense generalized eigh subset_by_value.
    Returns freqs (Hz), and (optionally) mass-normalized shapes expanded to the
    free master DOF set, plus the free-dof index array."""
    free = np.setdiff1d(np.arange(NM), fix_idx)
    # AUTOSPC: drop fully-disconnected DOFs (e.g. shield grids when shield
    # groups are zeroed in a variant); require they carry no mass either.
    kdiag_all = K.diagonal()
    dead = free[kdiag_all[free] == 0.0]
    if dead.size:
        assert M.diagonal()[dead].max() == 0.0, "zero-K DOF carries mass"
        free = np.setdiff1d(free, dead)
    Kf = K[np.ix_(free, free)].tocsc()
    Mf = M[np.ix_(free, free)].tocsr()
    mdiag = Mf.diagonal()
    # massive = any DOF with mass coupling (M rows with any nonzero)
    massive = np.where(mdiag > 0)[0]
    massless = np.where(mdiag == 0)[0]
    # M must have no off-diagonal coupling into massless rows (lumped: true)
    Koo = Kf[np.ix_(massless, massless)]
    Kom = Kf[np.ix_(massless, massive)]
    lu = spla.splu(Koo.tocsc())
    S = lu.solve(Kom.toarray())                     # Koo^-1 Kom
    Kred = (Kf[np.ix_(massive, massive)].toarray()
            - Kf[np.ix_(massive, massless)].toarray() @ S)
    Mred = Mf[np.ix_(massive, massive)].toarray()
    Kred = 0.5 * (Kred + Kred.T)
    lam_hi = (2 * np.pi * fmax) ** 2
    w2, V = sla.eigh(Kred, Mred, subset_by_value=(-np.inf, lam_hi),
                     driver="gvx")
    freqs = np.sign(w2) * np.sqrt(np.abs(w2)) / (2 * np.pi)
    if not want_shapes:
        return freqs, None, free
    Phi = np.zeros((NM, V.shape[1]))
    Phi_free = np.zeros((free.size, V.shape[1]))
    Phi_free[massive] = V
    Phi_free[massless] = -S @ V
    Phi[free] = Phi_free
    return freqs, Phi, free


def region_dofs_mask():
    """Masks of master DOFs by region for KE attribution (via M groups)."""
    return None


# ------------------------------------------------------------------ nominal
nominal = dict(meta["nominal_scalars"])
K, M = build(nominal)
freqs, Phi, free = solve_modes(K, M, spc_idx, want_shapes=True)
n_500 = int(np.sum(freqs <= FMAX))
print(f"[nominal] modes <= {FMAX} Hz: {n_500} (solved to {FMARGIN} Hz: "
      f"{freqs.size}); f1={freqs[0]:.2f} Hz; elapsed {time.time()-T0:.0f}s")

# KE fractions per M-group, SE fractions per K-group (identifiability gate)
lam = (2 * np.pi * freqs) ** 2
KE = {}
for n, A in MG.items():
    KE[n] = np.einsum("ij,ij->j", Phi, A @ Phi)
KE_tot = sum(KE.values())
SE = {}
for n, A in KG.items():
    if nominal.get(f"K_{n}", 1.0) == 0.0:
        continue
    SE[n] = np.einsum("ij,ij->j", Phi, A @ Phi) / np.maximum(lam, 1e-30)


def ke_region_label(j):
    m = {"frame": KE["m_beam_wall"][j] + KE["m_beam_rest"][j],
         "thrust_plate": KE["m_plate"][j], "shield": KE["m_shield"][j],
         "valve_panel": KE["m_valveframe"][j] + KE["m_valvemass"][j],
         "electronics_box": KE["m_ebox"][j],
         "white_box_upper": KE["m_wbox"][j]}
    tot = KE_tot[j]
    fr = {k: float(v / tot) for k, v in m.items()}
    dom = max(fr, key=fr.get)
    return dom, fr


def mode_table(freqs, KEf=None):
    rows = []
    for j, f in enumerate(freqs):
        if f > FMAX:
            break
        row = dict(mode=j + 1, freq_hz=round(float(f), 3))
        if KEf is not None:
            dom, fr = ke_region_label(j)
            row["dominant_region"] = dom
            row["ke_fractions"] = {k: round(v, 4) for k, v in fr.items()}
        rows.append(row)
    return rows


tableA = mode_table(freqs, KEf=True)
with open(os.path.join(WS, "out", f"modes_nominal{SUFFIX}.json"), "w") as fh:
    json.dump(dict(config="nominal (deck + shield 1.7mm steel, feet SPC)",
                   n_modes_below_500=n_500, modes=tableA), fh, indent=1)

# save shapes for GIFs (first 40 modes or all <=500, whichever larger)
nkeep = min(Phi.shape[1], max(40, n_500))
np.savez_compressed(os.path.join(WS, "out", f"modes_nominal_shapes{SUFFIX}.npz"),
                    freqs=freqs[:nkeep], Phi=Phi[:, :nkeep],
                    master_dofs=arr["master_dofs"], spc_master_idx=spc_idx)

# strain-energy decomposition (identifiability gate artifact)
se_out = dict(
    note="f_ig = phi_i^T K_g phi_i / lambda_i (mass-normalized modes); "
         "sums to ~1 over groups per mode",
    groups=list(SE.keys()),
    per_mode=[{"mode": j + 1, "freq_hz": round(float(freqs[j]), 3),
               **{n: round(float(SE[n][j]), 4) for n in SE}}
              for j in range(n_500)])
with open(os.path.join(WS, "out", f"strain_energy_nominal{SUFFIX}.json"), "w") as fh:
    json.dump(se_out, fh, indent=1)

if os.environ.get("NOMINAL_ONLY"):
    print("NOMINAL_ONLY set: skipping variants and gates")
    sys.exit(0)


# ------------------------------------------------------------------ variants
def run_variant(name, scal_updates, fix=True, label_shield=False):
    scal = dict(nominal)
    scal.update(scal_updates)
    Kv, Mv = build(scal)
    fr, Phv, _ = solve_modes(Kv, Mv, spc_idx if fix else np.array([], int),
                             want_shapes=label_shield)
    out = dict(config=name, scalars={k: v for k, v in scal.items()
                                     if v != 1.0},
               n_modes_below_500=int(np.sum(fr <= FMAX)),
               freqs_hz=[round(float(f), 3) for f in fr[fr <= FMAX]])
    if label_shield:
        s_sh = scal.get("M_m_shield", 1.0)
        ke_sh = s_sh * np.einsum("ij,ij->j", Phv, MG["m_shield"] @ Phv)
        ke_tot = np.zeros_like(ke_sh)
        for n, A in MG.items():
            ke_tot += scal.get(f"M_{n}", 1.0) * np.einsum(
                "ij,ij->j", Phv, A @ Phv)
        frac = ke_sh / ke_tot
        j_sh = next((j for j in range(fr.size) if frac[j] > 0.5), None)
        out["first_shield_dominated_mode"] = (
            None if j_sh is None else dict(mode=j_sh + 1,
                                           freq_hz=round(float(fr[j_sh]), 3),
                                           shield_ke_fraction=round(float(frac[j_sh]), 3)))
    with open(os.path.join(WS, "out", f"modes_{name}{SUFFIX}.json"), "w") as fh:
        json.dump(out, fh, indent=1)
    print(f"[{name}] n<=500Hz: {out['n_modes_below_500']}, "
          f"f1={fr[0]:.3f} Hz, elapsed {time.time()-T0:.0f}s")
    return fr, out


# Deck-as-given: no shield AND no electronics box (the box bolts to the
# shield, D33 -- it cannot exist without its mounting surface; leaving it
# would create a floating spurious mechanism at 0 Hz).
fr_noshield, _ = run_variant("no_shield", {
    "K_shield_mem": 0.0, "K_shield_bend": 0.0, "K_shield_att": 0.0,
    "M_m_shield": 0.0, "K_att_ebox": 0.0, "K_att_ebox_rot": 0.0,
    "M_m_ebox": 0.0})

fr_ff, _ = run_variant("free_free", {}, fix=False)
n_rbm = int(np.sum(np.abs(fr_ff) < 0.5))
first_elastic_ff = float(fr_ff[n_rbm]) if fr_ff.size > n_rbm else None

fr_feet, _ = run_variant("feet_springs", {"K_feet_springs": 1.0}, fix=False)

# sensitivity arms (cheap scalar reassembly; the point of the architecture)
r = 0.5
fr_thalf, out_thalf = run_variant("shield_t_x0.5", {
    "K_shield_mem": r, "K_shield_bend": r ** 3, "M_m_shield": r},
    label_shield=True)
r = 2.0
fr_t2, out_t2 = run_variant("shield_t_x2", {
    "K_shield_mem": r, "K_shield_bend": r ** 3, "M_m_shield": r},
    label_shield=True)
fr_klo, _ = run_variant("screw_k_x0.01", {"K_shield_att": 0.01})
fr_khi, _ = run_variant("screw_k_x100", {"K_shield_att": 100.0})
# aluminum shield: E 10e6/29e6, rho 2.54e-4/7.324e-4
rE, rRho = 1.0e7 / 2.9e7, 2.54e-4 / 7.324e-4
fr_al, _ = run_variant("shield_aluminum", {
    "K_shield_mem": rE, "K_shield_bend": rE, "M_m_shield": rRho})

# ------------------------------------------------------------------ gates
# mass closure: model M total vs hand sum
mass_model = sum(A.diagonal()[0::6].sum() * nominal.get(f"M_{n}", 1.0)
                 for n, A in MG.items())
# hand sum (independent path): from parse + estimates
import importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
est = importlib.import_module("estimates")
d = json.load(open(os.path.join(WS, "out", "parsed_deck.json")))
xyzd = {int(k): np.array([v["x"], v["y"], v["z"]])
        for k, v in d["grids"].items()}
pbm = {int(k): v for k, v in d["pbeams"].items()}
rho = est.STEEL["rho"]
m_beams = sum(rho * pbm[c["pid"]]["A"]
              * np.linalg.norm(xyzd[c["gb"]] - xyzd[c["ga"]])
              for c in d["cbeams"])


def quad_area(pts):
    n = np.cross(pts[2] - pts[0], pts[3] - pts[1])
    return 0.5 * np.linalg.norm(n)


m_plate = sum(rho * meta["thrust_plate_t"]
              * quad_area(np.array([xyzd[g] for g in q["g"]]))
              for q in d["cquads"])
ext_u = est.ESTIMATES["shield_upper_extent"]["value"]
ext_l = est.ESTIMATES["shield_lower_extent"]["value"]
area_shield = (abs(ext_u["y1"] - ext_u["y0"]) * abs(ext_u["z1"] - ext_u["z0"])
               + abs(ext_l["y1"] - ext_l["y0"]) * abs(ext_l["z1"] - ext_l["z0"]))
m_shield = rho * meta["shield_t"] * area_shield
# valve assembly = INDEPENDENT recompute (not the model's own number): 80/20
# aluminum beam self-mass (sum rho_al*A*L) + lumped tank/valve masses.
from valve_frame import build_valve_frame
vf = build_valve_frame(est.ESTIMATES["valve_frame"]["value"])
A_ts = est.TSLOT_1515["A"]
rho_al = est.ALU["rho"]
m_vframe = sum(rho_al * A_ts * np.linalg.norm(vf["nodes"][b] - vf["nodes"][a])
               for a, b in vf["beams"])
m_vlump = sum(vf["lumped"].values()) * est.LBM
m_boxes = (est.ESTIMATES["electronics_box"]["value"]["mass_lbm"]
           + est.ESTIMATES["white_box_upper"]["value"]["mass_lbm"]) * est.LBM
mass_hand = m_beams + m_plate + m_shield + m_vframe + m_vlump + m_boxes

# negative eigenvalue check (fixed nominal)
neg = int(np.sum(freqs < -1e-6))

# limiting behavior: shield bending panel modes ~ t. Track the FIRST
# SHIELD-DOMINATED mode in each configuration (KE fraction > 0.5); with fixed
# screw-spring boundaries the ratio deviates from the ideal f~t law toward
# the boundary-spring-dominated side as the panel stiffens (physical, stated).
shield_modes = [j for j in range(n_500)
                if ke_region_label(j)[0] == "shield"]
j0 = shield_modes[0] if shield_modes else None
lim = None
if j0 is not None and out_thalf.get("first_shield_dominated_mode") \
        and out_t2.get("first_shield_dominated_mode"):
    f_nom = float(freqs[j0])
    f_lo = out_thalf["first_shield_dominated_mode"]["freq_hz"]
    f_hi = out_t2["first_shield_dominated_mode"]["freq_hz"]
    lim = dict(first_shield_mode_nominal=j0 + 1, f_nominal=f_nom,
               f_t_x0_5=f_lo, ratio_x0_5=round(f_lo / f_nom, 4),
               f_t_x2=f_hi, ratio_x2=round(f_hi / f_nom, 4),
               note="ideal thin-plate law: ratios 0.5 and 2.0; screw-spring "
                    "boundaries soften the x2 ratio (boundary becomes "
                    "relatively more compliant as the panel stiffens)")

gates = dict(
    mass_closure_rel_err=float(abs(mass_model - mass_hand) / mass_hand),
    mass_model_lbm=float(mass_model * 386.089),
    mass_hand_lbm=float(mass_hand * 386.089),
    free_free_n_rbm=n_rbm,
    free_free_first_elastic_hz=first_elastic_ff,
    free_free_rbm_max_hz=float(np.max(np.abs(fr_ff[:n_rbm]))) if n_rbm else None,
    n_negative_eigs_nominal=neg,
    n_modes_below_500_nominal=n_500,
    n_modes_below_500_no_shield=int(np.sum(fr_noshield <= FMAX)),
    at_least_30_modes=bool(n_500 >= 30),
    shield_t_limiting=lim,
    se_fraction_sum_check=float(np.mean(sum(SE[n][:n_500] for n in SE))),
    elapsed_s=round(time.time() - T0, 1),
)
with open(os.path.join(WS, "out", f"modal_gates{SUFFIX}.json"), "w") as fh:
    json.dump(gates, fh, indent=1, default=float)
print(json.dumps(gates, indent=1, default=float))
