#!/usr/bin/env python3
"""EXPLORATORY: fixed-PHYSICAL-damping re-score. Take the ERA-measured band zeta (~0.3%, from raw Test07 time
histories) and use it as FIXED damping in the frozen forward model; re-score held-out dev FRF. Asks: does
physically-correct damping (from raw data) beat A0's 1% and the 2 Hz FRF-fit's railed ~2-5% on held-out
prediction? Read-only: reuses the frf_damping workspace's femdamp/score HELPERS but writes NOTHING to its
query_log (the completed run is SHA-frozen)."""
import os, sys, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
WS = os.path.join(ROOT, "artifacts/reports/shocksat_frf_damping_updating_20260710")
sys.path.insert(0, os.path.join(WS, "code"))
import femdamp as D            # sets F.WS -> the frf_damping workspace (has the _enr packages)
import femlib as F
import metrics as MET
import score as SC

era = np.load(os.path.join(HERE, "era_result.npz"))
band_zeta = [float(z) for z in era["band_zeta"]]
print("ERA physical band zeta [%]:", [round(z * 100, 3) for z in band_zeta])


def score_fixed(cid, damping):
    """Held-out LODO P1'/P3/P2' for a package + damping spec, WITHOUT logging (mirrors score.score_candidate
    math)."""
    pkg = F.Package.load(cid)
    theta = np.asarray(pkg.theta_map()[0], float)
    caches = SC.load_caches()
    P1, P3, P2 = [], [], []
    for dev_key in F.DRIVE_KEYS:
        train = [k for k in F.DRIVE_KEYS if k != dev_key]
        rho, band_mask = SC._train_warp(pkg, theta, damping, train, caches)
        # global gain from train
        offs = []
        for tk in train:
            c = caches[tk]; rows, cols = SC._usable(pkg, c)
            if len(rows) == 0:
                continue
            lp = D.predict_logH_damped(pkg, theta, damping, tk, c["freqs"])[rows][:, c["band"]]
            ym = np.log10(np.abs(c["H1"][cols][:, c["band"]]) + 1e-300)
            offs.append(float(np.mean(ym - lp)))
        gain_db = 20.0 * float(np.mean(offs)) if offs else 0.0
        c = caches[dev_key]; fc = c["freqs"]; band = c["band"]
        rows, cols = SC._usable(pkg, c)
        logHp = D.predict_logH_damped(pkg, theta, damping, dev_key, fc)
        sel = band & band_mask if band_mask.shape[0] == len(fc) else band
        pk = [b for b in SC._matched_peak_bins(pkg, theta, fc) if sel[b]]
        p1s, p3s, p2s = [], [], []
        for r, cidx in zip(rows, cols):
            ym = np.log10(np.abs(c["H1"][cidx][band]) + 1e-300)
            p3 = MET.frac_corr(logHp[r][band], ym)
            if not np.isnan(p3):
                p3s.append(p3)
            ypw = MET.apply_scale_warp(logHp[r], fc, rho)
            p1 = MET.frac_corr(ypw[sel], np.log10(np.abs(c["H1"][cidx][sel]) + 1e-300))
            if not np.isnan(p1):
                p1s.append(p1)
            if pk:
                p2s.append(MET.frsf(10.0 ** (ypw[pk] + gain_db / 20.0), np.abs(c["H1"][cidx][pk]))[2])
        P1.append(np.median(p1s)); P3.append(np.median(p3s)); P2.append(np.median(p2s) if p2s else np.nan)
    return float(np.nanmean(P1)), float(np.nanmean(P3)), float(np.nanmean(P2))


specs = {
    "A0 (fixed 1%)":         ("A0_enr", {"kind": "fixed", "zeta": 0.01}),
    "A0d (FRF-fit ~2-5%)":   ("A0_enr", json.load(open(os.path.join(WS, "out", "a0d.json")))["best_damping"]),
    "A0 + ERA physical zeta":("A0_enr", {"kind": "band", "zeta": band_zeta}),
    "c06 (fixed 1%)":        ("c06_tb_xface_enr", {"kind": "fixed", "zeta": 0.01}),
    "c06 + ERA physical zeta":("c06_tb_xface_enr", {"kind": "band", "zeta": band_zeta}),
}
print("\n%-26s  %-8s %-8s %-8s" % ("arm", "P1'", "P3", "P2'(|FRSF-1|)"))
res = {}
for label, (cid, dmp) in specs.items():
    p1, p3, p2 = score_fixed(cid, dmp)
    res[label] = (p1, p3, p2)
    print("%-26s  %-8.4f %-8.4f %-8.4f" % (label, p1, p3, p2))

a0 = res["A0 (fixed 1%)"]
print("\n--- deltas vs A0 (fixed 1%) ---")
for label in ["A0d (FRF-fit ~2-5%)", "A0 + ERA physical zeta"]:
    d1 = res[label][0] - a0[0]; d2 = res[label][2] - a0[2]
    print("%-26s  dP1'=%+.4f   dP2'(amp)=%+.4f" % (label, d1, d2))
print("\nP2' is |FRSF-1| (amplitude error) — LOWER is better; P1' is FDAC-aligned FRAC — HIGHER is better.")
