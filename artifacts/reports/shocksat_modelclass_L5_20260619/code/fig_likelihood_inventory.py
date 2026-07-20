#!/usr/bin/env python3
"""Deck figure — the FULL inventory of likelihood / observable formulations evaluated across the program
(Cards A + this thread), correcting the deck's 2-formulation oversimplification. Status from the result JSONs
(Card A out/ + this thread out/) and the decisions logs. Tufte gate: a clean status table-figure."""
from __future__ import annotations
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

WS = Path(__file__).resolve().parent.parent
FIG = WS / "figures"
G, R, Y = "#1b7837", "#b2182b", "#cc8800"   # green / red / amber

# (formulation, observable, converges?, key result, status_color)
rows = [
    ("L5 modal peak-FREQUENCY", "matched modal freqs", "YES (R̂ 1.002)", "WORKING twin; held-out freq skill +0.93", G),
    ("L8b Beck — INFER shape field (.ash)", "peak |H| + .ash MAC, free shapes", "YES (R̂ 1.003)", "SHARPENS amplitude: interval 1203→559 (−53%)", G),
    ("L8 Beck mode-shape (modal_beck)", "shape MAC", "YES (R̂ 1.004)", "shape likelihood converges", G),
    ("Stage-1 analytic statFEM evidence", "modal freqs (fixed θ)", "closed form", "Ockham: richer stiffness doesn't earn it", G),
    ("L6 freq + MAC (single-hit shapes)", "freqs + quadrature MAC", "YES", "MAC-as-θ-constraint: ~null sharpening", Y),
    ("L10 freq + MAC (.ash shapes)", "freqs + .ash MAC", "NO (R̂ 1.03, ESS 95)", "did not converge; ~null", Y),
    ("L4 complex (magnitude + PHASE)", "complex |H| + phase", "—", "phase adds NOTHING (single-hit phase incoherent)", Y),
    ("modal peak-AMPLITUDE feature", "matched peak amplitudes", "NO (R̂ 55.8)", "amplitude-feature likelihood multimodal", R),
    ("Whole-FRF MAGNITUDE", "log|H| all freqs", "NO (R̂ 104 NUTS / 129 TMCMC)", "locally identifiable; σ_d runaway", R),
    ("Schneider faithful correlated discrepancy", "whole-FRF + space×freq corr", "NO (R̂ 9.2 / 1.1)", "structured discrepancy, still multimodal", R),
    ("IFT / PIFT (physics-in-prior, β)", "log|H| + trust temperature", "YES via TMCMC", "robustness arm (parallel thread)", Y),
]
fig, ax = plt.subplots(figsize=(13.0, 6.4)); ax.axis("off")
ax.text(0.0, 1.02, "Likelihood / observable formulations evaluated (≥10 across the program — not 2)", fontsize=13, fontweight="bold", transform=ax.transAxes)
hdr = ["formulation", "observable", "converges?", "key result"]
xs = [0.0, 0.30, 0.55, 0.74]
for x, h in zip(xs, hdr):
    ax.text(x, 0.95, h, fontsize=9.5, fontweight="bold", transform=ax.transAxes)
ax.plot([0, 1], [0.93, 0.93], color="0.5", lw=0.8, transform=ax.transAxes)
y = 0.89
for name, obs, conv, res, col in rows:
    ax.add_patch(plt.Rectangle((-0.012, y - 0.008), 0.012, 0.03, color=col, transform=ax.transAxes, clip_on=False))
    ax.text(xs[0], y, name, fontsize=8.6, transform=ax.transAxes, color="0.1")
    ax.text(xs[1], y, obs, fontsize=8.0, transform=ax.transAxes, color="0.35")
    ax.text(xs[2], y, conv, fontsize=8.0, transform=ax.transAxes, color=col, fontweight="bold")
    ax.text(xs[3], y, res, fontsize=8.0, transform=ax.transAxes, color="0.2")
    y -= 0.072
ax.text(0.0, y - 0.01, "Green = converges & useful   Amber = converges/null or single-hit limit   Red = non-converged / multimodal",
        fontsize=8, transform=ax.transAxes, color="0.4")
ax.text(0.0, y - 0.055, "Headline: the converging, useful observables are MODAL (frequency + the inferred shape field). The whole-FRF / "
        "amplitude-feature / correlated-discrepancy formulations are multimodal on this single-impact data.",
        fontsize=8.2, transform=ax.transAxes, color="#1f335e", fontweight="bold")
fig.text(0.5, 0.01, "Sources: statfem_real_validation_20260617/out/{modal_feature,modal_beck,modal_beck_ash,modal_mac,modal_ash_mac,"
         "phase_likelihood,modal_amp_feature,paramcount,tmcmc_faithful_*}.json + this thread out/stage1_evidence.json; IFT thread (memory).",
         ha="center", fontsize=6.4, color="0.45")
fig.savefig(FIG / "fig_likelihood_inventory.png", dpi=140, bbox_inches="tight"); plt.close(fig)
print("wrote fig_likelihood_inventory.png")
