"""Orchestrate the whole synthetic search: MAIN candidates + mandatory ablations + the
deliberate-overfit probe. Logs every config to results_table.csv with reusable-holdout
discipline, selects <=3 gate-passing finalists, writes finalists.json + saves finalist draws.

Reusable-holdout (Thresholdout-style): dev-LPD is jittered by Gaussian noise (sd=THRESH/2) and
an improvement is only REGISTERED if jittered dev > best_registered + THRESH. THRESH = 4.0 LPD
units ~= 1 standard error of the dev-LPD sum under a fresh 4-realization dev set (measured:
per-realization dev-LPD std ~1.97 -> SE of sum ~ 1.97*sqrt(4) ~ 3.9). See packet.md.
"""
import sys, os, time, json, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import jax, jax.numpy as jnp
jax.config.update("jax_enable_x64", True)
from data import load_aligned, coarsen
from fit import run_config, passes_gate
import forward

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
THRESH = 4.0           # reusable-holdout registration threshold (LPD units)
RNG = np.random.RandomState(20260609)
CHAINS, WARM, DRAW = 4, 600, 600

FIELDS = ["query_idx", "timestamp", "stage", "model_form", "disc", "like", "prior_width",
          "tau_f_scale", "tau_phi_scale", "noncentered", "infer_noise", "nmodes",
          "dev_lpd", "dev_lpd_registered", "waic_elpd", "p_waic", "max_rhat", "worst_rhat_var",
          "min_ess", "worst_ess_var", "div_frac", "gate_pass", "registered_improvement",
          "theta1", "theta2", "theta3", "theta4", "qoi_ref", "qoi_heldout"]


def base_cfg(**kw):
    c = dict(disc="freqshape", prior_width=0.3, nmodes=6, like="full", noncentered=True,
             infer_noise=True, tau_f_scale=0.05, tau_phi_scale=0.05)
    c.update(kw); return c


def main_configs():
    """Honest candidate sweep (varied model form / discrepancy / priors / likelihood / noise)."""
    cfgs = []
    cfgs.append(("MAIN", base_cfg(disc="none")))
    cfgs.append(("MAIN", base_cfg(disc="freq")))
    cfgs.append(("MAIN", base_cfg(disc="freqshape")))
    cfgs.append(("MAIN", base_cfg(disc="freqshape", prior_width=0.2)))
    cfgs.append(("MAIN", base_cfg(disc="freqshape", prior_width=0.5)))
    cfgs.append(("MAIN", base_cfg(disc="freqshape", like="freq")))          # feature/peak summary
    cfgs.append(("MAIN", base_cfg(disc="freqshape", infer_noise=False,
                                  sigma_f_fixed=0.005, sigma_phi_fixed=0.02)))
    cfgs.append(("MAIN", base_cfg(disc="freqshape", tau_phi_scale=0.02)))
    cfgs.append(("MAIN", base_cfg(disc="freqshape", tau_phi_scale=0.1)))
    cfgs.append(("MAIN", base_cfg(disc="freq", tau_f_scale=0.1)))
    return cfgs


def ablation_configs():
    """Contract S5: drop discrepancy; vary prior width; coarsen resolution; centered/non-centered."""
    cfgs = []
    cfgs.append(("ABL_dropdisc", base_cfg(disc="none")))                       # drop discrepancy
    cfgs.append(("ABL_prior", base_cfg(prior_width=0.1)))                      # narrow prior
    cfgs.append(("ABL_prior", base_cfg(prior_width=0.7)))                      # wide prior
    cfgs.append(("ABL_coarse", base_cfg(nmodes=4)))                            # coarsen modal res
    cfgs.append(("ABL_coarse", base_cfg(nmodes=3)))
    cfgs.append(("ABL_param", base_cfg(noncentered=False)))                    # centered
    cfgs.append(("ABL_param", base_cfg(noncentered=True)))                     # non-centered (ref)
    return cfgs


