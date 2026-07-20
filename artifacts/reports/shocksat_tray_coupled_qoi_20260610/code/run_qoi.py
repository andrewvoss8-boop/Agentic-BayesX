#!/usr/bin/env python3
"""Main QOI production: method x coupling comparison + uncertainty.

Stages (resumable: each stage skips itself if its output exists; the MC stage
checkpoints every 16 draws):
  nominal : nominal-parameter spectra + QOI (figures' workhorse)  -> out/nominal_spectra.npz, out/qoi_nominal.json
  srscache: SRS of the 8 input seeds on a Q grid (theta-independent) -> out/srs_cache.npz
  mc      : joint MC (N_JOINT draws) + OAT groups (N_OAT each)    -> out/mc_draws.npz, out/qoi_results.json, out/variance_decomposition.json
  sweeps  : deterministic sweeps (mount decades, damping grid,
            placement, record length, adapter mass, source damping) -> out/sweeps.json

QOI per contract C1: per-axis peak |F_d(t)| over the 20 s record.
Methods: time-history (reference; uncoupled + coupled), modal-SRS
(uncoupled by construction; Q in {10,25,50,'informed'}), PSD/Miles 3-sigma
envelope (uncoupled; same Q options). 'informed' = per-mode Q_k = 1/(2 zeta_k)
(the apples-to-apples variant); fixed Q = standard practice.

All states HYPOTHETICAL methods-demo quantities (no hardware validation).
"""
import argparse
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

SEEDS = list(range(8))
Q_GRID = [5, 8, 10, 12, 15, 20, 25, 30, 40, 50, 60, 80, 100]
Q_REPORT = [10, 25, 50, "informed"]
N_JOINT = 128
N_OAT = 64
F_BAND = (10.0, 1000.0)
RNG_SEED = 20260610

t0 = time.time()


def log(m):
    print(f"[{time.time()-t0:7.1f}s] {m}", flush=True)


# ---------------------------------------------------------------- shared bits
def load_posterior():
    d = np.load(os.path.join(models.SHK, "nuts_full_samples.npz"),
                allow_pickle=True)
    gn = [str(g) for g in d["gnames"]]
    return d["theta"], gn


def envs():
    return [methods.synth_input(s) for s in SEEDS]


def band_idx(env):
    """Indices of the (input-carrying) in-band rfft bins. The input is ZERO
    outside [f1, f2] by construction (C7), so transfer matrices only need
    evaluating there -- exact, not an approximation."""
    f = env["freqs"]
    return np.where((f >= env["f1"]) & (f <= env["f2"]))[0]


def transfer_matrices(chain, shk, freqs_band, theta_S=None, zeta_scale=1.0):
    Mch = models.apparent_mass(chain, freqs_band)
    Ys = shk.accelerance(freqs_band, theta_S, zeta_scale=zeta_scale)
    n = 6
    T_cpl = np.linalg.solve(np.eye(n)[None] + Mch @ Ys, Mch)
    return Mch, T_cpl, Ys


def th_peaks(Tmat, env, bidx):
    """time-history peaks (3,) for one (in-band) transfer matrix, one seed."""
    F = np.zeros((len(env["freqs"]), 3), complex)
    F[bidx] = np.einsum("fij,fj->fi", Tmat[:, :3, :3], env["A"][bidx])
    pk, _ = methods.peak_force_time(
        np.concatenate([F, np.zeros_like(F)], axis=1), env["N"])
    return pk


def srs_method(chain, env, Qspec, cache):
    """modal-SRS force (3,). Qspec int or 'informed' (per-mode nearest grid Q)."""
    f = chain["f"]
    use = (f >= F_BAND[0]) & (f <= F_BAND[1])
    fk = f[use]
    G2 = chain["Gamma"][use, :3]**2
    fn = cache["fn"]
    S = cache["S"]                        # (nseed, nQ, nfn, 3)
    qg = np.array(Q_GRID, float)
    si = env["seed"]
    if Qspec == "informed":
        Qk = 1.0/(2*chain["zeta"][use])
        qi = np.array([int(np.argmin(np.abs(qg - q))) for q in Qk])
    else:
        qi = np.full(len(fk), int(np.argmin(np.abs(qg - Qspec))))
    Sk = np.zeros((len(fk), 3))
    for d in range(3):
        for j in range(len(fk)):
            Sk[j, d] = np.interp(np.log(fk[j]), np.log(fn), S[si, qi[j], :, d])
    m_rb = np.diag(chain["M_rb"])[:3]
    m_resid = np.clip(m_rb - G2.sum(axis=0), 0.0, None)
    peak_a = np.max(np.abs(env["a"]), axis=0)
    return np.sqrt(np.sum((G2*Sk)**2, axis=0) + (m_resid*peak_a)**2)


