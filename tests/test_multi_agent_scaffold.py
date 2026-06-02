#!/usr/bin/env python3
"""Check the plain-English multi-agent scaffold files."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "artifacts" / "reports" / "multi_agent_first_loop_20260602"
REPORT = ROOT / "artifacts" / "tests" / "multi_agent_scaffold_report.json"


REQUIRED_PACKET_FILES = [
    "task.md",
    "framing.md",
    "assumptions.md",
    "quantity_contracts.md",
    "commands.md",
    "checks.json",
    "sources.md",
    "review.md",
    "next_prompt.md",
    "manifest.json",
]

REQUIRED_ROLES = ["lead", "runner", "checker", "reader", "reviewer", "notes"]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def main() -> int:
    failures: list[str] = []

    for filename in REQUIRED_PACKET_FILES:
        path = PACKET / filename
        if not path.exists():
            failures.append(f"missing packet file: {path}")

    manifest_path = PACKET / "manifest.json"
    manifest = read_json(manifest_path) if manifest_path.exists() else {}

    for key in [
        "payload_command",
        "sampler_standard",
        "agent_roles",
        "commands",
        "checks",
        "sources",
        "open_risks",
        "human_stop_point",
    ]:
        if key not in manifest:
            failures.append(f"manifest missing key: {key}")

    roles = set(manifest.get("agent_roles", []))
    for role in REQUIRED_ROLES:
        if role not in roles:
            failures.append(f"manifest missing role: {role}")

    for rel in manifest.get("role_files", []):
        if not (ROOT / rel).exists():
            failures.append(f"missing role file from manifest: {rel}")

    for rel in manifest.get("claude_agents", []):
        if not (ROOT / rel).exists():
            failures.append(f"missing Claude agent from manifest: {rel}")

    for rel in manifest.get("codex_prompts", []):
        if not (ROOT / rel).exists():
            failures.append(f"missing Codex prompt from manifest: {rel}")

    for rel in manifest.get("cursor_adapters", []):
        if not (ROOT / rel).exists():
            failures.append(f"missing Cursor adapter from manifest: {rel}")

    sampler = manifest.get("sampler_standard", {})
    if sampler.get("future_default") != "NUTS/HMC":
        failures.append("manifest does not state NUTS/HMC as future default")
    if "prototype" not in sampler.get("current_status", ""):
        failures.append("manifest does not label current sampler as prototype/legacy")

    claude_text = (ROOT / "CLAUDE.md").read_text()
    if "NUTS/HMC" not in claude_text:
        failures.append("CLAUDE.md missing NUTS/HMC sampler rule")
    if "random-walk Metropolis" not in claude_text:
        failures.append("CLAUDE.md missing prototype/legacy random-walk label")

    settings_path = ROOT / ".claude" / "settings.json"
    if settings_path.exists():
        settings = read_json(settings_path)
        if settings.get("agent") != "lead":
            failures.append(".claude/settings.json does not set lead as project agent")
    else:
        failures.append("missing .claude/settings.json")

    checks_path = PACKET / "checks.json"
    checks = read_json(checks_path) if checks_path.exists() else {}
    check_commands = [item.get("command") for item in checks.get("commands", [])]
    for required in [
        "bash scripts/run_fresh_2dof_statfem_fbs.sh",
        "python3 tests/test_fresh_2dof_rerun.py",
        "python3 tests/test_multi_agent_scaffold.py",
        "shasum -a 256 -c harness/checkers/manifest.sha256",
    ]:
        if required not in check_commands:
            failures.append(f"checks.json missing command: {required}")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "pass": not failures,
        "failures": failures,
        "packet": str(PACKET),
        "manifest": str(manifest_path),
        "roles": sorted(roles),
    }
    REPORT.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

