#!/usr/bin/env python3
"""A4 — 1-D profile likelihood of the iid log-magnitude whole-FRF likelihood that failed.

Target likelihood (documented from the frozen source, arm_b_nuts.py --theta-only, fold m_xpos_990x):
  y_{d,ch}(f) = log10|H1_meas| ; mu = log10|H_model(theta)| + gain_d  (windowed exact-eigh forward,
  Galerkin sub-basis r0=118, likelihood band 45-400 Hz, thin 2, <=30 ch/drive, 3 train drives)
  resid iid ~ Normal(0, sigma_n);  priors (for the penalized variant): log theta_g ~ N(0,0.25),
  gain_d ~ N(0,1) dex, sigma_n ~ HalfNormal(0.2).
This is the variant whose 4-chain NUTS separated (stored R-hat 44.7 on this fold, per-chain draws
retained frozen at out/armB/theta_only_m_xpos_990x.npz).

Profile: for the TWO stiffness multipliers with the largest whole-FRF sensitivity (energy-weighted RMS
of d log10|H| / d log theta_g at theta=1, central finite difference, step 0.01), sweep 41 log-spaced
points over the prior 95% range exp(+-1.96*0.25); other theta fixed at 1. At each grid point the
nuisances (3 drive gains, sigma_n) are PROFILED (optimized out), not frozen:
  - closed form: gain_d* = mean residual of that drive; sigma_n* = RMS residual after gains
    (exact MLE; verified by gradient norm at the optimum, recorded per point)
  - penalized (log-posterior) variant: L-BFGS-B from the closed form, priors added; also recorded.
Deterministic; no sampler. Output: out/a4_profile_likelihood.json
"""
import json
import os
import sys
import time
import numpy as np
from scipy.optimize import minimize

t0 = time.time()
WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
REPORTS = os.path.abspath(os.path.join(WS, ".."))
FSWS = os.path.join(REPORTS, "shocksat_full_spectrum_frf_20260714")
sys.path.insert(0, os.path.join(FSWS, "code"))
import arm_b_nuts as AB                    # noqa: E402  (frozen; module-level import only)
import jax.numpy as jnp                    # noqa: E402

FOLD = "m_xpos_990x"
NGRID = 41
LO, HI = np.exp(-1.96 * 0.25), np.exp(1.96 * 0.25)
GRID = np.exp(np.linspace(np.log(LO), np.log(HI), NGRID))

pkg = AB.WP.load("A0_wide")
sub = AB.SubBasis(pkg)
zf, zz = AB.WFW.WF.survey_table()
zmed = float(np.median(zz))
train_keys, data = AB.build_fold_data(pkg, FOLD, thin_bins=2, n_ch_max=30)
A_sub = jnp.asarray(sub.A_sub)
A_fix_sub = jnp.asarray(sub.A_fix_sub)
sens = jnp.asarray(sub.sens_sub)
GNAMES = [str(g) for g in np.asarray(pkg.gnames)] if hasattr(pkg, "gnames") else [
    "al_welds", "angle_brackets", "bottom_box", "contact", "cross_beam",
    "joints", "plates", "steel_welds", "top_box"]


def forward_mu0(theta):
    """Per-drive model log10|H| (no gain), replicating make_model() math exactly."""
    K = A_fix_sub + jnp.einsum("g,gij->ij", jnp.asarray(theta), A_sub)
    lam, Q = jnp.linalg.eigh(K)
    f = jnp.sqrt(jnp.clip(lam, 1e-6, None)) / (2 * jnp.pi)
    m_in = (f >= AB.F_SUPPORT[0]) & (f <= AB.F_SUB * 0.95)
    zi = jnp.where(f > zf[-1], zmed, jnp.interp(f, jnp.asarray(zf), jnp.asarray(zz)))
    Us_all = sens @ Q
    f_safe = jnp.where(m_in, f, 1e6)
    mus = {}
    for d in data:
        Ud = (jnp.asarray(sub.drv_sub[d["key"]]) @ Q) * m_in
        res = Us_all[d["rows"]] * Ud[None, :]
        mus[d["key"]] = np.asarray(AB.jax_windowed_logH(res, f_safe, zi, jnp.asarray(d["kbins"])))
    return mus


