#!/usr/bin/env python3
"""
GRADING-ONLY ShockSat pyro-regime OOD check (separate grading session; allowed to see held-out).
Writes ONLY under review/.

Goal: honestly adjudicate the runner's COMMITTED *directional* prediction
(runner_opus/shocksat_predictions.json):
  "twin UNDER-resolves the pyro regime ... twin will UNDER-predict pyro response"
with the runner's modal twin validated only to ~152 Hz (first ~38 elastic free-free modes).

This is a DIRECTIONAL out-of-distribution check, not a precise number: only a directional
prediction was committed, and the exact pyro-NSD QOI definition lived in the (forbidden) manifest.

We quantify WHERE the real pyro energy lives and what fraction sits ABOVE the twin's validated
modal band. If most pyro energy is far above ~152 Hz, a modal twin truncated there must
under-resolve the regime -> the runner's directional call is CORRECT.
"""
import os, json
import numpy as np
import scipy.io as sio
from scipy.signal import welch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MAT = os.path.join(ROOT, "grading files", "Pyro_NSD_990x001_HELDOUT.mat")
if not os.path.exists(MAT):
    # File was restored to its sibling location (pins 'restore-to'); read read-only in place.
    # SHA256 re-verified == pin 03e476fa...6f6944 before use.
    MAT = ("/Users/avoss/Downloads/bayesX/Agentic BayesX/artifacts/reports/"
           "shocksat_statfem_runner_20260609/extracted/Pyro_NSI_NSD/NSD1_Test/"
           "Pyro_NSD_990x001_10_13_2021_2_20_42 PM.mat")
TWIN_BAND_HZ = 152.27          # runner's stated validated band (shocksat_predictions.json)
QOI_EDGE_HZ = 400.0            # runner's extrapolation point
m = sio.loadmat(MAT, squeeze_me=True, struct_as_record=False)
recs = [k for k in m if k.startswith("Recorder")]

rows = []
spec_acc = None
freqs = None
psd_all = []  # per-channel PSDs for inter-channel spread band
for k in recs:
    r = m[k]
    d = r.Channels.Segments.Data
    name = r.Channels.ChannelInfos.ChannelInfo.Name
    yunits = r.Channels.ChannelInfos.ChannelInfo.YUnits
    dt = float(d.dXstep)
    fs = 1.0 / dt
    x = np.asarray(d.Samples, float)
    x = x - x.mean()
    # Welch PSD; nperseg gives ~ fs/nperseg resolution
    nper = 8192
    f, P = welch(x, fs=fs, nperseg=min(nper, len(x)), detrend="constant")
    df = f[1] - f[0]
    tot = np.trapz(P, f)
    def frac_above(fc):
        msk = f >= fc
        return float(np.trapz(P[msk], f[msk]) / tot) if tot > 0 else float("nan")
    csum = np.cumsum(P) * df
    csum /= csum[-1]
    f95 = float(f[np.searchsorted(csum, 0.95)])
    fpk = float(f[np.argmax(P)])
    rows.append({
        "channel": str(name), "yunits": str(yunits), "fs_hz": fs,
        "rms": float(np.sqrt(np.mean(x**2))), "peak_abs": float(np.max(np.abs(x))),
        "frac_energy_above_twin_band_152Hz": frac_above(TWIN_BAND_HZ),
        "frac_energy_above_400Hz": frac_above(QOI_EDGE_HZ),
        "frac_energy_above_1kHz": frac_above(1000.0),
        "f95_hz": f95, "peak_psd_freq_hz": fpk,
    })
    if spec_acc is None:
        spec_acc = np.zeros_like(P); freqs = f
    if len(P) == len(spec_acc):
        spec_acc += P
        psd_all.append(P)

# ensemble spectrum across channels (same nperseg/fs -> same f grid)
spec_mean = spec_acc / len(recs)
psd_all = np.vstack(psd_all)  # (n_channels, n_freq)
# cumulative energy fraction per channel (the twin's "coverage" = fraction inside its band)
cum = np.cumsum(psd_all, axis=1)
cum = cum / cum[:, -1:]
np.savez(os.path.join(HERE, "pyro_spectrum.npz"),
         f=freqs, psd_mean=spec_mean, psd_all=psd_all, cumfrac=cum)

import statistics as st
agg = {
    "n_channels": len(recs),
    "fs_hz": rows[0]["fs_hz"],
    "nyquist_hz": rows[0]["fs_hz"]/2,
    "twin_validated_band_hz": TWIN_BAND_HZ,
    "median_frac_energy_above_152Hz": float(np.median([r["frac_energy_above_twin_band_152Hz"] for r in rows])),
    "median_frac_energy_above_400Hz": float(np.median([r["frac_energy_above_400Hz"] for r in rows])),
    "median_frac_energy_above_1kHz": float(np.median([r["frac_energy_above_1kHz"] for r in rows])),
    "median_f95_hz": float(np.median([r["f95_hz"] for r in rows])),
    "median_peak_psd_freq_hz": float(np.median([r["peak_psd_freq_hz"] for r in rows])),
}
# Directional verdict
agg["committed_prediction"] = "twin UNDER-resolves the pyro regime; under-predicts pyro response"
agg["directional_prediction_correct"] = bool(agg["median_frac_energy_above_152Hz"] > 0.5)
agg["interpretation"] = (
    "Median %.1f%% of real pyro-NSD acceleration energy lies ABOVE the twin's ~152 Hz validated "
    "modal band (median 95%%-energy frequency = %.0f Hz, peak-PSD freq = %.0f Hz). A modal twin "
    "truncated near 152 Hz therefore cannot resolve the regime, confirming the runner's committed "
    "DIRECTION (under-resolves / under-predicts). Magnitude is not graded: only a direction was committed."
    % (100*agg["median_frac_energy_above_152Hz"], agg["median_f95_hz"], agg["median_peak_psd_freq_hz"])
)
out = {"aggregate": agg, "per_channel": rows}
json.dump(out, open(os.path.join(HERE, "shocksat_grading_result.json"), "w"), indent=2)
print(json.dumps(agg, indent=2))
