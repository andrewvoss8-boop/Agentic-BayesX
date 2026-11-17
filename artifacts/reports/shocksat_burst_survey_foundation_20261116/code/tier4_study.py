#!/usr/bin/env python3
"""Pre-registered scoring of NASA's 264 test-versus-FEM FRF plots (tier 4 of the fetch
plan). Rules are fixed in prereg_gated_analysis.md; do not change them after any of
the 264 plots has been seen.

Usage:
  tier4_study.py --plots DIR     DIR holds 11101X_Impact_Comparison/ and 11110Y_Impact_Comparison/
  tier4_study.py --dry-run       synthetic NASA-style plots with known answers (pipeline test)

Per plot (file Acceleration_<node><axis><sign>.png):
 1. digitise the magnitude panel (digitize_frf.py): black = test, red = NASA FEM;
    legend region = bottom 13 % x right 25 % of the panel (only data above ~300 Hz);
 2. x calibration from the 50 Hz gridlines; y calibration provisional (decade labels are
    not read); the test-minus-FEM metric does not depend on the y anchor;
 3. M1 per curve: median over 46.79-258.38 Hz of |20 log10(test/NASA FEM)| after both
    curves are power-averaged over 2.03 Hz (the line spacing of the project's shock caches);
 4. M2 per curve: same against the frozen project FEM, after the plot's absolute level is
    fixed by rounding to a whole decade the median offset between the project FEM and the
    digitised NASA FEM over 12-40 Hz (mass-controlled region below the first mode);
 5. QA gate (content-free): gridline-fit residual <= 1 px, panel edges at 10 and 400 Hz
    within 1 Hz, clipped fraction in band <= 0.10. M2 additionally needs an anchor residual
    <= 0.1 decade. Diagnostic only: distance of the nearest test peak to 54.19 Hz.
Aggregate: median over curves, 95 % interval by bootstrap over response nodes (2000
resamples, seed 20261117). Confirmatory set excludes the two drive-point curves shown in
NASA's deck (seen before registration).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import digitize_frf as dg  # noqa: E402
import fem_frf  # noqa: E402

BAND = (46.79, 258.38)
SMOOTH_HZ = 2.0345
ANCHOR_BAND = (12.0, 40.0)
SEEN = {("11101X", 11101, "X"), ("11110Y", 11110, "Y")}
DRIVES = {"11101X": (11101, "X"), "11110Y": (11110, "Y")}
NAME = re.compile(r"Acceleration_(\d+)([XYZ])([+-])\.png$")
THRESH = {"supported_m1_db": 6.0, "not_supported_m1_db": 8.0, "ci_upper_for_supported_db": 8.0}


def score_plot(path, fem, drive_key, zeta, legend_frac=(0.13, 0.25)):
    m = NAME.search(os.path.basename(path))
    node, axis = int(m.group(1)), m.group(2)
    im = dg.load_rgb(path)
    r0, r1, c0, c1 = dg.find_panel(im)
    mid = (r0 + r1) // 2
    # provisional y anchor: the detected gridline nearest the panel middle is called 10^0
    sub = im[r0:r1 + 1, c0:c1 + 1]
    h = [r + r0 for r in dg._grid_lines(sub, axis=0) if 3 < r < (r1 - r0) - 3]
    anchor_row = min(h, key=lambda r: abs(r - mid))
    cal = dg.calibrate(im, 50.0, 50.0, 0.0, anchor_row)
    leg = (int(cal.r1 - legend_frac[0] * (cal.r1 - cal.r0)), cal.r1, int(cal.c1 - legend_frac[1] * (cal.c1 - cal.c0)), cal.c1)
    cv = dg.extract(im, cal, {"test": "black", "fem": "red"}, exclude_boxes=[leg])
    ft = dg.classify_gaps(cv, "test", "fem")
    ff = dg.classify_gaps(cv, "fem", "test")
    f = cv["test"]["f_hz"]
    t, n = cv["test"]["log10_centre"], cv["fem"]["log10_centre"]
    ts, ns = dg.band_smooth_power(f, t, SMOOTH_HZ), dg.band_smooth_power(f, n, SMOOTH_HZ)
    m1 = dg.compare(f, ts, ns, *BAND)
    out = {"drive": drive_key, "node": node, "axis": axis, "file": os.path.basename(path),
           "m1_median_abs_db": m1["median_abs_db"], "m1_corr_log": m1["corr_log"], "m1_n": m1["n_points"],
           "calib_resid_px": max(cal.x_fit_resid_px, cal.y_fit_resid_px)}
    b = (f >= BAND[0]) & (f <= BAND[1])
    out["clipped_frac"] = float((ft["clipped"] | ff["clipped"])[b].mean())
    pk = [float(f[i]) for i in range(5, len(f) - 5)
          if 50 < f[i] < 60 and not np.isnan(cv["test"]["log10_top"][i])
          and cv["test"]["log10_top"][i] >= np.nanmax(cv["test"]["log10_top"][i - 5:i + 6])]
    out["freq_check_err_hz"] = float(min(abs(p - 54.19) for p in pk)) if pk else float("nan")
    # M2: absolute level from the project FEM in the mass-controlled band
    drv = DRIVES[drive_key]
    if fem.is_measured(node, axis):
        proj = fem.column_mean_log10(f, cal.hz_per_px, (node, axis), drv, zeta)
        a = (f >= ANCHOR_BAND[0]) & (f <= ANCHOR_BAND[1]) & ~np.isnan(n)
        off = float(np.median(proj[a] - n[a])) if a.sum() > 10 else float("nan")
        k = round(off) if np.isfinite(off) else 0
        out["anchor_offset_decades"] = off
        out["anchor_residual_decades"] = off - k if np.isfinite(off) else float("nan")
        m2 = dg.compare(f, dg.band_smooth_power(f, t + k, SMOOTH_HZ), dg.band_smooth_power(f, proj, SMOOTH_HZ), *BAND)
        out["m2_median_abs_db"] = m2["median_abs_db"]
        out["m2_corr_log"] = m2["corr_log"]
        nasa_vs_proj = dg.compare(f, dg.band_smooth_power(f, n + k, SMOOTH_HZ), dg.band_smooth_power(f, proj, SMOOTH_HZ), *BAND)
        out["nasa_fem_vs_project_fem_median_abs_db"] = nasa_vs_proj["median_abs_db"]
    out["axis_edges_hz"] = [float(cal.col_to_hz(cal.c0)), float(cal.col_to_hz(cal.c1))]
    # QA gate is content-free: gridline fit, axis extent 10-400 Hz, clipping. The 54.19 Hz
    # peak check is a reported diagnostic only (a response on a node line of mode 1 has no peak).
    out["qa_pass"] = bool(out["calib_resid_px"] <= 1.0 and out["clipped_frac"] <= 0.10
                          and abs(out["axis_edges_hz"][0] - 10.0) <= 1.0 and abs(out["axis_edges_hz"][1] - 400.0) <= 1.0)
    out["anchor_pass"] = bool(np.isfinite(out.get("anchor_residual_decades", np.nan)) and abs(out["anchor_residual_decades"]) <= 0.1)
    return out


def boot_median(vals, groups, n=2000, seed=20261117):
    vals, groups = np.asarray(vals, float), np.asarray(groups)
    ug = np.unique(groups)
    idx = {g: np.where(groups == g)[0] for g in ug}
    rng = np.random.default_rng(seed)
    meds = []
    for _ in range(n):
        pick = rng.choice(ug, len(ug), replace=True)
        meds.append(np.median(np.concatenate([vals[idx[g]] for g in pick])))
    return [float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))]


def aggregate(rows):
    conf = [r for r in rows if (r["drive"], r["node"], r["axis"]) not in SEEN and r["qa_pass"]]
    res = {"n_plots": len(rows), "n_confirmatory_after_qa": len(conf),
           "n_excluded_qa": sum(1 for r in rows if not r["qa_pass"]),
           "n_excluded_seen": sum(1 for r in rows if (r["drive"], r["node"], r["axis"]) in SEEN)}
    if not conf:
        res["verdict"] = "NO_DATA"
        return res
    v = [r["m1_median_abs_db"] for r in conf]
    g = [r["node"] for r in conf]
    m1 = float(np.median(v))
    ci = boot_median(v, g)
    res["M1_median_db"] = m1
    res["M1_ci95_db"] = ci
    res["M1_corr_median"] = float(np.median([r["m1_corr_log"] for r in conf]))
    c2 = [r for r in conf if r.get("anchor_pass")]
    if c2:
        res["M2_median_db"] = float(np.median([r["m2_median_abs_db"] for r in c2]))
        res["M2_ci95_db"] = boot_median([r["m2_median_abs_db"] for r in c2], [r["node"] for r in c2])
        res["M2_n"] = len(c2)
        res["nasa_fem_vs_project_fem_median_db"] = float(np.median([r["nasa_fem_vs_project_fem_median_abs_db"] for r in c2]))
    if m1 <= THRESH["supported_m1_db"] and ci[1] < THRESH["ci_upper_for_supported_db"]:
        res["verdict"] = "SUPPORTED"
    elif m1 >= THRESH["not_supported_m1_db"]:
        res["verdict"] = "NOT_SUPPORTED"
    else:
        res["verdict"] = "INCONCLUSIVE"
    return res


def run(plots_dir, zeta_rule="measured_interp"):
    fem = fem_frf.FEM()
    zeta = fem.zeta(zeta_rule)
    rows = []
    for dk in DRIVES:
        d = os.path.join(plots_dir, f"{dk}_Impact_Comparison")
        for fn in sorted(os.listdir(d)):
            if NAME.search(fn):
                try:
                    rows.append(score_plot(os.path.join(d, fn), fem, dk, zeta))
                except Exception as exc:  # recorded, never silently dropped
                    rows.append({"drive": dk, "file": fn, "error": repr(exc), "qa_pass": False, "node": -1, "axis": "?"})
    return rows, aggregate([r for r in rows if "error" not in r])


def dry_run(n_per_drive=6, seed=7):
    """Synthetic NASA-style plots: 'FEM' = frozen project FEM with zeta 0.01, 'test' = the
    same FEM with every mode shifted by a random +-4 % and its residue scaled by a random
    factor (log-normal, sd 0.2 decade). Known answer = M1 computed from the true curves."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fem = fem_frf.FEM()
    rng = np.random.default_rng(seed)
    tmp = tempfile.mkdtemp(prefix="tier4_dry_")
    truth = {}
    resp = [(n, a) for n in fem.nodes for a in "XYZ" if fem.is_measured(n, a)]
    for dk, drv in DRIVES.items():
        os.makedirs(os.path.join(tmp, f"{dk}_Impact_Comparison"))
        for (node, ax) in [resp[i] for i in rng.choice(len(resp), n_per_drive, replace=False)]:
            f = np.linspace(10, 400, 39001)
            zf = fem.zeta("constant", 0.01)
            hf = fem.accelerance(f, (node, ax), drv, zf)
            # perturbed "test": shift each mode, scale residues
            V0, wn0 = fem.V.copy(), fem.wn.copy()
            fem.wn = wn0 * (1 + rng.uniform(-0.04, 0.04, len(wn0))) * (fem.fn > 5) + wn0 * (fem.fn <= 5)
            s = 10 ** rng.normal(0, 0.2, len(wn0))
            fem.V = V0 * np.sqrt(s)[None, :]
            ht = fem.accelerance(f, (node, ax), drv, fem.zeta("measured_interp"))
            fem.V, fem.wn = V0, wn0
            lo = np.floor(np.log10(min(ht.min(), hf.min()))) - 0.3
            hi = np.ceil(np.log10(max(ht.max(), hf.max()))) + 0.1
            fig = plt.figure(figsize=(12.19, 9.14), dpi=100, facecolor=(240 / 255,) * 3)
            ax_ = fig.add_axes([0.08, 0.07, 0.895, 0.667], facecolor="white")
            ax_.semilogy(f, ht, color="black", lw=1.1, label="Test")
            ax_.semilogy(f, hf, color=(1, 0, 0), lw=1.1, label="FEM")
            ax_.set_xlim(10, 400); ax_.set_ylim(10 ** lo, 10 ** hi)
            ax_.set_xticks(np.arange(50, 401, 50))
            ax_.grid(True, which="major", color=(226 / 255,) * 3, lw=0.8); ax_.set_axisbelow(True)
            ax_.legend(loc="lower right", frameon=True, edgecolor="black", fancybox=False)
            fn = f"Acceleration_{node}{ax}+.png"
            fig.savefig(os.path.join(tmp, f"{dk}_Impact_Comparison", fn), dpi=100, facecolor=fig.get_facecolor())
            plt.close(fig)
            # truth on a fine grid: smooth |H|^2 over 2.03 Hz then median |dB| in band
            ff = np.arange(BAND[0] - 2, BAND[1] + 2, 0.02)
            pt = np.interp(ff, f, ht) ** 2
            pf = np.interp(ff, f, hf) ** 2
            k = int(round(SMOOTH_HZ / 0.02))
            ker = np.ones(k) / k
            st, sf = np.convolve(pt, ker, "same"), np.convolve(pf, ker, "same")
            b = (ff >= BAND[0]) & (ff <= BAND[1])
            truth[(dk, node, ax)] = float(np.median(np.abs(10 * np.log10(st[b] / sf[b]))))
    rows, agg = run_dry(tmp, fem)
    errs = [abs(r["m1_median_abs_db"] - truth[(r["drive"], r["node"], r["axis"])]) for r in rows if "error" not in r]
    return {"n_plots": len(rows), "n_errors": sum(1 for r in rows if "error" in r),
            "max_abs_err_m1_db": float(max(errs)), "median_abs_err_m1_db": float(np.median(errs)),
            "truth_m1_values_db": sorted(truth.values()), "qa_pass_fraction": float(np.mean([r["qa_pass"] for r in rows])),
            "anchor_pass_fraction": float(np.mean([r.get("anchor_pass", False) for r in rows])),
            "m2_vs_truth_note": "M2 here compares the synthetic test with the frozen FEM at measured damping; reported, not gated",
            "rows": rows, "aggregate": agg}


def run_dry(tmp, fem):
    zeta = fem.zeta("constant", 0.01)
    rows = []
    for dk in DRIVES:
        d = os.path.join(tmp, f"{dk}_Impact_Comparison")
        for fn in sorted(os.listdir(d)):
            rows.append(score_plot(os.path.join(d, fn), fem, dk, zeta))
    return rows, aggregate(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plots")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    if a.dry_run:
        res = dry_run()
        json.dump(res, open(os.path.join(WS, "qa", "tier4_dry_run.json"), "w"), indent=1, default=float)
        print(json.dumps({k: v for k, v in res.items() if k not in ("rows",)}, default=float, indent=1)[:1500])
        return 0 if res["max_abs_err_m1_db"] <= 0.5 and res["n_errors"] == 0 else 1
    rows, agg = run(a.plots)
    json.dump({"rows": rows, "aggregate": agg}, open(os.path.join(WS, "out", "tier4_results.json"), "w"), indent=1, default=float)
    print(json.dumps(agg, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
