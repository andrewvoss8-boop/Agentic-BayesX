#!/usr/bin/env python3
"""Immutable checker — ShockSat FRF-Domain Damping Updating (20260710).

Encodes the pre-registered gates from question_framing.md (card §9.3). Runs against THIS workspace and writes
checker_report.json. Exit code is non-zero ONLY on RED, so documented YELLOW findings do not abort the
one-command replay (AGENTS Result Status Standard). Every gate returns GREEN / YELLOW / RED with a reason.

Immutability: written to grade BOTH the pre-science state (most science artifacts absent -> those gates RED
"science not run") and the completed state, so it never needs editing during the trial. The pipeline emits
exactly the artifact schema this file reads. SHA-locked (CHECKER.sha256) BEFORE the science phase.

Artifact schema this checker defines (the pipeline must emit these):
  out/mech_gates.json      : {V1..V5: {pass, metric}}
  out/gate_D1.json         : {pass, viscous_peak_err, structural_peak_err, rayleigh_zeta_err}
  out/gate_D2.json         : {pass, recovered_ok, flagged_not_identifiable, note}
  out/gate_F.json          : {pass, identical, freq_shift, amp_scale, phase_flip}  (each True/False + values)
  out/gate_O.json          : {pass, selfmac_max_offdiag, fisher_rank, n_target, obs_resid_frac, unobs_resid_frac}
  out/query_log.jsonl      : one JSON/line, {track: agent|random, ...}
  out/spot_check_*.json    : {rel_err} for exact-basis decision scores (<=0.003)
  out/honesty_<cid>.json   : {lmo_widen_ratio, zeta_min, zeta_max, eta_max, damping_dim, disqualified}
  out/ablation.json        : {winner_margin, damping_only_margin, shape_only_margin, damping_share, attribution}
  out/nuts_<cid>.json      : {rhat_max, ess_min, div_frac}
  out/vault_scores.json ; VAULT_FREEZE.sha256 ; out/vault_download.log
  out/verdicts.json        : {S1,S2,S3,S4:{pass,...}, overall_claim}
  runtime.json ; out/fig_qa.json ; figures/*.png
"""
import json, os, re, glob, hashlib, sys

WS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
def wp(*p): return os.path.join(WS, *p)

AGENT_BUDGET = 60
RANDOM_BUDGET = 60
ZETA_LO, ZETA_HI = 0.002, 0.05      # physical-damping gate [0.2%, 5%]
ETA_HI = 0.20
DAMP_DIM_MAX = 10
SPOT_TOL = 0.003                    # exact-basis rule 0.3%
results = []

def add(gate, status, reason): results.append((gate, status, reason))
def exists(rel): return os.path.exists(wp(rel))
def load_json(rel):
    try:
        with open(wp(rel)) as f: return json.load(f)
    except Exception:
        return None

# ---------------------------------------------------------------- PRE gates
GATE_FILES = ["priority_deliverables.md", "question_framing.md", "quantity_contracts.md",
              "assumptions_ledger.md", "decisions_log.md", "REUSED_code.sha256"]
missing = [f for f in GATE_FILES if not exists(f)]
add("gate_files", "GREEN" if not missing else "RED",
    "all present" if not missing else f"missing {missing}")

def reused_integrity():
    p = wp("REUSED_code.sha256")
    if not os.path.exists(p): return ("RED", "REUSED_code.sha256 absent")
    bad = []
    for line in open(p):
        line = line.strip()
        if not line: continue
        h, rel = line.split(None, 1)
        src = os.path.join(ROOT, rel.strip())
        if not os.path.exists(src): bad.append(f"{rel} MISSING"); continue
        if hashlib.sha256(open(src, "rb").read()).hexdigest() != h: bad.append(f"{rel} CHANGED")
    return ("GREEN", "all reused sources unchanged") if not bad else ("RED", str(bad))
add("reused_integrity", *reused_integrity())

