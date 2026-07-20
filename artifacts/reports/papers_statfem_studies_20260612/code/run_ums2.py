"""Study G PRODUCTION method: unified modal statFEM with PHYSICS-BOUND shapes.

Lesson from the full-ambition run (D20): free latent mode shapes (Das/Debnath) have no data at
held-out spatial points, so they don't generalize -> held-out QOI ~1e9 wrong, R-hat 364.
Fix (the correct unification for held-out SPATIAL prediction):
  * mode SHAPES come from the parametric FEM: eigh of the reduced B x B K_tilde(theta) (cheap,
    differentiable, generalizes spatially). theta = quadrant group stiffnesses (the calibration).
  * per-mode DAMPING zeta_m stays LATENT (the Das/Debnath contribution: peaks fit, non-proportional).
  * Schneider correlated multiplicative discrepancy (smooth HMC form) absorbs residual model error.
  * statFEM trust gate = held-out QOI coverage.
Params ~22 (vs 481) -> well-conditioned. Reuses run_ums for data/config. UMS_REAL etc not used here.
Env: SMOKE2=1 tiny; UMS2_PROBE=1 -> 2-chain probe.  Outputs -> ../out/ums2_*.
"""
from __future__ import annotations
import json, math, os, time
import numpy as np
import jax, jax.numpy as jnp
from jax.scipy.linalg import solve_triangular
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS, init_to_value
from numpyro.diagnostics import summary
import ums_model as U
import run_ums as R   # module-level data + config (data gen runs once at import)

jax.config.update("jax_enable_x64", True); numpyro.set_host_device_count(4)
OUT = R.OUT
NM = 11                                            # modes <= ~64 Hz (avoid the 85 Hz degenerate pair)
B = R.B
Kt_stack = jnp.array(np.stack([np.array(k) for k in R.Kt_list]))   # [5,B,B]
KtN = [np.array(k) for k in R.Kt_list]
Phi_scan = jnp.array(R.Phi_scan); Phi_drive = jnp.array(R.Phi_drive)
PhiS = np.array(R.Phi_scan); PhiD = np.array(R.Phi_drive)
fI = jnp.array(R.F_INF); DF = R.DF
djnp = jnp.array(R.data_inf_all[:, R.oi])
OBS_LOCAL = jnp.array([R.scan.index(n) for n in R.obs_nodes])
coords_obs = R.coords_obs; coords_hold = R.coords_hold
A0N, A1N, FLOOR_EST = R.A0N, R.A1N, R.FLOOR_EST
QA_true, QB_true, QA_det, QB_det = R.QA_true, R.QB_true, R.QA_det, R.QB_det

def mvn_sep_logpdf(W, s, sigma, rho, Lz):
    e0 = W[0:1]
    rest = (W[1:] - rho[:, None] * W[:-1]) / jnp.sqrt(1 - rho ** 2)[:, None]
    Ef = jnp.concatenate([e0, rest], 0)
    E = solve_triangular(Lz, Ef.T, lower=True).T
    n = W.size; nf, npp = W.shape
    quad = jnp.sum(E * E) / sigma ** 2
    logdet = (2 * nf * 0 + 2 * n * jnp.log(sigma) + npp * jnp.sum(jnp.log(1 - rho ** 2))
              + nf * 2 * jnp.sum(jnp.log(jnp.diag(Lz))))
    return -0.5 * (n * jnp.log(2 * jnp.pi) + logdet + quad)

