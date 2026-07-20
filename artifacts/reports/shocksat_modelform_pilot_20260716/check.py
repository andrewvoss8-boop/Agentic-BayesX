#!/usr/bin/env python3
"""check.py — IMMUTABLE checker for the MODEL-FORM PILOT (Card C, 2026-07-16).

SHA-locked BEFORE any science (CHECKER.sha256); proven RED on the empty workspace; never edited during
the trial. Encodes the card's §4 gates. Three-tier lights per AGENTS.md: exit nonzero ONLY on RED.

OVERALL = INTEGRITY/CONDUCT ONLY. The science verdicts (HQ1/HQ2 — falsification is a valid outcome) are
recomputed and printed prominently in their own block (the Card-B D7 reporting-trap fix: science status
is surfaced next to the light, never hidden behind an integrity GREEN).

File schemas: quantity_contracts.md Q7. Decision rules: question_framing.md §4 (this file recomputes
them; it never predicts or requires that they be MET).
"""
import hashlib
import json
import math
import os
import sys

WS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(WS, "out")
FIGD = os.path.join(WS, "figures")
PKGD = os.path.join(WS, "data", "packages_mf")

DEV_KEYS = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]
CLASSES = ["connectivity", "mesh_density", "element_formulation", "geometry", "property_control"]
GENUINE = ["connectivity", "mesh_density", "element_formulation", "geometry"]
OP2CLS = {"rbe2_soften": "connectivity", "rbe3_convert": "connectivity",
          "refine": "mesh_density", "formulation": "element_formulation",
          "warp_panel": "geometry", "joint_offset": "geometry",
          "thickness": "property_control", "scale": "property_control"}
NEW_OPS = ["rbe3_convert", "formulation", "warp_panel", "joint_offset"]
ROUNDS = [1, 2, 3]
QUOTA_PER_CLASS = 2
BUDGET = 80
SPOT_MAX_PCT = 0.01          # enrichment self-consistency bar (percent; exact-by-construction ~1e-8)
REPRO_TOL = 0.01             # |my wr2_rnd001 exact - 0.16507| (ARPACK start-vector bar, Card A G07)
REPRO_TARGET = 0.16507158788301496
# A1 exact per-fold sub-200 P1' (pinned read-only constants; study out/exact_freeze_scores.json)
A1_FOLDS = {"m_xpos_990x": 0.27383077524106014, "m_zpos_990z": 0.4981758785260245,
            "m_ypos_990y": -0.0019679768987999383, "m_zpos_900z": -0.3153000782114738}
NUM_TOL = 1e-9


def jload(p):
    with open(p) as f:
        return json.load(f)


def jlines(p):
    rows = []
    with open(p) as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def finite_walk(obj, where, bad):
    if isinstance(obj, dict):
        for k, v in obj.items():
            finite_walk(v, f"{where}.{k}", bad)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            finite_walk(v, f"{where}[{i}]", bad)
    elif isinstance(obj, bool) or obj is None:
        if obj is None:
            bad.append(f"null at {where}")
    elif isinstance(obj, (int, float)):
        if not math.isfinite(float(obj)):
            bad.append(f"non-finite at {where}: {obj!r}")


def paired(deltas):
    n = len(deltas)
    m = sum(deltas) / n
    var = sum((d - m) ** 2 for d in deltas) / (n - 1)
    return m, (var ** 0.5) / (n ** 0.5)


def gate(fn):
    def wrapped():
        try:
            return fn()
        except Exception as ex:  # a crashed gate is a failed gate, never a silent pass
            return "RED", [f"gate crashed: {type(ex).__name__}: {ex}"]
    return wrapped


def load_queries():
    return jlines(os.path.join(OUT, "query_log.jsonl"))


def active_classes():
    dropped = {}
    dp = os.path.join(OUT, "dropped_classes.json")
    if os.path.exists(dp):
        dropped = jload(dp)
    return [c for c in CLASSES if c not in dropped], dropped


# ---------------------------------------------------------------- G01 finiteness
@gate
def g01():
    msgs, bad = [], []
    for fn in ("verdicts.json", "results_table.json", "complexity.json"):
        p = os.path.join(OUT, fn)
        if not os.path.exists(p):
            return "RED", [f"missing out/{fn}"]
        finite_walk(jload(p), fn, bad)
    for rec in load_queries():
        finite_walk({k: rec[k] for k in ("exact_sub200", "exact_b200_500", "exact_folds")},
                    f"query.{rec.get('cid')}", bad)
    if bad:
        return "RED", bad[:12]
    return "GREEN", ["every reported statistic finite (verdicts, results table, complexity, query log)"]


