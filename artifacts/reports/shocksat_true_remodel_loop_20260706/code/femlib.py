#!/usr/bin/env python3
"""femlib — shared FE layer for the TRUE agentic remodel loop (20260706).

Reuses (imports, never edits) fe_core.py from the Card-D remesh workspace. Provides:
  - model dict load + per-PID/subset shell reassembly (V1 must reproduce the stored Card-D blocks),
  - TRUE conforming refinement (2x2 quad / 4x tria subdivision) with hanging-node MPC ties where a refined
    edge borders an unrefined element (transition treatment; validated by V2/V3),
  - physically correct thickness fields (pass scaled t to the SAME element routines: membrane ∝ t,
    bending ∝ t^3, mass ∝ t — separated by construction in fe_core; V4 validates),
  - added connectivity (generalized 6x6 springs between node pairs; RBE2 release -> spring),
  - full-order sparse eigensolve in the candidate's OWN space (reduced-basis-trap rule D2),
  - candidate Package (own-basis stiffness blocks per θ group, obs/sens/drive/tray rows, FROZEN Hungarian
    pairing at θ=1) + S0-form θ_MAP fit (train-side .ash only, D6).
All float64. Eigensolves are logged to out/eigensolve_log.jsonl (budget accounting D7).
"""
from __future__ import annotations
import json, os, sys, time
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh
from scipy.optimize import linear_sum_assignment, minimize

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.abspath(os.path.join(WS, "..", "..", ".."))
REMESH = os.path.join(ROOT, "artifacts/reports/shocksat_fem_remesh_20260618")
MATD = os.path.join(REMESH, "matrices")
PSD = os.path.join(ROOT, "artifacts/reports/shocksat_psd_envelope_twin_20260623/data")
NETCG_DATA = os.path.join(ROOT, "artifacts/reports/shocksat_netcg_method_selection_20260701/data/multiref_modal")
sys.path.insert(0, os.path.join(REMESH, "scripts"))
from fe_core import (quad_local_frames, qm6_membrane, mitc4_bending,   # noqa: E402
                     cst_membrane, dkt_bending, _q4_dN)

K6ROT = 100.0
G_IN_S2 = 386.0886
SIGMA_SHIFT = -1.0e3
NMODES = 80
BAND = (45.0, 260.0)
ZETA = 0.01
DF_FORBID = 0.18
AX = {"X": 0, "Y": 1, "Z": 2}
BAD_DAQ = {29, 30, 31, 101}                     # TestLog-flagged bad channels (realfrf convention)
GROUPS = json.load(open(os.path.join(PSD, "groups.json")))["groups"]
GNAMES = sorted(GROUPS)                          # 9 groups, sorted (reduce_model convention)
PID2GROUP = {p: g for g, ps in GROUPS.items() for p in ps}
FIXED_PIDS = ["bush_99"]
DRIVE_KEYS = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]   # dev loop drives (D4)
VAULT_KEY = "m_xy_990xy"                        # reserved vault (D1/D4) — rows precomputed, data untouched
NSIG_THETA = 0.25
SIG_W2 = 0.05                                    # S0 likelihood sd = 5% of target eigenvalue


