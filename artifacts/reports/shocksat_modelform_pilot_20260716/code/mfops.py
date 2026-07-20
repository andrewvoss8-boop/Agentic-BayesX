#!/usr/bin/env python3
"""mfops — model-form operators for the pilot (Card C §2). Builds ONLY on the validated true-remodel
grammar (reused read-only) + the card's minimal NEW operators, each V-gated before any scored use:

  rbe3_convert  (connectivity)        rigid spider -> interpolation constraint (linearized RBE3):
                                      the RBE2 is RELEASED and the reference node's 6 DOFs become the
                                      weighted least-squares rigid fit of the master translations.
                                      Pure constraint change: K blocks untouched, T changes.
  formulation   (element_formulation) per-PID bending formulation change via the exposed fe_core knobs:
                                      Db ∝ bend_ratio (plate bending rigidity multiplier), Ds ∝ ts_t
                                      (transverse-shear factor; 5/6 = Mindlin default, large -> Kirchhoff
                                      limit). Stiffness-only (t unchanged => mass unchanged).
  warp_panel    (geometry)            impose a bubble-shaped out-of-plane warp on a FLAT panel
                                      (zero at the panel boundary); mass/stiffness reassembled from the
                                      moved coordinates for every touched PID.
  joint_offset  (geometry)            translate a joint/bracket interface node set (spider nodes + all
                                      nodes within R_JOINT of the spider reference) by a small vector.

Existing validated ops (refine, thickness, rbe2_soften, scale) delegate UNCHANGED to
actions.build_candidate(blocks_only=True). No cross-class combos (pre-registered).

build_T_mf extends femlib.build_T with RBE3 dependency rows; vgate_tbuilder requires EXACT equivalence
(max|dT| = 0, same kept DOFs) on the baseline model before any scored use.
"""
from __future__ import annotations
import os
import sys

import numpy as np
import scipy.sparse as sp

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _common as C                                  # noqa: E402

F, ACT = C.F, C.ACT

EXISTING_OPS = {"refine", "thickness", "rbe2_soften", "scale"}
NEW_OPS = {"rbe3_convert", "formulation", "warp_panel", "joint_offset"}
OP2CLS = {"rbe2_soften": "connectivity", "rbe3_convert": "connectivity",
          "refine": "mesh_density", "formulation": "element_formulation",
          "warp_panel": "geometry", "joint_offset": "geometry",
          "thickness": "property_control", "scale": "property_control"}
FLAT_PANEL_PIDS = {102, 106, 202, 206, 401, 701}     # rms plane deviation = 0 (assumptions_ledger)
WARP_AMP_CAP_IN = 0.25                               # |amp| <= min(2 t_pid, 0.25) inch
JOINT_D_CAP_IN = 0.35                                # |vec| <= 0.35 inch (~1 element edge)
R_JOINT = 0.75                                       # inch, full-displacement core radius
R_BLEND = 3.0                                        # inch, cosine taper to zero (D2 fix)
BR_RANGE = (0.7, 1.4)
TS_T_MENU = (0.35, 5.0 / 6.0, 5.0)
JAC_RATIO_MIN = 0.2
EDGE_SLOPE_MAX = 0.35
RBE3_COND_MAX = 1e10


def cls_of(spec):
    cs = {OP2CLS[o["op"]] for o in spec["ops"]}
    if len(cs) != 1:
        raise ValueError(f"{spec.get('cid')}: cross-class combo {sorted(cs)} (forbidden this pilot)")
    return cs.pop()


# ------------------------------------------------------------------ RBE3 (interpolation constraint)
def rbe3_maps(m, eids):
    """[(gn, gms, C)] with C (6, 3*n_masters): reference [u_R; th_R] = C @ stack(master translations).
    Uniform weights; linearized rigid LS fit q = argmin sum_i |u_i - (u_R + th_R x r_i)|^2 (exact for
    rigid fields by construction). Singular geometry (collinear masters) -> ValueError (dud)."""
    g2i = F.g2i_of(m)
    xyz = np.asarray(m["xyz"], float)
    want = set(int(e) for e in eids)
    out = []
    ptr = 0
    for eid, gn, cm, nGM in np.asarray(m["rbe2"]):
        gms = np.asarray(m["rbe2_gms"])[ptr:ptr + nGM]
        ptr += nGM
        if int(eid) not in want:
            continue
        xR = xyz[g2i[int(gn)]]
        Ps = []
        for gm in gms:
            r = xyz[g2i[int(gm)]] - xR
            P = np.zeros((3, 6))
            P[:, :3] = np.eye(3)
            P[:, 3:] = -F.skew(r)
            Ps.append(P)
        A = sum(P.T @ P for P in Ps)
        cond = np.linalg.cond(A)
        if not np.isfinite(cond) or cond > RBE3_COND_MAX:
            raise ValueError(f"rbe3_convert eid {int(eid)}: singular master geometry (cond {cond:.2e})")
        Ainv = np.linalg.inv(A)
        Cm = np.hstack([Ainv @ P.T for P in Ps])              # (6, 3n)
        out.append((int(gn), [int(g) for g in gms], Cm))
    if len(out) != len(want):
        raise ValueError(f"rbe3_convert: eids not all found ({len(out)}/{len(want)})")
    return out


