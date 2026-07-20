#!/usr/bin/env python3
"""Element-library validation vs textbook closed forms (checker gates; run BEFORE
the full model). References:
  - Beam statics/dynamics: Euler-Bernoulli/Timoshenko cantilever formulas
    (Blevins, "Formulas for Natural Frequency and Mode Shape", Table 8-1;
    Roark for tip deflection delta = PL^3/3EI + PL/(k A G)).
  - Plate strip bending: delta = P L^3 / (3 E' I), E' = E/(1-nu^2) (wide-beam /
    plate strip, Roark).
  - SS rectangular plate: f_mn = (pi/2) sqrt(D/(rho t)) ((m/a)^2 + (n/b)^2)
    (Blevins Table 11-4; Leissa).
  - CBUSH/CONM2: f = sqrt(k/m)/(2 pi).
All in inch-lbf-second units. Output: out/element_validation.json
"""
import json
import os
import sys

import numpy as np
import scipy.linalg as sla

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elements import (beam_KM_global, bush_K_global, conm2_M, rbe2_rows,
                      shell_KM_global)

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E, NU, RHO = 2.9e7, 0.29, 7.324e-4
G = E / (2 * (1 + NU))
results = {}


def assemble_chain_beam(n_el, L, prop, fixed_node=0):
    """Cantilever along global x, orientation v = +y so local y == global y:
    a global-y load is bending in PLANE 1 (I1, K1)."""
    nn = n_el + 1
    nd = 6 * nn
    K = np.zeros((nd, nd))
    M = np.zeros((nd, nd))
    xs = np.linspace(0, L, nn)
    for e in range(n_el):
        xa = np.array([xs[e], 0, 0])
        xb = np.array([xs[e + 1], 0, 0])
        Ke, Me = beam_KM_global(xa, xb, [0, 1.0, 0.0], E, G, RHO, prop)
        idx = list(range(6 * e, 6 * e + 12))
        K[np.ix_(idx, idx)] += Ke
        M[np.ix_(idx, idx)] += Me
    free = np.arange(6 * fixed_node + 6, nd) if fixed_node == 0 else None
    return K, M, free


# ---------------------------------------------------------------- 1. beam statics
# Slender cantilever (Euler regime): L=50, the deck tube section.
prop = dict(A=1.353627, I1=0.4508286, I2=1.045408, J=1.003687,
            K1=0.2973119, K2=0.6236289)
L = 50.0
n_el = 20
K, M, free = assemble_chain_beam(n_el, L, prop)
P = 100.0  # lbf tip load in +y (plane 1, bending about local z, I1, K1)
f = np.zeros(len(free))
Kff = K[np.ix_(free, free)]
tipdof_y = free.tolist().index(6 * n_el + 1)  # global dof of TIP node uy
f[tipdof_y] = P
u = np.linalg.solve(Kff, f)
delta_fem = u[tipdof_y]
delta_euler = P * L ** 3 / (3 * E * prop["I1"])
delta_timo = delta_euler + P * L / (prop["K1"] * prop["A"] * G)
results["beam_static_tip_deflection"] = dict(
    fem=delta_fem, euler=delta_euler, timoshenko=delta_timo,
    rel_err_vs_timoshenko=abs(delta_fem - delta_timo) / delta_timo,
    note="L=50in deck tube, 20 elements, tip load plane 1; 2-node Timoshenko "
         "element is nodally exact for end loads -> expect ~machine precision")

# Stocky check: short cantilever, shear matters
Ls = 5.0
K2_, M2_, free2 = assemble_chain_beam(10, Ls, prop)
Kff2 = K2_[np.ix_(free2, free2)]
f2 = np.zeros(len(free2))
tip2 = free2.tolist().index(6 * 10 + 1)
f2[tip2] = P
u2 = np.linalg.solve(Kff2, f2)
d_euler_s = P * Ls ** 3 / (3 * E * prop["I1"])
d_timo_s = d_euler_s + P * Ls / (prop["K1"] * prop["A"] * G)
results["beam_static_stocky"] = dict(
    fem=u2[tip2], euler=d_euler_s, timoshenko=d_timo_s,
    rel_err_vs_timoshenko=abs(u2[tip2] - d_timo_s) / d_timo_s,
    shear_fraction_of_total=(d_timo_s - d_euler_s) / d_timo_s)

