#!/usr/bin/env python3
"""Lightweight checks for the ShockSat new-papers applicability review."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

REQUIRED = [
    "priority_deliverables.md",
    "decisions_log.md",
    "bibliography.md",
    "paper_applicability_review.md",
    "runner_prompts/01_sequential_statfem_shocksat_runner_prompt.md",
    "runner_prompts/02_latent_force_bnn_shocksat_runner_prompt.md",
    "runner_prompts/03_multilevel_rom_submodel_shocksat_runner_prompt.md",
    "runtime.json",
]


def read(rel: str) -> str:
    path = ROOT / rel
    return path.read_text(encoding="utf-8") if path.exists() else ""


def add(checks: list[dict], gate: str, ok: bool, red_on_fail: bool = True, note: str = "") -> tuple[int, int]:
    status = "GREEN" if ok else ("RED" if red_on_fail else "YELLOW")
    item = {"gate": gate, "status": status}
    if note:
        item["note"] = note
    checks.append(item)
    if status == "RED":
        return 0, 1
    if status == "YELLOW":
        return 1, 0
    return 0, 0


def main() -> int:
    checks: list[dict] = []
    yellow = 0
    red = 0

    for rel in REQUIRED:
        y, r = add(checks, f"required_file:{rel}", (ROOT / rel).exists() and (ROOT / rel).stat().st_size > 100)
        yellow += y
        red += r

    review = read("paper_applicability_review.md")
    bib = read("bibliography.md")
    combined = review + "\n" + bib

    for phrase in [
        "Multi-level digital twin",
        "Statistical finite elements",
        "Probabilistic Digital Twin",
        "Applicability: HIGH",
        "Applicability: MODERATE-HIGH",
        "Applicability: MODERATE-LOW",
        "Overall: YELLOW",
    ]:
        y, r = add(checks, f"review_phrase:{phrase}", phrase in combined)
        yellow += y
        red += r

    for rel in REQUIRED[4:7]:
        prompt = read(rel)
        for phrase in [
            "AGENTS.md",
            "held-out",
            "check.py",
            "runtime.json",
            "GREEN",
            "YELLOW",
            "RED",
        ]:
            y, r = add(checks, f"prompt:{Path(rel).name}:{phrase}", phrase in prompt)
            yellow += y
            red += r

    for caution in [
        "No ShockSat metric has improved",
        "empirical Bayes",
        "not a Bayesian/statFEM contribution",
        "offline",
        "no measured local stress",
    ]:
        y, r = add(checks, f"honesty_caution:{caution}", caution in combined, red_on_fail=False)
        yellow += y
        red += r

    y, r = add(
        checks,
        "exploratory_status",
        False,
        red_on_fail=False,
        note="Runner prompts are hypotheses only; no ShockSat improvement is claimed until a future checker-backed run.",
    )
    yellow += y
    red += r

    overall = "RED" if red else ("YELLOW" if yellow else "GREEN")
    report = {
        "task": "Review three new papers for ShockSat applicability and create runner prompts where applicable.",
        "overall": overall,
        "counts": {
            "green": sum(1 for c in checks if c["status"] == "GREEN"),
            "yellow": sum(1 for c in checks if c["status"] == "YELLOW"),
            "red": sum(1 for c in checks if c["status"] == "RED"),
        },
        "checks": checks,
    }
    (ROOT / "checker_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 1 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())

