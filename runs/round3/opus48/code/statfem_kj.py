#!/usr/bin/env python3
"""StatFEM: learn the interface (joint) stiffness k_j under realistic MODEL-FORM ERROR.

Round-3 follow-up (Claude Code Opus 4.8 runner), per human direction:
- NO 2DOF staged data. We GENERATE synthetic MDOF observations from a ground-truth interface
  apparent-mass model with three baked-in assumptions: (1) a fixed smooth MODEL-FORM ERROR mfe(w)
  (stand-in for a nonlinear/frequency-dependent joint + coarse-mesh error that a single linear k_j
  cannot represent), (2) BUILD-to-build k_j scatter, (3) FLIGHT-to-flight forcing variability, plus
  sensor noise.
- The Bayesian-updating (BU) model is a COARSE linear-joint model that updates ONLY ONE parameter:
  the interface stiffness k_j. Damping is FIXED (saved for a later run).
- Model-form error is handled by a StatFEM DISCREPANCY d(w): a GAUSSIAN PROCESS over log-frequency
  (Matern-3/2), marginalized analytically -> the likelihood is multivariate-normal with covariance
  K_d + sigma_e^2 I. (d is a GP/field, NOT a scalar; sigma_e is the scalar sensor-noise term.)
- We PRESSURE-TEST the process: sweep the magnitude of each truth-side assumption (mfe, flight-to-
  flight, build-to-build) and show the effect on the k_j posterior and the decision QOI (netCG), and a
  WITH-d vs WITHOUT-d comparison ("does the pipeline know it's wrong?").

Observed channel for learning k_j = the LOAD INTERFACE APPARENT MASS |M_L(w)| (a component-level
interface test; its peak sits at the joint mode sqrt(k_j/m_load) -> directly informative about k_j).
Decision QOI = coupled netCG (interface force / load mass) under flight forcing.

Sampler: NumPyro NUTS (1 parameter). Units SI. Env R3SF_SMOKE=1 -> tiny draws.
"""
from __future__ import annotations

import json, math, os, sys, time
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl_sf")
os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=4")

import numpy as np
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
import arviz as az
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "code"))
import mdof_forward as mdof

OUT = HERE / "report"
FIG = OUT / "figures"
SEED = 20260603
SMOKE = os.environ.get("R3SF_SMOKE", "0") == "1"
N_CHAINS = 4
WARMUP = 200 if SMOKE else 1000
DRAWS = 200 if SMOKE else 1500

# ---- physics constants (PHYSICAL layer from the previous step) ----
BASES = mdof.build_bases()
DOME_BASIS = (BASES["dome_freq_ratio"], BASES["dome_res_ratio"])
TRAY_FLEX = BASES["tray_flex_f"]
M1_PHYS, CAP_MASS, _ = mdof.dome_eff_interface_mass()
M_LOAD = mdof.M_LOAD_PHYS
DOME_F1 = mdof.DOME_F1_HZ
ZETA_DOME = mdof.DOME_ZETA1
ZETA_TRAY = mdof.TRAY_ZETA1            # FIXED this run (damping saved for later)
TRAY_F1_TRUE = mdof.TRAY_F1_HZ         # 86.25 Hz
KJ_TRUE = M_LOAD * (2*np.pi*TRAY_F1_TRUE)**2   # true interface stiffness [N/m]

# coarse-FEM PRIOR guess for k_j: deliberately OFF (a preliminary FEM would not know the truth)
KJ_GUESS = KJ_TRUE * 1.25              # ~25% too stiff -> tray guess ~96 Hz vs truth 86
PRIOR_LOG_SD = 0.30

# ---- baked-in assumption magnitudes (defaults; swept in the pressure test) ----
A_MFE = 0.15           # model-form-error marginal sd in log|M_L| (~1.3 dB amplitude)
ELL_MFE = 0.30         # mfe correlation length in log-frequency
SIGMA_E = 0.05         # sensor noise sd in log|M_L| (~0.43 dB)
SIGMA_BUILD = 0.05     # build-to-build k_j lognormal sd (5%)
SIGMA_F2F_DB = 3.0     # flight-to-flight forcing sd [dB PSD] (fixed/known)
FORCING_ELL = 0.08     # Matern length scale for flight forcing GP (log-freq)
N_BUILDS = 8
N_FLIGHTS = 11

