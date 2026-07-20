#!/usr/bin/env python3
"""IMMUTABLE CHECKER — shocksat_composite_bakeoff_20260702 (SHA-locked BEFORE science; never edited during trial).

Verifies the pre-registered composite bake-off (task card docs/lab/composite_remodel_beck_runner_prompt.md):
full 2x3 matrix (M{0,1} x S{0,1,2} + statFEM F(k)), agentic-remodel funnel floors, shape-inclusive evidence
with prior-robustness, R1-R4 scoring gates, both historic metric traps, NUTS convergence, deliverables.

Three-tier per Result Status Standard: GREEN met / YELLOW documented honest miss / RED blocking.
Exit non-zero ONLY on RED. RED reasons are labeled 'claim_falsified' (pre-registered claim honestly
falsified — reportable) vs 'pipeline_failure' (missing/fabricated/inconsistent artifact — must fix).
"""
import json, os, sys
from pathlib import Path

WS = Path(__file__).resolve().parent
ARMS = ["M0S0", "M0S1", "M0S2", "M1S0", "M1S1", "M1S2"]
QOIS = ["shear_X", "shear_Y", "normal_Z"]
BARS = {"shear_X": 1.508, "shear_Y": 2.301, "normal_Z": 2.526}   # proven statFEM F(k) sharpness bars
COV_MIN, EXC_MAX = 0.95, 0.5                                     # R2 hard gate (1-oct, energy-weighted)
SIG_PRIOR_GRID = ["0.15", "0.25", "0.40"]

results = []   # (tier, gate, detail)


def add(tier, gate, detail):
    results.append((tier, gate, detail))


def jload(rel):
    p = WS / rel
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception as e:
        add("RED", f"parse:{rel}", f"pipeline_failure: unparseable ({e})")
        return None


# ---------------- gate files ----------------
for f in ["priority_deliverables.md", "question_framing.md", "quantity_contracts.md",
          "assumptions_ledger.md", "decisions_log.md"]:
    add("GREEN" if (WS / f).exists() else "RED", f"gatefile:{f}",
        "exists" if (WS / f).exists() else "pipeline_failure: missing gate file")

# ---------------- candidate funnel (P2) ----------------
cand = jload("out/candidates.json")
if cand is None:
    add("RED", "funnel:candidates", "pipeline_failure: out/candidates.json missing")
else:
    n = len(cand.get("candidates", []))
    add("GREEN" if n >= 100 else "RED", "funnel:n_candidates",
        f"{n} candidates (floor 100)" if n >= 100 else f"claim_falsified-or-pipeline: only {n} candidates (<100)")
    fams = cand.get("families_within_allowed", None)
    add("GREEN" if fams is True else "RED", "funnel:allowed_families",
        "declared within allowed families (no geometry rebuild)" if fams is True
        else "pipeline_failure: families_within_allowed not declared true")
t1 = jload("out/tier1_screen.json")
if t1 is None:
    add("RED", "funnel:tier1", "pipeline_failure: out/tier1_screen.json missing")
else:
    n1 = len(t1.get("scores", {}))
    ncand = len(cand.get("candidates", [])) if cand else 0
    add("GREEN" if ncand and n1 >= ncand else "RED", "funnel:tier1_complete",
        f"tier1 scored {n1}/{ncand}")
t2 = jload("out/tier2_full.json")
if t2 is None:
    add("RED", "funnel:tier2", "pipeline_failure: out/tier2_full.json missing")
else:
    n2 = len(t2.get("results", {}))
    add("GREEN" if 10 <= n2 <= 40 else "YELLOW", "funnel:tier2_count",
        f"{n2} full eigensolves (plan ~30)")
t3 = jload("out/tier3_evidence.json")
if t3 is None:
    add("RED", "funnel:tier3", "pipeline_failure: out/tier3_evidence.json missing")
