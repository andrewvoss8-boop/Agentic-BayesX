#!/usr/bin/env python3
"""Checker gate for canary experiment metrics."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    metrics_path = root / "experiments" / "canary" / "metrics.json"
    metrics = json.loads(metrics_path.read_text())

    rmse = float(metrics["rmse"])
    if rmse > 0.1:
        print(json.dumps({"status": "fail", "reason": "rmse-too-large", "rmse": rmse}, indent=2))
        return 2

    print(json.dumps({"status": "pass", "rmse": rmse}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
