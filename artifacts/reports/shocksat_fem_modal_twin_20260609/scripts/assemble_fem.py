#!/usr/bin/env python3
"""Assemble the ShockSat parametric FEM: per-property stiffness blocks K_pid,
lumped mass M, RBE2 elimination T, on the full 6-DOF-per-grid space.

K(theta) = sum_groups theta_g * (sum_{pid in g} K_pid)  -- stiffness is linear
in E (shells) and k (bushes), so scaling K_pid is exactly scaling the moduli.

Outputs: matrices/K_<pid>.npz, matrices/M.npz, matrices/T.npz, assembly_meta.json
Checks: total mass + CG vs NASA pptx (127.89 lb, CG_Z 28.01 in); rigid-body
energy of K_total; duplicate-dependent-DOF assertion for RBE2.
"""
import json
import time
import numpy as np
import scipy.sparse as sp
from fe_core import (quad_local_frames, qm6_membrane, mitc4_bending,
                     cst_membrane, dkt_bending)

K6ROT = 100.0          # PARAM,K6ROT from Modes.dat
GRAV = 386.088         # in/s^2 (NASA standard for lb->lbf*s^2/in)

t0 = time.time()
z = np.load("fem_model.npz", allow_pickle=True)
gids = z["gids"]; xyz = z["xyz"]
pshell = json.loads(str(z["pshell"])); pbush = json.loads(str(z["pbush"]))
mat1 = json.loads(str(z["mat1"])); cords = json.loads(str(z["cords"]))
g2i = {int(g): i for i, g in enumerate(gids)}
N = len(gids); NDOF = 6 * N

def dofs_of(gidx):
    return (6 * gidx[..., None] + np.arange(6)).reshape(*gidx.shape[:-1], -1)

# ---------------------------------------------------------------- shells
def shell_K_M(pid):
    """Returns (K_coo_triplets, M_diag_contrib) for all elements of pid."""
    p = pshell[str(pid)]
    m = mat1[str(p['mid1'])]
    E, nu, G, rho = m['E'], m['nu'], m['G'], m['rho']
    t = p['t']; br = p['bend_ratio']; tst = p['ts_t']
    rowsL, colsL, valsL = [], [], []
    Mdiag = np.zeros(NDOF)

    q = z["cquad4"]; qsel = q[:, 1] == pid
    tri = z["ctria3"]; tsel = tri[:, 1] == pid
    for kind, conn in (("q", q[qsel][:, 2:6]), ("t", tri[tsel][:, 2:5])):
        if len(conn) == 0:
            continue
        nidx = np.vectorize(g2i.get)(conn)               # (ne,nn)
        X = xyz[nidx]                                     # (ne,nn,3)
        nn = X.shape[1]
        if kind == "q":
            O, R, Xl2, warp = quad_local_frames(X)
            ne = len(X)
            Em = np.full(ne, E); num = np.full(ne, nu)
            Km, area = qm6_membrane(Xl2, Em, num, np.full(ne, t))
            Kb = mitc4_bending(Xl2, Em, num, np.full(ne, G),
                               np.full(ne, t), np.full(ne, br),
                               np.full(ne, tst))
        else:
            # tria local frame: e3 normal, e1 along side 1-2
            e1 = X[:, 1] - X[:, 0]
            e3 = np.cross(e1, X[:, 2] - X[:, 0])
            e3 /= np.linalg.norm(e3, axis=1, keepdims=True)
            e1 = e1 - (e1 * e3).sum(1, keepdims=True) * e3
            e1 /= np.linalg.norm(e1, axis=1, keepdims=True)
            e2 = np.cross(e3, e1)
            R = np.stack([e1, e2, e3], axis=1)
            O = X.mean(axis=1)
            Xl2 = np.einsum('eij,enj->eni', R, X - O[:, None, :])[..., :2]
            warp = np.zeros(len(X))
            ne = len(X)
            Em = np.full(ne, E); num = np.full(ne, nu)
            Km, area = cst_membrane(Xl2, Em, num, np.full(ne, t))
            Kb = dkt_bending(Xl2, Em, num, np.full(ne, t), np.full(ne, br))

        # local 6nn x 6nn: [u v w thx thy thz] per node
        Kl = np.zeros((ne, 6 * nn, 6 * nn))
        mi = np.array([6 * a + c for a in range(nn) for c in (0, 1)])
        bi = np.array([6 * a + c for a in range(nn) for c in (2, 3, 4)])
        Kl[:, mi[:, None], mi[None, :]] += Km
        Kl[:, bi[:, None], bi[None, :]] += Kb
        # drilling penalty (NX K6ROT): k = K6ROT*1e-6*G*t*A per node
        kdr = K6ROT * 1e-6 * G * t * area / nn            # (ne,)
        for a in range(nn):
            Kl[:, 6 * a + 5, 6 * a + 5] += kdr
        # rotate to global: u_local = R u_global per 3-block
        Kl4 = Kl.reshape(ne, 2 * nn, 3, 2 * nn, 3)
        Kg = np.einsum('eki,eakbl,elj->eaibj', R, Kl4, R).reshape(
            ne, 6 * nn, 6 * nn)
        dofs = dofs_of(nidx)                              # (ne,6nn)
        nd = 6 * nn
        rowsL.append(np.repeat(dofs, nd, axis=1).ravel())
        colsL.append(np.tile(dofs, (1, nd)).ravel())
        valsL.append(Kg.ravel())
        # lumped mass: translations rho*t*A/nn; rotations rho*t^3/12*A/nn
        mtr = rho * t * area / nn
        mro = rho * t ** 3 / 12.0 * area / nn
        for a in range(nn):
            for c in range(3):
                np.add.at(Mdiag, 6 * nidx[:, a] + c, mtr)
            for c in range(3, 6):
                np.add.at(Mdiag, 6 * nidx[:, a] + c, mro)
    if not rowsL:
        return None, Mdiag, {}
    Kc = sp.coo_matrix(
        (np.concatenate(valsL),
         (np.concatenate(rowsL), np.concatenate(colsL))),
        shape=(NDOF, NDOF)).tocsr()
    info = dict(n_elems=int(qsel.sum() + tsel.sum()))
    return Kc, Mdiag, info

