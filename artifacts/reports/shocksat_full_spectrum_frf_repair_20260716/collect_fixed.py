#!/usr/bin/env python3
"""Collect corrected exact arm statistics without writing the reviewed study."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import numpy as np


WS = Path(__file__).resolve().parent
ROOT = WS.parents[2]
SOURCE = ROOT / "artifacts/reports/shocksat_full_spectrum_frf_20260714"
OUT = WS / "out"
DEV = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]


def load(path):
    with Path(path).open() as f:
        return json.load(f)


def json_finite(value):
    if isinstance(value, dict):
        return {key: json_finite(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_finite(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def fold_values(exact, arm, band):
    return np.array(
        [exact[arm]["exact"]["folds"][fold][band]["P1p"] for fold in DEV],
        dtype=float,
    )


def paired(exact, arm, reference, band="sub200"):
    delta = fold_values(exact, arm, band) - fold_values(exact, reference, band)
    return {
        "delta_mean": float(delta.mean()),
        "delta_se": float(delta.std(ddof=1) / np.sqrt(delta.size)),
        "per_fold": delta.tolist(),
    }


def replay_original_checker():
    spec = importlib.util.spec_from_file_location("original_checker", SOURCE / "check.py")
    checker = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(checker)
    report = {}
    overall = "GREEN"
    for name, gate in checker.GATES:
        try:
            status, detail = gate()
        except Exception as exc:
            status, detail = "RED", f"gate crashed: {type(exc).__name__}: {exc}"
        report[name] = {"status": status, "detail": detail}
        if checker.RANK[status] > checker.RANK[overall]:
            overall = status
    report["OVERALL"] = overall
    report["note"] = "Gate functions imported directly to keep the reviewed workspace read-only."
    return report


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    exact = load(SOURCE / "out/exact_freeze_scores.json")
    table = {
        "basis": "EXACT enriched-at-theta_MAP scores from the reviewed study",
        "source": "../shocksat_full_spectrum_frf_20260714/out/exact_freeze_scores.json",
        "arms": {},
        "arm_F_rule": {
            "source": "pre_registered_sequential_B_then_C_then_D",
            "screening_sequence": {
                "A1": exact["A1"]["screen"]["sub200"],
                "B": exact["B"]["screen"]["sub200"],
                "C": exact["C"]["screen"]["sub200"],
                "D": exact["D"]["screen"]["sub200"],
            },
            "decision": "B does not beat A1; C beats A1; D does not beat C; therefore F=C",
        },
    }
    for arm in ("A0", "A1", "B", "C", "D", "R"):
        row = {}
        for band in ("sub200", "b200_500"):
            values = fold_values(exact, arm, band)
            row[band] = {
                "mean": float(values.mean()),
                "se": float(values.std(ddof=1) / np.sqrt(values.size)),
                "folds": dict(zip(DEV, values.tolist())),
                "screening": exact[arm]["screen"][band],
            }
        row["b500_ceiling"] = {
            "status": "not_certified",
            "reason": "reviewed FEM basis credible to 639 Hz; 1.25x margin caps scoring at 500 Hz",
        }
        if arm == "C":
            row["caveat"] = exact["C"]["caveat"]
        table["arms"][arm] = row
    table["arms"]["F"] = json.loads(json.dumps(table["arms"]["C"]))
    table["arms"]["F"]["equals"] = "C"
    table["arms"]["F"]["method_note"] = (
        "Corrected identity from the pre-registered sequential arm-F rule; no separate F exact solve exists."
    )

    eligible = ("B", "C", "D", "F")
    comparisons = {
        arm: paired(exact, "C" if arm == "F" else arm, "A1") for arm in eligible
    }
    best = max(eligible, key=lambda arm: comparisons[arm]["delta_mean"])
    s1 = comparisons[best]
    s1_pass = s1["delta_mean"] >= 0.05 and s1["delta_mean"] >= 2 * s1["delta_se"]
    s2 = paired(exact, "D", "R")
    s2_pass = s2["delta_mean"] >= s2["delta_se"]

    original_verdicts = load(SOURCE / "out/verdicts.json")
    verdicts = {
        "S1": {
            "status": "GREEN" if s1_pass else "YELLOW",
            "claim": "eligible B/C/D/F arm beats A1 by >=+0.05 and >=2x paired-fold SE",
            "numbers": {"best_arm": best, **s1, "two_se": 2 * s1["delta_se"]},
            "note": "F is C under the pre-registered rule; random control R is not eligible as F.",
        },
        "S2": {
            "status": "GREEN" if s2_pass else "YELLOW",
            "claim": "agent D beats random R by >=1x paired-fold SE",
            "numbers": s2,
        },
    }
    for key in ("S3", "S4", "S5"):
        verdicts[key] = json_finite(original_verdicts[key])
    verdicts["H1"] = {
        "status": verdicts["S1"]["status"],
        "anchor": "S1",
        "summary": original_verdicts["H1"]["summary"],
    }
    verdicts["H2"] = {
        "status": verdicts["S2"]["status"],
        "anchor": "S2",
        "summary": (
            "Agent D does not beat equal-budget random R on the two exact-rescored screening winners; "
            "breadth remains limited by exact reranking and the agent's zero genuine model-form proposals."
        ),
    }
    for key in ("H3", "H4", "H5"):
        verdicts[key] = original_verdicts[key]

    replay = replay_original_checker()
    (OUT / "arms_bands_table.json").write_text(
        json.dumps(table, indent=2, allow_nan=False)
    )
    (OUT / "verdicts.json").write_text(json.dumps(verdicts, indent=2, allow_nan=False))
    (OUT / "original_checker_replay.json").write_text(json.dumps(replay, indent=2))
    summary = {
        "S1": verdicts["S1"],
        "S2": verdicts["S2"],
        "original_checker_overall": replay["OVERALL"],
        "original_defects_repaired": [
            "nested exact-fold path",
            "null exact fold standard errors",
            "non-finite S1/S2 statistics",
            "post-hoc F=R identity",
        ],
        "remaining_limitations": [
            "arm-C exact row uses fold-1 shape MAP for all folds",
            "only the screening-winning D and R candidates were exact-rescored",
            "original checker G09 remains immutable and incomplete",
        ],
    }
    (OUT / "repair_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps({"S1": verdicts["S1"], "S2": verdicts["S2"]}, indent=2))


if __name__ == "__main__":
    main()
