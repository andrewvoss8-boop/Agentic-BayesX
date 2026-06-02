#!/usr/bin/env python3
"""Deterministic artifact verifier used by harness driver."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Iterable


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_files_exist(base_dir: Path, required_files: Iterable[str]) -> list[str]:
    missing: list[str] = []
    for rel in required_files:
        target = base_dir / rel
        if not target.exists():
            missing.append(rel)
    return missing


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-dir", required=True, type=Path)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text())
    required = spec.get("required_files", [])
    if not isinstance(required, list):
        raise ValueError("spec.required_files must be a list")

    missing = ensure_files_exist(args.base_dir, required)
    result = {
        "base_dir": str(args.base_dir),
        "missing": missing,
        "required_count": len(required),
        "artifact_hashes": {},
        "status": "pass" if not missing else "fail",
    }

    if not missing:
        for rel in required:
            result["artifact_hashes"][rel] = sha256_file(args.base_dir / rel)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2))
    return 0 if result["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
