#!/usr/bin/env python3
"""Monte-Carlo over train/held-out SPLITS for the WORKING method (Card A next-action #5, decisions_log D16).

Card §7 asks for score DISTRIBUTIONS over Monte-Carlo configs. The randomizable axis on this data is the
observed/held-out channel SPLIT only -- impact-location and hit collapse to ONE each (D2, labeled reduction:
1 impact, 1 hit). We run the MC on the CONVERGED method (L5 modal-feature calibration + marginal QOI discrepancy,
heldout_qoi.py); the whole-FRF arms (M0-M3) are non-converged + give useless QOI (scores_summary.json) so an MC
over them is omitted (established at 1 split).

For each of N>=25 seeds: fresh channel split -> L5 NUTS calibration (on observed modes) -> held-out-sensor peak-|H|
and band-GRMS scored. Collect distributions of coverage / interval(Winkler) / CRPS / z-std. Output: out/mc_summary.json
(n_configs, per_arm score distributions, per_split rows, L5-convergence fraction).
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import heldout_qoi as hq

WS = Path(__file__).resolve().parent.parent


def dist(vals):
    v = np.asarray(vals, float)
    return {"mean": float(np.mean(v)), "med": float(np.median(v)),
            "p5": float(np.percentile(v, 5)), "p95": float(np.percentile(v, 95)),
            "min": float(np.min(v)), "max": float(np.max(v))}


def run(n_splits=25, warmup=600, samples=600, chains=4, n_draws=300, force=False):
    outp = WS / "out" / "mc_summary.json"
    if outp.exists() and not force:
        print(f"[skip] {outp.name}"); return json.loads(outp.read_text())
    t0 = time.time()
    per_split, conv_flags = [], []
    collect = {v: {q: {m: [] for m in ("coverage", "interval", "crps", "zstd")} for q in ("peak", "band")}
               for v in ("theta_plus_qoi_discrepancy", "theta_only")}
    for s in range(n_splits):
        rec = hq.run(seed=s, n_draws=n_draws, warmup=warmup, samples=samples, chains=chains, write=False)
        cdiag = rec["calibration"]["diag"]
        conv_flags.append(bool(cdiag["converged"]))
        row = {"seed": s, "n_obs": rec["n_observed"], "n_ho": rec["n_heldout"],
               "calib_rhat": cdiag["max_rhat"], "calib_converged": bool(cdiag["converged"])}
        for v, key in (("theta_plus_qoi_discrepancy", "scores_theta_plus_qoi_discrepancy"),
                       ("theta_only", "scores_theta_only")):
            for q in ("peak", "band"):
                a = rec[key][q]
                collect[v][q]["coverage"].append(a["coverage_frac"])
                collect[v][q]["interval"].append(a["interval_score_mean"])
                collect[v][q]["crps"].append(a["crps_mean"])
                collect[v][q]["zstd"].append(a["z_std"])
                if v == "theta_plus_qoi_discrepancy":
                    row[f"{q}_cov"] = a["coverage_frac"]; row[f"{q}_is"] = a["interval_score_mean"]
        per_split.append(row)
        print(f"  split {s:2d}: calib R-hat {cdiag['max_rhat']:.3f} conv {cdiag['converged']} | "
              f"+disc PEAK cov {collect['theta_plus_qoi_discrepancy']['peak']['coverage'][-1]:.2f} "
              f"IS {collect['theta_plus_qoi_discrepancy']['peak']['interval'][-1]:.3g}", flush=True)

    per_arm = {v: {q: {m: dist(collect[v][q][m]) for m in ("coverage", "interval", "crps", "zstd")}
                   for q in ("peak", "band")} for v in collect}
    rec_out = {"study": "statfem_real_validation_20260617", "deliverable": "MC_heldout_QOI_distributions",
               "method": "L5_modal_calibrated + marginal_QOI_discrepancy (the CONVERGED method)",
               "n_configs": int(n_splits), "mc_axis": "channel train/held-out split ONLY (1 impact, 1 hit; "
               "labeled reduction per D2)", "headline": "interval_score",
               "calib_converged_frac": float(np.mean(conv_flags)),
               "per_arm": per_arm, "per_split": per_split,
               "tmcmc_or_nuts": {"sampler": "NUTS", "warmup": warmup, "samples": samples, "chains": chains},
               "runtime_s": time.time() - t0,
               "note": "Whole-FRF arms (M0-M3) omitted from the MC: non-converged + useless QOI (scores_summary.json), "
                       "established at 1 split. YELLOW data caveat: 1 hit / 1 impact (split axis only)."}
    (WS / "out").mkdir(exist_ok=True)
    outp.write_text(json.dumps(rec_out, indent=2))
    pk = per_arm["theta_plus_qoi_discrepancy"]["peak"]
    print(f"\nMC DONE: {n_splits} splits | L5 calib converged {rec_out['calib_converged_frac']*100:.0f}% of splits")
    print(f"  +disc PEAK coverage med {pk['coverage']['med']:.2f} [{pk['coverage']['p5']:.2f},{pk['coverage']['p95']:.2f}]"
          f" | interval med {pk['interval']['med']:.3g} | z-std med {pk['zstd']['med']:.2f}")
    print(f"  runtime {rec_out['runtime_s']:.0f}s -> {outp}")
    return rec_out


if __name__ == "__main__":
    kw = {}
    for a in sys.argv[1:]:
        if a.startswith("--n="): kw["n_splits"] = int(a.split("=")[1])
        elif a == "--force": kw["force"] = True
    run(**kw)
