#!/usr/bin/env python3
"""StatFEM on the 6-strut hexapod tray: learn ONE k_j from the 6-DOF interface apparent mass, under a
SPATIAL (symmetry-breaking, in-the-physics) model-form error + a FREQUENCY (output GP) model-form error,
with build-to-build and sensor noise. Headline = SEQUENTIAL learning: k_j and the predictive FRF move
toward truth and uncertainty shrinks as more builds are acquired; a residual bias persists because the
spatial model-form error is OUTSIDE the single-k_j span (and is partly caught by the discrepancy).

NUTS samples log_kj (the ONE physical parameter) + a per-component low-rank (KL) frequency discrepancy
d(w). Damping is a FIXED structural loss (eta) only to make FRFs finite (NOT a learned parameter).
Observed channel = the 6 DIAGONAL components of the interface apparent mass M_app(w) over 20-2000 Hz.
Units SI. Env R3HX_SMOKE=1 -> tiny draws.
"""
from __future__ import annotations
import json, math, os, sys, time
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl_hx")
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
import tray_hexapod as hx

OUT = HERE/"report"; FIG = OUT/"figures"
SEED = 20260603
SMOKE = os.environ.get("R3HX_SMOKE", "0") == "1"
N_CHAINS = 4
WARMUP = 150 if SMOKE else 700
DRAWS = 200 if SMOKE else 900

# physics
KTT_U, KTB_U, KBB_U = hx.assemble(np.ones(6))     # unit-stiffness (per-strut=1) condensation blocks
M_MAT = hx.M_MAT
ETA = 0.04                                          # fixed structural loss (finite FRF peaks; NOT learned)
KJ_TRUE, IZ = hx.calibrate_kj(86.25)
KJ_GUESS = KJ_TRUE*1.25
PRIOR_LOG_SD = 0.30

# baked-in ground-truth assumptions
A_SPATIAL = 0.20      # spatial (per-strut) model-form error amplitude (systematic, symmetry-breaking)
A_FREQ = 0.10         # frequency output model-form error sd (log), per component
ELL_FREQ = 0.40
SIGMA_E = 0.08        # sensor noise sd (log) ~ 0.7 dB amplitude (more realistic)
SIGMA_BUILD = 0.04    # build-to-build k_j lognormal sd (4%)
N_BUILDS = 8

# discrepancy GP (BU model's frequency d) -- low-rank KL, per component
SIGMA_D = 0.10; ELL_D = 0.40; M_KL = 6
NDOF = 6
F = np.geomspace(20.0, 2000.0, 140)
LN10 = math.log(10.0)


def _appmass_diag(Ktt, Ktb, Kbb, freqs):
    """Diagonal of the interface apparent mass over freqs (numpy, complex-stiffness)."""
    Ktt = Ktt*(1+1j*ETA); Ktb = Ktb*(1+1j*ETA); Kbb = Kbb*(1+1j*ETA)
    w = 2*np.pi*freqs; out = np.empty((len(freqs), NDOF))
    for j, wj in enumerate(w):
        D = Ktt - (wj**2)*M_MAT
        Zb = Kbb - Ktb.T @ np.linalg.solve(D, Ktb)
        out[j] = np.abs(np.diag(-Zb/(wj**2)))
    return out                                       # (nf, 6)


def appmass_diag_truth(k_struts, freqs):
    Ktt, Ktb, Kbb = hx.assemble(k_struts)
    return _appmass_diag(Ktt, Ktb, Kbb, freqs)


def appmass_diag_bu_jax(kj, freqs):
    """JAX, differentiable in kj: uniform struts -> blocks scale linearly with kj."""
    w = 2*jnp.pi*freqs
    s = kj*(1+1j*ETA)
    Ktt = s*jnp.asarray(KTT_U); Ktb = s*jnp.asarray(KTB_U); Kbb = s*jnp.asarray(KBB_U)
    Mm = jnp.asarray(M_MAT)
    def one(wj):
        D = Ktt - (wj**2)*Mm
        Zb = Kbb - Ktb.T @ jnp.linalg.solve(D, Ktb)
        return jnp.abs(jnp.diag(-Zb/(wj**2)))
    return jax.vmap(one)(w)                          # (nf, 6)


