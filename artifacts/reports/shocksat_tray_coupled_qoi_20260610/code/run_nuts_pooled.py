#!/usr/bin/env python3
"""POOLED-mount NUTS calibration (D15, Andrew's 6->3 pooling suggestion).

Same synthetic survey data, same frequency-only likelihood and tracking as
run_nuts_mount.py; the ONLY change is the mount parameterization:
  P3 'p3b' : t_all (k_tx=k_ty=k_tz), r_lat (k_rx=k_ry), r_z      (3 params)
  P2 'p2'  : t_all, r_all                                        (2 params)
FIM prediction (out/pooled_fim.json, at the realized 3.7% floor): P2 fully
separable; P3's third direction sits AT the prior precision (marginal).
This run is the sampler confirmation of that prediction.

Honesty: the truth is NOT symmetric (and has off-diagonal coupling), so the
pooled model is deliberately coarser than the truth; sigma_f absorbs the
asymmetry. Pooled 'truth' references are therefore EFFECTIVE values only.
Run with ../../../.venv_nuts/bin/python. Resumable per tag.
"""
import json
import os
import sys
import time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(WS, "out")

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp  # noqa: E402
import numpyro  # noqa: E402
import numpyro.distributions as dist  # noqa: E402
from numpyro.infer import MCMC, NUTS  # noqa: E402
from numpyro.diagnostics import summary as npy_summary  # noqa: E402

assert jnp.zeros(1).dtype == jnp.float64
t0 = time.time()


def log(m):
    print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)


rom = np.load(os.path.join(OUT, "coupled_rom.npz"))
B_fix = jnp.asarray(rom["B_fix"])
B_mount = jnp.asarray(rom["B_mount"])
B_tray = jnp.asarray(rom["B_tray"])
pairing = json.load(open(os.path.join(OUT, "pairing_coupled.json")))
Qa = jnp.asarray(rom[f"anchorQ_x{pairing['anchor_mult']}"])
calib = [p for p in pairing["pairs"] if p["calib_ok"]]
m_idx = jnp.asarray([p["anchor_mode"] for p in calib])
f_data = jnp.asarray([p["f_data"] for p in calib])

NAMES = ["k_tx", "k_ty", "k_tz", "k_rx", "k_ry", "k_rz"]
POOL = {
    "p3b": [["k_tx", "k_ty", "k_tz"], ["k_rx", "k_ry"], ["k_rz"]],
    "p2":  [["k_tx", "k_ty", "k_tz"], ["k_rx", "k_ry", "k_rz"]],
}


def make_B(groups):
    B = np.zeros((6, len(groups)))
    for gi, g in enumerate(groups):
        for nm in g:
            B[NAMES.index(nm), gi] = 1.0
    return jnp.asarray(B)


