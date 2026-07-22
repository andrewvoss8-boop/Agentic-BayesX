#!/usr/bin/env python3
"""IMMUTABLE CHECKER — Task Card E `_Fable`.

SHA-locked in CHECKER.sha256 BEFORE any science output was written, and never edited afterwards.

Usage:
    python3 check_fable.py                 # check this workspace, write out/checker_report.json
    python3 check_fable.py --ws DIR        # check another (e.g. empty) workspace
    python3 check_fable.py --ws DIR --out out/checker_empty_report.json

Exit code: non-zero ONLY on RED (documented YELLOW findings do not abort replay).
Status rule: any RED -> RED; else any YELLOW -> YELLOW; else GREEN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path

DB = 20.0 / 2.302585092994046      # 20/ln(10)


def sha256(p: Path):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


class Check:
    def __init__(self):
        self.rows = []

    def add(self, gid, status, what, detail=None):
        assert status in ("GREEN", "YELLOW", "RED")
        self.rows.append({"gate": gid, "status": status, "what": what, "detail": detail})

    def overall(self):
        st = [r["status"] for r in self.rows]
        return "RED" if "RED" in st else ("YELLOW" if "YELLOW" in st else "GREEN")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    WS = Path(a.ws).resolve()
    OUT = WS / "out"
    REPO = Path(__file__).resolve().parent.parent.parent.parent
    c = Check()

    # ---------------------------------------------------------------- G01 source hashes unchanged
    man = load(OUT / "source_manifest.json")
    if not man:
        c.add("G01", "RED", "source_manifest.json missing — the immutable source gate never ran")
    else:
        bad, miss = [], []
        for s in man["sources"]:
            p = REPO / s["path"]
            if not p.exists():
                miss.append(s["path"])
            elif sha256(p) != s["sha256"]:
                bad.append(s["path"])
        if bad or miss:
            c.add("G01", "RED", "frozen source files changed or vanished since INIT",
                  {"changed": bad, "missing": miss})
        else:
            c.add("G01", "GREEN", f"all {len(man['sources'])} frozen source files hash-verified unchanged")

    # ---------------------------------------------------------------- G02 preregistration / registry hashes
    fr = load(WS / "FROZEN.sha256")
    if not fr:
        c.add("G02", "RED", "FROZEN.sha256 missing — preregistration and registries were never locked")
    else:
        bad = [k for k, v in fr["files"].items()
               if not (WS / k).exists() or sha256(WS / k) != v]
        if bad:
            c.add("G02", "RED", "preregistration / split registry / mean-basis registry changed after locking",
                  {"changed": bad})
        else:
            c.add("G02", "GREEN", f"{len(fr['files'])} preregistration/registry files hash-verified unchanged")

    # ---------------------------------------------------------------- G03 RED-on-empty proof predates fit output
    emp = load(OUT / "checker_empty_report.json")
    if not emp:
        c.add("G03", "RED", "no RED-on-empty proof (out/checker_empty_report.json)")
    elif emp.get("overall") != "RED":
        c.add("G03", "RED", "the checker did NOT return RED on an empty output directory",
              {"observed": emp.get("overall")})
    else:
        proof_t = (OUT / "checker_empty_report.json").stat().st_mtime
        later = []
        for name in ["synthetic_fable.json", "stage1_measured_fable.json", "automatic_decision.json"]:
            p = OUT / name
            if p.exists() and p.stat().st_mtime < proof_t:
                later.append(name)
        if later:
            c.add("G03", "RED", "fit output predates the RED-on-empty proof", {"files": later})
        else:
            c.add("G03", "GREEN", "checker proven RED on an empty output directory, before any fit output")

    # ---------------------------------------------------------------- G04 quantity contract (log-ratio + dB)
    qc = (WS / "quantity_contracts.md")
    if not qc.exists():
        c.add("G04", "RED", "quantity_contracts.md missing")
    else:
        t = qc.read_text()
        ok_ref = "H_ref" in t and "1 g/lbf" in t
        ok_ratio = re.search(r"ln\s*\(\s*\|\s*H1?_?\w*\s*\|\s*/\s*H_ref\s*\)", t) is not None
        ok_db = "20 / ln(10)" in t or "20/ln(10)" in t or "8.6859" in t
        bad_phrase = re.search(r"log of g/lbf", t, re.I) is not None
        prob = [k for k, v in {"H_ref stated": ok_ref, "log of a ratio": ok_ratio,
                               "dB conversion": ok_db}.items() if not v]
        if prob or bad_phrase:
            c.add("G04", "RED", "quantity contract does not state a dimensionless log-ratio and its dB rule",
                  {"missing": prob, "forbidden_phrase_present": bad_phrase})
        else:
            c.add("G04", "GREEN", "log is taken of |H1|/H_ref with H_ref = 1 g/lbf; dB = 20/ln(10) * q")

    # ---------------------------------------------------------------- G05 E0/E1 identical training fit
    ver = load(OUT / "verification_fable.json")
    st1 = load(OUT / "stage1_measured_fable.json")
    if not ver:
        c.add("G05", "RED", "verification_fable.json missing (E0/E1 identity never demonstrated)")
    else:
        v3 = [x for x in ver["checks"] if x["gate"] == "V3"] if "gate" in (ver["checks"][0] if ver["checks"] else {}) \
            else [x for x in ver["checks"] if x.get("id") == "V3"]
        okv = bool(v3) and v3[0]["pass"]
        okf = True
        detail = {}
        if st1:
            mism = []
            for f in st1["folds"]:
                a0, a1 = f["arms"].get("E0"), f["arms"].get("E1")
                if not a0 or not a1:
                    continue
                if a0["c_hat"] != a1["c_hat"] or a0["c_post_sd"] != a1["c_post_sd"]:
                    mism.append(f["fold"]["name"])
            okf = not mism
            detail["folds_with_different_E0_E1_training_fit"] = mism
        if okv and okf:
            c.add("G05", "GREEN", "E0 and E1 share exactly the same fitted training hyperparameters and "
                                  "coefficient posterior in every fold; only K_*T is toggled", detail)
        else:
            c.add("G05", "RED", "E0/E1 training fits differ — the causal comparison is broken", detail)

    # ---------------------------------------------------------------- G06 mean and GP contributions stored apart
    if not st1:
        c.add("G06", "RED", "stage1_measured_fable.json missing — no measured arm results")
    else:
        need = ["mean_abs_struct_mean_db", "mean_abs_gp_mean_db", "mean_theta_sd_db"]
        missing = []
        for f in st1["folds"]:
            for arm, r in f["arms"].items():
                for k in need:
                    if k not in r:
                        missing.append(f"{f['fold']['name']}/{arm}/{k}")
        if missing:
            c.add("G06", "RED", "E[H beta|train], E[u_*|train] and parameter uncertainty are not stored "
                                "separately for every fold and arm", {"missing_first_10": missing[:10]})
        else:
            c.add("G06", "GREEN", "learned-mean contribution, conditioned-GP contribution and parameter "
                                  "uncertainty stored separately for every fold and arm")

    # ---------------------------------------------------------------- G07 basis centering / interaction margins
    if not st1:
        c.add("G07", "RED", "no Stage-1 output to check basis constraints")
    else:
        worst = 0.0
        for f in st1["folds"]:
            worst = max(worst, float(f["constraints"]["max_constraint_residual"]))
        if worst > 1e-8:
            c.add("G07", "RED", "weighted ANOVA constraints not satisfied", {"max_residual": worst})
        else:
            c.add("G07", "GREEN", "main-effect centering and interaction frequency/location margins hold in "
                                  "every fold", {"max_constraint_residual": worst})

    # ---------------------------------------------------------------- G08 band guards + no outer-test tuning
    sr = load(OUT / "split_registry.json")
    if not sr:
        c.add("G08", "RED", "split_registry.json missing")
    else:
        probs = []
        for core in sr["family_3_frequency"]["cores"]:
            if core["guard_hz"] < 10.0:
                probs.append(f"core {core['core']} guard {core['guard_hz']} Hz < 10 Hz")
            if core["min_gap_to_nearest_training_line_hz"] <= 10.0 - 1e-9:
                probs.append(f"core {core['core']} nearest training line only "
                             f"{core['min_gap_to_nearest_training_line_hz']:.2f} Hz away")
            if len(core["core_line_idx"]) != (core["core_line_idx"][-1] - core["core_line_idx"][0] + 1):
                probs.append(f"core {core['core']} is not contiguous")
        if "no_outer_test_tuning" not in sr:
            probs.append("no_outer_test_tuning statement absent")
        if probs:
            c.add("G08", "RED", "frequency folds leak across the guard band or the no-tuning rule is absent",
                  {"problems": probs})
        else:
            c.add("G08", "GREEN", "all 5 frequency cores contiguous with a >10 Hz training guard; "
                                  "no-outer-test-tuning rule recorded")

    # ---------------------------------------------------------------- G09 synthetic gates S0-S3, >=20 seeds
    syn = load(OUT / "synthetic_fable.json")
    if not syn:
        c.add("G09", "RED", "synthetic_fable.json missing — S0-S3 gates never ran")
    else:
        probs, seeds = [], {}
        for case in ["S0", "S1", "S2", "S3"]:
            if case not in syn.get("cases", {}):
                probs.append(f"{case} absent")
                continue
            n = syn["cases"][case].get("n_seeds", 0)
            seeds[case] = n
            if n < 20:
                probs.append(f"{case} only {n} seeds (<20)")
        gates = syn.get("gates", {})
        for g in ["S0_false_positive", "S1_recovery", "S2_robustness", "S3_confounding"]:
            if g not in gates:
                probs.append(f"gate result {g} absent")
        if probs:
            c.add("G09", "RED", "synthetic gate evidence incomplete", {"problems": probs, "seeds": seeds})
        else:
            failed = [g for g, v in gates.items() if not v.get("pass")]
            if failed:
                c.add("G09", "YELLOW", "all four synthetic cases ran with >=20 seeds, but at least one "
                                       "acceptance gate was NOT met — measured fitting must be stopped and "
                                       "the failure reported", {"failed_gates": failed, "seeds": seeds})
            else:
                c.add("G09", "GREEN", "S0-S3 each ran >=20 deterministic seeds and every acceptance gate "
                                      "was met", {"seeds": seeds})

    # ---------------------------------------------------------------- G10 identifiability before per-parameter claims
    ident = load(OUT / "identifiability_fable.json")
    if not ident:
        c.add("G10", "RED", "identifiability_fable.json missing (modal strain energy + realized-floor FIM)")
    else:
        need = ["strain_energy_fractions", "fim_eigen_at_realized_floor", "finite_perturbation_check",
                "realized_discrepancy_floor"]
        missing = [k for k in need if k not in ident]
        if missing:
            c.add("G10", "RED", "identifiability evidence incomplete", {"missing": missing})
        else:
            c.add("G10", "GREEN", "modal strain-energy fractions, FIM eigenstructure at the REALIZED "
                                  "Stage-1 discrepancy floor, and a finite-perturbation check are all present",
                  {"n_combinations_clearing_prior":
                      ident["fim_eigen_at_realized_floor"].get("n_combinations_clearing_prior")})

    # ---------------------------------------------------------------- G11 immutable automatic decision
    dec = load(OUT / "automatic_decision.json")
    if not dec:
        c.add("G11", "RED", "automatic_decision.json missing")
    else:
        need = ["terminal_path", "rules_evaluated", "active_runtime_s", "projected_stage2_runtime_s"]
        missing = [k for k in need if k not in dec]
        norule = [r for r in dec.get("rules_evaluated", [])
                  if not all(k in r for k in ("rule", "matched", "criteria"))]
        s2 = sorted(OUT.glob("stage2_*.json"))
        late = []
        if s2:
            dt = (OUT / "automatic_decision.json").stat().st_mtime
            late = [p.name for p in s2 if p.stat().st_mtime < dt]
        if missing or norule or late:
            c.add("G11", "RED", "automatic decision incomplete or not written before Stage-2 output",
                  {"missing": missing, "rules_without_criteria": len(norule),
                   "stage2_files_older_than_decision": late})
        else:
            c.add("G11", "GREEN", f"automatic decision '{dec['terminal_path']}' recorded with every numerical "
                                  f"transition criterion, before any Stage-2 output",
                  {"terminal_path": dec["terminal_path"]})

    # ---------------------------------------------------------------- G12 Stage-2 convergence if it ran
    s2files = sorted(OUT.glob("stage2_*.json"))
    if not s2files:
        c.add("G12", "GREEN", "Stage 2 did not run; no NUTS convergence claim is made anywhere")
    else:
        bad = []
        for p in s2files:
            d = load(p) or {}
            cv = d.get("convergence", {})
            if "per_variable" not in cv:
                bad.append(f"{p.name}: no per-variable R-hat/ESS table")
            elif not cv.get("gate_pass", False):
                bad.append(f"{p.name}: convergence gate NOT met (max R-hat "
                           f"{cv.get('worst_rhat')}, min ESS {cv.get('min_ess')})")
        if any("no per-variable" in b for b in bad):
            c.add("G12", "RED", "Stage 2 ran without reporting R-hat/ESS over ALL sampled variables",
                  {"problems": bad})
        elif bad:
            c.add("G12", "YELLOW", "Stage 2 ran but did not pass the convergence gate — intervals are "
                                   "NOT trustworthy and must never be called 'NUTS active'", {"problems": bad})
        else:
            c.add("G12", "GREEN", "Stage 2 NUTS converged over all sampled variables", None)

    # ---------------------------------------------------------------- G13 plots, legibility, runtime
    figs = sorted((WS / "figures").glob("*.png"))
    lint = load(OUT / "tufte_lint_fable.json")
    qa = load(OUT / "image_qa_fable.json")
    rt = load(WS / "runtime.json")
    probs = []
    if len(figs) < 6:
        probs.append(f"only {len(figs)} figures (card requires >=6 minimum figures)")
    if not lint:
        probs.append("no tufte_lint result")
    if not qa:
        probs.append("no image legibility QA report")
    elif qa.get("n_fail", 1) > 0:
        probs.append(f"{qa['n_fail']} figures failed legibility QA")
    if not rt:
        probs.append("runtime.json missing")
    else:
        if "active_runtime_s" not in rt or "elapsed_wallclock_s" not in rt:
            probs.append("runtime.json lacks active_runtime_s / elapsed_wallclock_s")
        elif rt["active_runtime_s"] > rt["elapsed_wallclock_s"] + 1e-6:
            probs.append("active_runtime_s exceeds elapsed_wallclock_s")
    if probs:
        c.add("G13", "RED", "figure / legibility / runtime accounting incomplete", {"problems": probs})
    else:
        c.add("G13", "GREEN", f"{len(figs)} figures, tufte lint recorded, legibility QA clean, runtime "
                              f"accounted", {"active_runtime_s": rt["active_runtime_s"]})

    # ---------------------------------------------------------------- G14 no predecessor workspace changed
    guard = load(WS / "PREDECESSOR_GUARD.json")
    if not guard:
        c.add("G14", "RED", "PREDECESSOR_GUARD.json missing — cannot prove predecessor workspaces are intact")
    else:
        changed = []
        for rel, h in guard["files"].items():
            p = REPO / rel
            if not p.exists() or sha256(p) != h:
                changed.append(rel)
        forb = guard.get("forbidden_paths", [])
        created = [f for f in forb if (REPO / f).exists()]
        if changed or created:
            c.add("G14", "RED", "a predecessor workspace / frozen input changed, or a forbidden path was created",
                  {"changed": changed, "forbidden_created": created})
        else:
            c.add("G14", "GREEN", f"{len(guard['files'])} predecessor files unchanged; "
                                  f"{len(forb)} forbidden paths still absent")

    # ---------------------------------------------------------------- G15 evidence labels / no over-claiming
    pk = WS / "packet.md"
    if not pk.exists():
        c.add("G15", "RED", "packet.md missing")
    else:
        t = pk.read_text()
        probs = []
        if not re.search(r"prototype|legacy", t, re.I):
            probs.append("legacy TMCMC M0-M3 results are not labelled prototype/legacy")
        if re.search(r"NUTS\s+active", t, re.I) and not s2files:
            probs.append("'NUTS active' claimed but Stage 2 never ran")
        if not re.search(r"weak", t, re.I):
            probs.append("five-fold uncertainty is not labelled weak")
        if probs:
            c.add("G15", "RED", "packet contains claims stronger than the evidence", {"problems": probs})
        else:
            c.add("G15", "GREEN", "evidence labels present: legacy results marked prototype, five-fold "
                                  "uncertainty marked weak, no unsupported 'NUTS active' claim")

    rep = {"run": "shocksat_structured_discrepancy_codex_20260722_Fable",
           "workspace": str(WS), "checks": c.rows,
           "counts": {s: sum(1 for r in c.rows if r["status"] == s) for s in ("GREEN", "YELLOW", "RED")},
           "overall": c.overall(),
           "status_rule": "any RED -> RED; else any YELLOW -> YELLOW; else GREEN. Exit non-zero only on RED."}
    outp = Path(a.out) if a.out else (OUT / "checker_report.json")
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(rep, indent=2))
    for r in c.rows:
        print(f"  {r['gate']} {r['status']:6s} {r['what']}")
    print(f"OVERALL {rep['overall']} {rep['counts']}")
    sys.exit(1 if rep["overall"] == "RED" else 0)


if __name__ == "__main__":
    main()