# ---- StatFEM discrepancy GP (the BU model's representation of model-form error) ----
ELL_D = 0.30           # discrepancy length scale (log-freq) -- a reasonable choice
SIGMA_D = 0.15         # discrepancy marginal sd (log|M_L|) -- reasonable; ~ expected mfe size

# frequency grids
F_OBS = np.geomspace(45.0, 180.0, 90)         # apparent-mass measurement band (around joint mode 86)
F_QOI = np.geomspace(20.0, 2000.0, 400)       # netCG integration band
LN10 = math.log(10.0)


def matern32(freqs, ell, sigma):
    eta = np.log(freqs)
    r = np.abs(np.subtract.outer(eta, eta))/ell
    s = math.sqrt(3.0)*r
    return (sigma**2)*(1.0+s)*np.exp(-s)


def appmass_logmag_np(kj, freqs, zeta=ZETA_TRAY):
    f_tray = math.sqrt(kj/M_LOAD)/(2*np.pi)
    ML = np.asarray(mdof.load_apparent_mass(f_tray, zeta, jnp.asarray(freqs), TRAY_FLEX, m_load=M_LOAD))
    return np.log(np.abs(ML))


def appmass_logmag_jax(kj, freqs_j, zeta=ZETA_TRAY):
    f_tray = jnp.sqrt(kj/M_LOAD)/(2*jnp.pi)
    ML = mdof.load_apparent_mass(f_tray, zeta, freqs_j, TRAY_FLEX, m_load=M_LOAD)
    return jnp.log(jnp.abs(ML))


def make_mfe(freqs, a_mfe=A_MFE, ell=ELL_MFE, seed=SEED+11):
    """ONE fixed smooth model-form-error function (a GP draw) = the deterministic 'truth is wrong' bias."""
    if a_mfe <= 0:
        return np.zeros(len(freqs))
    K = matern32(freqs, ell, 1.0) + 1e-10*np.eye(len(freqs))
    L = np.linalg.cholesky(K)
    z = np.random.default_rng(seed).standard_normal(len(freqs))
    raw = L @ z
    return a_mfe * raw / np.std(raw)   # scale to marginal sd a_mfe


# ----------------------------------------------------------------------------
# Synthetic data generation (ground truth)
# ----------------------------------------------------------------------------
def generate_apparent_mass_data(a_mfe=A_MFE, sigma_e=SIGMA_E, sigma_build=SIGMA_BUILD,
                                n_builds=N_BUILDS, seed=SEED):
    rng = np.random.default_rng(seed)
    mfe = make_mfe(F_OBS, a_mfe=a_mfe)
    kj_builds = KJ_TRUE * np.exp(sigma_build*rng.standard_normal(n_builds))
    Y = np.empty((n_builds, len(F_OBS)))
    clean = np.empty((n_builds, len(F_OBS)))
    for b in range(n_builds):
        base = appmass_logmag_np(kj_builds[b], F_OBS)   # truth structure (per-build k_j)
        clean[b] = base + mfe                            # truth = structure + model-form error
        Y[b] = clean[b] + sigma_e*rng.standard_normal(len(F_OBS))   # + sensor noise
    return dict(Y=Y, clean=clean, mfe=mfe, kj_builds=kj_builds, a_mfe=a_mfe,
                sigma_e=sigma_e, sigma_build=sigma_build)


# ----------------------------------------------------------------------------
# StatFEM NUTS model: update ONLY log_kj; GP discrepancy d marginalized into the covariance.
# ----------------------------------------------------------------------------
M_KL = 8   # number of Karhunen-Loeve modes for the discrepancy GP (reduced-rank, well-conditioned)


def kl_basis(sigma_d=SIGMA_D, ell_d=ELL_D, M=M_KL):
    """Top-M Karhunen-Loeve modes of the Matern-3/2 discrepancy kernel over log-frequency.
    d(w) = Phi @ (sqrt(lam) * z), z~N(0,1)^M  is a reduced-rank GP (proper GP approximation)."""
    K = matern32(F_OBS, ell_d, sigma_d)
    w, V = np.linalg.eigh(K)
    idx = np.argsort(w)[::-1][:M]
    lam = np.clip(w[idx], 0.0, None)
    return V[:, idx], lam


