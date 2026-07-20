#!/usr/bin/env python3
"""arm_c_nuts — amplitude-TRAINED Beck-style shape inference (card §6 arm C; decisions D5).

Per LODO fold: NUTS over a shape-perturbation field for the MATCHED (survey-paired, sub-260 Hz) modes of
the wide package, theta FIXED at theta_MAP_wide (attribution isolation: the shape lever alone; deviation
from the composite run's co-inference, documented D5). Field lives in the wide theta=1 eigenbasis,
truncated to basis vectors with f <= F_FIELD Hz (labeled truncation):

  phi_i = e_{k_i} + tau * P raw_i,   raw_i ~ Normal(0,1)^{r0}, tau = 0.3 (composite convention)
  f_i   = Rayleigh(phi_i; K(theta_MAP)) / 2pi
  L = survey-freq term (sigma_w2~HN(0.15) x target)  +  survey-shape MAC term (sigma_phi~HN(0.3))
      + TRAIN amplitude term: log10|W[H]| with matched-mode residues from phi_i (all other modes fixed at
        theta_MAP), bins 45-300 Hz thinned, ONE global gain per train drive, iid sigma_n~HN(0.3).

Known failure mode (composite): confident shapes where no data checks them -> per-point gain but net-CG
coverage loss. Reported, not hidden (netcg coverage computed downstream). Resumable per fold.
"""
from __future__ import annotations
import argparse, json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                            # noqa: E402
import wscore_wide as SW                             # noqa: E402
import wide_forward as WFW                           # noqa: E402
import arm_b_nuts as AB                              # noqa: E402  (jax_windowed_logH + constants)

import jax                                            # noqa: E402
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp                               # noqa: E402
import numpyro                                        # noqa: E402
import numpyro.distributions as dist                  # noqa: E402
from numpyro.infer import MCMC, NUTS, init_to_median  # noqa: E402

OUTD = os.path.join(WS, "out", "armC")
os.makedirs(OUTD, exist_ok=True)
TAU = 0.3
F_FIELD = 400.0                                       # shape-field basis truncation (D5)
AMP_BAND = (45.0, 300.0)                              # amplitude-term bins (matched modes live sub-260)
MAC_MIN = 0.5                                         # matched modes entering the field


def matched_modes(pkg):
    pairs = np.asarray(pkg.pairs)
    sel = pairs[pairs[:, 2] >= MAC_MIN]
    ks = sel[:, 1].astype(int)
    rs = sel[:, 0].astype(int)
    return rs, ks


def build_fold_data(pkg, fold_key, thin_bins=2, n_ch_max=40):
    caches = SW.load_caches()
    train_keys = [k for k in SW.DEV_KEYS if k != fold_key]
    data = []
    for tk in train_keys:
        c = caches[tk]
        bm = (c["freqs"] >= AMP_BAND[0]) & (c["freqs"] <= AMP_BAND[1]) & c["band"]
        rows, cols = SW._usable(pkg, c, bm)
        step = max(1, int(np.ceil(len(rows) / n_ch_max)))
        rows, cols = rows[::step], cols[::step]
        bidx = np.where(bm)[0][::thin_bins]
        fc = c["freqs"][bidx]
        kb = np.round(fc * AB.NFRAME / AB.FS).astype(int)
        y = np.log10(np.abs(c["H1"][cols][:, bidx]) + 1e-300)
        data.append(dict(key=tk, rows=rows, kbins=kb, fc=fc, y=y))
    return train_keys, data


