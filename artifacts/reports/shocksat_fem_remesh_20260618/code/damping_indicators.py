#!/usr/bin/env python3
"""Card D follow-up — indicators of complex/non-proportional damping at the hard
locations, from the AUTHORITATIVE NASA free-free modal-test summary spreadsheet
(`ShkSat Free Free Mode Shapes Summary VJS.xlsx`).

Non-proportional ("complex") damping signature = modal damping that depends on
WHICH substructure flexes (mode shape), not just frequency, and that concentrates
at dissipative interfaces (bolted joints, bulkheads, contact). Output: the per-mode
zeta table tagged by description, the damping spread, and the joint/bulkhead-vs-
panel contrast.
"""
import json, os
import numpy as np
import openpyxl

XLSX = ("../shocksat_statfem_runner_20260609/extracted/FEM/Correlation/"
        "Modal_Test_Data_Use_in_Correlation2021/FINAL_FF/FF_Final_Data/"
        "ShkSat Free Free Mode Shapes Summary VJS.xlsx")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ws = openpyxl.load_workbook(os.path.join(HERE, XLSX), data_only=True)["Sheet1"]

JOINT_KW = ["bulkhead", "cross", "joint", "drum", "contact"]
modes = []
for rr in range(4, ws.max_row + 1):
    f = ws.cell(row=rr, column=3).value
    z = ws.cell(row=rr, column=4).value
    d = ws.cell(row=rr, column=5).value
    if isinstance(f, (int, float)) and isinstance(z, (int, float)) and 0 < z < 0.5:
        desc = str(d) if d else ""
        is_joint = any(k in desc.lower() for k in JOINT_KW)
        modes.append(dict(freq_hz=round(f, 2), zeta_pct=round(z*100, 3),
                          joint_bulkhead=is_joint, desc=desc.replace("\n", " / ")))

zs = np.array([m["zeta_pct"] for m in modes])
zj = np.array([m["zeta_pct"] for m in modes if m["joint_bulkhead"]])
zp = np.array([m["zeta_pct"] for m in modes if not m["joint_bulkhead"]])
out = dict(
    source=XLSX, n_modes=len(modes),
    zeta_min_pct=float(zs.min()), zeta_median_pct=float(np.median(zs)),
    zeta_max_pct=float(zs.max()), zeta_spread_x=float(zs.max()/zs.min()),
    joint_bulkhead_mean_zeta_pct=float(zj.mean()) if len(zj) else None,
    panel_other_mean_zeta_pct=float(zp.mean()) if len(zp) else None,
    contrast_x=float(zj.mean()/zp.mean()) if len(zj) and len(zp) else None,
    top_damped=sorted(modes, key=lambda m: -m["zeta_pct"])[:6],
    note=("Measured mode SHAPES were curve-fit as REAL normal modes (.ash stores real "
          "float32 shapes) -> the survey assumed proportional damping; complex (phase) "
          "content was not retained. These zeta are real measured per-mode damping; the "
          "interface-localization is the indirect complex-damping indicator. The modal-twin "
          "parsed .ash 'damp' array (0.25-1.05) is mislabeled vs this authoritative column "
          "(~65x) -> data-hygiene flag; Card A used uniform zeta=1% (over-damps panels, "
          "under-damps bulkhead modes)."))
os.makedirs(f"{HERE}/out", exist_ok=True)
json.dump(out, open(f"{HERE}/out/damping_indicators.json", "w"), indent=1)

print(f"n_modes={out['n_modes']}  zeta {out['zeta_min_pct']:.3f}-{out['zeta_max_pct']:.3f}% "
      f"({out['zeta_spread_x']:.1f}x spread)")
print(f"joint/bulkhead modes mean zeta {out['joint_bulkhead_mean_zeta_pct']:.3f}% vs "
      f"panel/other {out['panel_other_mean_zeta_pct']:.3f}% -> {out['contrast_x']:.1f}x more damped")
print("top-damped modes:")
for m in out["top_damped"]:
    print(f"  {m['freq_hz']:7.1f} Hz  {m['zeta_pct']:.3f}%  "
          f"{'[JOINT/BULKHEAD]' if m['joint_bulkhead'] else '             '} {m['desc'][:60]}")