# ---------------------------------------------------------------- V1-V5 mechanics
def mech_gates():
    m = load_json("out/mech_gates.json")
    if m is None: return ("RED", "out/mech_gates.json missing (science not run)")
    need = ["V1", "V2", "V3", "V4", "V5"]
    miss = [k for k in need if k not in m]
    if miss: return ("RED", f"mech gates missing {miss}")
    fails = [k for k in need if not m[k].get("pass", False)]
    if fails: return ("RED", f"mechanics gates FAILED {fails} (blocks science)")
    return ("GREEN", "V1-V5 pass: " + ", ".join(f"{k}={m[k].get('metric')}" for k in need))
add("mechanics_V1_V5", *mech_gates())

# ---------------------------------------------------------------- Gate D1 damping physics
def gate_D1():
    d = load_json("out/gate_D1.json")
    if d is None: return ("RED", "out/gate_D1.json missing (damping physics not validated -> run VOID)")
    if not d.get("pass", False):
        return ("RED", f"damping physics FAILED: {d} (analytic FRF peak height not reproduced)")
    return ("GREEN", f"damping physics: viscous {d.get('viscous_peak_err')}, "
                     f"structural {d.get('structural_peak_err')}, rayleigh {d.get('rayleigh_zeta_err')} (<=2%)")
add("gate_D1_damping_physics", *gate_D1())

# ---------------------------------------------------------------- Gate D2 damping identifiability @2Hz
def gate_D2():
    d = load_json("out/gate_D2.json")
    if d is None: return ("RED", "out/gate_D2.json missing (resolution/identifiability not tested)")
    if not d.get("pass", False):
        return ("YELLOW", f"damping identifiability test inconclusive: {d.get('note')}")
    return ("GREEN", f"identifiability@2Hz honored: recovered {d.get('recovered_ok')}, "
                     f"flagged-not-identifiable {d.get('flagged_not_identifiable')} ({d.get('note')})")
add("gate_D2_identifiability", *gate_D2())

# ---------------------------------------------------------------- Gate F metric correctness
def gate_F():
    d = load_json("out/gate_F.json")
    if d is None: return ("RED", "out/gate_F.json missing (FDAC/FRAC/FRSF not validated)")
    subs = ["identical", "freq_shift", "amp_scale", "phase_flip"]
    bad = [s for s in subs if not (d.get(s, {}) or {}).get("pass", False)]
    if bad: return ("RED", f"metric-correctness sub-tests FAILED {bad}: {d}")
    return ("GREEN", "FDAC/FRAC/FRSF correct on all 4 synthetic sub-tests "
                     "(identical, freq-shift, amp-scale, phase-flip)")
add("gate_F_metrics", *gate_F())

# ---------------------------------------------------------------- Gate O sensor observability
def gate_O():
    d = load_json("out/gate_O.json")
    if d is None: return ("RED", "out/gate_O.json missing (observability bound not computed)")
    need = ["selfmac_max_offdiag", "fisher_rank", "n_target", "obs_resid_frac", "unobs_resid_frac"]
    miss = [k for k in need if k not in d]
    if miss: return ("RED", f"gate_O missing fields {miss}")
    # Reporting gate: it must have RUN and produced the partition. The FINDING (data- vs model-limited) is
    # reported, not pass/fail. Flag YELLOW if most residual is unobservable (bounds reachable headroom).
    ur = d.get("unobs_resid_frac", 0.0)
    if ur >= 0.5:
        return ("YELLOW", f"observability bound: {ur:.2f} of A0 residual is sensor-UNOBSERVABLE "
                          f"(data-limited; no updating can fix it). self-MAC off-diag {d.get('selfmac_max_offdiag')}, "
                          f"Fisher rank {d.get('fisher_rank')}/{d.get('n_target')}")
    return ("GREEN", f"observability computed: {ur:.2f} residual unobservable, self-MAC off-diag "
                     f"{d.get('selfmac_max_offdiag')}, Fisher rank {d.get('fisher_rank')}/{d.get('n_target')}")
