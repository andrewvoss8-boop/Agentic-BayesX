#!/usr/bin/env python3
"""POINT-BY-POINT, FREQUENCY-BY-FREQUENCY FRF residual map (Andrew) to GUIDE remeshing. Isolates the SHAPE error by
using a freq+damping-CORRECTED FEM (measured per-mode freq + measured damping + FEM shapes + ONE global gain, NO
per-channel fit), so r(s,f)=log|H_meas|-log|H_corr| reflects what remeshing must fix (not freq/damping).

Outputs WHERE (per-sensor band-RMS residual mapped on the structure, aggregated by height-region) and WHICH MODES
(cross-channel-RMS residual vs frequency + per-mode freq/amplitude/shape-MAC error), to target the next bottom_box
remesh. Reuses saved baseline modes (+X), no eigensolve. Output: out/residual_map.json + figures/residual_map.png.
"""
from __future__ import annotations
import csv, json, sys
from pathlib import Path
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from modal_multiref import CACHE
WS = Path(__file__).resolve().parent.parent

z = np.load(WS / "out" / "edits" / "baseline" / "modes.npz", allow_pickle=True)
Phi = z["Phi"]; pd = z["pd"]; ffem = z["freqs_fem"]; daq = [int(d) for d in z["daq"]]
c = dict(np.load(CACHE / "m_xpos_990x.npz", allow_pickle=True)); c["daq"] = [int(d) for d in c["daq"]]
f = c["freqs"]; w = 2 * np.pi * f; ci = {d: c["daq"].index(d) for d in daq}
Hmeas = np.array([c["H1"][ci[d]] for d in daq]).T                       # (Nf,Nc)
mm = np.load(WS / "data" / "measured_modes.npz", allow_pickle=True); mfr = mm["freqs"]; mdp = mm["damp"] / 100.0
j = np.array([int(np.argmin(np.abs(mfr - ff))) for ff in ffem]); wr = mfr[j] * 2 * np.pi
tau = -(122880 - 1) / (250000.0 * np.log(0.05)); eta = 2.0 * (mdp[j] + 1.0 / (2 * np.pi * mfr[j] * tau))
den = (1 + 1j * eta)[None, :] * (wr ** 2)[None, :] - (w ** 2)[:, None]
Hraw = (-(w ** 2)[:, None, None]) * (Phi[None, :, :] * pd[None, None, :]) / den[:, None, :]   # (Nf,Nc,nm)
Hraw = Hraw.sum(2)                                                      # FEM physics synth (no per-ch fit)
g = np.median(np.log(np.abs(Hmeas) + 1e-30) - np.log(np.abs(Hraw) + 1e-30))
Hcorr = Hraw * np.exp(g)
r = np.log(np.abs(Hmeas) + 1e-30) - np.log(np.abs(Hcorr) + 1e-30)       # (Nf,Nc) shape-error residual (nat log)

# sensor coords + region (channel_map)
rows = {int(rr["daq_channel"]): rr for rr in csv.DictReader(open(WS / "data" / "channel_map.csv"))
        if rr["configuration"] == "tap_impact"}
xyz = np.array([[float(rows[d]["x_in"]), float(rows[d]["y_in"]), float(rows[d]["z_in"])] for d in daq])
desc = [rows[d]["description"] for d in daq]
rms_s = np.sqrt(np.mean(r ** 2, 0))                                     # per-sensor band-RMS residual
bias_s = np.median(r, 0)                                                # per-sensor signed bias (test-FEM)
rms_f = np.sqrt(np.mean(r ** 2, 1))                                     # per-frequency cross-channel RMS residual

# region by Z-height bins (the column axis)
zc = xyz[:, 2]; zb = [(zc < 12.4), (zc >= 12.4) & (zc < 18.4), (zc >= 18.4) & (zc < 24.4), (zc >= 24.4)]
zlab = ["Z<12.4 (lower/bottom_box)", "12.4-18.4", "18.4-24.4", "Z>=24.4 (upper/top_box)"]
region = {zlab[i]: round(float(np.sqrt(np.mean(r[:, m] ** 2))), 3) for i, m in enumerate(zb) if m.any()}

