#!/usr/bin/env python3
"""check_surrogate — forward-approximation gates for arm B (D6 record + D10 operative gate).
(1) documents the RETIRED first-order surrogate's error (D6 failure record);
(2) the OPERATIVE gate: Galerkin sub-basis (modes <= F_SUB) exact-eigh forward vs the full-r exact forward
    on the likelihood band 45-500 Hz — pass if median <= 0.05 dex across prior draws + posterior mean.
Writes/updates out/armB_surrogate_check.json."""
import json, os, sys
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402
import wide_forward as WFW                     # noqa: E402
import wscore_wide as SW                       # noqa: E402
import arm_b_nuts as AB                        # noqa: E402
import jax.numpy as jnp                        # noqa: E402

BANDS = [("sub200", 45.0, 200.0), ("b200_500", 200.0, 500.0), ("b500_1000", 500.0, 1000.0)]


def surrogate_logH(pkg, sur, theta, dkey, fc):
    lam, R = sur.modes_np(theta)
    f = np.sqrt(np.clip(lam, 1e-6, None)) / (2 * np.pi)
    m_in = (f >= AB.F_SUPPORT[0]) & (f <= AB.F_SUPPORT[1])
    zi = WFW.zeta_table(f)
    Us = np.asarray(pkg.sens_rows) @ R
    Ud = (np.asarray(pkg.drives[dkey]) @ R) * m_in
    res = Us * Ud[None, :]
    kb = np.round(np.asarray(fc) * AB.NFRAME / AB.FS).astype(int)
    return np.asarray(AB.jax_windowed_logH(jnp.asarray(res), jnp.asarray(np.where(m_in, f, 1e6)),
                                           jnp.asarray(zi), jnp.asarray(kb)))


def subbasis_logH(pkg, sub, theta, dkey, fc):
    lam, Q = sub.modes_np(theta)
    f = np.sqrt(np.clip(lam, 1e-6, None)) / (2 * np.pi)
    m_in = (f >= AB.F_SUPPORT[0]) & (f <= AB.F_SUB * 0.95)
    zi = WFW.zeta_table(f)
    Us = sub.sens_sub @ Q
    Ud = (sub.drv_sub[dkey] @ Q) * m_in
    res = Us * Ud[None, :]
    kb = np.round(np.asarray(fc) * AB.NFRAME / AB.FS).astype(int)
    return np.asarray(AB.jax_windowed_logH(jnp.asarray(res), jnp.asarray(np.where(m_in, f, 1e6)),
                                           jnp.asarray(zi), jnp.asarray(kb)))


def main(theta_extra=None, label_extra="posterior_mean"):
    pkg = WP.load("A0_wide")
    sur = AB.Surrogate(pkg)
    sub = AB.SubBasis(pkg)
    caches = SW.load_caches()
    dkey = "m_xpos_990x"
    c = caches[dkey]
    fc = c["freqs"][c["band"]]
    rng = np.random.default_rng(20260714)
    thetas = [np.exp(rng.normal(0, 0.25, 9)) for _ in range(12)]
    cases = [("prior_draw_%02d" % i, th) for i, th in enumerate(thetas)]
    if theta_extra is not None:
        cases.append((label_extra, np.asarray(theta_extra, float)))
    out = {"delta_lambda_floor": sur.delta, "drive": dkey, "r0_subbasis": sub.r0, "cases": []}
    for name, th in cases:
        exact = WFW.predict_logH(pkg, th, dkey, fc, windowed=True)
        surr = surrogate_logH(pkg, sur, th, dkey, fc)
        gal = subbasis_logH(pkg, sub, th, dkey, fc)
        rec = {"case": name, "theta_absmax_dev": float(np.max(np.abs(th - 1)))}
        for bn, lo, hi in BANDS:
            bm = (fc >= lo) & (fc < hi)
            if bm.sum() == 0:
                continue
            d = np.abs(surr[:, bm] - exact[:, bm])
            rec[bn] = {"med_dex": round(float(np.median(d)), 4), "p90_dex": round(float(np.percentile(d, 90)), 4)}
            if hi <= 500.0:
                dg = np.abs(gal[:, bm] - exact[:, bm])
                rec[bn]["galerkin_med_dex"] = round(float(np.median(dg)), 4)
                rec[bn]["galerkin_p90_dex"] = round(float(np.percentile(dg, 90)), 4)
        out["cases"].append(rec)
    med_sub200 = float(np.median([c["sub200"]["med_dex"] for c in out["cases"]]))
    out["median_over_cases_sub200_dex"] = med_sub200
    out["pass_D6"] = bool(med_sub200 <= 0.15)
    gvals = [c[b]["galerkin_med_dex"] for c in out["cases"] for b in ("sub200", "b200_500")
             if "galerkin_med_dex" in c.get(b, {})]
    out["galerkin_median_dex_45_500"] = float(np.median(gvals)) if gvals else None
    out["pass_D10_galerkin"] = bool(out["galerkin_median_dex_45_500"] is not None
                                    and out["galerkin_median_dex_45_500"] <= 0.05)
    p = os.path.join(WS, "out", "armB_surrogate_check.json")
    if os.path.exists(p):
        prev = json.load(open(p))
        prev_cases = {c["case"] for c in prev.get("cases", [])}
        out["cases"] = prev.get("cases", []) + [c for c in out["cases"] if c["case"] not in prev_cases]
    json.dump(out, open(p, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(json.loads(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else "posterior_mean")
    else:
        main()
