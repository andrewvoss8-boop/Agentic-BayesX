#!/usr/bin/env python3
"""Task Card E `_Fable` — freeze the checker and the preregistration, and prove RED on an empty workspace.

Order matters and is enforced by the checker itself:
  1. FROZEN.sha256          preregistration + registries + quantity contract, hashed
  2. PREDECESSOR_GUARD.json every predecessor/frozen input hashed + the forbidden paths this run must not create
  3. checker_empty_report   proof the checker returns RED on an empty output directory
  4. CHECKER.sha256         the checker itself, hashed; never edited afterwards
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common_fable as C  # noqa: E402

FROZEN_FILES = ["preregistration.md", "quantity_contracts.md", "assumptions_ledger.md",
                "question_framing.md", "priority_deliverables.md",
                "out/split_registry.json", "out/mean_basis_registry.json", "out/basis_fable.npz",
                "out/source_manifest.json", "out/data_inventory.json", "out/known_answer_fable.json"]

# paths this run must NEVER create or modify
FORBIDDEN = [
    "artifacts/reports/shocksat_structured_discrepancy_codex_20260722",   # the card's own un-suffixed workspace
]

GUARDED_DIRS = [
    "docs/agents/structured_mean_discrepancy_20260722",
    "docs/agents/structured_discrepancy_codex_review_20260722",
]


def sha256(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    WS = C.WS
    # 1 -------------------------------------------------------------- FROZEN.sha256
    files = {}
    for rel in FROZEN_FILES:
        p = WS / rel
        if not p.exists():
            raise SystemExit(f"STOP: cannot lock, missing {rel}")
        files[rel] = sha256(p)
    (WS / "FROZEN.sha256").write_text(json.dumps(
        {"locked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "what": "preregistration, framing, registries and the immutable source-gate artifacts; the checker "
                 "verifies these hashes are unchanged at report time",
         "files": files}, indent=2))

    # 2 -------------------------------------------------------------- PREDECESSOR_GUARD.json
    man = json.loads((C.OUT / "source_manifest.json").read_text())
    guard = {s["path"]: s["sha256"] for s in man["sources"]}
    for d in GUARDED_DIRS:
        for p in sorted((C.REPO / d).rglob("*")):
            if p.is_file():
                guard[str(p.relative_to(C.REPO))] = sha256(p)
    (WS / "PREDECESSOR_GUARD.json").write_text(json.dumps(
        {"locked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "what": "every frozen input plus every file in Task Card D's directory and the Codex review "
                 "directory; none may change during this run",
         "n_files": len(guard), "forbidden_paths": FORBIDDEN, "files": guard}, indent=2))

    # 3 -------------------------------------------------------------- RED-on-empty proof
    with tempfile.TemporaryDirectory() as td:
        empty = Path(td) / "empty_ws"
        (empty / "out").mkdir(parents=True)
        (empty / "figures").mkdir()
        rep = C.OUT / "checker_empty_report.json"
        r = subprocess.run([sys.executable, str(WS / "check_fable.py"), "--ws", str(empty),
                            "--out", str(rep)], capture_output=True, text=True)
        d = json.loads(rep.read_text())
        print(r.stdout.strip()[-400:])
        if d["overall"] != "RED" or r.returncode == 0:
            raise SystemExit(f"STOP: checker did not return RED (exit {r.returncode}) on an empty workspace")
        print(f"RED-on-empty proven: overall {d['overall']}, exit {r.returncode}, "
              f"{d['counts']} on an empty output directory")

    # 4 -------------------------------------------------------------- CHECKER.sha256
    h = sha256(WS / "check_fable.py")
    (WS / "CHECKER.sha256").write_text(json.dumps(
        {"locked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
         "check_fable.py": h,
         "rule": "the checker is immutable for the rest of this run; any edit invalidates the results"},
        indent=2))
    print(f"CHECKER.sha256 locked: {h[:16]}...")


if __name__ == "__main__":
    main()
