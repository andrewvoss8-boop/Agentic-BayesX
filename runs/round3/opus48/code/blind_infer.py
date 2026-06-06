#!/usr/bin/env python3
"""BLIND hierarchical StatFEM inference (NumPyro NUTS) against Codex's PUBLISHED observations.

Consumes ONLY runs/round3/codex_truth/dataset/observations.npz (read-only). Does NOT read the sealed
truth. Fits the coarse engineering forward model (blind_model.py) to the per-build 6-DOF interface
apparent mass; learns the physical parameters + the hierarchy (sigma_build) + sensor noise (sigma_e) +
a per-DOF frequency discrepancy d (HSGP over log-freq, sigma_d learned, ell_d FIXED per D19 to avoid the
sigma_d<->sigma_e ridge). Reports convergence over ALL latents + held-out calibration (whole builds +
whole frequency band) + companions (effective-vs-nominal count, starve-the-data, with/without-d).

Env: R3BLIND_SMOKE=1 -> tiny quick test (NOT for reporting). Outputs report/blind_results.json,
report/blind_nuts_diagnostics.(md|json), report/blind_posterior.npz, and figures.
"""
from __future__ import annotations
import os, sys, math, json, time
from pathlib import Path
os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/agentic_bayesx_mpl_blind")
os.environ.setdefault("XLA_FLAGS", "--xla_force_host_platform_device_count=4")
import numpy as np
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS, init_to_value
import arviz as az
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.signal import find_peaks

HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / "code"))
import blind_model as bm
from adaptive_freq import adaptive_frequency_grid

OUT = HERE / "report"; FIG = OUT / "figures"
SEED = 20260604
SMOKE = os.environ.get("R3BLIND_SMOKE", "0") == "1"
N_CHAINS = 4
WARMUP = int(os.environ.get("R3BLIND_WARMUP", "150" if SMOKE else "1500"))
DRAWS = int(os.environ.get("R3BLIND_DRAWS", "150" if SMOKE else "1000"))
# without-d / starve are DIAGNOSTIC companions (not the reported gate); cap their cost because the
# no-discrepancy geometry is pathologically stiff (it hits max tree depth every draw -> that stiffness is
# itself evidence the discrepancy is needed, documented as a finding).
DIAG_WARMUP = 100 if SMOKE else 400
DIAG_DRAWS = 100 if SMOKE else 400
NDOF = bm.NDOF
M_HSGP = 3                      # HSGP rank per DOF (LOW-rank: smooth-trend discrepancy only, so it cannot
                                # reshape each mode arbitrarily -> keeps the physics identified / unimodal)
ELL_D_FIXED = 0.45             # FIXED discrepancy length-scale (normalized log-freq units), per D19
FBAND = (40.0, 115.0)         # inference band: the well-modeled first mode cluster (holds the QOI energy 66/96 Hz)
HELDOUT_BAND = (82.0, 95.0)   # whole frequency band held out for calibration (inside the modal cluster)


# ---------- adaptive grid from DATA peaks (we do NOT know the true modes) ----------
def data_peak_modes(obs, fband):
    f = obs["f"]; mag = obs["mag"].mean(axis=0)   # (6,nf) build-averaged
    sel = (f >= fband[0]) & (f <= fband[1])
    modes = []
    for i in range(NDOF):
        m = mag[i][sel]; ff = f[sel]
        pk, _ = find_peaks(m, prominence=m.max() * 0.05)
        modes += list(ff[pk])
    modes = np.array(sorted(set(np.round(modes, 1))))
    return modes


def build_grid(obs):
    modes = data_peak_modes(obs, FBAND)
    grid = adaptive_frequency_grid(modes, np.full(len(modes), 0.04), FBAND[0], FBAND[1],
                                   base_per_decade=8, pts_per_mode=5, n_halfwidths=4)
    return np.asarray(grid), modes


# ---------- HSGP basis over log-frequency (lets sigma_d scale a fixed basis) ----------
def hsgp_basis(freqs, M):
    u = np.log(freqs); umid = 0.5 * (u.min() + u.max()); uhalf = 0.5 * (u.max() - u.min())
    un = (u - umid) / uhalf
    L = 1.4; j = np.arange(1, M + 1); omega = np.pi * j / (2 * L)
    Phi = np.sin(np.outer(un + L, omega)) / np.sqrt(L)
    return Phi, omega


