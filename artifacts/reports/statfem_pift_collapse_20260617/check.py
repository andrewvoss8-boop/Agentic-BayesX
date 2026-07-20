#!/usr/bin/env python3
"""IMMUTABLE checker — Card B: PIFT posterior-collapse / orthogonal-Schneider cure (StatFEM ShockSat).

Written BEFORE results (card §6: "Immutable check.py written FIRST"). Encodes GREEN/YELLOW/RED acceptance per
AGENTS.md Result Status Standard + the task card. Exits non-zero ONLY on RED. YELLOW = documented, non-fatal,
never "success".

What this checker certifies: that the COLLAPSE SWEEP is built and reported WITH NUMBERS (σ_d-width, identified-θ
width, and a sharpness-aware held-out score vs observation-density N, per arm), with NUTS convergence labeled
per N-cell; that the EFFECTIVE-SAMPLE-SIZE accounting is present; that the collapse-vs-plateau VERDICT is stated
with the verified PIFT quote + the analogy mapping; that the SYNTHETIC controlled cross-check exists; and that
the REAL matched-path leg uses a matched-path (NOT SOL111) likelihood. It does NOT force a verdict direction —
whether our StatFEM collapses and whether orthogonal-Schneider cures it is the SCIENCE, reported either way
(card §1, §9).
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
COMP = "../statfem_shocksat_eval_20260616"   # synthetic companion = provenance source for copied modules

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
ARMS_HEAD = ["M0", "M1", "M3"]        # naive / iid / orthogonal-Schneider (M2 optional)
REDUCE_FRF_GREEN = 0.03               # reduced-vs-full FRF max rel err: GREEN threshold
REDUCE_FRF_CEIL = 0.12                # YELLOW ceiling (documented 74-mode truncation), else RED
SCORE_FIELDS = ["interval_score_db", "crps_db", "coverage", "width_db", "pit_ks"]


def conv_ok(n):
    return (n["max_rhat"] <= RHAT_MAX and n["min_ess"] >= ESS_MIN and n["div_frac"] < DIV_MAX)


# ---- required artifacts ---------------------------------------------------
required = [
    "decisions_log.md", "priority_deliverables.md", "analogy_mapping.md", "references_and_quotes.md",
    "assumptions_ledger.md", "question_framing.md", "quantity_contracts.md",
    "packet.md", "run_all.sh", "runtime.json",
    "code/core.py", "code/nuts_arms.py", "code/predict.py",
    "code/scoring.py", "code/run_ladder.py", "code/ess_accounting.py", "code/aggregate_sweep.py",
    "code/identifiability.py", "code/image_qa.py",
    "code/fig_collapse_curves.py", "code/fig_ess_vs_N.py", "code/fig_theta_width.py",
    "code/fig_synth_collapse_demo.py", "code/fig_schematic.py",
    "out/config.json", "out/config_real.json",
    "out/sweep_synth.json", "out/sweep_real.json", "out/ess_accounting.json", "out/verdict.json",
    "out/identifiability.json", "out/discretization.json", "out/image_qa.json", "out/text_overlap.json",
    "figures/fig_collapse_curves.png", "figures/fig_ess_vs_N.png", "figures/fig_theta_width.png",
    "figures/fig_synth_collapse_demo.png", "figures/fig_schematic.png",
]
for p in required:
    gate(f"artifact:{p}", "GREEN" if os.path.exists(p) else "RED", p)

# ---- integrity: copied scaffolds are BYTE-IDENTICAL to the companion (card §9 "copy, never edit") ----
for f in ["core.py", "nuts_arms.py", "predict.py"]:
    try:
        a, b = sha256(f"code/{f}"), sha256(f"{COMP}/code/{f}")
        gate(f"integrity:copied_unedited:{f}", "GREEN" if a == b else "RED",
             f"code/{f} SHA == companion ({a[:12]}…)" if a == b
             else f"code/{f} DIFFERS from the companion original (editing a copied scaffold = RED)")
    except FileNotFoundError as e:
        gate(f"integrity:copied_unedited:{f}", "RED", f"cannot verify: {e}")
try:
    a, b = sha256("data/reduced_blocks.npz"), sha256(f"{COMP}/data/reduced_blocks.npz")
    gate("integrity:reduced_blocks_copied_unedited", "GREEN" if a == b else "RED",
         f"data/reduced_blocks.npz SHA == companion/modal-twin ({a[:12]}…)" if a == b
         else "reduced_blocks.npz DIFFERS from the provenance original (integrity violation)")
except FileNotFoundError as e:
    gate("integrity:reduced_blocks_copied_unedited", "RED", f"cannot verify: {e}")

# ---- anti-cheat: no coupled tray model (card §3) --------------------------
tray_hits = [os.path.basename(p) for p in glob.glob("code/*.py")
             if re.search(r"tray_coupled|shocksat_tray", open(p).read())]
cfg = jload("out/config.json")
prov_ok = bool(cfg and cfg.get("testbed") == "plain_shocksat_9group" and not cfg.get("uses_tray", False))
gate("anti_cheat:no_coupled_tray_model", "GREEN" if (not tray_hits and prov_ok) else "RED",
     "plain-ShockSat only; no coupled-tray reference; config provenance = plain_shocksat_9group"
     if (not tray_hits and prov_ok) else f"FORBIDDEN tray usage {tray_hits}; prov_ok={prov_ok}")

# ---- anti-cheat: real-data leg uses a MATCHED-PATH (not SOL111) likelihood (card §6 RED) ----
cfgr = jload("out/config_real.json")
if cfgr is None:
    gate("anti_cheat:matched_path_not_sol111", "RED", "out/config_real.json missing (real-data leg not built)")
else:
    matched = (cfgr.get("frf_path") == "matched_impact_node" and not cfgr.get("uses_sol111", True))
    gate("anti_cheat:matched_path_not_sol111", "GREEN" if matched else "RED",
         f"real FRF likelihood path = {cfgr.get('frf_path')!r}, uses_sol111={cfgr.get('uses_sol111')}"
         + ("" if matched else "  (SOL111/mismatched-path FRF likelihood = RED)"))

# ---- load sweeps ----------------------------------------------------------
sw_s = jload("out/sweep_synth.json")
sw_r = jload("out/sweep_real.json")


def check_sweep(sw, tag):
    """Numbers-present + convergence-labeled gates for one sweep file."""
    if sw is None:
        gate(f"sweep:{tag}:present", "RED", f"out/sweep_{tag}.json missing")
        return
    cells = sw.get("cells", [])
    if not cells:
        gate(f"sweep:{tag}:present", "RED", f"sweep_{tag} has no cells")
        return
    # numbers present per cell
    missing = []
    for c in cells:
        ok = ("N" in c and isinstance(c.get("sigma_d"), dict) and "width" in c["sigma_d"]
              and "theta_width_identified" in c and isinstance(c.get("score"), dict)
              and all(k in c["score"] for k in SCORE_FIELDS))
        if not ok:
            missing.append((c.get("arm"), c.get("N")))
    gate(f"sweep:{tag}:numbers_present", "GREEN" if not missing else "RED",
         f"σ_d-width, θ-width, sharpness-aware score(+coverage/width/PIT) present for all {len(cells)} {tag} cells"
         if not missing else f"{tag} cells MISSING required numbers: {missing[:6]} (claim without numbers = RED)")
    # arms covered
    arms = {c.get("arm") for c in cells}
    have_head = all(a in arms for a in ARMS_HEAD)
    gate(f"sweep:{tag}:headline_arms_present", "GREEN" if have_head else "RED",
         f"{tag} arms present = {sorted(arms)} (need naive M0 / iid M1 / orthogonal-Schneider M3)")
    # multiple N (a sweep, not a point)
    Ns = sorted({c.get("N") for c in cells})
    gate(f"sweep:{tag}:is_a_sweep", "GREEN" if len(Ns) >= 3 else "RED",
         f"{tag} observation-density ladder has {len(Ns)} distinct N values: {Ns}")
    # convergence labeled
    nuts = [c for c in cells if isinstance(c.get("nuts"), dict)]
    nonconv = [c for c in nuts if not conv_ok(c["nuts"])]
    undoc = [c for c in nonconv if c.get("converged", False)]
    if undoc:
        gate(f"convergence:{tag}:undocumented_nonconvergence", "RED",
             f"{len(undoc)} {tag} cell(s) report converged=True but FAIL the gate (undocumented)")
    if not nuts:
        gate(f"convergence:{tag}", "RED", f"no NUTS diagnostics in {tag} cells")
    elif not nonconv:
        worst = max(nuts, key=lambda c: c["nuts"]["max_rhat"])
        gate(f"convergence:{tag}", "GREEN",
             f"all {len(nuts)} {tag} cells cleared the gate; worst R-hat {worst['nuts']['max_rhat']:.3f}, "
             f"min ESS {min(c['nuts']['min_ess'] for c in nuts):.0f}, "
             f"max div {max(c['nuts']['div_frac'] for c in nuts):.3f}")
    else:
        gate(f"convergence:{tag}", "YELLOW",
             f"{len(nuts)-len(nonconv)}/{len(nuts)} {tag} cells converged; {len(nonconv)} labeled "
             f"not-yet-converged (intervals not-trustworthy at those N)")


check_sweep(sw_s, "synth")
check_sweep(sw_r, "real")

# ---- synthetic controlled cross-check: known model-form error documented ---
if sw_s is not None:
    truth = sw_s.get("truth", {})
    ok = bool(truth.get("theta_truth") and truth.get("known_model_form_error"))
    gate("crosscheck:synthetic_known_model_form_error", "GREEN" if ok else "RED",
         f"synthetic truth documents the KNOWN model-form error: {truth.get('known_model_form_error','?')}"
         if ok else "synthetic sweep does not document its known model-form error truth")
else:
    gate("crosscheck:synthetic_known_model_form_error", "RED", "sweep_synth.json missing")

# ---- effective-sample-size accounting -------------------------------------
ess = jload("out/ess_accounting.json")
if ess and "by_arm" in ess and all(a in ess["by_arm"] for a in ARMS_HEAD):
    ok = all(isinstance(ess["by_arm"][a].get("N"), list) and isinstance(ess["by_arm"][a].get("N_eff"), list)
             and len(ess["by_arm"][a]["N"]) == len(ess["by_arm"][a]["N_eff"]) and ess["by_arm"][a]["N"]
             for a in ARMS_HEAD)
    gate("ess:accounting_present", "GREEN" if ok else "RED",
         "effective-sample-size N_eff(N) reported for naive/iid/orthogonal (iid grows ∝N; correlated saturates)"
         if ok else "ess_accounting present but N/N_eff arrays incomplete for some arm")
else:
    gate("ess:accounting_present", "RED", "out/ess_accounting.json missing or incomplete")

# ---- verdict stated WITH the verified PIFT quote + analogy mapping ---------
PIFT_QUOTE = "collapses to a single function irrespective of the value of"
vd = jload("out/verdict.json")
pk = open("packet.md").read() if os.path.exists("packet.md") else ""
am_ok = os.path.exists("analogy_mapping.md")
quote_in_packet = PIFT_QUOTE in pk
verdict_keys = vd is not None and ("our_statfem_collapses" in vd and "orthogonal_cures" in vd)
gate("verdict:stated_with_pift_quote_and_mapping",
     "GREEN" if (verdict_keys and quote_in_packet and am_ok) else "RED",
     "verdict.json states collapse-vs-cure; packet carries the verbatim PIFT quote; analogy_mapping.md present"
     if (verdict_keys and quote_in_packet and am_ok)
     else f"verdict_keys={verdict_keys}, pift_quote_in_packet={quote_in_packet}, analogy_mapping={am_ok}")

# FINDING (GREEN regardless of direction — the science, reported either way; card §1/§9)
if verdict_keys:
    col = vd.get("our_statfem_collapses"); cure = vd.get("orthogonal_cures")
    gate("finding:collapse_and_cure_direction", "GREEN",
         f"FINDING (reported whichever way it falls): does OUR StatFEM (iid/naive) collapse? = {col}; "
         f"does orthogonal-Schneider cure it (plateau)? = {cure}. Evidence: {vd.get('evidence', {})}")
else:
    gate("finding:collapse_and_cure_direction", "RED", "verdict.json missing the two finding booleans")

# ---- identifiability gate (strain energy + FIM) ----------------------------
idf = jload("out/identifiability.json")
if idf and "strain_energy" in idf and "fim" in idf:
    gate("identifiability:strain_energy_and_fim", "GREEN",
         f"per-group modal strain-energy ({len(idf['strain_energy'])} groups) + FRF-FIM eigen-view "
         f"({idf['fim'].get('n_above_prior','?')} combos above prior precision) reported")
else:
    gate("identifiability:strain_energy_and_fim", "RED", "out/identifiability.json incomplete")

# ---- discretization (reduced-vs-full FRF; inherited 74-mode-truncation YELLOW) ----
dz = jload("out/discretization.json")
if dz and "reduced_vs_full" in dz:
    err = dz["reduced_vs_full"].get("max_rel_err_at_peaks")
    diag = dz["reduced_vs_full"].get("diagnosis")
    if err is None:
        gate("discretization:reduced_frf_validated", "RED", "reduced-vs-full FRF error not reported")
    elif err <= REDUCE_FRF_GREEN:
        gate("discretization:reduced_frf_validated", "GREEN", f"reduced-vs-full max rel err {err:.4f} ≤ {REDUCE_FRF_GREEN}")
    elif err <= REDUCE_FRF_CEIL and diag:
        gate("discretization:reduced_frf_validated", "YELLOW",
             f"reduced-vs-full max rel err {err:.4f} (>{REDUCE_FRF_GREEN}, ≤{REDUCE_FRF_CEIL}); documented: {diag}")
    else:
        gate("discretization:reduced_frf_validated", "RED",
             f"reduced-vs-full max rel err {err:.4f} exceeds ceiling {REDUCE_FRF_CEIL} or lacks diagnosis")
else:
    gate("discretization:reduced_frf_validated", "RED", "out/discretization.json missing reduced_vs_full")

# ---- reference gate --------------------------------------------------------
ref_txt = (open("references_and_quotes.md").read() if os.path.exists("references_and_quotes.md") else "") + pk
need_refs = {"PIFT/2301.07609": "2301.07609", "IFT/2306.02150": "2306.02150",
             "statFEM": "statFEM", "Plumlee": "Plumlee", "Kennedy": "Kennedy"}
miss_ref = [k for k, tok in need_refs.items() if tok.lower() not in ref_txt.lower()]
gate("reference:pift_ift_statfem_plumlee_koh", "GREEN" if not miss_ref else "RED",
     "PIFT/IFT/statFEM/Plumlee/KOH all cited" if not miss_ref else f"missing references: {miss_ref}")

# ---- figures: tufte lint + image QA + text overlap ------------------------
fig_scripts = ["fig_collapse_curves", "fig_ess_vs_N", "fig_theta_width", "fig_synth_collapse_demo", "fig_schematic"]
for s in fig_scripts:
    log = f"logs/tufte_{s}.txt"
    if os.path.exists(log):
        txt = open(log).read()
        bad = bool(re.search(r"POTENTIAL ISSUES|\bERROR\b", txt)) and "No obvious" not in txt
        gate(f"tufte_lint:{s}", "GREEN" if not bad else "YELLOW", "clean" if not bad else "tufte_lint flagged issues")
    else:
        gate(f"tufte_lint:{s}", "RED", f"missing {log}")

qa = jload("out/image_qa.json")
if qa is not None:
    ok = qa.get("ALL_OK", False)
    bad = [k for k, v in qa.items() if isinstance(v, dict) and not v.get("ok", True)]
    gate("image_qa:legibility", "GREEN" if ok else "RED", "pixel legibility all pass" if ok else f"FAIL: {bad}")
else:
    gate("image_qa:legibility", "RED", "out/image_qa.json missing")

to = jload("out/text_overlap.json")
if to is not None:
    nbad = sum(len(v) for v in to.values()) if isinstance(to, dict) else 0
    gate("text_overlap:auditor", "GREEN" if nbad == 0 else "RED", f"{nbad} overlapping text pair(s)")
else:
    gate("text_overlap:auditor", "RED", "out/text_overlap.json missing")

# ---- documentation gates ---------------------------------------------------
gate("doc:method_summary_present", "GREEN" if re.search(r"method summary", pk, re.I) else "RED",
     "packet has a method-summary section")
gate("doc:likelihood_choice_present",
     "GREEN" if ("whole" in pk.lower() and "log" in pk.lower() and "frf" in pk.lower()) else "RED",
     "packet states the whole-log-FRF likelihood data-usage choice")
gate("doc:observation_density_axis_defined",
     "GREEN" if ("observation density" in pk.lower() or "n_freq" in pk.lower() or "collocation" in pk.lower()) else "RED",
     "packet defines the observation-density N axis (the collocation↔observation analogy)")

# ---- runtime accounting ----------------------------------------------------
rt = jload("runtime.json")
if rt and "active_runtime_s" in rt and "elapsed_wallclock_s" in rt:
    okp = isinstance(rt.get("phases"), dict) and len(rt["phases"]) >= 1
    le = rt["active_runtime_s"] <= rt["elapsed_wallclock_s"] + 1e-6
    gate("runtime:accounting", "GREEN" if (okp and le) else "YELLOW",
         f"active {rt['active_runtime_s']}s ≤ wall {rt['elapsed_wallclock_s']}s; per-phase timing present={okp}")
else:
    gate("runtime:accounting", "RED", "runtime.json missing active/elapsed timing")

# ---- honest scope (always YELLOW) -----------------------------------------
gate("scope:synthetic_single_truth", "YELLOW",
     "synthetic leg = one truth realization with one injected Schneider field (a controlled known-error twin)")
gate("scope:real_single_impact", "YELLOW",
     "real leg = single-impact matched-path FRF (no hit-to-hit averaging); coherence-weighted, 1-hit SNR")
gate("scope:no_universal_parameter_recovery", "YELLOW",
     "claim is collapse/plateau of σ_d-uncertainty + held-out score vs N; ~4/9 groups identifiable (modal-twin)")

order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
overall = max((g["status"] for g in gates), key=lambda x: order[x]) if gates else "RED"
counts = {k: sum(g["status"] == k for g in gates) for k in order}
json.dump({"overall": overall, "counts": counts, "gates": gates}, open("checker_report.json", "w"), indent=2)
for g in gates:
    print(f"[{g['status']:6}] {g['gate']}: {g['detail']}")
print(f"\nOVERALL {overall}  GREEN {counts['GREEN']} / YELLOW {counts['YELLOW']} / RED {counts['RED']}")
sys.exit(1 if overall == "RED" else 0)
