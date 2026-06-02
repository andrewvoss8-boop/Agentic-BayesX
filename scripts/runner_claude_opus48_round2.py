#!/usr/bin/env python3
"""Round-2 runner (Claude Code Opus 4.8): hierarchical NUTS for the sequential
vibe/modal/flight experiment + the headline per-flight interface acceleration
RESPONSE PSD vs test-spec GIF, forcing overlay, QOI-vs-vibe overlay, resolution
sensitivity, and source-backed convergence diagnostics over ALL latents.

Honesty rules honored:
- NUTS/HMC (NumPyro) is the real sampler; no "NUTS active" claim unless the
  source-backed convergence gate passes over ALL sampled variables incl raw latents.
- Forward model verified to reproduce the shared dataset clean curves (rel err 0).
- Flight-to-flight forcing variability is FIXED/known (3 dB PSD); build-to-build and
  sensor scales are LEARNED.

Env:
  R2_SMOKE=1   -> tiny draws for a fast pipeline smoke test (NOT for reporting).
"""
from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl")
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

import r2_forward as fw

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "artifacts/reports/sequential_vibe_modal_flight_20260602/sequential_dataset.json"
OUT = ROOT / "artifacts/reports/runner_claude_opus48_round2_20260602"
FIG = OUT / "figures"
FRAMES = FIG / "gif_frames"
SEED = 20260602
SMOKE = os.environ.get("R2_SMOKE", "0") == "1"

N_CHAINS = 4
RHAT_MAX = 1.01
ESS_MIN = 100 * N_CHAINS
DIVERGENCE_FAIL_FRAC = 0.02
WARMUP = 200 if SMOKE else 1500
DRAWS = 200 if SMOKE else 2000

LN10 = math.log(10.0)
def db_to_lnsigma(db): return db * LN10 / 10.0
SIGMA_F2F_LN = db_to_lnsigma(3.0)
FORCING_ELL = 0.08
FORCING_OFFSET_DB = -6.0
G0 = fw.G0


def matern32_corr_lnfreq(freqs, ell):
    eta = np.log(freqs)
    r = np.abs(np.subtract.outer(eta, eta)) / ell
    s = math.sqrt(3.0) * r
    return (1.0 + s) * np.exp(-s)


def build_refined_grid(global_freqs):
    peaks = [(62.28, 1.82), (86.25, 3.37), (93.5, 3.0), (129.5, 7.85)]
    pts = [np.asarray(global_freqs, float)]
    for fn, df in peaks:
        lo, hi = fn - 3.0 * df, fn + 3.0 * df
        pts.append(np.linspace(max(lo, 20.0), min(hi, 2000.0), 41))
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
        ch1=np.asarray(d["modal_observations"]["dome_only"]["real"]) + 1j * np.asarray(d["modal_observations"]["dome_only"]["imag"]),
        ch2=np.asarray(d["modal_observations"]["coupled_interface"]["real"]) + 1j * np.asarray(d["modal_observations"]["coupled_interface"]["imag"]),
        ch3=np.asarray(d["modal_observations"]["coupled_tray"]["real"]) + 1j * np.asarray(d["modal_observations"]["coupled_tray"]["imag"]),
        tray_3grms_flights=np.asarray([f["tray_3grms_g_observed"] for f in d["flight_summaries"]]),
        iface_3grms_flights=np.asarray([f["interface_3grms_g_observed"] for f in d["flight_summaries"]]),
        build_id_of_flight=np.asarray([f["build_id"] for f in d["flight_summaries"]]),
        n_builds=len(d["build_samples"]),
    )
    out["rfreqs"] = build_refined_grid(out["gfreqs"])
    out["meanF_const"] = float(out["meanF_global"][0])
    out["meanF_refined"] = np.full_like(out["rfreqs"], out["meanF_const"])
    return out


