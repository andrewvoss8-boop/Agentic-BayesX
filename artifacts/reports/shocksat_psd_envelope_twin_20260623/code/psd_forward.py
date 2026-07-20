#!/usr/bin/env python3
"""Complex matched-path forward for the PSD-envelope twin (NEW; D6).

realfrf.fem_logmag returns log|H| (magnitude) — fine for the per-reference PSD |H|², but the COMBINED
uniform-correlated input needs the COMPLEX H to sum coherently across drives before squaring. This module
replicates realfrf's EXACT eigh-resolvent accelerance but returns complex H (g/lbf); validated to match
realfrf.fem_logmag's |H| to ~1e-12 (see validate_build.py). Reused files are untouched.

  H_{s,d}(w) = -w² Σ_k U_s[k] U_d[k] / ((1+i·eta)·lam_k - w²) / G_IN_S2     (eta = 2 zeta)
Per-reference PSD: S = |H_d|²·S_F0.  Combined-correlated PSD: S = |Σ_d H_d|²·S_F0  (coherent complex sum).
"""
from __future__ import annotations
import numpy as np
import realfrf as rf

G_IN_S2 = rf.G_IN_S2


def drive_row_for(R, xyz, axis):
    """Reduced drive row for a point+axis. 'XY' = unit diagonal (X-row + Y-row)/sqrt(2) (D6, documented)."""
    if axis == "XY":
        rx, *_ = R.reduced_row(xyz, "X"); ry, *_ = R.reduced_row(xyz, "Y")
        return (rx + ry) / np.sqrt(2.0)
    row, *_ = R.reduced_row(xyz, axis)
    return row


def forward_H_batch(R, freqs, theta_batch, drive_row, resp_rows, eta, chunk=200):
    """Complex accelerance H (g/lbf): theta_batch (M,9) -> (M, Nf, Ns). Same math as realfrf.fem_logmag_batch
    but complex (no abs). drive_row (74,); resp_rows (Ns,74)."""
    theta_batch = np.atleast_2d(np.asarray(theta_batch, float))
    M = theta_batch.shape[0]
    w = 2 * np.pi * np.asarray(freqs, float)
    Nf, Ns = len(freqs), resp_rows.shape[0]
    eta = np.asarray(eta, float)
    eta_b = eta.reshape(1, -1, 1) if eta.ndim == 1 else eta        # scalar OR per-frequency (Nf,)
    out = np.empty((M, Nf, Ns), complex)
    for s0 in range(0, M, chunk):
        th = theta_batch[s0:s0 + chunk]
        K = R.A_fix[None] + np.einsum("cg,gij->cij", th, R.A)
        lam, Q = np.linalg.eigh(K)
        lam = np.clip(lam, 1e-9, None)
        Us = np.einsum("sm,cmk->csk", resp_rows, Q)              # (c,Ns,r)
        ud = np.einsum("m,cmk->ck", drive_row, Q)               # (c,r)
        g = (1.0 + 1j * eta_b) * lam[:, None, :] - (w ** 2)[None, :, None]
        H = -(w ** 2)[None, :, None] * np.einsum("csk,ck,cfk->cfs",
                                                 Us.astype(complex), ud.astype(complex), 1.0 / g)
        out[s0:s0 + chunk] = H / G_IN_S2
    return out


def forward_H_single(R, freqs, theta, drive_row, resp_rows, eta):
    return forward_H_batch(R, freqs, np.atleast_2d(theta), drive_row, resp_rows, eta)[0]


def psd_from_H(H, s_f0=1.0):
    """Response PSD (g^2/Hz per unit flat force PSD) from complex accelerance H (g/lbf). |H|^2 * S_F0."""
    return (np.abs(H) ** 2) * float(s_f0)


def combined_H(H_list):
    """Coherent (complex) sum of per-drive H's = response to a uniform, fully-correlated, in-phase input
    at all drives simultaneously (D6b)."""
    out = H_list[0].copy()
    for H in H_list[1:]:
        out = out + H
    return out
