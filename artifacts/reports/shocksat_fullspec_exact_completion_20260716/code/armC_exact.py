#!/usr/bin/env python3
"""armC_exact — T1: the HONEST arm-C exact-basis score (card §2 T1).

WHY THIS EXISTS
The study's arm-C exact aggregate (0.157) is INVALID and was withdrawn (review C6 / decisions D17):
`rescore_freeze.py:78` loaded ONE shape MAP (fold `m_xpos_990x`'s) and applied it to all four LODO folds.
That MAP was fit on the other three drives, so for 3 of the 4 folds the "held-out" drive had already been
seen by the shapes being scored. Those three numbers are memory, not prediction.

WHAT THIS DOES INSTEAD
For EACH of the 4 folds independently:
  1. refit the shape-field MAP on the ENRICHED (exact-at-theta_MAP) basis `A0_wide__enr` using ONLY that
     fold's 3 TRAIN drives  -> `arm_c_score.map_fold(pkg_enr, ones(9), fold)`, multi-start 4, deterministic
     seed (the study's own leakage-safe fitter, imported read-only and reused verbatim);
  2. score THAT fold with ITS OWN MAP via `arm_c_nuts.shapes_forward` + `wscore_wide`'s warp/gain/grade
     machinery (the same scorer every other arm used, so the comparison is basis- and method-matched).

theta is held at the study's MAP, which the enriched package has FOLDED IN -> scoring is at theta=ones(9)
(study D14/D22 convention). The shape field is what gets re-optimized against the exact basis.

LEAKAGE RULE (absolute): fold k's MAP must never have seen drive k. Every saved MAP records its
`train_keys`; the checker (G04) RED-fails on any fold whose train_keys contain its own key, on fewer than 4
distinct MAP files, and on two folds whose MAP files are byte-identical.

NO SAMPLER: this is a deterministic multi-start L-BFGS optimum, not a posterior. Arm C's NUTS was
non-converged (fold-1 R-hat 13.95, ESS 2; study D13) and that diagnostic rides along with every number.
Resumable: an existing per-fold MAP .npz is skip-loaded.
"""
from __future__ import annotations
import json, os, sys, time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                # noqa: E402  (redirects all writes into this workspace)

sys.path.insert(0, C.STUDY_CODE)
import arm_c_score as ACS                          # noqa: E402  (read-only reuse: map_fold)

BASIS = "A0_wide__enr"                             # exact-at-theta_MAP basis shared by A0/A1/C (study D14)
N_STARTS = 4                                       # card: multi-start >= 4, deterministic seeds
MAPD = os.path.join(C.MY_OUT, "armC_exact_maps")
os.makedirs(MAPD, exist_ok=True)


def fit_fold(pkg, one, fold):
    """Refit the shape-field MAP for ONE fold on its 3 train drives. Returns (raw_mean, ks, r0, meta)."""
    train_keys = [k for k in C.DEV_KEYS if k != fold]
    mp = os.path.join(MAPD, f"shapes_map_{fold}.npz")
    if os.path.exists(mp):
        z = np.load(mp, allow_pickle=True)
        meta = json.loads(str(z["meta"]))
        print(f"  [{fold}] MAP exists (resume-skip), nlp {meta['nlp']:.3f}", flush=True)
        return z["raw_mean"], np.asarray(z["ks"], int), int(z["r0"]), meta
    t0 = time.time()
    print(f"  [{fold}] refitting shape MAP on TRAIN {train_keys} ...", flush=True)
    raw, ks, r0, nlp = ACS.map_fold(pkg, one, fold, n_starts=N_STARTS)
    dt = time.time() - t0
    meta = {"fold": fold, "train_keys": train_keys, "n_starts": N_STARTS, "nlp": float(nlp),
            "basis": BASIS, "theta_convention": "ones(9); theta_MAP folded into the enriched basis",
            "seed": 20260715, "fit_s": round(dt, 1),
            "method": "deterministic multi-start L-BFGS-B MAP (no sampler); arm_c_score.map_fold reused "
                      "read-only from the study",
            "leakage_note": f"fit on 3 TRAIN drives only; held-out drive {fold} NOT seen"}
    np.savez_compressed(mp, raw_mean=raw, ks=ks, r0=r0, meta=json.dumps(meta))
    print(f"  [{fold}] MAP done, nlp {nlp:.3f} ({dt:.0f}s)", flush=True)
    return raw, np.asarray(ks, int), int(r0), meta


def score_fold(pkg, one, fold, fwd, caches):
    """Score ONE fold with ITS OWN shape MAP — same machinery as every other arm."""
    train_keys = [k for k in C.DEV_KEYS if k != fold]
    rho, bmasks = C.SW._train_warp(pkg, one, train_keys, caches, True, None, fwd)
    fold_mask = None
    if bmasks:
        fm = np.zeros(len(caches[fold]["freqs"]), bool)
        for tk, mmask in bmasks.items():
            if mmask.shape[0] == fm.shape[0]:
                fm |= mmask
        fold_mask = fm if fm.sum() >= C.SW.MIN_BAND else None
    gain_db = C.SW._fold_gain(pkg, one, train_keys, caches, True, None, fwd)
    bands = C.SW._grade_bands(pkg, one, fold, caches[fold], rho, fold_mask, True, None, None, fwd)
    return bands, float(rho), float(gain_db)


