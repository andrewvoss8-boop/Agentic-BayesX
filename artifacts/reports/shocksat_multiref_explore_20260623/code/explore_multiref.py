#!/usr/bin/env python3
"""Read-only EXPLORATION of the newly pulled multi-reference modal-hammer data (Test01 +X / Test02 +Z /
Test04 +XY, node 990, 6 hits each). NO sampler, NO FEM — pure data-quality diagnostic so we can decide,
BEFORE embarking, whether this data is clean/combinable enough to be the width lever for the PSD-envelope twin.

Replicates the EXACT windowing in shocksat_multiref_amplitude_20260622/code/multiref_frf.py (which itself
reuses realfrf.PROC), but self-contained (no realfrf/core import → no FEM dependency):
  per hit: force = Recorder116 (lb); impact-aligned single FFT; force box (+-2 ms) + exponential response
  window (end 0.05); ensemble over hits that fit the N=200000 window:
    H1 = (Sum Y conj F) / (Sum |F|^2);  coh = |Sum Y conjF|^2 / (Sum|F|^2 Sum|Y|^2)  (multi-HIT coherence).

Reports, per reference: hits used/skipped, peak force (lbf), force-spectrum -3 dB rolloff (modal vs impact
bandwidth), in-band (45-260 Hz) coherence median/90th/max vs uncorrelated floor 1/n_hits, and the consensus
modal peak frequencies (channel-median |H1|). Also runs the same on Test07 (+X impact) / Test08 (+Z impact)
for a same-direction modal-vs-impact quality comparison. Output: out/explore_summary.json + console.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
import scipy.io as sio
from scipy.signal import find_peaks

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; OUT.mkdir(exist_ok=True)
RUNNER_EXTRACTED = WS.parent / "shocksat_statfem_runner_20260609" / "extracted"
NEW_EXTRACTED = WS / "data" / "extracted"

FS = 250000.0
BAND = (45.0, 260.0)
FORCE_RECORDER = 116
N_ACCEL = 115
BAD_DAQ = {29, 30, 31, 101}
# N reduced from Card G's 200000 (0.8 s) because the MODAL-hammer records are pre-triggered: the impact lands
# mid-record (~500 ms), leaving ~0.5 s of post-impact ring-down. N=122880 (0.49 s, df=2.03 Hz) fits all hits.
PROC = {"N": 122880, "force_ms": 2.0, "exp_end": 0.05, "pre_gap": 200}

REFS = [
    ("Test01 +X modal", NEW_EXTRACTED / "Test01_ModalHammer_990x", "modal"),
    ("Test02 +Z modal", NEW_EXTRACTED / "Test02_ModalHammer_990z", "modal"),
    ("Test04 +XY modal", NEW_EXTRACTED / "Test04_ModalHammer_990xy", "modal"),
    ("Test07 +X impact (Card A ref)", RUNNER_EXTRACTED / "Test07_ImpactHammer_990x", "impact"),
    ("Test08 +Z impact (Card G)", RUNNER_EXTRACTED / "Test08_ImpactHammer_990z", "impact"),
]


def _exp_window(N, end):
    return np.exp(np.log(end) * np.arange(N) / (N - 1))


def _samples(struct):
    return np.asarray(struct.Channels.Segments.Data.Samples, float)


def build(folder, daqs):
    files = sorted(folder.glob("*.mat"))
    N = PROC["N"]; pre_gap = PROC["pre_gap"]
    half = int(PROC["force_ms"] * 1e-3 * FS)
    ewin = _exp_window(N, PROC["exp_end"])
    freqs = np.fft.rfftfreq(N, 1 / FS)
    bm = (freqs >= BAND[0]) & (freqs <= BAND[1])
    Sxx = np.zeros(bm.sum()); Sxy = np.zeros((len(daqs), bm.sum()), complex); Syy = np.zeros((len(daqs), bm.sum()))
    Fpsd_sum = np.zeros(len(freqs))
    used, skipped, fpk = [], [], []
    for fp in files:
        want = [f"Recorder{FORCE_RECORDER}"] + [f"Recorder{d}" for d in daqs]
        M = sio.loadmat(str(fp), variable_names=want, struct_as_record=False, squeeze_me=True)
        if f"Recorder{FORCE_RECORDER}" not in M:
            skipped.append(fp.name + " [no force ch]"); continue
        F = _samples(M[f"Recorder{FORCE_RECORDER}"])
        ip = int(np.argmax(np.abs(F))); start = max(0, ip - pre_gap)
        if start + N > len(F):
            skipped.append(fp.name + " [window overruns]"); continue
        sl = slice(start, start + N); pk = ip - start
        fwin = np.zeros(N); fwin[max(0, pk - half):pk + half] = 1.0
        Ff = np.fft.rfft(F[sl] * fwin)
        Y = np.array([_samples(M[f"Recorder{d}"]) for d in daqs])
        Yf = np.fft.rfft(Y[:, sl] * ewin, axis=1)
        Sxx += (np.abs(Ff) ** 2)[bm]; Sxy += Yf[:, bm] * np.conj(Ff)[bm]; Syy += (np.abs(Yf) ** 2)[:, bm]
        Fpsd_sum += np.abs(Ff) ** 2
        used.append(fp.name); fpk.append(float(np.max(np.abs(F))))
    if not used:
        return {"n_hits_used": 0, "n_hits_skipped": len(skipped), "skipped": skipped}
    n = len(used)
    H1 = Sxy / Sxx[None, :]
    coh = (np.abs(Sxy) ** 2) / (Sxx[None, :] * Syy + 1e-300)
    fbm = freqs[bm]
    # force-spectrum -3 dB rolloff (broadband, from DC): where mean force PSD drops 3 dB below its low-f plateau
    Fpsd = Fpsd_sum / n; lowf = (freqs > 20) & (freqs < 200)
    plateau = np.median(Fpsd[lowf]); roll = freqs[np.where(Fpsd < plateau / 2)[0]]
    f_roll = float(roll[roll > 200][0]) if np.any(roll > 200) else float("nan")
    # consensus modal peaks: channel-median |H1| in band
    mag = np.median(np.abs(H1), axis=0)
    pk_idx, _ = find_peaks(np.log(mag + 1e-300), prominence=0.3, distance=max(1, int(2.0 / (fbm[1] - fbm[0]))))
    peaks = [round(float(fbm[i]), 1) for i in pk_idx]
    return {"n_hits_used": n, "n_hits_skipped": len(skipped), "used": used, "skipped": skipped,
            "peak_force_lbf_median": float(np.median(fpk)), "peak_force_lbf_range": [float(min(fpk)), float(max(fpk))],
            "force_-3dB_rolloff_hz": f_roll, "coh_uncorrelated_floor": round(1.0 / n, 3),
            "coh_inband_median": float(np.median(coh)), "coh_inband_90th": float(np.percentile(coh, 90)),
            "coh_inband_max": float(coh.max()),
            "coh_at_peaks_median": float(np.median([np.median(coh[:, np.argmin(np.abs(fbm - p))]) for p in peaks])) if peaks else None,
            "n_modal_peaks_45_260": len(peaks), "modal_peaks_hz": peaks}


def main():
    daqs = [d for d in range(1, N_ACCEL + 1) if d not in BAD_DAQ]
    t0 = time.time(); res = {}
    for label, folder, kind in REFS:
        if not folder.exists():
            print(f"[skip] {label}: {folder} not found"); res[label] = {"missing": True}; continue
        print(f"[{time.time()-t0:5.0f}s] processing {label} ({folder.name}) ...", flush=True)
        r = build(folder, daqs); r["kind"] = kind; res[label] = r
        if r["n_hits_used"]:
            print(f"   hits {r['n_hits_used']} (skip {r['n_hits_skipped']}); peakF {r['peak_force_lbf_median']:.2f} lbf;"
                  f" force-3dB {r['force_-3dB_rolloff_hz']:.0f} Hz")
            print(f"   coherence in-band: median {r['coh_inband_median']:.3f} / 90th {r['coh_inband_90th']:.3f}"
                  f" / max {r['coh_inband_max']:.3f}  (uncorr floor {r['coh_uncorrelated_floor']}); at-peaks {r['coh_at_peaks_median']}")
            print(f"   modal peaks 45-260 Hz ({r['n_modal_peaks_45_260']}): {r['modal_peaks_hz']}")
        else:
            print(f"   NO usable hits (skipped {r['n_hits_skipped']}): {r['skipped']}")
    res["_meta"] = {"runtime_s": round(time.time() - t0, 1), "n_daq": len(daqs), "band_hz": list(BAND),
                    "proc": PROC, "fs_hz": FS, "note": "read-only data diagnostic; no sampler, no FEM"}
    (OUT / "explore_summary.json").write_text(json.dumps(res, indent=2))
    print(f"\nwrote {OUT/'explore_summary.json'}  ({res['_meta']['runtime_s']}s)")


if __name__ == "__main__":
    main()
