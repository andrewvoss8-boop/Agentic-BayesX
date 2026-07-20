#!/usr/bin/env python3
"""mc_noise — how big is a MEANINGFUL width difference? (AGENTS Sensitivity Gate)

The S3/S4 numbers are ratios of Monte-Carlo band percentiles. The netcg machinery uses a FIXED seed (0), so
every comparison in this card is paired and deterministic — but that does NOT make a 1% width difference
real. This script re-runs the DELIVERED band over many seeds to measure the MC dispersion of the width-ratio
statistic itself, giving a noise floor against which the finalist effects must be read.

Nothing here is tuned or selected on; it is a measurement of the estimator's own variability.
Writes out/mc_noise.json.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import numpy as np

WS = Path(__file__).resolve().parent.parent
REPORTS = WS.parent
NETCG = REPORTS / "shocksat_netcg_method_selection_20260701"
for p in (REPORTS / "shocksat_psd_envelope_twin_20260623" / "code", NETCG / "code", WS / "code"):
    sys.path.insert(0, str(p))
import netcg_qoi as NC   # noqa: E402
import netcg_port as P   # noqa: E402

AXES = [(0, "shear_X"), (1, "shear_Y"), (2, "normal_Z")]
N_SEEDS = 24


def main():
    t0 = time.time()
    model = NC.QOIModel()
    z = np.load(NETCG / "out" / "theta_post_L5.npz", allow_pickle=True)
    theta_post = z["theta_post"]
    theta_map = np.median(theta_post, axis=0)

    out = {"design": f"delivered statFEM F(k) band re-scored over {N_SEEDS} independent MC seeds; the "
                     "width-ratio statistic's own dispersion = the noise floor for reading S3/S4 effects.",
           "n_seeds": N_SEEDS, "axes": {}}
    for axis, name in AXES:
        ref = P.fem6_ref_grms(model, theta_map, axis)
        vals = []
        for s in range(N_SEEDS):
            lo, med, hi = NC.Method(model, axis, theta_post, kind="statfem_fk", seed=s).band()
            vals.append(NC.grms(hi - lo) / ref)
        v = np.array(vals)
        out["axes"][name] = {
            "seed0_delivered": round(float(v[0]), 3),
            "mean": round(float(v.mean()), 4), "sd": round(float(v.std(ddof=1)), 4),
            "min": round(float(v.min()), 3), "max": round(float(v.max()), 3),
            "rel_sd_pct": round(100 * float(v.std(ddof=1) / v.mean()), 2),
            "two_sd_band": [round(float(v.mean() - 2 * v.std(ddof=1)), 3),
                            round(float(v.mean() + 2 * v.std(ddof=1)), 3)],
            "meaningful_diff_gt_2sd": round(2 * float(v.std(ddof=1)), 3)}
        print(f"[{name}] delivered {v[0]:.3f} | over {N_SEEDS} seeds: mean {v.mean():.3f} "
              f"sd {v.std(ddof=1):.4f} ({out['axes'][name]['rel_sd_pct']}%) "
              f"-> a width difference must exceed ~{2 * v.std(ddof=1):.3f} to be MC-meaningful")
    out["active_s"] = round(time.time() - t0, 1)
    (WS / "out" / "mc_noise.json").write_text(json.dumps(out, indent=2))
    print("wrote out/mc_noise.json")


if __name__ == "__main__":
    main()