# ---------------------------------------------------------------- G02 stratification + class attribution
@gate
def g02():
    qs = load_queries()
    if not qs:
        return "RED", ["no scored candidates (out/query_log.jsonl missing/empty)"]
    act, dropped = active_classes()
    msgs, bad = [], []
    for c, meta in dropped.items():
        vg = os.path.join(OUT, f"vgate_{meta.get('vgate','')}.json")
        if c in ("connectivity", "mesh_density", "property_control"):
            bad.append(f"class {c} may not be dropped (pre-validated operators exist)")
        elif not (os.path.exists(vg) and jload(vg).get("status") == "FAIL"):
            bad.append(f"class {c} dropped without a documented FAILED V-gate ({vg})")
    for rec in qs:
        cls = rec.get("cls")
        ops = rec.get("ops", [])
        if cls not in CLASSES:
            bad.append(f"{rec.get('cid')}: unknown class {cls}")
            continue
        if not ops or any(OP2CLS.get(o) != cls for o in ops):
            bad.append(f"{rec.get('cid')}: ops {ops} not all of class {cls} (no cross-class combos)")
        if rec.get("track") == "agent" and not str(rec.get("diagnosis_link", "")).strip():
            bad.append(f"{rec.get('cid')}: agent candidate without diagnosis_link")
        if rec.get("track") == "random" and rec.get("seed") is None:
            bad.append(f"{rec.get('cid')}: random candidate without seed")
    for r in ROUNDS:
        for tr in ("agent", "random"):
            for c in act:
                n = sum(1 for q in qs if q.get("round") == r and q.get("track") == tr
                        and q.get("cls") == c)
                if n != QUOTA_PER_CLASS:
                    bad.append(f"quota r{r}/{tr}/{c}: {n} != {QUOTA_PER_CLASS}")
    if bad:
        return "RED", bad[:15]
    msgs.append(f"quota met: {QUOTA_PER_CLASS}/class x {len(act)} classes x 3 rounds x 2 tracks "
                f"= {len(qs)} scored")
    if dropped:
        return "YELLOW", msgs + [f"DROPPED classes (documented failed V-gate): {sorted(dropped)} — "
                                 f"a {len(act)}-class pilot; caveat carries to every claim"]
    return "GREEN", msgs


# ---------------------------------------------------------------- G03 exact-basis + mech + reproduction
@gate
def g03():
    qs = load_queries()
    if not qs:
        return "RED", ["no scored candidates"]
    bad = []
    for rec in qs:
        cid = rec.get("cid")
        for k in rec:
            if "screening" in k.lower():
                bad.append(f"{cid}: FORBIDDEN screening-score key {k}")
        if rec.get("basis") != "exact_at_thetaMAP":
            bad.append(f"{cid}: basis tag {rec.get('basis')!r} != exact_at_thetaMAP")
        sp = rec.get("spot_max_pct")
        if sp is None or not math.isfinite(float(sp)) or float(sp) > SPOT_MAX_PCT:
            bad.append(f"{cid}: enrichment self-consistency {sp}% > {SPOT_MAX_PCT}%")
        ep = rec.get("enriched_pkg")
        if not ep or not os.path.exists(os.path.join(PKGD, f"{ep}.npz")):
            bad.append(f"{cid}: enriched package {ep!r} missing on disk")
        mech = rec.get("mech", {})
        if not mech.get("pass"):
            bad.append(f"{cid}: mech gate not passed: {mech}")
        if mech.get("n_rbm") != 6:
            bad.append(f"{cid}: n_rbm {mech.get('n_rbm')} != 6")
        folds = rec.get("exact_folds", {})
        if sorted(folds) != sorted(DEV_KEYS):
            bad.append(f"{cid}: fold keys {sorted(folds)} != dev keys")
    rp = os.path.join(OUT, "repro_check.json")
    if not os.path.exists(rp):
        bad.append("missing out/repro_check.json (pipeline reproduction, contract Q4)")
    else:
        r = jload(rp)
        d = abs(float(r.get("mine_exact_sub200", float("nan"))) - REPRO_TARGET)
        if not math.isfinite(d) or d > REPRO_TOL:
            bad.append(f"reproduction |diff| {d} > {REPRO_TOL} (wr2_rnd001 target {REPRO_TARGET})")
    if bad:
        return "RED", bad[:15]
    return "GREEN", [f"all {len(qs)} scored records exact-basis (self-consistency <= {SPOT_MAX_PCT}%), "
                     "mech gates passed, enriched packages on disk, pipeline reproduction within "
                     f"{REPRO_TOL} of the Card-A number"]