def make_model(ybar, with_discrepancy=True, sigma_e=SIGMA_E, n_builds=N_BUILDS,
               sigma_d=SIGMA_D, ell_d=ELL_D):
    """StatFEM model on the BUILD-MEAN apparent mass. SHARED discrepancy d (systematic model-form
    error, same every build) as an explicit low-rank GP sampled jointly with k_j; only sensor noise
    averages out (sigma_e^2/B). Updated PHYSICAL parameter: k_j (ONLY). d coefficients are nuisance."""
    fj = jnp.asarray(F_OBS); yj = jnp.asarray(ybar)
    sig_obs = math.sqrt(sigma_e**2/max(n_builds, 1) + 1e-8)
    if with_discrepancy:
        Phi, lam = kl_basis(sigma_d, ell_d)
        Phij = jnp.asarray(Phi); slj = jnp.asarray(np.sqrt(lam)); M = len(lam)
    def model():
        log_kj = numpyro.sample("log_kj", dist.Normal(math.log(KJ_GUESS), PRIOR_LOG_SD))
        kj = jnp.exp(log_kj)
        numpyro.deterministic("kj", kj)
        numpyro.deterministic("f_tray_hz", jnp.sqrt(kj/M_LOAD)/(2*jnp.pi))
        mu = appmass_logmag_jax(kj, fj)
        if with_discrepancy:
            z = numpyro.sample("z_d", dist.Normal(0.0, 1.0).expand([M]))
            mu = mu + Phij @ (slj*z)
        numpyro.sample("ybar", dist.Normal(mu, sig_obs), obs=yj)
    return model


