#!/usr/bin/env python3
"""Empirical frequency noise floor from replicate modal tests.

Reads 'ShkSat Free Free Mode Shapes Summary VJS.xlsx':
  Sheet1 = three impact-hammer runs (09/10/11), Burst = burst-random runs.
Matches every run's modes to the final .ash frequencies (within 2.5%) and
reports per-mode relative scatter. This is the test-to-test repeatability
evidence behind the frequency-noise prior in the likelihood.
"""
import json
import numpy as np
import openpyxl

XLSX = ("../shocksat_statfem_runner_20260609/extracted/FEM/Correlation/"
        "Modal_Test_Data_Use_in_Correlation2021/FINAL_FF/FF_Final_Data/"
        "ShkSat Free Free Mode Shapes Summary VJS.xlsx")

ash = np.load("measured_modes.npz")["freqs"]          # final 33 modes

def read_runs(ws):
    """Columns appear in blocks of 5 (Mode,Freq,Damp,Desc,blank) starting
    at col B, G, L, ... Return list of freq arrays."""
    rows = list(ws.iter_rows(values_only=True))
    runs = []
    for c0 in range(1, len(rows[2] or []), 5):
        freqs = []
        for r in rows[3:]:
            if r is None or c0 + 1 >= len(r):
                continue
            v = r[c0 + 1]
            try:
                freqs.append(float(v))
            except (TypeError, ValueError):
                continue
        if freqs:
            runs.append(np.array(freqs))
    return runs

wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
impact = read_runs(wb["Sheet1"])
burst = read_runs(wb["Burst"])
print(f"impact runs: {[len(r) for r in impact]}, "
      f"burst runs: {[len(r) for r in burst]}")

def match(runs):
    """per .ash mode: list of matched run freqs (nearest within 2.5%)."""
    out = {}
    for i, f0 in enumerate(ash):
        vals = []
        for r in runs:
            j = int(np.argmin(np.abs(r - f0)))
            if abs(r[j] / f0 - 1) < 0.025:
                vals.append(float(r[j]))
        if len(vals) >= 2:
            out[i] = vals
    return out

rep = {"ash_freqs": [round(float(f), 3) for f in ash]}
for name, runs in (("impact", impact), ("burst", burst),
                   ("all", impact + burst)):
    m = match(runs)
    scat = {i: float(np.std(v, ddof=1) / np.mean(v)) for i, v in m.items()}
    rep[name] = dict(
        n_runs=len(runs),
        per_mode_rel_std={str(k + 1): round(v, 6) for k, v in scat.items()},
        median_rel_std=float(np.median(list(scat.values()))) if scat else None,
        p90_rel_std=float(np.percentile(list(scat.values()), 90))
        if scat else None,
        max_rel_std=float(max(scat.values())) if scat else None)
    print(name, {k: round(rep[name][k], 5) if isinstance(rep[name][k], float)
                 else rep[name][k]
                 for k in ("n_runs", "median_rel_std", "p90_rel_std",
                           "max_rel_std")})
json.dump(rep, open("noise_floor.json", "w"), indent=1)
