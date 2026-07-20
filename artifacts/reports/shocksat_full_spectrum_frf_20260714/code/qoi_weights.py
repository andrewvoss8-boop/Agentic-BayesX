#!/usr/bin/env python3
"""qoi_weights — derive per-SENSOR weights for the QOI-weighted score (Q2; decisions D5).
stage0_qoi_weights.json is per-MODE: each shear QOI lists top modes with weight_pct. Per-sensor weight:
  w(sensor) ∝ Σ_modes (shearX_pct + shearY_pct)(mode) × |φ_mode(sensor)|   at θ_MAP (A0_wide package),
normalized to sum 1 over package sensors. φ from the wide package's frozen pairing: the stage0 mode is
matched to the package mode by frequency (nearest, ≤2% mismatch else skipped+reported).
Writes out/qoi_sensor_weights.json (daq -> weight)."""
import json, os, sys
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402

SRC = os.path.join(ROOT, "artifacts/reports/shocksat_netcg_method_selection_20260701/out/stage0_qoi_weights.json")


def main():
    w = json.load(open(SRC))
    mode_w = {}
    for q in ("tray_shear_X", "tray_shear_Y"):
        for m in w["qoi_participation"][q]["top_modes"]:
            mode_w[round(float(m["hz"]), 1)] = mode_w.get(round(float(m["hz"]), 1), 0.0) + float(m["weight_pct"])
    pkg = WP.load("A0_wide")
    theta, _, _ = pkg.theta_map()
    f, Q = pkg.modes(theta)
    sens = np.asarray(pkg.sens_rows) @ Q        # (n_sens, r) mode shapes at sensors
    wt = np.zeros(len(pkg.sens_daq))
    skipped = []
    for hz, mw in mode_w.items():
        k = int(np.argmin(np.abs(f - hz)))
        if abs(f[k] / hz - 1.0) > 0.02:
            skipped.append({"hz": hz, "nearest_fem": float(f[k])})
            continue
        wt += mw * np.abs(sens[:, k])
    wt = wt / wt.sum()
    out = {"weights": {str(d): float(v) for d, v in zip(pkg.sens_daq, wt)},
           "derivation": "sum over stage0 shear X+Y top modes of weight_pct * |phi_mode(sensor)| at theta_MAP",
           "n_modes_used": len(mode_w) - len(skipped), "skipped_modes": skipped,
           "top10": sorted(zip([int(d) for d in pkg.sens_daq], wt.tolist()),
                           key=lambda x: -x[1])[:10]}
    json.dump(out, open(os.path.join(WS, "out", "qoi_sensor_weights.json"), "w"), indent=1)
    print(json.dumps(out["top10"]))


if __name__ == "__main__":
    main()
