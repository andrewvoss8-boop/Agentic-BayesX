"""
JAX Phase-1 hexapod build: hand-assembled flat-shell tray (ACM plate + Q4 membrane)
+ 3-D beam struts with spherical (moment-free) end joints + stiff translational joint
springs, fixed base. Dense generalized eigensolve.

Independent re-derivation: elements in fe_elements.py (own derivation); shares only the
raw spec inputs (shared/spec.py). No K/M, eigen-results, or frequency tables imported
from the CalculiX or TensorMesh builds.

Run (one command):  ../../.venv/bin/python build_jax.py
Outputs: results.json, ../figures/*.png, convergence + jax-gradient demo printed/saved.
"""
import os
import sys
import json
import time
import numpy as np
import scipy.linalg as sla
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Line3DCollection

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "shared"))
import spec  # raw shared inputs only
import fe_elements as fe

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.abspath(os.path.join(HERE, "..", "figures"))
os.makedirs(FIG, exist_ok=True)


# ---------------------------------------------------------------------------
def grid1d(required, target_h):
    """1-D coordinate list that contains all 'required' values and fills each
    gap with ~uniform spacing close to target_h."""
    req = sorted(set(required))
    out = [req[0]]
    for lo, hi in zip(req[:-1], req[1:]):
        n = max(1, int(round((hi - lo) / target_h)))
        for k in range(1, n + 1):
            out.append(lo + (hi - lo) * k / n)
    return np.array(sorted(set(np.round(out, 9))))


def build_model(target_h_mm=30.0):
    """Assemble K, M (numpy) for the hexapod. Returns dict with matrices, node
    coords, dof maps, and bookkeeping."""
    T = spec.TRAY
    z = T["z_mid"]
    apex = spec.apex_m()
    foot = spec.foot_m()

    # tray tensor grid (m); include apex x,y coords exactly
    ax = [a[0] for a in apex.values()]
    ay = [a[1] for a in apex.values()]
    xs = grid1d([-T["Lx"]/2, *ax, T["Lx"]/2], target_h_mm*1e-3)
    ys = grid1d([-T["Ly"]/2, *ay, T["Ly"]/2], target_h_mm*1e-3)
    NX, NY = len(xs), len(ys)

    # node table
    coords = []
    nid = {}
    for j in range(NY):
        for i in range(NX):
            nid[("t", i, j)] = len(coords)
            coords.append([xs[i], ys[j], z])
    # strut nodes (top=apex side, bottom=foot side)
    strut_nodes = {}
    for name, ak, fk in spec.STRUTS:
        nt = len(coords); coords.append(list(apex[ak])); strut_nodes[(name, "top")] = nt
        nb = len(coords); coords.append(list(foot[fk])); strut_nodes[(name, "bot")] = nb
    coords = np.array(coords)
    nn = len(coords)
    ndof = 6 * nn
    K = np.zeros((ndof, ndof))
    M = np.zeros((ndof, ndof))

    def add(Ke, Me, node_list):
        dofs = []
        for n_ in node_list:
            dofs += list(range(6*n_, 6*n_+6))
        idx = np.array(dofs)
        K[np.ix_(idx, idx)] += np.asarray(Ke)
        M[np.ix_(idx, idx)] += np.asarray(Me)

    # tray shell elements
    nelem_tray = 0
    for j in range(NY-1):
        for i in range(NX-1):
            a_half = (xs[i+1]-xs[i])/2.0
            b_half = (ys[j+1]-ys[j])/2.0
            Ke, Me = fe.shell4(a_half, b_half, T["E"], T["nu"], T["t"], T["rho"])
            ns = [nid[("t", i, j)], nid[("t", i+1, j)],
                  nid[("t", i+1, j+1)], nid[("t", i, j+1)]]
            add(Ke, Me, ns)
            nelem_tray += 1

    # struts: 3-D beams (circular tube Iy=Iz=I)
    S = spec.STRUT
    for name, ak, fk in spec.STRUTS:
        nt = strut_nodes[(name, "top")]
        nb = strut_nodes[(name, "bot")]
        Ke, Me, L = fe.beam3d(coords[nt], coords[nb], S["E"], S["A"],
                              S["I"], S["I"], S["J"], S["G"], S["rho"])
        add(Ke, Me, [nt, nb])

    # joint springs (explicit, stiff, translational-only => moment-free spherical)
    kj = spec.JOINT["k_trans"]
    for name, ak, fk in spec.STRUTS:
        nt = strut_nodes[(name, "top")]
        nb = strut_nodes[(name, "bot")]
        apex_node = nid[("t", int(np.where(xs == apex[ak][0])[0][0]),
                              int(np.where(ys == apex[ak][1])[0][0]))]
        # tray-apex <-> strut-top translational coupling
        for d in range(3):
            i = 6*apex_node + d
            jj = 6*nt + d
            K[i, i] += kj; K[jj, jj] += kj
            K[i, jj] -= kj; K[jj, i] -= kj
        # strut-bottom translations grounded (foot fixed) through stiff spring
        for d in range(3):
            K[6*nb + d, 6*nb + d] += kj
        # Ground ONLY the axial-spin rotational mechanism: a beam strut with full
        # spherical (moment-free) releases at both ends can spin freely about its
        # own axis (carries no load, zero strain energy -> spurious rigid mode).
        # Add a small torsional ground about the strut axis at the bottom node;
        # bending rotations stay free (still spherical). k_spin pushes the spin
        # mode far out of band (~kHz); it does not affect structural modes.
        axis = (np.asarray(coords[nt]) - np.asarray(coords[nb]))
        axis = axis/np.linalg.norm(axis)
        k_spin = 1.0e2  # N*m/rad
        Krot = k_spin*np.outer(axis, axis)
        K[6*nb+3:6*nb+6, 6*nb+3:6*nb+6] += Krot

    return dict(K=K, M=M, coords=coords, nid=nid, strut_nodes=strut_nodes,
                xs=xs, ys=ys, NX=NX, NY=NY, nn=nn, ndof=ndof,
                nelem_tray=nelem_tray, apex=apex, foot=foot)


