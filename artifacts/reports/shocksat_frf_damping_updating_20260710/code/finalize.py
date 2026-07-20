#!/usr/bin/env python3
"""Finalists (EXACT-BASIS, card §6 + the completed run's D18/D22 guard) + S4 attribution ablation.

The loop screened/dev-scored on base own-basis packages (reduced-basis inflation, labeled). DECISION-relevant
scores must be exact-basis: we reuse the completed run's ENRICHED (_enr) packages (own-basis, 128 modes,
spot-checked to ~1e-7) and re-score the freeze set here (off-budget freeze-set re-evaluation, NOT new search).
Damping specs are basis-independent (band zeta is purely frequency-based), applied to the exact packages.

Freeze set (exact-basis):
  A0_enr              baseline, fixed zeta=1%                         [baseline]
  A0d_enr             A0_enr + best-fit damping (A0d)                 [damping_only]
  c06_tb_xface_enr    shape edit, fixed zeta=1%                       [shape_only]
  a04_welds_t074_enr  shape edit, fixed zeta=1%                       [shape_only]
  b_c06_enr           c06_enr + best-fit damping                      [both]
  rnd003_enr          random-track exact-basis best, fixed zeta=1%    [random]
S4: damping_only margin must be >= 2/3 of the winner's margin over A0 to attribute a gain to DAMPING.
"""
import json, os, sys, shutil, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femdamp as D
import femlib as F
import score as SC

WS = D.WS
TRL = os.path.join(F.ROOT, "artifacts/reports/shocksat_true_remodel_loop_20260706")
ENR = ["A0_enr", "c06_tb_xface_enr", "a04_welds_t074_enr", "a16_bb_splits_combo_enr",
       "b04_ctrl_bb_scale_enr", "rnd003_enr"]


def setup_enr():
    dst = os.path.join(WS, "data", "packages")
    for cid in ENR:
        src = os.path.join(TRL, "data", "packages", cid + ".npz")
        d = os.path.join(dst, cid + ".npz")
        if os.path.exists(src) and not os.path.exists(d):
            shutil.copy2(src, d)
    # spot-check provenance: reuse the validated exact-basis checks (SAME packages), re-keyed to rel_err
    for cid in ENR:
        src = os.path.join(TRL, "out", f"spot_check_{cid}.json")
        if os.path.exists(src):
            s = json.load(open(src))
            out = {"cid": cid, "rel_err": float(s.get("max_rel_err", s.get("rel_err", 0.0))),
                   "n_modes": s.get("n_modes"), "pass_0p3pct": bool(s.get("pass_0p3pct")),
                   "provenance": "exact-basis reduction validated in shocksat_true_remodel_loop_20260706 "
                                 "(identical package); reused here read-only"}
            json.dump(out, open(os.path.join(WS, "out", f"spot_check_{cid}.json"), "w"), indent=1)


def main():
    t0 = time.time()
    setup_enr()
    a0d = json.load(open(os.path.join(WS, "out", "a0d.json")))
    dmp = a0d["best_damping"]                       # band4 (frequency-based -> basis independent)
    fixed = {"kind": "fixed", "zeta": 0.01}
    finals = [
        ("A0_enr", "A0_enr", fixed, "baseline", "modal_only", "inherited FEM exact-basis, zeta=1% (bar)"),
        ("A0d_enr", "A0_enr", dmp, "damping_only", "A0d_band", "A0_enr + best-fit band damping"),
        ("c06_enr", "c06_tb_xface_enr", fixed, "shape_only", "shape", "top-box cross-face shape, zeta=1%"),
        ("a04_enr", "a04_welds_t074_enr", fixed, "shape_only", "shape", "weld-thinning shape, zeta=1%"),
        ("b_c06_enr", "c06_tb_xface_enr", dmp, "both", "shape_plus_damping", "c06 shape + best-fit damping"),
        ("rnd003_enr", "rnd003_enr", fixed, "random", "random", "random-track exact-basis best, zeta=1%"),
    ]
    scores = {}
    for label, cid, damping, ablation, family, rat in finals:
        pkg = F.Package.load(cid)
        th = np.asarray(pkg.theta_map()[0], float)
        rec = SC.score_candidate(cid, "finalist", damping=damping, theta_override=th, family=family,
                                 ablation=ablation, rationale=rat, enforce_budget=False, label=label)
        scores[label] = {k: rec[k] for k in ("P1p_mean", "P1p_se", "P3_mean", "P2p_mean",
                                             "alignment_gain", "P1p_folds", "damping_dim", "ablation")}
        scores[label]["cid"] = cid
        scores[label]["damping"] = damping
        print(f"  {label:12s} P1'={rec['P1p_mean']:.4f} (SE {rec['P1p_se']}) P3={rec['P3_mean']:.4f} "
              f"P2'={rec['P2p_mean']:.4f} [{ablation}]", flush=True)

    A0 = scores["A0_enr"]["P1p_mean"]
    se_A0 = scores["A0_enr"]["P1p_se"] or 0.1
    # margins over A0 (exact-basis)
    m_damp = scores["A0d_enr"]["P1p_mean"] - A0
    m_shape = max(scores["c06_enr"]["P1p_mean"], scores["a04_enr"]["P1p_mean"]) - A0
    m_both = scores["b_c06_enr"]["P1p_mean"] - A0
    agent_best = max(scores[k]["P1p_mean"] for k in ("A0d_enr", "c06_enr", "a04_enr", "b_c06_enr"))
    winner_label = max(("A0d_enr", "c06_enr", "a04_enr", "b_c06_enr"), key=lambda k: scores[k]["P1p_mean"])
    winner_margin = agent_best - A0
    damping_share = (m_damp / winner_margin) if winner_margin > 1e-9 else 0.0
    if winner_margin <= 0:
        attribution = "no lever cleared the floor (winner does not beat A0 exact-basis)"
    elif damping_share >= 2 / 3:
        attribution = "improvement attributable to DAMPING"
    else:
        attribution = "improvement is shape/theta; DAMPING lever unproven"
    ablation = {"winner_label": winner_label, "winner_margin": round(float(winner_margin), 4),
                "damping_only_margin": round(float(m_damp), 4),
                "shape_only_margin": round(float(m_shape), 4),
                "both_margin": round(float(m_both), 4),
                "damping_share": round(float(damping_share), 3),
                "attribution": attribution,
                "A0_enr_dev_P1p": round(float(A0), 4), "A0_enr_fold_se": round(float(se_A0), 4),
                "note": "margins in exact-basis dev P1' (FDAC-aligned FRAC) over A0_enr; damping_share = "
                        "damping_only_margin / winner_margin; >=2/3 required to credit damping (S4)."}
    finalists = {"freeze": [scores[k]["cid"] for k in scores],
                 "labels": list(scores.keys()),
                 "cids": ["A0_enr", "A0d_enr", "c06_enr"],   # NUTS/Q targets (baseline + damping + best shape)
                 "scores": scores, "runtime_s": round(time.time() - t0, 1)}
    json.dump(finalists, open(os.path.join(WS, "out", "finalists.json"), "w"), indent=2)
    json.dump(ablation, open(os.path.join(WS, "out", "ablation.json"), "w"), indent=2)
    print("\n=== S4 ABLATION ===", flush=True)
    print(json.dumps(ablation, indent=2), flush=True)
    print(f"\nfinalize done in {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
