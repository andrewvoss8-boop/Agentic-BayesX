#!/usr/bin/env python3
"""A0 baseline build + score. A0 = inherited FEM, multi-start modal theta_MAP, FIXED zeta=1% (the bar).
Also previews A0 at the survey-median damping (zeta=0.32%) as an A0d-lite sanity check (NOT the fitted A0d).
Resumable: skips the eigensolve if the package exists. Launch detached (eigensolve)."""
import json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femdamp as D           # sets F.WS -> our workspace
import femlib as F
import score as SC

WS = D.WS
t0 = time.time()


def build_A0():
    pkgp = os.path.join(WS, "data", "packages", "A0.npz")
    if os.path.exists(pkgp):
        print("A0 package exists, skipping eigensolve"); return
    print("building A0 package (full-order eigensolve)...", flush=True)
    m = F.load_model()
    blocks = F.baseline_blocks(m)
    F.build_package(m, blocks, cid="A0", tag="baseline", note="inherited FEM (A0)")
    print("A0 package built", flush=True)


def main():
    build_A0()
    pkg = F.Package.load("A0")
    th, fun, ok = pkg.theta_map()
    json.dump({"theta": th.tolist(), "free_names": list(pkg.free_names), "nlp": fun, "success": bool(ok)},
              open(os.path.join(WS, "out", "theta_map_A0.json"), "w"), indent=1)
    print("A0 theta_MAP:", dict(zip(pkg.free_names, np.round(th, 3))), flush=True)
    # A0: fixed zeta = 1% (the bar); score off-budget (baseline, not a search query)
    recs = {}
    recs["A0"] = SC.score_candidate("A0", "baseline", damping={"kind": "fixed", "zeta": 0.01},
                                    theta_override=th, family="modal_only", ablation="baseline",
                                    rationale="inherited FEM, fixed zeta=1% (the bar)", enforce_budget=False)
    # A0d-lite preview: survey-median band zeta (NOT the fitted A0d; just isolates the zeta=1%->0.32% effect)
    recs["A0d_lite"] = SC.score_candidate("A0", "baseline",
                                          damping={"kind": "band", "zeta": [0.0032] * 4},
                                          theta_override=th, family="damping_preview", ablation="damping_only",
                                          rationale="A0 at survey-median zeta 0.32% (A0d preview)",
                                          enforce_budget=False)
    for k, r in recs.items():
        print(f"\n=== {k} ===")
        print(json.dumps({kk: r[kk] for kk in ("P1p_mean", "P3_mean", "P2p_mean", "alignment_gain",
                                               "P1p_folds")}, indent=1))
    json.dump({k: {kk: r[kk] for kk in ("P1p_mean", "P3_mean", "P2p_mean", "alignment_gain",
                                        "P1p_folds", "damping")} for k, r in recs.items()},
              open(os.path.join(WS, "out", "baseline_summary.json"), "w"), indent=1)
    print(f"\nbaseline done in {time.time()-t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
