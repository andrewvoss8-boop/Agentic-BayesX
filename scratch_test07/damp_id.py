#!/usr/bin/env python3
"""EXPLORATORY (not a formal study): time-domain modal damping ID from the re-downloaded Test07 +X impact
records. Fits zeta per survey mode by band-pass + Hilbert-envelope log-decrement on the free decay, to test
whether ShockSat's true damping is light (~0.3%, as the survey says) vs the 5% the 2 Hz FRF-fit railed to.
One drive (Test07_990x), hit 001; sanity pass before any re-download of the other drives."""
import os, sys, glob
import numpy as np
import scipy.io as sio
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
MAT = glob.glob(os.path.join(HERE, "*001_*.mat"))[0]
mm = np.load(os.path.join(ROOT, "artifacts/reports/shocksat_fem_remesh_20260618/measured_modes.npz"))
mfreq = np.asarray(mm["freqs"], float)
mdamp = np.asarray(mm["damp"], float) / 100.0        # percent -> ratio (D7)

print("loading", os.path.basename(MAT), "...", flush=True)
m = sio.loadmat(MAT, squeeze_me=True, struct_as_record=False)


def chan(i):
    r = m[f"Recorder{i}"]
    ci = r.Channels.ChannelInfos.ChannelInfo
    d = r.Channels.Segments.Data
    fs = 1.0 / float(np.atleast_1d(d.dXstep).ravel()[0])
    return str(ci.Name), str(ci.YUnits), fs, np.asarray(d.Samples, float).ravel()


# --- units survey (find any force channel) ---
units = {}
for i in range(1, 129):
    if f"Recorder{i}" in m:
        _, yu, _, _ = chan(i)
        units[yu] = units.get(yu, 0) + 1
print("channel units histogram:", units)

# --- pick high-SNR accel channels: those with the largest post-impact energy ---
FS = None
sig_energy = []
raw = {}
for i in range(1, 129):
    if f"Recorder{i}" not in m:
        continue
    name, yu, fs, x = chan(i)
    if yu.strip().lower() != "g":
        continue
    FS = fs
    raw[i] = (name, x)
    sig_energy.append((float(np.var(x)), i))
sig_energy.sort(reverse=True)
top = [i for _, i in sig_energy[:10]]
print(f"fs={FS:.0f} Hz, nsamp={len(next(iter(raw.values()))[1])}, using top-energy channels {top}", flush=True)

# --- decimate to ~2500 Hz for efficient narrowband filtering ---
q = int(FS // 2500)
fs_d = FS / q
print(f"decimate by {q} -> fs_d={fs_d:.1f} Hz")

# impact index from the highest-energy channel (sharp onset)
x0 = raw[top[0]][1]
imp = int(np.argmax(np.abs(x0)))
print(f"impact at sample {imp} ({imp/FS*1000:.1f} ms)")


def zeta_logdec(xb, fs, fn, n_cyc=25):
    """log-decrement zeta from the Hilbert envelope decay of a band-passed signal xb.
    Fits the EARLY, high-SNR decay only (peak -> min(n_cyc periods, env~1/e^2)) so closely-spaced-mode beating
    and the noise-floor tail do not inflate the slope. Also returns a linearity R^2 as a quality flag."""
    env = np.abs(signal.hilbert(xb))
    env /= env.max() + 1e-30
    le = np.log(env + 1e-12)
    n = len(env)
    t = np.arange(n) / fs
    pk = int(np.argmax(env))
    lo = pk + int(0.005 * fs)
    win_cyc = pk + int(n_cyc / fn * fs)                 # n_cyc modal periods after the peak
    below = np.where(env[pk:] < np.exp(-2))[0]          # or where env drops to 1/e^2
    win_env = pk + (below[0] if len(below) else n - pk - 1)
    hi = min(win_cyc, win_env, n - 1)
    if hi - lo < int(0.02 * fs):
        return np.nan, 0.0
    tt, ll = t[lo:hi], le[lo:hi]
    A, cov = np.polyfit(tt, ll, 1, cov=True)
    slope = A[0]                                        # = -zeta*wn
    resid = ll - np.polyval(A, tt)
    r2 = 1.0 - np.var(resid) / (np.var(ll) + 1e-30)
    zeta = -slope / (2 * np.pi * fn)
    return float(zeta), float(r2)


# pre-decimate the top channels once (post-impact only)
xd_top = {i: signal.decimate(raw[i][1][imp:], q, ftype="fir", zero_phase=True) for i in top}
# nearest-neighbor spacing (isolation flag)
nn = np.array([min([abs(fn - o) for o in mfreq if o != fn] + [1e9]) for fn in mfreq])

print("\nmode  f_survey  zeta_survey   zeta_TD(isolated,cleanfit)   n_ch  isolated?")
rows = []
for k, fn in enumerate(mfreq):
    bw = min(2.5, max(1.2, 0.012 * fn))             # tighter +/- band
    lo, hi = (fn - bw) / (fs_d / 2), (fn + bw) / (fs_d / 2)
    if hi >= 1.0:
        continue
    sos = signal.butter(4, [lo, hi], btype="band", output="sos")
    zs = []
    for i in top:
        xb = signal.sosfiltfilt(sos, xd_top[i])
        z, r2 = zeta_logdec(xb, fs_d, fn)
        if np.isfinite(z) and 1e-4 < z < 0.15 and r2 > 0.92:   # keep only clean linear decays
            zs.append(z)
    isolated = nn[k] >= 3.0
    if zs:
        zmed = float(np.median(zs))
        rows.append((fn, mdamp[k], zmed, len(zs), isolated))
        print(f"{k:3d} {fn:8.1f}  {mdamp[k]*100:6.3f}%       {zmed*100:6.3f}%                    "
              f"{len(zs):3d}   {'yes' if isolated else 'NO(overlap)'}")

iso = np.array([(r[1], r[2]) for r in rows if r[4]])
allr = np.array([(r[1], r[2]) for r in rows])
print(f"\nSUMMARY (clean-fit r2>0.92):")
print(f"  ALL modes:       survey median {np.median(allr[:,0])*100:.3f}%  |  time-domain median "
      f"{np.median(allr[:,1])*100:.3f}%  (n={len(allr)})")
if len(iso):
    print(f"  ISOLATED modes:  survey median {np.median(iso[:,0])*100:.3f}%  |  time-domain median "
          f"{np.median(iso[:,1])*100:.3f}%  (n={len(iso)})")
print("  => vs the 2 Hz FRF-fit that railed to the 5% physical-gate ceiling")
