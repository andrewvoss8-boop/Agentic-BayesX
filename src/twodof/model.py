"""2DOF frequency-domain model utilities for FBS/StatFEM experiments."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TwoDofParams:
    m1: float
    m2: float
    k1: float
    k2: float
    k12: float
    c1: float
    c2: float
    c12: float


def default_from_natural_frequencies(f1_hz: float = 110.0, f2_hz: float = 75.0) -> TwoDofParams:
    """Assume nominal masses and derive baseline stiffness from uncoupled natural frequencies."""
    m1 = 1.0
    m2 = 0.6
    w1 = 2.0 * math.pi * f1_hz
    w2 = 2.0 * math.pi * f2_hz
    k1 = m1 * w1**2
    k2 = m2 * w2**2
    zeta1 = 0.015
    zeta2 = 0.020
    c1 = 2.0 * zeta1 * math.sqrt(k1 * m1)
    c2 = 2.0 * zeta2 * math.sqrt(k2 * m2)
    return TwoDofParams(m1=m1, m2=m2, k1=k1, k2=k2, k12=k2, c1=c1, c2=c2, c12=c2)


def matrices(p: TwoDofParams) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    m = np.array([[p.m1, 0.0], [0.0, p.m2]], dtype=float)
    k = np.array([[p.k1 + p.k12, -p.k12], [-p.k12, p.k2 + p.k12]], dtype=float)
    c = np.array([[p.c1 + p.c12, -p.c12], [-p.c12, p.c2 + p.c12]], dtype=float)
    return m, c, k


def dynamic_stiffness(p: TwoDofParams, omega: float) -> np.ndarray:
    m, c, k = matrices(p)
    return k + 1j * omega * c - (omega**2) * m


def frf_matrix(p: TwoDofParams, omega: float) -> np.ndarray:
    z = dynamic_stiffness(p, omega)
    return np.linalg.inv(z)


def accel_over_force_matrix(p: TwoDofParams, freqs_hz: np.ndarray) -> np.ndarray:
    """Acceleration/force FRF matrix with rows=response DOF and columns=force DOF."""
    out = np.zeros((len(freqs_hz), 2, 2), dtype=np.complex128)
    for i, f in enumerate(freqs_hz):
        w = 2.0 * math.pi * float(f)
        out[i] = -(w**2) * frf_matrix(p, w)
    return out


def apparent_mass_from_drivepoint(p: TwoDofParams, freqs_hz: np.ndarray, dof: int) -> np.ndarray:
    """Apparent mass = F / a at selected drive dof (0 or 1)."""
    out = []
    for f in freqs_hz:
        w = 2.0 * math.pi * float(f)
        h = frf_matrix(p, w)
        h_jj = h[dof, dof]
        a_over_f = -(w**2) * h_jj
        out.append(1.0 / a_over_f)
    return np.asarray(out, dtype=np.complex128)


def apparent_mass_dome_uncoupled(
    freqs_hz: np.ndarray,
    m1: float,
    k1: float,
    c1: float,
) -> np.ndarray:
    out = []
    for f in freqs_hz:
        w = 2.0 * math.pi * float(f)
        z = k1 + 1j * w * c1 - (w**2) * m1
        h = 1.0 / z
        a_over_f = -(w**2) * h
        out.append(1.0 / a_over_f)
    return np.asarray(out, dtype=np.complex128)


def sdof_base_reaction_apparent_mass(
    freqs_hz: np.ndarray,
    mass: float,
    stiffness: float,
    damping: float,
) -> np.ndarray:
    """Base reaction force over base acceleration for a base-driven SDOF load."""
    out = []
    for f in freqs_hz:
        w = 2.0 * math.pi * float(f)
        dynamic_stiffness_sdof = stiffness + 1j * w * damping - (w**2) * mass
        mount_stiffness = stiffness + 1j * w * damping
        out.append(mass * mount_stiffness / dynamic_stiffness_sdof)
    return np.asarray(out, dtype=np.complex128)


def sdof_source_apparent_mass(
    freqs_hz: np.ndarray,
    mass: float,
    stiffness: float,
    damping: float,
) -> np.ndarray:
    """Source apparent mass looking back into a fixed-base SDOF mounting structure."""
    out = []
    for f in freqs_hz:
        w = 2.0 * math.pi * float(f)
        dynamic_stiffness_sdof = stiffness + 1j * w * damping - (w**2) * mass
        out.append(-dynamic_stiffness_sdof / (w**2))
    return np.asarray(out, dtype=np.complex128)


def common_base_reaction_apparent_mass(p: TwoDofParams, freqs_hz: np.ndarray) -> dict[str, np.ndarray]:
    """Support reaction force over common base acceleration for the coupled 2DOF system."""
    m, c, k = matrices(p)
    base_c = np.diag([p.c1, p.c2]).astype(np.complex128)
    base_k = np.diag([p.k1, p.k2]).astype(np.complex128)
    influence = np.ones(2, dtype=np.complex128)
    primary = []
    tray = []
    total = []
    for f in freqs_hz:
        w = 2.0 * math.pi * float(f)
        z = k + 1j * w * c - (w**2) * m
        rel_disp = np.linalg.solve(z, (w**2) * m @ influence)
        support_reactions = (base_k + 1j * w * base_c) @ rel_disp
        apparent = -support_reactions / (w**2)
        primary.append(apparent[0])
        tray.append(apparent[1])
        total.append(np.sum(apparent))
    return {
        "primary_support": np.asarray(primary, dtype=np.complex128),
        "tray_support": np.asarray(tray, dtype=np.complex128),
        "total_base": np.asarray(total, dtype=np.complex128),
    }


def tray_base_to_tray_accel_transfer(freqs_hz: np.ndarray, p: TwoDofParams) -> np.ndarray:
    """Standalone tray acceleration over base acceleration."""
    out = []
    for f in freqs_hz:
        w = 2.0 * math.pi * float(f)
        num = p.k2 + 1j * w * p.c2
        den = p.k2 + 1j * w * p.c2 - p.m2 * (w**2)
        out.append(num / den)
    return np.asarray(out, dtype=np.complex128)


def tray_accel_from_m1_force(p: TwoDofParams, freqs_hz: np.ndarray, force_spectrum: np.ndarray) -> np.ndarray:
    """Accel spectrum at tray (dof=1) due to force on m1 (dof=0)."""
    if len(freqs_hz) != len(force_spectrum):
        raise ValueError("freqs_hz and force_spectrum length mismatch")
    out = []
    for i, f in enumerate(freqs_hz):
        w = 2.0 * math.pi * float(f)
        h = frf_matrix(p, w)
        x2 = h[1, 0] * force_spectrum[i]
        a2 = -(w**2) * x2
        out.append(a2)
    return np.asarray(out, dtype=np.complex128)


def power_law_force_spectrum(freqs_hz: np.ndarray, amp: float, fc: float) -> np.ndarray:
    """Simple positive real forcing spectrum magnitude model."""
    mag = amp / np.sqrt(1.0 + (freqs_hz / fc) ** 2)
    return mag.astype(np.complex128)