else:
    # shape-inclusive evidence + prior robustness (R4 machinery)
    ok_obs = "MAC" in str(t3.get("observable", "")) or t3.get("shape_inclusive") is True
    add("GREEN" if ok_obs else "RED", "evidence:shape_inclusive",
        "evidence observable includes shape/MAC" if ok_obs
        else "pipeline_failure: frequency-only evidence used as selector (FORBIDDEN)")
    bp = t3.get("by_sigma_prior", {})
    missing = [s for s in SIG_PRIOR_GRID if s not in bp]
    add("GREEN" if not missing else "RED", "evidence:prior_robustness",
        f"sigma_prior grid complete {SIG_PRIOR_GRID}" if not missing
        else f"pipeline_failure: missing prior widths {missing}")

# ---------------- matrix scorecard (P1, R1-R4) ----------------
sc = jload("out/matrix_scorecard.json")
if sc is None:
    add("RED", "matrix:scorecard", "pipeline_failure: out/matrix_scorecard.json missing")
else:
    arms = sc.get("arms", {})
    for a in ARMS:
        if a not in arms:
            add("RED", f"matrix:arm:{a}", "pipeline_failure: arm missing (silent arm-dropping forbidden)")
    # metric traps declared
    add("GREEN" if sc.get("per_mode_amp_fit_in_scores") is False else "RED", "trap1:amp_fit",
        "no per-mode amplitude/phase fitting in scores (declared)" if sc.get("per_mode_amp_fit_in_scores") is False
        else "pipeline_failure: per_mode_amp_fit_in_scores not declared false")
    add("GREEN" if str(sc.get("pairing_method", "")).startswith("assignment") and sc.get("pairing_frozen") is True
        else "RED", "trap2:pairing",
        f"pairing={sc.get('pairing_method')} frozen={sc.get('pairing_frozen')}")
    add("GREEN" if sc.get("full_inband_mode_set") is True else "RED", "modes:full_set",
        "full in-band mode set declared (LIMITED DATA, NEVER LIMITED MODES)")
    for a, rec in arms.items():
        if a not in ARMS:
            continue
        # convergence (skip-for-reuse allowed only if labeled reused_proven with source)
        d = rec.get("nuts_diag", {})
        conv = d.get("converged")
        if conv is True:
            add("GREEN", f"nuts:{a}", f"R-hat {d.get('max_rhat')} ESS {d.get('min_ess')} div {d.get('divergences')}")
        elif conv is False:
            add("YELLOW", f"nuts:{a}", f"NOT converged (R-hat {d.get('max_rhat')}) — intervals labeled not-yet-converged")
        else:
            add("RED", f"nuts:{a}", "pipeline_failure: no NUTS diagnostics recorded")
        nm = rec.get("n_modes_used")
        add("GREEN" if isinstance(nm, int) and nm >= 15 else "RED", f"modes:{a}",
            f"n_modes_used={nm}" if isinstance(nm, int) and nm >= 15
            else f"pipeline_failure-or-pruning: n_modes_used={nm} (<15)")
        # R3 leave-modes-out audit
        r3 = rec.get("R3_leave_modes_out", {})
        wr = [v.get("widen_ratio", 0) for v in r3.values()] if r3 else []
        if not wr:
            add("RED", f"R3:{a}", "pipeline_failure: leave-modes-out audit missing")
        elif min(wr) > 1.0:
            add("GREEN", f"R3:{a}", f"widen ratios {['%.2f' % w for w in wr]} all > 1")
        else:
            dq = rec.get("disqualified") is True
            add("YELLOW" if dq else "RED", f"R3:{a}",
                f"widen ratio min {min(wr):.2f} <= 1 -> {'DISQUALIFIED (flagged)' if dq else 'pipeline_failure: overconfident arm not flagged disqualified'}")
        # R2 coverage per QOI
        for q in QOIS:
            r2 = rec.get("R2", {}).get(q)
            if r2 is None:
                add("RED", f"R2:{a}:{q}", "pipeline_failure: R2 missing")
                continue
            cov, exc = r2.get("weighted_coverage", 0), r2.get("energy_wtd_pos_dB_exceed", 99)
            covers = cov >= COV_MIN and exc <= EXC_MAX
            add("GREEN" if covers else "YELLOW", f"R2:{a}:{q}",
                f"cov {cov} exceed {exc} dB sharpness {r2.get('sharpness_vs_fem6db')} (bar {BARS[q]})"
                + ("" if covers else " — DOES NOT COVER (cannot win this QOI)"))
        # R1 present
        r1 = rec.get("R1", {})
        add("GREEN" if {"coverage", "crps_skill", "sigma_qoi"} <= set(r1) else "RED", f"R1:{a}",
            f"cov {r1.get('coverage')} CRPS-skill {r1.get('crps_skill')} sigma {r1.get('sigma_qoi')}"
            if {"coverage", "crps_skill", "sigma_qoi"} <= set(r1) else "pipeline_failure: R1 metrics missing")
    # delivery recommendation + R4
    deliv = sc.get("delivered", {})
    for q in ["shear", "normal"]:
        rec_q = deliv.get(q, {})
        arm = rec_q.get("arm")
        if arm not in ARMS:
            add("RED", f"deliver:{q}", "pipeline_failure: no delivered arm recommendation")
            continue
        n_best = rec_q.get("best_of_N")
        add("GREEN" if isinstance(n_best, int) and n_best >= 1 else "RED", f"winnerscurse:{q}",
            f"best-of-{n_best}" if n_best else "pipeline_failure: best_of_N not stated")
        arec = arms.get(arm, {})
        if arm.startswith("M1"):
            ev, ho = rec_q.get("evidence_beats_M0"), rec_q.get("heldout_beats_M0")
            add("GREEN" if (ev is True and ho is True) else "RED", f"R4:{q}",
                f"M1 delivery: evidence_beats_M0={ev} heldout_beats_M0={ho}"
                + ("" if (ev and ho) else " -> pipeline_failure: R4 violated (evidence-only wins are not delivered)"))
        if arec.get("disqualified") is True:
            add("RED", f"deliver:{q}:dq", "pipeline_failure: delivered arm is R3-disqualified")

