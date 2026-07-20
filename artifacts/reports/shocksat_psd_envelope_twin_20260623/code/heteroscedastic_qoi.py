#!/usr/bin/env python3
"""Phase C — does a TWO-POPULATION (hard-region vs rest) discrepancy honestly TIGHTEN the held-out CI?

Diagnostic (discrepancy_diagnostic.json): the 8 a-priori-hard accels (impact face/bulkheads/bolted joint/strut/
dish, Card D) average ~17 dB peak error vs ~6.5 dB for the rest -- the residual is predictable by the KNOWN
hard-region flag (NOT by generic DR/snap/z). A single pooled iid lognormal sigma_QOI must inflate EVERY channel's
CI to cover the hard tails. Here we estimate the QOI discrepancy SEPARATELY for hard vs rest OBSERVED channels and
transfer by the channel's hard/rest flag -> the ~90% well-modeled channels get a TIGHT CI, only the 8 hard stay WIDE.
The hard flag is prior structural knowledge (set before seeing held-out amplitudes); held-out coverage keeps it honest.

Mean model = L5 freq calibration + uniform zeta=1% + window (ARM1, our best). Compares POOLED vs HARD/REST
discrepancy on the SAME split. Output: out/heteroscedastic_qoi_seed<seed>.json.
"""
from __future__ import annotations
import json, sys, time
from types import SimpleNamespace
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_feature as mf
import heldout_qoi as hq
import dampcorr_qoi as dc
import score as SC

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
HARD = {4, 27, 38, 40, 52, 69, 92, 98}


