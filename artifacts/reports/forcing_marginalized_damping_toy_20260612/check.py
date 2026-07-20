#!/usr/bin/env python3
"""Checker for forcing-marginalized amplitude-dependent damping toy.

Exit non-zero only on RED. YELLOW means documented, non-fatal limitation.
"""
import json
import os
import sys

gates = []


def gate(name, status, detail):
    gates.append({"gate": name, "status": status, "detail": detail})


def exists(path):
    return os.path.exists(path)


required = [
    "priority_deliverables.md",
    "decisions_log.md",
    "assumptions_ledger.md",
    "quantity_contracts.md",
    "packet.md",
    "run_all.sh",
    "code/run_toy.py",
    "out/summary.json",
    "out/posterior_samples.npz",
    "figures/fig1_forcing_cancellation.png",
    "figures/fig2_ratio_fit.png",
    "figures/fig3_damping_posterior.png",
    "figures/fig4_qoi_posterior.png",
    "image_qa.json",
]
for path in required:
    gate(f"artifact_{path}", "GREEN" if exists(path) else "RED", path)

if exists("out/summary.json"):
    s = json.load(open("out/summary.json"))
    fmax = s["forcing_cancellation"]["max_relative_error"]
    gate(
        "forcing_integrated_out",
        "GREEN" if fmax < 1e-10 else "RED",
        f"hidden-force response ratio equals direct transfer ratio; max relative error {fmax:.2e}",
    )

    d = s["nuts_diagnostics"]
    conv = d["max_rhat"] <= 1.05 and d["min_ess"] >= 200 and d["div_frac"] < 0.02
    gate(
        "nuts_convergence",
        "GREEN" if conv else "YELLOW",
        f"R-hat {d['max_rhat']:.3f}; ESS {d['min_ess']:.0f}; div frac {d['div_frac']:.3f}",
    )

    p = s["damping_learning"]
    gate(
        "high_amplitude_damping_detected",
        "GREEN" if p["prob_zeta_high_gt_low"] >= 0.95 else "YELLOW",
        f"P(zeta_high > zeta_low) = {p['prob_zeta_high_gt_low']:.3f}",
    )
    gate(
        "effective_damping_truth_covered",
        "GREEN" if p["truth_low_covered"] and p["truth_high_covered"] else "YELLOW",
        f"truth covered: low={p['truth_low_covered']} high={p['truth_high_covered']}",
    )

    c = s["heldout_ratio_coverage"]
    gate(
        "heldout_ratio_coverage",
        "GREEN" if c["coverage_fraction"] >= 0.85 else "YELLOW",
        f"{c['covered']}/{c['n']} clean held-out log-ratio values covered by 95% posterior bands",
    )

    q = s["qoi_coverage"]
    gate(
        "qoi_coverage",
        "GREEN" if q["covered"] == q["n"] else "YELLOW",
        f"{q['covered']}/{q['n']} damping-dependent QOIs cover the synthetic truth",
    )

    gate(
        "nonlinear_law_not_identified",
        "YELLOW",
        "Designed limitation: the true slip/friction law is hidden; only equivalent damping at tested amplitudes is inferred.",
    )

if exists("image_qa.json"):
    qa = json.load(open("image_qa.json"))
    gate(
        "image_legibility_proxy",
        "GREEN" if qa["pass"] else "YELLOW",
        f"{qa['n_figures']} figures checked; failures={qa['failures']}",
    )

order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
overall = max((g["status"] for g in gates), key=lambda x: order[x])
counts = {k: sum(g["status"] == k for g in gates) for k in order}
report = {"overall": overall, "counts": counts, "gates": gates}
json.dump(report, open("checker_report.json", "w"), indent=2)
print(json.dumps(report, indent=2))
sys.exit(1 if overall == "RED" else 0)
