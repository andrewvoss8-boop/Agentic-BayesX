#!/usr/bin/env python3
"""Aggregate the per-split cells -> out/scorecard.json (the head-to-head the immutable check.py reads + turns
into the verdict). Reads:
  out/ift_tmcmc_cells/ift_tmcmc_seed*.json   (IFT arm = physics-in-prior, learned beta, TMCMC escalation)
  out/l5_cells/l5_seed*.json                 (L5 arm  = StatFEM modal-feature + QOI discrepancy; the bar)
  out/m2_cells/m2_seed*.json                 (M2 arm  = StatFEM whole-FRF Schneider; physics-in-likelihood)
  out/ift_cells/ift_seed00.json              (IFT-under-NUTS multimodality evidence, context)

No verdict is computed here. check.py generates WIN/ROBUSTNESS-WIN/TIE/HONEST-NEGATIVE from these numbers.
"""
from __future__ import annotations
import glob
import json
from pathlib import Path

import numpy as np

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"


def dist(vals):
    v = np.asarray([x for x in vals if x is not None and np.isfinite(x)], float)
    if v.size == 0:
        return {"med": None, "p5": None, "p95": None, "n": 0}
    return {"med": float(np.median(v)), "p5": float(np.percentile(v, 5)),
            "p95": float(np.percentile(v, 95)), "min": float(v.min()), "max": float(v.max()), "n": int(v.size)}


def block(per_split_scores, conv_flags, extra=None):
    b = {"converged_frac": float(np.mean(conv_flags)) if conv_flags else 0.0, "n_splits": len(per_split_scores)}
    for q in ("peak", "band"):
        b[q] = {"interval": dist([s[q].get("interval_score_mean") for s in per_split_scores]),
                "crps": dist([s[q].get("crps_mean") for s in per_split_scores]),
                "logpd": dist([s[q].get("logpd_mean") for s in per_split_scores]),
                "coverage": dist([s[q].get("coverage_frac") for s in per_split_scores]),
                "zstd": dist([s[q].get("z_std") for s in per_split_scores])}
    if extra:
        b.update(extra)
    return b


def load_cells(pattern, score_key="scores", conv_path=None):
    rows = []
    for f in sorted(glob.glob(str(OUT / pattern))):
        r = json.loads(Path(f).read_text())
        rows.append(r)
    return rows