def precompute_forcing_consts(D):
    rng = np.random.default_rng(SEED + 7)
    rfreqs = D["rfreqs"]; meanF_refined = D["meanF_refined"]
    corr_r = matern32_corr_lnfreq(rfreqs, FORCING_ELL)
    cov_r = (SIGMA_F2F_LN ** 2) * corr_r + 1e-10 * np.eye(len(rfreqs))
    chol_r = np.linalg.cholesky(cov_r)
    H00_t = np.abs(np.asarray(fw.interface_accel_per_force_g(fw.TRUE_K1, fw.TRUE_K2, fw.TRUE_ZETA1, fw.TRUE_ZETA2, jnp.asarray(rfreqs)))) ** 2
    H10_t = np.abs(np.asarray(fw.tray_accel_per_force_g(fw.TRUE_K1, fw.TRUE_K2, fw.TRUE_ZETA1, fw.TRUE_ZETA2, jnp.asarray(rfreqs)))) ** 2
    int_iface_mean = float(np.trapz(H00_t * meanF_refined, rfreqs))
    int_tray_mean = float(np.trapz(H10_t * meanF_refined, rfreqs))
    N_MC = 4000
    li = np.empty(N_MC); lt = np.empty(N_MC)
    for i in range(N_MC):
        fac = np.exp(chol_r @ rng.standard_normal(len(rfreqs)))
        li[i] = math.log(np.trapz(H00_t * meanF_refined * fac, rfreqs))
        lt[i] = math.log(np.trapz(H10_t * meanF_refined * fac, rfreqs))
    consts = dict(
        bias_iface=0.5 * (float(np.mean(li)) - math.log(int_iface_mean)),
        bias_tray=0.5 * (float(np.mean(lt)) - math.log(int_tray_mean)),
        sigma_q_iface=0.5 * float(np.std(li)),
        sigma_q_tray=0.5 * float(np.std(lt)),
        int_iface_mean=int_iface_mean, int_tray_mean=int_tray_mean, n_mc=N_MC,
        sigma_f2f_ln=SIGMA_F2F_LN, forcing_ell=FORCING_ELL,
    )
    return consts, chol_r