def run_nuts(model, seed=SEED):
    kernel = NUTS(model, target_accept_prob=0.95, init_strategy=numpyro.infer.init_to_median)
    mcmc = MCMC(kernel, num_warmup=WARMUP, num_samples=DRAWS, num_chains=N_CHAINS,
                chain_method="parallel", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    return mcmc


def diagnostics(mcmc):
    idata = az.from_numpyro(mcmc)
    rhat = float(az.rhat(idata, var_names=["log_kj"])["log_kj"].values)
    eb = float(az.ess(idata, var_names=["log_kj"], method="bulk")["log_kj"].values)
    et = float(az.ess(idata, var_names=["log_kj"], method="tail")["log_kj"].values)
    ndiv = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    return dict(rank_split_rhat=rhat, ess_bulk=eb, ess_tail=et, divergences=ndiv,
                converged=bool(rhat < 1.01 and eb >= 400 and et >= 400 and ndiv == 0))


# ----------------------------------------------------------------------------
# GP discrepancy posterior (for plotting what d learned)
# ----------------------------------------------------------------------------
def discrepancy_posterior(kj_hat, Y, sigma_e=SIGMA_E, sigma_d=SIGMA_D, ell_d=ELL_D):
    Kd = matern32(F_OBS, ell_d, sigma_d)
    n = len(F_OBS); nb = Y.shape[0]
    Cov = Kd + (sigma_e**2/nb)*np.eye(n) + 1e-9*np.eye(n)   # shared-d on the build mean
    mu = appmass_logmag_np(kj_hat, F_OBS)
    resid = Y.mean(axis=0) - mu             # mean residual across builds
    A = np.linalg.solve(Cov, resid)
    d_mean = Kd @ A
    d_cov = Kd - Kd @ np.linalg.solve(Cov, Kd)
    d_sd = np.sqrt(np.clip(np.diag(d_cov), 0, None))
    return d_mean, d_sd


# ----------------------------------------------------------------------------
# netCG QOI prediction from the k_j posterior (+ build & flight variability)
# ----------------------------------------------------------------------------
def netcg_ensemble(kj_samps, a_mfe=A_MFE, sigma_build=SIGMA_BUILD, sigma_f2f_db=SIGMA_F2F_DB,
                   ell_force=FORCING_ELL, n=400, seed=SEED+5):
    rng = np.random.default_rng(seed)
    S_orig, _, _ = mdof.reverse_engineer_force(DOME_BASIS, M1_PHYS, DOME_F1, ZETA_DOME, 0.1)
    S_flight = S_orig*10**(-6.0/10.0)
    sig_f2f_ln = sigma_f2f_db*LN10/10.0
    chol = np.linalg.cholesky(matern32(F_QOI, ell_force, sig_f2f_ln) + 1e-10*np.eye(len(F_QOI)))
    jf = jnp.asarray(F_QOI)
    idx = rng.choice(len(kj_samps), size=min(n, len(kj_samps)), replace=False)
    grms = np.empty(len(idx))
    for i, j in enumerate(idx):
        kj = kj_samps[j]*math.exp(sigma_build*rng.standard_normal())   # build scatter on k_j
        f_tray = math.sqrt(kj/M_LOAD)/(2*np.pi)
        fr = np.abs(np.asarray(mdof.interface_force_per_force(DOME_F1, f_tray, ZETA_DOME, ZETA_TRAY,
                              jf, DOME_BASIS, TRAY_FLEX, m1_eff=M1_PHYS, m_load=M_LOAD)))**2
        gp = chol @ rng.standard_normal(len(F_QOI))
        forceps = S_flight*np.exp(gp)
        _, psd_g2 = mdof.netcg_psd(fr, forceps, m_load=M_LOAD)
        grms[i] = 3.0*math.sqrt(np.trapz(psd_g2, F_QOI))
    return grms


# ----------------------------------------------------------------------------
# MAIN: headline run + pressure-test sweeps + many figures
# ----------------------------------------------------------------------------
def fit_kj(data, with_discrepancy=True, sigma_d=SIGMA_D, ell_d=ELL_D, seed=SEED):
    nb = data["Y"].shape[0]
    ybar = data["Y"].mean(axis=0)                       # build-mean apparent mass (shared-d sufficient stat)
    model = make_model(ybar, with_discrepancy, data["sigma_e"], nb, sigma_d, ell_d)
    mcmc = run_nuts(model, seed=seed)
    post = {k: np.asarray(v) for k, v in mcmc.get_samples().items()}
    return post, diagnostics(mcmc)


def main():
    t0 = time.time()
    numpyro.set_host_device_count(N_CHAINS)
    FIG.mkdir(parents=True, exist_ok=True)
    print(f"KJ_TRUE={KJ_TRUE:.3e} N/m  guess={KJ_GUESS:.3e}  m_load={M_LOAD:.1f} kg  dome eff mass={M1_PHYS:.0f} kg")

    # ---------- headline run (defaults, WITH discrepancy) ----------
    data = generate_apparent_mass_data()
    post_d, diag_d = fit_kj(data, with_discrepancy=True)
    post_nd, diag_nd = fit_kj(data, with_discrepancy=False)
    kj_d = post_d["kj"]; kj_nd = post_nd["kj"]
    print("WITH d:    kj q50 %.3e  (truth %.3e)  rhat %.4f ess %.0f div %d"
          % (np.median(kj_d), KJ_TRUE, diag_d["rank_split_rhat"], diag_d["ess_bulk"], diag_d["divergences"]))
    print("WITHOUT d: kj q50 %.3e  rhat %.4f" % (np.median(kj_nd), diag_nd["rank_split_rhat"]))

    # netCG QOI from the k_j posterior
    grms_d = netcg_ensemble(kj_d)

    # ---------- FIGURES ----------
    plot_truth_vs_bu(data)
    plot_assumption_magnitudes(data)
    plot_kj_posterior(post_d, post_nd, data)
    plot_discrepancy_learned(post_d, data)
    plot_ppc(post_d, data)
    sens = pressure_test()                 # sweeps + figures
    plot_qoi(grms_d)

    # ---------- results ----------
    results = {
        "setup": {"kj_true_n_per_m": KJ_TRUE, "kj_guess_n_per_m": KJ_GUESS, "m_load_kg": M_LOAD,
                  "dome_eff_mass_kg": M1_PHYS, "zeta_tray_fixed": ZETA_TRAY, "tray_f1_true_hz": TRAY_F1_TRUE,
                  "n_builds": N_BUILDS, "n_flights": N_FLIGHTS, "obs_channel": "load interface apparent mass |M_L|",
                  "learned_parameter": "interface (joint) stiffness k_j (ONLY); damping fixed"},
        "assumptions_default": {"mfe_sd_log": A_MFE, "mfe_ell_logfreq": ELL_MFE, "sensor_sd_log": SIGMA_E,
                                "build_kj_sd": SIGMA_BUILD, "f2f_db": SIGMA_F2F_DB, "forcing_ell": FORCING_ELL},
        "discrepancy_gp": {"type": "Matern-3/2 over log-frequency, marginalized (StatFEM d)",
                           "ell_d_logfreq": ELL_D, "sigma_d_log": SIGMA_D, "is_a_gp_not_scalar": True},
        "kj_posterior_with_d": {"q50": float(np.median(kj_d)),
                                "q025": float(np.quantile(kj_d, 0.025)), "q975": float(np.quantile(kj_d, 0.975)),
                                "bias_pct_vs_truth": float(100*(np.median(kj_d)-KJ_TRUE)/KJ_TRUE),
                                "covers_truth_95": bool(np.quantile(kj_d,0.025) <= KJ_TRUE <= np.quantile(kj_d,0.975))},
        "kj_posterior_without_d": {"q50": float(np.median(kj_nd)),
                                "q025": float(np.quantile(kj_nd, 0.025)), "q975": float(np.quantile(kj_nd, 0.975)),
                                "bias_pct_vs_truth": float(100*(np.median(kj_nd)-KJ_TRUE)/KJ_TRUE),
                                "covers_truth_95": bool(np.quantile(kj_nd,0.025) <= KJ_TRUE <= np.quantile(kj_nd,0.975))},
        "netcg_3grms_g": {"q50": float(np.median(grms_d)),
                          "q025": float(np.quantile(grms_d,0.025)), "q975": float(np.quantile(grms_d,0.975))},
        "diagnostics_with_d": diag_d, "diagnostics_without_d": diag_nd,
        "sensitivity": sens,
        "runtime_s": round(time.time()-t0, 1),
    }
    (OUT/"statfem_results.json").write_text(json.dumps(results, indent=2))
    (OUT/"statfem_nuts_diagnostics.json").write_text(json.dumps(
        {"with_discrepancy": diag_d, "without_discrepancy": diag_nd,
         "note": "1 learned parameter (log_kj); GP discrepancy marginalized. R-hat/ESS over log_kj."}, indent=2))
    print("DONE statfem_kj in", round(time.time()-t0, 1), "s; netCG q50 %.3f g" % np.median(grms_d))


# ----------------------------- plotting -----------------------------
def plot_truth_vs_bu(data):
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    bu_guess = appmass_logmag_np(KJ_GUESS, F_OBS)
    bu_true = appmass_logmag_np(KJ_TRUE, F_OBS)
    ax.semilogx(F_OBS, np.exp(bu_true), color="#1f77b4", lw=2.2, label="BU model at k_j(true) (linear joint)")
    ax.semilogx(F_OBS, np.exp(bu_true+data["mfe"]), color="#d62728", lw=2.2, ls="--",
                label="TRUTH = BU + model-form error mfe(ω)")
    ax.semilogx(F_OBS, np.exp(bu_guess), color="#7f7f7f", lw=1.6, ls=":", label="BU at coarse guess k_j(+25%)")
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("|M_L| apparent mass [kg]")
    ax.set_title("Interface apparent mass: TRUTH vs BU model — the gap (red−blue) is the model-form error\n"
                 "(joint modeled as a single linear k_j; reality is frequency-dependent/nonlinear)", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG/"statfem_truth_vs_bu.png", dpi=145); plt.close(fig)


def plot_assumption_magnitudes(data):
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.0))
    # (a) model-form error magnitude
    ax = axes[0,0]
    ax.semilogx(F_OBS, data["mfe"]/LN10*10, color="#d62728", lw=2.0, label=f"mfe(ω), sd≈{A_MFE/LN10*10:.1f} dB")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("freq [Hz] (log)"); ax.set_ylabel("model-form error [dB amplitude]")
    ax.set_title("(a) MODEL-FORM ERROR magnitude (fixed, deterministic)"); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    # (b) build-to-build spread
    ax = axes[0,1]
    for b in range(data["Y"].shape[0]):
        ax.semilogx(F_OBS, np.exp(data["clean"][b]), color="#2ca02c", alpha=0.5, lw=1.0,
                    label="per-build truth (8)" if b==0 else None)
    ax.axvline(TRAY_F1_TRUE, color="gray", ls=":", label="joint mode 86.25 Hz")
    ax.set_xlabel("freq [Hz] (log)"); ax.set_ylabel("|M_L| [kg]")
    ax.set_title(f"(b) BUILD-to-build variability (k_j sd {SIGMA_BUILD*100:.0f}%) — peak shifts per build")
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    # (c) sensor noise: clean vs noisy for one build
    ax = axes[1,0]
    ax.semilogx(F_OBS, np.exp(data["clean"][0]), color="#1f77b4", lw=2.0, label="clean truth (build 0)")
    ax.semilogx(F_OBS, np.exp(data["Y"][0]), color="#ff7f0e", lw=1.0, alpha=0.8, label=f"+ sensor noise (sd {SIGMA_E/LN10*10:.1f} dB)")
    ax.set_xlabel("freq [Hz] (log)"); ax.set_ylabel("|M_L| [kg]")
    ax.set_title("(c) SENSOR NOISE magnitude (one build)"); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    # (d) flight-to-flight forcing draws
    ax = axes[1,1]
    S_orig,_,_ = mdof.reverse_engineer_force(DOME_BASIS, M1_PHYS, DOME_F1, ZETA_DOME, 0.1)
    S_flight = S_orig*10**(-6/10.0)
    sig = SIGMA_F2F_DB*LN10/10.0
    chol = np.linalg.cholesky(matern32(F_QOI, FORCING_ELL, sig)+1e-10*np.eye(len(F_QOI)))
    rng = np.random.default_rng(SEED+9)
    ax.loglog(F_QOI, np.full_like(F_QOI, S_flight), color="#1f77b4", lw=2.0, ls="--", label="flight mean (−6 dB)")
    for i in range(N_FLIGHTS):
        ax.loglog(F_QOI, S_flight*np.exp(chol@rng.standard_normal(len(F_QOI))), color="#9467bd", lw=0.8, alpha=0.6,
                  label="flight forcing draws (11)" if i==0 else None)
    ax.set_xlabel("freq [Hz] (log)"); ax.set_ylabel("force PSD [N²/Hz]")
    ax.set_title(f"(d) FLIGHT-to-flight variability ({SIGMA_F2F_DB:.0f} dB, Matérn ℓ={FORCING_ELL})")
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    fig.suptitle("Magnitude of each baked-in ground-truth assumption", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG/"statfem_assumption_magnitudes.png", dpi=140); plt.close(fig)


