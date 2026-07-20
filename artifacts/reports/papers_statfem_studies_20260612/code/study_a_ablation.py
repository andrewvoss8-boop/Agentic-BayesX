"""Study A ablation (D37) — isolate the CORRELATION knob behind slide 6.

Study A's V1 vs V2 changes three things at once (linear->log error space; iid->correlated; 1->4 nuisance scales).
This adds the missing controlled variant to attribute the effect, run together with V1 and V2 on IDENTICAL data/split:

  V1       = linear-additive iid          (Study A baseline)
  V2-iid   = log-multiplicative + separate sig_w/sig_th, but kernel R = IDENTITY (correlation OFF)   <-- THE ABLATION
  V2       = log-multiplicative + Schneider correlated kernel (len_f, r inferred)   (Study A headline)

Reads: if V2-iid CONVERGES, the log transform (not correlation) fixes mixing and correlation's job is the tight
interleaved BANDS (via neighbour conditioning); if V2-iid STILL FAILS, correlation is load-bearing for convergence too.
Data generation is copied VERBATIM from run_study_a.py (same seed) so the data is identical. Outputs -> ../out/.
"""
from __future__ import annotations
import json, math, os, time
import numpy as np
import jax, jax.numpy as jnp
from jax.scipy.linalg import solve_triangular
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS
from numpyro.diagnostics import summary
import forward as F

jax.config.update("jax_enable_x64", True); numpyro.set_host_device_count(4)
OUT = os.path.join(os.path.dirname(__file__), "..", "out")
RNG = np.random.default_rng(20260612)

# ---- data generation: VERBATIM from run_study_a.py (identical data) ----
M1, M2, M3 = 1.0, 0.6, 0.25
F1, F2, F3 = 110.0, 75.0, 220.0
Z1, Z2, Z3 = 0.015, 0.020, 0.030
NF = 56
FREQS = np.geomspace(30.0, 200.0, NF)
COORDS = np.array([0.0, 1.0]); NMP = COORDS.shape[0]
SIG_W_STAR, SIG_TH_STAR = 0.12, 0.10
LF_STAR, LZ_STAR, R_STAR = 18.0, 0.6, 0.8
SIG_IID, ADD_FRAC = 0.03, 0.015

def truth_k_c():
    w1, w2, w3 = 2*math.pi*F1, 2*math.pi*F2, 2*math.pi*F3
    k1 = M1*w1**2; k2 = M2*w2**2; k3 = M3*w3**2
    c1 = float(F.zeta_to_c(Z1, k1, M1)); c2 = float(F.zeta_to_c(Z2, k2, M2)); c3 = float(F.zeta_to_c(Z3, k3, M3))
    return dict(k1=k1, k2=k2, k12=k2, k23=k3, c1=c1, c2=c2, c12=c2, c23=c3)
TK = truth_k_c()
truth_accel = np.array(F.accelerance_3dof(jnp.array(FREQS), TK['k1'], TK['k2'], TK['k12'], TK['k23'],
                                          TK['c1'], TK['c2'], TK['c12'], TK['c23'], M1, M2, M3))
R_inj = np.array(F.schneider_R(jnp.array(FREQS), jnp.array(COORDS), LF_STAR, LZ_STAR, R_STAR))
n = R_inj.shape[0]; Lr = np.linalg.cholesky(R_inj + 1e-10*np.eye(n))
w_inj = SIG_W_STAR*(Lr@RNG.standard_normal(n)); th_inj = SIG_TH_STAR*(Lr@RNG.standard_normal(n))
eps = np.exp(w_inj + 1j*th_inj).reshape(NF, NMP)
data = truth_accel*eps
med = np.median(np.abs(truth_accel))
data = data + ADD_FRAC*med*(RNG.standard_normal((NF, NMP)) + 1j*RNG.standard_normal((NF, NMP)))
data = data + SIG_IID*np.abs(data)*(RNG.standard_normal((NF, NMP)) + 1j*RNG.standard_normal((NF, NMP)))/math.sqrt(2)
data_mag = np.abs(data)

w1n, w2n = 2*math.pi*F1, 2*math.pi*F2
K1N, K2N = M1*w1n**2, M2*w2n**2; K12N = K2N
PRI = dict(lk_sd=0.18, lz_sd=0.35)
fj, cj = jnp.array(FREQS), jnp.array(COORDS)

# ---- model pieces (identical to run_study_a) ----
def model_accel(k1, k2, k12, z1, z2, freqs):
    c1 = F.zeta_to_c(z1, k1, M1); c2 = F.zeta_to_c(z2, k2, M2)
    return F.accelerance_2dof(freqs, k1, k2, k12, c1, c2, c2, M1, M2)

