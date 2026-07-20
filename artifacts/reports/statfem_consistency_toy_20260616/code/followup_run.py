#!/usr/bin/env python3
"""Run follow-up E1 (localized-defect error class) for the three constructions over a defect-depth sweep,
at the finest discretization and n=8, and write followup/defect_summary.json. Resumable per cell."""
from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WS = HERE.parent
OUT = WS / "followup"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))

import jax  # noqa: E402
import core  # noqa: E402
import nuts_marg as nm  # noqa: E402
import statfem as sf  # noqa: E402
import followup as fu  # noqa: E402

DEPTHS = [0.0, 0.15, 0.30, 0.50]
N_REP = 8
N_C = 64
N_EL = 64
SIGMA_R = 0.05
NWARM = NSAMP = 1000


def conv(d):
    return bool(d["max_rhat"] <= 1.05 and d["min_ess"] >= 200 and d["div_frac"] < 0.02)


def th(flat):
    t = flat["theta"]
    return {"mean": float(np.mean(t)), "sd": float(np.std(t)),
            "lo": float(np.percentile(t, 2.5)), "hi": float(np.percentile(t, 97.5))}


def run_cell(construction, depth):
    data = fu.make_data_defect(depth, n_rep=N_REP)
    rec = {"construction": construction, "depth": float(depth)}
    t0 = time.time()
    if construction == "M-lik":
        pc = core.lik_precompute_fd(N_C)
        flat, diag, _ = nm.run(pc, data, "M-lik", sigma_r=SIGMA_R, num_warmup=NWARM, num_samples=NSAMP)
        hc = nm.heldout_coverage(pc, data, flat, "M-lik", sigma_r=SIGMA_R)
    elif construction == "M-ift":
        pc = core.lik_precompute_fd(N_C)
        flat, diag, _ = nm.run(pc, data, "M-ift", num_warmup=NWARM, num_samples=NSAMP)
        hc = nm.heldout_coverage(pc, data, flat, "M-ift")
        rec["beta"] = nm.mift_beta_posterior(pc, data, flat)
    else:
        fp = sf.fe_precompute(N_EL)
        flat, diag, _ = sf.run(fp, data, num_warmup=NWARM, num_samples=NSAMP)
        hc = sf.heldout_coverage(fp, data, flat)
        rec["sigma_d"] = {"med": float(np.median(flat["sigma_d"])),
                          "lo": float(np.percentile(flat["sigma_d"], 2.5)),
                          "hi": float(np.percentile(flat["sigma_d"], 97.5))}
    rec["nuts"] = diag
    rec["converged"] = conv(diag)
    rec["runtime_s"] = round(time.time() - t0, 2)
    rec["theta"] = th(flat)
    rec["coverage_heldout"] = hc["frac"]
    return rec


def main():
    cells = {}
    p_all = OUT / "defect_summary.json"
    for construction in ("M-lik", "M-statfem", "M-ift"):
        cells[construction] = []
        for depth in DEPTHS:
            cp = OUT / f"cell_{construction.replace('-','')}_d{depth:.2f}.json"
            if cp.exists():
                rec = json.load(open(cp))
            else:
                print(f"[run ] {construction} depth={depth} ...", flush=True)
                rec = run_cell(construction, depth)
                json.dump(rec, open(cp, "w"), indent=1)
                print(f"       theta {rec['theta']['mean']:.4f} rhat {rec['nuts']['max_rhat']:.3f} "
                      f"conv {rec['converged']} cov {rec['coverage_heldout']:.2f} "
                      f"{'sigd '+format(rec.get('sigma_d',{}).get('med',0),'.4f') if 'sigma_d' in rec else ''} "
                      f"{rec['runtime_s']:.0f}s", flush=True)
            cells[construction].append(rec)
            jax.clear_caches(); gc.collect()
    summary = {"theta_true": core.THETA_TRUE, "depths": DEPTHS, "defect_region": [fu.DEFECT_A, fu.DEFECT_B],
               "ref_nel": fu.REF_NEL, "cells": cells}
    json.dump(summary, open(p_all, "w"), indent=1)
    print(f"wrote {p_all}")


if __name__ == "__main__":
    main()