def matern32_sdens(omega, sigma, ell):
    return (sigma**2) * (1.0 / ell**3) / (3.0 / ell**2 + omega**2)**2


# ---------- data prep ----------
def prepare(obs):
    grid, modes = build_grid(obs)
    f = obs["f"]
    # interpolate observed log|apparent mass| onto the fixed grid, per build per DOF
    Y = np.empty((obs["mag"].shape[0], NDOF, len(grid)))
    for b in range(obs["mag"].shape[0]):
        for i in range(NDOF):
            Y[b, i] = np.interp(np.log(grid), np.log(f), obs["logmag"][b, i])
    M_base6, m_dome, lf = bm.rigid_base_from_asymptote(obs)
    k0 = bm.nominal_k_strut(86.25)
    Phi, omega = hsgp_basis(grid, M_HSGP)
    return dict(grid=grid, modes=modes, Y=Y, M_base6=M_base6, m_dome=m_dome, lf=lf,
                k0=k0, Phi=Phi, omega=omega)


# ---------- model ----------
SIGMA_D_FIXED = 0.3            # capped discrepancy magnitude (log) when learn_sigma_d=False (breaks the ridge)


SIGMA_BUILD_FIXED = 0.05      # physical build-to-build k scatter (~5%) when learn_sigma_build=False


F_DOME_FIXED = 93.5           # nominal dome bounce (Hz) when learn_f_dome=False


def make_model(P, Y, with_d=True, learn_sigma_e=True, freq_mask=None, learn_sigma_d=False,
               learn_sigma_build=True, learn_f_dome=True):
    """freq_mask: boolean over grid; True = USED in the likelihood (held-out band -> False -> excluded by
    INDEXING, not imputed -- avoids creating latent y_unobserved vars that bloat the convergence gate).
    learn_sigma_d=False -> FIX the discrepancy magnitude (SIGMA_D_FIXED) to break the sigma_d<->sigma_e
    ridge that de-identifies the physics under a frequency-only discrepancy (D19). True -> learn it (the
    flexible-discrepancy variant that EXHIBITS the ridge -- reported as a finding, not the gated fit)."""
    B = Y.shape[0]
    gridj = jnp.asarray(P["grid"]); Phij = jnp.asarray(P["Phi"]); omegaj = jnp.asarray(P["omega"])
    M_base6 = jnp.asarray(P["M_base6"]); m_dome = float(P["m_dome"]); k0 = float(P["k0"])
    use = np.ones(len(P["grid"]), bool) if freq_mask is None else freq_mask.astype(bool)
    use_idx = jnp.asarray(np.where(use)[0])
    yj = jnp.asarray(Y[:, :, use])                                        # (B,6,nf_used) likelihood data
    fwd_batch = jax.vmap(lambda k, fd: bm.forward_logmag(k, fd, M_base6, m_dome, gridj), in_axes=(0, None))

    def model():
        log_k = numpyro.sample("log_k_strut_pop", dist.Normal(math.log(k0), 0.40))
        numpyro.deterministic("k_strut_pop", jnp.exp(log_k))
        if learn_f_dome:
            f_dome = numpyro.sample("f_dome", dist.TruncatedNormal(93.5, 6.0, low=70.0, high=115.0))
        else:
            f_dome = numpyro.deterministic("f_dome", jnp.asarray(F_DOME_FIXED))
        # build-to-build stiffness scatter: physically a few % (task: +-5% @3sigma on fn -> ~3% on k);
        # tight PHYSICAL prior (not convergence-gaming) -- the unconstrained smoke gave 49% (absurd).
        if learn_sigma_build:
            sigma_build = numpyro.sample("sigma_build", dist.HalfNormal(0.05))
        else:
            sigma_build = numpyro.deterministic("sigma_build", jnp.asarray(SIGMA_BUILD_FIXED))
        z = numpyro.sample("z_b", dist.Normal(0, 1).expand([B]))          # non-centered per-build
        k_b = jnp.exp(log_k + sigma_build * z)
        sigma_e = numpyro.sample("sigma_e", dist.HalfNormal(0.12)) if learn_sigma_e else 0.10  # sensor ~1 dB
        mu = fwd_batch(k_b, f_dome)                                       # (B,6,nf)
        if with_d:
            if learn_sigma_d:
                sigma_d = numpyro.sample("sigma_d", dist.HalfNormal(0.25))
            else:
                sigma_d = numpyro.deterministic("sigma_d", jnp.asarray(SIGMA_D_FIXED))  # CAPPED (breaks ridge)
            sd = jnp.sqrt(matern32_sdens(omegaj, sigma_d, ELL_D_FIXED))   # (M,)
            beta = numpyro.sample("beta", dist.Normal(0, 1).expand([NDOF, M_HSGP]))
            d = (Phij @ (sd * beta).T).T                                  # (6,nf)
            mu = mu + d[None, :, :]
        mu_used = mu[:, :, use_idx]                                       # (B,6,nf_used)
        numpyro.sample("y", dist.Normal(mu_used, sigma_e), obs=yj)
    return model


