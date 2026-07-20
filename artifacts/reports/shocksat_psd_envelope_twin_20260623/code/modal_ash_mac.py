#!/usr/bin/env python3
"""L10 — modal freq + MAC likelihood on the proper modal-survey (.ash) shapes with MAC-BASED matching (D20).

Corrects the two data problems found with L6/L8: (1) use the .ash EMA mode shapes (measured_modes.npz, 33 modes x
76 nodes x 3 axes) -- NOT the single-impact operating-deflection shapes (MAC~0.04, unusable); (2) pair each .ash
mode to the FEM mode of HIGHEST MAC -- NOT nearest frequency (which mis-pairs dense modes / mode crossings).

Calibrates theta two ways on the SAME MAC-matched .ash modes -- (A) frequency only, (B) frequency + MAC shape term
-- and scores held-out IMPACT-channel peak |H| QOI for both, to isolate whether the .ash shapes SHARPEN the bands.

Likelihood per matched mode r (FEM mode k_r fixed by MAC-match at theta=1):
  freq:  (omega_hat_r^2 - lambda_{k_r}(theta))^2 / (sigma_w omega_hat_r^2)^2
  MAC :  (1 - MAC( G_ash phi_{k_r}(theta), phi_hat_r ))^2 / sigma_mac^2          [shape, .ash DOFs]
Output: out/modal_ash_mac.json.
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
import modal_mac as mm                     # reuse predict_qoi

WS = Path(__file__).resolve().parent.parent
TWIN = WS.parent / "shocksat_fem_modal_twin_20260609"


def load_ash_matched(R, mac_min=0.3, n_max=20):
    """Map .ash measured modes/shapes to the reduced basis + MAC-match to FEM modes (at theta=1). Cached."""
    cache = WS / "out" / "ash_match.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        return dict(G=z["G"], meas_shape=z["meas_shape"], mfr=z["mfr"],
                    pairs=[(int(p[0]), int(p[1]), float(p[2])) for p in z["pairs"]])
    z = np.load(TWIN / "measured_modes.npz", allow_pickle=True)
    sh = np.asarray(z["shapes"], float); mfr = np.asarray(z["freqs"], float)
    nodes = np.asarray(z["nodes"]); msk = np.asarray(z["measured"])
    fm = np.load(TWIN / "fem_model.npz")                          # frugal: read only gids + xyz (no string arrays)
    gids = np.asarray(fm["gids"]); xyz_fm = np.asarray(fm["xyz"])
    gid2xyz = {int(g): xyz_fm[i] for i, g in enumerate(gids)}
    rows, mi = [], []
    for ni, g in enumerate(nodes):
        for a in range(3):
            if msk[ni, a]:
                try:
                    r, _, _ = R.reduced_row(gid2xyz[int(g)], ["X", "Y", "Z"][a]); rows.append(r); mi.append((ni, a))
                except Exception:
                    pass
    G = np.array(rows)                                                   # (n_dof, 74)
    meas_shape = np.array([[sh[r, ni, a] for (ni, a) in mi] for r in range(len(mfr))]).T   # (n_dof, 33)
    K1 = R.A_fix + R.A.sum(0); lam1, Q1 = np.linalg.eigh(K1)

    def macv(a, b):
        return (a @ b) ** 2 / ((a @ a) * (b @ b) + 1e-30)
    FemAll = G @ Q1                                                      # (n_dof, 74)
    pairs = []
    used = set()
    nfem = FemAll.shape[1]
    for r in range(len(mfr)):
        macs = np.array([macv(FemAll[:, k], meas_shape[:, r]) for k in range(nfem)])
        k = int(np.argmax(macs))
        if macs[k] >= mac_min and k not in used:
            pairs.append((r, k, float(macs[k]))); used.add(k)
    pairs = sorted(pairs, key=lambda p: mfr[p[0]])[:n_max]
    (WS / "out").mkdir(exist_ok=True)
    np.savez(cache, G=G, meas_shape=meas_shape, mfr=mfr, pairs=np.array(pairs, float))
    return dict(G=G, meas_shape=meas_shape, mfr=mfr, pairs=pairs)


def calibrate(R, ash, fg, use_mac, seed=20260617, warmup=1000, samples=1000, chains=4):
    fem_k = np.array([p[1] for p in ash["pairs"]]); ash_r = np.array([p[0] for p in ash["pairs"]])
    tgt_w2 = jnp.asarray((ash["mfr"][ash_r] * 2 * np.pi) ** 2)
    G = jnp.asarray(ash["G"]); phm = ash["meas_shape"][:, ash_r]
    phm = phm / (np.linalg.norm(phm, axis=0, keepdims=True) + 1e-30); phm = jnp.asarray(phm)
    femk = jnp.asarray(fem_k)
    A = jnp.asarray(R.A); A_fix = jnp.asarray(R.A_fix); fg_arr = jnp.asarray(np.array(fg)); nfree = len(fg)

    def model():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, rf.core.NSIG_THETA).expand([nfree]).to_event(1))
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(lt))
        sig = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        K = A_fix + jnp.einsum("g,gij->ij", theta, A)
        lam, Q = jnp.linalg.eigh(K); lam = jnp.clip(lam, 1e-9, None)
        var = (sig * tgt_w2) ** 2
        numpyro.factor("freq", -0.5 * jnp.sum((tgt_w2 - lam[femk]) ** 2 / var + jnp.log(2 * jnp.pi * var)))
        if use_mac:
            sig_mac = numpyro.sample("sigma_mac", dist.HalfNormal(0.3))
            phi_fem = G @ Q[:, femk]                                     # (n_dof, n_modes)
            mac = jnp.sum(phi_fem * phm, 0) ** 2 / (jnp.sum(phi_fem ** 2, 0) * jnp.sum(phm ** 2, 0) + 1e-30)
            numpyro.factor("mac", -0.5 * jnp.sum((1.0 - mac) ** 2 / sig_mac ** 2 + jnp.log(2 * jnp.pi * sig_mac ** 2)))

    kernel = NUTS(model, target_accept_prob=0.9, init_strategy=init_to_median, dense_mass=True, max_tree_depth=9)
    mcmc = MCMC(kernel, num_warmup=warmup, num_samples=samples, num_chains=chains, chain_method="sequential",
                progress_bar=False)
    mcmc.run(jax.random.PRNGKey(seed), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    flat = {k: np.asarray(v).reshape((-1,) + tuple(v.shape[2:])) for k, v in g.items()}
    st = nuts_summary(g, group_by_chain=True)
    diag = {"max_rhat": max(float(np.nanmax(v["r_hat"])) for v in st.values()),
            "min_ess": min(float(np.nanmin(v["n_eff"])) for v in st.values()),
            "divergences": int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())}
    diag["converged"] = bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200
                             and diag["divergences"] < 0.02 * chains * samples)
    theta_post = np.ones((flat["log_theta"].shape[0], 9)); theta_post[:, fg] = np.exp(flat["log_theta"])
    smac = float(np.median(flat["sigma_mac"])) if use_mac else None
    return theta_post, diag, smac


def run(seed=0, obs_frac=0.6, warmup=1000, samples=1000, chains=4, force=False):
    outp = WS / "out" / "modal_ash_mac.json"
    if outp.exists() and not force:
        print(f"[skip] {outp.name}"); return json.loads(outp.read_text())
    t0 = time.time(); fg = [2, 4, 6, 8]
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
    ash = load_ash_matched(R)
    macs = [round(p[2], 2) for p in ash["pairs"]]
    th_f, d_f, _ = calibrate(R, ash, fg, use_mac=False, warmup=warmup, samples=samples, chains=chains)
    th_m, d_m, smac = calibrate(R, ash, fg, use_mac=True, warmup=warmup, samples=samples, chains=chains)
    qf = mm.predict_qoi(th_f, R, freqs, obs_pos, ho_pos, ch, meas, didx, fb, seed=seed)
    qm = mm.predict_qoi(th_m, R, freqs, obs_pos, ho_pos, ch, meas, didx, fb, seed=seed)
    rec = {"likelihood": "L10_ash_freqMAC (.ash EMA shapes + MAC matching)", "split_seed": seed,
           "n_matched_ash_modes": len(ash["pairs"]), "match_MAC_values": macs,
           "match_MAC_mean": float(np.mean(macs)), "n_observed_impact": int(n_obs), "n_heldout_impact": int(len(ho_pos)),
           "ash_freq_only": {"calib": d_f, "heldout_peak": qf},
           "ash_freq_plus_MAC": {"calib": d_m, "sigma_mac_med": smac, "heldout_peak": qm},
           "theta_med_freq": {rf.GNAMES[g_]: float(np.median(th_f[:, g_])) for g_ in fg},
           "theta_med_MAC": {rf.GNAMES[g_]: float(np.median(th_m[:, g_])) for g_ in fg},
           "runtime_s": time.time() - t0}
    (WS / "out").mkdir(exist_ok=True); outp.write_text(json.dumps(rec, indent=2))
    print(f"L10 .ash + MAC-matching (split {seed}): {len(ash['pairs'])} modes matched, mean match-MAC {np.mean(macs):.2f}")
    print(f"  .ash FREQ-only: conv {d_f['converged']} R-hat {d_f['max_rhat']:.3f} | held-out peak cover {qf['coverage']:.2f} "
          f"IS {qf['interval_score']:.0f} z-std {qf['z_std']:.2f} width {qf['mean_width_db']:.1f}dB sig {qf['sigma_qoi']:.2f}")
    print(f"  .ash FREQ+MAC : conv {d_m['converged']} R-hat {d_m['max_rhat']:.3f} div {d_m['divergences']} | "
          f"held-out peak cover {qm['coverage']:.2f} IS {qm['interval_score']:.0f} z-std {qm['z_std']:.2f} "
          f"width {qm['mean_width_db']:.1f}dB sig {qm['sigma_qoi']:.2f}  (sigma_mac {smac})")
    print(f"  -> shapes {'SHARPEN' if qm['interval_score']<qf['interval_score']*0.97 else 'do NOT meaningfully sharpen'} "
          f"(IS {qm['interval_score']:.0f} vs {qf['interval_score']:.0f}); runtime {rec['runtime_s']:.0f}s")
    return rec


if __name__ == "__main__":
    run(force="--force" in sys.argv)
