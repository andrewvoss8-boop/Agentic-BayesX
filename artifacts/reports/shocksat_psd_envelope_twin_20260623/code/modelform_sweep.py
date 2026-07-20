#!/usr/bin/env python3
"""MODEL-FORM sweep (Andrew "sweep all possibilities", informed by the CAD/photo): the structure is a heavy STEEL
bottom (bottom_box, MAT1002 rho 7.4e-4) + light ALUMINUM top (top_box, MAT1001) + thick aluminum DISH plates
(501/601/701) on top. The diagnosed problem is a mass/stiffness DISTRIBUTION error (right fundamental freq, wrong
shape) — never tested because we only varied stiffness MAGNITUDES, never DENSITY/MASS distribution. Sweep the
steel<->aluminum E AND rho balance + the dish mass. Score FRF corr + global MAC + FUNDAMENTAL-mode MAC (currently
0.12 — the key: does redistributing fix the 54 Hz shape?). Usage: python3 modelform_sweep.py
"""
from __future__ import annotations
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import correlate_all as CA
import remodel as RM

WS = Path(__file__).resolve().parent.parent
ST = [101, 102, 103]; AL = [201, 202, 203]; DISH = [501, 601, 701]
def Esc(pids, f): return {"scale": {f"shell_{p}": f for p in pids}}
def merge(*ds):
    out = {"scale": {}, "mass_scale": {}}
    for d in ds:
        out["scale"].update(d.get("scale", {})); out["mass_scale"].update(d.get("mass_scale", {}))
    return {k: v for k, v in out.items() if v}

SWEEP = {
    # density / mass distribution (NEW lever)
    "steel_rho_lo": {"mass_scale": {"steel": 0.7}}, "steel_rho_hi": {"mass_scale": {"steel": 1.3}},
    "al_rho_lo": {"mass_scale": {"aluminum": 0.8}}, "al_rho_hi": {"mass_scale": {"aluminum": 1.25}},
    "dish_mass_lo": {"mass_scale": {"dish": 0.6}}, "dish_mass_hi": {"mass_scale": {"dish": 1.5}},
    "steelLight_alHeavy": {"mass_scale": {"steel": 0.7, "aluminum": 1.3}},
    "steelHeavy_alLight": {"mass_scale": {"steel": 1.3, "aluminum": 0.7}},
    # combined E + rho (true material change)
    "steel_soft_light": merge(Esc(ST, 0.8), {"mass_scale": {"steel": 0.8}}),
    "steel_stiff_heavy": merge(Esc(ST, 1.2), {"mass_scale": {"steel": 1.2}}),
    "al_stiff": Esc(AL, 1.25), "al_soft": Esc(AL, 0.8),
    # best-guess distribution shift: soften+lighten steel, stiffen aluminum, lighten dish
    "combo_shift": merge(Esc(ST, 0.8), Esc(AL, 1.15), {"mass_scale": {"steel": 0.8, "dish": 0.7}}),
}

if __name__ == "__main__":
    rows = []
    for eid, e in SWEEP.items():
        try:
            r = CA.score(eid, e); rows.append(r)
            print(f"{eid:22s} FRFcorr {r['FRF_logmag_corr_median']:.3f} | MAC {r['global_MAC']:.3f} | "
                  f"FUND-MAC {r['fundamental_MAC']:.2f} (was 0.12) | low3 {r['low3_MAC']}", flush=True)
        except Exception as ex:
            print(f"{eid}: FAILED {ex}", flush=True)
    (WS / "out" / "modelform_sweep.json").write_text(json.dumps(rows, indent=2))
    best = max(rows, key=lambda r: r["FRF_logmag_corr_median"]) if rows else None
    bestf = max(rows, key=lambda r: r["fundamental_MAC"]) if rows else None
    print(f"\nBEST FRFcorr: {best['edit_id']} {best['FRF_logmag_corr_median']:.3f} (baseline 0.296, prior-best 0.359)")
    print(f"BEST FUND-MAC: {bestf['edit_id']} {bestf['fundamental_MAC']:.2f} (baseline 0.12 — >0.5 would be a real shape fix)")