def phys_params():
    lk1 = numpyro.sample("lk1", dist.Normal(math.log(K1N), PRI['lk_sd']))
    lk2 = numpyro.sample("lk2", dist.Normal(math.log(K2N), PRI['lk_sd']))
    lk12 = numpyro.sample("lk12", dist.Normal(math.log(K12N), PRI['lk_sd']))
    z1 = numpyro.sample("z1", dist.LogNormal(math.log(Z1), PRI['lz_sd']))
    z2 = numpyro.sample("z2", dist.LogNormal(math.log(Z2), PRI['lz_sd']))
    return jnp.exp(lk1), jnp.exp(lk2), jnp.exp(lk12), z1, z2

def mvn0_logpdf(x, L, sigma):
    nn = x.shape[0]; y = solve_triangular(L, x, lower=True)
    quad = jnp.sum(y*y)/(sigma**2); logdet = 2*jnp.sum(jnp.log(jnp.diag(L))) + 2*nn*jnp.log(sigma)
    return -0.5*(nn*jnp.log(2*jnp.pi) + logdet + quad)

def model_v1(freqs, d):                                   # linear-additive iid
    k1, k2, k12, z1, z2 = phys_params()
    sig = numpyro.sample("sig_obs", dist.LogNormal(math.log(0.05), 0.7))
    A = model_accel(k1, k2, k12, z1, z2, freqs); scale = sig*jnp.median(jnp.abs(A))
    numpyro.sample("obs_r", dist.Normal(0., scale), obs=(jnp.real(d)-jnp.real(A)).reshape(-1))
    numpyro.sample("obs_i", dist.Normal(0., scale), obs=(jnp.imag(d)-jnp.imag(A)).reshape(-1))

def model_v2iid(freqs, d):                                # THE ABLATION: log-multiplicative, separate scales, R = I
    k1, k2, k12, z1, z2 = phys_params()
    sw = numpyro.sample("sig_w", dist.LogNormal(math.log(0.1), 1.0))
    sth = numpyro.sample("sig_th", dist.LogNormal(math.log(0.1), 1.0))
    A = model_accel(k1, k2, k12, z1, z2, freqs)
    w, th = F.stack_w_theta(d, A)
    numpyro.sample("ll_w", dist.Normal(0., sw), obs=w)    # iid over freq x point
    numpyro.sample("ll_th", dist.Normal(0., sth), obs=th)

def model_v2(freqs, d, coords):                           # log-multiplicative + Schneider correlation
    k1, k2, k12, z1, z2 = phys_params()
    sw = numpyro.sample("sig_w", dist.LogNormal(math.log(0.1), 1.0))
    sth = numpyro.sample("sig_th", dist.LogNormal(math.log(0.1), 1.0))
    lf = numpyro.sample("len_f", dist.LogNormal(math.log(10.0), 0.6))
    r = numpyro.sample("r_split", dist.Uniform(0., 1.))
    A = model_accel(k1, k2, k12, z1, z2, freqs)
    w, th = F.stack_w_theta(d, A)
    R = F.schneider_R(freqs, coords, lf, 0.6, r) + 1e-8*jnp.eye(w.shape[0]); L = jnp.linalg.cholesky(R)
    numpyro.factor("ll_w", mvn0_logpdf(w, L, sw)); numpyro.factor("ll_th", mvn0_logpdf(th, L, sth))

def run_nuts(model, name, nw=900, ns=900, **kw):
    t0 = time.time()
    k = NUTS(model, target_accept_prob=0.92, init_strategy=numpyro.infer.init_to_median)
    mc = MCMC(k, num_warmup=nw, num_samples=ns, num_chains=4, chain_method="sequential", progress_bar=False)
    mc.run(jax.random.PRNGKey(0), **kw, extra_fields=("diverging",))
    s = mc.get_samples(group_by_chain=True); div = int(jnp.sum(mc.get_extra_fields()["diverging"]))
    st = summary(s, group_by_chain=True)
    mr = max(float(np.nanmax(v["r_hat"])) for v in st.values()); me = min(float(np.nanmin(v["n_eff"])) for v in st.values())
    flat = {k_: np.array(v).reshape(-1, *v.shape[2:]) for k_, v in s.items()}
    return dict(name=name, max_rhat=mr, min_ess=me, divergences=div, runtime_s=time.time()-t0), flat

