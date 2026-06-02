#!/usr/bin/env python3
"""Harness runner with immutable checker verification and run bundle logging."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
from pathlib import Path


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(manifest_path: Path) -> dict[str, str]:
    lines = [
        line.strip()
        for line in manifest_path.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    out: dict[str, str] = {}
    for line in lines:
        digest, rel = line.split(maxsplit=1)
        out[rel.strip()] = digest.strip()
    return out


def verify_manifest(repo_root: Path, manifest: dict[str, str]) -> list[str]:
    mismatches: list[str] = []
    for rel, expected in manifest.items():
        actual_path = repo_root / rel
        if not actual_path.exists():
            mismatches.append(f"{rel}:missing")
            continue
        actual = sha256_file(actual_path)
        if actual != expected:
            mismatches.append(f"{rel}:hash-mismatch")
    return mismatches


def git_head(repo_root: Path) -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip()
    except Exception:
        return "nogit"


def run_command(command: str, cwd: Path) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        cwd=cwd,
        shell=True,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONHASHSEED": "0"},
    )
    stdout = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode, stdout


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    cfg = json.loads(args.config.read_text())
    trial_name = cfg["trial_name"]
    work_dir = (repo_root / cfg["work_dir"]).resolve()
    run_cmd = cfg["run_command"]
    check_cmd = cfg["check_command"]
    checker_manifest = (repo_root / cfg["checker_manifest"]).resolve()
    immutable_manifest = load_manifest(checker_manifest)

    pre_mismatch = verify_manifest(repo_root, immutable_manifest)
    if pre_mismatch:
        print(json.dumps({"status": "fail", "reason": "checker-modified-before-run", "details": pre_mismatch}, indent=2))
        return 3

    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bundle_dir = repo_root / "artifacts" / "runs" / f"{trial_name}-{ts}"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    run_code, run_log = run_command(run_cmd, work_dir)
    check_code, check_log = run_command(check_cmd, work_dir)

    post_mismatch = verify_manifest(repo_root, immutable_manifest)
    status = "pass" if (run_code == 0 and check_code == 0 and not post_mismatch) else "fail"

    metadata = {
        "trial_name": trial_name,
        "timestamp": ts,
        "status": status,
        "git_head": git_head(repo_root),
        "config_path": str(args.config),
        "run_command": run_cmd,
        "check_command": check_cmd,
        "run_code": run_code,
        "check_code": check_code,
        "checker_manifest": str(checker_manifest),
        "checker_manifest_mismatch_before": pre_mismatch,
        "checker_manifest_mismatch_after": post_mismatch,
    }
    (bundle_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (bundle_dir / "run.log").write_text(run_log)
    (bundle_dir / "check.log").write_text(check_log)

    print(json.dumps(metadata, indent=2))
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
