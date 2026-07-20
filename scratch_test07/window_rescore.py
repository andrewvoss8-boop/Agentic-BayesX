#!/usr/bin/env python3
"""EXPLORATORY (a): resolution-consistent re-score. Tests the frame-broadening explanation for why physically-
correct damping (~0.3%) does NOT match the 2 Hz FRFs. The measured FRF was made with a ~0.49 s FFT frame -> a
spectral window ~2 Hz wide, which broadens every resonance regardless of true damping. So we broaden the
PHYSICAL-zeta model FRF with the SAME window (convolve with the analysis-window spectral kernel) and compare:
  naive physical zeta (0.3%)   vs   window-matched physical zeta   vs   A0 (1%),  each against the measured cache.
If window-matching recovers the match (and its effective damping ~1-2%), the frame-broadening explanation is
confirmed. In-sample across the 4 dev drives (a processing diagnostic, not the held-out metric). Read-only."""
import os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
WS = os.path.join(ROOT, "artifacts/reports/shocksat_frf_damping_updating_20260710")
sys.path.insert(0, os.path.join(WS, "code"))
import femdamp as D
import femlib as F
import metrics as MET
import score as SC

era = np.load(os.path.join(HERE, "era_result.npz"))
band_zeta = [float(z) for z in era["band_zeta"]]

# --- measurement analysis window: Hann over the cache frame T = N/fs (N=122880, fs=250 kHz) ---
T = 122880 / 250000.0
fs_sim = 5000.0
w = np.hanning(int(T * fs_sim))
Nfft = 2 ** 18
W = np.abs(np.fft.rfft(w, Nfft)); W /= W.max()
fk = np.fft.rfftfreq(Nfft, 1 / fs_sim)
DF = 0.1
off = np.arange(-6, 6 + DF, DF)
kernel = np.interp(np.abs(off), fk, W); kernel /= kernel.sum()   # ~2 Hz-wide smoothing kernel
print(f"analysis frame T={T:.3f} s -> Hann main-lobe ~{2/T:.1f} Hz; smoothing kernel {len(kernel)} taps")


def eff_zeta(fn):
    """effective (apparent) damping the window imposes at frequency fn: half-power width ~ (2/T)/fn / 2."""
    return (1.5 / T) / (2 * fn)     # ~ window half-power bandwidth / (2 f)


def model_H(pkg, theta, damping, dkey, fgrid, windowed=False):
    H = D.predict_H_damped(pkg, theta, damping, dkey, fgrid)     # (nch, nf) complex, physical units
    if not windowed:
        return H
    Hc = np.empty_like(H)
    for c in range(H.shape[0]):
        Hc[c] = np.convolve(H[c], kernel, mode="same")
    return Hc


def evaluate(cid, damping, windowed):
    pkg = F.Package.load(cid)
    theta = np.asarray(pkg.theta_map()[0], float)
    caches = SC.load_caches()
    fgrid = np.arange(20.0, 290.0, DF)
    p3, frsf = [], []
    for dkey in F.DRIVE_KEYS:
        c = caches[dkey]; fc = c["freqs"]; band = c["band"]
        rows, cols = SC._usable(pkg, c)
        if len(rows) == 0:
            continue
        Hm = model_H(pkg, theta, damping, dkey, fgrid, windowed=windowed)   # on fine grid
        pk = SC._matched_peak_bins(pkg, theta, fc)
        for r, cidx in zip(rows, cols):
            yp = np.log10(np.interp(fc, fgrid, np.abs(Hm[r])) + 1e-300)[band]
            ym = np.log10(np.abs(c["H1"][cidx][band]) + 1e-300)
            cc = MET.frac_corr(yp, ym)
            if not np.isnan(cc):
                p3.append(cc)
            if pk:
                ypk = np.interp(np.asarray(fc)[pk], fgrid, np.abs(Hm[r]))
                gain = np.median(np.abs(c["H1"][cidx][pk]) / (ypk + 1e-300))
                frsf.append(MET.frsf(ypk * gain, np.abs(c["H1"][cidx][pk]))[2])
    return float(np.median(p3)), float(np.median(frsf))


phys = {"kind": "band", "zeta": band_zeta}
print("\n%-34s  %-10s %-14s" % ("model variant", "corr(log|H|)", "|FRSF-1| (amp)"))
for label, cid, dmp, win in [
    ("A0  ζ=1%  (naive)",            "A0_enr", {"kind": "fixed", "zeta": 0.01}, False),
    ("A0  physical ζ~0.3% (naive)",  "A0_enr", phys, False),
    ("A0  physical ζ~0.3% + WINDOW", "A0_enr", phys, True),
    ("A0  physical ζ~0.3% + WINDOW ", "A0_enr", phys, True),  # (repeat guard, ignore)
]:
    if label.endswith(" "):
        continue
    c, a = evaluate(cid, dmp, win)
    print("%-34s  %-10.4f %-14.4f" % (label, c, a))

print("\neffective (window-imposed) apparent damping at a few freqs:")
for fn in (60, 120, 200, 250):
    print(f"  {fn:3d} Hz: window-equivalent zeta ~ {eff_zeta(fn)*100:.2f}%  (physical ~0.3%)")
print("\n=> if 'physical + WINDOW' correlates with the measured FRF like A0's 1% (and >> naive physical),\n"
      "   the 2 Hz peak width is a PROCESSING artifact, not damping — consistent processing lets physical\n"
      "   damping be used correctly.")
