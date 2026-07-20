#!/usr/bin/env python3
"""Validate the added beam/bar element against analytic solutions (D10).
Same standard as the reused ShockSat shell library (<=~0.5-1% vs closed form).

Checks:
  V1 free-free beam -> exactly 6 rigid-body zero modes.
  V2 cantilever 1st bending vs Euler-Bernoulli (beta1=1.875104).
  V3 cantilever axial (fixed-free rod) f1 = c/(4L), c=sqrt(E/rho).
  V4 cantilever torsion f1 = (1/4L) sqrt(G*J/(rho*Ip)) (circular: J=Ip).
  V5 simply-supported 1st bending f1 = (pi/L)^2 sqrt(EI/rhoA)/(2pi).
  V6 free-free translation/rotation: K @ rigid_body_vector ~ 0 (residual).
  V7 bar3d two-force member: fixed-free axial f1 = c/(4L) (struts).
"""
import json
import time
import numpy as np
from beam_element import beam3d, bar3d

T0 = time.time()
OUT = {}

# round Al strut/ring-like section
E, nu, rho = 71e9, 0.33, 2800.0
G = E / (2 * (1 + nu))
do, di = 0.025, 0.022                     # m, tube
A = np.pi / 4 * (do**2 - di**2)
Iy = Iz = np.pi / 64 * (do**4 - di**4)
J = Ip = np.pi / 32 * (do**4 - di**4)
L = 1.0
NE = 16
nodes = np.zeros((NE + 1, 3)); nodes[:, 0] = np.linspace(0, L, NE + 1)
ndof = 6 * (NE + 1)


def assemble_beam(vref=(0, 0, 1)):
    K = np.zeros((ndof, ndof)); M = np.zeros((ndof, ndof))
    for e in range(NE):
        Ke, Me = beam3d(nodes[e], nodes[e + 1], E, nu, A, Iy, Iz, J, rho, vref)
        d = list(range(6 * e, 6 * e + 6)) + list(range(6 * (e + 1), 6 * (e + 1) + 6))
        for i, ii in enumerate(d):
            for j, jj in enumerate(d):
                K[ii, jj] += Ke[i, j]; M[ii, jj] += Me[i, j]
    return K, M


def modes(K, M, fixed, nmodes=8):
    from scipy.linalg import eigh
    free = np.setdiff1d(np.arange(ndof), fixed)
    w, v = eigh(K[np.ix_(free, free)], M[np.ix_(free, free)])
    w = np.clip(w, 0, None)
    return np.sqrt(w) / (2 * np.pi), free, v


K, M = assemble_beam()

# V1 free-free: 6 rigid-body modes. Count by frequency cutoff (unambiguous:
# rigid f ~ 0, lowest elastic = 149 Hz) rather than an eigenvalue-scale threshold.
from scipy.linalg import eigh
w_ff = eigh(K, M, eigvals_only=True)
f_ff = np.sqrt(np.clip(w_ff, 0, None)) / (2 * np.pi)
nzero = int(np.sum(f_ff < 1.0))
OUT["V1_freefree_zero_modes"] = {"n_zero": nzero, "expected": 6,
                                 "f1_rigid_max_hz": float(f_ff[5]),
                                 "f7_elastic_hz": float(f_ff[6]),
                                 "ok": nzero == 6}

# V2 cantilever bending (fix node 0 all 6 dof)
fixed0 = list(range(6))
f, _, _ = modes(K, M, fixed0)
beta1 = 1.8751040687
f_bend = beta1**2 / (2 * np.pi) * np.sqrt(E * Iz / (rho * A * L**4))
fb = f[f > 1e-6][0]
OUT["V2_cantilever_bending"] = {"fem_hz": float(fb), "analytic_hz": float(f_bend),
                                "err_pct": float(100 * (fb - f_bend) / f_bend),
                                "ok": abs(fb - f_bend) / f_bend < 0.01}

# V3 cantilever axial: isolate axial by reading the axial-dominated mode.
c = np.sqrt(E / rho)
f_axial = c / (4 * L)
# axial modes appear among the spectrum; pick nearest to analytic
fall, free, v = modes(K, M, fixed0, nmodes=40)
fa = fall[np.argmin(np.abs(fall - f_axial))]
OUT["V3_cantilever_axial"] = {"fem_hz": float(fa), "analytic_hz": float(f_axial),
                              "err_pct": float(100 * (fa - f_axial) / f_axial),
                              "ok": abs(fa - f_axial) / f_axial < 0.01}