def run(P, Y, with_d=True, learn_sigma_e=True, freq_mask=None, seed=SEED, full_diag=False,
        warmup=None, draws=None, max_tree_depth=9, learn_sigma_d=False, learn_sigma_build=True,
        learn_f_dome=True):
    warmup = WARMUP if warmup is None else warmup
    draws = DRAWS if draws is None else draws
    model = make_model(P, Y, with_d, learn_sigma_e, freq_mask, learn_sigma_d, learn_sigma_build, learn_f_dome)
    kernel = NUTS(model, target_accept_prob=0.9, max_tree_depth=max_tree_depth, dense_mass=False,
                  init_strategy=init_to_value(values={"log_k_strut_pop": math.log(P["k0"]), "f_dome": 93.5}))
    mc = MCMC(kernel, num_warmup=warmup, num_samples=draws, num_chains=N_CHAINS,
              chain_method="parallel", progress_bar=False)
    _t = time.time()
    mc.run(jax.random.PRNGKey(seed), extra_fields=("diverging", "num_steps"))
    print("    [run] with_d=%s builds=%d band_pts=%d -> %.1fs" %
          (with_d, Y.shape[0], int(freq_mask.sum()) if freq_mask is not None else -1, time.time() - _t), flush=True)
    post = {k: np.asarray(v) for k, v in mc.get_samples().items()}
    idata = az.from_numpyro(mc)
    # convergence over ALL sampled latents (incl. raw z_b and beta coeffs)
    rh = az.rhat(idata); es_bulk = az.ess(idata, method="bulk"); es_tail = az.ess(idata, method="tail")
    worst = {"rhat": 0.0, "ess_bulk": 1e18, "ess_tail": 1e18, "rhat_var": "", "ess_var": ""}
    per_var = {}
    for v in rh.data_vars:
        r = float(np.nanmax(rh[v].values)); eb = float(np.nanmin(es_bulk[v].values)); et = float(np.nanmin(es_tail[v].values))
        per_var[v] = {"max_rhat": r, "min_ess_bulk": eb, "min_ess_tail": et}
        if r > worst["rhat"]: worst["rhat"] = r; worst["rhat_var"] = v
        if eb < worst["ess_bulk"]: worst["ess_bulk"] = eb; worst["ess_var"] = v
        if et < worst["ess_tail"]: worst["ess_tail"] = et
    ndiv = int(np.asarray(mc.get_extra_fields()["diverging"]).sum())
    ntot = N_CHAINS * draws
    diag = {"worst_rhat": worst["rhat"], "worst_rhat_var": worst["rhat_var"],
            "min_ess_bulk": worst["ess_bulk"], "min_ess_tail": worst["ess_tail"], "min_ess_var": worst["ess_var"],
            "divergences": ndiv, "divergence_frac": ndiv / max(ntot, 1), "n_draws_total": ntot,
            "gate_pass": bool(worst["rhat"] < 1.01 and worst["ess_bulk"] >= 400 and worst["ess_tail"] >= 400
                              and ndiv / max(ntot, 1) < 0.02)}
    if full_diag:
        diag["per_var"] = per_var
    return post, diag


# ---------- prediction & coverage ----------
_PREDICTORS = {}