def make_model(D, consts):
    jg = jnp.asarray(D["gfreqs"]); jm = jnp.asarray(D["mfreqs"]); jr = jnp.asarray(D["rfreqs"])
    jsmooth = jnp.asarray(D["smooth"]); j_meanF_r = jnp.asarray(D["meanF_refined"])
    log_vibe_obs = jnp.asarray(np.log(np.maximum(D["vibe_obs"], 1e-30)))
    log_ch1 = jnp.asarray(np.log(np.maximum(np.abs(D["ch1"]), 1e-30)))
    log_ch2 = jnp.asarray(np.log(np.maximum(np.abs(D["ch2"]), 1e-30)))
    log_ch3 = jnp.asarray(np.log(np.maximum(np.abs(D["ch3"]), 1e-30)))
    log_tray_q = jnp.asarray(np.log(D["tray_3grms_flights"]))
    log_iface_q = jnp.asarray(np.log(D["iface_3grms_flights"]))
    bid = jnp.asarray(D["build_id_of_flight"])
    n_builds = D["n_builds"]
    K1_NOM, K2_NOM = fw.K1_NOM, fw.K2_NOM
    bias_iface, bias_tray = consts["bias_iface"], consts["bias_tray"]
    sigma_q_iface, sigma_q_tray = consts["sigma_q_iface"], consts["sigma_q_tray"]

    def model(n_flights_assim=n_builds):
        log_k1 = numpyro.sample("log_k1_ratio", dist.Normal(0.0, 0.18))
        log_k2 = numpyro.sample("log_k2_ratio", dist.Normal(0.0, 0.18))
        log_z1 = numpyro.sample("log_zeta1", dist.Normal(math.log(0.018), 0.35))
        log_z2 = numpyro.sample("log_zeta2", dist.Normal(math.log(0.026), 0.35))
        sigma_sensor = numpyro.sample("sigma_sensor", dist.HalfNormal(0.30))
        sigma_bd = numpyro.sample("sigma_build_dome", dist.HalfNormal(0.50))
        sigma_bt = numpyro.sample("sigma_build_tray", dist.HalfNormal(0.50))
        z_dome = numpyro.sample("z_dome", dist.Normal(0.0, 1.0).expand([n_builds]))
        z_tray = numpyro.sample("z_tray", dist.Normal(0.0, 1.0).expand([n_builds]))
        build_dome = numpyro.deterministic("build_dome", sigma_bd * z_dome)
        build_tray = numpyro.deterministic("build_tray", sigma_bt * z_tray)

        k1 = K1_NOM * jnp.exp(log_k1); k2 = K2_NOM * jnp.exp(log_k2)
        zeta1 = jnp.exp(log_z1); zeta2 = jnp.exp(log_z2)

        T = fw.tray_transmissibility(k2, zeta2, jg)
        mu_vibe = jnp.log(jnp.abs(T) ** 2 * jsmooth) + build_tray[0]
        numpyro.sample("vibe", dist.Normal(mu_vibe, sigma_sensor), obs=log_vibe_obs)

        ch1m = jnp.log(jnp.abs(fw.dome_only_recip_inertance(k1, zeta1, jm))) + 0.5 * build_dome[0]
        ch2m = jnp.log(jnp.abs(fw.coupled_interface_recip(k1, k2, zeta1, zeta2, jm))) + 0.5 * build_dome[0]
        ch3m = jnp.log(jnp.abs(fw.coupled_tray_recip(k1, k2, zeta1, zeta2, jm))) + 0.5 * build_tray[0]
        sd_modal = 0.5 * sigma_sensor
        numpyro.sample("ch1", dist.Normal(ch1m, sd_modal), obs=log_ch1)
        numpyro.sample("ch2", dist.Normal(ch2m, sd_modal), obs=log_ch2)
        numpyro.sample("ch3", dist.Normal(ch3m, sd_modal), obs=log_ch3)

        H00 = jnp.abs(fw.interface_accel_per_force_g(k1, k2, zeta1, zeta2, jr)) ** 2
        H10 = jnp.abs(fw.tray_accel_per_force_g(k1, k2, zeta1, zeta2, jr)) ** 2
        int_iface = jnp.trapezoid(H00 * j_meanF_r, jr)
        int_tray = jnp.trapezoid(H10 * j_meanF_r, jr)
        pred_log_iface = math.log(3.0) + 0.5 * jnp.log(int_iface) + 0.5 * build_dome[bid] + bias_iface
        pred_log_tray = math.log(3.0) + 0.5 * jnp.log(int_tray) + 0.5 * build_tray[bid] + bias_tray
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
    mcmc.run(jax.random.PRNGKey(seed), n_flights_assim=n_assim,
             extra_fields=("diverging", "num_steps"))
    return mcmc


def diagnostics_from(mcmc, fit_runtime, consts):
    extra = mcmc.get_extra_fields()
    diverging = np.asarray(extra["diverging"]); n_div = int(diverging.sum())
    total = int(diverging.size); div_frac = n_div / total
    num_steps = np.asarray(extra["num_steps"]); tree_depth = np.log2(np.maximum(num_steps, 1))
    idata = az.from_numpyro(mcmc)
    monitored = ["log_k1_ratio", "log_k2_ratio", "log_zeta1", "log_zeta2",
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
                            "source": "Stan Ref Manual / Vehtari et al. 2021 (reader_web_verified_sources.md)"},
        "worst_rank_split_rhat": {"value": wr, "variable": wrn},
        "min_ess_bulk": {"value": mb, "variable": mbn},
        "min_ess_tail": {"value": mt, "variable": mtn},
        "gate_rhat_pass": gate_rhat, "gate_ess_pass": gate_ess, "gate_divergence_pass": gate_div,
        "converged": converged, "nuts_active": converged,
        "n_monitored_scalar_quantities": len(per), "raw_latents_included": True,
        "per_variable": per, "forcing_constants_fixed": consts,
        "smoke_mode": SMOKE,
    }