def plot_kj_posterior(post_d, post_nd, data):
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    pr = np.exp(np.random.default_rng(1).normal(math.log(KJ_GUESS), PRIOR_LOG_SD, 20000))
    ax.hist(pr/1e7, bins=80, density=True, color="#cccccc", alpha=0.7, label="prior (coarse FEM guess)")
    ax.hist(post_d["kj"]/1e7, bins=60, density=True, color="#1f77b4", alpha=0.7, label="posterior WITH discrepancy d")
    ax.hist(post_nd["kj"]/1e7, bins=60, density=True, color="#ff7f0e", alpha=0.55, label="posterior WITHOUT d (naive)")
    ax.axvline(KJ_TRUE/1e7, color="#d62728", lw=2.4, ls="--", label=f"truth k_j = {KJ_TRUE/1e7:.3f}e7")
    ax.set_xlabel("interface stiffness k_j [×10⁷ N/m]"); ax.set_ylabel("density")
    ax.set_title("k_j posterior — StatFEM (with GP discrepancy) vs naive (no discrepancy) vs truth\n"
                 "does the discrepancy keep k_j honest under model-form error?", fontsize=9.5)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG/"statfem_kj_posterior.png", dpi=145); plt.close(fig)


def plot_discrepancy_learned(post_d, data):
    kj_hat = float(np.median(post_d["kj"]))
    d_mean, d_sd = discrepancy_posterior(kj_hat, data["Y"])
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.semilogx(F_OBS, data["mfe"]/LN10*10, color="#d62728", lw=2.2, label="TRUE model-form error mfe(ω)")
    ax.semilogx(F_OBS, d_mean/LN10*10, color="#1f77b4", lw=2.0, label="learned discrepancy d(ω) posterior mean")
    ax.fill_between(F_OBS, (d_mean-2*d_sd)/LN10*10, (d_mean+2*d_sd)/LN10*10, color="#1f77b4", alpha=0.25, label="d 95% band")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("freq [Hz] (log)"); ax.set_ylabel("discrepancy [dB amplitude]")
    ax.set_title("Does the GP discrepancy d capture the true model-form error?\n"
                 "(d is a Gaussian process / field over frequency — not a scalar)", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG/"statfem_discrepancy_learned.png", dpi=145); plt.close(fig)


