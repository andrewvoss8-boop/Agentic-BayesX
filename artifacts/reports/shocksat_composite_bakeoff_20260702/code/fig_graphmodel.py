#!/usr/bin/env python3
"""Run-specific graphical model / likelihood diagram for the composite bake-off (pure schematic — no numeric
data; Plot-Gate exemption for schematics noted). Shows the three shape-use likelihoods (S0/S1/S2), the model
axis (M0/M1 candidate blocks), the always-on statFEM F(k) output discrepancy, and what is inferred vs fixed."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"; FIG.mkdir(exist_ok=True)


def box(ax, xy, w, h, text, fc="#eef2f7", ec="#1f4e79", fs=8, style="round,pad=0.02"):
    b = FancyBboxPatch(xy, w, h, boxstyle=style, fc=fc, ec=ec, lw=1.1)
    ax.add_patch(b)
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, p0, p1, **kw):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=11,
                                 color=kw.get("color", "#444"), lw=kw.get("lw", 1.1),
                                 linestyle=kw.get("ls", "-")))


def main():
    fig, ax = plt.subplots(figsize=(12.5, 7.0))
    ax.set_xlim(0, 12.5); ax.set_ylim(0, 7); ax.axis("off")

    # priors / parameters
    box(ax, (0.3, 5.6), 2.6, 0.9, "log θ_p ~ N(0, 0.25)\np = 9 groups (M0)\n(+couple/joint params, M1)",
        fc="#f5eede", ec="#8a6d1f")
    box(ax, (0.3, 4.3), 2.6, 0.8, "σ_w2 ~ HalfN(0.15)\nσ_mac, σ_φ ~ HalfN(0.3)", fc="#f5eede", ec="#8a6d1f")
    box(ax, (0.3, 2.9), 2.6, 0.9, "S2 only:\nraw ~ N(0,1)^(80×nm)\nφ = φ_FEM + 0.3·raw", fc="#f5eede",
        ec="#8a6d1f")

    # model axis
    box(ax, (3.6, 5.5), 3.0, 1.1, "K(θ) = A_fix + Σ θ_p A_p\n80-dim candidate basis\nM0 inherited | M1 remodel\n"
        "(tier-2 full eigensolve)", fc="#e8efe8", ec="#2b7a2b")
    box(ax, (3.6, 3.9), 3.0, 1.0, "eigh → λ_k(θ), Q(θ)\nfrozen Hungarian pairing\nto 33 .ash survey modes",
        fc="#e8efe8", ec="#2b7a2b")

    # likelihood blocks
    box(ax, (7.3, 5.7), 4.7, 0.85, "S0 freq (Kiran Eq 25):  ω̂²_r ~ N(λ_kr(θ), (σ_w2·ω̂²_r)²)   [all matched modes]",
        fc="#eef2f7")
    box(ax, (7.3, 4.65), 4.7, 0.85, "S1 freq+MAC:  + (1−MAC_r(θ))² / σ_mac²,  MAC on .ash live DOFs\n"
        "(differentiable jnp.eigh; A7 cluster-gradient caveat)", fc="#eef2f7")
    box(ax, (7.3, 3.6), 4.7, 0.85, "S2 Beck field: Rayleigh ω²(φ) freq term + MAC(φ, φ̂_ash) pull\n"
        "(mode-matching-free; shapes are parameters)", fc="#eef2f7")

    # data
    box(ax, (7.3, 2.45), 4.7, 0.75, "DATA: .ash EMA survey (33 modes × 76 nodes × 3 ax, freqs+shapes)\n"
        "5 tap-test drive caches = HELD OUT (answer keys only)", fc="#f7ecec", ec="#b03030")

    # QOI + F(k)
    box(ax, (3.6, 1.0), 3.4, 1.2, "net-CG QOI forward\nG_d(ω)=Σ g_i φ_d,i ω²/D_i\ntray z≥55in, ζ=0.01\n"
        "(7004C force convention)", fc="#e8efe8", ec="#2b7a2b")
    box(ax, (7.9, 1.0), 4.1, 1.2, "statFEM F(k) output discrepancy — ALWAYS ON\n1-oct-correlated log-amp field,"
        "\nmarginal 0.25→0.80 where unmeasured\nmodes drive (A4)", fc="#efe8f2", ec="#6f2b7a")

    arrow(ax, (2.9, 6.0), (3.6, 6.0))
    arrow(ax, (5.1, 5.5), (5.1, 4.9))
    arrow(ax, (6.6, 4.4), (7.3, 6.0)); arrow(ax, (6.6, 4.4), (7.3, 5.05)); arrow(ax, (6.6, 4.4), (7.3, 4.0))
    arrow(ax, (2.9, 3.35), (7.3, 3.85), color="#8a6d1f")
    arrow(ax, (9.6, 3.6), (9.6, 3.2), color="#b03030")   # data into likelihoods
    arrow(ax, (5.1, 3.9), (5.1, 2.2))
    arrow(ax, (7.0, 1.6), (7.9, 1.6))
    arrow(ax, (2.9, 4.7), (7.3, 5.9), color="#8a6d1f", ls="--")

    ax.set_title("Composite bake-off: run-specific graphical model (M{0,1} × S{0,1,2} + F(k)); "
                 "posterior θ (and φ for S2) via NUTS, 4 chains, x64", fontsize=10, loc="left")
    fig.text(0.01, 0.01, "SCHEMATIC (no numeric data). Inferred: θ, σ_w2, (σ_mac | σ_φ, raw), one global gain "
             "per held-out fold. Fixed: ζ=0.01, tier σ's (A2/A3), F(k) form (A4), tray region, pairing. "
             "NOT inferred: per-mode true amplitudes (tier MC), unmeasured drumhead shapes. "
             "Workspace: shocksat_composite_bakeoff_20260702.", fontsize=7.3)
    fig.savefig(FIG / "fig_graphmodel.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("wrote fig_graphmodel.png")


if __name__ == "__main__":
    main()
