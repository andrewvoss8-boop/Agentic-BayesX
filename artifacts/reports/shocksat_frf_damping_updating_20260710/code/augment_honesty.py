#!/usr/bin/env python3
"""Write per-FINALIST-LABEL honesty JSONs merging (a) the leave-modes-out widen ratio from the package's
qoi honesty run with (b) the physical-damping audit of the finalist's damping spec (zeta_min/max, eta_max,
damping_dim, disqualified). The checker reads honesty_*.json for BOTH the lmo gate and the physical-damping /
damping-dim gates. A finalist whose inferred damping breaches zeta in [0.2%,5%] or eta<=0.2 is DISQUALIFIED."""
import json, os, sys, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femdamp as D
WS = D.WS
Z_LO, Z_HI, ETA_HI = D.ZETA_LO, D.ZETA_HI, D.ETA_HI


def zeta_bounds(dmp):
    k = dmp.get("kind", "fixed")
    if k == "fixed":
        z = [float(dmp.get("zeta", 0.01))]
    elif k == "band":
        z = [float(x) for x in dmp["zeta"]]
    elif k == "rayleigh":
        w = 2 * np.pi * np.array([54.2, 256.8])
        z = list(dmp["alpha"] / (2 * w) + dmp["beta"] * w / 2)
    else:
        z = [0.01]
    eta = max([float(v) for v in dmp.get("eta", {}).values()] + [0.0])
    return float(min(z)), float(max(z)), eta


def main():
    fin = json.load(open(os.path.join(WS, "out", "finalists.json")))
    sc = fin["scores"]
    # map finalist label -> package cid
    lmo_of = {}
    for f in glob.glob(os.path.join(WS, "out", "honesty_*.json")):
        d = json.load(open(f))
        # only the qoi-written package-keyed files carry lmo_widen_ratio + no damping fields
        if "lmo_widen_ratio" in d and "damping_dim" not in d:
            lmo_of[os.path.basename(f)[8:-5]] = d.get("lmo_widen_ratio")
    for label, s in sc.items():
        cid = s["cid"]; dmp = s["damping"]
        zmn, zmx, emx = zeta_bounds(dmp)
        dq = bool(zmn < Z_LO or zmx > Z_HI or emx > ETA_HI)
        out = {"cid_label": label, "package": cid,
               "lmo_widen_ratio": lmo_of.get(cid),
               "zeta_min": round(zmn, 5), "zeta_max": round(zmx, 5), "eta_max": round(emx, 5),
               "damping_dim": int(D.damping_dim(dmp)), "disqualified": dq,
               "is_winner_or_baseline": True,
               "note": "physical-damping gate zeta in [0.2%,5%], eta<=0.2; a 'win' breaching these is "
                       "DISQUALIFIED as an amplitude-fit in disguise."}
        json.dump(out, open(os.path.join(WS, "out", f"honesty_{label}.json"), "w"), indent=1)
        print(f"  honesty_{label}: lmo={out['lmo_widen_ratio']} zeta[{zmn:.4f},{zmx:.4f}] eta{emx:.3f} "
              f"dim{out['damping_dim']} DQ={dq}", flush=True)
    # remove package-keyed qoi honesty files that are not finalist labels (avoid duplicates lacking damping)
    labels = set(sc.keys())
    for f in glob.glob(os.path.join(WS, "out", "honesty_*.json")):
        name = os.path.basename(f)[8:-5]
        d = json.load(open(f))
        if name not in labels and "damping_dim" not in d:
            os.remove(f)


if __name__ == "__main__":
    main()
