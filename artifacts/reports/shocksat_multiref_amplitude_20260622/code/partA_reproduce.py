#!/usr/bin/env python3
"""Part A — DUPLICATE the Card F value program on +X-only (integrity / reproduction baseline).

Runs the BYTE-IDENTICAL inherited Card F scripts (freq_value, value_eval, modal_beck_ash) on the +X cache and
writes partA_-prefixed copies of the results, plus a comparison vs the documented Card F numbers. Resumable: each
sub-step skips if its partA_*.json already exists (so a killed/relaunched detached run does not start over).

Target headline (Card F packet §2/§3, checker_twin_report):
  freq CRPS-skill vs climatology   ≈ +0.93   (freq_value seed 0)
  non-hard amplitude CRPS-skill    ≈ −1.0    (value_eval seeds 0,1,2 mean)
  Beck shape-field FEM→INFERRED    ≈ −0.68 → −0.25 (modal_beck_ash seeds 0,1,2 mean)
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"; OUT.mkdir(exist_ok=True)
CARD_F = WS.parent / "shocksat_modelclass_L5_20260619" / "out"


def _load(p):
    return json.loads(Path(p).read_text()) if Path(p).exists() else None


def step_freq():
    outp = OUT / "partA_freq_value_seed00.json"
    if outp.exists():
        print(f"[skip] {outp.name}"); return
    import freq_value as fv
    rec = fv.run(seed=0, write=False)
    outp.write_text(json.dumps(rec, indent=2))
    print(f"[done] freq seed0 skill {rec['twin_vs_climatology']['crps_skill']:+.3f}")


def step_amp():
    import value_eval as ve
    for s in (0, 1, 2):
        outp = OUT / f"partA_value_eval_seed{s:02d}.json"
        if outp.exists():
            print(f"[skip] {outp.name}"); continue
        rec = ve.run(seed=s, write=False)
        outp.write_text(json.dumps(rec, indent=2))
        print(f"[done] value_eval seed{s} non-hard skill {rec['NON_HARD']['crps_skill_vs_clim']:+.3f}")


def step_beck():
    outp = OUT / "partA_modal_beck_ash.json"
    if outp.exists():
        print(f"[skip] {outp.name}"); return
    import modal_beck_ash as mb
    seeds = {}
    fem_sk, inf_sk = [], []
    for s in (0, 1, 2):
        # modal_beck_ash.run writes a fixed out/modal_beck_ash.json; remove so force re-runs each seed cleanly
        fixed = OUT / "modal_beck_ash.json"
        if fixed.exists():
            fixed.unlink()
        rec = mb.run(seed=s, force=True)
        fs = rec["heldout_peak_FEM_shapes"]["crps_skill_vs_clim"]
        is_ = rec["heldout_peak_INFERRED_shapes"]["crps_skill_vs_clim"]
        seeds[str(s)] = {"fem_skill": fs, "inf_skill": is_,
                         "fem_IS": rec["heldout_peak_FEM_shapes"]["interval_score"],
                         "inf_IS": rec["heldout_peak_INFERRED_shapes"]["interval_score"],
                         "inf_cover": rec["heldout_peak_INFERRED_shapes"]["coverage"],
                         "conv": rec["diag"]["converged"], "max_rhat": rec["diag"]["max_rhat"],
                         "min_ess": rec["diag"]["min_ess"]}
        fem_sk.append(fs); inf_sk.append(is_)
        print(f"[done] beck seed{s} FEM {fs:+.3f} INF {is_:+.3f} conv {rec['diag']['converged']}")
    agg = {"deliverable": "Part A reproduction of Beck shape-field lever (modal_beck_ash seeds 0-2)",
           "seeds": seeds,
           "heldout_peak_FEM_shapes": {"crps_skill_vs_clim": float(np.mean(fem_sk))},
           "heldout_peak_INFERRED_shapes": {"crps_skill_vs_clim": float(np.mean(inf_sk))},
           "mean_fem_IS": float(np.mean([seeds[k]["fem_IS"] for k in seeds])),
           "mean_inf_IS": float(np.mean([seeds[k]["inf_IS"] for k in seeds])),
           "all_converged": bool(all(seeds[k]["conv"] for k in seeds))}
    outp.write_text(json.dumps(agg, indent=2))


def compare():
    """Write a side-by-side vs the documented Card F numbers."""
    rep = {"deliverable": "Part A reproduction vs Card F documented headline (+X single-reference)"}
    f = _load(OUT / "partA_freq_value_seed00.json")
    cf_f = _load(CARD_F / "freq_value_seed00.json")
    if f:
        rep["frequency"] = {"reproduced_crps_skill": f["twin_vs_climatology"]["crps_skill"],
                            "cardF_crps_skill": (cf_f["twin_vs_climatology"]["crps_skill"] if cf_f else 0.93),
                            "reproduced_freq_err_pct": [f["value_of_updating_vs_nominal"]["nominal_fem_median_abs_freq_err_pct"],
                                                        f["value_of_updating_vs_nominal"]["calibrated_median_abs_freq_err_pct"]]}
    ve = [ _load(OUT / f"partA_value_eval_seed{s:02d}.json") for s in (0, 1, 2)]
    sk = [v["NON_HARD"]["crps_skill_vs_clim"] for v in ve if v]
    if sk:
        rep["amplitude"] = {"reproduced_nonhard_skill_per_seed": sk,
                            "reproduced_nonhard_skill_mean": float(np.mean(sk)), "cardF_mean": -1.0}
    b = _load(OUT / "partA_modal_beck_ash.json")
    if b:
        rep["beck_shapefield"] = {"reproduced_fem_skill": b["heldout_peak_FEM_shapes"]["crps_skill_vs_clim"],
                                  "reproduced_inf_skill": b["heldout_peak_INFERRED_shapes"]["crps_skill_vs_clim"],
                                  "cardF_fem": -0.68, "cardF_inf": -0.25}
    (OUT / "partA_summary.json").write_text(json.dumps(rep, indent=2))
    print("\n=== PART A SUMMARY ===")
    print(json.dumps(rep, indent=2))


if __name__ == "__main__":
    t0 = time.time()
    step_freq()
    step_amp()
    step_beck()
    compare()
    print(f"\nPart A total runtime {time.time()-t0:.0f}s")
