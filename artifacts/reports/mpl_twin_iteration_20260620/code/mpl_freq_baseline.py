#!/usr/bin/env python3
"""Run the (b) FREQUENCY headline: matched-eigenfrequency NUTS calibration + held-out per-peak scoring across the
5 LOLO splits. Writes out/freq_baseline.json and updates out/model_registry.json with the carry-forward frequency
twin (class F0). Reuses score.py byte-identical.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mpl_freq as MF

OUT = MF.OUT; HELD = MF.HELD


def main():
    t0 = time.time()
    P = MF.precompute()
    per = []; conv_all = {}
    for h in HELD:
        train = [l for l in HELD if l != h]
        post, conv = MF.calibrate_freq(P, train)
        conv_all[h] = conv
        sc = MF.score_freq(P, h, post)
        sc["held_out"] = h; sc["convergence"] = conv
        sc["theta_median"] = {g: float(np.median(np.asarray(post["theta"])[:, i])) for i, g in enumerate(P["groups"])}
        per.append(sc)
        print(f"[{h:10s}] peaks {sc['n_peaks']} | twin |df| {sc['twin_median_df_pct']:.2f}% "
              f"(nominal {sc['nominal_fem_median_df_pct']:.2f}%, nearest-pooled {sc['nearest_pooled_peak_median_df_pct']:.2f}%) "
              f"| CRPS-skill vs pooled clim {sc['crps_skill_vs_clim_pooled']:+.2f} cov {sc['twin_coverage']:.2f} "
              f"| conv {conv['converged']} (R̂{conv['max_rhat']:.3f} ESS{conv['min_ess']:.0f})")

    def agg(key):
        v = [s[key] for s in per]
        return {"mean": float(np.mean(v)), "std": float(np.std(v)), "per_split": [round(float(x), 3) for x in v]}

    keys = ["crps_skill_vs_clim_pooled", "twin_median_df_pct", "nominal_fem_median_df_pct",
            "nearest_pooled_peak_median_df_pct", "twin_coverage", "twin_interval"]
    summary = {k: agg(k) for k in keys}
    allconv = all(c["converged"] for c in conv_all.values())
    rec = {"deliverable": "(b) FREQUENCY headline: matched-eigenfrequency NUTS twin vs climatology, 5 LOLO splits",
           "groups_calibrated": P["groups"], "alive_frac": MF.ALIVE_FRAC, "match_window": MF.MATCH_WIN,
           "band_hz": list(MF.FBAND), "per_split": per, "summary": summary,
           "all_splits_converged": bool(allconv),
           "caveat": "dense modal forest (29-71 alive modes/node) => a FEM mode sits near every measured peak; "
                     "the pooled-ensemble climatology is a WIDE (weak) bar, the nearest-pooled-peak |df| is the "
                     "fairer bar for 'does the twin add location-specific info beyond global modes'.",
           "runtime_s": round(time.time() - t0, 1)}
    (OUT / "freq_baseline.json").write_text(json.dumps(rec, indent=2))

    # update registry with F0 (carry-forward frequency twin)
    reg = json.loads((OUT / "model_registry.json").read_text()) if (OUT / "model_registry.json").exists() else {"rows": [], "rounds": []}
    f0 = {"class_id": "F0_freq_calibrated6grp",
          "hypothesis": "FREQUENCY headline: 6 K-groups calibrated on matched alive-mode eigenfrequencies (D7 pivot)",
          "changed": "headline QOI -> per-location modal frequency (identifiable); transmissibility = diagnostic",
          "n_params": len(P["groups"]) + 1,
          "nuts_converged": bool(allconv),
          "worst_rhat": float(max(c["max_rhat"] for c in conv_all.values())),
          "min_ess": float(min(c["min_ess"] for c in conv_all.values())),
          "heldout_freq_crps_skill_pooled_mean": summary["crps_skill_vs_clim_pooled"]["mean"],
          "twin_median_df_pct_mean": summary["twin_median_df_pct"]["mean"],
          "nominal_median_df_pct_mean": summary["nominal_fem_median_df_pct"]["mean"],
          "nearest_pooled_df_pct_mean": summary["nearest_pooled_peak_median_df_pct"]["mean"],
          "coverage_mean": summary["twin_coverage"]["mean"],
          "verdict": "carry-forward (frequency)"}
    reg["rows"] = [r for r in reg.get("rows", []) if r.get("class_id") != "F0_freq_calibrated6grp"] + [f0]
    reg.setdefault("rounds", []).append({"round": "0b", "classes": ["F0_freq_calibrated6grp"]})
    reg["program_verdict"] = ("YELLOW (frequency twin established as carry-forward; transmissibility-shape "
                              "uncorrelated [D6]; richer-form search pending)")
    (OUT / "model_registry.json").write_text(json.dumps(reg, indent=2))
    print(f"\nFREQUENCY baseline (mean over 5 splits): twin |df| {summary['twin_median_df_pct']['mean']:.2f}% vs "
          f"nominal {summary['nominal_fem_median_df_pct']['mean']:.2f}% vs nearest-pooled "
          f"{summary['nearest_pooled_peak_median_df_pct']['mean']:.2f}% | CRPS-skill(pooled) "
          f"{summary['crps_skill_vs_clim_pooled']['mean']:+.2f} cov {summary['twin_coverage']['mean']:.2f} | "
          f"converged {allconv} | {rec['runtime_s']}s")


if __name__ == "__main__":
    main()
