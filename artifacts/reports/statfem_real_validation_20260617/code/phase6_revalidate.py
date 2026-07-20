#!/usr/bin/env python3
"""Card C Phase 6 -- re-validate the twin on Card D's REFINED-mesh FEM (BLOCKED until Card D delivers).

When Card D (artifacts/reports/shocksat_fem_remesh_20260618) delivers a refined-mesh reduced model in the same
format the validation study consumes (A, A_fix stiffness blocks + the node->reduced-row mapping that realfrf.
load_reduced builds), this harness re-runs the WORKING twin on it and reports the held-out-QOI improvement at the
hard channels:
  1. L5 (heldout_qoi.run)            -> peak/band QOI on the refined mesh
  2. hardened Beck (mc_beck_full)    -> 25-split MC on the refined mesh
  3. delta vs the coarse-mesh baseline at the 7 hard channels (4,27,40,52,69,92,98)

As of this run Card D has produced only region_diagnosis.json (no refined reduced model), so Phase 6 is BLOCKED.
This script detects the deliverable and either runs the re-validation or records the blocked status -- no fabricated
numbers. Output: out/phase6_status.json.
"""
import json
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent.parent
CARD_D = WS.parent / "shocksat_fem_remesh_20260618"
# expected refined-model artifact names (any one present => deliverable ready)
CANDIDATES = ["out/refined_reduced.npz", "out/reduced_blocks_refined.npz", "out/refined_fem_reduced.npz",
              "out/refined_model.npz"]


def deliverable_path():
    for c in CANDIDATES:
        p = CARD_D / c
        if p.exists():
            return p
    return None


def run():
    p = deliverable_path()
    status = {"deliverable": "Phase6_revalidate_on_refined_mesh", "card_d_workspace": str(CARD_D),
              "checked_for": [str(CARD_D / c) for c in CANDIDATES]}
    if p is None:
        status["status"] = "BLOCKED"
        status["reason"] = ("Card D has not yet delivered a refined-mesh reduced FEM (only region_diagnosis.json "
                            "present). Re-validation harness is ready; re-run this script when the refined reduced "
                            "model lands. No numbers fabricated.")
        status["protocol_when_unblocked"] = [
            "point realfrf.load_reduced at the refined reduced model (same A/A_fix/row-map format)",
            "python code/heldout_qoi.py --force  -> out/heldout_qoi_L5.json (refined)",
            "python code/mc_beck_full.py 25      -> out/mc_beck_full_summary.json (refined)",
            "compare held-out peak/band IS at hard channels {4,27,40,52,69,92,98} vs the coarse-mesh baseline",
            "GREEN only if the refined mesh measurably lowers held-out IS at the hard channels (before/after table)"]
        print("PHASE 6: BLOCKED -- Card D refined-mesh FEM not yet delivered. Harness ready; status recorded.")
    else:
        status["status"] = "READY"
        status["found"] = str(p)
        status["note"] = "Refined model found. Re-run heldout_qoi + mc_beck_full pointed at it (manual wiring step)."
        print(f"PHASE 6: refined model found at {p}. Wire realfrf.load_reduced to it and re-run the twin.")
    (WS / "out").mkdir(exist_ok=True)
    (WS / "out" / "phase6_status.json").write_text(json.dumps(status, indent=2))
    return status


if __name__ == "__main__":
    run()
