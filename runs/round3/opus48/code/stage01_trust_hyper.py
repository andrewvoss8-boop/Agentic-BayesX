#!/usr/bin/env python3
"""Stage 0 + Stage 1 (master_plan.md): trust harness + learn ALL hyperparameters.

- INDEPENDENT truth (fixes the D10 over-convenience): spatial per-strut error + a FREQUENCY model-form
  error built from Gaussian BUMPS (NOT the Matern family the inference discrepancy uses) + build scatter +
  sensor noise. So the discrepancy model is itself mildly misspecified -> honest test.
- Learn ALL hyperparameters: k_j_pop, sigma_build (hierarchical, aleatory), and the discrepancy size
  sigma_d AND length-scale ell_d (via a Hilbert-space reduced-rank GP so ell_d is differentiable with a
  FIXED basis), and sensor noise sigma_e. Nothing fixed by hand.
- TRUST HARNESS (the primary concern): held-out calibration (leave out whole BUILDS and a whole FREQUENCY
  BAND -> 95% predictive coverage), effective-vs-nominal independent-sample count, with- vs
  without-discrepancy, and a starve-the-data check. Frequency grid is the adaptive grid (fixed during
  inference), built from the solved mount modes.

Observed channel: 6-DOF interface apparent mass of the 6-strut hexapod tray. Sampler: NumPyro NUTS over
ALL latents (incl. GP coefficients + hierarchical per-build latents). Env R3S01_SMOKE=1 -> tiny draws.
"""
from __future__ import annotations
import os, sys, math, json, time
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl_s01")
os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=4")
import numpy as np
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS, init_to_value
import arviz as az
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE/"code"))
import statfem_hexapod as hxs
import tray_hexapod as hx
from adaptive_freq import adaptive_frequency_grid, points_in_halfpower_bands

OUT = HERE/"report"; FIG = OUT/"figures"
SEED = 20260604
SMOKE = os.environ.get("R3S01_SMOKE", "0") == "1"
N_CHAINS = 4
WARMUP = 200 if SMOKE else 800
DRAWS = 200 if SMOKE else 800
NDOF = 6
KJ_TRUE = hxs.KJ_TRUE; KJ_GUESS = hxs.KJ_GUESS
SIGMA_BUILD_TRUE = 0.05; SIGMA_E_TRUE = 0.08; A_SPATIAL = 0.20
N_BUILDS = 6
M_HSGP = 8

# Adaptive grid from the SOLVED mount modes (fixed during inference). Modest density -> tractable NUTS.
_kj0, _ = hx.calibrate_kj(86.25)
MOUNT_MODES = hx.modes(np.full(6, _kj0))
F = adaptive_frequency_grid(MOUNT_MODES, np.full(len(MOUNT_MODES), 0.04), 25.0, 400.0,
                            base_per_decade=8, pts_per_mode=9, n_halfwidths=6)
NF = len(F)


# ---------- Hilbert-space reduced-rank GP basis (lets us LEARN ell_d, sigma_d with a fixed basis) ----------
def hsgp_basis(freqs, M):
    u = np.log(freqs); umid = 0.5*(u.min()+u.max()); uhalf = 0.5*(u.max()-u.min())
    un = (u-umid)/uhalf                       # normalized log-frequency in [-1,1]
    L = 1.4                                    # domain half-length (with boundary margin)
    j = np.arange(1, M+1)
    omega = np.pi*j/(2*L)                      # sqrt eigenvalues
    Phi = np.sin(np.outer(un+L, omega))/np.sqrt(L)   # (nf, M)
    return Phi, omega
PHI, OMEGA = hsgp_basis(F, M_HSGP)
PHIj = jnp.asarray(PHI); OMEGAj = jnp.asarray(OMEGA)


def matern32_sdens(omega, sigma, ell):
    """Matern-3/2 1-D spectral density (up to a constant folded into sigma); ell in normalized-u units."""
    return (sigma**2) * (1.0/ell**3) / (3.0/ell**2 + omega**2)**2


