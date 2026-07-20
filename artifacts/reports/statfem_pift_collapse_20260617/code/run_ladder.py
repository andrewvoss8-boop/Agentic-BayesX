#!/usr/bin/env python3
"""The COLLAPSE N-LADDER driver (NEW file; imports the copied core/nuts_arms/predict, edits none).

Sweeps observation density N = N_freq · N_sensor on a geometric ladder and, per arm (M0 naive / M1 iid /
M3 orthogonal-Schneider; M2 optional), records the σ_d posterior width, the identified-θ width, and a
sharpness-aware held-out QOI score. Resumable: one JSON per cell; skips finished cells.

Densification = the SAME underlying truth sampled denser (not a new truth per N). We generate the truth once on
a FINE master grid (geomspace 45–260 Hz, NMAX points) — FEM(θ_truth) × ONE fixed Schneider correlated-complex
field + fixed measurement noise — and every ladder cell uses an EXACT DECIMATED SUBSET of that master grid
(NMAX % N_freq == 0). So "more frequency points" means resolving the same fixed truth more finely, which is
exactly the PIFT "more collocation points" limit (card §2/§5). The model FRF is evaluated analytically at the
cell grid.

  primary axis  : N_freq ∈ {20,40,80,160,320,640}  (160 = modal-twin default; 320/640 = "beyond" by densifying)
  secondary axis: N_sensor ∈ {3,6,12,18}            (held-out evaluation set FIXED across the sensor ladder)
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WS = HERE.parent
OUT = WS / "out"
OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(HERE))

import core            # noqa: E402  (copied, unedited)
import nuts_arms as na  # noqa: E402
import predict as pr   # noqa: E402
import scoring as sc   # noqa: E402

NMAX = 640                      # master fine grid (all ladder N_freq divide 640)
OBS_MAX = 18                    # observed pool size (sensor ladder draws subsets)
INFORMED_GROUPS = ["bottom_box", "top_box", "plates", "cross_beam"]   # modal-twin 4/9 identifiable set
SEED_TRUTH = 20260617
# the controlled known-model-form-error truth (combo "mixed": identifiable + unidentifiable θ bias)
TRUTH_COMBO = 3


def layout(model):
    """Fixed drive, fixed observed-pool (18, spread along z), fixed held-out set. Returns indices into
    `all_ch = pool + heldout` so any observed subset + the held-out set are columns of one master truth."""
    ch = core.select_channels(model, n_observed=OBS_MAX)
    pool = list(ch["observed"])              # 18 channels spread along z
    held = list(ch["heldout"])               # fixed held-out evaluation set
    drive = ch["drive"]
    all_ch = pool + held
    return drive, pool, held, all_ch


def make_master(model, drive, all_ch, theta_truth, zeta=core.ZETA_NOM):
    """FEM(θ_truth) × ONE fixed Schneider field + fixed meas noise on the NMAX master grid. (NMAX, Nall)."""
    master_f = core.freq_grid(n=NMAX)
    coords_all = model.dof_xyz[np.asarray(all_ch)]
    rng_f = np.random.default_rng(SEED_TRUTH)
    H = core.frf_np(model, master_f, theta_truth, all_ch, drive, zeta=zeta)
    field = core.schneider_field(master_f, coords_all, rng_f)        # the genuine model-form error
    truth_lm = np.log(np.abs(H * field))                            # (NMAX, Nall) clean-truth log|H|
    rng_m = np.random.default_rng(SEED_TRUTH + 1)
    meas_lm = truth_lm + rng_m.normal(0, core.SIGMA_MEAS, truth_lm.shape)
    return master_f, truth_lm, meas_lm


def cell_grids(n_freq, n_sensor, pool, held):
    step = NMAX // n_freq
    assert step * n_freq == NMAX, f"N_freq {n_freq} must divide {NMAX}"
    fidx = np.arange(0, NMAX, step)                                  # exact decimated subset
    sel = np.linspace(0, len(pool) - 1, n_sensor).astype(int)
    observed = [pool[i] for i in sel]
    obs_cols = [i for i, c in enumerate(pool) if c in set(observed)]  # columns into all_ch (pool first)
    ho_cols = list(range(len(pool), len(pool) + len(held)))
    return fidx, observed, obs_cols, ho_cols


def theta_widths(theta_rows):
    wid = {r["group"]: (r["hi"] - r["lo"]) for r in theta_rows}
    w_id = float(np.mean([wid[g] for g in INFORMED_GROUPS]))
    w_all = float(np.mean(list(wid.values())))
    return w_id, w_all, {g: float(wid[g]) for g in INFORMED_GROUPS}


def run_cell(model, master_f, truth_lm, meas_lm, drive, pool, held, theta_truth,
            n_freq, n_sensor, arm, nwarm, nsamp, nchain, leg, zeta=core.ZETA_NOM):
    fidx, observed, obs_cols, ho_cols = cell_grids(n_freq, n_sensor, pool, held)
    freqs = master_f[fidx]
    truth_obs = truth_lm[np.ix_(fidx, obs_cols)]
    truth_ho = truth_lm[np.ix_(fidx, ho_cols)]
    meas_obs = meas_lm[np.ix_(fidx, obs_cols)]
    t0 = time.time()
    samples, diag, _ = na.run_arm(arm, model, freqs, meas_obs, observed, drive, zeta=zeta,
                                  num_warmup=nwarm, num_samples=nsamp, num_chains=nchain,
                                  seed=SEED_TRUTH + n_freq + n_sensor)
    ctx = pr.PredCtx(model, freqs, observed, held, drive, arm, zeta=zeta)
    res = pr.predict_cell(ctx, samples, truth_ho, meas_obs, core.GNAMES, theta_truth, INFORMED_GROUPS)
    score = sc.score_cell(ctx, samples, truth_ho, meas_obs)
    w_id, w_all, w_groups = theta_widths(res["theta"])
    sd = res["sigma_d"]
    sd_width = float(sd["hi"] - sd["lo"])
    np.savez_compressed(OUT / f"samples_{leg}_{arm}_nf{n_freq}_ns{n_sensor}.npz",
                        log_theta=samples["log_theta"].astype(np.float32),
                        sigma_d=np.asarray(samples.get("sigma_d", np.zeros(len(samples["log_theta"])))).astype(np.float32))
    rec = {"leg": leg, "arm": arm, "N_freq": int(n_freq), "N_sensor": int(n_sensor),
           "N": int(n_freq * n_sensor), "axis_band_hz": list(core.BAND),
           "nuts": diag,
           "converged": bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02),
           "sigma_d": {"lo": sd["lo"], "med": sd["med"], "hi": sd["hi"], "width": sd_width, "fixed": sd.get("fixed", False)},
           "theta_width_identified": w_id, "theta_width_all": w_all, "theta_width_groups": w_groups,
           "score": score,
           "heldout_coverage": res["heldout_coverage"],
           "runtime_s": round(time.time() - t0, 2)}
    return rec


def parse_cells(args):
    nf = [int(x) for x in args.nfreq.split(",")]
    ns = [int(x) for x in args.nsensor.split(",")]
    arms = args.arms.split(",")
    # cartesian over (nf,ns) only where one axis is at its anchor (a +-shaped ladder, not full grid)
    cells = []
    for a in arms:
        for f in nf:
            cells.append((f, args.ns_anchor, a))           # frequency ladder (sensor fixed)
        for s in ns:
            if s != args.ns_anchor:
                cells.append((args.nf_anchor, s, a))        # sensor ladder (freq fixed)
    # de-dup, then order by ascending N (cheap first) so low-N-all-arms land first (early trend read)
    seen = set(); uniq = []
    for c in cells:
        if c not in seen:
            seen.add(c); uniq.append(c)
    uniq.sort(key=lambda c: (c[0] * c[1], c[2]))
    return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--leg", default="synth")
    ap.add_argument("--nfreq", default="20,40,80,160,320")
    ap.add_argument("--nsensor", default="3,6,12,18")
    ap.add_argument("--nf-anchor", type=int, default=160)
    ap.add_argument("--ns-anchor", type=int, default=6)
    ap.add_argument("--arms", default="M0,M1,M3")
    ap.add_argument("--only", default="")     # e.g. "M1:20:6,M3:320:6" to run a P1 probe subset
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    nwarm, nsamp, nchain = (150, 150, 1) if args.smoke else (1000, 1000, 4)
    model = core.load_model()
    drive, pool, held, all_ch = layout(model)
    theta_truth = core.theta_vector(core.COMBOS[TRUTH_COMBO]["theta"])
    master_f, truth_lm, meas_lm = make_master(model, drive, all_ch, theta_truth)

    # config (synthetic provenance)
    cfg_path = OUT / "config.json"
    if not cfg_path.exists() and args.leg == "synth":
        json.dump({"testbed": "plain_shocksat_9group", "uses_tray": False,
                   "source": "reduced_blocks.npz COPIED from companion/modal-twin (D1/D4)",
                   "leg": "synthetic", "truth_combo": core.COMBOS[TRUTH_COMBO]["name"],
                   "theta_truth": {g: float(theta_truth[i]) for i, g in enumerate(core.GNAMES)},
                   "known_model_form_error": "injected Schneider correlated-complex field (freq×space) + θ bias; "
                                             "NOT representable by any θ scaling",
                   "band_hz": list(core.BAND), "nmax_master": NMAX, "drive_dof": drive,
                   "observed_pool": pool, "heldout": held, "informed_groups": INFORMED_GROUPS,
                   "sigma_meas": core.SIGMA_MEAS,
                   "schneider": {"len_logf": core.DISC_LEN_LOGF, "len_z": core.DISC_LEN_Z,
                                 "std_lo": core.DISC_STD_LO, "std_hi": core.DISC_STD_HI},
                   "inference_uses_true_corr_lengths": True},
                  open(cfg_path, "w"), indent=1)

    if args.only:
        cells = []
        for tok in args.only.split(","):
            a, f, s = tok.split(":")
            cells.append((int(f), int(s), a))
    else:
        cells = parse_cells(args)

    t_all = time.time()
    for (f, s, arm) in cells:
        p = OUT / f"cell_{args.leg}_{arm}_nf{f}_ns{s}.json"
        if p.exists():
            print(f"[skip] {p.name}", flush=True); continue
        print(f"[run ] leg={args.leg} arm={arm} N_freq={f} N_sensor={s} N={f*s} ...", flush=True)
        rec = run_cell(model, master_f, truth_lm, meas_lm, drive, pool, held, theta_truth,
                       f, s, arm, nwarm, nsamp, nchain, args.leg)
        json.dump(rec, open(p, "w"), indent=1)
        sd = rec["sigma_d"]; scr = rec["score"]
        print(f"       done {p.name}  rhat={rec['nuts']['max_rhat']:.3f} ess={rec['nuts']['min_ess']:.0f} "
              f"div={rec['nuts']['div_frac']:.3f} | sd_w={sd['width']:.3f} th_w_id={rec['theta_width_identified']:.3f} "
              f"| IS={scr['interval_score_db']:.2f}dB cov={scr['coverage']:.2f} w={scr['width_db']:.1f}dB "
              f"t={rec['runtime_s']}s", flush=True)
    print(f"ALL CELLS in {time.time()-t_all:.1f}s", flush=True)


if __name__ == "__main__":
    main()
