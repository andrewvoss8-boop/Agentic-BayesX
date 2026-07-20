#!/usr/bin/env python3
"""IMMUTABLE checker — StatFEM consistency toy (Experiment A).

Written BEFORE results (anti-cheating; AGENTS.md). Encodes GREEN/YELLOW/RED acceptance per the
Result Status Standard and this study's task card (sec 6, 8). Exits non-zero ONLY on RED.

What this checker can certify: that the consistency / discretization-invariance CRITERION was built
and REPORTED WITH NUMBERS for all three constructions (M-lik, M-statfem, M-ift) on a solver-validated
testbed with gate-converged (or labelled) NUTS posteriors. It deliberately does NOT hard-code the
direction of the verdict (drift vs invariant) — pre-deciding the answer is forbidden. The scientific
verdict is reported from the numbers; only the SCAFFOLDING (numbers exist, solver validated, sampler
converged, testbed positive control passes) is gated.
"""
import glob
import hashlib
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

# ---- hashes of prior immutable / scaffold files (must be UNCHANGED) --------
PRIOR_HASHES = {
    "../confidently_wrong_modelform_20260616/check.py":
        "3fff858f08c459d4ceef5031dcca97bc31ffdd5767f2044354486ff1dc6b8ef0",
    "../paper_virtual_sensing_uq_toy_20260613/code/nuts_update.py":
        "0694d7879dd952c8838469b7adbcc926ec8a5b37e28f0b20ba66885a6dbae101",
}

# ---- acceptance constants -------------------------------------------------
RHAT_MAX, ESS_MIN, DIV_MAX = 1.05, 200, 0.02
THETA_TRUE = 1.15
SOLVER_TOL = 1e-3        # max rel-err of finest discretization vs analytic truth
RATE_LO, RATE_HI = 1.5, 2.6   # expected ~h^2 (2nd-order) convergence rate band
CONTROL_BIAS_TOL = 0.04  # at eps=0, finest discretization + largest n: |theta_mean - theta_true|
NOMINAL_COV = 0.95

gates = []


def gate(name, status, detail):
    gates.append({"gate": name, "status": status, "detail": detail})


def jload(p):
    return json.load(open(p)) if os.path.exists(p) else None


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ---- required artifacts ---------------------------------------------------
required = [
    "decisions_log.md", "priority_deliverables.md", "question_framing.md",
    "assumptions_ledger.md", "quantity_contracts.md", "packet.md", "run_all.sh", "runtime.json",
    "code/core.py", "code/nuts_marg.py", "code/statfem.py", "code/solver_validation.py",
    "code/run_sweep.py", "code/aggregate.py", "code/viz.py", "code/image_qa.py",
    "code/fig_solver.py", "code/fig_schematic.py", "code/fig_money.py",
    "code/fig_concentration.py", "code/fig_coverage.py", "code/fig_identifiability.py",
    "figures/figV_solver_convergence.png", "figures/figS_schematic.png",
    "figures/figA_money_theta_vs_knob.png", "figures/figC1_concentration.png",
    "figures/figC3_coverage.png", "figures/figI_identifiability.png",
    "out/solver_validation.json", "out/sweep_summary.json", "out/identifiability.json",
    "out/image_qa.json", "out/text_overlap.json",
]
for p in required:
    gate(f"artifact:{p}", "GREEN" if os.path.exists(p) else "RED", p)

# ---- integrity: prior immutable / scaffold files unchanged; core fresh -----
for p, h in PRIOR_HASHES.items():
    if not os.path.exists(p):
        gate(f"integrity:prior_unchanged:{os.path.basename(p)}", "YELLOW", f"prior file absent ({p})")
    else:
        ok = sha(p) == h
        gate(f"integrity:prior_unchanged:{os.path.basename(p)}", "GREEN" if ok else "RED",
             "byte-identical to the recorded hash (prior immutable/scaffold NOT edited in place)"
             if ok else f"HASH CHANGED for {p} — a prior immutable/scaffold file was edited (forbidden)")

if os.path.exists("code/core.py"):
    src = open("code/core.py").read()
    fresh = ("paper_virtual" not in src) and ("confidently_wrong" not in src) and ("import core" not in src)
    gate("integrity:core_fresh", "GREEN" if fresh else "YELLOW",
         "core.py is a fresh, self-contained rod model (does not import/copy a sibling study's scaffold)")
else:
    gate("integrity:core_fresh", "RED", "code/core.py missing")

# ---- solver validation FIRST (P4): forward -> analytic truth ---------------
sv = jload("out/solver_validation.json")
if sv is None:
    gate("solver:validated_against_analytic", "RED", "out/solver_validation.json missing — cannot make any "
         "consistency claim without solver validation")
