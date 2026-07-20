"""Study L — can we SHARPEN the Study-K real-data bands? (REAL panel, no new data).

Study K covers 5/5 held-out points but with WIDE bands (95% CI ~1.3-3x median). Open question: is the width
fundamental, or can per-mode residue-amplitude calibration tighten it? A/B (both build on K's per-mode freq winner):
  L_freqonly = per-mode frequency only (a_m = 1)            -> reproduce K (5/5, wide) = control.
  L_freqamp  = per-mode frequency + per-mode residue amplitude a_m ~ LogNormal(0,0.2) -> can it sharpen?
RISK (D35): a_m scales modal peak height, which global damping gz / gamp also scale -> a partial amplitude ridge
(D30 pathology, per-mode). PASS = R-hat<=1.05 AND coverage>=4/5 AND median band ratio drops. FAIL (ridge / coverage
loss) -> finding: width is the amplitude-shape limit; needs multi-reference data. Either outcome honest.
Decision = 4-chain all-variable gate ONLY (D34). Env L_PROBE=1 -> 2-chain crash test.  Outputs -> ../out/studyl_*.
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
OUT = J.OUT; M = J.M; LGAMP0 = J.LGAMP0; GAMP = math.exp(LGAMP0)


def mobility_am(sm, gz, am, pts_idx, freqs):
    """Same residue mobility as Study J/K but each mode's residue scaled by a_m (modal-participation calibration)."""
    fm = sm * J.fFEA_j; wm = 2 * jnp.pi * fm
    zeta = jnp.clip(gz * 0.01, 1e-3, 0.1)
    w = 2 * jnp.pi * freqs
    denom = wm[None, :] ** 2 - w[:, None] ** 2 + 2j * zeta * wm[None, :] * w[:, None]
    Pp = J.Phi_j[pts_idx]
    num = Pp * J.PHId_j[None, :] * am[None, :]
    Hr = jnp.einsum("fm,pm->fp", 1.0 / denom, num)
    return (1j * w)[:, None] * Hr * GAMP


def model(amp):
    sm = numpyro.sample("sm", dist.LogNormal(0.0, 0.04).expand([M]))      # per-mode freq (K winner)
    gz = numpyro.sample("gz", dist.LogNormal(0.0, 0.25))
    am = numpyro.sample("am", dist.LogNormal(0.0, 0.2).expand([M])) if amp else jnp.ones(M)
    sw = numpyro.sample("sig_w", dist.LogNormal(math.log(0.2), 0.6))
    sth = numpyro.sample("sig_th", dist.LogNormal(math.log(0.3), 0.6))
    lf = numpyro.sample("len_f", dist.LogNormal(math.log(4.0), 0.5))
    lz = numpyro.sample("len_z", dist.LogNormal(math.log(0.3), 0.5))
    Y = mobility_am(sm, gz, am, J.OBS_j, J.FBj)
    scale = jnp.abs(Y) + J.KAP
    r = (J.Yobs_j.T - Y) / scale
    rho = jnp.exp(-J.DF / lf) * jnp.ones(J.nf - 1)
    Lz = J.exp_chol(jnp.array(J.co), lz)
    numpyro.factor("lw", J.mvn_sep(jnp.real(r), sw, rho, Lz))
    numpyro.factor("lt", J.mvn_sep(jnp.imag(r), sth, rho, Lz))


def run(amp, nw, ns, nchain):
    init = dict(sm=jnp.ones(M), gz=jnp.array(1.0), sig_w=jnp.array(0.3), sig_th=jnp.array(0.3),
                len_f=jnp.array(4.0), len_z=jnp.array(0.3))
    if amp: init["am"] = jnp.ones(M)
    t0 = time.time()
    mc = MCMC(NUTS(lambda: model(amp), target_accept_prob=0.92, max_tree_depth=10, step_size=1e-3,
                   init_strategy=init_to_value(values=init)),
              num_warmup=nw, num_samples=ns, num_chains=nchain, chain_method="sequential", progress_bar=False)
    mc.run(jax.random.PRNGKey(1), extra_fields=("diverging",))
    s = mc.get_samples(group_by_chain=True); div = int(jnp.sum(mc.get_extra_fields()["diverging"]))
    st = summary(s, group_by_chain=True)
    mr = max(float(np.nanmax(v["r_hat"])) for v in st.values()); me = min(float(np.nanmin(v["n_eff"])) for v in st.values())
    flat = {k: np.array(v).reshape(-1, *v.shape[2:]) for k, v in s.items()}
    res = dict(max_rhat=mr, min_ess=me, divergences=div, div_frac=div / (nchain * ns), runtime_s=time.time() - t0)
    print(("freqamp" if amp else "freqonly"), {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res.items()})
    return res, flat


