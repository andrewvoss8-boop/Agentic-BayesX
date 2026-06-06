# Matplotlib recipes for Tufte-style numeric graphics

Concrete "how" to turn the principles in [principles.md](principles.md) into
matplotlib defaults. Adapt to plotly/seaborn equivalently. These are starting
points, not a mandate — content and honesty win over any single setting.

## A reusable low-chartjunk style
```python
import matplotlib.pyplot as plt

TUFTE_RC = {
    "figure.dpi": 150,
    "savefig.dpi": 200,
    "font.size": 11,
    "axes.spines.top": False,      # erase frame ink
    "axes.spines.right": False,
    "axes.edgecolor": "#444444",
    "axes.linewidth": 0.8,
    "axes.grid": True,
    "grid.color": "#dddddd",       # muted gridlines, below data
    "grid.linewidth": 0.6,
    "axes.axisbelow": True,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.frameon": False,       # no legend box
    "axes.titlelocation": "left",  # titles read like sentences
}
plt.rcParams.update(TUFTE_RC)
```

## Erase non-data-ink
```python
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.tick_params(length=3)
# light gridlines only on the axis that helps value reading:
ax.grid(True, axis="y", color="#dddddd", linewidth=0.6)
ax.grid(False, axis="x")
```

## Direct labeling instead of a legend
```python
for name, y in series.items():
    ax.plot(x, y, linewidth=1.4)
    ax.annotate(name, xy=(x[-1], y[-1]), xytext=(4, 0),
                textcoords="offset points", va="center", fontsize=9)
ax.margins(x=0.08)  # room for the labels at line ends
```

## Range-frame (axes show the data range; ticks at quartiles)
```python
import numpy as np
def range_frame(ax, x, y):
    ax.spines["left"].set_bounds(np.min(y), np.max(y))
    ax.spines["bottom"].set_bounds(np.min(x), np.max(x))
    ax.set_yticks(np.quantile(y, [0, .25, .5, .75, 1]))
    ax.set_xticks(np.quantile(x, [0, .25, .5, .75, 1]))
```

## Small multiples with shared scales
```python
fig, axes = plt.subplots(2, 3, figsize=(9, 5), sharex=True, sharey=True)
for ax, (label, yk) in zip(axes.ravel(), cases.items()):
    ax.plot(x, yk, linewidth=1.2)
    ax.set_title(label, fontsize=9)        # label in place
# shared limits => honest comparison; one axis label set, not six
fig.supxlabel("frequency [Hz]"); fig.supylabel("apparent mass [kg]")
```

## Lie-factor hygiene
- Bar charts: `ax.set_ylim(bottom=0)` — never truncate a bar baseline.
- Don't encode a single number by area/volume (no bubble area for a scalar unless area = the quantity).
- Avoid `ax.twinx()` dual axes unless both scales are independently meaningful and labeled; never tune them to overlay two curves and imply correlation.
- No `projection="3d"` for data that is 1-D or 2-D.

## Color discipline
```python
# sequential / continuous -> perceptually uniform, NOT jet/rainbow
im = ax.pcolormesh(X, Y, Z, cmap="viridis")        # or "magma","cividis"
# categories -> few, distinguishable, colorblind-safe hues
CB = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#56B4E9", "#D55E00"]
# keep grayscale-legible: vary linestyle/marker too, not color alone
```

## Captions that do work
Put the quantity contract and provenance in the caption/title, e.g.:
> Load apparent mass M(f) = F_base / a_base [kg], driving-point, fixed-base BC.
> Synthetic truth (1 dataset, no flight-to-flight variability) vs posterior median
> + 95% band. Frequency axis log. Source: run runs/round3/opus48, 2026-06-04.

## Residual / zoom companion panel
```python
fig, (ax, axr) = plt.subplots(2, 1, height_ratios=[3, 1], sharex=True)
ax.plot(f, truth, label="truth"); ax.plot(f, pred, label="posterior median")
axr.plot(f, pred - truth); axr.axhline(0, color="#888", linewidth=0.7)
axr.set_ylabel("resid")
```

## Sparklines (word-sized, for tables of per-parameter diagnostics)
```python
def sparkline(ax, y):
    ax.plot(y, linewidth=0.8); ax.axis("off")
    ax.plot(len(y)-1, y[-1], "o", markersize=2)  # mark the latest value
# embed one tiny axes per table row (per-parameter trace / ESS history)
```

## matplotlib / plotly anti-defaults to override
- Turn off the top/right spines (default frame = chartjunk).
- Replace default tab10 only if you need colorblind safety; keep series few.
- Remove the legend box; prefer direct labels.
- For frequency-domain structural-dynamics plots use `ax.set_xscale("log")`
  unless you justify linear (project rule). State linear/dB explicitly; avoid dB
  unless standard for the quantity.