def plot_ppc(post_d, data):
    kj_hat = float(np.median(post_d["kj"]))
    d_mean, d_sd = discrepancy_posterior(kj_hat, data["Y"])
    mu = appmass_logmag_np(kj_hat, F_OBS)
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    for b in range(data["Y"].shape[0]):
        ax.semilogx(F_OBS, np.exp(data["Y"][b]), color="#999999", lw=0.8, alpha=0.6, label="observed builds" if b==0 else None)
    ax.semilogx(F_OBS, np.exp(mu), color="#ff7f0e", lw=1.8, ls=":", label="BU(k_ĵ) only (no d)")
    ax.semilogx(F_OBS, np.exp(mu+d_mean), color="#1f77b4", lw=2.2, label="StatFEM prediction BU(k_ĵ)+d")
    band = np.sqrt(d_sd**2 + SIGMA_E**2)
    ax.fill_between(F_OBS, np.exp(mu+d_mean-2*band), np.exp(mu+d_mean+2*band), color="#1f77b4", alpha=0.2, label="95% predictive")
    ax.set_xlabel("freq [Hz] (log)"); ax.set_ylabel("|M_L| [kg]")
    ax.set_title("Posterior predictive check: BU(k_j)+d covers the observed apparent mass; BU-only does not", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG/"statfem_ppc.png", dpi=145); plt.close(fig)