def _get_predictor(P):
    """jitted SINGLE-sample predictor (vmap over freq only): fast, small compile.
    args (logk, fdome, sigma_d, beta) -> log|apparent mass| (6,nf). beta=0 -> no discrepancy."""
    key = (id(P), len(P["grid"]))
    if key in _PREDICTORS:
        return _PREDICTORS[key]
    gridj = jnp.asarray(P["grid"]); M_base6 = jnp.asarray(P["M_base6"]); m_dome = float(P["m_dome"])
    Phij = jnp.asarray(P["Phi"]); omegaj = jnp.asarray(P["omega"])

    @jax.jit
    def one(logk, fdome, sigma_d, beta):
        mu = bm.forward_logmag(jnp.exp(logk), fdome, M_base6, m_dome, gridj)   # (6,nf)
        sd = jnp.sqrt(matern32_sdens(omegaj, sigma_d, ELL_D_FIXED))
        return mu + (Phij @ (sd * beta).T).T
    _PREDICTORS[key] = one
    return one


def predict_logmag(P, post, n=300, new_build=True, rng=None):
    """Posterior predictive log|apparent mass| (6,nf) samples for a NEW build (k drawn from population).
    Returns (mu samples (n,6,nf), sigma_e samples (n,)). jitted single-sample forward + Python loop."""
    rng = rng or np.random.default_rng(0)
    S = post["k_strut_pop"].shape[0]; idx = rng.choice(S, min(n, S), replace=False)
    has_d = "beta" in post
    se = post.get("sigma_e", np.full(S, 0.10))[idx]
    logk = np.log(post["k_strut_pop"][idx])
    if new_build and "sigma_build" in post:
        logk = logk + post["sigma_build"][idx] * rng.standard_normal(len(idx))
    fdome = post["f_dome"][idx]
    sigma_d = post["sigma_d"][idx] if has_d else np.zeros(len(idx))
    beta = post["beta"][idx] if has_d else np.zeros((len(idx), NDOF, M_HSGP))
    fn = _get_predictor(P)
    out = np.empty((len(idx), NDOF, len(P["grid"])))
    for i in range(len(idx)):
        out[i] = np.asarray(fn(float(logk[i]), float(fdome[i]), float(sigma_d[i]), jnp.asarray(beta[i])))
    return out, se


def coverage(P, post, Y_heldout, freq_idx=None, level=0.95, rng=None):
    rng = rng or np.random.default_rng(1)
    mu, se = predict_logmag(P, post, n=300, new_build=True, rng=rng)
    draws = mu + se[:, None, None] * rng.standard_normal(mu.shape)
    a = (1 - level) / 2
    lo = np.quantile(draws, a, axis=0); hi = np.quantile(draws, 1 - a, axis=0)
    fmask = np.ones(len(P["grid"]), bool) if freq_idx is None else freq_idx
    covs, widths = [], []
    for b in range(Y_heldout.shape[0]):
        obs = Y_heldout[b][:, fmask]; L = lo[:, fmask]; H = hi[:, fmask]
        covs.append(float(np.mean((obs >= L) & (obs <= H))))
        widths.append(float(np.mean(H - L)))
    return float(np.mean(covs)), covs, float(np.mean(widths))


