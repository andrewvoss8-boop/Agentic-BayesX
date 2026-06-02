#!/usr/bin/env python3
"""Candidate model artifact for canary trial."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    candidate = {
        "x": 2.0,
        "notes": "Deterministic baseline candidate.",
    }
    (root / "candidate.json").write_text(json.dumps(candidate, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