# ---------- independent truth ----------
def freq_bumps(seed):
    """FREQUENCY model-form error as Gaussian bumps in log-freq (NOT Matern -> independent of inference d)."""
    rng = np.random.default_rng(seed); u = np.log(F); D = np.zeros((NDOF, NF))
    for c in range(NDOF):
        for _ in range(2):
            c0 = rng.uniform(u.min(), u.max()); w = rng.uniform(0.15, 0.45); a = rng.uniform(-0.18, 0.18)
            D[c] += a*np.exp(-0.5*((u-c0)/w)**2)
    return D


def gen_truth(seed=SEED, n_builds=N_BUILDS):
    rng = np.random.default_rng(seed); spat = hx.spatial_error_pattern(A_SPATIAL)
    dfreq = freq_bumps(seed+1)
    kjb = KJ_TRUE*np.exp(SIGMA_BUILD_TRUE*rng.standard_normal(n_builds))
    Y = np.empty((n_builds, NDOF, NF))
    for b in range(n_builds):
        Y[b] = np.log(hxs.appmass_diag_truth(kjb[b]*spat, F)).T + dfreq + SIGMA_E_TRUE*rng.standard_normal((NDOF, NF))
    return dict(Y=Y, kjb=kjb, dfreq=dfreq, spat=spat)


_appm_batch = jax.vmap(lambda k: hxs.appmass_diag_bu_jax(k, jnp.asarray(F)), in_axes=0)   # (B,nf,6)


def make_model(Y, with_d=True, learn_sigma_e=True, freq_mask=None):
    B = Y.shape[0]; yj = jnp.asarray(Y)                        # (B,6,nf)
    mask = jnp.asarray(np.ones(NF) if freq_mask is None else freq_mask.astype(float))  # 1=use,0=hold-out
    def model():
        log_kj = numpyro.sample("log_kj_pop", dist.Normal(math.log(KJ_GUESS), 0.30))
        numpyro.deterministic("kj_pop", jnp.exp(log_kj))
        sigma_build = numpyro.sample("sigma_build", dist.HalfNormal(0.10))
        z = numpyro.sample("z_b", dist.Normal(0, 1).expand([B]))
        kj_b = jnp.exp(log_kj + sigma_build*z)
        sigma_e = numpyro.sample("sigma_e", dist.HalfNormal(0.15)) if learn_sigma_e else 0.08
        appm = _appm_batch(kj_b)                               # (B,nf,6)
        mu = jnp.log(appm).transpose(0, 2, 1)                  # (B,6,nf)
        if with_d:
            sigma_d = numpyro.sample("sigma_d", dist.HalfNormal(0.20))
            # INFORMATIVE length-scale prior (R5 guard): keep ell_d in a physically-sensible band so it
            # cannot collapse to noise-like tiny scales (which re-opens over-counting). Lower-bounded.
            ell_raw = numpyro.sample("ell_d", dist.LogNormal(math.log(0.45), 0.30))
            ell_d = numpyro.deterministic("ell_d_eff", 0.20 + ell_raw)  # lower-bounded ~0.2 (norm-u)
            sd = jnp.sqrt(matern32_sdens(OMEGAj, sigma_d, ell_d))     # (M,)
            beta = numpyro.sample("beta", dist.Normal(0, 1).expand([NDOF, M_HSGP]))
            d = (PHIj @ (sd*beta).T).T                          # (6,nf)
            mu = mu + d[None, :, :]
        numpyro.sample("y", dist.Normal(mu, sigma_e), obs=yj, obs_mask=jnp.broadcast_to(mask, yj.shape) > 0.5)
    return model


