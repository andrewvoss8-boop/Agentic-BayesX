#!/usr/bin/env python3
"""L5 — modal peak-FREQUENCY feature likelihood, extracting peaks FROM the real single-impact FRF (D9/D10).

Why: the whole-|H| magnitude likelihood is locally-identifiable/near-singular on real data (NUTS R-hat 104,
TMCMC R-hat 129 — D6/D7/D10). The FE-updating literature's well-behaved choice is the MODAL/eigenvalue
likelihood (Kiran §4.3.1, Eq 25): match FEM eigenvalues ω_r²(θ) to MEASURED modal frequencies. We extract the
measured frequencies from the REAL FRF (hit-001, single-impact) — still Andrew's real-FRF observable, just its
identifiable PEAK FEATURES instead of every magnitude point. Our own modal twin proved this converges (R-hat
1.022) on this exact structure. Eigenvalues are cleanly differentiable (no eigenvector degeneracy) → NUTS works.

Likelihood (Kiran Eq 25):  ln p = -0.5 Σ_r [ (ω̂_r² - ω_r²(θ))² / σ² + log(2π σ²) ],  σ = modal-freq error std.
θ ~ LogNormal(0,0.25); σ (rel) ~ HalfNormal. NUTS 4 chains, all-variable gate.

Output: out/modal_feature.json (extracted modes, matches, convergence, θ posterior, held-out-mode prediction).
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
from scipy.signal import find_peaks

import jax, jax.numpy as jnp
import numpyro, numpyro.distributions as dist
from numpyro.diagnostics import summary as nuts_summary
from numpyro.infer import MCMC, NUTS, init_to_median
jax.config.update("jax_enable_x64", True)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf

WS = Path(__file__).resolve().parent.parent
DR_MIN = 30.0


def extract_measured_modes(meas, ch, dr_min=DR_MIN, min_channels=4, bin_hz=1.5, tol_hz=2.5):
    """Consensus modal frequencies = where MANY channels independently place a peak. For each high-DR channel
    collect its in-band peaks (≤1 vote per channel per ~bin), histogram the pooled peaks, and take local maxima
    of the histogram with support >= min_channels distinct channels. Returns frequencies [Hz] + channel support."""
    fr = meas["freqs"]; bm = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); fb = fr[bm]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    chan_peaks = []
    for d in ch.daq:
        if meas["dyn_range"][didx[d]] <= dr_min:
            continue
        mag = np.abs(meas["H"][didx[d]][bm])
        pk, _ = find_peaks(mag, prominence=mag.max() * 0.06)
        chan_peaks.append(fb[pk])
    edges = np.arange(rf.BAND[0], rf.BAND[1] + bin_hz, bin_hz)
    centers = 0.5 * (edges[:-1] + edges[1:])
    hist = np.zeros(len(centers))
    for pks in chan_peaks:                       # 1 vote per channel per bin
        b = np.unique(np.clip(np.digitize(pks, edges) - 1, 0, len(centers) - 1))
        hist[b] += 1
    loc, _ = find_peaks(hist, height=min_channels, distance=max(1, int(round(tol_hz / bin_hz))))
    freqs, support = [], []
    for i in loc:
        # refine: channel-support count within tol of this candidate, support-weighted mean frequency
        cand = centers[i]
        sup = sum(np.any(np.abs(pks - cand) <= tol_hz) for pks in chan_peaks)
        if sup >= min_channels:
            near = np.concatenate([pks[np.abs(pks - cand) <= tol_hz] for pks in chan_peaks if np.any(np.abs(pks - cand) <= tol_hz)])
            freqs.append(float(np.median(near))); support.append(int(sup))
    order = np.argsort(freqs)
    return np.array(freqs)[order], np.array(support)[order]


def fem_modes_np(R, theta):
    K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
    lam = np.clip(np.linalg.eigvalsh(K), 1e-9, None)
    return np.sqrt(lam) / (2 * np.pi)


def match(R, meas_f, tol_pct=12.0):
    """Match each measured frequency to the nearest FEM mode index at θ=1 (within tol_pct). Returns matched
    (mode_index, measured_hz) pairs + the held-out (unmatched-to-a-used-mode) for prediction."""
    femf = fem_modes_np(R, np.ones(9))
    pairs, used = [], set()
    for mf in meas_f:
        j = int(np.argmin(np.abs(femf - mf)))
        if abs(femf[j] - mf) / mf <= tol_pct / 100 and j not in used:
            pairs.append((j, float(mf))); used.add(j)
    return pairs, femf


def calibrate_modal(R, obs_mode_idx, obs_w_hz, fg=None, seed=20260617, warmup=1000, samples=1000, chains=4):
    """Reusable L5 calibration (additive helper; the converged run() below is untouched).

    Calibrate the 9-group stiffness multipliers theta from MEASURED modal frequencies (Kiran Eq 25,
    eigenVALUE likelihood) on a GIVEN set of FEM mode indices `obs_mode_idx` matched to measured
    frequencies `obs_w_hz` [Hz]. Same model form, prior, and NUTS config as run(). Returns
    (theta_post (Ndraws,9), sigma_w2 (Ndraws,), diag dict). Used by the held-out-SENSOR QOI predictor."""
    fg = list(range(9)) if fg is None else list(fg)
    A = jnp.asarray(R.A); A_fix = jnp.asarray(R.A_fix)
    obs_modes = jnp.asarray(np.asarray(obs_mode_idx))
    tgt_w2 = jnp.asarray((np.asarray(obs_w_hz) * 2 * np.pi) ** 2)
    fg_arr = jnp.asarray(np.array(fg)); nfree = len(fg)

    def model():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, rf.core.NSIG_THETA).expand([nfree]).to_event(1))
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(lt))
        sig = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        K = A_fix + jnp.einsum("g,gij->ij", theta, A)
        lam = jnp.clip(jnp.linalg.eigvalsh(K), 1e-9, None)
        w2 = lam[obs_modes]
        var = (sig * tgt_w2) ** 2
        numpyro.factor("lik", -0.5 * jnp.sum((tgt_w2 - w2) ** 2 / var + jnp.log(2 * jnp.pi * var)))

    kernel = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median, dense_mass=True, max_tree_depth=8)
    mcmc = MCMC(kernel, num_warmup=warmup, num_samples=samples, num_chains=chains,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in g.items()}
    stats = nuts_summary(g, group_by_chain=True)
    max_rhat = max(float(np.nanmax(v["r_hat"])) for v in stats.values())
    min_ess = min(float(np.nanmin(v["n_eff"])) for v in stats.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    theta_post = np.ones((flat["log_theta"].shape[0], 9)); theta_post[:, fg] = np.exp(flat["log_theta"])
    diag = {"max_rhat": max_rhat, "min_ess": min_ess, "divergences": div,
            "div_frac": div / (chains * samples), "n_chains": chains, "draws": chains * samples,
            "converged": bool(max_rhat <= 1.05 and min_ess >= 200 and div < 0.02 * chains * samples)}
    return theta_post, flat["sigma_w2"], diag


def run(free_groups=None, n_obs_modes=None, seed=20260617, warmup=1000, samples=1000, chains=4):
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    meas_f, support = extract_measured_modes(meas, ch)
    pairs, femf0 = match(R, meas_f)
    idx = np.array([p[0] for p in pairs]); wmeas = np.array([p[1] for p in pairs])
    # held-out split over MODES: observe first n_obs, predict the rest
    n_match = len(pairs)
    n_obs = n_match if n_obs_modes is None else min(n_obs_modes, n_match - 1)
    obs_idx, obs_w = idx[:n_obs], wmeas[:n_obs]
    ho_idx, ho_w = idx[n_obs:], wmeas[n_obs:]
    fg = list(range(9)) if free_groups is None else list(free_groups)
    A = jnp.asarray(R.A); A_fix = jnp.asarray(R.A_fix)
    obs_modes = jnp.asarray(obs_idx)
    tgt_w2 = jnp.asarray((obs_w * 2 * np.pi) ** 2)            # measured ω² on observed modes
    fg_arr = jnp.asarray(np.array(fg)); nfree = len(fg)

    def model():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, rf.core.NSIG_THETA).expand([nfree]).to_event(1))
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(lt))
        sig = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))   # rel. ω² error std
        K = A_fix + jnp.einsum("g,gij->ij", theta, A)
        lam = jnp.clip(jnp.linalg.eigvalsh(K), 1e-9, None)        # eigenVALUES: clean gradients
        w2 = lam[obs_modes]
        var = (sig * tgt_w2) ** 2
        numpyro.factor("lik", -0.5 * jnp.sum((tgt_w2 - w2) ** 2 / var + jnp.log(2 * jnp.pi * var)))

    t0 = time.time()
    kernel = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median, dense_mass=True, max_tree_depth=8)
    mcmc = MCMC(kernel, num_warmup=warmup, num_samples=samples, num_chains=chains,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in g.items()}
    stats = nuts_summary(g, group_by_chain=True)
    max_rhat = max(float(np.nanmax(v["r_hat"])) for v in stats.values())
    min_ess = min(float(np.nanmin(v["n_eff"])) for v in stats.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    conv = max_rhat <= 1.05 and min_ess >= 200 and div < 0.02 * chains * samples
    # held-out-mode prediction: posterior FEM frequency at held-out mode indices vs measured
    theta_post = np.ones((flat["log_theta"].shape[0], 9)); theta_post[:, fg] = np.exp(flat["log_theta"])
    ho_cov = []
    import score as SC
    ho_scores = []
    for j, mode_j in enumerate(ho_idx):
        fpred = np.array([fem_modes_np(R, theta_post[s])[mode_j] for s in
                          np.linspace(0, len(theta_post) - 1, 300).astype(int)])
        sc = SC.score_qoi(fpred, ho_w[j])
        ho_cov.append(sc["covered"]); ho_scores.append(sc)
    rec = {"likelihood": "L5_modal_peak_frequency", "observable": "peaks_from_real_FRF",
           "n_measured_modes": len(meas_f), "measured_freqs_hz": [round(x, 1) for x in meas_f.tolist()],
           "n_matched": n_match, "matched_pairs_modeidx_hz": [[int(p[0]), round(p[1], 1)] for p in pairs],
           "n_observed_modes": int(n_obs), "n_heldout_modes": int(len(ho_idx)),
           "free_groups": [rf.GNAMES[i] for i in fg], "runtime_s": time.time() - t0,
           "diag": {"max_rhat": max_rhat, "min_ess": min_ess, "divergences": div,
                    "div_frac": div / (chains * samples), "n_chains": chains, "draws": chains * samples},
           "converged": bool(conv),
           "sigma_w2_rel": {"med": float(np.median(flat["sigma_w2"])),
                            "lo": float(np.percentile(flat["sigma_w2"], 2.5)),
                            "hi": float(np.percentile(flat["sigma_w2"], 97.5))},
           "theta_post": {rf.GNAMES[g_]: {"med": float(np.median(theta_post[:, g_])),
                                          "lo": float(np.percentile(theta_post[:, g_], 2.5)),
                                          "hi": float(np.percentile(theta_post[:, g_], 97.5))} for g_ in fg},
           "heldout_mode_coverage": {"covered": int(np.sum(ho_cov)), "n": len(ho_idx),
                                     "frac": float(np.mean(ho_cov)) if ho_cov else None},
           "heldout_mode_interval_score_mean": float(np.mean([s["interval_score"] for s in ho_scores])) if ho_scores else None}
    (WS / "out").mkdir(exist_ok=True)
    (WS / "out" / "modal_feature.json").write_text(json.dumps(rec, indent=2))
    print(f"L5 modal-feature: {len(meas_f)} measured modes, {n_match} matched to FEM; "
          f"observe {n_obs}, hold out {len(ho_idx)}")
    print(f"  CONVERGED={conv} R-hat {max_rhat:.3f} ESS {min_ess:.0f} div {div} | "
          f"sigma_w2 {rec['sigma_w2_rel']['med']:.3f} | {rec['runtime_s']:.0f}s")
    print(f"  held-out-mode coverage: {rec['heldout_mode_coverage']}")
    print("  theta medians:", {rf.GNAMES[g_]: round(float(np.median(theta_post[:, g_])), 2) for g_ in fg})
    return rec


if __name__ == "__main__":
    run(n_obs_modes=None)
