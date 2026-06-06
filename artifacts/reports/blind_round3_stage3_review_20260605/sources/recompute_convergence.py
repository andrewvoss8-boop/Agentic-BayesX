#!/usr/bin/env python3
"""Independent recompute of rank-split R-hat + bulk/tail ESS for ALL latents,
both the WITH-discrepancy and WITHOUT-discrepancy posteriors.
Reshape flattened numpyro draws to (chains, draws) chain-major and use ArviZ."""
import numpy as np
import arviz as az
from pathlib import Path

REP = Path("runs/round3/opus48/report")

def recompute(npz, n_chains):
    P = np.load(REP / npz)
    n_total = len(P["log_k_pop"])
    n_draw = n_total // n_chains
    assert n_chains * n_draw == n_total, (n_total, n_chains)
    # vector latents to expand
    scalar = ["log_k_pop", "f_dome", "sigma_build", "sigma_e", "sigma_d"]
    vector = {"d_raw": 6, "d0": 6, "z_b": 6}
    worst_rhat = 0.0; min_bulk = 1e18; min_tail = 1e18; rows = []
    def add(name, flat):
        nonlocal worst_rhat, min_bulk, min_tail
        arr = flat.reshape(n_chains, n_draw)
        # arviz expects (chain, draw)
        r = float(az.rhat(arr, method="rank"))
        eb = float(az.ess(arr, method="bulk"))
        et = float(az.ess(arr, method="tail"))
        rows.append((name, r, eb, et))
        worst_rhat = max(worst_rhat, r); min_bulk = min(min_bulk, eb); min_tail = min(min_tail, et)
    for s in scalar:
        if s in P.files:
            v = P[s]
            # sigma_d may be deterministic 0 in nodisc -> skip degenerate
            if np.allclose(v, v[0]):
                continue
            add(s, v)
    for vn, k in vector.items():
        if vn in P.files:
            M = P[vn]
            for j in range(k):
                col = M[:, j]
                if np.allclose(col, col[0]):
                    continue
                add(f"{vn}[{j}]", col)
    return rows, worst_rhat, min_bulk, min_tail, n_chains, n_draw

for npz, nc, label in [("blind3_posterior.npz", 4, "WITH-discrepancy (sigma_d learned)"),
                       ("blind3_posterior_nodisc.npz", 4, "WITHOUT-discrepancy (per-strut only)")]:
    rows, wr, mb, mt, ncn, nd = recompute(npz, nc)
    print(f"\n===== {label} : {npz}  reshaped ({ncn} chains x {nd} draws) =====")
    print(f"{'latent':14s} {'R-hat':>8s} {'ESSbulk':>9s} {'ESStail':>9s}")
    for name, r, eb, et in rows:
        print(f"{name:14s} {r:8.4f} {eb:9.1f} {et:9.1f}")
    print(f"WORST R-hat {wr:.4f} | min bulk ESS {mb:.1f} | min tail ESS {mt:.1f}")
    gate = (wr < 1.01 and mb >= 400 and mt >= 400)
    print(f"GATE (R-hat<1.01, bulk&tail ESS>=400): {'PASS' if gate else 'FAIL'}")