def run_fold(fold_key, n_warm=800, n_samp=600):
    tag = f"shapes_{fold_key}"
    outp = os.path.join(OUTD, tag + ".npz")
    if os.path.exists(outp):
        print(f"{tag}: exists (resume-skip)")
        return
    t0 = time.time()
    pkg = WP.load("A0_wide")
    theta = np.asarray(json.load(open(os.path.join(WS, "out", "theta_map_wide.json")))
                       ["theta_map_vec"], float)
    rs, ks = matched_modes(pkg)
    nm = len(ks)
    r = np.asarray(pkg.A).shape[1]
    freqs_el = np.asarray(pkg.freqs_el)
    r0 = int(np.sum(freqs_el <= F_FIELD))
    K_MAP = np.asarray(pkg.A_fix) + np.einsum("g,gij->ij", theta, np.asarray(pkg.A))
    lamM, QM = np.linalg.eigh(K_MAP)
    fM = np.sqrt(np.clip(lamM, 1e-9, None)) / (2 * np.pi)
    m_in = (fM >= 35.0) & (fM <= 700.0)               # amplitude-term modal support (band top 300 Hz x2.3)
    zi_all = WFW.zeta_table(fM)
    # fixed (non-matched) modal quantities at theta_MAP
    sens = np.asarray(pkg.sens_rows)
    mm = np.load(os.path.join(WP.F.REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1)
    mfreqs = np.asarray(mm["freqs"], float)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
    phm = msh[rs].T                                    # (n_live, nm)
    phm = phm / (np.linalg.norm(phm, axis=0, keepdims=True) + 1e-30)
    tgt = (mfreqs[rs] * 2 * np.pi) ** 2
    train_keys, data = build_fold_data(pkg, fold_key)
    counts = {d["key"]: {"n_ch": int(len(d["rows"])), "n_bins": int(len(d["kbins"]))} for d in data}
    print(f"{tag}: nm={nm} r0={r0} train={train_keys} counts={counts}", flush=True)

    Kj = jnp.asarray(K_MAP)
    ash = jnp.asarray(np.asarray(pkg.ash_rows)[live])  # (n_live=132, r): restrict to MEASURED dofs (MAC)
    phmj = jnp.asarray(phm)
    tgtj = jnp.asarray(tgt)
    sensj = jnp.asarray(sens)
    QMj = jnp.asarray(QM)
    ks_j = jnp.asarray(ks)
    zM = jnp.asarray(zi_all)
    fM_safe = jnp.asarray(np.where(m_in, fM, 1e6))
    m_in_j = jnp.asarray(m_in)
    drv = {d["key"]: jnp.asarray(np.asarray(pkg.drives[d["key"]])) for d in data}
    zf_s, zz_s = WFW.WF.survey_table()
    zmed = float(np.median(zz_s))
    zfj = jnp.asarray(zf_s); zzj = jnp.asarray(zz_s)

    def model():
        raw = numpyro.sample("raw", dist.Normal(0, 1).expand([r0, nm]).to_event(2))
        # phi in basis coords: unit vector at k_i + tau*field (first r0 coords)
        phi = jnp.zeros((r, nm)).at[ks_j, jnp.arange(nm)].set(1.0)
        phi = phi.at[:r0, :].add(TAU * raw)
        nrm = jnp.sqrt(jnp.sum(phi * phi, 0) + 1e-30)
        phi_n = phi / nrm
        ray = jnp.sum(phi_n * (Kj @ phi_n), 0)
        f_new = jnp.sqrt(jnp.clip(ray, 1e-6, None)) / (2 * jnp.pi)
        sig = numpyro.sample("sigma_w2", dist.HalfNormal(0.15))
        var = (sig * tgtj) ** 2
        numpyro.factor("freq", -0.5 * jnp.sum((tgtj - ray) ** 2 / var + jnp.log(2 * jnp.pi * var)))
        gp = ash @ phi_n                               # (228 live dofs, nm) -> MAC vs survey shapes
        mac = jnp.sum(gp * phmj, 0) ** 2 / (jnp.sum(gp * gp, 0) * jnp.sum(phmj * phmj, 0) + 1e-30)
        sig_p = numpyro.sample("sigma_phi", dist.HalfNormal(0.3))
        numpyro.factor("shape", -0.5 * jnp.sum((1.0 - mac) ** 2 / sig_p ** 2
                                               + jnp.log(2 * jnp.pi * sig_p ** 2)))
        # amplitude term: modes = fixed theta_MAP set with matched modes REPLACED by (phi_n, f_new)
        sigma_n = numpyro.sample("sigma_n", dist.HalfNormal(0.3))
        Us_fix = sensj @ QMj                           # (n_sens, r) fixed shapes (eigenvector coords)
        Us_phi = sensj @ phi_n                         # (n_sens, nm) inferred shapes
        f_all = fM_safe.at[ks_j].set(f_new)
        zi = jnp.where(f_all > zfj[-1], zmed, jnp.interp(f_all, zfj, zzj))
        for d in data:
            gain = numpyro.sample(f"gain_{d['key']}", dist.Normal(0.0, 1.0))
            Ud_fix = (drv[d["key"]] @ QMj) * m_in_j
            Ud_phi = drv[d["key"]] @ phi_n
            res = (Us_fix * Ud_fix[None, :]).at[:, ks_j].set(Us_phi * Ud_phi[None, :])
            mu = AB.jax_windowed_logH(res[d["rows"]], f_all, zi, jnp.asarray(d["kbins"])) + gain
            numpyro.sample(f"y_{d['key']}", dist.Normal(0.0, sigma_n)
                           .expand(d["y"].shape).to_event(2), obs=jnp.asarray(d["y"]) - mu)

    kern = NUTS(model, target_accept_prob=0.9, dense_mass=False, init_strategy=init_to_median)
    mcmc = MCMC(kern, num_warmup=n_warm, num_samples=n_samp, num_chains=4,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(20260714), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    from numpyro.diagnostics import summary as npr_summary
    summ = npr_summary(g, group_by_chain=True)
    rhat_max = max(float(np.nanmax(v["r_hat"])) for v in summ.values())
    ess_min = min(float(np.nanmin(v["n_eff"])) for v in summ.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    n_tot = 4 * n_samp
    raw_mean = np.asarray(g["raw"]).reshape(-1, r0, nm).mean(0)
    np.savez_compressed(outp, raw_mean=raw_mean, ks=ks, rs=rs, r0=r0, tau=TAU,
                        meta=json.dumps({"fold": fold_key, "train_keys": train_keys, "counts": counts,
                                         "rhat_max": rhat_max, "ess_min": ess_min,
                                         "div_frac": div / n_tot, "nm": nm,
                                         "theta_fixed": "theta_MAP_wide (D5)",
                                         "active_s": round(time.time() - t0, 1)}))
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": f"armC_{tag}", "active_s": round(time.time() - t0, 1)}) + "\n")
    print(f"{tag}: rhat_max={rhat_max:.4f} ess_min={ess_min:.0f} div={div}/{n_tot} "
          f"({time.time()-t0:.0f}s)", flush=True)


def shapes_forward(pkg, theta, raw_mean, ks, r0, tau=TAU):
    """Deterministic forward with posterior-mean inferred shapes (for wscore_wide fwd hook)."""
    K = np.asarray(pkg.A_fix) + np.einsum("g,gij->ij", np.asarray(theta, float), np.asarray(pkg.A))
    lam, Q = np.linalg.eigh(K)
    f = np.sqrt(np.clip(lam, 1e-9, None)) / (2 * np.pi)
    r = K.shape[0]
    nm = len(ks)
    phi = np.zeros((r, nm))
    phi[ks, np.arange(nm)] = 1.0
    phi[:r0, :] += tau * raw_mean
    phi /= np.sqrt((phi ** 2).sum(0) + 1e-30)
    ray = np.einsum("im,ij,jm->m", phi, K, phi)
    f_new = np.sqrt(np.clip(ray, 1e-6, None)) / (2 * np.pi)
    f_all = f.copy(); f_all[ks] = f_new

    def fwd(pkg_, theta_, dkey, fc):
        m_in = (f_all >= WFW.F_SUPPORT[0]) & (f_all <= WFW.F_SUPPORT[1])
        zi = WFW.zeta_table(f_all)
        Us = np.asarray(pkg_.sens_rows) @ Q
        Ud = (np.asarray(pkg_.drives[dkey]) @ Q) * m_in
        res = Us * Ud[None, :]
        Us_p = np.asarray(pkg_.sens_rows) @ phi
        Ud_p = np.asarray(pkg_.drives[dkey]) @ phi
        res[:, ks] = Us_p * Ud_p[None, :]
        return WFW.WF._windowed_H(res, np.where(m_in, f_all, 1e6), zi, np.asarray(fc, float)) / WFW.G_IN_S2
    return fwd


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("fold")
    ap.add_argument("--warm", type=int, default=800)
    ap.add_argument("--samp", type=int, default=600)
    a = ap.parse_args()
    run_fold(a.fold, a.warm, a.samp)
