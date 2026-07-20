#!/usr/bin/env python3
"""IMMUTABLE checker for Card A: validate the orthogonal-Schneider StatFEM twin on the REAL ShockSat.

Written BEFORE results (defines the acceptance contract). Do NOT edit during the trial.
Reads the pipeline's out/*.json + figures, applies the §9 gates, writes checker_report.json, and exits
non-zero ONLY on RED (documented YELLOW does not abort replay). Three-tier per gate: green/yellow/red.

Run:  ../../.venv_nuts/bin/python check.py     (or via run_all.sh)
"""
from __future__ import annotations
import json, sys
from pathlib import Path

WS = Path(__file__).resolve().parent
OUT = WS / "out"
FIG = WS / "figures"

# convergence thresholds (AGENTS.md NUTS gate)
RHAT_MAX, ESS_MIN, DIV_FRAC_MAX = 1.05, 200.0, 0.02
MC_MIN_CONFIGS = 25


def load(p):
    p = Path(p)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


GATES = []


def gate(name, status, detail):
    assert status in ("green", "yellow", "red")
    GATES.append({"gate": name, "status": status, "detail": detail})


# ---------------------------------------------------------------- G1 provenance / plain ShockSat
def g_provenance():
    bad = []
    for f in (WS / "code").glob("*.py"):
        t = f.read_text().lower()
        if "tray_coupled" in t or "shocksat_tray" in t:
            bad.append(f.name)
    cfg = load(OUT / "run_config.json")
    uses_tray = cfg.get("uses_tray", False) if cfg else None
    if bad:
        gate("provenance_plain_shocksat", "red", f"tray reference in {bad}")
    elif uses_tray:
        gate("provenance_plain_shocksat", "red", "run_config uses_tray=True")
    else:
        gate("provenance_plain_shocksat", "green",
              "no tray refs; plain 9-group FEM" + ("" if cfg else " (run_config.json pending)"))


# ---------------------------------------------------------------- G2 matched-path, no SOL111
def g_observable():
    san = load(OUT / "matched_path_sanity.json")
    inv = load(OUT / "observable_investigation.json")
    if san is None or inv is None:
        gate("observable_validated", "red", "missing matched_path_sanity.json / observable_investigation.json")
        return
    # FEM first mode vs measured first .ash mode ~54 Hz; single-impact reprocess aligns to <5 Hz median
    si = inv.get("single_impact_reprocess", {})
    errs = [si[c]["median_peak_ash_err_hz"] for c in ("ch1", "ch50", "ch87") if c in si]
    ok_align = errs and max(errs) < 5.0
    # FEM peak near 54-55 present for at least one channel (matched-path sane)
    fem_lowmode = False
    for c in san.get("channels", {}).values():
        for z, b in c.get("by_zeta", {}).items():
            if any(abs(p - 54.4) < 2.0 for p in b.get("fem_peaks_hz", [])):
                fem_lowmode = True
    if ok_align and fem_lowmode:
        gate("observable_validated", "green",
             f"single-impact peak->mode err max {max(errs):.1f} Hz; FEM first mode ~54 Hz matches measured")
    else:
        gate("observable_validated", "yellow",
             f"alignment partial (peak err {errs}, fem_lowmode={fem_lowmode})")


# ---------------------------------------------------------------- G3 arms + convergence
def _cell_files():
    d = OUT / "cells"
    return sorted(d.glob("*.json")) if d.exists() else []