def log_runtime(step, t_s, extra=None):
    rec = {"step": step, "t_s": round(float(t_s), 2), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
    if extra:
        rec.update(extra)
    with open(os.path.join(WS, "logs", "runtime_log.jsonl"), "a") as f:
        f.write(json.dumps(rec) + "\n")


def log_eigensolve(tag, cid, n_dof, t_s):
    with open(os.path.join(WS, "out", "eigensolve_log.jsonl"), "a") as f:
        f.write(json.dumps({"tag": tag, "cid": cid, "n_dof": int(n_dof),
                            "t_s": round(float(t_s), 1),
                            "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}) + "\n")


# ------------------------------------------------------------------ model dict
def load_model():
    """fem_model.npz -> mutable dict (lists where edits append)."""
    z = np.load(os.path.join(REMESH, "fem_model.npz"), allow_pickle=True)
    m = {k: z[k] for k in z.files}
    m["pshell"] = json.loads(str(z["pshell"]))
    m["pbush"] = json.loads(str(z["pbush"]))
    m["mat1"] = json.loads(str(z["mat1"]))
    m["cords"] = json.loads(str(z["cords"]))
    m["released_rbe2"] = []                      # eids of released spiders (connect family)
    m["extra_springs"] = []                      # [(ga, gb, kvals6, cid)]
    m["hanging"] = {}                            # dep gid -> (ga, gb) masters
    return m


def g2i_of(m):
    return {int(g): i for i, g in enumerate(m["gids"])}


# ------------------------------------------------------------------ shell assembly (subset-capable)
def assemble_shell(m, pid, qmask=None, tmask=None, t_scale=1.0):
    """K (full-space csr) + lumped Mdiag for the selected elements of `pid`.
    Follows assemble_fem.shell_K_M EXACTLY (V1 reproduces stored blocks at t_scale=1, full masks).
    t_scale multiplies the PHYSICAL thickness: membrane/shear ∝ t, bending ∝ t^3 (via fe_core), mass ∝ t."""
    g2i = g2i_of(m)
    xyz = np.asarray(m["xyz"], float)
    N = len(m["gids"]); NDOF = 6 * N
    p = m["pshell"][str(pid)]
    mat = m["mat1"][str(p["mid1"])]
    E, nu, G, rho = mat["E"], mat["nu"], mat["G"], mat["rho"]
    t = p["t"] * float(t_scale); br = p["bend_ratio"]; tst = p["ts_t"]
    q = np.asarray(m["cquad4"]); tri = np.asarray(m["ctria3"])
    qsel = (q[:, 1] == pid) if qmask is None else ((q[:, 1] == pid) & qmask)
    tsel = (tri[:, 1] == pid) if tmask is None else ((tri[:, 1] == pid) & tmask)
    rowsL, colsL, valsL = [], [], []
    Mdiag = np.zeros(NDOF)
    n_el = 0
    for kind, conn in (("q", q[qsel][:, 2:6]), ("t", tri[tsel][:, 2:5])):
        if len(conn) == 0:
            continue
        n_el += len(conn)
        nidx = np.vectorize(g2i.get)(conn)
        X = xyz[nidx]
        nn = X.shape[1]
        ne = len(X)
        Em = np.full(ne, E); num = np.full(ne, nu)
        if kind == "q":
            O, R, Xl2, warp = quad_local_frames(X)
            Km, area = qm6_membrane(Xl2, Em, num, np.full(ne, t))
            Kb = mitc4_bending(Xl2, Em, num, np.full(ne, G),
                               np.full(ne, t), np.full(ne, br), np.full(ne, tst))
        else:
            e1 = X[:, 1] - X[:, 0]
            e3 = np.cross(e1, X[:, 2] - X[:, 0])
            e3 /= np.linalg.norm(e3, axis=1, keepdims=True)
            e1 = e1 - (e1 * e3).sum(1, keepdims=True) * e3
            e1 /= np.linalg.norm(e1, axis=1, keepdims=True)
            e2 = np.cross(e3, e1)
            R = np.stack([e1, e2, e3], axis=1)
            O = X.mean(axis=1)
            Xl2 = np.einsum('eij,enj->eni', R, X - O[:, None, :])[..., :2]
            Km, area = cst_membrane(Xl2, Em, num, np.full(ne, t))
            Kb = dkt_bending(Xl2, Em, num, np.full(ne, t), np.full(ne, br))
        Kl = np.zeros((ne, 6 * nn, 6 * nn))
        mi = np.array([6 * a + c for a in range(nn) for c in (0, 1)])
        bi = np.array([6 * a + c for a in range(nn) for c in (2, 3, 4)])
        Kl[:, mi[:, None], mi[None, :]] += Km
        Kl[:, bi[:, None], bi[None, :]] += Kb
        # drilling penalty, rigid-rotation-invariant form (assemble_fem exactly)
        if kind == "q":
            dN0 = _q4_dN(0.0, 0.0)
            J = np.einsum('ka,eaj->ekj', dN0, Xl2)
            dN_xy = np.linalg.solve(J, np.broadcast_to(dN0, (ne, 2, nn)).copy())
            dNdx, dNdy = dN_xy[:, 0, :], dN_xy[:, 1, :]
        else:
            x1, y1 = Xl2[:, 0, 0], Xl2[:, 0, 1]
            x2, y2 = Xl2[:, 1, 0], Xl2[:, 1, 1]
            x3, y3 = Xl2[:, 2, 0], Xl2[:, 2, 1]
            A2 = (x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)
            dNdx = np.stack([y2 - y3, y3 - y1, y1 - y2], axis=1) / A2[:, None]
            dNdy = np.stack([x3 - x2, x1 - x3, x2 - x1], axis=1) / A2[:, None]
        Bw = np.zeros((ne, 6 * nn))
        Bw[:, 0::6] = -0.5 * dNdy
        Bw[:, 1::6] = 0.5 * dNdx
        kdr = K6ROT * 1e-6 * G * t * area / nn
        for a in range(nn):
            Ba = -Bw.copy()
            Ba[:, 6 * a + 5] += 1.0
            Kl += kdr[:, None, None] * np.einsum('ei,ej->eij', Ba, Ba)
        Kl4 = Kl.reshape(ne, 2 * nn, 3, 2 * nn, 3)
        Kg = np.einsum('eki,eakbl,elj->eaibj', R, Kl4, R).reshape(ne, 6 * nn, 6 * nn)
        dofs = (6 * nidx[..., None] + np.arange(6)).reshape(ne, -1)
        nd = 6 * nn
        rowsL.append(np.repeat(dofs, nd, axis=1).ravel())
        colsL.append(np.tile(dofs, (1, nd)).ravel())
        valsL.append(Kg.ravel())
        mtr = rho * t * area / nn
        mro = rho * t ** 3 / 12.0 * area / nn
        for a in range(nn):
            for c in range(3):
                np.add.at(Mdiag, 6 * nidx[:, a] + c, mtr)
            for c in range(3, 6):
                np.add.at(Mdiag, 6 * nidx[:, a] + c, mro)
    if not rowsL:
        return sp.csr_matrix((NDOF, NDOF)), Mdiag, 0
    K = sp.coo_matrix((np.concatenate(valsL),
                       (np.concatenate(rowsL), np.concatenate(colsL))),
                      shape=(NDOF, NDOF)).tocsr()
    return K, Mdiag, n_el


def skew(v):
    s = np.zeros((3, 3))
    s[0, 1], s[0, 2] = -v[2], v[1]
    s[1, 0], s[1, 2] = v[2], -v[0]
    s[2, 0], s[2, 1] = -v[1], v[0]
    return s


def bush_pairs_K(m, pairs):
    """Generalized 6x6 springs between node pairs: [(ga, gb, kvals6, cid)]. CBUSH midpoint convention."""
    g2i = g2i_of(m)
    xyz = np.asarray(m["xyz"], float)
    NDOF = 6 * len(m["gids"])
    rows, cols, vals = [], [], []
    for ga, gb, kvals, cid in pairs:
        ia, ib = g2i[int(ga)], g2i[int(gb)]
        xa, xb = xyz[ia], xyz[ib]
        P = 0.5 * (xa + xb)
        ra, rb = P - xa, P - xb
        R = np.eye(3) if cid == 0 else np.array(m["cords"][str(cid)]["R"])
        B = np.zeros((6, 12))
        B[0:3, 0:3] = -R
        B[0:3, 3:6] = R @ skew(ra)
        B[0:3, 6:9] = R
        B[0:3, 9:12] = -R @ skew(rb)
        B[3:6, 3:6] = -R
        B[3:6, 9:12] = R
        Ke = B.T @ np.diag(np.asarray(kvals, float)) @ B
        d = np.concatenate([6 * ia + np.arange(6), 6 * ib + np.arange(6)])
        rows.append(np.repeat(d, 12)); cols.append(np.tile(d, 12)); vals.append(Ke.ravel())
    if not rows:
        return sp.csr_matrix((NDOF, NDOF))
    return sp.coo_matrix((np.concatenate(vals),
                          (np.concatenate(rows), np.concatenate(cols))),
                         shape=(NDOF, NDOF)).tocsr()


def bush_pid_K(m, pid):
    sel = np.asarray(m["cbush"])[:, 1] == int(pid.split("_")[1]) if isinstance(pid, str) else \
        np.asarray(m["cbush"])[:, 1] == pid
    els = np.asarray(m["cbush"])[sel]
    kvals = m["pbush"][str(int(pid.split('_')[1]) if isinstance(pid, str) else pid)]["k"]
    return bush_pairs_K(m, [(ga, gb, kvals, cid) for _, _, ga, gb, cid in els])


# ------------------------------------------------------------------ T (RBE2 + hanging ties)
def build_T(m):
    """RBE2 elimination + hanging-node midpoint ties u_mid = (u_a+u_b)/2 (all 6 comps).
    One-level substitution if a hanging master is itself RBE2-dependent. Released spiders skipped."""
    g2i = g2i_of(m)
    xyz = np.asarray(m["xyz"], float)
    NDOF = 6 * len(m["gids"])
    released = set(int(e) for e in m.get("released_rbe2", []))
    dep_rows = {}
    ptr = 0
    for eid, gn, cm, nGM in np.asarray(m["rbe2"]):
        gms = np.asarray(m["rbe2_gms"])[ptr:ptr + nGM]; ptr += nGM
        if int(eid) in released:
            continue
        cmd = [int(c) - 1 for c in str(cm)]
        for gm in gms:
            for c in cmd:
                dof = 6 * g2i[int(gm)] + c
                assert dof not in dep_rows, f"DOF {dof} dependent twice"
                dep_rows[dof] = [(6 * g2i[int(gn)] + c, 1.0)]
                if c < 3:
                    r = xyz[g2i[int(gm)]] - xyz[g2i[int(gn)]]
                    S = skew(r)
                    for cc in range(3):
                        v = -S[c, cc]
                        if v != 0.0:
                            dep_rows[dof].append((6 * g2i[int(gn)] + 3 + cc, v))
    # hanging ties (substitute one level through RBE2 deps if needed)
    for gid_mid, (ga, gb) in m.get("hanging", {}).items():
        im = g2i[int(gid_mid)]
        for c in range(6):
            dof = 6 * im + c
            assert dof not in dep_rows
            terms = []
            for gmast in (ga, gb):
                md = 6 * g2i[int(gmast)] + c
                if md in dep_rows:
                    terms += [(d2, 0.5 * v2) for d2, v2 in dep_rows[md]]
                else:
                    terms.append((md, 0.5))
            dep_rows[dof] = terms
    dep = np.array(sorted(dep_rows), dtype=np.int64) if dep_rows else np.array([], np.int64)
    keep = np.setdiff1d(np.arange(NDOF), dep)
    colmap = -np.ones(NDOF, dtype=np.int64)
    colmap[keep] = np.arange(len(keep))
    rows = [keep]; cols = [colmap[keep]]; vals = [np.ones(len(keep))]
    for dof in dep:
        for d2, v2 in dep_rows[dof]:
            assert colmap[d2] >= 0, "chained dependency unresolved"
            rows.append([dof]); cols.append([colmap[d2]]); vals.append([v2])
    T = sp.coo_matrix((np.concatenate([np.asarray(v, float) for v in vals]),
                       (np.concatenate([np.asarray(r, np.int64) for r in rows]),
                        np.concatenate([np.asarray(c, np.int64) for c in cols]))),
                      shape=(NDOF, len(keep))).tocsr()
    return T, keep


# ------------------------------------------------------------------ TRUE refinement
def refine_region(m, pid_list, note=""):
    """Conforming 2x2 quad / 4x tria subdivision of ALL elements of the given pids. Edge midpoints shared;
    midpoints on edges bordering UNREFINED elements become hanging nodes tied by MPC (transition treatment).
    Mutates a COPY of the model dict; returns (m_new, info)."""
    m = dict(m)  # shallow; replaced keys re-assigned below
    gids = list(np.asarray(m["gids"]).tolist())
    xyz = [np.asarray(x, float) for x in np.asarray(m["xyz"])]
    g2i = {int(g): i for i, g in enumerate(gids)}
    gfile = list(np.asarray(m["gfile"]).tolist())
    q = np.asarray(m["cquad4"]); qf = np.asarray(m["cquad4_file"])
    tr = np.asarray(m["ctria3"]); tf = np.asarray(m["ctria3_file"])
    pidset = set(int(p) for p in pid_list)
    qsel = np.isin(q[:, 1], list(pidset))
    tsel = np.isin(tr[:, 1], list(pidset))
    # edge incidence over ALL shell elements (for hanging detection)
    def edges_of(conn):
        nn = conn.shape[1]
        return [frozenset((int(conn[e, a]), int(conn[e, (a + 1) % nn]))) for e in range(len(conn))
                for a in range(nn)]
    unref_edges = set()
    for conn, sel in ((q[:, 2:6], qsel), (tr[:, 2:5], tsel)):
        un = conn[~sel[:len(conn)]] if len(conn) else conn
        for e in range(len(un)):
            nn = un.shape[1]
            for a in range(nn):
                unref_edges.add(frozenset((int(un[e, a]), int(un[e, (a + 1) % nn]))))
    next_gid = max(gids) + 1
    edge_mid = {}
    ftag = str(qf[qsel][0]) if qsel.any() else (str(tf[tsel][0]) if tsel.any() else "refined")

    def coord(g):
        return xyz[g2i[int(g)]]

    def get_mid(ga, gb):
        nonlocal next_gid
        key = frozenset((int(ga), int(gb)))
        if key not in edge_mid:
            edge_mid[key] = next_gid
            gids.append(next_gid); xyz.append(0.5 * (coord(ga) + coord(gb)))
            gfile.append(ftag)
            g2i[next_gid] = len(gids) - 1
            next_gid += 1
        return edge_mid[key]

    new_q, new_qf = [], []
    next_eid = int(max(q[:, 0].max() if len(q) else 0, tr[:, 0].max() if len(tr) else 0)) + 1
    for k in np.where(qsel)[0]:
        eid, pid, n0, n1, n2, n3 = (int(x) for x in q[k])
        m01, m12, m23, m30 = get_mid(n0, n1), get_mid(n1, n2), get_mid(n2, n3), get_mid(n3, n0)
        cg = next_gid
        gids.append(cg); xyz.append(0.25 * (coord(n0) + coord(n1) + coord(n2) + coord(n3)))
        gfile.append(ftag); g2i[cg] = len(gids) - 1; next_gid += 1
        for sub in [(n0, m01, cg, m30), (m01, n1, m12, cg), (cg, m12, n2, m23), (m30, cg, m23, n3)]:
            new_q.append([next_eid, pid, *sub]); new_qf.append(str(qf[k])); next_eid += 1
    new_t, new_tf = [], []
    for k in np.where(tsel)[0]:
        eid, pid, n0, n1, n2 = (int(x) for x in tr[k])
        m01, m12, m20 = get_mid(n0, n1), get_mid(n1, n2), get_mid(n2, n0)
        for sub in [(n0, m01, m20), (m01, n1, m12), (m20, m12, n2), (m01, m12, m20)]:
            new_t.append([next_eid, pid, *sub]); new_tf.append(str(tf[k])); next_eid += 1
    # hanging = midpoint of an edge also carried by an unrefined element
    hanging = dict(m.get("hanging", {}))
    n_hang = 0
    for key, gid_mid in edge_mid.items():
        if key in unref_edges:
            ga, gb = sorted(key)
            hanging[int(gid_mid)] = (int(ga), int(gb))
            n_hang += 1
    m["gids"] = np.array(gids, dtype=np.asarray(m["gids"]).dtype)
    m["xyz"] = np.array(xyz, float)
    m["gfile"] = np.array(gfile, dtype=np.asarray(m["gfile"]).dtype)
    m["cquad4"] = np.vstack([q[~qsel], np.array(new_q, dtype=q.dtype)]) if new_q else q[~qsel]
    m["cquad4_file"] = np.concatenate([qf[~qsel], np.array(new_qf, dtype=qf.dtype)]) if new_qf else qf[~qsel]
    if new_t:
        m["ctria3"] = np.vstack([tr[~tsel], np.array(new_t, dtype=tr.dtype)])
        m["ctria3_file"] = np.concatenate([tf[~tsel], np.array(new_tf, dtype=tf.dtype)])
    else:
        m["ctria3"] = tr[~tsel]; m["ctria3_file"] = tf[~tsel]
    m["hanging"] = hanging
    info = dict(pids=sorted(pidset), n_quads_refined=int(qsel.sum()), n_trias_refined=int(tsel.sum()),
                n_new_grids=len(gids) - len(np.asarray(load_model()["gids"])) if False else None,
                n_hanging=n_hang, note=note)
    info["n_grids"] = len(gids)
    return m, info


# ------------------------------------------------------------------ full-order solve + package
def channels_map():
    """channel_map.csv (tap_impact) -> {daq:int -> (xyz tuple, axis letter)} (sign dropped: |H| scoring)."""
    import csv
    out = {}
    with open(os.path.join(PSD, "channel_map.csv")) as f:
        for r in csv.DictReader(f):
            if r["configuration"] != "tap_impact":
                continue
            ax = r["structural_axis"].lstrip("-")
            if ax not in AX:
                continue
            out[int(r["daq_channel"])] = ((float(r["x_in"]), float(r["y_in"]), float(r["z_in"])), ax)
    return out


def cache_meta():
    """Drive caches -> {key: {daq list, xyz, axis}} WITHOUT touching H1 (safe for package building)."""
    meta = {}
    for key in DRIVE_KEYS + [VAULT_KEY]:
        c = np.load(os.path.join(NETCG_DATA, key + ".npz"), allow_pickle=True)
        meta[key] = {"daq": [int(d) for d in c["daq"]],
                     "xyz": tuple(float(x) for x in c["xyz"]), "axis": str(c["axis"])}
    return meta


def nearest_dof_row(m, W, point, axletter):
    """Row of W = (T @ Ve) for the DOF nearest `point` on axis. W: (NDOF_full, n_el) dense."""
    xyz = np.asarray(m["xyz"], float)
    order = np.argsort(np.linalg.norm(xyz - np.asarray(point, float), axis=1))[:20]
    for nn in order:
        d = 6 * int(nn) + AX[axletter]
        row = np.asarray(W[d, :]).ravel()
        if np.abs(row).sum() > 0:
            return row
    raise KeyError(f"no live DOF near {point} axis {axletter}")


def drive_row(m, W, xyz_pt, axis):
    if axis == "XY":
        return nearest_dof_row(m, W, xyz_pt, "X") + nearest_dof_row(m, W, xyz_pt, "Y")
    return nearest_dof_row(m, W, xyz_pt, axis)


def participation_mask(sens_rows, frac=0.10):
    """D12a: modes whose sensor-participation rms < frac x median are UNOBSERVABLE (penalty artifacts,
    interior-local modes) and excluded from pairing — they are not evidence."""
    rms = np.linalg.norm(np.asarray(sens_rows), axis=0)
    return rms >= frac * np.median(rms)


def hungarian_pairing(freqs_el, ash_rows, live, mfreqs, mshapes_live, allowed=None):
    """Frozen 1:1 pairing (pairing.py conventions): maximize MAC, |df|/f > 0.18 forbidden.
    allowed: bool mask over model modes (D12a unobservable-mode exclusion)."""
    phi_fem = ash_rows[live, :]                          # (132, n_el)
    num = (mshapes_live @ phi_fem) ** 2
    den = (np.sum(mshapes_live ** 2, 1)[:, None] * np.sum(phi_fem ** 2, 0)[None, :])
    MAC = num / (den + 1e-300)
    DF = freqs_el[None, :] / mfreqs[:, None] - 1.0
    cost = -MAC.copy()
    cost[np.abs(DF) > DF_FORBID] = 1e3
    if allowed is not None:
        cost[:, ~np.asarray(allowed, bool)] = 1e3
    ri, ci = linear_sum_assignment(cost)
    pairs = []
    for it, jf in zip(ri, ci):
        if cost[it, jf] >= 1e3:
            continue
        pairs.append((int(it), int(jf), float(MAC[it, jf])))
    return pairs, MAC


def greedy_pairing(freqs_el, ash_rows, live, mfreqs, mshapes_live):
    """The FORBIDDEN greedy per-test argmax pairing (V5 demonstrates its churn; never used in scoring)."""
    phi_fem = ash_rows[live, :]
    num = (mshapes_live @ phi_fem) ** 2
    den = (np.sum(mshapes_live ** 2, 1)[:, None] * np.sum(phi_fem ** 2, 0)[None, :])
    MAC = num / (den + 1e-300)
    DF = freqs_el[None, :] / mfreqs[:, None] - 1.0
    MACg = MAC.copy(); MACg[np.abs(DF) > DF_FORBID] = -1
    return [(it, int(np.argmax(MACg[it])), float(MACg[it].max())) for it in range(len(mfreqs))
            if MACg[it].max() > 0]


class Package:
    """Own-basis candidate package. K(theta) = A_fix + sum_g theta_g A[g]; mass = I (M-orthonormal basis)."""

    def __init__(self, d):
        self.__dict__.update(d)

    @classmethod
    def load(cls, cid):
        z = np.load(os.path.join(WS, "data", "packages", f"{cid}.npz"), allow_pickle=True)
        d = {k: z[k] for k in z.files}
        d["free_names"] = [str(n) for n in d["free_names"]]
        d["cid"] = str(d["cid"])
        d["sens_daq"] = [int(x) for x in d["sens_daq"]]
        d["meta"] = json.loads(str(d["meta"]))
        d["drives"] = {k: d[f"drive_{k}"] for k in DRIVE_KEYS + [VAULT_KEY]}
        d["pairs"] = np.asarray(d["pairs"])
        return cls(d)

    def K(self, theta):
        return self.A_fix + np.einsum("g,gij->ij", np.asarray(theta, float), self.A)

    def modes(self, theta):
        lam, Q = np.linalg.eigh(self.K(theta))
        return np.sqrt(np.clip(lam, 1e-9, None)) / (2 * np.pi), Q

    def theta_map(self):
        """S0-form MAP (D6): lognormal prior sd 0.25; Gaussian on paired eigenvalues sd 5%%. .ash only.
        D12b: only pairs with MAC >= 0.3 enter the likelihood (spatial aliases are not frequency evidence)."""
        mfreqs = np.asarray(self.mfreqs, float)
        pairs = np.asarray(self.pairs)
        pairs = pairs[pairs[:, 2] >= 0.3]
        femk = pairs[:, 1].astype(int)
        tgt = (mfreqs[pairs[:, 0].astype(int)] * 2 * np.pi) ** 2
        var = (SIG_W2 * tgt) ** 2
        A = np.asarray(self.A); A_fix = np.asarray(self.A_fix)

        def nlp(lt):
            K = A_fix + np.einsum("g,gij->ij", np.exp(lt), A)
            lam = np.clip(np.linalg.eigvalsh(K), 1e-9, None)
            return 0.5 * np.sum((tgt - lam[femk]) ** 2 / var) + 0.5 * np.sum(lt ** 2) / NSIG_THETA ** 2

        # D19: multi-start (deterministic; .ash-only objective -> no dev leakage). Keep lowest NLP.
        rng = np.random.default_rng(20260706)
        starts = [np.zeros(len(self.free_names))] + \
                 [rng.normal(0.0, NSIG_THETA, len(self.free_names)) for _ in range(4)]
        best = None
        for x0 in starts:
            res = minimize(nlp, x0, method="L-BFGS-B", options=dict(maxiter=200))
            if best is None or res.fun < best.fun:
                best = res
        return np.exp(best.x), float(best.fun), bool(best.success)


def build_package(m, blocks, cid, tag, note=""):
    """Full-order eigensolve in the candidate's OWN space + own-basis projections + frozen pairing.
    blocks: {name: K_csr_full}; must include '_fixed_bush99'. M built from m via caller (passed in blocks
    meta) — here we take M_csr from blocks.pop('__M__')."""
    t0 = time.time()
    M = blocks.pop("__M__")
    T, keep = build_T(m)
    Ktot = None
    for name, Kb in blocks.items():
        Ktot = Kb if Ktot is None else Ktot + Kb
    Kr = (T.T @ (Ktot @ T)).tocsc()
    Mr = (T.T @ (M @ T)).tocsc()
    lam, V = eigsh(Kr, k=NMODES, M=Mr, sigma=SIGMA_SHIFT, which="LM")
    idx = np.argsort(lam); lam = lam[idx]; V = V[:, idx]
    n_rbm = int(np.sum(lam < (2 * np.pi * 10.0) ** 2))       # modes below 10 Hz = rigid (numerical RBMs
    # sit at 0.4-1.2 Hz from the drilling-penalty scale; first elastic is 54.6 Hz — 10 Hz is a safe split)-body
    Ve = V[:, 6:]
    freqs_el = np.sqrt(np.clip(lam[6:], 0, None)) / (2 * np.pi)
    dt = time.time() - t0
    log_eigensolve(tag, cid, Kr.shape[0], dt)
    # full-field dense basis ONCE: every projection below is sparse x dense (fast)
    W = np.asarray(T @ Ve)                                    # (NDOF_full, n_el)
    A = {}
    A_fix = None
    for name, Kb in blocks.items():
        Ab = W.T @ (Kb @ W)
        if name == "_fixed_bush99":
            A_fix = Ab
        else:
            A[name] = Ab
    free_names = sorted(A)
    # observation rows
    mm = np.load(os.path.join(REMESH, "measured_modes.npz"), allow_pickle=True)
    live = np.asarray(mm["measured"]).reshape(-1)
    mfreqs = np.asarray(mm["freqs"], float)
    msh = np.asarray(mm["shapes"], float).reshape(33, -1)[:, live]
    obs_dofs = np.load(os.path.join(MATD, "obs_dofs.npy"))    # 228 full-space DOFs (76 ash nodes x3)
    ash_rows = W[obs_dofs, :]                                 # (228, n_el)
    # sensor rows FIRST (needed for the D12a unobservable-mode pairing exclusion)
    chmap = channels_map()
    cmeta = cache_meta()
    all_daq = sorted(set(d for k in cmeta for d in cmeta[k]["daq"])
                     - BAD_DAQ)
    sens_daq, sens_rows = [], []
    for d in all_daq:
        if d not in chmap:
            continue
        pt, ax = chmap[d]
        try:
            sens_rows.append(nearest_dof_row(m, W, pt, ax))
            sens_daq.append(d)
        except KeyError:
            pass
    allowed = participation_mask(np.array(sens_rows))
    pairs, MAC = hungarian_pairing(freqs_el, ash_rows, live, mfreqs, msh, allowed=allowed)
    drives = {k: drive_row(m, W, cmeta[k]["xyz"], cmeta[k]["axis"]) for k in DRIVE_KEYS + [VAULT_KEY]}
    # tray selectors (netcg TRAY_Z convention, full-field via W)
    node_z = np.asarray(m["xyz"], float)[:, 2]
    tray_nodes = np.where(node_z >= 55.0)[0]
    tray = np.zeros((3, Ve.shape[1]))
    for a in range(3):
        tray[a] = W[6 * tray_nodes + a, :].sum(0)
    d = dict(cid=cid, free_names=free_names,
             A=np.stack([A[g] for g in free_names]), A_fix=A_fix,
             freqs_el=freqs_el, n_rbm=n_rbm, lam_all=lam,
             ash_rows=ash_rows, live=live, mfreqs=mfreqs,
             pairs=np.array([[p[0], p[1], p[2]] for p in pairs]),
             sens_daq=sens_daq, sens_rows=np.array(sens_rows),
             tray=tray, meta=json.dumps(dict(note=note, tag=tag, solve_s=round(dt, 1),
                                             n_dof=int(Kr.shape[0]), n_rbm=n_rbm)))
    for k, v in drives.items():
        d[f"drive_{k}"] = v
    os.makedirs(os.path.join(WS, "data", "packages"), exist_ok=True)
    np.savez_compressed(os.path.join(WS, "data", "packages", f"{cid}.npz"), **d)
    d["drives"] = drives
    d["meta"] = json.loads(d["meta"])
    return Package(d)


def baseline_blocks(m):
    """Stored Card-D blocks (inherited model) grouped to the 9 groups + fixed."""
    blocks = {}
    for g, pids in GROUPS.items():
        Kg = None
        for p in pids:
            Kp = sp.load_npz(os.path.join(MATD, f"K_{p}.npz"))
            Kg = Kp if Kg is None else Kg + Kp
        blocks[g] = Kg
    blocks["_fixed_bush99"] = sp.load_npz(os.path.join(MATD, "K_bush_99.npz"))
    blocks["__M__"] = sp.load_npz(os.path.join(MATD, "M.npz"))
    return blocks


def predict_logH(pkg, theta, dkey, fc):
    """log10|H| (n_sens, n_freq), accelerance g/lbf BEFORE the global gain. Viscous 2 z wi w convention.
    NO per-mode/per-channel fitting of any kind here."""
    f, Q = pkg.modes(theta)
    inb = np.where((f >= BAND[0] - 10) & (f <= BAND[1] + 40))[0]   # modal sum support incl. band edges
    Us = np.asarray(pkg.sens_rows) @ Q[:, inb]
    Ud = np.asarray(pkg.drives[dkey]) @ Q[:, inb]
    wi = 2 * np.pi * f[inb]
    w = 2 * np.pi * np.asarray(fc, float)
    D = wi[None, :] ** 2 - (w ** 2)[:, None] + 2j * ZETA * wi[None, :] * w[:, None]
    H = -(w ** 2)[None, :] * ((Us * Ud[None, :])[:, None, :] / D[None, :, :]).sum(-1)
    return np.log10(np.abs(H) / G_IN_S2 + 1e-300)
