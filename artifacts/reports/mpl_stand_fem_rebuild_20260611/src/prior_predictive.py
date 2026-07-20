#!/usr/bin/env python3
"""Prior-predictive forward propagation of the electronics-box mass prior
(FABLE, 2026-06-11, D34). NO SAMPLER, NO POSTERIOR: pushes Andrew's '2-4 lb'
prior FORWARD through the parametric model to the observable it moves, so we
can see what the tap test will (and will not) resolve, and hand a calibrated
prior + an honest identifiability note to the next (posterior-update) card.

Observable choice (honest): the box at 2-4 lb does NOT form one clean mode --
it is a 6-DOF rigid body on soft, CG-offset bolts coupled to the flexible
1.7 mm shield, so its response energy is SMEARED across a veering cluster of
coupled box/shield modes (~17-45 Hz; the peak box mode jumps branches with
mass). We therefore propagate the prior through the structure's FUNDAMENTAL
frequency f1, which by eigenvalue interlacing is MONOTONE in any added mass
(clean, theorem-backed). Caveat carried everywhere: at 2-4 lb f1 is the VALVE
assembly mode (box participation ~0.15), so f1 is only WEAKLY box-sensitive
and partly confounded with valve mass -- the box mass is better resolved by
the 17-45 Hz cluster, which the next card should use.

Outputs: out/prior_predictive.json
"""
import json
import os
import sys
from statistics import NormalDist

import numpy as np
import scipy.linalg as sla
import scipy.sparse as sp
import scipy.sparse.linalg as spla

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(WS, "out", "model")
meta = json.load(open(os.path.join(MODEL, "meta.json")))
arr = np.load(os.path.join(MODEL, "arrays.npz"))
spc = arr["spc_master_idx"]
NM = meta["ndof_master"]
nominal = dict(meta["nominal_scalars"])
EBOX_NOMINAL_LBM = 3.0

KG = {n: sp.load_npz(os.path.join(MODEL, "groups", f"K_{n}.npz"))
      for n in meta["K_groups"]}
MG = {n: sp.load_npz(os.path.join(MODEL, "groups", f"M_{n}.npz"))
      for n in meta["M_groups"]}


def build(sc):
    K = M = None
    for n, A in KG.items():
        s = sc.get("K_" + n, 1.0)
        if s:
            K = s * A if K is None else K + s * A
    for n, A in MG.items():
        s = sc.get("M_" + n, 1.0)
        if s:
            M = s * A if M is None else M + s * A
    return K.tocsr(), M.tocsr()


def fundamental(K, M):
    """f1 (Hz) and the box KE fraction in mode 1."""
    free = np.setdiff1d(np.arange(NM), spc)
    dead = free[K.diagonal()[free] == 0]
    free = np.setdiff1d(free, dead)
    Kf = K[np.ix_(free, free)].tocsc()
    Mf = M[np.ix_(free, free)].tocsr()
    md = np.where(Mf.diagonal() > 0)[0]
    zd = np.where(Mf.diagonal() == 0)[0]
    lu = spla.splu(Kf[np.ix_(zd, zd)].tocsc())
    S = lu.solve(Kf[np.ix_(zd, md)].toarray())
    Kr = Kf[np.ix_(md, md)].toarray() - Kf[np.ix_(md, zd)].toarray() @ S
    Mr = Mf[np.ix_(md, md)].toarray()
    Kr = 0.5 * (Kr + Kr.T)
    w2, V = sla.eigh(Kr, Mr, subset_by_index=[0, 0])
    f1 = float(np.sqrt(max(w2[0], 0)) / (2 * np.pi))
    phi = np.zeros(NM)
    pf = np.zeros(free.size)
    pf[md] = V[:, 0]
    pf[zd] = -S @ V[:, 0]
    phi[free] = pf
    ke_box = float(phi @ (MG["m_ebox"] @ phi))   # mass-normalized => fraction
    return f1, ke_box


# Dense mass grid so the forward map is captured faithfully THROUGH the box
# mode<->fundamental veering/crossing near 2-2.5 lb (where a single parametric
# law fails). Forward map = direct monotone interpolation, NOT a fitted law.
masses = np.arange(2.0, 4.0001, 0.25)
f1s, kes = [], []
for m in masses:
    sc = dict(nominal)
    sc["M_m_ebox"] = m / EBOX_NOMINAL_LBM
    K, M = build(sc)
    f1, ke = fundamental(K, M)
    f1s.append(f1)
    kes.append(ke)
