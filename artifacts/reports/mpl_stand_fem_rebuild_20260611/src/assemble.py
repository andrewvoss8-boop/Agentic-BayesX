#!/usr/bin/env python3
"""Parametric assembly for the MPL stand rebuild (FABLE, 2026-06-11).

Builds per-GROUP constant sparse matrices on the RBE2-reduced ("master") DOF set
so that K(theta) = sum_g s_g(theta) * K_g and M(theta) = sum_g m_g(theta) * M_g
with CHEAP reassembly (the ShockSat modal-twin pattern). No sampler here; this
is the structure a future NUTS task consumes.

Adds to the deck (decisions D22-D24, estimates.py):
  - SHIELD: two vertical 1.7 mm steel CQUAD4 panels at x=61.5 (front-wall
    surface plane), attached by 6-DOF screw springs to nearest frame grids.
  - Mounted masses: valve panel / electronics box / white upper box as
    CONM2 (+rotary inertia) on new CG grids, each spring-attached to nearest
    frame grids (local modes exist); PSU box as bare CONM2 on the nearest
    existing frame grid (non-QOI clutter).

Outputs: out/model/{arrays.npz, meta.json, groups/{K,M}_<name>.npz}
         out/groups.json (human-readable group table)
"""
import json
import os
import sys
import time

import numpy as np
import scipy.sparse as sp
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from elements import (beam_KM_global, bush_K_global, conm2_M, rbe2_rows,
                      shell_parts_global)
from estimates import ESTIMATES, STEEL, ALU, TSLOT_1515, LBM

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T0 = time.time()

d = json.load(open(os.path.join(WS, "out", "parsed_deck.json")))
E, NU, RHO = STEEL["E"], STEEL["nu"], STEEL["rho"]
G = E / (2 * (1 + NU))
# DRILL_SCALE env override supports the drilling-stiffness sensitivity arm
DRILL = float(os.environ.get("DRILL_SCALE", ESTIMATES["drill_scale"]["value"]))
OUT_SUB = os.environ.get("OUT_SUBDIR", "model")

# ---------------------------------------------------------------- grid table
grid_ids = sorted(int(k) for k in d["grids"])
xyz = {int(k): np.array([v["x"], v["y"], v["z"]]) for k, v in d["grids"].items()}
region = {g: "frame" for g in grid_ids}
qgrids = {g for q in d["cquads"] for g in q["g"]}
for g in qgrids:
    region[g] = "thrust_plate"

# ---- shield mesh (new grids, ids 800000+) ----
shield_quads = []  # (gid list, panel)
shield_grid_ids = []


def add_shield_panel(name, ext, nx, nz, next_id):
    ys = np.linspace(ext["y0"], ext["y1"], nx + 1)
    zs = np.linspace(ext["z0"], ext["z1"], nz + 1)
    ids = np.zeros((nx + 1, nz + 1), int)
    for j, zv in enumerate(zs):
        for i, yv in enumerate(ys):
            gid = next_id
            next_id += 1
            grid_ids.append(gid)
            xyz[gid] = np.array([ext["x"], yv, zv])
            region[gid] = "shield"
            shield_grid_ids.append(gid)
            ids[i, j] = gid
    for j in range(nz):
        for i in range(nx):
            shield_quads.append(([int(ids[i, j]), int(ids[i + 1, j]),
                                  int(ids[i + 1, j + 1]), int(ids[i, j + 1])],
                                 name))
    return ids, next_id


mesh = ESTIMATES["shield_mesh"]["value"]
REFINE = int(os.environ.get("SHIELD_REFINE", "1"))  # h-refinement spot-check
upper_ids, nid_next = add_shield_panel(
    "upper", ESTIMATES["shield_upper_extent"]["value"],
    REFINE * mesh["upper_nx"], REFINE * mesh["upper_nz"], 800000)
lower_ids, nid_next = add_shield_panel(
    "lower", ESTIMATES["shield_lower_extent"]["value"],
    REFINE * mesh["lower_nx"], REFINE * mesh["lower_nz"], nid_next)

# ---- mounted-mass CG grids (ids 900002+) ----
mounted = {}
for key, gid in (("electronics_box", 900002), ("white_box_upper", 900003)):
    v = ESTIMATES[key]["value"]
    grid_ids.append(gid)
    xyz[gid] = np.array(v["cg"], float)
    region[gid] = key
    mounted[key] = gid

