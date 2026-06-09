"""Run NUTS for one config; compute convergence diagnostics over ALL sampled variables,
held-out dev-LPD, WAIC, and posterior summaries (theta, QOI)."""
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpy as np
from numpyro.infer import MCMC, NUTS
from numpyro.diagnostics import effective_sample_size, split_gelman_rubin
import forward
import model as M


def _flatten_sites(samples_gbc):
    """samples_gbc: dict site -> (chains, draws, *shape). Yield (name, arr(chains,draws))."""
    out = {}
    for name, arr in samples_gbc.items():
        a = np.asarray(arr)
        if a.ndim == 2:
            out[name] = a
        else:
            flat = a.reshape(a.shape[0], a.shape[1], -1)
            for k in range(flat.shape[2]):
                out[f"{name}[{k}]"] = flat[:, :, k]
    return out


# sampled (not deterministic) sites we must diagnose, incl. raw hierarchical latents
_SAMPLED = {"log_theta", "sigma_f", "sigma_phi", "tau_f", "tau_phi", "tau",
            "d_z", "g_z", "d", "g"}


def run_config(cfg, data, seed=0, chains=4, warmup=600, draws=600, qoi=True):
    ref = data["ref"]
    mdl = M.make_model(cfg, ref)
    kernel = NUTS(mdl, target_accept_prob=cfg.get("target_accept", 0.9),
                  dense_mass=cfg.get("dense_mass", False))
    mcmc = MCMC(kernel, num_warmup=warmup, num_samples=draws, num_chains=chains,
                chain_method="sequential", progress_bar=False)
    rng = jax.random.PRNGKey(seed)
    mcmc.run(rng, train_f=jnp.asarray(data["train_f"]), train_phi=jnp.asarray(data["train_phi"]),
             extra_fields=("diverging",))
    div = np.asarray(mcmc.get_extra_fields()["diverging"])
    div_frac = float(div.mean())

    gbc = mcmc.get_samples(group_by_chain=True)
    # diagnostics over ALL sampled variables (incl. raw latents d_z/g_z)
    flat = _flatten_sites({k: v for k, v in gbc.items() if k in _SAMPLED})
    rhats, esss = {}, {}
    for name, a in flat.items():
        rhats[name] = float(split_gelman_rubin(a))
        esss[name] = float(effective_sample_size(a))
    max_rhat = max(rhats.values()); min_ess = min(esss.values())
    worst_rhat = max(rhats, key=rhats.get); worst_ess = min(esss, key=esss.get)

    # posterior draws (merged)
    samples = mcmc.get_samples()
    draws_np = {k: np.asarray(v) for k, v in samples.items()}

    # held-out dev LPD + train WAIC
    pw_dev = M.predict_pointwise(draws_np, data["dev_f"], data["dev_phi"], cfg, ref)
    dev_lpd = M.lpd_total(pw_dev)
    pw_tr = M.predict_pointwise(draws_np, data["train_f"], data["train_phi"], cfg, ref)
    waic_elpd, p_waic = M.waic(pw_tr)

    theta_mean = draws_np["theta"].mean(0)
    theta_sd = draws_np["theta"].std(0)

    res = dict(dev_lpd=dev_lpd, waic_elpd=waic_elpd, p_waic=p_waic,
               max_rhat=max_rhat, min_ess=min_ess, div_frac=div_frac,
               worst_rhat_var=worst_rhat, worst_ess_var=worst_ess,
               theta_mean=theta_mean.tolist(), theta_sd=theta_sd.tolist(),
               n_sampled_scalar=len(flat), rhats=rhats, esss=esss)

    if qoi:
        # posterior QOI: peak receptance per path, averaged over a thinned set of draws
        th = draws_np["theta"]
        idx = np.linspace(0, th.shape[0] - 1, min(200, th.shape[0])).astype(int)
        qref = np.array([float(forward.receptance_peak(jnp.asarray(th[i]), 11, 0)) for i in idx])
        qhld = np.array([float(forward.receptance_peak(jnp.asarray(th[i]), 5, 8)) for i in idx])
        res["qoi_ref_mean"] = float(qref.mean()); res["qoi_ref_sd"] = float(qref.std())
        res["qoi_heldout_mean"] = float(qhld.mean()); res["qoi_heldout_sd"] = float(qhld.std())
    res["draws"] = draws_np
    return res


def passes_gate(res, max_rhat=1.05, min_ess=200, max_div=0.02):
    return (res["max_rhat"] <= max_rhat and res["min_ess"] >= min_ess
            and res["div_frac"] < max_div)