f1s = np.array(f1s)

# f1 must be non-increasing in box mass (eigenvalue interlacing); enforce a
# tiny monotone clamp against numerical noise, then linearly interpolate.
f1_mono = np.minimum.accumulate(f1s)
mono_violation = float(np.max(f1s - f1_mono))   # ~0 expected
fit = lambda m: np.interp(m, masses, f1_mono)   # monotone, exact at nodes
grid_reproduction_err = float(np.max(np.abs(fit(masses) - f1_mono)))

# prior: LogNormal with 95% = [2,4] lbm
z = NormalDist().inv_cdf(0.975)
median = float(np.sqrt(2.0 * 4.0))
sigma_ln = float(np.log(4.0 / 2.0) / (2 * z))
rng = np.random.default_rng(20260611)
m_draws = np.exp(rng.normal(np.log(median), sigma_ln, 200000))
m_draws = np.clip(m_draws, masses[0], masses[-1])   # interp domain
f_draws = fit(m_draws)
q = lambda x, p: float(np.quantile(x, p))
box_ke_span = [round(float(min(kes)), 3), round(float(max(kes)), 3)]

out = dict(
    note="PRIOR-PREDICTIVE (forward push of Andrew's 2-4 lb box-mass prior "
         "through M(theta) -> fundamental frequency f1). NOT a posterior; no "
         "sampler. The next card UPDATES this with the tap test.",
    prior=dict(dist="lognormal", median_lbm=median, sigma_ln=sigma_ln,
               mass_95_lbm=[2.0, 4.0],
               source="Andrew 2026-06-11: 'between 2 and 4 pounds'"),
    f1_grid=dict(mass_lbm=masses.tolist(),
                 f1_hz=[round(x, 3) for x in f1s],
                 box_ke_fraction_in_mode1=[round(x, 3) for x in kes]),
    forward_map=dict(method="direct monotone linear interpolation of f1(m) "
                     "(NOT a parametric law: the box mode crosses the "
                     "fundamental near 2-2.5 lb, box KE-in-mode-1 jumps "
                     f"{box_ke_span[0]}->{box_ke_span[1]}, so a single 1/f^2 "
                     "law does not fit; interpolation is exact at the grid)",
                     monotone_violation_hz=round(mono_violation, 5),
                     grid_reproduction_err_hz=round(grid_reproduction_err, 6)),
    prior_predictive_f1_hz=dict(
        median=round(q(f_draws, 0.5), 2),
        p2_5=round(q(f_draws, 0.025), 2), p97_5=round(q(f_draws, 0.975), 2),
        at_mass_2lb=round(float(fit(2.0)), 2),
        at_mass_3lb=round(float(fit(3.0)), 2),
        at_mass_4lb=round(float(fit(4.0)), 2)),
    identifiability_caveat=(
        "The box does NOT cleanly own a single mode across 2-4 lb: its mode "
        "CROSSES the fundamental near 2-2.5 lb (box KE-in-mode-1 jumps "
        f"{box_ke_span[0]}->{box_ke_span[1]}) and its energy otherwise smears "
        "across a veering 17-45 Hz shield cluster (no single clean peak). f1 "
        "stays monotone in box mass (interlacing) but shifts only ~0.8 Hz "
        "across the whole prior and is partly confounded with valve mass. "
        "=> the tap test resolves box mass only WEAKLY from f1; the next card "
        "should use the 17-45 Hz cluster (and ideally a sensor ON the box) to "
        "update it, and expect box-mass vs valve-mass confounding."),
    plain_english=(
        f"Andrew's 2-4 lb prior maps the FUNDAMENTAL to "
        f"{q(f_draws,0.5):.1f} Hz, 95% band [{q(f_draws,0.025):.1f}, "
        f"{q(f_draws,0.975):.1f}] Hz -- but that mode is valve-dominated, so "
        "the box mass barely moves it. Honest read: a single-peak tap test "
        "under-resolves this box mass; see identifiability_caveat."),
    samples_for_fig=dict(mass=m_draws[:5000].tolist(),
                         f1=f_draws[:5000].tolist()),
)
with open(os.path.join(WS, "out", "prior_predictive.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print(json.dumps({k: out[k] for k in
                  ("prior", "f1_grid", "forward_map",
                   "prior_predictive_f1_hz")},
                 indent=1))
print(out["identifiability_caveat"])
