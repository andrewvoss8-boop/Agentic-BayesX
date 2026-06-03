"""
FEM feasibility spike for Agentic BayesX, round 3.

Goal: minimal DIFFERENTIABLE FEM, end-to-end, validated against an analytical benchmark.

Tool decision (see report/spike_report.md and commands.md for evidence):
  - PREFERRED tool TensorMesh (PyTorch) REFUSED to run: tensormesh-fem 0.1.1 requires
    Python >=3.10 and uses PEP-604 'X | Y' annotations that raise TypeError on the only
    available interpreter (Python 3.9.6). No Python 3.10+ / brew / pyenv on this machine.
  - scikit-fem assembles K,M but is NOT autodiff, so it cannot exercise the differentiability
    requirement that the real NUTS pipeline needs.
  - The project's NUTS sampler stack is JAX/numpyro (.venv_nuts). So this spike falls back to
    a FIRST-PRINCIPLES Euler-Bernoulli beam FEM assembled by hand IN JAX. This is the
    "assemble K and M yourself" path, but in JAX so gradients flow (jax.grad) for NUTS.

Component: 1D Euler-Bernoulli cantilever beam (clamped-free), 2-node Hermite-cubic elements,
DOFs per node = [transverse displacement w, rotation theta]. Consistent mass matrix.

Validation benchmark (analytical, e.g. Blevins / vibrationdata-Irvine cantilever):
  omega_n = (betaL_n)^2 * sqrt(EI / (rho * A * L^4)),  betaL = 1.875104, 4.694091, 7.854757,
  10.995541, 14.137168 (clamped-free).

Units: strict SI (m, kg, s, Pa, N).
"""
import json
import time
import numpy as np
import jax
import jax.numpy as jnp
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

jax.config.update("jax_enable_x64", True)  # float64: eigenvalues need it

HERE = __file__.rsplit("/code/", 1)[0]
FIGDIR = HERE + "/report/figures"

# ----------------------------------------------------------------------------
# Beam properties (SI). Steel rectangular cross-section.
# ----------------------------------------------------------------------------
E0 = 210.0e9        # Pa, Young's modulus (steel)
RHO = 7850.0        # kg/m^3, density (steel)
L = 1.0             # m, beam length
B = 0.050           # m, cross-section width
H0 = 0.005          # m, cross-section thickness (height)

BETA_L = np.array([1.875104, 4.694091, 7.854757, 10.995541, 14.137168])


def section(b, h):
    A = b * h                 # m^2, area
    I = b * h ** 3 / 12.0     # m^4, second moment of area
    return A, I


def analytical_freqs(E, rho, L, A, I, n=5):
    """Analytical clamped-free Euler-Bernoulli natural frequencies (Hz)."""
    wn = (BETA_L[:n] ** 2) * np.sqrt(E * I / (rho * A * L ** 4))  # rad/s
    return wn / (2.0 * np.pi)


# ----------------------------------------------------------------------------
# Element matrices (Euler-Bernoulli, Hermite cubic). DOF order [w1,th1,w2,th2].
# ----------------------------------------------------------------------------
def beam_element_K(EI, le):
    le2 = le * le
    le3 = le2 * le
    k = jnp.array([
        [12.0,    6.0 * le,   -12.0,    6.0 * le],
        [6.0 * le, 4.0 * le2, -6.0 * le, 2.0 * le2],
        [-12.0,  -6.0 * le,    12.0,   -6.0 * le],
        [6.0 * le, 2.0 * le2, -6.0 * le, 4.0 * le2],
    ])
    return (EI / le3) * k


def beam_element_M(rhoA, le):
    le2 = le * le
    m = jnp.array([
        [156.0,    22.0 * le,   54.0,   -13.0 * le],
        [22.0 * le, 4.0 * le2,  13.0 * le, -3.0 * le2],
        [54.0,    13.0 * le,   156.0,  -22.0 * le],
        [-13.0 * le, -3.0 * le2, -22.0 * le, 4.0 * le2],
    ])
    return (rhoA * le / 420.0) * m