def run(Y, with_d=True, learn_sigma_e=True, freq_mask=None, seed=SEED):
    model = make_model(Y, with_d, learn_sigma_e, freq_mask)
    kernel = NUTS(model, target_accept_prob=0.95, max_tree_depth=10,
                  init_strategy=init_to_value(values={"log_kj_pop": math.log(KJ_GUESS)}))
    mc = MCMC(kernel, num_warmup=WARMUP, num_samples=DRAWS, num_chains=N_CHAINS,
              chain_method="parallel", progress_bar=False)
    mc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    post = {k: np.asarray(v) for k, v in mc.get_samples().items()}
    names = [n for n in ["log_kj_pop", "sigma_build", "sigma_e", "sigma_d", "ell_d"] if n in post]
    idata = az.from_numpyro(mc)
    rh = az.rhat(idata, var_names=names); es = az.ess(idata, var_names=names)
    diag = {"worst_rhat": float(max(float(rh[n].values) for n in names)),
            "min_ess": float(min(float(es[n].values) for n in names)),
            "divergences": int(np.asarray(mc.get_extra_fields()["diverging"]).sum())}
    return post, diag


def predict_mean_curves(post, kj_new=None, n=200, rng=None):
    """Posterior predictive mu = log appm(kj) + d for a NEW build (kj_new sampled from population) or for
    the in-sample population mean. Returns samples (n, 6, nf) of mu, plus sigma_e samples."""
    rng = rng or np.random.default_rng(0)
    S = post["kj_pop"].shape[0]; idx = rng.choice(S, min(n, S), replace=False)
    kjp = post["kj_pop"][idx]; sb = post.get("sigma_build", np.zeros(S))[idx]
    se = post.get("sigma_e", np.full(S, 0.08))[idx]
    out = np.empty((len(idx), NDOF, NF))
    has_d = "beta" in post
    for i, j in enumerate(idx):
        kj = kjp[i]*math.exp(sb[i]*rng.standard_normal())     # a NEW build draw
        appm = np.log(np.abs(np.asarray(hxs.appmass_diag_bu_jax(kj, jnp.asarray(F))))).T  # (6,nf)
        if has_d:
            sd = np.sqrt(np.asarray(matern32_sdens(OMEGA, post["sigma_d"][idx[i]], post["ell_d_eff"][idx[i]])))
            d = (PHI @ (sd[None, :]*post["beta"][idx[i]]).T).T
            appm = appm + d
        out[i] = appm
    return out, se


def coverage(post, Y_heldout, freq_idx=None, rng=None):
    """95% predictive coverage of held-out observations (new builds, or held-out freq band of train builds)."""
    rng = rng or np.random.default_rng(1)
    mu, se = predict_mean_curves(post, n=300, rng=rng)        # (n,6,nf)
    # predictive draws = mu + N(0, sigma_e); pool sigma_e by sampling
    nsamp = mu.shape[0]
    sef = se[:, None, None]
    draws = mu + sef*rng.standard_normal(mu.shape)
    lo = np.quantile(draws, 0.025, axis=0); hi = np.quantile(draws, 0.975, axis=0)   # (6,nf)
    fmask = np.ones(NF, bool) if freq_idx is None else freq_idx
    covs = []
    for b in range(Y_heldout.shape[0]):
        obs = Y_heldout[b][:, fmask]; L = lo[:, fmask]; H = hi[:, fmask]
        covs.append(float(np.mean((obs >= L) & (obs <= H))))
    return float(np.mean(covs)), covs