def main():
    t_start = time.time()
    pkg = C.WP.load(BASIS)
    one = np.ones(len(pkg.free_names))
    caches = C.SW.load_caches()
    print(f"arm-C exact: basis {BASIS} (r={np.asarray(pkg.A).shape[1]}), theta=ones(9), "
          f"{len(C.DEV_KEYS)} per-fold refits", flush=True)

    folds, per_fold_map_nlp = {}, {}
    for fold in C.DEV_KEYS:
        raw, ks, r0, meta = fit_fold(pkg, one, fold)
        fwd = C.AC.shapes_forward(pkg, one, raw, ks, r0)
        bands, rho, gain_db = score_fold(pkg, one, fold, fwd, caches)
        rec = {"train_keys": meta["train_keys"], "n_starts": meta["n_starts"],
               "map_file": os.path.relpath(os.path.join(MAPD, f"shapes_map_{fold}.npz"), C.WS),
               "map_nlp": meta["nlp"], "rho": round(rho, 4), "gain_dB": round(gain_db, 3),
               "bands": {b: bands[b].get("P1p") for b in ("sub200", "b200_500")},
               "bands_detail": {b: {k: v for k, v in bands[b].items()} for b in ("sub200", "b200_500")}}
        C.assert_finite(rec["bands"], f"armC.{fold}.bands")
        folds[fold] = rec
        per_fold_map_nlp[fold] = meta["nlp"]
        print(f"  [{fold}] sub200 {rec['bands']['sub200']:+.4f}  b200_500 {rec['bands']['b200_500']:+.4f}",
              flush=True)

    # ---- leakage self-audit (belt and braces; the checker re-verifies independently)
    audit = {"per_fold_map_distinct": len({folds[f]["map_file"] for f in folds}) == len(folds),
             "no_fold_trained_on_itself": all(f not in folds[f]["train_keys"] for f in folds),
             "train_keys_are_the_other_three": all(
                 sorted(folds[f]["train_keys"]) == sorted([k for k in C.DEV_KEYS if k != f]) for f in folds)}
    if not all(audit.values()):
        raise RuntimeError(f"LEAKAGE AUDIT FAILED: {audit}")

    fold_mean = {b: float(np.mean([folds[f]["bands"][b] for f in C.DEV_KEYS])) for b in ("sub200", "b200_500")}

    # ---- paired delta vs A1-exact (same enriched basis, same 4 folds -> a clean paired comparison)
    ex = C.study_exact_freeze()
    a1 = ex["A1"]["exact"]["folds"]
    paired = {}
    for b in ("sub200", "b200_500"):
        deltas = [folds[f]["bands"][b] - a1[f][b]["P1p"] for f in C.DEV_KEYS]
        dm, se, pf = C.paired_stats(deltas)
        paired[b] = {"delta_mean": dm, "delta_se": se, "per_fold": pf,
                     "two_se": 2 * se, "A1_exact_per_fold": [a1[f][b]["P1p"] for f in C.DEV_KEYS],
                     "A1_exact_mean": ex["A1"]["exact"][b],
                     "S1_rule_met": bool(dm >= 0.05 and dm >= 2 * se)}
    C.assert_finite(paired, "armC.paired")

    # ---- the study's (invalid) number, for the record — NOT used as a comparator
    withdrawn = {"study_exact_sub200": ex["C"]["exact"]["sub200"],
                 "study_exact_b200_500": ex["C"]["exact"]["b200_500"],
                 "study_caveat": ex["C"].get("caveat", ""),
                 "why_invalid": "rescore_freeze.py:78 applied fold m_xpos_990x's shape MAP to all 4 folds; "
                                "3/4 exact fold scores therefore saw their held-out drive (review C6, "
                                "accepted D17). Shown for the audit trail only; not a valid comparator.",
                 "screening_sub200_leakage_safe": 0.189}

    out = {"card": "T1 — honest arm-C exact score (per-fold refits)",
           "basis": BASIS,
           "theta_convention": "ones(9): the enriched basis has theta_MAP folded in (study D14/D22)",
           "method": "deterministic multi-start (n=4) L-BFGS-B MAP of the shape field per fold, refit on "
                     "that fold's 3 TRAIN drives only; scored with wscore_wide warp+global-gain+grade. "
                     "NO SAMPLER: this is an optimizer point estimate, not a posterior.",
           "sampler_status": {"sampler_run": False,
                              "study_armC_nuts": "non-converged/multimodal (fold-1 R-hat 13.95, ESS 2; D13)",
                              "note": "posterior uncertainty for arm C remains UNRESOLVED; these are "
                                      "deterministic MAP scores only"},
           "leakage_audit": audit,
           "folds": folds, "fold_mean": fold_mean,
           "paired_delta_vs_A1_exact": paired,
           "map_nlp_per_fold": per_fold_map_nlp,
           "withdrawn_study_number": withdrawn,
           "generated": time.strftime("%Y-%m-%dT%H:%M:%S")}
    C.assert_finite(fold_mean, "armC.fold_mean")
    with open(os.path.join(C.MY_OUT, "armC_exact.json"), "w") as f:
        json.dump(out, f, indent=1)
    C.log_step("armC_exact", time.time() - t_start, folds=len(folds))

    print("\n=== T1 RESULT (arm C, honest per-fold exact refits) ===")
    for b in ("sub200", "b200_500"):
        p = paired[b]
        print(f"  {b:9s}: C {fold_mean[b]:+.4f}  A1 {p['A1_exact_mean']:+.4f}  "
              f"delta {p['delta_mean']:+.4f} +/- {p['delta_se']:.4f} (2SE {p['two_se']:.4f})  "
              f"S1 rule met: {p['S1_rule_met']}")
    print(f"  (study's withdrawn leaky number was sub200 {withdrawn['study_exact_sub200']:.4f})")


if __name__ == "__main__":
    main()
