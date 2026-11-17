#!/usr/bin/env python3
"""Recover numeric curves from a raster FRF plot (one magnitude panel, linear
frequency axis, logarithmic magnitude axis, curves distinguished by colour).

Why: NASA's correlation deck shows test-versus-FEM frequency response functions
(FRFs) only as pictures. Reading the numbers back out of the pixels lets the
FEM-versus-test gap on NASA's modal-quality data be measured with data in hand.

How (plain English):
 1. Find the plot panel: the largest block of rows and columns that is not the
    figure's grey background.
 2. Find the solid light-grey gridlines. They sit at known axis values (every
    50 Hz; every power of ten), so a straight-line fit of pixel position against
    axis value gives the pixel-to-value calibration.
 3. In every pixel column, collect the pixels of each curve colour. The curve value
    for that column is the centre of those pixels (in log magnitude); the top and
    bottom of the stroke are kept as well, because a resonance narrower than one
    pixel is drawn as a vertical stroke.

Limits that the known-answer test (test_digitize.py) measures rather than assumes:
one pixel is about 0.36 Hz and 0.2 dB in the NASA figures; a curve hidden under
another curve is assigned the covering curve's value and flagged.

Units: frequency Hz; magnitude in the plot's own unit (g/lbf for the NASA figures).
"""
from __future__ import annotations

import dataclasses
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image


@dataclasses.dataclass
class Calibration:
    r0: int; r1: int; c0: int; c1: int        # panel bounds, inclusive pixel indices
    px_per_hz: float; col_at_0hz: float       # column = col_at_0hz + px_per_hz * f
    px_per_decade: float; row_at_1: float     # row = row_at_1 - px_per_decade * log10(value)
    v_grid_cols: List[int]; h_grid_rows: List[int]
    x_fit_resid_px: float; y_fit_resid_px: float

    def col_to_hz(self, c):
        return (np.asarray(c, float) - self.col_at_0hz) / self.px_per_hz

    def row_to_log10(self, r):
        return (self.row_at_1 - np.asarray(r, float)) / self.px_per_decade

    @property
    def hz_per_px(self):
        return 1.0 / self.px_per_hz

    @property
    def db_per_px(self):
        return 20.0 / self.px_per_decade


def _runs(idx: Sequence[int]) -> List[Tuple[int, int]]:
    idx = [int(i) for i in idx]
    if not idx:
        return []
    out = [[idx[0], idx[0]]]
    for v in idx[1:]:
        if v == out[-1][1] + 1:
            out[-1][1] = v
        else:
            out.append([v, v])
    return [tuple(r) for r in out]


def find_panel(im: np.ndarray, background=(240, 240, 240)) -> Tuple[int, int, int, int]:
    """Largest block of rows, then columns, in which more than half the pixels differ
    from the figure background colour."""
    nonbg = ~(im == np.array(background)).all(2)
    r0, r1 = max(_runs(np.where(nonbg.mean(1) > 0.5)[0]), key=lambda r: r[1] - r[0])
    c0, c1 = max(_runs(np.where(nonbg[r0:r1 + 1].mean(0) > 0.5)[0]), key=lambda r: r[1] - r[0])
    return r0, r1, c0, c1


def _grid_lines(sub: np.ndarray, axis: int, lo=200, hi=238, frac=0.6) -> List[int]:
    """Indices (along `axis`) of solid neutral light-grey lines: at least `frac` of the
    pixels along the line are grey with equal R, G, B between lo and hi."""
    grey = (sub[:, :, 0] == sub[:, :, 1]) & (sub[:, :, 1] == sub[:, :, 2]) & (sub[:, :, 0] >= lo) & (sub[:, :, 0] <= hi)
    f = grey.mean(0 if axis == 1 else 1)
    return [int(np.mean(r)) for r in _runs(np.where(f > frac)[0])]


def _fit_comb(pos: Sequence[float], step_guess: float, anchor_pos: float, anchor_val: float, val_step: float):
    """Assign each detected gridline an axis value by its distance from an anchor line
    (in whole steps), then least-squares fit position = a + b * value."""
    pos = np.asarray(pos, float)
    k = np.round((pos - anchor_pos) / step_guess)
    vals = anchor_val + k * val_step
    b, a = np.polyfit(vals, pos, 1)
    resid = float(np.max(np.abs(a + b * vals - pos)))
    return a, b, resid