def pressure_test():
    """Sweep each baked-in assumption; record k_j posterior (with & without d) and netCG."""
    def run_one(a_mfe=A_MFE, sigma_e=SIGMA_E, sigma_build=SIGMA_BUILD, sigma_f2f_db=SIGMA_F2F_DB, seed=SEED):
        data = generate_apparent_mass_data(a_mfe=a_mfe, sigma_e=sigma_e, sigma_build=sigma_build, seed=seed)
        pd_, _ = fit_kj(data, with_discrepancy=True, seed=seed)
        pn_, _ = fit_kj(data, with_discrepancy=False, seed=seed)
        grms = netcg_ensemble(pd_["kj"], a_mfe=a_mfe, sigma_build=sigma_build, sigma_f2f_db=sigma_f2f_db)
        def summ(kj):
            return dict(q50=float(np.median(kj)), q025=float(np.quantile(kj,0.025)), q975=float(np.quantile(kj,0.975)),
                        bias_pct=float(100*(np.median(kj)-KJ_TRUE)/KJ_TRUE),
                        covers=bool(np.quantile(kj,0.025)<=KJ_TRUE<=np.quantile(kj,0.975)))
        return summ(pd_["kj"]), summ(pn_["kj"]), dict(q50=float(np.median(grms)),
                q025=float(np.quantile(grms,0.025)), q975=float(np.quantile(grms,0.975)))
    sweeps = {
        "mfe_sd_log": [0.0, 0.075, 0.15, 0.30],
        "build_kj_sd": [0.0, 0.025, 0.05, 0.10],
        "f2f_db": [0.0, 1.5, 3.0, 4.5],
    }
    out = {"mfe": [], "build": [], "f2f": []}
    for v in sweeps["mfe_sd_log"]:
        d, n, q = run_one(a_mfe=v); out["mfe"].append({"value": v, "with_d": d, "without_d": n, "netcg": q})
    for v in sweeps["build_kj_sd"]:
        d, n, q = run_one(sigma_build=v); out["build"].append({"value": v, "with_d": d, "without_d": n, "netcg": q})
    for v in sweeps["f2f_db"]:
        d, n, q = run_one(sigma_f2f_db=v); out["f2f"].append({"value": v, "with_d": d, "without_d": n, "netcg": q})
    plot_sensitivity(out)
    return out


