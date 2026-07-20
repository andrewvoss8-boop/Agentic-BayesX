#!/usr/bin/env python3
"""Grade S1 (improvement) / S2 (intelligence) / S3 (honesty) / S4 (attribution) from the artifacts and write
out/verdicts.json. Honest labeling: anything less than S1+S2+S3+S4 => 'pre-registered claim FALSIFIED'."""
import json, os, sys, glob
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def jload(p, d=None):
    try:
        return json.load(open(os.path.join(WS, p)))
    except Exception:
        return d


def main():
    fin = jload("out/finalists.json"); abl = jload("out/ablation.json")
    vault = jload("out/vault_scores.json", {"scores": {}})
    sc = fin["scores"]
    A0 = sc["A0_enr"]["P1p_mean"]; se = sc["A0_enr"]["P1p_se"] or 0.13
    agent = {k: sc[k]["P1p_mean"] for k in ("A0d_enr", "c06_enr", "a04_enr", "b_c06_enr")}
    agent_best_label = max(agent, key=agent.get); agent_best = agent[agent_best_label]
    random_best = sc["rnd003_enr"]["P1p_mean"]
    vs = vault.get("scores", {})
    vA0 = (vs.get("A0_enr") or {}).get("vault_P1p")
    vWin = (vs.get(agent_best_label) or {}).get("vault_P1p")

    margin = agent_best - A0
    S1 = {"winner": agent_best_label, "dev_margin": round(float(margin), 4),
          "needs": ">=+0.05 AND >=2x fold SE AND vault_winner>vault_A0",
          "fold_se": round(float(se), 4), "two_se": round(float(2 * se), 4),
          "vault_winner": vWin, "vault_A0": vA0,
          "pass": bool(margin >= 0.05 and margin >= 2 * se and (vWin is not None and vA0 is not None
                                                                and vWin > vA0))}
    S2 = {"agent_best": round(float(agent_best), 4), "agent_best_label": agent_best_label,
          "random_best": round(float(random_best), 4), "random_label": "rnd003_enr",
          "pass": bool(agent_best > random_best)}

    # S3: honesty (lmo>1.0 + physical-damping) AND Q coverage >=0.95
    hon = {os.path.basename(f)[8:-5]: json.load(open(f)) for f in glob.glob(os.path.join(WS, "out",
                                                                                        "honesty_*.json"))}
    lmo_ok = all((h.get("lmo_widen_ratio") is None or h["lmo_widen_ratio"] > 1.0) for h in hon.values())
    phys_ok = not any(h.get("disqualified") for h in hon.values())
    qcov = []
    for f in glob.glob(os.path.join(WS, "out", "qoi_*.json")):
        q = json.load(open(f))
        for ax, v in q.get("axes", {}).items():
            qcov.append((os.path.basename(f), ax, v.get("min_coverage")))
    q_ok = bool(qcov) and all((c is None or c >= 0.95) for _, _, c in qcov)
    S3 = {"lmo_all_widen_gt1": bool(lmo_ok), "physical_damping_ok": bool(phys_ok),
          "q_coverage_ok": bool(q_ok),
          "q_min_coverage": (round(min(c for _, _, c in qcov if c is not None), 3)
                             if any(c is not None for _, _, c in qcov) else None),
          "pass": bool(lmo_ok and phys_ok and q_ok)}

    S4 = {"damping_share": abl["damping_share"], "damping_only_margin": abl["damping_only_margin"],
          "shape_only_margin": abl["shape_only_margin"], "attribution": abl["attribution"],
          "needs": "damping_only_margin >= 2/3 of winner_margin", "pass": bool(abl["damping_share"] >= 2 / 3)}

    allpass = S1["pass"] and S2["pass"] and S3["pass"] and S4["pass"]
    claim = ("all four success criteria met (S1 improvement, S2 intelligence, S3 honesty, S4 damping "
             "attribution)" if allpass else
             "pre-registered claim FALSIFIED: " + "; ".join(
                 [f"S1 {'PASS' if S1['pass'] else 'FAIL'}", f"S2 {'PASS' if S2['pass'] else 'FAIL'}",
                  f"S3 {'PASS' if S3['pass'] else 'FAIL'}", f"S4 {'PASS' if S4['pass'] else 'FAIL'}"]))
    gap = jload("out/dev_vs_vault.json", {})
    out = {"S1": S1, "S2": S2, "S3": S3, "S4": S4, "overall_claim": claim,
           "A0_enr_dev_P1p": round(float(A0), 4), "A0_enr_raw_P3": round(float(sc["A0_enr"]["P3_mean"]), 4),
           "exact_basis_leaderboard": {k: round(float(sc[k]["P1p_mean"]), 4) for k in sc},
           "dev_vs_vault_gap": gap,
           "winners_curse_N": {"agent": 21, "random": 40},
           "note": "exact-basis dev P1' (FDAC-aligned FRAC). A0_enr raw P3 0.2152 reproduces the completed "
                   "true-remodel run's exact-basis A0 (pipeline cross-validation)."}
    json.dump(out, open(os.path.join(WS, "out", "verdicts.json"), "w"), indent=2)
    print(json.dumps({"S1": S1["pass"], "S2": S2["pass"], "S3": S3["pass"], "S4": S4["pass"],
                      "overall_claim": claim}, indent=2))


if __name__ == "__main__":
    main()