def model_fem(iid=False, data=None, freqs=None, obs_local=None, coords=None):
    data = djnp if data is None else data
    freqs = fI if freqs is None else freqs
    obs_local = OBS_LOCAL if obs_local is None else obs_local
    coords = coords_obs if coords is None else coords
    nf_loc = freqs.shape[0]; df_loc = freqs[1] - freqs[0]
    s_g = numpyro.sample("s_g", dist.LogNormal(0.0, 0.15).expand([4]))
    a0 = numpyro.sample("a0", dist.LogNormal(math.log(A0N), 0.4))
    a1 = numpyro.sample("a1", dist.LogNormal(math.log(A1N), 0.4))
    gz = numpyro.sample("gz", dist.LogNormal(0.0, 0.3))    # ONE global damping scale (D23: per-mode unidentifiable)
    sadd = FLOOR_EST                                        # noise floor FIXED (D23: inferring it joined the ridge)
    sw = numpyro.sample("sig_w", dist.LogNormal(math.log(0.15), 0.6))
    sth = numpyro.sample("sig_th", dist.LogNormal(math.log(0.25), 0.6))
    if not iid:
        lf = numpyro.sample("len_f", dist.LogNormal(math.log(6.0), 0.5))
        lz = numpyro.sample("len_z", dist.LogNormal(math.log(0.15), 0.5))
    Ktil = jnp.einsum("g,gij->ij", jnp.concatenate([s_g, jnp.ones(1)]), Kt_stack)
    Ctil = a0 * jnp.eye(B) + a1 * Ktil
    w2, V = jnp.linalg.eigh(Ktil)                  # ascending; M_tilde = I
    c = V[:, :NM].T                                 # [NM,B] eigenvectors (the FEM mode shapes)
    fm = jnp.sqrt(jnp.clip(w2[:NM], 1e-9, None)) / (2 * jnp.pi)
    wm = 2 * jnp.pi * fm
    zeta_ray = 0.5 * jnp.einsum("mi,ij,mj->m", c, Ctil, c) / wm
    zeta = jnp.clip(zeta_ray * gz, 2e-3, 0.2)    # global damping scale (proportional; floor 0.2%)
    lam = -zeta * wm + 1j * wm * jnp.sqrt(1 - zeta ** 2)
    psi = c @ Phi_scan.T                           # [NM,20]
    a_m = 2.0 * lam * jnp.sum(c * c, 1) + jnp.einsum("mi,ij,mj->m", c, Ctil, c)
    Hobs = U.residue_frf_jax(lam, psi[:, obs_local], c @ Phi_drive, a_m, freqs)
    scale = jnp.abs(Hobs) + sadd
    r_c = (data - Hobs) / scale
    W = jnp.real(r_c); Th = jnp.imag(r_c)
    if iid:
        rho = jnp.zeros(nf_loc - 1); Lz = jnp.eye(coords.shape[0])
    else:
        rho = jnp.exp(-df_loc / lf) * jnp.ones(nf_loc - 1)
        Lz = U.exp_chol(jnp.array(coords), lz)
    numpyro.factor("llw", mvn_sep_logpdf(W, None, sw, rho, Lz))
    numpyro.factor("llt", mvn_sep_logpdf(Th, None, sth, rho, Lz))

INIT = dict(s_g=jnp.ones(4), a0=jnp.array(A0N), a1=jnp.array(A1N), gz=jnp.array(1.0),
            sig_w=jnp.array(0.4), sig_th=jnp.array(0.4),
            len_f=jnp.array(6.0), len_z=jnp.array(0.15))

def run_nuts(iid, nw, ns, nchain, tag, **mk):
    t0 = time.time()
    init = {k: v for k, v in INIT.items() if not (iid and k in ("len_f", "len_z"))}
    mc = MCMC(NUTS(lambda: model_fem(iid, **mk), target_accept_prob=0.9, max_tree_depth=10,
                   init_strategy=init_to_value(values=init)),
              num_warmup=nw, num_samples=ns, num_chains=nchain, chain_method="sequential",
              progress_bar=False)
    mc.run(jax.random.PRNGKey(3), extra_fields=("diverging",))
    s = mc.get_samples(group_by_chain=True); div = int(jnp.sum(mc.get_extra_fields()["diverging"]))
    st = summary(s, group_by_chain=True)
    mr = max(float(np.nanmax(v["r_hat"])) for v in st.values())
    me = min(float(np.nanmin(v["n_eff"])) for v in st.values())
    flat = {k: np.array(v).reshape(-1, *v.shape[2:]) for k, v in s.items()}
    res = dict(tag=tag, max_rhat=mr, min_ess=me, divergences=div, div_frac=div / (nchain * ns),
               runtime_s=time.time() - t0, n_draws=nchain * ns)
    print(tag, {k: (round(res[k], 4) if isinstance(res[k], float) else res[k]) for k in res})
    return res, flat

