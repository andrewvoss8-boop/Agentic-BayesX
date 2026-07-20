"""Study K — per-mode frequency calibration on the REAL panel (refines Study J's 2/5 coverage).

Reuses run_studyj's real data + FEA basis + mobility + discrepancy machinery. A/B (both amplitude FIXED):
  K-global  = Study J (one global frequency scale sf).
  K-permode = per-mode frequency scales s_m (each pinned by its sharp peak; the Study D lesson).
Question: does per-mode frequency calibration improve REAL held-out QOI coverage, or is the limit elsewhere
(shapes / discrepancy)? Either answer is a real finding.  Outputs -> ../out/studyk_*.
"""
from __future__ import annotations
import json, math, os, time
import numpy as np
import jax, jax.numpy as jnp
import numpyro, numpyro.distributions as dist
from numpyro.infer import MCMC, NUTS, init_to_value
from numpyro.diagnostics import summary
import run_studyj as J

jax.config.update("jax_enable_x64", True); numpyro.set_host_device_count(4)
OUT = J.OUT; M = J.M; LGAMP0 = J.LGAMP0
GAMP = math.exp(LGAMP0)

def model(permode):
    if permode:
        sm = numpyro.sample("sm", dist.LogNormal(0.0, 0.04).expand([M]))   # per-mode (peaks pin)
    else:
        sf = numpyro.sample("sf", dist.LogNormal(0.0, 0.05)); sm = sf * jnp.ones(M)
    gz = numpyro.sample("gz", dist.LogNormal(0.0, 0.25))
    sw = numpyro.sample("sig_w", dist.LogNormal(math.log(0.2), 0.6))
    sth = numpyro.sample("sig_th", dist.LogNormal(math.log(0.3), 0.6))
    lf = numpyro.sample("len_f", dist.LogNormal(math.log(4.0), 0.5))
    lz = numpyro.sample("len_z", dist.LogNormal(math.log(0.3), 0.5))
    Y = J.mobility(sm, gz, GAMP, J.OBS_j, J.FBj)
    scale = jnp.abs(Y) + J.KAP
    r = (J.Yobs_j.T - Y) / scale
    rho = jnp.exp(-J.DF / lf) * jnp.ones(J.nf - 1)
    Lz = J.exp_chol(jnp.array(J.co), lz)
    numpyro.factor("lw", J.mvn_sep(jnp.real(r), sw, rho, Lz))
    numpyro.factor("lt", J.mvn_sep(jnp.imag(r), sth, rho, Lz))

def run(permode, nw, ns, nchain):
    init = dict(gz=jnp.array(1.0), sig_w=jnp.array(0.3), sig_th=jnp.array(0.3),
                len_f=jnp.array(4.0), len_z=jnp.array(0.3))
    init["sm" if permode else "sf"] = jnp.ones(M) if permode else jnp.array(1.0)
    t0 = time.time()
    mc = MCMC(NUTS(lambda: model(permode), target_accept_prob=0.92, max_tree_depth=10, step_size=1e-3,
                   init_strategy=init_to_value(values=init)),
              num_warmup=nw, num_samples=ns, num_chains=nchain, chain_method="sequential", progress_bar=False)
    mc.run(jax.random.PRNGKey(1), extra_fields=("diverging",))
    s = mc.get_samples(group_by_chain=True); div = int(jnp.sum(mc.get_extra_fields()["diverging"]))
    st = summary(s, group_by_chain=True)
    mr = max(float(np.nanmax(v["r_hat"])) for v in st.values()); me = min(float(np.nanmin(v["n_eff"])) for v in st.values())
    flat = {k: np.array(v).reshape(-1, *v.shape[2:]) for k, v in s.items()}
    res = dict(max_rhat=mr, min_ess=me, divergences=div, div_frac=div / (nchain * ns), runtime_s=time.time() - t0)
    print(("permode" if permode else "global"), {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()})
    return res, flat