def predict(flat, variant, hold_idx, train_idx, S=400):
    rng = np.random.default_rng(7)
    idx = rng.choice(flat['lk1'].shape[0], size=min(S, flat['lk1'].shape[0]), replace=False)
    mags = np.full((len(idx), NF, NMP), np.nan)
    def positions(fids): return np.concatenate([fid*NMP + np.arange(NMP) for fid in fids])
    tr_pos = positions(train_idx); ho_pos = positions(hold_idx)
    for sdx, i in enumerate(idx):
        k1 = math.exp(flat['lk1'][i]); k2 = math.exp(flat['lk2'][i]); k12 = math.exp(flat['lk12'][i])
        z1 = flat['z1'][i]; z2 = flat['z2'][i]
        A = np.array(model_accel(k1, k2, k12, z1, z2, fj))
        if variant == 'v1':
            sig = flat['sig_obs'][i]; scale = sig*np.median(np.abs(A))
            pred = A + scale*(rng.standard_normal((NF, NMP)) + 1j*rng.standard_normal((NF, NMP)))
        elif variant == 'v2iid':                          # marginal iid log-error, NO conditioning
            sw = flat['sig_w'][i]; sth = flat['sig_th'][i]
            w_h = sw*rng.standard_normal(len(ho_pos)); th_h = sth*rng.standard_normal(len(ho_pos))
            fp = A.reshape(-1).copy(); fp[ho_pos] = A.reshape(-1)[ho_pos]*np.exp(w_h + 1j*th_h); pred = fp.reshape(NF, NMP)
        else:                                             # v2: GP-condition held-out log-error on train residuals
            sw = flat['sig_w'][i]; sth = flat['sig_th'][i]; lf = flat['len_f'][i]; r = flat['r_split'][i]
            R = np.array(F.schneider_R(fj, cj, lf, 0.6, r)) + 1e-8*np.eye(NF*NMP)
            lr = (np.log(data) - np.log(A)).reshape(-1)
            w_tr = np.real(lr)[tr_pos]; th_tr = np.imag(lr)[tr_pos]
            Rtt = R[np.ix_(tr_pos, tr_pos)]; Rht = R[np.ix_(ho_pos, tr_pos)]; Rhh = R[np.ix_(ho_pos, ho_pos)]
            Kc = Rht@np.linalg.inv(Rtt); mu_w = Kc@w_tr; mu_th = Kc@th_tr
            cov = Rhh - Kc@Rht.T; cov = (cov + cov.T)/2 + 1e-9*np.eye(cov.shape[0]); Lc = np.linalg.cholesky(cov)
            w_h = mu_w + sw*(Lc@rng.standard_normal(len(ho_pos))); th_h = mu_th + sth*(Lc@rng.standard_normal(len(ho_pos)))
            fp = A.reshape(-1).copy(); fp[ho_pos] = A.reshape(-1)[ho_pos]*np.exp(w_h + 1j*th_h); pred = fp.reshape(NF, NMP)
        mags[sdx] = np.abs(pred)
    q = np.nanpercentile(mags, [2.5, 50, 97.5], axis=0); lo, hi = q[0], q[2]
    ho = np.array(sorted(hold_idx))
    inside = (data_mag >= lo) & (data_mag <= hi)
    return dict(coverage=float(np.mean(inside[ho])), band_width=float(np.mean((hi-lo)[ho])))

def main():
    all_idx = np.arange(NF); hold = all_idx[1::4]; train = np.array([i for i in all_idx if i not in set(hold)])
    runs = [("v1", "V1 linear-iid", model_v1, dict(freqs=fj[train], d=jnp.array(data[train]))),
            ("v2iid", "V2-iid log-iid (ABLATION)", model_v2iid, dict(freqs=fj[train], d=jnp.array(data[train]))),
            ("v2", "V2 log-correlated", model_v2, dict(freqs=fj[train], d=jnp.array(data[train]), coords=cj))]
    out = {}
    for tag, name, model, kw in runs:
        res, flat = run_nuts(model, name, **kw)
        res.update(predict(flat, tag, hold, train))
        out[tag] = dict(name=name, **{k: res[k] for k in ("max_rhat", "min_ess", "divergences", "coverage", "band_width", "runtime_s")})
        print(f"{name:30s} R-hat {res['max_rhat']:7.3f} | ESS {res['min_ess']:7.1f} | cover {res['coverage']*100:5.1f}% | band {res['band_width']:.3f}")
    conv = out["v2iid"]["max_rhat"] <= 1.05
    out["verdict"] = (
        ("V2-iid CONVERGES (R-hat %.3f) -> the LOG TRANSFORM fixes mixing; correlation's job is the tight interleaved "
         "BANDS via conditioning (V2 band %.2f vs V2-iid %.2f)." % (out["v2iid"]["max_rhat"], out["v2"]["band_width"], out["v2iid"]["band_width"]))
        if conv else
        ("V2-iid STILL FAILS (R-hat %.2f) -> correlation is load-bearing for CONVERGENCE too, not only for the bands." % out["v2iid"]["max_rhat"]))
    json.dump(out, open(os.path.join(OUT, "study_a_ablation.json"), "w"), indent=2)
    print("VERDICT:", out["verdict"]); print("saved out/study_a_ablation.json")

if __name__ == "__main__":
    main()