def matern32(freqs, ell, sigma):
    eta = np.log(freqs); r = np.abs(np.subtract.outer(eta, eta))/ell
    s = math.sqrt(3.0)*r
    return (sigma**2)*(1+s)*np.exp(-s)


def kl_basis(sigma_d=SIGMA_D, ell_d=ELL_D, M=M_KL):
    K = matern32(F, ell_d, sigma_d); w, V = np.linalg.eigh(K)
    idx = np.argsort(w)[::-1][:M]
    return V[:, idx], np.clip(w[idx], 0, None)


def make_freq_error(seed):
    """Per-component smooth frequency output error (independent GP draws)."""
    K = matern32(F, ELL_FREQ, 1.0) + 1e-10*np.eye(len(F)); L = np.linalg.cholesky(K)
    rng = np.random.default_rng(seed); D = np.empty((NDOF, len(F)))
    for c in range(NDOF):
        raw = L @ rng.standard_normal(len(F)); D[c] = A_FREQ*raw/np.std(raw)
    return D


def generate_data(a_spatial=A_SPATIAL, seed=SEED):
    """Per-build observed log|M_app diag| (NDOF x nf). Truth = spatial-error struts (systematic) +
    per-component frequency error (systematic) + per-build k_j scatter + sensor noise."""
    rng = np.random.default_rng(seed)
    spat = hx.spatial_error_pattern(a_spatial)            # shared systematic azimuthal pattern
    dfreq = make_freq_error(seed+1)                       # shared systematic frequency error (NDOF,nf)
    kj_builds = KJ_TRUE*np.exp(SIGMA_BUILD*rng.standard_normal(N_BUILDS))
    Y = np.empty((N_BUILDS, NDOF, len(F)))
    for b in range(N_BUILDS):
        truth = appmass_diag_truth(kj_builds[b]*spat, F)  # (nf,6)
        logm = np.log(truth).T + dfreq                    # (6,nf): structure(spatial) + freq error
        Y[b] = logm + SIGMA_E*rng.standard_normal((NDOF, len(F)))
    clean_mean_truth = np.log(appmass_diag_truth(KJ_TRUE*spat, F)).T + dfreq
    bu_truth_kj = np.log(np.asarray(appmass_diag_bu_jax(KJ_TRUE, F))).T   # BU shape at true k_j (no errors)
    return dict(Y=Y, kj_builds=kj_builds, spat=spat, dfreq=dfreq,
                clean_mean_truth=clean_mean_truth, bu_truth_kj=bu_truth_kj)


def make_model(Ybar, n_builds, with_d=True):
    fj = jnp.asarray(F); yj = jnp.asarray(Ybar)         # (6, nf)
    sig = math.sqrt(SIGMA_E**2/max(n_builds, 1) + 1e-8)
    if with_d:
        Phi, lam = kl_basis(); Phij = jnp.asarray(Phi); slj = jnp.asarray(np.sqrt(lam)); M = len(lam)
    def model():
        log_kj = numpyro.sample("log_kj", dist.Normal(math.log(KJ_GUESS), PRIOR_LOG_SD))
        kj = jnp.exp(log_kj); numpyro.deterministic("kj", kj)
        mu = jnp.log(appmass_diag_bu_jax(kj, fj)).T      # (6, nf)
        if with_d:
            z = numpyro.sample("z_d", dist.Normal(0, 1).expand([NDOF, M]))
            d = (Phij @ (slj*z).T).T                     # (6, nf)
            mu = mu + d
        numpyro.sample("y", dist.Normal(mu, sig), obs=yj)
    return model