def rebuild(flat, i):
    s_g = flat["s_g"][i]
    Ktil = sum(s_g[g] * KtN[g] for g in range(4)) + KtN[4]
    Ctil = flat["a0"][i] * np.eye(B) + flat["a1"][i] * Ktil
    w2, V = np.linalg.eigh(Ktil); c = V[:, :NM].T
    fm = np.sqrt(np.clip(w2[:NM], 1e-9, None)) / (2 * np.pi); wm = 2 * np.pi * fm
    zr = 0.5 * np.einsum("mi,ij,mj->m", c, Ctil, c) / wm
    zeta = np.clip(zr * flat["gz"][i], 2e-3, 0.2)
    lam = -zeta * wm + 1j * wm * np.sqrt(1 - zeta ** 2)
    a_m = 2 * lam * np.sum(c * c, 1) + np.einsum("mi,ij,mj->m", c, Ctil, c)
    return lam, c, a_m, fm, zeta

def predictive(flat, iid, S, rng):
    idx = rng.choice(flat["s_g"].shape[0], size=min(S, flat["s_g"].shape[0]), replace=False)
    nf = len(R.F_INF); bm = (R.F_INF >= R.BAND[0]) & (R.F_INF <= R.BAND[1])
    fg = np.arange(R.F_INF[0], R.F_INF[-1] + 1e-9, 0.5)
    obs_scan = [R.scan.index(n) for n in R.obs_nodes]; co = R.xy[obs_scan]; ch = coords_hold
    hloc = [R.scan.index(n) for n in R.hold_nodes]; sloc = R.hold_nodes.index(R.SHOWCASE)
    data_obs = R.data_inf_all[:, obs_scan]
    qoiA = np.zeros((len(idx), 5)); qoiB = np.zeros((len(idx), 5))
    show = np.zeros((len(idx), nf)); show_phys = np.zeros((len(idx), nf)); zpost = np.zeros((len(idx), NM)); fpost = np.zeros((len(idx), NM))
    for k, i in enumerate(idx):
        lam, c, a_m, fm, zeta = rebuild(flat, i); zpost[k] = zeta; fpost[k] = fm
        psi = c @ PhiS.T
        Hh = U.residue_frf_numpy(lam, psi[:, hloc], c @ PhiD, a_m, R.F_INF)
        kap = FLOOR_EST
        if iid:
            fwg = rng.normal(0, flat["sig_w"][i], (len(fg), 5)); ftg = rng.normal(0, flat["sig_th"][i], (len(fg), 5))
        else:
            Hobs = U.residue_frf_numpy(lam, psi[:, obs_scan], c @ PhiD, a_m, R.F_INF)
            r_c = (data_obs - Hobs) / (np.abs(Hobs) + kap); Wo = np.real(r_c); To = np.imag(r_c)
            lz = flat["len_z"][i]; lf = flat["len_f"][i]; sw_ = flat["sig_w"][i]; st_ = flat["sig_th"][i]
            dzo = np.sqrt(((co[:, None] - co[None]) ** 2).sum(-1)); dzoh = np.sqrt(((co[:, None] - ch[None]) ** 2).sum(-1)); dzh = np.sqrt(((ch[:, None] - ch[None]) ** 2).sum(-1))
            Rz = np.exp(-dzo / lz) + 1e-8 * np.eye(len(co)); Kz = np.linalg.solve(Rz, np.exp(-dzoh / lz)); Qz = np.exp(-dzoh / lz).T @ Kz
            # subsample obs freqs to the field grid for conditioning speed
            ofg = np.arange(R.F_INF[0], R.F_INF[-1] + 1e-9, 0.5)
            oidx = [int(np.argmin(np.abs(R.F_INF - f))) for f in ofg]
            Wo_g = Wo[oidx]; To_g = To[oidx]
            dfo = np.abs(ofg[:, None] - ofg[None]); Rf = np.exp(-dfo / lf) + 1e-8 * np.eye(len(ofg))
            Qf = np.exp(-dfo / lf) @ np.linalg.solve(Rf, np.exp(-dfo / lf))
            covK = np.kron(np.exp(-dfo / lf), np.exp(-dzh / lz)) - np.kron(Qf, Qz)
            covK = (covK + covK.T) / 2 + 1e-8 * np.eye(covK.shape[0]); Lc = np.linalg.cholesky(covK)
            meanw = (Wo_g @ Kz); meant = (To_g @ Kz)
            g1 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(len(ofg), 5)
            g2 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(len(ofg), 5)
            fwg = meanw + sw_ * g1; ftg = meant + st_ * g2; fg = ofg
        fw = np.stack([np.interp(R.F_INF, fg, fwg[:, h]) for h in range(5)], 1)
        ft = np.stack([np.interp(R.F_INF, fg, ftg[:, h]) for h in range(5)], 1)
        Hp = Hh + (np.abs(Hh) + kap) * (fw + 1j * ft)
        mag = np.abs(Hp); qoiA[k] = mag[bm].max(0); qoiB[k] = np.sqrt((mag[bm] ** 2).mean(0))
        show[k] = mag[:, sloc]; show_phys[k] = np.abs(Hh[:, sloc])
    return dict(qoiA=qoiA, qoiB=qoiB, show=show, show_phys=show_phys, zpost=zpost, fpost=fpost)

