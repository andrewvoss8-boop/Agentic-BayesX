#!/usr/bin/env python3
"""Distill the +Y (Test03/990y) 5th drive to the SAME cache format as the 4 canonical modal references.

REUSES (imports, never edits) the psd_envelope_twin machinery:
  - multiref_frf.build_reference / save_cache  (byte-identical windowing: N=122880, band 45-260 Hz, exp window,
    force window, same accel channel set = Recorders 1..115 minus BAD_DAQ {29,30,31,101} = 111 channels).
The +Y modal hammer (Test03) has a different tip/force spectrum than the impact tests, so a per-reference gain is
expected downstream (same as +XY); the FRF SHAPE (peaks/participations) is what the trust/updating use.

Output: <ws>/data/multiref_modal/m_ypos_990y.npz  (matches m_xpos_990x.npz schema).
Also copies the 4 canonical caches into <ws>/data/multiref_modal/ so all 5 drives live together.
Resumable: skips m_ypos_990y.npz if it already exists (use --force to rebuild).
"""
from __future__ import annotations
import sys, json, time, shutil
from pathlib import Path
import numpy as np

WS = Path(__file__).resolve().parent.parent
BASE = WS.parent / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(BASE / "code"))
import multiref_frf as mr  # reused, unedited

N_MODAL = 122880
CANON_DIR = BASE / "data" / "multiref_modal"
OUT_DIR = WS / "data" / "multiref_modal"; OUT_DIR.mkdir(parents=True, exist_ok=True)


def main(force=False):
    t0 = time.time()
    # point the loader at THIS workspace's extracted Test03 hits
    mr.EXTRACTED = WS / "data" / "extracted_modal"
    # copy the 4 canonical caches next to the new +Y cache (tiny; keeps all 5 drives in one dir)
    for p in sorted(CANON_DIR.glob("m_*.npz")):
        dst = OUT_DIR / p.name
        if not dst.exists():
            shutil.copy2(p, dst)
    outp = OUT_DIR / "m_ypos_990y.npz"
    if outp.exists() and not force:
        z = np.load(outp, allow_pickle=True)
        print(f"m_ypos_990y.npz exists: {int(z['n_hits_used'])} hits, {z['freqs'].size} freqs, "
              f"{z['H1'].shape[0]} channels (skipping rebuild)")
        return
    rec = mr.build_reference("ypos_990y", N=N_MODAL)
    if rec is None or not rec.get("n_hits_used"):
        raise SystemExit("no usable Test03/990y hits extracted")
    mr.save_cache(rec, outp)
    coh = rec["coherence"]; mag = np.median(np.abs(rec["H1"]), axis=0)
    from scipy.signal import find_peaks
    fb = rec["freqs"]
    pk, _ = find_peaks(np.log(mag + 1e-300), prominence=0.3, distance=max(1, int(2.0 / (fb[1] - fb[0]))))
    peaks = [round(float(fb[i]), 1) for i in pk]
    summ = {"label": rec["label"], "axis": rec["axis"], "xyz": rec["xyz"], "N": N_MODAL,
            "n_hits_used": rec["n_hits_used"], "n_hits_skipped": rec["n_hits_skipped"],
            "df_hz": rec["df_hz"], "n_freqs": int(fb.size), "n_channels": int(rec["H1"].shape[0]),
            "coh_inband_median": float(np.median(coh)), "n_modal_peaks": len(peaks), "modal_peaks_hz": peaks,
            "used": rec["used"], "runtime_s": round(time.time() - t0, 1)}
    (WS / "out" / "ypos_cache_summary.json").write_text(json.dumps(summ, indent=2))
    print(f"[m_ypos_990y] {rec['label']} axis {rec['axis']}: hits {rec['n_hits_used']} "
          f"(skip {rec['n_hits_skipped']}); df {rec['df_hz']:.2f} Hz; {fb.size} freqs; "
          f"{rec['H1'].shape[0]} ch; coh med {np.median(coh):.3f}; {len(peaks)} peaks {peaks}")
    print(f"runtime {time.time()-t0:.0f}s -> {outp}")


if __name__ == "__main__":
    main(force="--force" in sys.argv)
