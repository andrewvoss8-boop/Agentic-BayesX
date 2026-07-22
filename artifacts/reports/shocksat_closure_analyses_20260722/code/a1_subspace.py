#!/usr/bin/env python3
"""A1 — prior-whitened identified-subspace analysis of the stored modal NUTS posterior.

Coordinates: t = log theta (9 part-group stiffness multipliers). Prior t ~ N(0, 0.25^2) iid
(frozen twin ledger A8) => whitening = t/0.25. Eigendecompose Cov(t/0.25) over the 4000 stored
draws. Eigenvalue lambda_k = posterior/prior variance ratio along eigenvector v_k (dimensionless;
<1 = data contracted that combination, ~1 = prior-like).

CI: circular block bootstrap WITHIN each 1000-draw chain segment (ledger N1: block 40 ~ 2x the
worst autocorrelation time implied by stored min ESS 232), 1000 resamples, seed 0.

Known-answer gate (Andrew's read-only calc): contracted ~0.019, 0.029, 0.259, 0.355; five
prior-like 0.872-1.166. Claim scope: SUBSPACE ONLY (per-parameter identifiability is NOT claimed).
Physics naming reuses the frozen joint_strain_energy.json.

Output: out/a1_subspace.json
"""
import json
import os
import time
import numpy as np

t0 = time.time()
WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TW = os.path.join(WS, "..", "shocksat_fem_modal_twin_20260609")

NSIG = 0.25
BLOCK = 40
NBOOT = 1000
SEED = 0
CHAIN_LEN = 1000
ADJ_CONTRACTED = [0.019, 0.029, 0.259, 0.355]
ADJ_PRIORLIKE_RANGE = [0.872, 1.166]

z = np.load(os.path.join(TW, "nuts_full_samples.npz"))
gnames = [str(g) for g in z["gnames"]]
theta = np.asarray(z["theta"], float)                 # (4000, 9) pooled, chain-ordered 4x1000
N, P = theta.shape
assert N == 4000 and P == 9
W = np.log(theta) / NSIG                              # prior-whitened log coordinates


def eigdec(w):
    C = np.cov(w, rowvar=False, ddof=1)
    lam, V = np.linalg.eigh(C)                        # ascending
    return lam, V


lam0, V0 = eigdec(W)

# ---- circular block bootstrap within chains ----
rng = np.random.default_rng(SEED)
nch = N // CHAIN_LEN
nblk_per_chain = int(np.ceil(CHAIN_LEN / BLOCK))
boot_lams = np.empty((NBOOT, P))
for b in range(NBOOT):
    rows = []
    for c in range(nch):
        starts = rng.integers(0, CHAIN_LEN, nblk_per_chain)
        idx = (starts[:, None] + np.arange(BLOCK)[None, :]) % CHAIN_LEN
        rows.append(c * CHAIN_LEN + idx.reshape(-1)[:CHAIN_LEN])
    boot_lams[b] = eigdec(W[np.concatenate(rows)])[0]
ci = np.percentile(boot_lams, [2.5, 97.5], axis=0)    # (2, 9), ascending eigenvalue order

# ---- known-answer gate ----
within = []
for k, adj in enumerate(ADJ_CONTRACTED):              # 4 smallest, ascending
    within.append(bool(ci[0, k] <= adj <= ci[1, k]))
for k in range(4, P):                                 # five prior-like: CI overlaps adjudicated range
    within.append(bool(ci[1, k] >= ADJ_PRIORLIKE_RANGE[0] and ci[0, k] <= ADJ_PRIORLIKE_RANGE[1]))
gate_pass = all(within)

# ---- physical naming of the strong (contracted) directions ----
se = json.load(open(os.path.join(TW, "joint_strain_energy.json")))["group_summary"]
directions = []
for k in range(P):
    v = V0[:, k]
    comp = sorted(zip(gnames, v), key=lambda t: -abs(t[1]))
    top = [(g, round(float(c), 3)) for g, c in comp if abs(c) >= 0.25][:4]
    directions.append({
        "rank_ascending": k,
        "eigenvalue_post_over_prior_var": round(float(lam0[k]), 4),
        "ci95": [round(float(ci[0, k]), 4), round(float(ci[1, k]), 4)],
        "top_components_logtheta": top,
        "all_components": {g: round(float(c), 4) for g, c in zip(gnames, V0[:, k])},
        "strain_energy_mean_pct_of_top_groups": {
            g: round(se[g]["mean_se_pct"], 2) for g, _ in top if g in se},
    })

# plain-English names for the contracted directions
def name_dir(d):
    gs = [g for g, c in d["top_components_logtheta"]]
    return " + ".join(gs[:3]) + (" mix" if len(gs) > 1 else " (nearly pure)")


out = {
    "source_run": "shocksat_fem_modal_twin_20260609/nuts_full_samples.npz (4000 pooled NUTS draws, "
                  "converged full-calibration run: worst R-hat 1.022, min ESS 232)",
    "coordinates": "log theta, whitened by prior sd 0.25 (prior cov = 0.25^2 I)",
    "claim_scope": "subspace_only",
    "eigenvalues_ascending": [round(float(x), 4) for x in lam0],
    "eigenvalues_ci95": [[round(float(ci[0, k]), 4), round(float(ci[1, k]), 4)] for k in range(P)],
    "n_contracted_below_half": int(np.sum(lam0 < 0.5)),
    "bootstrap": {"method": "circular block bootstrap within 1000-draw chain segments",
                  "block_len": BLOCK, "n_boot": NBOOT, "seed": SEED,
                  "rationale": "min ESS 232 => tau_hat ~ 17 draws; block 40 ~ 2x tau_hat"},
    "known_answer_gate": {
        "adjudicated_contracted": ADJ_CONTRACTED,
        "adjudicated_priorlike_range": ADJ_PRIORLIKE_RANGE,
        "within_ci": within, "pass": bool(gate_pass)},
    "directions": directions,
    "contracted_direction_names": [name_dir(directions[k]) for k in range(4)],
    "interpretation_note": (
        "The 18 modal frequencies pin down 4 stiffness COMBINATIONS (posterior/prior variance "
        "0.02-0.36), not 9 individual parameters; the remaining 5 directions return the prior. "
        "Physics tie-in via frozen joint_strain_energy.json (subspace-level claim only)."),
    "runtime_s": round(time.time() - t0, 1),
}
json.dump(out, open(os.path.join(WS, "out", "a1_subspace.json"), "w"), indent=1)
print(f"eigenvalues (asc): {[round(float(x),3) for x in lam0]}")
print(f"known-answer gate: {'PASS' if gate_pass else 'FAIL'} within_ci={within}")
print(f"contracted directions: {[name_dir(directions[k]) for k in range(4)]}")
print(f"runtime {out['runtime_s']}s")
