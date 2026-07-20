#!/usr/bin/env python3
"""IMMUTABLE checker for Card E (richer model form through L5 -> held-out QOI at the 8 hard accels).

Three-tier (AGENTS Result-Status): GREEN threshold met / YELLOW documented miss w/ caveat / RED blocking.
Overall = RED if any gate red; else YELLOW if any yellow; else GREEN. Exits non-zero ONLY on RED.

Design intent: BOTH a measured SHARPENING and a rigorous scoped HONEST NEGATIVE are acceptable outcomes.
RED is reserved for (a) a missing/ill-formed artifact, (b) a broken integrity reconstruction, (c) a verdict
claim STRONGER than the held-out interval-score evidence supports (anti-over-claim guard).

Run from the workspace root:  python3 check.py
Baseline (no artifacts yet) = RED = not-done.
"""
from __future__ import annotations
import json, sys
from pathlib import Path

WS = Path(__file__).resolve().parent
OUT = WS / "out"
FIG = WS / "figures"

GREEN, YELLOW, RED = "GREEN", "YELLOW", "RED"
results = []  # (gate, status, msg)


def g(gate, status, msg):
    results.append((gate, status, msg))


def load(name):
    p = OUT / name
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception as e:
        return {"__parse_error__": str(e)}


# ---- thresholds (stated; deviations must be justified in packet) ----
RECON_TOL = 1e-9          # per-PID blocks must reconstruct nominal groups + eigvals
RHAT_MAX = 1.05
ESS_MIN = 200
DIV_FRAC_MAX = 0.02
N_SPLITS_MIN = 25
COVER_LO, COVER_HI = 0.80, 1.0     # "calibrated" band for held-out coverage (≈0.95 target, tolerant)
ZSTD_LO, ZSTD_HI = 0.5, 2.0        # z-std calibration band (≈1 target)
SHARPEN_REL = 0.02                 # require >2% interval-score reduction to CALL it a sharpening


# ===== Gate 1: INTEGRITY (per-PID reduced blocks reconstruct the nominal) =====
intg = load("integrity.json")
if intg is None:
    g("integrity", RED, "out/integrity.json missing — per-PID reduced blocks not built/verified")
elif "__parse_error__" in intg:
    g("integrity", RED, f"integrity.json parse error: {intg['__parse_error__']}")
else:
    e_grp = intg.get("recon_group_max_abs_rel")
    e_eig = intg.get("nominal_recon_max_rel_eigval_err")
    npid = intg.get("n_pids")
    if e_grp is None or e_eig is None:
        g("integrity", RED, "integrity.json missing recon error fields")
    elif e_grp <= RECON_TOL and e_eig <= RECON_TOL:
        g("integrity", GREEN, f"{npid} per-PID blocks reconstruct nominal: group {e_grp:.1e}, eigval {e_eig:.1e} (<= {RECON_TOL:.0e})")
    else:
        g("integrity", RED, f"reconstruction off tolerance: group {e_grp:.1e}, eigval {e_eig:.1e} (> {RECON_TOL:.0e})")


# ===== Gate 2: IDENTIFIABILITY GATE (strain-energy fraction + FIM eigen view) — REQUIRED before any conclusion =====
ident = load("identifiability_rich.json")
if ident is None:
    g("identifiability", RED, "out/identifiability_rich.json missing — modal-identifiability gate not run")
elif "__parse_error__" in ident:
    g("identifiability", RED, f"identifiability_rich.json parse error: {ident['__parse_error__']}")
else:
    need = ("params", "fim", "n_matched_modes", "pretest_lever")
    miss = [k for k in need if k not in ident]
    has_se = all(("se_frac_peak" in p and "se_frac_typical" in p) for p in ident.get("params", [])) and len(ident.get("params", [])) > 0
    fim = ident.get("fim", {})
    has_fim = all(k in fim for k in ("discrepancy_floor_rel", "n_combos_above_prior", "singular_values"))
    if miss:
        g("identifiability", RED, f"identifiability missing fields: {miss}")
    elif not has_se:
        g("identifiability", RED, "identifiability params missing per-param strain-energy fractions")
    elif not has_fim:
        g("identifiability", RED, "identifiability FIM block missing required fields")
    else:
        nid = len(ident.get("verdict_identifiable_params", []))
        nno = len(ident.get("verdict_nonidentifiable_params", []))
        g("identifiability", GREEN, f"gate present: {len(ident['params'])} new params, {ident['n_matched_modes']} matched modes; "
          f"{fim['n_combos_above_prior']} combos clear floor (rel {fim['discrepancy_floor_rel']}); "
          f"identifiable {nid} / non-identifiable {nno}")


# ===== Gate 3: L5 CONVERGENCE on the richer model (NUTS/TMCMC; all-variable) =====
calib = load("l5_rich_calib.json")
if calib is None:
    g("l5_convergence", RED, "out/l5_rich_calib.json missing — richer model not run through L5")
elif "__parse_error__" in calib:
    g("l5_convergence", RED, f"l5_rich_calib.json parse error: {calib['__parse_error__']}")
