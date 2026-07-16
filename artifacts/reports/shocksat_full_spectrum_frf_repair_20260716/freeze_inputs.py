#!/usr/bin/env python3
"""Freeze the minimal reviewed-study inputs before repair collection."""
from __future__ import annotations

import hashlib
from pathlib import Path


WS = Path(__file__).resolve().parent
ROOT = WS.parents[2]
SOURCE = ROOT / "artifacts/reports/shocksat_full_spectrum_frf_20260714"
INPUTS = [
    "check.py",
    "CHECKER.sha256",
    "code/collect_results.py",
    "code/arm_f_combine.py",
    "out/exact_freeze_scores.json",
    "out/arm_E.json",
    "out/netcg_results.json",
    "out/vault_results.json",
    "out/query_log.jsonl",
]


def main():
    rows = []
    for rel in INPUTS:
        digest = hashlib.sha256((SOURCE / rel).read_bytes()).hexdigest()
        rows.append(f"{digest}  {rel}")
    (WS / "SOURCE_INPUTS.sha256").write_text("\n".join(rows) + "\n")
    print(f"froze {len(rows)} reviewed inputs")


if __name__ == "__main__":
    main()
