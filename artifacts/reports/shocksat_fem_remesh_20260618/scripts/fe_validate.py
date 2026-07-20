#!/usr/bin/env python3
"""Element-level verification for fe_core (run before any full assembly).

Checks (all must pass; results written to fe_validate_report.json):
V1 QM6 membrane: exactly 3 zero-energy modes (2 translations + 1 in-plane rot)
   on a distorted element.
V2 QM6 slender cantilever (in-plane bending): tip deflection vs
   Timoshenko beam within 2%.
V3 MITC4: exactly 3 zero-energy modes (1 translation + 2 rotations) on a
   distorted element; no spurious shear locking on thin plates.
V4 MITC4 simply supported square plate fundamental frequency vs thin-plate
   analytic within 2% (consistent-ish lumped mass).
V5 DKT: 3 zero-energy modes; SS plate (tria mesh) fundamental within 3%.
V6 CST patch: constant-strain field reproduced exactly.
"""
import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from fe_core import qm6_membrane, mitc4_bending, cst_membrane, dkt_bending

E_, nu_, rho_ = 1.0e7, 0.3, 2.5e-4
G_ = E_ / (2 * (1 + nu_))
rep = {}

def nzero(K, tol=1e-8):
    w = np.linalg.eigvalsh(K)
    return int((np.abs(w) < tol * np.abs(w).max()).sum()), w

# ---- V1: QM6 zero modes on distorted quad
Xl2 = np.array([[[0., 0.], [2.2, 0.1], [1.9, 1.8], [-0.1, 1.4]]])
K, area = qm6_membrane(Xl2, np.array([E_]), np.array([nu_]), np.array([0.1]))
nz, w = nzero(K[0])
rep['V1_qm6_zero_modes'] = dict(n_zero=nz, expected=3, ok=nz == 3)

# ---- V2: QM6 cantilever, L=48, h=4, t=1, P=40 (Cook-style slender beam)
L, h, t, P = 48.0, 4.0, 1.0, 40.0
nx, ny = 24, 2
xs = np.linspace(0, L, nx + 1); ys = np.linspace(-h / 2, h / 2, ny + 1)
nid = {}
coords = []
for j, y in enumerate(ys):
    for i, x in enumerate(xs):
        nid[(i, j)] = len(coords); coords.append((x, y))
coords = np.array(coords)
quads = []
for j in range(ny):
    for i in range(nx):
        quads.append((nid[(i, j)], nid[(i + 1, j)],
                      nid[(i + 1, j + 1)], nid[(i, j + 1)]))
quads = np.array(quads)
Xl = coords[quads]
Ke, _ = qm6_membrane(Xl, np.full(len(quads), E_), np.full(len(quads), nu_),
                     np.full(len(quads), t))
ndof = 2 * len(coords)
rows, cols, vals = [], [], []
for e, q in enumerate(quads):
    dofs = np.array([[2 * n, 2 * n + 1] for n in q]).ravel()
    rows.append(np.repeat(dofs, 8)); cols.append(np.tile(dofs, 8))
    vals.append(Ke[e].ravel())
K = sp.csr_matrix((np.concatenate(vals),
                   (np.concatenate(rows), np.concatenate(cols))),
                  shape=(ndof, ndof))
fixed = [d for (i, j), n in nid.items() if i == 0 for d in (2 * n, 2 * n + 1)]
free = np.setdiff1d(np.arange(ndof), fixed)
F = np.zeros(ndof)
tip_nodes = [n for (i, j), n in nid.items() if i == nx]
for n in tip_nodes:
    F[2 * n + 1] = P / len(tip_nodes)
u = np.zeros(ndof)
u[free] = spla.spsolve(K[np.ix_(free, free)].tocsc(), F[free])
delta = np.mean([u[2 * n + 1] for n in tip_nodes])
I = t * h ** 3 / 12
delta_beam = P * L ** 3 / (3 * E_ * I) + P * L / (5 / 6 * G_ * h * t)
rep['V2_qm6_cantilever'] = dict(fem=float(delta), beam=float(delta_beam),
                                err_pct=float(100 * (delta / delta_beam - 1)),
                                ok=abs(delta / delta_beam - 1) < 0.02)