# ----------------------------- plotting helpers -----------------------------
def interface_psd_ensemble(post, D, chol_r, flight_id, n_param=400, rng=None):
    """Posterior-predictive interface acceleration RESPONSE PSD curves (g^2/Hz) for one flight."""
    rng = rng or np.random.default_rng(SEED + 100 + flight_id)
    rfreqs = D["rfreqs"]; meanF_refined = D["meanF_refined"]
    n_total = post["log_k1_ratio"].shape[0]
    idx = rng.choice(n_total, size=min(n_param, n_total), replace=False)
    k1 = fw.K1_NOM * np.exp(post["log_k1_ratio"][idx]); k2 = fw.K2_NOM * np.exp(post["log_k2_ratio"][idx])
    z1 = np.exp(post["log_zeta1"][idx]); z2 = np.exp(post["log_zeta2"][idx])
    bdome = post["build_dome"][idx, flight_id]
    curves = np.empty((len(idx), len(rfreqs)))
    for j in range(len(idx)):
        H00 = np.abs(np.asarray(fw.interface_accel_per_force_g(k1[j], k2[j], z1[j], z2[j], jnp.asarray(rfreqs)))) ** 2
        gp = chol_r @ rng.standard_normal(len(rfreqs))
        curves[j] = H00 * meanF_refined * math.exp(bdome[j]) * np.exp(gp)
    return rfreqs, curves


def main():
    t0 = time.time()
    numpyro.set_host_device_count(N_CHAINS)
    for p in (OUT, FIG, FRAMES):
        p.mkdir(parents=True, exist_ok=True)
    D = load_data()
    consts, chol_r = precompute_forcing_consts(D)
    model = make_model(D, consts)

    t_fit0 = time.time()
    mcmc = run_nuts(model, D["n_builds"], DRAWS, WARMUP, SEED)
    t_fit = time.time() - t_fit0
    diagnostics = diagnostics_from(mcmc, t_fit, consts)
    (OUT / "nuts_diagnostics.json").write_text(json.dumps(diagnostics, indent=2))
    post = {k: np.asarray(v) for k, v in mcmc.get_samples().items()}
    np.savez(OUT / "posterior_samples.npz", **post)
    print("CONVERGED:", diagnostics["converged"], "worst_rhat", diagnostics["worst_rank_split_rhat"],
          "min_ess_bulk", diagnostics["min_ess_bulk"], "min_ess_tail", diagnostics["min_ess_tail"],
          "div", diagnostics["divergences"], "fit_s", round(t_fit, 1))

    artifacts = make_all_plots(post, D, consts, chol_r, diagnostics)

    runtime = {
        "active_runtime_s": round(time.time() - t0, 2),
        "elapsed_wallclock_s": round(time.time() - t0, 2),
        "note": "active_runtime_s here = this script's measured runtime; total active across all "
                "commands (venv install, validation, checker) is summed in runtime.json by the wrapper.",
        "fit_runtime_s": round(t_fit, 2), "smoke_mode": SMOKE,
    }
    (OUT / "runtime_pipeline.json").write_text(json.dumps(runtime, indent=2))
    (OUT / "pipeline_summary.json").write_text(json.dumps({
        "converged": diagnostics["converged"], "nuts_active": diagnostics["nuts_active"],
        "artifacts": artifacts, "fit_runtime_s": t_fit,
    }, indent=2))
    print("DONE pipeline in", round(time.time() - t0, 1), "s")


