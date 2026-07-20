#!/usr/bin/env python3
"""L8b — Beck mode-matching-FREE on the GOOD .ash modal-survey shapes (the one remaining lever; D20/D22).

Unlike L6/L10 (MAC in the likelihood only constrains theta, which cannot move the FEM mode shapes), here the
SYSTEM mode shapes phi_r are FREE parameters pulled toward the .ash measured shapes (orthogonal/MAC term) and toward
Rayleigh-consistency with K(theta) -- so the shape FIELD itself is corrected and can transfer to held-out locations.
No eigendecomposition in the gradient (Rayleigh quotient), so it avoids the eigvec pathology.

Held-out test isolates the SHAPE correction: reconstruct the held-out IMPACT-channel peak |H| from the SAME 12
matched modes using (a) the INFERRED phi vs (b) the FEM phi -- does inferring the shape field improve/sharpen it?
Output: out/modal_beck_ash.json.
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
G_IN_S2 = rf.G_IN_S2
qoi_peak = rf.core.qoi_peak


def reconstruct_peak(Phi, w2r, resp_rows, drive, freqs, c, zeta=hq.ZETA):
    """Peak |accelerance g/lbf| per response channel from mass-normalized modes Phi (74,nm), freqs w2r (nm,)."""
    eta = 2.0 * zeta
    Us = resp_rows @ Phi; Ud = drive @ Phi; w = 2 * np.pi * np.asarray(freqs)
    g = (1 + 1j * eta) * w2r[None, :] - (w ** 2)[:, None]
    H = -(w ** 2)[:, None] * np.einsum("sk,k,fk->fs", Us.astype(complex), Ud.astype(complex), 1.0 / g)
    mag = np.abs(H) / G_IN_S2 * np.exp(c)
    return np.array([qoi_peak(mag[:, s]) for s in range(mag.shape[1])])


def run(seed=0, obs_frac=0.6, n_modes=12, tau=0.3, warmup=800, samples=800, chains=4, n_draws=200, force=False):
    outp = WS / "out" / "modal_beck_ash.json"
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
    ash = am.load_ash_matched(R)
    pairs = ash["pairs"][:n_modes]
    fem_k = np.array([p[1] for p in pairs]); ash_r = np.array([p[0] for p in pairs]); nm = len(pairs)
    G = ash["G"]; meas_shape = ash["meas_shape"][:, ash_r]
    meas_shape = meas_shape / (np.linalg.norm(meas_shape, axis=0, keepdims=True) + 1e-30)
    tgt_w2 = (ash["mfr"][ash_r] * 2 * np.pi) ** 2
    K1 = R.A_fix + R.A.sum(0); _, Q1 = np.linalg.eigh(K1); phi0 = Q1[:, fem_k]            # (74, nm) FEM shapes

    A = jnp.asarray(R.A); A_fix = jnp.asarray(R.A_fix); Gj = jnp.asarray(G); phm = jnp.asarray(meas_shape)
    phi0j = jnp.asarray(phi0); tgt = jnp.asarray(tgt_w2); fg_arr = jnp.asarray(np.array(fg)); nfree = len(fg)

    def model():
        lt = numpyro.sample("log_theta", dist.Normal(0.0, rf.core.NSIG_THETA).expand([nfree]).to_event(1))
        theta = jnp.ones(9).at[fg_arr].set(jnp.exp(lt))
        raw = numpyro.sample("raw", dist.Normal(0, 1).expand([74, nm]).to_event(2))
        phi = phi0j + tau * raw
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

    # held-out impact-channel peak QOI: reconstruct from INFERRED phi vs FEM phi (same nm modes) -> isolate shape effect
    theta_post = np.ones((flat["log_theta"].shape[0], 9)); theta_post[:, fg] = np.exp(flat["log_theta"])
    sub = np.linspace(0, flat["raw"].shape[0] - 1, min(flat["raw"].shape[0], n_draws)).astype(int)
    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]; drive = ch.drive_row
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    tru_obs = np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs]))           # (n_obs, Nf)
    peak_tru_ho = np.array([qoi_peak(np.abs(meas["H"][didx[d]][fb])) for d in ho_daqs])
    n_ho = len(ho_pos)

    def predict(use_inferred):
        pk = np.zeros((len(sub), n_ho))
        for j, s in enumerate(sub):
            theta = theta_post[s]; K = R.A_fix + np.einsum("g,gij->ij", theta, R.A)
            phi = (phi0 + tau * flat["raw"][s]) if use_inferred else phi0
            Phi = phi / (np.linalg.norm(phi, axis=0, keepdims=True) + 1e-30)
            w2r = np.sum(phi * (K @ phi), 0) / (np.sum(phi * phi, 0) + 1e-30)
            # gain on observed (reconstruct obs peaks, match measured obs peaks in log)
            obs_pk_pred = reconstruct_peak(Phi, w2r, obs_rows, drive, freqs, 0.0)
            obs_pk_meas = np.array([qoi_peak(tru_obs[k]) for k in range(len(obs_pos))])
            c = float(np.median(np.log(obs_pk_meas + 1e-30) - np.log(obs_pk_pred + 1e-30)))
            pk[j] = reconstruct_peak(Phi, w2r, ho_rows, drive, freqs, c)
        # QOI-level discrepancy from observed residual (same machinery)
        sig = float(np.std(np.log(np.median(pk, 0) + 1e-300) - np.log(peak_tru_ho + 1e-300)))
        drng = np.random.default_rng(seed + 5); sc = []
        for k in range(n_ho):
            ens = pk[:, k] * np.exp(drng.normal(0, max(sig, 1e-3), len(sub)))
            sc.append(SC.score_qoi(ens, peak_tru_ho[k]))
        clim = np.array([qoi_peak(tru_obs[k]) for k in range(len(obs_pos))])      # climatology = observed peaks
        clim_crps = float(np.mean([SC.score_qoi(clim, peak_tru_ho[k])["crps"] for k in range(n_ho)]))
        crps = float(np.mean([x["crps"] for x in sc]))
        return {"coverage": float(np.mean([x["covered"] for x in sc])), "sigma_qoi": sig,
                "interval_score": float(np.mean([x["interval_score"] for x in sc])),
                "crps": crps, "z_std": float(np.std([x["z"] for x in sc])),
                "clim_crps": clim_crps, "crps_skill_vs_clim": float(1 - crps / clim_crps)}

    q_inf = predict(True); q_fem = predict(False)
    rec = {"likelihood": "L8b_Beck_on_ash (free system shapes + .ash MAC + Rayleigh)", "split_seed": seed,
           "n_modes": nm, "n_observed_impact": int(n_obs), "n_heldout_impact": int(n_ho),
           "match_MAC_mean": float(np.mean([p[2] for p in pairs])), "tau": tau, "diag": diag,
           "sigma_phi_med": float(np.median(flat["sigma_phi"])),
           "heldout_peak_FEM_shapes": q_fem, "heldout_peak_INFERRED_shapes": q_inf, "runtime_s": time.time() - t0}
    (WS / "out").mkdir(exist_ok=True); outp.write_text(json.dumps(rec, indent=2))
    print(f"L8b Beck-on-.ash (split {seed}, {nm} modes, MAC {rec['match_MAC_mean']:.2f}): conv {diag['converged']} "
          f"R-hat {diag['max_rhat']:.3f} ESS {diag['min_ess']:.0f} div {diag['divergences']} | {rec['runtime_s']:.0f}s")
    print(f"  held-out peak  FEM-shapes : cover {q_fem['coverage']:.2f} IS {q_fem['interval_score']:.0f} sig {q_fem['sigma_qoi']:.2f}")
    print(f"  held-out peak  INFERRED   : cover {q_inf['coverage']:.2f} IS {q_inf['interval_score']:.0f} sig {q_inf['sigma_qoi']:.2f}")
    print(f"  -> inferring the shape field {'SHARPENS' if q_inf['interval_score']<q_fem['interval_score']*0.97 else 'does NOT sharpen'} "
          f"(IS {q_inf['interval_score']:.0f} vs {q_fem['interval_score']:.0f}); sigma_phi {rec['sigma_phi_med']:.2f}")
    return rec


if __name__ == "__main__":
    run(force="--force" in sys.argv)
