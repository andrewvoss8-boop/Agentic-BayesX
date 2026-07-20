#!/usr/bin/env python3
"""pipeline — per-candidate EXACT scoring for the model-form pilot (card §3 scoring rule).

Per candidate (ALL classes, uniform):
  1. build model+blocks (mfops; existing ops delegate to the validated actions path)
  2. own-space sparse eigensolve k=200 at theta=1 (sigma=-1e3) -> package (frozen survey pairing)
  3. mech gates (6 RBMs, mass contract, liveness, geometry quality recorded at build)
  4. multi-start deterministic theta_MAP (femlib S0-form, survey .ash only -> fold-independent)
  5. SECOND own-space solve at theta_MAP with theta folded in (enrich; exact by construction)
  6. exact LODO score at theta=ones (windowed + measured survey zeta)
NO theta=1-basis score is ever recorded as a score. NO SAMPLER. NO VAULT.

Commands (one candidate per process — Card A D4 memory lesson; all stages package-level resumable):
  baseline   A0 reference rebuild: complexity_ref.json + baseline elastic freqs (liveness reference)
  repro      pipeline reproduction check on the study's wr2_rnd001 (contract Q4)
  one        process the first pending spec in out/pending_specs/ without a partial; prints ALL DONE
"""
from __future__ import annotations
import json
import os
import sys
import time
import traceback

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                  # noqa: E402
import mfops as MO                                   # noqa: E402

F, WC, WP = C.F, C.WC, C.WP
PENDD = os.path.join(C.MY_OUT, "pending_specs")
os.makedirs(PENDD, exist_ok=True)
K_OWN = 200
TMAP = os.path.join(C.MY_OUT, "theta_maps.json")
CREF = os.path.join(C.MY_OUT, "complexity_ref.json")
BFRQ = os.path.join(C.MY_OUT, "baseline_elastic_freqs.npy")
MASS_CAP = {"property_control": 10.0, "geometry": 0.5, "connectivity": 0.01,
            "mesh_density": 1.0, "element_formulation": 0.01}   # % |delta mass| by class
LIVENESS_PCT = 0.05
N_LIVE_MODES = 60


def solve_own(m, blocks_no_M, M, tag, cid, k=K_OWN):
    """Own-space eigensolve; returns (lam, V, T, n_dof, dt). Every solve logged."""
    Ktot = None
    for name, Kb in blocks_no_M.items():
        Ktot = Kb if Ktot is None else Ktot + Kb
    T, keep = MO.build_T_mf(m)
    t0 = time.time()
    Kr = (T.T @ (Ktot @ T)).tocsc()
    Mr = (T.T @ (M @ T)).tocsc()
    lam, V = eigsh(Kr, k=k, M=Mr, sigma=F.SIGMA_SHIFT, which="LM")
    idx = np.argsort(lam)
    lam, V = lam[idx], V[:, idx]
    dt = time.time() - t0
    C.log_eig(tag, cid, Kr.shape[0], dt)
    return lam, V, T, int(Kr.shape[0]), dt


def mass_x(M):
    return float(np.asarray(M.diagonal())[0::6].sum())


def build_theta1_pkg(spec, track):
    """Stage 2: theta=1 own-space package (resumable at package level)."""
    cid = spec["cid"]
    pkg_p = os.path.join(C.MY_PKGD, f"{cid}.npz")
    side_p = os.path.join(C.MY_OUT, "partials", f"{cid}.build.json")
    if os.path.exists(pkg_p) and os.path.exists(side_p):
        return WP.load(cid), json.load(open(side_p))
    m, blocks, info = MO.build_model_blocks(spec)
    M = blocks.pop("__M__")
    lam, V, T, n_dof, dt = solve_own(m, blocks, M, "own_theta1_k%d" % K_OWN, cid)
    n_rbm = int((lam < (2 * np.pi * 10.0) ** 2).sum())
    Ve = V[:, n_rbm:]
    W = np.asarray(T @ Ve)
    json.dump(spec, open(os.path.join(C.MY_SPECD, f"{cid}.json"), "w"), indent=1)
    pkg = WC._package_from_W(m, blocks, W, lam[n_rbm:], cid,
                             note=f"mf-pilot own-space k={K_OWN} ({track})",
                             extra_meta={"n_dof": n_dof, "n_rbm": n_rbm,
                                         "solve_s": round(dt, 1), "track": track,
                                         "cls": spec.get("cls")})
    side = {"n_dof": n_dof, "n_rbm": n_rbm, "solve_s_theta1": round(dt, 1),
            "mass_x": mass_x(M), "build_info": info,
            "n_params": len(pkg.free_names)}
    json.dump(side, open(side_p, "w"), indent=1)
    return pkg, side


