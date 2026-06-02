#!/usr/bin/env python3
"""Check the sensitivity-to-assumptions artifact exists and is explicit about scope."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report_path = root / "artifacts" / "reports" / "sensitivity_assumptions" / "sensitivity_assumptions.json"
    md_path = root / "artifacts" / "reports" / "sensitivity_assumptions" / "sensitivity_assumptions.md"
    plot_path = root / "artifacts" / "reports" / "sensitivity_assumptions" / "sensitivity_error_assumptions.png"
    missing_files = [str(p.relative_to(root)) for p in [report_path, md_path, plot_path] if not p.exists()]

    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    scenarios = report.get("scenarios", [])
    scenario_count_ok = len(scenarios) >= 4
    scope_ok = "not yet posterior sensitivity" in report.get("scope", "")
    has_baseline = any(s.get("name") == "baseline" for s in scenarios)
    values_ok = all(
        s.get("median_channel_relative_error", -1) >= 0
        and s.get("max_channel_p95_relative_error", -1) >= 0
        for s in scenarios
    )

    out_report = {
        "missing_files": missing_files,
        "scenario_count": len(scenarios),
        "scenario_count_ok": scenario_count_ok,
        "scope_ok": scope_ok,
        "has_baseline": has_baseline,
        "values_ok": values_ok,
        "pass": not missing_files and scenario_count_ok and scope_ok and has_baseline and values_ok,
    }
    out = root / "artifacts" / "tests" / "sensitivity_artifact_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(out_report, indent=2))
    print(json.dumps(out_report, indent=2))
    return 0 if out_report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
