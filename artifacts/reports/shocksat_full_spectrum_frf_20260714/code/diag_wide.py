#!/usr/bin/env python3
"""diag_wide — the arm-D amplitude compass (card §6 D): TRAIN-side diagnosis from per-channel log|H|
residuals on the wide caches. Card rule: diagnosis reads drives in their TRAIN role only; since theta and
the model are fold-independent, the per-drive residual FIELD is the same object in every fold where that
drive is a train drive — the held-out fold's score is NEVER computed here (scores only via wscore_wide).
Outputs out/diagnosis_r<r>.json:
  - per (structural region x axis x band): n_ch, mean|resid| dex, median channel corr;
  - worst channels (region, axis, band, mean|resid|);
  - matched-peak df% vs survey pairing + extended measured peaks (200-1000 Hz);
  - modal strain-energy fraction per theta group for the paired modes (identifiability quantity
    f_{i,g} = theta_g phi_i^T A_g phi_i / lam_i).
"""
from __future__ import annotations
import json, os, sys
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402
import wscore_wide as SW                       # noqa: E402
import wide_forward as WFW                     # noqa: E402

F = WP.F
BANDS = [("sub200", 45.0, 200.0), ("b200_500", 200.0, 500.0), ("b500_1000", 500.0, 1000.0)]


def channel_regions(pkg):
    """daq -> structural region tag: gfile tag of the node nearest the channel location."""
    m = F.load_model()
    xyz = np.asarray(m["xyz"], float)
    tags = np.asarray(m["gfile"]).astype(str)
    chmap = F.channels_map()
    out = {}
    for d in pkg.sens_daq:
        pt, ax = chmap[d]
        j = int(np.argmin(np.linalg.norm(xyz - np.asarray(pt), axis=1)))
        out[d] = {"region": str(tags[j]).split("/")[-1], "axis": ax}
    return out


def build_diagnosis(pkg, theta, rnd, model_label):
    caches = SW.load_caches()
    reg_of = channel_regions(pkg)
    table = {}
    worst = []
    for dkey in SW.DEV_KEYS:
        c = caches[dkey]
        fc = c["freqs"]
        logHp = np.log10(np.abs(WFW.predict_H(pkg, theta, dkey, fc, windowed=True)) + 1e-300)
        rows, cols = SW._usable(pkg, c, c["band"])
        ym_all = np.log10(np.abs(c["H1"]) + 1e-300)
        off = float(np.mean(ym_all[cols][:, c["band"]] - logHp[rows][:, c["band"]]))
        for r, ci in zip(rows, cols):
            d = c["daq"][ci]
            reg, ax = reg_of[d]["region"], reg_of[d]["axis"]
            for bn, lo, hi in BANDS:
                bm = (fc >= lo) & (fc < min(hi, c["top"])) & c["band"]
                if bm.sum() < 8:
                    continue
                resid = ym_all[ci][bm] - logHp[r][bm] - off
                corr = float(np.corrcoef(logHp[r][bm], ym_all[ci][bm])[0, 1])
                key = f"{reg}|{ax}|{bn}"
                t = table.setdefault(key, {"n": 0, "sum_abs": 0.0, "corrs": []})
                t["n"] += 1
                t["sum_abs"] += float(np.mean(np.abs(resid)))
                t["corrs"].append(corr)
                worst.append({"drive": dkey, "daq": int(d), "region": reg, "axis": ax, "band": bn,
                              "mean_abs_resid_dex": round(float(np.mean(np.abs(resid))), 3),
                              "corr": round(corr, 3)})
    summary = {k: {"n_ch_drive": v["n"], "mean_abs_resid_dex": round(v["sum_abs"] / v["n"], 3),
                   "median_corr": round(float(np.median(v["corrs"])), 3)}
               for k, v in sorted(table.items())}
    worst = sorted(worst, key=lambda w: -w["mean_abs_resid_dex"])[:25]
    # matched-peak df% (survey pairing)
    f_el, _ = pkg.modes(theta)
    pairs = np.asarray(pkg.pairs)
    mfreqs = np.asarray(pkg.mfreqs, float)
    peak_df = [{"f_test": round(float(mfreqs[int(r)]), 1), "f_model": round(float(f_el[int(k)]), 1),
                "df_pct": round(100 * (f_el[int(k)] / mfreqs[int(r)] - 1), 2), "mac": round(float(mc), 3)}
               for r, k, mc in pairs if mc >= 0.3]
    # extended peaks vs model modes
    ext = json.load(open(os.path.join(WS, "out", "extended_peaks.json")))
    ext_match = []
    for cl in ext["clusters"]:
        if not cl["measured_3plus"]:
            continue
        hz = cl["hz_mean"]
        k = int(np.argmin(np.abs(f_el - hz)))
        ext_match.append({"f_meas": hz, "f_model_nearest": round(float(f_el[k]), 1),
                          "df_pct": round(100 * (f_el[k] / hz - 1), 2)})
    # strain-energy fractions per group for paired modes
    A = np.asarray(pkg.A)
    K = np.asarray(pkg.A_fix) + np.einsum("g,gij->ij", np.asarray(theta), A)
    lam, Q = np.linalg.eigh(K)
    se = {}
    for r, k, mc in pairs:
        if mc < 0.3:
            continue
        q = Q[:, int(k)]
        fr = {g: float(theta[gi] * q @ A[gi] @ q / max(lam[int(k)], 1e-9))
              for gi, g in enumerate(pkg.free_names)}
        se[f"{mfreqs[int(r)]:.1f}Hz"] = {g: round(v, 3) for g, v in
                                         sorted(fr.items(), key=lambda x: -x[1])[:4]}
    out = {"round": rnd, "model": model_label, "region_axis_band": summary, "worst_channels": worst,
           "survey_peak_df": peak_df, "extended_peak_match": ext_match, "strain_energy_top4": se,
           "note": "TRAIN-side residual fields; no fold dev scores computed here"}
    p = os.path.join(WS, "out", f"diagnosis_r{rnd}.json")
    json.dump(out, open(p, "w"), indent=1)
    print(f"diagnosis r{rnd} written ({len(summary)} region-axis-band cells)")
    return out


if __name__ == "__main__":
    rnd = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    cid = sys.argv[2] if len(sys.argv) > 2 else "A0_wide"
    pkg = WP.load(cid)
    tm = os.path.join(WS, "out", "theta_maps.json")
    if cid == "A0_wide":
        theta = np.asarray(json.load(open(os.path.join(WS, "out", "theta_map_wide.json")))["theta_map_vec"])
    elif os.path.exists(tm) and cid in json.load(open(tm)):
        theta = np.asarray(json.load(open(tm))[cid]["theta"])       # candidate's own multi-start MAP
    else:
        theta, _, _ = pkg.theta_map()
    build_diagnosis(pkg, theta, rnd, cid)
