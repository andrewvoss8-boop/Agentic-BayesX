#!/usr/bin/env python3
"""Phase 1 MC (Card C) -- hardened Beck-on-.ash across >=25 channel splits, FULL QOI (peak + band-GRMS), FAIR
observed-only QOI-discrepancy, measured per-mode damping, n_modes sweep. Attributes any sharpening to a named
mechanism by a 2x2 contrast per split:
    FEM_const      = FEM shapes, constant zeta=0.01           (the baseline reconstruction)
    FEM_measured   = FEM shapes, measured per-mode damping    (isolates DAMPING)
    INFER_const    = inferred shape field, constant zeta      (isolates SHAPE-FIELD correction)
    INFER_measured = inferred shapes + measured damping       (the full hardened twin)
Per config we report held-out peak |H| AND band-GRMS interval score (lower=sharper-while-calibrated), coverage,
and z-std, as distributions over splits. Calibration is split-independent (global .ash survey) -> done ONCE per
n_modes and reused (labeled). L5 reference numbers folded in for context.

Output: out/mc_beck_full_summary.json. Beck/Au/Vanik (2001) CACIE 16:1-11.
"""
import json
import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import modal_beck_full as M

WS = Path(__file__).resolve().parent.parent
CFGS = ("FEM_const", "FEM_measured", "INFER_const", "INFER_measured")


def _agg(per_split, qoi):
    """Distribution summaries over splits for one (config, qoi)."""
    IS = np.array([s[qoi]["interval_score"] for s in per_split])
    cov = np.array([s[qoi]["coverage"] for s in per_split])
    z = np.array([s[qoi]["z_std"] for s in per_split])
    return {"IS_median": float(np.median(IS)), "IS_p5": float(np.percentile(IS, 5)),
            "IS_p95": float(np.percentile(IS, 95)), "coverage_median": float(np.median(cov)),
            "z_std_median": float(np.median(z))}


def run(n_splits=25, n_modes_list=(12, 20), warmup=800, samples=800, chains=4, n_draws=150):
    L5 = json.loads((WS / "out" / "heldout_qoi_L5.json").read_text())
    L5ref = {"peak": L5["scores_theta_plus_qoi_discrepancy"]["peak"],
             "band": L5["scores_theta_plus_qoi_discrepancy"]["band"]}
    blocks = {}
    for nmreq in n_modes_list:
        cal = M.calibrate(n_modes=nmreq, warmup=warmup, samples=samples, chains=chains)
        eta_meas = M.per_mode_eta(cal, True)
        print(f"\n=== n_modes {cal['nm']} (MAC {cal['match_MAC']:.2f}) calib conv {cal['diag']['converged']} "
              f"R-hat {cal['diag']['max_rhat']:.3f} ESS {cal['diag']['min_ess']:.0f} ===", flush=True)
        per_split = {c: [] for c in CFGS}
        rows = []
        for s in range(n_splits):
            sc = M.score_split(cal, seed=s, n_draws=n_draws, eta_measured=eta_meas)
            for c in CFGS:
                per_split[c].append(sc[c])
            rows.append({"seed": s, **{c: {"peak_IS": sc[c]["peak"]["interval_score"],
                                            "band_IS": sc[c]["band"]["interval_score"],
                                            "peak_cov": sc[c]["peak"]["coverage"],
                                            "band_cov": sc[c]["band"]["coverage"]} for c in CFGS}})
            fi = sc["INFER_measured"]["peak"]["interval_score"]; ff = sc["FEM_const"]["peak"]["interval_score"]
            print(f"  nm{cal['nm']} split {s:2d}: FEM_const peak IS {ff:7.0f} -> INFER_measured {fi:7.0f} "
                  f"(cov {sc['INFER_measured']['peak']['coverage']:.2f})", flush=True)
        # mechanism attribution: head-to-head split counts on PEAK IS
        def sharper(ca, cb):  # ca sharper than cb (lower IS) in how many splits
            a = np.array([x["peak"]["interval_score"] for x in per_split[ca]])
            b = np.array([x["peak"]["interval_score"] for x in per_split[cb]])
            return int(np.sum(a < b)), float(np.median(a / np.maximum(b, 1e-9)))
        sh_full = sharper("INFER_measured", "FEM_const")
        sh_shape = sharper("INFER_const", "FEM_const")
        sh_damp = sharper("FEM_measured", "FEM_const")
        sh_damp_on_shape = sharper("INFER_measured", "INFER_const")
        blocks[f"n_modes_{cal['nm']}"] = {
            "calib_diag": cal["diag"], "match_MAC": cal["match_MAC"], "n_splits": n_splits,
            "peak": {c: _agg(per_split[c], "peak") for c in CFGS},
            "band": {c: _agg(per_split[c], "band") for c in CFGS},
            "mechanism_peak_IS": {
                "full_INFERmeas_vs_FEMconst": {"n_sharper": sh_full[0], "ratio_median": sh_full[1]},
                "shape_only_INFERconst_vs_FEMconst": {"n_sharper": sh_shape[0], "ratio_median": sh_shape[1]},
                "damping_only_FEMmeas_vs_FEMconst": {"n_sharper": sh_damp[0], "ratio_median": sh_damp[1]},
                "damping_on_shape_INFERmeas_vs_INFERconst": {"n_sharper": sh_damp_on_shape[0],
                                                             "ratio_median": sh_damp_on_shape[1]}},
            "per_split": rows}
        # incremental write (resumable across n_modes)
        (WS / "out").mkdir(exist_ok=True)
        (WS / "out" / "mc_beck_full_summary.json").write_text(json.dumps(
            {"method": "L8b_Beck_on_ash_HARDENED (Beck/Au/Vanik 2001)",
             "note": ("calibration split-INDEPENDENT (global .ash survey) reused across splits; QOI-discrepancy "
                      "sigma estimated on OBSERVED channels only (fair vs L5); peak |H| AND band-GRMS scored"),
             "L5_reference_theta_plus_qoi_disc": L5ref, "blocks": blocks}, indent=2))
    print("\nMC-BECK-FULL DONE.")
    for nm, b in blocks.items():
        pk = b["peak"]; m = b["mechanism_peak_IS"]
        print(f" {nm}: PEAK IS median FEM_const {pk['FEM_const']['IS_median']:.0f} -> "
              f"INFER_measured {pk['INFER_measured']['IS_median']:.0f} | full sharper "
              f"{m['full_INFERmeas_vs_FEMconst']['n_sharper']}/{b['n_splits']} "
              f"(shape {m['shape_only_INFERconst_vs_FEMconst']['n_sharper']}, "
              f"damp {m['damping_only_FEMmeas_vs_FEMconst']['n_sharper']})")
    print(f" L5 ref PEAK IS {L5ref['peak']['interval_score_mean']:.0f}  BAND IS {L5ref['band']['interval_score_mean']:.0f}")
    return blocks


if __name__ == "__main__":
    ns = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    run(n_splits=ns)
