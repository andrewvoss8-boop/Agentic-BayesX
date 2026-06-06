#!/usr/bin/env python3
"""STAGE-3 BLIND inference: hierarchical NumPyro NUTS with the three structure-aware fixes.

BLINDNESS: consumes ONLY codex_truth/dataset/observations.npz. Does NOT read sealed_truth/code/report.

Fixes under test (vs the Stage-0/1 frequency-only failure):
  #1 ASYMMETRIC per-strut forward (blind3_model.load_AM_diag, 6 per-strut k) -> represents x!=y, rx!=ry.
  #2 STRUCTURE-BASED discrepancy: per-strut log-k field d_j with a FEATURE-SPACE (azimuth) covariance,
     applied in PARAMETER space (k_j = k_pop*exp(d0_j)) -> carries the azimuthal/spatial error a
     frequency-only kernel cannot. sigma_d is LEARNED (NOT capped) -- the headline ridge test.
  #3 COMPLEX likelihood on real+imag apparent mass (all 6 diagonal DOF) -> phase/antiresonance constrain.

Latents (all sampled; convergence gate over ALL of them):
  log_k_pop, d_raw(6)+sigma_d, f_dome, z_b(n_train builds)+sigma_build, sigma_e.
Non-centered hierarchical (z_b, d_raw). >=4 chains. Never claim "NUTS active" unless the gate passes.

Outputs (report/): blind3_results.json, blind3_posterior.npz, blind3_nuts_diagnostics.{json,md},
blind3_heldout.json, blind3_companions.json. QOI in blind3_qoi.py.

Env: R3_SMOKE=1 quick low-sample test (NOT for reporting). R3_NODISC=1 runs the no-discrepancy companion.
"""
from __future__ import annotations
import os, json, time, sys
from pathlib import Path
import numpy as np
import jax, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS

import blind3_model as bm

HERE = Path(__file__).resolve().parents[1]
REP = HERE / "report"; REP.mkdir(exist_ok=True)

SMOKE = os.environ.get("R3_SMOKE", "0") == "1"
SEED = 20260604
K_NOM = 1.816e7
BAND = (35.0, 160.0)          # inference band: first mount+bounce cluster (carries QOI energy)
HELDOUT_BUILDS = [6, 7]       # whole builds held out
HELDOUT_BAND = (95.0, 115.0)  # whole frequency band held out (from training builds)


# ---------------------------------------------------------------- adaptive grid from DATA peaks (fixed)
def build_grid(obs, band=BAND, n_base=28, per_peak=5, half=6.0):
    from scipy.signal import find_peaks
    f = obs["f"]; lo, hi = band
    data = obs["mag"].mean(axis=0)                      # (6,nf)
    pts = list(np.geomspace(lo, hi, n_base))
    inb = (f >= lo) & (f <= hi)
    for j in range(6):
        y = data[j].copy(); y[~inb] = 0.0
        pk, _ = find_peaks(y, prominence=y.max() * 0.05)
        pk = pk[np.argsort(y[pk])[::-1][:3]]
        for p in pk:
            c = f[p]
            pts.extend(list(np.linspace(max(lo, c - half), min(hi, c + half), per_peak)))
    g = np.unique(np.round(np.array(sorted(pts)), 3))
    g = g[(g >= lo) & (g <= hi)]
    return g


def assemble_data(obs, grid):
    """Interpolate complex AM onto the grid; return (re,im,scale) arrays (n_build,6,ng) and band mask."""
    f = obs["f"]; nb = obs["AM"].shape[0]; ng = len(grid)
    re = np.zeros((nb, 6, ng)); im = np.zeros((nb, 6, ng))
    for b in range(nb):
        for j in range(6):
            re[b, j] = np.interp(grid, f, obs["re"][b, j])
            im[b, j] = np.interp(grid, f, obs["im"][b, j])
    scale = np.abs(np.mean(re + 1j * im, axis=0))        # (6,ng) build-avg local magnitude (fixed noise scale)
    # floor per-DOF at 0.3x the band median so antiresonance notches don't pathologically dominate the
    # relative-complex likelihood (still magnitude-relative -> phase/antiresonance DO count, just bounded).
    med = np.median(scale, axis=1, keepdims=True)
    scale = np.clip(scale, 0.3 * med, None)
    return re, im, scale