def run_tag(tag, nwarm=1000, ndraw=1000, mtd=8, chains=4, seed=0):
    pnz = os.path.join(OUT, f"nuts_pooled_{tag}_samples.npz")
    pcv = os.path.join(OUT, f"convergence_pooled_{tag}.json")
    if os.path.exists(pnz) and os.path.exists(pcv):
        log(f"{tag}: exists, skip")
        return json.load(open(pcv))
    Bm = make_B(POOL[tag])
    npool = Bm.shape[1]

    def model():
        th_p = numpyro.sample("theta_pool",
                              dist.LogNormal(jnp.zeros(npool), 1.15))
        th_T = numpyro.sample("theta_T", dist.LogNormal(jnp.zeros(5), 0.25))
        sigma_f = numpyro.sample("sigma_f", dist.HalfNormal(0.05))
        th6 = Bm @ th_p
        K = (B_fix + jnp.einsum("j,jab->ab", th6, B_mount)
             + jnp.einsum("g,gab->ab", th_T, B_tray))
        lam, Q = jnp.linalg.eigh(K)
        f = jnp.sqrt(jnp.clip(lam, 1e-12, None))/(2*jnp.pi)
        O = jnp.abs(Qa.T @ Q)
        k = jax.lax.stop_gradient(jnp.argmax(O[m_idx, :], axis=1))
        numpyro.sample("f_obs", dist.Normal(jnp.log(f[k]), sigma_f),
                       obs=jnp.log(f_data))

    log(f"{tag}: NUTS {chains}x({nwarm}+{ndraw}) depth {mtd}, "
        f"{npool} pooled mount params")
    kernel = NUTS(model, target_accept_prob=0.9, dense_mass=True,
                  max_tree_depth=mtd)
    mcmc = MCMC(kernel, num_warmup=nwarm, num_samples=ndraw,
                num_chains=chains, chain_method="sequential",
                progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    div = int(np.sum(np.asarray(mcmc.get_extra_fields()["diverging"])))
    samples = mcmc.get_samples(group_by_chain=True)
    s = npy_summary(samples, group_by_chain=True)
    rows, worst_rhat, min_ess = {}, 0.0, 1e18
    for name, st in s.items():
        rh = float(np.nanmax(st["r_hat"]))
        es = float(np.nanmin(st["n_eff"]))
        rows[name] = dict(r_hat_max=rh, ess_min=es)
        worst_rhat = max(worst_rhat, rh)
        min_ess = min(min_ess, es)
    conv = dict(tag=tag, per_variable=rows, worst_rhat=worst_rhat,
                min_ess=min_ess, divergences=div,
                divergence_fraction=div/(ndraw*chains),
                gate_pass=bool(worst_rhat <= 1.05 and min_ess >= 200
                               and div/(ndraw*chains) < 0.02),
                settings=dict(nwarm=nwarm, ndraw=ndraw, max_tree_depth=mtd,
                              chains=chains),
                pooling=[" + ".join(g) for g in POOL[tag]])
    flat = {k: np.asarray(v).reshape(-1, *np.asarray(v).shape[2:])
            for k, v in samples.items()}
    np.savez_compressed(pnz, **flat)
    json.dump(conv, open(pcv, "w"), indent=1)
    log(f"{tag}: worst_rhat {worst_rhat:.4f} min_ess {min_ess:.0f} div {div} "
        f"gate_pass {conv['gate_pass']}")
    return conv


if __name__ == "__main__":
    res = {}
    for tag in ("p2", "p3b"):
        res[tag] = run_tag(tag)
    # summary with effective pooled truth references (geometric means of the
    # asymmetric truth multipliers -- EFFECTIVE only; off-diagonals unmodeled)
    lock = json.load(open(os.path.join(OUT, "truth_lock.json")))["payload"]
    mt = np.array(lock["mount_mult_true"])
    gm = lambda idx: float(np.exp(np.mean(np.log(mt[idx]))))
    eff = dict(p2={"t_all": gm([0, 1, 2]), "r_all": gm([3, 4, 5])},
               p3b={"t_all": gm([0, 1, 2]), "r_lat": gm([3, 4]),
                    "r_z": float(mt[5])})
    summ = dict(note="pooled-mount sampler confirmation of out/pooled_fim.json"
                     " (D15); truth refs are EFFECTIVE geometric means of an "
                     "asymmetric truth", convergence=res,
                effective_truth=eff, posterior={})
    for tag in ("p2", "p3b"):
        z = np.load(os.path.join(OUT, f"nuts_pooled_{tag}_samples.npz"))
        tp = z["theta_pool"]
        names = list(eff[tag].keys())
        summ["posterior"][tag] = {
            n: dict(median=round(float(np.median(tp[:, i])), 3),
                    ci95=[round(float(np.percentile(tp[:, i], 2.5)), 3),
                          round(float(np.percentile(tp[:, i], 97.5)), 3)],
                    eff_truth=round(eff[tag][n], 3))
            for i, n in enumerate(names)}
        summ["posterior"][tag]["sigma_f_median"] = round(
            float(np.median(z["sigma_f"])), 4)
    json.dump(summ, open(os.path.join(OUT, "pooled_posterior.json"), "w"),
              indent=1)
    log("pooled_posterior.json written")
