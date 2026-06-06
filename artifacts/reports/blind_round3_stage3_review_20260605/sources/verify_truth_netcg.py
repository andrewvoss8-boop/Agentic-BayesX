#!/usr/bin/env python3
"""Independently verify the SEALED truth netCG is the canonical dynamic FBS (resonant), not the
forbidden frequency-flat rigid 0.28 constant, and check its f->0 rigid limit + resonant amplification.
Also confirm the inference fits the UNCHANGED apparent-mass data (netCG family != AM data)."""
import numpy as np
from pathlib import Path
SEALED = Path("runs/round3/codex_truth/sealed_truth")
sk = np.load(SEALED / "scoring_key.npz")
f = sk["frequency_hz"]
# z DOF = index 2 (dof order x,y,z,rx,ry,rz)
MSz = sk["clean_source_apparent_mass_real"][:, 2, :] + 1j*sk["clean_source_apparent_mass_imag"][:, 2, :]
MLz = sk["clean_load_apparent_mass_real"][:, 2, :] + 1j*sk["clean_load_apparent_mass_imag"][:, 2, :]
# FBS transmission ratio T(f) = |M_L/(M_S+M_L)|
T = np.abs(MLz/(MSz+MLz))   # (8, nf)
# low-f rigid limit (use lowest freq bin)
ilo = np.argmin(f)
print("freq min/max:", f.min(), f.max(), "nf", len(f))
print("truth m_source(z) low-f =", np.median(MSz[:, ilo].real), " m_load low-f =", np.median(MLz[:, ilo].real))
rigid = T[:, ilo]
print("truth f->0 transmission ratio (per build):", np.round(rigid, 4))
print("  -> rigid limit median = %.4f (canonical f->0 = m_load/(m_src+m_load))" % np.median(rigid))
# resonant amplification: peak transmission / rigid limit
peakT = T.max(axis=1)
peakf = f[T.argmax(axis=1)]
amp = peakT/rigid
print("truth peak transmission freq (per build) Hz:", np.round(peakf, 1))
print("resonant amplification peakT/rigid: min %.2f median %.2f max %.2f" %
      (amp.min(), np.median(amp), amp.max()))
print("=> netCG transfer is RESONANT (not flat) if amplification >> 1")

# Confirm published observed netCG == clean netCG (sensor noise negligible) -> scoring target consistent
obs = np.load("runs/round3/codex_truth/dataset/observations.npz", allow_pickle=True)
pub = obs["netcg_3grms_g"]; cln = sk["clean_netcg_3grms_g"]
print("\npublished vs clean netCG max abs delta:", np.abs(pub-cln).max(), " (sensor noise on QOI)")
# Confirm the AM data (what inference fits) is present & finite, independent of netCG family
am = obs["apparent_mass_real"]
print("apparent_mass_real shape", am.shape, "finite:", np.isfinite(am).all())