# per-mode error (matched): freq err already 0 (we used measured); report amplitude + shape MAC vs measured at peak
permode = []
for m in range(len(ffem)):
    fi = int(np.argmin(np.abs(f - mfr[j][m])))
    fem_pat = np.abs(Hcorr[fi]); tst_pat = np.abs(Hmeas[fi])
    mac = float((fem_pat @ tst_pat) ** 2 / ((fem_pat @ fem_pat) * (tst_pat @ tst_pat) + 1e-30))
    amp_db = float(20 * np.log10((tst_pat.max() + 1e-30) / (fem_pat.max() + 1e-30)))
    permode.append({"f_hz": round(float(mfr[j][m]), 1), "shape_MAC": round(mac, 2), "peak_amp_err_dB": round(amp_db, 1),
                    "band_resid_rms": round(float(np.sqrt(np.mean(r[max(0,fi-3):fi+4] ** 2))), 2)})
permode = sorted(permode, key=lambda d: -d["band_resid_rms"])

rec = {"reference": "+X", "n_channels": len(daq), "overall_resid_rms": round(float(np.sqrt(np.mean(r ** 2))), 3),
       "residual_by_height_region": region,
       "worst_sensors": [{"daq": daq[i], "rms": round(float(rms_s[i]), 2), "bias_dB": round(float(bias_s[i]*20/np.log(10)), 1),
                          "z_in": round(float(zc[i]), 1), "desc": desc[i][:32]} for i in np.argsort(-rms_s)[:8]],
       "worst_modes": permode[:8],
       "guide": "target the height-region + modes with the largest shape residual (freq+damping already corrected)"}
(WS / "out" / "residual_map.json").write_text(json.dumps(rec, indent=2))
print(json.dumps(rec, indent=2))

fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.4))
sc = ax[0].scatter(xyz[:, 1], zc, c=rms_s, cmap="viridis", s=40)
ax[0].set_xlabel("y (in)", fontsize=9); ax[0].set_ylabel("z = column height (in)", fontsize=9)
ax[0].set_title("WHERE: per-sensor band-RMS log|H| residual (shape error)", fontsize=9)
for i in np.argsort(-rms_s)[:5]:
    ax[0].annotate(f"ch{daq[i]}", (xyz[i,1], zc[i]), fontsize=6.5)
fig.colorbar(sc, ax=ax[0], label="RMS |log|H| residual|")
ax[0].spines[["top","right"]].set_visible(False)
ax[1].plot(f, rms_f, color="#222222", lw=1.2)
for ff in mfr[j]:
    ax[1].axvline(ff, color="0.8", lw=0.5)
ax[1].set_xscale("log"); ax[1].set_xlim(45, 260); ax[1].set_xlabel("frequency (Hz, log)", fontsize=9)
ax[1].set_ylabel("cross-channel RMS residual", fontsize=9)
ax[1].set_title("WHICH MODES: residual vs frequency (gray = FEM modes)", fontsize=9)
ax[1].spines[["top","right"]].set_visible(False)
cap = ("FRF mismatch map, +X. Residual = log|H_measured| - log|H_FEM| with FEM freq+damping ALREADY corrected "
       "(measured per-mode freq+ζ, FEM shapes, one global gain) → this is the SHAPE error remeshing must fix. "
       f"Overall RMS {rec['overall_resid_rms']}. Left: where (sensor position, column height z); right: which modes.")
fig.text(0.01, -0.02, cap, fontsize=7, wrap=True, va="top")
fig.tight_layout(rect=[0, 0.05, 1, 1])
out = WS / "figures" / "residual_map.png"; fig.savefig(out, dpi=150, bbox_inches="tight"); plt.close(fig)
print(f"\nwrote {out}")
print("residual by height-region:", region)
print("worst modes (Hz / shapeMAC / ampErr dB):", [(m["f_hz"], m["shape_MAC"], m["peak_amp_err_dB"]) for m in permode[:6]])
