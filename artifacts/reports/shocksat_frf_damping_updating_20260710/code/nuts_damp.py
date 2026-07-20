#!/usr/bin/env python3
"""Full NUTS posterior for finalists: theta (modal-frequency likelihood, eigvalsh) + band-zeta damping
(FRF-amplitude likelihood on the 4 dev drives at the MAP mode shapes). numpyro x64, 4 chains sequential.
All-variable R-hat/ESS/divergences (AGENTS convergence gate). Screening stayed MAP/deterministic (NO-sampler);
THIS is the only Bayesian-updating step.

Design (honest, labeled): damping is factorized from theta via the MAP modes -- damping does not move
eigenvalues, and D2 shows per-mode zeta is unidentifiable at 2 Hz, so the zeta posterior is expected wide /
prior-influenced. theta enters only the differentiable eigvalsh modal likelihood (no eigenvector gradients ->
numerically stable). Reads the 4 DEV drives only (never the vault).
Run detached: nohup python3 code/nuts_damp.py <cid> > logs/nuts_<cid>.log 2>&1 &
"""
import json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femdamp as D
import femlib as F
import score as SC

WS = D.WS
BAND = D.BAND
EDGES = D.BAND_EDGES
SIG_LOGH = 0.20              # FRF log10|H| discrepancy floor (amplitude noise+model)


def precompute(cid):
    """MAP modes/residues + measured log|H| per dev drive (usable channels, in band). numpy constants."""
    pkg = F.Package.load(cid)
    theta_map = np.asarray(pkg.theta_map()[0], float)
    f, Q = pkg.modes(theta_map)
    inb = np.where((f >= BAND[0] - 10) & (f <= BAND[1] + 40))[0]
    fi = f[inb]
    band_idx = np.clip(np.digitize(fi, EDGES) - 1, 0, len(EDGES) - 2)     # which zeta-band each mode is in
    caches = SC.load_caches()
    drives = []
    MAXCH, MAXF = 24, 45          # subsample for a tractable damping likelihood (zeta weakly identified, D2)
    for k in F.DRIVE_KEYS:
        c = caches[k]; fc = c["freqs"]; band = c["band"]
        rows, cols = SC._usable(pkg, c)
        if len(rows) == 0:
            continue
        if len(rows) > MAXCH:
            sel = np.linspace(0, len(rows) - 1, MAXCH).astype(int)
            rows, cols = rows[sel], cols[sel]
        bidx = np.where(band)[0]
        if len(bidx) > MAXF:
            bidx = bidx[np.linspace(0, len(bidx) - 1, MAXF).astype(int)]
        Us = np.asarray(pkg.sens_rows)[rows] @ Q[:, inb]         # (nch, nmode)
        Ud = np.asarray(pkg.drives[k]) @ Q[:, inb]               # (nmode,)
        residues = Us * Ud[None, :]                              # (nch, nmode)
        ym = np.log10(np.abs(c["H1"][cols][:, bidx]) + 1e-300)   # (nch, nf)
        drives.append({"res": residues, "wi": 2 * np.pi * fi, "w": 2 * np.pi * fc[bidx], "ym": ym})
    return pkg, theta_map, band_idx, drives


