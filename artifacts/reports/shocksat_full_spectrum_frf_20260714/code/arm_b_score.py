#!/usr/bin/env python3
"""arm_b_score — score arm B given that its NUTS posteriors are MULTIMODAL / non-converged (R-hat 29-360,
ESS~2; mechanism = rugged resonance-alignment likelihood, out/identifiability.json). Because a non-mixed
posterior mean is not meaningful, arm B is scored at a DETERMINISTIC multi-start amplitude-MAP (the best
mode) computed per fold on the TRAIN drives only (leakage-safe), on the SAME sub-basis exact-eigh
likelihood NUTS used (F_LIK 45-400). Scoring uses the full wide forward, all bands. Every arm-B posterior's
worst-case R-hat/ESS is registered to nuts_diagnostics.json as YELLOW (labeled not-trustworthy).

Records: arm 'B' = amplitude-MAP (with-error-term MAP), arm 'B_theta_only' = theta-only MAP (overconfidence
control). out/armB_summary.json carries posterior-mean-vs-MAP contrast + per-fold theta. Honest labels
everywhere: NUTS non-converged; MAP is a labeled deterministic fallback (AGENTS Sampler Decision)."""
import json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402
import wscore_wide as SW                       # noqa: E402
import wide_forward as WFW                     # noqa: E402
import arm_b_nuts as AB                        # noqa: E402
import check_surrogate as CS                   # noqa: E402

import jax                                     # noqa: E402
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp                        # noqa: E402
from scipy.optimize import minimize           # noqa: E402

OUTD = os.path.join(WS, "out", "armB")
t0 = time.time()


def amp_map_fold(pkg, sub, fold_key, theta_only, n_starts=5):
    """Multi-start deterministic MAP of the amplitude (+prior) likelihood on the 3 TRAIN drives (D19-style).
    Uses the sub-basis exact-eigh forward (same as the NUTS likelihood). Leakage-safe: excludes fold_key."""
    _, data = AB.build_fold_data(pkg, fold_key, thin_bins=2, n_ch_max=30)
    A_sub = jnp.asarray(sub.A_sub); A_fix = jnp.asarray(sub.A_fix_sub)
    sens = jnp.asarray(sub.sens_sub)
    drv = {d["key"]: jnp.asarray(sub.drv_sub[d["key"]]) for d in data}
    zf, zz = WFW.WF.survey_table(); zfj, zzj = jnp.asarray(zf), jnp.asarray(zz); zmed = float(np.median(zz))
    ydat = {d["key"]: jnp.asarray(d["y"]) for d in data}
    kbn = {d["key"]: jnp.asarray(d["kbins"]) for d in data}
    rowsn = {d["key"]: np.asarray(d["rows"]) for d in data}

    def nll(t):
        K = A_fix + jnp.einsum("g,gij->ij", jnp.exp(t), A_sub)
        lam, Q = jnp.linalg.eigh(K)
        f = jnp.sqrt(jnp.clip(lam, 1e-6, None)) / (2 * jnp.pi)
        m_in = (f >= AB.F_SUPPORT[0]) & (f <= AB.F_SUB * 0.95)
        zi = jnp.where(f > zfj[-1], zmed, jnp.interp(f, zfj, zzj))
        f_safe = jnp.where(m_in, f, 1e6)
        Us = sens @ Q
        sse, n = 0.0, 0
        for k in ydat:
            Ud = (drv[k] @ Q) * m_in
            res = Us[rowsn[k]] * Ud[None, :]
            mu = AB.jax_windowed_logH(res, f_safe, zi, kbn[k])
            r = ydat[k] - mu
            r = r - jnp.mean(r)
            sse = sse + jnp.sum(r ** 2); n += r.size
        return 0.5 * n * jnp.log(sse / n) + 0.5 * jnp.sum(t ** 2) / 0.25 ** 2

    val = jax.jit(nll); grad = jax.jit(jax.grad(nll))
    rng = np.random.default_rng(20260715)
    starts = [np.zeros(9)] + [rng.normal(0, 0.25, 9) for _ in range(n_starts - 1)]
    best = None
    for x0 in starts:
        r = minimize(lambda x: float(val(jnp.asarray(x))), x0, jac=lambda x: np.asarray(grad(jnp.asarray(x))),
                     method="L-BFGS-B", options=dict(maxiter=150))
        if best is None or r.fun < best.fun:
            best = r
    return np.exp(best.x), float(best.fun)


