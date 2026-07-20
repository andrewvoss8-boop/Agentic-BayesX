#!/usr/bin/env python3
"""A0 baseline (arm) + uncalibrated reference bar, under the LOCKED protocol (card §4.2: A0 FIRST;
all S1 thresholds are relative to A0's dev P1). Also runs the round-0 train-side diagnosis for the loop.

Tracks logged: 'baseline' (A0, θ_MAP) and 'reference' (inherited θ=1). Neither counts against the
agent/random budgets (checker counts only those two tracks).
"""
import json, os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F
import score as SC
import diag as DG

if __name__ == "__main__":
    done = set()
    if os.path.exists(SC.QLOG):
        done = set((json.loads(x)["cid"], json.loads(x)["track"]) for x in open(SC.QLOG) if x.strip())
    if ("A0", "baseline") not in done:
        rec = SC.score_candidate("A0", "baseline", rationale="inherited FEM, 9-group θ_MAP (S0 form, D6)",
                                 family="baseline", enforce_budget=False)
        print(json.dumps({k: rec[k] for k in ("cid", "P1_mean", "P1_folds", "P1_se", "P2_mean_dB",
                                              "n_matched_peaks_min")}, indent=1))
    if ("A0", "reference") not in done:
        pkg = F.Package.load("A0")
        rec = SC.score_candidate("A0", "reference", rationale="inherited FEM UNCALIBRATED (θ=1)",
                                 family="reference", enforce_budget=False,
                                 theta_override=np.ones(len(pkg.free_names)))
        print(json.dumps({k: rec[k] for k in ("cid", "P1_mean", "P1_folds", "P2_mean_dB")}, indent=1))
    if not os.path.exists(os.path.join(F.WS, "out", "diagnosis_r0.json")):
        DG.build_diagnosis("A0", 0)