def miles_method(chain, env, Qspec):
    f = chain["f"]
    use = (f >= F_BAND[0]) & (f <= F_BAND[1])
    fk = f[use]
    G2 = chain["Gamma"][use, :3]**2
    W = np.where((fk >= env["f1"]) & (fk <= env["f2"]), env["W0_SI"], 0.0)
    Q = 1.0/(2*chain["zeta"][use]) if Qspec == "informed" \
        else np.full(len(fk), float(Qspec))
    sig2 = np.sum((G2*np.sqrt((np.pi/2)*fk*Q*W)[:, None])**2, axis=0)
    m_rb = np.diag(chain["M_rb"])[:3]
    m_resid = np.clip(m_rb - G2.sum(axis=0), 0.0, None)
    sig = np.sqrt(sig2 + (m_resid*env["grms_SI_target"])**2)
    return 3.0*sig


def eval_draw(tray, shk, EV, cache, freqs, theta_S=None, theta_T=None,
              kmount=None, zeta_struct=0.01, zeta_mount_ref=0.05,
              zetaS_scale=1.0, want_spectra=False):
    """All methods, all seeds, one parameter draw."""
    chain = models.chain_modal(tray, theta_T, kmount,
                               zeta_struct=zeta_struct,
                               zeta_mount_ref=zeta_mount_ref)
    bidx = band_idx(EV[0])
    fb = freqs[bidx]
    Mch, T_cpl, Ys = transfer_matrices(chain, shk, fb, theta_S, zetaS_scale)
    r = dict(chain_f=chain["f"][:10].tolist(),
             m_eff_z=(chain["Gamma"][:, 2]**2)[:10].tolist())
    th_u = np.array([th_peaks(Mch, e, bidx) for e in EV])    # (nseed, 3)
    th_c = np.array([th_peaks(T_cpl, e, bidx) for e in EV])
    r["th_unc"] = th_u
    r["th_cpl"] = th_c
    for Q in Q_REPORT:
        key = f"Q{Q}" if Q != "informed" else "Qinf"
        r[f"srs_{key}"] = np.array([srs_method(chain, e, Q, cache) for e in EV])
        r[f"miles_{key}"] = miles_method(chain, EV[0], Q)  # seed-indep (analytic PSD)
    if want_spectra:
        af = np.zeros((len(fb), 6), complex)
        af[:, :3] = EV[0]["A"][bidx]
        F_u = np.einsum("fij,fj->fi", Mch, af)
        F_c = np.einsum("fij,fj->fi", T_cpl, af)
        r["spectra"] = dict(freqs=fb, F_unc=F_u[:, :3], F_cpl=F_c[:, :3],
                            Mch_diag=np.abs(Mch[:, [0, 1, 2], [0, 1, 2]]),
                            Ys_diag=np.abs(Ys[:, [0, 1, 2], [0, 1, 2]]),
                            chain=chain)
    return r


def summarize(arr, axis=0):
    return dict(median=np.median(arr, axis=axis).tolist(),
                p16=np.percentile(arr, 16, axis=axis).tolist(),
                p84=np.percentile(arr, 84, axis=axis).tolist(),
                p2_5=np.percentile(arr, 2.5, axis=axis).tolist(),
                p97_5=np.percentile(arr, 97.5, axis=axis).tolist())


# ------------------------------------------------------------------- stages
def stage_srscache(EV):
    p = os.path.join(OUT, "srs_cache.npz")
    if os.path.exists(p):
        log("srscache: exists, skip")
        return np.load(p)
    fn = methods.srs_grid(*F_BAND)
    S = np.zeros((len(SEEDS), len(Q_GRID), len(fn), 3))
    for si, e in enumerate(EV):
        for qi, Q in enumerate(Q_GRID):
            for d in range(3):
                S[si, qi, :, d] = methods.srs(e["a"][:, d], e["fs"], fn, Q)
        log(f"srscache: seed {si} done")
    np.savez_compressed(p, fn=fn, S=S, Q_grid=Q_GRID)
    return np.load(p)


