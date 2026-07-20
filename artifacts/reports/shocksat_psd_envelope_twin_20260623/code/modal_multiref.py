#!/usr/bin/env python3
"""Modal multi-reference data layer for the PSD-envelope twin (D2/D5).

Registers the 4 CLEAN modal-hammer references (both drive nodes) and builds band-limited (45-260 Hz) per-channel
H1 + multi-hit coherence caches by REUSING multiref_frf.build_reference BYTE-IDENTICAL (same windowing), with the
pre-trigger window N=122880 (0.49 s) the modal records require (impact lands mid-record at ~500 ms; D2).

Drive coords from TestLog_Tap impact-point centroids (filename direction reliable; 'Face' text = copy-paste artifact).
Samples are in engineering units (accels g, force lbf) ⇒ H1 in g/lbf directly (no per-channel cal / no ×100 gain; D2).
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import multiref_frf as mr

WS = Path(__file__).resolve().parent.parent
mr.EXTRACTED = WS / "data" / "extracted_modal"          # point the loader at our clean modal extraction
CACHE = WS / "data" / "multiref_modal"; CACHE.mkdir(exist_ok=True)
N_MODAL = 122880                                         # pre-trigger ring-down window (df ~ 2.03 Hz)

MODAL_REFS = {
    "m_xpos_990x":  dict(label="+X (990)",  folder="Test01_ModalHammer_990x",  xyz=(9.0, 7.6, 0.6), axis="X",
                         instrument="modal", note="Test01, 6 roving hits, node 990 +X face"),
    "m_zpos_990z":  dict(label="+Z (990)",  folder="Test02_ModalHammer_990z",  xyz=(9.0, 7.8, 0.0), axis="Z",
                         instrument="modal", note="Test02, 6 roving hits, node 990 +Z"),
    "m_xy_990xy":   dict(label="+XY (990)", folder="Test04_ModalHammer_990xy", xyz=(9.0, 9.0, 1.1), axis="XY",
                         instrument="modal", note="Test04, 6 roving hits, node 990 +X+Y corner (combined drive)"),
    "m_zpos_900z":  dict(label="+Z (900)",  folder="Test06_ModalHammer_900z",  xyz=(9.0, 0.0, 0.0), axis="Z",
                         instrument="modal", note="Test06, 6 roving hits, node 900 +Z (y~0 end; max phi_d contrast)"),
}
mr.REFS.update(MODAL_REFS)                               # register so build_reference/save_cache see them


def build_all():
    summ = {}
    t0 = time.time()
    for key in MODAL_REFS:
        rec = mr.build_reference(key, N=N_MODAL)
        if rec is None or not rec.get("n_hits_used"):
            print(f"[{key}] NO usable hits"); summ[key] = {"n_hits_used": 0}; continue
        mr.save_cache(rec, CACHE / f"{key}.npz")
        coh = rec["coherence"]; mag = np.median(np.abs(rec["H1"]), axis=0)
        from scipy.signal import find_peaks
        fb = rec["freqs"]; pk, _ = find_peaks(np.log(mag + 1e-300), prominence=0.3,
                                              distance=max(1, int(2.0 / (fb[1] - fb[0]))))
        peaks = [round(float(fb[i]), 1) for i in pk]
        coh_pk = float(np.median([np.median(coh[:, np.argmin(np.abs(fb - p))]) for p in peaks])) if peaks else None
        summ[key] = {"label": rec["label"], "axis": rec["axis"], "xyz": rec["xyz"],
                     "n_hits_used": rec["n_hits_used"], "n_hits_skipped": rec["n_hits_skipped"],
                     "df_hz": rec["df_hz"], "n_freqs": int(rec["freqs"].size),
                     "coh_inband_median": float(np.median(coh)), "coh_at_peaks_median": coh_pk,
                     "n_modal_peaks": len(peaks), "modal_peaks_hz": peaks}
        print(f"[{key}] {rec['label']}: hits {rec['n_hits_used']} (skip {rec['n_hits_skipped']}); "
              f"df {rec['df_hz']:.2f} Hz; coh med {np.median(coh):.3f} / at-peaks {coh_pk}; "
              f"{len(peaks)} peaks {peaks}")
    union = sorted({round(p, 0) for r in summ.values() for p in r.get("modal_peaks_hz", [])})
    summ["_meta"] = {"N": N_MODAL, "band": list(mr.BAND), "n_daq": int(mr.N_ACCEL - len(mr.BAD_DAQ)),
                     "runtime_s": round(time.time() - t0, 1), "union_peaks_hz": union,
                     "note": "clean modal multi-reference caches, both drive nodes (D2); samples in g & lbf"}
    (WS / "out" / "modal_cache_summary.json").write_text(json.dumps(summ, indent=2))
    print(f"\nunion modal peaks 45-260 Hz ({len(union)}): {union}")
    print(f"wrote out/modal_cache_summary.json  ({summ['_meta']['runtime_s']}s)")
    return summ


if __name__ == "__main__":
    build_all()
