#!/usr/bin/env python3
"""Probe one raw modal .mat: confirm record length, fs, force channel, pre-trigger impact sample, units/scale.
Read-only. Prints stats; writes nothing. (Re-grounding the time-domain ringdown caches before building them.)"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import scipy.io as sio

WS = Path(__file__).resolve().parent.parent
EXTR = WS.parent / "shocksat_psd_envelope_twin_20260623" / "data" / "extracted_modal"
FS = 250000.0
FORCE_REC = 116

def first_mat(folder):
    d = EXTR / folder
    return sorted(d.glob("*.mat"))[0]

def samp(M, r):
    return np.asarray(M[f"Recorder{r}"].Channels.Segments.Data.Samples, float)

def main():
    folder = sys.argv[1] if len(sys.argv) > 1 else "Test01_ModalHammer_990x"
    fp = first_mat(folder)
    print(f"file: {fp.name}")
    # probe force + a handful of accels
    want = [f"Recorder{FORCE_REC}"] + [f"Recorder{d}" for d in (1, 2, 50, 75, 110)]
    M = sio.loadmat(str(fp), variable_names=want, struct_as_record=False, squeeze_me=True)
    F = samp(M, FORCE_REC)
    N = len(F)
    ip = int(np.argmax(np.abs(F)))
    print(f"record length N = {N} samples = {N/FS*1000:.1f} ms @ fs={FS:.0f} Hz")
    print(f"force Recorder{FORCE_REC}: peak |F| = {np.abs(F).max():.2f} (lbf?) at sample {ip} = {ip/FS*1000:.1f} ms")
    print(f"  pre-impact samples: {ip} = {ip/FS*1000:.1f} ms ; post-impact (ringdown): {N-ip} = {(N-ip)/FS*1000:.1f} ms")
    print(f"  force baseline (pre-impact rms, first 50k): {np.sqrt(np.mean(F[:50000]**2)):.4f}")
    print(f"  force pulse width (samples > 10% peak): {(np.abs(F) > 0.1*np.abs(F).max()).sum()}")
    # try to read channel name/unit metadata if present
    try:
        rec = M[f"Recorder{FORCE_REC}"]
        ch = rec.Channels
        for attr in ("Name", "ChannelName", "Unit", "Units"):
            print(f"  force meta {attr}: {getattr(ch, attr, '?')}")
    except Exception as e:
        print("  (no channel meta:", e, ")")
    for d in (1, 50, 110):
        y = samp(M, d)
        # response near a mode: rms of post-impact ringdown vs pre-impact baseline
        pre = np.sqrt(np.mean(y[:ip-1000]**2)) if ip > 2000 else float("nan")
        post = np.sqrt(np.mean(y[ip+100:ip+25000]**2))
        print(f"  accel Rec{d}: peak |a|={np.abs(y).max():.3f} g? ; pre-rms={pre:.5f} post-rms={post:.5f} "
              f"SNR(post/pre)={post/(pre+1e-12):.1f}")

if __name__ == "__main__":
    main()