# ---- V3: MITC4 zero modes (distorted, thin)
Kb = mitc4_bending(Xl2, np.array([E_]), np.array([nu_]), np.array([G_]),
                   np.array([0.02]), np.array([1.0]), np.array([5 / 6]))
nz, w = nzero(Kb[0], tol=1e-9)
rep['V3_mitc4_zero_modes'] = dict(n_zero=nz, expected=3, ok=nz == 3)

# ---- V3b: MITC4 rigid tilts in NASTRAN sign convention (thx about x, etc.)
def rigid_resid(Kel, Xn, kind):
    u = np.zeros(Kel.shape[0])
    nn = Xn.shape[0]
    for a in range(nn):
        x, y = Xn[a]
        if kind == 'tilt_x':   # w=+y*thx, thx=1
            u[3 * a] = y; u[3 * a + 1] = 1.0
        else:                   # w=-x*thy, thy=1
            u[3 * a] = -x; u[3 * a + 2] = 1.0
    r = Kel @ u
    return float(np.abs(r).max() / np.abs(Kel).max())

rx = rigid_resid(Kb[0], Xl2[0], 'tilt_x')
ry = rigid_resid(Kb[0], Xl2[0], 'tilt_y')
rep['V3b_mitc4_rigid_tilt'] = dict(resid_x=rx, resid_y=ry,
                                   ok=max(rx, ry) < 1e-12)

# ---- V4: MITC4 SS plate fundamental
a, tp = 10.0, 0.1
nq = 12
xs = np.linspace(0, a, nq + 1)
nid = {}; coords = []
for j in range(nq + 1):
    for i in range(nq + 1):
        nid[(i, j)] = len(coords); coords.append((xs[i], xs[j]))
coords = np.array(coords)
quads = []
for j in range(nq):
    for i in range(nq):
        quads.append((nid[(i, j)], nid[(i + 1, j)],
                      nid[(i + 1, j + 1)], nid[(i, j + 1)]))
quads = np.array(quads)
Xl = coords[quads]
ne = len(quads)
Ke = mitc4_bending(Xl, np.full(ne, E_), np.full(ne, nu_), np.full(ne, G_),
                   np.full(ne, tp), np.ones(ne), np.full(ne, 5 / 6))
nn = len(coords); ndof = 3 * nn
rows, cols, vals = [], [], []
for e, q in enumerate(quads):
    dofs = np.array([[3 * n, 3 * n + 1, 3 * n + 2] for n in q]).ravel()
    rows.append(np.repeat(dofs, 12)); cols.append(np.tile(dofs, 12))
    vals.append(Ke[e].ravel())
K = sp.csr_matrix((np.concatenate(vals),
                   (np.concatenate(rows), np.concatenate(cols))),
                  shape=(ndof, ndof))
# lumped mass: w gets rho*t*A/4, rotations get rho*t^3/12*A/4
M = np.zeros(ndof)
elA = (a / nq) ** 2
for e, q in enumerate(quads):
    for n in q:
        M[3 * n] += rho_ * tp * elA / 4
        M[3 * n + 1] += rho_ * tp ** 3 / 12 * elA / 4
        M[3 * n + 2] += rho_ * tp ** 3 / 12 * elA / 4
# SS: w=0 on edges
fixed = [3 * n for (i, j), n in nid.items()
         if i in (0, nq) or j in (0, nq)]
free = np.setdiff1d(np.arange(ndof), fixed)
Kf = K[np.ix_(free, free)]
Mf = sp.diags(M[free])
w2, _ = spla.eigsh(Kf.tocsc(), k=3, M=Mf.tocsc(), sigma=0, which='LM')
f1 = np.sqrt(w2[0]) / (2 * np.pi)
D = E_ * tp ** 3 / (12 * (1 - nu_ ** 2))
f_ana = (np.pi / 2) * (1 / a ** 2 + 1 / a ** 2) * np.sqrt(D / (rho_ * tp))
rep['V4_mitc4_ss_plate'] = dict(fem=float(f1), analytic=float(f_ana),
                                err_pct=float(100 * (f1 / f_ana - 1)),
                                ok=abs(f1 / f_ana - 1) < 0.02)