# ---------------------------------------------------------------- G04 V-gates precede scored use
@gate
def g04():
    qs = load_queries()
    if not qs:
        return "RED", ["no scored candidates"]
    bad, msgs = [], []
    tb = os.path.join(OUT, "vgate_tbuilder.json")
    if not (os.path.exists(tb) and jload(tb).get("status") == "PASS"):
        bad.append("vgate_tbuilder missing or not PASS (unconditional: all candidates flow through the "
                   "extended T-builder)")
    first_use = {}
    for rec in qs:
        for o in rec.get("ops", []):
            if o in NEW_OPS:
                t = rec.get("ts", "")
                if o not in first_use or t < first_use[o]:
                    first_use[o] = t
    for o, t in sorted(first_use.items()):
        vp = os.path.join(OUT, f"vgate_{o}.json")
        if not os.path.exists(vp):
            bad.append(f"operator {o} scored without out/vgate_{o}.json")
            continue
        v = jload(vp)
        if v.get("status") != "PASS":
            bad.append(f"operator {o} scored but V-gate status {v.get('status')!r}")
        if str(v.get("ts", "9")) > t:
            bad.append(f"operator {o}: V-gate ts {v.get('ts')} AFTER first scored use {t}")
        msgs.append(f"{o}: V-gate {v.get('status')} at {v.get('ts')}, first scored use {t}")
    if bad:
        return "RED", bad
    return "GREEN", msgs or ["no NEW operators scored (existing validated grammar only) + tbuilder PASS"]


# ---------------------------------------------------------------- G05 finalists fold-provenance
@gate
def g05():
    fp = os.path.join(OUT, "finalists.json")
    if not os.path.exists(fp):
        return "RED", ["missing out/finalists.json"]
    fin = jload(fp)
    qs = load_queries()
    bad, warns = [], []
    for tr in ("agent", "random"):
        top2 = [r["cid"] for r in sorted([q for q in qs if q.get("track") == tr],
                                         key=lambda r: -r["exact_sub200"])[:2]]
        got = [f["cid"] for f in fin.get("finalists", []) if f.get("track") == tr]
        if sorted(top2) != sorted(got):
            bad.append(f"{tr} finalists {got} != top-2 exact {top2} (no cherry-picking)")
    for f in fin.get("finalists", []):
        pf = f.get("per_fold", [])
        if sorted(x.get("fold") for x in pf) != sorted(DEV_KEYS):
            bad.append(f"{f.get('cid')}: per-fold records incomplete")
            continue
        thetas = []
        for x in pf:
            if x.get("fold") in x.get("train_keys", []):
                bad.append(f"{f.get('cid')}/{x.get('fold')}: fold inside its own train_keys (leak)")
            if sorted(x.get("train_keys", [])) != sorted(k for k in DEV_KEYS if k != x.get("fold")):
                bad.append(f"{f.get('cid')}/{x.get('fold')}: train_keys wrong")
            thetas.append(tuple(round(float(t), 12) for t in x.get("theta_refit", [])))
        if len(set(thetas)) == 1:
            if f.get("degenerate_reason"):
                warns.append(f"{f.get('cid')}: identical per-fold thetas, flagged degenerate: "
                             f"{f['degenerate_reason']}")
            else:
                bad.append(f"{f.get('cid')}: per-fold refit thetas IDENTICAL across folds without a "
                           "degenerate flag (cross-fold-reuse symptom, the C6 lesson)")
    if bad:
        return "RED", bad
    if warns:
        return "YELLOW", warns
    return "GREEN", [f"{len(fin.get('finalists', []))} finalists = top-2/track; per-fold refits with "
                     "clean fold provenance (no cross-fold reuse of fitted objects)"]


