#!/usr/bin/env python3
"""wide_forward — window-matched FRF forward for the WIDE band (45 Hz -> certified ceiling).

Reuses the resolution run's wforward READ-ONLY: the exact measurement-window operator _windowed_H is
band-agnostic (takes mode freqs, zetas, target bins); only the modal support and the zeta table extension
are new here. Damping convention (card §6, ledger A2): survey per-mode zeta by frequency interpolation
inside the survey range; modes ABOVE the survey top (257.6 Hz) get the survey BAND MEDIAN zeta. ERA is a
cross-check only. NO free damping or amplitude fitting anywhere.
"""
from __future__ import annotations
import os, sys
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.abspath(os.path.join(WS, "..", "shocksat_resolution_consistent_scoring_20260713",
                                                "code")))
import wforward as WF                              # noqa: E402  (read-only reuse; brings femdamp/femlib)

G_IN_S2 = WF.G_IN_S2
F_SUPPORT = (35.0, 1650.0)                         # modal-sum support: every basis mode participates


def zeta_table(fi):
    """Per-mode viscous zeta for wide-band modes (fixed measured data; zero free parameters)."""
    fs_, zs_ = WF.survey_table()
    fi = np.asarray(fi, float)
    z = np.interp(fi, fs_, zs_)                    # end-clamped inside/below the survey range
    z[fi > fs_[-1]] = float(np.median(zs_))        # unmeasured above survey top -> band median (A2)
    return z


def modal_quantities(pkg, theta, dkey):
    f, Q = pkg.modes(theta)
    inb = np.where((f >= F_SUPPORT[0]) & (f <= F_SUPPORT[1]))[0]
    Us = np.asarray(pkg.sens_rows) @ Q[:, inb]
    Ud = np.asarray(pkg.drives[dkey]) @ Q[:, inb]
    return Us * Ud[None, :], f[inb]


def predict_H(pkg, theta, dkey, fc, windowed=True, flat_zeta=None):
    """Complex accelerance H (n_sens, n_freq) in g/lbf BEFORE global gain, at cache bins fc.
    flat_zeta: if set (e.g. 0.01 for the A0 convention), overrides the survey table."""
    residues, fi = modal_quantities(pkg, theta, dkey)
    zi = np.full(len(fi), float(flat_zeta)) if flat_zeta is not None else zeta_table(fi)
    if not windowed:
        wi = 2 * np.pi * fi
        return WF.D.frf_from_modes(residues, wi, zi, np.zeros(len(fi)), np.asarray(fc, float)) / G_IN_S2
    return WF._windowed_H(residues, fi, zi, np.asarray(fc, float)) / G_IN_S2


def predict_logH(pkg, theta, dkey, fc, windowed=True, flat_zeta=None):
    return np.log10(np.abs(predict_H(pkg, theta, dkey, fc, windowed, flat_zeta)) + 1e-300)