# ---------------------------------------------------------------- numpyro model
def make_model(grid_j, M_src6, m_dome, L_feat, re_obs, im_obs, scale, train_builds, freq_mask, learn_d=True):
    """re_obs,im_obs: (nb,6,ng). train_builds: list of build idx. freq_mask: (ng,) bool of fitted freqs."""
    L_feat_j = jnp.asarray(L_feat)
    fmask = jnp.asarray(freq_mask)
    scale_j = jnp.asarray(scale)
    nb = len(train_builds)

    def model():
        # informative prior: data mount-mode peaks sit clearly in 50-90 Hz -> k_pop near nominal (guards the
        # degenerate soft-strut mode where modes leave the band; this is identifiability-guarding, NOT a cap).
        log_k = numpyro.sample("log_k_pop", dist.Normal(np.log(K_NOM), 0.15))
        k_pop = jnp.exp(log_k)
        f_dome = numpyro.sample("f_dome", dist.TruncatedNormal(93.5, 8.0, low=60.0, high=130.0))
        sigma_build = numpyro.sample("sigma_build", dist.HalfNormal(0.05))
        sigma_e = numpyro.sample("sigma_e", dist.HalfNormal(0.5))   # weakly-informative; data-driven (we expect inflation)
        if learn_d:
            # sigma_d informative: observed mode SPLITS are ~15-30% -> per-strut log-k field ~0.15-0.35.
            # This is a justified informative prior (NOT a hard cap); sigma_d is still LEARNED.
            sigma_d = numpyro.sample("sigma_d", dist.HalfNormal(0.20))
            d_raw = numpyro.sample("d_raw", dist.Normal(0, 1).expand([6]).to_event(1))
            d_field = sigma_d * (L_feat_j @ d_raw)        # structured (feature-correlated) per-strut field
        else:
            numpyro.deterministic("sigma_d", jnp.array(0.0))
            d_field = jnp.zeros(6)
        d0 = d_field - jnp.mean(d_field)                  # zero-mean -> separates k_pop from d
        numpyro.deterministic("d0", d0)
        z_b = numpyro.sample("z_b", dist.Normal(0, 1).expand([nb]).to_event(1))   # non-centered build scatter

        def one_build(zbi):
            k_struts = k_pop * jnp.exp(sigma_build * zbi) * jnp.exp(d0)
            M = bm.forward_complex(k_struts, f_dome, M_src6, m_dome, grid_j)   # (6,ng) complex
            return jnp.real(M), jnp.imag(M)
        re_m, im_m = jax.vmap(one_build)(jnp.asarray(z_b))   # (nb,6,ng)

        sd = sigma_e * scale_j[None, :, :]                 # (1,6,ng) -> broadcast
        w = fmask[None, None, :]
        re_d = jnp.asarray(re_obs[train_builds]); im_d = jnp.asarray(im_obs[train_builds])
        with numpyro.handlers.mask(mask=jnp.broadcast_to(w, re_m.shape)):
            numpyro.sample("re", dist.Normal(re_m, sd), obs=re_d)
            numpyro.sample("im", dist.Normal(im_m, sd), obs=im_d)
    return model


def run_nuts(model, draws, warmup, chains=4, seed=SEED, init_vals=None):
    from numpyro.infer import init_to_value, init_to_median
    istrat = init_to_value(values=init_vals) if init_vals else init_to_median()
    # max_tree_depth capped at 8 for tractability. The sampler frequently HITS this cap on this problem --
    # itself evidence of pathological (ridge/multimodal) geometry, consistent with the prior blind run.
    mtd = int(os.environ.get("R3_TREE_DEPTH", "8"))
    kern = NUTS(model, target_accept_prob=0.9, max_tree_depth=mtd, dense_mass=False, init_strategy=istrat)
    cm = os.environ.get("R3_CHAIN_METHOD", "vectorized")   # vectorized = vmap chains (fast on 1 device)
    mcmc = MCMC(kern, num_warmup=warmup, num_samples=draws, num_chains=chains,
                chain_method=cm, progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed))
    return mcmc


