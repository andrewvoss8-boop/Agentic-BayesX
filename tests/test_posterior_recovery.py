#!/usr/bin/env python3
"""Posterior recovery smoke test for 2DOF synthetic data."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.inference.mcmc import InferenceConfig, run_mcmc
from src.twodof.synthetic_data import NoiseConfig, generate_dataset, save_dataset


def _rel_err(x: float, y: float) -> float:
    return abs(x - y) / max(abs(y), 1e-12)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    freqs = np.linspace(10.0, 180.0, 80)
    data = generate_dataset(
        freqs_hz=freqs,
        noise=NoiseConfig(seed=11, sigma_re=0.01, sigma_im=0.01, discrepancy_scale=0.015),
    )
    save_dataset(root / "artifacts" / "synthetic" / "twodof_dataset.json", data)

    post = run_mcmc(
        data,
        config=InferenceConfig(
            n_steps=1500,
            burn_in=400,
            thin=4,
            proposal_scale=0.02,
            seed=2,
        ),
    )

    truth = post["truth"]
    mean = post["posterior_mean"]
    checks = {
        "k1": _rel_err(mean["k1"], truth["params"]["k1"]),
        "k2": _rel_err(mean["k2"], truth["params"]["k2"]),
        "k12": _rel_err(mean["k12"], truth["params"]["k12"]),
        "force_amp": _rel_err(mean["force_amp"], truth["force_amp"]),
        "force_fc": _rel_err(mean["force_fc"], truth["force_fc"]),
        "qoi_peak_tray_accel": _rel_err(mean["qoi_peak_tray_accel"], truth["qoi_peak_tray_accel"]),
    }

    report = {
        "acceptance_rate": post["acceptance_rate"],
        "relative_errors": checks,
        "pass": all(v < 0.35 for v in checks.values()) and (0.01 < post["acceptance_rate"] < 0.85),
    }

    out = root / "artifacts" / "tests" / "posterior_recovery_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))

    if not report["pass"]:
        print(json.dumps(report, indent=2))
        return 2

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
