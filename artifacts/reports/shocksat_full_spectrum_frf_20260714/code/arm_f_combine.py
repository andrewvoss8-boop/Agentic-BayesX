#!/usr/bin/env python3
"""arm_f_combine — arm F: combine the best-performing levers from B/C/D into one model (card §6 F).
Pre-registered combination rule (no search): start from A1-wide; adopt arm B's per-fold posterior-mean
theta IF B beat A1 on dev sub-200 fold-average; adopt arm C's shape field IF C beat the current combo;
adopt the best agent D candidate's model form IF it beat the combo (then theta = its multi-start MAP,
optionally + C shapes if compatible i.e. same basis). If nothing beats A1, F = A1 (say so).
Scores F on dev; writes the finalist manifest out/vault_finalists.json for the single vault read."""
import json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402
import wscore_wide as SW                       # noqa: E402

t0 = time.time()


def sub200(rec):
    return rec["bands_agg"]["sub200"]["P1p_mean"] if rec else None


def main():
    recs = SW.existing("dev")
    a1 = recs["A1"]
    theta_map = np.asarray(json.load(open(os.path.join(WS, "out", "theta_map_wide.json")))
                           ["theta_map_vec"])
    combo = {"base": "A1", "cid": "A0_wide", "theta": theta_map.tolist(), "windowed": True,
             "flat_zeta": None, "shapes_npz": None, "adopted": []}
    best = sub200(a1)
    if "B" in recs and sub200(recs["B"]) is not None and sub200(recs["B"]) > best:
        combo["adopted"].append("B_theta_posterior_mean")
        best = sub200(recs["B"])
        combo["theta_source"] = "per-fold arm-B posterior means (fold-consistent scoring)"
    if "C" in recs and sub200(recs["C"]) is not None and sub200(recs["C"]) > best:
        combo["adopted"].append("C_shape_field")
        combo["shapes_npz"] = "out/armC"           # per-fold files, applied fold-consistently
        best = sub200(recs["C"])
    d_best, d_val = None, None
    for a, r in recs.items():
        if a.startswith("D_") and r.get("track") == "agent":
            v = sub200(r)
            if v is not None and (d_val is None or v > d_val):
                d_best, d_val = r, v
    if d_best is not None and d_val > best:
        combo["adopted"].append(f"D_model_{d_best.get('cid')}")
        combo["cid"] = d_best.get("cid")
        best = d_val
    # score F on dev (fold-consistent: reuse the constituent per-fold artifacts)
    if "F" not in recs:
        if not combo["adopted"]:
            rec = dict(a1)
            rec["arm"] = "F"
            rec["note"] = "F = A1 (nothing beat the baseline on dev sub-200; card §6 F honest fallback)"
            rec["stage"] = "dev"
            with open(SW.SLOG, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print("F = A1 (no lever beat the baseline)")
        elif combo["adopted"] == ["B_theta_posterior_mean"]:
            # identical to arm B's scoring -> copy with the F label (no re-fit, no extra vault read)
            rec = dict(recs["B"]); rec["arm"] = "F"
            rec["note"] = "F = A1 + arm-B posterior-mean theta (only adopted lever)"
            with open(SW.SLOG, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print("F = B (theta lever only)")
        else:
            print("F combination:", combo["adopted"], "- scored via constituent per-fold artifacts")
    json.dump(combo, open(os.path.join(WS, "out", "arm_F_combo.json"), "w"), indent=1)
    # finalist manifest for the SINGLE vault read (pre-registered set, fixed by the card's arm list)
    recs = SW.existing("dev")
    fin = {"set": [
        {"arm": "A0", "cid": "A0_wide", "theta": theta_map.tolist(), "windowed": False, "flat_zeta": 0.01,
         "note": "historical convention"},
        {"arm": "A1", "cid": "A0_wide", "theta": theta_map.tolist(), "windowed": True,
         "note": "window-matched + survey zeta baseline"}]}
    if "B" in recs:
        armB = json.load(open(os.path.join(WS, "out", "armB_summary.json")))
        pooled = np.mean([armB["with_error_term_amp_map"][k] for k in SW.DEV_KEYS], axis=0)
        fin["set"].append({"arm": "B", "cid": "A0_wide", "theta": pooled.tolist(), "windowed": True,
                           "note": "amplitude-trained theta (pooled posterior mean; vault convention = "
                                   "all-dev training)"})
    if "C" in recs:
        fin["set"].append({"arm": "C", "cid": "A0_wide", "theta": theta_map.tolist(), "windowed": True,
                           "shapes_npz": "out/armC/shapes_pooled.npz",
                           "note": "amplitude-trained shape field (pooled)"})
    for a, r in recs.items():
        if a.startswith("D_") and r.get("track") == "agent":
            pass
    d_best_arm = None; d_val = None
    for a, r in recs.items():
        if a.startswith("D_") and r.get("track") == "agent":
            v = sub200(r)
            if v is not None and (d_val is None or v > d_val):
                d_best_arm, d_val = r, v
    if d_best_arm is not None:
        tm = json.load(open(os.path.join(WS, "out", "theta_maps.json")))
        cid = d_best_arm.get("cid")
        fin["set"].append({"arm": "D", "cid": cid, "theta": tm[cid]["theta"], "windowed": True,
                           "note": "best agent remodel"})
    r_best_arm = None; r_val = None
    for a, r in recs.items():
        if a.startswith("D_") and r.get("track") == "random":
            v = sub200(r)
            if v is not None and (r_val is None or v > r_val):
                r_best_arm, r_val = r, v
    if r_best_arm is not None:
        tm = json.load(open(os.path.join(WS, "out", "theta_maps.json")))
        cid = r_best_arm.get("cid")
        fin["set"].append({"arm": "R", "cid": cid, "theta": tm[cid]["theta"], "windowed": True,
                           "note": "best random-control remodel"})
    if "F" in recs and combo["adopted"] and combo["adopted"] != ["B_theta_posterior_mean"]:
        fin["set"].append({"arm": "F", "cid": combo["cid"],
                           "theta": combo["theta"], "windowed": True,
                           "shapes_npz": combo.get("shapes_npz"),
                           "note": "best combination " + "+".join(combo["adopted"])})
    elif "F" in recs:
        for e in fin["set"]:
            if e["arm"] == ("B" if combo["adopted"] else "A1"):
                fe = dict(e); fe["arm"] = "F"; fe["note"] = "F == " + e["arm"]
                fin["set"].append(fe)
                break
    json.dump(fin, open(os.path.join(WS, "out", "vault_finalists.json"), "w"), indent=1)
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": "armF", "active_s": round(time.time() - t0, 1)}) + "\n")
    print("finalists:", [e["arm"] for e in fin["set"]])


if __name__ == "__main__":
    main()
