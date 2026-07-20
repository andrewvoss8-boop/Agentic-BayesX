"""Study H — THE CURE: constrained-discrepancy A/B on the Study G testbed (vision §13.2).

Arms (all share the converging D23 base = run_ums2.model_fem):
  H-orth   : Plumlee-lite ORTHOGONALITY — precomputed parameter fingerprints t_j (plug-in gradients
             at init); tight Gaussian factor on the residual's projection onto each fingerprint
             -> the discrepancy cannot absorb what a parameter can explain (kills the
             "undamped + discrepancy" basin).
  H-local  : per-quadrant damping gz_g (hierarchical partial pooling) mapped to modes via
             kinetic-energy fractions -> the soft+damped patch becomes locally representable.
  H-both   : orth + local.
Gates: 4-chain convergence (is the bimodality dead?) + held-out QOI coverage.
Outputs -> ../out/ums3_summary.json, ums3_<arm>.npz
"""
from __future__ import annotations
import json, math, os, time
import numpy as np
import jax, jax.numpy as jnp
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS, init_to_value
from numpyro.diagnostics import summary
import ums_model as U
import run_ums as R
import run_ums2 as R2

jax.config.update("jax_enable_x64", True); numpyro.set_host_device_count(4)
OUT = R.OUT
NM, B = R2.NM, R2.B
Kt_stack, KtN = R2.Kt_stack, R2.KtN
Phi_scan, Phi_drive, PhiS, PhiD = R2.Phi_scan, R2.Phi_drive, R2.PhiS, R2.PhiD
fI, DF, djnp, OBS_LOCAL = R2.fI, R2.DF, R2.djnp, R2.OBS_LOCAL
coords_obs, coords_hold = R2.coords_obs, R2.coords_hold
A0N, A1N, FLOOR_EST = R2.A0N, R2.A1N, R2.FLOOR_EST
QA_true, QB_true, QA_det, QB_det = R2.QA_true, R2.QB_true, R2.QA_det, R2.QB_det
Phi_full = np.array(R.Phi)                                    # [NN, B] shapes at ALL 40 nodes
QUAD = U.quadrant_groups()                                    # node -> quadrant 0..3

# ---------------- quadrant kinetic-energy fractions of each nominal mode ----------------
def energy_fractions(c):
    """c [NM,B] -> E [NM,4]: fraction of modal kinetic energy in each quadrant."""
    psi_full = c @ Phi_full.T                                  # [NM, NN]
    e2 = psi_full ** 2
    E = np.stack([e2[:, QUAD == g].sum(1) for g in range(4)], 1)
    return E / E.sum(1, keepdims=True)

# ---------------- fingerprints (plug-in gradients at init, Plumlee-style) ----------------
def model_residual_vec(theta):
    """vec([Re;Im]) of H/(|H|+kappa) at obs points/freqs, numpy. theta=(s_g[4],a0,a1,gz)."""
    s_g, a0, a1, gz = theta[:4], theta[4], theta[5], theta[6]
    Ktil = sum(s_g[g] * KtN[g] for g in range(4)) + KtN[4]
    Ctil = a0 * np.eye(B) + a1 * Ktil
    w2, V = np.linalg.eigh(Ktil); c = V[:, :NM].T
    fm = np.sqrt(np.clip(w2[:NM], 1e-9, None)) / (2 * np.pi); wm = 2 * np.pi * fm
    zr = 0.5 * np.einsum("mi,ij,mj->m", c, Ctil, c) / wm
    zeta = np.clip(zr * gz, 2e-3, 0.2)
    lam = -zeta * wm + 1j * wm * np.sqrt(1 - zeta ** 2)
    a_m = 2 * lam * np.sum(c * c, 1) + np.einsum("mi,ij,mj->m", c, Ctil, c)
    psi = c @ PhiS.T
    Hm = U.residue_frf_numpy(lam, psi[:, [R.scan.index(n) for n in R.obs_nodes]], c @ PhiD, a_m, R.F_INF)
    q = Hm / (np.abs(Hm) + FLOOR_EST)
    return np.concatenate([np.real(q).ravel(), np.imag(q).ravel()])

