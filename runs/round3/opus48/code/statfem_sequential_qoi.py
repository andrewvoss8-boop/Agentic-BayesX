#!/usr/bin/env python3
"""Sequential assimilation of the QOI: as each build (data point) is added, show the PRIOR vs POSTERIOR
(95% CI) of (a) the netCG tray response and (b) the coupled interface-acceleration PSD, against the
ground truth. Walk one data point at a time (slow GIF). Also a static three-way FRF:
truth vs BU(k_j)-only vs BU(k_j)+discrepancy d, to show what the learned discrepancy does (and doesn't).

Dome (source) from mdof_forward (bounce mode); tray (load) = 6-strut hexapod axial apparent mass at the
learned k_j; coupled via FBS; flight forcing reverse-engineered (dome interface response 0.1 g^2/Hz).
Bands: EPISTEMIC-only (k_j posterior; forcing at mean) collapses; TOTAL (k_j + build scatter + 3 dB
flight-to-flight forcing GP) stays wide -> answers 'why do the QOI bands stay the same size'.
Only the band + truth are drawn (not every build) to keep frames readable. Env R3SQ_SMOKE=1 -> tiny.
"""
from __future__ import annotations
import os, sys, math, json, time
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl_sq")
os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=4")
import numpy as np
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
from numpyro.infer import init_to_value
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import imageio.v2 as imageio

HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE/"code"))
import statfem_hexapod as hxs
import tray_hexapod as hx
import mdof_forward as mdof

OUT = HERE/"report"; FIG = OUT/"figures"
SEED = 20260604
SMOKE = os.environ.get("R3SQ_SMOKE", "0") == "1"
N_CHAINS = 4
WARMUP = 150 if SMOKE else 500
DRAWS = 150 if SMOKE else 700
GIF_DUR = 6.0           # seconds/frame (5x slower than the earlier 1.2 s)

F_FIT = np.geomspace(33.0, 260.0, 60)      # band for fitting k_j from apparent-mass data
F_Q = np.geomspace(20.0, 2000.0, 160)      # band for the QOI (netCG / interface PSD)
NDOF = hxs.NDOF; KJ_TRUE = hxs.KJ_TRUE; KJ_GUESS = hxs.KJ_GUESS
SIGMA_E = hxs.SIGMA_E; SIGMA_BUILD = hxs.SIGMA_BUILD
G0 = mdof.G0; M_LOAD = hx.M_TRAY

# dome + forcing (fixed)
_b = mdof.build_bases(); DOME_BASIS = (_b["dome_freq_ratio"], _b["dome_res_ratio"])
M1_PHYS, _, _ = mdof.dome_eff_interface_mass()
S_ORIG, _, _ = mdof.reverse_engineer_force(DOME_BASIS, M1_PHYS, mdof.DOME_F1_HZ, mdof.DOME_ZETA1, 0.1)
S_FLIGHT = S_ORIG*10**(-6.0/10.0)
SIGMA_F2F_LN = 3.0*math.log(10.0)/10.0
YS_Q = np.asarray(mdof.source_accelerance(mdof.DOME_F1_HZ, mdof.DOME_ZETA1, jnp.asarray(F_Q),
                                          DOME_BASIS[0], DOME_BASIS[1], m1_eff=M1_PHYS))
_FORCING_CHOL = np.linalg.cholesky(hxs.matern32(F_Q, 0.08, SIGMA_F2F_LN) + 1e-10*np.eye(len(F_Q)))


def _kl(F):
    K = hxs.matern32(F, hxs.ELL_D, hxs.SIGMA_D); w, V = np.linalg.eigh(K)
    idx = np.argsort(w)[::-1][:hxs.M_KL]; return V[:, idx], np.clip(w[idx], 0, None)
PHI_FIT, LAM_FIT = _kl(F_FIT)


