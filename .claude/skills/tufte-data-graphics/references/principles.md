# Tufte's corpus — principles and sources

This file compiles the principles from Edward R. Tufte's published books. It was
written from the established/published corpus, not a live web scrape. Where you
need exact wording or page numbers, consult the books directly (cited below).

## Primary sources (Tufte's books)
1. **The Visual Display of Quantitative Information**, 2nd ed., Graphics Press, 2001 (1st ed. 1983). — data-ink, chartjunk, lie factor, data density, graphical integrity/excellence.
2. **Envisioning Information**, Graphics Press, 1990. — escaping flatland, micro/macro, layering & separation, small multiples, color, "smallest effective difference", 1+1=3 clutter.
3. **Visual Explanations**, Graphics Press, 1997. — images/quantities/evidence, causality, the Challenger and cholera-map case studies, animation, disinformation.
4. **Beautiful Evidence**, Graphics Press, 2006. — the six analytical-design principles, sparklines, data-rich word-sized graphics, mapped pictures, "corrupt techniques".
5. **Seeing with Fresh Eyes**, Graphics Press, 2020. — observation, comparisons, content reasoning, contemporary examples.

Supplementary: Tufte's essays and forum at tufte.com (not fetched this session).

## Graphical excellence (VDQI)
> Graphical excellence is that which gives to the viewer the greatest number of
> ideas in the shortest time with the least ink in the smallest space.

Excellence = well-designed presentation of interesting data: substance,
statistics, design together. It is nearly always **multivariate** and it
**tells the truth** about the data.

## The six analytical-design principles (Beautiful Evidence) — the keystone
1. **Comparisons.** Show comparisons, contrasts, differences. "Compared with what?" is the first question of statistical thinking.
2. **Causality, mechanism, structure, explanation.** Move from description to why.
3. **Multivariate.** Show more than one or two variables; the world is multivariate, so reasoning about it should be too.
4. **Integration of evidence.** Completely integrate words, numbers, images, diagrams. Whatever it takes to explain — don't segregate by mode of production.
5. **Documentation.** Provide a detailed title, indicate authors/sponsors, document data sources, show complete measurement scales, point out relevant issues.
6. **Content counts most of all.** Analytical presentations ultimately stand or fall on the quality, relevance, and integrity of their content.

## Data-ink and the data-ink ratio (VDQI)
- **Data-ink** = the non-erasable core of a graphic, the ink that represents data.
- **Data-ink ratio** = data-ink / total ink used = proportion of a graphic's ink devoted to the non-redundant display of data-information.
- Principles: **maximize the data-ink ratio, within reason**; **erase non-data-ink**; **erase redundant data-ink**; **revise and edit**.
- Practical erasures: kill the frame/box, most gridlines, tick redundancy, background shading, and any "container" that carries no number.

## Chartjunk (VDQI)
Interior decoration that carries no information. Three offenders:
- **Unintentional optical art / moiré vibration** — dense hatching, cross-hatch, vibrating patterns.
- **The grid** — heavy gridlines competing with the data; mute or remove them.
- **The duck** — a graphic so dominated by decoration that the form swamps the content (named after the Big Duck building).
Modern ducks: 3-D bars, gradient fills, drop shadows, clip-art, "infographic" icons standing in for numbers.

## Graphical integrity & the Lie Factor (VDQI)
- **Lie Factor = (size of effect shown in the graphic) / (size of effect in the data).** Honest graphics have Lie Factor ≈ 1.0 (roughly 0.95–1.05).
- Six integrity principles:
  1. Representation of numbers, as physically measured on the graphic, should be **directly proportional** to the quantities.
  2. Clear, detailed, thorough **labeling**; label important events in the data.
  3. Show **data variation, not design variation**.
  4. For money/time series, use **standardized/deflated** units where relevant.
  5. **Number of dimensions in the graphic ≤ number of dimensions in the data** (no 3-D for 1-D data; no area/volume encoding a single number).
  6. Don't **quote data out of context**; show enough surrounding data.

## Data density & small multiples (VDQI, Envisioning Information)
- **Data density** = number of entries in the data matrix / area of the graphic. Maximize within reason; "graphics can be shrunk way down."
- **Small multiples**: repeated small frames sharing scales/structure, varying one variable. They invite comparison, are efficient, and resist distortion. Use them instead of one overloaded panel.

## Layering, separation & color (Envisioning Information)
- **Layering and separation**: organize ink into visual layers (foreground data, background context) using value/weight, not noise.
- **1 + 1 = 3 (or more)**: every added line/border creates extra visual interactions; clutter multiplies. Remove unneeded separators; let whitespace separate.
- **Smallest effective difference**: make visual distinctions **as subtle as possible while still clear** — minimum contrast that does the job.
- **Color**: use sparingly and purposefully — to label (distinguish categories), to measure (sequential/diverging scales), to represent reality, or to enliven. Avoid loud, clashing palettes. Prefer muted "colors of nature." For sequential data use perceptually uniform maps; avoid rainbow/jet.

## Micro/macro readings & escaping flatland (Envisioning Information)
- Rich detail at the micro level can coexist with macro structure; high resolution lets readers select their own stories. Detail is not clutter when it is organized.
- **Escaping flatland**: real problems are multidimensional; the challenge is representing 3-D+ information on 2-D surfaces honestly (small multiples, layering, careful projection — not gratuitous 3-D effects).

## Integration of text and graphics (Beautiful Evidence)
- Words and pictures belong together; annotate the data **in place**. Avoid legends that force the eye to ping-pong; put labels next to the lines they name.
- **Multifunctioning graphical elements**: an element can carry data and also do labeling/structuring work (e.g., a data point that is also a tick).
- **Range-frame / dot-dash-plot**: let the axis lines themselves show the data range and marginal distribution (e.g., axes spanning only min→max; ticks at quartiles).

## Sparklines (Beautiful Evidence)
- **Sparkline** = a small, intense, word-sized graphic with typographic resolution, embedded in text/tables. Use for dense time series, diagnostics, and per-row trends where a full chart is overkill. Good fit for per-parameter posterior trace/ESS summaries inline in a table.

## Corrupt techniques Tufte names to avoid
- **Pie charts** — low data density, hard to compare angles. "The only design worse than a pie chart is several of them." Prefer a sorted bar chart or a table.
- **Chartjunk / 3-D effects / ducks** (above).
- **Disproportionate scaling** (area/volume for 1-D data) → inflated Lie Factor.
- **Dual axes** scaled to manufacture a correlation.
- **Truncated baselines** on bar charts.
- **Over-encoding** with redundant color + pattern + label for one distinction.

## Quick mnemonic
Show the data → erase non-data-ink → erase redundant data-ink → tell the truth
(Lie Factor ≈ 1) → label in place → document scales/sources → content first.
