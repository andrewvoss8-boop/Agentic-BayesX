#!/usr/bin/env python3
"""arm_b_nuts — amplitude-TRAINED Bayesian updating of the 9 group stiffnesses (card §6 arm B).

FIRST ShockSat run where theta ever sees per-channel FRF amplitude data. Per LODO fold: NUTS posterior over
theta with the likelihood on the 3 TRAIN drives' log10|H1| over the certified band (whole-data likelihood,
Q7 contract):

  y_{d,ch}(f) = log10|W[H](theta)_{d,ch}(f)| + gain_d + eps_{d,ch}(f)
  eps ~ GP over log10(f): cov = sigma_e^2 * SE(log10 f; ell) + sigma_n^2 I   (marginalized analytically,
        one shared kernel across channels/drives; statFEM-style correlated output error)
  theta_g = exp(t_g), t_g ~ Normal(0, 0.25);  gain_d ~ Normal(0, 1.0) dex (ONE global gain per drive)
  sigma_e ~ HalfNormal(0.5), ell ~ LogNormal(ln 0.1, 0.5) [log10-Hz], sigma_n ~ HalfNormal(0.2)

FORWARD INSIDE NUTS (decisions D10; the D6 first-order surrogate FAILED its 0.15-dex gate in the dry run
— 0.64 dex at a 1-sigma prior draw, dense-spectrum physics): EXACT jnp.linalg.eigh on the GALERKIN
sub-basis of theta=1 modes <= F_SUB Hz (r0 ~ 230); likelihood band 45-500 Hz (labeled deviation from the
card's whole-band likelihood; 500-1000 Hz becomes doubly-held-out for every arm). Galerkin truncation is
gated by out/armB_surrogate_check.json (sub-basis vs full-r exact forward, <=0.05 dex median on 45-500).
Window operator: exact JAX port (gated by out/armB_jax_check.json). SCORING always uses the exact
within-basis eigh at the posterior-mean theta on the FULL r basis (wscore_wide), all three bands.
Controls: --theta-only drops the correlated term (overconfidence control). float64, 4 chains.
Thinning (ledger A4): every 2nd bin, <=40 channels — counts recorded. Resumable per (fold, variant).
"""
from __future__ import annotations
import argparse, json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                            # noqa: E402
import wscore_wide as SW                             # noqa: E402
import wide_forward as WFW                           # noqa: E402

import jax                                            # noqa: E402
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp                               # noqa: E402
import numpyro                                        # noqa: E402
import numpyro.distributions as dist                  # noqa: E402
from numpyro.infer import MCMC, NUTS, init_to_median  # noqa: E402

OUTD = os.path.join(WS, "out", "armB")
os.makedirs(OUTD, exist_ok=True)

# ---- window constants (wforward provenance; identical numbers) ----
FS = 250000.0
NFRAME = 122880
PRE_GAP = 200
EXP_END = 0.05
DT = 1.0 / FS
RHO_WIN = float(np.exp(np.log(EXP_END) / (NFRAME - 1)))
W_N0 = RHO_WIN ** PRE_GAP
M_SUM = NFRAME - PRE_GAP
G_IN_S2 = 386.0886
F_SUPPORT = (35.0, 1650.0)
F_SUB = 450.0                # Galerkin sub-basis top (D11: real basis credible to 640; r0~118)
F_LIK = (45.0, 400.0)        # likelihood band (D11); 400-500 partial-held-out, 500+ FEM-limited


def jax_windowed_logH(res, fi, zi, kbins):
    """JAX port of wforward._windowed_H -> log10|H| (n_sens, n_k). res (n_sens, nm); fi/zi (nm,)."""
    wn = 2 * jnp.pi * fi
    zi = jnp.clip(zi, 1e-8, 0.999)
    sig = zi * wn
    wd = wn * jnp.sqrt(1.0 - zi ** 2)
    p_pl = -sig + 1j * wd
    r_pl = (2.0 * sig * p_pl + wn ** 2) / (2j * wd)
    ephi = jnp.exp(-2j * jnp.pi * kbins / NFRAME)
    zp = (RHO_WIN * jnp.exp(p_pl * DT))[:, None] * ephi[None, :]
    zm = (RHO_WIN * jnp.exp(jnp.conj(p_pl) * DT))[:, None] * ephi[None, :]
    Sp = (1.0 - zp ** M_SUM) / (1.0 - zp)
    Sm = (1.0 - zm ** M_SUM) / (1.0 - zm)
    term = -W_N0 + DT * (r_pl[:, None] * Sp + jnp.conj(r_pl)[:, None] * Sm)
    H = res @ term / G_IN_S2
    return jnp.log10(jnp.abs(H) + 1e-300)