else:
    def _ok(block):
        err = block.get("max_rel_err", [])
        rate = block.get("rate_est", None)
        finest_ok = len(err) > 0 and err[-1] < SOLVER_TOL
        decreasing = len(err) >= 2 and err[-1] < err[0]
        rate_ok = rate is not None and RATE_LO <= rate <= RATE_HI
        return finest_ok and decreasing, rate_ok, (err[-1] if err else None), rate
    for key, label in (("fd", "FD operator (M-lik/M-ift)"), ("fe", "FE eigensolve (M-statfem)")):
        b = sv.get(key)
        if not b:
            gate(f"solver:{key}_converges", "RED", f"{label} convergence block missing")
            continue
        conv_ok, rate_ok, finest, rate = _ok(b)
        status = "GREEN" if (conv_ok and rate_ok) else ("YELLOW" if conv_ok else "RED")
        gate(f"solver:{key}_converges", status,
             f"{label}: finest max rel-err {finest:.2e} (< {SOLVER_TOL}? {finest is not None and finest < SOLVER_TOL}); "
             f"rate~{rate:.2f} (in [{RATE_LO},{RATE_HI}]? {rate_ok})")

# ---- NUTS convergence over every cell -------------------------------------
cells = [json.load(open(p)) for p in glob.glob("out/cell_*.json")]
nuts_cells = [c for c in cells if "nuts" in c]
if not nuts_cells:
    gate("convergence:all_cells", "RED", "no NUTS cells found")
else:
    def conv(d):
        return d["max_rhat"] <= RHAT_MAX and d["min_ess"] >= ESS_MIN and d["div_frac"] < DIV_MAX
    nonconv = [c for c in nuts_cells if not conv(c["nuts"])]
    if nonconv:
        # label, do not silently pass; not-yet-converged cells are YELLOW (cannot be used as evidence)
        worst = max(nonconv, key=lambda c: c["nuts"]["max_rhat"])
        gate("convergence:all_cells", "YELLOW",
             f"{len(nonconv)}/{len(nuts_cells)} NUTS cells NOT converged (labelled not-yet-converged); "
             f"worst R-hat {worst['nuts']['max_rhat']:.2f} @ {worst.get('construction')}/{worst.get('knob')}="
             f"{worst.get('level')}/eps={worst.get('eps')}/n={worst.get('n')}")
    else:
        w = max(nuts_cells, key=lambda c: c["nuts"]["max_rhat"])["nuts"]
        gate("convergence:all_cells", "GREEN",
             f"{len(nuts_cells)} NUTS cells all cleared the gate; worst R-hat {w['max_rhat']:.3f}, "
             f"min ESS {min(c['nuts']['min_ess'] for c in nuts_cells):.0f}, "
             f"max div-frac {max(c['nuts']['div_frac'] for c in nuts_cells):.3f}")

# ---- the consistency criterion: NUMBERS for all 3 constructions ------------
SS = jload("out/sweep_summary.json")
CONSTRUCTIONS = ["M-lik", "M-statfem", "M-ift"]
if SS is None:
    gate("consistency:summary_present", "RED", "out/sweep_summary.json missing")
else:
    gate("consistency:summary_present", "GREEN", f"theta_true={SS.get('theta_true')}")
    cons = SS.get("constructions", {})
    verdicts = SS.get("verdicts", {})
    for cn in CONSTRUCTIONS:
        c = cons.get(cn)
        if not c:
            gate(f"consistency:{cn}_numbers", "RED", f"{cn} block missing from summary")
            continue
        # C2: a discretization-sensitivity NUMBER for every knob x eps
        c2_ok = True
        c2_msgs = []
        for kn, kb in c.get("knobs", {}).items():
            for eps, eb in kb.get("eps", {}).items():
                v = eb.get("c2_spread")
                if v is None:
                    c2_ok = False
                else:
                    c2_msgs.append(f"{kn}@eps{eps}: spread(theta_mean)={v:.4f}")
        # C1: concentration final SD + bias present at each eps
        c1_ok = all(("final_sd" in cb and "abs_bias_final" in cb)
                    for cb in c.get("concentration", {}).values()) and len(c.get("concentration", {})) > 0
        # C3: a held-out coverage number somewhere in the knob sweeps
        cov_vals = [eb.get("coverage_heldout") for kb in c.get("knobs", {}).values()
                    for eb in kb.get("eps", {}).values() if eb.get("coverage_heldout") is not None]
        c3_ok = len(cov_vals) > 0
        numbers_ok = c2_ok and c1_ok and c3_ok and bool(verdicts.get(cn))
        gate(f"consistency:{cn}_numbers", "GREEN" if numbers_ok else "RED",
             f"C1 conc (final_sd+bias) {'OK' if c1_ok else 'MISSING'}; C2 [{'; '.join(c2_msgs) if c2_msgs else 'MISSING'}]; "
             f"C3 coverage {'OK' if c3_ok else 'MISSING'}; verdict {'present' if verdicts.get(cn) else 'MISSING'}")

    # testbed positive control: at least one construction concentrates on theta_true at eps=0
    control = []
    for cn in CONSTRUCTIONS:
        cc = cons.get(cn, {}).get("concentration", {}).get("0.0")
        if cc and "abs_bias_final" in cc:
            ok = cc["abs_bias_final"] <= CONTROL_BIAS_TOL
            control.append((cn, ok, cc["abs_bias_final"], cc.get("final_sd")))
            gate(f"control:{cn}_concentrates_eps0",
                 "GREEN" if ok else "YELLOW",
                 f"eps=0 control: {cn} |theta_mean-theta_true|={cc['abs_bias_final']:.4f} "
                 f"(<= {CONTROL_BIAS_TOL}? {ok}); final SD {cc.get('final_sd'):.4f} "
                 f"(a YELLOW here is a FINDING: this construction misses even the no-error control)")
    if control:
        gate("control:testbed_valid",
             "GREEN" if any(ok for _, ok, _, _ in control) else "RED",
             "at least one construction concentrates on theta_true at eps=0 (testbed + solver are sound)"
             if any(ok for _, ok, _, _ in control) else
             "NO construction concentrates at eps=0 — testbed/solver suspect (cannot attribute drift to method)")
    else:
        gate("control:testbed_valid", "RED", "no eps=0 concentration results found")

    # verdict per construction must be stated (text), traceable to the numbers
    miss = [cn for cn in CONSTRUCTIONS if not verdicts.get(cn)]
    gate("consistency:verdict_per_construction",
         "GREEN" if not miss else "RED",
         "per-construction verdict stated" if not miss else f"missing verdict for {miss}")

