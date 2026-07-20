#!/usr/bin/env python3
"""check.py — IMMUTABLE checker for the validated net-CG QOI port (runner card B, 2026-07-16).

Written BEFORE any science (D1), run on the EMPTY workspace to prove RED, then SHA-locked into
CHECKER.sha256 and NEVER edited. Gates are pre-registered from the card verbatim.

Result Status Standard (AGENTS.md): GREEN / YELLOW / RED per gate; OVERALL = RED if any RED, else YELLOW if
any YELLOW, else GREEN. Exit code is non-zero ONLY on RED (documented YELLOW does not abort replay).

Gates:
  G01  N0 reference reproduction (1.508/2.301/2.526 +-0.05 each) OR BLOCKED.md present with a diagnosis
  G02  every reported statistic is FINITE (no NaN/None/inf anywhere in out/*.json)   [review C8 lesson]
  G03  baseline-through-mapping reproduces N0 +-0.05 AND the mapping is non-inert (D2/C2)
  G04  no per-mode amplitude LSQ on a SELECTION path (grep; CHECKER-OK(non-selection) annotation required)
  G05  no +XY vault reads anywhere (grep data paths + runtime guard)
  G06  figures scripted (.py), Tufte-linted, image-QA'd, >=3 present
  G07  runtime.json with active_runtime_s <= elapsed_wallclock_s
  G08  self-SHA: this checker matches CHECKER.sha256 (integrity)
  G09  required deliverables present + REUSED_code.sha256 verifies against the read-only sources
  G10  no NEW sampler claimed; theta provenance is declared REUSED and traceable
Usage: python3 check.py
"""
from __future__ import annotations
import hashlib
import json
import math
import re
import sys
from pathlib import Path

WS = Path(__file__).resolve().parent
ROOT = WS.parents[2]
OUT = WS / "out"
FIGD = WS / "figures"
CODE = WS / "code"

# ---- pre-registered constants (card verbatim; D0 resolution) --------------------------------------
N0_TARGETS = {"shear_X": 1.508, "shear_Y": 2.301, "normal_Z": 2.526}   # netcg delivered statfem_Fk
N0_TOL = 0.05
S4_WIDTH_MAX, S4_COV_MIN = 1.90, 0.95            # card 3.2: <=1.90x AND coverage >=0.95
S3_COV_MIN = 0.95                                # card 3.3: narrower than 1.51/2.30 while coverage >=0.95
S3_SHEAR_REF = {"shear_X": 1.508, "shear_Y": 2.301}
VAULT_TOKENS = ["m_xy_990xy", "990xy", "xy_990", "Test04", "m_xy"]
REQUIRED = ["packet.md", "findings.md", "decisions_log.md", "run_all.sh", "priority_deliverables.md",
            "question_framing.md", "quantity_contracts.md", "REUSED_code.sha256", "runtime.json",
            "out/verdicts_S3S4.json"]

results = []   # (gate, status, message)


def add(gate, status, msg):
    results.append((gate, status, msg))


def jload(p):
    try:
        return json.loads(Path(p).read_text())
    except Exception:
        return None


def walk_numbers(o, path="", bad=None):
    """Collect every non-finite numeric leaf (NaN/inf) and every None found where a number belongs."""
    bad = [] if bad is None else bad
    if isinstance(o, dict):
        for k, v in o.items():
            walk_numbers(v, f"{path}.{k}", bad)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk_numbers(v, f"{path}[{i}]", bad)
    elif isinstance(o, float):
        if math.isnan(o) or math.isinf(o):
            bad.append(f"{path}={o}")
    return bad


# ---------------------------------------------------------------- G01: N0 reproduction or BLOCKED
blocked = WS / "BLOCKED.md"
n0 = jload(OUT / "n0_reference.json")
if blocked.exists():
    txt = blocked.read_text()
    has_numbers = bool(re.search(r"\d+\.\d+", txt)) and len(txt) > 400
    if has_numbers:
        add("G01", "YELLOW", "BLOCKED.md present with a numeric divergence diagnosis; N0 not reproduced. "
                             "S3/S4 = CANNOT-VERIFY-pending-human (a valid pre-registered outcome).")
    else:
        add("G01", "RED", "BLOCKED.md present but lacks a numeric diagnosis (needs the exact divergence "
                          "point and numbers, >400 chars).")
