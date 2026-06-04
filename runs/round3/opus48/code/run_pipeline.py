#!/usr/bin/env python3
"""Round-3 MDOF pipeline (Claude Code Opus 4.8 runner).

Hierarchical NumPyro NUTS inference + MDOF/FBS forward prediction of the netCG QOI and the
force-driven coupled INTERFACE accelerance response PSD vs spec, with the narrow-band exceedance
headline, sensitivity sweeps, resolution study, and source-backed convergence over ALL latents.

LIKELIHOOD (data layer): the staged data is a 2DOF synthetic; our MDOF model reduces EXACTLY to it
at the first mode (verified, tests/validate_fem.py). The likelihood therefore uses the data-consistent
single-mode reduction (round-2 2DOF forward, r2_forward) mapped from the inferred component
fundamentals f_dome, f_tray and damping. WHOLE-PSD/FRF likelihood is the default; a labeled
peak-feature comparison is also reported.

PREDICTION (physical MDOF layer): the netCG QOI and the interface response PSD use the full MDOF model
(mdof_forward) with FEM-derived higher modes and PHYSICAL load mass for netCG. Per-structure
build-to-build scatter perturbs fn AND damping (+-5% @3sigma) per flight, on top of the PSD-level build
effect and the fixed 3 dB flight forcing GP.

Env: R3_SMOKE=1 -> tiny draws for a fast pipeline smoke test (NOT for reporting).
"""
from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl_r3")
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
import imageio.v2 as imageio

HERE = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(HERE / "code"))
sys.path.insert(0, str(ROOT / "scripts"))  # round-2 r2_forward (read-only, data-consistent reduction)

import mdof_forward as mdof
import r2_forward as r2

DATA = ROOT / "artifacts/reports/sequential_vibe_modal_flight_20260602/sequential_dataset.json"
OUT = HERE / "report"
FIG = OUT / "figures"
FRAMES = FIG / "gif_frames"
SEED = 20260603
SMOKE = os.environ.get("R3_SMOKE", "0") == "1"

N_CHAINS = 4
RHAT_MAX = 1.01
ESS_MIN = 100 * N_CHAINS   # >= 400 at 4 chains (bulk AND tail)
DIVERGENCE_FAIL_FRAC = 0.02
WARMUP = 200 if SMOKE else 1500
DRAWS = 200 if SMOKE else 2000

LN10 = math.log(10.0)
def db_to_lnsigma(db): return db * LN10 / 10.0
SIGMA_F2F_LN = db_to_lnsigma(3.0)         # fixed flight-to-flight 3 dB PSD
FORCING_ELL = 0.08                         # Matern-3/2 log-frequency length scale
FORCING_OFFSET_DB = -6.0                   # pre-data conservative DESIGN ENVELOPE (NOT a GEVS margin)
G0 = mdof.G0
# per-structure build-to-build scatter on fn AND damping: +-5% @3sigma -> sigma=0.05/3 (lognormal)
SIGMA_STRUCT_BUILD = 0.05 / 3.0

# nominal->truth anchors
DOME_F1 = mdof.DOME_F1_HZ   # 93.50
TRAY_F1 = mdof.TRAY_F1_HZ   # 86.25

# PHYSICAL prediction layer (deviates from round-2 abstract scaling per human direction):
# dome BOUNCE-mode physical effective interface mass + forcing REVERSE-ENGINEERED so the dome-only
# interface response peaks at 0.1 g^2/Hz at the bounce mode under the +6 dB initial forcing.
# Populated in main(); read by the prediction functions.
PHYS = {}
DOME_RESP_TARGET_G2HZ = 0.1


def f_to_k1(f):  # dome: k1 = M1 (2 pi f)^2
    return r2.M1 * (2*np.pi*f)**2
def f_to_k2(f):  # tray: k2 = M2 (2 pi f)^2
    return r2.M2 * (2*np.pi*f)**2


def matern32_corr_lnfreq(freqs, ell):
    eta = np.log(freqs)
    r = np.abs(np.subtract.outer(eta, eta)) / ell
    s = math.sqrt(3.0) * r
    return (1.0 + s) * np.exp(-s)


def build_refined_grid(global_freqs):
    # mode-local clusters near the coupled features + MDOF higher dome modes (NO hard-coded lines/band:
    # cluster widths scale with each mode's half-power bandwidth ~ 2*zeta*fn)
    bases = mdof.build_bases()
    dome_modes = (DOME_F1 * bases["dome_freq_ratio"]).tolist()
    peaks = [62.3, TRAY_F1, DOME_F1, 119.5] + dome_modes
    pts = [np.asarray(global_freqs, float)]
    for fn in peaks:
        if fn <= 20.0 or fn >= 2000.0:
            continue
        df = max(2.0*0.02*fn, 0.5)
        pts.append(np.linspace(max(fn-4*df, 20.0), min(fn+4*df, 2000.0), 41))
    return np.unique(np.concatenate(pts))


def load_data():
    d = json.loads(DATA.read_text())
    out = dict(
        gfreqs=np.asarray(d["freqs_hz"]),
        mfreqs=np.asarray(d["modal_freqs_hz"]),
        smooth=np.asarray(d["smoothline_psd_g2_per_hz"]),
        meanF_global=np.asarray(d["mean_flight_force_psd_n2_per_hz"]),
        origF_global=np.asarray(d["original_flat_force_psd_n2_per_hz"]),
        vibe_obs=np.asarray(d["tray_vibe_response"]["observed_psd_g2_per_hz"]),
        vibe_3grms_obs=d["tray_vibe_response"]["observed_3grms_g"],
        smooth_3grms=28.26901890473986,
        ch1=np.asarray(d["modal_observations"]["dome_only"]["real"]) + 1j*np.asarray(d["modal_observations"]["dome_only"]["imag"]),
        ch2=np.asarray(d["modal_observations"]["coupled_interface"]["real"]) + 1j*np.asarray(d["modal_observations"]["coupled_interface"]["imag"]),
        ch3=np.asarray(d["modal_observations"]["coupled_tray"]["real"]) + 1j*np.asarray(d["modal_observations"]["coupled_tray"]["imag"]),
        tray_3grms_flights=np.asarray([f["tray_3grms_g_observed"] for f in d["flight_summaries"]]),
        iface_3grms_flights=np.asarray([f["interface_3grms_g_observed"] for f in d["flight_summaries"]]),
        build_id_of_flight=np.asarray([f["build_id"] for f in d["flight_summaries"]]),
        n_builds=len(d["build_samples"]),
    )
    out["rfreqs"] = build_refined_grid(out["gfreqs"])
    out["meanF_const"] = float(out["meanF_global"][0])
    out["meanF_refined"] = np.full_like(out["rfreqs"], out["meanF_const"])
    return out