# ---- V5: DKT zero modes + SS plate (tria mesh)
Xt = np.array([[[0., 0.], [2.0, 0.1], [0.9, 1.7]]])
Kt = dkt_bending(Xt, np.array([E_]), np.array([nu_]), np.array([0.05]),
                 np.array([1.0]))
nz, w = nzero(Kt[0], tol=1e-9)
rep['V5a_dkt_zero_modes'] = dict(n_zero=nz, expected=3, ok=nz == 3)
rx = rigid_resid(Kt[0], Xt[0], 'tilt_x')
ry = rigid_resid(Kt[0], Xt[0], 'tilt_y')
rep['V5c_dkt_rigid_tilt'] = dict(resid_x=rx, resid_y=ry,
                                 ok=max(rx, ry) < 1e-12)

tris = []
for j in range(nq):
    for i in range(nq):
        n1, n2, n3, n4 = (nid[(i, j)], nid[(i + 1, j)],
                          nid[(i + 1, j + 1)], nid[(i, j + 1)])
        tris.append((n1, n2, n3)); tris.append((n1, n3, n4))
tris = np.array(tris)
Xl = coords[tris]
ne = len(tris)
Ke = dkt_bending(Xl, np.full(ne, E_), np.full(ne, nu_), np.full(ne, tp),
                 np.ones(ne))
rows, cols, vals = [], [], []
for e, q in enumerate(tris):
    dofs = np.array([[3 * n, 3 * n + 1, 3 * n + 2] for n in q]).ravel()
    rows.append(np.repeat(dofs, 9)); cols.append(np.tile(dofs, 9))
    vals.append(Ke[e].ravel())
K = sp.csr_matrix((np.concatenate(vals),
                   (np.concatenate(rows), np.concatenate(cols))),
                  shape=(ndof, ndof))
Kf = K[np.ix_(free, free)]
w2, _ = spla.eigsh(Kf.tocsc(), k=3, M=Mf.tocsc(), sigma=0, which='LM')
f1 = np.sqrt(w2[0]) / (2 * np.pi)
rep['V5b_dkt_ss_plate'] = dict(fem=float(f1), analytic=float(f_ana),
                               err_pct=float(100 * (f1 / f_ana - 1)),
                               ok=abs(f1 / f_ana - 1) < 0.03)

# ---- V6: CST constant strain patch
Xc = np.array([[[0., 0.], [3.0, 0.2], [1.1, 2.5]]])
Kc, A = cst_membrane(Xc, np.array([E_]), np.array([nu_]), np.array([0.1]))
# impose u = x*1e-3 (exx = 1e-3): forces must match sigma*t on edges; check
# energy: 0.5 u'Ku == 0.5 * exx*C11*exx * A * t
uvec = np.zeros(6)
uvec[0::2] = Xc[0][:, 0] * 1e-3
Eng = 0.5 * uvec @ Kc[0] @ uvec
C11 = E_ / (1 - nu_ ** 2)
Eng_ana = 0.5 * C11 * (1e-3) ** 2 * A[0] * 0.1
rep['V6_cst_patch'] = dict(fem=float(Eng), analytic=float(Eng_ana),
                           ok=abs(Eng / Eng_ana - 1) < 1e-10)

ok = all(bool(v.get('ok', False)) for v in rep.values() if isinstance(v, dict))
rep['ALL_OK'] = ok
enc = lambda o: bool(o) if isinstance(o, np.bool_) else float(o)
json.dump(rep, open("fe_validate_report.json", "w"), indent=1, default=enc)
print(json.dumps(rep, indent=1, default=enc))