# ---- 80/20 valve sub-frame nodes (ids 910000+; D38) ----
from valve_frame import build_valve_frame, beam_orient
vframe = build_valve_frame(ESTIMATES["valve_frame"]["value"], id0=910000)
for nid, p in vframe["nodes"].items():
    grid_ids.append(nid)
    xyz[nid] = p
    region[nid] = "valve_panel"

N = len(grid_ids)
gidx = {g: i for i, g in enumerate(grid_ids)}
ndof = 6 * N
X = np.array([xyz[g] for g in grid_ids])

# frame-grid KD-tree (deck grids only, excluding thrust-plate interior)
frame_ids = [g for g in grid_ids if region[g] in ("frame",)]
ftree = cKDTree(np.array([xyz[g] for g in frame_ids]))


def nearest_frame(p, k=1):
    dist, ii = ftree.query(np.asarray(p, float), k=k)
    if k == 1:
        return [frame_ids[int(ii)]], [float(dist)]
    return [frame_ids[int(j)] for j in np.atleast_1d(ii)], list(np.atleast_1d(dist))


# ---------------------------------------------------------------- group assembly
class Group:
    def __init__(self):
        self.r, self.c, self.v = [], [], []

    def add(self, idx, mat):
        idx = np.asarray(idx)
        nz = np.nonzero(mat)
        self.r.extend(idx[nz[0]])
        self.c.extend(idx[nz[1]])
        self.v.extend(mat[nz])

    def csr(self):
        return sp.coo_matrix((self.v, (self.r, self.c)),
                             shape=(ndof, ndof)).tocsr()


Kg = {n: Group() for n in
      ["beam_wall", "beam_rest", "plate_mem", "plate_bend", "shield_mem",
       "shield_bend", "bush_joints", "shield_att", "valveframe", "valve_mount",
       "att_ebox", "att_ebox_rot", "att_wbox", "feet_springs"]}
Mg = {n: Group() for n in
      ["m_beam_wall", "m_beam_rest", "m_plate", "m_shield", "m_valveframe",
       "m_valvemass", "m_ebox", "m_wbox"]}


def dofs(gids):
    return np.concatenate([np.arange(6 * gidx[g], 6 * gidx[g] + 6) for g in gids])


# ---- beams (group split: wall vs rest, D25) ----
pb = {int(k): v for k, v in d["pbeams"].items()}
n_wall = 0
for c in d["cbeams"]:
    p = pb[c["pid"]]
    xa, xb = xyz[c["ga"]], xyz[c["gb"]]
    Ke, Me = beam_KM_global(xa, xb, c["v"], E, G, RHO, p)
    wall = (58.0 < xa[0] < 63.0) and (58.0 < xb[0] < 63.0)
    n_wall += int(wall)
    idx = dofs([c["ga"], c["gb"]])
    Kg["beam_wall" if wall else "beam_rest"].add(idx, Ke)
    Mg["m_beam_wall" if wall else "m_beam_rest"].add(idx, Me)

# ---- thrust plate quads ----
psh = list(d["pshells"].values())[0]
T_PLATE = psh["t"]
oop_max_plate = 0.0
for q in d["cquads"]:
    pts = np.array([xyz[g] for g in q["g"]])
    Km, Kb, Me, oop = shell_parts_global(pts, E, NU, RHO, T_PLATE, DRILL)
    oop_max_plate = max(oop_max_plate, oop)
    idx = dofs(q["g"])
    Kg["plate_mem"].add(idx, Km)
    Kg["plate_bend"].add(idx, Kb)
    Mg["m_plate"].add(idx, Me)

# ---- shield quads ----
T_SHIELD = ESTIMATES["shield_thickness_in"]["value"]
oop_max_shield = 0.0
for gids, _name in shield_quads:
    pts = np.array([xyz[g] for g in gids])
    Km, Kb, Me, oop = shell_parts_global(pts, E, NU, RHO, T_SHIELD, DRILL)
    oop_max_shield = max(oop_max_shield, oop)
    idx = dofs(gids)
    Kg["shield_mem"].add(idx, Km)
    Kg["shield_bend"].add(idx, Kb)
    Mg["m_shield"].add(idx, Me)

