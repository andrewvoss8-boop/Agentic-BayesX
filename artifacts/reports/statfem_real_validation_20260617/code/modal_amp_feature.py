#!/usr/bin/env python3
"""Simulation B — amplitude/damping modal-feature likelihood (Card A, decisions_log D15).

L5 (modal_feature.py) calibrates theta from peak FREQUENCIES only and predicts held-out-sensor QOI that is
CALIBRATED but WIDE (~x2.7 amplitude error, dominated by the single-damping-ratio model-form floor that Schneider
Fig 6 also hit). Here we add the peak AMPLITUDES and infer a PER-MODE loss factor eta_r = 2*zeta_r, then predict
held-out QOI with that per-mode damping. Question: does per-mode damping SHARPEN the calibrated bands?

On-resonance amplitude of mode r at channel s (viscous/structural damping):
  |H_peak,r,s| ~= |phi_{s,r} phi_{d,r}| / eta_r * e^c       (phi = mass-normalized mode shape from Q(theta);
                                                              |.| removes the eigenvector sign ambiguity)
Likelihood = L5 eigenvalue (frequency) factor + a log-amplitude Gaussian factor over (matched modes x obs channels).
Inferred: theta (4 groups), log_eta_r (per matched mode), gain c, sigma_w2 (freq), sigma_a (log-amp). NUTS, all-var
gate. Predict held-out channel peak-|H| / band-GRMS by modal-superposition FRF with the inferred eta_r.

Output: out/modal_amp_feature.json
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
import score as SC
import modal_feature as mf

WS = Path(__file__).resolve().parent.parent
DR_MIN = 30.0
ETA_NOM = 2 * rf.ZETA_NOM          # nominal loss factor 0.02
qoi_peak = rf.core.qoi_peak
qoi_band = rf.core.qoi_band


def reconstruct_frf_logmag(R, theta, eta_modes, mode_idx, resp_rows, drive_row, freqs, c):
    """Modal-superposition |accelerance g/lbf| with PER-MODE loss factors eta_modes on the matched modes
    (other modes use ETA_NOM). numpy, for prediction/QOI. Returns log|H| (Nf, Ns)."""
    K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
    lam, Q = np.linalg.eigh(K); lam = np.clip(lam, 1e-9, None)
    eta = np.full(len(lam), ETA_NOM)
    eta[mode_idx] = eta_modes
    Us = resp_rows @ Q; Ud = drive_row @ Q
    w = 2 * np.pi * np.asarray(freqs)
    g = (1 + 1j * eta)[None, :] * lam[None, :] - (w ** 2)[:, None]
    H = -(w ** 2)[:, None] * np.einsum("sk,k,fk->fs", Us.astype(complex), Ud.astype(complex), 1.0 / g)
    return np.log(np.abs(H) / rf.G_IN_S2) + c


def run(seed=0, obs_frac=0.6, n_draws=300, warmup=1000, samples=1000, chains=4, force=False):
    outp = WS / "out" / "modal_amp_feature.json"
    if outp.exists() and not force:
        print(f"[skip] {outp.name}"); return json.loads(outp.read_text())
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]

    # measured modes from observed channels + match to FEM
    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    mode_idx = np.array([p[0] for p in pairs]); meas_w = np.array([p[1] for p in pairs])
    Rn = len(pairs)

    # measured peak log-amplitude per matched mode x observed channel: |H_meas,s| at the bin nearest f_r
    fidx = np.array([int(np.argmin(np.abs(freqs - f))) for f in meas_w])
    Hmeas_obs = np.array([np.abs(meas["H"][didx[d]][fb]) for d in obs_daqs])     # (Ns, Nf)
    logA_meas = np.log(Hmeas_obs[:, fidx] + 1e-300)                              # (Ns, Rn)
    resp_obs = ch.rows[obs_pos]; resp_ho = ch.rows[ho_pos]; drive = ch.drive_row

    fg = mf.run.__defaults__ and None
    fg = [2, 4, 6, 8]
    A = jnp.asarray(R.A); A_fix = jnp.asarray(R.A_fix)
    midx = jnp.asarray(mode_idx)
    tgt_w2 = jnp.asarray((meas_w * 2 * np.pi) ** 2)
    Ro = jnp.asarray(resp_obs); Dr = jnp.asarray(drive)
    logA = jnp.asarray(logA_meas)
    fg_arr = jnp.asarray(np.array(fg)); nfree = len(fg)
    c0 = float(np.median(logA_meas - np.log(1.0)))   # rough gain seed (not used as prior center precisely)

    def model():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, rf.core.NSIG_THETA).expand([nfree]).to_event(1))
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(lt))
        log_eta = numpyro.sample("log_eta", dist.Normal(np.log(ETA_NOM), 0.7).expand([Rn]).to_event(1))
        c = numpyro.sample("gain", dist.Normal(5.6, 1.5))
        sig_w = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        sig_a = numpyro.sample("sigma_a", dist.HalfNormal(0.7))
        K = A_fix + jnp.einsum("g,gij->ij", theta, A)
        lam, Q = jnp.linalg.eigh(K); lam = jnp.clip(lam, 1e-9, None)
        w2 = lam[midx]
        var_w = (sig_w * tgt_w2) ** 2
        numpyro.factor("freq", -0.5 * jnp.sum((tgt_w2 - w2) ** 2 / var_w + jnp.log(2 * jnp.pi * var_w)))
        phis = (Ro @ Q)[:, midx]                     # (Ns, Rn)
        phid = (Dr @ Q)[midx]                        # (Rn,)
        logA_model = jnp.log(jnp.abs(phis * phid[None, :]) + 1e-30) - log_eta[None, :] + c
        numpyro.factor("amp", -0.5 * jnp.sum((logA - logA_model) ** 2 / sig_a ** 2
                                             + jnp.log(2 * jnp.pi * sig_a ** 2)))

    kernel = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median, dense_mass=False, max_tree_depth=10)
    mcmc = MCMC(kernel, num_warmup=warmup, num_samples=samples, num_chains=chains,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(20260617), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in g.items()}
    stats = nuts_summary(g, group_by_chain=True)
    max_rhat = max(float(np.nanmax(v["r_hat"])) for v in stats.values())
    min_ess = min(float(np.nanmin(v["n_eff"])) for v in stats.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    conv = max_rhat <= 1.05 and min_ess >= 200 and div < 0.02 * chains * samples

    # held-out QOI prediction with per-mode damping
    theta_post = np.ones((flat["log_theta"].shape[0], 9)); theta_post[:, fg] = np.exp(flat["log_theta"])
    eta_post = np.exp(flat["log_eta"]); c_post = flat["gain"]
    sub = np.linspace(0, len(c_post) - 1, min(len(c_post), n_draws)).astype(int)
    tru_ho = np.log(np.array([np.abs(meas["H"][didx[ch.daq[p]]][fb]) for p in ho_pos]) + 1e-300)  # (n_ho, Nf)
    n_ho = len(ho_pos)
    peak = np.zeros((len(sub), n_ho)); band = np.zeros((len(sub), n_ho))
    for j, s in enumerate(sub):
        lm = reconstruct_frf_logmag(R, theta_post[s], eta_post[s], mode_idx, resp_ho, drive, freqs, c_post[s])
        mag = np.exp(lm)                              # (Nf, n_ho)
        for k in range(n_ho):
            peak[j, k] = qoi_peak(mag[:, k]); band[j, k] = qoi_band(mag[:, k], freqs)
    pk, bd = [], []
    for k in range(n_ho):
        pk.append(SC.score_qoi(peak[:, k], qoi_peak(np.exp(tru_ho[k]))))
        bd.append(SC.score_qoi(band[:, k], qoi_band(np.exp(tru_ho[k]), freqs)))

    def aggr(s):
        return {"interval_score_mean": float(np.mean([x["interval_score"] for x in s])),
                "crps_mean": float(np.mean([x["crps"] for x in s])),
                "logpd_mean": float(np.mean([x["logpd"] for x in s])),
                "coverage_frac": float(np.mean([x["covered"] for x in s])),
                "z_std": float(np.std([x["z"] for x in s])),
                "mean_width_db": float(np.mean([x["width_db"] for x in s]))}
    rec = {"likelihood": "B_modal_freq_plus_amplitude_permode_damping", "n_matched_modes": Rn,
           "n_observed": int(n_obs), "n_heldout": int(n_ho), "split_seed": seed,
           "diag": {"max_rhat": max_rhat, "min_ess": min_ess, "div_frac": div / (chains * samples),
                    "n_chains": chains, "draws": chains * samples}, "converged": bool(conv),
           "eta_post_median": {f"mode_{int(i)}": float(np.median(eta_post[:, j]))
                               for j, i in enumerate(mode_idx)},
           "eta_range": [float(np.percentile(np.median(eta_post, 0), 5)),
                         float(np.percentile(np.median(eta_post, 0), 95))],
           "sigma_a_med": float(np.median(flat["sigma_a"])),
           "heldout_peak": aggr(pk), "heldout_band": aggr(bd), "runtime_s": time.time() - t0}
    (WS / "out").mkdir(exist_ok=True)
    outp.write_text(json.dumps(rec, indent=2))
    print(f"B modal+amplitude: {Rn} modes, observe {n_obs} ch, hold out {n_ho}; CONVERGED={conv} "
          f"R-hat {max_rhat:.3f} ESS {min_ess:.0f} div {div}")
    print(f"  per-mode eta median range {rec['eta_range']} (nominal {ETA_NOM}); sigma_a {rec['sigma_a_med']:.2f}")
    print(f"  held-out PEAK: cover {rec['heldout_peak']['coverage_frac']:.2f} IS "
          f"{rec['heldout_peak']['interval_score_mean']:.3g} z-std {rec['heldout_peak']['z_std']:.2f} "
          f"width {rec['heldout_peak']['mean_width_db']:.1f} dB")
    print(f"  held-out BAND: cover {rec['heldout_band']['coverage_frac']:.2f} IS "
          f"{rec['heldout_band']['interval_score_mean']:.3g} width {rec['heldout_band']['mean_width_db']:.1f} dB")
    print(f"  runtime {rec['runtime_s']:.0f}s")
    return rec


if __name__ == "__main__":
    run(force="--force" in sys.argv)