def precompute_forcing_consts(D, offset_db=FORCING_OFFSET_DB, ell=FORCING_ELL):
    rng = np.random.default_rng(SEED + 7)
    rfreqs = D["rfreqs"]
    # mean force at chosen offset (data mean already at -6 dB; rescale if offset differs)
    base_mean = D["meanF_const"] * 10**((offset_db - FORCING_OFFSET_DB)/10.0)
    meanF_refined = np.full_like(rfreqs, base_mean)
    corr_r = matern32_corr_lnfreq(rfreqs, ell)
    cov_r = (SIGMA_F2F_LN**2)*corr_r + 1e-10*np.eye(len(rfreqs))
    chol_r = np.linalg.cholesky(cov_r)
    # data-consistent (single-mode) interface & tray accel^2 for the flight 3grms likelihood (round-2)
    k1 = f_to_k1(DOME_F1); k2 = f_to_k2(TRAY_F1)
    H00_t = np.abs(np.asarray(r2.interface_accel_per_force_g(k1, k2, r2.TRUE_ZETA1, r2.TRUE_ZETA2, jnp.asarray(rfreqs))))**2
    H10_t = np.abs(np.asarray(r2.tray_accel_per_force_g(k1, k2, r2.TRUE_ZETA1, r2.TRUE_ZETA2, jnp.asarray(rfreqs))))**2
    int_iface_mean = float(np.trapz(H00_t*meanF_refined, rfreqs))
    int_tray_mean = float(np.trapz(H10_t*meanF_refined, rfreqs))
    N_MC = 1000 if SMOKE else 4000
    li = np.empty(N_MC); lt = np.empty(N_MC)
    for i in range(N_MC):
        fac = np.exp(chol_r @ rng.standard_normal(len(rfreqs)))
        li[i] = math.log(np.trapz(H00_t*meanF_refined*fac, rfreqs))
        lt[i] = math.log(np.trapz(H10_t*meanF_refined*fac, rfreqs))
    consts = dict(
        bias_iface=0.5*(float(np.mean(li)) - math.log(int_iface_mean)),
        bias_tray=0.5*(float(np.mean(lt)) - math.log(int_tray_mean)),
        sigma_q_iface=0.5*float(np.std(li)), sigma_q_tray=0.5*float(np.std(lt)),
        int_iface_mean=int_iface_mean, int_tray_mean=int_tray_mean, n_mc=N_MC,
        sigma_f2f_ln=SIGMA_F2F_LN, forcing_ell=ell, forcing_offset_db=offset_db, base_mean=base_mean,
    )
    return consts, chol_r, meanF_refined


def make_model(D, consts):
    jg = jnp.asarray(D["gfreqs"]); jm = jnp.asarray(D["mfreqs"])
    jr = jnp.asarray(D["rfreqs"]); jsmooth = jnp.asarray(D["smooth"])
    j_meanF_r = jnp.asarray(consts["base_mean"]*np.ones_like(D["rfreqs"]))
    log_vibe_obs = jnp.asarray(np.log(np.maximum(D["vibe_obs"], 1e-30)))
    log_ch1 = jnp.asarray(np.log(np.maximum(np.abs(D["ch1"]), 1e-30)))
    log_ch2 = jnp.asarray(np.log(np.maximum(np.abs(D["ch2"]), 1e-30)))
    log_ch3 = jnp.asarray(np.log(np.maximum(np.abs(D["ch3"]), 1e-30)))
    log_tray_q = jnp.asarray(np.log(D["tray_3grms_flights"]))
    log_iface_q = jnp.asarray(np.log(D["iface_3grms_flights"]))
    bid = jnp.asarray(D["build_id_of_flight"]); n_builds = D["n_builds"]
    bias_iface, bias_tray = consts["bias_iface"], consts["bias_tray"]
    sigma_q_iface, sigma_q_tray = consts["sigma_q_iface"], consts["sigma_q_tray"]

    def model(n_flights_assim=n_builds):
        # priors centered at the prior-round NOMINAL (dome 110, tray 75); data must pull to 93.5/86.25
        log_fd = numpyro.sample("log_f_dome", dist.Normal(math.log(110.0), 0.18))
        log_ft = numpyro.sample("log_f_tray", dist.Normal(math.log(75.0), 0.18))
        log_z1 = numpyro.sample("log_zeta_dome", dist.Normal(math.log(0.018), 0.35))
        log_z2 = numpyro.sample("log_zeta_tray", dist.Normal(math.log(0.026), 0.35))
        sigma_sensor = numpyro.sample("sigma_sensor", dist.HalfNormal(0.30))
        sigma_bd = numpyro.sample("sigma_build_dome", dist.HalfNormal(0.50))
        sigma_bt = numpyro.sample("sigma_build_tray", dist.HalfNormal(0.50))
        z_dome = numpyro.sample("z_dome", dist.Normal(0.0, 1.0).expand([n_builds]))
        z_tray = numpyro.sample("z_tray", dist.Normal(0.0, 1.0).expand([n_builds]))
        build_dome = numpyro.deterministic("build_dome", sigma_bd*z_dome)
        build_tray = numpyro.deterministic("build_tray", sigma_bt*z_tray)

        f_dome = jnp.exp(log_fd); f_tray = jnp.exp(log_ft)
        zeta1 = jnp.exp(log_z1); zeta2 = jnp.exp(log_z2)
        k1 = r2.M1*(2*jnp.pi*f_dome)**2; k2 = r2.M2*(2*jnp.pi*f_tray)**2

        # vibe PSD (tray transmissibility), whole-curve
        T = r2.tray_transmissibility(k2, zeta2, jg)
        mu_vibe = jnp.log(jnp.abs(T)**2 * jsmooth) + build_tray[0]
        numpyro.sample("vibe", dist.Normal(mu_vibe, sigma_sensor), obs=log_vibe_obs)
        # modal FRFs (log-magnitude, whole-curve)
        ch1m = jnp.log(jnp.abs(r2.dome_only_recip_inertance(k1, zeta1, jm))) + 0.5*build_dome[0]
        ch2m = jnp.log(jnp.abs(r2.coupled_interface_recip(k1, k2, zeta1, zeta2, jm))) + 0.5*build_dome[0]
        ch3m = jnp.log(jnp.abs(r2.coupled_tray_recip(k1, k2, zeta1, zeta2, jm))) + 0.5*build_tray[0]
        sd_modal = 0.5*sigma_sensor
        numpyro.sample("ch1", dist.Normal(ch1m, sd_modal), obs=log_ch1)
        numpyro.sample("ch2", dist.Normal(ch2m, sd_modal), obs=log_ch2)
        numpyro.sample("ch3", dist.Normal(ch3m, sd_modal), obs=log_ch3)
        # flight 3grms scalars (whole-PSD integrated), forcing GP integrated out (fixed sigma_q)
        H00 = jnp.abs(r2.interface_accel_per_force_g(k1, k2, zeta1, zeta2, jr))**2
        H10 = jnp.abs(r2.tray_accel_per_force_g(k1, k2, zeta1, zeta2, jr))**2
        int_iface = jnp.trapezoid(H00*j_meanF_r, jr); int_tray = jnp.trapezoid(H10*j_meanF_r, jr)
        pred_log_iface = math.log(3.0) + 0.5*jnp.log(int_iface) + 0.5*build_dome[bid] + bias_iface
        pred_log_tray = math.log(3.0) + 0.5*jnp.log(int_tray) + 0.5*build_tray[bid] + bias_tray
        mask = (jnp.arange(n_builds) < n_flights_assim).astype(jnp.float64)
        with numpyro.handlers.scale(scale=mask):
            numpyro.sample("flight_iface", dist.Normal(pred_log_iface, sigma_q_iface), obs=log_iface_q)
            numpyro.sample("flight_tray", dist.Normal(pred_log_tray, sigma_q_tray), obs=log_tray_q)
    return model


