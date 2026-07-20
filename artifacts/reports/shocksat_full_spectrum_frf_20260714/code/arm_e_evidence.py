#!/usr/bin/env python3
"""arm_e_evidence — H5 re-test: does AMPLITUDE-INCLUSIVE Bayesian model-class selection rank candidates
like held-out scoring does? (card §6 E; decisions D5)

Candidate set (pre-registered): A0_wide baseline + the top D-loop candidates by dev sub-200 P1' (up to 10,
both tracks — the selection score must not know the tracks) + the composite run's historical evidence
winner rand10 REBUILT read-only in this study's machinery (spec copied from the composite workspace).

Evidence per candidate (Laplace at the amplitude-MAP; composite convention prior sweep):
  L(theta) = sum_drives sum_{ch,f} logN(y - mu(theta) - gain_d ; 0, sigma_n)  [D6 surrogate forward]
           + sum_paired logN(lam_tgt - lam(theta); 0, (0.05 lam_tgt)^2)      [S0 freq term]
  profile gains (closed form per drive), sigma_n (closed form); Laplace over theta only (d=9+),
  logZ ~ logL(theta*) + logPrior(theta*) + d/2 ln(2pi) - 1/2 ln det H,  H = -d2 logPost (jax hessian).
Deliverable: Spearman(evidence rank, held-out dev sub-200 rank) per prior width + scatter data
(out/arm_E.json). ALL 4 dev drives in the selection likelihood (selection is not fold-based); the held-out
comparison uses the LODO fold-averages already logged — the two use the same data differently, exactly the
H5 question."""
import json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402
import wscore_wide as SW                       # noqa: E402
import wide_forward as WFW                     # noqa: E402
import arm_b_nuts as AB                        # noqa: E402

import jax                                     # noqa: E402
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp                        # noqa: E402
from jax.scipy.optimize import minimize as jmin  # noqa: E402

PRIOR_SIGS = (0.15, 0.25, 0.40)
t0 = time.time()


def build_data(pkg):
    caches = SW.load_caches()
    data = []
    for tk in SW.DEV_KEYS:
        c = caches[tk]
        rows, cols = SW._usable(pkg, c, c["band"])
        step = max(1, int(np.ceil(len(rows) / 30)))
        rows, cols = rows[::step], cols[::step]
        lik_band = c["band"] & (c["freqs"] >= AB.F_LIK[0]) & (c["freqs"] <= AB.F_LIK[1])
        bidx = np.where(lik_band)[0][::3]
        fc = c["freqs"][bidx]
        kb = np.round(fc * AB.NFRAME / AB.FS).astype(int)
        y = np.log10(np.abs(c["H1"][cols][:, bidx]) + 1e-300)
        data.append(dict(key=tk, rows=np.asarray(rows), kbins=jnp.asarray(kb), y=jnp.asarray(y)))
    return data


