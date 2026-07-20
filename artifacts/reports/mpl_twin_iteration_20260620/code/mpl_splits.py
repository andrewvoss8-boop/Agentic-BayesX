#!/usr/bin/env python3
"""Five leave-ONE-accel-location-out splits (D-C). Hold out exactly one of {interface, beam, valve, avi-L, avi-R}
per split; train on the other four. SHIELD is the fixed transmissibility reference and is ALWAYS in training
(it is the denominator of |T|, never held out). Leakage control: a location's taps AND its acoustic record stay
together (they are the same physical placement). The coupled-ruler config is a SEPARATE robustness validation
(D-E), NOT one of these 5 splits. Writes out/splits.json.
"""
from __future__ import annotations
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "out"; OUT.mkdir(exist_ok=True)
HELD = ["interface", "beam", "valve", "avi-L", "avi-R"]
REF = "shield"


def main():
    splits = []
    for h in HELD:
        train = [l for l in HELD if l != h]      # shield is reference, implicitly always present
        splits.append({"split_id": f"LOLO_{h}", "held_out": h, "train": train,
                       "reference_in_training": REF})
    rec = {"deliverable": "5 leave-one-accel-location-out splits",
           "axis": "leave_one_location_out",
           "reference": f"{REF} (fixed transmissibility denominator, always in training)",
           "leakage_controlled": True,
           "leakage_note": "each location's taps + acoustic record stay together; shield never held out.",
           "coupled_ruler": "separate robustness validation (D-E), not one of the 5 LOLO splits",
           "n_splits": len(splits), "splits": splits}
    (OUT / "splits.json").write_text(json.dumps(rec, indent=2))
    print(f"wrote {len(splits)} LOLO splits (ref={REF}):")
    for s in splits:
        print(f"  {s['split_id']:18s} hold-out {s['held_out']:10s} train {s['train']}")


if __name__ == "__main__":
    main()
