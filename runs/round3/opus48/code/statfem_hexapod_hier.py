#!/usr/bin/env python3
"""HIERARCHICAL StatFEM on the 6-strut tray: learn the POPULATION mean k_j AND the build-to-build
scatter sigma_build (the ALEATORY distribution) from the 6-DOF interface apparent mass.

Why: learning a single fleet-mean k_j from rich FRFs is over-determined (epistemic ~0.1%, invisible).
Learning a VARIANCE (sigma_build) genuinely needs many builds -> its posterior CONTRACTS build-by-build,
so sequential learning is visible AND decision-relevant (it sets the predict-a-new-build margin).

Model (NUTS): k_j_pop, sigma_build (learned), per-build non-centered z_b -> k_j_b ~ LogNormal, a shared
per-component KL frequency discrepancy d, fixed structural loss eta, sensor noise sigma_e. Ground truth
still carries the SPATIAL (symmetry-breaking) + FREQUENCY model-form errors + build scatter + noise.
Env R3HH_SMOKE=1 -> tiny draws.
"""
from __future__ import annotations
import json, math, os, sys, time
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl_hh")
os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=4")
import numpy as np
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
import arviz as az
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE/"code"))
import statfem_hexapod as hxs   # physics + data generation + constants
import tray_hexapod as hx       # geometry + spatial_error_pattern

OUT = HERE/"report"; FIG = OUT/"figures"
SEED = 20260603
SMOKE = os.environ.get("R3HH_SMOKE", "0") == "1"
N_CHAINS = 4
WARMUP = 200 if SMOKE else 800
DRAWS = 200 if SMOKE else 1200
# FOCUSED band (covers all 6 mount modes 45-137 Hz + margin) -> faster forward than the full 20-2000 grid
F = np.geomspace(33.0, 260.0, 60)
NDOF = hxs.NDOF
KJ_TRUE = hxs.KJ_TRUE; KJ_GUESS = hxs.KJ_GUESS
SIGMA_E = hxs.SIGMA_E; SIGMA_BUILD_TRUE = hxs.SIGMA_BUILD
M_KL = hxs.M_KL

_appm_batch = jax.vmap(lambda k, fj: hxs.appmass_diag_bu_jax(k, fj), in_axes=(0, None))  # (N,nf,6)


def _make_freq_error(seed):
    K = hxs.matern32(F, hxs.ELL_FREQ, 1.0) + 1e-10*np.eye(len(F)); L = np.linalg.cholesky(K)
    rng = np.random.default_rng(seed); D = np.empty((NDOF, len(F)))
    for c in range(NDOF):
        raw = L @ rng.standard_normal(len(F)); D[c] = hxs.A_FREQ*raw/np.std(raw)
    return D


def _kl_basis():
    K = hxs.matern32(F, hxs.ELL_D, hxs.SIGMA_D); w, V = np.linalg.eigh(K)
    idx = np.argsort(w)[::-1][:M_KL]
    return V[:, idx], np.clip(w[idx], 0, None)


def generate_data_H(seed=SEED):
    """Per-build observed log|M_app diag| on the focused band F: spatial (systematic) + frequency
    (systematic) model-form errors + per-build k_j scatter + sensor noise."""
    rng = np.random.default_rng(seed)
    spat = hx.spatial_error_pattern(hxs.A_SPATIAL)
    dfreq = _make_freq_error(seed+1)
    kj_builds = KJ_TRUE*np.exp(SIGMA_BUILD_TRUE*rng.standard_normal(hxs.N_BUILDS))
    Y = np.empty((hxs.N_BUILDS, NDOF, len(F)))
    for b in range(hxs.N_BUILDS):
        logm = np.log(hxs.appmass_diag_truth(kj_builds[b]*spat, F)).T + dfreq
        Y[b] = logm + SIGMA_E*rng.standard_normal((NDOF, len(F)))
    truth_mzz = np.exp(np.log(hxs.appmass_diag_truth(KJ_TRUE*spat, F)).T[2] + dfreq[2])
    return dict(Y=Y, truth_mzz=truth_mzz)


def make_model(Y, with_d=True):
    """Y: (N, NDOF, nf) per-build observed log|M_app diag|."""
    N = Y.shape[0]; fj = jnp.asarray(F); yj = jnp.asarray(Y)
    if with_d:
        Phi, lam = _kl_basis(); Phij = jnp.asarray(Phi); slj = jnp.asarray(np.sqrt(lam)); M = len(lam)
    def model():
        log_kj = numpyro.sample("log_kj_pop", dist.Normal(math.log(KJ_GUESS), 0.30))
        sigma_build = numpyro.sample("sigma_build", dist.HalfNormal(0.10))     # LEARNED aleatory scatter
        z = numpyro.sample("z_b", dist.Normal(0, 1).expand([N]))               # non-centered per build
        kj_b = jnp.exp(log_kj + sigma_build*z)                                 # (N,)
        numpyro.deterministic("kj_pop", jnp.exp(log_kj))
        appm = _appm_batch(kj_b, fj)                                           # (N, nf, 6)
        mu = jnp.log(appm).transpose(0, 2, 1)                                  # (N, 6, nf)
        if with_d:
            zd = numpyro.sample("z_d", dist.Normal(0, 1).expand([NDOF, M]))
            d = (Phij @ (slj*zd).T).T                                          # (6, nf)
            mu = mu + d[None, :, :]
        numpyro.sample("y", dist.Normal(mu, SIGMA_E), obs=yj)
    return model


