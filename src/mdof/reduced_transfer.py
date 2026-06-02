"""Simple MDOF FEM-style transfer function and modal reduction prototype."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MdofSystem:
    m: np.ndarray
    c: np.ndarray
    k: np.ndarray


def chain_system(n: int = 6, m0: float = 1.0, k0: float = 5.0e5, zeta: float = 0.01) -> MdofSystem:
    m = np.eye(n) * m0
    k = np.zeros((n, n), dtype=float)
    for i in range(n):
        if i > 0:
            k[i, i] += k0
            k[i, i - 1] -= k0
            k[i - 1, i] -= k0
            k[i - 1, i - 1] += k0
    c = 2.0 * zeta * np.sqrt(k0 * m0) * np.eye(n)
    return MdofSystem(m=m, c=c, k=k)


def modal_reduction(sys: MdofSystem, n_modes: int = 3) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    evals, evecs = np.linalg.eigh(np.linalg.solve(sys.m, sys.k))
    idx = np.argsort(evals)
    phi = evecs[:, idx[:n_modes]]
    m_r = phi.T @ sys.m @ phi
    c_r = phi.T @ sys.c @ phi
    k_r = phi.T @ sys.k @ phi
    return m_r, c_r, k_r


def frf_drivepoint(m: np.ndarray, c: np.ndarray, k: np.ndarray, freqs_hz: np.ndarray, dof: int) -> np.ndarray:
    out = []
    for f in freqs_hz:
        w = 2.0 * math.pi * float(f)
        z = k + 1j * w * c - (w**2) * m
        h = np.linalg.inv(z)
        out.append(h[dof, dof])
    return np.asarray(out, dtype=np.complex128)


def reduced_drivepoint_frf(sys: MdofSystem, freqs_hz: np.ndarray, dof: int = 0, n_modes: int = 3) -> np.ndarray:
    m_r, c_r, k_r = modal_reduction(sys, n_modes=n_modes)
    phi = np.linalg.eigh(np.linalg.solve(sys.m, sys.k))[1][:, :n_modes]
    out = []
    for f in freqs_hz:
        w = 2.0 * math.pi * float(f)
        z_r = k_r + 1j * w * c_r - (w**2) * m_r
        h_r = np.linalg.inv(z_r)
        h_full_approx = phi @ h_r @ phi.T
        out.append(h_full_approx[dof, dof])
    return np.asarray(out, dtype=np.complex128)