def build_T_mf(m):
    """femlib.build_T (verbatim construction) + RBE3 dependency rows. vgate_tbuilder proves EXACT
    equivalence with femlib.build_T when m has no 'rbe3' entries."""
    g2i = F.g2i_of(m)
    xyz = np.asarray(m["xyz"], float)
    NDOF = 6 * len(m["gids"])
    released = set(int(e) for e in m.get("released_rbe2", []))
    dep_rows = {}
    ptr = 0
    for eid, gn, cm, nGM in np.asarray(m["rbe2"]):
        gms = np.asarray(m["rbe2_gms"])[ptr:ptr + nGM]
        ptr += nGM
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
                    S = F.skew(r)
                    for cc in range(3):
                        v = -S[c, cc]
                        if v != 0.0:
                            dep_rows[dof].append((6 * g2i[int(gn)] + 3 + cc, v))
    # RBE3 reference-node rows (one-level substitution through RBE2 deps of masters)
    for gn, gms, Cm in m.get("rbe3", []):
        for c in range(6):
            dof = 6 * g2i[int(gn)] + c
            assert dof not in dep_rows, f"RBE3 reference DOF {dof} already dependent"
            terms = []
            for j, gm in enumerate(gms):
                for cc in range(3):
                    v = float(Cm[c, 3 * j + cc])
                    if v == 0.0:
                        continue
                    md = 6 * g2i[int(gm)] + cc
                    if md in dep_rows:
                        terms += [(d2, v * v2) for d2, v2 in dep_rows[md]]
                    else:
                        terms.append((md, v))
            dep_rows[dof] = terms
    # hanging ties (verbatim femlib logic; substitute one level through existing deps)
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
    rows = [keep]
    cols = [colmap[keep]]
    vals = [np.ones(len(keep))]
    for dof in dep:
        for d2, v2 in dep_rows[dof]:
            assert colmap[d2] >= 0, "chained dependency unresolved"
            rows.append([dof])
            cols.append([colmap[d2]])
            vals.append([v2])
    T = sp.coo_matrix((np.concatenate([np.asarray(v, float) for v in vals]),
                       (np.concatenate([np.asarray(r, np.int64) for r in rows]),
                        np.concatenate([np.asarray(c, np.int64) for c in cols]))),
                      shape=(NDOF, len(keep))).tocsr()
    return T, keep


# ------------------------------------------------------------------ geometry helpers
def panel_frame(m, pid):
    g2i = F.g2i_of(m)
    xyz = np.asarray(m["xyz"], float)
    q = np.asarray(m["cquad4"])
    tr = np.asarray(m["ctria3"])
    nodes = set()
    for conn, sel in ((q[:, 2:6], q[:, 1] == pid), (tr[:, 2:5], tr[:, 1] == pid)):
        for row in conn[sel]:
            nodes.update(int(g) for g in row)
    idx = np.array([g2i[g] for g in sorted(nodes)])
    X = xyz[idx]
    ctr = X.mean(0)
    _, _, Vt = np.linalg.svd(X - ctr, full_matrices=False)
    return idx, X, ctr, Vt


def apply_warp_panel(m, pid, amp):
    if int(pid) not in FLAT_PANEL_PIDS:
        raise ValueError(f"warp_panel: pid {pid} not in flat-panel menu {sorted(FLAT_PANEL_PIDS)}")
    t = float(m["pshell"][str(int(pid))]["t"])
    cap = min(2.0 * t, WARP_AMP_CAP_IN)
    if abs(float(amp)) > cap + 1e-12:
        raise ValueError(f"warp_panel: |amp| {abs(amp):.3f} > cap {cap:.3f} (pid {pid}, t={t})")
    idx, X, ctr, Vt = panel_frame(m, pid)
    n = Vt[2]
    u = (X - ctr) @ Vt[0]
    v = (X - ctr) @ Vt[1]
    u0, u1, v0, v1 = u.min(), u.max(), v.min(), v.max()
    s = np.sin(np.pi * (u - u0) / (u1 - u0)) * np.sin(np.pi * (v - v0) / (v1 - v0))
    xyz = np.asarray(m["xyz"], float).copy()
    xyz[idx] = X + float(amp) * s[:, None] * n[None, :]
    m["xyz"] = xyz
    moved = set(int(g) for g, sv in zip(np.asarray(m["gids"])[idx], s) if abs(sv) > 1e-6)
    return moved