def assemble(E, rho, L, A, I, nele):
    """Assemble global K, M (JAX) and return clamped (free) reduced matrices.
    Cantilever: node 0 clamped -> remove DOFs 0 (w0) and 1 (theta0)."""
    nnode = nele + 1
    ndof = 2 * nnode
    le = L / nele
    EI = E * I
    rhoA = rho * A
    Ke = beam_element_K(EI, le)
    Me = beam_element_M(rhoA, le)
    K = jnp.zeros((ndof, ndof))
    M = jnp.zeros((ndof, ndof))
    for e in range(nele):
        d = jnp.array([2 * e, 2 * e + 1, 2 * e + 2, 2 * e + 3])
        K = K.at[jnp.ix_(d, d)].add(Ke)
        M = M.at[jnp.ix_(d, d)].add(Me)
    free = jnp.arange(2, ndof)  # drop clamped DOFs 0,1
    Kr = K[jnp.ix_(free, free)]
    Mr = M[jnp.ix_(free, free)]
    return Kr, Mr


# ----------------------------------------------------------------------------
# Differentiable generalized eigensolve via Cholesky whitening.
#   K phi = lambda M phi ;  M = Lc Lc^T ;  Asym = Lc^-1 K Lc^-T ;  eigh(Asym).
#   jnp.linalg.eigh is differentiable -> gradients flow to E, h, etc.
# ----------------------------------------------------------------------------
def eig_freqs(E, rho, L, b, h, nele, n=5):
    A, I = section(b, h)
    Kr, Mr = assemble(E, rho, L, A, I, nele)
    Lc = jnp.linalg.cholesky(Mr)
    Linv = jnp.linalg.inv(Lc)
    Asym = Linv @ Kr @ Linv.T
    Asym = 0.5 * (Asym + Asym.T)  # symmetrize for numerical safety
    evals, evecs = jnp.linalg.eigh(Asym)  # ascending
    evals = jnp.clip(evals, a_min=0.0)
    omega = jnp.sqrt(evals)               # rad/s
    f = omega / (2.0 * jnp.pi)            # Hz
    # back-transform modes to physical (M-orthonormal): phi = Lc^-T y
    phi = Linv.T @ evecs                  # columns mass-normalized: phi^T M phi = I
    return f[:n], omega[:n], phi


def first_freq_scalar(E, h):
    """Scalar f_1 (Hz) for autodiff gradient check w.r.t. (E, h)."""
    f, _, _ = eig_freqs(E, RHO, L, B, h, nele=20, n=1)
    return f[0]


# ----------------------------------------------------------------------------
# Drive-point FRF (accelerance) by modal superposition. Mass-normalized modes.
#   receptance H(w) = sum_r phi_r[o] phi_r[i] / (wr^2 - w^2 + 2 i zeta_r wr w)
#   accelerance A(w) = -w^2 H(w).  Drive-point: o == i -> residues phi_r^2 >= 0
#   => guarantees pole-zero interlacing (antiresonance between each resonance).
# ----------------------------------------------------------------------------
def drive_point_accelerance(omega_modes, phi, dof, freqs_hz, zeta):
    w = 2.0 * np.pi * freqs_hz
    wr = np.asarray(omega_modes)
    res = np.asarray(phi)[dof, :] ** 2  # phi_r[dof]^2, real, >= 0
    H = np.zeros_like(w, dtype=complex)
    for r in range(len(wr)):
        denom = (wr[r] ** 2 - w ** 2) + 2j * zeta * wr[r] * w
        H += res[r] / denom
    return -(w ** 2) * H  # accelerance (m/s^2 per N)


