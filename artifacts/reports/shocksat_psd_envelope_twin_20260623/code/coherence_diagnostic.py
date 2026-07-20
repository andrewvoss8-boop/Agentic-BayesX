#!/usr/bin/env python3
"""Card G Part B step 0 — DATA-QUALITY diagnostic (cheap; contextualises every amplitude verdict, never a stop).

For each reference (+X/+Z/+Y/900z) builds the multi-hit ensemble FRF (realfrf-identical N=200000 windowing) and
reports COHERENCE — overall in-band, and crucially AT THE MODAL RESONANCES (the consensus matched mode frequencies,
where the peak-amplitude QOI lives) — at the drive-point accel and the 8 hard accels.

Two coherence estimates per reference (both reported; few-hit coherence is upward-biased, floor ≈ 1/n_hits):
  - N=200000 (df 1.25 Hz): identical window to +X/Card-A (the apples-to-apples processing); fewer fitting hits.
  - N=65536  (df 3.81 Hz): more fitting hits → lower floor, more reliable; resolves modes (spacing ≥10 Hz).
Plus a Welch broadband estimate (matches the documented +X "~0.07" 100-10 kHz manifest number) for context.

Saves the matched N=200000 ensemble FRF per reference to data/multiref/<key>.npz (used by mechanism + calibration).
Output: out/coherence_by_reference.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
from types import SimpleNamespace
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import multiref_frf as mrf

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; OUT.mkdir(exist_ok=True)
MULTIREF = WS / "data" / "multiref"; MULTIREF.mkdir(parents=True, exist_ok=True)
HARD = [4, 27, 38, 40, 52, 69, 92, 98]
# documented +X 4-hit Welch coherence (hammer_frf_subset_manifest.json; broadband 100-10k Hz, the "~0.07" headline)
XPLUS_MANIFEST = WS.parent / "shocksat_statfem_runner_20260609" / "hammer_frf_subset_manifest.json"


def _coh_at(freqs, coh_row, targets, tol=2.0):
    """Median coherence at the nearest bin to each target resonance freq (within tol Hz)."""
    vals = []
    for t in targets:
        k = int(np.argmin(np.abs(freqs - t)))
        if abs(freqs[k] - t) <= tol:
            vals.append(float(coh_row[k]))
    return vals


def run():
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    # consensus resonance frequencies (reference-invariant; from the +X cache) matched to FEM modes
    meas_f, _ = mf.extract_measured_modes(meas, ch)
    pairs, _ = mf.match(R, meas_f)
    res_hz = sorted(float(p[1]) for p in pairs)
    daq_to_pos = {d: i for i, d in enumerate(ch.daq)}

    rec = {"deliverable": "per-reference coherence diagnostic (data quality), evaluated AT modal resonances",
           "resonance_freqs_hz": [round(x, 1) for x in res_hz], "hard_accels": HARD, "references": {}}

    for key, ref in mrf.REFS.items():
        entry = {"label": ref["label"], "axis": ref["axis"], "instrument": ref["instrument"],
                 "drive_xyz": list(ref["xyz"]), "note": ref["note"]}
        # drive-point accel = nearest mapped accel to the drive xyz
        dist = np.linalg.norm(ch.coords - np.array(ref["xyz"]), axis=1)
        dp_pos = int(np.argmin(dist)); dp_daq = int(ch.daq[dp_pos])
        entry["drivepoint_accel_daq"] = dp_daq; entry["drivepoint_snap_in"] = float(dist[dp_pos])

        built = {}
        for N in (200000, 65536):
            b = mrf.build_reference(key, daqs=ch.daq, N=N)
            if b is None or b.get("n_hits_used", 0) == 0:
                entry[f"N{N}"] = {"n_hits_used": 0 if b is None else b.get("n_hits_used", 0),
                                  "n_hits_skipped": None if b is None else b.get("n_hits_skipped")}
                continue
            built[N] = b
            freqs = b["freqs"]; coh = b["coherence"]; daq = list(b["daq"])
            pos = {int(d): i for i, d in enumerate(daq)}
            # at-resonance coherence rows
            dp_res = _coh_at(freqs, coh[pos[dp_daq]], res_hz) if dp_daq in pos else []
            hard_res = {}
            for hd in HARD:
                if hd in pos:
                    v = _coh_at(freqs, coh[pos[hd]], res_hz)
                    if v:
                        hard_res[str(hd)] = float(np.median(v))
            all_res = []
            for i in range(coh.shape[0]):
                all_res += _coh_at(freqs, coh[i], res_hz)
            entry[f"N{N}"] = {
                "n_hits_used": b["n_hits_used"], "n_hits_skipped": b["n_hits_skipped"],
                "coh_floor_uncorrelated": round(b["coh_floor_uncorrelated"], 3), "df_hz": round(b["df_hz"], 3),
                "coherence_median_inband": float(np.median(coh)),
                "coherence_at_resonance_median": float(np.median(all_res)) if all_res else None,
                "coherence_at_resonance_p90": float(np.percentile(all_res, 90)) if all_res else None,
                "drivepoint_at_resonance_median": float(np.median(dp_res)) if dp_res else None,
                "hard_accels_at_resonance_median": hard_res,
                "welch": b.get("welch")}
        # headline band-median coherence for the checker (prefer the lower-floor N=65536 estimate)
        primary = built.get(65536) or built.get(200000)
        entry["coherence_median_band"] = (float(np.median(primary["coherence"])) if primary else None)
        entry["at_resonance_p90_primary"] = entry.get("N65536", {}).get("coherence_at_resonance_p90") \
            if "N65536" in entry else entry.get("N200000", {}).get("coherence_at_resonance_p90")
        # save the matched N=200000 ensemble FRF for mechanism/calibration
        if 200000 in built:
            mrf.save_cache(built[200000], MULTIREF / f"{key}.npz")
            entry["frf_cache"] = f"data/multiref/{key}.npz"
        rec["references"][key] = entry
        print(f"{key} ({ref['label']}, {ref['instrument']}): "
              f"N200000 hits {entry.get('N200000',{}).get('n_hits_used')}, N65536 hits {entry.get('N65536',{}).get('n_hits_used')} | "
              f"at-resonance coh median {entry.get('N65536',{}).get('coherence_at_resonance_median')}, "
              f"p90 {entry.get('N65536',{}).get('coherence_at_resonance_p90')}, "
              f"drivepoint {entry.get('N65536',{}).get('drivepoint_at_resonance_median')}")

    # documented +X manifest broadband number for context
    if XPLUS_MANIFEST.exists():
        try:
            man = json.loads(XPLUS_MANIFEST.read_text())
            rec["xplus_manifest_note"] = {
                "source": "hammer_frf_subset_manifest.json (Test07 +X, 4 hits, Welch)",
                "processing": man.get("processing", {}).get("frequency_band_reported_hz"),
                "acceptance_note": man.get("processing", {}).get("acceptance_note")}
        except Exception:
            pass
    rec["interpretation"] = (
        "Broadband/Welch coherence is low (the documented +X ~0.07 is a 100-10 kHz number, dominated by bands with no "
        "hammer energy). The relevant metric for the modal-amplitude QOI is coherence AT the resonances: read the "
        "at_resonance_p90 / drivepoint values against the few-hit floor (1/n_hits). High at-resonance coherence ⇒ the "
        "confound-break has signal; near-floor ⇒ data-quality ceiling (verdict ii).")
    rec["runtime_s"] = time.time() - t0
    (OUT / "coherence_by_reference.json").write_text(json.dumps(rec, indent=2))
    print(f"\nwrote coherence_by_reference.json ({rec['runtime_s']:.0f}s)")
    return rec


if __name__ == "__main__":
    run()