def probe_configs():
    """Contract S6 deliberate overfit. Two arms:
    (A) per-realization wild discrepancy (expected to trip the convergence gate);
    (B) ADAPTIVE garden-of-forking-paths: many queries chasing dev-LPD with growing flexibility,
        no self-restraint -> best-dev climbs above true generalization (vault adjudicates).
    """
    cfgs = []
    # Arm A: per-realization additive freq discrepancy, increasingly wild
    for ts in [0.1, 0.2, 0.4, 0.8]:
        cfgs.append(("PROBE_perrealiz", base_cfg(disc="probe", prior_width=0.5, tau_f_scale=ts)))
    # Arm B: adaptive flexibility ramp (each query peeks at dev, keeps best)
    ramp = [
        base_cfg(disc="none"),
        base_cfg(disc="freq"),
        base_cfg(disc="freqshape", tau_phi_scale=0.02),
        base_cfg(disc="freqshape", tau_phi_scale=0.05),
        base_cfg(disc="freqshape", tau_phi_scale=0.1),
        base_cfg(disc="freqshape", tau_phi_scale=0.1, prior_width=0.5),
        base_cfg(disc="freqshape", tau_phi_scale=0.2, prior_width=0.5),
        base_cfg(disc="freqshape", tau_phi_scale=0.2, prior_width=0.7, tau_f_scale=0.1),
        base_cfg(disc="freqshape", tau_phi_scale=0.4, prior_width=0.7, tau_f_scale=0.15),
        base_cfg(disc="freqshape", tau_phi_scale=0.6, prior_width=0.9, tau_f_scale=0.2),
    ]
    for c in ramp:
        cfgs.append(("PROBE_adaptive", c))
    return cfgs


def qoi_for(res, n=100, ngrid=2000):
    th = res["draws"]["theta"]
    idx = np.linspace(0, th.shape[0] - 1, min(n, th.shape[0])).astype(int)
    qr = np.array([float(forward.receptance_peak(jnp.asarray(th[i]), 11, 0, ngrid=ngrid)) for i in idx])
    qh = np.array([float(forward.receptance_peak(jnp.asarray(th[i]), 5, 8, ngrid=ngrid)) for i in idx])
    return float(qr.mean()), float(qr.std()), float(qh.mean()), float(qh.std())