# V4 cantilever torsion: f1 = (1/4L) sqrt(GJ/(rho Ip))
f_tors = (1 / (4 * L)) * np.sqrt(G * J / (rho * Ip))
ft = fall[np.argmin(np.abs(fall - f_tors))]
OUT["V4_cantilever_torsion"] = {"fem_hz": float(ft), "analytic_hz": float(f_tors),
                                "err_pct": float(100 * (ft - f_tors) / f_tors),
                                "ok": abs(ft - f_tors) / f_tors < 0.01}

# V5 simply-supported bending in x-y: pin both ends translations v,w; allow
# axial at one end free. SS for bending = constrain v,w at both ends only.
fixed_ss = [1, 2, 0] + [6 * NE + 1, 6 * NE + 2]   # v,w both ends; u at node0
f_ss, _, _ = modes(K, M, fixed_ss)
f_ss1_an = (np.pi / L)**2 * np.sqrt(E * Iz / (rho * A)) / (2 * np.pi)
fss = f_ss[f_ss > 1e-6][0]
OUT["V5_simply_supported_bending"] = {
    "fem_hz": float(fss), "analytic_hz": float(f_ss1_an),
    "err_pct": float(100 * (fss - f_ss1_an) / f_ss1_an),
    "ok": abs(fss - f_ss1_an) / f_ss1_an < 0.01}

# V6 rigid-body residual: K @ (uniform translation) and (rotation) ~ 0
rt = np.zeros(ndof); rt[0::6] = 1.0           # uniform x-translation
res_t = np.linalg.norm(K @ rt) / (np.linalg.norm(K, 1) * np.linalg.norm(rt))
# rotation about z through origin: u=-y* th, v=x* th, rz=th
rr = np.zeros(ndof)
rr[0::6] = -nodes[:, 1]; rr[1::6] = nodes[:, 0]; rr[5::6] = 1.0
res_r = np.linalg.norm(K @ rr) / (np.linalg.norm(K, 1) * np.linalg.norm(rr) + 1e-30)
OUT["V6_rigid_body_residual"] = {"trans_resid": float(res_t),
                                 "rot_resid": float(res_r),
                                 "ok": res_t < 1e-12 and res_r < 1e-12}

# V7 bar element (struts): fixed-free axial
Kb = np.zeros((ndof, ndof)); Mb = np.zeros((ndof, ndof))
# map bar 6x6 (translations only) into the 6-dof/node layout
for e in range(NE):
    ke, me = bar3d(nodes[e], nodes[e + 1], E, A, rho)
    tdof = [6 * e, 6 * e + 1, 6 * e + 2, 6 * (e + 1), 6 * (e + 1) + 1, 6 * (e + 1) + 2]
    for i, ii in enumerate(tdof):
        for j, jj in enumerate(tdof):
            Kb[ii, jj] += ke[i, j]; Mb[ii, jj] += me[i, j]
# bar has zero stiffness on rotations + lateral at interior -> constrain all
# rotations everywhere and lateral everywhere, leave axial free (1-D rod test)
keepaxial = [6 * i for i in range(NE + 1)]
Kr = Kb[np.ix_(keepaxial, keepaxial)]; Mr = Mb[np.ix_(keepaxial, keepaxial)]
# fix node 0 axial
fr = list(range(1, NE + 1))
wbar = eigh(Kr[np.ix_(fr, fr)], Mr[np.ix_(fr, fr)], eigvals_only=True)
fbar = np.sqrt(np.clip(wbar, 0, None)) / (2 * np.pi)
fbar1 = fbar[fbar > 1e-6][0]
OUT["V7_bar_axial"] = {"fem_hz": float(fbar1), "analytic_hz": float(f_axial),
                       "err_pct": float(100 * (fbar1 - f_axial) / f_axial),
                       "ok": abs(fbar1 - f_axial) / f_axial < 0.01}

OUT["ALL_OK"] = all(bool(v.get("ok", False)) for k, v in OUT.items() if isinstance(v, dict))
OUT["runtime_s"] = time.time() - T0


def _san(o):
    if isinstance(o, dict):
        return {k: _san(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_san(x) for x in o]
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    return o


OUT = _san(OUT)
with open("out/beam_validation.json", "w") as fh:
    json.dump(OUT, fh, indent=1)
print(json.dumps(OUT, indent=1))