def fit(Ybar, n_builds, with_d=True, seed=SEED):
    kernel = NUTS(make_model(Ybar, n_builds, with_d), target_accept_prob=0.9,
                  init_strategy=numpyro.infer.init_to_median)
    mcmc = MCMC(kernel, num_warmup=WARMUP, num_samples=DRAWS, num_chains=N_CHAINS,
                chain_method="parallel", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    post = {k: np.asarray(v) for k, v in mcmc.get_samples().items()}
    idata = az.from_numpyro(mcmc)
    diag = dict(rank_split_rhat=float(az.rhat(idata, var_names=["log_kj"])["log_kj"].values),
                ess_bulk=float(az.ess(idata, var_names=["log_kj"], method="bulk")["log_kj"].values),
                divergences=int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum()))
    diag["converged"] = bool(diag["rank_split_rhat"] < 1.01 and diag["ess_bulk"] >= 400 and diag["divergences"] == 0)
    return post, diag


def main():
    t0 = time.time(); numpyro.set_host_device_count(N_CHAINS); FIG.mkdir(parents=True, exist_ok=True)
    print("KJ_TRUE %.3e  guess %.3e  axial mode idx %d" % (KJ_TRUE, KJ_GUESS, IZ))
    data = generate_data()

    # ---- SEQUENTIAL learning: fit with increasing #builds (every build -> smooth GIF) ----
    Ns = [1, 2, 3, 4, 5, 6, 7, 8] if not SMOKE else [1, 4, 8]
    seq = []
    post_by_N = {}
    for N in Ns:
        Ybar = data["Y"][:N].mean(axis=0)
        post, diag = fit(Ybar, N, with_d=True, seed=SEED+N)
        kj = post["kj"]; post_by_N[N] = post
        seq.append({"N_builds": N, "kj_q50": float(np.median(kj)),
                    "kj_q025": float(np.quantile(kj, 0.025)), "kj_q975": float(np.quantile(kj, 0.975)),
                    "kj_sd": float(np.std(kj)), "bias_pct": float(100*(np.median(kj)-KJ_TRUE)/KJ_TRUE),
                    "covers95": bool(np.quantile(kj, 0.025) <= KJ_TRUE <= np.quantile(kj, 0.975)),
                    "rhat": diag["rank_split_rhat"], "ess": diag["ess_bulk"], "div": diag["divergences"]})
        print("N=%d kj q50 %.3e bias %+.2f%% sd %.2e cov %s rhat %.3f ess %.0f"
              % (N, np.median(kj), seq[-1]["bias_pct"], np.std(kj), seq[-1]["covers95"], diag["rank_split_rhat"], diag["ess_bulk"]))

    # without discrepancy at full N (bias comparison)
    post_nd, diag_nd = fit(data["Y"][:N_BUILDS].mean(axis=0), N_BUILDS, with_d=False, seed=SEED+99)

    make_plots(data, seq, post_by_N, post_nd, Ns)
    make_gif(data, seq, post_by_N, Ns)

    res = {"setup": {"kj_true": KJ_TRUE, "kj_guess": KJ_GUESS, "n_dof_observed": NDOF, "band_hz": [20, 2000],
                     "learned": "single k_j", "eta_fixed": ETA, "n_struts": 6},
           "assumptions": {"a_spatial": A_SPATIAL, "a_freq": A_FREQ, "sigma_e": SIGMA_E,
                           "sigma_build": SIGMA_BUILD, "n_builds": N_BUILDS},
           "discrepancy": {"type": "per-component low-rank (KL) Matern frequency GP", "M_kl": M_KL,
                           "sigma_d": SIGMA_D, "ell_d": ELL_D},
           "sequential": seq,
           "full_N_without_discrepancy": {"kj_q50": float(np.median(post_nd["kj"])),
                                          "bias_pct": float(100*(np.median(post_nd["kj"])-KJ_TRUE)/KJ_TRUE),
                                          "covers95": bool(np.quantile(post_nd["kj"],0.025) <= KJ_TRUE <= np.quantile(post_nd["kj"],0.975))},
           "runtime_s": round(time.time()-t0, 1)}
    (OUT/"statfem_hexapod_results.json").write_text(json.dumps(res, indent=2))
    (OUT/"statfem_hexapod_nuts_diagnostics.json").write_text(json.dumps(
        {"sequential_with_d": [{k: s[k] for k in ("N_builds","rhat","ess","div")} for s in seq],
         "full_without_d": diag_nd}, indent=2))
    print("DONE statfem_hexapod in", round(time.time()-t0, 1), "s")


