#!/usr/bin/env python3
"""Check the linear-unit key transfer-function review artifact."""

from __future__ import annotations

import json
import math
from pathlib import Path


REQUIRED_FRFS = {
    "dome_only_a1_over_f1",
    "coupled_a1_over_f1",
    "coupled_a2_over_f1",
    "coupled_a1_over_f2",
    "coupled_a2_over_f2",
    "dome_source_apparent_mass_7004c",
    "dome_load_apparent_mass_7004c",
    "tray_load_apparent_mass_7004c",
    "coupled_primary_support_apparent_mass",
    "coupled_tray_support_apparent_mass",
    "coupled_total_base_apparent_mass",
}

APPARENT_MASS_FRFS = {
    "coupled_primary_support_apparent_mass",
    "coupled_tray_support_apparent_mass",
    "coupled_total_base_apparent_mass",
}

SOURCE_APPARENT_MASS_FRFS = {
    "dome_source_apparent_mass_7004c",
}

LOAD_APPARENT_MASS_FRFS = {
    "dome_load_apparent_mass_7004c",
    "tray_load_apparent_mass_7004c",
}


def _finite_positive(value: object) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value) and value >= 0.0


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    summary_path = root / "artifacts" / "reports" / "key_frf_summary.json"
    plot_path = root / "artifacts" / "plots" / "key_2dof_transfer_functions_linear.png"

    missing_files = [
        str(path.relative_to(root))
        for path in [summary_path, plot_path]
        if not path.exists()
    ]

    summary = json.loads(summary_path.read_text()) if summary_path.exists() else {}
    frfs = summary.get("frfs", [])
    frf_ids = {frf.get("id") for frf in frfs}
    missing_frfs = sorted(REQUIRED_FRFS - frf_ids)
    bad_units = [
        frf.get("id")
        for frf in frfs
        if frf.get("units") not in {"accel/force", "mass", "accel/accel"}
    ]
    bad_scales = [
        frf.get("id")
        for frf in frfs
        if frf.get("reported_scale") != "linear_magnitude_not_db"
    ]
    bad_values = [
        frf.get("id")
        for frf in frfs
        if not (
            _finite_positive(frf.get("min_magnitude"))
            and _finite_positive(frf.get("max_magnitude"))
            and _finite_positive(frf.get("min_frequency_hz"))
            and _finite_positive(frf.get("max_frequency_hz"))
        )
    ]
    load_apparent_mass_without_interior_peak = [
        frf.get("id")
        for frf in frfs
        if frf.get("id") in (APPARENT_MASS_FRFS | LOAD_APPARENT_MASS_FRFS) and not frf.get("max_is_interior_frequency")
    ]
    load_apparent_mass_without_resonant_amplification = [
        frf.get("id")
        for frf in frfs
        if (
            frf.get("id") in (APPARENT_MASS_FRFS | LOAD_APPARENT_MASS_FRFS)
            and _finite_positive(frf.get("first_magnitude"))
            and frf.get("max_magnitude", 0.0) <= 1.2 * max(frf.get("first_magnitude", 0.0), 1e-12)
        )
    ]
    source_apparent_mass_without_interior_notch = [
        frf.get("id")
        for frf in frfs
        if frf.get("id") in SOURCE_APPARENT_MASS_FRFS and not frf.get("min_is_interior_frequency")
    ]
    source_apparent_mass_without_low_frequency_growth = [
        frf.get("id")
        for frf in frfs
        if (
            frf.get("id") in SOURCE_APPARENT_MASS_FRFS
            and _finite_positive(frf.get("min_magnitude"))
            and frf.get("first_magnitude", 0.0) <= 10.0 * max(frf.get("min_magnitude", 0.0), 1e-12)
        )
    ]

    frequency_grid = summary.get("frequency_grid", {})
    reference_lines = summary.get("reference_lines", {})
    mass_lines = reference_lines.get("mass_units", {})
    fn_lines = reference_lines.get("uncoupled_natural_frequencies_hz", {})
    grid_ok = (
        frequency_grid.get("x_axis_scale") == "log"
        and frequency_grid.get("plot_grid_spacing") == "geometric"
        and frequency_grid.get("count", 0) >= 100
    )
    mass_reference_ok = all(
        _finite_positive(mass_lines.get(key))
        for key in ["m1_primary_dome", "m2_secondary_tray", "m1_plus_m2_total"]
    )
    total_mass_ok = (
        mass_reference_ok
        and abs(
            mass_lines["m1_plus_m2_total"]
            - (mass_lines["m1_primary_dome"] + mass_lines["m2_secondary_tray"])
        )
        < 1e-12
    )
    natural_frequency_reference_ok = all(
        _finite_positive(fn_lines.get(key))
        for key in ["tray_uncoupled_fn_hz", "dome_uncoupled_fn_hz"]
    )
    has_accel_force = any(frf.get("units") == "accel/force" for frf in frfs)
    has_source_apparent_mass = any(frf.get("quantity") == "source_apparent_mass" for frf in frfs)
    has_load_apparent_mass = any(frf.get("quantity") == "load_apparent_mass" for frf in frfs)
    has_apparent_mass = has_source_apparent_mass and has_load_apparent_mass
    count_ok = summary.get("frf_count", 0) >= 5 and len(frfs) >= 5

    report = {
        "missing_files": missing_files,
        "missing_frfs": missing_frfs,
        "bad_units": bad_units,
        "bad_scales": bad_scales,
        "bad_values": bad_values,
        "load_apparent_mass_without_interior_peak": load_apparent_mass_without_interior_peak,
        "load_apparent_mass_without_resonant_amplification": load_apparent_mass_without_resonant_amplification,
        "source_apparent_mass_without_interior_notch": source_apparent_mass_without_interior_notch,
        "source_apparent_mass_without_low_frequency_growth": source_apparent_mass_without_low_frequency_growth,
        "grid_ok": grid_ok,
        "mass_reference_ok": mass_reference_ok,
        "total_mass_ok": total_mass_ok,
        "natural_frequency_reference_ok": natural_frequency_reference_ok,
        "has_accel_force": has_accel_force,
        "has_source_apparent_mass": has_source_apparent_mass,
        "has_load_apparent_mass": has_load_apparent_mass,
        "frf_count": summary.get("frf_count"),
        "pass": (
            not missing_files
            and not missing_frfs
            and not bad_units
            and not bad_scales
            and not bad_values
            and not load_apparent_mass_without_interior_peak
            and not load_apparent_mass_without_resonant_amplification
            and not source_apparent_mass_without_interior_notch
            and not source_apparent_mass_without_low_frequency_growth
            and grid_ok
            and mass_reference_ok
            and total_mass_ok
            and natural_frequency_reference_ok
            and has_accel_force
            and has_apparent_mass
            and count_ok
        ),
    }
    out = root / "artifacts" / "tests" / "key_transfer_functions_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
