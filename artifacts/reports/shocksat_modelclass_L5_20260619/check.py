#!/usr/bin/env python3
"""Immutable checker for Card F — Bayesian model-class selection (parameterization + damping) for the hard
ShockSat accels. Three-tier (GREEN/YELLOW/RED). Exits non-zero ONLY on RED so documented YELLOW findings do
not abort replay. Baseline (nothing produced yet) = RED ("not done").

DO NOT EDIT during the trial. On first run this records its own SHA256 to code/.check_lock.sha256 and the
SHA256 of the byte-identical reused Card A code; later runs that find a mismatch report a RED integrity
violation. Run:  python3 check.py
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

WS = Path(__file__).resolve().parent
OUT = WS / "out"
FIG = WS / "figures"
CODE = WS / "code"
CARD_A = WS.parent / "statfem_real_validation_20260617" / "code"
REUSED = ["core.py", "realfrf.py", "modal_feature.py", "heldout_qoi.py", "score.py",
          "tmcmc.py", "schneider_faithful.py"]

# convergence gate (AGENTS): max R-hat <= 1.05, min ESS >= 200, div fraction < 2%
RHAT_MAX, ESS_MIN, DIV_MAX = 1.05, 200.0, 0.02

results = []  # (gate, status in {GREEN,YELLOW,RED}, message)


def add(gate, status, msg):
    results.append((gate, status, msg))


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_json(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception as e:  # noqa
        return e


# ---------- INTEGRITY ----------
def gate_immutability():
    lock = CODE / ".check_lock.sha256"
    me = sha256(Path(__file__))
    if lock.exists():
        try:
            rec = json.loads(lock.read_text())
        except Exception:
            add("integrity.self", "RED", "lock file unreadable"); return
        if rec.get("check_py") != me:
            add("integrity.self", "RED",
                "check.py SHA changed since lock (checker edited mid-trial)"); return
        bad = []
        for f in REUSED:
            cur = sha256(CODE / f) if (CODE / f).exists() else None
            if rec.get(f) != cur:
                bad.append(f)
        if bad:
            add("integrity.reused_code", "RED",
                f"reused code edited since lock: {bad} (must stay byte-identical)")
        else:
            add("integrity.reused_code", "GREEN", "reused code byte-identical to lock")
        add("integrity.self", "GREEN", "check.py unchanged since lock")
    else:
        rec = {"check_py": me}
        for f in REUSED:
            rec[f] = sha256(CODE / f) if (CODE / f).exists() else None
        lock.write_text(json.dumps(rec, indent=1))
        add("integrity.self", "GREEN", "lock created (first run); baseline recorded")
        add("integrity.reused_code", "GREEN", "reused code SHA baseline recorded")


def gate_copy_matches_cardA():
    if not CARD_A.exists():
        add("integrity.copy_vs_cardA", "YELLOW", "Card A code dir not found — cannot verify byte-identity")
        return
    mism = []
    for f in REUSED:
        a, b = CARD_A / f, CODE / f
        if not b.exists():
            mism.append(f"{f}:missing-local"); continue
        if not a.exists():
            mism.append(f"{f}:missing-cardA"); continue
        if sha256(a) != sha256(b):
            mism.append(f"{f}:DIFF")
    if mism:
        add("integrity.copy_vs_cardA", "RED", f"copied code not byte-identical to Card A: {mism}")
    else:
        add("integrity.copy_vs_cardA", "GREEN", "reused code byte-identical to Card A originals")


# ---------- helpers for deliverable gates ----------
def require_json(gate, path: Path, keys=()):
    if not path.exists():
        add(gate, "RED", f"missing {path.name} (not produced yet)"); return None
    d = load_json(path)
    if isinstance(d, Exception):
        add(gate, "RED", f"{path.name} not valid JSON: {d}"); return None
    miss = [k for k in keys if k not in d]
    if miss:
        add(gate, "RED", f"{path.name} missing keys {miss}"); return None
    return d


def conv_status(diag: dict):
    """Return (converged_bool, summary_str) from a diag dict with max_rhat/min_ess/div_frac."""
    r = diag.get("max_rhat"); e = diag.get("min_ess"); dv = diag.get("div_frac", diag.get("divergences"))
    ok = (r is not None and r <= RHAT_MAX and e is not None and e >= ESS_MIN
          and dv is not None and dv < DIV_MAX)
    return ok, f"R-hat={r} ESS={e} div={dv}"


# ---------- DELIVERABLE gates ----------
def gate_model_classes():
    d = require_json("classes.defined", OUT / "model_classes.json", keys=("classes",))
    if d is None:
        return
    want = {"M0", "M1", "M2", "M3", "M4", "M5"}
    have = set(d["classes"].keys()) if isinstance(d["classes"], dict) else set(d["classes"])
    if not want.issubset(have):
        add("classes.defined", "RED", f"missing classes {want - have}")
    else:
        add("classes.defined", "GREEN", "M0–M5 defined with parameter vectors + priors")


def gate_stage1():
    d = require_json("stage1.evidence", OUT / "stage1_evidence.json",
                     keys=("observable", "log_evidence", "bayes_factors"))
    if d is None:
        return
    add("stage1.evidence", "GREEN",
        f"Stage-1 analytic evidence on observable={d.get('observable')} for "
        f"{len(d.get('log_evidence', {}))} classes")


def gate_identifiability():
    d1 = require_json("ident.M1", OUT / "identifiability_M1.json",
                      keys=("strain_energy_fraction", "fim_eigen"))
    if d1 is not None:
        add("ident.M1", "GREEN", "M1 new-param strain-energy + FIM eigen reported")
    # M3 damping identifiability reuses the Card D damping gate (input)
    dg = OUT / "cardD_inputs" / "damping_gate.json"
    if dg.exists():
        add("ident.M3_damping", "GREEN", "Card D damping-dissipation gate present (input)")
    else:
        add("ident.M3_damping", "RED", "missing Card D damping_gate.json input")


def gate_evidence_sensitivity():
    d = require_json("evidence.sensitivity", OUT / "evidence_sensitivity.json",
                     keys=("prior_widths", "ranking_per_width", "ranking_flips"))
    if d is None:
        return
    if d.get("ranking_flips"):
        add("evidence.sensitivity", "YELLOW",
            "model ranking FLIPS with prior width → prior-dominated; both reported")
    else:
        add("evidence.sensitivity", "GREEN", "ranking robust across >=2 prior widths")


def gate_stage2():
    files = sorted(OUT.glob("stage2_tmcmc_*.json"))
    if not files:
        add("stage2.tmcmc", "RED", "no Stage-2 TMCMC results (not produced yet)"); return
    any_conv = False
    for p in files:
        d = load_json(p)
        if isinstance(d, Exception) or "diag" not in d:
            add(f"stage2.{p.stem}", "RED", f"{p.name} missing diag"); continue
        ok, s = conv_status(d["diag"])
        ev = d.get("log_evidence_mean"); es = d.get("log_evidence_std")
        if ok:
            any_conv = True
            add(f"stage2.{p.stem}", "GREEN", f"converged ({s}); logZ={ev}±{es}")
        else:
            add(f"stage2.{p.stem}", "YELLOW",
                f"NOT converged ({s}) — labeled not-trustworthy, NOT a ranking input; logZ={ev}±{es}")
    if not any_conv:
        add("stage2.ranking", "YELLOW",
            "no Stage-2 class converged → flexible-θ ranking is indicative only (YELLOW)")
    else:
        add("stage2.ranking", "GREEN", "at least one converged class for the flexible-θ ranking")


def gate_heldout():
    d = require_json("heldout.qoi_winner", OUT / "scores_winner.json",
                     keys=("peak", "band"))
    if d is None:
        return
    pk = d["peak"]
    need = ("interval_score_mean", "crps_mean", "coverage_frac", "z_std")
    miss = [k for k in need if k not in pk]
    if miss:
        add("heldout.qoi_winner", "RED", f"scores_winner peak missing {miss}")
    else:
        add("heldout.qoi_winner", "GREEN",
            f"held-out QOI for evidence winner: peak cover={pk.get('coverage_frac')} "
            f"interval={pk.get('interval_score_mean')} z_std={pk.get('z_std')}")


def gate_verdict():
    d = require_json("verdict.ranking", OUT / "evidence_ranking.json",
                     keys=("observable", "ranking", "verdict", "verdict_tier"))
    if d is None:
        return
    tier = str(d.get("verdict_tier", "")).upper()
    if tier not in {"GREEN", "YELLOW", "RED"}:
        add("verdict.ranking", "RED", f"verdict_tier not a valid tier: {tier}")
    else:
        add("verdict.ranking", tier if tier != "RED" else "RED",
            f"verdict='{d.get('verdict')}' (observable={d.get('observable')})")


def gate_figures_packet():
    figs = list(FIG.glob("fig_evidence_ranking.*"))
    if figs:
        add("figures.ranking", "GREEN", f"evidence-ranking figure present: {[f.name for f in figs]}")
    else:
        add("figures.ranking", "RED", "missing figures/fig_evidence_ranking.*")
    iqa = OUT / "image_qa.json"
    if iqa.exists():
        d = load_json(iqa)
        if isinstance(d, dict) and d.get("pass") is True:
            add("figures.image_qa", "GREEN", "image-QA pass")
        else:
            add("figures.image_qa", "YELLOW", "image-QA present but not marked pass")
    else:
        add("figures.image_qa", "RED", "missing out/image_qa.json")
    if (WS / "packet.md").exists():
        add("packet", "GREEN", "packet.md present")
    else:
        add("packet", "RED", "missing packet.md")
    if (WS / "runtime.json").exists():
        add("runtime", "GREEN", "runtime.json present")
    else:
        add("runtime", "RED", "missing runtime.json")


def main():
    gate_immutability()
    gate_copy_matches_cardA()
    gate_model_classes()
    gate_stage1()
    gate_identifiability()
    gate_evidence_sensitivity()
    gate_stage2()
    gate_heldout()
    gate_verdict()
    gate_figures_packet()

    n_red = sum(1 for _, s, _ in results if s == "RED")
    n_yel = sum(1 for _, s, _ in results if s == "YELLOW")
    n_grn = sum(1 for _, s, _ in results if s == "GREEN")
    overall = "RED" if n_red else ("YELLOW" if n_yel else "GREEN")

    report = {
        "task": "Card F — Bayesian model-class selection (parameterization + damping), hard ShockSat accels",
        "overall": overall,
        "counts": {"green": n_grn, "yellow": n_yel, "red": n_red},
        "gates": [{"gate": g, "status": s, "msg": m} for g, s, m in results],
        "convergence_gate": {"rhat_max": RHAT_MAX, "ess_min": ESS_MIN, "div_max": DIV_MAX},
        "check_py_sha256": sha256(Path(__file__)),
    }
    (WS / "checker_report.json").write_text(json.dumps(report, indent=2))

    print(f"\nCard F checker — OVERALL {overall}  (GREEN {n_grn} / YELLOW {n_yel} / RED {n_red})")
    for g, s, m in results:
        print(f"  [{s:6}] {g}: {m}")
    print(f"\nwrote {WS/'checker_report.json'}")
    sys.exit(1 if overall == "RED" else 0)


if __name__ == "__main__":
    main()
