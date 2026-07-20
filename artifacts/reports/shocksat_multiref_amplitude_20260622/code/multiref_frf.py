#!/usr/bin/env python3
"""Card G — multi-reference FRF + coherence processing (NEW; reuses realfrf's EXACT windowing constants).

For each excitation REFERENCE (drive direction/location) builds a band-limited (45-260 Hz) per-channel FRF cache:
  - per hit: force = Recorder116 (lb); window the force pulse (2 ms box) + exponential response window (end 0.05),
    impact-ALIGNED (start = argmax|F| - pre_gap) so the impact sits at the same in-window position every hit; single
    FFT. This is byte-identical processing to realfrf.reprocess_measured (PROC), just per-hit and per-reference.
  - ENSEMBLE over the hits that FIT the window (operator hit at random times → some impacts are too late for an
    N-sample window; those hits are skipped, recorded in n_hits_skipped):
        Sxx = Σ|F_i|²,  Sxy = Σ Y_i·conj(F_i),  Syy = Σ|Y_i|²
        H1   = Sxy / Sxx                          (the multi-hit FRF estimate; == Y/F for a single hit)
        coh  = |Sxy|² / (Sxx·Syy)                 (ordinary multi-HIT coherence; averaging axis = across impacts,
                                                   NOT segments of one transient — AGENTS Discretization Gate)
Coherence with few hits is biased high (floor ≈ 1/n_hits for uncorrelated signals); n_hits is reported next to it.
A separate Welch within-hit estimate (nperseg) is also reported for the broadband apples-to-apples vs the +X manifest.

Drive coordinates (TestLog_Tap; filename 990X/Y/Z / 900Z = the reliable impact DIRECTION; 'Face' text is a known
copy-paste artifact). The forward maps each to a reduced drive row via realfrf.Reduced.reduced_row(xyz, axis).
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np

import realfrf as rf

FS = rf.FS
BAND = rf.BAND
FORCE_RECORDER = rf.FORCE_RECORDER
G_IN_S2 = rf.G_IN_S2
BAD_DAQ = rf.BAD_DAQ
N_ACCEL = rf.N_ACCEL_RECORDERS

WS = Path(__file__).resolve().parent.parent
RUNNER = WS.parent / "shocksat_statfem_runner_20260609"
EXTRACTED = RUNNER / "extracted"

# Reference registry. dir = extracted .mat folder (relative to EXTRACTED); xyz/axis = drive; instrument; label.
REFS = {
    "xpos_990x": dict(label="+X", folder="Test07_ImpactHammer_990x", xyz=(9.0, 8.0, 1.0), axis="X",
                      instrument="impact", note="Test07 hit-001 (the Card A +X reference); only hit-001 on disk"),
    "zpos_990z": dict(label="+Z", folder="Test08_ImpactHammer_990z", xyz=(9.0, 8.0, 0.0), axis="Z",
                      instrument="impact", note="Test08; 5 hits on disk; small double-hit noted in TestLog"),
    "ypos_990y": dict(label="+Y", folder="Test03_ModalHammer_990y", xyz=(8.5, 9.0, 1.0), axis="Y",
                      instrument="modal", note="Test03 MODAL hammer (different tip/force spectrum → per-test gain)"),
    "z_900z": dict(label="900z", folder="Test10_ImpactHammer_900z", xyz=(9.0, 0.5, 0.0), axis="Z",
                   instrument="impact", note="Test10; different drive LOCATION (largest phi_d contrast)"),
}

PROC = rf.PROC  # {N, force_ms, exp_end, pre_gap, baseline_N}


def _hit_files(folder):
    d = EXTRACTED / folder
    return sorted(d.glob("*.mat")) if d.exists() else []


def _load_hit(matpath, daqs):
    import scipy.io as sio
    want = [f"Recorder{FORCE_RECORDER}"] + [f"Recorder{d}" for d in daqs]
    M = sio.loadmat(str(matpath), variable_names=want, struct_as_record=False, squeeze_me=True)
    F = np.asarray(M[f"Recorder{FORCE_RECORDER}"].Channels.Segments.Data.Samples, float)
    Y = np.array([np.asarray(M[f"Recorder{d}"].Channels.Segments.Data.Samples, float) for d in daqs])
    return F, Y


def _spectra(F, Y, N, force_ms, exp_end, pre_gap):
    """realfrf-identical windowed single-FFT spectra for one hit; None if the impact window does not fit."""
    ip = int(np.argmax(np.abs(F)))
    start = max(0, ip - pre_gap)
    if start + N > len(F):
        return None
    sl = slice(start, start + N)
    pk = ip - start
    half = int(force_ms * 1e-3 * FS)
    fwin = np.zeros(N); fwin[max(0, pk - half):pk + half] = 1.0
    ewin = rf._exp_window(N, exp_end)
    Ff = np.fft.rfft(F[sl] * fwin)
    Yf = np.fft.rfft(Y[:, sl] * ewin, axis=1)
    return Ff, Yf, ip


def build_reference(key, daqs=None, N=None, max_hits=None, welch_nperseg=16384):
    """Ensemble multi-hit FRF + coherence for one reference, band-limited to 45-260 Hz."""
    ref = REFS[key]
    N = PROC["N"] if N is None else int(N)
    daqs = [d for d in range(1, N_ACCEL + 1) if d not in BAD_DAQ] if daqs is None else list(daqs)
    files = _hit_files(ref["folder"])
    if not files:
        return None
    if max_hits:
        files = files[:max_hits]
    freqs = np.fft.rfftfreq(N, 1 / FS)
    bm = (freqs >= BAND[0]) & (freqs <= BAND[1])
    Sxx = np.zeros(bm.sum()); Sxy = np.zeros((len(daqs), bm.sum()), complex); Syy = np.zeros((len(daqs), bm.sum()))
    used, skipped, ips = [], [], []
    welch = None
    from scipy.signal import csd, welch as wl
    for fp in files:
        F, Y = _load_hit(fp, daqs)
        sp = _spectra(F, Y, N, PROC["force_ms"], PROC["exp_end"], PROC["pre_gap"])
        if sp is None:
            skipped.append(fp.name); continue
        Ff, Yf, ip = sp
        Sxx += (np.abs(Ff) ** 2)[bm]
        Sxy += Yf[:, bm] * np.conj(Ff)[bm]
        Syy += (np.abs(Yf) ** 2)[:, bm]
        used.append(fp.name); ips.append(int(ip))
        if welch is None:  # broadband Welch coherence on the FIRST used hit (apples-to-apples vs +X manifest)
            Fb = np.ascontiguousarray(np.broadcast_to(F, Y.shape))
            wf, Pxx = wl(F, fs=FS, nperseg=welch_nperseg)
            _, Pxy = csd(Y, Fb, fs=FS, nperseg=welch_nperseg, axis=1)
            _, Pyy = wl(Y, fs=FS, nperseg=welch_nperseg, axis=1)
            cohw = (np.abs(Pxy) ** 2) / (Pxx[None, :] * Pyy + 1e-300)
            wb = (wf >= BAND[0]) & (wf <= BAND[1])
            bb = (wf >= 100.0) & (wf <= 10000.0)
            welch = {"nperseg": welch_nperseg, "df_hz": float(wf[1] - wf[0]),
                     "median_inband_45_260": float(np.median(cohw[:, wb])),
                     "median_broadband_100_10k": float(np.median(cohw[:, bb]))}
    if not used:
        return {"key": key, **{k: ref[k] for k in ("label", "axis", "instrument", "note")},
                "n_hits_used": 0, "n_hits_skipped": len(skipped), "skipped": skipped, "files_total": len(files)}
    n = len(used)
    H1 = Sxy / Sxx[None, :]
    coh = (np.abs(Sxy) ** 2) / (Sxx[None, :] * Syy + 1e-300)
    return {"key": key, **{k: ref[k] for k in ("label", "axis", "instrument", "note")},
            "xyz": list(ref["xyz"]), "N": N, "df_hz": float(freqs[1] - freqs[0]),
            "freqs": freqs[bm], "H1": H1, "coherence": coh, "daq": daqs,
            "n_hits_used": n, "n_hits_skipped": len(skipped), "used": used, "skipped": skipped,
            "impact_idx": ips, "welch": welch, "coh_floor_uncorrelated": 1.0 / n}


def save_cache(rec, path):
    np.savez_compressed(path, freqs=rec["freqs"], H1=rec["H1"], coherence=rec["coherence"],
                        daq=np.array(rec["daq"]), xyz=np.array(rec["xyz"]), axis=rec["axis"],
                        label=rec["label"], instrument=rec["instrument"], N=rec["N"],
                        n_hits_used=rec["n_hits_used"], used=np.array(rec["used"]),
                        impact_idx=np.array(rec["impact_idx"]))


def load_cache(path):
    z = np.load(path, allow_pickle=True)
    return {k: z[k] for k in z.files}


if __name__ == "__main__":
    import sys
    key = sys.argv[1] if len(sys.argv) > 1 else "zpos_990z"
    N = int(sys.argv[2]) if len(sys.argv) > 2 else PROC["N"]
    rec = build_reference(key, N=N)
    if rec is None:
        print(f"{key}: no extracted hits"); sys.exit(0)
    print(f"{key} ({rec['label']}, {rec.get('instrument')}): hits used {rec['n_hits_used']} "
          f"skipped {rec['n_hits_skipped']} (N={N}, df={rec.get('df_hz')})")
    if rec["n_hits_used"]:
        coh = rec["coherence"]
        print(f"  in-band coherence: median {np.median(coh):.3f}, "
              f"90th pct {np.percentile(coh, 90):.3f}, max {coh.max():.3f} (uncorrelated floor {rec['coh_floor_uncorrelated']:.2f})")
        if rec["welch"]:
            print(f"  Welch (first hit): in-band 45-260 {rec['welch']['median_inband_45_260']:.3f}, "
                  f"broadband 100-10k {rec['welch']['median_broadband_100_10k']:.3f}")
