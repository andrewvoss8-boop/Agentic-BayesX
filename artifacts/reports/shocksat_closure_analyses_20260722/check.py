#!/usr/bin/env python3
"""Immutable checker — shocksat_closure_analyses_20260722 (Task Card A).

Three-tier standard (AGENTS.md): GREEN met / YELLOW documented miss with caveat / RED blocking.
Exit 1 ONLY if any gate is RED. Verifies the card's minimum checker list:
 1. frozen-input hashes unchanged end-to-end
 2. A1 known-answer gate (eigenvalues within bootstrap CI of adjudicated values)
 3. A2 reference reproduction + per-variant all-variable diagnostics + per-chain draws retained
 4. A3 known-answer reproduction + shear-vs-synthetic-Z labels in table AND figure captions
 5. A4 inner-optimizer convergence recorded at every grid point
 6. A5 provenance stated (found vs re-derived)
 7. figures: tufte lint + legibility QA artifacts present; every figure names its source run
 8. runtime.json active total <= 4 h
"""
import json
import os
import sys

WS = os.path.dirname(os.path.abspath(__file__))
GATES = {}


def gate(name, tier, msg):
    GATES[name] = {"tier": tier, "msg": msg}
    print(f"[{tier}] {name}: {msg}")


def load(rel):
    p = os.path.join(WS, rel)
    if not os.path.isfile(p):
        return None
    try:
        return json.load(open(p))
    except Exception as e:
        return {"_parse_error": str(e)}


