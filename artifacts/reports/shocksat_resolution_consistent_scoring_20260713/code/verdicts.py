#!/usr/bin/env python3
"""Pre-registered verdicts S1/S2/S3 (question_framing.md §Success criteria) from score_log + gate_W.
S1: dev P1'(B2)-P1'(B0) >= +0.03 AND >= 2x fold-SE of the PAIRED per-fold difference AND vault B2 > B0.
S2: decomposition window-alone (B3-B0), damping-alone (B1-B0), interaction (B2-B1-B3+B0).
S3: dev P1'(B2) >= P1'(B1) + 0.02 AND Gate W passed (direct or labeled)."""
import json, os, sys
import numpy as np

MY = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(MY, ".."))
OUT = os.path.join(WS, "out")

dev, vault = {}, {}
for line in open(os.path.join(OUT, "score_log.jsonl")):
    if line.strip():
        r = json.loads(line)
        (vault if r["stage"] == "vault" else dev)[r["arm"]] = r

gw = json.load(open(os.path.join(OUT, "gate_W.json")))
gate_w_pass = gw["pass_mode"] in ("direct", "labeled")

fold_keys = list(dev["B0"]["P1p_folds"])
d_folds = np.array([dev["B2"]["P1p_folds"][k] - dev["B0"]["P1p_folds"][k] for k in fold_keys])
delta = float(np.mean(d_folds))
se = float(d_folds.std(ddof=1) / np.sqrt(len(d_folds)))
s1 = {"delta_dev_P1p": delta, "per_fold_delta": {k: round(float(v), 4) for k, v in zip(fold_keys, d_folds)},
      "fold_se_delta": se, "threshold_abs": 0.03,
      "vault_B2": vault["B2"]["P1p_mean"], "vault_B0": vault["B0"]["P1p_mean"],
      "vault_B2_gt_B0": bool(vault["B2"]["P1p_mean"] > vault["B0"]["P1p_mean"])}
s1["pass"] = bool(delta >= 0.03 and delta >= 2 * se and s1["vault_B2_gt_B0"])

wa = dev["B3"]["P1p_mean"] - dev["B0"]["P1p_mean"]
da = dev["B1"]["P1p_mean"] - dev["B0"]["P1p_mean"]
inter = dev["B2"]["P1p_mean"] - dev["B1"]["P1p_mean"] - dev["B3"]["P1p_mean"] + dev["B0"]["P1p_mean"]
tot = dev["B2"]["P1p_mean"] - dev["B0"]["P1p_mean"]
s2 = {"window_alone": wa, "damping_alone": da, "interaction": inter, "total": tot,
      "damping_plus_interaction_ge_half_total": bool((da + inter) >= 0.5 * tot) if tot > 0 else None,
      "note": "attribution requirement applies only when S1 passes; window-alone dominating = "
              "'it's the window, damping still moot' (reported honestly)"}

d31 = dev["B2"]["P1p_mean"] - dev["B1"]["P1p_mean"]
s3 = {"B2_minus_B1_dev_P1p": d31, "threshold": 0.02, "gate_W_pass": gate_w_pass,
      "gate_W_mode": gw["pass_mode"], "pass": bool(d31 >= 0.02 and gate_w_pass)}

table = {a: {"dev_P1p": dev[a]["P1p_mean"], "dev_P1p_se": dev[a]["P1p_se"],
             "dev_P2p": dev[a]["P2p_mean"], "dev_P3": dev[a]["P3_mean"], "dev_P4_dB": dev[a]["P4_mean"],
             "vault_P1p": vault[a]["P1p_mean"], "vault_P2p": vault[a]["P2p_mean"],
             "vault_P4_dB": vault[a]["P4_mean"]} for a in ("B0", "B1", "B2", "B3", "B4", "B5")}
verdicts = {"S1": s1, "S2": s2, "S3": s3, "arms": table,
            "headline": ("S1 PASS: resolution-consistency wins" if s1["pass"] else
                         ("S1 FAIL (pre-registered claim falsified) but S3 PASS: mechanism confirmed, no "
                          "held-out advantage over the 1% convention" if s3["pass"] else
                          "S1 and S3 FAIL: claim falsified and mechanism not confirmed at threshold"))}
json.dump(verdicts, open(os.path.join(OUT, "verdicts.json"), "w"), indent=1)
print(json.dumps(verdicts, indent=1)[:2500])
