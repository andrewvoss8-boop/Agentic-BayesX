#!/usr/bin/env python3
"""Layer 1 (Bayesian): NUTS posterior over per-mode damping zeta from the ring-down envelopes.

The bootstrap CI in layer1_damping.py is a frequentist scatter measure. For a genuine POSTERIOR over zeta we use
NUTS/HMC (AGENTS sampler gate: zeta enters the dynamics nonlinearly, so a posterior over it must be NUTS, not the
linear-Gaussian filter of Layer 2). Model, per mode, pooling its high-SNR ring-down envelope traces:

  env_norm_i(t) = A_i * exp(-zeta * 2*pi*f0 * t) + c_i + noise,   noise ~ Normal(0, sigma_i)

zeta is SHARED across traces i (a mode's damping is global); A_i (amplitude), c_i (noise floor), sigma_i are
per-trace. zeta enters NONLINEARLY through exp(-zeta*...), and the additive floor c_i breaks log-linearity, so this
is a real nonlinear posterior (not a slope regression). Prior zeta ~ LogUniform(0.05%, 6%) -- IDENTICAL bounds to
D22, so "CI < half the prior log-width AND interior" is a like-for-like resolved test. 4 chains; report R-hat and
ESS over ALL sampled variables (incl. per-trace latents), divergence fraction (gate: R-hat<=1.05, ESS>=200, div<2%).
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

import jax
jax.config.update("jax_enable_x64", True)
import numpyro
numpyro.set_host_device_count(4)
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
from numpyro.diagnostics import summary as nsummary
import jax.numpy as jnp

sys.path.insert(0, str(Path(__file__).resolve().parent))
import decay_core as dc

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
REFS = ["m_xpos_990x", "m_zpos_990z", "m_xy_990xy", "m_zpos_900z"]
MODES = [75.3, 99.7, 122.1, 126.1, 136.3, 138.3, 140.4, 162.8, 172.9, 189.2, 195.3, 197.3, 199.4, 234.0, 244.1, 254.3]
ZLO, ZHI = 5e-4, 6e-2
PRIOR_LOGW = np.log(ZHI / ZLO)
MAX_TRACES = 16     # cap per mode (top SNR) to bound runtime
MAX_PTS = 80        # subsample envelope points per trace


def gather_traces(f0):
    others = [m for m in MODES if abs(m - f0) > 0.5]
    traces = []
    for key in REFS:
        r = dc.load_ring(key); fs = float(r["fs_dec"]); t = r["t"]; ip = int(np.median(r["impact_idx_dec"]))
        daq = list(r["daq"]); A = r["A"]
        for ci in range(A.shape[1]):
            for h in range(A.shape[0]):
                f = dc.decay_fit(A[h, ci], t, ip, f0, fs, neighbors=others, return_trace=True)
                if f and f["r2"] > 0.92 and f["snr"] > 10 and f["n_cycles"] > 12:
                    traces.append(f)
    traces.sort(key=lambda f: -f["snr"])
    return traces[:MAX_TRACES]


def model(t, y, tid, ntr, f0):
    """Hierarchical, non-centered (AGENTS convergence gate): each trace has its OWN zeta_i drawn around a
    population zeta_pop with log-spread s_between (= genuine between-channel/amplitude heterogeneity, a hook for
    Layer-2 residual nonlinearity). The reported damping is zeta_pop; its CI is honest (it includes heterogeneity,
    not just within-trace cycle abundance). zeta enters NONLINEARLY through exp(-zeta_i*w0*t)."""
    w0 = 2 * np.pi * f0
    u = numpyro.sample("u", dist.Uniform(np.log(ZLO), np.log(ZHI)))           # log zeta_pop
    zeta_pop = numpyro.deterministic("zeta", jnp.exp(u))
    s_between = numpyro.sample("s_between", dist.HalfNormal(0.5))
    z_raw = numpyro.sample("z_raw", dist.Normal(0, 1).expand([ntr]))          # non-centered
    zeta_i = jnp.exp(u + s_between * z_raw)                                   # (ntr,)
    A = numpyro.sample("A", dist.LogNormal(0.0, 0.3).expand([ntr]))
    c = numpyro.sample("c", dist.HalfNormal(0.15).expand([ntr]))
    sig = numpyro.sample("sigma", dist.HalfNormal(0.08).expand([ntr]))
    mu = A[tid] * jnp.exp(-zeta_i[tid] * w0 * t) + c[tid]
    numpyro.sample("obs", dist.Normal(mu, sig[tid]), obs=y)


def fit_mode(f0, seed=0):
    tr = gather_traces(f0)
    if len(tr) < 5:
        return dict(f_hz=f0, n_traces=len(tr), ok=False, note="too few clean traces for NUTS")
    ts, ys, tids = [], [], []
    for i, f in enumerate(tr):
        tw, ew = np.asarray(f["tw"]), np.asarray(f["ew"]) / f["peak_env"]
        if tw.size > MAX_PTS:
            idx = np.linspace(0, tw.size - 1, MAX_PTS).astype(int)
            tw, ew = tw[idx], ew[idx]
        ts.append(tw); ys.append(ew); tids.append(np.full(tw.size, i))
    t = np.concatenate(ts); y = np.concatenate(ys); tid = np.concatenate(tids)
    mcmc = MCMC(NUTS(model, target_accept_prob=0.9), num_warmup=600, num_samples=600,
                num_chains=4, chain_method="vectorized", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), jnp.asarray(t), jnp.asarray(y), jnp.asarray(tid), len(tr), f0,
             extra_fields=("diverging",))
    post = mcmc.get_samples(group_by_chain=True)
    extra = mcmc.get_extra_fields()
    div = int(np.asarray(extra["diverging"]).sum()) if "diverging" in extra else 0
    # R-hat / ESS over ALL sampled variables (u, A[], c[], sigma[]) -- exclude deterministic zeta from the gate set
    summ = nsummary({k: v for k, v in post.items() if k != "zeta"}, group_by_chain=True)
    rhats = [np.nanmax(summ[k]["r_hat"]) for k in summ]
    esss = [np.nanmin(summ[k]["n_eff"]) for k in summ]
    rhat = float(np.nanmax(rhats)); ess = float(np.nanmin(esss))
    z = np.asarray(post["zeta"]).reshape(-1) * 100  # percent (population zeta)
    lo, med, hi = np.percentile(z, [2.5, 50, 97.5])
    sb = np.asarray(post["s_between"]).reshape(-1)
    ci_logw = np.log(max(hi, 1e-6) / max(lo, 1e-6))
    n_total = 4 * 600
    div_frac = div / n_total
    conv = bool(rhat <= 1.05 and ess >= 200 and div_frac < 0.02)
    resolved = bool(conv and ci_logw < 0.5 * PRIOR_LOGW and med / 100 > ZLO * 1.1 and med / 100 < ZHI * 0.9)
    return dict(f_hz=f0, n_traces=len(tr), ok=True,
                zeta_pct=dict(med=round(float(med), 3), lo=round(float(lo), 3), hi=round(float(hi), 3)),
                ci_logwidth_frac_of_prior=round(ci_logw / PRIOR_LOGW, 3),
                s_between_log_med=round(float(np.median(sb)), 3),   # between-channel zeta heterogeneity (log spread)
                rhat_max=round(rhat, 4), ess_min=round(ess, 0), divergences=div, div_frac=round(div_frac, 4),
                n_samples=n_total, converged=conv, resolved=resolved)


def main():
    t0 = time.time()
    results = []
    for f0 in MODES:
        r = fit_mode(f0)
        results.append(r)
        if r.get("ok"):
            z = r["zeta_pct"]
            print(f"  {f0:6.1f} Hz: zeta {z['med']:.3f}% [{z['lo']:.3f},{z['hi']:.3f}] "
                  f"ci/prior {r['ci_logwidth_frac_of_prior']:.3f} | R-hat {r['rhat_max']:.3f} ESS {r['ess_min']:.0f} "
                  f"div {r['divergences']} | conv {r['converged']} resolved {r['resolved']}")
        else:
            print(f"  {f0:6.1f} Hz: {r['note']}")
    n_res = sum(r.get("resolved", False) for r in results)
    n_conv = sum(r.get("converged", False) for r in results)
    out = dict(deliverable="Layer 1 NUTS posterior over per-mode zeta (hierarchical exp-decay+floor envelope model)",
               sampler="NUTS/HMC, 4 chains, 600 warmup + 600 samples, target_accept 0.9, vectorized",
               prior="zeta ~ LogUniform(0.05%, 6%) (identical bounds to D22)",
               gate="converged = R-hat<=1.05 AND ESS>=200 AND div_frac<2%; resolved = converged AND CI<0.5*prior AND interior",
               n_modes=len(results), n_converged=n_conv, n_resolved=n_res, modes=results,
               runtime_s=round(time.time() - t0, 1),
               verdict=(f"{n_res}/{len(results)} union modes give a CONVERGED NUTS posterior over zeta that is "
                        f"RESOLVED (CI < half the D22 prior, interior), vs D22's 0/9 from the windowed FRF."))
    OUT.mkdir(exist_ok=True)
    (OUT / "layer1_nuts.json").write_text(json.dumps(out, indent=2))
    print(f"\nLayer 1 NUTS: {n_res}/{len(results)} resolved, {n_conv} converged | {out['runtime_s']:.0f}s")


if __name__ == "__main__":
    main()
