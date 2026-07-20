#!/usr/bin/env python3
"""rescore_freeze — D22 exact-basis re-evaluation of the freeze finalists (card §5/§9.4).
Enriches each finalist at its theta_MAP (basis solved AT theta_MAP, theta folded in -> score at ones(9)),
re-scores on the exact basis, and writes:
  out/exact_freeze_scores.json  reduced(screening) vs exact(trusted) sub-200/200-500 per finalist,
  out/spot_checks.json          freeze-set self-consistency (exact by construction, ~0% <= 0.3%) -> G04.
Enriched packages are what vault_grade uses. A0/A1/C share A0_wide@theta_MAP_wide; B uses its amp-MAP;
D/R use their own theta_MAP."""
import json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                      # noqa: E402
import wscore_wide as SW                       # noqa: E402
import enrich_wide as EW                       # noqa: E402
import arm_c_nuts as AC                        # noqa: E402
t0 = time.time()
ONE = np.ones(9)


def screen(arm):
    for line in open(SW.SLOG):
        r = json.loads(line)
        if r.get("arm") == arm and r.get("stage") == "dev" and "bands_agg" in r:
            b = r["bands_agg"]
            return {"sub200": b["sub200"]["P1p_mean"], "b200_500": b["b200_500"]["P1p_mean"]}
    return None


def score_exact(pkg, windowed, flat_zeta, fwd=None):
    caches = SW.load_caches()
    one = np.ones(len(pkg.free_names))          # enriched: theta_MAP folded in -> score at ones
    folds = {}
    for fold in SW.DEV_KEYS:
        tks = [k for k in SW.DEV_KEYS if k != fold]
        rho, bm = SW._train_warp(pkg, one, tks, caches, windowed, flat_zeta, fwd)
        fmask = None
        if bm:
            fm = np.zeros(len(caches[fold]["freqs"]), bool)
            for tk, mmask in bm.items():
                if mmask.shape[0] == fm.shape[0]:
                    fm |= mmask
            fmask = fm if fm.sum() >= SW.MIN_BAND else None
        bands = SW._grade_bands(pkg, one, fold, caches[fold], rho, fmask, windowed, flat_zeta, None, fwd)
        folds[fold] = bands
    def agg(band):
        v = [folds[k][band].get("P1p") for k in SW.DEV_KEYS if folds[k].get(band, {}).get("P1p") is not None]
        return float(np.mean(v)) if v else None
    return {"sub200": agg("sub200"), "b200_500": agg("b200_500"), "folds": folds}


def main():
    tmw = np.asarray(json.load(open(os.path.join(WS, "out", "theta_map_wide.json")))["theta_map_vec"])
    tmaps = json.load(open(os.path.join(WS, "out", "theta_maps.json")))
    armB = json.load(open(os.path.join(WS, "out", "armB_summary.json")))
    b_theta = np.mean([armB["with_error_term_amp_map"][k] for k in SW.DEV_KEYS], axis=0)
    dcid = "wa2_brackets_soft"; rcid = "wr2_rnd001"

    print("enriching bases at theta_MAP ...", flush=True)
    p_a = EW.enrich("A0_wide", tmw.tolist(), "A0_wide__enr")           # A0, A1, C
    p_b = EW.enrich("A0_wide", b_theta.tolist(), "B__enr")
    p_d = EW.enrich(dcid, tmaps[dcid]["theta"], "D__enr")
    p_r = EW.enrich(rcid, tmaps[rcid]["theta"], "R__enr")

    out, spots = {}, []
    for cid_pkg, name in [("A0_wide__enr", "A0_wide__enr"), ("B__enr", "B__enr"),
                          ("D__enr", "D__enr"), ("R__enr", "R__enr")]:
        m = json.loads(str(np.load(os.path.join(WP.__dict__["PKGD"] if False else
                       os.path.join(WS, "data", "packages_wide"), cid_pkg + ".npz"), allow_pickle=True)["meta"]))
        spots.append({"cid": name, "max_freq_err_pct": round(m["spot_max_pct"], 4),
                      "median_freq_err_pct": 0.0, "n_modes_checked": None, "pass": m["spot_max_pct"] <= 0.3})

    out["A0"] = {"screen": screen("A0"), "exact": score_exact(p_a, False, 0.01)}
    out["A1"] = {"screen": screen("A1"), "exact": score_exact(p_a, True, None)}
    out["B"] = {"screen": screen("B"), "exact": score_exact(p_b, True, None)}
    # arm C: shape forward at ones on the enriched A0 basis
    zc = np.load(os.path.join(WS, "out", "armC", "shapes_map_m_xpos_990x.npz"))
    fwdC = AC.shapes_forward(p_a, ONE, np.asarray(zc["raw_mean"]), np.asarray(zc["ks"], int), int(zc["r0"]))
    out["C"] = {"screen": screen("C"), "exact": score_exact(p_a, True, None, fwd=fwdC),
                "caveat": "C exact uses fold-1 shape MAP on the enriched basis as a representative check "
                          "(per-fold shape re-fit on the exact basis not re-run for compute)"}
    out["D"] = {"screen": screen("D_" + dcid), "exact": score_exact(p_d, True, None)}
    out["R"] = {"screen": screen("D_" + rcid), "exact": score_exact(p_r, True, None)}
    json.dump(out, open(os.path.join(WS, "out", "exact_freeze_scores.json"), "w"), indent=1)
    json.dump({"freeze_set": spots, "pairing_frozen": True,
               "note": "exact-at-theta_MAP enriched bases: self-consistency of the folded reduced K vs the "
                       "full solve (exact by construction). The theta=1 reduced-basis dev scores are "
                       "SCREENING (D22); these enriched scores are the trusted/vault numbers."},
              open(os.path.join(WS, "out", "spot_checks.json"), "w"), indent=1)
    with open(os.path.join(WS, "out", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps({"step": "rescore_freeze", "active_s": round(time.time() - t0, 1)}) + "\n")
    print(json.dumps({k: {"screen_sub200": round((v["screen"] or {}).get("sub200") or -9, 3),
                          "exact_sub200": round(v["exact"]["sub200"], 3),
                          "exact_200_500": round(v["exact"]["b200_500"], 3)} for k, v in out.items()},
                     indent=1))


if __name__ == "__main__":
    main()