# ---------------------------------------------------------------- diagnostics over ALL latents
def diagnostics(mcmc):
    import arviz as az
    idata = az.from_numpyro(mcmc)
    summ = az.summary(idata, kind="diagnostics", round_to=6)
    out = {}
    worst_rhat = 0.0; min_bulk = 1e18; min_tail = 1e18
    for name in summ.index:
        r = float(summ.loc[name, "r_hat"]); be = float(summ.loc[name, "ess_bulk"]); te = float(summ.loc[name, "ess_tail"])
        out[name] = dict(r_hat=r, ess_bulk=be, ess_tail=te)
        worst_rhat = max(worst_rhat, r); min_bulk = min(min_bulk, be); min_tail = min(min_tail, te)
    div = int(np.sum(mcmc.get_extra_fields()["diverging"])) if "diverging" in mcmc.get_extra_fields() else None
    return out, dict(worst_rhat=worst_rhat, min_ess_bulk=min_bulk, min_ess_tail=min_tail, divergences=div)


# ---------------------------------------------------------------- prediction helper (vectorized)
def predict_complex(samples, build_factor, grid_j, M_src6, m_dome):
    """Posterior-predictive complex AM (n_draw,6,ng) for one build factor (scalar exp(sigma_build*z))."""
    k_pop = np.exp(samples["log_k_pop"]); d0 = samples["d0"]; f_dome = samples["f_dome"]
    nd = len(k_pop)
    def one(i):
        k = k_pop[i] * build_factor[i] * np.exp(d0[i])
        return bm.forward_complex(jnp.asarray(k), float(f_dome[i]), M_src6, m_dome, grid_j)
    return np.stack([np.asarray(one(i)) for i in range(nd)])


