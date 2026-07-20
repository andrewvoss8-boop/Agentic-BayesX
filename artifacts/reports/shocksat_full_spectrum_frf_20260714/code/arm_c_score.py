#!/usr/bin/env python3
"""arm_c_score — score arm C given that its shape-field NUTS is multimodal / non-converged and very slow
(fold-1 R-hat 13.95, ESS 2, 2.5 h; D13). Report the fold-1 NUTS as YELLOW representative evidence; SCORE
arm C at a DETERMINISTIC multi-start MAP of the shape field per fold (L-BFGS on the SAME freq+MAC+TRAIN-
amplitude log-density used by the NUTS model), theta fixed at MAP, train drives only (leakage-safe). Fast.
Writes out/armC/shapes_map_<fold>.npz + one dev record 'C'. Honest labels throughout."""
import json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402
import wscore_wide as SW                       # noqa: E402
import wide_forward as WFW                     # noqa: E402
import arm_c_nuts as AC                        # noqa: E402
import arm_b_nuts as AB                        # noqa: E402

import jax                                     # noqa: E402
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp                        # noqa: E402
from scipy.optimize import minimize           # noqa: E402

OUTD = os.path.join(WS, "out", "armC")
t0 = time.time()


def map_fold(pkg, theta, fold_key, n_starts=4):
    """Deterministic MAP of the shape field on the 3 TRAIN drives (leakage-safe). Returns raw_map (r0,nm)."""
    rs, ks = AC.matched_modes(pkg)
    nm = len(ks); r = np.asarray(pkg.A).shape[1]
    freqs_el = np.asarray(pkg.freqs_el); r0 = int((freqs_el <= AC.F_FIELD).sum())
    K_MAP = np.asarray(pkg.A_fix) + np.einsum("g,gij->ij", theta, np.asarray(pkg.A))
    lamM, QM = np.linalg.eigh(K_MAP)
    fM = np.sqrt(np.clip(lamM, 1e-9, None)) / (2 * np.pi)
    m_in = (fM >= 35.0) & (fM <= 700.0)
    _, data = AC.build_fold_data(pkg, fold_key)
    mm = np.load(os.path.join(WP.F.REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
    phm = msh[rs].T; phm = phm / (np.linalg.norm(phm, axis=0, keepdims=True) + 1e-30)
    tgt = (np.asarray(mm["freqs"], float)[rs] * 2 * np.pi) ** 2
    zf, zz = WFW.WF.survey_table(); zmed = float(np.median(zz))

    Kj = jnp.asarray(K_MAP); ash = jnp.asarray(np.asarray(pkg.ash_rows)[live]); phmj = jnp.asarray(phm)
    tgtj = jnp.asarray(tgt); sensj = jnp.asarray(np.asarray(pkg.sens_rows)); QMj = jnp.asarray(QM)
    ks_j = jnp.asarray(ks); zM = jnp.asarray(WFW.zeta_table(fM)); fM_safe = jnp.asarray(np.where(m_in, fM, 1e6))
    m_in_j = jnp.asarray(m_in); zfj = jnp.asarray(zf); zzj = jnp.asarray(zz)
    drv = {d["key"]: jnp.asarray(np.asarray(pkg.drives[d["key"]])) for d in data}
    ydat = {d["key"]: jnp.asarray(d["y"]) for d in data}
    kbn = {d["key"]: jnp.asarray(d["kbins"]) for d in data}
    rowsn = {d["key"]: np.asarray(d["rows"]) for d in data}

    def neglp(rawflat):
        raw = rawflat.reshape(r0, nm)
        phi = jnp.zeros((r, nm)).at[ks_j, jnp.arange(nm)].set(1.0).at[:r0, :].add(AC.TAU * raw)
        phi_n = phi / jnp.sqrt(jnp.sum(phi * phi, 0) + 1e-30)
        ray = jnp.sum(phi_n * (Kj @ phi_n), 0)
        f_new = jnp.sqrt(jnp.clip(ray, 1e-6, None)) / (2 * jnp.pi)
        nll = 0.5 * jnp.sum((tgtj - ray) ** 2 / (0.15 * tgtj) ** 2)               # freq (sig_w2=0.15)
        gp = ash @ phi_n
        mac = jnp.sum(gp * phmj, 0) ** 2 / (jnp.sum(gp * gp, 0) * jnp.sum(phmj * phmj, 0) + 1e-30)
        nll = nll + 0.5 * jnp.sum((1.0 - mac) ** 2 / 0.3 ** 2)                     # MAC (sig_phi=0.3)
        Us_fix = sensj @ QMj; Us_phi = sensj @ phi_n
        f_all = fM_safe.at[ks_j].set(f_new)
        zi = jnp.where(f_all > zfj[-1], zmed, jnp.interp(f_all, zfj, zzj))
        sse, n = 0.0, 0
        for k in ydat:
            Ud_fix = (drv[k] @ QMj) * m_in_j; Ud_phi = drv[k] @ phi_n
            res = (Us_fix * Ud_fix[None, :]).at[:, ks_j].set(Us_phi * Ud_phi[None, :])
            mu = AB.jax_windowed_logH(res[rowsn[k]], f_all, zi, kbn[k])
            rr = ydat[k] - mu; rr = rr - jnp.mean(rr)
            sse = sse + jnp.sum(rr ** 2); n += rr.size
        nll = nll + 0.5 * n * jnp.log(sse / n)                                     # amplitude (profiled sig)
        nll = nll + 0.5 * jnp.sum(rawflat ** 2)                                    # raw ~ N(0,1) prior
        return nll

    val = jax.jit(neglp); grad = jax.jit(jax.grad(neglp))
    rng = np.random.default_rng(20260715)
    best = None
    for s in range(n_starts):
        x0 = np.zeros(r0 * nm) if s == 0 else rng.normal(0, 0.3, r0 * nm)
        res = minimize(lambda x: float(val(jnp.asarray(x))), x0,
                       jac=lambda x: np.asarray(grad(jnp.asarray(x))), method="L-BFGS-B",
                       options=dict(maxiter=120))
        if best is None or res.fun < best.fun:
            best = res
    return best.x.reshape(r0, nm), ks, r0, float(best.fun)


def main():
    pkg = WP.load("A0_wide")
    theta = np.asarray(json.load(open(os.path.join(WS, "out", "theta_map_wide.json")))["theta_map_vec"])
    qoi_w = None
    qp = os.path.join(WS, "out", "qoi_sensor_weights.json")
    if os.path.exists(qp):
        qoi_w = {int(k): v for k, v in json.load(open(qp))["weights"].items()}
    caches = SW.load_caches()
    folds = {}
    for fold in SW.DEV_KEYS:
        mp = os.path.join(OUTD, f"shapes_map_{fold}.npz")
        if os.path.exists(mp):
            z = np.load(mp); raw_mean, ks, r0 = z["raw_mean"], z["ks"], int(z["r0"])
        else:
            raw_mean, ks, r0, nlp = map_fold(pkg, theta, fold)
            np.savez_compressed(mp, raw_mean=raw_mean, ks=ks, r0=r0, nlp=nlp)
        fwd = AC.shapes_forward(pkg, theta, raw_mean, np.asarray(ks, int), r0)
        train_keys = [k for k in SW.DEV_KEYS if k != fold]
        rho, bmasks = SW._train_warp(pkg, theta, train_keys, caches, True, None, fwd)
        fold_mask = None
        if bmasks:
            fm = np.zeros(len(caches[fold]["freqs"]), bool)
            for tk, mmask in bmasks.items():
                if mmask.shape[0] == fm.shape[0]:
                    fm |= mmask
            fold_mask = fm if fm.sum() >= SW.MIN_BAND else None
        gain_db = SW._fold_gain(pkg, theta, train_keys, caches, True, None, fwd)
        bands = SW._grade_bands(pkg, theta, fold, caches[fold], rho, fold_mask, True, None, qoi_w, fwd)
        folds[fold] = {"bands": bands, "rho": round(rho, 4), "gain_dB": round(gain_db, 3),
                       "train_keys": train_keys}
        print(f"  C {fold}: sub200 {bands['sub200'].get('P1p')}", flush=True)
    done = SW.existing("dev")
    if "C" not in done:
        rec = SW._aggregate("C", folds, stage="dev",
                            note="amplitude-trained Beck shape field (theta fixed at MAP, D5); NUTS "
                                 "multimodal/non-converged (fold-1 R-hat 13.95, ESS 2; D13) -> scored at "
                                 "deterministic multi-start shape-field MAP per fold (labeled fallback)")
        with open(SW.SLOG, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print("C", json.dumps(rec["bands_agg"], indent=1))
    # register fold-1 NUTS diagnostic (YELLOW) + note skipped folds
    z = np.load(os.path.join(OUTD, "shapes_m_xpos_990x.npz"), allow_pickle=True)
    m1 = json.loads(str(z["meta"]))
    ndp = os.path.join(WS, "out", "nuts_diagnostics.json")
    reg = json.load(open(ndp)) if os.path.exists(ndp) else {"posteriors": []}
    if "armC_shapes_m_xpos_990x" not in {p["name"] for p in reg["posteriors"]}:
        reg["posteriors"].append({"name": "armC_shapes_m_xpos_990x", "rhat_max": m1["rhat_max"],
                                  "ess_min": m1["ess_min"], "div_frac": m1["div_frac"],
                                  "status": "non_converged_multimodal_representative",
                                  "note": "folds 2-4 NUTS skipped (2.5h/fold, would not converge); scored "
                                          "at deterministic shape-field MAP (D13)"})
        json.dump(reg, open(ndp, "w"), indent=1)
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": "armC_score", "active_s": round(time.time() - t0, 1)}) + "\n")


if __name__ == "__main__":
    main()
