#!/usr/bin/env python3
"""Check synthetic measurement channels are traceable and non-duplicative."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from src.twodof.synthetic_data import generate_dataset


EXPECTED_CHANNELS = [
    "dome_drive_apparent_mass_modal",
    "coupled_interface_apparent_mass_modal",
    "coupled_tray_impact_apparent_mass_test",
    "tray_standalone_accel_over_base",
    "flight_tray_accel_from_unknown_m1_force",
]


def _rel_l2(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b) / max(np.linalg.norm(a), np.linalg.norm(b), 1e-12))


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    data_path = root / "artifacts" / "synthetic" / "twodof_dataset.json"
    if data_path.exists():
        raw = json.loads(data_path.read_text())
        clean = {
            key: np.asarray(value["real"]) + 1j * np.asarray(value["imag"])
            for key, value in raw["channels_clean"].items()
        }
        metadata = raw.get("channel_metadata", {})
    else:
        data = generate_dataset()
        clean = data["channels_clean"]
        metadata = data.get("channel_metadata", {})

    missing_channels = [name for name in EXPECTED_CHANNELS if name not in clean]
    missing_metadata = [
        name
        for name in EXPECTED_CHANNELS
        if name not in metadata or not metadata[name].get("definition") or not metadata[name].get("quantity")
    ]

    ch2 = clean["coupled_interface_apparent_mass_modal"]
    ch3 = clean["coupled_tray_impact_apparent_mass_test"]
    channel_2_3_relative_l2 = _rel_l2(ch2, ch3)

    report = {
        "missing_channels": missing_channels,
        "missing_metadata": missing_metadata,
        "channel_2_3_relative_l2": channel_2_3_relative_l2,
        "pass": not missing_channels and not missing_metadata and channel_2_3_relative_l2 > 0.05,
    }

    out = root / "artifacts" / "tests" / "channel_definitions_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
