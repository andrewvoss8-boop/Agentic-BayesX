#!/usr/bin/env python3
"""Checker for the GPT-5.6 adversarial review deliverables."""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path


WS = Path(__file__).resolve().parent
RANK = {"GREEN": 0, "YELLOW": 1, "RED": 2}


def gate_files():
    required = [
        "review.md",
        "next_steps.md",
        "decisions_log.md",
        "out/claim_audit.json",
        "out/recomputed_checks.json",
        "out/fim_step_sensitivity.json",
        "runtime.json",
    ]
    missing = [name for name in required if not (WS / name).exists()]
    return ("RED", f"missing: {missing}") if missing else ("GREEN", "all required review files exist")


def gate_claims():
    path = WS / "out/claim_audit.json"
    if not path.exists():
        return "RED", "claim audit missing"
    claims = json.loads(path.read_text())
    expected = {f"C{i}" for i in range(1, 9)}
    if set(claims) != expected:
        return "RED", f"claim IDs are {sorted(claims)}, expected C1-C8"
    allowed = {"SOUND", "OVER-CLAIMED", "WRONG", "CANNOT-VERIFY"}
    bad = [key for key, value in claims.items() if value.get("status") not in allowed]
    if bad:
        return "RED", f"invalid claim statuses: {bad}"
    required = {"status", "gate_status", "file_checked", "recomputed_number", "study_number", "note"}
    incomplete = [key for key, value in claims.items() if not required.issubset(value)]
    if incomplete:
        return "RED", f"incomplete claim records: {incomplete}"
    return "GREEN", "all eight claims have complete structured verdicts"


def gate_report():
    if not (WS / "review.md").exists():
        return "RED", "review.md missing"
    text = (WS / "review.md").read_text()
    required = [
        "Overall review status: RED",
        "Does the study's OVERALL YELLOW",
        "S1, S2, and S5",
        "S3 and S4",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        return "RED", f"report missing required conclusions: {missing}"
    return "GREEN", "report states overall status and corrected S1-S5 conclusion"


def gate_next_steps():
    if not (WS / "next_steps.md").exists():
        return "RED", "next_steps.md missing"
    text = (WS / "next_steps.md").read_text().lower()
    required = [
        "geometry",
        "element formulation",
        "mesh topology",
        "connectivity",
        "cost",
        "exact re-rank",
        "net-cg",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        return "RED", f"next steps missing: {missing}"
    return "GREEN", "next steps are costed and include genuine model-form actions"


def gate_repair():
    repair = WS.parent / "shocksat_full_spectrum_frf_repair_20260716/checker_report.json"
    if not repair.exists():
        return "RED", "repair checker report missing"
    result = json.loads(repair.read_text())
    if result.get("OVERALL") != "YELLOW":
        return "RED", f"repair checker is {result.get('OVERALL')}, expected YELLOW"
    return "YELLOW", "repair is YELLOW because the original checker remains incomplete"


def gate_runtime():
    if not (WS / "runtime.json").exists():
        return "RED", "runtime.json missing"
    runtime = json.loads((WS / "runtime.json").read_text())
    active = runtime.get("active_runtime_s")
    elapsed = runtime.get("elapsed_wallclock_s")
    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in (active, elapsed)):
        return "RED", "runtime fields non-finite"
    if active > elapsed:
        return "RED", f"active {active} exceeds elapsed {elapsed}"
    return "GREEN", f"active {active:.1f}s <= elapsed {elapsed:.1f}s"


def gate_self_sha():
    lock = WS / "REVIEW_CHECKER.sha256"
    if not lock.exists():
        return "RED", "review checker lock missing"
    want = lock.read_text().split()[0]
    have = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if want != have:
        return "RED", "check_review.py changed after lock"
    return "GREEN", f"review checker matches lock ({have[:12]}...)"


GATES = [
    ("V01_files", gate_files),
    ("V02_claims", gate_claims),
    ("V03_report", gate_report),
    ("V04_next_steps", gate_next_steps),
    ("V05_repair_status", gate_repair),
    ("V06_runtime", gate_runtime),
    ("V07_checker_immutable", gate_self_sha),
]


def main():
    report = {}
    overall = "GREEN"
    for name, gate in GATES:
        try:
            status, detail = gate()
        except Exception as exc:
            status, detail = "RED", f"gate crashed: {type(exc).__name__}: {exc}"
        report[name] = {"status": status, "detail": detail}
        if RANK[status] > RANK[overall]:
            overall = status
        print(f"[{status:6s}] {name}: {detail}")
    report["OVERALL"] = overall
    (WS / "review_checker_report.json").write_text(json.dumps(report, indent=2))
    print(f"\nOVERALL: {overall}")
    sys.exit(1 if overall == "RED" else 0)


if __name__ == "__main__":
    main()