def build_fingerprints():
    th0 = np.array([1, 1, 1, 1, A0N, A1N, 1.0])
    base = model_residual_vec(th0)
    cols = []
    for j in range(7):
        th = th0.copy(); th[j] *= 1.02                          # 2% log-step
        cols.append((model_residual_vec(th) - base) / 0.0198)   # d/dlog theta
    T = np.stack(cols, 1)                                       # [2n, 7]
    Q, _ = np.linalg.qr(T)                                      # orthonormal fingerprint basis
    return jnp.array(Q)

T_ORTH = build_fingerprints()
SIG_ORTH = 0.02     # tight: fingerprint-aligned residual must be sensor-noise small (documented)

def model_h(orth=False, local=False):
    s_g = numpyro.sample("s_g", dist.LogNormal(0.0, 0.15).expand([4]))
    a0 = numpyro.sample("a0", dist.LogNormal(math.log(A0N), 0.4))
    a1 = numpyro.sample("a1", dist.LogNormal(math.log(A1N), 0.4))
    if local:
        gz0 = numpyro.sample("gz", dist.LogNormal(0.0, 0.3))
        eta = numpyro.sample("eta_g", dist.Normal(0.0, 1.0).expand([4]))   # non-centered
        sig_eta = numpyro.sample("sig_eta", dist.HalfNormal(0.5))
        gz_g = gz0 * jnp.exp(eta * sig_eta)                                 # per-quadrant damping
    else:
        gz = numpyro.sample("gz", dist.LogNormal(0.0, 0.3))
    sw = numpyro.sample("sig_w", dist.LogNormal(math.log(0.15), 0.6))
    sth = numpyro.sample("sig_th", dist.LogNormal(math.log(0.25), 0.6))
    lf = numpyro.sample("len_f", dist.LogNormal(math.log(6.0), 0.5))
    lz = numpyro.sample("len_z", dist.LogNormal(math.log(0.15), 0.5))
    Ktil = jnp.einsum("g,gij->ij", jnp.concatenate([s_g, jnp.ones(1)]), Kt_stack)
    Ctil = a0 * jnp.eye(B) + a1 * Ktil
    w2, V = jnp.linalg.eigh(Ktil); c = V[:, :NM].T
    fm = jnp.sqrt(jnp.clip(w2[:NM], 1e-9, None)) / (2 * jnp.pi); wm = 2 * jnp.pi * fm
    zr = 0.5 * jnp.einsum("mi,ij,mj->m", c, Ctil, c) / wm
    if local:
        psi_full = c @ jnp.array(Phi_full).T
        e2 = psi_full ** 2
        E = jnp.stack([jnp.sum(e2[:, QUAD == g], 1) for g in range(4)], 1)
        E = E / jnp.sum(E, 1, keepdims=True)                                # [NM,4]
        zeta = jnp.clip(zr * (E @ gz_g), 2e-3, 0.2)
    else:
        zeta = jnp.clip(zr * gz, 2e-3, 0.2)
    lam = -zeta * wm + 1j * wm * jnp.sqrt(1 - zeta ** 2)
    psi = c @ Phi_scan.T
    a_m = 2.0 * lam * jnp.sum(c * c, 1) + jnp.einsum("mi,ij,mj->m", c, Ctil, c)
    Hobs = U.residue_frf_jax(lam, psi[:, OBS_LOCAL], c @ Phi_drive, a_m, fI)
    scale = jnp.abs(Hobs) + FLOOR_EST
    r_c = (djnp - Hobs) / scale
    W = jnp.real(r_c); Th = jnp.imag(r_c)
    rho = jnp.exp(-DF / lf) * jnp.ones(fI.shape[0] - 1)
    Lz = U.exp_chol(jnp.array(coords_obs), lz)
    numpyro.factor("llw", R2.mvn_sep_logpdf(W, None, sw, rho, Lz))
    numpyro.factor("llt", R2.mvn_sep_logpdf(Th, None, sth, rho, Lz))
    if orth:
        # Plumlee-lite: the residual's components along parameter fingerprints must be
        # sensor-noise small -> the field cannot impersonate a parameter (vision 5.2b).
        rv = jnp.concatenate([W.reshape(-1), Th.reshape(-1)])
        proj = T_ORTH.T @ rv                                                 # [7]
        numpyro.sample("orth", dist.Normal(0.0, SIG_ORTH), obs=proj / math.sqrt(rv.shape[0] // 7))

INIT_H = dict(s_g=jnp.ones(4), a0=jnp.array(A0N), a1=jnp.array(A1N), gz=jnp.array(1.0),
              eta_g=jnp.zeros(4), sig_eta=jnp.array(0.2),
              sig_w=jnp.array(0.4), sig_th=jnp.array(0.4),
              len_f=jnp.array(6.0), len_z=jnp.array(0.15))

def run_arm(orth, local, nw, ns, nchain, tag):
    t0 = time.time()
    init = {k: v for k, v in INIT_H.items() if (local or k not in ("eta_g", "sig_eta"))}
    mc = MCMC(NUTS(lambda: model_h(orth, local), target_accept_prob=0.9, max_tree_depth=10,
                   step_size=5e-3, init_strategy=init_to_value(values=init)),
              num_warmup=nw, num_samples=ns, num_chains=nchain, chain_method="sequential",
              progress_bar=False)
    mc.run(jax.random.PRNGKey(3), extra_fields=("diverging",))
    s = mc.get_samples(group_by_chain=True); div = int(jnp.sum(mc.get_extra_fields()["diverging"]))
    st = summary(s, group_by_chain=True)
    mr = max(float(np.nanmax(v["r_hat"])) for v in st.values())
    me = min(float(np.nanmin(v["n_eff"])) for v in st.values())
    flat = {k: np.array(v).reshape(-1, *v.shape[2:]) for k, v in s.items()}
    chains = {k: np.array(v) for k, v in s.items()}
    res = dict(tag=tag, max_rhat=mr, min_ess=me, divergences=div, div_frac=div / (nchain * ns),
               runtime_s=time.time() - t0)
    print(tag, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()})
    return res, flat, chains

def rebuild_h(flat, i, local):
    s_g = flat["s_g"][i]
    Ktil = sum(s_g[g] * KtN[g] for g in range(4)) + KtN[4]
    Ctil = flat["a0"][i] * np.eye(B) + flat["a1"][i] * Ktil
    w2, V = np.linalg.eigh(Ktil); c = V[:, :NM].T
    fm = np.sqrt(np.clip(w2[:NM], 1e-9, None)) / (2 * np.pi); wm = 2 * np.pi * fm
    zr = 0.5 * np.einsum("mi,ij,mj->m", c, Ctil, c) / wm
    if local:
        gz_g = flat["gz"][i] * np.exp(flat["eta_g"][i] * flat["sig_eta"][i])
        E = energy_fractions(c)
        zeta = np.clip(zr * (E @ gz_g), 2e-3, 0.2)
    else:
        zeta = np.clip(zr * flat["gz"][i], 2e-3, 0.2)
    lam = -zeta * wm + 1j * wm * np.sqrt(1 - zeta ** 2)
    a_m = 2 * lam * np.sum(c * c, 1) + np.einsum("mi,ij,mj->m", c, Ctil, c)
    return lam, c, a_m

def predictive_h(flat, local, S, rng):
    """Held-out predictive with frequency+space conditioned Schneider field (as in run_ums2)."""
    idx = rng.choice(flat["s_g"].shape[0], size=min(S, flat["s_g"].shape[0]), replace=False)
    nf = len(R.F_INF); bm = (R.F_INF >= R.BAND[0]) & (R.F_INF <= R.BAND[1])
    fg = np.arange(R.F_INF[0], R.F_INF[-1] + 1e-9, 0.5)
    obs_scan = [R.scan.index(n) for n in R.obs_nodes]; co = R.xy[obs_scan]; ch = coords_hold
    hloc = [R.scan.index(n) for n in R.hold_nodes]; sloc = R.hold_nodes.index(R.SHOWCASE)
    data_obs = R.data_inf_all[:, obs_scan]
    qoiA = np.zeros((len(idx), 5)); qoiB = np.zeros((len(idx), 5)); show = np.zeros((len(idx), nf))
    for k, i in enumerate(idx):
        lam, c, a_m = rebuild_h(flat, i, local)
        psi = c @ PhiS.T
        Hh = U.residue_frf_numpy(lam, psi[:, hloc], c @ PhiD, a_m, R.F_INF)
        Hobs = U.residue_frf_numpy(lam, psi[:, obs_scan], c @ PhiD, a_m, R.F_INF)
        r_c = (data_obs - Hobs) / (np.abs(Hobs) + FLOOR_EST)
        Wo = np.real(r_c); To = np.imag(r_c)
        lz = flat["len_z"][i]; lf = flat["len_f"][i]; sw_ = flat["sig_w"][i]; st_ = flat["sig_th"][i]
        dzo = np.sqrt(((co[:, None] - co[None]) ** 2).sum(-1)); dzoh = np.sqrt(((co[:, None] - ch[None]) ** 2).sum(-1)); dzh = np.sqrt(((ch[:, None] - ch[None]) ** 2).sum(-1))
        Rz = np.exp(-dzo / lz) + 1e-8 * np.eye(len(co)); Kz = np.linalg.solve(Rz, np.exp(-dzoh / lz)); Qz = np.exp(-dzoh / lz).T @ Kz
        ofg = np.arange(R.F_INF[0], R.F_INF[-1] + 1e-9, 0.5)
        oidx = [int(np.argmin(np.abs(R.F_INF - f))) for f in ofg]
        dfo = np.abs(ofg[:, None] - ofg[None]); Rf = np.exp(-dfo / lf) + 1e-8 * np.eye(len(ofg))
        Qf = np.exp(-dfo / lf) @ np.linalg.solve(Rf, np.exp(-dfo / lf))
        covK = np.kron(np.exp(-dfo / lf), np.exp(-dzh / lz)) - np.kron(Qf, Qz)
        covK = (covK + covK.T) / 2 + 1e-8 * np.eye(covK.shape[0]); Lc = np.linalg.cholesky(covK)
        mw = Wo[oidx] @ Kz; mt = To[oidx] @ Kz
        g1 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(len(ofg), 5)
        g2 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(len(ofg), 5)
        fw = np.stack([np.interp(R.F_INF, ofg, (mw + sw_ * g1)[:, h]) for h in range(5)], 1)
        ft = np.stack([np.interp(R.F_INF, ofg, (mt + st_ * g2)[:, h]) for h in range(5)], 1)
        Hp = Hh + (np.abs(Hh) + FLOOR_EST) * (fw + 1j * ft)
        mag = np.abs(Hp); qoiA[k] = mag[bm].max(0); qoiB[k] = np.sqrt((mag[bm] ** 2).mean(0))
        show[k] = mag[:, sloc]
    return dict(qoiA=qoiA, qoiB=qoiB, show=show)

def qoi_stats(P):
    out = {}
    for nm_, arr, tru in (("A", P["qoiA"], QA_true), ("B", P["qoiB"], QB_true)):
        lo, md, hi = np.percentile(arr, [2.5, 50, 97.5], 0)
        out[nm_] = dict(lo=lo.tolist(), med=md.tolist(), hi=hi.tolist(), truth=tru.tolist(),
                        cover=[bool(l <= t <= h) for l, t, h in zip(lo, tru, hi)])
    out["n_cover"] = int(sum(out["A"]["cover"]) + sum(out["B"]["cover"]))
    return out

def main():
    probe = os.environ.get("H_PROBE", "0") == "1"
    nw, ns, nchain = (500, 250, 2) if probe else (900, 450, 4)
    arms = [("H_orth", True, False), ("H_local", False, True), ("H_both", True, True)]
    rng = np.random.default_rng(7)
    out = {}
    for tag, orth, local in arms:
        res, flat, chains = run_arm(orth, local, nw, ns, nchain, tag)
        P = predictive_h(flat, local, 150 if probe else 250, rng)
        q = qoi_stats(P)
        res["qoi"] = q
        res["gz_per_chain"] = [float(np.median(chains["gz"][c])) for c in range(nchain)]
        out[tag] = res
        np.savez(os.path.join(OUT, f"ums3_{tag}.npz"),
                 qoiA=P["qoiA"], qoiB=P["qoiB"], show=P["show"],
                 gz=flat["gz"], s_g=flat["s_g"],
                 **({"eta_g": flat["eta_g"], "sig_eta": flat["sig_eta"]} if local else {}))
        print(f"  {tag}: QOI {q['n_cover']}/10  gz/chain {np.round(res['gz_per_chain'],2)}")
    json.dump(dict(arms=out, probe=probe,
                   qoi_truth=dict(A=QA_true.tolist(), B=QB_true.tolist()),
                   sig_orth=SIG_ORTH, note="Study H constrained-discrepancy A/B (vision 13.2)"),
              open(os.path.join(OUT, "ums3_summary.json"), "w"), indent=2)
    print("saved ums3_summary.json")

if __name__ == "__main__":
    main()