add("gate_O_observability", *gate_O())

# ---------------------------------------------------------------- query budget
def budget():
    p = wp("out/query_log.jsonl")
    if not os.path.exists(p): return ("RED", "out/query_log.jsonl missing")
    n = {"agent": 0, "random": 0}
    try:
        for line in open(p):
            line = line.strip()
            if not line: continue
            t = json.loads(line).get("track")
            if t in n: n[t] += 1
    except Exception as e:
        return ("RED", f"query_log parse error {e}")
    over = []
    if n["agent"] > AGENT_BUDGET: over.append(f"agent {n['agent']}>{AGENT_BUDGET}")
    if n["random"] > RANDOM_BUDGET: over.append(f"random {n['random']}>{RANDOM_BUDGET}")
    if over: return ("RED", "BUDGET EXCEEDED " + str(over))
    if n["agent"] == 0 and n["random"] == 0: return ("RED", "query_log empty (science not run)")
    return ("GREEN", f"within budget: agent {n['agent']}<={AGENT_BUDGET}, random {n['random']}<={RANDOM_BUDGET}")
add("query_budget", *budget())

# ---------------------------------------------------------------- no dev-cache reads in the loop
def no_dev_leak():
    lp = wp("code/loop.py")
    if not os.path.exists(lp): return ("RED", "code/loop.py missing (science not run)")
    src = open(lp).read()
    bad = re.findall(r"np\.load\([^)]*m_[a-z0-9_]+\.npz", src)
    if bad: return ("RED", f"loop.py reads drive caches directly (dev leak risk): {bad}")
    return ("GREEN", "loop.py contains no direct drive-cache reads (dev returns scalars only)")
add("no_dev_residual_leak", *no_dev_leak())

# ---------------------------------------------------------------- no amplitude/damping LSQ + markers + dim<=10
def no_lsq():
    sp = wp("code/score.py")
    if not os.path.exists(sp): return ("RED", "code/score.py missing (science not run)")
    src = open(sp).read()
    hits = [m for m in ("lstsq", "pinv", "np.linalg.solve(") if m in src]
    if hits: return ("RED", f"score.py contains LSQ-like calls {hits} (per-mode amp/damping fit forbidden)")
    for mk in ("NO-PER-MODE-LSQ", "LOW-DIM-PHYSICAL-DAMPING-ONLY"):
        if mk not in src: return ("YELLOW", f"score.py lacks the {mk} marker; manual review required")
    return ("GREEN", "score.py: one global gain + low-dim physical damping only, no per-mode amp/damping LSQ")
add("no_amplitude_or_damping_lsq", *no_lsq())

# ---------------------------------------------------------------- damping dimension <= 10 (all scored cands)
def damp_dim():
    fs = glob.glob(wp("out/honesty_*.json"))
    if not fs: return ("RED", "no out/honesty_*.json (damping-dim not auditable yet)")
    over = []
    for f in fs:
        dd = json.load(open(f)).get("damping_dim")
        if dd is not None and dd > DAMP_DIM_MAX: over.append((os.path.basename(f), dd))
    if over: return ("RED", f"damping dimension >{DAMP_DIM_MAX} {over} (amplitude-fit in disguise)")
    return ("GREEN", f"all audited candidates have damping_dim <= {DAMP_DIM_MAX}")
add("damping_dim_le_10", *damp_dim())

# ---------------------------------------------------------------- exact-basis rule for decision scores
def exact_basis():
    fs = glob.glob(wp("out/spot_check_*.json"))
    if not fs: return ("RED", "no out/spot_check_*.json (exact-basis rule not verified)")
    bad = []
    for f in fs:
        re_ = json.load(open(f)).get("rel_err")
        if re_ is not None and re_ > SPOT_TOL: bad.append((os.path.basename(f), re_))
    if bad: return ("RED", f"decision scores exceed exact-basis tol {SPOT_TOL}: {bad} (enrich required)")
    return ("GREEN", f"all {len(fs)} freeze-set spot checks within exact-basis tol {SPOT_TOL}")
