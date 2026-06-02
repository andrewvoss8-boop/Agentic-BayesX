#!/usr/bin/env python3
"""Generate a first-pass sensitivity-to-assumptions artifact."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from src.twodof.synthetic_data import NoiseConfig, generate_dataset


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "artifacts" / "reports" / "sensitivity_assumptions"


def _rel_error_metrics(data: dict) -> dict:
    per_channel = {}
    for name, clean in data["channels_clean"].items():
        total = data["error_components"][name]["total_error"]
        denom = np.maximum(np.abs(clean), 1e-12)
        rel = np.abs(total) / denom
        per_channel[name] = {
            "median_relative_error": float(np.median(rel)),
            "p95_relative_error": float(np.quantile(rel, 0.95)),
            "max_relative_error": float(np.max(rel)),
        }
    return per_channel


def _scenario_summary(name: str, noise: NoiseConfig) -> dict:
    data = generate_dataset(noise=noise)
    per_channel = _rel_error_metrics(data)
    all_medians = [values["median_relative_error"] for values in per_channel.values()]
    all_p95 = [values["p95_relative_error"] for values in per_channel.values()]
    return {
        "name": name,
        "noise_config": {
            "sigma_re": noise.sigma_re,
            "sigma_im": noise.sigma_im,
            "discrepancy_scale": noise.discrepancy_scale,
            "discrepancy_corr_logfreq": noise.discrepancy_corr_logfreq,
            "discrepancy_coordinate": noise.discrepancy_coordinate,
            "seed": noise.seed,
        },
        "qoi_peak_tray_accel_truth": data["truth"]["qoi_peak_tray_accel"],
        "median_channel_relative_error": float(np.median(all_medians)),
        "max_channel_p95_relative_error": float(np.max(all_p95)),
        "per_channel": per_channel,
    }


def _plot_scenarios(scenarios: list[dict], path: Path) -> Path:
    names = [s["name"] for s in scenarios]
    med = [s["median_channel_relative_error"] for s in scenarios]
    p95 = [s["max_channel_p95_relative_error"] for s in scenarios]
    x = np.arange(len(names))
    width = 0.36

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - width / 2, med, width, label="median channel rel error")
    ax.bar(x + width / 2, p95, width, label="max channel p95 rel error")
    ax.set_xticks(x, names, rotation=25, ha="right")
    ax.set_ylabel("relative error vs clean synthetic truth")
    ax.set_title("Sensitivity to assumed synthetic error hyperparameters", loc="left", fontweight="bold")
    ax.grid(True, axis="y", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    baseline = NoiseConfig()
    configs = [
        ("baseline", baseline),
        ("high_sensor_noise", replace(baseline, sigma_re=0.05, sigma_im=0.05)),
        ("high_gp_discrepancy", replace(baseline, discrepancy_scale=0.08)),
        ("long_gp_correlation", replace(baseline, discrepancy_corr_logfreq=0.20)),
        ("low_noise_optimistic", replace(baseline, sigma_re=0.005, sigma_im=0.005, discrepancy_scale=0.01)),
    ]
    scenarios = [_scenario_summary(name, noise) for name, noise in configs]
    plot_path = _plot_scenarios(scenarios, OUT_DIR / "sensitivity_error_assumptions.png")

    report = {
        "purpose": "First-pass sensitivity check for assumed synthetic observation noise and GP discrepancy hyperparameters.",
        "scope": "Synthetic data error sensitivity only; this is not yet posterior sensitivity or BOED.",
        "plot": str(plot_path.relative_to(ROOT)),
        "scenarios": scenarios,
        "miss_documented": "The original packet named uncertainty types but did not show sensitivity to those assumptions.",
    }
    (OUT_DIR / "sensitivity_assumptions.json").write_text(json.dumps(report, indent=2))

    rows = "\n".join(
        f"| {s['name']} | {s['noise_config']['sigma_re']} | {s['noise_config']['discrepancy_scale']} | "
        f"{s['noise_config']['discrepancy_corr_logfreq']} | {s['median_channel_relative_error']:.4g} | "
        f"{s['max_channel_p95_relative_error']:.4g} |"
        for s in scenarios
    )
    md = f"""# Sensitivity to Error Assumptions

This first sensitivity artifact varies the synthetic observation-noise and GP-discrepancy assumptions and measures error against the clean synthetic truth.

It is deliberately modest: it does not claim posterior sensitivity, BOED usefulness, or robustness of the engineering conclusion. It documents a miss in the prior packet: uncertainty types were named, but the workflow did not show how outputs change under different assumptions.

![Sensitivity plot](<{plot_path.resolve()}>)

| Scenario | sigma_re | discrepancy_scale | discrepancy_corr_logfreq | median rel error | max p95 rel error |
|---|---:|---:|---:|---:|---:|
{rows}

## Next Sensitivity Steps

- Repeat the study through full MCMC posterior summaries, not only synthetic-data error summaries.
- Vary structural assumptions such as damping, source/load convention, and tied versus untied coupling.
- Report whether experiment recommendations or QOI uncertainty rankings change under each assumption set.
"""
    (OUT_DIR / "sensitivity_assumptions.md").write_text(md)
    print(json.dumps({"report": str((OUT_DIR / "sensitivity_assumptions.json").relative_to(ROOT)), "plot": str(plot_path.relative_to(ROOT))}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