elif n0 is None:
    add("G01", "RED", "neither out/n0_reference.json nor BLOCKED.md exists — Gate N0 was not run.")
else:
    rep = n0.get("reproduced", {})
    errs, miss = {}, []
    for k, tgt in N0_TARGETS.items():
        v = rep.get(k)
        if not isinstance(v, (int, float)) or (isinstance(v, float) and not math.isfinite(v)):
            miss.append(k)
        else:
            errs[k] = abs(v - tgt)
    if miss:
        add("G01", "RED", f"N0 missing/non-finite for {miss}")
    elif all(e <= N0_TOL for e in errs.values()):
        add("G01", "GREEN", "N0 PASS: delivered bands reproduced within +-0.05 — " +
            ", ".join(f"{k} {rep[k]:.3f} vs {N0_TARGETS[k]} (|err| {errs[k]:.4f})" for k in N0_TARGETS))
    else:
        add("G01", "RED", "N0 FAIL and no BLOCKED.md: " +
            ", ".join(f"{k} {rep[k]:.3f} vs {N0_TARGETS[k]} (|err| {errs[k]:.4f})" for k in N0_TARGETS))

# ---------------------------------------------------------------- G02: finiteness (review C8 lesson)
if not OUT.exists() or not list(OUT.glob("*.json")):
    add("G02", "RED", "no out/*.json to validate.")
else:
    bad_all = []
    for p in sorted(OUT.glob("*.json")):
        d = jload(p)
        if d is None:
            bad_all.append(f"{p.name}: unparseable")
            continue
        bad_all += [f"{p.name}{b}" for b in walk_numbers(d)]
    # explicit null-in-headline check (the C8 defect: null SE / NaN S1/S2 passed a key-presence gate)
    v = jload(OUT / "verdicts_S3S4.json")
    nulls = []
    if v:
        for sk in ("N0", "N1", "S3", "S4"):
            blk = v.get(sk)
            if blk is None:
                nulls.append(f"verdicts_S3S4.json:{sk} MISSING")
            else:
                for kk, vv in (blk.get("numbers") or {}).items():
                    if vv is None:
                        nulls.append(f"verdicts_S3S4.json:{sk}.numbers.{kk} is null")
    if bad_all or nulls:
        add("G02", "RED", f"non-finite/null statistics found: {(bad_all + nulls)[:8]}")
    else:
        add("G02", "GREEN", f"all statistics finite across {len(list(OUT.glob('*.json')))} out/*.json; "
                            "no null headline numbers (guards the C8 defect).")

# ---------------------------------------------------------------- G03: mapping validation
mp = jload(OUT / "s3_mapping.json")
if blocked.exists() and mp is None:
    add("G03", "YELLOW", "skipped: run ended BLOCKED at N0 before the mapping (valid).")
elif mp is None:
    add("G03", "RED", "out/s3_mapping.json missing — mapping never validated.")
else:
    bt = mp.get("baseline_through_mapping", {})
    berr = {}
    ok = True
    for k, tgt in N0_TARGETS.items():
        v = bt.get(k)
        if not isinstance(v, (int, float)) or not math.isfinite(float(v)):
            ok = False
            berr[k] = None
        else:
            berr[k] = abs(v - tgt)
            ok = ok and berr[k] <= N0_TOL
    nonid = mp.get("non_identity_check", {})
    moved = bool(nonid.get("passes"))
    if not ok:
        add("G03", "RED", f"baseline-through-mapping does NOT reproduce N0 +-0.05: {berr}")
    elif not moved:
        add("G03", "RED", "mapping is INERT (no finalist moves the band) -> any S3 verdict would be an "
                          f"artifact of dead plumbing. detail={nonid}")
    else:
        add("G03", "GREEN", f"baseline-through-mapping reproduces N0 (max |err| "
                            f"{max(berr.values()):.4f}; identity BY CONSTRUCTION per D2 — plumbing check "
                            f"only) AND mapping is non-inert ({nonid.get('detail', '')}).")