def main():
    out = {}
    t0 = time.time()

    A0, I0 = section(B, H0)
    out["section"] = {"A_m2": A0, "I_m4": I0, "b_m": B, "h_m": H0, "L_m": L,
                      "E_Pa": E0, "rho_kgm3": RHO}

    # --- (4) Validation + mesh convergence vs analytical benchmark ---
    f_anal = analytical_freqs(E0, RHO, L, A0, I0, n=5)
    out["analytical_freqs_Hz"] = f_anal.tolist()
    out["betaL"] = BETA_L.tolist()

    conv = {}
    fe_by_mesh = {}
    for nele in [5, 10, 20, 40]:
        f, omega, phi = eig_freqs(E0, RHO, L, B, H0, nele, n=5)
        f = np.asarray(f)
        err = 100.0 * (f - f_anal) / f_anal
        conv[str(nele)] = {"f_Hz": f.tolist(), "err_pct": err.tolist()}
        fe_by_mesh[nele] = (f, omega, phi)
    out["mesh_convergence"] = conv

    # use nele=40 as the reference mesh for FRF + mode shapes
    nele_ref = 40
    f_ref, omega_ref, phi_ref = fe_by_mesh[nele_ref]
    out["fem_freqs_Hz_nele40"] = np.asarray(f_ref).tolist()
    out["err_pct_nele40"] = (100.0 * (np.asarray(f_ref) - f_anal) / f_anal).tolist()

    # --- (3a) mode shapes figure ---
    nnode = nele_ref + 1
    x = np.linspace(0, L, nnode)
    phi_np = np.asarray(phi_ref)
    # reduced DOFs: index 0 -> w at node1. transverse DOFs are even reduced indices (0,2,4,..)
    wdof = np.arange(0, 2 * nele_ref, 2)  # reduced indices of w (node1..nodeN)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for r in range(4):
        shape = np.concatenate([[0.0], phi_np[wdof, r]])  # prepend clamped node w=0
        shape = shape / np.max(np.abs(shape))
        ax.plot(x, shape, marker=".", label=f"mode {r+1}: {np.asarray(f_ref)[r]:.1f} Hz")
    ax.axhline(0, color="k", lw=0.5)
    ax.set_xlabel("x along beam [m]")
    ax.set_ylabel("normalized transverse mode shape")
    ax.set_title("Cantilever Euler-Bernoulli mode shapes (JAX FEM, nele=40)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGDIR + "/modes.png", dpi=130)
    plt.close(fig)

    # --- benchmark overlay bar/scatter ---
    fig, ax = plt.subplots(figsize=(6.5, 4.0))
    idx = np.arange(1, 6)
    ax.plot(idx, f_anal, "ks-", label="analytical (betaL)", ms=7)
    for nele in [5, 10, 20, 40]:
        fm = np.asarray(conv[str(nele)]["f_Hz"])
        ax.plot(idx, fm, "o--", ms=4, label=f"FEM nele={nele}")
    ax.set_yscale("log")
    ax.set_xlabel("mode number")
    ax.set_ylabel("natural frequency [Hz]")
    ax.set_title("FEM vs analytical cantilever frequencies (benchmark overlay)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGDIR + "/benchmark_overlay.png", dpi=130)
    plt.close(fig)

    # --- (3b) drive-point FRF at tip, with antiresonance check ---
    zeta = 0.02  # 2% modal damping
    tip_w_dof = wdof[-1]  # reduced index of w at the free tip node
    fmax = float(np.asarray(f_ref)[4]) * 1.3
    freqs = np.linspace(1.0, fmax, 6000)
    acc = drive_point_accelerance(omega_ref, phi_ref, tip_w_dof, freqs, zeta)
    mag = np.abs(acc)

    # detect resonances (peaks) and antiresonances (troughs) in log-mag
    logm = np.log10(mag)
    res_idx = [i for i in range(1, len(mag) - 1) if logm[i] > logm[i - 1] and logm[i] > logm[i + 1]]
    anti_idx = [i for i in range(1, len(mag) - 1) if logm[i] < logm[i - 1] and logm[i] < logm[i + 1]]
    res_f = freqs[res_idx]
    anti_f = freqs[anti_idx]
    # interlacing: count antiresonances strictly between consecutive resonances
    interlaced = 0
    for k in range(len(res_f) - 1):
        if np.any((anti_f > res_f[k]) & (anti_f < res_f[k + 1])):
            interlaced += 1
    out["frf"] = {
        "zeta": zeta, "dof": "tip transverse w", "f_band_Hz": [1.0, fmax],
        "resonances_Hz": res_f.tolist(), "antiresonances_Hz": anti_f.tolist(),
        "n_resonances": len(res_f), "n_antiresonances": len(anti_f),
        "interlaced_gaps": int(interlaced), "interlacing_gaps_possible": max(len(res_f) - 1, 0),
        "interlacing_ok": bool(interlaced == max(len(res_f) - 1, 0) and len(res_f) >= 2),
    }

    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.loglog(freqs, mag, lw=1.2, label="drive-point accelerance |A(f)|")
    ax.plot(res_f, mag[res_idx], "r^", ms=7, label="resonances")
    ax.plot(anti_f, mag[anti_idx], "bv", ms=7, label="antiresonances")
    ax.set_xlabel("frequency [Hz] (log)")
    ax.set_ylabel("accelerance |a/F|  [(m/s^2)/N] (log)")
    ax.set_title("Drive-point accelerance at tip (zeta=2%) — pole/zero interlacing")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGDIR + "/frf_drivepoint.png", dpi=130)
    plt.close(fig)

    # --- (5) differentiability check: grad of f_1 w.r.t. E and h ---
    grad_fn = jax.jit(jax.grad(first_freq_scalar, argnums=(0, 1)))
    # warm-up (jit compile) then time
    _ = grad_fn(E0, H0)
    jax.block_until_ready(_)
    tg = time.time()
    g = grad_fn(E0, H0)
    jax.block_until_ready(g)
    grad_time = time.time() - tg
    gE, gh = float(g[0]), float(g[1])

    # finite-difference cross-check
    def f1_np(E, h):
        return float(first_freq_scalar(E, h))
    f1 = f1_np(E0, H0)
    dE = E0 * 1e-6
    dh = H0 * 1e-6
    fd_E = (f1_np(E0 + dE, H0) - f1_np(E0 - dE, H0)) / (2 * dE)
    fd_h = (f1_np(E0, H0 + dh) - f1_np(E0, H0 - dh)) / (2 * dh)
    # closed-form (EXACT) gradients: f1 ~ sqrt(E) so df1/dE = f1/(2E);
    # f1 ~ h (I ~ h^3, A ~ h => omega ~ sqrt(I/A) ~ h) so df1/dh = f1/h.
    ana_E = f1 / (2.0 * E0)
    ana_h = f1 / H0
    out["differentiability"] = {
        "f1_Hz": f1,
        "grad_f1_wrt_E_autograd": gE, "grad_f1_wrt_E_fd": fd_E, "grad_f1_wrt_E_closedform": ana_E,
        "rel_err_E_vs_closedform": abs(gE - ana_E) / abs(ana_E),
        "rel_err_E_vs_fd": abs(gE - fd_E) / abs(fd_E),
        "grad_f1_wrt_h_autograd": gh, "grad_f1_wrt_h_fd": fd_h, "grad_f1_wrt_h_closedform": ana_h,
        "rel_err_h_vs_closedform": abs(gh - ana_h) / abs(ana_h),
        "rel_err_h_vs_fd": abs(gh - fd_h) / abs(fd_h),
        "grad_eval_time_s_after_jit": grad_time,
        "note": ("FD on E is roundoff-limited (E~2e11); autograd is judged against the EXACT "
                 "closed-form derivative, which is the rigorous check."),
        "autograd_works": bool(abs(gE - ana_E) / abs(ana_E) < 1e-3
                               and abs(gh - ana_h) / abs(ana_h) < 1e-3),
    }

    out["total_runtime_s"] = time.time() - t0
    with open(HERE + "/report/results.json", "w") as fh:
        json.dump(out, fh, indent=2)

    # console summary
    print("=== FEM SPIKE RESULTS ===")
    print("analytical f (Hz):", np.round(f_anal, 3))
    print("FEM nele=40 f(Hz):", np.round(np.asarray(f_ref), 3))
    print("err%% nele=40    :", np.round(out['err_pct_nele40'], 4))
    print("FRF resonances Hz:", np.round(res_f, 2))
    print("FRF antires.  Hz:", np.round(anti_f, 2))
    print("interlacing OK   :", out['frf']['interlacing_ok'],
          f"({interlaced}/{max(len(res_f)-1,0)} gaps filled)")
    d = out["differentiability"]
    print(f"df1/dE autograd={d['grad_f1_wrt_E_autograd']:.6e} closedform={d['grad_f1_wrt_E_closedform']:.6e} "
          f"relerr={d['rel_err_E_vs_closedform']:.2e}")
    print(f"df1/dh autograd={d['grad_f1_wrt_h_autograd']:.6e} closedform={d['grad_f1_wrt_h_closedform']:.6e} "
          f"relerr={d['rel_err_h_vs_closedform']:.2e}")
    print("autograd works   :", d["autograd_works"],
          f"(grad eval {d['grad_eval_time_s_after_jit']*1e3:.2f} ms after jit)")
    print("total runtime s  :", round(out["total_runtime_s"], 2))


if __name__ == "__main__":
    main()