def score_variant(pkg, sub, variant, arm, qoi_w):
    done = SW.existing("dev")
    if arm in done:
        print(f"{arm} already scored (resume-skip)")
        return done[arm], {}
    caches = SW.load_caches()
    folds, maps = {}, {}
    for fold in SW.DEV_KEYS:
        th, nllv = amp_map_fold(pkg, sub, fold, theta_only=(variant == "theta_only"))
        maps[fold] = th.tolist()
        train_keys = [k for k in SW.DEV_KEYS if k != fold]
        rho, bmasks = SW._train_warp(pkg, th, train_keys, caches, True, None)
        fold_mask = None
        if bmasks:
            fm = np.zeros(len(caches[fold]["freqs"]), bool)
            for tk, mm in bmasks.items():
                if mm.shape[0] == fm.shape[0]:
                    fm |= mm
            fold_mask = fm if fm.sum() >= SW.MIN_BAND else None
        gain_db = SW._fold_gain(pkg, th, train_keys, caches, True, None)
        bands = SW._grade_bands(pkg, th, fold, caches[fold], rho, fold_mask, True, None, qoi_w)
        folds[fold] = {"bands": bands, "rho": round(rho, 4), "gain_dB": round(gain_db, 3),
                       "train_keys": train_keys, "amp_map_theta": th.tolist()}
        print(f"  {arm} {fold}: sub200 {bands['sub200'].get('P1p')}", flush=True)
    rec = SW._aggregate(arm, folds, stage="dev",
                        note=f"amplitude-trained {variant}: scored at per-fold multi-start amplitude-MAP; "
                             f"NUTS posterior MULTIMODAL/non-converged (R-hat up to 360, ESS~2) -> MAP is a "
                             f"labeled deterministic fallback (see identifiability.json)")
    with open(SW.SLOG, "a") as f:
        f.write(json.dumps(rec) + "\n")
    return rec, maps


def main():
    pkg = WP.load("A0_wide")
    sub = AB.SubBasis(pkg)
    qoi_w = None
    qp = os.path.join(WS, "out", "qoi_sensor_weights.json")
    if os.path.exists(qp):
        qoi_w = {int(k): v for k, v in json.load(open(qp))["weights"].items()}
    diags, summary = [], {}
    for variant, arm in (("with_error_term", "B"), ("theta_only", "B_theta_only")):
        for fold in SW.DEV_KEYS:
            p = os.path.join(OUTD, f"{variant}_{fold}.npz")
            if not os.path.exists(p):
                print(f"missing {p}"); return
            z = np.load(p, allow_pickle=True); meta = json.loads(str(z["meta"]))
            diags.append({"name": f"armB_{variant}_{fold}", "rhat_max": meta["rhat_max"],
                          "ess_min": meta["ess_min"], "div_frac": meta["div_frac"],
                          "status": "non_converged_multimodal", "sampler": "NUTS"})
            summary[f"{variant}_{fold}"] = {
                "post_mean_theta": dict(zip(pkg.free_names,
                                            np.round(np.exp(np.asarray(z["t_log_theta"]).reshape(-1, 9)
                                                            .mean(0)), 4).tolist())),
                "rhat_max": meta["rhat_max"], "ess_min": meta["ess_min"], "div_frac": meta["div_frac"],
                "sigma_e_mean": (float(np.mean(z["sigma_e"])) if "sigma_e" in z.files else None),
                "sigma_n_mean": float(np.mean(z["sigma_n"]))}
        rec, maps = score_variant(pkg, sub, variant, arm, qoi_w)
        summary[f"{variant}_amp_map"] = maps
        print(arm, json.dumps(rec["bands_agg"], indent=1), flush=True)
    # register YELLOW diagnostics
    ndp = os.path.join(WS, "out", "nuts_diagnostics.json")
    reg = json.load(open(ndp)) if os.path.exists(ndp) else {"posteriors": []}
    have = {p["name"] for p in reg["posteriors"]}
    reg["posteriors"] += [d for d in diags if d["name"] not in have]
    json.dump(reg, open(ndp, "w"), indent=1)
    json.dump(summary, open(os.path.join(WS, "out", "armB_summary.json"), "w"), indent=1)
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": "armB_score", "active_s": round(time.time() - t0, 1)}) + "\n")


if __name__ == "__main__":
    main()
