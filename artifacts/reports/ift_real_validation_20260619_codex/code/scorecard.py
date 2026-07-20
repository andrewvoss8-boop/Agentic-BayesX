#!/usr/bin/env python3
"""Assemble the IFT-vs-StatFEM held-out-sensor QOI scorecard.

Inputs are generated IFT outputs in `out/` plus copied read-only baseline
provenance in `provenance/`. This script does not rerun or alter the StatFEM
workspace.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

WS = Path(__file__).resolve().parent.parent
OUT = WS / "out"
PROV = WS / "provenance"


def load_json(path):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else None


def _status_dist(d, metric, qoi):
    try:
        return d["summary"][qoi][metric]
    except Exception:
        return None


def _l5_summary():
    mc = load_json(PROV / "mc_summary.json")
    seed0 = load_json(PROV / "heldout_qoi_L5.json")
    out = {"source": "provenance/mc_summary.json + heldout_qoi_L5.json", "n_splits": None}
    if mc:
        out["n_splits"] = mc.get("n_configs")
        out["converged_frac"] = mc.get("calib_converged_frac")
        out["qoi"] = {}
        for q in ("peak", "band"):
            arm = mc["per_arm"]["theta_plus_qoi_discrepancy"][q]
            out["qoi"][q] = {
                "coverage": arm["coverage"],
                "interval": arm["interval"],
                "crps": arm["crps"],
                "zstd": arm["zstd"],
                "logpd": None,
                "note": "logpd distribution was not stored by the inherited L5 MC; seed0 logpd below if available.",
            }
    if seed0:
        out.setdefault("seed0", {})
        out["seed0"] = {
            q: {
                "interval": seed0["scores_theta_plus_qoi_discrepancy"][q]["interval_score_mean"],
                "crps": seed0["scores_theta_plus_qoi_discrepancy"][q]["crps_mean"],
                "logpd": seed0["scores_theta_plus_qoi_discrepancy"][q]["logpd_mean"],
                "coverage": seed0["scores_theta_plus_qoi_discrepancy"][q]["coverage_frac"],
                "zstd": seed0["scores_theta_plus_qoi_discrepancy"][q]["z_std"],
            }
            for q in ("peak", "band")
        }
    return out


def _m2_summary():
    sc = load_json(PROV / "scores_summary.json")
    m2file = load_json(PROV / "tmcmc_faithful_M2_ident4_n8.json")
    out = {"source": "provenance/scores_summary.json + tmcmc_faithful_M2_ident4_n8.json"}
    if sc and "M2" in sc.get("arms", {}):
        arm = sc["arms"]["M2"]
        out["seed0"] = {
            "peak": {
                "interval": arm["peak"]["interval_score"],
                "crps": arm["peak"]["crps"],
                "logpd": arm["peak"]["logpd"],
                "coverage": arm["peak"]["coverage_frac"],
                "zstd": arm["peak"].get("z_std"),
            },
            "band": {
                "interval": arm["band"]["interval_score"],
                "crps": arm["band"]["crps"],
                "logpd": arm["band"]["logpd"],
                "coverage": arm["band"]["coverage_frac"],
                "zstd": arm["band"].get("z_std"),
            },
        }
        out["sigma_w"] = arm.get("sigma_w")
        out["converged"] = arm.get("converged")
        out["diag"] = arm.get("calib_diag")
    if m2file:
        out["faithful_tmcmc_diag"] = m2file.get("diag")
        out["faithful_tmcmc_converged"] = m2file.get("converged")
    out["distribution_note"] = "M2 whole-FRF baseline is copied as a direct one-split failure; no 25-split M2 distribution exists in the inherited workspace."
    return out


def _l8_summary():
    b = load_json(PROV / "mc_beck_summary.json")
    if not b:
        return None
    return {
        "source": "provenance/mc_beck_summary.json",
        "method": b.get("method"),
        "n_splits": b.get("n_splits"),
        "converged_frac": b.get("converged_frac"),
        "peak_interval_median": b.get("inf_IS_median"),
        "peak_coverage_median": b.get("inf_coverage_median"),
        "note": "Optional sharpened Beck mode-matching-free baseline; inherited summary is peak-focused.",
    }


def _ift_summary(tag="headline"):
    mc = load_json(OUT / f"ift_mc_{tag}.json")
    if mc:
        return {"source": f"out/ift_mc_{tag}.json", "kind": "mc", **mc}
    split = load_json(OUT / f"ift_split_0_{tag}.json")
    if split:
        return {
            "source": f"out/ift_split_0_{tag}.json",
            "kind": "single_split",
            "n_splits": 1,
            "converged_frac": 1.0 if split.get("converged") else 0.0,
            "beta_weak_frac": 1.0 if split.get("beta", {}).get("weakly_identified") else 0.0,
            "summary": {
                q: {
                    "coverage": {"med": split["scores"][q]["coverage_frac"]},
                    "interval": {"med": split["scores"][q]["interval_score_mean"]},
                    "crps": {"med": split["scores"][q]["crps_mean"]},
                    "logpd": {"med": split["scores"][q]["logpd_mean"]},
                    "zstd": {"med": split["scores"][q]["z_std"]},
                }
                for q in ("peak", "band")
            },
            "per_split": [
                {
                    "seed": 0,
                    "converged": split.get("converged"),
                    "max_rhat": split["diag"]["max_rhat"],
                    "min_ess": split["diag"]["min_ess"],
                    "div_frac": split["diag"]["div_frac"],
                    "beta_med": split["beta"]["med"],
                    "beta_weakly_identified": split["beta"]["weakly_identified"],
                    "peak_interval": split["scores"]["peak"]["interval_score_mean"],
                    "band_interval": split["scores"]["band"]["interval_score_mean"],
                }
            ],
        }
    return None


def generate_verdict(ift, l5, m2):
    if not ift:
        return {
            "verdict": "INCOMPLETE",
            "status": "RED",
            "reason": "No IFT result exists yet.",
        }
    if ift["kind"] != "mc" or ift.get("n_splits", 0) < 25:
        return {
            "verdict": "INCOMPLETE",
            "status": "RED",
            "reason": "IFT has not yet been scored on >=25 split seeds.",
        }
    conv_frac = float(ift.get("converged_frac", 0.0))
    if conv_frac < 1.0:
        return {
            "verdict": "HONEST_NEGATIVE",
            "status": "YELLOW",
            "reason": f"IFT did not satisfy the convergence gate on all splits (converged fraction {conv_frac:.2f}); non-convergence is documented, not presented as success.",
        }
    l5_peak = l5["qoi"]["peak"]["interval"]["med"]
    l5_band = l5["qoi"]["band"]["interval"]["med"]
    ift_peak = ift["summary"]["peak"]["interval"]["med"]
    ift_band = ift["summary"]["band"]["interval"]["med"]
    ift_cov = min(ift["summary"]["peak"]["coverage"]["med"], ift["summary"]["band"]["coverage"]["med"])
    l5_cov = min(l5["qoi"]["peak"]["coverage"]["med"], l5["qoi"]["band"]["coverage"]["med"])
    if ift_peak < l5_peak and ift_band < l5_band and ift_cov >= l5_cov:
        return {"verdict": "WIN", "status": "GREEN", "reason": "IFT beats L5 interval scores at equal-or-better calibration."}
    close_peak = abs(ift_peak - l5_peak) / max(l5_peak, 1e-30) <= 0.2
    close_band = abs(ift_band - l5_band) / max(l5_band, 1e-30) <= 0.2
    if close_peak and close_band:
        return {"verdict": "TIE", "status": "GREEN", "reason": "IFT and L5 are within the pre-set split-spread tolerance."}
    m2_failed = bool(m2.get("faithful_tmcmc_converged") is False or m2.get("converged") is False)
    if m2_failed and np.isfinite(ift_peak) and np.isfinite(ift_band):
        return {
            "verdict": "ROBUSTNESS-WIN",
            "status": "GREEN",
            "reason": "IFT converged and produced finite proper scores while copied M2 whole-FRF baseline is non-converged.",
        }
    return {
        "verdict": "HONEST_NEGATIVE",
        "status": "YELLOW",
        "reason": "IFT converged but did not beat L5 and did not earn a robustness-win interpretation.",
    }


def write_convergence_table(rec):
    ift = rec.get("IFT") or {}
    l5 = rec.get("L5_modal_feature_marginal_qoi_discrepancy") or {}
    m2 = rec.get("M2_whole_frf_schneider") or {}
    ift_rows = ift.get("per_split", [])
    table = {
        "study": rec["study"],
        "gate": {"max_rhat": 1.05, "min_ess": 200, "div_frac_lt": 0.02},
        "arms": {
            "IFT": {
                "sampler": (ift.get("sampler") or {}).get("name"),
                "n_splits": ift.get("n_splits"),
                "converged_frac": ift.get("converged_frac"),
                "worst_rhat": max([r.get("max_rhat", float("nan")) for r in ift_rows]) if ift_rows else None,
                "min_ess": min([r.get("min_ess", float("nan")) for r in ift_rows]) if ift_rows else None,
                "max_div_frac": max([r.get("div_frac", float("nan")) for r in ift_rows]) if ift_rows else None,
                "beta_included": True,
                "status": "YELLOW" if ift.get("converged_frac", 0) < 1 else "GREEN",
            },
            "L5": {
                "sampler": "NUTS",
                "n_splits": l5.get("n_splits"),
                "converged_frac": l5.get("converged_frac"),
                "status": "GREEN" if l5.get("converged_frac") == 1.0 else "YELLOW",
                "note": "copied modal-feature baseline summary",
            },
            "M2": {
                "sampler": "TMCMC",
                "n_splits": 1,
                "converged": m2.get("faithful_tmcmc_converged", m2.get("converged")),
                "worst_rhat": ((m2.get("faithful_tmcmc_diag") or m2.get("diag") or {}).get("max_rhat")),
                "min_ess": ((m2.get("faithful_tmcmc_diag") or m2.get("diag") or {}).get("min_ess")),
                "status": "YELLOW",
                "note": "copied one-split whole-FRF failure; not a 25-split distribution",
            },
        },
    }
    (OUT / "convergence_table.json").write_text(json.dumps(table, indent=2))
    return table


def main(tag="headline"):
    OUT.mkdir(exist_ok=True)
    ift = _ift_summary(tag)
    l5 = _l5_summary()
    m2 = _m2_summary()
    l8 = _l8_summary()
    verdict = generate_verdict(ift, l5, m2)
    rec = {
        "study": "ift_real_validation_20260619_codex",
        "tag": tag,
        "qoi": ["peak_accelerance_g_per_lbf", "band_GRMS_g_per_lbf"],
        "headline_scores": ["interval_score", "crps", "log_predictive_density"],
        "status": verdict["status"],
        "verdict": verdict["verdict"],
        "verdict_reason": verdict["reason"],
        "IFT": ift,
        "L5_modal_feature_marginal_qoi_discrepancy": l5,
        "M2_whole_frf_schneider": m2,
        "L8_beck_optional": l8,
        "warnings": [
            "YELLOW: inherited L5 MC summary lacks per-split logpd distribution; seed0 logpd is available.",
            "YELLOW: M2 inherited baseline is a direct one-split whole-FRF failure, not a 25-split distribution.",
            "YELLOW: IFT headline uses log-magnitude moment approximation because log(abs(field)) is nonlinear.",
            "YELLOW: one hit and one impact; randomization is channel split only.",
        ],
    }
    outp = OUT / "scorecard.json"
    outp.write_text(json.dumps(rec, indent=2))
    write_convergence_table(rec)
    print(f"scorecard: {rec['verdict']} ({rec['status']}) -> {outp}")
    print(rec["verdict_reason"])
    return rec


if __name__ == "__main__":
    main()
