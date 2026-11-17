#!/usr/bin/env python3
"""Known-answer test of digitize_frf.py.

Draws synthetic two-curve FRF plots whose true numbers are known, in the same pixel
geometry and colour scheme as the NASA figures (grey figure background, white panel,
solid light-grey gridlines every 50 Hz and every decade, black curve drawn first, red
curve on top, legend box in the lower right), digitises them with the production
code, and reports the error. The plots are test fixtures written to a temporary
directory, not review figures; they deliberately copy the NASA layout (linear
frequency axis, legend box) because the digitiser must face the same obstacles.

Truth definition: a pixel column spans about 0.36 Hz. The true value for a column is
the mean of log10|H| over the frequencies that column covers.

Writes qa/digitizer_known_answer.json. Exit code 1 if any threshold is missed.
"""
import json
import os
import sys
import tempfile

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import digitize_frf as dg  # noqa: E402

THRESH = {"calib_px": 1.0, "curve_median_db": 0.5, "curve_p95_db": 3.0,
          "metric_median_abs_db": 0.5, "metric_corr": 0.03}


def accelerance(f, fn, zeta, a):
    """|sum over modes of a_r * (-w^2) / (w_r^2 - w^2 + 2 i zeta_r w_r w)| ; a_r > 0 mimics a drive point."""
    w = 2 * np.pi * f[:, None]
    wn = 2 * np.pi * fn[None, :]
    h = (a[None, :] * (-w ** 2) / (wn ** 2 - w ** 2 + 2j * zeta[None, :] * wn * w)).sum(1)
    return np.abs(h)


def make_case(seed, panel_px, ylim_log, path):
    rng = np.random.default_rng(seed)
    n = 22
    fn_t = np.sort(rng.uniform(52, 390, n))
    zt = rng.uniform(0.002, 0.008, n)
    at = 10 ** rng.uniform(-0.6, 0.6, n) * 0.6
    fn_f = fn_t * (1 + rng.normal(0, 0.04, n))
    zf = np.full(n, 0.01)
    af = at * 10 ** rng.normal(0, 0.2, n)
    truth = {"test": lambda f: accelerance(f, fn_t, zt, at), "fem": lambda f: accelerance(f, fn_f, zf, af)}

    wpx, hpx = panel_px
    fig_w, fig_h, dpi = 1219, 914, 100
    fig = plt.figure(figsize=(fig_w / dpi, fig_h / dpi), dpi=dpi, facecolor=(240 / 255,) * 3)
    ax = fig.add_axes([99 / fig_w, 1 - 849 / fig_h, wpx / fig_w, hpx / fig_h], facecolor="white")
    f = np.linspace(10, 400, 60001)
    ax.semilogy(f, truth["test"](f), color="black", lw=1.1, label="Test")
    ax.semilogy(f, truth["fem"](f), color=(1, 0, 0), lw=1.1, label="FEM")
    ax.set_xlim(10, 400)
    ax.set_ylim(10 ** ylim_log[0], 10 ** ylim_log[1])
    ax.set_xticks(np.arange(50, 401, 50))
    ax.grid(True, which="major", color=(226 / 255,) * 3, lw=0.8)
    ax.set_axisbelow(True)
    for s in ax.spines.values():
        s.set_color((0.3, 0.3, 0.3)); s.set_linewidth(0.8)
    ax.legend(loc="lower right", frameon=True, edgecolor="black", fancybox=False)
    ax.set_xlabel("Frequency (Hz)"); ax.set_ylabel("A/F (G/lbf)")
    fig.canvas.draw()
    # exact pixel mapping from the renderer (rows counted from the top of the image)
    (x0, y0), (x1, y1) = ax.transData.transform([(10, 10 ** ylim_log[0]), (400, 10 ** ylim_log[1])])
    leg = ax.get_legend().get_window_extent()
    exact = {"px_per_hz": (x1 - x0) / 390.0, "col_at_0hz": x0 - 10 * (x1 - x0) / 390.0 - 0.5,
             "px_per_decade": (y1 - y0) / (ylim_log[1] - ylim_log[0]),
             "row_at_1": fig_h - (y0 + (0 - ylim_log[0]) * (y1 - y0) / (ylim_log[1] - ylim_log[0])) - 0.5,
             "legend_box": [int(fig_h - leg.y1) - 3, int(fig_h - leg.y0) + 3, int(leg.x0) - 3, int(leg.x1) + 3]}
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
    return truth, exact


