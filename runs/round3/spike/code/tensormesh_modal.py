"""
TensorMesh retest (Python 3.13) — modal + differentiability validation.

Context: Python 3.13.13 was installed via uv, so TensorMesh (PyTorch differentiable FEM) now
installs and imports (it needs py>=3.10; the earlier 3.9.6 box could not run it). This script
tests whether TensorMesh can (a) assemble K and M, (b) give a modal solve that matches the
Euler-Bernoulli cantilever benchmark, and (c) provide gradients suitable for NUTS.

Findings baked into the approach (see report):
- TensorMesh exposes ONLY continuum elements (Line/Tri/Quad/Tet/Hex); NO Euler-Bernoulli beam /
  C1 shell element. So we validate with a SLENDER 2D plane-stress continuum cantilever; its
  frequencies sit slightly BELOW the thin-beam EB benchmark (shear/continuum), shrinking with slenderness.
- The built-in `from_mesh(E=...)` DETACHES E from autograd (material-parameter gradient does NOT
  flow through it). BUT linear-elastic K is exactly linear in E (verified max|K(2E)-2K(E)|=0) and
  M is independent of density, so we assemble UNIT matrices (geometry-differentiable) and scale by
  (E, rho) tensors externally -> full material-parameter autograd is recovered. DOF order = interleaved.
- nu = 0 so the 2D continuum reduces cleanly to EB (no plane-stress/strain ambiguity).
"""
import json, time
import numpy as np
import torch
import tensormesh as tm

torch.set_default_dtype(torch.float64)

HERE = __file__.rsplit("/code/", 1)[0]

# ---- geometry / material (SI) ----
L = 1.0          # m, length
H = 0.02         # m, thickness (slender: L/H = 50)
T = 1.0          # m, out-of-plane thickness (plane stress; cancels in eig)
E0 = 210.0e9     # Pa
NU = 0.0         # -> clean EB reduction
RHO = 7850.0     # kg/m^3
BETA1 = 1.875104 # clamped-free EB first root


def eb_freqs(E, rho, L, A, I, n=3):
    bl = np.array([1.875104, 4.694091, 7.854757])[:n]
    return (bl**2) * np.sqrt(E * I / (rho * A * L**4)) / (2 * np.pi)


def build_unit_matrices(chara_length, order=1):
    """Assemble K at E=1 (geometry-differentiable, then scale by E) and scalar M.
    Returns dense torch tensors K_unit (2N x 2N), M_scalar (N x N), points, left_mask."""
    mesh = tm.Mesh.gen_rectangle(chara_length=chara_length, left=0.0, right=L,
                                 bottom=0.0, top=H, order=order)
    pts = mesh.points
    N = pts.shape[0]
    K_unit = tm.LinearElasticityElementAssembler.from_mesh(mesh, E=1.0, nu=NU)(pts).to_dense()
    M_scalar = tm.MassElementAssembler.from_mesh(mesh)(pts).to_dense()
    K_unit = 0.5 * (K_unit + K_unit.T)
    M_scalar = 0.5 * (M_scalar + M_scalar.T)
    left_mask = (pts[:, 0] < 1e-9)  # clamp left edge nodes (both dofs)
    return K_unit, M_scalar, pts, left_mask, N


def vector_mass(M_scalar, rho, T):
    """Expand scalar consistent mass to interleaved 2-DOF/node vector mass, x rho x thickness."""
    N = M_scalar.shape[0]
    Mv = torch.zeros(2 * N, 2 * N, dtype=M_scalar.dtype)
    Mv[0::2, 0::2] = M_scalar
    Mv[1::2, 1::2] = M_scalar
    return rho * T * Mv


def gen_eig_freqs(K, M, k=3):
    """Differentiable generalized eig K phi = omega^2 M phi via Cholesky whitening."""
    Lc = torch.linalg.cholesky(M)
    Y = torch.linalg.solve(Lc, K)                 # Lc^{-1} K
    A = torch.linalg.solve(Lc, Y.T).T             # Lc^{-1} K Lc^{-T}
    A = 0.5 * (A + A.T)
    evals = torch.linalg.eigvalsh(A)              # ascending, differentiable
    evals = torch.clamp(evals, min=0.0)
    omega = torch.sqrt(evals)
    f = omega / (2 * np.pi)
    return f[:k]


def reduce_free(K, M, left_mask):
    N = left_mask.shape[0]
    free = torch.ones(2 * N, dtype=torch.bool)
    free[0::2][left_mask] = False
    free[1::2][left_mask] = False
    idx = torch.where(free)[0]
    return K[idx][:, idx], M[idx][:, idx]


def f1_of_E(E_scale, K_unit_free, M_free):
    """First natural frequency as a differentiable function of E (K = E * K_unit)."""
    K = E_scale * K_unit_free
    return gen_eig_freqs(K, M_free, k=1)[0]