def stage_nominal(tray, shk, EV, cache, freqs, theta_med):
    # deterministic per-unit-input transfer magnitudes (figure F4)
    pt = os.path.join(OUT, "nominal_transfers.npz")
    if not os.path.exists(pt):
        bidx = band_idx(EV[0])
        fb = freqs[bidx]
        chain = models.chain_modal(tray)
        Mch, T_cpl, _ = transfer_matrices(chain, shk, fb, theta_med)
        np.savez_compressed(pt, freqs=fb,
                            T_unc_zz=Mch[:, 2, 2], T_cpl_zz=T_cpl[:, 2, 2],
                            T_unc_xx=Mch[:, 0, 0], T_cpl_xx=T_cpl[:, 0, 0],
                            T_unc_yy=Mch[:, 1, 1], T_cpl_yy=T_cpl[:, 1, 1])
        log("nominal: transfers written")
    p = os.path.join(OUT, "nominal_spectra.npz")
    if os.path.exists(p):
        log("nominal: exists, skip")
        return
    r = eval_draw(tray, shk, EV, cache, freqs, theta_S=theta_med,
                  want_spectra=True)
    sp = r.pop("spectra")
    ch = sp.pop("chain")
    np.savez_compressed(
        p, freqs=sp["freqs"], F_unc=sp["F_unc"], F_cpl=sp["F_cpl"],
        Mch_diag=sp["Mch_diag"], Ys_diag=sp["Ys_diag"],
        chain_f=ch["f"], chain_zeta=ch["zeta"],
        chain_meff=ch["Gamma"][:, :3]**2, M_rb=ch["M_rb"],
        a0=EV[0]["a"], seed0=EV[0]["seed"])
    qn = {k: (v.tolist() if isinstance(v, np.ndarray) else v)
          for k, v in r.items()}
    qn["note"] = ("HYPOTHETICAL methods demo; theta_S = predecessor posterior "
                  "median; theta_T = 1; mount nominal (A1). Units N.")
    json.dump(qn, open(os.path.join(OUT, "qoi_nominal.json"), "w"), indent=1)
    log("nominal: done. th_cpl seed-medians [N]: "
        f"{np.median(np.array(qn['th_cpl']), axis=0).round(1).tolist()}")


def draw_params(rng, thetaS_samp, mode):
    """mode in {'joint','S','T','mount'}; returns (theta_S, theta_T, kmount)."""
    tS = thetaS_samp[rng.integers(len(thetaS_samp))] if mode in ("joint", "S") else None
    tT = ({g: float(v) for g, v in zip(models.TRAY_PARAMS,
                                       np.exp(rng.normal(0, 0.25, 5)))}
          if mode in ("joint", "T") else None)
    km = ({p: float(models.MOUNT_NOMINAL[p]*np.exp(rng.normal(0, 1.15)))
           for p in models.MOUNT_PARAMS}
          if mode in ("joint", "mount") else None)
    return tS, tT, km