def solve_modes(K, M, nmodes=10, free_free=False, model=None):
    """Generalized eigensolve. Solve M v = mu K v (K p.d.) => mu = 1/omega^2,
    robust to singular M (massless rotational/drilling DOFs)."""
    ndof = K.shape[0]
    # prune dead DOFs: tray drilling (rz) carries no stiffness AND no mass.
    dK = np.abs(np.diag(K)); dM = np.abs(np.diag(M))
    dead = (dK < 1e-9*dK.max()) & (dM < 1e-9*dM.max())
    free = [d for d in range(ndof) if not dead[d]]
    Kf = K[np.ix_(free, free)]
    Mf = M[np.ix_(free, free)]
    if free_free:
        # K singular (rigid body): shift K to make p.d. for the M v = mu (K+sI) v
        # trick is messy; instead solve K v = w2 M v with M regularized.
        eps = 1e-6 * np.trace(Mf)/Mf.shape[0]
        Mr = Mf + eps*np.eye(Mf.shape[0])
        w2 = sla.eigh(Kf, Mr, eigvals_only=True)
        w2 = np.clip(w2, 0, None)
        f = np.sort(np.sqrt(w2)/(2*np.pi))
        return f[:nmodes], None, free
    mu, V = sla.eigh(Mf, Kf)
    order = np.argsort(mu)[::-1]  # largest mu = lowest freq
    mu = mu[order]; V = V[:, order]
    good = mu > 1e-13*mu.max()
    mu = mu[good]; V = V[:, good]
    f = 1.0/(2*np.pi*np.sqrt(mu))
    return f[:nmodes], V[:, :nmodes], free