def main():
    t0 = time.time(); numpyro.set_host_device_count(N_CHAINS); FIG.mkdir(parents=True, exist_ok=True)
    print("grid points NF=%d  modes=%s  pts in half-power bands=%s" %
          (NF, np.round(np.unique(np.round(MOUNT_MODES, 1)), 1).tolist(),
           points_in_halfpower_bands(F, MOUNT_MODES, 0.04)))
    truth = gen_truth(); Y = truth["Y"]
    Btrain = N_BUILDS - 2                                     # hold out last 2 builds
    band = (F > 70.0) & (F < 100.0)                          # hold out a frequency band (around 86 Hz)
    train_fmask = ~band

    # ---- WITH discrepancy, learn all hyperparameters, on training builds + training band ----
    post, diag = run(Y[:Btrain], with_d=True, learn_sigma_e=True, freq_mask=train_fmask, seed=SEED+1)
    # ---- WITHOUT discrepancy (same data) ----
    post_nd, diag_nd = run(Y[:Btrain], with_d=False, learn_sigma_e=True, freq_mask=train_fmask, seed=SEED+2)
    # ---- starve the data: 1 build, with d ----
    post_st, diag_st = run(Y[:1], with_d=True, learn_sigma_e=True, freq_mask=train_fmask, seed=SEED+3)

    def summ(p):
        kj = p["kj_pop"]
        return dict(kj_q50=float(np.median(kj)), kj_sd=float(np.std(kj)),
                    kj_bias_pct=float(100*(np.median(kj)-KJ_TRUE)/KJ_TRUE),
                    kj_95=[float(np.quantile(kj, .025)), float(np.quantile(kj, .975))],
                    covers_truth=bool(np.quantile(kj, .025) <= KJ_TRUE <= np.quantile(kj, .975)))
    # held-out coverage: (a) new builds (the 2 held out), full freq; (b) held-out band on train builds
    cov_newbuilds, _ = coverage(post, Y[Btrain:], freq_idx=None, rng=np.random.default_rng(10))
    cov_band_train, _ = coverage(post, Y[:Btrain], freq_idx=band, rng=np.random.default_rng(11))
    cov_nb_nd, _ = coverage(post_nd, Y[Btrain:], freq_idx=None, rng=np.random.default_rng(12))
    cov_band_nd, _ = coverage(post_nd, Y[:Btrain], freq_idx=band, rng=np.random.default_rng(13))

    # effective vs nominal sample count for k_j_pop (Gaussian information-gain proxy)
    sigma_prior = 0.30
    n_eff = float((sigma_prior/np.std(np.log(post["kj_pop"])))**2)
    nominal = int(Btrain*NDOF*train_fmask.sum())

    results = {
        "stage": "0+1 trust harness + learn all hyperparameters",
        "grid": {"n_points": NF, "band_hz": [25, 400], "adaptive": True,
                 "min_pts_in_halfpower": int(min(points_in_halfpower_bands(F, MOUNT_MODES, 0.04).values()))},
        "learned_hyperparameters_with_d": {
            "kj_pop": summ(post), "sigma_build_q50": float(np.median(post["sigma_build"])),
            "sigma_build_true": SIGMA_BUILD_TRUE,
            "sigma_e_q50": float(np.median(post["sigma_e"])), "sigma_e_true": SIGMA_E_TRUE,
            "sigma_d_q50": float(np.median(post["sigma_d"])),
            "ell_d_q50_normu": float(np.median(post["ell_d_eff"]))},
        "without_discrepancy": {"kj_pop": summ(post_nd)},
        "starve_1build": {"kj_pop": summ(post_st)},
        "HELD_OUT_CALIBRATION_95": {
            "with_d_new_builds_coverage": cov_newbuilds, "with_d_heldout_band_coverage": cov_band_train,
            "without_d_new_builds_coverage": cov_nb_nd, "without_d_heldout_band_coverage": cov_band_nd,
            "note": "target ~0.95; with_d should be near 0.95 and beat without_d (which collapses onto bias)."},
        "effective_vs_nominal": {"n_eff_kj": n_eff, "nominal_points": nominal,
                                 "ratio": n_eff/max(nominal, 1),
                                 "note": "n_eff << nominal => correlated model error; tightness is not from "
                                         "independent data. n_eff ~ (sigma_prior/sigma_post)^2."},
        "convergence": {"with_d": diag, "without_d": diag_nd, "starve": diag_st},
        "independent_truth": "spatial per-strut error + Gaussian-bump frequency error (NON-Matern) + build "
                             "scatter + sensor noise; inference discrepancy is Matern HSGP -> mildly "
                             "misspecified (honest).",
        "runtime_s": round(time.time()-t0, 1)}
    (OUT/"stage01_results.json").write_text(json.dumps(results, indent=2))

    make_plots(post, post_nd, truth, band, Btrain, results)
    print(json.dumps({k: results[k] for k in ("HELD_OUT_CALIBRATION_95", "effective_vs_nominal")}, indent=2))
    print("kj bias with_d %.2f%% (covers %s) | without_d %.2f%% (covers %s) | starve %.2f%%" %
          (summ(post)["kj_bias_pct"], summ(post)["covers_truth"], summ(post_nd)["kj_bias_pct"],
           summ(post_nd)["covers_truth"], summ(post_st)["kj_bias_pct"]))
    print("learned: sigma_build %.3f (true %.3f) sigma_e %.3f (true %.3f) sigma_d %.3f ell_d %.3f | conv %s"
          % (np.median(post["sigma_build"]), SIGMA_BUILD_TRUE, np.median(post["sigma_e"]), SIGMA_E_TRUE,
             np.median(post["sigma_d"]), np.median(post["ell_d_eff"]), diag))
    print("DONE stage01 in", round(time.time()-t0, 1), "s")


