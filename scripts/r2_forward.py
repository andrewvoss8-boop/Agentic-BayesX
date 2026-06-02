#!/usr/bin/env python3
"""Differentiable JAX 2DOF forward model for the round-2 sequential vibe/modal/flight run.

Coupled dome(m1)+tray(m2) system, matching the convention in
scripts/fresh_2dof_statfem_fbs.py exactly (verified numerically against the shared
dataset clean curves).

Channels:
  H = accel/force matrix = -w^2 * Z^-1, Z = K + i w C - w^2 M
    K = [[k1+k2, -k2],[-k2, k2]], C = [[c1+c2,-c2],[-c2,c2]], M = diag(m1,m2)
    c1 = 2 zeta1 sqrt(k1 m1), c2 = 2 zeta2 sqrt(k2 m2)
  interface accel/force (g)  = H[0,0]/g0
  tray accel/force-at-1 (g)  = H[1,0]/g0   (tray response to force into dome DOF)
  tray transmissibility       T = mount/(mount - m2 w^2), mount = k2 + i w c2
  dome-only recip inertance   ch1 = z_dome / (-w^2) -> |ch1| = |z_dome|/w^2, z_dome=k1+i w c1 - w^2 m1
  coupled recip inertance     ch2 = 1/H[0,0], ch3 = 1/H[1,1]
"""
from __future__ import annotations

import math
import jax.numpy as jnp

G0 = 9.80665
M1 = 1.0
M2 = 0.6
DOME_NOM_HZ = 110.0
TRAY_NOM_HZ = 75.0
DOME_NOM_ZETA = 0.018
TRAY_NOM_ZETA = 0.026
K1_NOM = M1 * (2.0 * math.pi * DOME_NOM_HZ) ** 2
K2_NOM = M2 * (2.0 * math.pi * TRAY_NOM_HZ) ** 2

# Truth used by the shared dataset generator (fresh_2dof true_params)
TRUE_K1 = (0.85 ** 2) * K1_NOM
TRUE_K2 = (1.15 ** 2) * K2_NOM
TRUE_ZETA1 = 1.25 * DOME_NOM_ZETA   # 0.0225
TRUE_ZETA2 = 0.75 * TRAY_NOM_ZETA   # 0.0195


def _damping(k1, k2, zeta1, zeta2):
    c1 = 2.0 * zeta1 * jnp.sqrt(k1 * M1)
    c2 = 2.0 * zeta2 * jnp.sqrt(k2 * M2)
    return c1, c2


def accel_over_force(k1, k2, zeta1, zeta2, freqs_hz):
    """Return complex H00 (interface) and H10 (tray) accel/force entries (m/s^2 per N)."""
    w = 2.0 * jnp.pi * freqs_hz
    c1, c2 = _damping(k1, k2, zeta1, zeta2)
    # Z entries (complex), vectorized over frequency
    z11 = (k1 + k2) + 1j * w * (c1 + c2) - (w ** 2) * M1
    z12 = -k2 - 1j * w * c2
    z21 = z12
    z22 = k2 + 1j * w * c2 - (w ** 2) * M2
    det = z11 * z22 - z12 * z21
    # inv(Z) = 1/det [[z22,-z12],[-z21,z11]]; H = -w^2 inv(Z)
    H00 = -(w ** 2) * z22 / det
    H10 = -(w ** 2) * (-z21) / det
    return H00, H10


def interface_accel_per_force_g(k1, k2, zeta1, zeta2, freqs_hz):
    H00, _ = accel_over_force(k1, k2, zeta1, zeta2, freqs_hz)
    return H00 / G0


def tray_accel_per_force_g(k1, k2, zeta1, zeta2, freqs_hz):
    _, H10 = accel_over_force(k1, k2, zeta1, zeta2, freqs_hz)
    return H10 / G0


def tray_transmissibility(k2, zeta2, freqs_hz):
    w = 2.0 * jnp.pi * freqs_hz
    c2 = 2.0 * zeta2 * jnp.sqrt(k2 * M2)
    mount = k2 + 1j * w * c2
    return mount / (mount - M2 * (w ** 2))


def dome_only_recip_inertance(k1, zeta1, freqs_hz):
    w = 2.0 * jnp.pi * freqs_hz
    c1 = 2.0 * zeta1 * jnp.sqrt(k1 * M1)
    z = k1 + 1j * w * c1 - (w ** 2) * M1
    a_over_f = -(w ** 2) / z
    return 1.0 / a_over_f


def coupled_interface_recip(k1, k2, zeta1, zeta2, freqs_hz):
    H00, _ = accel_over_force(k1, k2, zeta1, zeta2, freqs_hz)
    return 1.0 / H00


def coupled_tray_recip(k1, k2, zeta1, zeta2, freqs_hz):
    w = 2.0 * jnp.pi * freqs_hz
    c1, c2 = _damping(k1, k2, zeta1, zeta2)
    z11 = (k1 + k2) + 1j * w * (c1 + c2) - (w ** 2) * M1
    z12 = -k2 - 1j * w * c2
    z22 = k2 + 1j * w * c2 - (w ** 2) * M2
    det = z11 * z22 - z12 * z12
    H11 = -(w ** 2) * z11 / det
    return 1.0 / H11