# ---------------------------------------------------------------- G06 budgets + seeds
@gate
def g06():
    qs = load_queries()
    if not qs:
        return "RED", ["no scored candidates"]
    bad = []
    for tr in ("agent", "random"):
        n = sum(1 for q in qs if q.get("track") == tr)
        if n > BUDGET:
            bad.append(f"{tr} budget exceeded: {n} > {BUDGET}")
    if not os.path.exists(os.path.join(OUT, "seeds.json")):
        bad.append("missing out/seeds.json")
    if bad:
        return "RED", bad
    na = sum(1 for q in qs if q.get("track") == "agent")
    nr = len(qs) - na
    return "GREEN", [f"budgets ok: agent {na}/{BUDGET}, random {nr}/{BUDGET}; seeds recorded"]


# ---------------------------------------------------------------- G07 leakage + vault
@gate
def g07():
    bad = []
    for fn in ("query_log.jsonl", "finalists.json", "score_log.jsonl"):
        p = os.path.join(OUT, fn)
        if os.path.exists(p):
            with open(p) as f:
                if "m_xy_990xy" in f.read():
                    bad.append(f"VAULT key appears in out/{fn}")
    vg = os.path.join(OUT, "vault_guard.json")
    if not os.path.exists(vg):
        bad.append("missing out/vault_guard.json")
    elif jload(vg).get("xy_files_opened") != 0:
        bad.append(f"vault guard reports +XY opens: {jload(vg).get('xy_files_opened')}")
    coded = os.path.join(WS, "code")
    if os.path.isdir(coded):
        for fn in sorted(os.listdir(coded)):
            if fn.endswith(".py"):
                with open(os.path.join(coded, fn)) as f:
                    src = f.read()
                if "score_vault" in src:
                    bad.append(f"code/{fn} references score_vault (forbidden this card)")
    if not os.path.exists(os.path.join(OUT, "query_log.jsonl")):
        bad.append("no query log (cannot certify leakage-free scoring)")
    if bad:
        return "RED", bad
    return "GREEN", ["no vault reads (guard 0 opens; key absent from all logs); no score_vault path"]


# ---------------------------------------------------------------- G08 complexity table + penalty rule
@gate
def g08():
    p = os.path.join(OUT, "complexity.json")
    if not os.path.exists(p):
        return "RED", ["missing out/complexity.json"]
    comp = jload(p)
    qs = {q["cid"]: q for q in load_queries()}
    if not qs:
        return "RED", ["no scored candidates"]
    bad = []
    for cid, rec in qs.items():
        c = comp.get(cid)
        if not c:
            bad.append(f"{cid}: missing from complexity table")
            continue
        for k in ("n_dof", "delta_dof_pct", "n_params", "delta_n_params", "solve_ratio"):
            v = c.get(k)
            if v is None or not math.isfinite(float(v)):
                bad.append(f"{cid}: complexity.{k} = {v!r}")
        deltas = [rec["exact_folds"][f] - A1_FOLDS[f] for f in DEV_KEYS]
        m, se = paired(deltas)
        should = bool(m < se and float(c.get("delta_dof_pct", 0)) > 10.0)
        if bool(c.get("not_worth_it")) != should:
            bad.append(f"{cid}: not_worth_it={c.get('not_worth_it')} but rule says {should} "
                       f"(gain {m:+.4f} vs 1xSE {se:.4f}, dDOF {c.get('delta_dof_pct')}%)")
    if bad:
        return "RED", bad[:12]
    n_nwi = sum(1 for c in comp.values() if c.get("not_worth_it"))
    return "GREEN", [f"complexity complete for {len(qs)} candidates; not-worth-it rule verified "
                     f"({n_nwi} labeled)"]


# ---------------------------------------------------------------- G09 figures scripted/linted/QA'd
@gate
def g09():
    mp = os.path.join(OUT, "fig_manifest.json")
    qp = os.path.join(OUT, "fig_qa.json")
    bad = []
    if not os.path.exists(mp):
        return "RED", ["missing out/fig_manifest.json"]
    man = jload(mp)
    figs = [f for f in man if f.endswith(".png")]
    if len(figs) < 5:
        bad.append(f"only {len(figs)} figures in manifest (need >= 5)")
    for f in figs:
        if not os.path.exists(os.path.join(FIGD, f)):
            bad.append(f"figure {f} missing on disk")
        script = man[f].get("script", "")
        if not os.path.exists(os.path.join(WS, script)):
            bad.append(f"figure {f}: generating script {script!r} missing (must be a saved .py)")
    if not os.path.exists(os.path.join(OUT, "tufte_lint.txt")):
        bad.append("missing out/tufte_lint.txt (tufte-data-graphics lint output)")
    if not os.path.exists(qp):
        bad.append("missing out/fig_qa.json (legibility QA)")
    else:
        qa = jload(qp)
        for f in figs:
            if f not in qa:
                bad.append(f"figure {f} has no QA record")
            elif not qa[f].get("pass"):
                bad.append(f"figure {f} failed legibility QA: {qa[f]}")
    if bad:
        return "RED", bad
    return "GREEN", [f"{len(figs)} figures, all scripted + linted + QA-passed"]


