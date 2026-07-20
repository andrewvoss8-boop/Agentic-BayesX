#!/usr/bin/env python3
"""Card G Part B — MECHANISM: does multi-reference break the participation÷damping confound? (deterministic)

Theory: at a resonance of mode k, |H_{s,k}(d)| ∝ φ_{s,k}·φ_{d,k}/ζ_k. The cross-reference RATIO
    R_meas(s,k; d1,d2) = |H_{s,k}(d1)| / |H_{s,k}(d2)| = φ_{d1,k}/φ_{d2,k}
is INDEPENDENT of the sensor s AND of the damping ζ_k — a pure drive-participation ratio. So if multi-reference data
is good, this measured ratio should (a) be ~constant across sensors s (the φ_s and ζ cancel) and (b) match the FEM
drive ratio |φ_{d1,k}|/|φ_{d2,k}| = |drive_row(d1)·Q_k| / |drive_row(d2)·Q_k|. Recovering it = the confound is broken
(we have isolated φ_d from φ_s and ζ); failing it (scatter across s, no FEM match) = the data cannot break it here.

Two readouts:
  - sensor-independence: CoV (std/mean of log-ratio) of R_meas across sensors at each (mode, pair) — small ⇒ clean.
  - FEM agreement: Spearman/Pearson corr of median_s log R_meas(k) vs log R_FEM(k) over excited modes — high ⇒ the
    measured drive-shape ratio recovers the predicted one.
Only modes EXCITED in BOTH references (peak above the coherence/amplitude floor) are used; a drive on a mode's node
line does not excite it. Reported per reference PAIR, and weighted by at-resonance coherence (data quality).

Output: out/drive_shape_ratio.json.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
from itertools import combinations
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import multiref_frf as mrf

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; MULTIREF = WS / "data" / "multiref"
NCOMMON = 65536
COH_MIN = 0.5            # use a sensor at a mode only if both references' at-resonance coherence exceeds this
PEAK_TOL_HZ = 6.0        # local-peak search half-window around a matched resonance


def _local_peak(freqs, mag, f0, tol=PEAK_TOL_HZ):
    m = np.abs(freqs - f0) <= tol
    if not m.any():
        return None, None
    idx = np.where(m)[0]
    j = idx[int(np.argmax(mag[idx]))]
    return float(mag[j]), int(j)


def run():
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    meas_f, _ = mf.extract_measured_modes(meas, ch)
    pairs, _ = mf.match(R, meas_f)
    mode_idx = [int(p[0]) for p in pairs]; res_hz = [float(p[1]) for p in pairs]
    # FEM modes at theta=1
    K = R.A_fix + R.A.sum(0); lam, Q = np.linalg.eigh(K)

    # load N=65536 caches; align daq order (caches built on ch.daq)
    refs = {}
    for key in mrf.REFS:
        p = MULTIREF / f"{key}_N{NCOMMON}.npz"
        if not p.exists():
            continue
        z = mrf.load_cache(p)
        refs[key] = {"freqs": z["freqs"], "H1": z["H1"], "coh": z["coherence"], "daq": list(z["daq"].tolist()),
                     "axis": str(z["axis"]), "instrument": str(z["instrument"]), "n_hits": int(z["n_hits_used"]),
                     "label": str(z["label"])}
        # drive participation per FEM mode: drive_row(xyz,axis) @ Q
        drow, _, _ = R.reduced_row(tuple(mrf.REFS[key]["xyz"]), mrf.REFS[key]["axis"])
        refs[key]["phi_d"] = drow @ Q              # (74,) modal drive participations
    keys = list(refs.keys())
    # common sensor order = ch.daq positions present in all caches (they all used ch.daq, so identical)
    base_daq = refs[keys[0]]["daq"]
    n_sensors = len(base_daq)

    out = {"deliverable": "drive-shape-ratio mechanism: does |H(d1)|/|H(d2)| recover phi_d ratio (sensor- & zeta-free)?",
           "common_N": NCOMMON, "coh_min": COH_MIN, "n_matched_modes": len(mode_idx),
           "references": {k: {"label": refs[k]["label"], "instrument": refs[k]["instrument"],
                              "n_hits": refs[k]["n_hits"]} for k in keys}, "pairs": {}}

    all_corr = []
    for d1, d2 in combinations(keys, 2):
        A, B = refs[d1], refs[d2]
        log_meas_med, log_fem, mode_cov, n_sens_used, coh_pair = [], [], [], [], []
        for mi, (mj, f0) in enumerate(zip(mode_idx, res_hz)):
            phi1 = float(A["phi_d"][mj]); phi2 = float(B["phi_d"][mj])
            if abs(phi2) < 1e-12:
                continue
            rfem = abs(phi1) / abs(phi2)
            ratios, used = [], 0
            for si in range(n_sensors):
                m1, j1 = _local_peak(A["freqs"], np.abs(A["H1"][si]), f0)
                m2, j2 = _local_peak(B["freqs"], np.abs(B["H1"][si]), f0)
                if m1 is None or m2 is None or m2 <= 0 or m1 <= 0:
                    continue
                c1 = float(A["coh"][si, j1]); c2 = float(B["coh"][si, j2])
                if c1 < COH_MIN or c2 < COH_MIN:
                    continue
                ratios.append(np.log(m1 / m2)); used += 1
            if used >= 4:                          # need a few coherent sensors to assess sensor-independence
                lr = np.array(ratios)
                log_meas_med.append(float(np.median(lr)))
                log_fem.append(float(np.log(rfem)))
                mode_cov.append(float(np.std(lr)))     # spread across sensors (small ⇒ sensor-independent)
                n_sens_used.append(used)
        npts = len(log_meas_med)
        entry = {"label_pair": f"{A['label']}/{B['label']}",
                 "instrument_pair": f"{A['instrument']}/{B['instrument']}",
                 "n_modes_excited_both": npts,
                 "median_sensor_spread_log": (float(np.median(mode_cov)) if npts else None),
                 "median_n_sensors_per_mode": (float(np.median(n_sens_used)) if npts else None)}
        if npts >= 4:
            lm = np.array(log_meas_med); lf = np.array(log_fem)
            entry["pearson_logratio_meas_vs_fem"] = float(np.corrcoef(lm, lf)[0, 1])
            from scipy.stats import spearmanr
            entry["spearman_logratio_meas_vs_fem"] = float(spearmanr(lm, lf).correlation)
            # how well sensor-independent vs the spread you'd get from noise: compare sensor-spread to ratio range
            entry["fem_logratio_range"] = float(lf.max() - lf.min())
            all_corr.append((entry["instrument_pair"], entry["pearson_logratio_meas_vs_fem"], npts))
        out["pairs"][f"{d1}__{d2}"] = entry

    # headline: best impact-impact pair and best any pair; clean (modal-involving) pair noted separately
    imp = [(p, c, n) for (p, c, n) in all_corr if "impact/impact" in p]
    out["corr_meas_vs_fem_ratio"] = (float(np.median([c for _, c, _ in all_corr])) if all_corr else None)
    out["best_pair_corr"] = (max([c for _, c, _ in all_corr]) if all_corr else None)
    out["impact_impact_pairs_corr"] = imp
    out["interpretation"] = (
        "High corr + small sensor-spread ⇒ the cross-reference peak ratio recovers the FEM drive-participation ratio "
        "independent of sensor and damping = the confound is breakable from this data. Near-zero corr / large "
        "sensor-spread (expected where at-resonance coherence is near the noise floor) ⇒ the impact data cannot break "
        "it; only clean (modal-hammer-involving) pairs can.")
    out["runtime_s"] = time.time() - t0
    OUT.mkdir(exist_ok=True)
    (OUT / "drive_shape_ratio.json").write_text(json.dumps(out, indent=2))
    print(f"drive-shape-ratio mechanism ({out['runtime_s']:.0f}s): median corr {out['corr_meas_vs_fem_ratio']}, "
          f"best {out['best_pair_corr']}")
    for k, e in out["pairs"].items():
        print(f"  {e['label_pair']:10s} ({e['instrument_pair']}): modes {e['n_modes_excited_both']}, "
              f"corr {e.get('pearson_logratio_meas_vs_fem')}, sensor-spread {e.get('median_sensor_spread_log')}")
    return out


if __name__ == "__main__":
    run()