def g_arms_convergence():
    cells = _cell_files()
    if not cells:
        gate("arms_present", "red", "no out/cells/*.json")
        gate("nuts_convergence", "red", "no cells to check")
        return
    arms = set()
    nonconv_unlabeled, nonconv_labeled, conv = [], [], 0
    for cf in cells:
        c = load(cf)
        if not c:
            continue
        arms.add(c.get("arm"))
        d = c.get("diag", {})
        ok = (d.get("max_rhat", 9) <= RHAT_MAX and d.get("min_ess", 0) >= ESS_MIN
              and d.get("div_frac", 1) < DIV_FRAC_MAX)
        if ok:
            conv += 1
        elif c.get("not_yet_converged", False):
            nonconv_labeled.append(cf.name)
        else:
            nonconv_unlabeled.append(cf.name)
    have = {"M0", "M3"} <= arms
    gate("arms_present", "green" if have else "red",
         f"arms={sorted(a for a in arms if a)} (need M0 naive + M3 orthogonal)")
    if nonconv_unlabeled:
        gate("nuts_convergence", "red", f"{len(nonconv_unlabeled)} cells non-converged & UNLABELED: "
             f"{nonconv_unlabeled[:4]}")
    elif nonconv_labeled:
        gate("nuts_convergence", "yellow",
             f"{conv} converged; {len(nonconv_labeled)} labeled not-yet-converged (YELLOW)")
    else:
        gate("nuts_convergence", "green", f"all {conv} cells converged (R-hat<=1.05, ESS>=200, div<2%)")


# ---------------------------------------------------------------- G4 orthogonal-Schneider + sharpness
def g_sharpness():
    s = load(OUT / "scores_summary.json")
    if not s:
        gate("orthogonal_schneider_sharpness", "red", "missing out/scores_summary.json")
        gate("sharpness_headline_not_coverage", "red", "missing scores_summary")
        return
    arms = s.get("arms", {})
    m3 = arms.get("M3", {})
    need = ("interval_score", "crps", "logpd")
    has_proper = all(k in m3 for k in need)
    has_pit = "pit" in m3 or "pit_stats" in m3
    has_z = "z_stats" in m3 or "z" in m3
    if has_proper and has_pit and has_z:
        gate("orthogonal_schneider_sharpness", "green",
             f"M3 reports {need}+PIT+z (interval_score={m3.get('interval_score')})")
    else:
        gate("orthogonal_schneider_sharpness", "red",
             f"M3 missing proper-score/PIT/z (proper={has_proper},pit={has_pit},z={has_z})")
    if s.get("headline") in need and s.get("peak_weighted") and s.get("coherence_weighted"):
        gate("sharpness_headline_not_coverage", "green",
             f"headline={s.get('headline')} (proper score), peak+coherence weighted; coverage secondary")
    else:
        gate("sharpness_headline_not_coverage", "yellow",
             f"headline={s.get('headline')}, peak_weighted={s.get('peak_weighted')}, "
             f"coherence_weighted={s.get('coherence_weighted')}")


# ---------------------------------------------------------------- G5 wide-band doesn't win
def g_wideband():
    w = load(OUT / "wideband_demo.json")
    if not w:
        gate("wideband_doesnt_win", "red", "missing out/wideband_demo.json")
        return
    if w.get("coverage_up_but_score_worse"):
        gate("wideband_doesnt_win", "green",
             f"wide-band: coverage {w.get('wide_coverage')} > {w.get('base_coverage')} "
             f"but interval score {w.get('wide_interval_score')} WORSE than {w.get('base_interval_score')}")
    else:
        gate("wideband_doesnt_win", "red", "demo did not show coverage-up-but-proper-score-worse")


# ---------------------------------------------------------------- G6 parameter-count study
def g_paramcount():
    p = load(OUT / "paramcount.json")
    if not p:
        gate("parameter_count_study", "red", "missing out/paramcount.json")
        return
    methods = p.get("methods", {})
    need = {"all9", "fim_downselect"}
    have_evidence_or_pool = any(k in methods for k in ("evidence", "hier_pool"))
    if need <= set(methods) and have_evidence_or_pool and p.get("winner"):
        gate("parameter_count_study", "green",
             f"methods={list(methods)}; winner={p.get('winner')} (scored on held-out QOI)")
    else:
        gate("parameter_count_study", "yellow", f"methods={list(methods)} (need all9+fim_downselect+evidence/pool)")