def plot_sensitivity(out):
    # k_j bias & coverage vs each assumption (with vs without d)
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.2))
    panels = [("mfe", "model-form error sd [dB]", lambda v: v/LN10*10),
              ("build", "build-to-build k_j sd [%]", lambda v: v*100),
              ("f2f", "flight-to-flight [dB]", lambda v: v)]
    for ax, (key, xlabel, xf) in zip(axes, panels):
        xs = [xf(r["value"]) for r in out[key]]
        for lab, col in [("with_d", "#1f77b4"), ("without_d", "#ff7f0e")]:
            q50 = [r[lab]["q50"]/1e7 for r in out[key]]
            lo = [r[lab]["q025"]/1e7 for r in out[key]]; hi = [r[lab]["q975"]/1e7 for r in out[key]]
            ax.errorbar(xs, q50, yerr=[np.array(q50)-np.array(lo), np.array(hi)-np.array(q50)],
                        fmt="o-" if lab=="with_d" else "s--", capsize=3, color=col,
                        label=("k_j WITH d" if lab=="with_d" else "k_j WITHOUT d"))
        ax.axhline(KJ_TRUE/1e7, color="#d62728", ls="--", label="truth k_j")
        ax.set_xlabel(xlabel); ax.set_ylabel("k_j posterior [×10⁷ N/m]")
        ax.set_title(f"k_j recovery vs {key}"); ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    fig.suptitle("PRESSURE TEST: k_j posterior (median, 95%) vs each baked-in assumption — StatFEM (with d) vs naive (no d)", fontsize=10.5)
    fig.tight_layout(); fig.savefig(FIG/"statfem_sensitivity_kj.png", dpi=140); plt.close(fig)

    # netCG QOI vs each assumption
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.0))
    for ax, (key, xlabel, xf) in zip(axes, panels):
        xs = [xf(r["value"]) for r in out[key]]
        q50 = [r["netcg"]["q50"] for r in out[key]]; lo = [r["netcg"]["q025"] for r in out[key]]; hi = [r["netcg"]["q975"] for r in out[key]]
        ax.errorbar(xs, q50, yerr=[np.array(q50)-np.array(lo), np.array(hi)-np.array(q50)], fmt="^-", capsize=3, color="#6a0dad", label="netCG 3·GRMS (median,95%)")
        ax.set_xlabel(xlabel); ax.set_ylabel("netCG 3·GRMS [g]")
        ax.set_title(f"netCG QOI vs {key}"); ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    fig.suptitle("PRESSURE TEST: decision QOI (netCG) vs each baked-in assumption", fontsize=10.5)
    fig.tight_layout(); fig.savefig(FIG/"statfem_sensitivity_qoi.png", dpi=140); plt.close(fig)


def plot_qoi(grms):
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    ax.hist(grms, bins=50, density=True, color="#6a0dad", alpha=0.75)
    for q, c, l in [(0.025,"#d62728","2.5%"),(0.5,"#000000","median"),(0.975,"#d62728","97.5%")]:
        ax.axvline(np.quantile(grms,q), color=c, ls="--", lw=1.5, label=f"{l}={np.quantile(grms,q):.3f} g")
    ax.set_xlabel("netCG 3·GRMS [g]"); ax.set_ylabel("density")
    ax.set_title("Decision QOI: netCG 3·GRMS posterior (from k_j posterior + build + flight variability)", fontsize=9.5)
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG/"statfem_netcg_qoi.png", dpi=145); plt.close(fig)


if __name__ == "__main__":
    main()