else:
    # accept either a single record or {"variants": {name: diag}}
    recs = calib.get("variants")
    recs = recs if isinstance(recs, dict) else {"_": calib}
    worst = None
    for name, r in recs.items():
        d = r.get("diag", r)
        rh, ess, dfrac = d.get("max_rhat"), d.get("min_ess"), d.get("div_frac")
        if rh is None or ess is None or dfrac is None:
            g("l5_convergence", RED, f"[{name}] missing diag fields (max_rhat/min_ess/div_frac)")
            worst = RED
            continue
        ok = (rh <= RHAT_MAX and ess >= ESS_MIN and dfrac < DIV_FRAC_MAX)
        if ok:
            g("l5_convergence", GREEN, f"[{name}] CONVERGED R-hat {rh:.3f} ESS {ess:.0f} div_frac {dfrac:.3f}")
        else:
            g("l5_convergence", YELLOW, f"[{name}] NOT-YET-CONVERGED R-hat {rh:.3f} ESS {ess:.0f} div_frac {dfrac:.3f} "
              f"(YELLOW; intervals labeled not-trustworthy, NOT 'NUTS active')")
            worst = YELLOW if worst != RED else worst


# ===== Gate 4: HELD-OUT before/after at the 8 hard accels (>=25-split MC) =====
ho = load("heldout_before_after.json")
verdict_sharpen = None
if ho is None:
    g("heldout", RED, "out/heldout_before_after.json missing — before/after held-out QOI not scored")
elif "__parse_error__" in ho:
    g("heldout", RED, f"heldout_before_after.json parse error: {ho['__parse_error__']}")
else:
    ns = ho.get("n_splits", 0)
    before = ho.get("before", {}); after = ho.get("after", {})
    bh, ah = before.get("hard", {}), after.get("hard", {})
    bo, ao = before.get("other", {}), after.get("other", {})
    need_h = ("interval_score_mean", "crps_mean", "coverage_frac", "z_std")
    if ns < N_SPLITS_MIN:
        g("heldout", RED, f"n_splits {ns} < required {N_SPLITS_MIN}")
    elif not (all(k in bh for k in need_h) and all(k in ah for k in need_h)):
        g("heldout", RED, "heldout before/after missing required hard-accel score fields")
    else:
        # derive sharpen verdict from the numbers (anti-over-claim)
        b_is, a_is = bh["interval_score_mean"], ah["interval_score_mean"]
        rel = (b_is - a_is) / b_is if b_is else 0.0
        cov_ok = COVER_LO <= ah["coverage_frac"] <= COVER_HI
        z_ok = ZSTD_LO <= abs(ah["z_std"]) <= ZSTD_HI
        # other-channel non-degradation
        degraded = False
        if bo.get("interval_score_mean") and ao.get("interval_score_mean"):
            degraded = ao["interval_score_mean"] > bo["interval_score_mean"] * (1 + SHARPEN_REL)
        verdict_sharpen = bool(rel > SHARPEN_REL and cov_ok and z_ok and not degraded)
        g("heldout", GREEN, f"{ns} splits; hard-accel interval {b_is:.4g}->{a_is:.4g} ({rel*100:+.1f}%), "
          f"after cover {ah['coverage_frac']:.2f} z-std {ah['z_std']:.2f}, other-degraded={degraded}; "
          f"DERIVED sharpen={verdict_sharpen}")


# ===== Gate 5: FIGURES + image-QA =====
need_figs = ["fig_identifiability.png", "fig_before_after.png"]
missing_figs = [f for f in need_figs if not (FIG / f).exists()]
iqa = load("image_qa.json")
if missing_figs:
    g("figures", RED, f"missing figures: {missing_figs}")
elif iqa is None:
    g("figures", RED, "out/image_qa.json missing — image-legibility QA not run")
elif iqa.get("all_pass") is True:
    g("figures", GREEN, f"{len(need_figs)} figures present; image-QA all_pass")
else:
    g("figures", YELLOW, f"figures present but image-QA not all_pass: {iqa.get('failures', '?')}")


# ===== Gate 6: VERDICT consistency (anti-over-claim) =====
verd = load("verdict.json")
if verd is None:
    g("verdict", RED, "out/verdict.json missing — scoped verdict not generated")
elif "__parse_error__" in verd:
    g("verdict", RED, f"verdict.json parse error: {verd['__parse_error__']}")
else:
    claim = verd.get("claim_sharpen")
    if claim is None:
        g("verdict", RED, "verdict.json missing claim_sharpen")
    elif verdict_sharpen is None:
        g("verdict", RED, "verdict claims an outcome but held-out gate did not produce a derived verdict")
    elif bool(claim) != bool(verdict_sharpen):
        g("verdict", RED, f"OVER-CLAIM GUARD: verdict claim_sharpen={claim} disagrees with held-out-derived {verdict_sharpen}")
    else:
        g("verdict", GREEN, f"verdict consistent with held-out evidence: claim_sharpen={claim}")


# ---- roll up ----
order = {GREEN: 0, YELLOW: 1, RED: 2}
overall = GREEN
for _, s, _ in results:
    if order[s] > order[overall]:
        overall = s
ng = sum(s == GREEN for _, s, _ in results)
ny = sum(s == YELLOW for _, s, _ in results)
nr = sum(s == RED for _, s, _ in results)

print("=" * 78)
print("Card E checker — richer model form through L5 -> held-out QOI @ 8 hard accels")
print("=" * 78)
for gate, status, msg in results:
    print(f"[{status:6}] {gate:16} {msg}")
print("-" * 78)
print(f"OVERALL: {overall}   ({ng} GREEN / {ny} YELLOW / {nr} RED)")
report = {"overall": overall, "n_green": ng, "n_yellow": ny, "n_red": nr,
          "gates": [{"gate": a, "status": b, "msg": c} for a, b, c in results],
          "derived_sharpen": verdict_sharpen}
(WS / "checker_report.json").write_text(json.dumps(report, indent=2))
sys.exit(1 if overall == RED else 0)