def main():
    t0 = time.time(); numpyro.set_host_device_count(N_CHAINS); FIG.mkdir(parents=True, exist_ok=True)
    obs = bm.load_observations()
    P = prepare(obs)
    B = P["Y"].shape[0]
    grid = P["grid"]
    band = (grid >= HELDOUT_BAND[0]) & (grid <= HELDOUT_BAND[1])
    train_fmask = ~band
    Btrain = B - 2                                  # hold out last 2 whole builds
    print("grid NF=%d  band=%s  data-peak modes=%s" % (len(grid), FBAND, np.round(P["modes"], 1).tolist()), flush=True)
    print("held-out builds: %d,%d ; held-out band: %s Hz (%d pts)" % (Btrain, Btrain + 1, HELDOUT_BAND, band.sum()), flush=True)

    # MAIN fit: with d, learn sigma_e, train builds + training band (the reported, gated fit)
    post, diag = run(P, P["Y"][:Btrain], with_d=True, learn_sigma_e=True, freq_mask=train_fmask, seed=SEED + 1, full_diag=True)

    def psumm(p, key):
        x = p[key]
        return dict(q50=float(np.median(x)), sd=float(np.std(x)),
                    ci95=[float(np.quantile(x, .025)), float(np.quantile(x, .975))])

    # held-out coverage (MAIN model)
    cov_nb, covs_nb, w_nb = coverage(P, post, P["Y"][Btrain:], freq_idx=None, rng=np.random.default_rng(10))
    cov_band, covs_band, w_band = coverage(P, post, P["Y"][:Btrain], freq_idx=band, rng=np.random.default_rng(11))

    # COMPANIONS (env-gated): without-d + starve-the-data. The no-discrepancy geometry is pathologically
    # stiff (it hits max tree depth constantly -> evidence the discrepancy is REQUIRED), so they are bounded
    # and OPTIONAL; the reported gate is the with-d main fit above.
    DO_COMPANIONS = os.environ.get("R3BLIND_COMPANIONS", "1") == "1"
    post_nd = post_st = None; diag_nd = diag_st = diag_flex = {"skipped": True}
    cov_nb_nd = cov_band_nd = w_nb_nd = None
    if DO_COMPANIONS:
        post_nd, diag_nd = run(P, P["Y"][:Btrain], with_d=False, learn_sigma_e=True, freq_mask=train_fmask,
                               seed=SEED + 2, warmup=DIAG_WARMUP, draws=DIAG_DRAWS, max_tree_depth=6)
        post_st, diag_st = run(P, P["Y"][:1], with_d=True, learn_sigma_e=True, freq_mask=train_fmask,
                               seed=SEED + 3, warmup=DIAG_WARMUP, draws=DIAG_DRAWS, max_tree_depth=8)
        cov_nb_nd, _, w_nb_nd = coverage(P, post_nd, P["Y"][Btrain:], freq_idx=None, rng=np.random.default_rng(12))
        cov_band_nd, _, w_band_nd = coverage(P, post_nd, P["Y"][:Btrain], freq_idx=band, rng=np.random.default_rng(13))
        # FLEXIBLE-discrepancy variant (learn sigma_d) -> EXHIBITS the sigma_d<->sigma_e ridge (D19);
        # reported as a finding (non-convergence), NOT the gated fit. Bounded cost.
        post_flex, diag_flex = run(P, P["Y"][:Btrain], with_d=True, learn_sigma_e=True, learn_sigma_d=True,
                                   freq_mask=train_fmask, seed=SEED + 4, warmup=DIAG_WARMUP, draws=DIAG_DRAWS,
                                   max_tree_depth=7)
        diag_flex = {**diag_flex, "sigma_d_q50": float(np.median(post_flex["sigma_d"])),
                     "sigma_e_q50": float(np.median(post_flex["sigma_e"])),
                     "sigma_build_q50": float(np.median(post_flex["sigma_build"]))}

    # effective vs nominal sample count for k_strut_pop
    sigma_prior = 0.40
    n_eff = float((sigma_prior / np.std(np.log(post["k_strut_pop"])))**2)
    nominal = int(Btrain * NDOF * train_fmask.sum())

    results = {
        "role": "BLIND inference vs Codex independent truth (master scores vs sealed truth)",
        "forward_model": "coarse: M_base6 rigid (from low-f asymptote) + hexapod(k_strut) + dome axial resonator(f_dome); 6 equal struts; eta fixed; magnitude-only log-likelihood",
        "grid": {"n_points": int(len(grid)), "band_hz": list(FBAND), "adaptive_from_data_peaks": True,
                 "data_peak_modes_hz": [float(x) for x in P["modes"]]},
        "n_builds_total": B, "n_builds_train": Btrain, "heldout_builds": [Btrain, B - 1],
        "heldout_freq_band_hz": list(HELDOUT_BAND),
        "learned_with_d": {
            "k_strut_pop": psumm(post, "k_strut_pop"), "k_strut_nominal": P["k0"],
            "f_dome": psumm(post, "f_dome"),
            "sigma_build": psumm(post, "sigma_build"),
            "sigma_e": psumm(post, "sigma_e"),
            "sigma_d": psumm(post, "sigma_d")},
        "learned_without_d": ({"k_strut_pop": psumm(post_nd, "k_strut_pop"), "sigma_e": psumm(post_nd, "sigma_e"),
                               "note": "DIAGNOSTIC (bounded tree depth 6) — stiff geometry; not gate-grade"}
                              if post_nd is not None else "skipped (run with R3BLIND_COMPANIONS=1)"),
        "starve_1build": ({"k_strut_pop": psumm(post_st, "k_strut_pop"), "note": "DIAGNOSTIC (1 build)"}
                          if post_st is not None else "skipped (run with R3BLIND_COMPANIONS=1)"),
        "HELD_OUT_CALIBRATION_95": {
            "with_d_new_builds_coverage": cov_nb, "with_d_new_builds_mean_width": w_nb, "per_build": covs_nb,
            "with_d_heldout_band_coverage": cov_band, "with_d_heldout_band_mean_width": w_band,
            "without_d_new_builds_coverage": cov_nb_nd, "without_d_new_builds_mean_width": w_nb_nd,
            "without_d_heldout_band_coverage": cov_band_nd,
            "note": "target ~0.95. Read coverage WITH width/sigma_e: wide-but-covering is NOT success. Expect "
                    "model-form bias -> possible under-coverage in bands the coarse model misses."},
        "effective_vs_nominal": {"n_eff_k_strut": n_eff, "nominal_points": nominal, "ratio": n_eff / max(nominal, 1),
                                 "note": "n_eff<<nominal => correlated model error; tightness not from independent data."},
        "convergence": {"with_d_CAPPED_discrepancy_MAIN": diag, "without_d": diag_nd, "starve": diag_st,
                        "flexible_learn_sigma_d_RIDGE": diag_flex,
                        "gate": "rank-split R-hat<1.01, bulk&tail ESS>=400 over ALL latents, div<2%, 4 chains, non-centered",
                        "note": "MAIN fit CAPS sigma_d (=%.2f) to break the ridge. The flexible variant LEARNS sigma_d and EXHIBITS the ridge (de-identified, non-converged) -- reported as a finding per D19." % SIGMA_D_FIXED},
        "runtime_s": round(time.time() - t0, 1)}
    (OUT / "blind_results.json").write_text(json.dumps(results, indent=2))

    # save posterior for the QOI script
    np.savez(OUT / "blind_posterior.npz",
             k_strut_pop=post["k_strut_pop"], f_dome=post["f_dome"], sigma_build=post["sigma_build"],
             sigma_e=post["sigma_e"], sigma_d=post["sigma_d"], beta=post["beta"], z_b=post["z_b"],
             grid=grid, M_base6=P["M_base6"], m_dome=P["m_dome"], omega=P["omega"], Phi=P["Phi"],
             ell_d=ELL_D_FIXED, heldout_band=np.array(HELDOUT_BAND), Btrain=Btrain)

    write_diag_md(results)
    make_plots(P, post, obs, band, Btrain, results)
    print(json.dumps({"convergence_with_d": diag, "HELD_OUT": results["HELD_OUT_CALIBRATION_95"],
                      "effective_vs_nominal": results["effective_vs_nominal"]}, indent=2))
    print("k_strut_pop q50 %.3e (nominal %.3e)  f_dome %.1f  sigma_build %.3f  sigma_e %.3f  sigma_d %.3f" %
          (np.median(post["k_strut_pop"]), P["k0"], np.median(post["f_dome"]),
           np.median(post["sigma_build"]), np.median(post["sigma_e"]), np.median(post["sigma_d"])))
    print("GATE PASS:", diag["gate_pass"], "| worst R-hat %.4f (%s) min ESS bulk %.0f tail %.0f | div %d (%.2f%%)" %
          (diag["worst_rhat"], diag["worst_rhat_var"], diag["min_ess_bulk"], diag["min_ess_tail"],
           diag["divergences"], 100 * diag["divergence_frac"]))
    print("DONE blind_infer in", round(time.time() - t0, 1), "s")


