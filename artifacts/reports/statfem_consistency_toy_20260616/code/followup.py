#!/usr/bin/env python3
"""Follow-up E1 -- a SECOND model-form-error class that is NOT theta-like: a spatially-localized
stiffness defect. The main study's Winkler foundation acted theta-like across the drive band, so all
three constructions absorbed it into a biased theta and looked the same. A LOCAL stiffness loss
EA(x)=theta_true*(1 - depth*1[a<=x<=b]) cannot be represented by a global theta OR by a smooth additive
constant -- it is exactly the spatially-structured discrepancy that statFEM's additive spatial GP term is
DESIGNED to absorb, but physics-in-likelihood (M-lik) and physics-in-prior (M-ift) have no such term.
This presses on the DIFFERENCE between the discrepancy mechanisms.

Truth is a HIGH-RESOLUTION reference forced-response solve (variable-EA FE, n_el=512) -- NOT analytic
(labelled as such). The three inference models are UNCHANGED (uniform-EA, defect omitted = the model-form
error). Reuses core / nuts_marg / statfem; no edits to those modules."""
from __future__ import annotations

import numpy as np

import core

DEFECT_A, DEFECT_B = 0.4, 0.6        # localized stiffness-loss region (middle fifth of the rod)
REF_NEL = 512                         # high-resolution reference mesh for the (non-analytic) truth


def EA_defect(depth):
    """True axial rigidity: global scale theta_true with a local fractional loss of size `depth`."""
    def EA(x):
        x = np.asarray(x, dtype=float)
        return core.THETA_TRUE * (1.0 - depth * ((x >= DEFECT_A) & (x <= DEFECT_B)))
    return EA


def fe_assemble_varEA(n_el, EA_of_x):
    """Consistent-mass axial-bar FE with element-wise EA (variable coefficient). Fixed-free."""
    Le = core.L / n_el
    nn = n_el + 1
    K = np.zeros((nn, nn)); M = np.zeros((nn, nn))
    me = (core.RHOA * Le / 6.0) * np.array([[2.0, 1.0], [1.0, 2.0]])
    for e in range(n_el):
        x_mid = (e + 0.5) * Le
        EA_e = float(EA_of_x(x_mid))
        ke = (EA_e / Le) * np.array([[1.0, -1.0], [-1.0, 1.0]])
        idx = [e, e + 1]
        K[np.ix_(idx, idx)] += ke
        M[np.ix_(idx, idx)] += me
    free = np.arange(1, nn)
    x_nodes = np.arange(nn) * Le
    return K[np.ix_(free, free)], M[np.ix_(free, free)], x_nodes[1:]


def fe_response_varEA(n_el, EA_of_x, omega, sensors=core.SENSORS):
    """Forced drive-point response at sensors for a variable-EA rod (uniform unit load)."""
    K, M, x_nodes = fe_assemble_varEA(n_el, EA_of_x)
    b = core.fe_assemble_load(n_el)
    u = np.linalg.solve(K - omega ** 2 * M, b)
    xn = np.concatenate(([0.0], x_nodes)); uf = np.concatenate(([0.0], u))
    return np.interp(sensors, xn, uf)


def make_data_defect(depth, n_rep=1, seed=20260616):
    """Data for the localized-defect truth (high-resolution reference solve), same observable/noise model
    as core.make_data. depth=0 => uniform theta_true rod (no error control)."""
    rng = np.random.default_rng(seed + 31 + int(round(depth * 1e6)) + 7919 * n_rep)
    EA = EA_defect(depth)
    nf = len(core.DRIVE_FREQS_FIT)
    u_true = np.column_stack([fe_response_varEA(REF_NEL, EA, w) for w in core.DRIVE_FREQS_FIT])
    sig_u = np.maximum(core.SIGMA_U_REL * np.sqrt(np.mean(u_true ** 2, axis=0)), 1e-6)
    y_u = u_true[None, :, :] + rng.normal(0, 1, (n_rep, len(core.SENSORS), nf)) * sig_u[None, None, :]
    u_held = np.column_stack([fe_response_varEA(REF_NEL, EA, w) for w in core.DRIVE_FREQS_HELDOUT])
    sig_uh = np.maximum(core.SIGMA_U_REL * np.sqrt(np.mean(u_held ** 2, axis=0)), 1e-6)
    return core.Data(drive_fit=core.DRIVE_FREQS_FIT.copy(), drive_held=core.DRIVE_FREQS_HELDOUT.copy(),
                     y_u=y_u, u_true=u_true, sigma_u=sig_u, u_held_true=u_held, sigma_u_held=sig_uh,
                     eps=float(depth), n_rep=int(n_rep))
