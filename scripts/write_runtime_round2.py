#!/usr/bin/env python3
"""Write runtime.json with active_runtime_s (sum of per-command execution times) and
elapsed_wallclock_s. Active excludes human-approval wait. Reads the pipeline /usr/bin/time
'real' from pipeline_run.log and optional measured components from runtime_components.json."""
from __future__ import annotations
import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "artifacts/reports/runner_claude_opus48_round2_20260602"


def parse_real_seconds(log_path: Path):
    if not log_path.exists():
        return None
    m = re.search(r"^real\s+([0-9.]+)", log_path.read_text(), re.MULTILINE)
    return float(m.group(1)) if m else None


def main():
    comp_path = OUT / "runtime_components.json"
    comp = json.loads(comp_path.read_text()) if comp_path.exists() else {}
    pipeline_real = parse_real_seconds(OUT / "pipeline_run.log")
    if pipeline_real is not None:
        comp["full_pipeline_run_s"] = round(pipeline_real, 2)
    # components are per-command active execution times (s)
    components = {
        "environment_build_venv_install_s": comp.get("environment_build_venv_install_s", 0.0),
        "forward_model_validation_s": comp.get("forward_model_validation_s", 0.0),
        "smoke_test_s": comp.get("smoke_test_s", 0.0),
        "full_pipeline_run_s": comp.get("full_pipeline_run_s", 0.0),
        "discarded_first_full_run_s": comp.get("discarded_first_full_run_s", 0.0),
        "checker_s": comp.get("checker_s", 0.0),
    }
    active = round(sum(components.values()), 2)
    elapsed = round(comp.get("elapsed_wallclock_s", active), 2)
    if elapsed < active:
        elapsed = active
    runtime = {
        "active_runtime_s": active,
        "elapsed_wallclock_s": elapsed,
        "note": "active_runtime_s = sum of per-command execution times (env build + validation + smoke "
                "+ full pipeline run + checker + one discarded first full run). elapsed_wallclock_s "
                ">= active (includes brief gaps between commands; no human-approval wait was inside "
                "the measured commands).",
        "components_s": components,
        "reported_fit_only_s": comp.get("reported_fit_only_s"),
    }
    (OUT / "runtime.json").write_text(json.dumps(runtime, indent=2))
    print(json.dumps(runtime, indent=2))


if __name__ == "__main__":
    main()