def write_diag_md(res):
    d = res["convergence"]["with_d_CAPPED_discrepancy_MAIN"]
    lines = ["# Blind inference — NUTS convergence diagnostics", "",
             "Sampler: NumPyro NUTS, %d chains, %d warmup + %d draws, non-centered hierarchy, target_accept 0.95." % (N_CHAINS, WARMUP, DRAWS),
             "Gate: rank-split R-hat<1.01, bulk&tail ESS>=400 over ALL latents (incl. raw z_b + discrepancy beta), divergences<2%.", "",
             "## Main fit (with discrepancy)",
             "- worst R-hat: **%.4f** (var: %s)" % (d["worst_rhat"], d["worst_rhat_var"]),
             "- min bulk ESS: **%.0f**, min tail ESS: **%.0f** (var: %s)" % (d["min_ess_bulk"], d["min_ess_tail"], d["min_ess_var"]),
             "- divergences: **%d / %d (%.2f%%)**" % (d["divergences"], d["n_draws_total"], 100 * d["divergence_frac"]),
             "- **GATE PASS: %s**" % d["gate_pass"], "",
             "If the gate FAILS, this is reported as the result (NOT 'NUTS active'); a likely cause is the",
             "sigma_d<->sigma_e ridge under a mis-structured (frequency-only) discrepancy that cannot represent",
             "the spatial/higher-mode model-form error (see decisions_log D19).", "",
             "## Per-variable (worst over array elements)"]
    if "per_var" in d:
        lines.append("| variable | max R-hat | min bulk ESS | min tail ESS |")
        lines.append("|---|---|---|---|")
        for v, s in d["per_var"].items():
            lines.append("| %s | %.4f | %.0f | %.0f |" % (v, s["max_rhat"], s["min_ess_bulk"], s["min_ess_tail"]))
    (OUT / "blind_nuts_diagnostics.md").write_text("\n".join(lines))
    (OUT / "blind_nuts_diagnostics.json").write_text(json.dumps(res["convergence"], indent=2))


