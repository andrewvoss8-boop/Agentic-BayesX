#!/usr/bin/env python3
"""Lightweight acceptance checks for the notch literature review packet."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent

REQUIRED = [
    "lit_review.md",
    "bibliography.md",
    "novelty_and_fto_notes.md",
    "gaps_and_next_experiments.md",
    "decisions_log.md",
    "priority_deliverables.md",
]


def has(path: str, needle: str) -> bool:
    return needle in (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    checks = []
    red = 0
    yellow = 0

    for name in REQUIRED:
        ok = (ROOT / name).exists() and (ROOT / name).stat().st_size > 200
        checks.append({"gate": f"required_file:{name}", "status": "GREEN" if ok else "RED"})
        red += 0 if ok else 1

    lit_path = ROOT / "lit_review.md"
    lit = lit_path.read_text(encoding="utf-8") if lit_path.exists() else ""
    for letter in "ABCDEFGH":
        ok = re.search(rf"^## {letter}\.", lit, re.MULTILINE) is not None
        checks.append({"gate": f"lit_section:{letter}", "status": "GREEN" if ok else "RED"})
        red += 0 if ok else 1

    for label in ["CONFIRMED", "PARTIALLY-KNOWN", "NOVEL-AS-FAR-AS-FOUND", "CONTRADICTED"]:
        ok = label in lit
        status = "GREEN" if ok else "YELLOW"
        checks.append({"gate": f"in_house_status_label_seen:{label}", "status": status})
        yellow += 0 if ok else 1

    for tier in ["Tier: standard", "Tier: peer-reviewed", "Tier: conference", "Tier: patent"]:
        seen = tier in lit or tier in (ROOT / "bibliography.md").read_text(encoding="utf-8")
        status = "GREEN" if seen else "YELLOW"
        checks.append({"gate": f"source_tier_seen:{tier}", "status": status})
        yellow += 0 if seen else 1

    fto = (ROOT / "novelty_and_fto_notes.md").read_text(encoding="utf-8") if (ROOT / "novelty_and_fto_notes.md").exists() else ""
    for phrase in ["US8731868B2", "not a legal opinion", "before public sharing"]:
        ok = phrase.lower() in fto.lower()
        checks.append({"gate": f"fto_phrase:{phrase}", "status": "GREEN" if ok else "RED"})
        red += 0 if ok else 1

    unverified_as_fact = "UNVERIFIED FACT" in (lit + fto)
    checks.append({"gate": "no_unverified_fact_marker", "status": "RED" if unverified_as_fact else "GREEN"})
    red += 1 if unverified_as_fact else 0

    documented_limits = "limited access" in ((ROOT / "bibliography.md").read_text(encoding="utf-8").lower() if (ROOT / "bibliography.md").exists() else "")
    checks.append({
        "gate": "coverage_limits_documented",
        "status": "YELLOW" if documented_limits else "GREEN",
        "note": "Limited-access sources are documented; review is usable with this caveat.",
    })
    yellow += 1 if documented_limits else 0

    overall = "RED" if red else ("YELLOW" if yellow else "GREEN")
    report = {
        "overall": overall,
        "green": sum(1 for c in checks if c["status"] == "GREEN"),
        "yellow": sum(1 for c in checks if c["status"] == "YELLOW"),
        "red": red,
        "checks": checks,
    }
    (ROOT / "checker_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())
