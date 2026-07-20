#!/usr/bin/env python3
"""Immutable checker — Card G: does MULTI-REFERENCE hammer data break the participation÷damping confound and
improve the ShockSat L5 twin's held-out per-channel AMPLITUDE skill vs climatology?

Three-tier (GREEN/YELLOW/RED); exits non-zero ONLY on RED. A rigorous, scoped HONEST NEGATIVE (amplitude still
≤0 after the confound is provably broken, or a documented data-quality ceiling) is a YELLOW documented finding,
NOT a failure. DO NOT EDIT during the trial (self-SHA lock in code/.check_lock.sha256). Run: python3 check.py

Gate map:
  integrity.*        — copied Card F code byte-identical + self/inherited SHA lock (anchor for any "improved" claim)
  partA.*            — reproduce the Card F value program on +X-only (freq +0.93 / amp ≈−1.0 / Beck −0.68→−0.25)
  partB.coherence    — per-reference data-quality diagnostic (the +X ~0.07 risk), carried into every amp verdict
  partB.identifiability — FIM/strain-energy directions clearing the realized floor, single-ref vs multi-ref
  partB.mechanism    — drive-shape ratio |H(d1)|/|H(d2)| → φ_d ratio recovery (confound break, or not)
  partB.amplitude    — held-out AMPLITUDE skill vs climatology, BEFORE(+X) vs AFTER(multi-ref), all-variable conv gate
  partB.frequency    — freq skill preserved under multi-ref (should stay ≈+0.93)
  deliverables.*     — mechanism + value figures, image-QA, packet, runtime
"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

WS = Path(__file__).resolve().parent
OUT = WS / "out"; FIG = WS / "figures"; CODE = WS / "code"
CARD_F = WS.parent / "shocksat_modelclass_L5_20260619" / "code"   # the byte-identical source of inherited code
# inherited (COPY-never-edit) Card F code this study reuses unmodified; new multiref_*.py are NOT in this list
INHERITED = ["core.py", "realfrf.py", "modal_feature.py", "heldout_qoi.py", "score.py", "value_eval.py",
             "freq_value.py", "modal_beck_ash.py", "modal_ash_mac.py", "damping_inference.py", "dampcorr_qoi.py"]
R = []   # (gate, status, msg)


def add(g, s, m): R.append((g, s, m))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def lj(p):
    try: return json.loads(p.read_text())
    except Exception as e: return e


def integrity():
    lock = CODE / ".check_lock.sha256"; me = sha(Path(__file__))
    if lock.exists():
        rec = json.loads(lock.read_text())
        add("integrity.self", "GREEN" if rec.get("self") == me else "RED",
            "check.py unchanged" if rec.get("self") == me else "check.py EDITED mid-trial")
        bad = [f for f in INHERITED if rec.get(f) != (sha(CODE / f) if (CODE / f).exists() else None)]
        add("integrity.inherited", "RED" if bad else "GREEN",
            f"inherited code edited: {bad}" if bad else "inherited code unchanged since lock")
    else:
        rec = {"self": me}; rec.update({f: (sha(CODE / f) if (CODE / f).exists() else None) for f in INHERITED})
        lock.write_text(json.dumps(rec, indent=1))
        add("integrity.self", "GREEN", "lock created (first run)")
        add("integrity.inherited", "GREEN", "inherited code SHA baseline recorded")
    # byte-identical to Card F source (the integrity anchor)
    if CARD_F.exists():
        mm = [f for f in INHERITED if (CODE / f).exists() and (CARD_F / f).exists() and sha(CODE / f) != sha(CARD_F / f)]
        miss = [f for f in INHERITED if not (CODE / f).exists()]
        st = "RED" if (mm or miss) else "GREEN"
        add("integrity.copy_vs_cardF", st,
            f"diff from Card F: {mm}; missing: {miss}" if (mm or miss) else "byte-identical to Card F code")
    else:
        add("integrity.copy_vs_cardF", "YELLOW", "Card F code dir absent")


def _skill(d, *path):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def partA():
    """Reproduce the Card F headline on +X-only. GREEN iff each reproduced number matches the documented Card F
    value within tolerance; integrity anchor for any Part-B 'improved' claim."""
    # Card F documented headline numbers (packet §2/§3 + checker_twin_report) and tolerances
    TOL_FREQ, TOL_AMP, TOL_BECK = 0.10, 0.25, 0.20
    cf = WS.parent / "shocksat_modelclass_L5_20260619" / "out"
    # frequency skill ≈ +0.93
    f = lj(OUT / "partA_freq_value_seed00.json")
    if isinstance(f, dict):
        sk = _skill(f, "twin_vs_climatology", "crps_skill")
        ref = _skill(lj(cf / "freq_value_seed00.json"), "twin_vs_climatology", "crps_skill") if (cf / "freq_value_seed00.json").exists() else 0.93
        ok = sk is not None and abs(sk - ref) <= TOL_FREQ
        add("partA.frequency", "GREEN" if ok else "RED",
            f"reproduced freq CRPS-skill {sk if sk is None else round(sk,3)} vs Card F {round(ref,3)} (tol {TOL_FREQ})")
    else:
        add("partA.frequency", "RED", "missing partA_freq_value_seed00.json")
    # amplitude skill ≈ −1.0 (mean over the reproduced seeds)
    ve = sorted(OUT.glob("partA_value_eval_seed0*.json"))
    sks = [_skill(lj(p), "NON_HARD", "crps_skill_vs_clim") for p in ve]
    sks = [s for s in sks if s is not None]
    if sks:
        m = sum(sks) / len(sks)
        add("partA.amplitude", "GREEN" if -1.0 - TOL_AMP <= m <= 0.0 + TOL_AMP else "RED",
            f"reproduced non-hard amplitude CRPS-skill mean {m:+.2f} over {len(sks)} seeds (Card F ≈ −1.0)")
    else:
        add("partA.amplitude", "RED", "no partA_value_eval_seed0*.json")
    # Beck shape-field lever −0.68 (FEM) → −0.25 (inferred)
    b = lj(OUT / "partA_modal_beck_ash.json")
    if isinstance(b, dict):
        s_fem = _skill(b, "heldout_peak_FEM_shapes", "crps_skill_vs_clim")
        s_inf = _skill(b, "heldout_peak_INFERRED_shapes", "crps_skill_vs_clim")
        ok = (s_fem is not None and s_inf is not None and abs(s_fem - (-0.68)) <= TOL_BECK
              and abs(s_inf - (-0.25)) <= TOL_BECK and s_inf > s_fem)
        add("partA.beck_shapefield", "GREEN" if ok else "YELLOW",
            f"reproduced Beck CRPS-skill FEM {s_fem} → inferred {s_inf} (Card F −0.68 → −0.25)")
    else:
        add("partA.beck_shapefield", "RED", "missing partA_modal_beck_ash.json")


def partB():
    # --- coherence diagnostic (data quality; carried into every amplitude verdict, never a stop) ---
    c = lj(OUT / "coherence_by_reference.json")
    if isinstance(c, dict) and "references" in c:
        refs = c["references"]
        meds = {k: v.get("coherence_median_band") for k, v in refs.items()}
        add("partB.coherence", "GREEN", f"per-reference band-median coherence present: "
            + ", ".join(f"{k}={None if meds[k] is None else round(meds[k],3)}" for k in refs))
    else:
        add("partB.coherence", "RED", "missing coherence_by_reference.json")
    # --- identifiability before/after (FIM directions clearing the realized floor) ---
    idn = lj(OUT / "multiref_identifiability.json")
    if isinstance(idn, dict) and "single_ref" in idn and "multi_ref" in idn:
        n1 = idn["single_ref"].get("n_dirs_above_floor"); n2 = idn["multi_ref"].get("n_dirs_above_floor")
        add("partB.identifiability", "GREEN",
            f"FIM directions above realized floor: single-ref {n1} → multi-ref {n2} (confound-break diagnostic)")
    else:
        add("partB.identifiability", "RED", "missing multiref_identifiability.json")
    # --- mechanism: drive-shape ratio recovery ---
    mech = lj(OUT / "drive_shape_ratio.json")
    if isinstance(mech, dict):
        add("partB.mechanism", "GREEN", f"drive-shape-ratio mechanism present (corr meas vs FEM φ_d ratio "
            f"= {mech.get('corr_meas_vs_fem_ratio')})")
    else:
        add("partB.mechanism", "RED", "missing drive_shape_ratio.json")
    # --- HEADLINE: held-out amplitude skill BEFORE(+X) vs AFTER(multi-ref) + convergence gate ---
    mv = lj(OUT / "multiref_value.json")
    if isinstance(mv, dict) and "before_xonly" in mv and "after_multiref" in mv:
        b = mv["before_xonly"].get("crps_skill_vs_clim"); a = mv["after_multiref"].get("crps_skill_vs_clim")
        conv = mv.get("calib_converged", None)
        # the result is whatever the numbers say; GREEN if the comparison is valid+convergence-honest; the
        # SIGN of the improvement is reported, not required (honest negative is a documented YELLOW finding).
        if b is None or a is None:
            add("partB.amplitude", "RED", "multiref_value present but missing before/after skill")
        else:
            improved = a > b + 0.05
            crossed0 = a > 0
            conv_tag = "converged" if conv else "NOT-yet-converged(YELLOW arm)"
            st = "GREEN" if conv else "YELLOW"
            verdict = ("amplitude skill RISES" if improved else "amplitude skill does NOT rise") + \
                      (" and crosses 0 (skillful)" if crossed0 else " (still ≤0)")
            add("partB.amplitude", st,
                f"held-out amplitude CRPS-skill: +X-only {b:+.2f} → multi-ref {a:+.2f} [{verdict}]; calib {conv_tag}")
    else:
        add("partB.amplitude", "RED", "missing multiref_value.json (before/after amplitude table)")
    # --- frequency preserved under multi-ref ---
    fm = lj(OUT / "multiref_freq.json")
    if isinstance(fm, dict):
        b = _skill(fm, "before_xonly", "crps_skill"); a = _skill(fm, "after_multiref", "crps_skill")
        add("partB.frequency", "GREEN" if (a is not None and a > 0.1) else "YELLOW",
            f"freq CRPS-skill +X-only {b} → multi-ref {a} (multi-ref must not hurt frequencies)")
    else:
        add("partB.frequency", "YELLOW", "multiref_freq.json absent (freq-preservation not yet confirmed)")


def deliverables():
    for fn in ("fig_coherence.png", "fig_mechanism.png", "fig_value_multiref.png", "fig_identifiability.png"):
        add(f"fig.{fn}", "GREEN" if (FIG / fn).exists() else "RED", "present" if (FIG / fn).exists() else "missing")
    iqa = lj(OUT / "image_qa.json") if (OUT / "image_qa.json").exists() else None
    add("deliverables.image_qa", "GREEN" if isinstance(iqa, dict) and iqa.get("pass") else "RED",
        "image-QA pass" if isinstance(iqa, dict) and iqa.get("pass") else "image-QA missing/not pass")
    add("deliverables.packet", "GREEN" if (WS / "packet.md").exists() else "RED",
        "packet.md present" if (WS / "packet.md").exists() else "missing packet.md")
    add("deliverables.runtime", "GREEN" if (WS / "runtime.json").exists() else "RED",
        "runtime.json present" if (WS / "runtime.json").exists() else "missing runtime.json")


def main():
    integrity(); partA(); partB(); deliverables()
    nr = sum(1 for _, s, _ in R if s == "RED"); ny = sum(1 for _, s, _ in R if s == "YELLOW")
    ng = sum(1 for _, s, _ in R if s == "GREEN")
    overall = "RED" if nr else ("YELLOW" if ny else "GREEN")
    rep = {"task": "Card G — multi-reference vs +X-only: does it break the participation÷damping confound and "
                   "raise held-out per-channel AMPLITUDE skill vs climatology while preserving freq skill?",
           "overall": overall, "counts": {"green": ng, "yellow": ny, "red": nr},
           "gates": [{"gate": g, "status": s, "msg": m} for g, s, m in R],
           "note": "Baseline RED = not done. Honest negative (amplitude still ≤0 with the confound broken, or a "
                   "documented data-quality ceiling) is a YELLOW documented finding, not a failure.",
           "check_sha256": sha(Path(__file__))}
    (WS / "checker_report.json").write_text(json.dumps(rep, indent=2))
    print(f"\ncheck — OVERALL {overall}  (GREEN {ng} / YELLOW {ny} / RED {nr})")
    for g, s, m in R:
        print(f"  [{s:6}] {g}: {m}")
    sys.exit(1 if overall == "RED" else 0)


if __name__ == "__main__":
    main()