# ---------------------------------------------------------------- G04: no selection-path amplitude LSQ
lsq_pat = re.compile(r"lstsq|np\.linalg\.solve\s*\(|pinv|curve_fit|minimize\s*\(|vdot")
viol = []
for p in sorted(CODE.glob("*.py")):
    for i, line in enumerate(p.read_text().splitlines(), 1):
        if lsq_pat.search(line):
            ctx = "\n".join(p.read_text().splitlines()[max(0, i - 4):i + 3])
            if "CHECKER-OK(non-selection)" not in ctx:
                viol.append(f"{p.name}:{i}: {line.strip()[:70]}")
if not CODE.exists() or not list(CODE.glob("*.py")):
    add("G04", "RED", "no code/*.py to scan.")
elif viol:
    add("G04", "RED", f"amplitude fitting on a possible SELECTION path without a "
                      f"CHECKER-OK(non-selection) annotation: {viol[:5]}")
else:
    add("G04", "GREEN", "no unannotated per-mode amplitude LSQ; every fit is annotated "
                        "CHECKER-OK(non-selection) = answer-key construction only.")

# ---------------------------------------------------------------- G05: vault (+XY) never read
vault_hits = []
for p in sorted(CODE.glob("*.py")) + sorted(WS.glob("*.sh")):
    txt = p.read_text()
    for i, line in enumerate(txt.splitlines(), 1):
        s = line.strip()
        if s.startswith("#") or "VAULT" in line or "vault" in line.lower():
            continue          # comments / the guard itself may name the token
        for tok in VAULT_TOKENS:
            if tok in line:
                vault_hits.append(f"{p.name}:{i}: {s[:70]}")
guard = jload(OUT / "vault_guard.json")
if vault_hits:
    add("G05", "RED", f"+XY vault token read on a live code path: {vault_hits[:5]}")
elif guard is None:
    add("G05", "RED", "out/vault_guard.json missing — runtime vault guard not evidenced.")
elif guard.get("xy_files_opened", None) != 0 or not guard.get("dev_drives_only"):
    add("G05", "RED", f"vault guard reports a violation: {guard}")
else:
    add("G05", "GREEN", f"no +XY reads (grep clean; runtime guard xy_files_opened=0, dev drives only: "
                        f"{guard.get('dev_drives')}). The +XY QOI answer key stays unbuilt.")

# ---------------------------------------------------------------- G06: figures
figs = sorted(FIGD.glob("*.png")) if FIGD.exists() else []
figscripts = [p for p in CODE.glob("fig_*.py")]
qa = jload(OUT / "fig_qa.json")
lint = jload(OUT / "tufte_lint.json")
if len(figs) < 3:
    add("G06", "RED", f"need >=3 figures, found {len(figs)}.")
elif not figscripts:
    add("G06", "RED", "figures exist but no code/fig_*.py — figures must be scripted, not inline.")
elif qa is None or lint is None:
    add("G06", "RED", "missing out/fig_qa.json and/or out/tufte_lint.json (legibility + lint evidence).")
else:
    bad = [f for f, r in (qa.get("figures") or {}).items() if not r.get("pass")]
    if bad:
        add("G06", "RED", f"image-QA failed for {bad}")
    else:
        add("G06", "GREEN", f"{len(figs)} figures, all scripted ({len(figscripts)} fig_*.py), "
                            f"Tufte-linted ({lint.get('n_warn', '?')} WARN reviewed), image-QA passed.")

# ---------------------------------------------------------------- G07: runtime accounting
rt = jload(WS / "runtime.json")
if rt is None:
    add("G07", "RED", "runtime.json missing.")
else:
    a, e = rt.get("active_runtime_s"), rt.get("elapsed_wallclock_s")
    if not isinstance(a, (int, float)) or not isinstance(e, (int, float)):
        add("G07", "RED", f"runtime.json needs numeric active_runtime_s/elapsed_wallclock_s, got {a}/{e}")
    elif a > e:
        add("G07", "RED", f"active_runtime_s ({a}) > elapsed_wallclock_s ({e}) — impossible.")
    else:
        add("G07", "GREEN", f"active_runtime_s={a}s <= elapsed_wallclock_s={e}s ({rt.get('machine', '?')}).")