def stage_mc(tray, shk, EV, cache, freqs, thetaS_samp, theta_med):
    pres = os.path.join(OUT, "qoi_results.json")
    if os.path.exists(pres):
        log("mc: exists, skip")
        return
    ckpt = os.path.join(OUT, "mc_checkpoint.npz")
    plan = ([("joint", i) for i in range(N_JOINT)]
            + [(m, i) for m in ("S", "T", "mount") for i in range(N_OAT)])
    done = {}
    if os.path.exists(ckpt):
        z = np.load(ckpt, allow_pickle=True)
        done = z["done"].item()
        log(f"mc: resuming with {len(done)} draws done")
    keys = None
    for j, (mode, i) in enumerate(plan):
        tag = f"{mode}_{i}"
        if tag in done:
            continue
        mode_id = {"joint": 0, "S": 1, "T": 2, "mount": 3}[mode]
        rng = np.random.default_rng([RNG_SEED, mode_id, i])
        tS, tT, km = draw_params(rng, thetaS_samp, mode)
        if tS is None:
            tS = theta_med            # OAT: non-varied at posterior median/nominal
        r = eval_draw(tray, shk, EV, cache, freqs, tS, tT, km)
        rec = {k: np.asarray(v) for k, v in r.items()
               if k not in ("chain_f", "m_eff_z")}
        rec["chain_f1"] = np.asarray(r["chain_f"][:6])
        if keys is None:
            keys = sorted(rec)
        done[tag] = rec
        if (len(done) % 16 == 0) or (j == len(plan)-1):
            np.savez_compressed(ckpt, done=np.array(done, dtype=object))
            log(f"mc: {len(done)}/{len(plan)} checkpointed")
    np.savez_compressed(ckpt, done=np.array(done, dtype=object))

    # ----- summaries
    def collect(mode, n, key):
        return np.stack([done[f"{mode}_{i}"][key] for i in range(n)])

    res = dict(meta=dict(
        n_joint=N_JOINT, n_oat=N_OAT, seeds=len(SEEDS),
        label="HYPOTHETICAL methods demo (no tray was ever mounted)",
        units="N", qoi="per-axis peak |F_d(t)| over 20 s record (contract C1)"))
    methods_keys = (["th_unc", "th_cpl"]
                    + [f"srs_Q{q}" for q in (10, 25, 50)] + ["srs_Qinf"]
                    + [f"miles_Q{q}" for q in (10, 25, 50)] + ["miles_Qinf"])
    joint = {k: collect("joint", N_JOINT, k) for k in methods_keys}
    # seed-median per draw for parameter-uncertainty summaries
    for k in methods_keys:
        arr = joint[k]
        med_seed = np.median(arr, axis=1) if arr.ndim == 3 else arr
        res[f"joint_{k}"] = summarize(med_seed)
    # method ratios vs the time-history references (per draw, seed-matched)
    ratios = {}
    th_u = joint["th_unc"]                       # (N, nseed, 3)
    th_c = joint["th_cpl"]
    for k in methods_keys[2:]:
        arr = joint[k]
        if arr.ndim == 2:                        # miles: (N,3) no seed axis
            ru = arr[:, None, :]/th_u
            rc = arr[:, None, :]/th_c
        else:
            ru = arr/th_u
            rc = arr/th_c
        ratios[f"{k}_over_th_unc"] = summarize(ru.reshape(-1, 3))
        ratios[f"{k}_over_th_cpl"] = summarize(rc.reshape(-1, 3))
    ratios["th_unc_over_th_cpl"] = summarize((th_u/th_c).reshape(-1, 3))
    res["ratios"] = ratios
    res["force_limiting_factor_joint"] = summarize((th_u/th_c).reshape(-1, 3))
    json.dump(res, open(pres, "w"), indent=1)

    # ----- variance decomposition (OAT main effects, seed-median QOI)
    vd = dict(note=("OAT main-effect approximation: var of seed-median peak "
                    "when ONLY one input group varies (others at nominal/"
                    "posterior-median), as a fraction of the joint variance. "
                    "Fractions need not sum to 1 (interactions ignored)."),
              groups={})
    for k in ("th_unc", "th_cpl"):
        vj = np.var(np.median(joint[k], axis=1), axis=0)
        row = {}
        for mode in ("S", "T", "mount"):
            arr = collect(mode, N_OAT, k)
            vo = np.var(np.median(arr, axis=1), axis=0)
            row[mode] = (vo/vj).tolist()
        # seed/aleatory share: variance over seeds at nominal-ish (joint draws'
        # per-draw seed variance, averaged) / joint variance
        v_seed = np.mean(np.var(joint[k], axis=1), axis=0)
        row["seed_aleatory"] = (v_seed/vj).tolist()
        vd["groups"][k] = row
        vd[f"joint_var_{k}"] = vj.tolist()
    # mount-vs-rest dominance verdict per axis (coupled time-history)
    mt = np.array(vd["groups"]["th_cpl"]["mount"])
    rest = np.array(vd["groups"]["th_cpl"]["S"]) + np.array(vd["groups"]["th_cpl"]["T"])
    vd["mount_dominated_axes"] = (mt > rest).tolist()
    json.dump(vd, open(os.path.join(OUT, "variance_decomposition.json"), "w"),
              indent=1)
    log("mc: summaries written")