def make_plots(post, post_nd, truth, band, Btrain, results):
    # hyperparameter posteriors
    fig, axes = plt.subplots(1, 4, figsize=(16, 4.0))
    for ax, (key, true, lbl) in zip(axes, [("sigma_build", SIGMA_BUILD_TRUE, "σ_build (build scatter)"),
                                           ("sigma_e", SIGMA_E_TRUE, "σ_e (sensor noise)"),
                                           ("sigma_d", None, "σ_d (discrepancy size)"),
                                           ("ell_d_eff", None, "ℓ_d (discrepancy length, norm-u)")]):
        ax.hist(post[key], bins=40, density=True, color="#1f77b4", alpha=0.75)
        if true is not None: ax.axvline(true, color="#d62728", lw=2, ls="--", label=f"true {true}")
        ax.set_title(lbl, fontsize=9.5); ax.legend(fontsize=8); ax.grid(True, alpha=0.3)
    fig.suptitle("Stage 1: ALL hyperparameters LEARNED (none fixed)", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG/"stage01_hyperparameters.png", dpi=140); plt.close(fig)

    # held-out calibration: predictive band vs held-out new build (M_zz) + the held-out frequency band
    mu, se = predict_mean_curves(post, n=300, rng=np.random.default_rng(20))
    lo = np.quantile(mu + se[:, None, None]*np.random.default_rng(21).standard_normal(mu.shape), 0.025, axis=0)
    hi = np.quantile(mu + se[:, None, None]*np.random.default_rng(22).standard_normal(mu.shape), 0.975, axis=0)
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    c = 2
    ax.fill_between(F, np.exp(lo[c]), np.exp(hi[c]), color="#1f77b4", alpha=0.3, label="95% predictive (new build)")
    ax.loglog(F, np.exp(np.median(mu, axis=0)[c]), color="#1f77b4", lw=1.6, label="predictive median")
    ax.loglog(F, np.exp(truth["Y"][Btrain][c]), color="#d62728", lw=1.8, ls="--", label="HELD-OUT new build (truth)")
    ax.axvspan(F[band].min(), F[band].max(), color="orange", alpha=0.15, label="held-out frequency band")
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("M_zz apparent mass [kg]")
    ax.set_title(f"Held-out calibration (M_zz): with-d new-build coverage "
                 f"{results['HELD_OUT_CALIBRATION_95']['with_d_new_builds_coverage']:.2f}, held-out-band "
                 f"{results['HELD_OUT_CALIBRATION_95']['with_d_heldout_band_coverage']:.2f} "
                 f"(target 0.95); without-d {results['HELD_OUT_CALIBRATION_95']['without_d_new_builds_coverage']:.2f}", fontsize=9.0)
    ax.grid(True, which="both", alpha=0.25); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/"stage01_heldout_calibration.png", dpi=145); plt.close(fig)


if __name__ == "__main__":
    main()
