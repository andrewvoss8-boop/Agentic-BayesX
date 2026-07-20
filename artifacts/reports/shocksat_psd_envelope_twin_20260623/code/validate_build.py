#!/usr/bin/env python3
"""Unit-validate the NEW building blocks before wiring the probe (validity-before-rigor).
  (1) psd_forward complex H matches realfrf.fem_logmag |H| (same eigh-resolvent) to ~1e-12.
  (2) per-reference vs combined-coherent PSD shapes are sane (combined != sum of magnitudes).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import psd_forward as pf

R = rf.load_reduced()
ch = rf.build_channels(R, list(range(1, rf.N_ACCEL_RECORDERS + 1)))
freqs = np.linspace(45.0, 260.0, 200)
theta = np.ones(9)
zeta = rf.ZETA_NOM; eta = 2.0 * zeta
resp = ch.rows[:6]; drive = ch.drive_row

# (1) complex forward |H| == exp(realfrf.fem_logmag)
lm = rf.fem_logmag(R, freqs, theta, resp, drive, zeta=zeta)        # log(|H|/G)
H = pf.forward_H_single(R, freqs, theta, drive, resp, eta)         # complex H/G
d = np.max(np.abs(np.log(np.abs(H)) - lm))
print(f"(1) complex-forward vs realfrf log|H| max abs diff = {d:.2e}  ({'PASS' if d < 1e-9 else 'FAIL'})")

# (2) coherent combine differs from incoherent magnitude-sum (sanity)
dr_x = pf.drive_row_for(R, (9.0, 7.6, 0.6), "X")
dr_z = pf.drive_row_for(R, (9.0, 7.8, 0.0), "Z")
dr_xy = pf.drive_row_for(R, (9.0, 9.0, 1.1), "XY")
Hx = pf.forward_H_single(R, freqs, theta, dr_x, resp, eta)
Hz = pf.forward_H_single(R, freqs, theta, dr_z, resp, eta)
Hcomb = pf.combined_H([Hx, Hz])
psd_x = pf.psd_from_H(Hx); psd_comb = pf.psd_from_H(Hcomb)
incoh = pf.psd_from_H(Hx) + pf.psd_from_H(Hz)
print(f"(2) per-ref +X PSD median {np.median(psd_x):.3e}; coherent-combined median {np.median(psd_comb):.3e}; "
      f"incoherent-sum median {np.median(incoh):.3e}")
print(f"    coherent != incoherent (interference present): "
      f"{'YES' if np.max(np.abs(psd_comb - incoh))/np.median(incoh) > 0.1 else 'no'}")
print(f"    +XY drive row finite & nonzero: {np.all(np.isfinite(dr_xy)) and np.linalg.norm(dr_xy) > 0}")
print("psd_forward validation done")
