#!/usr/bin/env python3
"""Sensitivity gate (task §9): vary what is most likely to flip the robust/brittle verdict.

The 4 arms already test discrepancy STRUCTURE; the 5 combos already test realization. Here we vary, on a
representative combo (3 = mixed), the arms M0 (naive) and M2 (Schneider) -- the key contrast -- across:
  - held-out-channel choice (a different observed set)
  - damping value (zeta = 0.01, 0.03)
  - frequency band (narrower 60-200 Hz)
  - inference correlation-length MISMATCH (M2 assumes wrong ell_f, ell_z while truth keeps the injected ones)
Reduced draws (700+700) for speed; resumable (tagged cells skipped by aggregate). Output: out/sensitivity.json.
"""
from __future__ import annotations

import glob
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WS = HERE.parent
OUT = WS / "out"
sys.path.insert(0, str(HERE))

import core            # noqa: E402
import nuts_arms as na  # noqa: E402
import predict as pr   # noqa: E402
import run_sweep as rs  # noqa: E402

COMBO = 3
NW, NS, NC = 700, 700, 4


def alt_channels(model):
    """A different observed set: pick 6 nodes NOT used as the default observed (shifted selection)."""
    ch = core.select_channels(model)
    # rotate: use the default held-out's first 6 as the new observed, predict the default observed + rest
    new_obs = ch["heldout"][:6]
    pool = [c for c in (ch["observed"] + ch["heldout"][6:]) ]
    new_held = pool[:14]
    return {"drive": ch["drive"], "observed": list(new_obs), "heldout": list(new_held)}


def run_one(model, freqs, observed, heldout, drive, arm, zeta, tag, seed_off=0,
            len_logf=core.DISC_LEN_LOGF, len_z=core.DISC_LEN_Z):
    tt = core.theta_vector(core.COMBOS[COMBO]["theta"])
    meas, _, tho = rs.gen_truth(model, freqs, observed, heldout, drive, tt, COMBO, zeta=zeta)
    t0 = time.time()
    samples, diag, _ = na.run_arm(arm, model, freqs, meas, observed, drive, zeta=zeta,
                                  num_warmup=NW, num_samples=NS, num_chains=NC,
                                  seed=20260616 + COMBO + seed_off, len_logf=len_logf, len_z=len_z)
    ctx = pr.PredCtx(model, freqs, observed, heldout, drive, arm, zeta=zeta, len_logf=len_logf, len_z=len_z)
    res = pr.predict_cell(ctx, samples, tho, meas, core.GNAMES, tt, rs.INFORMED_GROUPS)
    return {"tag": tag, "sensitivity": True, "combo_idx": COMBO, "arm": arm, "zeta": zeta,
            "len_logf": len_logf, "len_z": len_z,
            "nuts": diag,
            "converged": bool(diag["max_rhat"] <= 1.05 and diag["min_ess"] >= 200 and diag["div_frac"] < 0.02),
            "heldout_coverage": res["heldout_coverage"], "sigma_d": res["sigma_d"],
            "mean_band_width_db": res["mean_band_width_db"], "runtime_s": round(time.time() - t0, 2)}


def cell_p(tag, arm):
    return OUT / f"cell_{tag}{COMBO}_{arm}.json"


def main():
    model = core.load_model()
    ch = core.select_channels(model)
    f = core.freq_grid()
    fnar = core.freq_grid(lo=60.0, hi=200.0)
    alt = alt_channels(model)

    jobs = [
        ("altch", ch, f, core.ZETA_NOM, None, dict(observed=alt["observed"], heldout=alt["heldout"])),
        ("zeta01", ch, f, 0.01, None, {}),
        ("zeta03", ch, f, 0.03, None, {}),
        ("bandnar", ch, fnar, core.ZETA_NOM, None, {}),
        ("lenmis", ch, f, core.ZETA_NOM, dict(len_logf=2 * core.DISC_LEN_LOGF, len_z=2 * core.DISC_LEN_Z), {}),
    ]
    results = []
    for tag, chh, freqs, zeta, lens, kw in jobs:
        arms = ["M0", "M2"] if tag != "lenmis" else ["M2"]   # lenmis only affects the correlated arm
        observed = kw.get("observed", chh["observed"])
        heldout = kw.get("heldout", chh["heldout"])
        drive = chh["drive"]
        ll = (lens or {}).get("len_logf", core.DISC_LEN_LOGF)
        lz = (lens or {}).get("len_z", core.DISC_LEN_Z)
        for arm in arms:
            p = cell_p(tag, arm)
            if p.exists():
                print(f"[skip] {p.name}", flush=True)
                results.append(json.load(open(p)))
                continue
            print(f"[run ] sensitivity {tag} arm={arm} ...", flush=True)
            rec = run_one(model, freqs, observed, heldout, drive, arm, zeta, tag,
                          seed_off=hash(tag) % 1000, len_logf=ll, len_z=lz)
            json.dump(rec, open(p, "w"), indent=1)
            hc = rec["heldout_coverage"]
            print(f"       {tag}/{arm} rhat={rec['nuts']['max_rhat']:.3f} covP/B="
                  f"{hc['peak']['frac']:.2f}/{hc['band']['frac']:.2f} sigd={rec['sigma_d']['med']:.3f}", flush=True)
            results.append(rec)

    # summary: combined coverage per (tag, arm) vs the baseline (main combo3 cells)
    base = {}
    for arm in ("M0", "M2"):
        bp = OUT / f"cell_{COMBO}_{arm}.json"
        if bp.exists():
            base[arm] = json.load(open(bp))["heldout_coverage"]["combined"]["frac"]
    summary = {"combo": COMBO, "baseline_combined": base, "arms_varied": ["M0", "M2"], "rows": []}
    for r in results:
        summary["rows"].append({"tag": r["tag"], "arm": r["arm"], "zeta": r["zeta"],
                                "len_logf": r.get("len_logf"), "len_z": r.get("len_z"),
                                "combined_coverage": r["heldout_coverage"]["combined"]["frac"],
                                "converged": r["converged"], "sigma_d_med": r["sigma_d"]["med"]})
    # verdict: is the naive-vs-Schneider gap stable (Schneider >= naive) across all variations?
    by = {}
    for r in summary["rows"]:
        by.setdefault(r["tag"], {})[r["arm"]] = r["combined_coverage"]
    stable = all(("M2" in v and "M0" in v and v["M2"] >= v["M0"]) or ("M0" not in v) for v in by.values())
    summary["schneider_beats_naive_in_all_variations"] = bool(stable)
    json.dump(summary, open(OUT / "sensitivity.json", "w"), indent=1)
    print("sensitivity verdict (Schneider >= naive in all variations):", stable)


if __name__ == "__main__":
    main()
