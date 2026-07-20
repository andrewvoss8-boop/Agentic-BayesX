#!/usr/bin/env python3
"""Checker for the virtual-sensing-target credibility toy (E1-E4).

Green/Yellow/Red per AGENTS.md. Exit non-zero ONLY on RED. YELLOW = documented, non-fatal.
"""
import json
import os
import sys

gates = []


def gate(name, status, detail):
    gates.append({"gate": name, "status": status, "detail": detail})


def jload(p):
    return json.load(open(p)) if os.path.exists(p) else None


def conv_status(nuts):
    ok = nuts["max_rhat"] <= 1.05 and nuts["min_ess"] >= 200 and nuts["div_frac"] < 0.02
    return ("GREEN" if ok else "YELLOW",
            f"R-hat {nuts['max_rhat']:.3f}, ESS {nuts['min_ess']:.0f}, div {nuts['div_frac']:.3f}")


# ---- required artifacts ----
required = [
    "priority_deliverables.md", "decisions_log.md", "question_framing.md",
    "assumptions_ledger.md", "quantity_contracts.md", "packet.md", "run_all.sh",
    "code/core.py", "code/nuts_update.py", "code/viz.py",
    "code/exp1_discriminating.py", "code/exp2_baselines_sweep.py",
    "code/exp3_config_trend_identifiability.py", "code/exp4_biased_reconstruction.py",
    "out/exp1_summary.json", "out/exp2_summary.json", "out/exp3_summary.json", "out/exp4_summary.json",
    "figures/exp1_masked_prediction.png", "figures/exp1_qoi_coverage.png",
    "figures/exp2_baselines_sweep.png", "figures/exp3_softening_trend.png",
    "figures/exp3_identifiability.png", "figures/exp4_biased_reconstruction.png",
]
for p in required:
    gate(f"artifact:{p}", "GREEN" if os.path.exists(p) else "RED", p)

# ---- E1 discriminating ----
e1 = jload("out/exp1_summary.json")
if e1:
    s, d = conv_status(e1["nuts_diagnostics"])
    gate("E1_nuts_convergence", s, d)
    bq = e1["bayes_masked_qoi_coverage"]; dq = e1["det_masked_qoi_coverage"]
    gate("E1_bayes_covers_masked_qoi", "GREEN" if bq["covered"] == bq["n"] else "YELLOW",
         f"Bayes {bq['covered']}/{bq['n']} vs deterministic {dq['covered']}/{dq['n']} masked-channel QOIs covered")
    gate("E1_uq_beats_point_estimate", "GREEN" if bq["covered"] > dq["covered"] else "YELLOW",
         f"discrepancy-aware UQ covers more masked QOIs than the deterministic point estimate")
    hc = e1["heldout_hf_logmag_coverage"]
    gate("E1_heldout_hf_coverage", "GREEN" if hc["fraction"] >= 0.85 else "YELLOW",
         f"{hc['covered']}/{hc['n']} = {hc['fraction']:.2f} high-freq held-out lines covered")

# ---- E2 baselines + sweep ----
e2 = jload("out/exp2_summary.json")
if e2:
    gate("E2_all_nuts_converged", "GREEN" if e2["all_nuts_converged"] else "YELLOW",
         "all swept-level NUTS runs cleared the convergence gate"
         if e2["all_nuts_converged"] else "one or more swept levels did not converge (flagged on figure)")
    # FAU-Up tracks reconstruction error in the plausible range; physics floor exists.
    lo = e2["levels"][0]; hi = e2["levels"][-1]
    gate("E2_fau_tracks_recon_error", "GREEN" if lo["fau_up_err_db"] < e2["meas_up_floor_db"] else "YELLOW",
         f"good-level FAU-Up err {lo['fau_up_err_db']:.1f} dB below Meas-Up floor {e2['meas_up_floor_db']:.1f} dB")
    cov_ok = all(r["bayes_masked_qoi_covered"] == r["bayes_masked_qoi_n"] for r in e2["levels"] if r["nuts_converged"])
    gate("E2_bayes_coverage_maintained", "GREEN" if cov_ok else "YELLOW",
         "Bayesian masked-channel coverage maintained across converged reconstruction-error levels")

# ---- E3 trend + identifiability ----
e3 = jload("out/exp3_summary.json")
if e3:
    gate("E3_all_nuts_converged", "GREEN" if e3["all_nuts_converged"] else "YELLOW", "per-config NUTS convergence")
    gate("E3_softening_trend_recovered", "GREEN" if e3["trend"]["softening_monotonic_and_separated"] else "YELLOW",
         f"aggregate mean-alpha A1>A2>A3 with separated 95% intervals: medians {['%.3f'%v for v in e3['trend']['mean_alpha_A1A2A3_median']]}")
    ratio = e3["per_mode_vs_aggregate"]["local_mode_width_vs_observed_modes_ratio"]
    gate("E3_failed_sensor_mode_least_identified", "GREEN" if ratio > 2.0 else "YELLOW",
         f"failed-sensor local-mode alpha posterior is {ratio:.1f}x wider than observed modes (effective indicator)")

# ---- E4 coherent bias stress ----
e4 = jload("out/exp4_summary.json")
if e4:
    gate("E4_all_nuts_converged", "GREEN" if e4["all_nuts_converged"] else "YELLOW", "all four E4 NUTS runs converge")
    h = e4["headline"]
    gate("E4_correlated_unbiased_control_recovers_alpha4",
         "GREEN" if h["correlated_unbiased_control_covers_alpha4"] else "RED",
         "unbiased reconstruction + correlated discrepancy recovers true alpha_4 (method validated)")
    fooled = (not h["iid_covers_alpha4"]) and (not h["correlated_biased_covers_alpha4"])
    gate("E4_coherent_bias_confounds_parameter", "GREEN" if fooled else "YELLOW",
         "a coherent reconstruction bias is confounded with the failed-sensor mode stiffness; "
         "neither iid nor correlated UQ recovers alpha_4 under the bias")
    gate("E4_qoi_vs_parameter_distinction", "GREEN" if (h["iid_covers_qoi"] and h["correlated_covers_qoi"]) else "YELLOW",
         "amplitude QOI stays covered while the parameter (physical sign) is wrong: QOI coverage != parameter recovery")

# ---- honest scope (always yellow) ----
gate("scope:surrogate_not_FAU_network", "YELLOW",
     "Virtual ground truth is a LABELED surrogate calibrated to the paper's masked-channel residual, "
     "NOT the FAU deep network; we test the updating stage + its deferred UQ, not the network.")
gate("scope:single_realization_effective_indicators", "YELLOW",
     "One synthetic realization per config; no test/flight variability; alpha/beta/gamma are effective "
     "ROM-level indicators, not microscopic joint measurements (the paper's own caveat).")

# ---- image legibility ----
for tag in ["exp1", "exp2", "exp3", "exp4"]:
    qa = jload(f"image_qa_{tag}.json")
    if qa is not None:
        gate(f"image_legibility:{tag}", "GREEN" if qa["pass"] else "YELLOW",
             f"{qa['n_figures']} figures; failures={qa['failures']}")

order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
overall = max((g["status"] for g in gates), key=lambda x: order[x]) if gates else "RED"
counts = {k: sum(g["status"] == k for g in gates) for k in order}
report = {"overall": overall, "counts": counts, "gates": gates}
json.dump(report, open("checker_report.json", "w"), indent=2)
print(json.dumps(report, indent=2))
print(f"\nOVERALL {overall}  GREEN {counts['GREEN']} / YELLOW {counts['YELLOW']} / RED {counts['RED']}")
sys.exit(1 if overall == "RED" else 0)