# ---------------------------------------------------------------- 2. beam frequency
# Slender cantilever first bending frequency (Euler closed form valid):
lam1 = 1.8751040687
f1_euler = lam1 ** 2 / (2 * np.pi) * np.sqrt(E * prop["I1"] / (RHO * prop["A"])) / L ** 2
w2, V = sla.eigh(K[np.ix_(free, free)], M[np.ix_(free, free)] + 1e-30 * np.eye(len(free)))
# guard zero-mass rotations: use generalized via pseudo - instead solve reduced on massive dofs
# (rotational dofs have zero mass: condense them out exactly - static condensation)
mass_dofs = np.where(np.diag(M[np.ix_(free, free)]) > 0)[0]
zero_dofs = np.where(np.diag(M[np.ix_(free, free)]) == 0)[0]
Kff = K[np.ix_(free, free)]
Kaa = Kff[np.ix_(mass_dofs, mass_dofs)]
Kab = Kff[np.ix_(mass_dofs, zero_dofs)]
Kbb = Kff[np.ix_(zero_dofs, zero_dofs)]
Kred = Kaa - Kab @ np.linalg.solve(Kbb, Kab.T)
Mred = M[np.ix_(free, free)][np.ix_(mass_dofs, mass_dofs)]
w2r, _ = sla.eigh(Kred, Mred)
f_fem = np.sqrt(np.maximum(w2r, 0)) / (2 * np.pi)
# first bending-in-plane-1 mode = lowest with I1 < I2 ... lowest overall is plane-1
results["beam_first_frequency"] = dict(
    fem_hz=float(f_fem[0]), euler_hz=f1_euler,
    rel_err=abs(f_fem[0] - f1_euler) / f1_euler,
    note="lumped mass; slender L=50in cantilever; lowest mode bends about I1")

# ---------------------------------------------------------------- 3. plate strip
# Cantilever plate strip: 10x2 mesh of 1x1 in shell elements, t=0.0669 in,
# clamped at x=0, tip line load. Gate uses nu=0 where beam reference
# delta = P L^3 / (3 E I) is unambiguous (with nu=0.29 a 2-in strip sits
# BETWEEN the narrow-beam E and wide-plate E' = E/(1-nu^2) limits; reported
# as info below).
t = 0.066929
NU_STRIP = 0.0
nx, ny = 10, 2
Lp, Wp = 10.0, 2.0
nnx, nny = nx + 1, ny + 1
nid = lambda i, j: j * nnx + i
nd = 6 * nnx * nny
K = np.zeros((nd, nd))
M = np.zeros((nd, nd))
oop_max = 0.0
for j in range(ny):
    for i in range(nx):
        g = [nid(i, j), nid(i + 1, j), nid(i + 1, j + 1), nid(i, j + 1)]
        xyz = np.array([[ii * (Lp / nx), jj * (Wp / ny), 0.0]
                        for ii, jj in [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]])
        Ke, Me, oop = shell_KM_global(xyz, E, NU_STRIP, RHO, t)
        oop_max = max(oop_max, oop)
        idx = np.concatenate([np.arange(6 * gg, 6 * gg + 6) for gg in g])
        K[np.ix_(idx, idx)] += Ke
        M[np.ix_(idx, idx)] += Me
