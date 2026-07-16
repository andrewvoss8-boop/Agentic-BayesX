#!/usr/bin/env python3
"""Immutable checker for the 2026-07-16 full-spectrum result-collection repair."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from pathlib import Path


WS = Path(__file__).resolve().parent
ROOT = WS.parents[2]
SOURCE = ROOT / "artifacts/reports/shocksat_full_spectrum_frf_20260714"
RANK = {"GREEN": 0, "YELLOW": 1, "RED": 2}
DEV = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]


def load(path):
    with Path(path).open() as f:
        return json.load(f)


def finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def gate_source_checker():
    want = (SOURCE / "CHECKER.sha256").read_text().split()[0]
    have = sha256(SOURCE / "check.py")
    if want != have:
        return "RED", "reviewed check.py no longer matches its immutable SHA"
    return "GREEN", f"reviewed check.py remains immutable ({have[:12]}...)"


def gate_source_inputs():
    manifest = WS / "SOURCE_INPUTS.sha256"
    if not manifest.exists():
        return "RED", "SOURCE_INPUTS.sha256 missing"
    bad = []
    for line in manifest.read_text().splitlines():
        if not line.strip():
            continue
        want, rel = line.split("  ", 1)
        path = SOURCE / rel
        if not path.exists() or sha256(path) != want:
            bad.append(rel)
    if bad:
        return "RED", "reviewed repair inputs changed: " + ", ".join(bad)
    return "GREEN", "all reviewed repair inputs match their pre-repair hashes"


def gate_table_complete():
    path = WS / "out/arms_bands_table.json"
    if not path.exists():
        return "RED", "corrected arms table missing"
    table = load(path)
    bad = []
    for arm in ("A0", "A1", "B", "C", "D", "R", "F"):
        row = table.get("arms", {}).get(arm)
        if row is None:
            bad.append(f"{arm} missing")
            continue
        for band in ("sub200", "b200_500"):
            cell = row.get(band, {})
            if not finite(cell.get("mean")) or not finite(cell.get("se")):
                bad.append(f"{arm}/{band} non-finite mean or SE")
    if bad:
        return "RED", "; ".join(bad)
    return "GREEN", "all exact arm means and fold standard errors are finite"


def gate_recomputed_from_folds():
    exact = load(SOURCE / "out/exact_freeze_scores.json")
    table = load(WS / "out/arms_bands_table.json")
    bad = []
    for arm in ("A0", "A1", "B", "C", "D", "R"):
        for band in ("sub200", "b200_500"):
            values = [exact[arm]["exact"]["folds"][fold][band]["P1p"] for fold in DEV]
            mean = sum(values) / len(values)
            saved = table["arms"][arm][band]["mean"]
            if abs(mean - saved) > 5e-13:
                bad.append(f"{arm}/{band}: {saved} != fold mean {mean}")
    if bad:
        return "RED", "; ".join(bad)
    return "GREEN", "corrected means reproduce the four exact fold values"


def gate_arm_f_identity():
    table = load(WS / "out/arms_bands_table.json")
    f = table["arms"]["F"]
    c = table["arms"]["C"]
    if f.get("equals") != "C":
        return "RED", f"F must equal C under the pre-registered sequential rule, got {f.get('equals')}"
    if any(f[b] != c[b] for b in ("sub200", "b200_500")):
        return "RED", "F=C label set but numeric rows differ"
    if table.get("arm_F_rule", {}).get("source") != "pre_registered_sequential_B_then_C_then_D":
        return "RED", "arm-F method identity/provenance missing"
    return "GREEN", "F=C follows the pre-registered B→C→D sequential adoption rule"


def gate_verdicts():
    path = WS / "out/verdicts.json"
    if not path.exists():
        return "RED", "corrected verdicts missing"
    verdicts = load(path)
    bad = []
    for key in ("S1", "S2"):
        record = verdicts.get(key, {})
        numbers = record.get("numbers", {})
        for field in ("delta_mean", "delta_se"):
            if not finite(numbers.get(field)):
                bad.append(f"{key}.{field} non-finite")
    if verdicts.get("S1", {}).get("status") != "YELLOW":
        bad.append("S1 must be YELLOW/not-met after eligible-arm correction")
    if verdicts.get("S2", {}).get("status") != "YELLOW":
        bad.append("S2 must be YELLOW/not-met")
    if bad:
        return "RED", "; ".join(bad)
    n1 = verdicts["S1"]["numbers"]
    n2 = verdicts["S2"]["numbers"]
    return (
        "GREEN",
        f"S1 finite: {n1['best_arm']} Δ={n1['delta_mean']:.6f}, 2SE={2*n1['delta_se']:.6f}; "
        f"S2 finite: Δ={n2['delta_mean']:.6f}, SE={n2['delta_se']:.6f}",
    )


def gate_original_checker_replay():
    path = WS / "out/original_checker_replay.json"
    if not path.exists():
        return "RED", "read-only original-checker replay missing"
    replay = load(path)
    if replay.get("OVERALL") != "YELLOW":
        return "RED", f"original checker replay changed: {replay.get('OVERALL')}"
    if replay.get("G12_checker_immutable", {}).get("status") != "GREEN":
        return "RED", "original G12 is not GREEN"
    return "YELLOW", "original checker still says YELLOW, but its G09 missed the collector defects repaired here"


def gate_self_sha():
    lock = WS / "CHECKER.sha256"
    if not lock.exists():
        return "RED", "repair checker SHA lock missing"
    want = lock.read_text().split()[0]
    have = sha256(__file__)
    if want != have:
        return "RED", "repair check.py changed after SHA lock"
    return "GREEN", f"repair check.py matches lock ({have[:12]}...)"


GATES = [
    ("R01_reviewed_checker_immutable", gate_source_checker),
    ("R02_reviewed_inputs_frozen", gate_source_inputs),
    ("R03_finite_table_statistics", gate_table_complete),
    ("R04_fold_recomputation", gate_recomputed_from_folds),
    ("R05_arm_F_method_identity", gate_arm_f_identity),
    ("R06_finite_S1_S2_verdicts", gate_verdicts),
    ("R07_original_checker_replay", gate_original_checker_replay),
    ("R08_repair_checker_immutable", gate_self_sha),
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
    (WS / "checker_report.json").write_text(json.dumps(report, indent=2))
    print(f"\nOVERALL: {overall}")
    sys.exit(1 if overall == "RED" else 0)


if __name__ == "__main__":
    main()