def main():
    # ---- 1. hashes unchanged ----
    hv = load("out/end_hash_verify.json")
    if hv is None:
        gate("hashes", "RED", "out/end_hash_verify.json missing (end-of-run hash verify not done)")
    elif not hv.get("ok"):
        gate("hashes", "RED", f"frozen inputs CHANGED: {hv.get('mismatch')}")
    else:
        gate("hashes", "GREEN", f"{hv.get('n_checked')} frozen inputs unchanged")

    # ---- 2. A1 known answer ----
    a1 = load("out/a1_subspace.json")
    if a1 is None:
        gate("a1_known_answer", "RED", "out/a1_subspace.json missing")
    else:
        ka = a1.get("known_answer_gate", {})
        n_ok = sum(bool(x) for x in ka.get("within_ci", []))
        n = len(ka.get("within_ci", []))
        if ka.get("pass") and n >= 4:
            gate("a1_known_answer", "GREEN",
                 f"{n_ok}/{n} adjudicated eigenvalues inside bootstrap CI "
                 f"(contracted {ka.get('adjudicated_contracted')})")
        else:
            gate("a1_known_answer", "RED", f"known-answer gate FAILED: {ka}")
        nb = a1.get("bootstrap", {})
        if nb.get("n_boot", 0) >= 1000 and nb.get("block_len", 0) >= 2:
            gate("a1_bootstrap", "GREEN",
                 f"block bootstrap n={nb['n_boot']} block_len={nb['block_len']}")
        else:
            gate("a1_bootstrap", "RED", f"bootstrap spec below card minimum: {nb}")
        if a1.get("claim_scope") == "subspace_only":
            gate("a1_scope", "GREEN", "claim scoped to subspace (no per-parameter identifiability)")
        else:
            gate("a1_scope", "RED", "claim_scope must be 'subspace_only'")

    # ---- 3. A2 sweep ----
    a2 = load("out/a2_sigma_f_sweep.json")
    if a2 is None:
        gate("a2_reference", "RED", "out/a2_sigma_f_sweep.json missing")
    else:
        rr = a2.get("reference_reproduction", {})
        if rr.get("pass"):
            gate("a2_reference", "GREEN",
                 f"HalfNormal(0.05) rerun reproduces stored posterior "
                 f"(sigma_f {rr.get('sigma_f_median'):.4f} vs stored {rr.get('stored_sigma_f_median'):.4f}; "
                 f"theta max|dev| {rr.get('theta_max_abs_dev'):.4f} <= tol {rr.get('theta_tol'):.4f})")
        else:
            gate("a2_reference", "RED", f"reference reproduction FAILED: {rr}")
        variants = a2.get("variants", {})
        if len(variants) < 5:
            gate("a2_variants", "RED", f"only {len(variants)}/5 prior variants present")
        else:
            bad, yellow = [], []
            for name, v in variants.items():
                conv = v.get("convergence", {})
                pv = conv.get("per_variable", {})
                draws = os.path.join(WS, "out", "a2_draws", f"{name}.npz")
                if not pv or "worst_rhat" not in conv or not os.path.isfile(draws):
                    bad.append(name)
                elif not conv.get("gate_pass"):
                    yellow.append(f"{name} (rhat {conv['worst_rhat']:.3f} ess {conv['min_ess']:.0f})")
            if bad:
                gate("a2_variants", "RED",
                     f"variants missing all-variable diagnostics or per-chain draws: {bad}")
            elif yellow:
                gate("a2_variants", "YELLOW",
                     f"5 variants complete; NON-CONVERGED (documented, intervals not trustworthy): {yellow}")
            else:
                gate("a2_variants", "GREEN", "5/5 variants converged with all-variable diagnostics + per-chain draws")

    # ---- 4. A3 known answer + labels ----
    a3 = load("out/a3_calibration_table.json")
    if a3 is None:
        gate("a3_known_answer", "RED", "out/a3_calibration_table.json missing")
    else:
        ka = a3.get("known_answer_gate", {})
        if ka.get("reproduced"):
            gate("a3_known_answer", "GREEN",
                 f"stored coverage/width reproduced (max|dev| {ka.get('max_abs_dev')})")
        else:
            gate("a3_known_answer", "RED", f"stored bake-off numbers NOT reproduced: {ka}")
        txt = json.dumps(a3)
        if "self-consistency, NOT validation" in txt:
            gate("a3_labels_table", "GREEN", "normal-Z synthetic label present in table JSON")
        else:
            gate("a3_labels_table", "RED", "normal-Z 'self-consistency, NOT validation' label missing from table")
        zw = a3.get("normal_z_widths", {})
        if zw.get("delivered_reference") == 2.526 and zw.get("tier_updated") == 2.958:
            gate("a3_z_widths", "GREEN", "2.526 (reference) and 2.958 (tier-updated) stated adjacently")
        else:
            gate("a3_z_widths", "RED", f"adjacent normal-Z width statement missing/wrong: {zw}")
        conv = a3.get("crps", {}).get("envelope_convention_sensitivity")
        if conv and len(conv) >= 3:
            gate("a3_crps_convention", "GREEN", f"{len(conv)} envelope scoring conventions reported")
        else:
            gate("a3_crps_convention", "RED", "envelope CRPS convention sensitivity missing (<3 conventions)")

    # ---- 5. A4 inner-opt convergence at every grid point ----
    a4 = load("out/a4_profile_likelihood.json")
    if a4 is None:
        gate("a4_inner_opt", "RED", "out/a4_profile_likelihood.json missing")
    else:
        profs = a4.get("profiles", {})
        if len(profs) < 2:
            gate("a4_inner_opt", "RED", f"need 2 profiled parameters, got {len(profs)}")
        else:
            missing, failed, npts = [], [], []
            for pname, prof in profs.items():
                pts = prof.get("points", [])
                npts.append(len(pts))
                for pt in pts:
                    io = pt.get("inner_opt")
                    if io is None or "converged" not in io:
                        missing.append(pname)
                        break
                failed.extend(f"{pname}@{pt.get('theta'):.3f}" for pt in pts
                              if pt.get("inner_opt", {}).get("converged") is False)
            if missing or min(npts) < 41:
                gate("a4_inner_opt", "RED",
                     f"inner-opt record missing ({missing}) or grid <41 pts ({npts})")
            elif failed:
                gate("a4_inner_opt", "YELLOW",
                     f"all {npts} pts recorded; inner opt NOT converged at {len(failed)} pts: {failed[:5]}")
            else:
                gate("a4_inner_opt", "GREEN",
                     f"inner-opt converged and recorded at every grid point ({npts} pts)")
            if a4.get("likelihood_form_documented") and a4.get("choice_rule"):
                gate("a4_form", "GREEN", "likelihood form + parameter choice rule documented")
            else:
                gate("a4_form", "RED", "likelihood form or choice rule not documented")

    # ---- 6. A5 provenance ----
    a5 = load("out/a5_phase_diagnostic.json")
    if a5 is None:
        gate("a5_provenance", "RED", "out/a5_phase_diagnostic.json missing")
    elif a5.get("provenance") in ("found", "re-derived") and a5.get("sha256") and a5.get("source_path"):
        gate("a5_provenance", "GREEN",
             f"provenance={a5['provenance']} circ_var={a5.get('circular_variance')}")
    else:
        gate("a5_provenance", "RED", f"provenance/sha/source missing: {a5}")

    # ---- 7. figures: lint + QA + source naming ----
    fm = load("out/fig_manifest.json")
    lint_p = os.path.join(WS, "out", "tufte_lint.txt")
    qa = load("out/fig_qa.json")
    if fm is None or not fm.get("figures"):
        gate("figures", "RED", "out/fig_manifest.json missing/empty")
    else:
        miss = [f["path"] for f in fm["figures"] if not os.path.isfile(os.path.join(WS, f["path"]))]
        nosrc = [f["path"] for f in fm["figures"] if "source" not in f.get("caption", "").lower()
                 and "nuts_full_samples" not in f.get("caption", "")
                 and "run:" not in f.get("caption", "").lower()]
        if miss or nosrc:
            gate("figures", "RED", f"missing figures {miss}; captions without source naming {nosrc}")
        elif not os.path.isfile(lint_p) or qa is None:
            gate("figures", "RED", "tufte_lint.txt or fig_qa.json missing")
        elif not qa.get("all_pass"):
            gate("figures", "YELLOW", f"legibility QA flags: {qa.get('flags')}")
        else:
            gate("figures", "GREEN",
                 f"{len(fm['figures'])} figures exist, captions name sources, lint+QA artifacts present")

    # ---- 8. runtime ----
    rt = load("runtime.json")
    if rt is None or "active_runtime_s" not in rt:
        gate("runtime", "RED", "runtime.json missing active_runtime_s")
    elif rt["active_runtime_s"] > 14400:
        gate("runtime", "RED", f"active runtime {rt['active_runtime_s']}s exceeds 4 h cap")
    else:
        gate("runtime", "GREEN",
             f"active {rt['active_runtime_s']:.0f}s <= 14400s (wallclock {rt.get('elapsed_wallclock_s')})")

    # ---- overall ----
    tiers = [g["tier"] for g in GATES.values()]
    overall = "RED" if "RED" in tiers else ("YELLOW" if "YELLOW" in tiers else "GREEN")
    counts = {t: tiers.count(t) for t in ("GREEN", "YELLOW", "RED")}
    report = {"overall": overall, "counts": counts, "gates": GATES}
    out_p = os.path.join(WS, "out", "checker_report.json")
    os.makedirs(os.path.dirname(out_p), exist_ok=True)
    json.dump(report, open(out_p, "w"), indent=1)
    print(f"OVERALL {overall} {counts}")
    return 1 if overall == "RED" else 0


if __name__ == "__main__":
    sys.exit(main())