# ---------------------------------------------------------------- bushes
def skew(v):
    s = np.zeros((3, 3))
    s[0, 1], s[0, 2] = -v[2], v[1]
    s[1, 0], s[1, 2] = v[2], -v[0]
    s[2, 0], s[2, 1] = -v[1], v[0]
    return s

def bush_K(pid):
    sel = z["cbush"][:, 1] == pid
    els = z["cbush"][sel]
    kvals = np.array(pbush[str(pid)]['k'])
    rows, cols, vals = [], [], []
    for eid, _, ga, gb, cid in els:
        ia, ib = g2i[ga], g2i[gb]
        xa, xb = xyz[ia], xyz[ib]
        P = 0.5 * (xa + xb)
        ra, rb = P - xa, P - xb
        R = np.eye(3) if cid == 0 else np.array(cords[str(cid)]['R'])
        B = np.zeros((6, 12))
        B[0:3, 0:3] = -R
        B[0:3, 3:6] = R @ skew(ra)
        B[0:3, 6:9] = R
        B[0:3, 9:12] = -R @ skew(rb)
        B[3:6, 3:6] = -R
        B[3:6, 9:12] = R
        Ke = B.T @ np.diag(kvals) @ B
        d = np.concatenate([6 * ia + np.arange(6), 6 * ib + np.arange(6)])
        rows.append(np.repeat(d, 12)); cols.append(np.tile(d, 12))
        vals.append(Ke.ravel())
    Kc = sp.coo_matrix(
        (np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
        shape=(NDOF, NDOF)).tocsr()
    return Kc, dict(n_elems=int(sel.sum()), k=kvals.tolist())

# ---------------------------------------------------------------- CONM2
def conm2_M():
    rows, cols, vals = [], [], []
    for row in z["conm2"]:
        eid, g, m = int(row[0]), int(row[1]), row[2]
        off = row[3:6]
        I11, I21, I22, I31, I32, I33 = row[6:12]
        Icm = np.array([[I11, I21, I31], [I21, I22, I32], [I31, I32, I33]])
        S = skew(off)
        M6 = np.zeros((6, 6))
        M6[0:3, 0:3] = m * np.eye(3)
        M6[0:3, 3:6] = -m * S          # F = m*(a + alpha x c) -> coupling
        M6[3:6, 0:3] = m * S
        M6[3:6, 3:6] = Icm + m * (S @ S.T)
        i = g2i[g]
        d = 6 * i + np.arange(6)
        rows.append(np.repeat(d, 6)); cols.append(np.tile(d, 6))
        vals.append(M6.ravel())
    return sp.coo_matrix(
        (np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
        shape=(NDOF, NDOF)).tocsr()

# ---------------------------------------------------------------- RBE2 -> T
def build_T():
    rb = z["rbe2"]; gms_flat = z["rbe2_gms"]
    dep_rows = {}
    ptr = 0
    indep_of = {}
    for eid, gn, cm, nGM in rb:
        gms = gms_flat[ptr:ptr + nGM]; ptr += nGM
        cmd = [int(c) - 1 for c in str(cm)]
        for gm in gms:
            for c in cmd:
                dof = 6 * g2i[gm] + c
                assert dof not in dep_rows, f"DOF {dof} dependent twice"
                dep_rows[dof] = (g2i[gn], c, g2i[gm])
    # no chaining: GN dofs must not themselves be dependent
    for dof, (ign, c, igm) in dep_rows.items():
        for cc in range(6):
            assert 6 * ign + cc not in dep_rows, "chained RBE2 - unhandled"
    dep = np.array(sorted(dep_rows))
    keep = np.setdiff1d(np.arange(NDOF), dep)
    colmap = -np.ones(NDOF, dtype=np.int64)
    colmap[keep] = np.arange(len(keep))
    rows, cols, vals = [keep], [colmap[keep]], [np.ones(len(keep))]
    for dof in dep:
        ign, c, igm = dep_rows[dof]
        r = xyz[igm] - xyz[ign]
        if c < 3:  # translation: u_dep = u_gn + theta_gn x r
            rows.append([dof]); cols.append([colmap[6 * ign + c]]); vals.append([1.0])
            S = skew(r)   # (theta x r) = -skew(r) theta = skew(theta) r
            # u_dep_c = u_gn_c + (theta x r)_c ; (theta x r) = -S @ theta
            for cc in range(3):
                v = -S[c, cc]
                if v != 0.0:
                    rows.append([dof]); cols.append([colmap[6 * ign + 3 + cc]])
                    vals.append([v])
        else:      # rotation: theta_dep = theta_gn
            rows.append([dof]); cols.append([colmap[6 * ign + c]]); vals.append([1.0])
    T = sp.coo_matrix(
        (np.concatenate(vals).astype(float),
         (np.concatenate(rows).astype(int), np.concatenate(cols).astype(int))),
        shape=(NDOF, len(keep))).tocsr()
    return T, keep, dep

# ================================================================= driver
if __name__ == "__main__":
    import os
    os.makedirs("matrices", exist_ok=True)
    meta = {"pids": {}, "NDOF": int(NDOF)}
    Mdiag_total = np.zeros(NDOF)
    for pid in sorted(int(k) for k in pshell):
        K, Mdiag, info = shell_K_M(pid)
        sp.save_npz(f"matrices/K_shell_{pid}.npz", K)
        Mdiag_total += Mdiag
        meta["pids"][f"shell_{pid}"] = dict(
            **info, file=pshell[str(pid)]['file'],
            mid=pshell[str(pid)]['mid1'], t=pshell[str(pid)]['t'],
            nnz=int(K.nnz))
        print(f"shell pid {pid}: {info['n_elems']} elems, nnz {K.nnz}, "
              f"t={time.time()-t0:.0f}s", flush=True)
    for pid in sorted(int(k) for k in pbush):
        K, info = bush_K(pid)
        sp.save_npz(f"matrices/K_bush_{pid}.npz", K)
        meta["pids"][f"bush_{pid}"] = dict(
            **info, file=pbush[str(pid)]['file'], nnz=int(K.nnz))
        print(f"bush pid {pid}: {info['n_elems']} elems", flush=True)

    Mc = conm2_M()
    M = sp.diags(Mdiag_total).tocsr() + Mc
    sp.save_npz("matrices/M.npz", M)

    T, keep, dep = build_T()
    sp.save_npz("matrices/T.npz", T)
    np.save("matrices/keep_dofs.npy", keep)

    # ------------------------------ checks
    # rigid vectors (basic frame, about origin)
    RV = np.zeros((NDOF, 6))
    for i in range(N):
        RV[6 * i + 0, 0] = RV[6 * i + 1, 1] = RV[6 * i + 2, 2] = 1.0
        x, y, zz = xyz[i]
        RV[6 * i + 1, 3] = -zz; RV[6 * i + 2, 3] = y; RV[6 * i + 3, 3] = 1.0
        RV[6 * i + 0, 4] = zz; RV[6 * i + 2, 4] = -x; RV[6 * i + 4, 4] = 1.0
        RV[6 * i + 0, 5] = -y; RV[6 * i + 1, 5] = x; RV[6 * i + 5, 5] = 1.0
    mass_mat = RV.T @ (M @ RV)
    m_tot = mass_mat[0, 0]
    # first moments from translation-rotation coupling of the rigid 6x6:
    # int x dm = mass_mat[1,5]; int y dm = mass_mat[2,3]; int z dm = mass_mat[0,4]
    cg = np.array([mass_mat[1, 5], mass_mat[2, 3], mass_mat[0, 4]]) / m_tot
    Ktot = None
    for f in sorted(os.listdir("matrices")):
        if f.startswith("K_"):
            Kp = sp.load_npz(f"matrices/{f}")
            Ktot = Kp if Ktot is None else Ktot + Kp
    # rigid-body strain energy (should be ~0 relative to K norm)
    rbe = np.array([float(RV[:, j] @ (Ktot @ RV[:, j])) for j in range(6)])
    kscale = abs(Ktot).max()
    meta["checks"] = dict(
        total_mass=float(m_tot), total_weight_lb=float(m_tot * GRAV),
        nasa_weight_lb=127.89,
        weight_err_pct=float(100 * (m_tot * GRAV / 127.89 - 1)),
        cg=[float(c) for c in cg], nasa_cg=[0.0, 0.0, 28.01],
        rigid_energy=rbe.tolist(), K_max=float(kscale),
        rigid_energy_rel=(rbe / kscale).tolist(),
        n_dep_dofs=int(len(dep)), n_keep_dofs=int(len(keep)))
    json.dump(meta, open("assembly_meta.json", "w"), indent=1)
    print(json.dumps(meta["checks"], indent=1))
    print(f"done in {time.time()-t0:.0f}s")
