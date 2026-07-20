#!/usr/bin/env python3
"""Decisive REFRAME test (integrating the two browser memos): does an INTEGRATED quantity correlate far better
than per-point response? Reuses the SAVED baseline FEM modes (no eigensolve → no contention with running jobs).

Synthesize the +X FEM FRF (FEM shapes Phi + drive participation pd + MEASURED per-mode freq+damping + per-mode
complex scale LSQ-fit to all channels), then compare FEM vs measured on:
  (1) per-point log|H| correlation                                  [baseline ~0.30]
  (2) band-averaged log-energy correlation (Memo A band metric)
  (3) NET response sqrt(sum_s |H_s|^2) correlation (Memo C CG/area-integrated proxy)
  (4) DRIVE-POINT apparent mass |1/H_dp| correlation (Memo C 7004C-native QOI)
  (5) FDAC-style per-band frequency-shift: does allowing a shift recover per-point corr? (Memo A)
  (6) modal-overlap factor MOF(f)=n(f)*2*zeta*f per band -> where to switch to band/energy targets
Output: out/diag_reframe.json + console.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from modal_multiref import CACHE
WS = Path(__file__).resolve().parent.parent

z = np.load(WS / "out" / "edits" / "baseline" / "modes.npz", allow_pickle=True)
Phi = z["Phi"]; pd = z["pd"]; ffem = z["freqs_fem"]; daq = [int(d) for d in z["daq"]]
c = dict(np.load(CACHE / "m_xpos_990x.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
f = c["freqs"]; w = 2 * np.pi * f
ci = {d: c["daq"].index(d) for d in daq}
Hmeas = np.array([c["H1"][ci[d]] for d in daq]).T          # (Nf, Nc) complex measured
mm = np.load(WS / "data" / "measured_modes.npz", allow_pickle=True); mfr = mm["freqs"]; mdp = mm["damp"] / 100.0
# assign measured freq+damping to each FEM matched mode by nearest measured frequency
j = np.array([int(np.argmin(np.abs(mfr - ff))) for ff in ffem]); wr = mfr[j] * 2 * np.pi
N122880 = 122880; tau = -(N122880 - 1) / (250000.0 * np.log(0.05))
eta = 2.0 * (mdp[j] + 1.0 / (2 * np.pi * mfr[j] * tau))
zeta_med = float(np.median(mdp[j] + 1.0 / (2 * np.pi * mfr[j] * tau)))
denom = (1 + 1j * eta)[None, :] * (wr ** 2)[None, :] - (w ** 2)[:, None]
basis = (-(w ** 2)[:, None, None]) * (Phi[None, :, :] * pd[None, None, :]) / denom[:, None, :]  # (Nf,Nc,nm)
A = basis.reshape(-1, len(pd)); b = Hmeas.reshape(-1)
AhA = A.conj().T @ A + 1e-3 * np.eye(len(pd)) * np.real(np.trace(A.conj().T @ A)) / len(pd)
a = np.linalg.solve(AhA, A.conj().T @ b)
Hsyn = basis @ a                                            # (Nf,Nc) FEM synth FRF (best per-mode scales)

def corr(x, y): return float(np.corrcoef(x, y)[0, 1])
lm = np.log(np.abs(Hmeas) + 1e-30); ls = np.log(np.abs(Hsyn) + 1e-30)

# (1) per-point
pp = float(np.median([corr(ls[:, k], lm[:, k]) for k in range(len(daq))]))
# (2) band-averaged log-energy (15 Hz bands)
edges = np.arange(45, 261, 15); bidx = np.clip(np.digitize(f, edges) - 1, 0, len(edges) - 2)
def bandavg(H):
    out = np.zeros((len(edges) - 1, H.shape[1]))
    for bb in range(len(edges) - 1):
        m = bidx == bb
        if m.any(): out[bb] = np.log(np.sqrt(np.mean(np.abs(H[m]) ** 2, 0)) + 1e-30)
    return out
ba = float(np.median([corr(bandavg(Hsyn)[:, k], bandavg(Hmeas)[:, k]) for k in range(len(daq))]))
# (3) net response sqrt(sum|H|^2)
net_s = np.sqrt(np.sum(np.abs(Hsyn) ** 2, 1)); net_m = np.sqrt(np.sum(np.abs(Hmeas) ** 2, 1))
netc = corr(np.log(net_s + 1e-30), np.log(net_m + 1e-30))
# (4) drive-point apparent mass: H_dp = sum pd^2 a (-w^2)/denom ; M=1/|H_dp|; measured = nearest accel to drive
basis_dp = (-(w ** 2)[:, None]) * (pd ** 2)[None, :] / denom
Hdp_s = basis_dp @ a; Mdp_s = 1.0 / (np.abs(Hdp_s) + 1e-30)
drive_xyz = np.array([9.0, 7.6, 0.6])
import csv as _csv
rows = {r["daq_channel"]: r for r in _csv.DictReader(open(WS / "data" / "channel_map.csv")) if r["configuration"] == "tap_impact"}
dist = {d: np.linalg.norm(np.array([float(rows[str(d)]["x_in"]), float(rows[str(d)]["y_in"]), float(rows[str(d)]["z_in"])]) - drive_xyz) for d in daq if str(d) in rows}
dp_daq = min(dist, key=dist.get); Hdp_m = Hmeas[:, daq.index(dp_daq)]; Mdp_m = 1.0 / (np.abs(Hdp_m) + 1e-30)
apparent_mass_corr = corr(np.log(Mdp_s + 1e-30), np.log(Mdp_m + 1e-30))
# (5) FDAC: allow a global freq shift on the FEM synth (warp), best corr per channel
def best_shift_corr(k):
    best = -1
    for sh in range(-6, 7):
        x = np.roll(ls[:, k], sh)
        cc = corr(x, lm[:, k])
        best = max(best, cc)
    return best
fdac = float(np.median([best_shift_corr(k) for k in range(len(daq))]))
# (6) MOF per 50 Hz band
mof = {}
for lo in range(45, 260, 50):
    hi = lo + 50; nb = int(((ffem >= lo) & (ffem < hi)).sum()); fc = lo + 25
    mof[f"{lo}-{hi}"] = round(float((nb / 50.0) * 2 * zeta_med * fc), 2)

rec = {"reference": "+X (Test01)", "n_channels": len(daq), "n_modes": len(pd), "median_zeta": round(zeta_med, 4),
       "per_point_logmag_corr": round(pp, 3), "band_avg_logenergy_corr": round(ba, 3),
       "net_response_corr": round(netc, 3), "drivepoint_apparent_mass_corr": round(apparent_mass_corr, 3),
       "drivepoint_channel": dp_daq, "per_point_corr_with_freq_shift_FDAC": round(fdac, 3),
       "MOF_per_band": mof, "note": "integrated/band quantities vs per-point; reused saved baseline modes (no eigensolve)"}
(WS / "out" / "diag_reframe.json").write_text(json.dumps(rec, indent=2))
print(json.dumps(rec, indent=2))
print(f"\nPER-POINT log|H| corr {pp:.2f}  ->  band-avg {ba:.2f} | NET {netc:.2f} | DRIVE-PT apparent-mass {apparent_mass_corr:.2f}")
print(f"FDAC (freq-shift-allowed) per-point {fdac:.2f}  (gain over {pp:.2f} = {fdac-pp:+.2f}; small => residual is amplitude not freq)")
print(f"MOF per band: {mof}  (>~2.5 => switch to band/energy target)")
