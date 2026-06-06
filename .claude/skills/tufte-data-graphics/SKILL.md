---
name: tufte-data-graphics
description: Apply Edward Tufte's principles for displaying quantitative information whenever you generate, edit, or review a visual graph of numeric data (matplotlib/plotly/seaborn plots, FRF/PSD/time-history curves, posterior/QOI figures, charts, dashboards, report figures). Use to maximize data-ink, kill chartjunk, keep the lie factor near 1, label data directly, and document scales/sources so a reader can audit the numbers.
---

# Tufte Data Graphics

Make every figure of numeric data show the data honestly, densely, and clearly,
following Edward Tufte's published corpus (five books; see
[references/principles.md](references/principles.md) for sources and the full
rationale).

## When this applies
Any time you produce or modify a graphic that displays numbers: matplotlib /
plotly / seaborn / ggplot figures, FRF / PSD / time-history overlays, posterior
and QOI plots, sensitivity charts, convergence diagnostics, tables-as-figures,
or report/packet figures. If you are about to write plotting code or a checker
for a quantity, read this first.

## The one rule above all
**Show the data.** The graphic exists to let a reader compare numbers and find
your mistakes, not to decorate a report. If a design choice hides, distorts, or
crowds out the data, change the choice.

## Tufte's six analytical-design principles (the keystone — *Beautiful Evidence*)
1. **Show comparisons** — every QOI gets a baseline/reference/contrast (truth vs observed, prior vs posterior, with vs without discrepancy).
2. **Show causality/structure** — make the mechanism visible (annotate the resonance, the mode, the interface).
3. **Show multivariate data** — do not flatten to one variable when the decision depends on several; use small multiples.
4. **Integrate words, numbers, images** — label the data *on* the plot; captions carry the numbers.
5. **Document** — name the source, units, measurement scale, date, and what is synthetic vs measured.
6. **Content counts most** — a beautiful plot of the wrong quantity is a failure; pin the quantity contract first.

## Working checklist (apply before saving any figure)
- [ ] **Data-ink.** Erase non-data ink: heavy borders, dense gridlines, background fills, redundant tick labels, 3-D effects, drop shadows, gratuitous color. Keep ink that carries a number.
- [ ] **No chartjunk.** No moiré/hatch fills, no decorative "ducks", no 3-D bars/pies, no skeuomorphism. Light, thin gridlines only where they aid reading values.
- [ ] **Lie factor ≈ 1.** Visual size of an effect = numeric size of the effect (target 0.95–1.05). Proportional axes; bar charts start at zero; no truncated/dual axes that exaggerate.
- [ ] **Direct labeling.** Prefer labels at the end of each line over a legend that forces eye travel. If a legend is unavoidable, order it to match the curves.
- [ ] **Honest scales, documented.** State linear vs log on each axis and why. (Project rule: frequency axes log unless justified; avoid dB unless standard for the quantity — state linear/dB explicitly.)
- [ ] **Range/quartile awareness.** Let axes/ticks show the data's actual range; show spread (CI bands, residuals), not just a mean line.
- [ ] **Small multiples** for comparison across cases/parameters/flights instead of one overloaded panel or many inconsistent one-offs (same scales across panels).
- [ ] **Show residual/zoom.** When a full-scale overlay can hide meaningful differences, add a residual or zoom panel (already a project gate).
- [ ] **Absolute vs normalized.** Show absolute injected error/noise separately from normalized diagnostics; label normalized plots as diagnostics and explain the denominator.
- [ ] **Color discipline.** Color encodes data or distinguishes series; use few, distinguishable hues; never color as decoration. Keep grayscale-legible where possible.
- [ ] **Caption does work.** Caption states the quantity (numerator/denominator/coordinate/units), data count (datasets/replicates), synthetic-vs-measured, and the takeaway.
- [ ] **1 + 1 = 3.** Too many separators/borders create visual noise; remove rules between panels when whitespace already separates them.

## Anti-patterns to refuse
Pie charts (use a bar chart or table — Tufte: "the only design worse than a pie
chart is several of them"); 3-D bar/line charts; dual y-axes scaled to imply a
correlation; truncated bar baselines; rainbow/jet colormaps for sequential data
(use perceptually uniform e.g. viridis); legends when direct labels fit;
red/green as the only distinction; chartjunk backgrounds.

## How to use this skill
1. Read this checklist; for the concrete matplotlib "how", see
   [references/matplotlib-recipes.md](references/matplotlib-recipes.md).
2. For this project's structural-dynamics figures (FRF/PSD/posterior/QOI) and how
   these rules combine with the existing CLAUDE.md figure gates, see
   [references/project-domain.md](references/project-domain.md).
3. **Optional heuristic lint:** after writing a plotting script, run
   `python .claude/skills/tufte-data-graphics/scripts/tufte_lint.py <plot_script.py>`
   to flag common violations (3-D, jet/rainbow, pie, dB-without-justification,
   linear-frequency, legend-when-direct-label-fits). It is a heuristic aid, not a
   proof of quality — a clean lint does not mean the figure is good.
4. Do not claim a figure "follows Tufte" unless you actually applied the
   checklist; note any deliberate deviation and why (Tufte's rules are guidance,
   not law — content and honesty win over any single rule).