def predict(flat, amp, S, rng):
    n = flat["gz"].shape[0]; idx = rng.choice(n, size=min(S, n), replace=False)
    hold_j = jnp.array(J.HOLD); obs_j = jnp.array(J.OBSP); nfb = len(J.FB)
    co = J.co; ch = J.ch; FB = J.FB; KAP = J.KAP
    qoi = np.zeros((len(idx), 5))
    for k, i in enumerate(idx):
        sm = jnp.array(flat["sm"][i]); gz = jnp.array(flat["gz"][i])
        am = jnp.array(flat["am"][i]) if amp else jnp.ones(M)
        Yh = np.array(mobility_am(sm, gz, am, hold_j, J.FBj))
        Yo = np.array(mobility_am(sm, gz, am, obs_j, J.FBj))
        r = (J.YOBS[J.OBSP].T - Yo) / (np.abs(Yo) + KAP); Wo = np.real(r); To = np.imag(r)
        lz = flat["len_z"][i]; lf = flat["len_f"][i]; sw_ = flat["sig_w"][i]; st_ = flat["sig_th"][i]
        dzo = np.sqrt(((co[:, None] - co[None]) ** 2).sum(-1)); dzoh = np.sqrt(((co[:, None] - ch[None]) ** 2).sum(-1)); dzh = np.sqrt(((ch[:, None] - ch[None]) ** 2).sum(-1))
        Rz = np.exp(-dzo / lz) + 1e-8 * np.eye(len(co)); Kz = np.linalg.solve(Rz, np.exp(-dzoh / lz)); Qz = np.exp(-dzoh / lz).T @ Kz
        dfo = np.abs(FB[:, None] - FB[None]); Rf = np.exp(-dfo / lf) + 1e-8 * np.eye(nfb); Qf = np.exp(-dfo / lf) @ np.linalg.solve(Rf, np.exp(-dfo / lf))
        covK = np.kron(np.exp(-dfo / lf), np.exp(-dzh / lz)) - np.kron(Qf, Qz); covK = (covK + covK.T) / 2 + 1e-8 * np.eye(covK.shape[0]); Lc = np.linalg.cholesky(covK)
        mw = Wo @ Kz; mt = To @ Kz
        g1 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(nfb, 5); g2 = (Lc @ rng.standard_normal(covK.shape[0])).reshape(nfb, 5)
        Yp = Yh + (np.abs(Yh) + KAP) * ((mw + sw_ * g1) + 1j * (mt + st_ * g2))
        qoi[k] = np.abs(Yp).max(0)
    lo, md, hi = np.percentile(qoi, [2.5, 50, 97.5], 0)
    qtrue = np.abs(J.YOBS[J.HOLD]).max(1)
    cover = [bool(l <= t <= h) for l, t, h in zip(lo, qtrue, hi)]
    width = (hi / np.maximum(lo, 1e-30))                       # multiplicative 95% band width per point
    return dict(n_cover=int(sum(cover)), cover=cover, lo=lo.tolist(), med=md.tolist(), hi=hi.tolist(),
                truth=qtrue.tolist(), band_ratio=width.tolist(), median_band_ratio=float(np.median(width)))


def main():
    probe = os.environ.get("L_PROBE", "0") == "1"
    nw, ns, nchain = (400, 200, 2) if probe else (1000, 500, 4)
    rng = np.random.default_rng(5); out = {}
    for amp, tag in [(False, "L_freqonly"), (True, "L_freqamp")]:
        res, flat = run(amp, nw, ns, nchain)
        P = predict(flat, amp, 250, rng)
        res["qoi"] = {k: P[k] for k in ("n_cover", "cover", "lo", "med", "hi", "truth", "band_ratio", "median_band_ratio")}
        if amp:
            res["am_post"] = np.percentile(flat["am"], [2.5, 50, 97.5], 0).tolist()
        out[tag] = res
        print(f"  {tag}: QOI {P['n_cover']}/5  median band-ratio {P['median_band_ratio']:.2f}x  cover {P['cover']}")
    a, b = out["L_freqonly"], out["L_freqamp"]
    sharper = b["qoi"]["median_band_ratio"] < 0.85 * a["qoi"]["median_band_ratio"]
    kept = b["qoi"]["n_cover"] >= 4 and b["max_rhat"] <= 1.05
    verdict = ("freqamp SHARPENS while keeping coverage" if (sharper and kept)
               else ("freqamp does NOT converge (amplitude ridge) -> width is fundamental w/o multi-ref data"
                     if b["max_rhat"] > 1.05 else
                     "freqamp converges but does NOT sharpen materially -> width is shape/discrepancy-limited"))
    json.dump(dict(arms=out, probe=probe, verdict=verdict,
                   note="Study L real-data A/B: per-mode freq vs per-mode freq+amplitude; does it sharpen Study-K bands?"),
              open(os.path.join(OUT, "studyl_summary.json"), "w"), indent=2)
    print("VERDICT:", verdict); print("saved studyl_summary.json")


if __name__ == "__main__":
    main()
