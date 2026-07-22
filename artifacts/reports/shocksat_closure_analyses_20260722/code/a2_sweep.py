#!/usr/bin/env python3
"""A2 — sigma_f prior-sensitivity sweep on the frozen modal-frequency NUTS model.

Reuses the FROZEN twin module (shocksat_fem_modal_twin_20260609/scripts/run_nuts.py) read-only:
same reduced model, pairing, stop-gradient mode tracking, NUTS settings (warmup/draws 1000, 4 chains,
target_accept 0.9, dense mass, max_tree_depth 8). The likelihood is exactly the frozen one (18 paired
log-frequencies, no MAC); only the sigma_f PRIOR varies:
  hn002 HalfNormal(0.02) · hn005 HalfNormal(0.05) [REFERENCE, seed 42 = must reproduce stored
  posterior] · hn015 HalfNormal(0.15) · hc005 HalfCauchy(0.05) · exp005 Exponential(mean 0.05).
Per-chain draws retained (out/a2_draws/<name>.npz, arrays (4,1000,...)) — the stored pooled draws'
omission is not repeated. Resumable: finished variants are skipped on relaunch.

Also: prior predictive check per variant (do prior draws' predicted frequencies contain the measured
18?) and posterior predictive PIT for the reference. Output: out/a2_sigma_f_sweep.json
"""
import json
import os
import sys
import time
import numpy as np

t0 = time.time()
WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
TW = os.path.abspath(os.path.join(WS, "..", "shocksat_fem_modal_twin_20260609"))
DRAWS_DIR = os.path.join(WS, "out", "a2_draws")
os.makedirs(DRAWS_DIR, exist_ok=True)

_cwd = os.getcwd()
os.chdir(TW)                    # frozen module loads its data via relative paths (read-only)
sys.path.insert(0, os.path.join(TW, "scripts"))
import run_nuts as RN           # noqa: E402
os.chdir(_cwd)

import jax                      # noqa: E402
import jax.numpy as jnp         # noqa: E402
import numpyro                  # noqa: E402
import numpyro.distributions as dist  # noqa: E402
from numpyro.infer import MCMC, NUTS  # noqa: E402
from scipy.stats import norm    # noqa: E402

CALIB = RN.calib_modes
m_idx, f_meas, shp, _ = RN.targets_for(CALIB)
log_fm = np.log(np.asarray(f_meas))

PRIORS = {
    "hn002": ("HalfNormal(0.02)", lambda: dist.HalfNormal(0.02), 101),
    "hn005_reference": ("HalfNormal(0.05) [frozen reference]", lambda: dist.HalfNormal(0.05), 42),
    "hn015": ("HalfNormal(0.15)", lambda: dist.HalfNormal(0.15), 102),
    "hc005": ("HalfCauchy(0.05)", lambda: dist.HalfCauchy(0.05), 103),
    "exp005": ("Exponential(mean 0.05)", lambda: dist.Exponential(1.0 / 0.05), 104),
}


def make_model(prior_fn):
    def model(m_idx, f_meas, shp, use_mac):
        theta = numpyro.sample("theta", dist.LogNormal(jnp.zeros(9), RN.NSIG))
        sigma_f = numpyro.sample("sigma_f", prior_fn())
        pf, _, _ = RN.forward(theta, m_idx)
        numpyro.sample("f_obs", dist.Normal(jnp.log(pf), sigma_f), obs=jnp.log(f_meas))
    return model


def run_variant(name, prior_fn, seed):
    p = os.path.join(DRAWS_DIR, f"{name}.npz")
    if os.path.exists(p):
        z = np.load(p, allow_pickle=True)
        samples = {k: jnp.asarray(z[k]) for k in ("theta", "sigma_f")}
        return samples, int(z["divergences"]), float(z["runtime_s"])
    t1 = time.time()
    kernel = NUTS(make_model(prior_fn), target_accept_prob=0.9, dense_mass=True, max_tree_depth=8)
    mcmc = MCMC(kernel, num_warmup=1000, num_samples=1000, num_chains=4,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), m_idx, f_meas, shp, False, extra_fields=("diverging",))
    div = int(np.sum(np.asarray(mcmc.get_extra_fields()["diverging"])))
    samples = mcmc.get_samples(group_by_chain=True)
    rt = round(time.time() - t1, 1)
    np.savez_compressed(p, theta=np.asarray(samples["theta"]),
                        sigma_f=np.asarray(samples["sigma_f"]),
                        divergences=div, runtime_s=rt, seed=seed,
                        gnames=np.array([str(g) for g in RN.rb["gnames"]]))
    return samples, div, rt


def prior_predictive_check(prior_name, prior_fn, n=800, seed=7):
    """Fraction of the 18 measured log-frequencies inside the per-mode central 95% prior predictive."""
    rng = np.random.default_rng(seed)
    with numpyro.handlers.seed(rng_seed=seed):
        sig_draws = np.asarray([numpyro.sample(f"s{i}", prior_fn()) for i in range(n)])
    th_draws = np.exp(rng.normal(0, RN.NSIG, (n, 9)))
    fwd = jax.jit(lambda t: RN.forward(t, m_idx)[0])
    lp = np.array([np.log(np.asarray(fwd(jnp.asarray(th)))) for th in th_draws])   # (n, 18)
    lp_noise = lp + rng.normal(0, 1, lp.shape) * sig_draws[:, None]
    lo, hi = np.percentile(lp_noise, [2.5, 97.5], axis=0)
    inside = (log_fm >= lo) & (log_fm <= hi)
    return float(inside.mean()), int(inside.sum())


