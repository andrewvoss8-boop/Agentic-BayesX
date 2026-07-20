#!/usr/bin/env python3
"""L6 — frequency + MAC modal likelihood (Argyris/Metsovo "Bayesian bridge"; decisions_log D20).

Adds mode-SHAPE information to the converged frequency-only L5 via the Modal Assurance Criterion (MAC). Per
matched mode r, the MAC value between the FEM mode shape phi_r(theta)|obs and the MEASURED quadrature shape
phi_hat_r|obs = Im(H_obs(omega_hat_r)) (the imaginary part of the FRF at resonance ~ the mode shape for light
damping) is ONE feature per mode -> robust to redundant / closely-spaced sensors (Argyris's thesis; we have triads
98/99 & 100/101/102 at single locations). Likelihood += -0.5 * sum_r [(1-MAC_r)^2/sigma_mac^2 + log(2pi sigma_mac^2)].

Runs L5 (freq-only) AND L6 (freq+MAC) on the SAME split and scores held-out-sensor peak |H| QOI for both -> does
MAC SHARPEN the ~x2.7 amplitude bands while staying calibrated? Output: out/modal_mac.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np

import jax
import jax.numpy as jnp
jax.config.update("jax_enable_x64", True)
import numpyro
import numpyro.distributions as dist
from numpyro.diagnostics import summary as nuts_summary
from numpyro.infer import MCMC, NUTS, init_to_median

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq
import score as SC

WS = Path(__file__).resolve().parent.parent
qoi_peak = rf.core.qoi_peak
qoi_band = rf.core.qoi_band


def calibrate_mac(R, obs_modes, tgt_w2_hz, phi_meas, resp_obs, fg, seed=20260617, warmup=1000, samples=1000, chains=4):
    """NUTS on theta + sigma_w (freq, L5) + sigma_mac (MAC). phi_meas: (n_obs, n_modes) measured quadrature shapes."""
    A = jnp.asarray(R.A); A_fix = jnp.asarray(R.A_fix)
    obs_modes = jnp.asarray(np.asarray(obs_modes)); tgt_w2 = jnp.asarray((np.asarray(tgt_w2_hz) * 2 * np.pi) ** 2)
    Ro = jnp.asarray(resp_obs); Phm = jnp.asarray(phi_meas); fg_arr = jnp.asarray(np.array(fg)); nfree = len(fg)
    Phm_n = Phm / (jnp.linalg.norm(Phm, axis=0, keepdims=True) + 1e-30)        # normalize measured shapes

    def model():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, rf.core.NSIG_THETA).expand([nfree]).to_event(1))
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(lt))
        sig = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        sig_mac = numpyro.sample("sigma_mac", dist.HalfNormal(0.3))
        K = A_fix + jnp.einsum("g,gij->ij", theta, A)
        lam, Q = jnp.linalg.eigh(K); lam = jnp.clip(lam, 1e-9, None)
        w2 = lam[obs_modes]
        var = (sig * tgt_w2) ** 2
        numpyro.factor("freq", -0.5 * jnp.sum((tgt_w2 - w2) ** 2 / var + jnp.log(2 * jnp.pi * var)))
        phi_fem = (Ro @ Q)[:, obs_modes]                                      # (n_obs, n_modes)
        num = jnp.sum(phi_fem * Phm_n, axis=0) ** 2                           # (phi_fem^T phi_hat)^2
        den = jnp.sum(phi_fem ** 2, axis=0) * jnp.sum(Phm_n ** 2, axis=0) + 1e-30
        mac = num / den
        numpyro.factor("mac", -0.5 * jnp.sum((1.0 - mac) ** 2 / sig_mac ** 2 + jnp.log(2 * jnp.pi * sig_mac ** 2)))

    kernel = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median, dense_mass=True, max_tree_depth=9)
    mcmc = MCMC(kernel, num_warmup=warmup, num_samples=samples, num_chains=chains, chain_method="sequential",
                progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in g.items()}
    stats = nuts_summary(g, group_by_chain=True)
    diag = {"max_rhat": max(float(np.nanmax(v["r_hat"])) for v in stats.values()),
            "min_ess": min(float(np.nanmin(v["n_eff"])) for v in stats.values()),
            "divergences": int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())}
    diag["converged"] = bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200
                             and diag["divergences"] < 0.02 * chains * samples)
    theta_post = np.ones((flat["log_theta"].shape[0], 9)); theta_post[:, fg] = np.exp(flat["log_theta"])
    return theta_post, flat.get("sigma_mac"), diag


def predict_qoi(theta_post, R, freqs, obs_pos, ho_pos, ch, meas, didx, fb, n_draws=300, seed=0):
    """Held-out peak/band QOI (theta+gain + QOI-level marginal discrepancy from observed) -> aggregate scores."""
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T
    wq = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T.ravel()
    sub = np.linspace(0, theta_post.shape[0] - 1, min(theta_post.shape[0], n_draws)).astype(int)
    lm_obs = rf.fem_logmag_batch(R, freqs, theta_post[sub], ch.rows[obs_pos], ch.drive_row, zeta=hq.ZETA)
    lm_ho = rf.fem_logmag_batch(R, freqs, theta_post[sub], ch.rows[ho_pos], ch.drive_row, zeta=hq.ZETA)
    n_ho = len(ho_pos); peak_ob = np.zeros((len(sub), len(obs_pos))); peak_ho = np.zeros((len(sub), n_ho))
    for j in range(len(sub)):
        c = hq.wmedian((tru_obs - lm_obs[j]).ravel(), wq)
        po = np.exp(lm_obs[j] + c); ph = np.exp(lm_ho[j] + c)
        for k in range(len(obs_pos)):
            peak_ob[j, k] = qoi_peak(po[:, k])
        for k in range(n_ho):
            peak_ho[j, k] = qoi_peak(ph[:, k])
    peak_tru_ob = np.array([qoi_peak(np.exp(tru_obs[:, k])) for k in range(len(obs_pos))])
    sig = float(np.std(np.log(np.median(peak_ob, 0) + 1e-300) - np.log(peak_tru_ob + 1e-300)))
    drng = np.random.default_rng(seed + 3)
    pk = []
    for k in range(n_ho):
        ens = peak_ho[:, k] * np.exp(drng.normal(0, sig, len(sub)))
        pk.append(SC.score_qoi(ens, qoi_peak(np.exp(tru_ho[:, k]))))
    return {"coverage": float(np.mean([s["covered"] for s in pk])), "sigma_qoi": sig,
            "interval_score": float(np.mean([s["interval_score"] for s in pk])),
            "crps": float(np.mean([s["crps"] for s in pk])),
            "z_std": float(np.std([s["z"] for s in pk])),
            "mean_width_db": float(np.mean([s["width_db"] for s in pk]))}


def run(seed=0, obs_frac=0.6, warmup=1000, samples=1000, chains=4, force=False):
    outp = WS / "out" / "modal_mac.json"
    if outp.exists() and not force:
        print(f"[skip] {outp.name}"); return json.loads(outp.read_text())
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]
    fg = [2, 4, 6, 8]
    # modes + matched + measured quadrature shapes at observed channels
    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    idx = np.array([p[0] for p in pairs]); wmeas = np.array([p[1] for p in pairs])
    binr = np.array([int(np.argmin(np.abs(freqs - f))) for f in wmeas])
    phi_meas = np.array([np.imag(meas["H"][didx[d]][fb])[binr] for d in obs_daqs])   # (n_obs, n_modes)

    # L5 (freq only) and L6 (freq + MAC) on the SAME split
    th5, _, d5 = mf.calibrate_modal(R, idx, wmeas, fg=fg, warmup=warmup, samples=samples, chains=chains)
    th6, smac, d6 = calibrate_mac(R, idx, wmeas, phi_meas, ch.rows[obs_pos], fg, warmup=warmup, samples=samples, chains=chains)
    q5 = predict_qoi(th5, R, freqs, obs_pos, ho_pos, ch, meas, didx, fb, seed=seed)
    q6 = predict_qoi(th6, R, freqs, obs_pos, ho_pos, ch, meas, didx, fb, seed=seed)

    rec = {"likelihood": "L6_freq_plus_MAC (Argyris/Metsovo)", "split_seed": seed,
           "n_modes": len(pairs), "n_observed": int(n_obs), "n_heldout": int(len(ho_pos)),
           "free_groups": [rf.GNAMES[i] for i in fg],
           "L5_freq_only": {"calib": d5, "heldout_peak": q5},
           "L6_freq_plus_MAC": {"calib": d6, "sigma_mac_med": float(np.median(smac)) if smac is not None else None,
                                "heldout_peak": q6},
           "theta_med_L5": {rf.GNAMES[g_]: float(np.median(th5[:, g_])) for g_ in fg},
           "theta_med_L6": {rf.GNAMES[g_]: float(np.median(th6[:, g_])) for g_ in fg},
           "runtime_s": time.time() - t0}
    (WS / "out").mkdir(exist_ok=True); outp.write_text(json.dumps(rec, indent=2))
    print(f"L6 freq+MAC vs L5 (split {seed}, {len(pairs)} modes, obs {n_obs}/ho {len(ho_pos)}):")
    print(f"  L5 freq : conv {d5['converged']} R-hat {d5['max_rhat']:.3f} | held-out peak cover {q5['coverage']:.2f} "
          f"IS {q5['interval_score']:.0f} z-std {q5['z_std']:.2f} width {q5['mean_width_db']:.1f}dB sig {q5['sigma_qoi']:.2f}")
    print(f"  L6 +MAC : conv {d6['converged']} R-hat {d6['max_rhat']:.3f} div {d6['divergences']} | "
          f"held-out peak cover {q6['coverage']:.2f} IS {q6['interval_score']:.0f} z-std {q6['z_std']:.2f} "
          f"width {q6['mean_width_db']:.1f}dB sig {q6['sigma_qoi']:.2f}")
    print(f"  -> MAC {'SHARPER' if q6['interval_score']<q5['interval_score'] else 'NOT sharper'} "
          f"(IS {q6['interval_score']:.0f} vs {q5['interval_score']:.0f}); sigma_mac {rec['L6_freq_plus_MAC']['sigma_mac_med']}")
    print(f"  runtime {rec['runtime_s']:.0f}s")
    return rec


if __name__ == "__main__":
    run(force="--force" in sys.argv)