def stage_sweeps(tray, shk, EV, cache, freqs, theta_med):
    p = os.path.join(OUT, "sweeps.json")
    if os.path.exists(p):
        log("sweeps: exists, skip")
        return
    out = {}

    def qoi_of(r):
        return dict(
            th_unc=np.median(r["th_unc"], axis=0).tolist(),
            th_cpl=np.median(r["th_cpl"], axis=0).tolist(),
            srs_Qinf=np.median(r["srs_Qinf"], axis=0).tolist(),
            miles_Qinf=np.asarray(r["miles_Qinf"]).tolist(),
            chain_f=r["chain_f"][:6])

    # mount decade sweep (common multiplier on all 6)
    sw = []
    for mult in [0.05, 0.158, 0.5, 1.0, 1.58, 5.0, 15.8, 50.0, 158.0, 500.0]:
        km = {q: models.MOUNT_NOMINAL[q]*mult for q in models.MOUNT_PARAMS}
        r = eval_draw(tray, shk, EV, cache, freqs, theta_med, kmount=km)
        sw.append(dict(mult=mult, k_tz=km["k_tz"], **qoi_of(r)))
        log(f"sweeps: mount x{mult} f1={r['chain_f'][0]:.1f} Hz")
    out["mount_multiplier"] = sw

    # damping grid
    sw = []
    for zs in (0.005, 0.01, 0.02):
        for zm in (0.02, 0.05, 0.10):
            r = eval_draw(tray, shk, EV, cache, freqs, theta_med,
                          zeta_struct=zs, zeta_mount_ref=zm)
            sw.append(dict(zeta_struct=zs, zeta_mount=zm, **qoi_of(r)))
    out["damping_grid"] = sw

    # source damping x0.5 / x2
    sw = []
    for zsc in (0.5, 1.0, 2.0):
        r = eval_draw(tray, shk, EV, cache, freqs, theta_med, zetaS_scale=zsc)
        sw.append(dict(zetaS_scale=zsc, **qoi_of(r)))
    out["source_damping"] = sw

    # alternate placement (top-plate edge node)
    alt = json.load(open(os.path.join(OUT, "mount_node.json")))["alt_edge_gid"]
    shk_alt = models.ShockSatInterface(node_gid=alt)
    r = eval_draw(tray, shk_alt, EV, cache, freqs, theta_med)
    out["placement_alt_edge"] = dict(gid=alt, **qoi_of(r))

    # record length / df probe (T=10 s, 4 seeds)
    EV10 = [methods.synth_input(s, T=10.0) for s in SEEDS[:4]]
    f10 = EV10[0]["freqs"]
    r = eval_draw(tray, shk, EV10, cache, f10, theta_med)
    out["record_T10s"] = dict(note="df doubled to 0.1 Hz; ONLY time-history "
                              "peaks reported (SRS cache is for the 20 s "
                              "records, so srs/miles outputs are not valid "
                              "for this probe)",
                              th_unc=np.median(r["th_unc"], axis=0).tolist(),
                              th_cpl=np.median(r["th_cpl"], axis=0).tolist())

    # adapter mass probe (+0.5 kg at base point translations)
    tray2 = dict(tray)
    M2 = tray["M"].copy()
    ibt = tray["ibase"][:3]
    M2[ibt, ibt] += 0.5
    tray2["M"] = M2
    r = eval_draw(tray2, shk, EV, cache, freqs, theta_med)
    out["adapter_mass_0p5kg"] = qoi_of(r)

    json.dump(out, open(p, "w"), indent=1)
    log("sweeps: done")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="all",
                    choices=["all", "nominal", "srscache", "mc", "sweeps"])
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    log("build tray ...")
    tray = models.build_tray_chain()
    log("load ShockSat interface ...")
    shk = models.ShockSatInterface()
    EV = envs()
    freqs = EV[0]["freqs"]
    thetaS_samp, gn = load_posterior()
    assert gn == shk.gnames, "gname order mismatch"
    theta_med = np.median(thetaS_samp, axis=0)
    cache = stage_srscache(EV)
    if args.stage in ("all", "nominal"):
        stage_nominal(tray, shk, EV, cache, freqs, theta_med)
    if args.stage in ("all", "mc"):
        stage_mc(tray, shk, EV, cache, freqs, thetaS_samp, theta_med)
    if args.stage in ("all", "sweeps"):
        stage_sweeps(tray, shk, EV, cache, freqs, theta_med)
    log("run_qoi done")


if __name__ == "__main__":
    main()
