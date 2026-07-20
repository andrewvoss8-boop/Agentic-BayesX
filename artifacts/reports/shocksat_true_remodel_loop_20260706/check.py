#!/usr/bin/env python3
"""Immutable checker — ShockSat TRUE Agentic Remodeling Loop (20260706).

Encodes the pre-registered gates from question_framing.md. Runs against THIS
workspace and writes checker_report.json. Exit code is non-zero ONLY on RED, so
documented YELLOW findings do not abort the one-command replay (AGENTS Result
Status Standard). Every gate returns one of GREEN / YELLOW / RED with a reason.

Design note (immutability): this checker is written to grade BOTH the pre-science
state (most science artifacts absent -> those gates RED "missing") and the
completed state, so it never needs editing during the trial. The pipeline emits
exactly the artifact schema this file reads. It is SHA-locked (CHECKER.sha256)
only after the pipeline skeleton exists and the science phase is authorized.
"""
import json, os, re, glob, hashlib, subprocess, sys

WS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
def wp(*p): return os.path.join(WS, *p)

AGENT_BUDGET = 60
RANDOM_BUDGET = 60
BAND = (45.0, 260.0)
results = []  # (gate, status, reason)

def add(gate, status, reason): results.append((gate, status, reason))

def exists(rel): return os.path.exists(wp(rel))

def load_json(rel):
    try:
        with open(wp(rel)) as f: return json.load(f)
    except Exception:
        return None

# ---------------------------------------------------------------- PRE gates
GATE_FILES = ["priority_deliverables.md", "question_framing.md",
              "quantity_contracts.md", "assumptions_ledger.md",
              "decisions_log.md", "REUSED_code.sha256"]
missing = [f for f in GATE_FILES if not exists(f)]
add("gate_files", "GREEN" if not missing else "RED",
    "all present" if not missing else f"missing {missing}")

# REUSED source integrity: recorded hashes must still match the live sources.
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
        got = hashlib.sha256(open(src, "rb").read()).hexdigest()
        if got != h: bad.append(f"{rel} CHANGED")
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

# ---------------------------------------------------------------- budget
def budget():
    p = wp("out/query_log.jsonl")
    if not os.path.exists(p): return ("RED", "out/query_log.jsonl missing")
    n = {"agent": 0, "random": 0}
    try:
        for line in open(p):
            line = line.strip()
            if not line: continue
            r = json.loads(line)
            t = r.get("track")
            if t in n: n[t] += 1
    except Exception as e:
        return ("RED", f"query_log parse error {e}")
    over = []
    if n["agent"] > AGENT_BUDGET: over.append(f"agent {n['agent']}>{AGENT_BUDGET}")
    if n["random"] > RANDOM_BUDGET: over.append(f"random {n['random']}>{RANDOM_BUDGET}")
    if over: return ("RED", "BUDGET EXCEEDED " + str(over))
    if n["agent"] == 0 and n["random"] == 0: return ("RED", "query_log empty (science not run)")
    return ("GREEN", f"within budget: agent {n['agent']}<= {AGENT_BUDGET}, random {n['random']}<= {RANDOM_BUDGET}")
add("query_budget", *budget())

# ---------------------------------------------------------------- no dev-residual-field reads in the loop
def no_dev_leak():
    lp = wp("code/loop.py")
    if not os.path.exists(lp): return ("RED", "code/loop.py missing (science not run)")
    src = open(lp).read()
    # the loop must not directly np.load the drive caches; only the score module may.
    bad = re.findall(r"np\.load\([^)]*m_[a-z0-9_]+\.npz", src)
    if bad: return ("RED", f"loop.py reads drive caches directly (dev-residual leak risk): {bad}")
    return ("GREEN", "loop.py contains no direct drive-cache reads (dev returns scalars only)")
add("no_dev_residual_leak", *no_dev_leak())

