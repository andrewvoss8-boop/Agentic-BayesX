#!/usr/bin/env python3
"""Combine the model-form sweep WINNERS (lighten aluminum top + lighten dish — the top-mass-too-heavy direction),
which the sweep never combined. Does combining the winning distribution directions push FRF corr past ~0.38?"""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import correlate_all as CA

EDITS = {
    "lighten_top":         {"mass_scale": {"aluminum": 0.8, "dish": 0.6}},
    "lighten_top_strong":  {"mass_scale": {"aluminum": 0.7, "dish": 0.5}},
    "lighten_top_alstiff": {"mass_scale": {"aluminum": 0.8, "dish": 0.6},
                            "scale": {f"shell_{p}": 1.25 for p in (201, 202, 203)}},
}
for eid, e in EDITS.items():
    r = CA.score(eid, e)
    print(f"{eid:22s} FRFcorr {r['FRF_logmag_corr_median']:.3f} (baseline 0.296, sweep-best al_rho_lo 0.379) | "
          f"MAC {r['global_MAC']:.3f} | low3 {r['low3_MAC']}", flush=True)
