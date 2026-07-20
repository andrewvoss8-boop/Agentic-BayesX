#!/usr/bin/env python3
"""Card C Phase 3 -- quality threshold tau as a SWEPT variable (Andrew D9). For the working modal/Beck twin the
'peak/band-keep' knob is the matched-mode QUALITY threshold: which .ash<->FEM mode pairs to trust by their MAC
(modal assurance criterion, 0=orthogonal 1=identical shapes). We sweep tau over the kept-mode set and report which
tau MAXIMIZES the held-out proper score (minimizes interval score) for the hardened Beck twin (inferred shapes +
measured damping), peak |H| AND band-GRMS, across the 25-split MC.

tau levels:  full20 (all matched) | mac>=0.5 | mac>=0.7 | top6 (6 highest-MAC modes)
Each tau = its own Beck calibration (split-independent, cached). Output: out/tau_sweep_summary.json.
"""
import json
import sys
import time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import realfrf as rf
import modal_beck_full as M

WS = Path(__file__).resolve().parent.parent


def tau_levels():
    R = rf.load_reduced()
    import modal_ash_mac as am
    pairs = am.load_ash_matched(R)["pairs"]                       # list of (ash_r, fem_k, mac)
    mac = np.array([p[2] for p in pairs])
    order = np.argsort(-mac)
    return {
        "full20": list(range(len(pairs))),
        "mac_ge_0.5": [i for i in range(len(pairs)) if mac[i] >= 0.5],
        "mac_ge_0.7": [i for i in range(len(pairs)) if mac[i] >= 0.7],
        "top6": list(order[:6]),
    }, mac


def run(n_splits=25, n_draws=120, warmup=800, samples=800, chains=4):
    t0 = time.time(); levels, mac = tau_levels()
    res = {}
    for name, idx in levels.items():
        cal = M.calibrate(pairs_idx=idx, cache_tag=f"tau_{name}", warmup=warmup, samples=samples, chains=chains)
        eta = M.per_mode_eta(cal, True)
        pk, bd, cp, cb = [], [], [], []
        for s in range(n_splits):
            sc = M.score_split(cal, seed=s, n_draws=n_draws, eta_measured=eta)["INFER_measured"]
            pk.append(sc["peak"]["interval_score"]); bd.append(sc["band"]["interval_score"])
            cp.append(sc["peak"]["coverage"]); cb.append(sc["band"]["coverage"])
        res[name] = {"n_modes": cal["nm"], "mac_min": float(min(mac[i] for i in idx)),
                     "mac_mean": float(np.mean([mac[i] for i in idx])),
                     "calib_converged": cal["diag"]["converged"], "calib_rhat": cal["diag"]["max_rhat"],
                     "peak_IS_median": float(np.median(pk)), "peak_cov_median": float(np.median(cp)),
                     "band_IS_median": float(np.median(bd)), "band_cov_median": float(np.median(cb))}
        print(f"  tau {name:11s} ({cal['nm']:2d} modes, MAC>={res[name]['mac_min']:.2f}): conv "
              f"{cal['diag']['converged']} | peak IS {res[name]['peak_IS_median']:.0f} cov "
              f"{res[name]['peak_cov_median']:.2f} | band IS {res[name]['band_IS_median']:.0f}", flush=True)
        (WS / "out").mkdir(exist_ok=True)
        (WS / "out" / "tau_sweep_summary.json").write_text(json.dumps(
            {"deliverable": "Phase3_tau_sweep (matched-mode MAC quality threshold)", "n_splits": n_splits,
             "levels": res, "runtime_s": time.time() - t0}, indent=2))
    best_pk = min(res, key=lambda k: res[k]["peak_IS_median"])
    best_bd = min(res, key=lambda k: res[k]["band_IS_median"])
    print(f"\nTAU SWEEP DONE. Best held-out PEAK IS: tau={best_pk} ({res[best_pk]['peak_IS_median']:.0f}); "
          f"best BAND IS: tau={best_bd} ({res[best_bd]['band_IS_median']:.0f}).")
    return res


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 25)
