#!/usr/bin/env python3
"""O4: posterior QOI propagation + value of information (D10, contract C10).

AFTER = mount+tray from the NUTS posterior (mount_posterior final tag) x
theta_S from the predecessor posterior x 8 seeds, through the SAME QOI
pipeline as the BEFORE case (out/qoi_results.json joint = prior-mount).

TRUTH QOI = full truth model (6x6 off-diagonal mount, truth thetas) via the
direct dynamic-stiffness apparent mass + FBS, same 8 seeds. Truth params are
REVEALED here (truth_lock.json SHA verified) — the sampler never read them.

VOI metrics: 68/95 % interval-width ratios (after/before), truth coverage
before/after, force-limiting-factor tightening, parameter recovery table.
Output: out/voi_results.json (+ out/posterior_qoi_draws.npz).
"""
import hashlib
import json
import os
import sys
import time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WS = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(WS, "out")
sys.path.insert(0, HERE)
import models  # noqa: E402
import methods  # noqa: E402
import run_qoi  # noqa: E402

N_AFTER = 128
t0 = time.time()


def log(m):
    print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)


def main():
    pres = os.path.join(OUT, "voi_results.json")
    if os.path.exists(pres):
        log("voi_results.json exists, skip")
        return

    # ---- inputs
    post = json.load(open(os.path.join(OUT, "mount_posterior.json")))
    tag = post["final_tag"]
    z = np.load(os.path.join(OUT, f"nuts_mount_{tag}_samples.npz"))
    tm = z["theta_m"]                          # (S, 6) mount multipliers
    tt = z["theta_T"]                          # (S, 5)
    conv = post["convergence"]
    lock = json.load(open(os.path.join(OUT, "truth_lock.json")))
    blob = json.dumps(lock["payload"], sort_keys=True).encode()
    assert hashlib.sha256(blob).hexdigest() == lock["sha256"], \
        "truth_lock SHA mismatch"
    truth = lock["payload"]

    tray = models.build_tray_chain()
    shk = models.ShockSatInterface()
    thetaS_samp, gn = run_qoi.load_posterior()
    EV = run_qoi.envs()
    freqs = EV[0]["freqs"]
    cache = np.load(os.path.join(OUT, "srs_cache.npz"))
    knom = np.array([models.MOUNT_NOMINAL[p] for p in models.MOUNT_PARAMS])

    # ---- AFTER: posterior-mount propagation
    rng = np.random.default_rng(20260611)
    rows = rng.choice(len(tm), size=N_AFTER, replace=False)
    after = {k: [] for k in ("th_unc", "th_cpl", "srs_Qinf", "miles_Qinf")}
    for i, ri in enumerate(rows):
        km = {p: float(knom[j]*tm[ri, j])
              for j, p in enumerate(models.MOUNT_PARAMS)}
        tT = {g: float(tt[ri, gi])
              for gi, g in enumerate(models.TRAY_PARAMS)}
        tS = thetaS_samp[rng.integers(len(thetaS_samp))]
        r = run_qoi.eval_draw(tray, shk, EV, cache, freqs, tS, tT, km)
        after["th_unc"].append(np.median(np.asarray(r["th_unc"]), axis=0))
        after["th_cpl"].append(np.median(np.asarray(r["th_cpl"]), axis=0))
        after["srs_Qinf"].append(np.median(np.asarray(r["srs_Qinf"]), axis=0))
        after["miles_Qinf"].append(np.asarray(r["miles_Qinf"]))
        if (i+1) % 16 == 0:
            log(f"after-draw {i+1}/{N_AFTER}")
    after = {k: np.array(v) for k, v in after.items()}
    np.savez_compressed(os.path.join(OUT, "posterior_qoi_draws.npz"), **after)

    # ---- TRUTH QOI (full truth model, direct evaluation)
    log("truth QOI (direct 6x6-mount evaluation) ...")
    bidx = run_qoi.band_idx(EV[0])
    fb = freqs[bidx]
    chain_nom = models.chain_modal(tray)       # for the dashpot sizing only
    Km6 = np.array(truth["mount_K_full"])
    Mch_t = models.apparent_mass_direct(
        tray, truth["theta_T_true"], None, fb,
        cdiag=chain_nom["cdiag"], Km6=Km6)
    thS_true = np.array([truth["theta_S_true"][g] for g in gn])
    Ys_t = shk.accelerance(fb, thS_true)
    T_cpl_t = np.linalg.solve(np.eye(6)[None] + Mch_t @ Ys_t, Mch_t)
    pk_u, pk_c = [], []
    for e in EV:
        pk_u.append(run_qoi.th_peaks(Mch_t, e, bidx))
        pk_c.append(run_qoi.th_peaks(T_cpl_t, e, bidx))
    truth_qoi = dict(th_unc=np.median(pk_u, axis=0).tolist(),
                     th_cpl=np.median(pk_c, axis=0).tolist(),
                     th_unc_seeds=np.array(pk_u).tolist(),
                     th_cpl_seeds=np.array(pk_c).tolist())
    log(f"truth QOI th_cpl = {np.round(truth_qoi['th_cpl'],1).tolist()} N")

    # ---- BEFORE bands (existing prior-mount joint MC)
    before = json.load(open(os.path.join(OUT, "qoi_results.json")))

    def width(s, lo, hi, d):
        return s[hi][d] - s[lo][d]

    voi = dict(
        label=("SYNTHETIC-TRUTH value-of-information experiment (D10); "
               "HYPOTHETICAL configuration; truth revealed only here"),
        final_tag=tag, convergence=conv,
        convergence_status=("green (gate passed)" if conv["gate_pass"] else
                            "YELLOW: NOT converged - intervals not "
                            "trustworthy"),
        truth_qoi=truth_qoi, axes="xyz")
    table = {}
    for k in ("th_unc", "th_cpl"):
        sb = before[f"joint_{k}"]
        arr = after[k]
        sa = run_qoi.summarize(arr)
        row = dict(before=sb, after=sa)
        for d in range(3):
            w95b = width(sb, "p2_5", "p97_5", d)
            w95a = width(sa, "p2_5", "p97_5", d)
            w68b = width(sb, "p16", "p84", d)
            w68a = width(sa, "p16", "p84", d)
            tq = truth_qoi[k][d]
            row[f"axis_{'xyz'[d]}"] = dict(
                width95_ratio_after_over_before=round(w95a/w95b, 4),
                width68_ratio_after_over_before=round(w68a/w68b, 4),
                truth_covered_before=bool(sb["p2_5"][d] <= tq <= sb["p97_5"][d]),
                truth_covered_after=bool(sa["p2_5"][d] <= tq <= sa["p97_5"][d]),
                truth_N=round(tq, 1),
                after_median_N=round(sa["median"][d], 1),
                before_median_N=round(sb["median"][d], 1))
        table[k] = row
    voi["qoi_table"] = table
    # force-limiting factor tightening
    fl_after = after["th_unc"]/after["th_cpl"]
    voi["force_limiting_factor"] = dict(
        before=before["force_limiting_factor_joint"],
        after=run_qoi.summarize(fl_after),
        truth=[round(u/c, 3) for u, c in
               zip(truth_qoi["th_unc"], truth_qoi["th_cpl"])])
    # parameter recovery (the diagonal model's k = EFFECTIVE stiffness given
    # the off-diagonal truth -- caveat per C10)
    names_m = ["k_tx", "k_ty", "k_tz", "k_rx", "k_ry", "k_rz"]
    rec = []
    for j, nme in enumerate(names_m):
        lo, med, hi = np.percentile(tm[:, j], [2.5, 50, 97.5])
        tr = truth["mount_mult_true"][j]
        rec.append(dict(param=nme, truth_mult=round(tr, 3),
                        post_median=round(float(med), 3),
                        ci95=[round(float(lo), 3), round(float(hi), 3)],
                        covered=bool(lo <= tr <= hi),
                        prior_ci95=[round(float(np.exp(-1.96*1.15)), 3),
                                    round(float(np.exp(1.96*1.15)), 3)]))
    voi["mount_recovery"] = rec
    rec_t = []
    for gi, g in enumerate(models.TRAY_PARAMS):
        lo, med, hi = np.percentile(tt[:, gi], [2.5, 50, 97.5])
        tr = truth["theta_T_true"][g]
        rec_t.append(dict(param=g, truth=round(tr, 3),
                          post_median=round(float(med), 3),
                          ci95=[round(float(lo), 3), round(float(hi), 3)],
                          covered=bool(lo <= tr <= hi)))
    voi["tray_recovery"] = rec_t
    voi["sigma_f"] = dict(median=post["sigma_f_median"],
                          ci95=post["sigma_f_ci95"],
                          injected_noise=0.003,
                          note=("sigma_f above the 0.3 % injected noise floor "
                                "measures the structured model-form "
                                "discrepancy (off-diagonal mount + theta_S "
                                "median-vs-draw gap)"))
    json.dump(voi, open(pres, "w"), indent=1)
    log("voi_results.json written")
    for k in ("th_unc", "th_cpl"):
        for d, ax in enumerate("xyz"):
            r = table[k][f"axis_{ax}"]
            log(f"{k} F{ax}: width95 after/before = "
                f"{r['width95_ratio_after_over_before']}, truth covered "
                f"before={r['truth_covered_before']} "
                f"after={r['truth_covered_after']}")


if __name__ == "__main__":
    main()