# ---------------------------------------------------------------- G10 runtime accounting
@gate
def g10():
    p = os.path.join(WS, "runtime.json")
    if not os.path.exists(p):
        return "RED", ["missing runtime.json"]
    r = jload(p)
    a, e = r.get("active_runtime_s"), r.get("elapsed_wallclock_s")
    if not (isinstance(a, (int, float)) and isinstance(e, (int, float)) and 0 < a <= e):
        return "RED", [f"runtime invalid: active {a}, wallclock {e} (need 0 < active <= wallclock)"]
    if not os.path.exists(os.path.join(OUT, "eigensolve_log.jsonl")):
        return "RED", ["missing out/eigensolve_log.jsonl (every solve must be logged)"]
    n = len(jlines(os.path.join(OUT, "eigensolve_log.jsonl")))
    return "GREEN", [f"active {a/3600:.2f} h <= wallclock {e/3600:.2f} h; {n} eigensolves logged"]


# ---------------------------------------------------------------- G11 self-SHA
@gate
def g11():
    p = os.path.join(WS, "CHECKER.sha256")
    if not os.path.exists(p):
        return "RED", ["missing CHECKER.sha256 (checker must be SHA-locked before science)"]
    with open(__file__, "rb") as f:
        me = hashlib.sha256(f.read()).hexdigest()
    locked = open(p).read().split()[0]
    if me != locked:
        return "RED", [f"checker sha {me[:12]} != locked {locked[:12]} (IMMUTABILITY VIOLATION)"]
    return "GREEN", [f"checker sha verified {me[:12]}"]


# ---------------------------------------------------------------- G12 verdict consistency (recompute)
@gate
def g12():
    vp = os.path.join(OUT, "verdicts.json")
    if not os.path.exists(vp):
        return "RED", ["missing out/verdicts.json"]
    v = jload(vp)
    qs = load_queries()
    if not qs:
        return "RED", ["no scored candidates"]
    bad = []
    tracks = {t: [q for q in qs if q["track"] == t] for t in ("agent", "random")}
    if not tracks["agent"] or not tracks["random"]:
        return "RED", ["a track has zero scored candidates"]
    best = {t: max(rows, key=lambda r: r["exact_sub200"]) for t, rows in tracks.items()}
    d1 = [best["agent"]["exact_folds"][f] - best["random"]["exact_folds"][f] for f in DEV_KEYS]
    m1, se1 = paired(d1)
    h1 = v.get("HQ1", {}).get("primary", {})
    if abs(h1.get("delta_mean", 1e9) - m1) > NUM_TOL or abs(h1.get("delta_se", 1e9) - se1) > NUM_TOL:
        bad.append(f"HQ1 primary mismatch: recomputed {m1:+.6f}+/-{se1:.6f} vs stored "
                   f"{h1.get('delta_mean')}+/-{h1.get('delta_se')}")
    if bool(h1.get("met")) != bool(m1 >= se1):
        bad.append(f"HQ1 primary met flag inconsistent (recomputed {m1 >= se1})")
    dm = [(sum(r["exact_folds"][f] for r in tracks["agent"]) / len(tracks["agent"])
           - sum(r["exact_folds"][f] for r in tracks["random"]) / len(tracks["random"]))
          for f in DEV_KEYS]
    m2, se2 = paired(dm)
    h2 = v.get("HQ1", {}).get("secondary", {})
    if abs(h2.get("delta_mean", 1e9) - m2) > NUM_TOL:
        bad.append(f"HQ1 secondary mismatch: recomputed {m2:+.6f} vs stored {h2.get('delta_mean')}")
    any_met = False
    for c in GENUINE:
        rows = [q for q in qs if q["cls"] == c]
        if not rows:
            continue
        b = max(rows, key=lambda r: r["exact_sub200"])
        dc = [b["exact_folds"][f] - A1_FOLDS[f] for f in DEV_KEYS]
        mc, sec = paired(dc)
        stored = v.get("HQ2", {}).get("per_class", {}).get(c, {}).get("best", {})
        if abs(stored.get("delta_mean", 1e9) - mc) > NUM_TOL or \
           abs(stored.get("delta_se", 1e9) - sec) > NUM_TOL:
            bad.append(f"HQ2 {c} mismatch: recomputed {mc:+.6f}+/-{sec:.6f} vs stored "
                       f"{stored.get('delta_mean')}+/-{stored.get('delta_se')}")
        if bool(stored.get("met")) != bool(mc >= sec):
            bad.append(f"HQ2 {c} met flag inconsistent")
        any_met = any_met or (mc >= sec)
    if bool(v.get("HQ2", {}).get("met")) != any_met:
        bad.append(f"HQ2 overall met flag inconsistent (recomputed {any_met})")
    for r in ROUNDS:
        if any(q.get("round") == r and q.get("track") == "agent" for q in qs):
            if not os.path.exists(os.path.join(OUT, f"round_summary_r{r}.md")):
                bad.append(f"missing out/round_summary_r{r}.md (diagnosis->class->edit links)")
    if bad:
        return "RED", bad
    return "GREEN", ["verdicts recomputed from query log + pinned A1 folds: all values and met flags "
                     "consistent; round summaries present"]