def main():
    # ---- IFT (TMCMC) ----
    ift_cells = load_cells("ift_tmcmc_cells/ift_tmcmc_seed*.json")
    ift_scores = [c["scores"] for c in ift_cells]
    ift_conv = [bool(c["convergence"]["converged"]) for c in ift_cells]
    ift_seeds = [c["split_seed"] for c in ift_cells]
    beta_meds = [c["beta_posterior"]["beta_med"] for c in ift_cells]
    beta_weak = [bool(c["beta_posterior"]["weakly_identified"]) for c in ift_cells]
    beta_collapsed = [bool(c["beta_posterior"]["collapsed"]) for c in ift_cells]
    bstar = ift_cells[0]["beta_posterior"]["beta_star"] if ift_cells else None
    ift_extra = {"seeds": ift_seeds, "sampler": "TMCMC", "tmcmc_escalated": True,
                 "nuts_multimodal": True,
                 "beta": {"beta_med_dist": dist(beta_meds), "beta_star": bstar,
                          "collapse_factor_med": (float(bstar / np.median(beta_meds)) if (bstar and beta_meds) else None),
                          "weakly_identified_frac": float(np.mean(beta_weak)) if beta_weak else None,
                          "collapsed": bool(np.mean(beta_collapsed) > 0.5) if beta_collapsed else False},
                 "crossrun_rhat_dist": dist([c["convergence"]["max_rhat_crossrun"] for c in ift_cells]),
                 "log_evidence_dist": dist([c["convergence"]["log_evidence_mean"] for c in ift_cells])}

    # ---- L5 (NUTS modal-feature; the bar) ----
    l5_cells = load_cells("l5_cells/l5_seed*.json")
    l5_scores = [c["scores"] for c in l5_cells]
    l5_conv = [bool(c["converged"]) for c in l5_cells]
    l5_seeds = [c["seed"] for c in l5_cells]

    # ---- M2 (whole-FRF Schneider; physics-in-likelihood; expected non-converged) ----
    m2_cells = load_cells("m2_cells/m2_seed*.json")
    m2_scores = [c["scores"] for c in m2_cells]
    m2_conv = [bool(c["converged"]) for c in m2_cells]
    m2_seeds = [c["seed"] for c in m2_cells]
    m2_rhat = dist([c["diag"]["max_rhat"] for c in m2_cells]) if m2_cells else {}

    # ---- IFT-under-NUTS context (the multimodality evidence) ----
    nuts_ctx = {}
    p = OUT / "ift_cells" / "ift_seed00.json"
    if p.exists():
        c = json.loads(p.read_text())
        nuts_ctx = {"seed": 0, "max_rhat": c["convergence"]["max_rhat"],
                    "min_ess": c["convergence"]["min_ess"], "divergences": c["convergence"]["divergences"],
                    "note": "IFT under NUTS: multimodal (0 div, huge R-hat) -> TMCMC escalation"}

    scorecard = {
        "study": "ift_real_validation_20260619", "deliverable": "head_to_head_heldout_QOI_scorecard",
        "seeds": l5_seeds,    # the full 25-split axis (L5 carries it; IFT/M2 on labeled subsets)
        "n_splits": len(l5_seeds),
        "mc_axis": "channel train/held-out split ONLY (1 impact, 1 hit; labeled reduction, YELLOW)",
        "headline_scores": ["interval", "crps", "logpd"], "secondary": ["coverage", "zstd"],
        "scorer": "score.py (byte-identical, manifest_sha256.txt)",
        "apples_to_apples": "same data/forward/splits/scorer; arms differ only in WHERE physics/trust lives",
        "arms": {
            "IFT": block(ift_scores, ift_conv, ift_extra),
            "L5": block(l5_scores, l5_conv, {"seeds": l5_seeds, "sampler": "NUTS",
                        "observable": "modal peak frequencies (DIFFERENT, unimodal observable)"}),
            "M2": block(m2_scores, m2_conv, {"seeds": m2_seeds, "sampler": "NUTS",
                        "observable": "whole-FRF log|H| (SAME as IFT)", "max_rhat_dist": m2_rhat,
                        "tmcmc_cite": "StatFEM D10: M2-TMCMC cross-run R-hat 129, sigma_d->7.4 (variance singularity)",
                        "note": "physics-in-LIKELIHOOD; expected NON-converged; QOI flagged"}),
        },
        "ift_under_nuts": nuts_ctx,
        "context": "IFT and M2 share the log|H| observable -> both multimodal under NUTS; under TMCMC, IFT "
                   "(bounded beta) reproduces while M2 (free sigma_d) does not. L5 is a different, unimodal "
                   "observable and is the converged sharpness bar.",
    }
    OUT.mkdir(exist_ok=True)
    (OUT / "scorecard.json").write_text(json.dumps(scorecard, indent=2))
    a = scorecard["arms"]
    print(f"scorecard.json written: IFT conv {a['IFT']['converged_frac']*100:.0f}% (n={a['IFT']['n_splits']}) | "
          f"L5 conv {a['L5']['converged_frac']*100:.0f}% (n={a['L5']['n_splits']}) | "
          f"M2 conv {a['M2']['converged_frac']*100:.0f}% (n={a['M2']['n_splits']})")
    for arm in ("IFT", "L5", "M2"):
        pk = a[arm]["peak"]; bd = a[arm]["band"]
        print(f"  {arm}: PEAK interval {pk['interval']['med']} cover {pk['coverage']['med']} | "
              f"BAND interval {bd['interval']['med']} cover {bd['coverage']['med']}")
    return scorecard


if __name__ == "__main__":
    main()
