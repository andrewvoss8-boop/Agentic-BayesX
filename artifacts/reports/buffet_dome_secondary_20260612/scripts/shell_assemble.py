#!/usr/bin/env python3
"""Shared shell-element composition (QM6+MITC4 quads / CST+DKT trias +
rigid-rotation-invariant drilling penalty + lumped mass), the SAME code path
for build_model.py (production) and validate_assembly.py (Donnell check).
Pattern follows the validated ShockSat assemble_fem.py."""
import numpy as np
from fe_core import (quad_local_frames, qm6_membrane, mitc4_bending,
                     cst_membrane, dkt_bending, _q4_dN)


def make_shell_group(XYZ, rows, cols, vals, Mdiag, K6ROT_default=100.0):
    """Bind mesh coords + triplet accumulators; return shell_group()."""

    def shell_group(conn, grp_ids, E, nu, t, rho, G=None, K6ROT=None):
        if len(conn) == 0:
            return 0.0
        K6ROT = K6ROT_default if K6ROT is None else K6ROT
        G = E / (2 * (1 + nu)) if G is None else G
        X = XYZ[conn]; ne, nn = conn.shape[0], conn.shape[1]
        if nn == 4:
            O, Rl, Xl2, warp = quad_local_frames(X)
            Em = np.full(ne, E); num = np.full(ne, nu)
            Km, area = qm6_membrane(Xl2, Em, num, np.full(ne, t))
            Kb = mitc4_bending(Xl2, Em, num, np.full(ne, G),
                               np.full(ne, t), np.ones(ne), np.full(ne, 5 / 6))
        else:
            e1 = X[:, 1] - X[:, 0]
            e3 = np.cross(e1, X[:, 2] - X[:, 0])
            e3 /= np.linalg.norm(e3, axis=1, keepdims=True)
            e1 = e1 - (e1 * e3).sum(1, keepdims=True) * e3
            e1 /= np.linalg.norm(e1, axis=1, keepdims=True)
            e2 = np.cross(e3, e1)
            Rl = np.stack([e1, e2, e3], axis=1)
            O = X.mean(axis=1)
            Xl2 = np.einsum('eij,enj->eni', Rl, X - O[:, None, :])[..., :2]
            Em = np.full(ne, E); num = np.full(ne, nu)
            Km, area = cst_membrane(Xl2, Em, num, np.full(ne, t))
            Kb = dkt_bending(Xl2, Em, num, np.full(ne, t), np.ones(ne))
        Kl = np.zeros((ne, 6 * nn, 6 * nn))
        mi = np.array([6 * a + c for a in range(nn) for c in (0, 1)])
        bi = np.array([6 * a + c for a in range(nn) for c in (2, 3, 4)])
        Kl[:, mi[:, None], mi[None, :]] += Km
        Kl[:, bi[:, None], bi[None, :]] += Kb
        if nn == 4:
            dN0 = _q4_dN(0.0, 0.0)
            J = np.einsum('ka,eaj->ekj', dN0, Xl2)
            dN_xy = np.linalg.solve(J, np.broadcast_to(dN0, (ne, 2, nn)).copy())
            dNdx, dNdy = dN_xy[:, 0, :], dN_xy[:, 1, :]
        else:
            x1, y1 = Xl2[:, 0, 0], Xl2[:, 0, 1]
            x2, y2 = Xl2[:, 1, 0], Xl2[:, 1, 1]
            x3, y3 = Xl2[:, 2, 0], Xl2[:, 2, 1]
            A2 = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
            dNdx = np.stack([y2 - y3, y3 - y1, y1 - y2], 1) / A2[:, None]
            dNdy = np.stack([x3 - x2, x1 - x3, x2 - x1], 1) / A2[:, None]
        Bw = np.zeros((ne, 6 * nn))
        Bw[:, 0::6] = -0.5 * dNdy; Bw[:, 1::6] = 0.5 * dNdx
        kdr = K6ROT * 1e-6 * G * t * area / nn
        for a_ in range(nn):
            Ba = -Bw.copy(); Ba[:, 6 * a_ + 5] += 1.0
            Kl += kdr[:, None, None] * np.einsum('ei,ej->eij', Ba, Ba)
        Kl4 = Kl.reshape(ne, 2 * nn, 3, 2 * nn, 3)
        Kg = np.einsum('eki,eakbl,elj->eaibj', Rl, Kl4, Rl).reshape(
            ne, 6 * nn, 6 * nn)
        dofs = (6 * conn[..., None] + np.arange(6)).reshape(ne, -1)
        nd = 6 * nn
        rows.append(np.repeat(dofs, nd, axis=1).ravel())
        cols.append(np.tile(dofs, (1, nd)).ravel())
        vals.append(Kg.ravel())
        mtr = rho * t * area / nn
        mro = rho * t ** 3 / 12.0 * area / nn
        for a_ in range(nn):
            for c in range(3):
                np.add.at(Mdiag, 6 * conn[:, a_] + c, mtr)
            for c in range(3, 6):
                np.add.at(Mdiag, 6 * conn[:, a_] + c, mro)
        return float((rho * t * area).sum())

    return shell_group
