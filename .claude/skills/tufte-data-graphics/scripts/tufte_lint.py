#!/usr/bin/env python3
"""tufte_lint.py — heuristic chartjunk linter for plotting scripts.

Scans a Python plotting script (matplotlib/plotly/seaborn) for common Tufte
violations and prints WARN/INFO notes. This is a HEURISTIC AID, not a proof of
quality: a clean lint does NOT mean a figure is good, and a warning may be a
justified choice. It only reads source text; it does not render figures.

Usage:
    python tufte_lint.py path/to/plot_script.py [more.py ...]

Exit code: 0 always (advisory tool; do not gate CI on it without review).
"""
from __future__ import annotations
import re
import sys
from pathlib import Path

# (regex, level, message). Levels: WARN (likely chartjunk), INFO (check intent).
CHECKS = [
    (r"projection\s*=\s*['\"]3d['\"]|Axes3D|mplot3d", "WARN",
     "3-D axes for what is usually 1-D/2-D data → inflated Lie Factor (VDQI). Use small multiples/2-D."),
    (r"\.pie\s*\(|px\.pie|go\.Pie", "WARN",
     "Pie chart: low data density, hard angle comparison. Prefer a sorted bar chart or table (Tufte)."),
    (r"cmap\s*=\s*['\"](jet|rainbow|hsv|gist_rainbow|nipy_spectral)['\"]", "WARN",
     "Rainbow/jet colormap is not perceptually uniform. Use viridis/magma/cividis for sequential data."),
    (r"\.twinx\s*\(|\.twiny\s*\(", "INFO",
     "Dual axis: only if both scales are independently meaningful + labeled; never to imply a correlation."),
    (r"plt\.legend|ax\.legend|legend\s*=\s*True", "INFO",
     "Legend present: prefer direct end-of-line labels to avoid eye ping-pong (Beautiful Evidence)."),
    (r"shadow\s*=\s*True", "WARN",
     "Legend/element shadow = non-data ink (chartjunk). Remove."),
    (r"set_facecolor\(|facecolor\s*=\s*['\"](?!none|white|#fff)", "INFO",
     "Background fill: ensure it carries information; otherwise it is non-data ink."),
    (r"hatch\s*=", "INFO",
     "Hatch fill can cause moiré vibration (chartjunk). Use a solid muted fill or none."),
    (r"\bbar\w*\(", "INFO",
     "Bar chart: ensure baseline starts at zero (set_ylim(bottom=0)) — no truncated baselines."),
    (r"\b(dB|decibel|20\s*\*\s*np\.log10|10\s*\*\s*np\.log10)\b", "INFO",
     "dB detected: state linear/dB explicitly and justify dB (project rule: avoid dB unless standard)."),
]

FREQ_HINT = re.compile(r"freq|frf|psd|hz|spectra|spectrum|apparent_mass|accel", re.I)
LOGX = re.compile(r"set_xscale\(\s*['\"]log['\"]|xscale\s*=\s*['\"]log['\"]|loglog\(|semilogx\(")


def lint_text(text: str) -> list[tuple[str, str]]:
    findings: list[tuple[str, str]] = []
    for pat, level, msg in CHECKS:
        if re.search(pat, text):
            findings.append((level, msg))
    # frequency-domain plots should use a log x-axis unless justified
    if FREQ_HINT.search(text) and "plot" in text.lower() and not LOGX.search(text):
        findings.append((
            "INFO",
            "Looks like a frequency-domain plot but no log x-axis found. "
            "Project rule: log frequency axis unless justified.",
        ))
    # de-duplicate, preserve order
    seen, out = set(), []
    for f in findings:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def main(argv: list[str]) -> int:
    paths = argv[1:]
    if not paths:
        print(__doc__)
        return 0
    total = 0
    for p in paths:
        fp = Path(p)
        if not fp.exists():
            print(f"[skip] {p}: not found")
            continue
        findings = lint_text(fp.read_text(encoding="utf-8", errors="ignore"))
        print(f"\n=== {p} ===")
        if not findings:
            print("  no heuristic flags (NOT a guarantee of quality — apply the SKILL.md checklist).")
        for level, msg in findings:
            print(f"  [{level}] {msg}")
            total += 1
    print(f"\n{total} heuristic flag(s). Advisory only — review each against intent and the Tufte checklist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