def column_truth(fun, f_centres, hz_per_px, n_sub=41):
    off = np.linspace(-0.5, 0.5, n_sub) * hz_per_px
    return np.log10(fun((f_centres[:, None] + off[None, :]).ravel())).reshape(len(f_centres), n_sub).mean(1)


def run_case(seed, panel_px, ylim_log, anchor_log10, tmp):
    path = os.path.join(tmp, f"case_{seed}.png")
    truth, exact = make_case(seed, panel_px, ylim_log, path)
    im = dg.load_rgb(path)
    row_hint = int(round(exact["row_at_1"] - exact["px_per_decade"] * anchor_log10))
    cal = dg.calibrate(im, x_grid_step_hz=50.0, x_anchor_hz=50.0, y_anchor_log10=anchor_log10, y_anchor_row_hint=row_hint)
    curves = dg.extract(im, cal, {"test": "black", "fem": "red"}, exclude_boxes=[tuple(exact["legend_box"])])
    flags_fem = dg.classify_gaps(curves, "fem", "test")
    flags = dg.classify_gaps(curves, "test", "fem")
    hidden = flags["hidden"]
    f = curves["test"]["f_hz"]
    band = (f >= 45) & (f <= 200)
    res = {"seed": seed, "panel_px": list(panel_px),
           "calib_err_px": {"x_at_10hz": abs((cal.col_at_0hz + 10 * cal.px_per_hz) - (exact["col_at_0hz"] + 10 * exact["px_per_hz"])),
                            "x_at_400hz": abs((cal.col_at_0hz + 400 * cal.px_per_hz) - (exact["col_at_0hz"] + 400 * exact["px_per_hz"])),
                            "y_at_1": abs(cal.row_at_1 - exact["row_at_1"]),
                            "y_at_100": abs((cal.row_at_1 - 2 * cal.px_per_decade) - (exact["row_at_1"] - 2 * exact["px_per_decade"]))},
           "hz_per_px": cal.hz_per_px, "db_per_px": cal.db_per_px,
           "hidden_fraction_in_band": float(hidden[band].mean()),
           "clipped_fraction_in_band": {"test": float(flags["clipped"][band].mean()), "fem": float(flags_fem["clipped"][band].mean())},
           "unresolved_gap_fraction_in_band": {"test": float(flags["gap"][band].mean()), "fem": float(flags_fem["gap"][band].mean())}}
    tr = {}
    for name in ("test", "fem"):
        t = column_truth(truth[name], f, cal.hz_per_px)
        tr[name] = t
        e = 20 * (curves[name]["log10_centre"] - t)[band]
        e = e[~np.isnan(e)]
        res[f"curve_err_db_{name}"] = {"median_abs": float(np.median(np.abs(e))), "p95_abs": float(np.percentile(np.abs(e), 95)),
                                       "max_abs": float(np.max(np.abs(e))), "mean_signed": float(np.mean(e))}
    # Like-for-like: truth is evaluated on exactly the columns the digitiser kept
    # (clipped columns are unknown to it and are reported separately above).
    keep = ~np.isnan(curves["test"]["log10_centre"]) & ~np.isnan(curves["fem"]["log10_centre"])
    tt = np.where(keep, tr["test"], np.nan)
    tf_ = np.where(keep, tr["fem"], np.nan)
    got = dg.compare(f, curves["test"]["log10_centre"], curves["fem"]["log10_centre"], 45, 200)
    want = dg.compare(f, tt, tf_, 45, 200)
    want_all = dg.compare(f, tr["test"], tr["fem"], 45, 200)
    res["metric"] = {"digitised": got, "truth_same_columns": want, "truth_all_columns": want_all,
                     "err_median_abs_db": abs(got["median_abs_db"] - want["median_abs_db"]),
                     "err_corr": abs(got["corr_log"] - want["corr_log"])}
    gs = dg.compare(f, dg.band_smooth_power(f, curves["test"]["log10_centre"], 2.03), dg.band_smooth_power(f, curves["fem"]["log10_centre"], 2.03), 45, 200)
    ws = dg.compare(f, dg.band_smooth_power(f, tt, 2.03), dg.band_smooth_power(f, tf_, 2.03), 45, 200)
    res["metric_2hz_smoothed"] = {"digitised": gs, "truth_same_columns": ws,
                                  "err_median_abs_db": abs(gs["median_abs_db"] - ws["median_abs_db"]),
                                  "err_corr": abs(gs["corr_log"] - ws["corr_log"])}
    return res


