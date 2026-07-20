#!/usr/bin/env python3
"""EXPLORATORY: multi-output ERA (Eigensystem Realization Algorithm) modal ID from the Test07 +X free-decay,
to get clean per-mode damping (incl. the low modes log-decrement inflated) + re-identified frequencies. Uses
the hammer free-decay as the impulse response (Markov parameters). Stabilization across model orders keeps
physical poles. Saves scratch_test07/era_result.npz (matched per-survey-mode zeta + 4-band zeta) for the
fixed-damping re-score. One drive, hit 001."""
import os, glob
import numpy as np
import scipy.io as sio
from scipy import signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
MAT = glob.glob(os.path.join(HERE, "*001_*.mat"))[0]
mm = np.load(os.path.join(ROOT, "artifacts/reports/shocksat_fem_remesh_20260618/measured_modes.npz"))
mfreq = np.asarray(mm["freqs"], float); mdamp = np.asarray(mm["damp"], float) / 100.0
EDGES = np.array([45.0, 69.8, 108.2, 167.7, 260.0])
FMIN, FMAX = 45.0, 260.0

print("loading", os.path.basename(MAT), "...", flush=True)
m = sio.loadmat(MAT, squeeze_me=True, struct_as_record=False)


def chan(i):
    r = m[f"Recorder{i}"]; ci = r.Channels.ChannelInfos.ChannelInfo; d = r.Channels.Segments.Data
    fs = 1.0 / float(np.atleast_1d(d.dXstep).ravel()[0])
    return str(ci.Name), str(ci.YUnits), fs, np.asarray(d.Samples, float).ravel()


# collect accel channels + find impact
FS = None; accel = {}
for i in range(1, 129):
    if f"Recorder{i}" not in m:
        continue
    name, yu, fs, x = chan(i)
    if yu.strip().lower() == "g":
        FS = fs; accel[i] = x
top = [i for _, i in sorted(((np.var(x), i) for i, x in accel.items()), reverse=True)[:16]]
imp = int(np.argmax(np.abs(accel[top[0]])))
print(f"fs={FS:.0f} Hz, impact at {imp/FS*1000:.1f} ms, using {len(top)} channels", flush=True)

