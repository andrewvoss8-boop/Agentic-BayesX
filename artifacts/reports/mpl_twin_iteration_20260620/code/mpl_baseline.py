#!/usr/bin/env python3
"""Round-0 BASELINE: score the as-received fable rev-3 twin (NOMINAL theta=1 deterministic+discrepancy AND
NUTS-CALIBRATED) on all 5 leave-one-location-out splits, against the CLIMATOLOGY no-skill bar. Establishes the
immutable numbers to beat. Writes out/baseline_scores.json, out/climatology.json, out/class_M0.json, and seeds
out/model_registry.json. Reuses score.py byte-identical. Resumable (skips splits already written to the partial).

THREE held-out scores per split (D-A): (1) CRPS-skill vs climatology (on band-GRMS of |T| AND whole-curve
interval), (2) interval/Winkler + coverage, (3) band-GRMS error (gain-free |T|). mean +/- spread over 5 splits.
"""
from __future__ import annotations
import json, os, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mpl_calibrate as CAL
import score as SC

OUT = CAL.OUT
HELD = CAL.HELD; REF = CAL.REF
SMOKE = os.environ.get("SMOKE", "0") == "1"


def grms_of_logT(logT, f):
    return float(np.sqrt(np.trapz(np.exp(logT) ** 2, f)))


def score_heldout(P, h, train, pred_logT_samples):
    """pred_logT_samples: (S, Nf) predictive log|T| at held-out h. Returns the 3-score block + climatology + skill."""
    f = P["fgrid"]; truth = np.log(np.maximum(P["Tmeas"][h], 1e-12))
    # (3) whole-curve + band-GRMS error
    frf = SC.frf_score(pred_logT_samples, truth, f)
    # (1)+(2) scalar band-GRMS QOI
    grms_s = np.sqrt(np.trapz(np.exp(pred_logT_samples) ** 2, f, axis=1))
    grms_truth = grms_of_logT(truth, f)
    qoi = SC.score_qoi(grms_s, grms_truth)
    # climatology = observed (train) location |T| curves as the population
    clim_log = np.stack([np.log(np.maximum(P["Tmeas"][l], 1e-12)) for l in train], 0)   # (n_train, Nf)
    clim_grms = np.array([grms_of_logT(clim_log[i], f) for i in range(clim_log.shape[0])])
    clim_qoi = SC.score_qoi(clim_grms, grms_truth)
    clim_frf = SC.frf_score(clim_log, truth, f)
    skill_grms = float(1 - qoi["crps"] / max(clim_qoi["crps"], 1e-30))
    skill_curve = float(1 - frf["weighted_interval_score"] / max(clim_frf["weighted_interval_score"], 1e-30))
    return {
        "grms_truth": grms_truth, "grms_pred_median": float(np.median(grms_s)),
        "grms_rel_err": frf["grms_rel_err"],
        "crps_grms": qoi["crps"], "clim_crps_grms": clim_qoi["crps"], "crps_skill_vs_clim_grms": skill_grms,
        "interval_grms": qoi["interval_score"], "coverage_grms": qoi["covered"], "z_grms": qoi["z"],
        "whole_curve_interval": frf["weighted_interval_score"],
        "clim_whole_curve_interval": clim_frf["weighted_interval_score"],
        "interval_skill_vs_clim_curve": skill_curve,
        "peak_freq_err_hz": frf["peak_freq_err_hz"],
    }


def nominal_predictive(P, h, train, n_draws=400, seed=0):
    """theta=1, zeta=1%, c = median training residual, sigma_d = std training residual; predictive samples."""
    theta = np.ones(len(P["groups_used"])); zeta = 0.01
    res = []
    for l in train:
        pl = CAL.predict_logT_np(P, theta, zeta, l)
        res.append(np.log(np.maximum(P["Tmeas"][l], 1e-12)) - pl)
    res = np.concatenate(res)
    c = float(np.median(res)); sig = float(np.std(res))
    ph = CAL.predict_logT_np(P, theta, zeta, h) + c
    rng = np.random.default_rng(seed)
    samp = ph[None, :] + rng.normal(0, sig, (n_draws, len(P["fgrid"])))
    point_grms = grms_of_logT(ph, P["fgrid"])
    truth_grms = grms_of_logT(np.log(np.maximum(P["Tmeas"][h], 1e-12)), P["fgrid"])
    fem_point_db = abs(20 * np.log10(max(point_grms, 1e-30) / max(truth_grms, 1e-30)))
    return samp, c, sig, fem_point_db


def calibrated_predictive(P, h, post, n_draws=400, seed=1):
    nsamp = post["theta"].shape[0]
    idx = np.linspace(0, nsamp - 1, min(nsamp, n_draws)).astype(int)
    rng = np.random.default_rng(seed)
    out = np.zeros((len(idx), len(P["fgrid"])))
    for j, s in enumerate(idx):
        th = np.asarray(post["theta"][s]); ze = float(np.asarray(post["zeta"][s]))
        c = float(np.asarray(post["c"][s])); sg = float(np.asarray(post["sigma_d"][s]))
        out[j] = CAL.predict_logT_np(P, th, ze, h) + c + rng.normal(0, sg, len(P["fgrid"]))
    return out


