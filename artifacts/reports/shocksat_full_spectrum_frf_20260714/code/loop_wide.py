#!/usr/bin/env python3
"""loop_wide — arm-D remodel loop driver with the amplitude compass (card §6 D).

Query = ONE candidate dev-scored on the 4 LODO folds (all bands). Budgets (G05): agent <= 80, random <= 80;
every dev query appends to out/query_log.jsonl. theta per candidate = femlib S0-form multi-start theta_MAP
(.ash survey only -> no dev leakage; >=5 deterministic starts, D19), cached in out/theta_maps.json.
Commands:
  score <spec.json path|cid> <track> <round>     build (if needed) + theta_MAP + dev score + query log
  random_round <round> <n> <seed>                n random-grammar candidates (actions.random_specs menu)
  spot <cid>                                     G04 exact-basis spot check (full solve at theta_MAP)
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np

WS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wide_package as WP                        # noqa: E402
import wide_candidates as WC                     # noqa: E402
import wscore_wide as SW                         # noqa: E402
ACT = WC.ACT
F = WP.F

QLOG = os.path.join(WS, "out", "query_log.jsonl")
TMAP = os.path.join(WS, "out", "theta_maps.json")


def q_count(track):
    if not os.path.exists(QLOG):
        return 0
    return sum(1 for line in open(QLOG) if line.strip() and json.loads(line).get("track") == track)


def q_done():
    done = set()
    if os.path.exists(QLOG):
        for line in open(QLOG):
            if line.strip():
                done.add(json.loads(line)["cid"])
    return done


def theta_map_cached(pkg):
    d = json.load(open(TMAP)) if os.path.exists(TMAP) else {}
    if pkg.cid in d:
        return np.asarray(d[pkg.cid]["theta"], float)
    t0 = time.time()
    theta, nlp, ok = pkg.theta_map()
    d[pkg.cid] = {"theta": np.asarray(theta, float).tolist(), "free_names": pkg.free_names,
                  "nlp": float(nlp), "ok": bool(ok), "t_s": round(time.time() - t0, 1)}
    json.dump(d, open(TMAP, "w"), indent=1)
    return np.asarray(theta, float)


def score_candidate(spec, track, rnd, seed=None):
    cid = spec["cid"]
    if cid in q_done():
        print(f"{cid}: already queried (resume-skip)")
        return None
    n = q_count(track)
    if n >= 80:
        raise RuntimeError(f"{track} budget exhausted ({n}/80)")
    pkg = WC.build(spec, track)
    theta = theta_map_cached(pkg)
    qoi_w = None
    qp = os.path.join(WS, "out", "qoi_sensor_weights.json")
    if os.path.exists(qp):
        qoi_w = {int(k): v for k, v in json.load(open(qp))["weights"].items()}
    rec = SW.score_dev_wide(f"D_{cid}", pkg, theta, note=f"loop {track} r{rnd}", qoi_w=qoi_w,
                            track=track, query_meta={"cid": cid, "round": rnd})
    q = {"track": track, "cid": cid, "round": rnd, "family": spec.get("family", ACT.classify(spec)[0]),
         "sub200_P1p": rec["bands_agg"]["sub200"]["P1p_mean"],
         "b200_500_P1p": rec["bands_agg"]["b200_500"]["P1p_mean"],
         "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if seed is not None:
        q["seed"] = seed
    with open(QLOG, "a") as f:
        f.write(json.dumps(q) + "\n")
    print(f"[{track} r{rnd}] {cid}: sub200 {q['sub200_P1p']:.4f}  200-500 {q['b200_500_P1p']}")
    return q


def random_round(rnd, n, seed):
    specs = ACT.random_specs(200, seed=seed)          # large pool, then filter buildable/first-n
    out = []
    for s in specs:
        if len(out) >= n:
            break
        s = dict(s)
        s["cid"] = f"wr{rnd}_{s['cid']}"
        try:
            q = score_candidate(s, "random", rnd, seed=seed)
            if q:
                out.append(q)
        except ValueError as e:                        # oversized/dud random draws are skipped, logged
            with open(os.path.join(WS, "out", "random_duds.jsonl"), "a") as f:
                f.write(json.dumps({"cid": s["cid"], "err": str(e)}) + "\n")
        except RuntimeError as e:
            print(str(e)); break
    return out


def spot_check(cid):
    """G04: full own-space solve at the candidate's theta_MAP; compare in-band (<=1000 Hz) frequencies."""
    pkg = WP.load(cid)
    theta = theta_map_cached(pkg)
    spec_p = os.path.join(WC.SPECD, f"{cid}.json")
    spec = json.load(open(spec_p)) if os.path.exists(spec_p) else {"cid": cid, "ops": []}
    if spec.get("ops"):
        m, blocks = WC.ACT.build_candidate(dict(spec), tag_track="spot", blocks_only=True)
    else:                                              # baseline A0_wide (no edits)
        m = F.load_model()
        blocks = F.baseline_blocks(m)
    M = blocks.pop("__M__")
    th_of = dict(zip(pkg.free_names, theta))
    Kth = blocks["_fixed_bush99"].copy()
    for g, Kb in blocks.items():
        if g != "_fixed_bush99":
            Kth = Kth + th_of[g] * Kb
    T, keep = F.build_T(m)
    from scipy.sparse.linalg import eigsh
    t0 = time.time()
    Kr = (T.T @ (Kth @ T)).tocsc()
    Mr = (T.T @ (M @ T)).tocsc()
    lam, _ = eigsh(Kr, k=WC.K_OWN, M=Mr, sigma=F.SIGMA_SHIFT, which="LM")
    lam = np.sort(lam)
    WC.log_eig("spot_check", cid, Kr.shape[0], time.time() - t0)
    f_full = np.sqrt(np.clip(lam, 0, None)) / (2 * np.pi)
    f_full = f_full[f_full >= 10.0]
    f_red = np.sort(pkg.modes(theta)[0])
    f_red = f_red[(f_red >= 10.0)]
    # compare only the SCORED band (<=500 Hz, D11 cap) where BOTH the fresh k=K_OWN full solve and the
    # reduced basis are fully converged; above ~550 Hz the k=200 solve truncates before the 209-mode basis,
    # so an element-wise edge comparison would be a truncation artifact, not a basis error.
    CMP_TOP = 500.0
    nn = min(int((f_full <= CMP_TOP).sum()), int((f_red <= CMP_TOP).sum()))
    rel = np.abs(f_red[:nn] / f_full[:nn] - 1.0)
    rec = {"cid": cid, "n_modes_checked": int(nn), "max_freq_err_pct": round(float(rel.max() * 100), 4),
           "median_freq_err_pct": round(float(np.median(rel) * 100), 4),
           "pass_0p3pct": bool(rel.max() <= 0.003)}
    p = os.path.join(WS, "out", "spot_checks_raw.jsonl")
    with open(p, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec))
    return rec


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "score":
        spec = json.load(open(sys.argv[2])) if os.path.exists(sys.argv[2]) else \
            json.load(open(os.path.join(WC.SPECD, sys.argv[2] + ".json")))
        score_candidate(spec, sys.argv[3], int(sys.argv[4]))
    elif cmd == "random_round":
        random_round(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    elif cmd == "spot":
        spot_check(sys.argv[2])
