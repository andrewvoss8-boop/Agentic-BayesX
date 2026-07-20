#!/usr/bin/env python3
"""Bayesian calibration of the ShockSat modal twin with NUTS (NumPyro).

Inferred variables (theta_g = 9 part-group stiffness scales, dimensionless,
median 1; sigma_f = log-frequency residual sd; optionally sigma_mac):
    K_red(theta) = A_fix + sum_g theta_g A_g      (r x r, mass = I)
    lam, Q = eigh(K_red);  f = sqrt(lam)/(2 pi)
Mode tracking: each calibrated/held-out test mode is tied to a NOMINAL model
mode m (Hungarian pairing in pairing.py). At each theta the current model mode
is the column of Q with max |overlap| to the nominal eigenvector Q1[:,m]; the
index is an integer (stop-gradient) so gradients flow through eigenvalues /
eigenvectors, not through the (piecewise-constant) assignment. (NUTS rule:
this is the documented non-differentiable-pairing handling.)

Likelihood:
  log f_pred,m ~ Normal(log f_meas,m, sigma_f)          [always]
  if use_mac:  MAC_m ~ Normal(1, sigma_mac)             [pseudo-likelihood;
               eigenvector gradients are ill-conditioned for near-degenerate
               pairs -> watch divergences; reported as a sensitivity arm.]

Usage:
  python run_nuts.py band [--mac]      # calibrate <=120 Hz, predict 120-300
  python run_nuts.py lomo [--mac]      # leave-one-mode-out over calib modes
Outputs: nuts_<tag>_samples.npz, convergence_<tag>.json, heldout_<tag>.json
"""
import json
import sys
import time
import numpy as np

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
from numpyro.diagnostics import summary as npy_summary

assert jnp.zeros(1).dtype == jnp.float64, "x64 not active"

t0 = time.time()
def log(m): print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)

# ----------------------------------------------------------------- data
rb = np.load("matrices/reduced_blocks.npz")
gnames = [str(g) for g in rb["gnames"]]
A = jnp.asarray(rb["A"])                     # (9,r,r)
A_fix = jnp.asarray(rb["A_fix"])             # (r,r)
obs_V = jnp.asarray(rb["obs_V"])             # (228,r)
r = A_fix.shape[0]

mm = np.load("measured_modes.npz")
mfreqs = mm["freqs"]
live = jnp.asarray(mm["measured"].reshape(-1).astype(float))   # (228,)
tst_shapes = mm["shapes"].reshape(33, -1)    # (33,228)

pairing = json.load(open("pairing.json"))
pairs = {p["test_mode"]: p for p in pairing["pairs"]}
calib_modes = pairing["calib_test_modes"]

K1 = np.asarray(A_fix) + np.asarray(A).sum(0)
_, Q1np = np.linalg.eigh(K1)
Q1 = jnp.asarray(Q1np)                        # (r,r) nominal modes, ascending
NSIG = 0.25                                   # theta prior sigma (ledger A8)

def targets_for(test_modes):
    m_idx = jnp.asarray([pairs[t]["model_mode"] for t in test_modes])
    f_meas = jnp.asarray([mfreqs[t - 1] for t in test_modes])
    shp = jnp.asarray([tst_shapes[t - 1] for t in test_modes])
    return m_idx, f_meas, shp, np.array(test_modes)

def forward(theta, m_idx):
    K = A_fix + jnp.einsum('g,gij->ij', theta, A)
    lam, Q = jnp.linalg.eigh(K)
    f = jnp.sqrt(jnp.clip(lam, 1e-12, None)) / (2 * jnp.pi)
    O = jnp.abs(Q1.T @ Q)                      # overlap nominal vs current
    k = jax.lax.stop_gradient(jnp.argmax(O[m_idx, :], axis=1))
    return f[k], obs_V @ Q[:, k], k            # (n,), (228,n), (n,)

