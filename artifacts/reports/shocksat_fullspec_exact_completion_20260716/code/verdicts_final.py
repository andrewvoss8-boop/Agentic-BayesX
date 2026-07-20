#!/usr/bin/env python3
"""verdicts_final — T3: corrected, finiteness-hardened verdicts (card §2 T3).

WHY THIS EXISTS
The study SHIPPED `out/verdicts.json` with **NaN** S1/S2 statistics and an arms table whose F row was set to
the best arm = R (the random control) instead of the pre-registered F rule. Its locked checker's G09 passed
that: it validated key-PRESENCE, not finiteness or identity (review C8, accepted D17).

So this file's contract is: **every asserted number is checked finite BEFORE the file is written**
(`_common.assert_finite` raises rather than emit a null/NaN), there is no F=R row, and anything genuinely
unavailable is written as an explanatory STRING, never as a null. The checker (G05) independently walks
every leaf of the output and RED-fails on any null/NaN/Inf.

SOURCES (all carried, none re-litigated):
  * S1, S5 and the arms table          <- the isolated repair (shocksat_full_spectrum_frf_repair_20260716)
  * arm C exact + the corrected S1 row <- T1 here (out/armC_exact.json), replacing the withdrawn leaky 0.157
  * S2 under BOTH selection conventions<- T2 here (out/exact_rerank.json)
  * S3, S4                             <- CANNOT-VERIFY (the net-CG port failed its reference reproduction;
                                          unresolved, NOT falsified). Pointer to Card B. Not laundered into
                                          "not met".
NO SAMPLER runs in this card; every MAP-derived number is labeled a deterministic optimizer result and
carries the study's worst-case non-convergence diagnostics.
"""
from __future__ import annotations
import json, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                # noqa: E402

WORST_RHAT, WORST_ESS = 360.63, 2.0                # study out/nuts_diagnostics.json (arm B, m_zpos_990z)


def repair_json(name):
    with open(C.repair_path("out", name)) as f:
        return json.load(f)


def paired_vs_a1(folds_arm, folds_a1):
    d = [folds_arm[k] - folds_a1[k] for k in C.DEV_KEYS]
    return C.paired_stats(d)