def enrich_mf(spec, theta, free_names, out_cid):
    """Stage 5: exact-at-theta_MAP enrichment through MY builder (mirrors enrich_wide.enrich)."""
    pkg_p = os.path.join(C.MY_PKGD, f"{out_cid}.npz")
    if os.path.exists(pkg_p):
        return WP.load(out_cid)
    if spec.get("ops"):
        m, blocks, _ = MO.build_model_blocks(spec)
    else:
        m = F.load_model()
        blocks = F.baseline_blocks(m)
    M = blocks.pop("__M__")
    th_of = dict(zip(free_names, np.asarray(theta, float)))
    Kth = blocks["_fixed_bush99"].copy()
    for g, Kb in blocks.items():
        if g != "_fixed_bush99":
            Kth = Kth + th_of[g] * Kb
    T, keep = MO.build_T_mf(m)
    t0 = time.time()
    Kr = (T.T @ (Kth @ T)).tocsc()
    Mr = (T.T @ (M @ T)).tocsc()
    lam, V = eigsh(Kr, k=K_OWN, M=Mr, sigma=F.SIGMA_SHIFT, which="LM")
    idx = np.argsort(lam)
    lam, V = lam[idx], V[:, idx]
    dt = time.time() - t0
    C.log_eig("enrich_at_thetaMAP", out_cid, Kr.shape[0], dt)
    n_rbm = int((lam < (2 * np.pi * 10.0) ** 2).sum())
    Ve = V[:, n_rbm:]
    W = np.asarray(T @ Ve)
    freqs_el = np.sqrt(np.clip(lam[n_rbm:], 0, None)) / (2 * np.pi)
    A, A_fix = {}, None
    for name, Kb in blocks.items():
        Ab = W.T @ (Kb @ W)
        if name == "_fixed_bush99":
            A_fix = Ab
        else:
            A[name] = th_of[name] * Ab                # fold theta_MAP in -> evaluate at ones
    free2 = sorted(A)
    Kchk = A_fix + sum(A.values())
    f_red = np.sort(np.sqrt(np.clip(np.linalg.eigvalsh(Kchk), 1e-9, None)) / (2 * np.pi))
    nn = int((freqs_el <= 500).sum())
    rel = np.abs(np.sort(freqs_el)[:nn] / f_red[:nn] - 1.0)
    mm = np.load(os.path.join(F.REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1)
    mfreqs = np.asarray(mm["freqs"], float)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
    obs_dofs = np.load(os.path.join(F.MATD, "obs_dofs.npy"))
    ash_rows = W[obs_dofs, :]
    chmap = F.channels_map()
    cmeta = F.cache_meta()
    all_daq = sorted(set(d for kk in cmeta for d in cmeta[kk]["daq"]) - F.BAD_DAQ)
    sens_daq, sens_rows = [], []
    for dq in all_daq:
        if dq not in chmap:
            continue
        pt, ax = chmap[dq]
        try:
            sens_rows.append(F.nearest_dof_row(m, W, pt, ax))
            sens_daq.append(dq)
        except KeyError:
            pass
    allowed = F.participation_mask(np.array(sens_rows))
    pairs, _ = F.hungarian_pairing(freqs_el, ash_rows, live, mfreqs, msh, allowed=allowed)
    node_z = np.asarray(m["xyz"], float)[:, 2]
    tray_nodes = np.where(node_z >= 55.0)[0]
    tray = np.zeros((3, W.shape[1]))
    for a in range(3):
        tray[a] = W[6 * tray_nodes + a, :].sum(0)
    d = dict(cid=out_cid, free_names=free2, A=np.stack([A[g] for g in free2]), A_fix=A_fix,
             freqs_el=freqs_el, n_rbm=0, lam_all=lam[n_rbm:], ash_rows=ash_rows, live=live,
             mfreqs=mfreqs, pairs=np.array([[p[0], p[1], p[2]] for p in pairs]),
             sens_daq=sens_daq, sens_rows=np.array(sens_rows), tray=tray,
             meta=json.dumps(dict(note="mf-pilot exact-at-theta_MAP enrichment",
                                  base=spec.get("cid", "A0"), r=int(W.shape[1]),
                                  theta_map=list(map(float, theta)),
                                  spot_max_pct=float(rel.max() * 100),
                                  solve_s=round(dt, 1), n_rbm_solve=n_rbm)))
    for kk in F.DRIVE_KEYS + [F.VAULT_KEY]:
        d[f"drive_{kk}"] = F.drive_row(m, W, cmeta[kk]["xyz"], cmeta[kk]["axis"])
    np.savez_compressed(pkg_p, **d)
    return WP.load(out_cid)


def theta_map_cached(pkg):
    d = json.load(open(TMAP)) if os.path.exists(TMAP) else {}
    if pkg.cid in d:
        return np.asarray(d[pkg.cid]["theta"], float)
    t0 = time.time()
    theta, nlp, ok = pkg.theta_map()
    d[pkg.cid] = {"theta": np.asarray(theta, float).tolist(), "free_names": pkg.free_names,
                  "nlp": float(nlp), "ok": bool(ok), "n_starts": 5,
                  "t_s": round(time.time() - t0, 1)}
    json.dump(d, open(TMAP, "w"), indent=1)
    return np.asarray(theta, float)


def mech_check(spec, pkg, side):
    ref = json.load(open(CREF))
    bfr = np.load(BFRQ)
    fe = np.sort(np.asarray(pkg.freqs_el, float))
    n = min(N_LIVE_MODES, len(fe), len(bfr))
    shift = float(np.max(np.abs(fe[:n] / bfr[:n] - 1.0)) * 100)
    dm_pct = 100.0 * (side["mass_x"] - ref["mass_x"]) / ref["mass_x"]
    cap = MASS_CAP[spec["cls"]]
    checks = {"n_rbm": side["n_rbm"], "mass_delta_pct": round(dm_pct, 4),
              "max_mode_shift_pct": round(shift, 4)}
    ok = (side["n_rbm"] == 6 and abs(dm_pct) <= cap and shift >= LIVENESS_PCT)
    q = (side.get("build_info") or {}).get("quality")
    if q:
        checks["min_jac_ratio"] = q["min_jac_ratio"]
        checks["max_edge_slope"] = q["max_edge_slope"]
    checks["pass"] = bool(ok)
    if not ok:
        why = []
        if side["n_rbm"] != 6:
            why.append(f"n_rbm {side['n_rbm']} != 6")
        if abs(dm_pct) > cap:
            why.append(f"|dmass| {dm_pct:.3f}% > {cap}% ({spec['cls']})")
        if shift < LIVENESS_PCT:
            why.append(f"max mode shift {shift:.4f}% < {LIVENESS_PCT}% (numerical no-op)")
        checks["why"] = "; ".join(why)
    return checks


def do_candidate(spec):
    """Full pipeline for one spec; writes out/partials/<cid>.json (scored) or dud record."""
    cid = spec["cid"]
    t0 = time.time()
    pp = os.path.join(C.PARTD, f"{cid}.json")
    try:
        spec["cls"] = MO.cls_of(spec)
        pkg, side = build_theta1_pkg(spec, spec["track"])
        mech = mech_check(spec, pkg, side)
        if not mech["pass"]:
            raise ValueError(f"mech gate: {mech.get('why')}")
        theta = theta_map_cached(pkg)
        epkg = enrich_mf(spec, theta, pkg.free_names, f"{cid}__xenr")
        spot = float(epkg.meta.get("spot_max_pct"))
        agg, folds = C.score_exact(epkg)
        if any(agg[b] is None for b in ("sub200", "b200_500")):
            raise ValueError(f"null band aggregate {agg}")
        ref = json.load(open(CREF))
        rec = {"cid": cid, "track": spec["track"], "round": spec["round"], "cls": spec["cls"],
               "ops": [o["op"] for o in spec["ops"]],
               "basis": "exact_at_thetaMAP",
               "exact_sub200": agg["sub200"], "exact_b200_500": agg["b200_500"],
               "exact_folds": {f: folds[f]["sub200"] for f in C.DEV_KEYS},
               "exact_folds_b200_500": {f: folds[f]["b200_500"] for f in C.DEV_KEYS},
               "theta_map": [float(t) for t in theta],
               "enriched_pkg": f"{cid}__xenr", "spot_max_pct": spot,
               "n_dof": side["n_dof"],
               "delta_dof_pct": round(100.0 * (side["n_dof"] - ref["n_dof"]) / ref["n_dof"], 3),
               "n_params": side["n_params"], "mech": mech,
               "solve_s_theta1": side["solve_s_theta1"],
               "solve_s_enrich": float(epkg.meta.get("solve_s")),
               "wall_s": round(time.time() - t0, 1), "ts": C.now()}
        if spec.get("seed") is not None:
            rec["seed"] = spec["seed"]
        if spec.get("diagnosis_link"):
            rec["diagnosis_link"] = spec["diagnosis_link"]
        C.assert_finite({k: rec[k] for k in ("exact_sub200", "exact_b200_500")}, f"{cid}.agg")
        C.assert_finite(rec["exact_folds"], f"{cid}.folds")
        json.dump(rec, open(pp, "w"), indent=1)
        print(f"[{cid}] {spec['track']}/{spec['cls']}: exact sub200 {rec['exact_sub200']:+.4f} "
              f"(spot {spot:.2e}%, {rec['wall_s']:.0f}s)", flush=True)
    except Exception as ex:
        dud = {"cid": cid, "track": spec.get("track"), "round": spec.get("round"),
               "cls": spec.get("cls"), "reason": f"{type(ex).__name__}: {ex}",
               "traceback": traceback.format_exc()[-600:], "ts": C.now()}
        with open(os.path.join(C.MY_OUT, "duds.jsonl"), "a") as fh:
            fh.write(json.dumps(dud) + "\n")
        json.dump({"dud": True, **dud}, open(pp, "w"), indent=1)
        print(f"[{cid}] DUD: {dud['reason']}", flush=True)
    finally:
        C.flush_vault_guard(f"candidate_{cid}")


def cmd_baseline():
    if os.path.exists(CREF) and os.path.exists(BFRQ):
        print("baseline reference exists (resume-skip)")
        return
    t0 = time.time()
    m = F.load_model()
    blocks = F.baseline_blocks(m)
    M = blocks.pop("__M__")
    lam, V, T, n_dof, dt = solve_own(m, blocks, M, "baseline_ref_k%d" % K_OWN, "A0_ref")
    n_rbm = int((lam < (2 * np.pi * 10.0) ** 2).sum())
    fe = np.sqrt(np.clip(lam[n_rbm:], 0, None)) / (2 * np.pi)
    np.save(BFRQ, np.sort(fe))
    json.dump({"n_dof": n_dof, "solve_s_ref": round(dt, 1), "mass_x": mass_x(M),
               "n_rbm": n_rbm, "k": K_OWN, "ts": C.now()},
              open(CREF, "w"), indent=1)
    C.log_step("baseline_ref", time.time() - t0, n_dof=n_dof)
    print(f"baseline: n_dof {n_dof}, n_rbm {n_rbm}, solve {dt:.0f}s", flush=True)
    C.flush_vault_guard("baseline")


def cmd_repro():
    """Contract Q4: rebuild + enrich + score the study's wr2_rnd001 through THIS pipeline."""
    rp = os.path.join(C.MY_OUT, "repro_check.json")
    if os.path.exists(rp):
        print("repro exists (resume-skip)")
        return
    t0 = time.time()
    spec = json.load(open(os.path.join(C.STUDY, "out", "candidate_specs", "wr2_rnd001.json")))
    theta = json.load(open(os.path.join(C.STUDY, "out", "theta_maps.json")))["wr2_rnd001"]["theta"]
    spec = dict(spec)
    spec["cid"] = "wr2_rnd001_mfr"                     # avoid symlink collision; study spec verbatim
    m, blocks = C.ACT.build_candidate(dict(spec), tag_track="repro", blocks_only=True)
    M = blocks.pop("__M__")
    lam, V, T, n_dof, dt = solve_own(m, blocks, M, "repro_theta1", spec["cid"])
    n_rbm = int((lam < (2 * np.pi * 10.0) ** 2).sum())
    W = np.asarray(T @ V[:, n_rbm:])
    pkg = WC._package_from_W(m, blocks, W, lam[n_rbm:], spec["cid"],
                             note="repro rebuild of study wr2_rnd001 via mf pipeline",
                             extra_meta={"n_dof": n_dof, "n_rbm": n_rbm})
    epkg = enrich_mf(spec, theta, pkg.free_names, "wr2_rnd001_mfr__xenr")
    agg, folds = C.score_exact(epkg)
    out = {"cid": "wr2_rnd001_mfr", "mine_exact_sub200": agg["sub200"],
           "target": 0.16507158788301496, "tol": 0.01,
           "abs_diff": abs(agg["sub200"] - 0.16507158788301496),
           "folds": {f: folds[f]["sub200"] for f in C.DEV_KEYS},
           "spot_max_pct": float(epkg.meta.get("spot_max_pct")),
           "theta_source": "study theta_maps.json (verbatim, never re-optimized)",
           "wall_s": round(time.time() - t0, 1), "ts": C.now()}
    C.assert_finite({"mine": out["mine_exact_sub200"]}, "repro")
    json.dump(out, open(rp, "w"), indent=1)
    print(f"repro: mine {out['mine_exact_sub200']:.6f} vs target {out['target']:.6f} "
          f"(|diff| {out['abs_diff']:.2e}; bar 0.01)", flush=True)
    C.flush_vault_guard("repro")


def cmd_one():
    pend = sorted(fn for fn in os.listdir(PENDD) if fn.endswith(".json"))
    todo = [fn for fn in pend
            if not os.path.exists(os.path.join(C.PARTD, fn))]
    if not todo:
        print("ALL DONE (no pending specs without partials)", flush=True)
        return
    spec = json.load(open(os.path.join(PENDD, todo[0])))
    print(f"[{len(pend) - len(todo) + 1}/{len(pend)}] {spec['cid']}", flush=True)
    do_candidate(spec)
    print(f"{len(todo) - 1} pending", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "one"
    {"baseline": cmd_baseline, "repro": cmd_repro, "one": cmd_one}[cmd]()