# band-limit to 45-260 Hz and decimate to ~1500 Hz (>2x 260), take the free-decay after impact
q = int(FS // 1500); fs_d = FS / q
sos_bp = signal.butter(6, [FMIN / (fs_d / 2), FMAX / (fs_d / 2)], btype="band", output="sos")
Y = []
for i in top:
    xd = signal.decimate(accel[i][imp:], q, ftype="fir", zero_phase=True)
    Y.append(signal.sosfiltfilt(sos_bp, xd))
L = min(len(y) for y in Y)
Ldec = int(0.35 * fs_d)                       # ~0.35 s of clean decay
Y = np.array([y[:min(L, Ldec)] for y in Y])   # (m, L)
mch, L = Y.shape
print(f"decimated fs_d={fs_d:.1f} Hz, decay length {L} samples ({L/fs_d*1000:.0f} ms)", flush=True)


def era(Y, fs, alpha, order):
    """multi-output ERA. Y: (m, L) impulse response. Returns (freqs, zetas, mode-shape columns)."""
    m, L = Y.shape
    beta = L - alpha - 1
    # block Hankel H0 (alpha*m x beta), H1 shifted by one sample
    H0 = np.empty((alpha * m, beta)); H1 = np.empty((alpha * m, beta))
    for a in range(alpha):
        H0[a * m:(a + 1) * m, :] = Y[:, a:a + beta]
        H1[a * m:(a + 1) * m, :] = Y[:, a + 1:a + 1 + beta]
    U, S, Vt = np.linalg.svd(H0, full_matrices=False)
    n = order
    Un, Sn, Vn = U[:, :n], S[:n], Vt[:n, :]
    S12 = np.diag(1.0 / np.sqrt(Sn))
    A = S12 @ Un.T @ H1 @ Vn.T @ S12
    C = (Un @ np.diag(np.sqrt(Sn)))[:m, :]     # output matrix (mode shapes at channels)
    mu, Phi = np.linalg.eig(A)
    s = np.log(mu.astype(complex)) * fs        # continuous poles
    fr = np.abs(s) / (2 * np.pi)
    ze = -np.real(s) / (np.abs(s) + 1e-30)
    shapes = C @ Phi
    return fr, ze, shapes


# stabilization across model orders: a pole is physical if freq stable (<0.5%) & damping stable (<20%)
alpha = 180
orders = [60, 80, 100, 120, 140]
polelist = []
for od in orders:
    fr, ze, sh = era(Y, fs_d, alpha, od)
    keep = (fr > FMIN) & (fr < FMAX) & (ze > 1e-4) & (ze < 0.10) & (np.imag(np.log(1)) == 0)
    for k in np.where(keep)[0]:
        polelist.append((od, float(fr[k]), float(ze[k])))
# reference order (highest) poles, validated against the next-lower order
ref = [(f, z) for od, f, z in polelist if od == orders[-1]]
prev = [(f, z) for od, f, z in polelist if od == orders[-2]]
stable = []
for f, z in ref:
    near = [(pf, pz) for pf, pz in prev if abs(pf - f) / f < 0.005 and abs(pz - z) / (z + 1e-9) < 0.25]
    if near:
        stable.append((f, z))
# dedupe (complex-conjugate pairs -> same |f|); cluster within 0.4 Hz
stable = sorted(stable)
clustered = []
for f, z in stable:
    if clustered and abs(f - clustered[-1][0]) < 0.4:
        continue
    clustered.append((f, z))
idf = np.array([f for f, _ in clustered]); idz = np.array([z for _, z in clustered])
print(f"\nERA stable physical modes in band: {len(idf)}")

# match to survey by nearest frequency (<3%)
print("\nmode  f_survey  zeta_survey  f_ERA    zeta_ERA   df%")
matched = []
for k, fn in enumerate(mfreq):
    j = int(np.argmin(np.abs(idf - fn))) if len(idf) else -1
    if j >= 0 and abs(idf[j] - fn) / fn < 0.03:
        matched.append((fn, mdamp[k], idf[j], idz[j]))
        print(f"{k:3d} {fn:8.1f}   {mdamp[k]*100:6.3f}%   {idf[j]:7.2f}  {idz[j]*100:6.3f}%   "
              f"{(idf[j]/fn-1)*100:+5.2f}")
    else:
        print(f"{k:3d} {fn:8.1f}   {mdamp[k]*100:6.3f}%    (no ERA match within 3%)")

M = np.array([(a, b, c, d) for a, b, c, d in matched])
zsurv, zera = M[:, 1], M[:, 3]
print(f"\nSUMMARY: matched {len(M)}/{len(mfreq)} survey modes")
print(f"  survey zeta median {np.median(zsurv)*100:.3f}%  |  ERA zeta median {np.median(zera)*100:.3f}%")
print(f"  (vs the 2 Hz FRF-fit that railed to the 5% physical-gate ceiling)")

# 4-band zeta from ERA-matched modes (for the fixed-damping re-score); fall back to band-median survey
band_zeta = []
for b in range(len(EDGES) - 1):
    inb = (M[:, 2] >= EDGES[b]) & (M[:, 2] < EDGES[b + 1])
    band_zeta.append(float(np.median(zera[inb])) if inb.any() else float(np.median(zera)))
print("\n4-band ERA zeta (D8 edges):", [round(z * 100, 3) for z in band_zeta], "%")
# per-survey-mode zeta table (ERA where matched, else survey)
per_mode = np.array([dict(zip(mfreq, [np.nan] * len(mfreq)))[f] if False else np.nan for f in mfreq])
zmap = {round(a, 1): d for a, b, c, d in matched}
per_mode = np.array([zmap.get(round(f, 1), mdamp[k]) for k, f in enumerate(mfreq)])
np.savez(os.path.join(HERE, "era_result.npz"),
         id_freq=idf, id_zeta=idz, matched=M, band_edges=EDGES,
         band_zeta=np.array(band_zeta), survey_freq=mfreq, per_mode_zeta=per_mode)
print("saved era_result.npz")
