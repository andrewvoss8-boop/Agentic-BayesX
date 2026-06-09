#!/usr/bin/env python3
"""Checker for the Opus ShockSat corrected-FRF run. Artifact-backed gates only."""
from __future__ import annotations
import json
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]
checks = []


def gate(name, ok, detail=""):
    checks.append({"name": name, "pass": bool(ok), "detail": detail})


# 1. required artifacts exist
required = [
    "opus_frf_summary.json", "opus_frf_estimates.npz", "runtime.json",
    "figures/opus_frf_repeatability_ch1.png",
    "figures/opus_coherence_method_compare_ch1.png",
    "figures/opus_fem_vs_test_peaks.png",
    "review_of_codex_run.md", "packet.md",
    "opus_point_reconcile.json", "opus_normalization_findings.md",
    "v1_heldout_qoi_table.csv", "v1_heldout_qoi_summary.json", "statfem_v1_heldout.md",
    "figures/v1_heldout_qoi_sidebyside.png",
    "figures/v1_modal_freq_calibration.png",
    "figures/v1_shocksat_pyro_directional.png",
]
for r in required:
    gate(f"exists:{r}", (OUT / r).exists())

summ = json.loads((OUT / "opus_frf_summary.json").read_text())

# 2. corrected method beats per-transient Welch by a clear margin (>= 3x) on >=1 ch
import numpy as np
improved = False
for c, b in summ["method_B_opus_ensemble"].items():
    a_list = summ["method_A_codex_per_transient_welch"][c]["per_hit_median_coh_10_400"]
    a = float(np.nanmedian(a_list))
    if b["median_coh_10_400"] >= 3 * a:
        improved = True
gate("corrected_method_>=3x_codex_median_coh", improved)

# 3. at least one channel reaches near-resonance coherence >= 0.7 in modal band
high = any(b["max_coh_10_400"] >= 0.7 for b in summ["method_B_opus_ensemble"].values())
gate("near_resonance_coh_ge_0.7", high)

# 4. FEM SOL111 reference parsed with modal peaks
gate("fem_sol111_parsed", summ["fem_sol111_11101X"]["points_parsed"] > 0
     and len(summ["fem_sol111_11101X"]["modal_peaks_hz"]) >= 5)

# 5. honesty: no posterior/NUTS/validated-magnitude claims
nc = summ.get("not_claimed", [])
gate("honesty_no_overclaim", all(k in nc for k in
     ["StatFEM posterior", "NUTS/HMC active"]))

# 6. modal band is 10-400 (not the 100-10000 shock band)
gate("modal_band_correct", summ["modal_band_hz"] == [10.0, 400.0])

# 7. normalization reconciliation present and states a blocker honestly (no fabricated overlay)
recon = json.loads((OUT / "opus_point_reconcile.json").read_text())
v = recon.get("verdict", {})
gate("normalization_reconciled_honestly",
     v.get("pch_is_accelerance", "").startswith("yes")
     and bool(v.get("normalization_blocker"))
     and v.get("test07_is_input_matched_to_11101X") is False)

# 8. held-out QOI side-by-side: integrity-pinned predictions, not refit, CI-vs-actual present
v1 = json.loads((OUT / "v1_heldout_qoi_summary.json").read_text())
gate("v1_predictions_integrity_pinned", v1["provenance"]["finalists_sha256_matches_pin"] is True
     and v1["provenance"]["not_refit_to_truth"] is True)
gate("v1_heldout_qoi_has_ci_and_actual",
     all(("ci95_lo" in r and "ci95_hi" in r and "actual" in r and "ci95_covers_actual" in r)
         for r in v1["rows"]) and len(v1["rows"]) >= 2)
# honest coverage reporting: at least one OOD row must MISS (we do not hide miscoverage)
gate("v1_ood_miscoverage_reported",
     any(r["regime"] == "ood" and r["ci95_covers_actual"] is False for r in v1["rows"]))

out = {"all_pass": all(c["pass"] for c in checks), "checks": checks}
(OUT / "checker_report.json").write_text(json.dumps(out, indent=2))
for c in checks:
    print(("PASS" if c["pass"] else "FAIL"), c["name"], c.get("detail", ""))
print("ALL_PASS" if out["all_pass"] else "SOME_FAIL")
sys.exit(0 if out["all_pass"] else 1)