def model(m_idx, f_meas, shp, use_mac):
    theta = numpyro.sample(
        "theta", dist.LogNormal(jnp.zeros(len(gnames)), NSIG))
    sigma_f = numpyro.sample("sigma_f", dist.HalfNormal(0.05))
    pf, psh, _ = forward(theta, m_idx)
    numpyro.sample("f_obs", dist.Normal(jnp.log(pf), sigma_f),
                   obs=jnp.log(f_meas))
    if use_mac:
        sigma_mac = numpyro.sample("sigma_mac", dist.HalfNormal(0.2))
        a = psh.T * live; b = shp * live
        mac = (jnp.sum(a * b, 1) ** 2) / (jnp.sum(a * a, 1) *
                                          jnp.sum(b * b, 1) + 1e-30)
        numpyro.sample("mac_obs", dist.Normal(mac, sigma_mac),
                       obs=jnp.ones_like(mac))

def run_nuts(test_modes, use_mac, seed=0, nwarm=1000, ndraw=1000, chains=4):
    m_idx, f_meas, shp, _ = targets_for(test_modes)
    # D21: dense_mass + capped tree depth. Measured: trees saturate 1023
    # steps (curved sloppy ridge; 0 divergences) -> depth 8 keeps exact NUTS
    # at 4x cost reduction; convergence gate (R-hat/ESS/div) still decides.
    # D22: env-var overrides for the band remedy rerun (defaults unchanged).
    import os as _os
    nwarm = int(_os.environ.get("NUTS_WARMUP", nwarm))
    ndraw = int(_os.environ.get("NUTS_DRAWS", ndraw))
    mtd = int(_os.environ.get("NUTS_MTD", 8))
    kernel = NUTS(model, target_accept_prob=0.9, dense_mass=True,
                  max_tree_depth=mtd)
    mcmc = MCMC(kernel, num_warmup=nwarm, num_samples=ndraw,
                num_chains=chains, chain_method="sequential",
                progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), m_idx, f_meas, shp, use_mac,
             extra_fields=("diverging",))
    div = int(np.sum(np.asarray(mcmc.get_extra_fields()["diverging"])))
    return mcmc.get_samples(group_by_chain=True), div

def convergence(samples, div, ndraw, chains):
    s = npy_summary(samples, group_by_chain=True)
    rows, worst_rhat, min_ess = {}, 0.0, 1e18
    for name, st in s.items():
        rh = float(np.nanmax(st["r_hat"])); es = float(np.nanmin(st["n_eff"]))
        rows[name] = dict(r_hat_max=rh, ess_min=es)
        worst_rhat = max(worst_rhat, rh); min_ess = min(min_ess, es)
    dfrac = div / (ndraw * chains)
    return dict(per_variable=rows, worst_rhat=worst_rhat, min_ess=min_ess,
                divergences=div, divergence_fraction=dfrac,
                gate_pass=bool(worst_rhat <= 1.05 and min_ess >= 200
                               and dfrac < 0.02),
                thresholds=dict(rhat=1.05, ess=200, div_frac=0.02))

def predict(samples, test_modes):
    th = samples["theta"].reshape(-1, len(gnames))
    sf = samples["sigma_f"].reshape(-1)
    m_idx, f_meas, shp, tnums = targets_for(test_modes)
    fwd = jax.jit(lambda t: forward(t, m_idx))
    S = th.shape[0]; take = np.linspace(0, S - 1, min(S, 2000)).astype(int)
    pf_all, mac_all, kk = [], [], []
    for i in take:
        pf, psh, k = fwd(jnp.asarray(th[i]))
        a = psh.T * live; b = shp * live
        mac = (jnp.sum(a * b, 1) ** 2) / (jnp.sum(a * a, 1) *
                                          jnp.sum(b * b, 1) + 1e-30)
        pf_all.append(np.asarray(pf)); mac_all.append(np.asarray(mac))
        kk.append(np.asarray(k))
    pf_all = np.array(pf_all); mac_all = np.array(mac_all); kk = np.array(kk)
    rng = np.random.default_rng(0)
    pred_noise = pf_all * np.exp(rng.normal(0, np.asarray(sf[take])[:, None]))
    f_meas = np.asarray(f_meas)
    rows = []
    for j, t in enumerate(tnums):
        fm = float(f_meas[j])
        lo, med, hi = np.percentile(pf_all[:, j], [2.5, 50, 97.5])
        plo, phi = np.percentile(pred_noise[:, j], [2.5, 97.5])
        rows.append(dict(
            test_mode=int(t), f_meas=fm, f_pred_median=float(med),
            ci95_param=[float(lo), float(hi)],
            ci95_pred=[float(plo), float(phi)],
            err_pct=float(100 * (med / fm - 1)),
            covers_param=bool(lo <= fm <= hi),
            covers_pred=bool(plo <= fm <= phi),
            mac_median=float(np.median(mac_all[:, j])),
            track_unique=bool(len(np.unique(kk[:, j])) == 1)))
    return rows

