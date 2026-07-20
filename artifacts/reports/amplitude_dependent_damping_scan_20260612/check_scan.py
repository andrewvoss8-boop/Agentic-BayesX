#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent


def main() -> int:
    checks = []
    results_path = OUT / "results.json"
    report_path = OUT / "analysis_report.md"
    required = [
        results_path,
        report_path,
        OUT / "runtime.json",
        OUT / "figures/mpl_ruler_amplitude_screen.png",
        OUT / "figures/dataset_status_summary.png",
        OUT / "priority_deliverables.md",
        OUT / "decisions_log.md",
        OUT / "assumptions_ledger.md",
        OUT / "quantity_contracts.md",
    ]
    for path in required:
        checks.append({"name": f"exists:{path.name}", "status": "GREEN" if path.exists() else "RED"})
    if results_path.exists():
        data = json.loads(results_path.read_text())
        checks.append({"name": "overall_status_yellow", "status": "GREEN" if data.get("result_status") == "YELLOW" else "RED"})
        checks.append({"name": "mpl_signs_present", "status": "GREEN" if data.get("mpl", {}).get("signs_present") else "RED"})
        checks.append({"name": "shocksat_low_coherence_caveat", "status": "GREEN" if "coherence" in data.get("shocksat", {}).get("interpretation", "").lower() else "RED"})
        checks.append({"name": "panel_amplitude_sweep_caveat", "status": "GREEN" if "amplitude" in data.get("suspended_panel", {}).get("interpretation", "").lower() else "RED"})
    if report_path.exists():
        text = report_path.read_text()
        for phrase in [
            "MPL test stand: YELLOW",
            "ShockSat: YELLOW",
            "Suspended panel: YELLOW",
            "not a calibrated hysteresis loop",
            "Overall status: YELLOW",
        ]:
            checks.append({"name": f"report_mentions:{phrase}", "status": "GREEN" if phrase in text else "RED"})
    red = sum(1 for c in checks if c["status"] == "RED")
    green = sum(1 for c in checks if c["status"] == "GREEN")
    report = {
        "overall": "RED" if red else "YELLOW",
        "green": green,
        "red": red,
        "yellow": 1 if red == 0 else 0,
        "yellow_caveat": "This is a triage screen; hysteresis is not proven by a force-displacement loop.",
        "checks": checks,
    }
    (OUT / "checker_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 1 if red else 0


if __name__ == "__main__":
    raise SystemExit(main())
