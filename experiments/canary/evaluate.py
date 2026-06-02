#!/usr/bin/env python3
"""Deterministic evaluation for canary trial."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    baseline = json.loads((root / "baseline.json").read_text())
    candidate = json.loads((root / "candidate.json").read_text())

    target = float(baseline["target_x"])
    x = float(candidate["x"])
    rmse = abs(x - target)

    metrics = {
        "rmse": rmse,
        "target_x": target,
        "x": x,
        "status": "pass" if rmse <= 0.1 else "fail",
    }
    (root / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
