#!/usr/bin/env python3
"""IMMUTABLE checker — StatFEM ShockSat held-out-QOI evaluation (Experiment B).

Written BEFORE results (task card §11). Encodes GREEN/YELLOW/RED acceptance per AGENTS.md Result Status
Standard and the task card. Exits non-zero ONLY on RED. YELLOW = documented, non-fatal, never "success".

What this checker can certify: that the held-out-sensor-QOI trust test is BUILT and REPORTED WITH NUMBERS for
naive / StatFEM-iid / Schneider / orthogonal across 5 bias combos, with convergence labeled, θ tied to the
strain-energy/FIM identifiability gate, the reduced FRF validated against a fuller solve, and a scorecard.
It does NOT force StatFEM to win — the direction the coverage numbers fall is the science (task §1, §14).
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

gates = []


def gate(name, status, detail):
    gates.append({"gate": name, "status": status, "detail": detail})


def jload(p):
    return json.load(open(p)) if os.path.exists(p) else None


def sha256(p):
    h = hashlib.sha256()
    h.update(open(p, "rb").read())
    return h.hexdigest()


# ---- acceptance constants -------------------------------------------------
RHAT_MAX, ESS_MIN, DIV_MAX = 1.05, 200, 0.02
NOMINAL = 0.95
NAIVE_MALADY_MAX = 0.80    # naive mean held-out QOI coverage must fall to <= this (materially below nominal)
DISC_QUANT_MIN = 0          # StatFEM coverage must be reported (numbers present); direction is a finding
REDUCE_FRF_TOL = 0.03       # reduced-vs-full FRF max relative error at QOI peaks (discretization gate)
N_COMBOS = 5
ARMS = ["M0", "M1", "M2", "M3"]


def conv_ok(n):
    return (n["max_rhat"] <= RHAT_MAX and n["min_ess"] >= ESS_MIN and n["div_frac"] < DIV_MAX)


# ---- required artifacts ---------------------------------------------------
required = [
    "decisions_log.md", "priority_deliverables.md", "question_framing.md",
    "assumptions_ledger.md", "quantity_contracts.md", "packet.md", "run_all.sh", "runtime.json",
    "code/core.py", "code/nuts_arms.py", "code/predict.py", "code/run_sweep.py",
    "code/identifiability.py", "code/discretization.py", "code/sensitivity.py", "code/aggregate.py",
    "code/viz.py", "code/image_qa.py",
    "code/fig_schematic.py", "code/fig_coverage.py", "code/fig_arm_comparison.py",
    "code/fig_theta_recovery.py", "code/fig_heldout_frf.py", "code/fig_identifiability.py",
    "out/config.json", "out/coverage_summary.json", "out/arm_comparison.json",
    "out/identifiability.json", "out/discretization.json", "out/scorecard.json",
    "out/image_qa.json", "out/text_overlap.json",
    "figures/fig_schematic.png", "figures/figA_heldout_qoi_coverage.png",
    "figures/figB_arm_comparison.png", "figures/figC_theta_recovery.png",
    "figures/figD_heldout_frf_bands.png", "figures/figE_identifiability.png",
]
for p in required:
    gate(f"artifact:{p}", "GREEN" if os.path.exists(p) else "RED", p)

# ---- integrity: reused FEM asset is the modal twin's, unedited -------------
MT = "../shocksat_fem_modal_twin_20260609"
try:
    a = sha256("data/reduced_blocks.npz")
    b = sha256(f"{MT}/matrices/reduced_blocks.npz")
    gate("integrity:reduced_blocks_copied_unedited", "GREEN" if a == b else "RED",
         f"data/reduced_blocks.npz SHA == modal-twin original ({a[:12]}...)" if a == b
         else "reduced_blocks.npz DIFFERS from the modal-twin original (edited copy = integrity violation)")
except FileNotFoundError as e:
    gate("integrity:reduced_blocks_copied_unedited", "RED", f"cannot verify: {e}")

# ---- anti-cheating: coupled tray model NOT used (task §3) ------------------
tray_hits = []
for p in glob.glob("code/*.py"):
    txt = open(p).read()
    if "shocksat_tray_coupled" in txt or "tray_coupled" in txt:
        tray_hits.append(os.path.basename(p))
cfg = jload("out/config.json")
prov_ok = bool(cfg and cfg.get("testbed") == "plain_shocksat_9group" and not cfg.get("uses_tray", False))
gate("anti_cheat:no_coupled_tray_model",
     "GREEN" if (not tray_hits and prov_ok) else "RED",
     "plain-ShockSat only; no coupled-tray reference in code; config provenance = plain_shocksat_9group"
     if (not tray_hits and prov_ok) else f"FORBIDDEN coupled-tray usage detected: {tray_hits}; prov_ok={prov_ok}")

# ---- load all main cells (combo x arm) ------------------------------------
cells = [json.load(open(p)) for p in glob.glob("out/cell_*.json")]
main = [c for c in cells if not c.get("sensitivity", False)]


def pick(arm):
    return sorted([c for c in main if c["arm"] == arm], key=lambda c: c["combo_idx"])


# ---- grid completeness: 5 combos x 4 arms ---------------------------------
have = {(c["combo_idx"], c["arm"]) for c in main}
missing = [(ci, a) for ci in range(1, N_COMBOS + 1) for a in ARMS if (ci, a) not in have]
gate("grid:5combos_x_4arms_present", "GREEN" if not missing else "RED",
     f"{len(have)}/{N_COMBOS*len(ARMS)} (combo,arm) cells present"
     + ("" if not missing else f"; MISSING {missing}"))

# ---- convergence: every NUTS arm converged OR labeled not-yet-converged ----
nuts_cells = [c for c in main if "nuts" in c]
nonconv = [c for c in nuts_cells if not conv_ok(c["nuts"])]
if nuts_cells:
    if not nonconv:
        worst = max(nuts_cells, key=lambda c: c["nuts"]["max_rhat"])
        gate("convergence:all_arms_converged", "GREEN",
             f"all {len(nuts_cells)} NUTS cells cleared the gate; worst R-hat "
             f"{worst['nuts']['max_rhat']:.3f}, min ESS {min(c['nuts']['min_ess'] for c in nuts_cells):.0f}, "
             f"max div-frac {max(c['nuts']['div_frac'] for c in nuts_cells):.3f}")
    else:
        # honest non-convergence is YELLOW (labeled), NOT red — but only if the cell flags converged=False
        undoc = [c for c in nonconv if c.get("converged", False)]
        if undoc:
            gate("convergence:undocumented_nonconvergence", "RED",
                 f"{len(undoc)} cell(s) report converged=True but FAIL the gate (undocumented non-convergence)")
        for c in nonconv:
            n = c["nuts"]
            gate(f"convergence:{c['combo_idx']}_{c['arm']}", "YELLOW",
                 f"NOT converged (labeled): R-hat {n['max_rhat']:.3f}, ESS {n['min_ess']:.0f}, "
                 f"div {n['div_frac']:.3f}; intervals not-trustworthy")
        gate("convergence:summary", "YELLOW",
             f"{len(nuts_cells)-len(nonconv)}/{len(nuts_cells)} NUTS cells converged; "
             f"{len(nonconv)} labeled not-yet-converged")
else:
    gate("convergence:all_arms_converged", "RED", "no NUTS cells found")

# ---- coverage numbers present for ALL cells (peak + band) ------------------
cov_missing = []
for c in main:
    hc = c.get("heldout_coverage", {})
    if not (hc.get("peak", {}).get("frac") is not None and hc.get("band", {}).get("frac") is not None):
        cov_missing.append((c["combo_idx"], c["arm"]))
gate("coverage:numbers_present_all_cells", "GREEN" if not cov_missing else "RED",
     "held-out QOI coverage (peak + band) reported with numbers for every cell"
     if not cov_missing else f"coverage numbers MISSING for {cov_missing} (a coverage claim without numbers = RED)")

# ---- money result: per-arm coverage distribution over the 5 combos ---------
cov = jload("out/coverage_summary.json")
if cov and all(a in cov.get("by_arm", {}) for a in ARMS):
    okdist = all(len(cov["by_arm"][a].get("per_combo_combined", [])) == N_COMBOS for a in ARMS)
    gate("money:coverage_distribution_over_5_combos", "GREEN" if okdist else "RED",
         "per-arm held-out-QOI coverage reported as a distribution over all 5 combos"
         if okdist else "coverage_summary missing per-combo distribution for some arm")
else:
    gate("money:coverage_distribution_over_5_combos", "RED", "out/coverage_summary.json incomplete")

# ---- malady: naive (M0) confidently wrong where injected error is large ----
if cov and "M0" in cov.get("by_arm", {}):
    m0 = cov["by_arm"]["M0"]
    m0_mean = m0.get("mean_combined")
    # confidently wrong = low coverage AND tight bands relative to a StatFEM arm
    m0_lt = (m0_mean is not None and m0_mean <= NAIVE_MALADY_MAX)
    gate("malady:naive_confidently_wrong",
         "GREEN" if m0_lt else "YELLOW",
         f"naive (M0) mean held-out-QOI coverage over 5 combos = {m0_mean:.2f} "
         f"(<= {NAIVE_MALADY_MAX} ? {m0_lt}); injected model-form error is {'NOT ' if not m0_lt else ''}"
         f"large enough to break naive coverage" + ("" if m0_lt else " (documented: θ absorbed it / honest)"))
else:
    gate("malady:naive_confidently_wrong", "RED", "naive coverage summary missing")

# ---- cure quantified + iid/Schneider/orthogonal comparison reported --------
acmp = jload("out/arm_comparison.json")
if acmp and all(a in acmp.get("arms", {}) for a in ARMS):
    have_cov = all(acmp["arms"][a].get("mean_combined_coverage") is not None for a in ARMS)
    gate("cure:statfem_d_coverage_quantified", "GREEN" if have_cov else "RED",
         "StatFEM-iid/Schneider/orthogonal held-out coverage quantified vs naive"
         if have_cov else "arm_comparison missing coverage for some arm")
    gate("comparison:iid_schneider_orthogonal_reported", "GREEN" if have_cov else "RED",
         "iid vs Schneider vs orthogonal comparison reported with numbers"
         if have_cov else "comparison numbers missing")
    # FINDING (verdict, either direction = honest): does ANY StatFEM arm restore coverage?
    best = max((acmp["arms"][a]["mean_combined_coverage"] for a in ("M1", "M2", "M3")), default=0.0)
    restored = best >= 0.90
    gate("finding:does_d_restore_coverage", "GREEN" if restored else "YELLOW",
         f"best StatFEM-arm mean coverage = {best:.2f} ({'restores' if restored else 'does NOT fully restore'} "
         f"held-out-QOI coverage); this is the science verdict, reported whichever way it falls")
else:
    gate("cure:statfem_d_coverage_quantified", "RED", "out/arm_comparison.json incomplete")

# ---- θ recovery tied to the strain-energy / FIM identifiability gate -------
idf = jload("out/identifiability.json")
if idf and "strain_energy" in idf and "fim" in idf:
    gate("identifiability:strain_energy_and_fim_reported", "GREEN",
         f"per-group modal strain-energy table ({len(idf['strain_energy'])} groups) + FRF-FIM eigen-view "
         f"({idf['fim'].get('n_above_prior','?')} combos above prior precision) reported BEFORE θ claims")
    # θ recovery cells must carry a 'covered' + 'informed' flag for every group
    bad = [c for c in main if "theta" not in c or any("covered" not in t or "informed" not in t
                                                      for t in c.get("theta", []))]
    gate("identifiability:theta_recovery_flags_present", "GREEN" if not bad else "RED",
         "every cell reports per-group θ covered + informed flags"
         if not bad else f"{len(bad)} cell(s) missing θ recovery flags")
else:
    gate("identifiability:strain_energy_and_fim_reported", "RED", "out/identifiability.json incomplete")

# ---- discretization: reduced FRF validated against a fuller solve ----------
dz = jload("out/discretization.json")
if dz and "reduced_vs_full" in dz:
    rvf = dz["reduced_vs_full"]
    err = rvf.get("max_rel_err_at_peaks")
    ok = (err is not None and err <= REDUCE_FRF_TOL)
    gate("discretization:reduced_frf_validated", "GREEN" if ok else "RED",
         f"reduced 74-mode FRF vs full-order direct solve at QOI peaks: max rel err {err:.4f} "
         f"(<= {REDUCE_FRF_TOL} ? {ok})" if err is not None
         else "reduced-vs-full FRF validation MISSING (task §11 RED: reduced FRF not validated)")
    if "grid_refine" in dz:
        gr = dz["grid_refine"].get("max_qoi_rel_shift")
        gate("discretization:grid_and_truncation_refine", "GREEN" if (gr is not None and gr <= 0.02) else "YELLOW",
             f"grid/truncation refinement max QOI rel shift {gr}")
else:
    gate("discretization:reduced_frf_validated", "RED", "out/discretization.json missing reduced_vs_full")

# ---- scorecard present -----------------------------------------------------
sc = jload("out/scorecard.json")
if sc and isinstance(sc.get("rows"), list) and len(sc["rows"]) >= 4:
    okrows = all(all(k in r for k in ("claim", "evidence", "verdict", "improvement")) for r in sc["rows"])
    gate("scorecard:present", "GREEN" if okrows else "RED",
         f"StatFEM scorecard with {len(sc['rows'])} claim->evidence->verdict->improvement rows"
         if okrows else "scorecard rows missing required fields")
else:
    gate("scorecard:present", "RED", "out/scorecard.json missing or too few rows")

# ---- figures: tufte lint + image QA + text-overlap auditor ----------------
fig_scripts = ["fig_schematic", "fig_coverage", "fig_arm_comparison", "fig_theta_recovery",
               "fig_heldout_frf", "fig_identifiability"]
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
         "pixel legibility all pass" if ok else f"image-QA FAIL: {bad}")
else:
    gate("image_qa:legibility", "RED", "out/image_qa.json missing")

to = jload("out/text_overlap.json")
if to is not None:
    nbad = sum(len(v) for v in to.values()) if isinstance(to, dict) else 0
    gate("text_overlap:auditor", "GREEN" if nbad == 0 else "RED",
         f"save-time bbox text-overlap auditor: {nbad} overlapping text pair(s)")
else:
    gate("text_overlap:auditor", "RED", "out/text_overlap.json missing")

# ---- documentation gates ---------------------------------------------------
pk = open("packet.md").read() if os.path.exists("packet.md") else ""
gate("doc:method_summary_present",
     "GREEN" if ("Method summary" in pk or "Method Summary" in pk) else "RED",
     "packet has a method-summary section")
gate("doc:data_count_present",
     "GREEN" if ("one synthetic realization" in pk.lower() or "single synthetic realization" in pk.lower()) else "RED",
     "packet states the synthetic-realization / replicate count")
gate("doc:likelihood_choice_present",
     "GREEN" if ("whole" in pk.lower() and "log" in pk.lower() and "frf" in pk.lower()) else "RED",
     "packet states the whole-log-FRF likelihood data-usage choice")

# ---- honest scope (always yellow) ------------------------------------------
gate("scope:single_realization", "YELLOW",
     "one synthetic realization per combo (5 combos = 5 distinct truths); no flight/build/test variability")
gate("scope:surrogate_error_model", "YELLOW",
     "injected model-form error is a synthetic surrogate (parametric θ bias + Schneider correlated complex "
     "field), not a measured real-structure discrepancy")
gate("scope:no_universal_parameter_recovery", "YELLOW",
     "claim is held-out QOI coverage + error detection, NOT universal θ recovery; the unidentifiable groups "
     "(joints/contact/welds) are missed by design (modal-twin 4/9 finding)")

# ---- combo-dependence (fragility) finding ---------------------------------
if cov and "M0" in cov.get("by_arm", {}):
    spreads = {a: cov["by_arm"][a].get("std_combined") for a in ARMS if cov["by_arm"].get(a)}
    frag = any((s is not None and s > 0.20) for s in spreads.values())
    gate("sensitivity:combo_dependence", "YELLOW" if frag else "GREEN",
         f"per-arm coverage std over 5 combos = "
         f"{ {a: (round(s,3) if s is not None else None) for a,s in spreads.items()} }"
         + ("; some arm is combo-fragile (>0.20)" if frag else "; verdict stable across combos"))

order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
overall = max((g["status"] for g in gates), key=lambda x: order[x]) if gates else "RED"
counts = {k: sum(g["status"] == k for g in gates) for k in order}
report = {"overall": overall, "counts": counts, "gates": gates}
json.dump(report, open("checker_report.json", "w"), indent=2)
for g in gates:
    print(f"[{g['status']:6}] {g['gate']}: {g['detail']}")
print(f"\nOVERALL {overall}  GREEN {counts['GREEN']} / YELLOW {counts['YELLOW']} / RED {counts['RED']}")
sys.exit(1 if overall == "RED" else 0)