def evidence_for(pkg, data, sig_prior):
    sub = AB.SubBasis(pkg)                          # D10: exact sub-basis eigh, same as arm B
    A_sub = jnp.asarray(sub.A_sub)
    A_fix_sub = jnp.asarray(sub.A_fix_sub)
    sens = jnp.asarray(sub.sens_sub)
    drv = {d["key"]: jnp.asarray(sub.drv_sub[d["key"]]) for d in data}
    zf_s, zz_s = WFW.WF.survey_table()
    zfj, zzj, zmed = jnp.asarray(zf_s), jnp.asarray(zz_s), float(np.median(zz_s))
    pairs = np.asarray(pkg.pairs)
    pairs = pairs[pairs[:, 2] >= 0.3]
    # map pair mode indices into the sub-basis index space (drop pairs above F_SUB)
    sub_of = {int(gk): j for j, gk in enumerate(sub.idx)}
    keep = [i for i in range(len(pairs)) if int(pairs[i, 1]) in sub_of]
    femk = jnp.asarray([sub_of[int(pairs[i, 1])] for i in keep])
    tgt = jnp.asarray((np.asarray(pkg.mfreqs)[pairs[keep, 0].astype(int)] * 2 * np.pi) ** 2)
    npar = int(A_sub.shape[0])

    def neg_logpost(t):
        K = A_fix_sub + jnp.einsum("g,gij->ij", jnp.exp(t), A_sub)
        lam, Q = jnp.linalg.eigh(K)
        f = jnp.sqrt(jnp.clip(lam, 1e-6, None)) / (2 * jnp.pi)
        m_in = (f >= AB.F_SUPPORT[0]) & (f <= AB.F_SUB * 0.95)
        zi = jnp.where(f > zfj[-1], zmed, jnp.interp(f, zfj, zzj))
        f_safe = jnp.where(m_in, f, 1e6)
        Us = sens @ Q
        sse, n_tot = 0.0, 0
        for d in data:
            Ud = (drv[d["key"]] @ Q) * m_in
            res = Us[d["rows"]] * Ud[None, :]
            mu = AB.jax_windowed_logH(res, f_safe, zi, d["kbins"])
            resid = d["y"] - mu
            resid = resid - jnp.mean(resid)             # profiled global gain per drive (closed form)
            sse = sse + jnp.sum(resid ** 2)
            n_tot += resid.size
        sig2 = sse / n_tot                              # profiled sigma_n^2
        nll_amp = 0.5 * n_tot * (jnp.log(2 * jnp.pi * sig2) + 1.0)
        var_f = (0.05 * tgt) ** 2
        nll_frq = 0.5 * jnp.sum((tgt - lam[femk]) ** 2 / var_f + jnp.log(2 * jnp.pi * var_f))
        nlp = 0.5 * jnp.sum(t ** 2) / sig_prior ** 2 + npar * jnp.log(sig_prior * jnp.sqrt(2 * jnp.pi))
        return nll_amp + nll_frq + nlp

    res = jmin(neg_logpost, jnp.zeros(npar), method="BFGS", options=dict(maxiter=200))
    t_star = res.x
    H = jax.hessian(neg_logpost)(t_star)
    sign, logdet = np.linalg.slogdet(np.asarray(H))
    if sign <= 0:
        logdet = float(np.log(np.abs(np.linalg.det(np.asarray(H))) + 1e-30))
    logZ = float(-res.fun + 0.5 * npar * np.log(2 * np.pi) - 0.5 * logdet)
    return logZ, np.exp(np.asarray(t_star))


def main():
    # candidate set: A0_wide + top loop candidates by dev sub-200 (<=10, tracks mixed) + rand10 rebuild
    recs = SW.existing("dev")
    loop = [(a, r) for a, r in recs.items() if a.startswith("D_")]
    loop.sort(key=lambda ar: -(ar[1]["bands_agg"]["sub200"]["P1p_mean"] or -9))
    cset = [("A0_wide", "A1")] + [(r.get("cid"), a) for a, r in loop[:10]]
    r10p = os.path.join(WS, "out", "candidate_specs", "rand10_rebuild.json")
    if os.path.exists(os.path.join(WS, "data", "packages_wide", "rand10_rebuild.npz")):
        cset.append(("rand10_rebuild", "rand10_rebuild"))
    out = {"candidates": [], "prior_sigs": list(PRIOR_SIGS)}
    for cid, arm in cset:
        pkg = WP.load(cid)
        data = build_data(pkg)
        row = {"cid": cid, "arm": arm,
               "heldout_sub200": (recs.get(arm) or recs.get("A1"))["bands_agg"]["sub200"]["P1p_mean"]}
        for sp in PRIOR_SIGS:
            lz, th = evidence_for(pkg, data, sp)
            row[f"logZ_sig{sp}"] = round(lz, 1)
        out["candidates"].append(row)
        print(row, flush=True)
    from scipy.stats import spearmanr
    hs = [c["heldout_sub200"] for c in out["candidates"]]
    for sp in PRIOR_SIGS:
        lz = [c[f"logZ_sig{sp}"] for c in out["candidates"]]
        out[f"spearman_sig{sp}"] = round(float(spearmanr(lz, hs).statistic), 3)
    out["spearman"] = out["spearman_sig0.25"]
    out["n_candidates"] = len(out["candidates"])
    json.dump(out, open(os.path.join(WS, "out", "arm_E.json"), "w"), indent=1)
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": "armE", "active_s": round(time.time() - t0, 1)}) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "candidates"}, indent=1))


if __name__ == "__main__":
    main()