# ---------------- deliverable artifacts ----------------
money = list(WS.glob("figures/fig_matrix*.png")) + list(WS.glob("figures/*money*.png"))
add("GREEN" if money and all(p.stat().st_size > 20000 for p in money) else "RED", "fig:money",
    f"{[p.name for p in money]}" if money else "pipeline_failure: matrix money figure missing")
for f in ["packet.md", "findings.md", "runtime.json"]:
    add("GREEN" if (WS / f).exists() else "RED", f"deliv:{f}",
        "exists" if (WS / f).exists() else "pipeline_failure: missing")
rt = jload("runtime.json")
if rt:
    ok = rt.get("active_runtime_s", 1e18) <= rt.get("elapsed_wallclock_s", 0)
    add("GREEN" if ok else "RED", "runtime:accounting",
        f"active {rt.get('active_runtime_s')}s <= wallclock {rt.get('elapsed_wallclock_s')}s" if ok
        else "pipeline_failure: active_runtime_s > elapsed_wallclock_s")

# ---------------- aggregate ----------------
tiers = [t for t, _, _ in results]
overall = "RED" if "RED" in tiers else ("YELLOW" if "YELLOW" in tiers else "GREEN")
ng, ny, nr = tiers.count("GREEN"), tiers.count("YELLOW"), tiers.count("RED")
report = {"overall": overall, "counts": {"green": ng, "yellow": ny, "red": nr},
          "gates": [{"tier": t, "gate": g, "detail": d} for t, g, d in results]}
(WS / "checker_report.json").write_text(json.dumps(report, indent=1))
print(f"OVERALL {overall}  ({ng}G/{ny}Y/{nr}R)")
for t, g, d in results:
    if t != "GREEN":
        print(f"  [{t}] {g}: {d}")
sys.exit(1 if overall == "RED" else 0)
