"""
TensorMesh (discretize) Phase-1 hexapod build.

discretize.TensorMesh is used as the STRUCTURED MESH GENERATOR for a continuum SOLID
tray (3-D linear elasticity on trilinear H8 hexahedra), with the six struts as 3-D
BAR/TRUSS members (axial two-force, matching the spherical-jointed push-rods) tied to
the tray through stiff joint springs, base feet fixed. Assemble sparse K and M; solve
the generalized eigenproblem with scipy.sparse.linalg.eigsh (shift-invert).

Independent re-derivation: H8 + truss assembly is derived here; shares only the raw
spec inputs (shared/spec.py). No K/M, eigen-results, or frequency tables imported from
the JAX, CalculiX, or Nastran builds. This build deliberately uses a DIFFERENT tray
idealization (solid hex) and DIFFERENT strut element (truss) than the JAX build, so the
cross-software comparison tests element theory, not a shared assembly.

Run: ../../.venv/bin/python build_tensormesh.py
"""
import os
import sys
import json
import time
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection
import discretize

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import spec

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.abspath(os.path.join(HERE, "..", "figures"))
os.makedirs(FIG, exist_ok=True)

# ---------------------------------------------------------------------------
# H8 trilinear hexahedron, 3-D isotropic elasticity.
# ---------------------------------------------------------------------------
_GP = [-1/np.sqrt(3), 1/np.sqrt(3)]


def _hex_shape(xi, eta, zeta):
    s = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                  [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)
    N = 0.125*(1+s[:, 0]*xi)*(1+s[:, 1]*eta)*(1+s[:, 2]*zeta)
    dN = np.zeros((8, 3))
    dN[:, 0] = 0.125*s[:, 0]*(1+s[:, 1]*eta)*(1+s[:, 2]*zeta)
    dN[:, 1] = 0.125*s[:, 1]*(1+s[:, 0]*xi)*(1+s[:, 2]*zeta)
    dN[:, 2] = 0.125*s[:, 2]*(1+s[:, 0]*xi)*(1+s[:, 1]*eta)
    return N, dN


def hex_KM(node_xyz, E, nu, rho):
    """24x24 K, M for a hex with 8 node coords (8x3)."""
    lam = E*nu/((1+nu)*(1-2*nu))
    mu = E/(2*(1+nu))
    D = np.array([
        [lam+2*mu, lam, lam, 0, 0, 0],
        [lam, lam+2*mu, lam, 0, 0, 0],
        [lam, lam, lam+2*mu, 0, 0, 0],
        [0, 0, 0, mu, 0, 0],
        [0, 0, 0, 0, mu, 0],
        [0, 0, 0, 0, 0, mu]], float)
    K = np.zeros((24, 24)); M = np.zeros((24, 24))
    for xi in _GP:
        for eta in _GP:
            for zeta in _GP:
                N, dN = _hex_shape(xi, eta, zeta)
                J = dN.T @ node_xyz           # 3x3
                detJ = np.linalg.det(J)
                dNx = np.linalg.solve(J, dN.T).T  # 8x3 d/dx
                B = np.zeros((6, 24))
                for a in range(8):
                    bx, by, bz = dNx[a]
                    c = 3*a
                    B[0, c] = bx; B[1, c+1] = by; B[2, c+2] = bz
                    B[3, c] = by; B[3, c+1] = bx
                    B[4, c+1] = bz; B[4, c+2] = by
                    B[5, c] = bz; B[5, c+2] = bx
                K += (B.T @ D @ B)*detJ
                Nm = np.zeros((3, 24))
                for a in range(8):
                    Nm[0, 3*a] = N[a]; Nm[1, 3*a+1] = N[a]; Nm[2, 3*a+2] = N[a]
                M += rho*(Nm.T @ Nm)*detJ
    return K, M


def truss_KM(p1, p2, E, A, rho):
    """6x6 (2 nodes x 3 trans) axial bar; consistent mass."""
    d = p2-p1
    L = np.linalg.norm(d)
    t = d/L
    k = E*A/L
    T = np.outer(t, t)
    K = np.block([[T, -T], [-T, T]])*k
    m = rho*A*L
    M = np.zeros((6, 6))
    # consistent truss mass: [[2I, I],[I,2I]]*mL/6
    M[:3, :3] = 2*np.eye(3); M[3:, 3:] = 2*np.eye(3)
    M[:3, 3:] = np.eye(3); M[3:, :3] = np.eye(3)
    M *= m/6.0
    return K, M


# ---------------------------------------------------------------------------
def grid1d(required, target_h):
    req = sorted(set(required))
    out = [req[0]]
    for lo, hi in zip(req[:-1], req[1:]):
        n = max(1, int(round((hi-lo)/target_h)))
        for k in range(1, n+1):
            out.append(lo+(hi-lo)*k/n)
    return np.array(sorted(set(np.round(out, 9))))