def run_nuts(model, n_assim, draws, warmup, seed):
    kernel = NUTS(model, target_accept_prob=0.99, max_tree_depth=12,
                  init_strategy=numpyro.infer.init_to_median)
    mcmc = MCMC(kernel, num_warmup=warmup, num_samples=draws, num_chains=N_CHAINS,
                chain_method="parallel", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), n_flights_assim=n_assim, extra_fields=("diverging", "num_steps"))
    return mcmc


def diagnostics_from(mcmc, fit_runtime, consts):
    extra = mcmc.get_extra_fields()
    diverging = np.asarray(extra["diverging"]); n_div = int(diverging.sum())
    total = int(diverging.size); div_frac = n_div/total
    num_steps = np.asarray(extra["num_steps"]); tree_depth = np.log2(np.maximum(num_steps, 1))
    idata = az.from_numpyro(mcmc)
    monitored = ["log_f_dome", "log_f_tray", "log_zeta_dome", "log_zeta_tray",
                 "sigma_sensor", "sigma_build_dome", "sigma_build_tray", "z_dome", "z_tray"]
    rhat = az.rhat(idata, var_names=monitored, method="rank")
    eb = az.ess(idata, var_names=monitored, method="bulk")
    et = az.ess(idata, var_names=monitored, method="tail")
    per = {}; wr = 0.0; wrn = ""; mb = math.inf; mbn = ""; mt = math.inf; mtn = ""
    for v in monitored:
        rv = np.atleast_1d(np.asarray(rhat[v].values)); bv = np.atleast_1d(np.asarray(eb[v].values)); tv = np.atleast_1d(np.asarray(et[v].values))
        for i in range(rv.size):
            name = v if rv.size == 1 else f"{v}[{i}]"
            r = float(rv.flat[i]); b = float(bv.flat[i]); t = float(tv.flat[i])
            per[name] = {"rank_split_rhat": r, "ess_bulk": b, "ess_tail": t}
            if r > wr: wr, wrn = r, name
            if b < mb: mb, mbn = b, name
            if t < mt: mt, mtn = t, name
    gate_rhat = wr < RHAT_MAX; gate_ess = (mb >= ESS_MIN) and (mt >= ESS_MIN); gate_div = div_frac < DIVERGENCE_FAIL_FRAC
    converged = gate_rhat and gate_ess and gate_div
    return {
        "sampler": "NUTS (NumPyro)", "n_chains": N_CHAINS, "n_warmup": WARMUP,
        "n_draws_per_chain": DRAWS, "total_post_warmup_draws": total,
        "target_accept_prob": 0.99, "max_tree_depth_setting": 12, "non_centered": True,
        "fit_runtime_s": fit_runtime, "divergences": n_div, "divergence_fraction": div_frac,
        "max_tree_depth_observed": float(tree_depth.max()), "mean_num_steps": float(num_steps.mean()),
        "gate_thresholds": {"rank_split_rhat_max": RHAT_MAX, "ess_bulk_min": ESS_MIN,
                            "ess_tail_min": ESS_MIN, "divergence_fraction_fail": DIVERGENCE_FAIL_FRAC,
                            "source": "Stan Ref Manual / Vehtari et al. 2021 (rank-split R-hat, bulk&tail ESS)"},
        "worst_rank_split_rhat": {"value": wr, "variable": wrn},
        "min_ess_bulk": {"value": mb, "variable": mbn}, "min_ess_tail": {"value": mt, "variable": mtn},
        "gate_rhat_pass": gate_rhat, "gate_ess_pass": gate_ess, "gate_divergence_pass": gate_div,
        "converged": converged, "nuts_active": converged,
        "n_monitored_scalar_quantities": len(per), "raw_latents_included": True,
        "per_variable": per, "forcing_constants_fixed": consts, "smoke_mode": SMOKE,
    }


# --------------------------- MDOF prediction ensembles ---------------------------
def _bases():
    b = mdof.build_bases()
    return (b["dome_freq_ratio"], b["dome_res_ratio"]), b["tray_flex_f"], b


def interface_and_netcg_ensemble(post, D, chol_r, flight_id, n_param=400, rng=None,
                                 struct_build=True):
    """Posterior-predictive ensembles for ONE flight (PHYSICAL layer):
       - interface accelerance RESPONSE PSD (g^2/Hz) [physical dome bounce mass + load mass, MDOF modes]
       - netCG PSD (g^2/Hz) and 3*GRMS_netCG (g) [physical load mass]
    Forcing = flat flight-mean force (REVERSE-ENGINEERED so dome-only interface response peaks at
    0.1 g^2/Hz under +6 dB initial forcing; flight = -6 dB design envelope) x Matern GP x build effect.
    Per-structure build-to-build scatter perturbs fn AND damping (+-5% @3sigma) when struct_build."""
    rng = rng or np.random.default_rng(SEED + 100 + flight_id)
    rfreqs = D["rfreqs"]
    dome_basis, tray_flex, _ = _bases()
    m1p = PHYS["m1_phys"]; mlp = PHYS["m_load_phys"]; force_flight = PHYS["force_flight_n2hz"]
    n_total = post["log_f_dome"].shape[0]
    idx = rng.choice(n_total, size=min(n_param, n_total), replace=False)
    fd = np.exp(post["log_f_dome"][idx]); ft = np.exp(post["log_f_tray"][idx])
    z1 = np.exp(post["log_zeta_dome"][idx]); z2 = np.exp(post["log_zeta_tray"][idx])
    bdome = post["build_dome"][idx, flight_id]
    jr = jnp.asarray(rfreqs)
    iface_curves = np.empty((len(idx), len(rfreqs)))
    netcg_curves = np.empty((len(idx), len(rfreqs)))
    netcg_grms = np.empty(len(idx))
    for j in range(len(idx)):
        # per-structure build scatter on fn AND damping
        if struct_build:
            fdj = fd[j]*math.exp(SIGMA_STRUCT_BUILD*rng.standard_normal())
            ftj = ft[j]*math.exp(SIGMA_STRUCT_BUILD*rng.standard_normal())
            z1j = z1[j]*math.exp(SIGMA_STRUCT_BUILD*rng.standard_normal())
            z2j = z2[j]*math.exp(SIGMA_STRUCT_BUILD*rng.standard_normal())
        else:
            fdj, ftj, z1j, z2j = fd[j], ft[j], z1[j], z2[j]
        gp = chol_r @ rng.standard_normal(len(rfreqs))
        forceps = force_flight*np.exp(gp)*math.exp(bdome[j])   # N^2/Hz (physical, re-derived)
        # interface accelerance response PSD (g^2/Hz), MDOF, PHYSICAL masses
        Hg = np.abs(np.asarray(mdof.interface_accel_per_force_g(fdj, ftj, z1j, z2j, jr, dome_basis,
                                                               tray_flex, m1_eff=m1p, m2_eff=mlp)))**2
        iface_curves[j] = Hg*forceps
        # netCG: physical interface force transfer -> netCG = F_iface/m_load (physical)
        fr = np.abs(np.asarray(mdof.interface_force_per_force(fdj, ftj, z1j, z2j, jr, dome_basis,
                                                             tray_flex, m1_eff=m1p, m_load=mlp)))**2
        psd_acc, psd_g2 = mdof.netcg_psd(fr, forceps, m_load=mlp)
        netcg_curves[j] = psd_g2
        netcg_grms[j] = 3.0*math.sqrt(np.trapz(psd_g2, rfreqs))
    return rfreqs, iface_curves, netcg_curves, netcg_grms