GATES = [("G01 finiteness of every reported statistic", g01),
         ("G02 stratification quota + class attribution", g02),
         ("G03 exact-basis scoring + mech gates + reproduction", g03),
         ("G04 V-gates precede scored use", g04),
         ("G05 finalist fold-provenance (no cross-fold reuse)", g05),
         ("G06 budgets + seeds", g06),
         ("G07 leakage + no vault", g07),
         ("G08 complexity table + penalty rule", g08),
         ("G09 figures scripted/linted/QA'd", g09),
         ("G10 runtime accounting", g10),
         ("G11 checker self-SHA", g11),
         ("G12 verdict consistency (recomputed)", g12)]


def main():
    results = []
    print("=" * 78)
    print("MODEL-FORM PILOT checker (immutable; Card C 2026-07-16)")
    print("=" * 78)
    for name, fn in GATES:
        status, msgs = fn()
        results.append((name, status, msgs))
        print(f"[{status:6s}] {name}")
        for m in msgs:
            print(f"         - {m}")
    n_red = sum(1 for _, s, _ in results if s == "RED")
    n_yel = sum(1 for _, s, _ in results if s == "YELLOW")
    overall = "RED" if n_red else ("YELLOW" if n_yel else "GREEN")
    print("-" * 78)
    print(f"OVERALL (integrity/conduct ONLY): {overall}  "
          f"({sum(1 for _, s, _ in results if s == 'GREEN')}G/{n_yel}Y/{n_red}R)")
    # science block — printed regardless, NEVER folded into OVERALL (falsification is valid)
    vp = os.path.join(OUT, "verdicts.json")
    if os.path.exists(vp):
        try:
            v = jload(vp)
            h1 = v.get("HQ1", {}).get("primary", {})
            print(f"SCIENCE (pre-registered; not an integrity gate): "
                  f"HQ1 {'MET' if h1.get('met') else 'NOT MET'} "
                  f"({h1.get('delta_mean', float('nan')):+.4f} vs 1xSE "
                  f"{h1.get('delta_se', float('nan')):.4f}); "
                  f"HQ2 {'MET' if v.get('HQ2', {}).get('met') else 'NOT MET'}")
            for c, cc in sorted(v.get("HQ2", {}).get("per_class", {}).items()):
                b = cc.get("best", {})
                print(f"    class {c:20s} best-vs-A1 {b.get('delta_mean', float('nan')):+.4f} "
                      f"+/- {b.get('delta_se', float('nan')):.4f} "
                      f"[{'MET' if b.get('met') else 'not met'}] best={b.get('cid')}")
        except Exception as ex:
            print(f"SCIENCE: verdicts.json unreadable ({ex})")
    else:
        print("SCIENCE: no verdicts yet")
    rep = {"overall": overall,
           "gates": [{"name": n, "status": s, "messages": m} for n, s, m in results]}
    with open(os.path.join(WS, "checker_report.json"), "w") as f:
        json.dump(rep, f, indent=1)
    sys.exit(1 if overall == "RED" else 0)


if __name__ == "__main__":
    main()