def main():
    out = {"tool": "TensorMesh " + tm.__version__, "torch": torch.__version__,
           "geometry": {"L_m": L, "H_m": H, "slenderness_LH": L / H, "nu": NU,
                        "E_Pa": E0, "rho_kgm3": RHO}}
    A = H * T
    I = T * H**3 / 12.0
    f_eb = eb_freqs(E0, RHO, L, A, I, n=3)
    out["eb_benchmark_Hz"] = f_eb.tolist()

    # mesh refinement: (order, chara_length) sweep -> shows T3 shear locking and its cure by P2
    conv = {}
    best = None
    runs = [(1, 0.02), (1, 0.01), (1, 0.005), (2, 0.02), (2, 0.01)]
    for order, cl in runs:
        t0 = time.time()
        Ku, Ms, pts, lmask, N = build_unit_matrices(cl, order=order)
        Mv = vector_mass(Ms, RHO, T)
        Kf, Mf = reduce_free(E0 * Ku, Mv, lmask)
        f = gen_eig_freqs(Kf, Mf, k=3).detach().numpy()
        dt = time.time() - t0
        err = 100 * (f - f_eb) / f_eb
        conv[f"P{order}_cl={cl}"] = {"order": order, "n_nodes": int(N),
                                     "n_free_dof": int(Kf.shape[0]),
                                     "f_Hz": f.tolist(), "err_pct_vs_EB": err.tolist(),
                                     "assemble_solve_s": dt}
        # pick P2 cl=0.01 as the accurate+affordable headline mesh for the grad demo
        if order == 2 and cl == 0.01:
            best = (cl, Ku, Ms, lmask, N)
    out["mesh_refinement"] = conv

    # headline mesh (P2, cl=0.01) used for differentiability demo
    cl, Ku, Ms, lmask, N = best
    Mv = vector_mass(Ms, RHO, T)
    # reduce unit K and M to free dofs once
    Kf_unit, Mf = reduce_free(Ku, Mv, lmask)

    # --- differentiability: d f1 / d E via factoring K = E*K_unit ---
    E_t = torch.tensor(E0, requires_grad=True)
    t0 = time.time()
    f1 = f1_of_E(E_t, Kf_unit, Mf)
    f1.backward()
    dt_grad = time.time() - t0
    gE = float(E_t.grad)
    f1v = float(f1)
    ana = f1v / (2 * E0)  # f1 ~ sqrt(E)
    out["differentiability"] = {
        "method": "K(E)=E*K_unit factoring (built-in from_mesh(E=) detaches; verified K linear in E)",
        "f1_Hz": f1v, "df1_dE_autograd": gE, "df1_dE_closedform": ana,
        "rel_err_vs_closedform": abs(gE - ana) / abs(ana),
        "grad_time_s": dt_grad,
        "autograd_through_E_builtin": False,  # documented: detaches
        "autograd_via_factoring": bool(abs(gE - ana) / abs(ana) < 1e-4),
        "geometry_grad_native": True,  # grad wrt mesh.points flows (probed separately)
    }

    # headline comparison at finest mesh
    f_best = gen_eig_freqs(E0 * Kf_unit, Mf, k=3).detach().numpy()
    out["tensormesh_freqs_Hz"] = f_best.tolist()
    out["err_pct_vs_EB"] = (100 * (f_best - f_eb) / f_eb).tolist()

    with open(HERE + "/report/tensormesh_results.json", "w") as fh:
        json.dump(out, fh, indent=2)

    # convergence figure: |err| of mode 1 vs n_free_dof, P1 vs P2
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    for order, mk, lbl in [(1, "o-", "P1 (linear tri) — shear locking"),
                           (2, "s-", "P2 (quadratic tri) — locking cured")]:
        pts_x, pts_y = [], []
        for v in conv.values():
            if v["order"] == order:
                pts_x.append(v["n_free_dof"]); pts_y.append(abs(v["err_pct_vs_EB"][0]))
        order_idx = np.argsort(pts_x)
        ax.loglog(np.array(pts_x)[order_idx], np.array(pts_y)[order_idx], mk, label=lbl)
    ax.axhline(1.0, color="g", ls="--", lw=1, label="1% error")
    ax.set_xlabel("free DOFs (log)"); ax.set_ylabel("|mode-1 error vs EB| % (log)")
    ax.set_title("TensorMesh continuum cantilever -> EB benchmark convergence")
    ax.grid(True, which="both", alpha=0.3); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(HERE + "/report/figures/tensormesh_convergence.png", dpi=130)
    plt.close(fig)

    print("=== TENSORMESH MODAL RETEST (py3.13) ===")
    print("EB benchmark Hz   :", np.round(f_eb, 3))
    for kk, v in conv.items():
        print(f"  {kk:>12}: nodes={v['n_nodes']:>4} f={np.round(v['f_Hz'],3)} "
              f"err%={np.round(v['err_pct_vs_EB'],3)} ({v['assemble_solve_s']:.2f}s)")
    print("finest f Hz       :", np.round(f_best, 3),
          " err% vs EB:", np.round(out["err_pct_vs_EB"], 3))
    d = out["differentiability"]
    print(f"df1/dE autograd(factored)={d['df1_dE_autograd']:.4e} closedform={d['df1_dE_closedform']:.4e} "
          f"relerr={d['rel_err_vs_closedform']:.2e}  ({d['grad_time_s']*1e3:.1f} ms)")
    print("autograd via factoring OK:", d["autograd_via_factoring"],
          "| built-in E-arg detaches:", not d["autograd_through_E_builtin"],
          "| geometry grad native:", d["geometry_grad_native"])


if __name__ == "__main__":
    main()