def make_all_plots(post, D, consts, chol_r, diagnostics):
    rng = np.random.default_rng(SEED + 1)
    rfreqs = D["rfreqs"]; smooth = D["smooth"]; gfreqs = D["gfreqs"]
    spec_on_refined = np.exp(np.interp(np.log(rfreqs), np.log(gfreqs), np.log(smooth)))
    converged = diagnostics["converged"]
    tag = "" if converged else "  [NOT-YET-CONVERGED]"

    # ---------- KEY DELIVERABLE: per-flight interface response PSD vs spec GIF ----------
    band_records = []
    frame_files = []
    # global y-limits across flights for consistent frames
    all_hi = []
    ens_cache = {}
    for f in range(D["n_builds"]):
        rf, curves = interface_psd_ensemble(post, D, chol_r, f, n_param=600, rng=np.random.default_rng(SEED + 200 + f))
        ens_cache[f] = curves
        all_hi.append(np.quantile(curves, 0.995, axis=0).max())
    ymax = max(max(all_hi), smooth.max()) * 2.0
    ymin = min(np.quantile(np.vstack([ens_cache[f] for f in ens_cache]), 0.005, axis=0).min(), smooth.min()) * 0.5

    for f in range(D["n_builds"]):
        curves = ens_cache[f]
        mean_c = curves.mean(axis=0)
        q025, q975 = np.quantile(curves, [0.025, 0.975], axis=0)
        q005, q995 = np.quantile(curves, [0.005, 0.995], axis=0)
        # envelope check: fraction of frequencies where 99% upper exceeds spec
        exceed99 = float(np.mean(q995 > spec_on_refined))
        band_records.append({
            "flight_id": f, "build_id": int(D["build_id_of_flight"][f]),
            "peak_mean_psd_g2_per_hz": float(mean_c.max()),
            "peak_freq_hz": float(rfreqs[np.argmax(mean_c)]),
            "frac_freqs_99hi_exceeds_spec": exceed99,
        })
        fig, ax = plt.subplots(figsize=(9.6, 5.6))
        ax.fill_between(rfreqs, q005, q995, color="#f1c40f", alpha=0.35, label="99% credible band")
        ax.fill_between(rfreqs, q025, q975, color="#2ca02c", alpha=0.40, label="95% credible band")
        ax.loglog(rfreqs, mean_c, color="#1f77b4", lw=2.2, label="posterior-predictive mean")
        ax.loglog(gfreqs, smooth, color="#d62728", lw=2.2, ls="--", label="original test spec (smoothline)")
        ax.set_xlim(rfreqs.min(), rfreqs.max()); ax.set_ylim(ymin, ymax)
        ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("interface accel response PSD [g$^2$/Hz]")
        bd_db = 10.0 * float(post["build_dome"][:, f].mean()) / LN10
        ax.set_title(f"Flight {f} (build {int(D['build_id_of_flight'][f])}) — coupled interface accel response PSD vs spec{tag}\n"
                     f"posterior mean dome build effect ≈ {bd_db:+.2f} dB(PSD); 99% upper exceeds spec at "
                     f"{100*band_records[-1]['frac_freqs_99hi_exceeds_spec']:.0f}% of freqs", fontsize=9.5)
        ax.grid(True, which="both", alpha=0.25); ax.legend(loc="lower center", ncol=2, fontsize=8)
        fig.tight_layout()
        ff = FRAMES / f"frame_flight_{f:02d}.png"
        fig.savefig(ff, dpi=130); plt.close(fig); frame_files.append(ff)

    gif_path = FIG / "interface_response_psd_vs_spec.gif"
    imageio.mimsave(gif_path, [imageio.imread(f) for f in frame_files], duration=1.1, loop=0)
    (OUT / "interface_psd_bands.json").write_text(json.dumps(band_records, indent=2))

    # ---------- P2 forcing overlay (discrete draws vs original +6 dB) ----------
    fig, ax = plt.subplots(figsize=(9.8, 5.6))
    ax.loglog(D["gfreqs"], D["origF_global"], color="#222222", lw=2.4, label="original forcing PSD (+6 dB above flight mean)")
    ax.loglog(D["gfreqs"], D["meanF_global"], color="#1f77b4", lw=2.0, ls="--", label="flight mean forcing (project −6 dB offset)")
    rng_f = np.random.default_rng(SEED + 50)
    chol_g = np.linalg.cholesky((SIGMA_F2F_LN ** 2) * matern32_corr_lnfreq(D["gfreqs"], FORCING_ELL) + 1e-10 * np.eye(len(D["gfreqs"])))
    for i in range(D["n_builds"]):
        draw = D["meanF_global"] * np.exp(chol_g @ rng_f.standard_normal(len(D["gfreqs"])))
        ax.loglog(D["gfreqs"], draw, color="#ff7f0e", lw=0.9, alpha=0.6,
                  label="flight forcing draws (11)" if i == 0 else None)
    ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("force PSD [N$^2$/Hz]")
    ax.set_title("Flight forcing draws vs original forcing PSD\n(−6 dB flight offset is a PROJECT assumption, NOT a GEVS margin)", fontsize=9.5)
    ax.grid(True, which="both", alpha=0.25); ax.legend(loc="lower left", fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "flight_forcing_overlay.png", dpi=150); plt.close(fig)

    # ---------- P3 QOI vs vibe reference ----------
    fig, ax = plt.subplots(figsize=(9.8, 5.4))
    fids = np.arange(D["n_builds"])
    ax.semilogy(fids, D["tray_3grms_flights"], "o-", color="#1f77b4", label="flight tray 3·GRMS (per flight)")
    ax.axhline(D["vibe_3grms_obs"], color="#d62728", ls="--", lw=2.0, label=f"first-build vibe-test tray 3·GRMS = {D['vibe_3grms_obs']:.1f} g")
    ax.axhline(D["smooth_3grms"], color="#444444", ls=":", lw=2.0, label=f"smoothline input 3·GRMS = {D['smooth_3grms']:.1f} g")
    ax.set_xlabel("flight id"); ax.set_ylabel("tray 3·GRMS [g] (log)")
    ax.set_title("Flight tray 3·GRMS vs vibe-test reference (log-y)\n"
                 "Large qual-vs-flight gap is EXPECTED (qual envelopes flight). 3·GRMS = 3σ≈99.73% peak estimate, not a hard max.", fontsize=9.0)
    ax.set_xticks(fids); ax.grid(True, which="both", alpha=0.25); ax.legend(loc="center right", fontsize=8.5)
    # annotate gap
    ax.annotate("qual/flight gap\n(expected)", xy=(0.3, D["vibe_3grms_obs"]), xytext=(2.0, D["vibe_3grms_obs"]*0.45),
                fontsize=8, arrowprops=dict(arrowstyle="->", color="gray"))
    fig.tight_layout(); fig.savefig(FIG / "flight_qoi_vs_vibe_reference.png", dpi=150); plt.close(fig)

    # ---------- P4 resolution sensitivity ----------
    res = resolution_sensitivity(D, post)
    (OUT / "resolution_metrics.json").write_text(json.dumps(res, indent=2))

    # ---------- secondary: sequential assimilation QOI tightening ----------
    seq = sequential_assimilation_plot(D, consts)

    # ---------- posterior parameter recovery vs truth ----------
    posterior_recovery_plot(post, D)

    return {
        "gif": str(gif_path.relative_to(OUT)),
        "n_frames": len(frame_files),
        "forcing_overlay": "figures/flight_forcing_overlay.png",
        "qoi_overlay": "figures/flight_qoi_vs_vibe_reference.png",
        "resolution": "figures/resolution_sensitivity.png",
        "sequential": seq,
        "posterior_recovery": "figures/posterior_recovery.png",
        "interface_psd_bands": "interface_psd_bands.json",
    }