# ---------------------------------------------------------------- no per-mode amplitude LSQ in selection
def no_lsq():
    sp = wp("code/score.py")
    if not os.path.exists(sp): return ("RED", "code/score.py missing (science not run)")
    src = open(sp).read()
    hits = [m for m in ("lstsq", "pinv", "np.linalg.solve(") if m in src]
    if hits: return ("RED", f"selection score.py contains LSQ-like calls {hits} (per-mode amplitude fit forbidden)")
    if "NO-PER-MODE-LSQ" not in src:
        return ("YELLOW", "score.py lacks the NO-PER-MODE-LSQ marker; manual review required")
    return ("GREEN", "score.py: one global gain only, no per-mode/per-channel amplitude LSQ")
add("no_amplitude_lsq", *no_lsq())

# ---------------------------------------------------------------- vault freeze ordering + touched once
def vault_order():
    fz = wp("VAULT_FREEZE.sha256")
    dl = wp("out/vault_download.log")
    if not os.path.exists(fz): return ("RED", "VAULT_FREEZE.sha256 missing (finalists not frozen)")
    if not os.path.exists(dl): return ("RED", "out/vault_download.log missing (vault not graded)")
    if os.path.getmtime(fz) > os.path.getmtime(dl):
        return ("RED", "INTEGRITY: vault downloaded BEFORE finalists frozen (freeze mtime > download mtime)")
    caches = glob.glob(wp("data/vault_*.npz"))
    if len(caches) > 1:
        return ("YELLOW", f"more than one vault cache ({len(caches)}); confirm 'touched once' per source")
    return ("GREEN", "finalists frozen before vault download; vault graded once")
add("vault_freeze_ordering", *vault_order())

# ---------------------------------------------------------------- NUTS finalists convergence
def nuts():
    fs = glob.glob(wp("out/nuts_*.json"))
    if not fs: return ("RED", "no out/nuts_*.json (finalist posteriors not run)")
    worst = []
    for f in fs:
        d = json.load(open(f))
        rhat = d.get("rhat_max"); ess = d.get("ess_min"); div = d.get("div_frac")
        ok = (rhat is not None and rhat <= 1.05 and ess is not None and ess >= 200
              and div is not None and div < 0.02)
        worst.append((os.path.basename(f), rhat, ess, div, ok))
    bad = [w for w in worst if not w[4]]
    if bad: return ("YELLOW", f"non-converged finalist(s) {bad} -> intervals not-trustworthy")
    return ("GREEN", "all finalists converged: " + "; ".join(f"{w[0]} rhat{w[1]} ess{w[2]} div{w[3]}" for w in worst))
add("nuts_finalists", *nuts())

# ---------------------------------------------------------------- leave-modes-out honesty present
def lmo():
    fs = glob.glob(wp("out/honesty_*.json"))
    if not fs: return ("RED", "no out/honesty_*.json (leave-modes-out not run)")
    dq = []
    for f in fs:
        d = json.load(open(f))
        wr = d.get("lmo_widen_ratio")
        if wr is not None and wr <= 1.0:
            dq.append((os.path.basename(f), wr))
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
    a = d.get("active_runtime_s"); w = d.get("elapsed_wallclock_s")
    if a is None or w is None: return ("RED", "runtime.json lacks active/elapsed")
    if a > w + 1e-6: return ("RED", f"active {a} > elapsed {w}")
    return ("GREEN", f"active {a}s <= elapsed {w}s")
add("runtime_accounting", *runtime())

# ---------------------------------------------------------------- S1/S2/S3 verdicts present + honest
def verdicts():
    d = load_json("out/verdicts.json")
    if d is None: return ("RED", "out/verdicts.json missing (S1/S2/S3 not graded)")
    need = ["S1", "S2", "S3", "overall_claim"]
    miss = [k for k in need if k not in d]
    if miss: return ("RED", f"verdicts missing {miss}")
    # a WIN claim requires all three True; otherwise must be labeled falsified.
    claim = d.get("overall_claim", "")
    if all(d.get(s, {}).get("pass") for s in ("S1", "S2", "S3")):
        return ("GREEN", f"S1+S2+S3 all pass; claim={claim}")
    if "falsified" in claim.lower():
        return ("YELLOW", f"pre-registered claim FALSIFIED (honest outcome): {claim}")
    return ("RED", f"S-gates not all pass but claim not labeled falsified: {claim}")
add("s1_s2_s3_verdicts", *verdicts())

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