# ---------------------------------------------------------------------------
def classify_modes(model, f, V, free):
    """Label each mode suspension / tray-flex / strut-self from the shape."""
    coords = model["coords"]; nid = model["nid"]; strut_nodes = model["strut_nodes"]
    NX, NY = model["NX"], model["NY"]
    free_index = {d: i for i, d in enumerate(free)}

    def full_vec(vred):
        u = np.zeros(model["ndof"])
        for d, i in free_index.items():
            u[d] = vred[i]
        return u

    tray_ids = [nid[("t", i, j)] for j in range(NY) for i in range(NX)]
    strut_ids = [v for v in strut_nodes.values()]
    labels = []
    diagnostics = []
    for m in range(V.shape[1]):
        u = full_vec(V[:, m])
        # tray translational displacements
        tray_t = np.array([u[6*n:6*n+3] for n in tray_ids])  # (Ntray,3)
        tray_xyz = coords[tray_ids]
        # fit rigid-body translation+rotation: u ~ t + theta x r
        # build least squares A [tx ty tz rx ry rz] = u
        nN = len(tray_ids)
        A = np.zeros((3*nN, 6)); b = np.zeros(3*nN)
        rc = tray_xyz - tray_xyz.mean(0)
        for k in range(nN):
            A[3*k:3*k+3, 0:3] = np.eye(3)
            x, y, zc = rc[k]
            A[3*k:3*k+3, 3:6] = np.array([[0, zc, -y], [-zc, 0, x], [y, -x, 0]])
            b[3*k:3*k+3] = tray_t[k]
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
        resid = b - A @ sol
        rigid_frac = 1.0 - np.linalg.norm(resid)/(np.linalg.norm(b)+1e-30)
        tray_amp = np.linalg.norm(tray_t)
        # strut interior motion: relative lateral motion of strut nodes vs their
        # endpoints; use total strut translational amplitude
        strut_t = np.array([u[6*n:6*n+3] for n in strut_ids])
        strut_amp = np.linalg.norm(strut_t)
        diagnostics.append(dict(rigid_frac=float(rigid_frac),
                                tray_amp=float(tray_amp),
                                strut_amp=float(strut_amp)))
        if strut_amp > 1.5*tray_amp:
            labels.append("strut-self")
        elif rigid_frac > 0.9:
            labels.append("suspension")
        else:
            labels.append("tray-flex")
    return labels, diagnostics


# ---------------------------------------------------------------------------
def fig_undeformed(model):
    coords = model["coords"]; nid = model["nid"]; sn = model["strut_nodes"]
    NX, NY = model["NX"], model["NY"]
    fig = plt.figure(figsize=(7, 6))
    ax = fig.add_subplot(111, projection="3d")
    # tray grid lines
    segs = []
    for j in range(NY):
        for i in range(NX-1):
            segs.append([coords[nid[("t", i, j)]], coords[nid[("t", i+1, j)]]])
    for i in range(NX):
        for j in range(NY-1):
            segs.append([coords[nid[("t", i, j)]], coords[nid[("t", i, j+1)]]])
    ax.add_collection3d(Line3DCollection(segs, colors="0.6", linewidths=0.4))
    # struts
    for name, ak, fk in spec.STRUTS:
        p1 = coords[sn[(name, "top")]]; p2 = coords[sn[(name, "bot")]]
        ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], "-", color="C3", lw=2)
    ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2], s=2, color="0.3")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
    ax.set_title("JAX build — undeformed mesh\n(ACM/Q4 shell tray + beam struts, fixed base)")
    _set_axes_equal(ax)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "jax_undeformed_mesh.png"), dpi=130)
    plt.close(fig)


def fig_modes(model, f, V, free, labels, nshow=6):
    coords = model["coords"]; nid = model["nid"]; sn = model["strut_nodes"]
    NX, NY = model["NX"], model["NY"]
    free_index = {d: i for i, d in enumerate(free)}

    def full_vec(vred):
        u = np.zeros(model["ndof"])
        for d, i in free_index.items():
            u[d] = vred[i]
        return u

    fig = plt.figure(figsize=(13, 8))
    for m in range(min(nshow, V.shape[1])):
        u = full_vec(V[:, m])
        disp = u.reshape(-1, 6)[:, :3]
        scale = 0.06 / (np.abs(disp).max() + 1e-30)
        dc = coords + scale*disp
        ax = fig.add_subplot(2, 3, m+1, projection="3d")
        # deformed tray surface (z displacement colored)
        X = np.array([[dc[nid[("t", i, j)], 0] for i in range(NX)] for j in range(NY)])
        Y = np.array([[dc[nid[("t", i, j)], 1] for i in range(NX)] for j in range(NY)])
        Z = np.array([[dc[nid[("t", i, j)], 2] for i in range(NX)] for j in range(NY)])
        ax.plot_surface(X, Y, Z, cmap="coolwarm", alpha=0.85, linewidth=0,
                        antialiased=True)
        for name, ak, fk in spec.STRUTS:
            p1 = dc[sn[(name, "top")]]; p2 = dc[sn[(name, "bot")]]
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], [p1[2], p2[2]], "-",
                    color="0.2", lw=1.5)
        ax.set_title(f"Mode {m+1}: {f[m]:.1f} Hz\n{labels[m]}", fontsize=9)
        ax.set_xticks([]); ax.set_yticks([]); ax.set_zticks([])
        _set_axes_equal(ax)
    fig.suptitle("JAX build — first 6 mode shapes (rigid joints = provisional upper bound)",
                 fontsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "jax_mode_shapes.png"), dpi=130)
    plt.close(fig)