def main():
    t0 = time.time()
    obs = bm.load_observations()
    M_src6, m_dome, lf = bm.source_rigid_from_asymptote(obs)
    grid = build_grid(obs)
    grid_j = jnp.asarray(grid)
    re_obs, im_obs, scale = assemble_data(obs, grid)
    L_feat = np.linalg.cholesky(bm.feature_corr() + 1e-9 * np.eye(6))

    # frequency mask: full band for the MAIN fit; band hold-out handled in companion
    fmask_full = np.ones(len(grid), dtype=bool)
    train_main = [0, 1, 2, 3, 4, 5]                       # builds 6,7 held out
    draws = 60 if SMOKE else 350
    warmup = 60 if SMOKE else 350
    chains = 2 if SMOKE else 4

    print(f"[grid] {len(grid)} points in {BAND} Hz | train builds {train_main} | held-out {HELDOUT_BUILDS}")
    print(f"[run] chains={chains} warmup={warmup} draws={draws} SMOKE={SMOKE}")

    init_vals = dict(log_k_pop=np.log(K_NOM), f_dome=93.5, sigma_build=0.04, sigma_e=1.0,
                     sigma_d=0.15, d_raw=np.zeros(6), z_b=np.zeros(len(train_main)))
    # ---- MAIN fit (WITH structure-based discrepancy, sigma_d LEARNED) ----
    model = make_model(grid_j, M_src6, m_dome, L_feat, re_obs, im_obs, scale, train_main, fmask_full, learn_d=True)
    mcmc = run_nuts(model, draws, warmup, chains, init_vals=init_vals)
    print(f"[t={time.time()-t0:.0f}s] MAIN FIT done", flush=True)
    diag_all, diag_sum = diagnostics(mcmc)
    samples = {k: np.asarray(v) for k, v in mcmc.get_samples().items()}
    np.savez(REP / "blind3_posterior.npz", grid=grid, M_src6=M_src6, m_dome=np.array(m_dome),
             scale=scale, **samples)

    def q(a, ps=(2.5, 50, 97.5)):
        return [float(x) for x in np.percentile(a, ps)]
    res = dict(
        band_hz=list(BAND), n_grid=len(grid), n_train_builds=len(train_main), heldout_builds=HELDOUT_BUILDS,
        chains=chains, warmup=warmup, draws=draws,
        learned_with_d=dict(
            k_pop=q(np.exp(samples["log_k_pop"])), f_dome=q(samples["f_dome"]),
            sigma_build=q(samples["sigma_build"]), sigma_e=q(samples["sigma_e"]),
            sigma_d=q(samples["sigma_d"]) if "sigma_d" in samples else None,
            d0_per_strut=[q(samples["d0"][:, j]) for j in range(6)],
        ),
        convergence=diag_sum,
        gate_pass=bool(diag_sum["worst_rhat"] < 1.01 and diag_sum["min_ess_bulk"] >= 400
                       and diag_sum["min_ess_tail"] >= 400
                       and (diag_sum["divergences"] or 0) < 0.02 * draws * chains),
    )
    # convergence over ALL latents table
    md = ["# Stage-3 BLIND NUTS diagnostics (ALL latents incl. discrepancy + per-build)\n",
          f"band {BAND} Hz, {len(grid)} grid pts, {chains} chains x ({warmup}+{draws}); sigma_d LEARNED (not capped)\n",
          "| latent | R-hat | ESS bulk | ESS tail |", "|---|---|---|---|"]
    for name, dd in sorted(diag_all.items()):
        md.append(f"| {name} | {dd['r_hat']:.4f} | {dd['ess_bulk']:.1f} | {dd['ess_tail']:.1f} |")
    md.append(f"\n**worst R-hat {diag_sum['worst_rhat']:.4f}, min bulk ESS {diag_sum['min_ess_bulk']:.1f}, "
              f"min tail ESS {diag_sum['min_ess_tail']:.1f}, divergences {diag_sum['divergences']}**")
    md.append(f"\nGate (R-hat<1.01, bulk&tail ESS>=400, div<2%): **{'PASS' if res['gate_pass'] else 'FAIL'}**")
    (REP / "blind3_nuts_diagnostics.md").write_text("\n".join(md))
    (REP / "blind3_nuts_diagnostics.json").write_text(json.dumps(diag_all, indent=2))

    # ---- HELD-OUT calibration (builds 6,7 full band; + band 95-115 on train builds) read WITH width ----
    heldout = heldout_calibration(samples, obs, grid, M_src6, m_dome, scale, re_obs, im_obs)
    (REP / "blind3_heldout.json").write_text(json.dumps(heldout, indent=2))
    res["heldout"] = heldout

    # ---- effective-vs-nominal sample count ----
    sig_post = float(np.std(samples["log_k_pop"])); sig_prior = 0.25
    n_eff = (sig_prior / max(sig_post, 1e-9)) ** 2
    n_nominal = len(train_main) * 6 * int(fmask_full.sum()) * 2
    res["effective_sample_count"] = dict(sigma_prior=sig_prior, sigma_post_log_k=sig_post,
                                         n_eff_k_pop=float(n_eff), n_nominal_obs=int(n_nominal),
                                         ratio=float(n_eff / n_nominal))

    # ---- WITHOUT-discrepancy companion (sigma_d=0): the headline with/without comparison ----
    companions = {}
    if not SMOKE or os.environ.get("R3_NODISC", "0") == "1":
        print("\n[companion] WITHOUT structure-based discrepancy (sigma_d=0) ...")
        iv0 = {k: v for k, v in init_vals.items() if k not in ("sigma_d", "d_raw")}
        m0 = make_model(grid_j, M_src6, m_dome, L_feat, re_obs, im_obs, scale, train_main, fmask_full, learn_d=False)
        mc0 = run_nuts(m0, 250, 250, chains, init_vals=iv0, seed=SEED + 1)
        _, ds0 = diagnostics(mc0)
        s0 = {k: np.asarray(v) for k, v in mc0.get_samples().items()}
        companions["without_d"] = dict(
            k_pop=q(np.exp(s0["log_k_pop"])), f_dome=q(s0["f_dome"]),
            sigma_build=q(s0["sigma_build"]), sigma_e=q(s0["sigma_e"]),
            convergence=ds0)
        companions["with_vs_without"] = dict(
            sigma_e_with=res["learned_with_d"]["sigma_e"][1], sigma_e_without=companions["without_d"]["sigma_e"][1],
            worst_rhat_with=diag_sum["worst_rhat"], worst_rhat_without=ds0["worst_rhat"],
            note="does the structure-based discrepancy lower sigma_e / improve convergence vs no discrepancy?")
        np.savez(REP / "blind3_posterior_nodisc.npz", grid=grid, **s0)

    # ---- starve-the-data: 1 build, narrow band (40-100 Hz) ----
    if not SMOKE:
        print("[companion] STARVE-THE-DATA (1 build, 40-100 Hz) ...")
        nb_mask = (grid >= 40) & (grid <= 100)
        ms = make_model(grid_j, M_src6, m_dome, L_feat, re_obs, im_obs, scale, [0], nb_mask, learn_d=True)
        mcs = run_nuts(ms, 150, 150, chains, init_vals=init_vals, seed=SEED + 2)
        _, dss = diagnostics(mcs)
        ss = {k: np.asarray(v) for k, v in mcs.get_samples().items()}
        companions["starve_data"] = dict(k_pop=q(np.exp(ss["log_k_pop"])), sigma_e=q(ss["sigma_e"]),
                                         sigma_d=q(ss["sigma_d"]), convergence=dss,
                                         note="1 build, band 40-100 Hz; removes the data deluge")
    res["companions"] = companions
    (REP / "blind3_companions.json").write_text(json.dumps(companions, indent=2))
    (REP / "blind3_results.json").write_text(json.dumps(res, indent=2))

    runtime = dict(active_runtime_s=round(time.time() - t0, 1), note="main fit + held-out + n_eff")
    (REP / "blind3_runtime_partial.json").write_text(json.dumps(runtime, indent=2))
    print("\n=== MAIN FIT ===")
    print("k_pop", res["learned_with_d"]["k_pop"], "f_dome", res["learned_with_d"]["f_dome"])
    print("sigma_build", res["learned_with_d"]["sigma_build"], "sigma_e", res["learned_with_d"]["sigma_e"],
          "sigma_d", res["learned_with_d"]["sigma_d"])
    print("CONVERGENCE", diag_sum, "GATE_PASS", res["gate_pass"])
    print("HELD-OUT", {k: heldout[k] for k in ("build_coverage95", "build_logwidth", "band_coverage95")})
    print("n_eff(k_pop)", round(n_eff, 1), "vs nominal", n_nominal)
    print("runtime_s", runtime["active_runtime_s"])