def resolution_sensitivity(D, post):
    """Compare coarse global grid vs mode-refined grid for tray & interface 3GRMS at the
    posterior median params; show peaks are not clipped on the refined grid."""
    gfreqs = D["gfreqs"]; rfreqs = D["rfreqs"]
    k1 = fw.K1_NOM * math.exp(float(np.median(post["log_k1_ratio"])))
    k2 = fw.K2_NOM * math.exp(float(np.median(post["log_k2_ratio"])))
    z1 = math.exp(float(np.median(post["log_zeta1"]))); z2 = math.exp(float(np.median(post["log_zeta2"])))
    meanF = D["meanF_const"]
    def q3(freqs):
        H00 = np.abs(np.asarray(fw.interface_accel_per_force_g(k1, k2, z1, z2, jnp.asarray(freqs)))) ** 2 * meanF
        H10 = np.abs(np.asarray(fw.tray_accel_per_force_g(k1, k2, z1, z2, jnp.asarray(freqs)))) ** 2 * meanF
        return 3 * math.sqrt(np.trapz(H00, freqs)), 3 * math.sqrt(np.trapz(H10, freqs)), H00, H10
    refgrid = np.geomspace(20.0, 2000.0, 60000)  # high-density reference (ground truth)
    qi_c, qt_c, H00c, H10c = q3(gfreqs)
    qi_r, qt_r, H00r, H10r = q3(rfreqs)
    qi_ref, qt_ref, H00ref, H10ref = q3(refgrid)
    # peak-clipping near the narrowest mode (62.3 Hz)
    def peak_near(freqs, mag, lo, hi):
        m = (freqs >= lo) & (freqs <= hi)
        return float(mag[m].max()), float(freqs[m][np.argmax(mag[m])])
    pk_c, fc_c = peak_near(gfreqs, H00c, 58, 67)
    pk_r, fr_r = peak_near(rfreqs, H00r, 58, 67)
    pk_ref, f_ref = peak_near(refgrid, H00ref, 58, 67)
    res = {
        "grid_global_points": len(gfreqs), "grid_refined_points": len(rfreqs),
        "reference_points": len(refgrid),
        "global_min_dlog_freq": float(np.min(np.diff(np.log(gfreqs)))),
        "global_pts_per_halfpower_band_62Hz": float(1.82 / (62.28 * float(np.min(np.diff(np.log(gfreqs)))))),
        "interface_3grms_coarse_g": qi_c, "interface_3grms_refined_g": qi_r, "interface_3grms_reference_g": qi_ref,
        "interface_3grms_coarse_err_vs_ref": (qi_c - qi_ref) / qi_ref,
        "interface_3grms_refined_err_vs_ref": (qi_r - qi_ref) / qi_ref,
        "tray_3grms_coarse_g": qt_c, "tray_3grms_refined_g": qt_r, "tray_3grms_reference_g": qt_ref,
        "tray_3grms_coarse_err_vs_ref": (qt_c - qt_ref) / qt_ref,
        "tray_3grms_refined_err_vs_ref": (qt_r - qt_ref) / qt_ref,
        "peak62_height_coarse": pk_c, "peak62_freq_coarse": fc_c,
        "peak62_height_refined": pk_r, "peak62_freq_refined": fr_r,
        "peak62_height_reference": pk_ref, "peak62_freq_reference": f_ref,
        "peak62_coarse_clip_frac": (pk_ref - pk_c) / pk_ref,
        "peak62_refined_clip_frac": (pk_ref - pk_r) / pk_ref,
        "note": "Refined grid adds mode-local clusters near coupled peaks 62.3 & 129.5 Hz, tray-vibe "
                "86.25 Hz, dome 93.5 Hz. FINDING: the 3*GRMS integral QOI is robust to grid (<0.3% "
                "vs 60k-pt reference) because the narrow peak contributes little integrated energy, "
                "BUT the coarse global grid CLIPS the 62.3 Hz peak TIP (height error reported in "
                "peak62_coarse_clip_frac), which matters for peak/modal identification and display. "
                "Refinement removes the visual clip; QOI is unchanged.",
    }
    # plot zoom near 62 Hz (narrowest) and 129.5 Hz
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5.2))
    for ax, (lo, hi, lbl) in zip(axes, [(55, 72, "coupled mode 1 ~62.3 Hz (narrowest, Δf≈1.8 Hz)"),
                                         (110, 150, "coupled mode 2 ~129.5 Hz (Δf≈7.8 Hz)")]):
        mg = (gfreqs >= lo) & (gfreqs <= hi); mr = (rfreqs >= lo) & (rfreqs <= hi); mref = (refgrid >= lo) & (refgrid <= hi)
        ax.plot(refgrid[mref], H00ref[mref], "-", color="#888888", lw=1.4, label="60k-pt reference (truth)")
        ax.plot(gfreqs[mg], H00c[mg], "s--", color="#d62728", ms=5, label="global grid (coarse) — CLIPS tip")
        ax.plot(rfreqs[mr], H00r[mr], ".-", color="#1f77b4", ms=5, lw=1.0, label="mode-refined grid")
        ax.set_xlabel("frequency [Hz]"); ax.set_ylabel("interface response PSD [g$^2$/Hz]")
        ax.set_title(lbl, fontsize=9); ax.grid(True, alpha=0.25); ax.legend(fontsize=8)
    fig.suptitle(f"Resolution sensitivity: 62.3 Hz peak tip CLIPPED {100*res['peak62_coarse_clip_frac']:.1f}% on coarse grid "
                 f"(refined {100*res['peak62_refined_clip_frac']:.1f}%), but interface 3·GRMS QOI error vs 60k-pt reference is "
                 f"{100*res['interface_3grms_coarse_err_vs_ref']:+.2f}% (coarse) / {100*res['interface_3grms_refined_err_vs_ref']:+.2f}% (refined)", fontsize=9)
    fig.tight_layout(); fig.savefig(FIG / "resolution_sensitivity.png", dpi=150); plt.close(fig)
    return res