def qoi_stats(P):
    out = {}
    for nm_, arr, tru in (("A", P["qoiA"], QA_true), ("B", P["qoiB"], QB_true)):
        lo, md, hi = np.percentile(arr, [2.5, 50, 97.5], 0)
        out[nm_] = dict(lo=lo.tolist(), med=md.tolist(), hi=hi.tolist(), truth=tru.tolist(),
                        cover=[bool(l <= t <= h) for l, t, h in zip(lo, tru, hi)])
    out["n_cover"] = int(sum(out["A"]["cover"]) + sum(out["B"]["cover"]))
    return out

def main():
    if os.environ.get("SMOKE2") == "1":
        r, fl = run_nuts(False, 150, 80, 2, "smoke2")
        P = predictive(fl, False, 60, np.random.default_rng(5)); print("QOI", qoi_stats(P)["n_cover"], "/10")
        return
    nchain = 4
    ru, flu = run_nuts(False, 1000, 700, nchain, "unified_fem")
    np.savez(os.path.join(OUT, "ums2_chk.npz"), **flu)   # checkpoint (recover if save crashes)
    ri, fli = run_nuts(True, 800, 500, nchain, "iid_fem")
    rng = np.random.default_rng(7)
    Pu = predictive(flu, False, 250, rng); Pi = predictive(fli, True, 250, rng)
    qu, qi = qoi_stats(Pu), qoi_stats(Pi)
    np.savez(os.path.join(OUT, "ums2_headline.npz"),
             showU=Pu["show"], showU_phys=Pu["show_phys"], showI=Pi["show"],
             qoiA_u=Pu["qoiA"], qoiB_u=Pu["qoiB"], qoiA_i=Pi["qoiA"], qoiB_i=Pi["qoiB"],
             zeta_post=np.percentile(Pu["zpost"], [2.5, 50, 97.5], 0),
             f_post=np.percentile(Pu["fpost"], [2.5, 50, 97.5], 0),
             s_g=flu["s_g"], a0=flu["a0"], a1=flu["a1"], sig_w=flu["sig_w"],
             len_f=flu["len_f"], len_z=flu["len_z"], gz=flu["gz"], NM=NM)
    js = dict(config=dict(method="FEM-shape unified modal statFEM (production)", NM=NM, n_params_approx=22,
                          band=R.BAND, n_obs=len(R.obs_nodes), n_hold=5),
              unified=ru, iid=ri, qoi_unified=qu, qoi_iid=qi,
              qoi_truth=dict(A=QA_true.tolist(), B=QB_true.tolist()),
              qoi_deterministic=dict(A=QA_det.tolist(), B=QB_det.tolist()),
              truth=dict(f=R.f_t[:NM].tolist(), zeta=R.z_t[:NM].tolist()),
              hyper=dict(s_g=[np.percentile(flu["s_g"][:, g], [2.5, 50, 97.5]).tolist() for g in range(4)],
                         len_f=np.percentile(flu["len_f"], [2.5, 50, 97.5]).tolist(),
                         len_z=np.percentile(flu["len_z"], [2.5, 50, 97.5]).tolist(),
                         sig_w=np.percentile(flu["sig_w"], [2.5, 50, 97.5]).tolist()))
    json.dump(js, open(os.path.join(OUT, "ums2_summary.json"), "w"), indent=2)
    print(json.dumps(dict(unified=dict(rhat=ru["max_rhat"], ess=ru["min_ess"], div=ru["divergences"],
                                       qoi=f"{qu['n_cover']}/10"),
                          iid=dict(rhat=ri["max_rhat"], qoi=f"{qi['n_cover']}/10")), indent=2))
    print("saved ums2_summary.json / ums2_headline.npz")

if __name__ == "__main__":
    main()