def main():
    t0 = time.time()
    stage_times = {}
    numpyro.set_host_device_count(N_CHAINS)
    for p in (OUT, FIG, FRAMES):
        p.mkdir(parents=True, exist_ok=True)
    D = load_data()
    ts = time.time(); consts, chol_r, meanF_refined = precompute_forcing_consts(D); stage_times["forcing_precompute_s"] = time.time()-ts
    model = make_model(D, consts)

    # PHYSICAL prediction layer: dome bounce-mode effective mass + reverse-engineered forcing
    dome_basis, tray_flex, _ = _bases()
    m1_phys, cap_mass, cap_area = mdof.dome_eff_interface_mass()
    S_orig, fpk, dome_peak = mdof.reverse_engineer_force(dome_basis, m1_phys, DOME_F1, mdof.DOME_ZETA1,
                                                         DOME_RESP_TARGET_G2HZ)
    S_flight = S_orig * 10**(FORCING_OFFSET_DB/10.0)   # -6 dB design envelope
    PHYS.update(m1_phys=m1_phys, m_load_phys=mdof.M_LOAD_PHYS, dome_cap_mass_kg=cap_mass,
                dome_cap_area_m2=cap_area, dome_bounce_particip=mdof.DOME_BOUNCE_PARTICIP,
                force_orig_n2hz=S_orig, force_flight_n2hz=S_flight, dome_resp_peak_freq_hz=fpk,
                dome_resp_target_g2hz=DOME_RESP_TARGET_G2HZ)
    (OUT/"forcing_reverse_engineered.json").write_text(json.dumps(PHYS, indent=2))
    print("PHYS forcing: dome eff mass %.1f kg (cap %.0f kg), orig +6dB force %.2f N^2/Hz, flight %.2f N^2/Hz"
          % (m1_phys, cap_mass, S_orig, S_flight))

    ts = time.time()
    mcmc = run_nuts(model, D["n_builds"], DRAWS, WARMUP, SEED)
    t_fit = time.time()-ts; stage_times["nuts_fit_s"] = t_fit
    diagnostics = diagnostics_from(mcmc, t_fit, consts)
    (OUT/"nuts_diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    post = {k: np.asarray(v) for k, v in mcmc.get_samples().items()}
    np.savez(OUT/"posterior_samples.npz", **post)
    print("CONVERGED:", diagnostics["converged"], "worst_rhat", diagnostics["worst_rank_split_rhat"],
          "min_ess_bulk", diagnostics["min_ess_bulk"], "min_ess_tail", diagnostics["min_ess_tail"],
          "div", diagnostics["divergences"], "fit_s", round(t_fit, 1))

    ts = time.time()
    artifacts = make_all(post, D, consts, chol_r, meanF_refined, diagnostics)
    stage_times["prediction_and_plots_s"] = time.time()-ts

    runtime = {"script_wall_s": round(time.time()-t0, 2),
               "active_compute_stages_s": {k: round(v, 2) for k, v in stage_times.items()},
               "fit_runtime_s": round(t_fit, 2), "smoke_mode": SMOKE}
    (OUT/"runtime_pipeline.json").write_text(json.dumps(runtime, indent=2))
    (OUT/"pipeline_summary.json").write_text(json.dumps({
        "converged": diagnostics["converged"], "nuts_active": diagnostics["nuts_active"],
        "artifacts": artifacts, "fit_runtime_s": t_fit}, indent=2))
    print("DONE pipeline in", round(time.time()-t0, 1), "s")


def standardized_bands(curves, spec_on_grid):
    """ONE standardized envelope band: central 99% = q0.5..q99.5; plus the one-sided 99%-hi exceedance
    fraction (fraction of frequencies where the 99.5th percentile exceeds the spec)."""
    q005, q05, q25, q50, q75, q975, q995 = np.quantile(
        curves, [0.005, 0.025, 0.25, 0.5, 0.75, 0.975, 0.995], axis=0)
    exceed99 = float(np.mean(q995 > spec_on_grid))
    exceed95 = float(np.mean(q975 > spec_on_grid))
    return dict(q005=q005, q025=q05, q50=q50, q975=q975, q995=q995,
                frac_99hi_exceeds_spec=exceed99, frac_95hi_exceeds_spec=exceed95)


def make_all(post, D, consts, chol_r, meanF_refined, diagnostics):
    rng = np.random.default_rng(SEED+1)
    rfreqs = D["rfreqs"]; smooth = D["smooth"]; gfreqs = D["gfreqs"]
    spec_on_refined = np.exp(np.interp(np.log(rfreqs), np.log(gfreqs), np.log(smooth)))
    converged = diagnostics["converged"]
    tag = "" if converged else "  [NOT-YET-CONVERGED]"

    # ---- per-flight ensembles ----
    iface_cache = {}; netcg_cache = {}; grms_cache = {}
    for f in range(D["n_builds"]):
        rf, ic, nc, ng = interface_and_netcg_ensemble(
            post, D, chol_r, f, n_param=300 if SMOKE else 600,
            rng=np.random.default_rng(SEED+200+f))
        iface_cache[f] = ic; netcg_cache[f] = nc; grms_cache[f] = ng

    # global y-limits
    all_hi = [np.quantile(iface_cache[f], 0.995, axis=0).max() for f in iface_cache]
    ymax = max(max(all_hi), smooth.max())*2.0
    ymin = min(min(np.quantile(iface_cache[f], 0.005, axis=0).min() for f in iface_cache), smooth.min())*0.5

    # ---- KEY GIF: interface accelerance response PSD vs spec (standardized band) ----
    band_records = []; frame_files = []
    for f in range(D["n_builds"]):
        curves = iface_cache[f]; B = standardized_bands(curves, spec_on_refined)
        ng = grms_cache[f]
        rec = {"flight_id": f, "build_id": int(D["build_id_of_flight"][f]),
               "iface_peak_mean_psd_g2_per_hz": float(curves.mean(axis=0).max()),
               "iface_peak_freq_hz": float(rfreqs[np.argmax(curves.mean(axis=0))]),
               "iface_frac_99hi_exceeds_spec": B["frac_99hi_exceeds_spec"],
               "iface_frac_95hi_exceeds_spec": B["frac_95hi_exceeds_spec"],
               "netcg_3grms_g_q50": float(np.quantile(ng, 0.5)),
               "netcg_3grms_g_95ci": [float(np.quantile(ng, 0.025)), float(np.quantile(ng, 0.975))],
               "netcg_3grms_g_99ci": [float(np.quantile(ng, 0.005)), float(np.quantile(ng, 0.995))]}
        band_records.append(rec)
        fig, ax = plt.subplots(figsize=(9.6, 5.6))
        ax.fill_between(rfreqs, B["q005"], B["q995"], color="#f1c40f", alpha=0.35,
                        label="central 99% band (q0.5–q99.5)")
        ax.fill_between(rfreqs, B["q025"], B["q975"], color="#2ca02c", alpha=0.40, label="95% band")
        ax.loglog(rfreqs, B["q50"], color="#1f77b4", lw=2.2, label="posterior-predictive median")
        ax.loglog(gfreqs, smooth, color="#d62728", lw=2.2, ls="--", label="test spec (smoothline)")
        ax.set_xlim(rfreqs.min(), rfreqs.max()); ax.set_ylim(ymin, ymax)
        ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("interface accel response PSD [g$^2$/Hz]")
        ax.set_title(f"Flight {f} (build {int(D['build_id_of_flight'][f])}) — coupled INTERFACE accelerance "
                     f"response PSD vs spec{tag}\nMDOF/FBS; 99%-hi exceeds spec at "
                     f"{100*rec['iface_frac_99hi_exceeds_spec']:.1f}% of freqs  |  netCG 3·GRMS "
                     f"q50={rec['netcg_3grms_g_q50']:.3f} g", fontsize=9.0)
        ax.grid(True, which="both", alpha=0.25); ax.legend(loc="lower center", ncol=2, fontsize=8)
        fig.tight_layout()
        ff = FRAMES/f"frame_flight_{f:02d}.png"; fig.savefig(ff, dpi=125); plt.close(fig); frame_files.append(ff)
    gif_path = FIG/"interface_netcg_psd_vs_spec.gif"
    imageio.mimsave(gif_path, [imageio.imread(f) for f in frame_files], duration=1.1, loop=0)
    (OUT/"interface_psd_bands.json").write_text(json.dumps(band_records, indent=2))

    # ---- netCG PSD vs spec headline (worst flight) + antiresonance annotation ----
    worst = int(np.argmax([r["iface_frac_99hi_exceeds_spec"] for r in band_records]))
    make_netcg_headline(netcg_cache[worst], rfreqs, spec_on_refined, gfreqs, smooth, worst, tag)

    # ---- component FRFs (validated transfer functions) ----
    make_component_frfs()

    # ---- forcing overlay ----
    make_forcing_overlay(D)

    # ---- netCG vs vibe reference ----
    make_netcg_vs_vibe(D, grms_cache)

    # ---- resolution sensitivity ----
    res = resolution_sensitivity(D, post)
    (OUT/"resolution_metrics.json").write_text(json.dumps(res, indent=2))

    # ---- sensitivity sweep: -6 dB offset + Matern ell ----
    sens = sensitivity_sweep(D, post)
    (OUT/"sensitivity.json").write_text(json.dumps(sens, indent=2))

    # ---- peak-feature vs whole-PSD comparison (labeled) ----
    pk = peak_feature_comparison(D, post)

    # ---- posterior recovery ----
    posterior_recovery_plot(post)

    # ---- results.json: numeric netCG QOI intervals (95% AND 99%) ----
    all_grms = np.concatenate([grms_cache[f] for f in grms_cache])
    results = {
        "qoi_netCG_3grms_g": {
            "definition": "3*sqrt(integral PSD_Fiface/m_load^2 df); m_load=tray total (136 kg avionics + isogrid panel)",
            "m_load_phys_kg": mdof.M_LOAD_PHYS,
            "overall_q50": float(np.quantile(all_grms, 0.5)),
            "overall_95ci": [float(np.quantile(all_grms, 0.025)), float(np.quantile(all_grms, 0.975))],
            "overall_99ci": [float(np.quantile(all_grms, 0.005)), float(np.quantile(all_grms, 0.995))],
            "per_flight": [{"flight_id": r["flight_id"], "q50": r["netcg_3grms_g_q50"],
                            "ci95": r["netcg_3grms_g_95ci"], "ci99": r["netcg_3grms_g_99ci"]}
                           for r in band_records]},
        "headline_narrowband_exceedance": {
            "worst_flight": worst,
            "worst_flight_frac_99hi_exceeds_spec": band_records[worst]["iface_frac_99hi_exceeds_spec"],
            "worst_flight_frac_95hi_exceeds_spec": band_records[worst]["iface_frac_95hi_exceeds_spec"],
            "band_definition": "central 99% = q0.5..q99.5; one-sided 99%-hi exceedance fraction per flight",
            "note": "A large overall scalar margin can coexist with a narrow-band 99% exceedance at a coupled resonance."},
        "anchors": {"dome_mode1_hz": DOME_F1, "tray_mode1_hz": TRAY_F1},
        "forcing_reverse_engineered": {
            "process": "flat ORIGINAL (+6 dB initial) force PSD chosen so the DOME-ONLY interface response "
                       "peaks at 0.1 g^2/Hz at the bounce mode; flight mean = -6 dB design envelope",
            "dome_bounce_eff_mass_kg": PHYS["m1_phys"], "dome_cap_mass_kg": PHYS["dome_cap_mass_kg"],
            "dome_bounce_participation": PHYS["dome_bounce_particip"],
            "force_orig_plus6dB_n2hz": PHYS["force_orig_n2hz"],
            "force_flight_minus6dB_n2hz": PHYS["force_flight_n2hz"],
            "dome_resp_target_g2hz": PHYS["dome_resp_target_g2hz"],
            "dome_resp_peak_freq_hz": PHYS["dome_resp_peak_freq_hz"],
            "m_load_phys_kg": PHYS["m_load_phys"],
            "note": "DEVIATION from round-2 abstract scaling (per human direction): forcing and masses are now "
                    "PHYSICAL; netCG is physically scaled (no longer abstract milli-g)."},
        "converged": converged, "nuts_active": diagnostics["nuts_active"],
        "resolution": res, "sensitivity": sens, "peak_feature_comparison": pk,
    }
    (OUT/"results.json").write_text(json.dumps(results, indent=2))

    return {"gif": str(gif_path.relative_to(OUT)), "n_frames": len(frame_files),
            "interface_psd_bands": "interface_psd_bands.json", "results": "results.json",
            "component_frfs": "figures/component_frfs.png", "netcg_headline": "figures/netcg_psd_headline.png"}


def make_netcg_headline(netcg_curves, rfreqs, spec_refined, gfreqs, smooth, flight, tag):
    B = standardized_bands(netcg_curves, spec_refined)
    # antiresonance: find local minima of median netCG PSD
    med = B["q50"]; logm = np.log10(med)
    anti = [i for i in range(1, len(med)-1) if logm[i] < logm[i-1] and logm[i] < logm[i+1]]
    fig, ax = plt.subplots(figsize=(9.8, 5.6))
    ax.fill_between(rfreqs, B["q005"], B["q995"], color="#f1c40f", alpha=0.35, label="central 99% band (q0.5–q99.5)")
    ax.fill_between(rfreqs, B["q025"], B["q975"], color="#2ca02c", alpha=0.40, label="95% band")
    ax.loglog(rfreqs, med, color="#6a0dad", lw=2.3, label="netCG PSD median (physical m_load)")
    ax.loglog(gfreqs, smooth, color="#d62728", lw=2.0, ls="--", label="test spec (smoothline) [reference]")
    if anti:
        ai = anti[int(np.argmin([med[a] for a in anti]))]
        ax.plot(rfreqs[ai], med[ai], "bv", ms=11, label=f"drive-point antiresonance ~{rfreqs[ai]:.0f} Hz")
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("netCG accel PSD [g$^2$/Hz] (log)")
    ax.set_title(f"netCG (net CG acceleration of the load) PSD — flight {flight}{tag}\n"
                 "QOI = F_interface/m_load (force-limited vibration / NASA-HDBK-7004 framing); "
                 "antiresonance notch shown", fontsize=9.0)
    ax.grid(True, which="both", alpha=0.25); ax.legend(loc="lower center", ncol=2, fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/"netcg_psd_headline.png", dpi=150); plt.close(fig)


def make_component_frfs():
    dome_basis, tray_flex, b = _bases()
    m1p = PHYS["m1_phys"]; mlp = PHYS["m_load_phys"]
    freqs = np.geomspace(20.0, 2000.0, 4000); jf = jnp.asarray(freqs)
    Ys = np.asarray(mdof.source_accelerance(DOME_F1, mdof.DOME_ZETA1, jf, dome_basis[0], dome_basis[1], m1_eff=m1p))
    ML = np.asarray(mdof.load_apparent_mass(TRAY_F1, mdof.TRAY_ZETA1, jf, tray_flex, m_load=mlp))
    H = np.asarray(mdof.interface_accel_per_force_g(DOME_F1, TRAY_F1, mdof.DOME_ZETA1, mdof.TRAY_ZETA1,
                                                    jf, dome_basis, tray_flex, m1_eff=m1p, m2_eff=mlp))
    frc = np.abs(np.asarray(mdof.interface_force_per_force(DOME_F1, TRAY_F1, mdof.DOME_ZETA1, mdof.TRAY_ZETA1,
                                                           jf, dome_basis, tray_flex, m1_eff=m1p, m_load=mlp)))
    fig, axes = plt.subplots(2, 2, figsize=(13, 8))
    ax = axes[0, 0]; ax.loglog(freqs, np.abs(Ys), color="#1f77b4", label="|Y_s| source free-iface accelerance")
    ax.set_title("Source (dome) free-interface accelerance"); ax.set_xlabel("freq [Hz] (log)")
    ax.set_ylabel("|a/F| [(m/s²)/N]"); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    ax = axes[0, 1]; ax.loglog(freqs, np.abs(ML), color="#2ca02c", label="|M_L| load apparent mass")
    ax.axhline(mlp, color="gray", ls=":", label=f"low-freq limit m_load={mlp:.0f} kg (physical)")
    ax.set_title("Load (tray) interface apparent mass"); ax.set_xlabel("freq [Hz] (log)")
    ax.set_ylabel("|F/a| [kg]"); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    ax = axes[1, 0]; ax.loglog(freqs, np.abs(H), color="#6a0dad", label="|H_iface| coupled accelerance (g/N)")
    ax.set_title("Coupled interface accelerance (drive-point; antiresonance notch)")
    ax.set_xlabel("freq [Hz] (log)"); ax.set_ylabel("|a/F| [g/N]"); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    ax = axes[1, 1]; ax.loglog(freqs, frc, color="#d62728", label="|F_iface/F_ext| force transfer")
    ax.set_title("Coupled interface FORCE transfer (netCG numerator)")
    ax.set_xlabel("freq [Hz] (log)"); ax.set_ylabel("|F_iface/F_ext| [-]"); ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    fig.suptitle("Key MDOF transfer functions at the single interface DOF (calibrated; dome mode1=93.5, tray mode1=86.25)", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG/"component_frfs.png", dpi=140); plt.close(fig)


def make_forcing_overlay(D):
    """Forcing overlay using the RE-DERIVED physical force (reverse-engineered so the dome-only
    interface response peaks at 0.1 g^2/Hz at the bounce mode under the +6 dB initial forcing)."""
    gf = D["gfreqs"]; S_orig = PHYS["force_orig_n2hz"]; S_flight = PHYS["force_flight_n2hz"]
    dome_basis, tray_flex, _ = _bases(); m1p = PHYS["m1_phys"]
    Ys = np.asarray(mdof.source_accelerance(DOME_F1, mdof.DOME_ZETA1, jnp.asarray(gf), dome_basis[0], dome_basis[1], m1_eff=m1p))
    dome_resp_orig = np.abs(Ys/G0)**2 * S_orig   # g^2/Hz dome-only interface response under +6 dB
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 5.3))
    ax = axes[0]
    ax.loglog(gf, np.full_like(gf, S_orig), color="#222222", lw=2.4, label=f"+6 dB INITIAL forcing (re-derived) = {S_orig:.0f} N²/Hz")
    ax.loglog(gf, np.full_like(gf, S_flight), color="#1f77b4", lw=2.0, ls="--", label=f"flight mean (−6 dB design envelope) = {S_flight:.0f} N²/Hz")
    rng_f = np.random.default_rng(SEED+50)
    chol_g = np.linalg.cholesky((SIGMA_F2F_LN**2)*matern32_corr_lnfreq(gf, FORCING_ELL) + 1e-10*np.eye(len(gf)))
    for i in range(D["n_builds"]):
        draw = S_flight*np.exp(chol_g @ rng_f.standard_normal(len(gf)))
        ax.loglog(gf, draw, color="#ff7f0e", lw=0.9, alpha=0.6, label="flight forcing draws (11)" if i == 0 else None)
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("force PSD [N$^2$/Hz]")
    ax.set_title("Re-derived physical forcing\n−6 dB flight offset = pre-data conservative DESIGN ENVELOPE (2× GRMS), NOT a GEVS margin", fontsize=9.0)
    ax.grid(True, which="both", alpha=0.25); ax.legend(loc="lower left", fontsize=7.5)
    ax = axes[1]
    ax.loglog(gf, dome_resp_orig, color="#6a0dad", lw=2.2, label="dome-only INTERFACE response under +6 dB")
    ax.axhline(PHYS["dome_resp_target_g2hz"], color="#d62728", ls="--", lw=2.0, label="reverse-engineer target = 0.1 g²/Hz")
    ax.axvline(PHYS["dome_resp_peak_freq_hz"], color="gray", ls=":", label=f"bounce mode {PHYS['dome_resp_peak_freq_hz']:.0f} Hz")
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("dome interface response PSD [g$^2$/Hz]")
    ax.set_title("Reverse-engineering check: dome interface response peaks at 0.1 g²/Hz at the bounce mode", fontsize=9.0)
    ax.grid(True, which="both", alpha=0.25); ax.legend(loc="lower center", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG/"flight_forcing_overlay.png", dpi=150); plt.close(fig)