def build(target_h_mm=20.0, nz=2):
    T = spec.TRAY
    apex = spec.apex_m(); foot = spec.foot_m()
    ax = [a[0] for a in apex.values()]; ay = [a[1] for a in apex.values()]
    xg = grid1d([-T["Lx"]/2, *ax, T["Lx"]/2], target_h_mm*1e-3)
    yg = grid1d([-T["Ly"]/2, *ay, T["Ly"]/2], target_h_mm*1e-3)
    z0 = T["z_mid"]-T["t"]/2
    zg = np.linspace(z0, z0+T["t"], nz+1)
    hx = np.diff(xg); hy = np.diff(yg); hz = np.diff(zg)
    mesh = discretize.TensorMesh([hx, hy, hz], origin=[xg[0], yg[0], zg[0]])
    nodes = mesh.nodes  # (Nn,3), ordering x fastest
    NX, NY, NZ = len(xg), len(yg), len(zg)

    def nidx(i, j, k):
        return i + j*NX + k*NX*NY  # discretize TensorMesh node ordering (x,y,z)

    # verify node ordering matches our index formula
    assert np.allclose(nodes[nidx(1, 0, 0)], [xg[1], yg[0], zg[0]]), "node order"

    n_tray = nodes.shape[0]
    # strut nodes appended: top + bottom per strut
    strut_nodes = {}
    extra = []
    for name, ak, fk in spec.STRUTS:
        strut_nodes[(name, "top")] = n_tray + len(extra); extra.append(apex[ak])
        strut_nodes[(name, "bot")] = n_tray + len(extra); extra.append(foot[fk])
    allnodes = np.vstack([nodes, np.array(extra)])
    nn = allnodes.shape[0]
    ndof = 3*nn

    K = sp.lil_matrix((ndof, ndof))
    M = sp.lil_matrix((ndof, ndof))

    def scatter(Ke, Me, node_ids):
        dofs = np.array([3*n+d for n in node_ids for d in range(3)])
        K[np.ix_(dofs, dofs)] += Ke
        M[np.ix_(dofs, dofs)] += Me

    # tray hexes
    nelem = 0
    for k in range(NZ-1):
        for j in range(NY-1):
            for i in range(NX-1):
                ids = [nidx(i, j, k), nidx(i+1, j, k), nidx(i+1, j+1, k), nidx(i, j+1, k),
                       nidx(i, j, k+1), nidx(i+1, j, k+1), nidx(i+1, j+1, k+1), nidx(i, j+1, k+1)]
                Ke, Me = hex_KM(allnodes[ids], T["E"], T["nu"], T["rho"])
                scatter(Ke, Me, ids)
                nelem += 1

    # struts (truss) + joint springs
    S = spec.STRUT
    kj = spec.JOINT["k_trans"]
    mid_k = (NZ-1)//2  # tray mid-plane node layer (z=0.098 when nz even)
    # find x,y indices of each apex on tray grid
    for name, ak, fk in spec.STRUTS:
        nt = strut_nodes[(name, "top")]; nb = strut_nodes[(name, "bot")]
        Ke, Me = truss_KM(allnodes[nt], allnodes[nb], S["E"], S["A"], S["rho"])
        scatter(Ke, Me, [nt, nb])
        ix = int(np.argmin(np.abs(xg-apex[ak][0])))
        iy = int(np.argmin(np.abs(yg-apex[ak][1])))
        tray_node = nidx(ix, iy, mid_k)
        # joint spring tray<->strut-top (translational)
        for d in range(3):
            a = 3*tray_node+d; b = 3*nt+d
            K[a, a] += kj; K[b, b] += kj; K[a, b] -= kj; K[b, a] -= kj
        # strut-bottom grounded (foot fixed) via stiff spring
        for d in range(3):
            K[3*nb+d, 3*nb+d] += kj

    return dict(K=sp.csr_matrix(K), M=sp.csr_matrix(M), nodes=allnodes,
                NX=NX, NY=NY, NZ=NZ, nidx=nidx, mid_k=mid_k, n_tray=n_tray,
                strut_nodes=strut_nodes, nelem=nelem, ndof=ndof, xg=xg, yg=yg, zg=zg)


def solve(model, nmodes=12):
    K = model["K"].tocsc(); M = model["M"].tocsc()
    # shift-invert around 0 for smallest eigenvalues (K p.d., M p.d.)
    vals, vecs = spla.eigsh(K, k=nmodes, M=M, sigma=0.0, which="LM")
    order = np.argsort(vals)
    vals = vals[order]; vecs = vecs[:, order]
    vals = np.clip(vals, 0, None)
    f = np.sqrt(vals)/(2*np.pi)
    return f, vecs