def _set_axes_equal(ax):
    limits = np.array([ax.get_xlim3d(), ax.get_ylim3d(), ax.get_zlim3d()])
    span = limits[:, 1] - limits[:, 0]
    centers = limits.mean(1)
    r = 0.5*span.max()
    ax.set_xlim3d(centers[0]-r, centers[0]+r)
    ax.set_ylim3d(centers[1]-r, centers[1]+r)
    ax.set_zlim3d(centers[2]-r, centers[2]+r)


# ---------------------------------------------------------------------------
def jax_gradient_demo():
    """Demonstrate the forward model is jax-differentiable: d f_lowest / d E_strut
    via a compact jnp assembly of the 6-strut suspension (rigid tray) sub-model.
    This is the future-NUTS hook; Phase 1 still reports the full eigensolve above."""
    try:
        import jax
        import jax.numpy as jnp
        from jax.scipy.linalg import eigh as jeigh
    except Exception as e:
        return {"available": False, "reason": str(e)}

    apex = spec.apex_m(); foot = spec.foot_m()
    S = spec.STRUT; T = spec.TRAY
    mass = T["rho"]*T["Lx"]*T["Ly"]*T["t"]
    # rigid tray: 3 translational DOF lumped mass; struts as axial springs to ground
    def f_lowest(E):
        k = jnp.zeros((3, 3))
        for name, ak, fk in spec.STRUTS:
            v = apex[ak] - foot[fk]
            L = jnp.linalg.norm(jnp.array(v))
            ka = E*S["A"]/L
            d = jnp.array(v)/L
            k = k + ka*jnp.outer(d, d)
        Mm = mass*jnp.eye(3)
        # standard eig via Cholesky of M
        Lc = jnp.linalg.cholesky(Mm)
        Linv = jnp.linalg.inv(Lc)
        A = Linv @ k @ Linv.T
        w2 = jnp.linalg.eigvalsh(A)
        return jnp.sqrt(jnp.min(w2))/(2*jnp.pi)
    val = float(f_lowest(S["E"]))
    grad = float(jax.grad(f_lowest)(S["E"]))
    return {"available": True, "f_lowest_axial_Hz": val,
            "d_f_lowest_d_Estrut_Hz_per_Pa": grad,
            "note": "compact axial-suspension submodel; proves param->freq is jax-grad-able"}