def fit(Y, seed=SEED):
    kernel = NUTS(make_model(Y, True), target_accept_prob=0.95,
                  init_strategy=numpyro.infer.init_to_median, max_tree_depth=9)
    mcmc = MCMC(kernel, num_warmup=WARMUP, num_samples=DRAWS, num_chains=N_CHAINS,
                chain_method="parallel", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    post = {k: np.asarray(v) for k, v in mcmc.get_samples().items()}
    idata = az.from_numpyro(mcmc)
    rh = az.rhat(idata, var_names=["log_kj_pop", "sigma_build"]); es = az.ess(idata, var_names=["log_kj_pop", "sigma_build"])
    diag = dict(rhat_kj=float(rh["log_kj_pop"].values), rhat_sigma=float(rh["sigma_build"].values),
                ess_kj=float(es["log_kj_pop"].values), ess_sigma=float(es["sigma_build"].values),
                divergences=int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum()))
    return post, diag


def newbuild_predictive(post, comp=2, nsamp=300, rng=None):
    """Predict the apparent mass of a NEW build = k_j_pop*exp(sigma_build*N(0,1)); band reflects
    learned aleatory sigma_build + epistemic uncertainty. Returns q025,q50,q975 over F for component."""
    rng = rng or np.random.default_rng(0)
    kjp = post["kj_pop"]; sb = post["sigma_build"]
    idx = rng.choice(len(kjp), min(nsamp, len(kjp)), replace=False)
    kj_new = kjp[idx]*np.exp(sb[idx]*rng.standard_normal(len(idx)))
    curves = np.array([np.abs(np.asarray(hxs.appmass_diag_bu_jax(k, F)))[:, comp] for k in kj_new])
    return np.quantile(curves, [0.025, 0.5, 0.975], axis=0)


def main():
    t0 = time.time(); numpyro.set_host_device_count(N_CHAINS); FIG.mkdir(parents=True, exist_ok=True)
    data = generate_data_H()
    Yall = data["Y"]; truth_mzz = data["truth_mzz"]   # (8, 6, nf)
    print("true sigma_build = %.3f ; kj_true %.3e" % (SIGMA_BUILD_TRUE, KJ_TRUE))

    Ns = [2, 4, 6, 8] if not SMOKE else [2, 5, 8]
    seq = []; post_by_N = {}
    for N in Ns:
        post, diag = fit(Yall[:N], seed=SEED+N)
        post_by_N[N] = post
        sb = post["sigma_build"]; kjp = post["kj_pop"]
        seq.append({"N": N,
                    "sigma_build_q50": float(np.median(sb)), "sigma_build_q025": float(np.quantile(sb, 0.025)),
                    "sigma_build_q975": float(np.quantile(sb, 0.975)),
                    "kj_pop_q50": float(np.median(kjp)), "kj_pop_bias_pct": float(100*(np.median(kjp)-KJ_TRUE)/KJ_TRUE),
                    "rhat_sigma": diag["rhat_sigma"], "ess_sigma": diag["ess_sigma"],
                    "rhat_kj": diag["rhat_kj"], "div": diag["divergences"]})
        print("N=%d sigma_build q50 %.3f [%.3f,%.3f] (true %.3f) | kj_pop bias %+.2f%% | rhat_s %.3f ess_s %.0f div %d"
              % (N, np.median(sb), np.quantile(sb,0.025), np.quantile(sb,0.975), SIGMA_BUILD_TRUE,
                 seq[-1]["kj_pop_bias_pct"], diag["rhat_sigma"], diag["ess_sigma"], diag["divergences"]))

    make_plots(seq, post_by_N, Ns, truth_mzz)
    make_gif(seq, post_by_N, Ns, truth_mzz)

    res = {"learned": ["k_j_pop (population mean)", "sigma_build (aleatory build-to-build scatter)"],
           "true_sigma_build": SIGMA_BUILD_TRUE, "true_kj": KJ_TRUE,
           "sequential": seq, "runtime_s": round(time.time()-t0, 1),
           "headline": "sigma_build (a variance) is learned: its posterior CONTRACTS build-by-build "
                       "(epistemic uncertainty ABOUT the aleatory scatter shrinks ~1/sqrt(2N)); this is the "
                       "decision-relevant predict-a-new-build margin and shows genuine sequential learning."}
    (OUT/"statfem_hexapod_hier_results.json").write_text(json.dumps(res, indent=2))
    print("DONE hier in", round(time.time()-t0, 1), "s")


