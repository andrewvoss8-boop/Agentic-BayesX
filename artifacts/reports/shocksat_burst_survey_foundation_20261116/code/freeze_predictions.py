#!/usr/bin/env python3
"""Freeze the project FEM's predictions for NASA's 264 test-versus-FEM comparison plots
(FEM/Correlation/FRF_Verification/{11101X,11110Y}_Impact_Comparison/, not yet
downloaded) BEFORE any of them is seen.

Drives: NASA's two SOL 111 load cases, unit force at grid 11101 in +X and at grid 11110
in +Y (decks recorded on 2026-06-09 in shocksat_statfem_runner_20260609/
nasa_correlation_frf_assets.json). Responses: the 132 measured components of the 76
survey nodes. Grid: 10 to 400 Hz in 0.25 Hz steps. Stored: log10|H| (g/lbf) as float16
(0.02 dB resolution) for the primary damping rule, plus input and output hashes in
prereg_frozen_inputs.json.
"""
import hashlib
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import fem_frf  # noqa: E402

DRIVES = {"11101X": (11101, "X"), "11110Y": (11110, "Y")}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    verify = "--verify" in sys.argv
    fem = fem_frf.FEM()
    f = np.arange(10.0, 400.0 + 1e-9, 0.25)
    z = fem.zeta("measured_interp")
    resp = [(n, a) for n in fem.nodes for a in "XYZ" if fem.is_measured(n, a)]
    out, keys = [], []
    for dk, drv in DRIVES.items():
        for (n, a) in resp:
            out.append(np.log10(fem.accelerance(f, (n, a), drv, z)).astype(np.float16))
            keys.append(f"{dk}|{n}{a}")
    arr = np.vstack(out)
    if verify:
        spec = json.load(open(os.path.join(WS, "prereg_frozen_inputs.json")))
        stored = np.load(os.path.join(WS, "out", "frozen_project_fem_predictions.npz"))["log10_g_per_lbf"]
        ok = (hashlib.sha256(arr.tobytes()).hexdigest() == spec["array_sha256"]
              and hashlib.sha256(stored.tobytes()).hexdigest() == spec["array_sha256"]
              and all(sha(p) == spec["inputs_sha256"][k] for k, p in
                      {"obs_V.npy": fem_frf.P_OBS, "eigvals.npy": fem_frf.P_EIG, "measured_modes.npz": fem_frf.P_MM}.items()))
        print("frozen predictions reproduce:", ok)
        sys.exit(0 if ok else 1)
    dest = os.path.join(WS, "out", "frozen_project_fem_predictions.npz")
    np.savez_compressed(dest, f_hz=f.astype(np.float32), log10_g_per_lbf=arr, keys=np.array(keys))
    spec = {
        "frozen_utc": "2026-11-17",
        "purpose": "pre-registered predictions for NASA's 264 FRF verification plots; computed before any plot was seen "
                   "(the two drive-point plots on deck slides 16 and 17 HAD been seen and are excluded from the confirmatory set)",
        "n_curves": len(keys), "n_responses_per_drive": len(resp), "drives": {k: list(v) for k, v in DRIVES.items()},
        "grid_hz": [10.0, 400.0, 0.25], "damping_rule": "measured_interp (see fem_frf.py)",
        "zeta_elastic_range": [float(z[fem.fn > 5].min()), float(z[fem.fn > 5].max())],
        "inputs_sha256": {"obs_V.npy": sha(fem_frf.P_OBS), "eigvals.npy": sha(fem_frf.P_EIG),
                          "measured_modes.npz": sha(fem_frf.P_MM), "fem_frf.py": sha(os.path.join(HERE, "fem_frf.py")),
                          "freeze_predictions.py": sha(os.path.abspath(__file__))},
        "output_sha256": sha(dest),
        "array_sha256": hashlib.sha256(arr.tobytes()).hexdigest(),
    }
    json.dump(spec, open(os.path.join(WS, "prereg_frozen_inputs.json"), "w"), indent=1)
    print(json.dumps({k: spec[k] for k in ("n_curves", "n_responses_per_drive", "zeta_elastic_range", "array_sha256")}))
    print("output bytes", os.path.getsize(dest))


if __name__ == "__main__":
    main()