def calibrate(im: np.ndarray, x_grid_step_hz: float, x_anchor_hz: float,
              y_anchor_log10: float, y_anchor_row_hint: int,
              background=(240, 240, 240), edge_margin: int = 3) -> Calibration:
    """Calibrate both axes from the gridlines.

    x_anchor_hz        axis value of the FIRST (left-most) interior vertical gridline
    y_anchor_log10     log10 of the magnitude at the horizontal gridline nearest to
                       pixel row y_anchor_row_hint (read once from the tick labels)
    """
    r0, r1, c0, c1 = find_panel(im, background)
    sub = im[r0:r1 + 1, c0:c1 + 1]
    v = [c + c0 for c in _grid_lines(sub, axis=1) if edge_margin < c < (c1 - c0) - edge_margin]
    h = [r + r0 for r in _grid_lines(sub, axis=0) if edge_margin < r < (r1 - r0) - edge_margin]
    if len(v) < 3 or len(h) < 3:
        raise ValueError(f"too few gridlines found (vertical {len(v)}, horizontal {len(h)})")
    step_x = float(np.min(np.diff(v)))
    a, b, rx = _fit_comb(v, step_x, v[0], x_anchor_hz, x_grid_step_hz)
    step_y = float(np.min(np.diff(h)))
    anchor = min(h, key=lambda r: abs(r - y_anchor_row_hint))
    if abs(anchor - y_anchor_row_hint) > 3:
        raise ValueError(f"no horizontal gridline within 3 px of the anchor row {y_anchor_row_hint}; "
                         f"detected rows {h}. Name a detected gridline as the anchor.")
    ay, by, ry = _fit_comb(h, step_y, anchor, y_anchor_log10, -1.0)   # rows grow downward
    return Calibration(r0, r1, c0, c1, px_per_hz=b, col_at_0hz=a, px_per_decade=-by, row_at_1=ay,
                       v_grid_cols=v, h_grid_rows=h, x_fit_resid_px=rx, y_fit_resid_px=ry)


def colour_weights(im: np.ndarray, spec: Dict[str, str]) -> Dict[str, np.ndarray]:
    """Per-pixel coverage weight in [0, 1] for each named curve (0 = not this curve).
    Anti-aliased edge pixels are blends of the curve colour with white, so the weight
    is how far the pixel has moved from white toward the curve colour. Supported kinds:
       'black'  dark neutral pixels
       'red'    red clearly above green and blue
       'mblue', 'morange', 'myellow'  the first three MATLAB default line colours"""
    r, g, b = im[:, :, 0].astype(float), im[:, :, 1].astype(float), im[:, :, 2].astype(float)
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    out = {}
    for name, kind in spec.items():
        if kind == "black":
            sel = (mx <= 150) & (mx - mn <= 40)
            w = (255.0 - (r + g + b) / 3.0) / 255.0
        elif kind == "red":
            sel = (r >= 150) & (r - np.maximum(g, b) >= 60)
            w = (255.0 - (g + b) / 2.0) / 255.0
        elif kind == "mblue":       # MATLAB default blue (0, 114, 189) and its blends with white
            sel = (b - r >= 50) & (b >= g)
            w = (255.0 - r) / 255.0
        elif kind == "morange":     # MATLAB default orange (217, 83, 25)
            sel = (r - b >= 60) & (r - g >= 45) & (g - b >= 10)
            w = (255.0 - b) / 255.0
        elif kind == "myellow":     # MATLAB default yellow (237, 177, 32)
            sel = (r - b >= 60) & (r - g < 45) & (g - b >= 40)
            w = (255.0 - b) / 255.0
        else:
            raise ValueError(kind)
        out[name] = np.where(sel, w, 0.0)
    return out


def extract(im: np.ndarray, cal: Calibration, spec: Dict[str, str],
            exclude_boxes: Sequence[Tuple[int, int, int, int]] = (), inset: int = 2) -> Dict[str, dict]:
    """Per pixel column inside the panel: coverage-weighted centre, top and bottom
    (log10 magnitude) of each curve's pixels. exclude_boxes are (row0, row1, col0,
    col1) regions to ignore (legends). Grey gridline pixels never match a curve
    colour. 'at_top' / 'at_bottom' mark columns whose stroke touches the panel edge,
    where the curve is leaving the plotted range."""
    weights = colour_weights(im, spec)
    cols = np.arange(cal.c0 + inset, cal.c1 - inset + 1)
    rows = np.arange(cal.r0 + inset, cal.r1 - inset + 1)
    valid = np.ones((len(rows), len(cols)), bool)
    for (a0, a1, b0, b1) in exclude_boxes:
        ra = (rows >= a0) & (rows <= a1)
        cb = (cols >= b0) & (cols <= b1)
        valid[np.ix_(ra, cb)] = False
    out = {}
    rr = rows[:, None] * np.ones((1, len(cols)))
    for name, w in weights.items():
        sub = w[np.ix_(rows, cols)] * valid
        on = sub > 0
        cnt = on.sum(0)
        tot = sub.sum(0)
        with np.errstate(invalid="ignore", divide="ignore"):
            centre = np.where(cnt > 0, (rr * sub).sum(0) / np.where(tot > 0, tot, 1.0), np.nan)
        top = np.where(cnt > 0, np.where(on, rr, np.inf).min(0), np.nan)     # smallest row = largest value
        bot = np.where(cnt > 0, np.where(on, rr, -np.inf).max(0), np.nan)
        out[name] = {"cols": cols, "f_hz": cal.col_to_hz(cols), "n_px": cnt,
                     "row_top": top, "row_bottom": bot,
                     "at_top": (cnt > 0) & (top <= rows[0] + 1), "at_bottom": (cnt > 0) & (bot >= rows[-1] - 1),
                     "log10_centre": cal.row_to_log10(centre),
                     "log10_top": cal.row_to_log10(top), "log10_bottom": cal.row_to_log10(bot)}
    return out