# ================= run all variants =================
results, ref_repro = {}, None
stored = json.load(open(os.path.join(TW, "theta_full.json")))
gnames = [str(g) for g in RN.rb["gnames"]]
for name, (label, prior_fn, seed) in PRIORS.items():
    print(f"--- {name} ({label}) seed {seed} ---", flush=True)
    samples, div, rt = run_variant(name, prior_fn, seed)
    conv = RN.convergence(samples, div, 1000, 4)
    flat = {k: np.asarray(v).reshape(-1, *np.asarray(v).shape[2:]) for k, v in samples.items()}
    sf = flat["sigma_f"]
    ppc_frac, ppc_n = prior_predictive_check(name, prior_fn)
    results[name] = {
        "prior": label, "seed": seed, "nuts_runtime_s": rt,
        "sigma_f_median": float(np.median(sf)),
        "sigma_f_ci95": [float(np.percentile(sf, 2.5)), float(np.percentile(sf, 97.5))],
        "theta_median": {g: float(np.median(flat["theta"][:, i])) for i, g in enumerate(gnames)},
        "convergence": conv,
        "status": "GREEN" if conv["gate_pass"] else "YELLOW (non-converged; intervals not trustworthy)",
        "prior_predictive_covered": f"{ppc_n}/18",
        "prior_predictive_frac": ppc_frac,
    }
    print(f"  sigma_f {results[name]['sigma_f_median']:.4f} "
          f"[{results[name]['sigma_f_ci95'][0]:.4f},{results[name]['sigma_f_ci95'][1]:.4f}] "
          f"rhat {conv['worst_rhat']:.4f} ess {conv['min_ess']:.0f} div {div} "
          f"pass {conv['gate_pass']} ppc {ppc_n}/18 ({rt}s)", flush=True)
    if name == "hn005_reference":
        dev_sf = abs(results[name]["sigma_f_median"] - stored["sigma_f_median"])
        # MC standard error of a posterior median ~ 1.25 * sd / sqrt(ESS); use per-parameter ESS
        devs, tols = [], []
        for i, g in enumerate(gnames):
            sd = float(np.std(flat["theta"][:, i]))
            ess = conv["per_variable"]["theta"]["ess_min"]
            devs.append(abs(results[name]["theta_median"][g] - stored["theta_median"][g]))
            tols.append(3 * 1.25 * sd / np.sqrt(ess))
        ref_repro = {
            "pass": bool(dev_sf <= 0.005 and all(d <= t for d, t in zip(devs, tols))),
            "sigma_f_median": results[name]["sigma_f_median"],
            "stored_sigma_f_median": stored["sigma_f_median"],
            "sigma_f_abs_dev": dev_sf, "sigma_f_tol": 0.005,
            "theta_max_abs_dev": float(max(devs)), "theta_tol": float(min(tols)),
            "theta_tols_per_param": [round(t, 4) for t in tols],
            "note": "same frozen forward/likelihood/settings/seed as the stored run; tolerance = "
                    "N4 (sigma_f +-0.005 abs; theta medians within 3x MC SE of the median)"}
        print(f"  REFERENCE REPRODUCTION: pass={ref_repro['pass']} "
              f"sigma_f dev {dev_sf:.5f}, theta max dev {max(devs):.5f}", flush=True)

# ================= posterior predictive PIT (reference) =================
zref = np.load(os.path.join(DRAWS_DIR, "hn005_reference.npz"), allow_pickle=True)
th_flat = zref["theta"].reshape(-1, 9)
sf_flat = zref["sigma_f"].reshape(-1)
take = np.linspace(0, len(th_flat) - 1, 500).astype(int)
fwd = jax.jit(lambda t: RN.forward(t, m_idx)[0])
pit = np.zeros(len(CALIB))
for s in take:
    lp = np.log(np.asarray(fwd(jnp.asarray(th_flat[s]))))
    pit += norm.cdf((log_fm - lp) / sf_flat[s])
pit /= len(take)

# floor conclusion sentences
floor = {}
for name, r in results.items():
    med = r["sigma_f_median"]
    conv_ok = r["convergence"]["gate_pass"]
    survives = 0.035 <= med <= 0.06
    floor[name] = (
        f"{r['prior']}: sigma_f median {med*100:.1f}% [{r['sigma_f_ci95'][0]*100:.1f}, "
        f"{r['sigma_f_ci95'][1]*100:.1f}]% — "
        + ("the ~4.6% floor and the model-form conclusion SURVIVE" if survives else
           "the floor moved outside 3.5-6.0%; conclusion is prior-sensitive HERE")
        + ("" if conv_ok else " [NON-CONVERGED variant: worst R-hat "
           f"{r['convergence']['worst_rhat']:.3f}, min ESS {r['convergence']['min_ess']:.0f} — "
           "interval not trustworthy]"))

out = {
    "source_run": "shocksat_fem_modal_twin_20260609 frozen modal twin (run_nuts.py likelihood, "
                  "18 paired log-frequencies, no MAC); sampler NUTS, 4 chains x 1000 draws, "
                  "per-chain draws retained in out/a2_draws/",
    "reference_reproduction": ref_repro,
    "variants": results,
    "floor_conclusion_per_variant": floor,
    "posterior_predictive_PIT_reference": {
        "per_mode": {str(t): round(float(p), 3) for t, p in zip(CALIB, pit)},
        "note": "PIT = posterior-predictive CDF at the measured value; calibrated => ~uniform(0,1)"},
    "runtime_s": round(time.time() - t0, 1),
}
json.dump(out, open(os.path.join(WS, "out", "a2_sigma_f_sweep.json"), "w"), indent=1)
print(json.dumps(floor, indent=1))
print(f"A2 done {out['runtime_s']}s")