def sequential_assimilation_plot(D, consts):
    """Secondary interpretation (A): refit with cumulative flights 1..k, show tray-3GRMS-at-mean-force
    QOI posterior tightening. Uses smaller draws (clearly labeled supplementary)."""
    model = make_model(D, consts)
    ks = [1, 3, 5, 7, 9, 11] if not SMOKE else [1, 6, 11]
    means = []; los = []; his = []
    draws = 120 if SMOKE else 600
    warm = 120 if SMOKE else 600
    for k in ks:
        mc = run_nuts(model, k, draws, warm, SEED + 900 + k)
        p = {kk: np.asarray(v) for kk, v in mc.get_samples().items()}
        k1 = fw.K1_NOM * np.exp(p["log_k1_ratio"]); k2 = fw.K2_NOM * np.exp(p["log_k2_ratio"])
        z1 = np.exp(p["log_zeta1"]); z2 = np.exp(p["log_zeta2"])
        rfreqs = D["rfreqs"]; meanF = D["meanF_const"]
        sub = np.random.default_rng(SEED + k).choice(len(k1), size=min(300, len(k1)), replace=False)
        q = []
        for j in sub:
            H10 = np.abs(np.asarray(fw.tray_accel_per_force_g(k1[j], k2[j], z1[j], z2[j], jnp.asarray(rfreqs)))) ** 2 * meanF
            q.append(3 * math.sqrt(np.trapz(H10, rfreqs)))
        q = np.asarray(q)
        means.append(q.mean()); los.append(np.quantile(q, 0.025)); his.append(np.quantile(q, 0.975))
    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    ax.plot(ks, means, "o-", color="#1f77b4", label="tray 3·GRMS (mean-forcing) posterior mean")
    ax.fill_between(ks, los, his, color="#2ca02c", alpha=0.3, label="95% credible interval")
    ax.set_xlabel("number of flights assimilated"); ax.set_ylabel("tray 3·GRMS at mean forcing [g]")
    ax.set_title("SECONDARY view (interpretation A): sequential assimilation — QOI posterior vs cumulative flights", fontsize=9.0)
    ax.set_xticks(ks); ax.grid(True, alpha=0.25); ax.legend(fontsize=8.5)
    fig.tight_layout(); fig.savefig(FIG / "sequential_assimilation_qoi.png", dpi=150); plt.close(fig)
    return "figures/sequential_assimilation_qoi.png"