N_TOT = sum(d["y"].size for d in data)


def profiled_loglik(mus):
    """Closed-form nuisance optimum + iid Gaussian loglik + gradient-norm verification."""
    gains = {d["key"]: float(np.mean(d["y"] - mus[d["key"]])) for d in data}
    sq = sum(float(np.sum((d["y"] - mus[d["key"]] - gains[d["key"]]) ** 2)) for d in data)
    sig2 = sq / N_TOT
    sig = float(np.sqrt(sig2))
    ll = -0.5 * N_TOT * np.log(2 * np.pi * sig2) - 0.5 * sq / sig2
    # gradient at optimum (should be ~0 by construction): dll/dgain_d, dll/dsigma
    g_gain = [float(np.sum(d["y"] - mus[d["key"]] - gains[d["key"]]) / sig2) for d in data]
    g_sig = float(-N_TOT / sig + sq / sig ** 3)
    gnorm = float(np.sqrt(np.sum(np.square(g_gain)) + g_sig ** 2))
    return ll, gains, sig, gnorm


def penalized(mus, gains0, sig0):
    """MAP-profile variant: add priors on gains (N(0,1)) and sigma_n (HalfNormal(0.2)); L-BFGS-B."""
    keys = [d["key"] for d in data]
    y_mu = {k: d["y"] - mus[k] for k, d in zip(keys, data)}

    def negpost(x):
        gs = x[:len(keys)]
        lsig = x[-1]
        sig2 = np.exp(2 * lsig)
        sq = sum(np.sum((y_mu[k] - g) ** 2) for k, g in zip(keys, gs))
        ll = -0.5 * N_TOT * np.log(2 * np.pi * sig2) - 0.5 * sq / sig2
        lp = -0.5 * np.sum(gs ** 2) - 0.5 * np.exp(2 * lsig) / 0.2 ** 2 + lsig
        return -(ll + lp)

    x0 = np.array([gains0[k] for k in keys] + [np.log(sig0)])
    r = minimize(negpost, x0, method="L-BFGS-B", options=dict(gtol=1e-8, maxiter=200))
    return float(-r.fun), bool(r.success), int(r.nit), float(np.max(np.abs(r.jac)))


# ---- sensitivity-based choice of the two profiled parameters ----
mus1 = forward_mu0(np.ones(9))
w_all = np.concatenate([(10 ** d["y"]).ravel() ** 2 for d in data])
w_all = w_all / w_all.sum()
sens_rms = []
STEP = 0.01
for g in range(9):
    up, dn = np.ones(9), np.ones(9)
    up[g] = np.exp(STEP)
    dn[g] = np.exp(-STEP)
    mu_up, mu_dn = forward_mu0(up), forward_mu0(dn)
    dd = np.concatenate([((mu_up[d["key"]] - mu_dn[d["key"]]) / (2 * STEP)).ravel() for d in data])
    sens_rms.append(float(np.sqrt(np.sum(w_all * dd ** 2))))
order = np.argsort(sens_rms)[::-1]
chosen = [int(order[0]), int(order[1])]
print("whole-FRF sensitivity (energy-wtd RMS d log10|H|/d log theta):",
      {GNAMES[g]: round(sens_rms[g], 3) for g in range(9)})
print("chosen:", [GNAMES[g] for g in chosen])

# ---- stored separated-chain locations (retained per-chain draws) ----
zc = np.load(os.path.join(FSWS, "out", "armB", f"theta_only_{FOLD}.npz"), allow_pickle=True)
t_chains = np.asarray(zc["t_log_theta"])          # (4, 500, 9)
chain_means = np.exp(t_chains.mean(axis=1))       # (4, 9) theta scale