def make_netcg_vs_vibe(D, grms_cache):
    fids = np.arange(D["n_builds"])
    q50 = [np.quantile(grms_cache[f], 0.5) for f in fids]
    lo = [np.quantile(grms_cache[f], 0.025) for f in fids]; hi = [np.quantile(grms_cache[f], 0.975) for f in fids]
    fig, ax = plt.subplots(figsize=(9.8, 5.4))
    ax.errorbar(fids, q50, yerr=[np.array(q50)-np.array(lo), np.array(hi)-np.array(q50)], fmt="o-",
                color="#6a0dad", capsize=3, label="netCG 3·GRMS (median, 95% CI) per flight")
    ax.axhline(D["smooth_3grms"], color="#444444", ls=":", lw=2.0, label=f"smoothline input 3·GRMS = {D['smooth_3grms']:.1f} g (vibe reference)")
    ax.set_xlabel("flight id"); ax.set_ylabel("netCG 3·GRMS [g] (log)"); ax.set_yscale("log")
    ax.set_title("netCG QOI (net CG accel of the 136 kg load) per flight vs vibe-test reference\n"
                 "netCG is force-limited (interface force / load mass) — DISTINCT from the round-2 tray-response 3·GRMS", fontsize=9.0)
    ax.set_xticks(fids); ax.grid(True, which="both", alpha=0.25); ax.legend(fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG/"netcg_vs_vibe_reference.png", dpi=150); plt.close(fig)