# ---------------------------------------------------------------------------
def main():
    t0 = time.time()
    runtime = {"commands": []}

    # baseline build
    tb = time.time()
    model = build_model(target_h_mm=30.0)
    f, V, free = solve_modes(model["K"], model["M"], nmodes=12, model=model)
    runtime["commands"].append({"name": "baseline_solve", "s": time.time()-tb})
    labels, diags = classify_modes(model, f, V, free)

    # free-free sanity (expect 6 near-zero rigid-body modes)
    Kff = model["K"].copy()
    # remove grounding: rebuild without grounded springs by subtracting kj on bot nodes
    # easier: rebuild a free-free model
    ff = build_model_freefree(target_h_mm=30.0)
    f_ff, _, _ = solve_modes(ff["K"], ff["M"], nmodes=10, free_free=True)

    # mesh convergence: coarse vs fine
    tb = time.time()
    model_c = build_model(target_h_mm=45.0)
    f_c, _, _ = solve_modes(model_c["K"], model_c["M"], nmodes=12, model=model_c)
    model_f = build_model(target_h_mm=20.0)
    f_f, _, _ = solve_modes(model_f["K"], model_f["M"], nmodes=12, model=model_f)
    runtime["commands"].append({"name": "convergence_solve", "s": time.time()-tb})

    # figures
    fig_undeformed(model)
    fig_modes(model, f, V, free, labels, nshow=6)

    # jax differentiability demo
    grad_demo = jax_gradient_demo()

    # near-degenerate pairs
    pairs = []
    for i in range(len(f)-1):
        rel = abs(f[i+1]-f[i])/max(f[i], 1e-9)
        if rel < 0.05:
            pairs.append([i+1, i+2, round(float(rel), 4)])

    elapsed = time.time()-t0
    nmode = min(10, len(f))
    results = {
        "agent": "opus",
        "tool": "jax",
        "solved_by": "opus",
        "units": "SI (m, kg, N, Hz)",
        "frame": "origin at tray center; +z up; tray mid-plane z=0.098 m; base z=0",
        "mass_case": "bare tray, no ballast; emergent shell mass ~3.086 kg",
        "boundary_condition": "feet fixed (grounded via stiff joint springs)",
        "joint_status": "RIGID (k_trans=1e9 N/m, translational-only => moment-free)",
        "frequencies_hz": [round(float(x), 3) for x in f[:nmode]],
        "frequency_label": "PROVISIONAL UPPER BOUND (rigid joints; real compliant joints lower these)",
        "mode_type": labels[:nmode],
        "mode_diagnostics": diags[:nmode],
        "element_types": {
            "tray": "flat shell = ACM/MZC non-conforming plate bending (12 DOF) + Q4 plane-stress membrane (8 DOF)",
            "struts": "3-D Euler-Bernoulli 2-node beam, consistent mass, spherical (moment-free) end joints",
            "joints": "explicit stiff translational springs (k=1e9 N/m)"},
        "mesh": {"tray_grid": f"{model['NX']}x{model['NY']} nodes, {model['nelem_tray']} shell elements",
                 "dof_total": int(model["ndof"]),
                 "target_h_mm": 30.0},
        "mesh_convergence": {
            "coarse_h45_hz": [round(float(x), 3) for x in f_c[:nmode]],
            "baseline_h30_hz": [round(float(x), 3) for x in f[:nmode]],
            "fine_h20_hz": [round(float(x), 3) for x in f_f[:nmode]],
            "max_abs_shift_h30_to_h20_hz": round(float(np.max(np.abs(f_f[:nmode]-f[:nmode]))), 3),
            "max_pct_shift_h30_to_h20": round(float(np.max(np.abs((f_f[:nmode]-f[:nmode])/f[:nmode]))*100), 2)},
        "near_degenerate_pairs": pairs,
        "fixed_base_no_zero_modes": bool(f[0] > 1.0),
        "fixed_base_lowest_mode_hz": round(float(f[0]), 3),
        "free_free_note": ("free-free is NOT a clean 6-rigid-body-mode check for this "
                           "model: each moment-free (spherical-both-ends) beam strut adds "
                           "a zero-energy swing mechanism when ungrounded, so the ungrounded "
                           "model shows 6 rigid-body + 6 strut-swing ~zero modes. The "
                           "grounding sanity check used instead is: fixed-base lowest mode "
                           "= %.1f Hz (>> 0), i.e. no spurious rigid-body mode of the "
                           "suspended tray." % float(f[0])),
        "free_free_lowest8_hz": [round(float(x), 4) for x in f_ff[:8]],
        "jax_differentiable_forward_model_demo": grad_demo,
        "integrity": "independent re-derivation; shares only shared/spec.py raw inputs; no porting of K/M, eigen-results, or frequency tables from other tools/agents",
        "runtime_s": round(elapsed, 2),
    }
    with open(os.path.join(HERE, "..", "results.json"), "w") as fo:
        json.dump(results, fo, indent=2)
    runtime["active_runtime_s"] = round(sum(c["s"] for c in runtime["commands"]), 2)
    runtime["elapsed_wallclock_s"] = round(elapsed, 2)
    with open(os.path.join(HERE, "..", "runtime.json"), "w") as fo:
        json.dump(runtime, fo, indent=2)

    print("First {} frequencies (Hz):".format(nmode))
    for i in range(nmode):
        print(f"  mode {i+1:2d}: {f[i]:8.2f} Hz   {labels[i]}")
    print("free-free first 8 (NOT a clean 6-RBM check; moment-free struts add swing modes):",
          np.round(f_ff[:8], 3))
    print("near-degenerate pairs:", pairs)
    print("max % shift h30->h20:", results["mesh_convergence"]["max_pct_shift_h30_to_h20"])
    print("jax grad demo:", grad_demo)
    print("DOF:", model["ndof"], " elapsed %.1fs" % elapsed)


def build_model_freefree(target_h_mm=30.0):
    """Same model but with NO grounding springs (struts free at the base)
    -> free-free sanity check for 6 rigid-body modes."""
    m = build_model(target_h_mm=target_h_mm)
    # subtract the grounded-bottom spring stiffness we added
    kj = spec.JOINT["k_trans"]
    for name, ak, fk in spec.STRUTS:
        nb = m["strut_nodes"][(name, "bot")]
        for d in range(3):
            m["K"][6*nb + d, 6*nb + d] -= kj
    return m


if __name__ == "__main__":
    main()