# ---- profiles ----
profiles = {}
for g in chosen:
    pts = []
    for th_g in GRID:
        theta = np.ones(9)
        theta[g] = th_g
        mus = forward_mu0(theta)
        ll, gains, sig, gnorm = profiled_loglik(mus)
        lp, ok, nit, jmax = penalized(mus, gains, sig)
        # prior on the swept/fixed thetas for the penalized curve
        lp += -0.5 * np.sum((np.log(theta) / 0.25) ** 2)
        pts.append({"theta": float(th_g), "profile_loglik": round(ll, 3),
                    "profile_logpost_penalized": round(lp, 3),
                    "sigma_n_hat": round(sig, 5),
                    "gains_hat": {k: round(v, 4) for k, v in gains.items()},
                    "inner_opt": {"converged": bool(ok and gnorm < 1e-4),
                                  "closed_form_grad_norm": gnorm,
                                  "lbfgs_success": ok, "lbfgs_iters": nit,
                                  "lbfgs_grad_max": jmax}})
        if not (ok and gnorm < 1e-4):
            print(f"WARN inner opt at {GNAMES[g]}={th_g:.3f}: gnorm={gnorm:.2e} lbfgs={ok}")
    lls = np.array([p["profile_loglik"] for p in pts])
    # local maxima count (interior strict maxima + boundary maxima)
    loc = [i for i in range(len(lls))
           if (i == 0 or lls[i] > lls[i - 1]) and (i == len(lls) - 1 or lls[i] > lls[i + 1])]
    profiles[GNAMES[g]] = {
        "param_index": g, "points": pts,
        "n_local_maxima": len(loc),
        "local_maxima_theta": [float(GRID[i]) for i in loc],
        "chain_means_theta": [round(float(c), 4) for c in chain_means[:, g]],
        "sensitivity_rank_value": round(sens_rms[g], 3)}

out = {
    "source_runs": [
        "shocksat_full_spectrum_frf_20260714 arm_b_nuts.py --theta-only, fold m_xpos_990x "
        "(stored NUTS: non_converged_multimodal, R-hat 44.7, ESS 2.0; per-chain draws "
        "out/armB/theta_only_m_xpos_990x.npz)"],
    "likelihood_form_documented": (
        "iid log-magnitude whole-FRF likelihood: y_{d,ch}(f)=log10|H1_meas| ~ Normal(log10|H_model("
        "theta)|+gain_d, sigma_n) over 3 train drives (m_zpos_990z, m_ypos_990y, m_zpos_900z), "
        "likelihood band 45-400 Hz thinned every 2nd bin, <=30 channels/drive (N=%d points); forward "
        "= exact eigh on the theta=1 Galerkin sub-basis (r0=118, F_SUB=450 Hz) + exponential-window "
        "operator; priors log theta ~ N(0,0.25), gain_d ~ N(0,1) dex, sigma_n ~ HalfNormal(0.2). "
        "Exact replication of the frozen make_model() theta-only branch." % N_TOT),
    "choice_rule": ("two groups with largest energy-weighted RMS of d log10|H|/d log theta_g at "
                    "theta=1 (central FD, step 0.01 in log theta), weights prop. to measured linear "
                    "|H|^2"),
    "sensitivity_all_groups": {GNAMES[g]: round(sens_rms[g], 3) for g in range(9)},
    "chosen_parameters": [GNAMES[g] for g in chosen],
    "grid": {"n": NGRID, "range_theta": [float(LO), float(HI)], "spacing": "log",
             "other_thetas": "fixed at 1.0"},
    "nuisance_profiling": "gains + sigma_n optimized at every grid point (closed-form MLE with "
                          "gradient-norm verification; penalized L-BFGS-B variant also recorded)",
    "profiles": profiles,
    "runtime_s": round(time.time() - t0, 1),
}
json.dump(out, open(os.path.join(WS, "out", "a4_profile_likelihood.json"), "w"), indent=1)
for n, p in profiles.items():
    print(f"{n}: n_local_maxima={p['n_local_maxima']} at theta={p['local_maxima_theta']}; "
          f"chains at {p['chain_means_theta']}")
print(f"A4 done {out['runtime_s']}s")