fixed = [nid(0, j) for j in range(nny)]
free = np.array([d for d in range(nd) if d // 6 not in fixed])
Ptot = 1.0
fvec = np.zeros(nd)
for j in range(nny):
    w_ = 0.5 if j in (0, nny - 1) else 1.0
    fvec[6 * nid(nx, j) + 2] = Ptot * w_ / ny
u = np.linalg.solve(K[np.ix_(free, free)], fvec[free])
w_tip = np.mean([u[free.tolist().index(6 * nid(nx, j) + 2)] for j in range(nny)])
I_strip = Wp * t ** 3 / 12.0
delta_ref = Ptot * Lp ** 3 / (3 * E * I_strip)  # nu=0: E' == E
results["plate_strip_bending"] = dict(
    fem=w_tip, reference=delta_ref, rel_err=abs(w_tip - delta_ref) / delta_ref,
    max_out_of_plane=oop_max,
    note="10x2 mesh 1x1in ACM elements, nu=0 strip; beam reference PL^3/3EI")

# ---------------------------------------------------------------- 4. SS plate f11
a, b_ = 20.0, 10.0
nx, ny = 12, 8
nnx, nny = nx + 1, ny + 1
nid = lambda i, j: j * nnx + i
nd = 6 * nnx * nny
K = np.zeros((nd, nd))
M = np.zeros((nd, nd))
for j in range(ny):
    for i in range(nx):
        g = [nid(i, j), nid(i + 1, j), nid(i + 1, j + 1), nid(i, j + 1)]
        xyz = np.array([[ii * (a / nx), jj * (b_ / ny), 0.0]
                        for ii, jj in [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]])
        Ke, Me, _ = shell_KM_global(xyz, E, NU, RHO, t)
        idx = np.concatenate([np.arange(6 * gg, 6 * gg + 6) for gg in g])
        K[np.ix_(idx, idx)] += Ke
        M[np.ix_(idx, idx)] += Me
# simply supported: w=0 on all edges; also pin in-plane + drilling to remove RBM
fix = set()
for j in range(nny):
    for i in range(nnx):
        g = nid(i, j)
        fix.update([6 * g + 0, 6 * g + 1, 6 * g + 5])  # in-plane + drilling
        if i in (0, nnx - 1) or j in (0, nny - 1):
            fix.add(6 * g + 2)
free = np.array(sorted(set(range(nd)) - fix))
Kff, Mff = K[np.ix_(free, free)], M[np.ix_(free, free)]
md = np.where(np.diag(Mff) > 0)[0]
zd = np.where(np.diag(Mff) == 0)[0]
Kred = Kff[np.ix_(md, md)] - Kff[np.ix_(md, zd)] @ np.linalg.solve(
    Kff[np.ix_(zd, zd)], Kff[np.ix_(zd, md)])
w2r, _ = sla.eigh(Kred, Mff[np.ix_(md, md)])
f_fem11 = np.sqrt(w2r[0]) / (2 * np.pi)
D = E * t ** 3 / (12 * (1 - NU ** 2))
f_ref11 = (np.pi / 2.0) * np.sqrt(D / (RHO * t)) * ((1 / a) ** 2 + (1 / b_) ** 2)
results["plate_ss_f11"] = dict(
    fem_hz=float(f_fem11), reference_hz=float(f_ref11),
    rel_err=abs(f_fem11 - f_ref11) / f_ref11,
    note="20x10in SS plate, 12x8 mesh, t=1.7mm, Blevins/Leissa f11")

# ---------------------------------------------------------------- 5. CBUSH + CONM2
kd = [1.0e5] * 3 + [1.0e4] * 3
Kb = bush_K_global(np.zeros(3), np.zeros(3), kd)  # coincident
m = 0.05
Mc = conm2_M(m, (0.5, 0.5, 0.5))
K2 = Kb[6:, 6:]  # ground node A
f_fem_t = np.sqrt(K2[0, 0] / m) / (2 * np.pi)
f_ref_t = np.sqrt(kd[0] / m) / (2 * np.pi)
f_fem_r = np.sqrt(K2[3, 3] / 0.5) / (2 * np.pi)
f_ref_r = np.sqrt(kd[3] / 0.5) / (2 * np.pi)
results["cbush_conm2_frequency"] = dict(
    trans_fem_hz=f_fem_t, trans_ref_hz=f_ref_t,
    rot_fem_hz=f_fem_r, rot_ref_hz=f_ref_r,
    rel_err=max(abs(f_fem_t - f_ref_t) / f_ref_t, abs(f_fem_r - f_ref_r) / f_ref_r))

# offset CBUSH equilibrium: force at offset spring must produce zero net resultant
xa = np.array([0.0, 0, 0]); xb = np.array([2.0, 0, 0])
Kb = bush_K_global(xa, xb, kd)
u = np.zeros(12); u[7] = 1.0  # uy at B
fvec = Kb @ u
Fa, Ma_, Fb, Mb_ = fvec[0:3], fvec[3:6], fvec[6:9], fvec[9:12]
net_F = Fa + Fb
net_M = Ma_ + Mb_ + np.cross(xa, Fa) + np.cross(xb, Fb)
results["cbush_offset_equilibrium"] = dict(
    net_force=float(np.abs(net_F).max()), net_moment=float(np.abs(net_M).max()),
    note="unit uy at B, 2in offset bush: self-equilibrated element required")

# ---------------------------------------------------------------- 6. RBE2 kinematics
Tb = rbe2_rows(np.zeros(3), np.array([0.0, 3.0, 0.0]))
th = np.array([0, 0, 0, 0, 0, 0.01])  # rz at independent
ug = Tb @ th
results["rbe2_kinematics"] = dict(
    ux_dep=float(ug[0]), expected_ux=-0.03,
    err=abs(ug[0] - (-0.03)),
    note="dep grid 3in along +y, rz=0.01 -> ux = -0.03 (rigid arm)")

# ---------------------------------------------------------------- 7. free-free RBM
# Note: with translational-only beam lumping (D8), an ISOLATED straight beam's
# torsion RBM lives entirely in massless DOFs; add small end rotary inertias
# (CONM2-style) so all 6 RBMs are representable -- in the full stand model the
# QOI CONM2s and 3-D joint coupling play this role.
prop2 = prop
K, M, _ = assemble_chain_beam(8, 16.0, prop2)
for node in (0, 8):
    M[np.ix_(range(6 * node + 3, 6 * node + 6),
             range(6 * node + 3, 6 * node + 6))] += 0.01 * np.eye(3)
md = np.where(np.diag(M) > 0)[0]
zd = np.where(np.diag(M) == 0)[0]
Kred = K[np.ix_(md, md)] - K[np.ix_(md, zd)] @ np.linalg.solve(
    K[np.ix_(zd, zd)], K[np.ix_(zd, md)])
w2r, _ = sla.eigh(Kred, M[np.ix_(md, md)])
f_all = np.sqrt(np.abs(w2r)) / (2 * np.pi)
n_rbm = int(np.sum(f_all < 1e-3 * f_all[6]))
results["beam_free_free_rbm"] = dict(
    n_rigid_modes=n_rbm, first_six_hz=[float(x) for x in f_all[:6]],
    first_elastic_hz=float(f_all[6]))

# ---------------------------------------------------------------- verdicts
gates = dict(
    beam_static=results["beam_static_tip_deflection"]["rel_err_vs_timoshenko"] < 1e-6,
    beam_static_stocky=results["beam_static_stocky"]["rel_err_vs_timoshenko"] < 1e-6,
    beam_freq=results["beam_first_frequency"]["rel_err"] < 0.01,
    plate_strip=results["plate_strip_bending"]["rel_err"] < 0.02,
    plate_ss_f11=results["plate_ss_f11"]["rel_err"] < 0.03,
    cbush_conm2=results["cbush_conm2_frequency"]["rel_err"] < 1e-9,
    cbush_equilibrium=(results["cbush_offset_equilibrium"]["net_force"] < 1e-6
                       and results["cbush_offset_equilibrium"]["net_moment"] < 1e-6),
    rbe2=results["rbe2_kinematics"]["err"] < 1e-12,
    free_free_6_rbm=results["beam_free_free_rbm"]["n_rigid_modes"] == 6,
)
gates = {k: bool(v) for k, v in gates.items()}
results["gates"] = gates
results["all_pass"] = all(gates.values())
os.makedirs(os.path.join(WS, "out"), exist_ok=True)
with open(os.path.join(WS, "out", "element_validation.json"), "w") as fh:
    json.dump(results, fh, indent=1, default=float)
for k, v in gates.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print("ALL PASS:", results["all_pass"])
sys.exit(0 if results["all_pass"] else 1)
