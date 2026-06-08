"""8-node linear hexahedral solid element (3 translational DOF per node)."""
from __future__ import annotations

import math

import numpy as np


def _shape_hex(xi: float, eta: float, zeta: float) -> np.ndarray:
    return 0.125 * np.array([
        (1 - xi) * (1 - eta) * (1 - zeta),
        (1 + xi) * (1 - eta) * (1 - zeta),
        (1 + xi) * (1 + eta) * (1 - zeta),
        (1 - xi) * (1 + eta) * (1 - zeta),
        (1 - xi) * (1 - eta) * (1 + zeta),
        (1 + xi) * (1 - eta) * (1 + zeta),
        (1 + xi) * (1 + eta) * (1 + zeta),
        (1 - xi) * (1 + eta) * (1 + zeta),
    ])


def _dshape_hex(xi: float, eta: float, zeta: float) -> np.ndarray:
    d = np.zeros((3, 8))
    d[0, :] = 0.125 * np.array([
        -(1 - eta) * (1 - zeta), (1 - eta) * (1 - zeta),
        (1 + eta) * (1 - zeta), -(1 + eta) * (1 - zeta),
        -(1 - eta) * (1 + zeta), (1 - eta) * (1 + zeta),
        (1 + eta) * (1 + zeta), -(1 + eta) * (1 + zeta),
    ])
    d[1, :] = 0.125 * np.array([
        -(1 - xi) * (1 - zeta), -(1 + xi) * (1 - zeta),
        (1 + xi) * (1 - zeta), (1 - xi) * (1 - zeta),
        -(1 - xi) * (1 + zeta), -(1 + xi) * (1 + zeta),
        (1 + xi) * (1 + zeta), (1 - xi) * (1 + zeta),
    ])
    d[2, :] = 0.125 * np.array([
        -(1 - xi) * (1 - eta), -(1 + xi) * (1 - eta),
        -(1 + xi) * (1 + eta), -(1 - xi) * (1 + eta),
        (1 - xi) * (1 - eta), (1 + xi) * (1 - eta),
        (1 + xi) * (1 + eta), (1 - xi) * (1 + eta),
    ])
    return d


def _elastic_matrix(E: float, nu: float) -> np.ndarray:
    lam = E * nu / ((1 + nu) * (1 - 2 * nu))
    mu = E / (2 * (1 + nu))
    c = np.zeros((6, 6))
    c[0, 0] = c[1, 1] = c[2, 2] = lam + 2 * mu
    c[0, 1] = c[0, 2] = c[1, 0] = c[1, 2] = c[2, 0] = c[2, 1] = lam
    c[3, 3] = c[4, 4] = c[5, 5] = mu
    return c


def hex8_ke_me(coords: np.ndarray, E: float, nu: float, rho: float) -> tuple[np.ndarray, np.ndarray]:
    c = _elastic_matrix(E, nu)
    ke = np.zeros((24, 24))
    me = np.zeros((24, 24))
    gpts = [
        (-1 / math.sqrt(3), -1 / math.sqrt(3), -1 / math.sqrt(3)),
        (1 / math.sqrt(3), -1 / math.sqrt(3), -1 / math.sqrt(3)),
        (1 / math.sqrt(3), 1 / math.sqrt(3), -1 / math.sqrt(3)),
        (-1 / math.sqrt(3), 1 / math.sqrt(3), -1 / math.sqrt(3)),
        (-1 / math.sqrt(3), -1 / math.sqrt(3), 1 / math.sqrt(3)),
        (1 / math.sqrt(3), -1 / math.sqrt(3), 1 / math.sqrt(3)),
        (1 / math.sqrt(3), 1 / math.sqrt(3), 1 / math.sqrt(3)),
        (-1 / math.sqrt(3), 1 / math.sqrt(3), 1 / math.sqrt(3)),
    ]
    for xi, eta, zeta in gpts:
        dN = _dshape_hex(xi, eta, zeta)
        j = dN @ coords
        detj = np.linalg.det(j)
        invj = np.linalg.inv(j)
        dNdx = invj @ dN
        b = np.zeros((6, 24))
        for a in range(8):
            ia = 3 * a
            gx, gy, gz = dNdx[:, a]
            b[0, ia] = gx
            b[1, ia + 1] = gy
            b[2, ia + 2] = gz
            b[3, ia] = gy
            b[3, ia + 1] = gx
            b[4, ia + 1] = gz
            b[4, ia + 2] = gy
            b[5, ia] = gz
            b[5, ia + 2] = gx
        ke += b.T @ c @ b * detj
        n = _shape_hex(xi, eta, zeta)
        nm = np.zeros((3, 24))
        for a in range(8):
            nm[:, 3 * a: 3 * a + 3] = np.eye(3) * n[a]
        me += rho * (nm.T @ nm) * detj
    return ke, me