def gen_data():
    rng = np.random.default_rng(SEED); spat = hx.spatial_error_pattern(hxs.A_SPATIAL)
    # frequency model-form error on F_FIT
    Kf = hxs.matern32(F_FIT, hxs.ELL_FREQ, 1.0)+1e-10*np.eye(len(F_FIT)); Lf = np.linalg.cholesky(Kf)
    dfreq = np.array([hxs.A_FREQ*(Lf@rng.standard_normal(len(F_FIT)))/np.std(Lf@rng.standard_normal(len(F_FIT))) for _ in range(NDOF)])
    kjb = KJ_TRUE*np.exp(SIGMA_BUILD*rng.standard_normal(hxs.N_BUILDS))
    Y = np.empty((hxs.N_BUILDS, NDOF, len(F_FIT)))
    for b in range(hxs.N_BUILDS):
        Y[b] = np.log(hxs.appmass_diag_truth(kjb[b]*spat, F_FIT)).T + dfreq + SIGMA_E*rng.standard_normal((NDOF, len(F_FIT)))
    return Y, spat


def fit_kj(Ybar, n_builds, seed):
    fj = jnp.asarray(F_FIT); yj = jnp.asarray(Ybar)
    sig = math.sqrt(SIGMA_E**2/max(n_builds, 1)+1e-8)
    Phij = jnp.asarray(PHI_FIT); slj = jnp.asarray(np.sqrt(LAM_FIT))
    def model():
        log_kj = numpyro.sample("log_kj", dist.Normal(math.log(KJ_GUESS), 0.30))
        numpyro.deterministic("kj", jnp.exp(log_kj))
        mu = jnp.log(hxs.appmass_diag_bu_jax(jnp.exp(log_kj), fj)).T
        z = numpyro.sample("z_d", dist.Normal(0, 1).expand([NDOF, PHI_FIT.shape[1]]))
        mu = mu + (Phij @ (slj*z).T).T
        numpyro.sample("y", dist.Normal(mu, sig), obs=yj)
    mc = MCMC(NUTS(model, target_accept_prob=0.95, init_strategy=init_to_value(values={"log_kj": math.log(KJ_GUESS)})), num_warmup=WARMUP, num_samples=DRAWS,
              num_chains=N_CHAINS, chain_method="parallel", progress_bar=False)
    mc.run(jax.random.PRNGKey(seed))
    return np.asarray(mc.get_samples()["kj"])


def couple(ML_zz, forcing):
    """ML_zz: (nf,) load axial apparent mass; forcing: (nf,) N^2/Hz. Returns iface accel PSD g^2/Hz, netCG PSD g^2/Hz."""
    H = YS_Q/(1.0+YS_Q*ML_zz); fr = YS_Q*ML_zz/(1.0+YS_Q*ML_zz)
    iface_psd = np.abs(H/G0)**2*forcing
    netcg_psd = np.abs(fr)**2*forcing/(M_LOAD**2)/(G0**2)
    return iface_psd, netcg_psd


def ml_bu(kj):
    return np.abs(np.asarray(hxs.appmass_diag_bu_jax(kj, jnp.asarray(F_Q)))[:, 2])


def qoi_bands(kj_samp, total=True, rng=None, nsamp=80):
    """Return (iface 2.5/50/97.5, netcg 2.5/50/97.5) over F_Q. total -> + build scatter + forcing GP."""
    rng = rng or np.random.default_rng(0)
    idx = rng.choice(len(kj_samp), min(nsamp, len(kj_samp)), replace=False)
    IF = np.empty((len(idx), len(F_Q))); NC = np.empty((len(idx), len(F_Q)))
    for i, j in enumerate(idx):
        kj = kj_samp[j]*(math.exp(SIGMA_BUILD*rng.standard_normal()) if total else 1.0)
        forcing = S_FLIGHT*(np.exp(_FORCING_CHOL@rng.standard_normal(len(F_Q))) if total else 1.0)
        IF[i], NC[i] = couple(ml_bu(kj), forcing)
    qi = np.quantile(IF, [0.025, 0.5, 0.975], axis=0); qn = np.quantile(NC, [0.025, 0.5, 0.975], axis=0)
    return qi, qn


