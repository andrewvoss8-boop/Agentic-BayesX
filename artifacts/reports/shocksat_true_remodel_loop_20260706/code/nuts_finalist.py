#!/usr/bin/env python3
"""Full NUTS θ posterior for finalists + A0 (card §6 finalists; AGENTS convergence gate).
S0 modal-frequency likelihood (rmodel.py conventions, D6): lognormal θ prior sd 0.25, Gaussian on paired
eigenvalues sd 5%, frozen pairing. 4 chains, x64, sequential. Writes out/nuts_<cid>.json (rhat_max/ess_min/
div_frac over ALL variables) + data/theta_post_<cid>.npz. Screening stays MAP/deterministic and is labeled
NO-sampler; THIS is the only Bayesian-updating step.
Run detached: nohup python3 code/nuts_finalist.py <cid> > logs/nuts_<cid>.log 2>&1 &
"""
import json, os, sys, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F

WS = F.WS


def run(cid, seed=20260706, warmup=1000, samples=1000, chains=4):
    import jax
    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist
    from numpyro.diagnostics import summary as nuts_summary
    from numpyro.infer import MCMC, NUTS, init_to_median

    pkg = F.Package.load(cid)
    assert jnp.asarray(np.asarray(pkg.A)).dtype == jnp.float64, "x64 not active"
    A = jnp.asarray(np.asarray(pkg.A))
    A_fix = jnp.asarray(np.asarray(pkg.A_fix))
    npar = len(pkg.free_names)
    pairs = np.asarray(pkg.pairs)
    pairs = pairs[pairs[:, 2] >= 0.3]                 # D12b: same likelihood pair filter as theta_map
    femk = jnp.asarray(pairs[:, 1].astype(int))
    mfreqs = np.asarray(pkg.mfreqs, float)
    tgt = jnp.asarray((mfreqs[pairs[:, 0].astype(int)] * 2 * np.pi) ** 2)

    def model():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, F.NSIG_THETA).expand([npar]).to_event(1))
        sig = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        K = A_fix + jnp.einsum("g,gij->ij", jnp.exp(lt), A)
        lam = jnp.clip(jnp.linalg.eigvalsh(K), 1e-9, None)
        var = (sig * tgt) ** 2
        numpyro.factor("freq", -0.5 * jnp.sum((tgt - lam[femk]) ** 2 / var
                                              + jnp.log(2 * jnp.pi * var)))

    t0 = time.time()
    kern = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median, dense_mass=True)
    mcmc = MCMC(kern, num_warmup=warmup, num_samples=samples, num_chains=chains,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    st = nuts_summary(g, group_by_chain=True)
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    diag = {"cid": cid,
            "rhat_max": round(max(float(np.nanmax(v["r_hat"])) for v in st.values()), 4),
            "ess_min": round(min(float(np.nanmin(v["n_eff"])) for v in st.values()), 1),
            "div_frac": div / (chains * samples), "divergences": div,
            "chains": chains, "draws": chains * samples,
            "runtime_s": round(time.time() - t0, 1),
            "likelihood": "S0 modal-frequency (paired eigenvalues, sd 5%), lognormal theta prior 0.25",
            "sampler": "NUTS numpyro x64, 4 chains sequential, dense mass"}
    diag["converged"] = bool(diag["rhat_max"] <= 1.05 and diag["ess_min"] >= 200
                             and diag["div_frac"] < 0.02)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(np.asarray(v).shape[2:])) for k, v in g.items()}
    np.savez_compressed(os.path.join(WS, "data", f"theta_post_{cid}.npz"),
                        theta_post=np.exp(flat["log_theta"]), sigma_w2=flat["sigma_w2"],
                        free_names=np.asarray(pkg.free_names))
    json.dump(diag, open(os.path.join(WS, "out", f"nuts_{cid}.json"), "w"), indent=1)
    F.log_runtime(f"nuts_{cid}", diag["runtime_s"])
    print(json.dumps(diag, indent=1))


if __name__ == "__main__":
    run(sys.argv[1])