def run(cid, seed=20260710, warmup=600, samples=600, chains=4):
    import jax
    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    import numpyro
    import numpyro.distributions as dist
    from numpyro.diagnostics import summary as nuts_summary
    from numpyro.infer import MCMC, NUTS, init_to_median

    pkg, theta_map, band_idx_np, drives = precompute(cid)
    assert jnp.asarray(np.asarray(pkg.A)).dtype == jnp.float64, "x64 not active"
    A = jnp.asarray(np.asarray(pkg.A)); A_fix = jnp.asarray(np.asarray(pkg.A_fix))
    npar = len(pkg.free_names)
    pairs = np.asarray(pkg.pairs); pairs = pairs[pairs[:, 2] >= 0.3]
    femk = jnp.asarray(pairs[:, 1].astype(int))
    mfreqs = np.asarray(pkg.mfreqs, float)
    tgt = jnp.asarray((mfreqs[pairs[:, 0].astype(int)] * 2 * np.pi) ** 2)
    band_idx = jnp.asarray(band_idx_np)
    Jd = [{k: jnp.asarray(v) for k, v in d.items()} for d in drives]
    z_lo, z_hi = D.ZETA_LO, D.ZETA_HI

    def frf_loglik(zeta_bands):
        zi = zeta_bands[band_idx]                                # per-mode zeta
        ll = 0.0
        for d in Jd:
            wi = d["wi"]; w = d["w"]; res = d["res"]; ym = d["ym"]
            Dd = wi[None, :] ** 2 - (w ** 2)[:, None] + 2j * zi[None, :] * wi[None, :] * w[:, None]
            H = -(w ** 2)[None, :] * (res[:, None, :] / Dd[None, :, :]).sum(-1)   # (nch, nf)
            yp = jnp.log10(jnp.abs(H) / F.G_IN_S2 + 1e-300)
            gain = jnp.mean(ym - yp)                             # one closed-form offset per drive
            ll = ll - 0.5 * jnp.sum((ym - (yp + gain)) ** 2) / SIG_LOGH ** 2
        return ll

    def model():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, F.NSIG_THETA).expand([npar]).to_event(1))
        sig = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        # band zeta ~ Uniform on the physical interval [0.2%, 5%] (bounded -> well-behaved even when the
        # FRF-amplitude likelihood rails to the ceiling; the logit-normal form saturated for A0).
        zeta = numpyro.sample("zeta_bands", dist.Uniform(z_lo, z_hi).expand([len(EDGES) - 1]).to_event(1))
        K = A_fix + jnp.einsum("g,gij->ij", jnp.exp(lt), A)
        lam = jnp.clip(jnp.linalg.eigvalsh(K), 1e-9, None)
        var = (sig * tgt) ** 2
        numpyro.factor("freq", -0.5 * jnp.sum((tgt - lam[femk]) ** 2 / var + jnp.log(2 * jnp.pi * var)))
        numpyro.factor("frf", frf_loglik(zeta))

    t0 = time.time()
    kern = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median)
    mcmc = MCMC(kern, num_warmup=warmup, num_samples=samples, num_chains=chains,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    st = nuts_summary(g, group_by_chain=True)
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    flat = {k: np.asarray(v).reshape((-1,) + tuple(np.asarray(v).shape[2:])) for k, v in g.items()}
    zeta_post = flat["zeta_bands"]
    diag = {"cid": cid,
            "rhat_max": round(max(float(np.nanmax(v["r_hat"])) for v in st.values()), 4),
            "ess_min": round(min(float(np.nanmin(v["n_eff"])) for v in st.values()), 1),
            "div_frac": div / (chains * samples), "divergences": div,
            "chains": chains, "draws": chains * samples, "runtime_s": round(time.time() - t0, 1),
            "zeta_bands_post_median": [round(float(x), 4) for x in np.median(zeta_post, 0)],
            "zeta_bands_post_q05_q95": [[round(float(a), 4), round(float(b), 4)] for a, b in
                                        zip(np.percentile(zeta_post, 5, 0), np.percentile(zeta_post, 95, 0))],
            "sampler": "NUTS numpyro x64 4 chains; theta~modal-freq lik, band-zeta~FRF-amplitude lik @MAP shapes",
            "damping_note": "wide/prior-influenced zeta posterior expected (D2: per-mode zeta unidentifiable "
                            "at 2 Hz); the 5-95%% width quantifies non-identifiability."}
    diag["converged"] = bool(diag["rhat_max"] <= 1.05 and diag["ess_min"] >= 200 and diag["div_frac"] < 0.02)
    np.savez_compressed(os.path.join(WS, "data", f"post_{cid}.npz"),
                        theta_post=np.exp(flat["log_theta"]), zeta_post=zeta_post,
                        sigma_w2=flat["sigma_w2"], free_names=np.asarray(pkg.free_names))
    json.dump(diag, open(os.path.join(WS, "out", f"nuts_{cid}.json"), "w"), indent=1)
    F.log_runtime(f"nuts_{cid}", diag["runtime_s"])
    print(json.dumps(diag, indent=1))


if __name__ == "__main__":
    run(sys.argv[1])