def truth_qoi(spat):
    ML = np.abs(np.asarray(hxs.appmass_diag_truth(KJ_TRUE*spat, F_Q))[:, 2])
    return couple(ML, S_FLIGHT)


def main():
    t0 = time.time(); numpyro.set_host_device_count(N_CHAINS); FIG.mkdir(parents=True, exist_ok=True)
    Y, spat = gen_data()
    tru_if, tru_nc = truth_qoi(spat)
    Ns = [0, 1, 2, 3, 4, 5, 6, 7, 8] if not SMOKE else [0, 4, 8]
    kj_by_N = {}
    kj_prior = np.exp(np.random.default_rng(1).normal(math.log(KJ_GUESS), 0.30, 2000))
    for N in Ns:
        if N == 0:
            kj_by_N[0] = kj_prior
        else:
            kj_by_N[N] = fit_kj(Y[:N].mean(axis=0), N, SEED+N)
        print("N=%d kj median %.3e" % (N, np.median(kj_by_N[N])))

    # precompute bands
    bands = {}
    for N in Ns:
        rng = np.random.default_rng(100+N)
        qi_t, qn_t = qoi_bands(kj_by_N[N], total=True, rng=rng)
        qi_e, qn_e = qoi_bands(kj_by_N[N], total=False, rng=np.random.default_rng(200+N))
        bands[N] = dict(if_total=qi_t, nc_total=qn_t, if_epi=qi_e, nc_epi=qn_e)

    _gif("netcg", bands, Ns, tru_nc, "netCG response PSD [g²/Hz]",
         "netCG (tray net-CG response) — prior → posterior as builds are assimilated")
    _gif("iface", bands, Ns, tru_if, "interface accel response PSD [g²/Hz]",
         "Coupled interface acceleration PSD — prior → posterior as builds are assimilated")
    static_frf_with_d(Y, spat)

    (OUT/"statfem_sequential_qoi_results.json").write_text(json.dumps({
        "Ns": Ns, "kj_median_by_N": {str(N): float(np.median(kj_by_N[N])) for N in Ns},
        "note": "QOI bands: TOTAL (epistemic k_j + build scatter + 3 dB forcing) barely shrinks because "
                "it is ALEATORY-dominated; EPISTEMIC-only (k_j) collapses with builds. netCG/interface PSD "
                "are predictions; ground truth (with spatial+freq model-form error) shown as the target.",
        "gif_duration_s_per_frame": GIF_DUR, "runtime_s": round(time.time()-t0, 1)}, indent=2))
    print("DONE sequential QOI in", round(time.time()-t0, 1), "s")


def _gif(tag, bands, Ns, truth, ylabel, title):
    FR = FIG/f"seq_{tag}_frames"; FR.mkdir(parents=True, exist_ok=True)
    key_t = "nc_total" if tag == "netcg" else "if_total"
    key_e = "nc_epi" if tag == "netcg" else "if_epi"
    ymax = max(bands[0][key_t][2].max(), truth.max())*3
    ymin = min(bands[Ns[-1]][key_e][0].min(), truth.min())*0.3
    frames = []
    prior = bands[0][key_t]
    for N in Ns:
        fig, ax = plt.subplots(figsize=(9.2, 5.4))
        ax.fill_between(F_Q, prior[0], prior[2], color="#cccccc", alpha=0.5, label="PRIOR 95% (total)")
        bt = bands[N][key_t]; be = bands[N][key_e]
        ax.fill_between(F_Q, bt[0], bt[2], color="#1f77b4", alpha=0.30, label="POSTERIOR 95% (total: +build +forcing)")
        ax.fill_between(F_Q, be[0], be[2], color="#ff7f0e", alpha=0.40, label="POSTERIOR 95% (epistemic k_j only)")
        ax.loglog(F_Q, bt[1], color="#1f77b4", lw=1.6, label="posterior median")
        ax.loglog(F_Q, truth, color="#d62728", lw=2.2, ls="--", label="ground truth (target)")
        ax.set_xlim(F_Q.min(), F_Q.max()); ax.set_ylim(ymin, ymax)
        ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel(ylabel)
        lbl = "PRIOR (no data)" if N == 0 else f"after {N} build(s)"
        ax.set_title(f"{title}\n{lbl}  —  EPISTEMIC band collapses; TOTAL band stays wide (aleatory-dominated)", fontsize=9.0)
        ax.grid(True, which="both", alpha=0.25); ax.legend(fontsize=7.8, loc="lower center", ncol=2)
        fig.tight_layout(); ff = FR/f"frame_N{N:02d}.png"; fig.savefig(ff, dpi=120); plt.close(fig); frames.append(ff)
    gif = FIG/f"seq_{tag}_prior_data_posterior.gif"
    imageio.mimsave(gif, [imageio.imread(f) for f in frames], duration=GIF_DUR, loop=0)
    print("wrote", gif)


