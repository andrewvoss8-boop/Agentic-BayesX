#!/usr/bin/env python3
"""Check tied coupling assumptions and saved synthetic error components."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np


EXPECTED_ERROR_COMPONENTS = {"gp_discrepancy", "iid_sensor_noise", "total_error"}


def _complex_from_json(raw: dict) -> np.ndarray:
    return np.asarray(raw["real"], dtype=float) + 1j * np.asarray(raw["imag"], dtype=float)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    data_path = root / "artifacts" / "synthetic" / "twodof_dataset.json"
    raw = json.loads(data_path.read_text()) if data_path.exists() else {}
    truth = raw.get("truth", {})
    params = truth.get("params", {})
    parameterization = truth.get("parameterization", {})
    noise = truth.get("noise", {})

    tied_coupling_ok = (
        abs(params.get("k12", float("nan")) - params.get("k2", float("nan"))) < 1e-9
        and abs(params.get("c12", float("nan")) - params.get("c2", float("nan"))) < 1e-12
        and parameterization.get("tied_parameters") == {"k12": "k2", "c12": "c2"}
    )
    log_frequency_gp_ok = (
        noise.get("discrepancy_coordinate") == "natural_log_frequency"
        and float(noise.get("discrepancy_corr_logfreq", -1.0)) > 0.0
        and "discrepancy_corr_hz" not in noise
    )

    missing_error_channels: list[str] = []
    missing_error_components: list[str] = []
    bad_error_reconstruction: list[str] = []
    channels_clean = raw.get("channels_clean", {})
    channels_obs = raw.get("channels_obs", {})
    error_components = raw.get("error_components", {})
    for channel in channels_clean:
        if channel not in error_components:
            missing_error_channels.append(channel)
            continue
        components = error_components[channel]
        missing = sorted(EXPECTED_ERROR_COMPONENTS - set(components))
        if missing:
            missing_error_components.extend([f"{channel}:{name}" for name in missing])
            continue
        clean = _complex_from_json(channels_clean[channel])
        obs = _complex_from_json(channels_obs[channel])
        total = _complex_from_json(components["total_error"])
        if not np.allclose(obs - clean, total, rtol=1e-10, atol=1e-10):
            bad_error_reconstruction.append(channel)

    report = {
        "tied_coupling_ok": tied_coupling_ok,
        "log_frequency_gp_ok": log_frequency_gp_ok,
        "missing_error_channels": missing_error_channels,
        "missing_error_components": missing_error_components,
        "bad_error_reconstruction": bad_error_reconstruction,
        "pass": (
            tied_coupling_ok
            and log_frequency_gp_ok
            and not missing_error_channels
            and not missing_error_components
            and not bad_error_reconstruction
        ),
    }
    out = root / "artifacts" / "tests" / "tied_coupling_and_errors_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