def predict(flat, permode, S, rng):
    n = flat["gz"].shape[0]; idx = rng.choice(n, size=min(S, n), replace=False)
    hold_j = jnp.array(J.HOLD); obs_j = jnp.array(J.OBSP); nfb = len(J.FB)
    co = J.co; ch = J.ch; FB = J.FB; KAP = J.KAP
    qoi = np.zeros((len(idx), 5)); magpred = np.zeros((len(idx), 5, nfb))
    for k, i in enumerate(idx):
        sm = flat["sm"][i] if permode else flat["sf"][i] * np.ones(M)
        gz = flat["gz"][i]
        Yh = np.array(J.mobility(jnp.array(sm), jnp.array(gz), GAMP, hold_j, J.FBj))
        Yo = np.array(J.mobility(jnp.array(sm), jnp.array(gz), GAMP, obs_j, J.FBj))
        r = (J.YOBS[J.OBSP].T - Yo) / (np.abs(Yo) + KAP); Wo = np.real(r); To = np.imag(r)
        lz = flat["len_z"][i]; lf = flat["len_f"][i]; sw_ = flat["sig_w"][i]; st_ = flat["sig_th"][i]
        dzo = np.sqrt(((co[:, None] - co[None]) ** 2).sum(-1)); dzoh = np.sqrt(((co[:, None] - ch[None]) ** 2).sum(-1)); dzh = np.sqrt(((ch[:, None] - ch[None]) ** 2).sum(-1))
        Rz = np.exp(-dzo / lz) + 1e-8 * np.eye(len(co)); Kz = np.linalg.solve(Rz, np.exp(-dzoh / lz)); Qz = np.exp(-dzoh / lz).T @ Kz
        dfo = np.abs(FB[:, None] - FB[None]); Rf = np.exp(-dfo / lf) + 1e-8 * np.eye(nfb); Qf = np.exp(-dfo / lf) @ np.linalg.solve(Rf, np.exp(-dfo / lf))
        covK = np.kron(np.exp(-dfo / lf), np.exp(-dzh / lz)) - np.kron(Qf, Qz); covK = (covK + covK.T) / 2 + 1e-8 * np.eye(covK.shape[0]); Lc = np.linalg.cholesky(covK)
        mw = Wo @ Kz; mt = To @ Kz
        g1 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(nfb, 5); g2 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(nfb, 5)
        Yp = Yh + (np.abs(Yh) + KAP) * ((mw + sw_ * g1) + 1j * (mt + st_ * g2))
        qoi[k] = np.abs(Yp).max(0); magpred[k] = np.abs(Yp).T
    lo, md, hi = np.percentile(qoi, [2.5, 50, 97.5], 0)
    qtrue = np.abs(J.YOBS[J.HOLD]).max(1)
    cover = [bool(l <= t <= h) for l, t, h in zip(lo, qtrue, hi)]
    return dict(n_cover=int(sum(cover)), cover=cover, lo=lo.tolist(), med=md.tolist(), hi=hi.tolist(),
                truth=qtrue.tolist(), magpred=magpred)

def main():
    probe = os.environ.get("K_PROBE", "0") == "1"
    nw, ns, nchain = (500, 250, 2) if probe else (1000, 500, 4)
    rng = np.random.default_rng(5); out = {}
    for permode, tag in [(False, "K_global"), (True, "K_permode")]:
        res, flat = run(permode, nw, ns, nchain)
        P = predict(flat, permode, 250, rng); res["qoi"] = {k: P[k] for k in ("n_cover", "cover", "lo", "med", "hi", "truth")}
        if permode:
            sm = np.percentile(flat["sm"], [2.5, 50, 97.5], 0)
            res["cal_freqs"] = (sm[1] * J.fFEA).tolist()
            np.savez(os.path.join(OUT, "studyk_permode.npz"), magpred=P["magpred"], sm_post=sm,
                     fFEA=J.fFEA, FB=J.FB, YOBS=J.YOBS, HOLD=J.HOLD)
        out[tag] = res
        print(f"  {tag}: QOI {P['n_cover']}/5  cover {P['cover']}")
    json.dump(dict(arms=out, probe=probe, fea_freqs=J.fFEA.tolist(),
                   exp_peaks=[8.25,10.5,22.12,24.0,39.88,45.0,46.5,58.75],
                   note="Study K real-data A/B: global vs per-mode frequency calibration (amplitude fixed)"),
              open(os.path.join(OUT, "studyk_summary.json"), "w"), indent=2)
    print("saved studyk_summary.json")

if __name__ == "__main__":
    main()