# ---------------------------------------------------------------- G7 MC distributions
def g_mc():
    m = load(OUT / "mc_summary.json")
    if not m:
        gate("mc_distributions", "red", "missing out/mc_summary.json")
        return
    n = m.get("n_configs", 0)
    if n >= MC_MIN_CONFIGS and "per_arm" in m:
        gate("mc_distributions", "green", f"{n} configs (split axis), per-arm score distributions present")
    elif n > 0:
        gate("mc_distributions", "yellow", f"{n} configs (<{MC_MIN_CONFIGS}, labeled reduction)")
    else:
        gate("mc_distributions", "red", "no MC configs")


# ---------------------------------------------------------------- G8 identifiability gate
def g_identifiability():
    i = load(OUT / "identifiability.json")
    if not i:
        gate("identifiability_gate", "red", "missing out/identifiability.json")
        return
    has = all(k in i for k in ("strain_energy", "fim", "finite_perturbation"))
    gate("identifiability_gate", "green" if has else "red",
         f"strain_energy+FIM+finite_perturbation present={has}; "
         f"n_identifiable={i.get('n_identifiable_groups')}")


# ---------------------------------------------------------------- G9 figures QA
def g_figures():
    req = ["fig_error_participation.png", "fig_scoring_suite.png", "fig_heldout_frf.png",
           "fig_mc_distributions.png", "fig_schematic.png"]
    missing = [r for r in req if not (FIG / r).exists()]
    il = load(FIG / "image_legibility_report.json")
    ov = load(FIG / "text_overlap_report.json")
    if missing:
        gate("required_figures", "red", f"missing figures: {missing}")
    else:
        gate("required_figures", "green", f"all {len(req)} required figures present")
    il_ok = il and il.get("pass", il.get("passed", False))
    ov_ok = ov and ov.get("pass", ov.get("passed", False))
    if il_ok and ov_ok:
        gate("figure_qa", "green", "image legibility + text-overlap pass")
    else:
        gate("figure_qa", "red", f"image_legibility={bool(il_ok)} text_overlap={bool(ov_ok)}")


# ---------------------------------------------------------------- G10 runtime
def g_runtime():
    r = load(WS / "runtime.json")
    if not r:
        gate("runtime_accounting", "red", "missing runtime.json")
        return
    a, e = r.get("active_runtime_s"), r.get("elapsed_wallclock_s")
    if a is not None and e is not None and a <= e + 1e-6:
        gate("runtime_accounting", "green", f"active {a:.0f}s <= elapsed {e:.0f}s")
    else:
        gate("runtime_accounting", "yellow", f"active={a}, elapsed={e}")


def main():
    g_provenance(); g_observable(); g_arms_convergence(); g_sharpness(); g_wideband()
    g_paramcount(); g_mc(); g_identifiability(); g_figures(); g_runtime()
    counts = {k: sum(1 for g in GATES if g["status"] == k) for k in ("green", "yellow", "red")}
    overall = "red" if counts["red"] else ("yellow" if counts["yellow"] else "green")
    report = {"study": "statfem_real_validation_20260617", "overall": overall,
              "counts": counts, "gates": GATES,
              "thresholds": {"rhat_max": RHAT_MAX, "ess_min": ESS_MIN, "div_frac_max": DIV_FRAC_MAX,
                             "mc_min_configs": MC_MIN_CONFIGS}}
    (WS / "checker_report.json").write_text(json.dumps(report, indent=2))
    print(f"OVERALL: {overall.upper()}  green={counts['green']} yellow={counts['yellow']} red={counts['red']}")
    for g in GATES:
        print(f"  [{g['status'][0].upper()}] {g['gate']}: {g['detail']}")
    sys.exit(1 if overall == "red" else 0)


if __name__ == "__main__":
    main()
