#!/usr/bin/env python3
"""Augment out/variance_decomposition.json with bootstrap 95% CIs on the OAT
variance-ratio main effects (answers 'why does a mount bar exceed 100%?').

The decomposition is an OAT (one-at-a-time) main-effect APPROXIMATION:
  ratio_g = Var_draws[ seed-median QOI | only group g varies ]
            / Var_draws[ seed-median QOI | all groups vary ].
This is NOT a Sobol first-order index (those are <=1 by construction); an OAT
ratio of two Monte-Carlo variance estimates (n_oat=64, n_joint=128) carries
~22% relative error and CAN exceed 1.0 by chance when one group dominates.
The bootstrap CI makes that explicit so a reader sees 1.05 ≈ 1.00.
"""
import json
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(WS, "out")
N_JOINT, N_OAT, NBOOT = 128, 64, 4000


def main():
    z = np.load(os.path.join(OUT, "mc_checkpoint.npz"), allow_pickle=True)
    done = z["done"].item()

    def collect(mode, n, key):
        return np.stack([done[f"{mode}_{i}"][key] for i in range(n)])

    vd = json.load(open(os.path.join(OUT, "variance_decomposition.json")))
    rng = np.random.default_rng(0)
    ci = {}
    for k in ("th_unc", "th_cpl"):
        jmed = np.median(collect("joint", N_JOINT, k), axis=1)   # (Nj,3)
        ci[k] = {}
        for mode in ("mount", "S", "T"):
            omed = np.median(collect(mode, N_OAT, k), axis=1)    # (No,3)
            boot = np.empty((NBOOT, 3))
            for b in range(NBOOT):
                bi = rng.integers(0, N_OAT, N_OAT)
                bj = rng.integers(0, N_JOINT, N_JOINT)
                boot[b] = np.var(omed[bi], axis=0)/np.var(jmed[bj], axis=0)
            lo, hi = np.percentile(boot, [2.5, 97.5], axis=0)
            ci[k][mode] = dict(point=[float(x) for x in np.var(omed, axis=0)
                                      / np.var(jmed, axis=0)],
                               ci95_lo=[float(x) for x in lo],
                               ci95_hi=[float(x) for x in hi])
    vd["bootstrap_ci95"] = ci
    vd["ratio_definition"] = (
        "OAT main-effect ratio = Var(seed-median QOI | only this group varies, "
        "others at nominal/posterior-median) / Var(seed-median QOI | all vary). "
        "NOT a Sobol index; >1 is possible and here is within Monte-Carlo error "
        "(n_oat=64, n_joint=128 -> ~22% rel. error on the ratio). A mount bar "
        "of 1.05 with CI [0.67,1.60] means 'essentially all of the variance', "
        "not literally >100%.")
    json.dump(vd, open(os.path.join(OUT, "variance_decomposition.json"), "w"),
              indent=1)
    print("variance_decomposition.json augmented with bootstrap CIs")
    for ax, a in enumerate("xyz"):
        m = ci["th_cpl"]["mount"]
        print(f"  th_cpl mount F{a}: {m['point'][ax]:.2f} "
              f"[{m['ci95_lo'][ax]:.2f}, {m['ci95_hi'][ax]:.2f}]")


if __name__ == "__main__":
    main()