class Surrogate:
    """RETIRED for arm B (failed the D6 gate; kept ONLY so check_surrogate can document the failure).
    First-order (lam + Tikhonov eigenvector) modal surrogate around theta=1."""

    def __init__(self, pkg):
        lam0 = np.asarray(pkg.lam_all)[int(pkg.n_rbm):]
        self.lam0 = lam0
        A = np.asarray(pkg.A)                        # (9, r, r) in the theta=1 eigenbasis
        self.A = A
        D0 = lam0[None, :] - lam0[:, None]           # D0_ji = lam_i - lam_j
        gaps = np.diff(np.sort(lam0))
        self.delta = float(0.5 * np.median(gaps))
        reg = D0 / (D0 ** 2 + self.delta ** 2)
        np.fill_diagonal(reg, 0.0)
        self.reg = reg
        self.diagA = np.stack([np.diag(A[g]) for g in range(A.shape[0])])   # (9, r)

    def modes_np(self, theta):
        dth = np.asarray(theta, float) - 1.0
        lam = self.lam0 + dth @ self.diagA
        R = np.eye(len(self.lam0)) + self.reg * np.einsum("g,gij->ij", dth, self.A)
        return lam, R


class SubBasis:
    """Galerkin sub-basis (theta=1 modes <= F_SUB) for the EXACT-eigh likelihood forward (D10)."""

    def __init__(self, pkg):
        freqs_el = np.asarray(pkg.freqs_el)
        self.idx = np.where(freqs_el <= F_SUB)[0]
        self.r0 = len(self.idx)
        A = np.asarray(pkg.A)
        self.A_sub = A[:, self.idx][:, :, self.idx]                 # (9, r0, r0)
        self.A_fix_sub = np.asarray(pkg.A_fix)[np.ix_(self.idx, self.idx)]
        self.sens_sub = np.asarray(pkg.sens_rows)[:, self.idx]
        self.drv_sub = {k: np.asarray(pkg.drives[k])[self.idx] for k in pkg.drives}

    def modes_np(self, theta):
        K = self.A_fix_sub + np.einsum("g,gij->ij", np.asarray(theta, float), self.A_sub)
        lam, Q = np.linalg.eigh(K)
        return lam, Q


def build_fold_data(pkg, fold_key, thin_bins=2, n_ch_max=40):
    """Train-drive data tensors for one fold, LIKELIHOOD BAND F_LIK only (D10).
    NEVER touches the fold's dev drive (leakage gate G06)."""
    caches = SW.load_caches()
    train_keys = [k for k in SW.DEV_KEYS if k != fold_key]
    data = []
    for tk in train_keys:
        c = caches[tk]
        lik_band = c["band"] & (c["freqs"] >= F_LIK[0]) & (c["freqs"] <= F_LIK[1])
        rows, cols = SW._usable(pkg, c, lik_band)
        step = max(1, int(np.ceil(len(rows) / n_ch_max)))
        rows, cols = rows[::step], cols[::step]
        bidx = np.where(lik_band)[0][::thin_bins]
        fc = c["freqs"][bidx]
        kbins = np.round(fc * NFRAME / FS).astype(int)
        y = np.log10(np.abs(c["H1"][cols][:, bidx]) + 1e-300)
        data.append(dict(key=tk, rows=np.asarray(rows), kbins=kbins, fc=fc, y=y))
    return train_keys, data