def classify(model, f, V):
    nodes = model["nodes"]; NX, NY, NZ = model["NX"], model["NY"], model["NZ"]
    nidx = model["nidx"]; mid_k = model["mid_k"]
    tray_ids = [nidx(i, j, mid_k) for j in range(NY) for i in range(NX)]
    strut_ids = list(model["strut_nodes"].values())
    labels = []; diag = []
    for m in range(V.shape[1]):
        u = V[:, m]
        tt = np.array([u[3*n:3*n+3] for n in tray_ids])
        txyz = nodes[tray_ids]
        nN = len(tray_ids)
        A = np.zeros((3*nN, 6)); b = np.zeros(3*nN)
        rc = txyz-txyz.mean(0)
        for kk in range(nN):
            A[3*kk:3*kk+3, :3] = np.eye(3)
            x, y, z = rc[kk]
            A[3*kk:3*kk+3, 3:] = [[0, z, -y], [-z, 0, x], [y, -x, 0]]
            b[3*kk:3*kk+3] = tt[kk]
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
        resid = b-A@sol
        rigid = 1.0-np.linalg.norm(resid)/(np.linalg.norm(b)+1e-30)
        tray_amp = np.linalg.norm(tt)
        st = np.array([u[3*n:3*n+3] for n in strut_ids])
        strut_amp = np.linalg.norm(st)
        diag.append(dict(rigid_frac=float(rigid), tray_amp=float(tray_amp),
                         strut_amp=float(strut_amp)))
        if strut_amp > 1.5*tray_amp:
            labels.append("strut-self")
        elif rigid > 0.9:
            labels.append("suspension")
        else:
            labels.append("tray-flex")
    return labels, diag


def fig_undeformed(model):
    nodes = model["nodes"]; NX, NY, NZ = model["NX"], model["NY"], model["NZ"]
    nidx = model["nidx"]; sn = model["strut_nodes"]
    fig = plt.figure(figsize=(7, 6)); ax = fig.add_subplot(111, projection="3d")
    k = NZ-1
    segs = []
    for j in range(NY):
        for i in range(NX-1):
            segs.append([nodes[nidx(i, j, k)], nodes[nidx(i+1, j, k)]])
    for i in range(NX):
        for j in range(NY-1):
            segs.append([nodes[nidx(i, j, k)], nodes[nidx(i, j+1, k)]])
    ax.add_collection3d(Line3DCollection(segs, colors="0.6", linewidths=0.4))
    for name, ak, fk in spec.STRUTS:
        p1 = nodes[sn[(name, "top")]]; p2 = nodes[sn[(name, "bot")]]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], "-", color="C3", lw=2)
    ax.set_title("TensorMesh build — undeformed mesh\n(solid H8 tray + truss struts, fixed base)")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
    _eq(ax); fig.tight_layout()
    fig.savefig(os.path.join(FIG, "tensormesh_undeformed_mesh.png"), dpi=130); plt.close(fig)


def fig_modes(model, f, V, labels, nshow=6):
    nodes = model["nodes"]; NX, NY, NZ = model["NX"], model["NY"], model["NZ"]
    nidx = model["nidx"]; sn = model["strut_nodes"]
    fig = plt.figure(figsize=(13, 8))
    k = NZ-1
    for m in range(min(nshow, V.shape[1])):
        u = V[:, m].reshape(-1, 3)
        scale = 0.06/(np.abs(u).max()+1e-30)
        dc = nodes+scale*u
        ax = fig.add_subplot(2, 3, m+1, projection="3d")
        X = np.array([[dc[nidx(i, j, k), 0] for i in range(NX)] for j in range(NY)])
        Y = np.array([[dc[nidx(i, j, k), 1] for i in range(NX)] for j in range(NY)])
        Z = np.array([[dc[nidx(i, j, k), 2] for i in range(NX)] for j in range(NY)])
        ax.plot_surface(X, Y, Z, cmap="coolwarm", alpha=0.85, linewidth=0)
        for name, ak, fk in spec.STRUTS:
            p1 = dc[sn[(name, "top")]]; p2 = dc[sn[(name, "bot")]]
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], "-", color="0.2", lw=1.5)
        ax.set_title(f"Mode {m+1}: {f[m]:.1f} Hz\n{labels[m]}", fontsize=9)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([]); _eq(ax)
    fig.suptitle("TensorMesh build — first 6 mode shapes (rigid joints = provisional upper bound)")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "tensormesh_mode_shapes.png"), dpi=130)
    plt.close(fig)


