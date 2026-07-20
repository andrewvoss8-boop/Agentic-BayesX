#!/usr/bin/env python3
"""Review figures for the ShockSat sequential statFEM pilot.

Figures follow the local Tufte checklist: log frequency for PSD, direct labels,
low chartjunk, and run/split/caveat text on the figure.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
FIG = WS / "figures"
FIG.mkdir(exist_ok=True)

TUFTE_RC = {
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#444444",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.frameon": False,
    "axes.titlelocation": "left",
}
plt.rcParams.update(TUFTE_RC)


def direct_label(ax, x, y, text, color, dy=0):
    ax.annotate(text, xy=(x[-1], y[-1]), xytext=(5, dy), textcoords="offset points",
                va="center", fontsize=8.5, color=color)


def plot_summary(results: dict) -> Path:
    colors = {"nominal_residual": "#0072B2", "stiffness_residual": "#D55E00"}
    refs = list(next(iter(results["summaries"].values())).keys())
    x = np.arange(len(refs))
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    for variant, color in colors.items():
        y = [results["summaries"][variant][r]["median_grms_ratio"] for r in refs]
        ax.plot(x, y, marker="o", linewidth=1.5, color=color)
        direct_label(ax, x, np.asarray(y), variant.replace("_", " "), color)
    ax.axhline(1.0, color="#555555", linewidth=0.9)
    ax.text(0.02, 0.16, "FEM+6 dB GRMS ratio = 1", transform=ax.transAxes,
            fontsize=8.5, color="#555555")
    ax.set_yscale("log")
    ax.set_ylim(0.8, 3.6)
    ax.set_xticks(x)
    ax.set_xticklabels([r.replace("m_", "").replace("_", "\n") for r in refs])
    ax.set_ylabel("median GRMS ratio vs FEM+6 dB (log scale)")
    ax.set_title("Sequential held-out PSD-envelope result by reference")
    ax.text(0.02, 0.94,
            "Run: shocksat_sequential_statfem_20260623; split seed 0, 90% training. "
            "YELLOW caveat: fixed filter hyperparameters; PSD metric only.",
            transform=ax.transAxes, fontsize=8, color="#333333", va="top",
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=2))
    fig.tight_layout()
    out = FIG / "fig_grms_summary.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_envelope(results: dict) -> Path:
    z = np.load(OUT / "example_envelopes.npz")
    key = "stiffness_residual_m_xpos_990x"
    if key not in z:
        key = sorted(z.files)[0]
    arr = z[key]
    f, data_psd, seq975_psd, seq_env, fem6_env = arr
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    series = [
        ("held-out measured PSD", data_psd, "#111111", 1.1),
        ("sequential 97.5% PSD", seq975_psd, "#0072B2", 1.0),
        ("sequential smoothline", seq_env, "#0072B2", 1.8),
        ("FEM+6 dB smoothline", fem6_env, "#D55E00", 1.8),
    ]
    for label, y, color, lw in series:
        ax.loglog(f, np.maximum(y, 1e-20), linewidth=lw, color=color,
                  alpha=0.55 if "97.5" in label else 1.0, label=label)
    ax.legend(loc="upper left", fontsize=8.5)
    ax.set_xlabel("frequency [Hz], log scale")
    ax.set_ylabel("response PSD [g^2/Hz], log scale")
    ax.set_title("Example held-out PSD-envelope comparison")
    ax.text(0.02, 0.03,
            r"Quantity: $S_{aa}=|H|^2 S_{F0}$, $S_{F0}=1$ lbf$^2$/Hz. "
            "Same smoothline algorithm for sequential and FEM+6 dB.",
            transform=ax.transAxes, fontsize=8, color="#333333",
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=2))
    fig.tight_layout()
    out = FIG / "fig_example_envelope.png"
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_method_graph(results: dict) -> Path:
    fig, ax = plt.subplots(figsize=(8.5, 3.6))
    ax.axis("off")
    boxes = [
        (0.07, 0.78, "Measured hammer\nforce $F_d(t)$\n[lbf]"),
        (0.32, 0.78, "Modal dynamics\n$q$, $\\dot q$\nnominal or stiffness-updated"),
        (0.59, 0.78, "Observed sensors\naccel $a_{obs}(t)$\n[g]"),
        (0.59, 0.38, "Fixed-prior\nstate update\n(not NUTS)"),
        (0.82, 0.38, "Held-out sensors\nPSD envelope\nGRMS + exceedance"),
    ]
    for x, y, text in boxes:
        ax.text(x, y, text, transform=ax.transAxes, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#444444", lw=0.8),
                fontsize=9)
    arrows = [
        ((0.16, 0.78), (0.23, 0.78)),
        ((0.44, 0.78), (0.51, 0.78)),
        ((0.59, 0.68), (0.59, 0.49)),
        ((0.67, 0.38), (0.74, 0.38)),
        ((0.36, 0.69), (0.51, 0.45)),
    ]
    for a, b in arrows:
        ax.annotate("", xy=b, xytext=a, xycoords=ax.transAxes, textcoords=ax.transAxes,
                    arrowprops=dict(arrowstyle="->", lw=1.0, color="#555555"))
    ax.text(0.02, 0.09,
            "Run-specific graphical model. Held-out sensor data are used only after prediction for PSD scoring.",
            transform=ax.transAxes, fontsize=8, color="#333333")
    out = FIG / "fig_method_graph.png"
    fig.savefig(out)
    plt.close(fig)
    return out


def main():
    results = json.loads((OUT / "results.json").read_text())
    made = [plot_summary(results), plot_envelope(results), plot_method_graph(results)]
    qa = {}
    for fp in made:
        from PIL import Image
        im = Image.open(fp)
        qa[fp.name] = {"width": im.width, "height": im.height, "mode": im.mode,
                       "legible_min_size_px": bool(im.width >= 1000 and im.height >= 600)}
    (OUT / "image_qa.json").write_text(json.dumps(qa, indent=2))
    print("Wrote figures:")
    for fp in made:
        print(f"  {fp}")


if __name__ == "__main__":
    main()