def static_frf_with_d(Y, spat):
    """Truth vs BU(k_j)-only vs BU(k_j)+discrepancy d, at N=8 (the three-way comparison)."""
    fj = jnp.asarray(F_FIT); Ybar = Y.mean(axis=0)
    # fit once more keeping z_d
    sig = math.sqrt(SIGMA_E**2/hxs.N_BUILDS+1e-8); Phij = jnp.asarray(PHI_FIT); slj = jnp.asarray(np.sqrt(LAM_FIT))
    def model():
        log_kj = numpyro.sample("log_kj", dist.Normal(math.log(KJ_GUESS), 0.30))
        numpyro.deterministic("kj", jnp.exp(log_kj))
        mu = jnp.log(hxs.appmass_diag_bu_jax(jnp.exp(log_kj), fj)).T
        z = numpyro.sample("z_d", dist.Normal(0, 1).expand([NDOF, PHI_FIT.shape[1]]))
        mu = mu + (Phij @ (slj*z).T).T
        numpyro.sample("y", dist.Normal(mu, sig), obs=jnp.asarray(Ybar))
    mc = MCMC(NUTS(model, target_accept_prob=0.95, init_strategy=init_to_value(values={"log_kj": math.log(KJ_GUESS)})), num_warmup=WARMUP, num_samples=DRAWS,
              num_chains=N_CHAINS, chain_method="parallel", progress_bar=False)
    mc.run(jax.random.PRNGKey(SEED+1)); post = mc.get_samples()
    kj_hat = float(np.median(np.asarray(post["kj"]))); zmean = np.asarray(post["z_d"]).mean(axis=0)
    d_mean = (PHI_FIT @ (np.sqrt(LAM_FIT)*zmean).T).T              # (6, nf)
    bu = np.log(np.abs(np.asarray(hxs.appmass_diag_bu_jax(kj_hat, fj))))   # (nf,6)
    truth = np.log(hxs.appmass_diag_truth(KJ_TRUE*spat, F_FIT))            # (nf,6)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4))
    for ax, (c, lbl) in zip(axes, [(2, "M_zz axial"), (0, "M_xx lateral (splits under spatial error)")]):
        ax.loglog(F_FIT, np.exp(truth[:, c]), color="#d62728", lw=2.4, label="ground truth")
        ax.loglog(F_FIT, np.exp(bu[:, c]), color="#ff7f0e", lw=1.8, ls=":", label="BU(k_ĵ) only")
        ax.loglog(F_FIT, np.exp(bu[:, c]+d_mean[c]), color="#1f77b4", lw=2.0, label="BU(k_ĵ) + learned discrepancy d")
        ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel(f"|{lbl.split()[0]}| [kg or kg·m²]")
        ax.set_title(lbl, fontsize=9.5); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    fig.suptitle("Are we learning the model-form error?  d catches the FREQUENCY error (blue→red) but NOT the "
                 "SPATIAL split (M_xx) — single k_j + frequency-d cannot represent it", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG/"frf_truth_bu_buplusd.png", dpi=140); plt.close(fig)
    print("wrote frf_truth_bu_buplusd.png  (kj_hat %.3e)" % kj_hat)


if __name__ == "__main__":
    main()