def run():
    t0 = time.time()
    data_full = load_aligned()
    rows, records = [], []
    qidx = 0
    best_registered = -np.inf
    timings = []

    def execute(stage, cfg):
        nonlocal qidx, best_registered
        qidx += 1
        d = coarsen(data_full, cfg["nmodes"]) if cfg["nmodes"] != 6 else data_full
        tc = time.time()
        res = run_config(cfg, d, seed=0, chains=CHAINS, warmup=WARM, draws=DRAW, qoi=False)
        timings.append(time.time() - tc)
        gate = passes_gate(res)
        # reusable holdout: jitter + threshold
        jit = res["dev_lpd"] + RNG.normal(0, THRESH / 2)
        registered = gate and (jit > best_registered + THRESH)
        if registered:
            best_registered = jit
        # QOI only for gate-passers (saves time)
        if gate:
            qr, qrs, qh, qhs = qoi_for(res)
        else:
            qr = qh = float("nan")
        row = dict(query_idx=qidx, timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"), stage=stage,
                   model_form="ff_chain12_4grp_m1", disc=cfg["disc"], like=cfg["like"],
                   prior_width=cfg["prior_width"], tau_f_scale=cfg["tau_f_scale"],
                   tau_phi_scale=cfg["tau_phi_scale"], noncentered=cfg["noncentered"],
                   infer_noise=cfg["infer_noise"], nmodes=cfg["nmodes"],
                   dev_lpd=round(res["dev_lpd"], 3), dev_lpd_registered=round(jit, 3),
                   waic_elpd=round(res["waic_elpd"], 3), p_waic=round(res["p_waic"], 3),
                   max_rhat=round(res["max_rhat"], 4), worst_rhat_var=res["worst_rhat_var"],
                   min_ess=round(res["min_ess"], 1), worst_ess_var=res["worst_ess_var"],
                   div_frac=round(res["div_frac"], 4), gate_pass=gate,
                   registered_improvement=registered,
                   theta1=round(res["theta_mean"][0], 4), theta2=round(res["theta_mean"][1], 4),
                   theta3=round(res["theta_mean"][2], 4), theta4=round(res["theta_mean"][3], 4),
                   qoi_ref=qr, qoi_heldout=qh)
        rows.append(row)
        records.append((stage, cfg, res, gate, registered))
        print(f"[{qidx:2d}] {stage:16s} {cfg['disc']:9s} pw{cfg['prior_width']} "
              f"tphi{cfg['tau_phi_scale']} nm{cfg['nmodes']} like={cfg['like']} "
              f"dev {res['dev_lpd']:7.2f} reg={registered} gate={gate} "
              f"maxR {res['max_rhat']:.3f} minESS {res['min_ess']:.0f} div {res['div_frac']:.3f}")
        return res

    for stage, cfg in main_configs() + ablation_configs() + probe_configs():
        execute(stage, cfg)

    # write results_table.csv
    with open(os.path.join(HERE, "results_table.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader()
        for r in rows:
            w.writerow(r)

    # probe curve (arm B adaptive): best-dev-so-far naive vs thresholdout
    probe_rows = [r for r in rows if r["stage"] == "PROBE_adaptive"]
    best_naive = -np.inf; best_thr = -np.inf; bt = -np.inf
    with open(os.path.join(HERE, "overfit_probe", "probe_curve.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["query", "dev_lpd", "best_dev_naive", "best_dev_thresholdout", "gate_pass"])
        for i, r in enumerate(probe_rows, 1):
            best_naive = max(best_naive, r["dev_lpd"])
            jit = r["dev_lpd"] + RNG.normal(0, THRESH / 2)
            if jit > bt + THRESH:
                bt = jit
            w.writerow([i, r["dev_lpd"], round(best_naive, 3), round(bt, 3), r["gate_pass"]])

    # ---- finalist selection: gate-passing, REGISTERED, distinct disc structures, best dev ----
    cand = [(st, cfg, res) for (st, cfg, res, gate, reg) in records
            if gate and st in ("MAIN", "ABL_dropdisc", "ABL_param")]
    cand.sort(key=lambda x: -x[2]["dev_lpd"])
    finalists = []
    seen = set()
    for st, cfg, res in cand:
        key = (cfg["disc"], cfg["like"], cfg["infer_noise"])
        if key in seen:
            continue
        seen.add(key)
        finalists.append((st, cfg, res))
        if len(finalists) == 3:
            break

    fjson = {"n_configs_tried": qidx, "finalists": []}
    os.makedirs(os.path.join(HERE, "diagnostics"), exist_ok=True)
    for k, (st, cfg, res) in enumerate(finalists):
        qr, qrs, qh, qhs = qoi_for(res, n=200, ngrid=4000)
        # predicted modes (Hz) at posterior mean theta + freq discrepancy d (if present)
        th = np.asarray(res["draws"]["theta"]).mean(0)
        fm, _ = forward.modes(jnp.asarray(th), 6); fm = np.asarray(fm)
        if "d" in res["draws"] and res["draws"]["d"].ndim == 2:
            dm = np.asarray(res["draws"]["d"]).mean(0)
            modes_hz = (fm * np.exp(dm)).tolist()
        else:
            modes_hz = fm.tolist()
        fid = f"F{k+1}_{cfg['disc']}_{cfg['like']}"
        fjson["finalists"].append({
            "id": fid, "pred_theta": [round(x, 5) for x in res["theta_mean"]],
            "pred_qoi_ref": qr, "pred_qoi_heldout": qh,
            "pred_modes_hz": [round(x, 4) for x in modes_hz],
            "dev_score": round(res["dev_lpd"], 3),
            "_meta": {"qoi_ref_sd": qrs, "qoi_heldout_sd": qhs, "stage": st,
                      "disc": cfg["disc"], "like": cfg["like"], "prior_width": cfg["prior_width"],
                      "max_rhat": res["max_rhat"], "min_ess": res["min_ess"],
                      "div_frac": res["div_frac"], "gate_pass": True,
                      "qoi_definition": "peak |H_{out,in}(w)| over 10-600 Hz, m/N, zeta=0.02"}})
        # save draws for diagnostics plots
        np.savez(os.path.join(HERE, "diagnostics", f"{fid}_draws.npz"),
                 **{kk: np.asarray(vv) for kk, vv in res["draws"].items()
                    if kk in ("log_theta", "theta", "sigma_f", "sigma_phi", "tau_f",
                              "tau_phi", "d", "g", "d_z", "g_z")})
        # save per-variable diagnostics
        with open(os.path.join(HERE, "diagnostics", f"{fid}_convergence.json"), "w") as fh:
            json.dump({"rhats": res["rhats"], "esss": res["esss"],
                       "max_rhat": res["max_rhat"], "min_ess": res["min_ess"],
                       "div_frac": res["div_frac"], "n_sampled_scalar": res["n_sampled_scalar"]},
                      fh, indent=2)

    with open(os.path.join(HERE, "finalists.json"), "w") as f:
        json.dump(fjson, f, indent=2)

    runtime = {"active_runtime_s": round(sum(timings), 1),
               "elapsed_wallclock_s": round(time.time() - t0, 1),
               "n_configs": qidx, "note": "active = sum of per-NUTS-fit wall time"}
    with open(os.path.join(HERE, "runtime_search.json"), "w") as f:
        json.dump(runtime, f, indent=2)
    print(f"\nN configs = {qidx}; finalists = {len(finalists)}; "
          f"active {runtime['active_runtime_s']}s wall {runtime['elapsed_wallclock_s']}s")


if __name__ == "__main__":
    run()
