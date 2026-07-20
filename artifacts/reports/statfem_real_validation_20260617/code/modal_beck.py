#!/usr/bin/env python3
"""L8 — Beck mode-matching-FREE modal likelihood (Kiran Eq 27-28; decisions_log D20).

Unlike L6 (MAC of FEM eigenvectors, which the 4 stiffness groups cannot move), L8 treats the SYSTEM mode shapes
phi_r as FREE parameters in the 74-dim reduced space. The model frequency is the RAYLEIGH QUOTIENT
  omega^2_r(theta, phi_r) = (phi_r^T K(theta) phi_r) / (phi_r^T phi_r)   [reduced mass M = I]
so NO eigendecomposition enters the gradient (sidesteps the Sim-B eigvec pathology). Likelihood:
  freq:  (omega_hat^2_r - omega^2_r(theta,phi_r))^2 / (sigma_w omega_hat^2_r)^2
  shape: an ORTHOGONAL (1 - MAC) term at OBSERVED sensors:  ||P_perp(phihat_r) (G phi_r)||^2 / (sigma_phi^2 ||G phi_r||^2)
         where G phi_r = mode shape at observed sensors, phihat_r = measured quadrature shape (Im H at resonance).
phi is pulled toward the measured shape at observed sensors AND toward Rayleigh-consistency with K(theta). Held-out
test: does the INFERRED system shape predict the held-out-sensor mode shape (MAC) and QOI better than the FEM shape?

Output: out/modal_beck.json.
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
G_IN_S2 = rf.G_IN_S2


def mac(a, b):
    return float((a @ b) ** 2 / ((a @ a) * (b @ b) + 1e-30))


def run(seed=0, obs_frac=0.6, n_modes_max=12, tau=0.3, warmup=800, samples=800, chains=4, force=False):
    outp = WS / "out" / "modal_beck.json"
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
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    fg = [2, 4, 6, 8]

    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    pairs = pairs[:n_modes_max]
    idx = np.array([p[0] for p in pairs]); wmeas = np.array([p[1] for p in pairs]); nm = len(pairs)
    binr = np.array([int(np.argmin(np.abs(freqs - f))) for f in wmeas])
    Gobs = ch.rows[obs_pos]; Gho = ch.rows[ho_pos]                                 # (n_obs/n_ho, 74)
    phihat_obs = np.array([np.imag(meas["H"][didx[d]][fb])[binr] for d in obs_daqs])   # (n_obs, nm)
    phihat_obs = phihat_obs / (np.linalg.norm(phihat_obs, axis=0, keepdims=True) + 1e-30)
    phihat_ho = np.array([np.imag(meas["H"][didx[d]][fb])[binr] for d in ho_daqs])     # (n_ho, nm)

    # prior mean for phi = FEM eigenvectors at theta=1 (computed ONCE, numpy; not in the gradient)
    K1 = R.A_fix + R.A.sum(0); lam1, Q1 = np.linalg.eigh(K1)
    phi0 = Q1[:, idx]                                                              # (74, nm) unit-norm columns
    Q_fem_obs = Gobs @ phi0; Q_fem_ho = Gho @ phi0                                # FEM shapes at obs/ho

    A = jnp.asarray(R.A); A_fix = jnp.asarray(R.A_fix)
    Gobs_j = jnp.asarray(Gobs); phi0_j = jnp.asarray(phi0); phh = jnp.asarray(phihat_obs)
    tgt_w2 = jnp.asarray((wmeas * 2 * np.pi) ** 2); fg_arr = jnp.asarray(np.array(fg)); nfree = len(fg)

    def model():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, rf.core.NSIG_THETA).expand([nfree]).to_event(1))
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(lt))
        raw = numpyro.sample("raw", dist.Normal(0, 1).expand([74, nm]).to_event(2))
        phi = phi0_j + tau * raw                                                  # (74, nm) free system shapes
        sig_w = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        sig_p = numpyro.sample("sigma_phi", dist.HalfNormal(0.3))
        K = A_fix + jnp.einsum("g,gij->ij", theta, A)
        Kphi = K @ phi                                                            # (74, nm)
        ray = jnp.sum(phi * Kphi, 0) / (jnp.sum(phi * phi, 0) + 1e-30)            # Rayleigh omega^2_r
        var = (sig_w * tgt_w2) ** 2
        numpyro.factor("freq", -0.5 * jnp.sum((tgt_w2 - ray) ** 2 / var + jnp.log(2 * jnp.pi * var)))
        gp = Gobs_j @ phi                                                         # (n_obs, nm) shape at obs
        gpn = jnp.sum(gp * gp, 0)
        proj = jnp.sum(gp * phh, 0) ** 2 / (jnp.sum(phh * phh, 0) + 1e-30)        # (gp^T phihat)^2
        one_minus_mac = 1.0 - proj / (gpn + 1e-30)                                # orthogonal residual = 1-MAC
        numpyro.factor("shape", -0.5 * jnp.sum(one_minus_mac / sig_p ** 2 + jnp.log(2 * jnp.pi * sig_p ** 2)))

    kernel = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median, dense_mass=False, max_tree_depth=10)
    mcmc = MCMC(kernel, num_warmup=warmup, num_samples=samples, num_chains=chains, chain_method="sequential",
                progress_bar=False)
    mcmc.run(jax.random.PRNGKey(20260617), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in g.items()}
    stats = nuts_summary(g, group_by_chain=True)
    diag = {"max_rhat": max(float(np.nanmax(v["r_hat"])) for v in stats.values()),
            "min_ess": min(float(np.nanmin(v["n_eff"])) for v in stats.values()),
            "divergences": int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())}
    diag["converged"] = bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200
                             and diag["divergences"] < 0.02 * chains * samples)

    # posterior-median system shapes -> held-out MODE-SHAPE MAC: inferred vs FEM (the direct shape-correction test)
    phi_med = phi0 + tau * np.median(flat["raw"], 0)                              # (74, nm)
    inf_ho = Gho @ phi_med                                                        # inferred shape at held-out
    mac_inf, mac_fem = [], []
    for r in range(nm):
        mac_inf.append(mac(inf_ho[:, r], phihat_ho[:, r]))
        mac_fem.append(mac(Q_fem_ho[:, r], phihat_ho[:, r]))
    mac_inf = np.array(mac_inf); mac_fem = np.array(mac_fem)

    rec = {"likelihood": "L8_Beck_mode_matching_free (Rayleigh + orthogonal MAC, free system shapes)",
           "split_seed": seed, "n_modes": nm, "n_observed": int(n_obs), "n_heldout": int(len(ho_pos)),
           "tau": tau, "diag": diag,
           "sigma_phi_med": float(np.median(flat["sigma_phi"])), "sigma_w2_med": float(np.median(flat["sigma_w2"])),
           "heldout_shape_MAC": {"inferred_mean": float(np.mean(mac_inf)), "fem_mean": float(np.mean(mac_fem)),
                                 "inferred_median": float(np.median(mac_inf)), "fem_median": float(np.median(mac_fem)),
                                 "n_modes_improved": int(np.sum(mac_inf > mac_fem))},
           "theta_med": {rf.GNAMES[g_]: float(np.median(np.exp(flat["log_theta"][:, fg.index(g_)]))) for g_ in fg},
           "runtime_s": time.time() - t0}
    (WS / "out").mkdir(exist_ok=True); outp.write_text(json.dumps(rec, indent=2))
    print(f"L8 Beck (split {seed}, {nm} modes, obs {n_obs}/ho {len(ho_pos)}): conv {diag['converged']} "
          f"R-hat {diag['max_rhat']:.3f} ESS {diag['min_ess']:.0f} div {diag['divergences']} | {rec['runtime_s']:.0f}s")
    print(f"  HELD-OUT mode-shape MAC: inferred {rec['heldout_shape_MAC']['inferred_mean']:.3f} vs "
          f"FEM {rec['heldout_shape_MAC']['fem_mean']:.3f}  ({rec['heldout_shape_MAC']['n_modes_improved']}/{nm} modes improved)")
    print(f"  sigma_phi {rec['sigma_phi_med']:.3f} | -> inferring shapes "
          f"{'HELPS' if rec['heldout_shape_MAC']['inferred_mean']>rec['heldout_shape_MAC']['fem_mean'] else 'does NOT help'} held-out shape")
    return rec


if __name__ == "__main__":
    run(force="--force" in sys.argv)