# ---- deck CBUSH joints ----
kb = np.array(list(d["pbushes"].values())[0], float)
for c in d["cbushes"]:
    Ke = bush_K_global(xyz[c["ga"]], xyz[c["gb"]], kb)
    Kg["bush_joints"].add(dofs([c["ga"], c["gb"]]), Ke)

# ---- shield screw springs ----
kt = ESTIMATES["shield_screw_k_trans"]["value"]
kr = ESTIMATES["shield_screw_k_rot"]["value"]
kscrew = [kt] * 3 + [kr] * 3
screw_log = []
stree = cKDTree(np.array([xyz[g] for g in shield_grid_ids]))
for (ylist, panel) in ((ESTIMATES["shield_screws_upper"]["value"], "upper"),
                       (ESTIMATES["shield_screws_lower"]["value"], "lower")):
    for (yv, zv) in ylist:
        p = np.array([61.5, yv, zv])
        _, si = stree.query(p)
        sgid = shield_grid_ids[int(si)]
        fgid, fd = nearest_frame(xyz[sgid])
        Ke = bush_K_global(xyz[sgid], xyz[fgid[0]], kscrew)
        Kg["shield_att"].add(dofs([sgid, fgid[0]]), Ke)
        screw_log.append(dict(panel=panel, shield_grid=int(sgid),
                              frame_grid=int(fgid[0]), gap_in=round(fd[0], 3)))

# ---- 80/20 valve sub-frame: aluminum beams + lumped tank/valve mass + mount ----
vf_spec = ESTIMATES["valve_frame"]["value"]
G_AL = ALU["E"] / (2 * (1 + ALU["nu"]))
prop_ts = dict(TSLOT_1515)
prop_ts["nsm"] = 0.0
vf_beam_log = []
for (ga, gb) in vframe["beams"]:
    Ke, Me = beam_KM_global(xyz[ga], xyz[gb], beam_orient(xyz[ga], xyz[gb]),
                            ALU["E"], G_AL, ALU["rho"], prop_ts)
    idxb = dofs([ga, gb])
    Kg["valveframe"].add(idxb, Ke)
    Mg["m_valveframe"].add(idxb, Me)
    vf_beam_log.append([int(ga), int(gb)])
# lumped tank/manifold/valve masses on frame nodes (isotropic point mass)
for nid, m_lbm in vframe["lumped"].items():
    Mg["m_valvemass"].add(dofs([nid]), conm2_M(m_lbm * LBM, (0, 0, 0)))
# mount the 4 bottom corners to the nearest deck base grids
kvm = [vf_spec["mount_k_trans"]] * 3 + [vf_spec["mount_k_rot"]] * 3
vf_mount_log = []
for mn in vframe["mount_nodes"]:
    fg, fd = nearest_frame(xyz[mn])
    Ke = bush_K_global(xyz[mn], xyz[fg[0]], kvm)
    Kg["valve_mount"].add(dofs([mn, fg[0]]), Ke)
    vf_mount_log.append(dict(frame_node=int(mn), stand_grid=int(fg[0]),
                             gap_in=round(fd[0], 2)))
frame_self_lbm = sum(Mg["m_valveframe"].csr().diagonal()[0::6]) * 386.089
valvemass_lbm = sum(vframe["lumped"].values())