def classify_gaps(curves: Dict[str, dict], name: str, other: str, reach: int = 15,
                  overlap_px: float = 3.0, max_interp_cols: int = 3) -> Dict[str, np.ndarray]:
    """Decide what happened in every column where curve `name` has no usable value.

    clipped   the curve has left the plotted range: its nearest drawn neighbours touch
              the top or bottom edge of the panel. The value is unknown, so the column
              is set to NaN and drops out of every comparison.
    hidden    the curve is drawn underneath `other`: its nearest drawn neighbours sit
              within overlap_px of the other curve's stroke. It is assigned the other
              curve's centre (true to within the stroke width).
    gap       neither: short gaps are linearly interpolated, long ones stay NaN.

    Columns where the stroke touches the panel edge are also set to NaN, because part
    of the stroke is cut off and its centre is biased."""
    c, o = curves[name], curves[other]
    n = len(c["cols"])
    missing = c["n_px"] == 0
    edge = c["at_top"] | c["at_bottom"]
    clipped = np.zeros(n, bool)
    hidden = np.zeros(n, bool)
    gap = np.zeros(n, bool)
    drawn = np.where(~missing)[0]
    for a, b in _runs(np.where(missing)[0]):
        left = drawn[drawn < a][-1] if (drawn < a).any() else None
        right = drawn[drawn > b][0] if (drawn > b).any() else None
        near = [k for k in (left, right) if k is not None and min(abs(k - a), abs(k - b)) <= reach]
        if any(edge[k] for k in near):
            clipped[a:b + 1] = True
            continue
        cover = o["n_px"][a:b + 1] > 0
        ok = False
        if cover.all() and near:
            ok = True
            for k in near:
                j = a if k < a else b                      # column of the gap adjacent to neighbour k
                lo, hi = o["row_top"][j] - overlap_px, o["row_bottom"][j] + overlap_px
                if not (c["row_bottom"][k] >= lo and c["row_top"][k] <= hi):
                    ok = False
        if ok:
            hidden[a:b + 1] = True
        else:
            gap[a:b + 1] = True
    for k in ("log10_centre", "log10_top", "log10_bottom"):
        v = c[k].copy()
        v[hidden] = o[k][hidden]
        v[clipped | edge] = np.nan
        c[k] = v
    y = c["log10_centre"]
    idx = np.arange(n)
    for a, b in _runs(idx[gap]):
        if b - a + 1 <= max_interp_cols and a > 0 and b < n - 1 and not np.isnan(y[a - 1]) and not np.isnan(y[b + 1]):
            for k in ("log10_centre", "log10_top", "log10_bottom"):
                v = c[k]
                v[a:b + 1] = np.interp(idx[a:b + 1], [a - 1, b + 1], [v[a - 1], v[b + 1]])
    return {"clipped": clipped | edge, "hidden": hidden, "gap": gap & np.isnan(c["log10_centre"])}


def load_rgb(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGB")).astype(int)


def band_smooth_power(f_hz: np.ndarray, log10_mag: np.ndarray, width_hz: float) -> np.ndarray:
    """Running mean of |H|^2 over a frequency window, returned as log10|H|. Mimics the
    resolution of a short-record spectrum whose line spacing equals width_hz."""
    p = 10.0 ** (2.0 * log10_mag)
    out = np.full_like(p, np.nan)
    half = width_hz / 2.0
    for i, f in enumerate(f_hz):
        m = (f_hz >= f - half) & (f_hz <= f + half) & ~np.isnan(p)
        if m.any():
            out[i] = p[m].mean()
    return 0.5 * np.log10(out)


def compare(f_hz, log10_a, log10_b, lo_hz, hi_hz) -> dict:
    """Agreement of two magnitude curves over [lo_hz, hi_hz].
       median_abs_db   median over frequency of |20 log10(a/b)| in decibels (dB); 6 dB is a factor of 2
       corr_log        Pearson correlation of the two log-magnitude curves (1 = same shape)"""
    m = (f_hz >= lo_hz) & (f_hz <= hi_hz) & ~np.isnan(log10_a) & ~np.isnan(log10_b)
    d = 20.0 * (log10_a[m] - log10_b[m])
    return {"band_hz": [lo_hz, hi_hz], "n_points": int(m.sum()),
            "median_abs_db": float(np.median(np.abs(d))), "mean_signed_db": float(np.mean(d)),
            "p90_abs_db": float(np.percentile(np.abs(d), 90)),
            "corr_log": float(np.corrcoef(log10_a[m], log10_b[m])[0, 1])}
