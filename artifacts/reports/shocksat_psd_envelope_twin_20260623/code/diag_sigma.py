#!/usr/bin/env python3
"""Robustness diagnostics for the probe's negative: is the wide band a real shape-error ceiling or a
sigma-estimation artifact? Characterize the cross-channel scatter on OBSERVED channels three ways
(all misalignment-free, calibrated model): (a) all matched peak heights, (b) the DOMINANT peak per channel,
(c) the band-GRMS per channel — and report what sigma the twin would NEED to beat FEM+6 dB, plus whether
FEM+6 dB itself envelopes the data."""
from __future__ import annotations
import sys, json
from types import SimpleNamespace
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks
sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf, modal_feature as mf, psd_forward as pf, psd_envelope as pe
from modal_multiref import MODAL_REFS, CACHE, N_MODAL
import multiref_frf as mr

ZSTRUCT = 0.01
def zeta_eff(f):
    tau = -(N_MODAL - 1) / (rf.FS * np.log(mr.PROC["exp_end"])); return ZSTRUCT + 1.0 / (2 * np.pi * f * tau)
def robust_sigma(x):
    return float(1.4826 * np.median(np.abs(x - np.median(x))))

R = rf.load_reduced()
caches = {k: dict(np.load(CACHE / f"{k}.npz", allow_pickle=True)) for k in MODAL_REFS}
for k in caches:
    caches[k]["daq"] = [int(d) for d in caches[k]["daq"]]
freqs = caches["m_xpos_990x"]["freqs"]; eta = zeta_eff(freqs); df = float(freqs[1] - freqs[0])
ch = rf.build_channels(R, [d for d in range(1, 116) if d not in rf.BAD_DAQ])
common = set(ch.daq)
for c in caches.values():
    common &= set(c["daq"])
daqs = [d for d in ch.daq if d in common]; pos = {d: i for i, d in enumerate(ch.daq)}
obs = sorted(daqs)  # use ALL common as the calibration population for this diagnostic

pooled = {}
for k, c in caches.items():
    md = {"freqs": freqs, "H": c["H1"], "daq": c["daq"],
          "dyn_range": np.array([np.abs(c["H1"][i]).max() ** 2 / (np.percentile(np.abs(c["H1"][i]) ** 2, 25) + 1e-300)
                                 for i in range(len(c["daq"]))])}
    fq, _ = mf.extract_measured_modes(md, SimpleNamespace(daq=obs))
    for j, hz in mf.match(R, fq)[0]:
        pooled.setdefault(int(j), []).append(float(hz))
oi = sorted(pooled); ow = np.array([np.median(pooled[j]) for j in oi])
tp, _, dg = mf.calibrate_modal(R, np.array(oi), ow, seed=7, warmup=600, samples=600, chains=4)
thmed = np.median(tp, axis=0)[None, :]
tol = max(1, int(round(5.0 / df)))

def mH(k, d):
    c = caches[k]; return c["H1"][c["daq"].index(d)]
def fH(k, d):
    return pf.forward_H_batch(R, freqs, thmed, pf.drive_row_for(R, tuple(float(x) for x in caches[k]["xyz"]),
                              str(caches[k]["axis"])), ch.rows[pos[d]][None, :], eta)[0, :, 0]

allpk, dompk, grmsr = [], [], []
for k in caches:
    for d in obs:
        m = np.abs(mH(k, d)); f = np.abs(fH(k, d))
        lm, lf = np.log(m + 1e-300), np.log(f + 1e-300)
        pk, _ = find_peaks(lm, prominence=0.3, distance=tol)
        for i in pk:
            lo, hi = max(0, i - tol), min(len(freqs), i + tol + 1)
            allpk.append(lm[i] - np.max(lf[lo:hi]))
        if len(pk):
            i = pk[np.argmax(lm[pk])]; lo, hi = max(0, i - tol), min(len(freqs), i + tol + 1)
            dompk.append(lm[i] - np.max(lf[lo:hi]))
        grmsr.append(np.log(pe.grms(freqs, m ** 2) + 1e-300) - np.log(pe.grms(freqs, f ** 2) + 1e-300))
allpk, dompk, grmsr = map(np.array, (allpk, dompk, grmsr))

def rep(name, x):
    g = float(np.median(x))
    print(f"  {name:16s} n={len(x):4d}  gain(med) {g:+.2f}  std {np.std(x - g):.2f}  robustMAD {robust_sigma(x):.2f}  "
          f"p10/p90 {np.percentile(x-g,10):+.2f}/{np.percentile(x-g,90):+.2f}")

print(f"calib converged={dg['converged']} (modes {len(oi)})")
print("cross-channel log-amplitude scatter (calibrated model, misalignment-tolerant):")
rep("all peaks", allpk); rep("dominant peak", dompk); rep("band-GRMS", grmsr)
sig_star = np.log(2.0) / 1.96
print(f"\nsigma needed for twin 97.5 env to beat FEM+6dB (amplitude): ~{sig_star:.2f}  "
      f"(=> PSD band +{10*np.log10(np.exp(2*1.96*sig_star)):.1f} dB == +6 dB)")
print("verdict-relevant: is ANY scatter measure below ~0.35? "
      f"{'YES' if min(np.std(allpk-np.median(allpk)), np.std(dompk-np.median(dompk)), np.std(grmsr-np.median(grmsr))) < 0.35 else 'NO'}")
# does FEM+6dB envelope the data on observed channels (sanity on the bar)?
fem6_cov = []
for k in caches:
    for d in obs:
        f = np.abs(fH(k, d)) * np.exp(np.median(allpk)); m = np.abs(mH(k, d))
        e6 = pe.smoothline_envelope(freqs, pe.add_db_psd(f ** 2, 6.0))
        fem6_cov.append(pe.exceedance(freqs, m ** 2, e6)["exceeding_energy_fraction"])
print(f"FEM+6dB exceeding-energy fraction (observed chans): median {np.median(fem6_cov):.3f}, "
      f"frac of channels with >2% exceed {np.mean(np.array(fem6_cov)>0.02):.2f}")