# ---- mounted masses (QOI boxes: CONM2 + springs) ----
mount_log = {}
for key, gname, mgname in (("electronics_box", "att_ebox", "m_ebox"),
                           ("white_box_upper", "att_wbox", "m_wbox")):
    v = ESTIMATES[key]["value"]
    m = v["mass_lbm"] * LBM
    a, b, c_ = v["dims_in"]
    inertia = (m * (b ** 2 + c_ ** 2) / 12.0, m * (a ** 2 + c_ ** 2) / 12.0,
               m * (a ** 2 + b ** 2) / 12.0)
    gid = mounted[key]
    Mg[mgname].add(dofs([gid]), conm2_M(m, inertia))
    katt = [v["k_att_trans"]] * 3 + [v["k_att_rot"]] * 3
    if "shield_bolts_yz" in v:
        # D33: electronics box bolts ON THE SHIELD (3 feet over the LabJack
        # sticker region) -> springs to the nearest SHIELD grid at each bolt
        fgids, fds = [], []
        for (yv, zv) in v["shield_bolts_yz"]:
            _, si = stree.query(np.array([61.5, yv, zv]))
            fgids.append(shield_grid_ids[int(si)])
            fds.append(float(np.linalg.norm(xyz[fgids[-1]] - xyz[gid])))
    else:
        # search near 'attach_near' if given (e.g. valve panel CG sits high
        # but bolts to the stand BASE per Andrew), else near the CG
        fgids, fds = nearest_frame(v.get("attach_near", xyz[gid]),
                                   k=v["n_attach"])
    for fg in fgids:
        if key == "electronics_box":
            # D43 model-form refinement: split the box mount into separate
            # TRANSLATIONAL and ROTATIONAL springs so the box can have BOTH a
            # bounce mode and a (distinct) rocking mode -- the data shows two
            # box peaks (~11 and ~27 Hz) that one coupled k could not produce.
            kt = [v["k_att_trans"]] * 3 + [0.0] * 3
            kr = [0.0] * 3 + [v["k_att_rot"]] * 3
            Kg["att_ebox"].add(dofs([gid, fg]), bush_K_global(xyz[gid],
                                                              xyz[fg], kt))
            Kg["att_ebox_rot"].add(dofs([gid, fg]), bush_K_global(xyz[gid],
                                                                 xyz[fg], kr))
        else:
            Kg[gname].add(dofs([gid, fg]), bush_K_global(xyz[gid], xyz[fg],
                                                         katt))
    mount_log[key] = dict(cg_grid=gid, mass_lbm=v["mass_lbm"],
                          attach_grids=[int(g) for g in fgids],
                          attach_dist_in=[round(x, 2) for x in fds],
                          attached_to=("shield" if "shield_bolts_yz" in v
                                       else "frame"),
                          inertia_diag=[float(i) for i in inertia])
# PSU CONM2 removed (D33: it was the electronics box double-counted)

# ---- foot grounding springs (variant group; nominal uses SPC) ----
kf = [ESTIMATES["foot_spring_k"]["value"]] * 6
spc_grids = sorted({g for s in d["spc1"] for g in s["grids"]})
for g in spc_grids:
    # ground spring: connect grid to ground = diagonal addition on its 6 DOFs
    Kg["feet_springs"].add(dofs([g]), np.diag(kf))

# ---------------------------------------------------------------- RBE2 reduction
dep_pairs = []  # (dep_gid, indep_gid)
gn_set = {r["gn"] for r in d["rbe2s"]}
for r in d["rbe2s"]:
    assert int(r["cm"]) == 123456, f"RBE2 {r['eid']} CM={r['cm']} unsupported"
    for gm in r["gm"]:
        assert gm not in gn_set, f"RBE2 chain at grid {gm} (dep is also indep)"
        dep_pairs.append((gm, r["gn"]))
dep_gids = [p[0] for p in dep_pairs]
assert len(dep_gids) == len(set(dep_gids)), "duplicate dependent grids"

master_mask = np.ones(ndof, bool)
for gm, _gn in dep_pairs:
    master_mask[6 * gidx[gm]:6 * gidx[gm] + 6] = False
master_dofs = np.where(master_mask)[0]
mpos = -np.ones(ndof, int)
mpos[master_dofs] = np.arange(master_dofs.size)

rows, cols, vals = [], [], []
for dof in master_dofs:  # identity part
    rows.append(dof)
    cols.append(mpos[dof])
    vals.append(1.0)
for gm, gn in dep_pairs:
    Tb = rbe2_rows(xyz[gn], xyz[gm])
    for i in range(6):
        for j in range(6):
            if Tb[i, j] != 0.0:
                rows.append(6 * gidx[gm] + i)
                cols.append(mpos[6 * gidx[gn] + j])
                vals.append(Tb[i, j])
T = sp.coo_matrix((vals, (rows, cols)), shape=(ndof, master_dofs.size)).tocsr()