def flatten(samples):
    return {k: np.asarray(v).reshape(-1, *np.asarray(v).shape[2:])
            for k, v in samples.items()}

# ===================================================================== main
if __name__ == "__main__":
    design = sys.argv[1] if len(sys.argv) > 1 else "band"
    use_mac = "--mac" in sys.argv
    tag = f"{design}{'_mac' if use_mac else ''}"
    log(f"design={design} use_mac={use_mac} r={r} calib={calib_modes}")

    if design == "band":
        held_in = [t for t in calib_modes if mfreqs[t - 1] <= 120.0]
        held_out = [t for t in calib_modes if mfreqs[t - 1] > 120.0]
        log(f"held_in (<=120Hz): {held_in}")
        log(f"held_out (>120Hz): {held_out}")
        samples, div = run_nuts(held_in, use_mac)
        conv = convergence(samples, div, 1000, 4)
        log(f"convergence: worst_rhat {conv['worst_rhat']:.4f} "
            f"min_ess {conv['min_ess']:.0f} div {div} pass {conv['gate_pass']}")
        flat = flatten(samples)
        ho_rows = predict(samples, held_out)
        hi_rows = predict(samples, held_in)
        np.savez_compressed(f"nuts_{tag}_samples.npz", gnames=np.array(gnames),
                            **flat)
        json.dump(conv, open(f"convergence_{tag}.json", "w"), indent=1)
        json.dump(dict(
            design=design, use_mac=use_mac, held_in=held_in, held_out=held_out,
            held_out_rows=ho_rows, held_in_rows=hi_rows,
            theta_median={g: float(np.median(flat["theta"][:, i]))
                          for i, g in enumerate(gnames)},
            theta_ci={g: [float(np.percentile(flat["theta"][:, i], 2.5)),
                          float(np.percentile(flat["theta"][:, i], 97.5))]
                      for i, g in enumerate(gnames)},
            sigma_f_median=float(np.median(flat["sigma_f"]))),
            open(f"heldout_{tag}.json", "w"), indent=1)
        cov = np.mean([rr["covers_pred"] for rr in ho_rows])
        log(f"held-out predictive coverage = {cov:.2f} "
            f"({sum(rr['covers_pred'] for rr in ho_rows)}/{len(ho_rows)})")

    elif design == "lomo":
        results, worst = [], {"rhat": 0.0, "ess": 1e18, "div": 0}
        for held in calib_modes:
            hi = [t for t in calib_modes if t != held]
            samples, div = run_nuts(hi, use_mac, seed=held)
            conv = convergence(samples, div, 1000, 4)
            row = predict(samples, [held])[0]
            row.update(conv_rhat=conv["worst_rhat"], conv_ess=conv["min_ess"],
                       conv_div=conv["divergences"])
            results.append(row)
            worst["rhat"] = max(worst["rhat"], conv["worst_rhat"])
            worst["ess"] = min(worst["ess"], conv["min_ess"])
            worst["div"] = max(worst["div"], conv["divergences"])
            log(f"LOMO held {held}: pred {row['f_pred_median']:.2f} meas "
                f"{row['f_meas']:.2f} err {row['err_pct']:+.2f}% "
                f"cov_pred {row['covers_pred']} rhat {conv['worst_rhat']:.3f}")
        cov = np.mean([rr["covers_pred"] for rr in results])
        json.dump(dict(
            design="lomo", use_mac=use_mac, rows=results,
            worst_convergence=worst, coverage_pred=float(cov),
            coverage_param=float(np.mean([rr["covers_param"]
                                          for rr in results]))),
            open(f"heldout_{tag}.json", "w"), indent=1)
        log(f"LOMO predictive coverage = {cov:.2f}; worst rhat "
            f"{worst['rhat']:.4f} min ess {worst['ess']:.0f}")
    log("done")