def apply_joint_offset(m, eids, vec):
    """Blended translation (D2 fix): full vector for nodes within R_JOINT of a spider reference (and
    the spider's own nodes), cosine-tapered to zero at R_BLEND, so the distortion spreads over the
    blend annulus instead of folding one element row (first gate run inverted boundary quads)."""
    vec = np.asarray(vec, float)
    if np.linalg.norm(vec) > JOINT_D_CAP_IN + 1e-12:
        raise ValueError(f"joint_offset: |vec| {np.linalg.norm(vec):.3f} > cap {JOINT_D_CAP_IN}")
    g2i = F.g2i_of(m)
    xyz = np.asarray(m["xyz"], float).copy()
    ptr = 0
    want = set(int(e) for e in eids)
    found = set()
    w = np.zeros(len(xyz))
    core_nodes = set()
    for eid, gn, cm, nGM in np.asarray(m["rbe2"]):
        gms = np.asarray(m["rbe2_gms"])[ptr:ptr + nGM]
        ptr += nGM
        if int(eid) not in want:
            continue
        found.add(int(eid))
        core_nodes.add(int(gn))
        core_nodes.update(int(g) for g in gms)
        r = np.linalg.norm(xyz - xyz[g2i[int(gn)]], axis=1)
        wi = np.zeros(len(xyz))
        wi[r <= R_JOINT] = 1.0
        ann = (r > R_JOINT) & (r < R_BLEND)
        wi[ann] = 0.5 * (1.0 + np.cos(np.pi * (r[ann] - R_JOINT) / (R_BLEND - R_JOINT)))
        w = np.maximum(w, wi)
    if found != want:
        raise ValueError(f"joint_offset: eids not found: {sorted(want - found)}")
    for g in core_nodes:
        w[g2i[g]] = 1.0
    moved_idx = np.where(w > 1e-6)[0]
    xyz[moved_idx] = xyz[moved_idx] + w[moved_idx, None] * vec[None, :]
    m["xyz"] = xyz
    gids = np.asarray(m["gids"])
    return set(int(g) for g in gids[moved_idx])


def quad_quality(m, quad_rows):
    """(min corner-Jacobian ratio, max edge slope) over the given cquad4 rows, from CURRENT coords."""
    from fe_core import quad_local_frames, _q4_dN
    g2i = F.g2i_of(m)
    xyz = np.asarray(m["xyz"], float)
    conn = np.asarray(m["cquad4"])[quad_rows][:, 2:6]
    nidx = np.vectorize(g2i.get)(conn)
    X = xyz[nidx]
    O, R, Xl2, warp = quad_local_frames(X)
    ratios = []
    for corner in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        dN = _q4_dN(*corner)
        J = np.einsum('in,enj->eij', dN, Xl2)
        d = np.linalg.det(J)
        ratios.append(d)
    D = np.stack(ratios, axis=1)                       # (ne, 4)
    if (D <= 0).any():
        return -1.0, float("inf")
    jr = float((D.min(1) / D.max(1)).min())
    # edge slope: out-of-plane deviation between adjacent corners / edge length
    slopes = []
    e3 = R[:, 2, :]                                    # fe_core: R rows = e1,e2,e3
    for a in range(4):
        b = (a + 1) % 4
        dz = np.abs(((X[:, a] - X[:, b]) * e3).sum(1))
        L = np.linalg.norm(X[:, a] - X[:, b], axis=1)
        slopes.append(dz / np.maximum(L, 1e-12))
    return jr, float(np.max(slopes))


# ------------------------------------------------------------------ block builders per class
def _stored_shell_K(pid, NDOF):
    return ACT.expand_csr(sp.load_npz(os.path.join(F.MATD, f"K_shell_{pid}.npz")), NDOF)


def _stored_pref_K(pref, NDOF):
    return ACT.expand_csr(sp.load_npz(os.path.join(F.MATD, f"K_{pref}.npz")), NDOF)


def _group_blocks(m, pid_K, excluded, NDOF):
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
                Kp = pid_K.get(pref)
                if Kp is None:
                    Kp = _stored_pref_K(pref, NDOF)
            Kg = Kp if Kg is None else Kg + Kp
        blocks[g] = Kg if Kg is not None else sp.csr_matrix((NDOF, NDOF))
    return blocks