def make_plots(P, post, obs, band, Btrain, results):
    grid = P["grid"]
    mu, se = predict_logmag(P, post, n=300, new_build=True, rng=np.random.default_rng(20))
    rng = np.random.default_rng(21)
    draws = mu + se[:, None, None] * rng.standard_normal(mu.shape)
    lo = np.quantile(draws, 0.025, axis=0); hi = np.quantile(draws, 0.975, axis=0); med = np.median(mu, axis=0)
    # predicted-vs-observed on held-out builds, all 6 DOF
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    for i, ax in enumerate(axes.ravel()):
        ax.fill_between(grid, np.exp(lo[i]), np.exp(hi[i]), color="#1f77b4", alpha=0.25, label="95% predictive (new build)")
        ax.loglog(grid, np.exp(med[i]), color="#1f77b4", lw=1.4, label="predictive median")
        for hb in range(Btrain, P["Y"].shape[0]):
            ax.loglog(grid, np.exp(P["Y"][hb, i]), lw=1.5, ls="--", alpha=0.9,
                      label="HELD-OUT build %d (obs)" % hb if hb == Btrain else None)
        ax.axvspan(HELDOUT_BAND[0], HELDOUT_BAND[1], color="orange", alpha=0.13,
                   label="held-out band" if i == 0 else None)
        ax.set_title("DOF %s" % bm.DOF[i], fontsize=10); ax.grid(True, which="both", alpha=0.25)
        ax.set_xlabel("frequency [Hz] (log)"); ax.set_ylabel("|apparent mass| [kg or kg·m²]")
        if i == 0: ax.legend(fontsize=7.5)
    fig.suptitle("BLIND held-out calibration: predicted (95%%) vs HELD-OUT builds — new-build coverage %.2f, held-out-band coverage %.2f (target 0.95)"
                 % (results["HELD_OUT_CALIBRATION_95"]["with_d_new_builds_coverage"],
                    results["HELD_OUT_CALIBRATION_95"]["with_d_heldout_band_coverage"]), fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "blind_heldout_calibration.png", dpi=140); plt.close(fig)

    # hyperparameter posteriors
    fig, axes = plt.subplots(1, 5, figsize=(19, 3.6))
    for ax, key, lbl in zip(axes, ["k_strut_pop", "f_dome", "sigma_build", "sigma_e", "sigma_d"],
                            ["k_strut_pop [N/m]", "f_dome [Hz]", "σ_build", "σ_e (sensor, log)", "σ_d (discrepancy)"]):
        ax.hist(post[key], bins=40, density=True, color="#1f77b4", alpha=0.8)
        ax.set_title(lbl, fontsize=10); ax.grid(True, alpha=0.3)
    axes[0].axvline(P["k0"], color="#d62728", ls="--", label="nominal"); axes[0].legend(fontsize=8)
    axes[1].axvline(93.5, color="#d62728", ls="--", label="nominal 93.5"); axes[1].legend(fontsize=8)
    fig.suptitle("Blind inference: learned parameters + hyperparameters (true values SEALED — master scores)", fontsize=11)
    fig.tight_layout(); fig.savefig(FIG / "blind_posteriors.png", dpi=140); plt.close(fig)


if __name__ == "__main__":
    main()