add("exact_basis_decision_scores", *exact_basis())

# ---------------------------------------------------------------- physical-damping bounds (finalists + A0d)
def phys_damp():
    fs = glob.glob(wp("out/honesty_*.json"))
    if not fs: return ("RED", "no out/honesty_*.json (physical-damping gate not evaluated)")
    dq = []
    for f in fs:
        d = json.load(open(f))
        zmn, zmx, emx = d.get("zeta_min"), d.get("zeta_max"), d.get("eta_max")
        bad = []
        if zmn is not None and zmn < ZETA_LO: bad.append(f"zeta_min {zmn}<{ZETA_LO}")
        if zmx is not None and zmx > ZETA_HI: bad.append(f"zeta_max {zmx}>{ZETA_HI}")
        if emx is not None and emx > ETA_HI: bad.append(f"eta_max {emx}>{ETA_HI}")
        if bad and d.get("is_winner_or_baseline", True):
            dq.append((os.path.basename(f), bad, d.get("disqualified")))
    if dq:
        undis = [x for x in dq if not x[2]]
        if undis: return ("RED", f"physical-damping breach presented as valid (must be DISQUALIFIED): {undis}")
        return ("YELLOW", f"candidate(s) breach physical-damping bounds and are correctly DISQUALIFIED: {dq}")
    return ("GREEN", f"all audited arms within physical damping bounds zeta[{ZETA_LO},{ZETA_HI}] eta<={ETA_HI}")
add("physical_damping_bounds", *phys_damp())

# ---------------------------------------------------------------- A0d damping baseline present
def a0d():
    if not (glob.glob(wp("out/*A0d*")) or load_json("out/verdicts.json") and
            "A0d" in json.dumps(load_json("out/verdicts.json") or {})):
        return ("RED", "A0d damping baseline arm absent (required reference for S4)")
    return ("GREEN", "A0d damping-updated baseline present")
add("a0d_baseline_present", *a0d())

# ---------------------------------------------------------------- S4 ablation present
def ablation():
    d = load_json("out/ablation.json")
    if d is None: return ("RED", "out/ablation.json missing (S4 attribution not decomposed)")
    need = ["winner_margin", "damping_only_margin", "shape_only_margin", "damping_share", "attribution"]
    miss = [k for k in need if k not in d]
    if miss: return ("RED", f"ablation missing fields {miss}")
    return ("GREEN", f"S4 ablation: damping_share {d.get('damping_share')} -> {d.get('attribution')}")
add("s4_ablation", *ablation())

# ---------------------------------------------------------------- vault freeze ordering + touched once
def vault_order():
    fz = wp("VAULT_FREEZE.sha256"); dl = wp("out/vault_download.log")
    if not os.path.exists(fz): return ("RED", "VAULT_FREEZE.sha256 missing (finalists not frozen)")
    if not os.path.exists(dl): return ("RED", "out/vault_download.log missing (vault not graded)")
    if os.path.getmtime(fz) > os.path.getmtime(dl):
        return ("RED", "INTEGRITY: vault read BEFORE finalists frozen (freeze mtime > download mtime)")
    caches = glob.glob(wp("data/vault_*.npz"))
    if len(caches) > 1: return ("YELLOW", f"more than one vault cache ({len(caches)}); confirm touched-once")
    return ("GREEN", "finalists frozen before vault read; vault graded once")
add("vault_freeze_ordering", *vault_order())

# ---------------------------------------------------------------- NUTS finalists (+A0/A0d) convergence
def nuts():
    fs = glob.glob(wp("out/nuts_*.json"))
    if not fs: return ("RED", "no out/nuts_*.json (finalist posteriors not run)")
    worst = []
    for f in fs:
        d = json.load(open(f))
        rhat, ess, div = d.get("rhat_max"), d.get("ess_min"), d.get("div_frac")
        ok = (rhat is not None and rhat <= 1.05 and ess is not None and ess >= 200
              and div is not None and div < 0.02)
        worst.append((os.path.basename(f), rhat, ess, div, ok))
    bad = [w for w in worst if not w[4]]
    if bad: return ("YELLOW", f"non-converged finalist(s) {bad} -> intervals not-trustworthy")
    return ("GREEN", "all finalists converged: " + "; ".join(
        f"{w[0]} rhat{w[1]} ess{w[2]} div{w[3]}" for w in worst))
