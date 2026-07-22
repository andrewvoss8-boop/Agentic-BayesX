#!/usr/bin/env python3
"""Extract audit tables for the ShockSat advisor report from frozen artifacts.

This script performs descriptive calculations only. It does not refit a model,
resample a posterior, or alter any study verdict.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve()
SUMMARY = HERE.parent.parent
REPORTS = SUMMARY.parent
OUT = SUMMARY / "out" / "advisor_audit_metrics.json"

MODAL = REPORTS / "shocksat_fem_modal_twin_20260609"
MODELFORM = REPORTS / "shocksat_modelform_pilot_20260716"
EXACT = REPORTS / "shocksat_fullspec_exact_completion_20260716"
NETCG_PORT = REPORTS / "shocksat_netcg_validated_port_20260716"
IFT = REPORTS / "ift_real_validation_20260619"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def modal_contraction() -> dict:
    path = MODAL / "nuts_full_samples.npz"
    z = np.load(path)
    theta = np.asarray(z["theta"], dtype=float)
    names = [str(value) for value in z["gnames"]]
    prior_log_sd = 0.25
    prior_sd_theta = math.sqrt(
        (math.exp(prior_log_sd**2) - 1.0) * math.exp(prior_log_sd**2)
    )
    corr = np.corrcoef(theta, rowvar=False)
    rows = []
    for index, name in enumerate(names):
        other = max(
            (candidate for candidate in range(len(names)) if candidate != index),
            key=lambda candidate: abs(corr[index, candidate]),
        )
        posterior_sd = float(np.std(theta[:, index], ddof=1))
        rows.append(
            {
                "group": name,
                "posterior_median": float(np.median(theta[:, index])),
                "posterior_sd": posterior_sd,
                "posterior_sd_over_prior_sd": posterior_sd / prior_sd_theta,
                "strongest_abs_correlation_partner": names[other],
                "correlation": float(corr[index, other]),
            }
        )
    return {
        "n_draws": int(theta.shape[0]),
        "prior": "LogNormal(log-median=0, log-sd=0.25)",
        "prior_sd_on_theta_scale": prior_sd_theta,
        "rows": rows,
        "interpretation_limit": (
            "Posterior contraction measures learning under this likelihood and prior. "
            "It is not a per-parameter identifiability certificate."
        ),
        "source": str(path),
        "source_sha256": sha256(path),
    }


def model_form_selection() -> dict:
    path = MODELFORM / "out" / "verdicts.json"
    verdicts = load_json(path)
    rows = []
    for name, record in verdicts["HQ2"]["per_class"].items():
        if not record["genuine"]:
            continue
        best = record["best"]
        control = record["class_mean_vs_A1"]
        rows.append(
            {
                "class": name,
                "n_pooled": int(record["n_pooled"]),
                "selected_best_candidate": best["cid"],
                "selected_best_delta_mean": float(best["delta_mean"]),
                "selected_best_delta_se": float(best["delta_se"]),
                "class_mean_delta_mean": float(control["delta_mean"]),
                "class_mean_delta_se": float(control["delta_se"]),
                "selection_note": record["note"],
            }
        )
    return {
        "rows": rows,
        "source": str(path),
        "source_sha256": sha256(path),
    }


def runtime_summary() -> list[dict]:
    studies = [
        ("Modal FEM + NUTS evaluation", MODAL / "runtime.json"),
        ("Exact 28-candidate rerank", EXACT / "runtime.json"),
        ("Model-form pilot", MODELFORM / "runtime.json"),
        ("Validated net-CG port", NETCG_PORT / "runtime.json"),
    ]
    rows = []
    for label, path in studies:
        record = load_json(path)
        rows.append(
            {
                "study": label,
                "active_runtime_s": float(record["active_runtime_s"]),
                "elapsed_wallclock_s": float(record["elapsed_wallclock_s"]),
                "source": str(path),
                "source_sha256": sha256(path),
            }
        )
    return rows


def posterior_bookkeeping() -> list[dict]:
    scorecard_path = IFT / "out" / "scorecard.json"
    scorecard = load_json(scorecard_path)
    ift = scorecard["arms"]["IFT"]
    m2 = scorecard["arms"]["M2"]
    return [
        {
            "run": "Modal frequency, all 18 modes",
            "target": "9 stiffness scales + fractional modal residual scale",
            "sampler": "NUTS, 4 chains",
            "diagnostic": "R-hat 1.022; ESS 232; 0 divergences",
            "finding": "Converged for the modal-frequency target only.",
            "raw_draws_retained": True,
        },
        {
            "run": "Whole-FRF +X held-out fold",
            "target": "stiffness, gain, and correlated output-error/noise scales",
            "sampler": "NUTS, 4 chains",
            "diagnostic": "R-hat 48.8; ESS 2.0 for the displayed fold (study worst R-hat 360.6)",
            "finding": "Chains occupied separated solutions; predictive interval is not trustworthy.",
            "raw_draws_retained": True,
        },
        {
            "run": "Free-discrepancy M2 whole-FRF comparator",
            "target": "stiffness + free discrepancy amplitude sigma_d",
            "sampler": "NUTS and TMCMC escalation",
            "diagnostic": "cross-run R-hat 129; sigma_d approached 7.4; reported interval scale was about 1e17",
            "finding": "The discrepancy scale was boundary-seeking and not stably identified.",
            "raw_draws_retained": False,
        },
        {
            "run": "IFT whole-FRF comparator",
            "target": "4 stiffness scales + bounded physics-trust beta + gain",
            "sampler": "TMCMC, 4 independent populations per split",
            "diagnostic": (
                f"cross-run R-hat {ift['crossrun_rhat_dist']['min']:.4f}–"
                f"{ift['crossrun_rhat_dist']['max']:.4f}; beta reduced "
                f"{ift['beta']['collapse_factor_med']:.1f}x from its forward-model nominal value"
            ),
            "finding": "Computationally reproducible for this bounded target; learned low physics trust and over-wide band-GRMS.",
            "raw_draws_retained": False,
        },
    ]


def main() -> None:
    payload = {
        "purpose": "source-backed audit tables for the advisor progress report",
        "science_recomputed": False,
        "modal_posterior_contraction": modal_contraction(),
        "model_form_selection": model_form_selection(),
        "runtime_summary": runtime_summary(),
        "posterior_bookkeeping": posterior_bookkeeping(),
        "trace_plot_limit": (
            "Raw modal and whole-FRF NUTS draws are retained. The reportable IFT/M2 TMCMC artifact set "
            "retains run summaries but not raw populations; no IFT/M2 trace or pair plot is reconstructed."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
