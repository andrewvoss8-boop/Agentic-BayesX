#!/usr/bin/env python3
"""Sensitivity of the arm-B local FIM to step, gain projection, and covariance."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.linalg import cho_factor, cho_solve


REVIEW = Path(__file__).resolve().parent
ROOT = REVIEW.parents[2]
STUDY = ROOT / "artifacts/reports/shocksat_full_spectrum_frf_20260714"
CODE = STUDY / "code"
sys.path.insert(0, str(CODE))

import wide_forward as WFW  # noqa: E402
import wide_package as WP  # noqa: E402
import wscore_wide as SW  # noqa: E402


STEPS = (0.005, 0.01, 0.02, 0.04)
F_LIK = (45.0, 400.0)
PRIOR_PRECISION = 16.0


def posterior_scales():
    vals = {"sigma_e": [], "sigma_n": [], "ell": []}
    for fold in SW.DEV_KEYS:
        z = np.load(STUDY / "out/armB" / f"with_error_term_{fold}.npz")
        for key in vals:
            vals[key].append(float(np.mean(z[key])))
    return {key: float(np.median(value)) for key, value in vals.items()}


def raw_predictions(pkg, caches, theta):
    blocks = []
    for drive in SW.DEV_KEYS:
        cache = caches[drive]
        mask = cache["band"] & (cache["freqs"] >= F_LIK[0]) & (cache["freqs"] <= F_LIK[1])
        rows, _ = SW._usable(pkg, cache, mask)
        freqs = cache["freqs"][mask]
        pred = np.log10(
            np.abs(WFW.predict_H(pkg, theta, drive, freqs, windowed=True))[rows] + 1e-300
        )
        blocks.append({"drive": drive, "freqs": freqs, "pred": pred})
    return blocks


def jacobian_blocks(pkg, caches, theta0, step):
    base = raw_predictions(pkg, caches, theta0)
    jac = [
        np.zeros((block["pred"].shape[0], block["pred"].shape[1], len(theta0)))
        for block in base
    ]
    for group in range(len(theta0)):
        plus = theta0.copy()
        minus = theta0.copy()
        plus[group] *= np.exp(step)
        minus[group] *= np.exp(-step)
        yp = raw_predictions(pkg, caches, plus)
        ym = raw_predictions(pkg, caches, minus)
        for index in range(len(base)):
            jac[index][:, :, group] = (yp[index]["pred"] - ym[index]["pred"]) / (2 * step)
    return base, jac


def eig_summary(matrix):
    eig = np.linalg.eigvalsh(matrix)[::-1]
    return {
        "eigenvalues_desc": eig.tolist(),
        "min": float(eig[-1]),
        "max": float(eig[0]),
        "n_clearing_prior_16": int((eig >= PRIOR_PRECISION).sum()),
    }


def matrices(base, jac, scales):
    diag_per_channel = np.zeros((9, 9))
    diag_global_gain = np.zeros((9, 9))
    correlated_global_gain = np.zeros((9, 9))
    variance = scales["sigma_e"] ** 2
    for block, derivative in zip(base, jac):
        per_channel = derivative - derivative.mean(axis=1, keepdims=True)
        flat_pc = per_channel.reshape(-1, 9)
        diag_per_channel += flat_pc.T @ flat_pc / variance

        global_gain = derivative - derivative.mean(axis=(0, 1), keepdims=True)
        flat_global = global_gain.reshape(-1, 9)
        diag_global_gain += flat_global.T @ flat_global / variance

        logf = np.log10(block["freqs"])
        delta = logf[:, None] - logf[None, :]
        covariance = (
            scales["sigma_e"] ** 2
            * np.exp(-0.5 * (delta / scales["ell"]) ** 2)
            + (scales["sigma_n"] ** 2 + 1e-8) * np.eye(logf.size)
        )
        factor = cho_factor(covariance, lower=True, check_finite=False)
        for channel in range(global_gain.shape[0]):
            dch = global_gain[channel]
            correlated_global_gain += dch.T @ cho_solve(
                factor, dch, check_finite=False
            )
    return {
        "study_diagonal_sigmae_per_channel_gain_removed": eig_summary(diag_per_channel),
        "diagonal_sigmae_global_drive_gain_removed": eig_summary(diag_global_gain),
        "likelihood_covariance_global_drive_gain_removed": eig_summary(
            correlated_global_gain
        ),
    }


def main():
    pkg = WP.load("A0_wide")
    caches = SW.load_caches()
    theta0 = np.asarray(
        json.loads((STUDY / "out/theta_map_wide.json").read_text())["theta_map_vec"]
    )
    scales = posterior_scales()
    output = {
        "posterior_scale_medians": scales,
        "prior_precision": PRIOR_PRECISION,
        "note": (
            "The study FIM uses sigma_e^2 I and removes a separate mean from every channel. "
            "The likelihood uses one gain per drive and a frequency-correlated covariance."
        ),
        "steps": {},
    }
    for step in STEPS:
        base, jac = jacobian_blocks(pkg, caches, theta0, step)
        output["steps"][str(step)] = matrices(base, jac, scales)
    path = REVIEW / "out/fim_step_sensitivity.json"
    path.write_text(json.dumps(output, indent=2))
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
