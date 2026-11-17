#!/usr/bin/env python3
"""Pilot: how far is NASA's FEM from NASA's own modal-test FRF, read from the two
drive-point comparison figures in NASA's correlation deck (slides 16 and 17), and
how repeatable are NASA's single-impact FRFs (slide 19)?

Status of this analysis: EXPLORATORY and post hoc. It was conceived after reading
the deck, it covers two drive-point FRFs only, and it uses NASA's FEM curve (damping
unknown), not this project's forward model. It motivates, and does not replace, the
pre-registered test on all 264 NASA comparison plots (prereg_gated_analysis.md).

Quantities (see quantity_contracts.md):
  H            accelerance FRF, response acceleration / input force, g/lbf, magnitude only
  median |dB|  median over frequency of |20 log10(|H_test| / |H_fem|)|; 6 dB = factor 2
  corr         Pearson correlation between log10|H_test| and log10|H_fem| over the band

Outputs: out/pilot_digitized_<slide>.csv, out/frf_wall_pilot.json
"""
from __future__ import annotations

import csv
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import digitize_frf as dg  # noqa: E402
import fem_frf  # noqa: E402

DD = os.path.join(WS, "data", "nasa_deck")
FIGS = {
    # y_anchor: a DETECTED horizontal gridline row and the power of ten printed beside it
    # in the figure (read from the tick labels). legend_box: rows/cols of the legend.
    "slide16_drive_point_11101X": {"file": "fig_slide16_drive_point_11101X.png", "dof": "11101 X+",
                                   "y_anchor_row": 448, "y_anchor_log10": 0.0, "legend_box": (775, 849, 930, 1189)},
    "slide17_drive_point_11110Y": {"file": "fig_slide17_drive_point_11110Y.png", "dof": "11110 Y+",
                                   "y_anchor_row": 341, "y_anchor_log10": 1.0, "legend_box": (778, 851, 935, 1192)},
}
BANDS = {"p1_band_45_200": (45.0, 200.0), "card_h_band_46p8_258p4": (46.79, 258.38),
         "below_150": (45.0, 150.0), "from_150_to_200": (150.0, 200.0), "from_200_to_400": (200.0, 400.0)}
# NASA's own listed frequencies (out/nasa_final_correlation.csv), used only to check the
# frequency calibration of the digitisation.
CHECK_TEST_HZ = [54.19, 69.98, 85.78]
CHECK_FEM_HZ = [54.68, 87.94]


def peaks(f, y_top, lo, hi, prominence=0.8, half_window=8, wide=25):
    out = []
    for i in range(wide, len(y_top) - wide):
        if not (lo < f[i] < hi) or np.isnan(y_top[i]):
            continue
        if y_top[i] >= np.nanmax(y_top[i - half_window:i + half_window + 1]) and \
           y_top[i] - np.nanmin(y_top[i - wide:i + wide + 1]) > prominence:
            if not out or f[i] - out[-1] > 1.5:
                out.append(float(f[i]))
    return out


def nearest_err(found, wanted):
    return [float(min(abs(x - w) for x in found)) if found else float("nan") for w in wanted]