# ---- identifiability (P5): theta->observable sensitivity reported ----------
idf = jload("out/identifiability.json")
if idf and idf.get("eps"):
    weak = any(b.get("weak") for b in idf["eps"].values())
    gate("identifiability:sensitivity_reported", "GREEN",
         f"dω/dθ reported per mode/eps; weak-identifiability flagged at some eps: {weak}")
else:
    gate("identifiability:sensitivity_reported", "RED", "out/identifiability.json missing/empty")

# ---- figures: tufte lint + image QA + text-overlap auditor ----------------
fig_scripts = ["fig_solver", "fig_schematic", "fig_money", "fig_concentration",
               "fig_coverage", "fig_identifiability"]
for s in fig_scripts:
    log = f"logs/tufte_{s}.txt"
    if os.path.exists(log):
        txt = open(log).read()
        bad = bool(re.search(r"POTENTIAL ISSUES|\bERROR\b", txt)) and "No obvious" not in txt
        gate(f"tufte_lint:{s}", "GREEN" if not bad else "YELLOW",
             "clean" if not bad else "tufte_lint flagged issues (see log)")
    else:
        gate(f"tufte_lint:{s}", "RED", f"missing {log}")

qa = jload("out/image_qa.json")
if qa is not None:
    ok = qa.get("ALL_OK", False)
    bad = [k for k, v in qa.items() if isinstance(v, dict) and not v.get("ok", True)]
    gate("image_qa:legibility", "GREEN" if ok else "RED",
         "pixel legibility: all pass" if ok else f"pixel legibility FAIL {bad}")
else:
    gate("image_qa:legibility", "RED", "out/image_qa.json missing")

to = jload("out/text_overlap.json")
if to is not None:
    nbad = sum(len(v) for v in to.values()) if isinstance(to, dict) else 0
    gate("text_overlap:auditor", "GREEN" if nbad == 0 else "RED",
         f"save-time bbox text-overlap auditor: {nbad} overlapping text pair(s)")
else:
    gate("text_overlap:auditor", "RED", "out/text_overlap.json missing")

# ---- doc: method summary + data count -------------------------------------
pk = open("packet.md").read() if os.path.exists("packet.md") else ""
gate("doc:method_summary_present",
     "GREEN" if ("Method summary" in pk or "Method Summary" in pk) else "RED",
     "packet has a method-summary section (where physics lives + equations per construction)")
gate("doc:data_count_present",
     "GREEN" if ("one synthetic" in pk.lower() or "single synthetic" in pk.lower()
                 or "synthetic realization" in pk.lower()) else "RED",
     "packet states the synthetic-realization / replicate count")
gate("doc:references_present",
     "GREEN" if all(x in pk for x in ["1905.06391", "2301.07609", "2306.02150"]) else "RED",
     "packet cites statFEM 1905.06391, PIFT 2301.07609, IFT 2306.02150")

# ---- honest scope (always yellow) -----------------------------------------
gate("scope:single_realization", "YELLOW",
     "one synthetic realization per replicate; no flight-to-flight / build-to-build variability modeled")
gate("scope:surrogate_error_model", "YELLOW",
     "model-form error is a SURROGATE (Winkler elastic foundation), not a measured real-structure discrepancy")
gate("scope:toy_not_universal", "YELLOW",
     "verdicts are for THIS minimal rod toy; they evaluate the constructions' behaviour, not a universal proof")

order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
overall = max((g["status"] for g in gates), key=lambda x: order[x]) if gates else "RED"
counts = {k: sum(g["status"] == k for g in gates) for k in order}
report = {"overall": overall, "counts": counts, "theta_true": THETA_TRUE, "gates": gates}
json.dump(report, open("checker_report.json", "w"), indent=2)
for g in gates:
    print(f"[{g['status']:6}] {g['gate']}: {g['detail']}")
print(f"\nOVERALL {overall}  GREEN {counts['GREEN']} / YELLOW {counts['YELLOW']} / RED {counts['RED']}")
sys.exit(1 if overall == "RED" else 0)
