#!/usr/bin/env python3
"""Figures for the burst-survey foundation packet (written to figures/).

fig1_pilot_frf_wall.png
  (a, b) NASA modal-test FRF and NASA FEM FRF digitised from deck slides 16 and 17, with
  the project's frozen nominal FEM; log-log axes, 45-260 Hz. (c) The two drive-point
  numbers next to the distribution of the project's 420 shock-sensor curves (Card H).
fig2_burst_resolution.png
  Frequency lines across the half-power width of NASA's 22 test modes (45-200 Hz) at five
  line spacings, from NASA's measured frequencies and damping (no simulation).
"""
import csv
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fem_frf  # noqa: E402

GREY, BLACK, RED, BLUE = "0.55", "black", "#c0392b", "#1f5fa8"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def load_digitised(key):
    rows = list(csv.DictReader(open(os.path.join(WS, "out", f"pilot_digitized_{key}.csv"))))
    f = np.array([float(r["f_hz"]) for r in rows])
    t = np.array([float(r["test_log10_g_per_lbf"]) for r in rows])
    m = np.array([float(r["fem_log10_g_per_lbf"]) for r in rows])
    return f, t, m


def fig1():
    fem = fem_frf.FEM()
    z = fem.zeta("measured_interp")
    pilot = json.load(open(os.path.join(WS, "out", "frf_wall_pilot.json")))
    ref = json.load(open(os.path.join(WS, "data", "project_reference_numbers.json")))
    fig = plt.figure(figsize=(12.5, 7.4))
    gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 0.62], hspace=0.32, wspace=0.55)
    cases = [("slide16_drive_point_11101X", (11101, "X"), "Drive point 11101 X+"),
             ("slide17_drive_point_11110Y", (11110, "Y"), "Drive point 11110 Y+")]
    for row, (key, dof, title) in enumerate(cases):
        ax = fig.add_subplot(gs[row, 0:2])
        f, t, m = load_digitised(key)
        s = (f >= 45) & (f <= 260)
        proj = fem.accelerance(f[s], dof, dof, z)
        ax.loglog(f[s], 10 ** t[s], color=BLACK, lw=0.9)
        ax.loglog(f[s], 10 ** m[s], color=RED, lw=0.9)
        ax.loglog(f[s], proj, color=BLUE, lw=0.8, alpha=0.85)
        ax.set_xlim(45, 260)
        ax.set_xticks([50, 70, 100, 150, 200, 250])
        ax.set_xticklabels(["50", "70", "100", "150", "200", "250"])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_ylabel("|accelerance| (g/lbf, log scale)")
        b = pilot["figures"][key]["bands"]
        ax.set_title(f"({'ab'[row]}) {title}", fontsize=10, loc="left")
        ax.text(0.36, 0.97, f"test vs NASA FEM, median |difference|: "
                f"{b['below_150']['pixel_grid']['median_abs_db']:.1f} dB below 150 Hz, "
                f"{b['from_150_to_200']['pixel_grid']['median_abs_db']:.1f} dB at 150-200 Hz",
                transform=ax.transAxes, fontsize=8, va="top", color="0.2")
        ax.text(0.01, 0.13, "NASA test", transform=ax.transAxes, color=BLACK, fontsize=8.5)
        ax.text(0.01, 0.07, "NASA FEM", transform=ax.transAxes, color=RED, fontsize=8.5)
        ax.text(0.01, 0.01, "project FEM", transform=ax.transAxes, color=BLUE, fontsize=8.5)
        if row == 1:
            ax.set_xlabel("frequency (Hz, log scale)")
    ax = fig.add_subplot(gs[:, 2])
    n0 = ref["card_h"]["n0_nominal_fem_db"]
    raw = None
    # Card H per-curve values are not stored here (private record); show its quantiles.
    qs = [("min", n0["min"]), ("5th pct", n0["p05"]), ("25th pct", n0["q25"]), ("median", n0["median"]), ("75th pct", n0["q75"])]
    for lbl, v in qs:
        ax.hlines(v, 0.55, 1.45, color=GREY, lw=1.2)
        ax.text(1.5, v, f"{lbl} {v:.1f}", va="center", fontsize=8, color="0.3")
    vals = [pilot["figures"][k]["bands"]["card_h_band_46p8_258p4"]["smoothed_2p03hz"]["median_abs_db"] for k, _, _ in cases]
    ax.plot([2.4, 2.4], vals, "o", color=BLACK, ms=5)
    for v, (k, _, t_) in zip(vals, cases):
        ax.text(2.55, v, f"{t_.split(': ')[0].replace('Drive point ', '')} {v:.1f}", va="center", fontsize=8)
    ax.set_xlim(0.4, 4.1)
    ax.set_ylim(0, 16)
    ax.set_xticks([1.0, 2.4])
    ax.set_xticklabels(["project FEM\nvs shock\nsensors\n(420 curves)", "NASA FEM\nvs NASA\nmodal test\n(2 curves)"], fontsize=8)
    ax.set_ylabel("per-curve median |20 log10(test/FEM)| (dB)\n46.8-258.4 Hz, 2.03 Hz averaged")
    ax.set_title("(c) same metric, different data (see caveats)", fontsize=9.5, loc="left")
    fig.text(0.01, -0.05, "Source: NASA ShockSat correlation deck (Final_Summary_Documentation_101521_rev1.pptx) slides 16-17, digitised from raster images "
             "(known-answer error 0.05 dB on the pixel-grid metric, 0.32 dB after 2.03 Hz averaging as in panel c). Project FEM: frozen nominal model, damping interpolated from NASA's impact survey. "
             "Card H: project study 2026-07-23 (shock accelerometers, transfer FRFs, 0.49 s windowed hammer records, zeta 0.01, one fitted gain per drive, in-sample). "
             "NASA's FEM was tuned to NASA's modal data. EXPLORATORY: two drive-point curves chosen by NASA, post hoc; not a like-for-like comparison.",
             fontsize=7, wrap=True, color="0.25")
    fig.savefig(os.path.join(WS, "figures", "fig1_pilot_frf_wall.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


def fig2():
    fem = fem_frf.FEM()
    sel = (fem.test_f >= 45) & (fem.test_f <= 200)
    width = 2 * fem.test_zeta[sel] * fem.test_f[sel]
    dfs = [2.0345, 0.5, 0.25, 0.125, 0.0625]
    labels = ["2.03 Hz\n(project shock caches)", "0.5 Hz\n(2 s frames)", "0.25 Hz\n(4 s frames)", "0.125 Hz\n(8 s frames)", "0.0625 Hz\n(16 s frames)"]
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    rng = np.random.default_rng(0)
    for k, df in enumerate(dfs):
        lines = width / df
        x = k + rng.uniform(-0.12, 0.12, len(lines))
        ax.semilogy(x, lines, "o", ms=4, color=BLACK, alpha=0.75)
        ax.text(k, 60, f"{int((lines >= 3).sum())} of {len(lines)}\n>= 3 lines", ha="center", fontsize=8.5)
    ax.axhline(3, color=RED, lw=0.9)
    ax.text(4.45, 3.3, "3 lines", color=RED, fontsize=8.5, ha="right")
    ax.set_xticks(range(len(dfs)))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_ylim(0.05, 150)
    ax.set_ylabel("frequency lines across half-power width\n2 zeta f / line spacing (log scale)")
    ax.set_title("Can the FRF resolve damping? NASA's 22 test modes, 45-200 Hz", fontsize=10, loc="left")
    fig.text(0.01, -0.06, "Source: NASA impact-survey fits (.ash, 33 modes; frequencies match NASA's deck slides 21-45), modes 45-200 Hz. "
             "Computed directly from measured frequency and damping; no simulation. Frame lengths of NASA's burst records are "
             "not yet known (files not yet downloadable).", fontsize=7, wrap=True, color="0.25")
    fig.savefig(os.path.join(WS, "figures", "fig2_burst_resolution.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig2()
    print("figures written")