def build_model_blocks(spec):
    """spec -> (model_dict, blocks incl '__M__' and '_fixed_bush99', build_info). Never solves,
    never writes. Existing-op specs delegate to the validated actions path unchanged."""
    ops = spec["ops"]
    kinds = {o["op"] for o in ops}
    info = {"quality": None, "moved_nodes": 0}
    if kinds <= EXISTING_OPS:
        m, blocks = ACT.build_candidate(dict(spec), tag_track="mf", blocks_only=True)
        return m, blocks, info
    if not kinds <= NEW_OPS:
        raise ValueError(f"{spec.get('cid')}: mixed existing/new ops {sorted(kinds)} unsupported")
    m = F.load_model()
    NDOF = 6 * len(m["gids"])
    pid_K = {p: _stored_shell_K(p, NDOF) for p in ACT.SHELL_PIDS}
    Mcur = ACT.expand_csr(sp.load_npz(os.path.join(F.MATD, "M.npz")), NDOF)
    extra = {}
    excluded = set()

    if kinds <= {"rbe3_convert"}:
        eids = [int(e) for o in ops for e in o["eids"]]
        m["rbe3"] = rbe3_maps(m, eids)
        m["released_rbe2"] = list(m.get("released_rbe2", [])) + eids
        info["n_rbe3"] = len(eids)

    elif kinds <= {"formulation"}:
        for o in ops:
            br = float(o.get("br_scale", 1.0))
            tst = o.get("ts_t", None)
            if not (BR_RANGE[0] - 1e-12 <= br <= BR_RANGE[1] + 1e-12):
                raise ValueError(f"formulation: br_scale {br} outside {BR_RANGE}")
            if tst is not None and not any(abs(float(tst) - v) < 1e-9 for v in TS_T_MENU):
                raise ValueError(f"formulation: ts_t {tst} not in menu {TS_T_MENU}")
            if br == 1.0 and tst is None:
                raise ValueError("formulation: no-op (br_scale=1, ts_t unset)")
            for pid in o["pids"]:
                m2 = dict(m)
                m2["pshell"] = dict(m["pshell"])
                p0 = dict(m2["pshell"][str(int(pid))])
                p0["bend_ratio"] = p0["bend_ratio"] * br
                if tst is not None:
                    p0["ts_t"] = float(tst)
                m2["pshell"][str(int(pid))] = p0
                Kn, _, _ = F.assemble_shell(m2, int(pid))
                name = o.get("name", f"form_{pid}")
                extra[name] = extra.get(name, sp.csr_matrix((NDOF, NDOF))) + Kn
                excluded.add(int(pid))
        info["n_form_pids"] = len(excluded)

    elif kinds <= {"warp_panel", "joint_offset"}:
        m0 = F.load_model()
        moved = set()
        for o in ops:
            if o["op"] == "warp_panel":
                moved |= apply_warp_panel(m, int(o["pid"]), float(o["amp"]))
            else:
                moved |= apply_joint_offset(m, [int(e) for e in o["eids"]],
                                            [float(x) for x in o["vec"]])
        if not moved:
            raise ValueError("geometry op moved no nodes")
        info["moved_nodes"] = len(moved)
        q = np.asarray(m["cquad4"])
        tr = np.asarray(m["ctria3"])
        aff_shell = set()
        edited_quads = np.zeros(len(q), bool)
        for conn, arr, mark in ((q[:, 2:6], q, True), (tr[:, 2:5], tr, False)):
            hit = np.isin(conn, list(moved)).any(axis=1)
            aff_shell.update(int(p) for p in arr[hit][:, 1])
            if mark:
                edited_quads = hit
        if edited_quads.any():
            jr, slope = quad_quality(m, np.where(edited_quads)[0])
            info["quality"] = {"min_jac_ratio": jr, "max_edge_slope": slope,
                               "n_edited_quads": int(edited_quads.sum())}
            if jr < JAC_RATIO_MIN:
                raise ValueError(f"geometry: corner-Jacobian ratio {jr:.3f} < {JAC_RATIO_MIN}")
            if slope > EDGE_SLOPE_MAX:
                raise ValueError(f"geometry: edge slope {slope:.3f} > {EDGE_SLOPE_MAX}")
        for pid in sorted(aff_shell):
            Kn, Md_new, _ = F.assemble_shell(m, pid)
            _, Md_old, _ = F.assemble_shell(m0, pid)
            pid_K[pid] = Kn
            Mcur = Mcur + sp.diags(Md_new - Md_old).tocsr()
        cb = np.asarray(m["cbush"])
        aff_bush = sorted({int(p) for _, p, ga, gb, _ in cb
                           if int(ga) in moved or int(gb) in moved})
        for bp in aff_bush:
            pid_K[f"bush_{bp}"] = F.bush_pid_K(m, f"bush_{bp}")
        info["affected_shell_pids"] = sorted(aff_shell)
        info["affected_bush_pids"] = aff_bush
    else:
        raise ValueError(f"unsupported op mix {sorted(kinds)}")

    blocks = _group_blocks(m, pid_K, excluded, NDOF)
    blocks.update(extra)
    fixed = _stored_pref_K("bush_99", NDOF)
    blocks["_fixed_bush99"] = fixed
    blocks["__M__"] = Mcur
    return m, blocks, info