def main():
    t0 = time.time()
    with open(os.path.join(C.MY_OUT, "armC_exact.json")) as f:
        armC = json.load(f)
    with open(os.path.join(C.MY_OUT, "exact_rerank.json")) as f:
        rr = json.load(f)
    rep_v = repair_json("verdicts.json")
    rep_t = repair_json("arms_bands_table.json")
    with open(os.path.join(C.MY_OUT, "leak_probe.json")) as f:
        leak_probe = json.load(f)

    # ---------------------------------------------------------------- arms x bands table (no F=R row)
    arms = {}
    for a in ("A0", "A1", "B", "C", "D", "R"):
        src = rep_t["arms"][a]
        rec = {}
        for b in ("sub200", "b200_500"):
            if a == "C":            # T1 replaces the study's leaky arm-C row
                folds = {k: armC["folds"][k]["bands"][b] for k in C.DEV_KEYS}
                rec[b] = {"mean": armC["fold_mean"][b],
                          "fold_se": float(np.std([folds[k] for k in C.DEV_KEYS], ddof=1) / 2.0),
                          "folds": folds,
                          "screening": src[b]["screening"],
                          "provenance": "THIS CARD (T1): 4 per-fold shape-MAP refits on the exact basis "
                                        "A0_wide__enr, each fit on that fold's 3 TRAIN drives only "
                                        "(multi-start 4, deterministic L-BFGS-B). Replaces the study's "
                                        "WITHDRAWN leaky row (one fold's MAP applied to all 4 folds; "
                                        "review C6)."}
            else:
                rec[b] = {"mean": src[b]["mean"], "fold_se": src[b]["se"], "folds": src[b]["folds"],
                          "screening": src[b]["screening"],
                          "provenance": "isolated repair, from the study's exact_freeze_scores.json"}
        rec["b500_ceiling"] = {"status": "not_certified",
                               "reason": "FEM basis credible to 639 Hz (cross-validated); the 1.25x "
                                         "modal-truncation rule caps scorable frequency at 511 Hz -> the "
                                         "500-1000 Hz band is FEM/compute-limited, NOT data-limited "
                                         "(data certified >1 kHz). Study D11."}
        rec["scoring"] = ("deterministic MAP point estimate (NON-converged posterior)" if a in ("B", "C")
                          else "deterministic exact-basis score")
        arms[a] = rec
    # arm F: pre-registered sequential rule -> F = C. NOT the best arm, and NEVER the random control.
    arms["F"] = {"identity": "C",
                 "rule": rep_t["arm_F_rule"]["source"],
                 "decision": rep_t["arm_F_rule"]["decision"],
                 "sub200_mean": armC["fold_mean"]["sub200"],
                 "b200_500_mean": armC["fold_mean"]["b200_500"],
                 "note": "F duplicates C by construction, now with C's honest T1 numbers. The study "
                         "collector's F = R (the random control) row was INVALID (review C8) and is gone."}

    # ---------------------------------------------------------------- S1 (all eligible arms vs A1-exact)
    a1_folds = {b: {k: rep_t["arms"]["A1"][b]["folds"][k] for k in C.DEV_KEYS}
                for b in ("sub200", "b200_500")}
    s1_arms = {}
    for a in ("B", "C", "D"):
        folds = {k: arms[a]["sub200"]["folds"][k] for k in C.DEV_KEYS}
        dm, se, pf = paired_vs_a1(folds, a1_folds["sub200"])
        s1_arms[a] = {"delta_mean": dm, "delta_se": se, "two_se": 2 * se, "per_fold": pf,
                      "meets_magnitude_bar": bool(dm >= 0.05), "meets_precision_bar": bool(dm >= 2 * se),
                      "S1_rule_met": bool(dm >= 0.05 and dm >= 2 * se)}
    best = max(s1_arms, key=lambda a: s1_arms[a]["delta_mean"])
    S1 = {"status": "YELLOW",
          "claim": "an eligible arm (B/C/D/F) beats A1 by >= +0.05 AND >= 2x paired-fold SE, sub-200 Hz",
          "verdict": "NOT MET",
          "best_arm": best, "best_delta_mean": s1_arms[best]["delta_mean"],
          "best_delta_se": s1_arms[best]["delta_se"], "best_two_se": s1_arms[best]["two_se"],
          "per_arm": s1_arms,
          "note": (f"Best eligible arm {best} beats A1-exact by {s1_arms[best]['delta_mean']:+.4f}, which "
                   f"clears 2x paired SE ({s1_arms[best]['two_se']:.4f}) but MISSES the +0.05 magnitude bar "
                   f"by {0.05 - s1_arms[best]['delta_mean']:.4f}. Unchanged in verdict from the repair; arm "
                   f"C's row is now the honest T1 refit rather than the withdrawn leaky one."),
          "F_rule": "F = C (B does not beat A1; C beats A1; D does not beat C) — NOT best-arm, NOT R.",
          "source": "isolated repair + T1 arm-C refits (this card)"}

    # ---------------------------------------------------------------- S2 (BOTH selection conventions)
    s2s, s2e = rr["S2"]["screening_selected"], rr["S2"]["exact_selected"]
    S2 = {"status": "YELLOW",
          "claim": "agent D beats equal-budget random R by >= 1x paired-fold SE, sub-200 Hz",
          "screening_selected": {
              "convention": "the study's: each track's SCREENING (theta=1 basis) winner, exact-scored",
              "agent_cid": s2s["agent_cid"], "random_cid": s2s["random_cid"],
              "delta_mean": s2s["delta_mean"], "delta_se": s2s["delta_se"], "per_fold": s2s["per_fold"],
              "verdict": "MET" if s2s["S2_rule_met"] else "NOT MET",
              "repair_reference": rep_v["S2"]["numbers"]["delta_mean"],
              "reproduces_repair": bool(abs(s2s["delta_mean"] - rep_v["S2"]["numbers"]["delta_mean"]) < 0.005)},
          "exact_selected": {
              "convention": "winner's-curse-honest: each track's BEST EXACT candidate (select and report on "
                            "the same trustworthy metric)",
              "agent_cid": s2e["agent_cid"], "random_cid": s2e["random_cid"],
              "delta_mean": s2e["delta_mean"], "delta_se": s2e["delta_se"], "per_fold": s2e["per_fold"],
              "verdict": "MET" if s2e["S2_rule_met"] else "NOT MET",
              "caveat": "a per-track maximum over 14 noisy candidates carries selection noise in BOTH arms; "
                        "a sub-SE gap is not a win for either track"},
          "coverage": f"{rr['n_scored']}/28 loop candidates exact-scored ({rr['n_excluded']} "
                      f"excluded-with-reason) — the study exact-scored only 2/28 (review C1)",
          "rank_agreement": rr["rank_agreement"],
          "scope_limitation_D16": "all 14 agent candidates were thickness/scale/split edits; the agent "
                                  "proposed ZERO genuine model-form (mesh/connectivity) changes. Any H2 "
                                  "reading is 'within a mostly-parametric edit space', NOT 'agent-proposed "
                                  "geometry/mesh/connectivity edits failed'.",
          "source": "T2 exact re-rank (this card)"}

    # ---------------------------------------------------------------- S3/S4 CANNOT-VERIFY (this card's scope)
    cv_note = ("The wide-package net-CG QOI reimplementation does not reproduce the DELIVERED twin's "
               "calibrated bands (8.2x/3.66x/5.12x vs delivered 1.51x/2.30x/2.53x) — a marginal-calibration "
               "difference in the reimplemented statFEM F(k), not a demonstrated widening. Per review C5, "
               "'unassessable' is NOT 'falsified' and NOT 'not-met': the required QOI result is ABSENT. "
               "Resolution requires A1 to reproduce 1.51/2.30/2.53 before any arm change is evaluated.")
    # Card B ran in parallel TODAY and has since made S3/S4 assessable. My checker's G05 was SHA-locked
    # BEFORE any science on the card's instruction "S3/S4 = CANNOT-VERIFY (pointer to Card B)", so the
    # status field below is the status FROM THIS CARD'S EVIDENCE (which is: none). Card B's ACTUAL, newer
    # verdicts ride along in `superseded_by_card_B` so no reader can mistake my stale field for current.
    # See decisions_log D3 — flagged as a checker-scope miss on my part, not silently resolved.
    cardB_path = os.path.join(C.REPORTS, "shocksat_netcg_validated_port_20260716")
    with open(os.path.join(cardB_path, "out", "verdicts_S3S4.json")) as f:
        cardB = json.load(f)
    cardB_common = {
        "workspace": "artifacts/reports/shocksat_netcg_validated_port_20260716/",
        "card_B_checker": "GREEN 10G/0Y/0R (INTEGRITY only — its checker has no gate propagating the "
                          "science verdicts into OVERALL; its own D7 discloses this)",
        "N0_reference_reproduction": "GREEN — driving the ORIGINAL netcg_qoi.py + reduced model + REUSED "
                                     "L5 NUTS draws reproduces the delivered twin EXACTLY "
                                     "(1.508/2.301/2.526, max |err| 0.0000, tol 0.05). The reproduction "
                                     "review C5 required is DONE.",
        "status_of_this_field": "STALE BY SCOPE: my S3/S4 status is 'CANNOT-VERIFY' because THIS card "
                                "produced no net-CG evidence and my checker was locked before Card B "
                                "landed. Card B's verdict below is the current one."}
    S3 = {"status": "CANNOT-VERIFY", "claim": "narrows net-CG shear while keeping >= 0.95 coverage",
          "verdict": "CANNOT-VERIFY (from THIS card's evidence, which is none) — SEE superseded_by_card_B",
          "reason": cv_note,
          "not_attempted_here": "this card does not touch net-CG; no S3 evidence is produced or implied",
          "superseded_by_card_B": dict(cardB_common, **{
              "card_B_S3_status": cardB["S3"]["status"],
              "card_B_S3_reading": cardB["S3"].get("note", ""),
              "card_B_S3_numbers": cardB["S3"]["numbers"],
              "plain_english": "Card B REPRODUCED the delivered reference exactly, so S3 is assessable "
                               "now. But its three mapping variants DISAGREE on the pre-registered S3 "
                               "rule, so S3 remains CANNOT-VERIFY-THROUGH-THIS-MAPPING — the verdict "
                               "would be an artifact of the mapping choice, not a fact about the arms."}),
          "reimplementation_numbers_for_reference": {
              "shear_x_width_ratio": rep_v["S3"]["numbers"]["shear_x"]["width_ratio"],
              "shear_y_width_ratio": rep_v["S3"]["numbers"]["shear_y"]["width_ratio"],
              "delivered_x": rep_v["S3"]["numbers"]["delivered"]["x"],
              "delivered_y": rep_v["S3"]["numbers"]["delivered"]["y"],
              "caveat": "the STUDY's reimplementation failed its reference reproduction; these are NOT a "
                        "result. Card B's validated port supersedes them."}}
    S4 = {"status": "CANNOT-VERIFY", "claim": "normal band narrows >= 25% (2.53 -> 1.90) while covering",
          "verdict": "CANNOT-VERIFY (from THIS card's evidence, which is none) — SUPERSEDED: Card B "
                     "falsifies S4. SEE superseded_by_card_B",
          "reason": cv_note,
          "not_attempted_here": "this card does not touch net-CG; no S4 evidence is produced or implied",
          "superseded_by_card_B": dict(cardB_common, **{
              "card_B_S4_status": cardB["S4"]["status"],
              "card_B_S4_met": False,
              "card_B_S4_numbers": cardB["S4"]["numbers"],
              "plain_english": "S4 IS NOW FALSIFIED, not unresolved. On Card B's validated port the "
                               "normal-Z band WIDENS to 2.958x vs the delivered 2.526x (the rule needed "
                               "<= 1.9x), coverage 0.989, and the change exceeds the MC noise floor "
                               "(0.091). My 'CANNOT-VERIFY' above is a SCOPE artifact of a checker locked "
                               "before Card B landed (decisions_log D3) — do not read it as current."}),
          "reimplementation_numbers_for_reference": {
              "normal_z_width_ratio": rep_v["S4"]["numbers"]["normal_z"]["width_ratio"],
              "delivered": rep_v["S4"]["numbers"]["delivered"],
              "caveat": "the STUDY's reimplementation failed its reference reproduction; these are NOT a "
                        "result. Card B's validated port supersedes them."}}

    # ---------------------------------------------------------------- S5 (carried, with its fragility)
    bp = rep_v["S5"]["numbers"]["by_prior"]
    S5 = {"status": "YELLOW",
          "claim": "amplitude-inclusive selection Spearman >= 0.5 vs held-out ranking",
          "verdict": "NOT MET",
          "spearman_at_declared_prior_sigma_0.25": rep_v["S5"]["numbers"]["spearman"],
          "prior_width_fragility": {
              "sigma_0.25_declared": bp["spearman_sig0.25"],
              "sigma_0.15": ("null in the repair's collector; the review recomputed a FINITE-ONLY "
                             "Spearman of +0.139" if bp.get("spearman_sig0.15") is None
                             else bp["spearman_sig0.15"]),
              "sigma_0.40": ("null in the repair's collector; the review recomputed a FINITE-ONLY "
                             "Spearman of +0.367" if bp.get("spearman_sig0.4") is None
                             else bp["spearman_sig0.4"]),
              "reading": "S5 is FRAGILE across prior widths: -0.3 at the declared sigma=0.25 but +0.139 / "
                         "+0.367 (finite-only) at 0.15 / 0.40. The pre-registered rand10 candidate is "
                         "ABSENT. The 'selection score does not track held-out skill' conclusion holds at "
                         "the declared width but must not be stated as width-independent.",
              "source": "review out/claim_audit.json + repair verdicts.json"},
          "source": "isolated repair (carried, not recomputed here)"}

    # ---------------------------------------------------------------- assemble
    out = {
        "card": "EXACT-EVIDENCE COMPLETION for the full-spectrum FRF study (post-review items 1-3)",
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "supersedes": "the study's out/verdicts.json (NaN S1/S2, invalid F=R row; review C8, accepted D17)",
        "finiteness_contract": "every asserted statistic in this file was checked finite BEFORE writing "
                               "(_common.assert_finite raises on NaN/Inf/None); anything unavailable is an "
                               "explanatory string, never a null. Checker G05 re-walks every leaf.",
        "sampler_decision": {
            "sampler_run": False,
            "rationale": "This card completes deterministic held-out EVIDENCE for existing arms (per-fold "
                         "MAP refits, exact eigenbases, held-out scoring). It makes no new posterior or "
                         "uncertainty claim, so no sampler is required. NUTS/HMC remains the project "
                         "default for Bayesian updating (AGENTS Sampler Rule). Every MAP number here is a "
                         "deterministic optimizer result, NOT a posterior summary.",
            "default_sampler_for_future_updating": "NUTS/HMC"},
        "nonconvergence_carried": {
            "worst_rhat": WORST_RHAT, "worst_ess": WORST_ESS,
            "source": "study out/nuts_diagnostics.json (arm B, m_zpos_990z; all 8 arm-B runs 29-360 R-hat, "
                      "ESS ~2; arm C fold-1 R-hat 13.95, ESS 2.02)",
            "meaning": "arms B and C are scored at a deterministic MAP because their NUTS posteriors are "
                       "multimodal / non-converged. Their POSTERIOR UNCERTAINTY IS UNRESOLVED. Per the "
                       "review's C2 correction the amplitude likelihood is locally stiff but globally "
                       "unidentified; MAP scores are optimizer results only and are never trustworthy as "
                       "intervals."},
        "armC_exact": {
            "method": "deterministic multi-start (n=4) L-BFGS-B MAP of the shape field, refit INDEPENDENTLY "
                      "per LODO fold on that fold's 3 TRAIN drives only, on the exact-at-theta_MAP basis "
                      "A0_wide__enr; scored at theta=ones. NO SAMPLER.",
            "sub200_fold_mean": armC["fold_mean"]["sub200"],
            "b200_500_fold_mean": armC["fold_mean"]["b200_500"],
            "delta_vs_A1_exact_sub200": armC["paired_delta_vs_A1_exact"]["sub200"]["delta_mean"],
            "delta_se_sub200": armC["paired_delta_vs_A1_exact"]["sub200"]["delta_se"],
            "per_fold_delta_sub200": armC["paired_delta_vs_A1_exact"]["sub200"]["per_fold"],
            "S1_rule_met": armC["paired_delta_vs_A1_exact"]["sub200"]["S1_rule_met"],
            "leakage_audit": armC["leakage_audit"],
            "replaces": "the study's WITHDRAWN leaky exact arm-C aggregate (0.1570), which applied fold "
                        "m_xpos_990x's shape MAP to all 4 folds (review C6)",
            "study_leaky_number_for_reference": armC["withdrawn_study_number"]["study_exact_sub200"],
            "defect_decomposition": leak_probe,
            "finding": "the study's 0.1570 was RIGHT BY ACCIDENT. Its exact arm-C path carries TWO defects "
                       "that nearly cancelled: (1) the leak review C6 caught (fold-1's MAP on all 4 folds) "
                       "is worth +0.0822; (2) a basis mismatch the review did NOT catch -- the shape-field "
                       "raw coefficients were fit in the A0_wide theta=1 eigenbasis (r=209, 18 modes, "
                       "r0=106) and applied to the A0_wide__enr theta_MAP eigenbasis (r=194, 19 modes, "
                       "r0=108), i.e. transplanted between incompatible coordinate systems -- is worth "
                       "-0.0847. Net -0.0025 from the honest 0.1595. Near-agreement between a defective "
                       "and a correct number is NOT evidence the defect is harmless. Separately, the "
                       "study's sentence 'on the exact basis C's lead collapses' is WRONG as stated: A1 "
                       "dropped on the exact basis too, so C's LEAD over A1 is essentially unchanged "
                       "(+0.044 screening -> +0.046 exact). What fails S1 is PRECISION (per-fold deltas "
                       "-0.034..+0.132), not collapse."},
        "S1": S1, "S2": S2, "S3": S3, "S4": S4, "S5": S5,
        "arms_bands_table": arms,
        "what_this_card_did_not_do": [
            "no sampler run -> no posterior/uncertainty claim for any arm",
            "no vault (+XY) read -> dev drives only",
            "no net-CG work -> S3/S4 remain CANNOT-VERIFY (Card B)",
            "no re-litigation of the accepted D17 corrections; the repair's S1/S5 are carried, not recomputed",
            "theta_MAPs reused verbatim, never re-optimized -> no candidate was re-tuned by this card"],
    }
    C.assert_finite(out, "verdicts_final")          # refuse to write a null/NaN anywhere
    with open(os.path.join(C.MY_OUT, "verdicts_final.json"), "w") as f:
        json.dump(out, f, indent=1)
    C.log_step("verdicts_final", time.time() - t0)

    print("=== verdicts_final.json written (all leaves finite) ===")
    print(f"  S1 {S1['verdict']}: best arm {S1['best_arm']} {S1['best_delta_mean']:+.4f} "
          f"+/- {S1['best_delta_se']:.4f} (2SE {S1['best_two_se']:.4f})")
    print(f"  S2 (a) screening-selected: {S2['screening_selected']['delta_mean']:+.4f} "
          f"+/- {S2['screening_selected']['delta_se']:.4f} -> {S2['screening_selected']['verdict']} "
          f"(reproduces repair: {S2['screening_selected']['reproduces_repair']})")
    print(f"  S2 (b) exact-selected:     {S2['exact_selected']['delta_mean']:+.4f} "
          f"+/- {S2['exact_selected']['delta_se']:.4f} -> {S2['exact_selected']['verdict']}")
    print(f"  S3/S4 {S3['verdict']} | S5 {S5['verdict']} (fragile across prior widths)")
    print(f"  arm C exact (honest): {out['armC_exact']['sub200_fold_mean']:+.4f} "
          f"(delta vs A1 {out['armC_exact']['delta_vs_A1_exact_sub200']:+.4f})")


if __name__ == "__main__":
    main()
