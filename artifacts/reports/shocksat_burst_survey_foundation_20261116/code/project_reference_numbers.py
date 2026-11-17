#!/usr/bin/env python3
"""Copy a few summary statistics of the project's 2026-07-23 Card H study into this
workspace, so the pilot can compare against them without the private record.

Card H ("Beck all-training FRF capacity") scored the project's FEM against the
shock-test hammer FRFs: 84 response channels x 5 hammer drive conditions = 420
curves, 105 frequency lines from 46.79 to 258.38 Hz (2.03 Hz spacing). Its
per-curve number is the median over those lines of |20 log10(measured / model)| in
dB. "N0" is the nominal FEM, "B1" the Bayesian-updated FEM. That workspace was never
pushed to the public repository; its text record is on branch
claude/ecstatic-carson-c3e4f9 of the private repository
andrewvoss8-boop/bayesx-disk-backup-2026-10-02 under recovered_text_extract/.

Usage: project_reference_numbers.py --card-h DIR   (DIR = the recovered Card H workspace)
Writes data/project_reference_numbers.json. Without --card-h it only verifies that
the committed JSON is present.
"""
import argparse
import csv
import hashlib
import json
import os
import sys

import numpy as np

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(WS, "data", "project_reference_numbers.json")
REL = "artifacts/reports/shocksat_beck_all_training_frf_capacity_20260723"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--card-h")
    a = ap.parse_args()
    if not a.card_h:
        d = json.load(open(DEST))
        print("committed reference numbers present:", d["card_h"]["n_curves"], "curves")
        return 0
    pc = os.path.join(a.card_h, "out", "per_curve_metrics.csv")
    cm = os.path.join(a.card_h, "out", "capacity_metrics.json")
    ck = os.path.join(a.card_h, "out", "checker_report.json")
    rows = list(csv.DictReader(open(pc)))
    meta = json.load(open(cm))["data_counts"]["cache_metadata"]
    n0 = np.array([float(r["n0_median_abs_residual_db"]) for r in rows])
    b1 = np.array([float(r["b1_median_abs_residual_db"]) for r in rows])
    dist, same = [], []
    for r in rows:
        d = meta[r["drive"]]
        s = np.array([float(r["x_in"]), float(r["y_in"]), float(r["z_in"])])
        dist.append(float(np.linalg.norm(s - np.array(d["drive_xyz_in"]))))
        same.append(d["drive_axis"] == r["response_axis"] or (d["drive_axis"] == "XY" and r["response_axis"] in "XY"))
    dist, same = np.array(dist), np.array(same)

    def q(v):
        return {"n": int(len(v)), "min": float(v.min()), "p05": float(np.percentile(v, 5)), "q25": float(np.percentile(v, 25)),
                "median": float(np.median(v)), "q75": float(np.percentile(v, 75)), "max": float(v.max())}

    def rank(v):
        o = np.argsort(v); r = np.empty(len(v)); r[o] = np.arange(len(v)); return r

    chk = json.load(open(ck))
    out = {
        "source": {"private_repo": "andrewvoss8-boop/bayesx-disk-backup-2026-10-02", "branch": "claude/ecstatic-carson-c3e4f9",
                   "path": "recovered_text_extract/bayesX/Agentic BayesX/" + REL,
                   "per_curve_metrics_sha256": sha(pc), "capacity_metrics_sha256": sha(cm),
                   "checker_overall": chk.get("overall"), "checker_summary": chk.get("summary")},
        "card_h": {
            "definition": "per-curve median over 105 frequency lines (46.79-258.38 Hz, 2.03 Hz spacing) of |20 log10(measured/model)| dB; "
                          "model has one fitted scalar gain per drive and zeta = 0.01; in-sample (resubstitution)",
            "n_curves": len(rows), "n_response_channels": 84, "n_drive_conditions": 5,
            "band_hz": [46.79, 258.38], "line_spacing_hz": 2.0345,
            "n0_nominal_fem_db": q(n0), "b1_updated_fem_db": q(b1),
            "drives": {k: {"drive_xyz_in": v["drive_xyz_in"], "drive_axis": v["drive_axis"], "n_hits_used": v["n_hits_used"]} for k, v in meta.items()},
            "near_drive": {
                "sensor_to_drive_distance_in": q(dist),
                "spearman_distance_vs_n0_error": float(np.corrcoef(rank(dist), rank(n0))[0, 1]),
                "n0_db_by_distance_in": {f"{lo}-{hi}": q(n0[(dist >= lo) & (dist < hi)]) for lo, hi in [(0, 4), (4, 10), (10, 20), (20, 40), (40, 80)]},
                "n0_db_same_axis_as_drive": q(n0[same]), "n0_db_other_axes": q(n0[~same]),
                "closest_sensor": {"distance_in": float(dist.min()), "n0_db_same_axis": float(n0[(dist == dist.min()) & same].min()) if ((dist == dist.min()) & same).any() else None},
            },
        },
    }
    json.dump(out, open(DEST, "w"), indent=1)
    print(json.dumps(out["card_h"]["n0_nominal_fem_db"]), out["source"]["checker_overall"], out["source"]["checker_summary"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
