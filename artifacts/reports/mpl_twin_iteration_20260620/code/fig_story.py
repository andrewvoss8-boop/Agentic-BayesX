#!/usr/bin/env python3
"""Story figures for the findings deck (Tufte gate applied). Generates:
  fig_geometry.png              - FEM stand + the 6 accel locations (sensor map)
  fig_measured_transmissibility.png - the gain-free |T| curves we try to predict (the DATA)
  fig_modal_forest.png          - FEM mode density (dense forest) + measured peaks + alive-modes/location
  fig_graphical_model.png       - run-specific statFEM observation-model / likelihood schematic
  fig_strain_energy.png         - modal strain-energy fraction per calibrated K-group (identifiability)
All numeric figures carry a run stamp; no jet/dB; log-frequency where applicable.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mpl_fem as FF
import mpl_freq as MF

WS = Path(__file__).resolve().parents[1]; OUT = WS / "out"; FIG = WS / "figures"
FIG.mkdir(exist_ok=True)
STAMP = "run mpl_twin_iteration_20260620"
REGION_COLORS = {"frame": "#9aa0a6", "shield": "#1f4e79", "thrust_plate": "#6aa84f",
                 "valve_panel": "#c1452b", "electronics_box": "#e69138", "white_box_upper": "#8e7cc3"}
LOC_MARK = {"interface": "o", "beam": "s", "valve": "^", "avi-L": "D", "avi-R": "D", "shield": "*"}


def fig_geometry():
    fem = FF.FEM_model()
    X = fem.X; reg = fem.region
    fig = plt.figure(figsize=(13, 5.6))
    for sp, (az, el, ttl) in enumerate([(-72, 18, "logo (+X) view"), (18, 22, "side view")]):
        ax = fig.add_subplot(1, 2, sp + 1, projection="3d")
        for rname, c in REGION_COLORS.items():
            m = reg == rname
            if m.sum():
                ax.scatter(X[m, 0], X[m, 1], X[m, 2], s=4, c=c, alpha=0.35, label=rname if sp == 0 else None)
        for loc, g in fem.NODE_GRID.items():
            p = X[fem.gpos[int(g)]]
            ax.scatter(*p, s=90, marker=LOC_MARK[loc], edgecolor="k", facecolor="yellow", zorder=5)
            ax.text(p[0], p[1], p[2], f"  {loc}", fontsize=8, weight="bold")
        gp = fem.X[fem.gpos[int(fem.NODE_GRID["shield"])]]  # also mark shield ref explicitly handled above
        ax.view_init(elev=el, azim=az); ax.set_title(ttl, fontsize=9)
        ax.set_xlabel("X (OOP)"); ax.set_ylabel("Y"); ax.set_zlabel("Z"); ax.tick_params(labelsize=6)
    fig.legend(loc="lower center", ncol=6, fontsize=7, frameon=False)
    fig.suptitle("MPL stand FEM — accel locations (yellow) on the shield (blue) / frame; sensor axis = OOP (+X). "
                 "Shield = transmissibility reference.", fontsize=10)
    fig.text(0.99, 0.01, STAMP, ha="right", fontsize=6, color="#666")
    fig.tight_layout(rect=[0, 0.06, 1, 0.95])
    fig.savefig(FIG / "fig_geometry.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("wrote fig_geometry.png")


def fig_measured():
    d = np.load(OUT / "measured_transmissibility.npz"); f = d["freqs"]
    fig, ax = plt.subplots(figsize=(11, 5.4))
    cols = {"interface": "#1f4e79", "beam": "#6aa84f", "valve": "#c1452b", "avi-L": "#e69138", "avi-R": "#8e7cc3"}
    for loc, c in cols.items():
        ax.loglog(f, d[f"T_{loc}"], color=c, lw=1.1, alpha=0.9)
        imax = int(np.argmax(d[f"T_{loc}"]))
        ax.text(f[imax], d[f"T_{loc}"][imax], f" {loc}", color=c, fontsize=8, weight="bold")
    ax.axhline(1.0, color="k", lw=0.7, ls="--"); ax.text(f[2], 1.05, "shield reference (|T|≡1)", fontsize=7)
    ax.set_xlabel("frequency (Hz, log)"); ax.set_ylabel("|T| = √(PSD_a/PSD_shield)  (–, log)")
    ax.set_title("The DATA to predict: gain-free output/output transmissibility at the 5 held-out locations "
                 "(uncoupled, OOP axis, fixed acoustic field)", fontsize=10, loc="left")
    ax.grid(True, which="both", lw=0.3, alpha=0.3)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.text(0.99, 0.01, STAMP, ha="right", fontsize=6, color="#666")
    fig.tight_layout()
    fig.savefig(FIG / "fig_measured_transmissibility.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("wrote fig_measured_transmissibility.png")


def fig_modal_forest():
    P = MF.precompute()
    fr = P["freqs"]; fr = fr[(fr >= 0) & (fr <= 300)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8))
    a1.hist(fr, bins=np.arange(0, 305, 10), color="#1f4e79", alpha=0.85)
    allpk = sorted(set(p for loc in MF.HELD for p in P["mpk"][loc]))
    for p in allpk:
        a1.axvline(p, color="#c1452b", lw=0.8, alpha=0.7)
    a1.set_xlabel("frequency (Hz)"); a1.set_ylabel("FEM modes per 10 Hz")
    a1.set_title(f"DENSE modal forest: {len(fr)} FEM modes < 300 Hz (red = measured peaks)", fontsize=9, loc="left")
    for s in ("top", "right"): a1.spines[s].set_visible(False)
    locs = MF.HELD + ["shield"]; al = [MF.alive_modes(P, l).size for l in locs]
    a2.barh(range(len(locs)), al, color="#6aa84f")
    a2.set_yticks(range(len(locs))); a2.set_yticklabels(locs, fontsize=8)
    a2.set_xlabel("# FEM modes 'alive' at the node (|φ_x| ≥ 10% of max)")
    a2.set_title("29–71 alive modes/node ⇒ a mode sits near every measured peak", fontsize=9, loc="left")
    for s in ("top", "right"): a2.spines[s].set_visible(False)
    fig.suptitle("Why FREQUENCY is a weak discriminator on this stand", fontsize=10)
    fig.text(0.99, 0.01, STAMP, ha="right", fontsize=6, color="#666")
    fig.tight_layout(rect=[0, 0.03, 1, 0.94])
    fig.savefig(FIG / "fig_modal_forest.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("wrote fig_modal_forest.png")


def fig_graphical_model():
    fig, ax = plt.subplots(figsize=(12, 5.6)); ax.axis("off"); ax.set_xlim(0, 12); ax.set_ylim(0, 7)

    def box(x, y, w, h, t, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", fc=fc, ec="k", lw=1.0))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=8.5)

    def arrow(x0, y0, x1, y1):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=12, color="#444", lw=1.2))

    box(0.3, 5.2, 2.6, 1.1, "K-group scalars θ\n(6 stiffness)\nprior logN(0,0.12)", "#dbe5f1")
    box(0.3, 3.4, 2.6, 1.1, "modal damping ζ\nprior logN(log1%,0.5)", "#dbe5f1")
    box(3.6, 4.3, 3.0, 1.6, "FEM forward (differentiable)\nλ_i(θ)=λ0_i(1+Σ_g SE_{i,g}(θ_g−1))\nT_a=|Σφ_aγ_i/D_i| / |Σφ_refγ_i/D_i|\n(input spectrum CANCELS)", "#e8f0e0")
    box(7.4, 5.2, 2.4, 1.1, "global centering c\n(training-only, gain-free)", "#dbe5f1")
    box(7.4, 3.4, 2.4, 1.1, "discrepancy d + noise\nlog|T| ~ N(·, σ_d²)", "#dbe5f1")
    box(10.2, 4.3, 1.6, 1.1, "measured\nlog|T_a(f)|", "#f4d7d0")
    arrow(2.9, 5.6, 3.6, 5.4); arrow(2.9, 3.9, 3.6, 4.7)
    arrow(6.6, 5.2, 7.4, 5.7); arrow(6.6, 4.5, 7.4, 4.0)
    arrow(9.8, 5.6, 10.4, 5.4); arrow(9.8, 3.9, 10.4, 4.7)
    ax.text(6, 6.6, "statFEM observation model on the no-force transmissibility (this run): "
            "y = forward(θ,ζ) + c + d + e", ha="center", fontsize=10, weight="bold")
    ax.text(6, 0.5, "FREQUENCY likelihood (headline) matches measured peaks ↔ alive FEM modes via λ_i(θ); "
            "whole-curve log|T| likelihood is the transmissibility arm. NUTS, ≥4 chains, convergence-gated.",
            ha="center", fontsize=8)
    ax.text(11.9, 0.05, STAMP, ha="right", fontsize=6, color="#666")
    fig.savefig(FIG / "fig_graphical_model.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("wrote fig_graphical_model.png")


def fig_strain_energy():
    P = MF.precompute()
    fr = P["freqs"]; m = fr <= 300
    fig, ax = plt.subplots(figsize=(12, 5.0))
    cols = plt.cm.tab10(np.linspace(0, 1, len(P["groups"])))
    for i, g in enumerate(P["groups"]):
        ax.plot(fr[m], P["se"][g][m], ".", ms=3, color=cols[i], label=g.replace("K_", ""))
    ax.set_xlabel("FEM mode frequency (Hz)"); ax.set_ylabel("modal strain-energy fraction f_{i,g} = φᵀK_gφ/λ")
    ax.set_title("Identifiability: which modes store strain energy in each calibrated K-group "
                 "(= the parameter→frequency sensitivity)", fontsize=9, loc="left")
    ax.set_ylim(0, 1.0); ax.legend(fontsize=7, frameon=False, ncol=3)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.text(0.99, 0.01, STAMP, ha="right", fontsize=6, color="#666")
    fig.tight_layout()
    fig.savefig(FIG / "fig_strain_energy.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("wrote fig_strain_energy.png")


def fig_near_resonance():
    nr = json.loads((OUT / "near_resonance.json").read_text()); pr = nr["pairs"]
    cols = {"interface": "#1f4e79", "beam": "#6aa84f", "valve": "#c1452b", "avi-L": "#e69138", "avi-R": "#8e7cc3"}
    fig, ax = plt.subplots(figsize=(8.2, 6.2))
    for loc, c in cols.items():
        xs = [np.log10(p["pred_ratio"] + 1e-9) for p in pr if p["loc"] == loc]
        ys = [np.log10(p["meas_peak_T"] + 1e-9) for p in pr if p["loc"] == loc]
        ax.scatter(xs, ys, s=55, color=c, edgecolor="k", lw=0.4, label=loc)
    lim = [-2.6, 1.2]
    ax.plot(lim, lim, "k--", lw=0.7, alpha=0.5)
    ax.text(lim[0] + 0.1, lim[0] + 0.25, "1:1 (perfect shape match)", fontsize=7, rotation=38, color="#555")
    ax.set_xlim(lim); ax.set_xlabel("log10  FEM |φ_a/φ_ref|  at nearest alive mode (load-free prediction)")
    ax.set_ylabel("log10  measured peak |T|")
    ax.set_title(f"(a) load-free near-resonance test: log-corr = {nr['log_corr_meas_vs_phi_ratio']:+.2f} "
                 f"(n={nr['n_pairs']})\nweak ⇒ shape ceiling is mode-shape error, NOT the unknown load",
                 fontsize=9, loc="left")
    ax.legend(fontsize=8, frameon=False, title="held-out loc")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    fig.text(0.99, 0.01, STAMP, ha="right", fontsize=6, color="#666")
    fig.tight_layout()
    fig.savefig(FIG / "fig_near_resonance.png", dpi=150, bbox_inches="tight"); plt.close(fig)
    print("wrote fig_near_resonance.png")


if __name__ == "__main__":
    fig_geometry(); fig_measured(); fig_modal_forest(); fig_graphical_model()
    fig_strain_energy(); fig_near_resonance()