add("nuts_finalists", *nuts())

# ---------------------------------------------------------------- leave-modes-out honesty present
def lmo():
    fs = glob.glob(wp("out/honesty_*.json"))
    if not fs: return ("RED", "no out/honesty_*.json (leave-modes-out not run)")
    dq = []
    for f in fs:
        wr = json.load(open(f)).get("lmo_widen_ratio")
        if wr is not None and wr <= 1.0: dq.append((os.path.basename(f), wr))
    if dq: return ("YELLOW", f"leave-modes-out DISQUALIFIES (widen<=1.0, overconfident): {dq}")
    return ("GREEN", f"leave-modes-out present, all widen>1.0 across {len(fs)} arm(s)")
add("leave_modes_out", *lmo())

# ---------------------------------------------------------------- figures + legibility
def figures():
    figs = glob.glob(wp("figures/*.png"))
    if not figs: return ("RED", "no figures/*.png")
    qa = load_json("out/fig_qa.json")
    if qa is None: return ("YELLOW", f"{len(figs)} figures present but no fig_qa.json legibility report")
    bad = [k for k, v in qa.items() if not v.get("legible", True)]
    if bad: return ("RED", f"illegible figures {bad}")
    return ("GREEN", f"{len(figs)} figures present + legibility QA passed")
add("figures_legibility", *figures())

# ---------------------------------------------------------------- runtime accounting
def runtime():
    d = load_json("runtime.json")
    if d is None: return ("RED", "runtime.json missing")
    a, w = d.get("active_runtime_s"), d.get("elapsed_wallclock_s")
    if a is None or w is None: return ("RED", "runtime.json lacks active/elapsed")
    if a > w + 1e-6: return ("RED", f"active {a} > elapsed {w}")
    return ("GREEN", f"active {a}s <= elapsed {w}s")
add("runtime_accounting", *runtime())

# ---------------------------------------------------------------- S1/S2/S3/S4 verdicts present + honest
def verdicts():
    d = load_json("out/verdicts.json")
    if d is None: return ("RED", "out/verdicts.json missing (S1..S4 not graded)")
    need = ["S1", "S2", "S3", "S4", "overall_claim"]
    miss = [k for k in need if k not in d]
    if miss: return ("RED", f"verdicts missing {miss}")
    claim = d.get("overall_claim", "")
    if all(d.get(s, {}).get("pass") for s in ("S1", "S2", "S3", "S4")):
        return ("GREEN", f"S1+S2+S3+S4 all pass; claim={claim}")
    if "falsif" in claim.lower():
        return ("YELLOW", f"pre-registered claim FALSIFIED (honest outcome): {claim}")
    return ("RED", f"S-gates not all pass but claim not labeled falsified: {claim}")
add("s1_s2_s3_s4_verdicts", *verdicts())

# ---------------------------------------------------------------- overall
order = {"GREEN": 0, "YELLOW": 1, "RED": 2}
overall = "GREEN"
for _, s, _ in results:
    if order[s] > order[overall]: overall = s
report = {"overall": overall,
          "counts": {k: sum(1 for _, s, _ in results if s == k) for k in ("GREEN", "YELLOW", "RED")},
          "gates": [{"gate": g, "status": s, "reason": r} for g, s, r in results]}
with open(wp("checker_report.json"), "w") as f:
    json.dump(report, f, indent=2)
for g, s, r in results:
    print(f"[{s:6}] {g}: {r}")
print(f"\nOVERALL: {overall}  {report['counts']}")
sys.exit(2 if overall == "RED" else 0)
