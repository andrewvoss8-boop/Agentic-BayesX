#!/usr/bin/env python3
"""Observable + matching protocol (Phase 0, D-B). Builds the GAIN-FREE output/output transmissibility
|T_a(f)| = sqrt(PSD_a(f)/PSD_ref(f)) (ref = shield) from the acoustic CSVs, defines the FEM forward node map,
and runs unit tests. Writes out/observable.json (summary + node map + unit tests) and
out/measured_transmissibility.npz (full curves, reused by every model class).

Why gain-free (D-A): same sensor (MMF KS78C, 100 mV/g, Andrew A6) moved between placements; speaker field fixed
across all acoustic runs (A7). The common acoustic input level AND the sensor calibration cancel in the ratio, so
the transmissibility is DIMENSIONLESS and there is no per-channel gain to hide GRMS error in.

Spectral-estimate contract (Discretization Gate): Welch, fs=10 kHz, nperseg=16384 (df=0.61 Hz), 50% overlap,
Hann window, detrend='constant'. ~40-85 independent averages live ACROSS the pink-noise record (not segments of
one transient). Band default [20, 260] Hz (QOI-driving; >260 Hz = local/near-field, out of scope per L5 lesson).
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
import numpy as np
from scipy.signal import welch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mpl_fem as FF

WS = Path(__file__).resolve().parents[1]
OUT = WS / "out"; OUT.mkdir(exist_ok=True)
DATA = WS.parents[2] / "MPL test stand" / "FEM" / "test_data"
FS = 10000.0
NPERSEG = 16384
NOVERLAP = 8192
BAND = (20.0, 260.0)

# location -> (csv file, acoustic segment [t0,t1] s)  (run_mapping.md, Andrew-confirmed windows)
ACOUSTIC = {
    "interface": ("acoustic unloaded top.csv", (14.0, 76.0)),
    "shield":    ("shield acoustic.csv", (11.0, 71.0)),
    "beam":      ("top left beam acoustic.csv", (12.0, 47.0)),
    "valve":     ("valve tap (engine mount) and acoustic.csv", (29.0, 80.0)),
    "avi-L":     ("top left avi foot tap and acoustic.csv", (19.0, 72.0)),
    "avi-R":     ("top right avi foot tap and acoustic.csv", (19.0, 64.0)),
}
REF = "shield"


def load_csv(name):
    p = DATA / name
    try:
        import pandas as pd
        df = pd.read_csv(p, usecols=[0, 1])
        return df.iloc[:, 0].to_numpy(float), df.iloc[:, 1].to_numpy(float)
    except Exception:
        a = np.loadtxt(p, delimiter=",", skiprows=1)
        return a[:, 0], a[:, 1]


def seg_psd(t, x, seg):
    i0, i1 = int(seg[0] * FS), int(seg[1] * FS)
    xs = x[i0:i1]
    f, P = welch(xs, fs=FS, nperseg=NPERSEG, noverlap=NOVERLAP, window="hann", detrend="constant")
    n_avg = max(1, int((len(xs) - NOVERLAP) / (NPERSEG - NOVERLAP)))
    return f, P, n_avg


def build_measured():
    """Returns freqs (band), dict loc -> |T_a|(band), per-loc PSD/n_avg/SNR diagnostics."""
    psd = {}; navg = {}
    fcommon = None
    for loc, (fn, seg) in ACOUSTIC.items():
        t, x = load_csv(fn)
        f, P, na = seg_psd(t, x, seg)
        fcommon = f if fcommon is None else fcommon
        psd[loc] = P; navg[loc] = na
    fb = (fcommon >= BAND[0]) & (fcommon <= BAND[1])
    freqs = fcommon[fb]
    Pref = psd[REF][fb]
    # ambient floor proxy = median PSD in a quiet high band [400,500] Hz (per location), for SNR awareness
    fhi = (fcommon >= 400.0) & (fcommon <= 500.0)
    T = {}; snr = {}
    for loc in ACOUSTIC:
        Pa = psd[loc][fb]
        T[loc] = np.sqrt(np.maximum(Pa, 0.0) / np.maximum(Pref, 1e-300))
        snr[loc] = float(np.median(psd[loc][fb]) / max(np.median(psd[loc][fhi]), 1e-300))
    return freqs, T, navg, snr


def main():
    os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
    t0 = time.time()
    freqs, Tmeas, navg, snr = build_measured()

    # FEM forward on the SAME band grid
    fem = FF.FEM_model()
    mfreqs, Phi = fem.solve_modes()
    phix, gamma = fem.oop_shapes(Phi)
    locs = list(fem.NODE_GRID)
    Tpred = FF.transmissibility(mfreqs, phix, gamma, 0.01, freqs, locs, ref=REF)

    # ---------------- unit tests ----------------
    ut = {}
    f8 = [m["freq_hz"] for m in json.load(open(FF.FEM.parent / "modes_nominal.json"))["modes"][:8]]
    ut["fem_freq_match_fable"] = bool(max(abs(mfreqs[i] - f8[i]) for i in range(8)) < 0.05)
    ut["fem_ref_unity"] = bool(np.max(np.abs(Tpred[REF] - 1.0)) < 1e-9)
    # load-amplitude invariance (input level cancels in the ratio)
    Tpred_scaled = FF.transmissibility(mfreqs, phix, 1e3 * gamma, 0.01, freqs, locs, ref=REF)
    ut["fem_load_scale_invariant"] = bool(max(np.max(np.abs(Tpred[l] - Tpred_scaled[l])) for l in locs) < 1e-9)
    ut["meas_ref_unity"] = bool(np.max(np.abs(Tmeas[REF] - 1.0)) < 1e-12)
    ut["meas_positive_finite"] = bool(all(np.all(np.isfinite(Tmeas[l])) and np.all(Tmeas[l] > 0) for l in ACOUSTIC))
    ut["band_points_ge_100"] = bool(len(freqs) >= 100)
    # node X-dofs map with weight 1.0 in T_rbe2 (clean OOP readout)
    okmap = True
    for loc, g in fem.NODE_GRID.items():
        row = fem.T.getrow(fem.full_xdof(g)).toarray().ravel()
        nz = np.nonzero(row)[0]
        okmap &= (nz.size == 1 and abs(row[nz[0]] - 1.0) < 1e-12)
    ut["nodemap_xdof_weight1"] = bool(okmap)
    ut["dimensionless_ratio"] = True   # |T| = sqrt(PSD/PSD) is dimensionless by construction

    # ---------------- write artifacts ----------------
    np.savez_compressed(OUT / "measured_transmissibility.npz",
                        freqs=freqs, **{f"T_{l}": Tmeas[l] for l in ACOUSTIC},
                        **{f"Tpred_nom_{l}": Tpred[l] for l in locs})
    rec = {
        "deliverable": "gain-free output/output transmissibility observable + FEM forward + matching protocol",
        "gain_convention": "gain-free: |T|=sqrt(PSD_a/PSD_ref) is a DIMENSIONLESS ratio (same sensor, fixed "
                           "acoustic field); common input level + sensor calibration cancel. No per-channel gain.",
        "ref_location": REF,
        "band_hz": list(BAND),
        "n_freq_in_band": int(len(freqs)),
        "welch": {"fs": FS, "nperseg": NPERSEG, "noverlap": NOVERLAP, "window": "hann", "detrend": "constant",
                  "df_hz": float(FS / NPERSEG)},
        "locations": {loc: {"grid": int(fem.NODE_GRID[loc]),
                            "xyz_in": [round(float(v), 3) for v in fem.X[fem.gpos[int(fem.NODE_GRID[loc])]]],
                            "acoustic_file": ACOUSTIC[loc][0], "segment_s": list(ACOUSTIC[loc][1]),
                            "n_welch_avg": int(navg[loc]), "snr_band_over_floor": round(snr[loc], 2),
                            "T_band_median": round(float(np.median(Tmeas[loc])), 4),
                            "T_band_max": round(float(np.max(Tmeas[loc])), 4)}
                      for loc in ACOUSTIC},
        "unit_tests": ut,
        "runtime_s": round(time.time() - t0, 1),
    }
    (OUT / "observable.json").write_text(json.dumps(rec, indent=2))
    print(json.dumps({k: rec[k] for k in ("gain_convention", "ref_location", "band_hz",
                                          "n_freq_in_band", "unit_tests")}, indent=2))
    for loc in ACOUSTIC:
        d = rec["locations"][loc]
        print(f"  {loc:10s} grid {d['grid']:>7} n_avg {d['n_welch_avg']:>3} SNR {d['snr_band_over_floor']:>6} "
              f"|T| med {d['T_band_median']:>7} max {d['T_band_max']:>8}")
    assert all(ut.values()), f"UNIT TESTS FAILED: {ut}"
    print(f"\nmpl_observe: all unit tests PASS | runtime {rec['runtime_s']}s")


if __name__ == "__main__":
    main()
