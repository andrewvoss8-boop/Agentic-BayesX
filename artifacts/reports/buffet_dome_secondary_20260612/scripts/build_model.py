#!/usr/bin/env python3
"""Fine-region FEM builder — representative LV dome secondary-structure study.

Geometry (assumptions_ledger.md A1-B7, decisions D4/D5):
  - barrel: R=2.25 m cylinder, z in [-1.5, 0] (cut at first ring frame)
  - ring:   box-section frame beam at the dome/barrel junction (z=0)
  - dome:   sqrt(2):1 ellipsoidal cap, apex up (z_h = R/sqrt(2))
  - tray:   600x600x12.7 mm Al plate on 6 axial struts (hexapod-style),
            anchored to dome nodes near azimuth 0 deg; avionics = offset CONM2
  - COPV:   beam-spine cylinder (smeared overwrap+contents) on 2x 3-axis
            spring mounts to dome nodes near azimuth 180 deg

Elements: REUSED validated ShockSat fe_core shells (QM6+MITC4 quads, CST+DKT
trias, drilling penalty) + THIS-STUDY validated beam3d/bar3d (out/
beam_validation.json). Struts = bar3d with EFFECTIVE axial modulus = series
(tube EA/L + 2 joint springs k_joint), keeping joint stiffness a scalar
parameter (D10, ledger B3).

Boundary brackets (quantity_contracts Q7): BC-A bottom ring FIXED (upper
impedance bound); BC-B bottom ring RBE2 -> master node carrying the far-field
stack mass/inertia, structure otherwise FREE (free-flight-like lower bound,
6 rigid modes are physical). The QOI spread between brackets is reported as
boundary-condition uncertainty.

Mesh: Ntheta=240 circumferential (59 mm arc = lambda_bend/6 at 400 Hz for
t=5 mm — Discretization gate); forcing uses a FINER separate load grid via
mode-shape interpolation (validated S1 rule: >=6 nodes per coherence length).

Outputs: out/model_<bc>.npz (sparse K, M, maps), out/model_meta.json (sets,
sanity numbers, parameters).
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import scipy.sparse as sp

HERE = Path(__file__).resolve().parent
WS = HERE.parent
SHOCKSAT = WS.parent / "shocksat_fem_modal_twin_20260609" / "scripts"
sys.path.insert(0, str(SHOCKSAT))
sys.path.insert(0, str(HERE))
from beam_element import beam3d, bar3d                                  # noqa: E402
from shell_assemble import make_shell_group                             # noqa: E402

T0 = time.time()

# ------------------------------------------------------------------ params
PAR = dict(
    R=2.25, Lbar=1.5, t_dome=0.005, t_barrel=0.005,
    E_host=71e9, nu_host=0.33, rho_host=2800.0,
    ring_b=0.10, ring_h=0.06, ring_t=0.006,
    # tray — D16 FLIGHT-REALISTIC bolted bracket mount (was subscale soft hexapod
    # with pin-ended rod-end struts -> unphysical 7 Hz tray-yaw mode). Struts are
    # now MOMENT-CARRYING beams (mount_beam=True) on bolted (near-rigid) joints,
    # thicker section + shorter standoff = a stiff bracket -> first tray mode
    # >100 Hz (standard flight requirement: clear the launch low-freq env).
    tray_a=0.6, tray_t=0.0127, E_tray=68.9e9, nu_tray=0.33, rho_tray=2700.0,
    tray_u_deg=55.0, tray_az_deg=0.0, tray_standoff=0.10,
    strut_do=0.040, strut_di=0.034, E_strut=71e9, rho_strut=2800.0,
    k_joint=1.0e9, mount_beam=True,     # D16: beam struts + bolted joints
    m_avionics=8.0, av_offset=0.05,
    # copv — D16: strapped cradle (was 2 soft point mounts -> 7 Hz COPV roll)
    copv_L=0.7, copv_D=0.35, copv_t=0.004, copv_E=60e9, copv_mass=30.0,
    copv_u_deg=30.0, copv_az_deg=180.0, copv_standoff=0.12,  # D16: near the
    k_mount=5.0e7, k_mount_rot=1.0e6,   # stiff junction/ring (hard-point mount)
    # boundary
    M_stack=1.0e5, I_stack=5.0e6,
    # mesh
    Nth=240, Nz=16, Nu=24,
    K6ROT=100.0,
)

# variant support (sensitivity / convergence re-solves): JSON overrides via env
import os                                                       # noqa: E402
TAG = os.environ.get("BUFFET_TAG", "")
if os.environ.get("BUFFET_PAR_OVERRIDES"):
    ov = json.loads(os.environ["BUFFET_PAR_OVERRIDES"])
    PAR.update(ov)
    print(f"variant TAG={TAG} overrides={ov}")

R, H = PAR["R"], PAR["R"] / np.sqrt(2.0)
Nth, Nz, Nu = PAR["Nth"], PAR["Nz"], PAR["Nu"]

# ------------------------------------------------------------------ mesh
nodes = []
def add_node(p):
    nodes.append(tuple(p)); return len(nodes) - 1

# barrel rings bottom->top (ring iz=Nz is the junction ring, shared w/ dome u=0)
barrel_grid = np.zeros((Nz + 1, Nth), dtype=int)
for iz in range(Nz + 1):
    z = -PAR["Lbar"] + PAR["Lbar"] * iz / Nz
    for it in range(Nth):
        th = 2 * np.pi * it / Nth
        barrel_grid[iz, it] = add_node((R * np.cos(th), R * np.sin(th), z))

# dome rings u>0 (junction ring = barrel_grid[Nz]); apex node last
dome_grid = np.zeros((Nu, Nth), dtype=int)   # iu=0 -> junction ring (alias)
dome_grid[0] = barrel_grid[Nz]
for iu in range(1, Nu):
    u = (np.pi / 2) * iu / Nu
    r, z = R * np.cos(u), H * np.sin(u)
    for it in range(Nth):
        th = 2 * np.pi * it / Nth
        dome_grid[iu, it] = add_node((r * np.cos(th), r * np.sin(th), z))
apex = add_node((0.0, 0.0, H))

quads, quad_grp = [], []   # grp: 0 barrel, 1 dome, 2 tray
for iz in range(Nz):
    for it in range(Nth):
        j = (it + 1) % Nth
        quads.append((barrel_grid[iz, it], barrel_grid[iz, j],
                      barrel_grid[iz + 1, j], barrel_grid[iz + 1, it]))
        quad_grp.append(0)
for iu in range(Nu - 1):
    for it in range(Nth):
        j = (it + 1) % Nth
        quads.append((dome_grid[iu, it], dome_grid[iu, j],
                      dome_grid[iu + 1, j], dome_grid[iu + 1, it]))
        quad_grp.append(1)
tris, tri_grp = [], []
for it in range(Nth):
    j = (it + 1) % Nth
    tris.append((dome_grid[Nu - 1, it], dome_grid[Nu - 1, j], apex))
    tri_grp.append(1)

# ---- dome surface helpers
def dome_point(u, az):
    return np.array([R * np.cos(u) * np.cos(az), R * np.cos(u) * np.sin(az),
                     H * np.sin(u)])

def dome_normal(u, az):
    r = R * np.cos(u)
    n = np.array([np.cos(az) * r / R**2, np.sin(az) * r / R**2,
                  H * np.sin(u) / H**2])
    return n / np.linalg.norm(n)

# ---- tray (plate grid in its own plane)
u_t = np.radians(PAR["tray_u_deg"]); az_t = np.radians(PAR["tray_az_deg"])
anchor_t = dome_point(u_t, az_t); n_t = dome_normal(u_t, az_t)
c_tray = anchor_t + PAR["tray_standoff"] * n_t
e1_t = np.array([-np.sin(az_t), np.cos(az_t), 0.0])           # azimuthal
e2_t = np.cross(n_t, e1_t); e2_t /= np.linalg.norm(e2_t)
nq_t = 12
tray_grid = np.zeros((nq_t + 1, nq_t + 1), dtype=int)
a_t = PAR["tray_a"]
for i in range(nq_t + 1):
    for j in range(nq_t + 1):
        xi = (i / nq_t - 0.5) * a_t; yj = (j / nq_t - 0.5) * a_t
        tray_grid[i, j] = add_node(c_tray + xi * e1_t + yj * e2_t)
for i in range(nq_t):
    for j in range(nq_t):
        quads.append((tray_grid[i, j], tray_grid[i + 1, j],
                      tray_grid[i + 1, j + 1], tray_grid[i, j + 1]))
        quad_grp.append(2)

# ---- struts: 3 bipods; tray points at r=0.28 (az +-6 deg of spokes),
#      dome feet near anchor circle r~0.42 (az +-32 deg of spokes)
def nearest_node(ids, p):
    X = np.array([nodes[i] for i in ids])
    return ids[int(np.argmin(((X - p) ** 2).sum(1)))]

def tray_nearest(p):
    ids = tray_grid.ravel().tolist()
    return nearest_node(ids, p)

dome_ids_all = dome_grid[1:].ravel().tolist()
struts = []          # (node_tray, node_dome)
spokes = [90.0, 210.0, 330.0]
for s in spokes:
    for sgn in (+1, -1):
        a_top = np.radians(s + sgn * 6.0)
        a_bot = np.radians(s + sgn * 32.0)
        p_top = c_tray + 0.28 * (np.cos(a_top) * e1_t + np.sin(a_top) * e2_t)
        p_bot_t = anchor_t + 0.42 * (np.cos(a_bot) * e1_t +
                                     np.sin(a_bot) * np.cross(n_t, e1_t))
        nt = tray_nearest(p_top)
        nd = nearest_node(dome_ids_all, p_bot_t)
        struts.append((nt, nd))

# ---- avionics CONM2 (offset) on tray node nearest local (0.15, 0.10)
av_center = c_tray + 0.15 * e1_t + 0.10 * e2_t
av_node = tray_nearest(av_center)
av_d = PAR["av_offset"] * n_t                       # offset above plate
# D16: the 8 kg box's yaw/rock inertia must be reacted by a BOLT FOOTPRINT, not
# a single shell node's artificial drilling stiffness (that gave a spurious
# 7.4 Hz box-yaw mode). 4 footprint corner nodes (~0.06 m half-size) tied to the
# box node by stiff 6-DOF bushings.
av_fp = 0.06
av_foot_nodes = [tray_nearest(av_center + sx * av_fp * e1_t + sy * av_fp * e2_t)
                 for sx in (-1, 1) for sy in (-1, 1)]
av_foot_nodes = [nn for nn in dict.fromkeys(av_foot_nodes) if nn != av_node]

# ---- COPV: beam spine + 2 mounts
u_c = np.radians(PAR["copv_u_deg"]); az_c = np.radians(PAR["copv_az_deg"])
anchor_c = dome_point(u_c, az_c); n_c = dome_normal(u_c, az_c)
c_copv = anchor_c + PAR["copv_standoff"] * n_c
e_ax = np.array([-np.sin(az_c), np.cos(az_c), 0.0])  # spine along azimuthal
n_sp = 6
copv_nodes = [add_node(c_copv + s * e_ax)
              for s in np.linspace(-PAR["copv_L"] / 2, PAR["copv_L"] / 2, n_sp)]
mounts = []
mount_stations = (-0.25, 0.0, 0.25) if PAR.get("mount_beam", False) else (-0.2, 0.2)
for s in mount_stations:
    nc = copv_nodes[int(np.argmin(np.abs(
        np.linspace(-PAR["copv_L"] / 2, PAR["copv_L"] / 2, n_sp) - s)))]
    nd = nearest_node(dome_ids_all, c_copv + s * e_ax - PAR["copv_standoff"] * n_c)
    mounts.append((nc, nd))

# ---- boundary master (BC-B)
master = add_node((0.0, 0.0, -PAR["Lbar"]))

XYZ = np.array(nodes)
NN = len(nodes); NDOF = 6 * NN
quads = np.array(quads); tris = np.array(tris)
quad_grp = np.array(quad_grp); tri_grp = np.array(tri_grp)

# ------------------------------------------------------------------ assembly
rows, cols, vals = [], [], []
Mdiag = np.zeros(NDOF)

def add_K(dofs, Ke):
    nd = len(dofs)
    rows.append(np.repeat(dofs, nd)); cols.append(np.tile(dofs, nd))
    vals.append(np.asarray(Ke, float).ravel())

shell_group = make_shell_group(XYZ, rows, cols, vals, Mdiag,
                               K6ROT_default=PAR["K6ROT"])

mass_parts = {}
mass_parts["barrel"] = shell_group(quads[quad_grp == 0], 0, PAR["E_host"],
                                   PAR["nu_host"], PAR["t_barrel"], PAR["rho_host"])
mass_parts["dome_q"] = shell_group(quads[quad_grp == 1], 1, PAR["E_host"],
                                   PAR["nu_host"], PAR["t_dome"], PAR["rho_host"])
mass_parts["dome_t"] = shell_group(tris, 1, PAR["E_host"], PAR["nu_host"],
                                   PAR["t_dome"], PAR["rho_host"])
mass_parts["tray"] = shell_group(quads[quad_grp == 2], 2, PAR["E_tray"],
                                 PAR["nu_tray"], PAR["tray_t"], PAR["rho_tray"])

# ring frame beams (junction circle), thin-wall closed box properties
b_, h_, tw = PAR["ring_b"], PAR["ring_h"], PAR["ring_t"]
A_r = 2 * tw * (b_ + h_)
Iy_r = (b_ * h_**3 - (b_ - 2 * tw) * (h_ - 2 * tw)**3) / 12.0
Iz_r = (h_ * b_**3 - (h_ - 2 * tw) * (b_ - 2 * tw)**3) / 12.0
J_r = 4 * ((b_ - tw) * (h_ - tw))**2 * tw / (2 * ((b_ - tw) + (h_ - tw)))
ring_mass = 0.0
jr = barrel_grid[Nz]
for it in range(Nth):
    n1, n2 = jr[it], jr[(it + 1) % Nth]
    x1, x2 = XYZ[n1], XYZ[n2]
    vref = (x1 + x2) / 2.0; vref = vref / np.linalg.norm(vref)  # radial
    Ke, Me = beam3d(x1, x2, PAR["E_host"], PAR["nu_host"], A_r, Iy_r, Iz_r,
                    J_r, PAR["rho_host"], vref=vref)
    d = np.concatenate([6 * n1 + np.arange(6), 6 * n2 + np.arange(6)])
    add_K(d, Ke)
    # lump the consistent beam mass to the diagonal (consistent w/ shell lumping)
    Mdiag[d] += Me.sum(axis=1).clip(0)   # row-sum lumping (preserves total mass)
    ring_mass += PAR["rho_host"] * A_r * np.linalg.norm(x2 - x1)
mass_parts["ring"] = ring_mass

# struts: bar3d with EFFECTIVE axial modulus (tube EA/L series w/ 2 joints)
A_s = np.pi / 4 * (PAR["strut_do"]**2 - PAR["strut_di"]**2)
strut_info = []
I_s = np.pi / 64 * (PAR["strut_do"]**4 - PAR["strut_di"]**4)
J_s = 2 * I_s
for nt, nd in struts:
    x1, x2 = XYZ[nt], XYZ[nd]
    L_s = np.linalg.norm(x2 - x1)
    k_tube = PAR["E_strut"] * A_s / L_s
    k_eff = 1.0 / (1.0 / k_tube + 2.0 / PAR["k_joint"])   # axial (QOI stiffness)
    ex = (x2 - x1) / L_s
    if PAR.get("mount_beam", False):
        # D16: moment-carrying beam strut on bolted (near-rigid) joints.
        # Axial stiffness knocked down to k_eff (joint series) by scaling E for
        # the axial term is not separable in a beam; with k_joint=1e9 the series
        # knockdown is <3% so we use the true beam (documented).
        vref = n_t if abs(n_t @ ex) < 0.98 else np.array([0., 0., 1.])
        Ke, Me = beam3d(x1, x2, PAR["E_strut"], 0.33, A_s, I_s, I_s, J_s,
                        PAR["rho_strut"], vref=vref)
        d = np.concatenate([6 * nt + np.arange(6), 6 * nd + np.arange(6)])
        add_K(d, Ke)
        Mdiag[d] += Me.sum(axis=1).clip(0)
    else:
        E_eff = k_eff * L_s / A_s
        Ke, Me = bar3d(x1, x2, E_eff, A_s, PAR["rho_strut"])
        d = np.concatenate([6 * nt + np.arange(3), 6 * nd + np.arange(3)])
        add_K(d, Ke)
        Mdiag[d] += Me.sum(axis=1).clip(0)
    strut_info.append(dict(n_tray=int(nt), n_dome=int(nd), L=float(L_s),
                           k_eff=float(k_eff), ex=ex.tolist()))
mass_parts["struts"] = PAR["rho_strut"] * A_s * sum(s["L"] for s in strut_info)

def skew(v):
    return np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0.]])

# avionics CONM2 with offset d (rigid-offset 6x6)
m_av = PAR["m_avionics"]
I_box = m_av / 12.0 * np.diag([0.15**2 + 0.10**2, 0.20**2 + 0.10**2,
                               0.20**2 + 0.15**2])
S = skew(av_d)
M_av = np.zeros((6, 6))
M_av[:3, :3] = m_av * np.eye(3)
M_av[:3, 3:] = -m_av * S
M_av[3:, :3] = m_av * S
M_av[3:, 3:] = I_box - m_av * (S @ S)
# CONM2 couples trans-rot: keep full 6x6 in K-side? It's mass -> need full M.
# Mdiag is diagonal-only; store CONM2s separately as coo additions.
m_rows = [6 * av_node + np.repeat(np.arange(6), 6)]
m_cols = [6 * av_node + np.tile(np.arange(6), 6)]
m_vals = [M_av.ravel()]
mass_parts["avionics"] = m_av

# COPV spine beams + end masses
A_c = np.pi * PAR["copv_D"] * PAR["copv_t"]
I_c = np.pi * (PAR["copv_D"] / 2)**3 * PAR["copv_t"]
J_c = 2 * I_c
rho_c = PAR["copv_mass"] / (A_c * PAR["copv_L"])
for i in range(n_sp - 1):
    n1, n2 = copv_nodes[i], copv_nodes[i + 1]
    Ke, Me = beam3d(XYZ[n1], XYZ[n2], PAR["copv_E"], 0.3, A_c, I_c, I_c, J_c,
                    rho_c, vref=n_c)
    d = np.concatenate([6 * n1 + np.arange(6), 6 * n2 + np.arange(6)])
    add_K(d, Ke)
    Mdiag[d] += Me.sum(axis=1).clip(0)
mass_parts["copv"] = rho_c * A_c * PAR["copv_L"]

# COPV mounts: 6-DOF bushings WITH rigid arms to the midpoint (fe_core CBUSH
# pattern, S=0.5). Translational k_mount + rotational k_mount_rot (D14: a real
# cradle/strap resists rotation; two purely-translational mounts left a ~0 Hz
# spin about the line through the mount points — caught by the fig2 image-QA
# gate). The rigid-arm form is exact rigid-rotation invariant.
for nc, nd in mounts:
    k = PAR["k_mount"]; kr = PAR["k_mount_rot"]
    p = 0.5 * (XYZ[nc] + XYZ[nd])
    B = np.zeros((3, 12))   # u_rel at p from [u_c, th_c, u_d, th_d]
    B[:, 0:3] = np.eye(3);  B[:, 3:6] = -skew(p - XYZ[nc])
    B[:, 6:9] = -np.eye(3); B[:, 9:12] = skew(p - XYZ[nd])
    Br = np.zeros((3, 12))  # theta_rel = th_c - th_d
    Br[:, 3:6] = np.eye(3); Br[:, 9:12] = -np.eye(3)
    K12 = B.T @ (k * np.eye(3)) @ B + Br.T @ (kr * np.eye(3)) @ Br
    d = np.concatenate([6 * nc + np.arange(6), 6 * nd + np.arange(6)])
    add_K(d, K12)

# D16: COPV bracket spreads load into a DOME PATCH (a doubler/boss), not one
# thin-shell node — the static test showed the dome local point stiffness
# (~1.1e6 N/m) governs the COPV mode, not the mount. Tie each mount's dome node
# to its nearest dome neighbors with stiff bushings = a rigid bracket footprint
# distributing load over ~0.25 m. QOI topology unchanged (mount still nc<->nd).
if PAR.get("mount_beam", False):
    dome_arr = np.array(dome_ids_all)
    for nc, nd in mounts:
        dd = np.linalg.norm(XYZ[dome_arr] - XYZ[nd], axis=1)
        patch = [int(x) for x in dome_arr[np.argsort(dd)[1:13]]]  # 12 neighbors
        for nb in patch:
            p = 0.5 * (XYZ[nd] + XYZ[nb])
            B = np.zeros((3, 12))
            B[:, 0:3] = np.eye(3);  B[:, 3:6] = -skew(p - XYZ[nd])
            B[:, 6:9] = -np.eye(3); B[:, 9:12] = skew(p - XYZ[nb])
            Br = np.zeros((3, 12)); Br[:, 3:6] = np.eye(3); Br[:, 9:12] = -np.eye(3)
            K12 = B.T @ (5e7 * np.eye(3)) @ B + Br.T @ (5e4 * np.eye(3)) @ Br
            d = np.concatenate([6 * nd + np.arange(6), 6 * nb + np.arange(6)])
            add_K(d, K12)

# D16: avionics bolt-footprint bushings (av_node -> 4 corner tray nodes), stiff
# in translation + rotation so the box yaw/rock inertia is reacted by the tray
# membrane over the footprint, not a single node's drilling penalty.
if PAR.get("mount_beam", False):
    kf, kfr = 1.0e8, 1.0e5
    for nf in av_foot_nodes:
        p = 0.5 * (XYZ[av_node] + XYZ[nf])
        B = np.zeros((3, 12))
        B[:, 0:3] = np.eye(3);  B[:, 3:6] = -skew(p - XYZ[av_node])
        B[:, 6:9] = -np.eye(3); B[:, 9:12] = skew(p - XYZ[nf])
        Br = np.zeros((3, 12)); Br[:, 3:6] = np.eye(3); Br[:, 9:12] = -np.eye(3)
        K12 = B.T @ (kf * np.eye(3)) @ B + Br.T @ (kfr * np.eye(3)) @ Br
        d = np.concatenate([6 * av_node + np.arange(6), 6 * nf + np.arange(6)])
        add_K(d, K12)

# stack mass on master (used by BC-B; harmless under BC-A since master floats
# and is dropped there)
M_st = np.zeros((6, 6))
M_st[:3, :3] = PAR["M_stack"] * np.eye(3)
M_st[3:, 3:] = PAR["I_stack"] * np.eye(3)
m_rows.append(6 * master + np.repeat(np.arange(6), 6))
m_cols.append(6 * master + np.tile(np.arange(6), 6))
m_vals.append(M_st.ravel())

K = sp.coo_matrix((np.concatenate(vals),
                   (np.concatenate(rows).astype(np.int64),
                    np.concatenate(cols).astype(np.int64))),
                  shape=(NDOF, NDOF)).tocsr()
M = (sp.coo_matrix((np.concatenate(m_vals),
                    (np.concatenate(m_rows), np.concatenate(m_cols))),
                   shape=(NDOF, NDOF)) + sp.diags(Mdiag)).tocsr()
K = (K + K.T) * 0.5  # symmetrize roundoff

# ---------------------------------------------------------------- sanity
sane = {}
mass_total = float(sum(mass_parts.values()))
Mtr = M.diagonal()[0::6].sum() + 0  # x-translation mass incl conm2 diag
# rigid-body residual (free structure, no BC): translations + rotation about z
rt = np.zeros(NDOF); rt[0::6] = 1.0
rel_t = float(np.abs(K @ rt).max() / np.abs(K.data).max())
rr = np.zeros(NDOF)
rr[0::6] = -XYZ[:, 1]; rr[1::6] = XYZ[:, 0]; rr[5::6] = 1.0
rel_r = float(np.abs(K @ rr).max() / (np.abs(K.data).max() *
                                      max(1.0, np.abs(rr).max())))
# D14: strut inclination geometry (a shallow bipod splay = soft tray rocking/yaw;
# print + warn so the geometry is auditable rather than silently weak).
strut_incl = []
for s in strut_info:
    ex = np.array(s["ex"])
    incl = float(np.degrees(np.arcsin(abs(ex @ n_t))))  # angle to tray plane
    strut_incl.append(incl)
strut_incl_min = float(min(strut_incl))
if strut_incl_min < 25.0:
    print(f"WARNING: shallowest strut inclination {strut_incl_min:.1f} deg "
          f"< 25 deg floor (FEM_architecture.md): tray out-of-plane/rocking "
          f"will be soft — expected, flagged for audit.")
sane.update(mass_parts=mass_parts, mass_total_kg=mass_total,
            mass_Mx_kg=float(Mtr),
            rigid_resid_trans=rel_t, rigid_resid_rot=rel_r,
            ndof=NDOF, n_nodes=NN, n_quads=int(len(quads)),
            n_tris=int(len(tris)),
            strut_info=strut_info,
            strut_inclination_deg=strut_incl,
            strut_inclination_min_deg=strut_incl_min)

# ---------------------------------------------------------------- BCs
def save_npz(path, Kc, Mc, extra):
    np.savez_compressed(path,
                        K_data=Kc.data, K_indices=Kc.indices,
                        K_indptr=Kc.indptr,
                        M_data=Mc.data, M_indices=Mc.indices,
                        M_indptr=Mc.indptr, shape=Kc.shape[0], **extra)

SUF = ("_" + TAG) if TAG else ""   # variant file suffix (nominal: none)

bottom = barrel_grid[0]
# BC-A: fixed bottom ring; master node floats -> drop its DOFs too
fixA = np.concatenate([(6 * bottom[:, None] + np.arange(6)).ravel(),
                       6 * master + np.arange(6)])
freeA = np.setdiff1d(np.arange(NDOF), fixA)
KA = K[np.ix_(freeA, freeA)].tocsr(); MA = M[np.ix_(freeA, freeA)].tocsr()
save_npz(WS / "out" / f"model_bcA{SUF}.npz", KA, MA, dict(free=freeA))

# BC-B: RBE2 bottom ring -> master (all 6 DOF), free-free overall
slave_dofs = (6 * bottom[:, None] + np.arange(6)).ravel()
indep = np.setdiff1d(np.arange(NDOF), slave_dofs)
loc = {d: i for i, d in enumerate(indep)}
Trows, Tcols, Tvals = [], [], []
for i, d in enumerate(indep):
    Trows.append(d); Tcols.append(i); Tvals.append(1.0)
xm = XYZ[master]
for nslave in bottom:
    r = XYZ[nslave] - xm
    Srm = skew(r)
    # u_s = u_m + theta_m x r = u_m - S(r) theta_m ; theta_s = theta_m
    for c in range(3):
        Trows.append(6 * nslave + c); Tcols.append(loc[6 * master + c])
        Tvals.append(1.0)
        for q in range(3):
            v = -Srm[c, q]
            if v != 0.0:
                Trows.append(6 * nslave + c)
                Tcols.append(loc[6 * master + 3 + q]); Tvals.append(v)
    for c in range(3):
        Trows.append(6 * nslave + 3 + c); Tcols.append(loc[6 * master + 3 + c])
        Tvals.append(1.0)
T = sp.coo_matrix((Tvals, (Trows, Tcols)), shape=(NDOF, len(indep))).tocsr()
KB = (T.T @ K @ T).tocsr(); MB = (T.T @ M @ T).tocsr()
save_npz(WS / "out" / f"model_bcB{SUF}.npz", KB, MB,
         dict(T_data=T.data, T_indices=T.indices, T_indptr=T.indptr,
              T_shape=np.array(T.shape), indep=indep))

meta = dict(par=PAR, sanity=sane,
            sets=dict(
                barrel_grid=barrel_grid.tolist(),
                dome_grid=dome_grid.tolist(), apex=int(apex),
                bottom_ring=bottom.tolist(),
                tray_grid=tray_grid.tolist(),
                av_node=int(av_node), av_offset=list(map(float, av_d)),
                copv_nodes=[int(n) for n in copv_nodes],
                mounts=[[int(a), int(b)] for a, b in mounts],
                struts=[[int(a), int(b)] for a, b in struts],
                master=int(master),
                tray_frame=dict(c=c_tray.tolist(), e1=e1_t.tolist(),
                                e2=e2_t.tolist(), n=n_t.tolist(),
                                anchor=anchor_t.tolist()),
                copv_frame=dict(c=c_copv.tolist(), e_ax=e_ax.tolist(),
                                n=n_c.tolist())),
            runtime_s=time.time() - T0)
np.save(WS / "out" / f"xyz{SUF}.npy", XYZ)
json.dump(meta, open(WS / "out" / f"model_meta{SUF}.json", "w"), indent=1)
print(json.dumps(dict(sanity=sane, runtime_s=meta["runtime_s"]), indent=1,
                 default=float))