def make_plots(data, seq, post_by_N, post_nd, Ns):
    # ---- (1) sequential k_j contraction + bias vs N ----
    fig, ax = plt.subplots(figsize=(9.0, 5.2))
    Nv = [s["N_builds"] for s in seq]; q50 = [s["kj_q50"]/1e7 for s in seq]
    lo = [s["kj_q025"]/1e7 for s in seq]; hi = [s["kj_q975"]/1e7 for s in seq]
    ax.errorbar(Nv, q50, yerr=[np.array(q50)-np.array(lo), np.array(hi)-np.array(q50)], fmt="o-", capsize=4,
                color="#1f77b4", label="k_j posterior (median, 95%) WITH discrepancy")
    ax.axhline(KJ_TRUE/1e7, color="#d62728", ls="--", lw=2, label=f"truth k_j = {KJ_TRUE/1e7:.3f}e7")
    ax.axhline(KJ_GUESS/1e7, color="#999999", ls=":", label="coarse prior guess (+25%)")
    ax.scatter([N_BUILDS+0.3], [np.median(post_nd["kj"])/1e7], color="#ff7f0e", marker="s", s=70, zorder=5,
               label="WITHOUT discrepancy (N=8)")
    ax.set_xlabel("number of builds acquired"); ax.set_ylabel("interface stiffness k_j [×10⁷ N/m]")
    ax.set_title("SEQUENTIAL learning: k_j moves toward truth and uncertainty shrinks as builds accumulate\n"
                 "(residual bias persists — the SPATIAL model-form error is outside the single-k_j span)", fontsize=9.5)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG/"hexapod_sequential_kj.png", dpi=145); plt.close(fig)

    # ---- (2) predictive apparent mass approaching truth: axial M_zz and a splitting lateral M_xx ----
    comps = [(2, "M_zz axial (86 Hz mode)"), (0, "M_xx lateral (splitting pair)")]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))
    for ax, (c, lbl) in zip(axes, comps):
        ax.loglog(F, np.exp(data["clean_mean_truth"][c]), color="#d62728", lw=2.2, label="TRUTH (spatial+freq error)")
        for N, col in zip(Ns, ["#cfe2ff", "#9ec5fe", "#6ea8fe", "#1f77b4"][:len(Ns)]):
            kj = post_by_N[N]["kj"]; sub = kj[np.random.default_rng(N).choice(len(kj), min(120, len(kj)), replace=False)]
            curves = np.array([np.abs(np.asarray(appmass_diag_bu_jax(k, F)))[:, c] for k in sub])
            lo, hi = np.quantile(curves, [0.025, 0.975], axis=0)
            ax.fill_between(F, lo, hi, color=col, alpha=0.5, label=f"BU predictive N={N}")
        ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel(f"|{lbl.split()[0]}| [kg or kg·m²]")
        ax.set_title(lbl, fontsize=9.5); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=7.5)
    fig.suptitle("Predictive interface apparent mass → truth as builds accumulate (band shrinks); "
                 "single-k_j cannot match the SPLIT lateral modes (residual model-form error)", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG/"hexapod_predictive_frf.png", dpi=140); plt.close(fig)

    # ---- (3) epistemic (shrinks) vs aleatory (constant) uncertainty vs N ----
    fig, ax = plt.subplots(figsize=(8.6, 5.0))
    epi = [s["kj_sd"]/1e7 for s in seq]
    ax.plot(Nv, epi, "o-", color="#1f77b4", label="EPISTEMIC: k_j posterior sd (shrinks ~1/√N)")
    ax.axhline(SIGMA_BUILD*KJ_TRUE/1e7, color="#2ca02c", ls="--", label=f"ALEATORY: build-to-build k_j sd ({SIGMA_BUILD*100:.0f}%, irreducible)")
    ax.set_xlabel("number of builds acquired"); ax.set_ylabel("k_j uncertainty [×10⁷ N/m]")
    ax.set_title("Aleatory vs epistemic: more data shrinks the epistemic fleet-mean k_j; build scatter is irreducible", fontsize=9.5)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG/"hexapod_aleatory_epistemic.png", dpi=145); plt.close(fig)