def main():
    tmp = tempfile.mkdtemp(prefix="digit_test_")
    cases = []
    for seed in (11, 12, 13, 14):
        cases.append(run_case(seed, (1090, 610), (-3.96, 2.05), 0.0, tmp))      # slide-16-like panel
    for seed in (21, 22):
        cases.append(run_case(seed, (1090, 610), (-4.13, 2.0), 1.0, tmp))       # slide-17-like panel, different anchor
    worst = {
        "calib_px": max(max(c["calib_err_px"].values()) for c in cases),
        "curve_median_db": max(max(c["curve_err_db_test"]["median_abs"], c["curve_err_db_fem"]["median_abs"]) for c in cases),
        "curve_p95_db": max(max(c["curve_err_db_test"]["p95_abs"], c["curve_err_db_fem"]["p95_abs"]) for c in cases),
        "metric_median_abs_db": max(c["metric"]["err_median_abs_db"] for c in cases),
        "metric_corr": max(c["metric"]["err_corr"] for c in cases),
    }
    # The 2 Hz power-smoothed variant is reported but not gated: a peak narrower than one
    # pixel has no recoverable power inside its column, so this variant carries a larger,
    # separately stated uncertainty.
    worst_smoothed = {"metric_median_abs_db": max(c["metric_2hz_smoothed"]["err_median_abs_db"] for c in cases),
                      "metric_corr": max(c["metric_2hz_smoothed"]["err_corr"] for c in cases)}
    ok = {k: bool(worst[k] <= THRESH[k]) for k in THRESH}
    out = {"n_cases": len(cases), "thresholds": THRESH, "worst": worst, "worst_2hz_smoothed_ungated": worst_smoothed,
           "pass": ok, "all_pass": all(ok.values()), "cases": cases}
    dest = os.path.join(HERE, "..", "qa", "digitizer_known_answer.json")
    json.dump(out, open(dest, "w"), indent=1)
    print(json.dumps({"worst": worst, "worst_2hz_smoothed_ungated": worst_smoothed, "pass": ok}, indent=1))
    for c in cases:
        print(c["seed"], {k: round(float(v), 2) for k, v in c["calib_err_px"].items()}, "hidden", round(c["hidden_fraction_in_band"], 3), "clipped", c["clipped_fraction_in_band"],
              "test", {k: round(v, 2) for k, v in c["curve_err_db_test"].items()}, "fem", {k: round(v, 2) for k, v in c["curve_err_db_fem"].items()},
              "metric err", round(c["metric"]["err_median_abs_db"], 3), round(c["metric"]["err_corr"], 4),
              "| truth median_abs", round(c["metric"]["truth_same_columns"]["median_abs_db"], 2), "corr", round(c["metric"]["truth_same_columns"]["corr_log"], 3),
              "| 2Hz err", round(c["metric_2hz_smoothed"]["err_median_abs_db"], 3), round(c["metric_2hz_smoothed"]["err_corr"], 4))
    return 0 if out["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