def make_model(pkg, sub, data, theta_only, zsurv_f, zsurv_z, zmed):
    A_sub = jnp.asarray(sub.A_sub)
    A_fix_sub = jnp.asarray(sub.A_fix_sub)
    sens = jnp.asarray(sub.sens_sub)
    drv = {d["key"]: jnp.asarray(sub.drv_sub[d["key"]]) for d in data}
    zf = jnp.asarray(zsurv_f); zz = jnp.asarray(zsurv_z)

    def model():
        t = numpyro.sample("t_log_theta", dist.Normal(0.0, 0.25).expand([A_sub.shape[0]]).to_event(1))
        K = A_fix_sub + jnp.einsum("g,gij->ij", jnp.exp(t), A_sub)
        lam, Q = jnp.linalg.eigh(K)                      # EXACT sub-basis modes (D10)
        f = jnp.sqrt(jnp.clip(lam, 1e-6, None)) / (2 * jnp.pi)
        m_in = (f >= F_SUPPORT[0]) & (f <= F_SUB * 0.95)   # drop the truncation-polluted top edge
        zi = jnp.where(f > zf[-1], zmed, jnp.interp(f, zf, zz))
        sigma_n = numpyro.sample("sigma_n", dist.HalfNormal(0.2))
        if not theta_only:
            sigma_e = numpyro.sample("sigma_e", dist.HalfNormal(0.5))
            ell = numpyro.sample("ell", dist.LogNormal(jnp.log(0.1), 0.5))
        Us_all = sens @ Q                                # (n_sens, r0)
        f_safe = jnp.where(m_in, f, 1e6)
        for d in data:
            gain = numpyro.sample(f"gain_{d['key']}", dist.Normal(0.0, 1.0))
            Ud = (drv[d["key"]] @ Q) * m_in
            res = Us_all[d["rows"]] * Ud[None, :]
            mu = jax_windowed_logH(res, f_safe, zi, jnp.asarray(d["kbins"])) + gain
            resid = jnp.asarray(d["y"]) - mu
            lf = jnp.log10(jnp.asarray(d["fc"]))
            if theta_only:
                numpyro.sample(f"y_{d['key']}", dist.Normal(0.0, sigma_n).expand(resid.shape).to_event(2),
                               obs=resid)
            else:
                dl = lf[:, None] - lf[None, :]
                Kf = sigma_e ** 2 * jnp.exp(-0.5 * (dl / ell) ** 2) \
                    + (sigma_n ** 2 + 1e-8) * jnp.eye(lf.shape[0])
                numpyro.sample(f"y_{d['key']}",
                               dist.MultivariateNormal(loc=jnp.zeros(lf.shape[0]), covariance_matrix=Kf)
                                   .expand([resid.shape[0]]).to_event(1),
                               obs=resid)
    return model


def run_fold(fold_key, theta_only=False, n_warm=500, n_samp=500, thin_bins=2, n_ch_max=30):
    variant = "theta_only" if theta_only else "with_error_term"
    tag = f"{variant}_{fold_key}"
    outp = os.path.join(OUTD, tag + ".npz")
    if os.path.exists(outp):
        print(f"{tag}: exists (resume-skip)")
        return
    t0 = time.time()
    pkg = WP.load("A0_wide")
    sub = SubBasis(pkg)
    zf, zz = WFW.WF.survey_table()
    train_keys, data = build_fold_data(pkg, fold_key, thin_bins, n_ch_max)
    counts = {d["key"]: {"n_ch": int(len(d["rows"])), "n_bins": int(len(d["kbins"]))} for d in data}
    print(f"{tag}: r0={sub.r0} train={train_keys} counts={counts}", flush=True)
    model = make_model(pkg, sub, data, theta_only, zf, zz, float(np.median(zz)))
    kernel = NUTS(model, target_accept_prob=0.9, dense_mass=True, init_strategy=init_to_median,
                  max_tree_depth=7)
    mcmc = MCMC(kernel, num_warmup=n_warm, num_samples=n_samp, num_chains=4,
                chain_method="sequential", progress_bar=False)
    mcmc.run(jax.random.PRNGKey(20260714), extra_fields=("diverging",))
    g = mcmc.get_samples(group_by_chain=True)
    samp = {k: np.asarray(v) for k, v in g.items()}
    from numpyro.diagnostics import summary as npr_summary
    summ = npr_summary(g, group_by_chain=True)
    rhat_max = max(float(np.nanmax(v["r_hat"])) for v in summ.values())
    ess_min = min(float(np.nanmin(v["n_eff"])) for v in summ.values())
    div = int(np.asarray(mcmc.get_extra_fields()["diverging"]).sum())
    n_tot = 4 * n_samp
    np.savez_compressed(outp, **samp,
                        meta=json.dumps({"fold": fold_key, "variant": variant, "train_keys": train_keys,
                                         "counts": counts, "rhat_max": rhat_max, "ess_min": ess_min,
                                         "div_frac": div / n_tot, "n_warm": n_warm, "n_samp": n_samp,
                                         "forward": "galerkin_subbasis_exact_eigh_D10", "r0": sub.r0,
                                         "active_s": round(time.time() - t0, 1)}))
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": f"armB_{tag}", "active_s": round(time.time() - t0, 1)}) + "\n")
    print(f"{tag}: rhat_max={rhat_max:.4f} ess_min={ess_min:.0f} div={div}/{n_tot} "
          f"({time.time()-t0:.0f}s)", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("fold")
    ap.add_argument("--theta-only", action="store_true")
    ap.add_argument("--warm", type=int, default=500)
    ap.add_argument("--samp", type=int, default=500)
    a = ap.parse_args()
    run_fold(a.fold, a.theta_only, a.warm, a.samp)