def make_gif(data, seq, post_by_N, Ns):
    """Build-by-build animation: predictive interface apparent mass (axial M_zz + splitting lateral M_xx)
    approaching truth as builds accumulate, with the k_j posterior contraction shown alongside."""
    FR = FIG/"hexapod_gif_frames"; FR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    comps = [(2, "M_zz axial [kg]"), (0, "M_xx lateral [kg] — splits under spatial error")]
    truth = {c: np.exp(data["clean_mean_truth"][c]) for c, _ in comps}
    # fixed axis limits across frames
    ylims = {c: (0.5*min(truth[c].min(), 1), 3.0*truth[c].max()) for c, _ in comps}
    # precompute predictive curves per N
    curves_by_N = {}
    for N in Ns:
        kj = post_by_N[N]["kj"]; sub = kj[rng.choice(len(kj), min(150, len(kj)), replace=False)]
        cc = {}
        for c, _ in comps:
            arr = np.array([np.abs(np.asarray(appmass_diag_bu_jax(k, F)))[:, c] for k in sub])
            cc[c] = np.quantile(arr, [0.025, 0.5, 0.975], axis=0)
        curves_by_N[N] = cc
    frames = []
    for k, N in enumerate(Ns):
        s = seq[k]
        fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.0))
        for ax, (c, lbl) in zip(axes[:2], comps):
            ax.loglog(F, truth[c], color="#d62728", lw=2.4, label="TRUTH (spatial+freq error)")
            lo, md, hi = curves_by_N[N][c]
            ax.fill_between(F, lo, hi, color="#1f77b4", alpha=0.35, label="BU predictive 95% (k_j post.)")
            ax.loglog(F, md, color="#1f77b4", lw=1.8, label="BU predictive median")
            ax.set_xlim(F.min(), F.max()); ax.set_ylim(*ylims[c])
            ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel(lbl, fontsize=9)
            ax.set_title(lbl.split(" —")[0], fontsize=9.5); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=7.5, loc="lower left")
        # k_j contraction panel (running)
        ax = axes[2]
        Nv = [seq[i]["N_builds"] for i in range(k+1)]
        q50 = [seq[i]["kj_q50"]/1e7 for i in range(k+1)]
        lo = [seq[i]["kj_q025"]/1e7 for i in range(k+1)]; hi = [seq[i]["kj_q975"]/1e7 for i in range(k+1)]
        ax.errorbar(Nv, q50, yerr=[np.array(q50)-np.array(lo), np.array(hi)-np.array(q50)], fmt="o-", capsize=4, color="#1f77b4", label="k_j posterior (95%)")
        ax.axhline(KJ_TRUE/1e7, color="#d62728", ls="--", lw=2, label=f"truth {KJ_TRUE/1e7:.3f}e7")
        ax.axhline(KJ_GUESS/1e7, color="#999", ls=":", label="prior guess (+25%)")
        ax.set_xlim(0.5, max(Ns)+0.5); ax.set_ylim(1.70, 2.32)
        ax.set_xlabel("number of builds acquired"); ax.set_ylabel("k_j [×10⁷ N/m]")
        ax.set_title("k_j posterior so far", fontsize=9.5); ax.grid(True, alpha=0.3); ax.legend(fontsize=8, loc="upper right")
        fig.suptitle(f"StatFEM sequential learning — after {N} build(s):  k_j={s['kj_q50']:.3e} N/m "
                     f"(bias {s['bias_pct']:+.2f}%), epistemic sd={s['kj_sd']:.1e}, covers truth={s['covers95']}  "
                     f"|  residual bias = SPATIAL model-form error (single k_j cannot split the lateral modes)", fontsize=10)
        fig.tight_layout()
        ff = FR/f"frame_N{N:02d}.png"; fig.savefig(ff, dpi=120); plt.close(fig); frames.append(ff)
    gif = FIG/"hexapod_sequential_learning.gif"
    imageio.mimsave(gif, [imageio.imread(f) for f in frames], duration=1.2, loop=0)
    print("wrote", gif, "with", len(frames), "frames")


if __name__ == "__main__":
    main()
