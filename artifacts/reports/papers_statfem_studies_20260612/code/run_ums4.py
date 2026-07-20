"""Study I — UNKNOWN STOCHASTIC FORCING (vision §5.0, the likely novelty home; first experiment).

Setup: same panel twin, but the force is NOT measured. Truth responses a_p(w) = H_p(w) * F(w),
F = unknown smooth random spectrum (level x shape x phase). Twin sees responses only.

Arms:
  I-ratio : observable = TRANSMISSIBILITY a_p/a_ref (ref = drive-point response). Forcing cancels
            EXACTLY (the apparent-mass logic; calibration gains at ref cancel too). Trade: any
            COMMON-MODE model error also cancels -> absolute discrepancy at held-out points is
            unobservable (physics-only QOI intervals; documented).
  I-joint : observable = absolute responses; log|F| and phase(F) inferred as smooth curves
            (26 control points, random-walk smoothness). Three-way inference
            physics x discrepancy x forcing -- the confounding risk the vision names.
Gates: convergence + held-out structural QOI (peak |H|, a forcing-independent structure property)
+ (I-joint) forcing-spectrum recovery. Outputs -> ../out/ums4_summary.json
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
A0N, A1N = R2.A0N, R2.A1N

# ---------------- Study I grid (decimated for runtime) + unknown-force data ----------------
FI4 = R.F_INF[::2]                                            # 0.25 Hz, 201 lines
sel4 = np.isin(np.round(R.F_INF, 4), np.round(FI4, 4))
obs_scan = [R.scan.index(n) for n in R.obs_nodes]
hloc = [R.scan.index(n) for n in R.hold_nodes]
rngI = np.random.default_rng(424242)
# truth clean H at obs/hold on FI4 (from the saved clean grid)
H_clean = R.H_clean_inf[sel4]                                  # [201, 20]
# unknown smooth force: log|F| = log F0 + smooth GP; smooth phase
nfI4 = len(FI4)
dff = np.abs(FI4[:, None] - FI4[None]); Rff = np.exp(-dff / 8.0) + 1e-8 * np.eye(nfI4)
Lf = np.linalg.cholesky(Rff)
logF_true = math.log(2.0) + 0.5 * (Lf @ rngI.standard_normal(nfI4))
phF_true = 0.6 * (Lf @ rngI.standard_normal(nfI4))
F_true = np.exp(logF_true + 1j * phF_true)                     # [201]
resp_clean = H_clean * F_true[:, None]                          # responses
FLOOR_R = np.median(np.abs(resp_clean[:, obs_scan])) * 2e-3
def cnoise(shape, scale): return scale * (rngI.standard_normal(shape) + 1j * rngI.standard_normal(shape)) / math.sqrt(2)
resp = resp_clean * (1 + cnoise(resp_clean.shape, 0.02)) + cnoise(resp_clean.shape, FLOOR_R)
RESP_OBS = resp[:, obs_scan]                                    # [201, 15] what the twin sees
# transmissibility data (ref = drive-point response = obs col 0)
T_DATA = RESP_OBS[:, 1:] / RESP_OBS[:, 0:1]                     # [201, 14]
KAP_T = float(np.quantile(np.abs(T_DATA), 0.02))
KAP_R = float(np.quantile(np.abs(RESP_OBS), 0.0015))
# structural QOI truth: peak |H| at held-out points over the band (FORCING-INDEPENDENT)
bm4 = (FI4 >= R.BAND[0]) & (FI4 <= R.BAND[1])
QA_true_I = np.abs(H_clean[:, hloc])[bm4].max(0)
fj4 = jnp.array(FI4); DF4 = float(FI4[1] - FI4[0])
T_j = jnp.array(T_DATA); RESP_j = jnp.array(RESP_OBS)
OBS_LOC = jnp.array(obs_scan)
# force control points (smoothness prior)
FCTRL = np.arange(FI4[0], FI4[-1] + 1e-9, 2.0)                  # 26 control freqs
INTERP = np.zeros((nfI4, len(FCTRL)))
for i, f in enumerate(FI4):
    j = min(np.searchsorted(FCTRL, f), len(FCTRL) - 1)
    j0 = max(j - 1, 0)
    t = 0.0 if j == j0 else (f - FCTRL[j0]) / (FCTRL[j] - FCTRL[j0])
    INTERP[i, j0] = 1 - t; INTERP[i, j] = t
INTERP_j = jnp.array(INTERP)

def fem_forward(s_g, a0, a1, gz, cols):
    Ktil = jnp.einsum("g,gij->ij", jnp.concatenate([s_g, jnp.ones(1)]), Kt_stack)
    Ctil = a0 * jnp.eye(B) + a1 * Ktil
    w2, V = jnp.linalg.eigh(Ktil); c = V[:, :NM].T
    fm = jnp.sqrt(jnp.clip(w2[:NM], 1e-9, None)) / (2 * jnp.pi); wm = 2 * jnp.pi * fm
    zr = 0.5 * jnp.einsum("mi,ij,mj->m", c, Ctil, c) / wm
    zeta = jnp.clip(zr * gz, 2e-3, 0.2)
    lam = -zeta * wm + 1j * wm * jnp.sqrt(1 - zeta ** 2)
    psi = c @ Phi_scan.T
    a_m = 2.0 * lam * jnp.sum(c * c, 1) + jnp.einsum("mi,ij,mj->m", c, Ctil, c)
    return U.residue_frf_jax(lam, psi[:, cols], c @ Phi_drive, a_m, fj4)

def phys():
    s_g = numpyro.sample("s_g", dist.LogNormal(0.0, 0.15).expand([4]))
    a0 = numpyro.sample("a0", dist.LogNormal(math.log(A0N), 0.4))
    a1 = numpyro.sample("a1", dist.LogNormal(math.log(A1N), 0.4))
    gz = numpyro.sample("gz", dist.LogNormal(0.0, 0.3))
    return s_g, a0, a1, gz

def disc_hypers():
    sw = numpyro.sample("sig_w", dist.LogNormal(math.log(0.15), 0.6))
    sth = numpyro.sample("sig_th", dist.LogNormal(math.log(0.25), 0.6))
    lf = numpyro.sample("len_f", dist.LogNormal(math.log(6.0), 0.5))
    lz = numpyro.sample("len_z", dist.LogNormal(math.log(0.15), 0.5))
    return sw, sth, lf, lz

def model_ratio():
    s_g, a0, a1, gz = phys()
    sw, sth, lf, lz = disc_hypers()
    Hm = fem_forward(s_g, a0, a1, gz, OBS_LOC)                  # [201,15]
    Tm = Hm[:, 1:] / Hm[:, 0:1]
    scale = jnp.abs(Tm) + KAP_T
    r = (T_j - Tm) / scale
    rho = jnp.exp(-DF4 / lf) * jnp.ones(nfI4 - 1)
    Lz = U.exp_chol(jnp.array(R.coords_obs[1:]), lz)
    numpyro.factor("lw", R2.mvn_sep_logpdf(jnp.real(r), None, sw, rho, Lz))
    numpyro.factor("lt", R2.mvn_sep_logpdf(jnp.imag(r), None, sth, rho, Lz))

def model_joint():
    s_g, a0, a1, gz = phys()
    sw, sth, lf, lz = disc_hypers()
    lF0 = numpyro.sample("logF0", dist.Normal(0.0, 1.5))
    dlF = numpyro.sample("dlogF", dist.Normal(0.0, 0.4).expand([len(FCTRL)]))
    dph = numpyro.sample("dphF", dist.Normal(0.0, 0.5).expand([len(FCTRL)]))
    logF = lF0 + INTERP_j @ jnp.cumsum(dlF) * 0.3               # smooth random-walk magnitude
    phF = INTERP_j @ jnp.cumsum(dph) * 0.3
    F = jnp.exp(logF + 1j * phF)
    Hm = fem_forward(s_g, a0, a1, gz, OBS_LOC)
    Am = Hm * F[:, None]
    scale = jnp.abs(Am) + KAP_R
    r = (RESP_j - Am) / scale
    rho = jnp.exp(-DF4 / lf) * jnp.ones(nfI4 - 1)
    Lz = U.exp_chol(jnp.array(R.coords_obs), lz)
    numpyro.factor("lw", R2.mvn_sep_logpdf(jnp.real(r), None, sw, rho, Lz))
    numpyro.factor("lt", R2.mvn_sep_logpdf(jnp.imag(r), None, sth, rho, Lz))

INIT_I = dict(s_g=jnp.ones(4), a0=jnp.array(A0N), a1=jnp.array(A1N), gz=jnp.array(1.0),
              sig_w=jnp.array(0.4), sig_th=jnp.array(0.4), len_f=jnp.array(6.0),
              len_z=jnp.array(0.15), logF0=jnp.array(math.log(2.0)),
              dlogF=jnp.zeros(len(FCTRL)), dphF=jnp.zeros(len(FCTRL)))

def run_arm(model, tag, keys, nw, ns, nchain):
    t0 = time.time()
    init = {k: v for k, v in INIT_I.items() if k in keys}
    mc = MCMC(NUTS(model, target_accept_prob=0.9, max_tree_depth=10, step_size=5e-3,
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
               runtime_s=time.time() - t0)
    print(tag, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()})
    return res, flat

def qoi_phys(flat, S, rng):
    """Physics-only held-out structural QOI: peak |H(theta)| (forcing-independent)."""
    idx = rng.choice(flat["s_g"].shape[0], size=min(S, flat["s_g"].shape[0]), replace=False)
    qa = np.zeros((len(idx), 5))
    for k, i in enumerate(idx):
        lam, c, a_m = R2.rebuild({**flat, "gz": flat["gz"]}, i)[:3] if False else (None, None, None)
        # rebuild inline (R2.rebuild expects its own flat keys; identical here)
        s_g = flat["s_g"][i]
        Ktil = sum(s_g[g] * KtN[g] for g in range(4)) + KtN[4]
        Ctil = flat["a0"][i] * np.eye(B) + flat["a1"][i] * Ktil
        w2, V = np.linalg.eigh(Ktil); c = V[:, :NM].T
        fm = np.sqrt(np.clip(w2[:NM], 1e-9, None)) / (2 * np.pi); wm = 2 * np.pi * fm
        zr = 0.5 * np.einsum("mi,ij,mj->m", c, Ctil, c) / wm
        zeta = np.clip(zr * flat["gz"][i], 2e-3, 0.2)
        lam = -zeta * wm + 1j * wm * np.sqrt(1 - zeta ** 2)
        a_m = 2 * lam * np.sum(c * c, 1) + np.einsum("mi,ij,mj->m", c, Ctil, c)
        Hh = U.residue_frf_numpy(lam, (c @ PhiS.T)[:, hloc], c @ PhiD, a_m, FI4)
        qa[k] = np.abs(Hh)[bm4].max(0)
    lo, md, hi = np.percentile(qa, [2.5, 50, 97.5], 0)
    cover = [bool(l <= t <= h) for l, t, h in zip(lo, QA_true_I, hi)]
    return dict(lo=lo.tolist(), med=md.tolist(), hi=hi.tolist(), truth=QA_true_I.tolist(),
                cover=cover, n_cover=int(sum(cover))), qa

def main():
    probe = os.environ.get("I_PROBE", "0") == "1"
    nw, ns, nchain = (500, 250, 2) if probe else (900, 450, 4)
    rng = np.random.default_rng(9)
    out = {}
    rr, fr_ = run_arm(model_ratio, "I_ratio",
                      ("s_g", "a0", "a1", "gz", "sig_w", "sig_th", "len_f", "len_z"), nw, ns, nchain)
    qr, qa_r = qoi_phys(fr_, 200, rng)
    rr["qoi"] = qr; out["I_ratio"] = rr
    rj, fj_ = run_arm(model_joint, "I_joint", tuple(INIT_I.keys()), nw, ns, nchain)
    qj, qa_j = qoi_phys(fj_, 200, rng)
    rj["qoi"] = qj
    # forcing recovery (I-joint)
    S = min(200, fj_["logF0"].shape[0]); ii = rng.choice(fj_["logF0"].shape[0], S, replace=False)
    logF_post = np.stack([fj_["logF0"][i] + INTERP @ np.cumsum(fj_["dlogF"][i]) * 0.3 for i in ii])
    lo, md, hi = np.percentile(logF_post, [2.5, 50, 97.5], 0)
    cov_F = float(np.mean((logF_true >= lo) & (logF_true <= hi)))
    rj["forcing_logF_coverage"] = cov_F
    out["I_joint"] = rj
    np.savez(os.path.join(OUT, "ums4_arrays.npz"),
             FI4=FI4, logF_true=logF_true, logF_lo=lo, logF_med=md, logF_hi=hi,
             qa_ratio=qa_r, qa_joint=qa_j, QA_true=QA_true_I,
             gz_ratio=fr_["gz"], gz_joint=fj_["gz"])
    json.dump(dict(arms=out, probe=probe,
                   note="Study I unknown-forcing A/B: transmissibility (forcing cancels) vs joint forcing inference (three-way)"),
              open(os.path.join(OUT, "ums4_summary.json"), "w"), indent=2)
    print("I_ratio QOI %d/5 | I_joint QOI %d/5, logF coverage %.2f" %
          (qr["n_cover"], qj["n_cover"], cov_F))
    print("saved ums4_summary.json")

if __name__ == "__main__":
    main()
