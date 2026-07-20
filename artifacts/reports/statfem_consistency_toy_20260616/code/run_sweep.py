#!/usr/bin/env python3
"""The consistency experiment: fit the SAME synthetic drive-point-FRF data with the three constructions
and refine the knobs. Resumable (skips finished cells) and CHUNKED (run one --only group per process so
jax compilation memory is freed between groups; see decisions_log D16).

Chunks (--only): mlik_sr | mlik_nc | mift_nc | statfem_h | concentration | all
Each cell records: all-variable NUTS diagnostics + converged flag; posterior theta (mean/sd/95% CI);
held-out drive-point-FRF 95% coverage; and the construction's model-error knob (sigma_r / beta / sigma_d).
Float64; BLAS threads pinned by run_all.sh.
"""
from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WS = HERE.parent
OUT = WS / "out"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))

import jax  # noqa: E402
import core  # noqa: E402
import nuts_marg as nm  # noqa: E402
import statfem as sf  # noqa: E402

NWARM, NSAMP, NCHAIN = 1000, 1000, 4
EPS_LEVELS = [0.0, 0.3]
N_FIX = 8                 # fixed replicate count for the knob sweeps
N_C_FIX = 64             # fixed FD resolution for M-lik sigma_r sweep + concentration
N_EL_FIX = 64           # fixed FE mesh for concentration
SIGMA_R_FIX = 0.05      # fixed residual noise for M-lik N_c sweep + concentration
SR_LEVELS = [0.005, 0.02, 0.05, 0.2, 0.5]
NC_LEVELS = [8, 16, 32, 64, 128]
NEL_LEVELS = [8, 16, 32, 64, 128]
N_LEVELS = [1, 4, 16, 64]


def theta_summ(flat):
    th = flat["theta"]
    return {"mean": float(np.mean(th)), "sd": float(np.std(th)),
            "lo": float(np.percentile(th, 2.5)), "med": float(np.median(th)),
            "hi": float(np.percentile(th, 97.5))}


def conv(d):
    return bool(d["max_rhat"] <= 1.05 and d["min_ess"] >= 200 and d["div_frac"] < 0.02)


def cell_path(construction, knob, level, eps, n):
    cn = construction.replace("-", "")
    lv = f"{level:.4g}"
    return OUT / f"cell_{cn}_{knob}_{lv}_eps{eps}_n{n}.json"


def run_cell(construction, knob, level, eps, n, N_c=N_C_FIX, n_el=N_EL_FIX, sigma_r=SIGMA_R_FIX,
             seed=20260616):
    data = core.make_data(eps, n_rep=n, seed=seed)
    rec = {"construction": construction, "knob": knob, "level": float(level), "eps": float(eps),
           "n": int(n), "N_c": int(N_c), "n_el": int(n_el)}
    t0 = time.time()
    if construction == "M-lik":
        pc = core.lik_precompute_fd(N_c)
        flat, diag, rt = nm.run(pc, data, "M-lik", sigma_r=sigma_r,
                                num_warmup=NWARM, num_samples=NSAMP, num_chains=NCHAIN)
        hc = nm.heldout_coverage(pc, data, flat, "M-lik", sigma_r=sigma_r)
        rec["sigma_r"] = float(sigma_r)
    elif construction == "M-ift":
        pc = core.lik_precompute_fd(N_c)
        flat, diag, rt = nm.run(pc, data, "M-ift",
                                num_warmup=NWARM, num_samples=NSAMP, num_chains=NCHAIN)
        hc = nm.heldout_coverage(pc, data, flat, "M-ift")
        rec["beta"] = nm.mift_beta_posterior(pc, data, flat)
    elif construction == "M-statfem":
        fp = sf.fe_precompute(n_el)
        flat, diag, rt = sf.run(fp, data, num_warmup=NWARM, num_samples=NSAMP, num_chains=NCHAIN)
        hc = sf.heldout_coverage(fp, data, flat)
        rec["sigma_d_med"] = float(np.median(flat["sigma_d"]))
    else:
        raise ValueError(construction)
    rec["nuts"] = diag
    rec["converged"] = conv(diag)
    rec["runtime_s"] = round(time.time() - t0, 2)
    rec["theta"] = theta_summ(flat)
    rec["coverage_heldout"] = hc["frac"]
    rec["coverage_detail"] = {"covered": hc["covered"], "n": hc["n"], "held_freqs": hc["held_freqs"]}
    return rec


def jobs_for(only):
    J = []
    if only in ("mlik_sr", "all"):
        for eps in EPS_LEVELS:
            for sr in SR_LEVELS:
                J.append(dict(construction="M-lik", knob="sigma_r", level=sr, eps=eps, n=N_FIX,
                              N_c=N_C_FIX, sigma_r=sr))
    if only in ("mlik_nc", "all"):
        for eps in EPS_LEVELS:
            for N in NC_LEVELS:
                J.append(dict(construction="M-lik", knob="N_c", level=N, eps=eps, n=N_FIX,
                              N_c=N, sigma_r=SIGMA_R_FIX))
    if only in ("mift_nc", "all"):
        for eps in EPS_LEVELS:
            for N in NC_LEVELS:
                J.append(dict(construction="M-ift", knob="N_c", level=N, eps=eps, n=N_FIX, N_c=N))
    if only in ("statfem_h", "all"):
        for eps in EPS_LEVELS:
            for ne in NEL_LEVELS:
                J.append(dict(construction="M-statfem", knob="h", level=ne, eps=eps, n=N_FIX, n_el=ne))
    if only in ("concentration", "all"):
        for eps in EPS_LEVELS:
            for n in N_LEVELS:
                J.append(dict(construction="M-lik", knob="n", level=n, eps=eps, n=n,
                              N_c=N_C_FIX, sigma_r=SIGMA_R_FIX))
                J.append(dict(construction="M-ift", knob="n", level=n, eps=eps, n=n, N_c=N_C_FIX))
                J.append(dict(construction="M-statfem", knob="n", level=n, eps=eps, n=n, n_el=N_EL_FIX))
    return J


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="all")
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    global NWARM, NSAMP
    if args.smoke:
        NWARM, NSAMP = 150, 150
    t_all = time.time()
    for kw in jobs_for(args.only):
        p = cell_path(kw["construction"], kw["knob"], kw["level"], kw["eps"], kw["n"])
        if p.exists():
            print(f"[skip] {p.name}", flush=True)
            continue
        print(f"[run ] {p.name} ...", flush=True)
        try:
            rec = run_cell(**kw)
            json.dump(rec, open(p, "w"), indent=1)
            print(f"       theta {rec['theta']['mean']:.4f} rhat {rec['nuts']['max_rhat']:.3f} "
                  f"ess {rec['nuts']['min_ess']:.0f} conv {rec['converged']} cov {rec['coverage_heldout']:.2f} "
                  f"{rec['runtime_s']:.0f}s", flush=True)
        except Exception as e:  # keep going; partial results are resumable
            print(f"       FAILED {p.name}: {e}", flush=True)
        jax.clear_caches()
        gc.collect()
    print(f"chunk '{args.only}' done in {time.time()-t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
