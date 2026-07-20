#!/usr/bin/env python3
"""O3: NUTS calibration of the mount from the synthetic mounted-config modal
survey (D10). Run with the PINNED venv:
    ../../../.venv_nuts/bin/python code/run_nuts_mount.py

Inferred (12 latents): theta_m (6 mount multipliers, LogNormal(0,1.15)),
theta_T (5 tray groups, LogNormal(0,0.25)), sigma_f (HalfNormal(0.05)).
Fixed: theta_S at predecessor posterior median (folded into B_fix; A24),
damping, geometry, condensation topology.

Forward (differentiable, reduced; adapted from the predecessor's run_nuts.py):
    K(theta) = B_fix + sum_j theta_m_j B_mount_j + sum_g theta_T_g B_tray_g
    lam, Q = eigh(K);  f = sqrt(lam)/(2 pi)
Mode tracking: survey modes are paired (pairing_coupled.json) to ANCHOR modes
(reduced model at the best-MAC mount-grid anchor); inside the sampler the
current mode is the eigh column with max |overlap| to the anchor eigenvector,
index taken with stop_gradient (documented non-differentiable handling).

Likelihood: log f_pred ~ Normal(log f_data, sigma_f) over calib-ok pairs.
This script reads ONLY survey_data.npz + pairing_coupled.json + the ROM —
NEVER truth_lock.json (A28 structural self-blinding).

AUTO-REMEDY: if the convergence gate fails (R-hat<=1.05, ESS>=200 over ALL
latents, div<2%), one rerun at 2000+2000 depth 9 (both runs kept, labeled).
Resumable: skips a stage whose output exists.
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

assert jnp.zeros(1).dtype == jnp.float64, "x64 not active"
t0 = time.time()


def log(m):
    print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)


# ------------------------------------------------------------------- inputs
rom = np.load(os.path.join(OUT, "coupled_rom.npz"))
B_fix = jnp.asarray(rom["B_fix"])
B_mount = jnp.asarray(rom["B_mount"])        # (6, nb, nb) incl. k_nom
B_tray = jnp.asarray(rom["B_tray"])          # (5, nb, nb)
nb = int(rom["nb"])

sv = np.load(os.path.join(OUT, "survey_data.npz"))
pairing = json.load(open(os.path.join(OUT, "pairing_coupled.json")))
anchor = pairing["anchor_mult"]
Qa = jnp.asarray(rom[f"anchorQ_x{anchor}"])  # (nb, nb) anchor eigvecs (asc)
calib = [p for p in pairing["pairs"] if p["calib_ok"]]
m_idx = jnp.asarray([p["anchor_mode"] for p in calib])
f_data = jnp.asarray([p["f_data"] for p in calib])
log(f"nb={nb} anchor=x{anchor} n_calib={len(calib)} "
    f"f_data range {float(f_data.min()):.1f}-{float(f_data.max()):.1f} Hz")


def forward(theta_m, theta_T):
    K = (B_fix + jnp.einsum("j,jab->ab", theta_m, B_mount)
         + jnp.einsum("g,gab->ab", theta_T, B_tray))
    lam, Q = jnp.linalg.eigh(K)
    f = jnp.sqrt(jnp.clip(lam, 1e-12, None))/(2*jnp.pi)
    O = jnp.abs(Qa.T @ Q)
    k = jax.lax.stop_gradient(jnp.argmax(O[m_idx, :], axis=1))
    return f[k], k


def model():
    theta_m = numpyro.sample("theta_m", dist.LogNormal(jnp.zeros(6), 1.15))
    theta_T = numpyro.sample("theta_T", dist.LogNormal(jnp.zeros(5), 0.25))
    sigma_f = numpyro.sample("sigma_f", dist.HalfNormal(0.05))
    pf, _ = forward(theta_m, theta_T)
    numpyro.sample("f_obs", dist.Normal(jnp.log(pf), sigma_f),
                   obs=jnp.log(f_data))


def convergence(samples, div, ndraw, chains):
    s = npy_summary(samples, group_by_chain=True)
    rows, worst_rhat, min_ess = {}, 0.0, 1e18
    for name, st in s.items():
        rh = float(np.nanmax(st["r_hat"]))
        es = float(np.nanmin(st["n_eff"]))
        rows[name] = dict(r_hat_max=rh, ess_min=es)
        worst_rhat = max(worst_rhat, rh)
        min_ess = min(min_ess, es)
    dfrac = div/(ndraw*chains)
    return dict(per_variable=rows, worst_rhat=worst_rhat, min_ess=min_ess,
                divergences=div, divergence_fraction=dfrac,
                gate_pass=bool(worst_rhat <= 1.05 and min_ess >= 200
                               and dfrac < 0.02),
                thresholds=dict(rhat=1.05, ess=200, div_frac=0.02))


def run(tag, nwarm, ndraw, mtd, chains=4, seed=0):
    pnz = os.path.join(OUT, f"nuts_mount_{tag}_samples.npz")
    pcv = os.path.join(OUT, f"convergence_mount_{tag}.json")
    if os.path.exists(pnz) and os.path.exists(pcv):
        log(f"{tag}: exists, skip")
        return json.load(open(pcv))
    log(f"{tag}: starting NUTS {chains}x({nwarm}+{ndraw}) depth {mtd}")
    kernel = NUTS(model, target_accept_prob=0.9, dense_mass=True,
                  max_tree_depth=mtd)
    mcmc = MCMC(kernel, num_warmup=nwarm, num_samples=ndraw,
                num_chains=chains, chain_method="sequential",
                progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    div = int(np.sum(np.asarray(mcmc.get_extra_fields()["diverging"])))
    samples = mcmc.get_samples(group_by_chain=True)
    conv = convergence(samples, div, ndraw, chains)
    conv["tag"] = tag
    conv["settings"] = dict(nwarm=nwarm, ndraw=ndraw, max_tree_depth=mtd,
                            chains=chains, dense_mass=True,
                            target_accept=0.9)
    flat = {k: np.asarray(v).reshape(-1, *np.asarray(v).shape[2:])
            for k, v in samples.items()}
    np.savez_compressed(pnz, **flat)
    json.dump(conv, open(pcv, "w"), indent=1)
    log(f"{tag}: worst_rhat {conv['worst_rhat']:.4f} min_ess "
        f"{conv['min_ess']:.0f} div {div} gate_pass {conv['gate_pass']} "
        f"({time.time()-t0:.0f}s)")
    return conv


def posterior_table(tag):
    z = np.load(os.path.join(OUT, f"nuts_mount_{tag}_samples.npz"))
    tm = z["theta_m"]
    tt = z["theta_T"]
    sf = z["sigma_f"]
    names_m = ["k_tx", "k_ty", "k_tz", "k_rx", "k_ry", "k_rz"]
    import models as _m
    return dict(
        mount_mult_median={n: float(np.median(tm[:, j]))
                           for j, n in enumerate(names_m)},
        mount_mult_ci95={n: [float(np.percentile(tm[:, j], 2.5)),
                             float(np.percentile(tm[:, j], 97.5))]
                         for j, n in enumerate(names_m)},
        tray_theta_median={g: float(np.median(tt[:, i]))
                           for i, g in enumerate(_m.TRAY_PARAMS)},
        tray_theta_ci95={g: [float(np.percentile(tt[:, i], 2.5)),
                             float(np.percentile(tt[:, i], 97.5))]
                         for i, g in enumerate(_m.TRAY_PARAMS)},
        sigma_f_median=float(np.median(sf)),
        sigma_f_ci95=[float(np.percentile(sf, 2.5)),
                      float(np.percentile(sf, 97.5))])


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    conv = run("base", nwarm=1000, ndraw=1000, mtd=8)
    final_tag = "base"
    if not conv["gate_pass"]:
        log("gate FAILED on base run -> auto-remedy 2000+2000 depth 9 (D10)")
        conv2 = run("remedy", nwarm=2000, ndraw=2000, mtd=9, seed=1)
        if (conv2["worst_rhat"] < conv["worst_rhat"]):
            final_tag = "remedy"
        conv = conv2 if final_tag == "remedy" else conv
    summ = posterior_table(final_tag)
    summ["final_tag"] = final_tag
    summ["convergence"] = conv
    summ["honesty"] = ("gate_pass=false means YELLOW: intervals NOT "
                       "trustworthy, never report as converged/NUTS-active"
                       if not conv["gate_pass"] else
                       "gate passed (R-hat<=1.05, ESS>=200, div<2% over all "
                       "latents)")
    json.dump(summ, open(os.path.join(OUT, "mount_posterior.json"), "w"),
              indent=1)
    log(f"final tag {final_tag}; posterior summary written")