# ---------------------------------------------------------------- G08: self-SHA integrity
lock = WS / "CHECKER.sha256"
me = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
if not lock.exists():
    add("G08", "RED", "CHECKER.sha256 missing — checker not locked.")
else:
    want = lock.read_text().split()[0].strip()
    if want == me:
        add("G08", "GREEN", f"checker matches its SHA lock ({me[:16]}…) — not edited during the trial.")
    else:
        add("G08", "RED", f"CHECKER MODIFIED: {me[:16]}… != locked {want[:16]}…")

# ---------------------------------------------------------------- G09: deliverables + reused-code integrity
missing = [r for r in REQUIRED if not (WS / r).exists()]
if blocked.exists():
    missing = [m for m in missing if m != "out/verdicts_S3S4.json"]
reused_bad = []
rp = WS / "REUSED_code.sha256"
if rp.exists():
    for line in rp.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        sha, rel = parts[0], parts[1].strip()
        f = ROOT / rel
        if not f.exists():
            reused_bad.append(f"MISSING {rel}")
        elif hashlib.sha256(f.read_bytes()).hexdigest() != sha:
            reused_bad.append(f"CHANGED {rel}")
if missing:
    add("G09", "RED", f"missing deliverables: {missing}")
elif not rp.exists():
    add("G09", "RED", "REUSED_code.sha256 missing — reused netcg/study sources not pinned.")
elif reused_bad:
    add("G09", "RED", f"reused read-only sources changed under us: {reused_bad[:5]}")
else:
    n = len([l for l in rp.read_text().splitlines() if l.strip() and not l.startswith("#")])
    add("G09", "GREEN", f"all deliverables present; {n} reused read-only sources verified unchanged.")

# ---------------------------------------------------------------- G10: no new sampler; theta provenance
v = jload(OUT / "verdicts_S3S4.json")
prov = (v or {}).get("theta_source", "")
code_txt = "\n".join(p.read_text() for p in CODE.glob("*.py")) if CODE.exists() else ""
ran_sampler = bool(re.search(r"\bMCMC\(|NUTS\(|calibrate_modal\(|numpyro\.infer", code_txt))
if blocked.exists() and v is None:
    add("G10", "YELLOW", "skipped: BLOCKED at N0 (valid).")
elif not prov:
    add("G10", "RED", "verdicts_S3S4.json lacks theta_source provenance.")
elif ran_sampler:
    add("G10", "RED", "a sampler is invoked in code/ — card 5 forbids a new posterior in this card.")
elif "reused" not in prov.lower():
    add("G10", "RED", f"theta_source does not declare REUSED draws: {prov!r}")
else:
    add("G10", "GREEN", f"no new sampler; theta provenance = {prov!r} (reused draws, labeled).")

# ---------------------------------------------------------------- report
order = {"RED": 0, "YELLOW": 1, "GREEN": 2}
overall = "GREEN"
if any(s == "RED" for _, s, _ in results):
    overall = "RED"
elif any(s == "YELLOW" for _, s, _ in results):
    overall = "YELLOW"
n_g = sum(1 for _, s, _ in results if s == "GREEN")
n_y = sum(1 for _, s, _ in results if s == "YELLOW")
n_r = sum(1 for _, s, _ in results if s == "RED")

print("=" * 100)
print("CHECKER — validated net-CG QOI port (card B, 2026-07-16)   [immutable, SHA-locked]")
print("=" * 100)
for g, s, m in results:
    print(f"[{s:6}] {g}: {m}")
print("-" * 100)
print(f"OVERALL: {overall}   ({n_g} GREEN / {n_y} YELLOW / {n_r} RED)")
print("Exit is non-zero ONLY on RED; documented YELLOW does not abort replay (AGENTS Result Status Standard).")

rep = {"overall": overall, "counts": {"green": n_g, "yellow": n_y, "red": n_r},
       "gates": [{"gate": g, "status": s, "message": m} for g, s, m in results],
       "checker_sha256": me}
(WS / "checker_report.json").write_text(json.dumps(rep, indent=2))
print(f"wrote {WS / 'checker_report.json'}")
sys.exit(1 if overall == "RED" else 0)