def resolution_sensitivity(D, post):
    gfreqs = D["gfreqs"]; rfreqs = D["rfreqs"]
    dome_basis, tray_flex, _ = _bases()
    fd = math.exp(float(np.median(post["log_f_dome"]))); ft = math.exp(float(np.median(post["log_f_tray"])))
    z1 = math.exp(float(np.median(post["log_zeta_dome"]))); z2 = math.exp(float(np.median(post["log_zeta_tray"])))
    m1p = PHYS["m1_phys"]; mlp = PHYS["m_load_phys"]; meanF = PHYS["force_flight_n2hz"]
    def q3(freqs):
        jf = jnp.asarray(freqs)
        Hg = np.abs(np.asarray(mdof.interface_accel_per_force_g(fd, ft, z1, z2, jf, dome_basis, tray_flex,
                                                              m1_eff=m1p, m2_eff=mlp)))**2*meanF
        return 3*math.sqrt(np.trapz(Hg, freqs)), Hg
    refgrid = np.geomspace(20.0, 2000.0, 60000)
    qi_c, Hc = q3(gfreqs); qi_r, Hr = q3(rfreqs); qi_ref, Href = q3(refgrid)
    def peak_near(freqs, mag, lo, hi):
        m = (freqs >= lo) & (freqs <= hi)
        return float(mag[m].max())
    pk_c = peak_near(gfreqs, Hc, 58, 67); pk_r = peak_near(rfreqs, Hr, 58, 67); pk_ref = peak_near(refgrid, Href, 58, 67)
    res = {"grid_global_points": len(gfreqs), "grid_refined_points": len(rfreqs), "reference_points": len(refgrid),
           "global_min_dlog_freq": float(np.min(np.diff(np.log(gfreqs)))),
           "interface_3grms_coarse_g": qi_c, "interface_3grms_refined_g": qi_r, "interface_3grms_reference_g": qi_ref,
           "interface_3grms_coarse_err_vs_ref": (qi_c-qi_ref)/qi_ref, "interface_3grms_refined_err_vs_ref": (qi_r-qi_ref)/qi_ref,
           "peak62_coarse_clip_frac": (pk_ref-pk_c)/pk_ref, "peak62_refined_clip_frac": (pk_ref-pk_r)/pk_ref,
           "rationale": "refined grid adds mode-local clusters whose width scales with each mode's half-power "
                        "bandwidth (~2*zeta*fn); no hard-coded lines-per-band. QOI integral is robust; coarse "
                        "grid clips the narrow 62 Hz peak tip (reported)."}
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.0))
    for ax, (lo, hi, lbl) in zip(axes, [(55, 72, "coupled mode ~62 Hz (narrow)"), (110, 135, "coupled mode ~119 Hz")]):
        mg = (gfreqs >= lo)&(gfreqs <= hi); mr = (rfreqs >= lo)&(rfreqs <= hi); mref = (refgrid >= lo)&(refgrid <= hi)
        ax.plot(refgrid[mref], Href[mref], "-", color="#888888", lw=1.4, label="60k-pt reference")
        ax.plot(gfreqs[mg], Hc[mg], "s--", color="#d62728", ms=5, label="global grid (coarse)")
        ax.plot(rfreqs[mr], Hr[mr], ".-", color="#1f77b4", ms=4, lw=1.0, label="mode-refined grid")
        ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("interface accel²/force² × meanF [g²/Hz]")
        ax.set_title(lbl, fontsize=9); ax.grid(True, alpha=0.25); ax.legend(fontsize=8)
    fig.suptitle(f"Resolution sensitivity: 62 Hz peak tip clipped {100*res['peak62_coarse_clip_frac']:.1f}% (coarse) / "
                 f"{100*res['peak62_refined_clip_frac']:.2f}% (refined); interface 3·GRMS QOI err vs 60k-ref "
                 f"{100*res['interface_3grms_coarse_err_vs_ref']:+.2f}% / {100*res['interface_3grms_refined_err_vs_ref']:+.2f}%", fontsize=9)
    fig.tight_layout(); fig.savefig(FIG/"resolution_sensitivity.png", dpi=150); plt.close(fig)
    return res