def digitise_pair(key, meta):
    im = dg.load_rgb(os.path.join(DD, meta["file"]))
    cal = dg.calibrate(im, x_grid_step_hz=50.0, x_anchor_hz=50.0,
                       y_anchor_log10=meta["y_anchor_log10"], y_anchor_row_hint=meta["y_anchor_row"])
    cv = dg.extract(im, cal, {"test": "black", "fem": "red"}, exclude_boxes=[meta["legend_box"]])
    flags_fem = dg.classify_gaps(cv, "fem", "test")
    flags_test = dg.classify_gaps(cv, "test", "fem")
    f = cv["test"]["f_hz"]
    with open(os.path.join(WS, "out", f"pilot_digitized_{key}.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["f_hz", "test_log10_g_per_lbf", "fem_log10_g_per_lbf", "test_flag", "fem_flag"])
        for i in range(len(f)):
            def flag(fl):
                return "clipped" if fl["clipped"][i] else "hidden" if fl["hidden"][i] else "gap" if fl["gap"][i] else ""
            w.writerow([f"{f[i]:.3f}", f"{cv['test']['log10_centre'][i]:.4f}", f"{cv['fem']['log10_centre'][i]:.4f}",
                        flag(flags_test), flag(flags_fem)])
    res = {"dof": meta["dof"], "source_file": meta["file"],
           "calibration": {"hz_per_px": cal.hz_per_px, "db_per_px": cal.db_per_px,
                           "vertical_gridline_cols": cal.v_grid_cols, "horizontal_gridline_rows": cal.h_grid_rows,
                           "x_fit_resid_px": cal.x_fit_resid_px, "y_fit_resid_px": cal.y_fit_resid_px,
                           "panel_edges_hz": [float(cal.col_to_hz(cal.c0)), float(cal.col_to_hz(cal.c1))],
                           "panel_edges_log10": [float(cal.row_to_log10(cal.r1)), float(cal.row_to_log10(cal.r0))]},
           "frequency_check": {
               "test_peaks_found_hz": peaks(f, cv["test"]["log10_top"], 45, 100),
               "fem_peaks_found_hz": peaks(f, cv["fem"]["log10_top"], 45, 100),
           }, "bands": {}}
    fc = res["frequency_check"]
    fc["test_abs_err_hz_vs_nasa_table"] = nearest_err(fc["test_peaks_found_hz"], CHECK_TEST_HZ)
    fc["fem_abs_err_hz_vs_nasa_table"] = nearest_err(fc["fem_peaks_found_hz"], CHECK_FEM_HZ)
    fc["max_abs_err_hz"] = float(np.nanmax(fc["test_abs_err_hz_vs_nasa_table"] + fc["fem_abs_err_hz_vs_nasa_table"]))
    t, m = cv["test"]["log10_centre"], cv["fem"]["log10_centre"]
    ts, ms = dg.band_smooth_power(f, t, 2.03), dg.band_smooth_power(f, m, 2.03)
    fem = fem_frf.FEM()
    dof = (int(meta["dof"].split()[0]), meta["dof"].split()[1][0])
    proj = fem.column_mean_log10(f, cal.hz_per_px, dof, dof, fem.zeta("measured_interp"))
    proj = np.where(np.isnan(t) & np.isnan(m), np.nan, proj)
    for name, (lo, hi) in BANDS.items():
        b = (f >= lo) & (f <= hi)
        res["bands"][name] = {
            "pixel_grid": dg.compare(f, t, m, lo, hi),
            "smoothed_2p03hz": dg.compare(f, ts, ms, lo, hi),
            "fraction_columns": {"test_hidden_under_fem": float(flags_test["hidden"][b].mean()),
                                 "test_clipped": float(flags_test["clipped"][b].mean()),
                                 "fem_clipped": float(flags_fem["clipped"][b].mean()),
                                 "unresolved_gap": float((flags_test["gap"] | flags_fem["gap"])[b].mean())},
            "project_fem_vs_nasa_fem": dg.compare(f, proj, m, lo, hi),
            "nasa_test_vs_project_fem": dg.compare(f, t, proj, lo, hi)}
    return res


def repeatability():
    """Slide 19: several single-impact FRFs overlaid. Per pixel column, the spread is the
    distance between the highest and lowest visible curve centres. A curve with no
    visible pixels in a column lies under another curve, i.e. within one stroke width."""
    im = dg.load_rgb(os.path.join(DD, "fig_slide19_operator_variability.png"))
    cal = dg.calibrate(im, x_grid_step_hz=50.0, x_anchor_hz=50.0, y_anchor_log10=0.0, y_anchor_row_hint=548)
    cv = dg.extract(im, cal, {"blue": "mblue", "orange": "morange", "yellow": "myellow"})
    f = cv["blue"]["f_hz"]
    stack = np.vstack([cv[k]["log10_centre"] for k in ("blue", "orange", "yellow")])
    n_vis = (~np.isnan(stack)).sum(0)
    with np.errstate(all="ignore"):
        spread_db = 20.0 * (np.nanmax(stack, 0) - np.nanmin(stack, 0))
    spread_db = np.where(n_vis >= 2, spread_db, 0.0)
    spread_db = np.where(n_vis == 0, np.nan, spread_db)
    stroke_px = float(np.nanmedian(np.concatenate([cv[k]["n_px"][cv[k]["n_px"] > 0] for k in cv])))
    out = {"source_file": "fig_slide19_operator_variability.png", "n_curves_resolved_by_colour": 3,
           "calibration": {"hz_per_px": cal.hz_per_px, "db_per_px": cal.db_per_px,
                           "x_fit_resid_px": cal.x_fit_resid_px, "y_fit_resid_px": cal.y_fit_resid_px},
           "median_stroke_px": stroke_px, "resolution_floor_db": stroke_px * cal.db_per_px, "bands": {}}
    for name, (lo, hi) in {"45_200": (45, 200), "45_150": (45, 150), "150_200": (150, 200), "200_400": (200, 400)}.items():
        b = (f >= lo) & (f <= hi) & ~np.isnan(spread_db)
        s = spread_db[b]
        out["bands"][name] = {"n_columns": int(b.sum()), "median_spread_db": float(np.median(s)),
                              "p90_spread_db": float(np.percentile(s, 90)), "max_spread_db": float(np.max(s)),
                              "fraction_columns_one_curve_visible": float((n_vis[b] == 1).mean())}
    return out


def main():
    out = {"status": "exploratory, post hoc, two drive-point FRFs; not a pre-registered result",
           "digitiser_known_answer": json.load(open(os.path.join(WS, "qa", "digitizer_known_answer.json")))["worst"],
           "figures": {k: digitise_pair(k, m) for k, m in FIGS.items()},
           "single_impact_repeatability_slide19": repeatability()}
    for band in BANDS:
        vals = [out["figures"][k]["bands"][band]["pixel_grid"] for k in FIGS]
        out.setdefault("summary", {})[band] = {
            "median_abs_db_each": [v["median_abs_db"] for v in vals],
            "corr_log_each": [v["corr_log"] for v in vals],
            "median_abs_db_mean_of_two": float(np.mean([v["median_abs_db"] for v in vals])),
            "corr_log_mean_of_two": float(np.mean([v["corr_log"] for v in vals])),
            "project_fem_vs_nasa_fem_db_each": [out["figures"][k]["bands"][band]["project_fem_vs_nasa_fem"]["median_abs_db"] for k in FIGS],
            "nasa_test_vs_project_fem_db_each": [out["figures"][k]["bands"][band]["nasa_test_vs_project_fem"]["median_abs_db"] for k in FIGS]}
    json.dump(out, open(os.path.join(WS, "out", "frf_wall_pilot.json"), "w"), indent=1)
    for k, r in out["figures"].items():
        print(k, "freq check max err Hz", round(r["frequency_check"]["max_abs_err_hz"], 3),
              "| test peaks", [round(x, 2) for x in r["frequency_check"]["test_peaks_found_hz"]],
              "| fem peaks", [round(x, 2) for x in r["frequency_check"]["fem_peaks_found_hz"]])
        for b, v in r["bands"].items():
            p, s = v["pixel_grid"], v["smoothed_2p03hz"]
            print(f"   {b:26} median|dB| {p['median_abs_db']:.2f} corr {p['corr_log']:+.3f} (n={p['n_points']})"
                  f" | 2.03 Hz smoothed {s['median_abs_db']:.2f} {s['corr_log']:+.3f} | projFEM-NASAFEM {v['project_fem_vs_nasa_fem']['median_abs_db']:.2f}"
                  f" test-projFEM {v['nasa_test_vs_project_fem']['median_abs_db']:.2f} | clipped test/fem "
                  f"{v['fraction_columns']['test_clipped']:.3f}/{v['fraction_columns']['fem_clipped']:.3f} hidden {v['fraction_columns']['test_hidden_under_fem']:.3f}")
    print("repeatability", json.dumps(out["single_impact_repeatability_slide19"]["bands"]))
    print("resolution floor dB", out["single_impact_repeatability_slide19"]["resolution_floor_db"])


if __name__ == "__main__":
    main()
