#!/usr/bin/env python3
"""Phase 1 (Card C) -- HARDEN + extend the Beck-on-.ash mode-shape-field twin (L8b) onto L5's footing.

Background (decisions_log D22): L8b infers the SYSTEM mode-shape field phi_r as free parameters pulled toward the
.ash measured shapes (orthogonal/MAC term) and toward Rayleigh-consistency with K(theta) -- no eigenvector in the
gradient (avoids the Sim-B 174-divergence pathology). It SHARPENED the held-out impact-channel peak |H| vs the FEM
shapes (D22 MC: 25/25 splits). This module makes it the hardened headline by removing three gaps in the D22 run:

  (1) FULL QOI on L5's footing: score BOTH peak accelerance |H| AND band-GRMS [g/lbf], with proper scores
      (interval/Winkler, CRPS, log-density) -- D22 scored peak only.
  (2) FAIR QOI-discrepancy: estimate the predictive band-width sigma_QOI on OBSERVED channels ONLY (transferred to
      held-out), exactly like L5 (heldout_qoi.qoi_disc). The D22 mc_beck.py estimated it from HELD-OUT truth (a
      leak that let Beck peek at held-out scatter); fixing it makes the L5-vs-Beck comparison apples-to-apples.
  (3) MEASURED per-mode damping: the .ash survey carries per-mode damping (measured_modes.npz['damp'], % critical),
      previously UNUSED -- reconstruction used a single constant zeta=0.01. Here zeta_eff,r = zeta_ash,r + zeta_w(f_r)
      (zeta_w = exponential-window-added damping, realfrf.measured_zeta_w). Question: does shape-field correction +
      measured per-mode damping break the ~x3 calibrated-but-wide amplitude ceiling?
  Plus n_modes sweep (12 -> 20 MAC-matched modes): do MORE matched modes sharpen?

Honesty note (carried in the output + surfaced to lead): the Beck CALIBRATION (NUTS over theta, phi) uses ONLY the
global .ash modal survey -- it does NOT depend on the impact-FRF channel split. So one calibration is reused across
all MC splits; the MC varies the held-out channel SET and the per-config gain, NOT the calibration. The 25-split MC
is therefore a held-out-channel-generalization test of ONE global calibration, not 25 recalibrations. Labeled.

Beck mode-matching-free method: Beck, Au & Vanik (2001), Comput.-Aided Civ. Infrastruct. Eng. 16:1-11.
Output: out/modal_beck_full.json (single split, all 4 reconstruct configs) and, via mc_beck_full.py,
out/mc_beck_full_summary.json (>=25-split MC).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

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
import heldout_qoi as hq
import modal_ash_mac as am
import score as SC

WS = Path(__file__).resolve().parent.parent
TWIN = WS.parent / "shocksat_fem_modal_twin_20260609"
G_IN_S2 = rf.G_IN_S2
qoi_peak = rf.core.qoi_peak
qoi_band = rf.core.qoi_band
TAU = 0.3                       # prior std on the free shape-field perturbation phi = phi0 + tau*raw (D22 value)


# ----------------------------------------------------------------------- forward reconstruction
def reconstruct_mag(Phi, w2r, resp_rows, drive, freqs, c, eta):
    """Full |accelerance g/lbf| (Nf, Ns) from mass-normalized modes Phi (74,nm), modal freqs^2 w2r (nm,),
    per-mode loss factor eta (scalar or (nm,)). c = additive log units-gain."""
    eta = np.broadcast_to(np.asarray(eta, float), w2r.shape)
    Us = resp_rows @ Phi; Ud = drive @ Phi; w = 2 * np.pi * np.asarray(freqs)
    g = (1.0 + 1j * eta[None, :]) * w2r[None, :] - (w ** 2)[:, None]            # (Nf, nm)
    H = -(w ** 2)[:, None] * np.einsum("sk,k,fk->fs", Us.astype(complex), Ud.astype(complex), 1.0 / g)
    return np.abs(H) / G_IN_S2 * np.exp(c)                                       # (Nf, Ns)


# ----------------------------------------------------------------------- calibration (split-INDEPENDENT, cached)
def calibrate(n_modes=12, warmup=800, samples=800, chains=4, force=False, pairs_idx=None, cache_tag=None):
    """NUTS over (theta on the 4 SE-identifiable groups, free shape field phi, sigma_w2, sigma_phi) using ONLY the
    global .ash modal survey (Rayleigh freq term + orthogonal .ash-MAC shape term). Returns flat posterior draws.
    Cached because it does NOT depend on the channel split. Default mode set = the first n_modes frequency-sorted
    pairs; pairs_idx (list of indices into ash['pairs']) selects an arbitrary subset (the Phase-3 tau sweep)."""
    tag = cache_tag if cache_tag is not None else f"nm{n_modes}"
    cache = WS / "out" / f"beck_calib_{tag}.npz"
    R = rf.load_reduced()
    ash = am.load_ash_matched(R)
    pairs = [ash["pairs"][i] for i in pairs_idx] if pairs_idx is not None else ash["pairs"][:n_modes]
    fem_k = np.array([p[1] for p in pairs]); ash_r = np.array([p[0] for p in pairs]); nm = len(pairs)
    K1 = R.A_fix + R.A.sum(0); _, Q1 = np.linalg.eigh(K1); phi0 = Q1[:, fem_k]      # (74, nm) FEM shapes
    if cache.exists() and not force:
        z = np.load(cache, allow_pickle=True)
        return dict(R=R, ash=ash, pairs=pairs, fem_k=fem_k, ash_r=ash_r, nm=nm, phi0=phi0,
                    log_theta=z["log_theta"], raw=z["raw"], diag=json.loads(str(z["diag"])),
                    match_MAC=float(z["match_MAC"]))
    fg = [2, 4, 6, 8]
    G = ash["G"]; meas_shape = ash["meas_shape"][:, ash_r]
    meas_shape = meas_shape / (np.linalg.norm(meas_shape, axis=0, keepdims=True) + 1e-30)
    tgt_w2 = (ash["mfr"][ash_r] * 2 * np.pi) ** 2
    A = jnp.asarray(R.A); A_fix = jnp.asarray(R.A_fix); Gj = jnp.asarray(G); phm = jnp.asarray(meas_shape)
    phi0j = jnp.asarray(phi0); tgt = jnp.asarray(tgt_w2); fg_arr = jnp.asarray(np.array(fg)); nfree = len(fg)

    def model():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, rf.core.NSIG_THETA).expand([nfree]).to_event(1))
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(lt))
        raw = numpyro.sample("raw", dist.Normal(0, 1).expand([74, nm]).to_event(2))
        phi = phi0j + TAU * raw
        sig_w = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        sig_p = numpyro.sample("sigma_phi", dist.HalfNormal(0.3))
        K = A_fix + jnp.einsum("g,gij->ij", theta, A)
        ray = jnp.sum(phi * (K @ phi), 0) / (jnp.sum(phi * phi, 0) + 1e-30)
        var = (sig_w * tgt) ** 2
        numpyro.factor("freq", -0.5 * jnp.sum((tgt - ray) ** 2 / var + jnp.log(2 * jnp.pi * var)))
        gp = Gj @ phi
        mac = jnp.sum(gp * phm, 0) ** 2 / (jnp.sum(gp * gp, 0) * jnp.sum(phm * phm, 0) + 1e-30)
        numpyro.factor("shape", -0.5 * jnp.sum((1.0 - mac) ** 2 / sig_p ** 2 + jnp.log(2 * jnp.pi * sig_p ** 2)))

    kernel = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median, dense_mass=False, max_tree_depth=10)
    mcmc = MCMC(kernel, num_warmup=warmup, num_samples=samples, num_chains=chains, chain_method="sequential",
                progress_bar=False)
    mcmc.run(jax.random.PRNGKey(20260617), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in g.items()}
    st = nuts_summary(g, group_by_chain=True)
    diag = {"max_rhat": max(float(np.nanmax(v["r_hat"])) for v in st.values()),
            "min_ess": min(float(np.nanmin(v["n_eff"])) for v in st.values()),
            "divergences": int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())}
    diag["converged"] = bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200
                             and diag["divergences"] < 0.02 * chains * samples)
    match_MAC = float(np.mean([p[2] for p in pairs]))
    (WS / "out").mkdir(exist_ok=True)
    np.savez(cache, log_theta=flat["log_theta"], raw=flat["raw"], diag=json.dumps(diag), match_MAC=match_MAC)
    return dict(R=R, ash=ash, pairs=pairs, fem_k=fem_k, ash_r=ash_r, nm=nm, phi0=phi0,
                log_theta=flat["log_theta"], raw=flat["raw"], diag=diag, match_MAC=match_MAC)


# ----------------------------------------------------------------------- per-mode damping
def per_mode_eta(cal, meas_zeta_field):
    """Loss factor eta_r per matched mode. measured: zeta_eff,r = zeta_ash,r + zeta_w(f_ash,r); const: 0.01."""
    ash_r = cal["ash_r"]; f_ash = cal["ash"]["mfr"][ash_r]
    z = np.load(TWIN / "measured_modes.npz", allow_pickle=True)
    zeta_ash = np.asarray(z["damp"], float)[ash_r] / 100.0                       # % critical -> fraction
    zeta_w = rf.measured_zeta_w(f_ash)
    return 2.0 * (zeta_ash + zeta_w)                                             # eta = 2*zeta


# ----------------------------------------------------------------------- held-out QOI scoring for one split
def score_split(cal, seed, obs_frac=0.6, n_draws=150, eta_measured=None):
    """For one channel split, score held-out peak |H| AND band-GRMS under the 4 reconstruct configs
    {FEM,INFERRED} shapes x {const,measured} damping. QOI-discrepancy sigma estimated on OBSERVED channels only."""
    R = cal["R"]; nm = cal["nm"]; phi0 = cal["phi0"]; fem_k = cal["fem_k"]
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]; drive = ch.drive_row
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    n_o = len(obs_pos); n_ho = len(ho_pos)

    # measured truth QOI
    tru_obs = [np.abs(meas["H"][didx[d]][fb]) for d in obs_daqs]
    tru_ho = [np.abs(meas["H"][didx[d]][fb]) for d in ho_daqs]
    peak_tru_obs = np.array([qoi_peak(m) for m in tru_obs])
    band_tru_obs = np.array([qoi_band(m, freqs) for m in tru_obs])
    peak_tru_ho = np.array([qoi_peak(m) for m in tru_ho])
    band_tru_ho = np.array([qoi_band(m, freqs) for m in tru_ho])

    eta_const = 0.02                                                            # 2*zeta_nom (zeta=0.01)
    log_theta = cal["log_theta"]; raw = cal["raw"]
    sub = np.linspace(0, raw.shape[0] - 1, min(raw.shape[0], n_draws)).astype(int)
    theta_post = np.ones((log_theta.shape[0], 9)); theta_post[:, [2, 4, 6, 8]] = np.exp(log_theta)

    def predict(use_inferred, eta):
        peak_o = np.zeros((len(sub), n_o)); band_o = np.zeros((len(sub), n_o))
        peak_h = np.zeros((len(sub), n_ho)); band_h = np.zeros((len(sub), n_ho))
        for j, s in enumerate(sub):
            theta = theta_post[s]; K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
            phi = (phi0 + TAU * raw[s]) if use_inferred else phi0
            Phi = phi / (np.linalg.norm(phi, axis=0, keepdims=True) + 1e-30)
            w2r = np.sum(phi * (K @ phi), 0) / (np.sum(phi * phi, 0) + 1e-30)
            # gain c fit on OBSERVED peaks (held-out never used for the gain)
            mag_o0 = reconstruct_mag(Phi, w2r, obs_rows, drive, freqs, 0.0, eta)
            obs_pk_pred = np.array([qoi_peak(mag_o0[:, k]) for k in range(n_o)])
            c = float(np.median(np.log(peak_tru_obs + 1e-30) - np.log(obs_pk_pred + 1e-30)))
            mag_o = mag_o0 * np.exp(c); mag_h = reconstruct_mag(Phi, w2r, ho_rows, drive, freqs, c, eta)
            for k in range(n_o):
                peak_o[j, k] = qoi_peak(mag_o[:, k]); band_o[j, k] = qoi_band(mag_o[:, k], freqs)
            for k in range(n_ho):
                peak_h[j, k] = qoi_peak(mag_h[:, k]); band_h[j, k] = qoi_band(mag_h[:, k], freqs)
        # QOI-discrepancy sigma estimated on OBSERVED channels only (log-scatter of predictive median vs measured)
        sig_pk = float(np.std(np.log(np.median(peak_o, 0) + 1e-300) - np.log(peak_tru_obs + 1e-300)))
        sig_bd = float(np.std(np.log(np.median(band_o, 0) + 1e-300) - np.log(band_tru_obs + 1e-300)))
        drng = np.random.default_rng(seed + 7)
        peak_hd = peak_h * np.exp(drng.normal(0, max(sig_pk, 1e-3), peak_h.shape))
        band_hd = band_h * np.exp(drng.normal(0, max(sig_bd, 1e-3), band_h.shape))

        def agg(draws, truth):
            sc = [SC.score_qoi(draws[:, k], truth[k]) for k in range(draws.shape[1])]
            return {"coverage": float(np.mean([x["covered"] for x in sc])),
                    "interval_score": float(np.mean([x["interval_score"] for x in sc])),
                    "crps": float(np.mean([x["crps"] for x in sc])),
                    "logpd": float(np.mean([x["logpd"] for x in sc])),
                    "z_std": float(np.std([x["z"] for x in sc]))}
        return {"peak": agg(peak_hd, peak_tru_ho), "band": agg(band_hd, band_tru_ho),
                "sigma_qoi_peak": sig_pk, "sigma_qoi_band": sig_bd}

    if eta_measured is None:
        eta_measured = per_mode_eta(cal, True)
    out = {"n_observed": n_o, "n_heldout": n_ho,
           "FEM_const":      predict(False, eta_const),
           "FEM_measured":   predict(False, eta_measured),
           "INFER_const":    predict(True,  eta_const),
           "INFER_measured": predict(True,  eta_measured)}
    return out


def run(seed=0, n_modes=12, warmup=800, samples=800, chains=4, n_draws=200, force=False):
    """Single-split hardened Beck-on-.ash, all 4 configs, peak+band QOI. -> out/modal_beck_full.json"""
    outp = WS / "out" / "modal_beck_full.json"
    if outp.exists() and not force:
        print(f"[skip] {outp.name}"); return json.loads(outp.read_text())
    t0 = time.time()
    cal = calibrate(n_modes=n_modes, warmup=warmup, samples=samples, chains=chains, force=force)
    eta_meas = per_mode_eta(cal, True)
    sc = score_split(cal, seed, n_draws=n_draws, eta_measured=eta_meas)
    rec = {"likelihood": "L8b_Beck_on_ash_HARDENED (peak+band QOI, observed-only sigma, measured damping)",
           "method_ref": "Beck, Au & Vanik (2001) CACIE 16:1-11", "split_seed": seed, "n_modes": cal["nm"],
           "match_MAC_mean": cal["match_MAC"], "calib_split_independent": True,
           "eta_measured_per_mode": [float(x) for x in eta_meas], "calib_diag": cal["diag"],
           "scores": sc, "runtime_s": time.time() - t0}
    (WS / "out").mkdir(exist_ok=True); outp.write_text(json.dumps(rec, indent=2))
    print(f"L8b HARDENED (split {seed}, {cal['nm']} modes, MAC {cal['match_MAC']:.2f}): calib conv "
          f"{cal['diag']['converged']} R-hat {cal['diag']['max_rhat']:.3f}")
    for cfg in ("FEM_const", "FEM_measured", "INFER_const", "INFER_measured"):
        p = sc[cfg]["peak"]; b = sc[cfg]["band"]
        print(f"  {cfg:14s} PEAK IS {p['interval_score']:7.0f} cov {p['coverage']:.2f} | "
              f"BAND IS {b['interval_score']:8.1f} cov {b['coverage']:.2f} | sig_pk {sc[cfg]['sigma_qoi_peak']:.2f}")
    print(f"  runtime {rec['runtime_s']:.0f}s")
    return rec


if __name__ == "__main__":
    run(force="--force" in sys.argv,
        n_modes=int(sys.argv[sys.argv.index("--nmodes") + 1]) if "--nmodes" in sys.argv else 12)