def sensitivity_sweep(D, post):
    """Sweep the -6 dB design-envelope offset and the Matern length-scale; report netCG 3GRMS shift."""
    dome_basis, tray_flex, _ = _bases()
    fd = math.exp(float(np.median(post["log_f_dome"]))); ft = math.exp(float(np.median(post["log_f_tray"])))
    z1 = math.exp(float(np.median(post["log_zeta_dome"]))); z2 = math.exp(float(np.median(post["log_zeta_tray"])))
    m1p = PHYS["m1_phys"]; mlp = PHYS["m_load_phys"]; S_orig = PHYS["force_orig_n2hz"]
    rfreqs = D["rfreqs"]; jf = jnp.asarray(rfreqs)
    fr2 = np.abs(np.asarray(mdof.interface_force_per_force(fd, ft, z1, z2, jf, dome_basis, tray_flex,
                                                          m1_eff=m1p, m_load=mlp)))**2
    offsets = [-9.0, -6.0, -3.0, 0.0]; ells = [0.04, 0.08, 0.16]
    rng = np.random.default_rng(SEED+321)
    offset_rows = []
    for off in offsets:
        base_mean = S_orig*10**(off/10.0)   # force at this offset below the +6 dB original (re-derived)
        ng = []
        for _ in range(200 if not SMOKE else 40):
            chol = np.linalg.cholesky((SIGMA_F2F_LN**2)*matern32_corr_lnfreq(rfreqs, FORCING_ELL)+1e-10*np.eye(len(rfreqs)))
            forceps = base_mean*np.exp(chol @ rng.standard_normal(len(rfreqs)))
            _, psd_g2 = mdof.netcg_psd(fr2, forceps, m_load=mlp)
            ng.append(3*math.sqrt(np.trapz(psd_g2, rfreqs)))
        offset_rows.append({"offset_db": off, "netcg_3grms_q50": float(np.quantile(ng, 0.5)),
                            "netcg_3grms_95ci": [float(np.quantile(ng, 0.025)), float(np.quantile(ng, 0.975))]})
    ell_rows = []
    base_mean = S_orig*10**(FORCING_OFFSET_DB/10.0)
    for ell in ells:
        chol = np.linalg.cholesky((SIGMA_F2F_LN**2)*matern32_corr_lnfreq(rfreqs, ell)+1e-10*np.eye(len(rfreqs)))
        ng = []
        for _ in range(200 if not SMOKE else 40):
            forceps = base_mean*np.exp(chol @ rng.standard_normal(len(rfreqs)))
            _, psd_g2 = mdof.netcg_psd(fr2, forceps, m_load=mlp)
            ng.append(3*math.sqrt(np.trapz(psd_g2, rfreqs)))
        ell_rows.append({"matern_ell": ell, "netcg_3grms_q50": float(np.quantile(ng, 0.5)),
                         "netcg_3grms_95ci": [float(np.quantile(ng, 0.025)), float(np.quantile(ng, 0.975))]})
    # dome bounce-mode effective-mass (participation) sweep — NEW key assumption. Note the forcing is
    # RE-DERIVED for each mass (so dome response stays pinned at 0.1 g^2/Hz), exposing the net effect.
    mass_rows = []
    for a in [0.25, 0.40, 0.55]:
        m1a, _, _ = mdof.dome_eff_interface_mass(particip=a)
        S_o, _, _ = mdof.reverse_engineer_force(dome_basis, m1a, DOME_F1, mdof.DOME_ZETA1, DOME_RESP_TARGET_G2HZ)
        base = S_o*10**(FORCING_OFFSET_DB/10.0)
        fr2a = np.abs(np.asarray(mdof.interface_force_per_force(fd, ft, z1, z2, jf, dome_basis, tray_flex,
                                                              m1_eff=m1a, m_load=mlp)))**2
        chol = np.linalg.cholesky((SIGMA_F2F_LN**2)*matern32_corr_lnfreq(rfreqs, FORCING_ELL)+1e-10*np.eye(len(rfreqs)))
        ng = []
        for _ in range(200 if not SMOKE else 40):
            forceps = base*np.exp(chol @ rng.standard_normal(len(rfreqs)))
            _, psd_g2 = mdof.netcg_psd(fr2a, forceps, m_load=mlp)
            ng.append(3*math.sqrt(np.trapz(psd_g2, rfreqs)))
        mass_rows.append({"bounce_particip": a, "dome_eff_mass_kg": float(m1a),
                          "rederived_orig_force_n2hz": float(S_o),
                          "netcg_3grms_q50": float(np.quantile(ng, 0.5)),
                          "netcg_3grms_95ci": [float(np.quantile(ng, 0.025)), float(np.quantile(ng, 0.975))]})
    fig, axes = plt.subplots(1, 3, figsize=(16.5, 5.0))
    ax = axes[0]; offs = [r["offset_db"] for r in offset_rows]; q = [r["netcg_3grms_q50"] for r in offset_rows]
    lo = [r["netcg_3grms_95ci"][0] for r in offset_rows]; hi = [r["netcg_3grms_95ci"][1] for r in offset_rows]
    ax.errorbar(offs, q, yerr=[np.array(q)-np.array(lo), np.array(hi)-np.array(q)], fmt="o-", capsize=3, color="#6a0dad", label="netCG 3·GRMS (median, 95%)")
    ax.axvline(-6.0, color="gray", ls="--", label="baseline −6 dB design envelope")
    ax.set_xlabel("flight-mean forcing offset [dB(PSD)]"); ax.set_ylabel("netCG 3·GRMS [g]")
    ax.set_title("Sensitivity to design-envelope offset"); ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    ax = axes[1]; e = [r["matern_ell"] for r in ell_rows]; q = [r["netcg_3grms_q50"] for r in ell_rows]
    lo = [r["netcg_3grms_95ci"][0] for r in ell_rows]; hi = [r["netcg_3grms_95ci"][1] for r in ell_rows]
    ax.errorbar(e, q, yerr=[np.array(q)-np.array(lo), np.array(hi)-np.array(q)], fmt="s-", capsize=3, color="#2ca02c", label="netCG 3·GRMS (median, 95%)")
    ax.axvline(0.08, color="gray", ls="--", label="baseline ℓ=0.08")
    ax.set_xlabel("Matérn-3/2 log-frequency length scale ℓ"); ax.set_ylabel("netCG 3·GRMS [g]")
    ax.set_title("Sensitivity to forcing GP length-scale"); ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    ax = axes[2]; mm = [r["dome_eff_mass_kg"] for r in mass_rows]; q = [r["netcg_3grms_q50"] for r in mass_rows]
    lo = [r["netcg_3grms_95ci"][0] for r in mass_rows]; hi = [r["netcg_3grms_95ci"][1] for r in mass_rows]
    ax.errorbar(mm, q, yerr=[np.array(q)-np.array(lo), np.array(hi)-np.array(q)], fmt="^-", capsize=3, color="#1f77b4", label="netCG 3·GRMS (median, 95%)")
    ax.axvline(PHYS["m1_phys"], color="gray", ls="--", label=f"baseline {PHYS['m1_phys']:.0f} kg (particip 0.40)")
    ax.set_xlabel("dome bounce-mode effective interface mass [kg]"); ax.set_ylabel("netCG 3·GRMS [g]")
    ax.set_title("Sensitivity to dome bounce effective mass\n(forcing RE-DERIVED per mass: dome resp pinned 0.1 g²/Hz)")
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    fig.suptitle("Decision sensitivity: −6 dB offset, Matérn length-scale (3 dB f2f fixed), dome bounce effective mass", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG/"sensitivity_offset_ell.png", dpi=150); plt.close(fig)
    return {"offset_sweep": offset_rows, "ell_sweep": ell_rows, "dome_mass_sweep": mass_rows,
            "note": "offset sweep is relative to the RE-DERIVED +6 dB original force; dome-mass sweep re-derives the "
                    "force at each mass so the dome interface response stays pinned at 0.1 g^2/Hz at the bounce mode."}


