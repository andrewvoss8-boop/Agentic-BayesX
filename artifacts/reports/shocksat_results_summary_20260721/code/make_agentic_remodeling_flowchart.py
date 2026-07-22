#!/usr/bin/env python3
"""Create the conceptual current-vs-planned agentic-remodeling flowchart.

This is a process schematic, not a numeric result. Solid blue boxes are
implemented components; dashed orange boxes are the proposed agent-facing CLI
and feedback-training layer.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "figures_revised" / "fig3_agentic_remodeling_cli.png"

NAVY = "#17365D"
BLUE = "#2E74B5"
PALE_BLUE = "#EAF2F8"
ORANGE = "#C56A2D"
PALE_ORANGE = "#FFF2E8"
INK = "#222222"
GREY = "#666666"
WHITE = "#FFFFFF"


def box(ax, xy, width, height, title, body, *, planned=False, title_size=11.2, body_size=8.8):
    color = ORANGE if planned else BLUE
    fill = PALE_ORANGE if planned else PALE_BLUE
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.8,
        edgecolor=color,
        facecolor=fill,
        linestyle=(0, (5, 3)) if planned else "solid",
        zorder=2,
    )
    ax.add_patch(patch)
    x, y = xy
    ax.text(x + width / 2, y + height - 0.035, title, ha="center", va="top",
            fontsize=title_size, fontweight="bold", color=NAVY if not planned else ORANGE, zorder=3)
    ax.text(x + width / 2, y + height - 0.105, body, ha="center", va="top",
            fontsize=body_size, color=INK, linespacing=1.22, zorder=3)
    return patch


def arrow(ax, start, end, *, color=GREY, rad=0.0, dashed=False, width=1.8):
    patch = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=12,
        linewidth=width,
        color=color,
        linestyle=(0, (4, 3)) if dashed else "solid",
        connectionstyle=f"arc3,rad={rad}",
        shrinkA=2,
        shrinkB=2,
        zorder=1,
    )
    ax.add_patch(patch)


def build() -> None:
    fig, ax = plt.subplots(figsize=(13.0, 6.7), dpi=180)
    fig.patch.set_facecolor(WHITE)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.035, 0.955, "Controlled model-form search: the agent is one proposer",
            ha="left", va="top", fontsize=19, color=NAVY, fontweight="bold")
    ax.text(0.035, 0.895,
            "Remeshing is one discrete operator family. Bayesian property updating occurs inside each valid model class.",
            ha="left", va="top", fontsize=11.3, color=GREY)

    box(ax, (0.035, 0.55), 0.145, 0.235, "Agent + short skill",
        "Chooses a registered\ndiscrete operator", planned=True,
        title_size=11.0, body_size=9.8)
    box(ax, (0.215, 0.55), 0.18, 0.235, "candidate.json",
        "Connectivity · joints\nHardware · geometry\nElement form · mesh",
        title_size=11.6, body_size=9.6)

    wrapper = FancyBboxPatch(
        (0.43, 0.29), 0.35, 0.54,
        boxstyle="round,pad=0.015,rounding_size=0.02",
        linewidth=2.0, edgecolor=ORANGE, facecolor="#FFFCF8",
        linestyle=(0, (6, 3)), zorder=0,
    )
    ax.add_patch(wrapper)
    ax.text(0.605, 0.805, "remodelctl  (proposed CLI wrapper)",
            ha="center", va="top", fontsize=11.8, color=ORANGE, fontweight="bold")

    box(ax, (0.455, 0.665), 0.30, 0.105, "1  Build the registered edit",
        "", title_size=11.0)
    box(ax, (0.455, 0.545), 0.30, 0.105, "2  Verify the mechanics",
        "", title_size=11.0)
    box(ax, (0.455, 0.425), 0.30, 0.105, "3  Bayesian update within class",
        "", title_size=11.0)
    box(ax, (0.455, 0.305), 0.30, 0.105, "4  Score with protected splits",
        "", title_size=11.0)

    box(ax, (0.82, 0.55), 0.155, 0.235, "Structured feedback",
        "Failure code\nTRAIN diagnostic\nRestricted DEV score", planned=True,
        title_size=10.8, body_size=9.5)

    arrow(ax, (0.18, 0.665), (0.215, 0.665), color=BLUE)
    arrow(ax, (0.395, 0.665), (0.43, 0.665), color=BLUE)
    arrow(ax, (0.78, 0.665), (0.82, 0.665), color=ORANGE, dashed=True)
    arrow(ax, (0.895, 0.55), (0.11, 0.54), color=ORANGE, dashed=True, rad=-0.28, width=1.7)

    ax.text(
        0.035, 0.205,
        "Agent boundary: it cannot change the verifier, data split, acceptance thresholds, budgets, scoring code, or final checker.",
        ha="left", va="center", fontsize=10.3, color=NAVY, fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.35", facecolor="#F2F4F7", edgecolor="#C9CED6", linewidth=1.0),
    )
    ax.text(0.035, 0.12,
            "EXISTS NOW    Candidate schema · registered operators/builders · verifier gates · protected splits · exact candidate scoring",
            ha="left", va="center", fontsize=9.7, color=BLUE, fontweight="bold")
    ax.text(0.035, 0.065,
            "NEXT INCREMENT    One CLI · stable JSON diagnostics · blind test: no feedback vs pass/fail vs structured feedback",
            ha="left", va="center", fontsize=9.7, color=ORANGE, fontweight="bold")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=220, bbox_inches="tight", facecolor=WHITE)
    plt.close(fig)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
