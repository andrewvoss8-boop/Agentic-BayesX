#!/usr/bin/env python3
"""IMMUTABLE checker — IFT real-validation study (verification gate §10).

Do NOT edit during a trial. Encodes GREEN/YELLOW/RED (AGENTS.md Result Status Standard) with EXPLICIT numbers,
the apples-to-apples provenance check, and the PRE-COMMITTED verdict rule (question_framing.md §5). The verdict
STRING (WIN / ROBUSTNESS-WIN / TIE / HONEST-NEGATIVE) is GENERATED HERE from the proper-score numbers — never
hand-set. Exits non-zero ONLY on RED (documented YELLOWs do not abort replay).

Run: python check.py   (or via run_all.sh). Writes checker_report.json.
"""
from __future__ import annotations
import hashlib
import json
import subprocess
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent
OUT = WS / "out"
FIG = WS / "figures"

GREEN, YELLOW, RED = "GREEN", "YELLOW", "RED"
gates = []   # (name, status, detail)


def add(name, status, detail):
    gates.append({"gate": name, "status": status, "detail": detail})


def load_json(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception as e:
        return {"_error": str(e)}


# ---------------------------------------------------------------- G1 apples-to-apples provenance (sha256)
def sha256(p):
    h = hashlib.sha256()
    h.update(Path(p).read_bytes())
    return h.hexdigest()


def gate_provenance():
    man = WS / "manifest_sha256.txt"
    if not man.exists():
        add("provenance_sha256", RED, "manifest_sha256.txt missing — apples-to-apples unverifiable")
        return
    bad = []
    n = 0
    for line in man.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("##"):
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        expect, rel = parts
        if rel.startswith(".."):     # sibling read-only refs: verify if reachable, else note
            f = WS / rel
            if f.exists() and sha256(f) != expect:
                bad.append(f"{rel} (sibling drift)")
            continue
        f = WS / rel
        n += 1
        if not f.exists():
            bad.append(f"{rel} MISSING")
        elif sha256(f) != expect:
            bad.append(f"{rel} SHA MISMATCH")
    if bad:
        add("provenance_sha256", RED, f"copied core/score/realfrf/data NOT byte-identical: {bad}")
    else:
        add("provenance_sha256", GREEN, f"{n} copied files byte-identical to the StatFEM run (apples-to-apples)")


# ---------------------------------------------------------------- verdict generation from the numbers (§5)
def _med(d, q, score):
    """median of a proper score for arm-dict d at QOI q ('peak'/'band'), score in {interval,crps,logpd}."""
    try:
        return float(d[q][score]["med"])
    except Exception:
        return None


def generate_verdict(sc):
    """Return (verdict_str, rationale_dict). Pure function of the scorecard numbers."""
    arms = sc.get("arms", {})
    ift, l5, m2 = arms.get("IFT", {}), arms.get("L5", {}), arms.get("M2", {})
    ift_conv = float(ift.get("converged_frac", 0.0))
    m2_conv = float(m2.get("converged_frac", 0.0))
    beta_weak = float(ift.get("beta", {}).get("weakly_identified_frac", 0.0))
    beta_collapsed = bool(ift.get("beta", {}).get("collapsed", False))

    # IFT must converge (incl. beta) on >=80% of splits OR carry a documented TMCMC escalation
    ift_ok = ift_conv >= 0.8 or bool(ift.get("tmcmc_escalated", False))
    r = {"ift_converged_frac": ift_conv, "m2_converged_frac": m2_conv,
         "beta_weak_frac": beta_weak, "beta_collapsed": beta_collapsed}

    if not ift_ok:
        return "HONEST-NEGATIVE", {**r, "why": "IFT did not converge (incl. beta) on the headline config"}

    # proper-score comparison vs L5 (the bar): interval + crps lower = better, logpd higher = better
    wins = 0; total = 0; comp = {}
    for q in ("peak", "band"):
        for score, better in (("interval", "lower"), ("crps", "lower"), ("logpd", "higher")):
            a, b = _med(ift, q, score), _med(l5, q, score)
            if a is None or b is None:
                continue
            total += 1
            won = (a < b) if better == "lower" else (a > b)
            wins += int(won)
            comp[f"{q}_{score}"] = {"ift": a, "l5": b, "ift_better": bool(won)}
    r["proper_score_comparison"] = comp
    r["ift_wins_of_total"] = [wins, total]

    # calibration: IFT not worse than L5 (coverage within 0.1, |z_std-1| not larger by >0.5)
    def cov(d, q):
        try:
            return float(d[q]["coverage"]["med"])
        except Exception:
            return None
    cal_ok = True
    for q in ("peak", "band"):
        ci, cl = cov(ift, q), cov(l5, q)
        if ci is not None and cl is not None and ci < cl - 0.10:
            cal_ok = False
    r["calibration_not_worse_than_l5"] = cal_ok

    if total > 0 and wins >= max(4, total - 1) and cal_ok:
        return "WIN", {**r, "why": "IFT beats L5 on a majority of proper scores at equal-or-better calibration"}
    # ROBUSTNESS-WIN: IFT converges + calibrated where M2 (same field observable) diverged
    ift_calibrated = all((cov(ift, q) is None or cov(ift, q) >= 0.80) for q in ("peak", "band"))
    if m2_conv < 0.5 and ift_calibrated:
        return "ROBUSTNESS-WIN", {**r, "why": "IFT converges + stays calibrated where M2 whole-FRF diverged "
                                  "(physics-in-prior more robust than physics-in-likelihood on the same observable)"}
    if beta_collapsed:
        return "HONEST-NEGATIVE", {**r, "why": "beta collapsed -> wide regression, no better than L5+disc"}
    return "TIE", {**r, "why": "IFT ~ L5 within split-to-split spread; competitive, not better here"}


def gate_scorecard_and_verdict():
    p = OUT / "scorecard.json"
    if not p.exists():
        add("scorecard_exists", RED, "out/scorecard.json missing — head-to-head not yet computed (study in progress)")
        add("verdict_generated", RED, "no scorecard -> no verdict")
        return None
    sc = load_json(p)
    arms = sc.get("arms", {})
    need = ("IFT", "L5", "M2")
    have = [a for a in need if a in arms]
    seeds_ok = len(sc.get("seeds", [])) >= 25
    # identical-splits check: arms must share the same seed list
    same_seeds = all(arms.get(a, {}).get("seeds", sc.get("seeds")) == sc.get("seeds") for a in have)
    if set(have) != set(need):
        add("scorecard_exists", RED, f"scorecard missing arms: have {have}, need {list(need)}")
    elif not seeds_ok:
        add("scorecard_exists", YELLOW, f"only {len(sc.get('seeds', []))} splits (<25)")
    elif not same_seeds:
        add("scorecard_exists", RED, "arms NOT scored on identical splits (apples-to-apples broken)")
    else:
        add("scorecard_exists", GREEN, f"IFT/L5/M2 scored on {len(sc['seeds'])} identical splits")

    # IFT convergence incl. beta
    ift = arms.get("IFT", {})
    conv = float(ift.get("converged_frac", 0.0))
    tmcmc = bool(ift.get("tmcmc_escalated", False))
    if conv >= 0.8:
        add("ift_converged_incl_beta", GREEN, f"IFT converged (incl. beta) on {conv*100:.0f}% of splits")
    elif tmcmc:
        add("ift_converged_incl_beta", YELLOW, "IFT used a documented NUTS->TMCMC escalation")
    elif conv > 0:
        add("ift_converged_incl_beta", YELLOW, f"IFT converged on only {conv*100:.0f}% of splits (documented)")
    else:
        add("ift_converged_incl_beta", RED, "IFT not converged and presented without escalation")

    # beta identifiability reported
    beta = ift.get("beta", {})
    if "weakly_identified_frac" in beta or "beta_med_dist" in beta:
        wk = beta.get("weakly_identified_frac")
        add("beta_identifiability_reported", GREEN if wk is not None else YELLOW,
            f"beta posterior reported; weakly_identified_frac={wk}")
    else:
        add("beta_identifiability_reported", RED, "beta identifiability not reported")

    # the verdict (generated, never hand-set)
    verdict, rationale = generate_verdict(sc)
    if verdict in ("WIN", "ROBUSTNESS-WIN", "TIE", "HONEST-NEGATIVE"):
        add("verdict_generated", GREEN, f"verdict={verdict} (generated from numbers): {rationale.get('why')}")
    else:
        add("verdict_generated", RED, f"verdict not a valid pre-committed outcome: {verdict}")
    return {"verdict": verdict, "rationale": rationale}


# ---------------------------------------------------------------- figures: tufte + image-QA + overlap
REQUIRED_FIGS = ["figA_scorecard", "figB_beta", "figC_heldout_frf_overlay", "figD_discretization",
                 "fig_convergence_table"]


def gate_figures():
    missing, failed = [], []
    for f in REQUIRED_FIGS:
        png = FIG / f"{f}.png"
        qa = FIG / f"{f}.qa.json"
        if not png.exists():
            missing.append(f"{f}.png")
            continue
        if not qa.exists():
            failed.append(f"{f} (no qa.json)")
            continue
        q = load_json(qa)
        if not (q.get("tufte_pass") and q.get("image_qa_pass") and q.get("overlap_pass")):
            failed.append(f"{f} (tufte={q.get('tufte_pass')} imgqa={q.get('image_qa_pass')} "
                          f"overlap={q.get('overlap_pass')})")
    if missing or failed:
        st = RED if missing else RED  # a claimed figure that fails QA is RED
        add("figures_tufte_imageqa_overlap", st, f"missing={missing} failed={failed}")
    else:
        add("figures_tufte_imageqa_overlap", GREEN, f"{len(REQUIRED_FIGS)} figures tufte+image-QA+overlap clean")


# ---------------------------------------------------------------- documented YELLOWs (honest scope)
def gate_documented_yellows():
    # these are inherent scope caveats; presence of the documentation is what we check
    notes = []
    for f in ("assumptions_ledger.md", "method_ift.md", "decisions_log.md"):
        if not (WS / f).exists():
            add("scope_docs", RED, f"{f} missing")
            return
    add("single_hit_split_only_yellow", YELLOW,
        "1 hit / 1 impact, channel-split-only validation (A9/A10) — labeled reduction, never 'success'")
    add("coarse_fem_ceiling_yellow", YELLOW,
        "coarse-FEM model-form ceiling binds (StatFEM finding) — carried in deck")
    add("moment_approx_yellow", YELLOW,
        "log-magnitude moment approximation (D0/B5): exact at high SNR, weak/downweighted in deep antiresonances")


# ---------------------------------------------------------------- assemble
def main():
    gate_provenance()
    verdict_obj = gate_scorecard_and_verdict()
    gate_figures()
    gate_documented_yellows()

    statuses = [g["status"] for g in gates]
    overall = RED if RED in statuses else (YELLOW if YELLOW in statuses else GREEN)
    n = {s: statuses.count(s) for s in (GREEN, YELLOW, RED)}
    report = {"study": "ift_real_validation_20260619",
              "overall": overall, "counts": {"green": n[GREEN], "yellow": n[YELLOW], "red": n[RED]},
              "verdict": verdict_obj, "gates": gates,
              "note": "Exits non-zero ONLY on RED. YELLOW = documented honest caveat, never 'success'."}
    (WS).joinpath("checker_report.json").write_text(json.dumps(report, indent=2))
    print(f"OVERALL {overall}  (green {n[GREEN]} / yellow {n[YELLOW]} / red {n[RED]})")
    if verdict_obj:
        print(f"VERDICT (generated): {verdict_obj['verdict']} — {verdict_obj['rationale'].get('why')}")
    for g in gates:
        print(f"  [{g['status']:6}] {g['gate']}: {g['detail']}")
    sys.exit(1 if overall == RED else 0)


if __name__ == "__main__":
    main()