# ---------------------------------------------------------------- reduce + save
outdir = os.path.join(WS, "out", OUT_SUB)
os.makedirs(os.path.join(outdir, "groups"), exist_ok=True)
sp.save_npz(os.path.join(outdir, "T_rbe2.npz"), T)
gtable = {}
Ksum = None
for name, g in Kg.items():
    A = g.csr()
    Ar = (T.T @ A @ T).tocsr()
    Ar.eliminate_zeros()
    sp.save_npz(os.path.join(outdir, "groups", f"K_{name}.npz"), Ar)
    gtable[f"K_{name}"] = dict(nnz=int(Ar.nnz))
    Ksum = Ar if Ksum is None else Ksum + Ar
for name, g in Mg.items():
    A = g.csr()
    Ar = (T.T @ A @ T).tocsr()
    Ar.eliminate_zeros()
    sp.save_npz(os.path.join(outdir, "groups", f"M_{name}.npz"), Ar)
    gtable[f"M_{name}"] = dict(nnz=int(Ar.nnz),
                               total_mass_x=float(Ar.diagonal()[0::6].sum()))

# AUTOSPC check on nominal K (excluding feet_springs which is variant-only)
Knom = Ksum - sp.load_npz(os.path.join(outdir, "groups", "K_feet_springs.npz"))
zero_diag = np.where(Knom.diagonal() == 0.0)[0]

# SPC: feet fixed (all 6 DOFs) -> indices within master set
spc_master = np.concatenate([np.arange(6 * gidx[g], 6 * gidx[g] + 6)
                             for g in spc_grids])
spc_master_idx = mpos[spc_master]
assert (spc_master_idx >= 0).all(), "SPC grid is RBE2-dependent?!"

np.savez_compressed(
    os.path.join(outdir, "arrays.npz"),
    grid_ids=np.array(grid_ids), X=X,
    region=np.array([region[g] for g in grid_ids]),
    master_dofs=master_dofs, spc_master_idx=spc_master_idx,
    zero_diag_master_idx=zero_diag)

meta = dict(
    n_grids=N, ndof_full=ndof, ndof_master=int(master_dofs.size),
    n_rbe2_dep_grids=len(dep_gids), n_spc_dofs=int(spc_master_idx.size),
    n_zero_diag_after_assembly=int(zero_diag.size),
    n_beam_wall=n_wall, n_beam_rest=len(d["cbeams"]) - n_wall,
    n_shield_quads=len(shield_quads), n_shield_grids=len(shield_grid_ids),
    oop_max_plate=oop_max_plate, oop_max_shield=oop_max_shield,
    thrust_plate_t=T_PLATE, shield_t=T_SHIELD,
    screw_log=screw_log, mount_log=mount_log,
    valve_frame=dict(series=vf_spec["series"], material=vf_spec["material"],
                     n_nodes=vframe["n_nodes"], n_beams=vframe["n_beams"],
                     beams=vf_beam_log, mount=vf_mount_log,
                     frame_self_mass_lbm=round(float(frame_self_lbm), 2),
                     tank_valve_lumped_lbm=round(float(valvemass_lbm), 2),
                     total_valve_assembly_lbm=round(
                         float(frame_self_lbm + valvemass_lbm), 2)),
    K_groups=[n for n in Kg], M_groups=[n for n in Mg],
    nominal_scalars={**{f"K_{n}": 1.0 for n in Kg}, **{f"M_{n}": 1.0 for n in Mg},
                     "K_feet_springs": 0.0},
    note_feet="nominal model: feet SPC-fixed, K_feet_springs scalar 0; "
              "variant: no SPC + K_feet_springs scalar 1",
    units="inch-lbf-second",
    elapsed_s=round(time.time() - T0, 2),
)
with open(os.path.join(outdir, "meta.json"), "w") as fh:
    json.dump(meta, fh, indent=1)
with open(os.path.join(WS, "out", "groups.json"), "w") as fh:
    json.dump(gtable, fh, indent=1)

print(json.dumps({k: meta[k] for k in
                  ("n_grids", "ndof_master", "n_rbe2_dep_grids",
                   "n_zero_diag_after_assembly", "n_beam_wall", "n_beam_rest",
                   "oop_max_plate", "oop_max_shield")}, indent=1))
print("mount_log:", json.dumps(mount_log, indent=1))
print("screw gaps (in):", sorted({s["gap_in"] for s in screw_log}))
print("OK, elapsed %.1fs" % (time.time() - T0))
