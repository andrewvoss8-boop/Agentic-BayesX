#!/usr/bin/env python3
"""Layer-0: build small TIME-DOMAIN ring-down caches from the clean modal-hammer .mat records.

The inherited multiref_modal caches are band-limited FRFs (frequency domain). This runner needs the raw
time histories (force in lbf + acceleration in g vs time) of the ring-downs to estimate decay rates.

Per reference (Test01 +X@990 / Test02 +Z@990 / Test04 +XY@990 / Test06 +Z@900), per hit (6 roving impacts):
  - load force Recorder116 (lbf) + all good accel Recorders 1..115 minus BAD_DAQ (g);
  - impact sample = argmax|F| (records are PRE-TRIGGERED: impact lands at ~500 ms = sample ~125,009);
  - anti-alias DECIMATE the full 1 s record from fs=250 kHz to fs_dec=2.5 kHz (factor 100; Nyquist 1.25 kHz,
    well above the 45-260 Hz band) with a zero-phase FIR so the decay envelope is preserved;
  - store the decimated force + accel time series (relative time to impact), impact index, and per-channel
    pre-impact / post-impact RMS for an SNR gate. Disk-thrifty: ~13 MB/ref compressed.

Units: accel g, force lbf (D2: per-channel cal already applied; samples already in engineering units). fs/pre-trigger
verified by probe_mat.py (N=250001, impact ~125,009 = 500 ms). AGENTS Discretization Gate: fs, decimation, window
all documented here and echoed into out/cache_summary.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.signal import decimate
import scipy.io as sio

WS = Path(__file__).resolve().parent.parent
PSDWS = WS.parent / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(PSDWS / "code"))
import realfrf as rf  # reused byte-identical (SHA in REUSED_code.sha256): FS, FORCE_RECORDER, BAD_DAQ, N_ACCEL

EXTR = PSDWS / "data" / "extracted_modal"
CACHE = WS / "data" / "ringdown"; CACHE.mkdir(parents=True, exist_ok=True)
FS = rf.FS                       # 250000.0
FORCE_REC = rf.FORCE_RECORDER    # 116
BAD = rf.BAD_DAQ                 # {29,30,31,101}
N_ACCEL = rf.N_ACCEL_RECORDERS   # 115
DECIM = 100                      # 250 kHz -> 2.5 kHz
FS_DEC = FS / DECIM

REFS = {
    "m_xpos_990x": dict(folder="Test01_ModalHammer_990x", label="+X (990)", axis="X", xyz=(9.0, 7.6, 0.6)),
    "m_zpos_990z": dict(folder="Test02_ModalHammer_990z", label="+Z (990)", axis="Z", xyz=(9.0, 7.8, 0.0)),
    "m_xy_990xy":  dict(folder="Test04_ModalHammer_990xy", label="+XY (990)", axis="XY", xyz=(9.0, 9.0, 1.1)),
    "m_zpos_900z": dict(folder="Test06_ModalHammer_900z", label="+Z (900)", axis="Z", xyz=(9.0, 0.0, 0.0)),
}


def good_daqs():
    return [d for d in range(1, N_ACCEL + 1) if d not in BAD]


def load_hit(matpath, daqs):
    want = [f"Recorder{FORCE_REC}"] + [f"Recorder{d}" for d in daqs]
    M = sio.loadmat(str(matpath), variable_names=want, struct_as_record=False, squeeze_me=True)
    F = np.asarray(M[f"Recorder{FORCE_REC}"].Channels.Segments.Data.Samples, float)
    A = np.array([np.asarray(M[f"Recorder{d}"].Channels.Segments.Data.Samples, float) for d in daqs])
    return F, A


def decim_chain(x, q, axis=-1):
    """Zero-phase FIR decimation by factor q via small stages (each <=10) to keep the anti-alias well-conditioned."""
    stages = {100: [5, 5, 4], 50: [5, 5, 2], 25: [5, 5], 10: [5, 2]}[q]
    for s in stages:
        x = decimate(x, s, ftype="fir", zero_phase=True, axis=axis)
    return x


def build_ref(key):
    ref = REFS[key]
    daqs = good_daqs()
    files = sorted((EXTR / ref["folder"]).glob("*.mat"))
    if not files:
        print(f"[{key}] no .mat in {EXTR / ref['folder']}"); return None
    Fs, As, ip_raw, fpk, apk, prerms, postrms = [], [], [], [], [], [], []
    for fp in files:
        F, A = load_hit(fp, daqs)
        ip = int(np.argmax(np.abs(F)))
        ip_raw.append(ip); fpk.append(float(np.abs(F).max()))
        apk.append(np.abs(A).max(axis=1))
        # pre-impact baseline (well before impact) and post-impact ring-down (first 100 ms after) at full fs
        pre = A[:, max(0, ip - 100000):ip - 2000]
        post = A[:, ip + 250:ip + 25250]   # ~1-101 ms after impact
        prerms.append(np.sqrt(np.mean(pre ** 2, axis=1)))
        postrms.append(np.sqrt(np.mean(post ** 2, axis=1)))
        Fd = decim_chain(F, DECIM)
        Ad = decim_chain(A, DECIM, axis=1)
        Fs.append(Fd); As.append(Ad)
    n_t = min(len(f) for f in Fs)
    Fs = np.array([f[:n_t] for f in Fs])                 # (n_hits, n_t)
    As = np.array([a[:, :n_t] for a in As])              # (n_hits, n_daq, n_t)
    ip_dec = np.array([int(round(ip / DECIM)) for ip in ip_raw])
    t = (np.arange(n_t) - int(np.median(ip_dec))) / FS_DEC   # seconds relative to impact (median)
    np.savez_compressed(
        CACHE / f"{key}.npz",
        F=Fs.astype(np.float32), A=As.astype(np.float32), t=t.astype(np.float32),
        daq=np.array(daqs), impact_idx_dec=ip_dec, impact_idx_raw=np.array(ip_raw),
        fs_dec=FS_DEC, fs_raw=FS, decim=DECIM, axis=ref["axis"], label=ref["label"],
        xyz=np.array(ref["xyz"]), force_peak_lbf=np.array(fpk), accel_peak_g=np.array(apk),
        pre_rms=np.array(prerms), post_rms=np.array(postrms), files=np.array([f.name for f in files]),
    )
    snr = np.array(postrms) / (np.array(prerms) + 1e-12)
    summ = dict(label=ref["label"], axis=ref["axis"], xyz=list(ref["xyz"]), folder=ref["folder"],
                n_hits=len(files), n_daq=len(daqs), n_t=int(n_t), fs_dec=float(FS_DEC), decim=DECIM,
                ringdown_ms=float((n_t - int(np.median(ip_dec))) / FS_DEC * 1000),
                impact_ms_median=float(np.median(ip_raw) / FS * 1000),
                force_peak_lbf_median=float(np.median(fpk)),
                snr_post_pre_median=float(np.median(snr)), snr_post_pre_p90=float(np.percentile(snr, 90)))
    print(f"[{key}] {ref['label']}: {len(files)} hits, {len(daqs)} ch, n_t={n_t} @ {FS_DEC:.0f} Hz; "
          f"ringdown {summ['ringdown_ms']:.0f} ms; Fpk {summ['force_peak_lbf_median']:.0f} lbf; "
          f"SNR med {summ['snr_post_pre_median']:.1f}")
    return summ


def main():
    t0 = time.time()
    summ = {}
    for key in REFS:
        s = build_ref(key)
        if s:
            summ[key] = s
    summ["_meta"] = dict(fs_raw=FS, fs_dec=FS_DEC, decim=DECIM, band=list(rf.BAND),
                         note="time-domain ring-down caches (decimated 250k->2.5k); g & lbf; impact pre-triggered ~500 ms",
                         runtime_s=round(time.time() - t0, 1))
    (WS / "out" / "cache_summary.json").write_text(json.dumps(summ, indent=2))
    print(f"\nwrote out/cache_summary.json ({summ['_meta']['runtime_s']}s); caches in data/ringdown/")


if __name__ == "__main__":
    main()