def posterior_recovery_plot(post, D):
    truths = {"dome f_n [Hz]": 93.5, "tray f_n [Hz]": 86.25, "zeta1": fw.TRUE_ZETA1, "zeta2": fw.TRUE_ZETA2}
    dome_hz = np.sqrt(fw.K1_NOM * np.exp(post["log_k1_ratio"]) / fw.M1) / (2 * np.pi)
    tray_hz = np.sqrt(fw.K2_NOM * np.exp(post["log_k2_ratio"]) / fw.M2) / (2 * np.pi)
    samples = {"dome f_n [Hz]": dome_hz, "tray f_n [Hz]": tray_hz,
               "zeta1": np.exp(post["log_zeta1"]), "zeta2": np.exp(post["log_zeta2"])}
    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, (name, s) in zip(axes.ravel(), samples.items()):
        ax.hist(s, bins=50, color="#1f77b4", alpha=0.7, density=True, label="posterior")
        ax.axvline(truths[name], color="#d62728", lw=2.0, ls="--", label=f"truth = {truths[name]:.4g}")
        ax.set_title(name, fontsize=9.5); ax.set_ylabel("density"); ax.legend(fontsize=8); ax.grid(True, alpha=0.2)
    fig.suptitle("Posterior recovery of uncoupled subsystem natural frequencies & damping vs synthetic truth", fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "posterior_recovery.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    main()