def _eq(ax):
    lim = np.array([ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()])
    c = lim.mean(1); r = 0.5*(lim[:, 1]-lim[:, 0]).max()
    ax.set_xlim3d(c[0]-r, c[0]+r); ax.set_ylim3d(c[1]-r, c[1]+r); ax.set_zlim3d(c[2]-r, c[2]+r)


def main():
    t0 = time.time(); rt = {"commands": []}
    tb = time.time()
    model = build(target_h_mm=20.0, nz=2)
    f, V = solve(model, nmodes=12)
    rt["commands"].append({"name": "baseline", "s": time.time()-tb})
    labels, diag = classify(model, f, V)

    tb = time.time()
    mc = build(target_h_mm=30.0, nz=2); fc, _ = solve(mc, 12)
    mf = build(target_h_mm=12.0, nz=2); ff, _ = solve(mf, 12)
    rt["commands"].append({"name": "convergence", "s": time.time()-tb})

    fig_undeformed(model); fig_modes(model, f, V, labels)

    nmode = min(10, len(f))
    pairs = [[i+1, i+2, round(float(abs(f[i+1]-f[i])/max(f[i], 1e-9)), 4)]
             for i in range(len(f)-1) if abs(f[i+1]-f[i])/max(f[i], 1e-9) < 0.05]
    results = {
        "agent": "opus", "tool": "tensormesh", "solved_by": "opus",
        "units": "SI (m, kg, N, Hz)",
        "frame": "origin at tray center; +z up; tray mid-plane z=0.098 m; base z=0",
        "mass_case": "bare tray, no ballast; emergent solid-hex mass ~3.086 kg",
        "boundary_condition": "feet fixed (grounded via stiff joint springs)",
        "joint_status": "RIGID (k_trans=1e9 N/m, translational => moment-free)",
        "frequencies_hz": [round(float(x), 3) for x in f[:nmode]],
        "frequency_label": "PROVISIONAL UPPER BOUND (rigid joints; real compliant joints lower these)",
        "mode_type": labels[:nmode], "mode_diagnostics": diag[:nmode],
        "element_types": {
            "tray": "solid trilinear hexahedron H8 (3-D isotropic elasticity, 2x2x2 Gauss, full integration) on discretize.TensorMesh",
            "struts": "3-D bar/truss (axial two-force member; matches spherical-jointed push-rod), consistent mass",
            "joints": "explicit stiff translational springs (k=1e9 N/m)"},
        "mesh": {"tray_grid": f"{model['NX']}x{model['NY']}x{model['NZ']} nodes, {model['nelem']} H8 elements",
                 "dof_total": int(model["ndof"]), "target_h_mm": 20.0, "nz_cells": 2},
        "mesh_convergence": {
            "coarse_h30_hz": [round(float(x), 3) for x in fc[:nmode]],
            "baseline_h20_hz": [round(float(x), 3) for x in f[:nmode]],
            "fine_h12_hz": [round(float(x), 3) for x in ff[:nmode]],
            "max_abs_shift_h20_to_h12_hz": round(float(np.max(np.abs(ff[:nmode]-f[:nmode]))), 3),
            "max_pct_shift_h20_to_h12": round(float(np.max(np.abs((ff[:nmode]-f[:nmode])/f[:nmode]))*100), 2),
            "note": "trilinear H8 full integration is stiff in bending (shear locking); tray-flex modes converge from above and are the most mesh-sensitive. Suspension modes (rigid-tray) are nearly mesh-independent."},
        "near_degenerate_pairs": pairs,
        "fixed_base_no_zero_modes": bool(f[0] > 1.0),
        "fixed_base_lowest_mode_hz": round(float(f[0]), 3),
        "integrity": "independent re-derivation; shares only shared/spec.py raw inputs; solid-hex tray + truss struts deliberately differ from the JAX plate-shell + beam build; no porting of K/M, eigen-results, or frequency tables.",
        "runtime_s": round(time.time()-t0, 2)}
    with open(os.path.join(HERE, "..", "results.json"), "w") as fo:
        json.dump(results, fo, indent=2)
    rt["active_runtime_s"] = round(sum(c["s"] for c in rt["commands"]), 2)
    rt["elapsed_wallclock_s"] = round(time.time()-t0, 2)
    with open(os.path.join(HERE, "..", "runtime.json"), "w") as fo:
        json.dump(rt, fo, indent=2)
    print("First %d freqs (Hz):" % nmode)
    for i in range(nmode):
        print(f"  mode {i+1:2d}: {f[i]:8.2f} Hz  {labels[i]}")
    print("pairs:", pairs)
    print("max %% shift h20->h12:", results["mesh_convergence"]["max_pct_shift_h20_to_h12"])
    print("DOF:", model["ndof"], "elapsed %.1fs" % (time.time()-t0))


if __name__ == "__main__":
    main()
