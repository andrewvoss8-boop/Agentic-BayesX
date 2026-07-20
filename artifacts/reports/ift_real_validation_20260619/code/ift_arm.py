#!/usr/bin/env python3
"""IFT arm — physics-in-PRIOR with a learned inverse-temperature beta (trust thermometer), on the SAME
log|H| observable as the StatFEM whole-FRF arm M2, via a DOCUMENTED log-magnitude moment approximation
(decisions_log D0/D1; human decision Andrew 2026-06-19).

WHY this construction (faithful to PIFT 2306.02150 / Alberts-Bilionis 2301.07609, adapted to ShockSat):
  - Field = reduced complex response u in C^74 at each drive frequency omega.
  - Physics-informed PRIOR on the field: pi(u|theta,beta) ~ exp(-(beta/2)||A u - f||^2 - (tau0/2)||u||^2),
    A(theta,omega) = (1+i*eta) K(theta) - omega^2 I, eta = 2*zeta, f = unit point force at the drive DOF.
    This is a complex Gaussian CN(mu_u, Sigma_u) with precision beta*A^H A + tau0 I and mean mu_u -> A^-1 f
    (the deterministic FEM response) as tau0 -> 0. beta = LEARNED inverse-temperature = trust in the physics.
  - Observation H_j(omega) = -omega^2 obs_V[s_j,:] . u is LINEAR in u  =>  H_j ~ CN(m_j, v_j),
    m_j = H_j^FEM(theta) (deterministic FEM accelerance), v_j = field-induced variance.
  - Diagonalize K = Q Lam Q^T (the eigh ALREADY in the forward). Then A^H A = Q diag(D_k) Q^T with
    D_k = (lam_k - omega^2)^2 + (eta lam_k)^2 = |g_k|^2, so (with p_j = obs_V[s_j] @ Q):
        m_j(omega) = omega^2 |sum_k p_{j,k} ud_k / g_k|,   g_k = (1+i eta) lam_k - omega^2
        v_j(omega) = omega^4 sum_k p_{j,k}^2 / (beta D_k + tau0)      (field-induced response variance)
    No extra solve; differentiable in theta (lam, Q) and beta.
  - MOMENT APPROXIMATION (the one honest deviation; Andrew's directive): log|H_j| with H_j ~ CN(m_j, v_j)
    is log-Rician, NOT Gaussian. We marginalize the field by matching the first two moments (delta-method /
    high-SNR propagation of CN through log|.|):
        E[log|H_j|]  ~= log|m_j| = log|H_j^FEM(theta)|
        Var[log|H_j|] ~= v_j / (2 |m_j|^2)
    LIKELIHOOD (observed channels x in-band frequencies):
        log|H_j^meas|(omega) ~ N( log|H_j^FEM(theta)| + c , sigma_meas^2 + v_j(omega;theta,beta)/(2|m_j|^2) )
    c = global units-gain nuisance (the ~x100-500 mass-norm/g constant, StatFEM D4); sigma_meas = 0.15.

  => IFT = a log|H| likelihood (SAME observable as M2) whose per-bin variance is PHYSICS-DERIVED and set by
     ONE learned trust scalar beta, vs M2's free sigma_d^2 x fixed-length Kronecker discrepancy. beta -> inf
     recovers a plain log|H| likelihood with only sigma_meas (full physics trust); beta -> 0 widens gracefully.
     The resonance singularity (D_k -> (eta lam_k)^2 small at omega^2 = lam_k) is the physical "FRF most
     uncertain at resonances"; the hysteretic damping (eta lam_k)^2 > 0 keeps A^H A positive-definite (tau0 is
     a tiny numerical jitter, NOT the regularizer). This is the apples-to-apples test of WHERE physics/trust
     lives (IFT prior vs M2 likelihood) on the IDENTICAL observable.

SCOPE of the approximation (carried as YELLOW everywhere): exact at high SNR K_j = |m_j|^2/v_j >> 1; biased in
deep antiresonances (low SNR), where v_j/(2|m_j|^2) is already large -> the likelihood near-ignores those bins,
so the error sits where the term is downweighted. Data is dynamic-range-eligible (median peak/floor ~147x) so
the informative peaks are high-SNR. We report per-(channel,freq) SNR.

Reuses (imports, never edits) the copied byte-identical realfrf.py (same forward), score.py (same scorer), and
the same split RNG as heldout_qoi.py. No results copied from any IFT/PIFT repo.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import jax
import jax.numpy as jnp
import numpyro
import numpyro.distributions as dist
from numpyro.diagnostics import summary as nuts_summary
from numpyro.infer import MCMC, NUTS, init_to_median

jax.config.update("jax_enable_x64", True)

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import score as SC

WS = Path(__file__).resolve().parent.parent

# ---- inherited assumptions (match StatFEM run; assumptions_ledger) --------------------------------
SIGMA_MEAS = 0.15          # iid log measurement+window+map noise floor on the real FRF (D1; swept)
NSIG_THETA = 0.25          # theta LogNormal(0,0.25) prior (StatFEM)
GAIN_PRIOR_SD = 1.5        # global units-gain c ~ Normal(c0, 1.5) (StatFEM D4)
ZETA = rf.ZETA_NOM         # 0.01 hysteretic-equiv modal damping (eta = 2 zeta)
DR_MIN = 30.0              # dynamic-range-eligible channels (SAME as heldout_qoi.py -> identical splits)
G_IN_S2 = rf.G_IN_S2
LOGG = float(np.log(G_IN_S2))
TAU0 = 1e-12               # numerical jitter only; the (eta lam)^2 damping is the physical regularizer
BETA_PRIOR_SD = 2.0        # log-beta prior sd (~1.7 decades each way; matches consistency toy); swept in §11

# the 4 FIM/strain-energy-identifiable groups (StatFEM identifiability gate) for the fair comparison
GNAMES = rf.GNAMES
IDENT_GROUPS = [GNAMES.index(g) for g in ("bottom_box", "top_box", "plates", "cross_beam")]


# =================================================================== field moments (jax, for NUTS)
def jax_moments_factory(R, freqs, resp_rows, drive_row, zeta=ZETA):
    """Returns moments(theta, beta) -> (logmag_glb (Nf,Ns), field_logvar (Nf,Ns)).
    logmag_glb = log|H g/lbf| (FEM mean, NO gain); field_logvar = v_j/(2|m_j|^2) (dimensionless)."""
    A = jnp.asarray(R.A); A_fix = jnp.asarray(R.A_fix)
    Rr = jnp.asarray(resp_rows); Dr = jnp.asarray(drive_row)
    w = jnp.asarray(2 * np.pi * np.asarray(freqs)); w2 = w ** 2; w4 = w2 ** 2
    eta = 2.0 * float(zeta)

    def moments(theta, beta):
        K = A_fix + jnp.einsum("g,gij->ij", theta, A)
        lam, Q = jnp.linalg.eigh(K)
        lam = jnp.clip(lam, 1e-9, None)
        p = Rr @ Q                                   # (Ns, r)  channel modal participation
        ud = Dr @ Q                                  # (r,)     drive modal participation
        g = (1.0 + 1j * eta) * lam[None, :] - w2[:, None]            # (Nf, r) complex
        Dk = (lam[None, :] - w2[:, None]) ** 2 + (eta * lam[None, :]) ** 2   # (Nf, r) = |g|^2
        H = -w2[:, None] * jnp.einsum("sk,k,fk->fs", p.astype(jnp.complex128),
                                      ud.astype(jnp.complex128), 1.0 / g)     # (Nf, Ns) raw
        m2 = jnp.abs(H) ** 2                                                  # (Nf, Ns) raw |m|^2
        v = w4[:, None] * jnp.einsum("sk,fk->fs", p ** 2, 1.0 / (beta * Dk + TAU0))   # (Nf, Ns) raw v_j
        field_logvar = v / (2.0 * m2 + 1e-300)
        logmag_glb = jnp.log(jnp.abs(H) + 1e-300) - LOGG
        return logmag_glb, field_logvar

    return moments


# =================================================================== field moments (numpy, batched, for prediction)
def moments_np_batch(R, freqs, theta_batch, beta_batch, resp_rows, drive_row, zeta=ZETA, chunk=100):
    """theta_batch (M,9), beta_batch (M,) -> logmag_glb (M,Nf,Ns) [log|H g/lbf|, no gain],
    field_logvar (M,Nf,Ns) [dimensionless v_j/(2|m_j|^2)]."""
    theta_batch = np.atleast_2d(theta_batch); beta_batch = np.atleast_1d(beta_batch)
    M = theta_batch.shape[0]
    w = 2 * np.pi * np.asarray(freqs); w2 = w ** 2; w4 = w2 ** 2
    eta = 2.0 * float(zeta); Nf = len(freqs); Ns = resp_rows.shape[0]
    lm = np.empty((M, Nf, Ns)); flv = np.empty((M, Nf, Ns))
    for s0 in range(0, M, chunk):
        th = theta_batch[s0:s0 + chunk]; bt = beta_batch[s0:s0 + chunk]
        K = R.A_fix[None] + np.einsum("cg,gij->cij", th, R.A)
        lam, Q = np.linalg.eigh(K); lam = np.clip(lam, 1e-9, None)
        p = np.einsum("sm,cmk->csk", resp_rows, Q)                       # (c,Ns,r)
        ud = np.einsum("m,cmk->ck", drive_row, Q)                        # (c,r)
        g = (1.0 + 1j * eta) * lam[:, None, :] - w2[None, :, None]        # (c,Nf,r)
        Dk = (lam[:, None, :] - w2[None, :, None]) ** 2 + (eta * lam[:, None, :]) ** 2
        H = -w2[None, :, None] * np.einsum("csk,ck,cfk->cfs",
                                           p.astype(complex), ud.astype(complex), 1.0 / g)   # (c,Nf,Ns)
        m2 = np.abs(H) ** 2
        v = w4[None, :, None] * np.einsum("csk,cfk->cfs", p ** 2, 1.0 / (bt[:, None, None] * Dk + TAU0))
        lm[s0:s0 + chunk] = np.log(np.abs(H) + 1e-300) - LOGG
        flv[s0:s0 + chunk] = v / (2.0 * m2 + 1e-300)
    return lm, flv


def beta_star(R, freqs, resp_rows, drive_row, zeta=ZETA, sigma_meas=SIGMA_MEAS):
    """Forward-model prior-centering constant (uses NO measured/held-out data, D2): beta* makes the median
    field log-variance over (channel,freq) equal sigma_meas^2 at nominal theta=1. Since field_logvar ~ 1/beta,
    field_logvar(beta) = field_logvar(beta=1)/beta -> beta* = median(field_logvar(beta=1)) / sigma_meas^2."""
    _, flv1 = moments_np_batch(R, freqs, np.ones((1, 9)), np.ones(1), resp_rows, drive_row, zeta)
    fl1 = np.median(flv1[0])
    return float(fl1 / sigma_meas ** 2)


# =================================================================== NUTS model + run
def make_model(moments, target_obs, c0, beta_star_val, sigma_meas=SIGMA_MEAS,
               free_groups=None, beta_prior_sd=BETA_PRIOR_SD, fixed_beta=None):
    tgt = jnp.asarray(target_obs)                      # (Nf, Ns) measured log|H g/lbf| on observed channels
    fg = list(range(9)) if free_groups is None else list(free_groups)
    fg_arr = jnp.asarray(np.array(fg)); nfree = len(fg)
    logbstar = float(np.log(beta_star_val))

    def model():
        log_theta_f = numpyro.sample("log_theta", dist.Normal(0.0, NSIG_THETA).expand([nfree]).to_event(1))
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(log_theta_f))
        if fixed_beta is not None:
            beta = float(fixed_beta)
        else:
            log_beta = numpyro.sample("log_beta", dist.Normal(logbstar, beta_prior_sd))
            beta = jnp.exp(log_beta)
        numpyro.deterministic("beta", beta)
        c = numpyro.sample("gain", dist.Normal(c0, GAIN_PRIOR_SD))
        logm, field_lv = moments(theta, beta)
        mean = logm + c
        var = sigma_meas ** 2 + field_lv
        R = tgt - mean
        numpyro.factor("lik", -0.5 * jnp.sum(R ** 2 / var + jnp.log(2 * jnp.pi * var)))

    return model


def run_ift(R, freqs, target_obs, resp_rows_obs, drive_row, c0, beta_star_val,
            zeta=ZETA, sigma_meas=SIGMA_MEAS, free_groups=None, beta_prior_sd=BETA_PRIOR_SD,
            fixed_beta=None, num_warmup=1000, num_samples=1000, num_chains=4, seed=20260619,
            max_tree_depth=8):
    moments = jax_moments_factory(R, freqs, resp_rows_obs, drive_row, zeta=zeta)
    model = make_model(moments, target_obs, c0, beta_star_val, sigma_meas=sigma_meas,
                       free_groups=free_groups, beta_prior_sd=beta_prior_sd, fixed_beta=fixed_beta)
    kernel = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median,
                  dense_mass=True, max_tree_depth=max_tree_depth)
    mcmc = MCMC(kernel, num_warmup=num_warmup, num_samples=num_samples, num_chains=num_chains,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    grouped = mcmc.get_samples(group_by_chain=True)
    # convergence over SAMPLED variables only (exclude the deterministic 'beta' alias; log_beta covers it)
    diag_vars = {k: v for k, v in grouped.items() if k != "beta"}
    stats = nuts_summary(diag_vars, group_by_chain=True)
    max_rhat = max(float(np.nanmax(v["r_hat"])) for v in stats.values())
    min_ess = min(float(np.nanmin(v["n_eff"])) for v in stats.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in grouped.items()}
    converged = bool(max_rhat <= 1.05 and min_ess >= 200 and div / (num_chains * num_samples) < 0.02)
    diag = {"max_rhat": max_rhat, "min_ess": min_ess, "divergences": div,
            "div_frac": div / (num_chains * num_samples), "n_chains": num_chains,
            "draws": num_chains * num_samples, "converged": converged,
            "rhat_per_var": {k: float(np.nanmax(v["r_hat"])) for k, v in stats.items()}}
    return flat, diag


# =================================================================== held-out QOI prediction + scoring
def predict_score_heldout(R, freqs, flat, theta_full_fn, ho_rows, drive_row, c_draws,
                          peak_truth, band_truth, zeta=ZETA, sigma_meas=SIGMA_MEAS, n_draws=300, seed=0):
    """IFT held-out-sensor QOI predictive. The widening is the PHYSICS-DERIVED field uncertainty (beta-controlled
    field_logvar), applied as a QOI-level log-normal multiplier (peak: field std at the peak frequency; band:
    energy-weighted field std over the band) -- the IFT analog of L5's marginal QOI discrepancy, avoiding the
    white-per-bin-then-max() peak-inflation pitfall (heldout_qoi.py). theta_full_fn maps a draw -> (9,) theta."""
    nsamp = len(flat["gain"])
    sub = np.linspace(0, nsamp - 1, min(nsamp, n_draws)).astype(int)
    theta_b = np.array([theta_full_fn(i) for i in sub])         # (M,9)
    beta_b = np.exp(flat["log_beta"][sub]) if "log_beta" in flat else np.full(len(sub), np.nan)
    c_b = c_draws[sub] if c_draws.ndim else c_draws
    lm_ho, flv_ho = moments_np_batch(R, freqs, theta_b, beta_b, ho_rows, drive_row, zeta)  # (M,Nf,Nho)
    M, Nf, Nho = lm_ho.shape
    rng = np.random.default_rng(seed + 17)
    peak_pred = np.zeros((M, Nho)); band_pred = np.zeros((M, Nho))
    df = freqs
    for j in range(M):
        Hmag = np.exp(lm_ho[j] + c_b[j])                        # (Nf,Nho) g/lbf predictive median curve
        std = np.sqrt(sigma_meas ** 2 + flv_ho[j])             # (Nf,Nho) per-bin field+meas log-std
        for k in range(Nho):
            col = Hmag[:, k]
            ipk = int(np.argmax(col))
            peak_pred[j, k] = col[ipk] * np.exp(rng.normal(0.0, std[ipk, k]))           # peak: std at peak freq
            wE = col ** 2 / max((col ** 2).sum(), 1e-300)                                # energy weight
            s_band = float(np.sqrt(np.sum(wE * std[:, k] ** 2)))                          # energy-wt field std
            band_pred[j, k] = np.sqrt(np.trapz(col ** 2, df)) * np.exp(rng.normal(0.0, s_band))
    pk = [SC.score_qoi(peak_pred[:, k], peak_truth[k]) for k in range(Nho)]
    bd = [SC.score_qoi(band_pred[:, k], band_truth[k]) for k in range(Nho)]
    return {"peak": _agg(pk), "band": _agg(bd)}, peak_pred, band_pred


def _agg(scores):
    if not scores:
        return {}
    keys = ("interval_score", "crps", "logpd")
    out = {k + "_mean": float(np.mean([s[k] for s in scores])) for k in keys}
    out["coverage_frac"] = float(np.mean([s["covered"] for s in scores]))
    out["mean_width_db"] = float(np.mean([s["width_db"] for s in scores]))
    out.update(SC.aggregate_pit_z([s["pit"] for s in scores], [s["z"] for s in scores]))
    out["n_channels"] = len(scores)
    return out


# =================================================================== one split end-to-end (resumable cell)
def wmedian(x, w):
    x = np.asarray(x, float); w = np.asarray(w, float)
    if x.size == 0:
        return 0.0
    idx = np.argsort(x); x = x[idx]; w = w[idx]; cw = np.cumsum(w)
    if cw[-1] <= 0:
        return float(np.median(x))
    return float(x[np.searchsorted(cw, 0.5 * cw[-1])])


def run_split(seed=0, obs_frac=0.6, free_groups=None, beta_prior_sd=BETA_PRIOR_SD, sigma_meas=SIGMA_MEAS,
              fixed_beta=None, warmup=1000, samples=1000, chains=4, n_draws=300, write=True, force=False,
              tag="ift"):
    """IFT arm on ONE held-out-sensor split (SAME split RNG as heldout_qoi.py -> apples-to-apples)."""
    outp = WS / "out" / "ift_cells" / f"{tag}_seed{seed:02d}.json"
    if write and outp.exists() and not force:
        print(f"[skip] {outp.name}")
        return json.loads(outp.read_text())
    t0 = time.time()
    fg = IDENT_GROUPS if free_groups is None else free_groups
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}

    # ---- SAME split as heldout_qoi.run (DR_MIN, obs_frac, rng) ----
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= DR_MIN)[0]
    perm = np.random.default_rng(seed).permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]; n_o = len(obs_pos); n_ho = len(ho_pos)

    # measured truth log|H g/lbf| on observed + held-out, in band
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T   # (Nf,n_o)
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T     # (Nf,n_ho)
    wq_obs = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T

    # ---- prior centering: gain c0 (observed-only, nominal theta) + beta* (forward-model only) ----
    lm0 = rf.fem_logmag(R, freqs, np.ones(9), obs_rows, ch.drive_row, zeta=ZETA)                 # (Nf,n_o)
    c0 = wmedian((tru_obs - lm0).ravel(), wq_obs.ravel())
    bstar = beta_star(R, freqs, obs_rows, ch.drive_row, zeta=ZETA, sigma_meas=sigma_meas)

    # ---- NUTS (incl. beta) on observed channels ----
    flat, diag = run_ift(R, freqs, tru_obs, obs_rows, ch.drive_row, c0, bstar, zeta=ZETA,
                         sigma_meas=sigma_meas, free_groups=fg, beta_prior_sd=beta_prior_sd,
                         fixed_beta=fixed_beta, num_warmup=warmup, num_samples=samples,
                         num_chains=chains, seed=20260619 + seed)

    # full-9 theta per draw (fixed groups = 1.0)
    log_theta = flat["log_theta"]                       # (nsamp, nfree)

    def theta_full_fn(i):
        th = np.ones(9); th[np.array(fg)] = np.exp(log_theta[i]); return th

    # per-draw gain c (observed-only, like L5: refit c at the draw's theta for a fair held-out level)
    nsamp = log_theta.shape[0]
    sub = np.linspace(0, nsamp - 1, min(nsamp, n_draws)).astype(int)
    c_draws_all = np.zeros(nsamp)
    # fast: compute observed FEM logmag for the subsampled draws to refit c, broadcast back is not needed
    theta_sub = np.array([theta_full_fn(i) for i in sub])
    lm_obs_sub = rf.fem_logmag_batch(R, freqs, theta_sub, obs_rows, ch.drive_row, zeta=ZETA)     # (M,Nf,n_o)
    c_sub = np.array([wmedian((tru_obs - lm_obs_sub[m]).ravel(), wq_obs.ravel()) for m in range(len(sub))])
    c_draws_all[sub] = c_sub
    # (predict_score uses the same `sub`; pass an aligned c-array)
    c_full = np.zeros(nsamp); c_full[sub] = c_sub

    # ---- truth QOI + held-out scoring ----
    peak_tru_ho = np.array([SC_qoi_peak(np.exp(tru_ho[:, k])) for k in range(n_ho)])
    band_tru_ho = np.array([SC_qoi_band(np.exp(tru_ho[:, k]), freqs) for k in range(n_ho)])
    scores, peak_pred, band_pred = predict_score_heldout(
        R, freqs, flat, theta_full_fn, ho_rows, ch.drive_row, c_full, peak_tru_ho, band_tru_ho,
        zeta=ZETA, sigma_meas=sigma_meas, n_draws=n_draws, seed=seed)

    # ---- beta posterior + identifiability (vs prior log-sd) ----
    if "log_beta" in flat:
        lb = flat["log_beta"]; med, lo, hi = np.percentile(lb, [50, 2.5, 97.5])
        ci_w = float(hi - lo)
        beta_post = {"logbeta_med": float(med), "logbeta_lo": float(lo), "logbeta_hi": float(hi),
                     "logbeta_ci_width": ci_w, "beta_med": float(np.exp(med)),
                     "beta_star": bstar, "log_beta_star": float(np.log(bstar)),
                     "prior_logsd": beta_prior_sd,
                     "weakly_identified": bool(ci_w > 0.5 * 2 * 1.96 * beta_prior_sd)}
    else:
        beta_post = {"fixed_beta": float(fixed_beta)}

    rec = {
        "deliverable": "IFT_heldout_sensor_QOI", "arm": "IFT_physics_prior_learned_beta",
        "qoi": ["peak_accelerance_g_per_lbf", "band_GRMS_g_per_lbf"],
        "observable": "log|H| (SAME as StatFEM M2; log-magnitude moment approximation, D0/D1)",
        "split_seed": seed, "obs_frac": obs_frac, "free_groups": [GNAMES[i] for i in fg],
        "n_channels_eligible": int(len(elig)), "n_observed": int(n_o), "n_heldout": int(n_ho),
        "observed_daqs": [int(d) for d in obs_daqs], "heldout_daqs": [int(d) for d in ho_daqs],
        "sigma_meas": sigma_meas, "zeta": ZETA, "beta_prior_sd": beta_prior_sd,
        "convergence": diag, "beta_posterior": beta_post,
        "gain_c0": float(c0), "gain_c_med": float(np.median(c_sub)),
        "scores": scores, "n_draws_used": int(len(sub)), "runtime_s": time.time() - t0,
    }
    if write:
        outp.parent.mkdir(parents=True, exist_ok=True)
        outp.write_text(json.dumps(rec, indent=2))
        print(f"IFT seed {seed}: obs {n_o} / held {n_ho} | converged={diag['converged']} "
              f"R-hat {diag['max_rhat']:.3f} ESS {diag['min_ess']:.0f} div {diag['divergences']} | "
              f"beta_med {beta_post.get('beta_med', float('nan')):.3g} (beta* {bstar:.3g}) "
              f"weakID={beta_post.get('weakly_identified')}")
        print(f"  PEAK cover {scores['peak']['coverage_frac']:.2f} interval {scores['peak']['interval_score_mean']:.3g} "
              f"CRPS {scores['peak']['crps_mean']:.3g} z-std {scores['peak']['z_std']:.2f} | "
              f"BAND cover {scores['band']['coverage_frac']:.2f} interval {scores['band']['interval_score_mean']:.3g}")
        print(f"  runtime {rec['runtime_s']:.0f}s -> {outp}")
    return rec


SC_qoi_peak = rf.core.qoi_peak
SC_qoi_band = rf.core.qoi_band


if __name__ == "__main__":
    kw = {}
    for a in sys.argv[1:]:
        if a.startswith("--seed="): kw["seed"] = int(a.split("=")[1])
        elif a.startswith("--warmup="): kw["warmup"] = int(a.split("=")[1])
        elif a.startswith("--samples="): kw["samples"] = int(a.split("=")[1])
        elif a.startswith("--chains="): kw["chains"] = int(a.split("=")[1])
        elif a.startswith("--ndraws="): kw["n_draws"] = int(a.split("=")[1])
        elif a == "--force": kw["force"] = True
    run_split(**kw)