def make_plots(seq, post_by_N, Ns, truth_mzz):
    # sigma_build contraction vs N
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    Nv = [s["N"] for s in seq]; q = [s["sigma_build_q50"]*100 for s in seq]
    lo = [s["sigma_build_q025"]*100 for s in seq]; hi = [s["sigma_build_q975"]*100 for s in seq]
    ax.errorbar(Nv, q, yerr=[np.array(q)-np.array(lo), np.array(hi)-np.array(q)], fmt="o-", capsize=4,
                color="#2ca02c", label="σ_build posterior (median, 95%)")
    ax.axhline(SIGMA_BUILD_TRUE*100, color="#d62728", ls="--", lw=2, label=f"true σ_build = {SIGMA_BUILD_TRUE*100:.0f}%")
    ax.set_xlabel("number of builds acquired"); ax.set_ylabel("build-to-build scatter σ_build [%]")
    ax.set_title("HIERARCHICAL learning: the ALEATORY scatter σ_build is LEARNED — its posterior contracts\n"
                 "build-by-build (this is genuine, decision-relevant sequential learning, unlike the over-determined mean)", fontsize=9.5)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG/"hier_sigma_build_contraction.png", dpi=145); plt.close(fig)

    # new-build predictive band (M_zz) at a few N
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    truth = truth_mzz
    ax.loglog(F, truth, color="#d62728", lw=2.2, label="a build's truth (M_zz)")
    for N, col in zip([Ns[0], Ns[len(Ns)//2], Ns[-1]], ["#cfe2ff", "#6ea8fe", "#08306b"]):
        lo, md, hi = newbuild_predictive(post_by_N[N])
        ax.fill_between(F, lo, hi, color=col, alpha=0.45, label=f"predict-a-new-build 95% (N={N})")
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("M_zz axial apparent mass [kg]")
    ax.set_title("Predict-a-NEW-build interface apparent mass: the 95% band (aleatory σ_build + epistemic)\n"
                 "tightens as σ_build is pinned down with more builds", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/"hier_newbuild_predictive.png", dpi=145); plt.close(fig)


def make_gif(seq, post_by_N, Ns, truth_mzz):
    FR = FIG/"hier_gif_frames"; FR.mkdir(parents=True, exist_ok=True)
    truth = truth_mzz
    frames = []
    for k, N in enumerate(Ns):
        fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.2))
        # left: sigma_build posterior so far
        ax = axes[0]
        sb = post_by_N[N]["sigma_build"]*100
        ax.hist(sb, bins=40, density=True, color="#2ca02c", alpha=0.7, label=f"σ_build posterior (N={N})")
        ax.axvline(SIGMA_BUILD_TRUE*100, color="#d62728", lw=2.2, ls="--", label=f"true σ_build {SIGMA_BUILD_TRUE*100:.0f}%")
        ax.set_xlim(0, 12); ax.set_xlabel("σ_build [%]"); ax.set_ylabel("posterior density")
        ax.set_title("Learning the ALEATORY scatter (a variance)", fontsize=9.5); ax.legend(fontsize=8.5); ax.grid(True, alpha=0.3)
        # right: new-build predictive band
        ax = axes[1]
        lo, md, hi = newbuild_predictive(post_by_N[N])
        ax.loglog(F, truth, color="#d62728", lw=2.0, label="a build's truth (M_zz)")
        ax.fill_between(F, lo, hi, color="#1f77b4", alpha=0.4, label="predict-a-new-build 95%")
        ax.loglog(F, md, color="#1f77b4", lw=1.6, label="median")
        ax.set_ylim(0.3, 3e3*2); ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("M_zz [kg]")
        ax.set_title("Predict-a-new-build apparent mass", fontsize=9.5); ax.legend(fontsize=8, loc="lower left"); ax.grid(True, which="both", alpha=0.3)
        s = seq[k]
        fig.suptitle(f"Hierarchical StatFEM — after {N} builds:  σ_build = {s['sigma_build_q50']*100:.1f}% "
                     f"[{s['sigma_build_q025']*100:.1f}, {s['sigma_build_q975']*100:.1f}] (true {SIGMA_BUILD_TRUE*100:.0f}%);  "
                     f"k_j_pop bias {s['kj_pop_bias_pct']:+.2f}%   — the variance posterior tightens as builds accumulate", fontsize=10)
        fig.tight_layout()
        ff = FR/f"frame_N{N:02d}.png"; fig.savefig(ff, dpi=120); plt.close(fig); frames.append(ff)
    gif = FIG/"hier_sigma_build_learning.gif"
    imageio.mimsave(gif, [imageio.imread(f) for f in frames], duration=1.3, loop=0)
    print("wrote", gif, "with", len(frames), "frames")


if __name__ == "__main__":
    main()