def peak_feature_comparison(D, post):
    """LABELED comparison: whole-PSD likelihood (default) vs a peak-only feature fit of the tray vibe peak.
    Shows the peak-only summary recovers a similar fundamental but discards band information."""
    gfreqs = D["gfreqs"]; vibe = D["vibe_obs"]
    ipk = int(np.argmax(vibe)); f_peak = float(gfreqs[ipk])
    # whole-PSD posterior median tray fn
    ft_whole = math.exp(float(np.median(post["log_f_tray"])))
    return {"whole_psd_tray_fn_hz_median": ft_whole, "peak_only_tray_fn_hz_estimate": f_peak,
            "diff_hz": abs(ft_whole - f_peak),
            "note": "WHOLE-PSD/FRF likelihood is the default (uses all 260 bins + 3 FRF curves + 11 flights). "
                    "Peak-only feature (argmax of vibe PSD) is a LABELED comparison; it recovers a similar tray "
                    "fundamental but discards band shape, damping identifiability, and off-peak fit."}


def posterior_recovery_plot(post):
    truths = {"dome f_n [Hz]": DOME_F1, "tray f_n [Hz]": TRAY_F1,
              "zeta_dome": r2.TRUE_ZETA1, "zeta_tray": r2.TRUE_ZETA2}
    samples = {"dome f_n [Hz]": np.exp(post["log_f_dome"]), "tray f_n [Hz]": np.exp(post["log_f_tray"]),
               "zeta_dome": np.exp(post["log_zeta_dome"]), "zeta_tray": np.exp(post["log_zeta_tray"])}
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, (name, s) in zip(axes.ravel(), samples.items()):
        ax.hist(s, bins=50, color="#1f77b4", alpha=0.7, density=True, label="posterior")
        ax.axvline(truths[name], color="#d62728", lw=2.0, ls="--", label=f"truth = {truths[name]:.4g}")
        ax.set_title(name, fontsize=9.5); ax.set_ylabel("density"); ax.legend(fontsize=8); ax.grid(True, alpha=0.2)
    fig.suptitle("Posterior recovery of component fundamentals & damping vs synthetic truth (priors centered at nominal 110/75 Hz)", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG/"posterior_recovery.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    main()