def run(seed=0, obs_frac=0.6, n_draws=400, warmup=1000, samples=1000, chains=4, write=True):
    t0 = time.time()
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    fr = meas["freqs"]; fb = (fr >= rf.BAND[0]) & (fr <= rf.BAND[1]); freqs = fr[fb]
    didx = {d: i for i, d in enumerate(meas["daq"])}
    tau = -(rf.PROC["N"] - 1) / (rf.FS * np.log(rf.PROC["exp_end"]))
    eta = np.full(R.A.shape[1], 2.0 * rf.ZETA_NOM)

    dr = np.array([meas["dyn_range"][didx[d]] for d in ch.daq])
    elig = np.where(dr >= hq.DR_MIN)[0]
    rng = np.random.default_rng(seed); perm = rng.permutation(elig)
    n_obs = int(round(obs_frac * len(perm)))
    obs_pos = np.sort(perm[:n_obs]); ho_pos = np.sort(perm[n_obs:])
    obs_daqs = [ch.daq[p] for p in obs_pos]; ho_daqs = [ch.daq[p] for p in ho_pos]
    hard_obs = np.array([1 if d in HARD else 0 for d in obs_daqs])
    hard_ho = np.array([1 if d in HARD else 0 for d in ho_daqs])

    meas_f, _ = mf.extract_measured_modes(meas, SimpleNamespace(daq=obs_daqs))
    pairs, _ = mf.match(R, meas_f)
    obs_mode_idx = np.array([p[0] for p in pairs]); obs_w_hz = np.array([p[1] for p in pairs])
    theta_post, sigw2, cdiag = mf.calibrate_modal(R, obs_mode_idx, obs_w_hz,
                                                  seed=20260617, warmup=warmup, samples=samples, chains=chains)
    Nd = theta_post.shape[0]; sub = np.linspace(0, Nd - 1, min(Nd, n_draws)).astype(int); thsub = theta_post[sub]

    obs_rows = ch.rows[obs_pos]; ho_rows = ch.rows[ho_pos]
    all_rows = np.vstack([obs_rows, ho_rows]); n_o = len(obs_pos); n_ho = len(ho_pos)
    lm = dc.fem_logmag_batch_permode(R, freqs, thsub, all_rows, ch.drive_row, eta, tau)
    lm_obs = lm[:, :, :n_o]; lm_ho = lm[:, :, n_o:]
    tru_obs = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in obs_daqs])) + 1e-300).T
    tru_ho = np.log(np.abs(np.array([meas["H"][didx[d]][fb] for d in ho_daqs])) + 1e-300).T
    wflat = np.array([meas["weight"][didx[d]][fb] for d in obs_daqs]).T.ravel()

    peak_ob = np.zeros((len(sub), n_o)); peak_ho = np.zeros((len(sub), n_ho))
    for j in range(len(sub)):
        c = hq.wmedian((tru_obs - lm_obs[j]).ravel(), wflat)
        po = np.exp(lm_obs[j] + c); ph = np.exp(lm_ho[j] + c)
        for k in range(n_o):
            peak_ob[j, k] = hq.SC_qoi_peak(po[:, k])
        for k in range(n_ho):
            peak_ho[j, k] = hq.SC_qoi_peak(ph[:, k])
    peak_tru_ob = np.array([hq.SC_qoi_peak(np.exp(tru_obs[:, k])) for k in range(n_o)])
    peak_tru_ho = np.array([hq.SC_qoi_peak(np.exp(tru_ho[:, k])) for k in range(n_ho)])

    res_ob = np.log(np.median(peak_ob, axis=0) + 1e-300) - np.log(peak_tru_ob + 1e-300)   # observed residuals
    sig_pool = float(np.std(res_ob))
    sig_hard = float(np.std(res_ob[hard_obs == 1])) if (hard_obs == 1).sum() >= 2 else sig_pool
    sig_rest = float(np.std(res_ob[hard_obs == 0])) if (hard_obs == 0).sum() >= 2 else sig_pool

    def score_with(sig_ho_vec):
        drng = np.random.default_rng(seed + 7)
        pk_d = peak_ho * np.exp(drng.normal(0.0, 1.0, peak_ho.shape) * sig_ho_vec[None, :])
        sp = [SC.score_qoi(pk_d[:, k], peak_tru_ho[k]) for k in range(n_ho)]
        agg = hq.aggregate(sp)
        cov = np.array([s["covered"] for s in sp]); iv = np.array([s["interval_score"] for s in sp])
        return {"overall": agg,
                "rest": {"coverage": float(cov[hard_ho == 0].mean()), "interval_mean": float(iv[hard_ho == 0].mean()),
                         "n": int((hard_ho == 0).sum())},
                "hard": {"coverage": float(cov[hard_ho == 1].mean()) if (hard_ho == 1).sum() else None,
                         "interval_mean": float(iv[hard_ho == 1].mean()) if (hard_ho == 1).sum() else None,
                         "n": int((hard_ho == 1).sum())}}

    pooled = score_with(np.full(n_ho, sig_pool))
    twopop = score_with(np.where(hard_ho == 1, sig_hard, sig_rest))

    rec = {"deliverable": "Phase-C two-population (hard vs rest) discrepancy -> does it tighten the CI honestly?",
           "split_seed": seed, "n_observed": n_o, "n_heldout": n_ho,
           "n_obs_hard": int(hard_obs.sum()), "n_ho_hard": int(hard_ho.sum()),
           "sigma_pooled": sig_pool, "sigma_hard": sig_hard, "sigma_rest": sig_rest,
           "calib_converged": bool(cdiag["converged"]),
           "POOLED_discrepancy": pooled, "TWOPOP_discrepancy": twopop, "runtime_s": time.time() - t0}
    if write:
        OUT.mkdir(exist_ok=True)
        (OUT / f"heteroscedastic_qoi_seed{seed:02d}.json").write_text(json.dumps(rec, indent=2))
    print(f"seed {seed}: obs {n_o} (hard {int(hard_obs.sum())}) / ho {n_ho} (hard {int(hard_ho.sum())}); "
          f"sig pool {sig_pool:.2f} hard {sig_hard:.2f} rest {sig_rest:.2f}")
    for tag, s in (("POOLED", pooled), ("TWOPOP", twopop)):
        o = s["overall"]["peak"]; rr = s["rest"]; hh = s["hard"]
        print(f"  {tag:7s} overall cover {o['coverage_frac']:.2f} int {o['interval_score_mean']:.0f} | "
              f"REST cover {rr['coverage']:.2f} int {rr['interval_mean']:.0f} (n{rr['n']}) | "
              f"HARD cover {hh['coverage']} int {hh['interval_mean']} (n{hh['n']})")
    print(f"  runtime {rec['runtime_s']:.0f}s")
    return rec


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    run(seed=seed)
