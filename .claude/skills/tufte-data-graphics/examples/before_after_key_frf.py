#!/usr/bin/env python3
"""Before/after demonstration of the tufte-data-graphics skill.

Target figure: the project's "key 2DOF transfer functions" review artifact
(artifacts/plots/key_2dof_transfer_functions_linear.png), produced by
scripts/visualize_results.py:plot_key_linear_transfer_functions.

This script recomputes the EXACT SAME curves from the SAME dataset
(artifacts/synthetic/twodof_dataset.json) so the only thing that changes between
BEFORE and AFTER is the *design*, not the numbers. It renders:

  examples/key_frf_BEFORE.png  — faithful replica of the current style
  examples/key_frf_AFTER.png   — same data, Tufte checklist applied

Run from repo root:  python3 .claude/skills/tufte-data-graphics/examples/before_after_key_frf.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from src.twodof.model import (  # noqa: E402
    TwoDofParams,
    accel_over_force_matrix,
    apparent_mass_dome_uncoupled,
    apparent_mass_from_drivepoint,
    common_base_reaction_apparent_mass,
    sdof_base_reaction_apparent_mass,
    sdof_source_apparent_mass,
    tray_base_to_tray_accel_transfer,
)

OUT = Path(__file__).resolve().parent


# ----------------------------------------------------------------------------
# Shared data (identical numbers for both figures)
# ----------------------------------------------------------------------------
def load_curves():
    raw = json.loads((ROOT / "artifacts/synthetic/twodof_dataset.json").read_text())
    t = raw["truth"]["params"]
    p = TwoDofParams(m1=t["m1"], m2=t["m2"], k1=t["k1"], k2=t["k2"],
                     k12=t["k12"], c1=t["c1"], c2=t["c2"], c12=t["c12"])
    df = np.asarray(raw["freqs_hz"], float)
    f = np.geomspace(df.min(), df.max(), 600)

    H = accel_over_force_matrix(p, f)
    accel = [
        ("Dome-only a1/F1", 1.0 / apparent_mass_dome_uncoupled(f, p.m1, p.k1, p.c1)),
        ("Coupled a1/F1", H[:, 0, 0]),
        ("Coupled a2/F1", H[:, 1, 0]),
        ("Coupled a1/F2", H[:, 0, 1]),
        ("Coupled a2/F2", H[:, 1, 1]),
    ]
    cbm = common_base_reaction_apparent_mass(p, f)
    appmass = [
        ("Source dome app. mass", sdof_source_apparent_mass(f, p.m1, p.k1, p.c1)),
        ("Dome load app. mass", sdof_base_reaction_apparent_mass(f, p.m1, p.k1, p.c1)),
        ("Tray load app. mass", sdof_base_reaction_apparent_mass(f, p.m2, p.k2, p.c2)),
        ("Coupled primary support", cbm["primary_support"]),
        ("Coupled tray support", cbm["tray_support"]),
        ("Coupled total base", cbm["total_base"]),
    ]
    tray = ("Standalone tray a2/abase", tray_base_to_tray_accel_transfer(f, p))
    masses = {"m1 dome": p.m1, "m2 tray": p.m2, "m1+m2 total": p.m1 + p.m2}
    fns = {"tray fn": float(np.sqrt(p.k2 / p.m2) / (2 * np.pi)),
           "dome fn": float(np.sqrt(p.k1 / p.m1) / (2 * np.pi))}
    return f, accel, appmass, tray, masses, fns


# ----------------------------------------------------------------------------
# BEFORE — faithful replica of the current style (chartjunk and all)
# ----------------------------------------------------------------------------
def make_before(f, accel, appmass, tray, masses, fns):
    plt.rcParams.update(matplotlib.rcParamsDefault)
    fig, ax = plt.subplots(3, 1, figsize=(11, 10), sharex=True)
    for name, v in accel:
        ax[0].plot(f, np.abs(v), lw=1.4, label=name)
    for name, v in appmass:
        ax[1].plot(f, np.abs(v), lw=1.4, label=name)
    ax[2].plot(f, np.abs(tray[1]), lw=1.4, label=tray[0])

    for lab, val in masses.items():
        ax[1].axhline(val, lw=1.0, ls="--", alpha=0.8, label=lab + " mass")
    for lab, val in fns.items():
        for a in ax:
            a.axvline(val, lw=0.9, ls=":", alpha=0.7)

    ax[0].set_title("Key acceleration/force FRFs (linear magnitude)")
    ax[0].set_ylabel("magnitude, accel/force")
    ax[1].set_title("7004C-style source/load apparent masses (linear magnitude)")
    ax[1].set_ylabel("magnitude, mass units")
    ax[2].set_title("Standalone tray base transfer (linear magnitude)")
    ax[2].set_ylabel("magnitude, accel/accel")
    ax[2].set_xlabel("Frequency (Hz)")
    for a in ax:
        a.set_xscale("log")
        a.grid(True, which="both", alpha=0.3)
        a.legend(fontsize=8, loc="best")
    ax[1].set_yscale("log")
    fig.suptitle("2DOF key transfer functions for review: log frequency axis, no dB scaling", fontsize=12)
    fig.tight_layout()
    path = OUT / "key_frf_BEFORE.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


# ----------------------------------------------------------------------------
# AFTER — same data, Tufte checklist applied
# ----------------------------------------------------------------------------
# colorblind-safe (Wong/Okabe-Ito), used across both data panels
CB = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9"]


def _tufte_axes(a):
    a.spines["top"].set_visible(False)
    a.spines["right"].set_visible(False)
    a.spines["left"].set_color("#555555")
    a.spines["bottom"].set_color("#555555")
    a.tick_params(length=3, colors="#555555")
    a.grid(True, axis="y", which="major", color="#e6e6e6", lw=0.6)
    a.grid(False, axis="x")
    a.set_axisbelow(True)


def _ordered_legend(a, series):
    """Frameless legend in the outside whitespace, ordered top->bottom to match
    the curves' vertical stacking at the right edge (less eye ping-pong than a
    boxed in-data legend). Colored text, no marker handles needed."""
    rank = np.argsort([-np.abs(v)[-1] for _, v in series])  # highest curve first
    y0, dy = 0.98, 0.075
    for slot, idx in enumerate(rank):
        name = series[idx][0]
        a.text(1.012, y0 - slot * dy, name, transform=a.transAxes, fontsize=8,
               color=CB[idx], va="top", ha="left", clip_on=False)


def make_after(f, accel, appmass, tray, masses, fns):
    plt.rcParams.update(matplotlib.rcParamsDefault)
    plt.rcParams.update({"font.size": 11, "axes.titlelocation": "left",
                         "axes.titlesize": 10.5, "axes.titleweight": "bold"})
    fig, ax = plt.subplots(3, 1, figsize=(11, 10.5), sharex=True)
    fig.subplots_adjust(right=0.78, hspace=0.32, top=0.90, bottom=0.09)

    # vertical reference lines: light, labeled in place once (top panel)
    for lab, val in fns.items():
        for a in ax:
            a.axvline(val, color="#bbbbbb", lw=0.8, ls=":", zorder=0)
        ax[0].annotate(f"{lab} {val:.0f} Hz", xy=(val, 1.0),
                       xycoords=("data", "axes fraction"), xytext=(0, 2),
                       textcoords="offset points", rotation=90, va="bottom",
                       ha="center", fontsize=7.5, color="#888888")

    # Panel 0: acceleration/force FRFs — direct end-of-line labels, no legend
    for (name, v), c in zip(accel, CB):
        ax[0].plot(f, np.abs(v), lw=1.5, color=c)
    _tufte_axes(ax[0])
    _ordered_legend(ax[0], accel)
    ax[0].set_title("Acceleration / force FRFs   a/F  [(m/s$^2$)/N]")
    ax[0].set_ylabel("|a/F|")

    # Panel 1: apparent masses — log y, direct labels, mass asymptotes in place
    for (name, v), c in zip(appmass, CB):
        ax[1].plot(f, np.abs(v), lw=1.5, color=c)
    ax[1].set_yscale("log")
    _tufte_axes(ax[1])
    for lab, val in masses.items():
        ax[1].axhline(val, color="#cfcfcf", lw=0.9, ls="--", zorder=0)
        ax[1].annotate(f"{lab} = {val:g}", xy=(f[0], val), xytext=(0, 2),
                       textcoords="offset points", fontsize=7.5, color="#999999",
                       va="bottom", ha="left")
    _ordered_legend(ax[1], appmass)
    ax[1].set_title("Source / load apparent mass   M = F/a  [kg]   (NASA-HDBK-7004C style)")
    ax[1].set_ylabel("|M|  [kg]  (log)")

    # Panel 2: ONE curve -> no legend at all, title names it
    ax[2].plot(f, np.abs(tray[1]), lw=1.5, color=CB[0])
    _tufte_axes(ax[2])
    pk = int(np.argmax(np.abs(tray[1])))
    ax[2].annotate(f"tray resonance\n{f[pk]:.0f} Hz", xy=(f[pk], np.abs(tray[1])[pk]),
                   xytext=(8, -2), textcoords="offset points", fontsize=8,
                   color="#555555", va="top")
    ax[2].set_title("Standalone tray base transfer   a$_2$/a$_{base}$  [g/g]")
    ax[2].set_ylabel("|a$_2$/a$_{base}$|")
    ax[2].set_xlabel("frequency [Hz]  (log)")

    for a in ax:
        a.set_xscale("log")
        a.margins(x=0.02)

    fig.suptitle("2DOF key transfer functions — synthetic truth (1 dataset; no flight-to-flight variability)",
                 fontsize=12.5, x=0.02, ha="left", weight="bold")
    fig.text(0.02, 0.012,
             "Driving-point quantities from the assembled 2DOF model. Log frequency, linear magnitude "
             "(no dB). Vertical dotted = uncoupled natural frequencies; dashed = mass asymptotes. "
             "Source: artifacts/synthetic/twodof_dataset.json.",
             fontsize=7.5, color="#777777", ha="left")
    path = OUT / "key_frf_AFTER.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


if __name__ == "__main__":
    data = load_curves()
    b = make_before(*data)
    a = make_after(*data)
    print("wrote:", b)
    print("wrote:", a)