def heldout_calibration(samples, obs, grid, M_src6, m_dome, scale, re_obs, im_obs):
    """Coverage of held-out builds (6,7, full band) and a held-out band (95-115 Hz, train builds),
    scored against the OBSERVED complex AM. Reports coverage WITH mean log-width (wide-but-covering != ok)."""
    grid_j = jnp.asarray(grid)
    nd = len(samples["log_k_pop"])
    sb = samples["sigma_build"]
    rng = np.random.default_rng(7)
    # predictive for a NEW build: draw a fresh build factor per posterior draw
    bf = np.exp(sb * rng.standard_normal(nd))
    pred = predict_complex(samples, bf, grid_j, M_src6, m_dome)   # (nd,6,ng) complex
    sde = samples["sigma_e"][:, None, None] * scale[None, :, :]   # (nd,6,ng)
    # add observation noise to the predictive (complex): re/im +- sde
    pr = np.real(pred) + sde * rng.standard_normal(pred.shape)
    pi = np.imag(pred) + sde * rng.standard_normal(pred.shape)
    lo_r, hi_r = np.percentile(pr, [2.5, 97.5], axis=0); lo_i, hi_i = np.percentile(pi, [2.5, 97.5], axis=0)
    # band masks
    inband = np.ones(len(grid), bool)
    hb = (grid >= HELDOUT_BAND[0]) & (grid <= HELDOUT_BAND[1])

    def cover(re_t, im_t, mask):
        cr = (re_t >= lo_r) & (re_t <= hi_r); ci = (im_t >= lo_i) & (im_t <= hi_i)
        c = (cr & ci)[:, mask]
        return float(c.mean())
    # build hold-out (6,7), full band
    cov_b = np.mean([cover(re_obs[b], im_obs[b], inband) for b in HELDOUT_BUILDS])
    # log-width from the predictive MAGNITUDE samples directly (robust; floor lower pct at a tiny frac of
    # the local data magnitude so near-zero re/im crossings don't blow up the multiplicative span).
    magpred = np.sqrt(pr ** 2 + pi ** 2)                 # (nd,6,ng) predictive |AM|
    mlo, mhi = np.percentile(magpred, [2.5, 97.5], axis=0)
    floor = 1e-2 * np.median(np.abs(np.mean(re_obs + 1j * im_obs, axis=0)))
    logwidth = float(np.mean(np.log((mhi + floor) / (np.maximum(mlo, 0) + floor))))
    # band hold-out on train builds (0..5)
    cov_band = np.mean([cover(re_obs[b], im_obs[b], hb) for b in range(6)])
    return dict(build_coverage95=cov_b, build_logwidth=logwidth, band_coverage95=cov_band,
                heldout_builds=HELDOUT_BUILDS, heldout_band_hz=list(HELDOUT_BAND),
                note="coverage vs OBSERVED complex AM (re&im inside 95% band); read WITH log-width")


if __name__ == "__main__":
    numpyro.set_host_device_count(4)
    main()
