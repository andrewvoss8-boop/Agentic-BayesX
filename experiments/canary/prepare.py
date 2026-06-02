#!/usr/bin/env python3
"""Immutable canary baseline setup."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    out = {
        "target_x": 2.0,
        "name": "quadratic_canary",
        "objective": "(x-target_x)^2",
    }
    (root / "baseline.json").write_text(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