def main():
    t0 = time.time()
    P = CAL.precompute(); P["groups_used"] = P["groups"]
    warmup, samples, chains = (200, 200, 2) if SMOKE else (1000, 1000, 4)
    per_split = []; clim_rows = []
    conv_all = {}
    for h in HELD:
        train = [l for l in HELD if l != h]
        # nominal
        nsamp, c_n, sig_n, fem_db = nominal_predictive(P, h, train)
        nom = score_heldout(P, h, train, nsamp)
        nom["centering_c"] = c_n; nom["sigma_d"] = sig_n; nom["fem_point_grms_err_db"] = fem_db
        # calibrated (NUTS)
        post, conv = CAL.calibrate_split(P, train, P["groups"], warmup=warmup, samples=samples, chains=chains)
        conv_all[h] = conv
        csamp = calibrated_predictive(P, h, post)
        cal = score_heldout(P, h, train, csamp)
        cal["theta_median"] = {g: float(np.median(np.asarray(post["theta"])[:, i])) for i, g in enumerate(P["groups"])}
        cal["zeta_median"] = float(np.median(np.asarray(post["zeta"])))
        cal["convergence"] = conv
        per_split.append({"held_out": h, "train": train, "nominal": nom, "calibrated": cal})
        clim_rows.append({"held_out": h, "clim_crps_grms": nom["clim_crps_grms"],
                          "clim_whole_curve_interval": nom["clim_whole_curve_interval"]})
        print(f"[{h}] nominal GRMS-skill {nom['crps_skill_vs_clim_grms']:+.2f} cov {nom['coverage_grms']} | "
              f"calib GRMS-skill {cal['crps_skill_vs_clim_grms']:+.2f} cov {cal['coverage_grms']} "
              f"curve-skill {cal['interval_skill_vs_clim_curve']:+.2f} | conv {conv['converged']} "
              f"(R̂{conv['max_rhat']:.3f} ESS{conv['min_ess']:.0f} div{conv['div_frac']:.3f})")

    def agg(key, kind):
        v = [s[kind][key] for s in per_split]
        return {"mean": float(np.mean(v)), "std": float(np.std(v)), "per_split": [round(float(x), 4) for x in v]}

    summary = {k: {"nominal": agg(k, "nominal"), "calibrated": agg(k, "calibrated")}
               for k in ["crps_skill_vs_clim_grms", "interval_grms", "coverage_grms", "grms_rel_err",
                         "interval_skill_vs_clim_curve", "peak_freq_err_hz"]}
    allconv = all(c["converged"] for c in conv_all.values())
    rec = {"deliverable": "Round-0 baseline (nominal + NUTS-calibrated M0) vs climatology, 5 LOLO splits",
           "groups_calibrated": P["groups"], "smoke": SMOKE,
           "per_split": per_split, "summary": summary,
           "all_splits_converged": bool(allconv),
           "runtime_s": round(time.time() - t0, 1)}
    (OUT / "baseline_scores.json").write_text(json.dumps(rec, indent=2))
    (OUT / "climatology.json").write_text(json.dumps(
        {"deliverable": "climatology no-skill bar (predict held-out |T|/GRMS from observed-location population)",
         "per_split": clim_rows}, indent=2))

    # class_M0.json + registry seed
    m0 = {"class_id": "M0_baseline_calibrated9grp",
          "hypothesis": "as-received fable rev-3 FEM, 6 major K-groups calibrated, uniform zeta, iid log|T| discrepancy",
          "changed": "baseline (carry-forward reference)", "n_params": len(P["groups"]) + 3,
          "nuts_converged": bool(allconv), "worst_rhat": float(max(c["max_rhat"] for c in conv_all.values())),
          "min_ess": float(min(c["min_ess"] for c in conv_all.values())),
          "heldout_crps_skill_grms_mean": summary["crps_skill_vs_clim_grms"]["calibrated"]["mean"],
          "heldout_interval_skill_curve_mean": summary["interval_skill_vs_clim_curve"]["calibrated"]["mean"],
          "grms_rel_err_mean": summary["grms_rel_err"]["calibrated"]["mean"],
          "verdict": "baseline/carry-forward"}
    (OUT / "class_M0.json").write_text(json.dumps(m0, indent=2))
    reg = {"deliverable": "model-class search registry", "rounds": [{"round": 0, "classes": ["M0_baseline_calibrated9grp"]}],
           "rows": [m0], "program_verdict": "YELLOW (baseline established; search rounds pending)"}
    (OUT / "model_registry.json").write_text(json.dumps(reg, indent=2))
    print(f"\nBASELINE summary (calibrated, mean over 5 splits): "
          f"GRMS-skill {summary['crps_skill_vs_clim_grms']['calibrated']['mean']:+.2f}, "
          f"curve-skill {summary['interval_skill_vs_clim_curve']['calibrated']['mean']:+.2f}, "
          f"GRMS rel-err {summary['grms_rel_err']['calibrated']['mean']:+.2f} | converged {allconv} | "
          f"runtime {rec['runtime_s']}s")


if __name__ == "__main__":
    main()
