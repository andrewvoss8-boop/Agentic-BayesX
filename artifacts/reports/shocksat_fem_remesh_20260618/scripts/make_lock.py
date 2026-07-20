#!/usr/bin/env python3
"""Lock-before-reveal evidence for the held-out predictions.

The genuine guarantee is structural: held-out modes never entered the
likelihood (run_nuts passes only held_in modes to the model). This script
records that guarantee and hashes the PREDICTION fields (median + CIs) so the
predictions cannot be retro-fitted to the actuals after grading.
"""
import hashlib
import json

lock = {"protocol": "held-out frequencies never enter the likelihood; "
                     "predictions are a function of the held-in posterior only",
        "designs": {}}
for tag in ("band", "band_mac", "lomo", "lomo_mac"):
    try:
        d = json.load(open(f"heldout_{tag}.json"))
    except FileNotFoundError:
        continue
    rows = d.get("held_out_rows") or d.get("rows")
    pred_only = [dict(test_mode=r["test_mode"],
                      f_pred_median=r["f_pred_median"],
                      ci95_param=r["ci95_param"],
                      ci95_pred=r["ci95_pred"]) for r in rows]
    blob = json.dumps(pred_only, sort_keys=True).encode()
    lock["designs"][tag] = dict(
        n=len(rows),
        held_in=d.get("held_in"),
        held_out=d.get("held_out"),
        prediction_sha256=hashlib.sha256(blob).hexdigest())
json.dump(lock, open("heldout_lock.json", "w"), indent=1)
print("wrote heldout_lock.json:",
      {k: v["prediction_sha256"][:12] for k, v in lock["designs"].items()})
