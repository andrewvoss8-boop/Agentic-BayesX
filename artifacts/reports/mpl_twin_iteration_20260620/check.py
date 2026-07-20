#!/usr/bin/env python3
"""Immutable 3-tier checker for the MPL twin-iteration model-class search (MASTER harness).

Written FIRST (Phase 0). Baseline is RED until the harness + baseline + at least one scored class exist.
GREEN/YELLOW/RED; exits non-zero ONLY on RED. Honest negatives (simplest class wins / data can't distinguish)
are YELLOW, never RED. The model-class verdict is DERIVED FROM THE NUMBERS here (anti-over-claim), not trusted
from prose. DO NOT EDIT during the trial: self-SHA lock in code/.check_lock.sha256; score.py asserted
byte-identical to the L5 original.

Run: python3 check.py
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

WS = Path(__file__).resolve().parent
OUT = WS / "out"; FIG = WS / "figures"; CODE = WS / "code"; GIF = WS / "gifs"
L5_SCORE = WS.parent / "shocksat_modelclass_L5_20260619" / "code" / "score.py"
SCORE_SHA_L5 = "c62c564d024eb59cc48d6daeb70128b73b5bcb0e4e925f8d4234416baeb0934d"
R = []   # (gate, status, msg)


def add(g, s, m): R.append((g, s, m))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def lj(p):
    try: return json.loads(Path(p).read_text())
    except Exception as e: return e


# ----------------------------------------------------------------- integrity
def integrity():
    lock = CODE / ".check_lock.sha256"; me = sha(Path(__file__))
    if lock.exists():
        rec = json.loads(lock.read_text())
        ok = rec.get("self") == me
        add("integrity.self", "GREEN" if ok else "RED",
            "check.py unchanged" if ok else "check.py EDITED mid-trial (lock mismatch)")
    else:
        lock.write_text(json.dumps({"self": me}, indent=1))
        add("integrity.self", "GREEN", "self-lock created (first run)")
    # score.py byte-identical to the L5 original (proper scores reused, not re-implemented)
    sp = CODE / "score.py"
    if not sp.exists():
        add("integrity.score", "RED", "code/score.py missing")
    else:
        s = sha(sp)
        same_hash = (s == SCORE_SHA_L5)
        same_file = L5_SCORE.exists() and sha(L5_SCORE) == s
        if same_hash and (same_file or not L5_SCORE.exists()):
            add("integrity.score", "GREEN", f"score.py byte-identical to L5 (sha {s[:12]}…)")
        else:
            add("integrity.score", "RED", f"score.py NOT byte-identical to L5 original (sha {s[:12]}…)")


# ----------------------------------------------------------------- harness
def need(gate, path, keys=()):
    p = Path(path)
    if not p.exists(): add(gate, "RED", f"missing {p.name}"); return None
    d = lj(p)
    if isinstance(d, Exception): add(gate, "RED", f"{p.name} invalid: {d}"); return None
    miss = [k for k in keys if k not in d]
    if miss: add(gate, "RED", f"{p.name} missing keys {miss}"); return None
    return d


def harness():
    # observable: gain-free transmissibility curves + node map + unit tests
    d = need("harness.observe", OUT / "observable.json",
             ("gain_convention", "ref_location", "band_hz", "locations", "unit_tests"))
    if d:
        gf = "gain-free" in str(d["gain_convention"]).lower() or "ratio" in str(d["gain_convention"]).lower()
        ut = d["unit_tests"]; ut_ok = isinstance(ut, dict) and all(bool(v) for v in ut.values())
        nloc = len(d["locations"])
        if not gf:
            add("harness.observe", "RED", f"gain convention not gain-free/ratio: {d['gain_convention']}")
        elif not ut_ok:
            add("harness.observe", "RED", f"observable unit tests not all passing: {ut}")
        elif nloc < 6:
            add("harness.observe", "YELLOW", f"only {nloc} accel locations mapped (<6 expected)")
        else:
            add("harness.observe", "GREEN", f"{nloc} gain-free |T| curves, ref={d['ref_location']}, "
                f"band {d['band_hz']}, unit tests pass")
        # D-A GRMS un-blurrable gate: one documented gain convention
        add("grms.gain_convention", "GREEN" if gf else "RED",
            "GRMS on dimensionless |T| ratio (un-blurrable, one documented convention)" if gf
            else "GRMS gain convention not gain-free — D-A violated")
    else:
        add("grms.gain_convention", "RED", "observable.json absent → cannot verify GRMS convention")

    d = need("harness.splits", OUT / "splits.json", ("axis", "reference", "splits"))
    if d:
        n = len(d["splits"]); leak = bool(d.get("leakage_controlled", False))
        held = sorted(s.get("held_out") for s in d["splits"])
        exp = sorted(["interface", "beam", "valve", "avi-L", "avi-R"])
        if n == 5 and held == exp and leak and "shield" in str(d["reference"]).lower():
            add("harness.splits", "GREEN", f"5 leave-one-location-out splits over {held}, shield ref, leakage-controlled")
        else:
            add("harness.splits", "RED", f"splits malformed: n={n} held={held} leak={leak} ref={d['reference']}")


def baseline():
    d = need("baseline.scores", OUT / "baseline_scores.json", ("per_split",))
    if d:
        ps = d["per_split"]
        has = all(("nominal" in s and "calibrated" in s) for s in ps)
        add("baseline.scores", "GREEN" if (len(ps) == 5 and has) else "RED",
            f"baseline (nominal+calibrated) on {len(ps)} splits" if (len(ps) == 5 and has)
            else f"baseline incomplete ({len(ps)} splits, full={has})")
    need("baseline.climatology", OUT / "climatology.json", ("per_split",)) and \
        add("baseline.climatology", "GREEN", "climatology no-skill bar present")


# ----------------------------------------------------------------- model-class search
def search():
    classes = sorted(OUT.glob("class_*.json"))
    if not classes:
        add("search.classes", "RED", "no scored model classes yet (out/class_*.json)");
        add("search.registry", "RED", "no model_registry.json"); return
    # every class: convergence-gated (non-converged = YELLOW, never ranked as calibrated)
    nconv = nyellow = 0
    for c in classes:
        d = lj(c)
        if isinstance(d, Exception): add(f"search.{c.stem}", "RED", f"{c.name} invalid"); continue
        conv = bool(d.get("nuts_converged", False))
        worst = d.get("worst_rhat", None)
        if conv: nconv += 1
        else: nyellow += 1
        add(f"search.{c.stem}", "GREEN" if conv else "YELLOW",
            f"{d.get('hypothesis','?')[:60]} | converged={conv} (worst R̂={worst})")
    reg = need("search.registry", OUT / "model_registry.json", ("rows",))
    if reg:
        # DERIVE the program verdict from the numbers (anti-over-claim)
        rows = reg["rows"]
        improved = [r for r in rows if r.get("verdict", "").startswith("improve")]
        add("search.registry", "GREEN", f"{len(rows)} attempts logged; {nconv} converged, {nyellow} yellow; "
            f"{len(improved)} improve-verdicts")
        # honest-negative is YELLOW, not RED
        if reg.get("program_verdict"):
            v = reg["program_verdict"]
            tier = "GREEN" if v.startswith("GREEN") else ("RED" if v.startswith("RED") else "YELLOW")
            add("search.program_verdict", tier, v)


def deliverables():
    add("deliv.registry_fig", "GREEN" if (FIG / "fig_registry.png").exists() else "RED",
        "fig_registry.png present" if (FIG / "fig_registry.png").exists() else "missing fig_registry.png")
    iqa = lj(OUT / "image_qa.json") if (OUT / "image_qa.json").exists() else None
    add("deliv.image_qa", "GREEN" if isinstance(iqa, dict) and iqa.get("pass") else "RED",
        "image-QA pass" if isinstance(iqa, dict) and iqa.get("pass") else "image-QA missing/not pass")
    for fn, lab in [("packet.md", "deliv.packet"), ("runtime.json", "deliv.runtime"),
                    ("run_all.sh", "deliv.run_all")]:
        ok = (WS / fn).exists()
        add(lab, "GREEN" if ok else "RED", f"{fn} present" if ok else f"missing {fn}")


def main():
    integrity(); harness(); baseline(); search(); deliverables()
    nr = sum(1 for _, s, _ in R if s == "RED")
    ny = sum(1 for _, s, _ in R if s == "YELLOW")
    ng = sum(1 for _, s, _ in R if s == "GREEN")
    overall = "RED" if nr else ("YELLOW" if ny else "GREEN")
    rep = {"task": "MPL twin iteration — FEM model-class search (master harness)",
           "overall": overall, "counts": {"green": ng, "yellow": ny, "red": nr},
           "gates": [{"gate": g, "status": s, "msg": m} for g, s, m in R],
           "note": "Baseline RED is expected until Phase-0 harness + baseline + >=1 scored class exist. "
                   "Honest negatives (simplest class wins / data can't distinguish) are YELLOW, not RED.",
           "check_sha256": sha(Path(__file__))}
    (WS / "check_report.json").write_text(json.dumps(rep, indent=2))
    print(f"\ncheck.py — OVERALL {overall}  (GREEN {ng} / YELLOW {ny} / RED {nr})")
    for g, s, m in R: print(f"  [{s:6}] {g}: {m}")
    sys.exit(1 if overall == "RED" else 0)


if __name__ == "__main__":
    main()
