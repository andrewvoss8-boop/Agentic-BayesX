#!/usr/bin/env python3
"""Action space (card §5) — edit-spec grammar, candidate builder, and the uniform RANDOM sampler.

Grammar (one spec = {"cid","family","ops":[...],"rationale","evidence"}; ops applied in canonical order
refine -> thickness -> split -> connect -> scale). BOTH tracks (agent + random) use THIS grammar/menus.

ops:
  {"op":"refine",      "pids":[...]}                                  family 1 (true mesh refinement)
  {"op":"thickness",   "pids":[...], "t_scale":s, "name":...}         family 3 (physical t: mem∝t, bend∝t³, mass∝t)
  {"op":"split",       "pid":p, "rule":{...}, "name":...}             family 2 (own-θ sub-region block)
       rule: {"type":"z_band","zlo":..,"zhi":..} | {"type":"near_points","points":[[x,y,z],..],"radius":r}
             | {"type":"halfspace","axis":0|1|2,"cut":c,"side":"lo"|"hi"}
  {"op":"rbe2_soften", "eids":[...], "k_trans":kt, "k_rot":kr, "name":...}   family 4 (rigid tie -> compliant
       springs; restores the spider DOFs = kinematic-hypothesis change)
  {"op":"scale",       "group":g, "factor":f}                          family 5 (parametric; alone => parametric_only)

Solve rule (D2/D7): refine/thickness/rbe2_soften => OWN-SPACE full eigensolve; split/scale-only => inherited
(A0) basis reduced package, REQUIRING full-order spot-checks (<=0.3%) before their dev scores are trusted.
Every candidate records family tags; a candidate with only 'scale' ops is tagged parametric_only.
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import femlib as F

WS = F.WS
SHELL_PIDS = [101, 102, 103, 104, 105, 106, 201, 202, 203, 204, 205, 206,
              301, 302, 401, 501, 601, 701]
BIG_PIDS = [101, 102, 103, 201, 202, 203, 401, 501, 601, 701]
BUSH_PIDS = [801, 802, 803, 804, 805, 806, 807, 902]        # bush_99 fixed
GROUP_OF_SHELL = {p: F.PID2GROUP[f"shell_{p}"] for p in SHELL_PIDS}


def expand_csr(K, ndof_new):
    K = K.tocoo()
    return sp.coo_matrix((K.data, (K.row, K.col)), shape=(ndof_new, ndof_new)).tocsr()


def elem_centroids(m, pid):
    g2i = F.g2i_of(m)
    xyz = np.asarray(m["xyz"], float)
    q = np.asarray(m["cquad4"]); tr = np.asarray(m["ctria3"])
    qs = q[:, 1] == pid; ts = tr[:, 1] == pid
    cq = xyz[np.vectorize(g2i.get)(q[qs][:, 2:6])].mean(1) if qs.any() else np.zeros((0, 3))
    ct = xyz[np.vectorize(g2i.get)(tr[ts][:, 2:5])].mean(1) if ts.any() else np.zeros((0, 3))
    return qs, ts, cq, ct


def rule_mask(m, pid, rule):
    qs, ts, cq, ct = elem_centroids(m, pid)
    def pred(c):
        if rule["type"] == "z_band":
            return (c[:, 2] >= rule["zlo"]) & (c[:, 2] <= rule["zhi"])
        if rule["type"] == "near_points":
            pts = np.asarray(rule["points"], float)
            dmin = np.min(np.linalg.norm(c[:, None, :] - pts[None, :, :], axis=2), axis=1) \
                if len(c) and len(pts) else np.full(len(c), 1e9)
            return dmin <= rule["radius"]
        if rule["type"] == "halfspace":
            v = c[:, rule["axis"]]
            return v <= rule["cut"] if rule["side"] == "lo" else v >= rule["cut"]
        raise ValueError(rule["type"])
    qmask = np.zeros(len(np.asarray(m["cquad4"])), bool)
    tmask = np.zeros(len(np.asarray(m["ctria3"])), bool)
    if qs.any():
        qmask[np.where(qs)[0]] = pred(cq)
    if ts.any():
        tmask[np.where(ts)[0]] = pred(ct)
    return qmask, tmask


def rbe2_legs(m, eids):
    """(gn, gm) leg pairs for the listed RBE2 eids."""
    legs = []
    ptr = 0
    for eid, gn, cm, nGM in np.asarray(m["rbe2"]):
        gms = np.asarray(m["rbe2_gms"])[ptr:ptr + nGM]; ptr += nGM
        if int(eid) in set(int(e) for e in eids):
            legs += [(int(gn), int(gm)) for gm in gms]
    return legs


def classify(spec):
    fams = set()
    for op in spec["ops"]:
        fams.add({"refine": "refine", "thickness": "thickness", "split": "split",
                  "rbe2_soften": "connect", "scale": "scale"}[op["op"]])
    needs_full = bool(fams & {"refine", "thickness", "connect"})
    tag = "parametric_only" if fams == {"scale"} else "+".join(sorted(fams))
    return tag, needs_full


ORDER = {"refine": 0, "thickness": 1, "split": 2, "rbe2_soften": 3, "scale": 4}


def build_candidate(spec, tag_track, blocks_only=False):
    """spec -> Package (own-space full solve or inherited-basis reduced, per the solve rule).
    blocks_only=True: return (model_dict, blocks incl '__M__') without solving (enrichment reuse, D22)."""
    cid = spec["cid"]
    pkg_path = os.path.join(WS, "data", "packages", f"{cid}.npz")
    if os.path.exists(pkg_path) and not blocks_only:
        return F.Package.load(cid), classify(spec)[0]
    famtag, needs_full = classify(spec)
    m = F.load_model()
    ops = sorted(spec["ops"], key=lambda o: ORDER[o["op"]])
    NDOF0 = 6 * len(m["gids"])
    refined_pids = set()
    # ---- refine first (changes the mesh)
    # D16 size guard: a targeted refine adds 4x the refined quads; cap total refined quads at 8000 so a
    # pathological random draw (e.g. refining the whole 26k-quad top box -> ~1M DOF) fails fast as a dud
    # instead of hanging the queue. Agent's largest refine is 5664 quads (a11) -> unaffected.
    REFINE_QUAD_CAP = 8000
    _q = np.asarray(m["cquad4"])
    _n_refine = sum(int((_q[:, 1] == p).sum()) for op in ops if op["op"] == "refine" for p in op["pids"])
    if _n_refine > REFINE_QUAD_CAP:
        raise ValueError(f"{cid}: refine selects {_n_refine} quads > cap {REFINE_QUAD_CAP} "
                         f"(pathological/oversized remodel; dud)")
    for op in ops:
        if op["op"] == "refine":
            m, info = F.refine_region(m, op["pids"], note=cid)
            refined_pids |= set(int(p) for p in op["pids"])
    NDOF = 6 * len(m["gids"])
    # current per-shell-PID stiffness (stored padded, or reassembled if refined) + M bookkeeping
    Mcur = expand_csr(sp.load_npz(os.path.join(F.MATD, "M.npz")), NDOF)
    pid_K = {}
    excluded = set()                     # pids whose K moved wholly into an extra block
    for p in SHELL_PIDS:
        if p in refined_pids:
            m0 = F.load_model()
            _, Md_old, _ = F.assemble_shell(m0, p)
            Kn, Md_new, _ = F.assemble_shell(m, p)
            pad = np.zeros(NDOF); pad[:len(Md_old)] = Md_old
            Mcur = Mcur - sp.diags(pad).tocsr() + sp.diags(Md_new).tocsr()
            pid_K[p] = Kn
        else:
            pid_K[p] = expand_csr(sp.load_npz(os.path.join(F.MATD, f"K_shell_{p}.npz")), NDOF)
    extra = {}
    scale_f = {g: 1.0 for g in F.GNAMES}
    for op in ops:
        if op["op"] == "thickness":
            for p in op["pids"]:
                K1 = pid_K[p] if p in refined_pids else F.assemble_shell(m, p)[0]
                Ks, Md_s, _ = F.assemble_shell(m, p, t_scale=op["t_scale"])
                _, Md_1, _ = F.assemble_shell(m, p)
                name = op.get("name", f"t_{p}")
                extra[name] = extra.get(name, sp.csr_matrix((NDOF, NDOF))) + Ks
                Mcur = Mcur + sp.diags(Md_s - Md_1).tocsr()
                excluded.add(p)
        elif op["op"] == "split":
            p = op["pid"]
            qm, tm = rule_mask(m, p, op["rule"])
            if not (qm.any() or tm.any()):
                raise ValueError(f"{cid}: split rule selects no elements of pid {p}")
            Ksub, _, nsub = F.assemble_shell(m, p, qmask=qm, tmask=tm)
            name = op.get("name", f"s_{p}")
            extra[name] = extra.get(name, sp.csr_matrix((NDOF, NDOF))) + Ksub
            pid_K[p] = pid_K[p] - Ksub
            spec.setdefault("split_info", {})[name] = int(nsub)
        elif op["op"] == "rbe2_soften":
            legs = rbe2_legs(m, op["eids"])
            if not legs:
                raise ValueError(f"{cid}: no RBE2 legs for eids")
            m["released_rbe2"] = list(m.get("released_rbe2", [])) + [int(e) for e in op["eids"]]
            kv = [op["k_trans"]] * 3 + [op["k_rot"]] * 3
            name = op.get("name", "rbe2_soft")
            extra[name] = extra.get(name, sp.csr_matrix((NDOF, NDOF))) + \
                F.bush_pairs_K(m, [(ga, gb, kv, 0) for ga, gb in legs])
        elif op["op"] == "scale":
            scale_f[op["group"]] *= float(op["factor"])
    # group blocks
    blocks = {}
    for g in F.GNAMES:
        Kg = None
        for pref in F.GROUPS[g]:
            if pref.startswith("shell_"):
                p = int(pref.split("_")[1])
                if p in excluded:
                    continue
                Kp = pid_K[p]
            else:
                Kp = expand_csr(sp.load_npz(os.path.join(F.MATD, f"K_{pref}.npz")), NDOF)
            Kg = Kp if Kg is None else Kg + Kp
        if Kg is None:
            Kg = sp.csr_matrix((NDOF, NDOF))
        blocks[g] = Kg * scale_f[g] if scale_f[g] != 1.0 else Kg
    blocks.update(extra)
    blocks["_fixed_bush99"] = expand_csr(sp.load_npz(os.path.join(F.MATD, "K_bush_99.npz")), NDOF)
    blocks["__M__"] = Mcur
    if blocks_only:
        return m, blocks
    os.makedirs(os.path.join(WS, "out", "candidate_specs"), exist_ok=True)
    json.dump(spec, open(os.path.join(WS, "out", "candidate_specs", f"{cid}.json"), "w"), indent=1)
    if needs_full:
        pkg = F.build_package(m, blocks, cid, tag=tag_track, note=famtag)
    else:
        pkg = build_package_reduced(m, blocks, cid, note=famtag)
    return pkg, famtag


def build_package_reduced(m, blocks, cid, note=""):
    """Inherited-basis (A0) reduced package for split/scale-only candidates (D2: no mesh/DOF/connectivity
    change). Labeled reduced_inherited_basis; requires spot-check validation before dev scores are trusted."""
    t0 = time.time()
    M = blocks.pop("__M__")
    T = sp.load_npz(os.path.join(F.MATD, "T.npz"))
    Ve = np.asarray(np.load(os.path.join(F.MATD, "V_keep.npy"), mmap_mode="r")[:, 6:], float)
    A = {}
    A_fix = None
    for name, Kb in blocks.items():
        Kv = (T.T @ (Kb @ T)) @ Ve
        Ab = Ve.T @ Kv
        if name == "_fixed_bush99":
            A_fix = Ab
        else:
            A[name] = Ab
    free_names = sorted(A)
    a0 = F.Package.load("A0")
    K1 = A_fix + sum(A.values())
    lam, Q1 = np.linalg.eigh(K1)
    freqs_el = np.sqrt(np.clip(lam, 1e-9, None)) / (2 * np.pi)
    mm = np.load(os.path.join(F.REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1)
    mfreqs = np.asarray(mm["freqs"], float)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
    ash_rows = np.asarray(a0.ash_rows) @ Q1
    sens_rot = np.asarray(a0.sens_rows) @ Q1
    allowed = F.participation_mask(sens_rot)
    pairs, _ = F.hungarian_pairing(freqs_el, ash_rows, live, mfreqs, msh, allowed=allowed)
    d = dict(cid=cid, free_names=free_names,
             A=np.stack([Q1.T @ A[g] @ Q1 for g in free_names]),
             A_fix=Q1.T @ A_fix @ Q1,
             freqs_el=freqs_el, n_rbm=6, lam_all=np.concatenate([np.zeros(6), lam]),
             ash_rows=ash_rows, live=live, mfreqs=mfreqs,
             pairs=np.array([[p[0], p[1], p[2]] for p in pairs]),
             sens_daq=list(a0.sens_daq), sens_rows=np.asarray(a0.sens_rows) @ Q1,
             tray=np.asarray(a0.tray) @ Q1,
             meta=json.dumps(dict(note=note, tag="reduced_inherited_basis",
                                  build_s=round(time.time() - t0, 1))))
    for k in F.DRIVE_KEYS + [F.VAULT_KEY]:
        d[f"drive_{k}"] = np.asarray(a0.drives[k]) @ Q1
    np.savez_compressed(os.path.join(WS, "data", "packages", f"{cid}.npz"), **d)
    d["drives"] = {k: d[f"drive_{k}"] for k in F.DRIVE_KEYS + [F.VAULT_KEY]}
    d["meta"] = json.loads(d["meta"])
    return F.Package(d)


# ------------------------------------------------------------------ uniform RANDOM sampler (A2)
def random_specs(n, seed=20260706, full_solve_cap=32):
    """Uniform proposals from the SAME grammar/menus. No diagnosis, no learning (card §4.2)."""
    rng = np.random.default_rng(seed)
    m = F.load_model()
    rbe2_eids = [int(e) for e in np.asarray(m["rbe2"])[:, 0]]
    bushg = sorted(set(int(g) for row in np.asarray(m["cbush"])[:, 2:4] for g in row))
    xyz = np.asarray(m["xyz"], float)
    g2i = F.g2i_of(m)
    bush_pts = xyz[[g2i[g] for g in bushg]]
    zlo, zhi = xyz[:, 2].min(), xyz[:, 2].max()
    specs = []
    n_full = 0
    k = 0
    while len(specs) < n:
        k += 1
        fam = rng.choice(["refine", "split", "thickness", "connect", "scale", "combo"])
        ops = []

        def op_refine():
            return {"op": "refine",
                    "pids": [int(p) for p in rng.choice(SHELL_PIDS, size=rng.integers(1, 3),
                                                        replace=False)]}

        def op_split():
            p = int(rng.choice(BIG_PIDS))
            r = rng.integers(0, 3)
            if r == 0:
                z0 = rng.uniform(zlo, zhi - 5)
                rule = {"type": "z_band", "zlo": float(z0), "zhi": float(z0 + rng.uniform(3, 15))}
            elif r == 1:
                idx = rng.choice(len(bush_pts), size=min(4, len(bush_pts)), replace=False)
                rule = {"type": "near_points", "points": bush_pts[idx].tolist(),
                        "radius": float(rng.uniform(1.0, 4.0))}
            else:
                ax = int(rng.integers(0, 3))
                rule = {"type": "halfspace", "axis": ax,
                        "cut": float(rng.uniform(xyz[:, ax].min(), xyz[:, ax].max())),
                        "side": str(rng.choice(["lo", "hi"]))}
            return {"op": "split", "pid": p, "rule": rule, "name": f"rsplit{k}"}

        def op_thick():
            return {"op": "thickness",
                    "pids": [int(p) for p in rng.choice(SHELL_PIDS, size=rng.integers(1, 4),
                                                        replace=False)],
                    "t_scale": float(np.exp(rng.uniform(np.log(0.6), np.log(1.6)))),
                    "name": f"rthick{k}"}

        def op_conn():
            n_e = int(rng.integers(1, min(21, len(rbe2_eids))))
            return {"op": "rbe2_soften",
                    "eids": [int(e) for e in rng.choice(rbe2_eids, size=n_e, replace=False)],
                    "k_trans": float(10 ** rng.uniform(4, 7)),
                    "k_rot": float(10 ** rng.uniform(3, 6)), "name": f"rconn{k}"}

        def op_scale():
            return {"op": "scale", "group": str(rng.choice(F.GNAMES)),
                    "factor": float(np.exp(rng.uniform(np.log(0.5), np.log(2.0))))}

        menu = {"refine": op_refine, "split": op_split, "thickness": op_thick,
                "connect": op_conn, "scale": op_scale}
        if fam == "combo":
            for f2 in rng.choice(["refine", "split", "thickness", "connect", "scale"],
                                 size=2, replace=False):
                ops.append(menu[str(f2)]())
        else:
            ops.append(menu[str(fam)]())
        spec = {"cid": f"rnd{len(specs):03d}", "family": str(fam), "ops": ops,
                "rationale": "uniform random draw (A2 comparator)", "evidence": "none (random)"}
        tag, needs_full = classify(spec)
        if needs_full and n_full >= full_solve_cap:
            continue                       # respect the equal-compute solve allocation (D7)
        if needs_full:
            n_full += 1
        specs.append(spec)
    return specs
