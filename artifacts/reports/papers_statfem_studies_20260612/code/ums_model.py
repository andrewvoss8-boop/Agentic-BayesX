"""Unified modal statFEM (UMS) = statFEM backbone + Das/Debnath latent complex modes
+ Schneider correlated multiplicative FRF discrepancy.  (Study G core module.)

Pieces:
  1. Plate-like grid FEM builders (truth = heterogeneous field + patch + dashpot + mass loading;
     inference = 4 quadrant stiffness groups + suspension scale + Rayleigh damping).
  2. Fixed Ritz basis Phi0 from the NOMINAL FEM (eigh done offline, never inside NUTS).
     Projected group matrices Kg_tilde (BxB) so the eigen-residual costs O(B^2).
  3. Complex-mode residue FRF synthesis (scale-invariant; no eigensolve in the loop).
  4. Separable Schneider likelihood: cov = sigma^2 * S (R_f kron R_z) S with OU (exponential)
     frequency kernel whitened by AR(1) innovations in O(n); S = delta-method noise-floor
     inflation. Self-tested against a dense MVN logpdf.

Run `python ums_model.py` (in .venv_nuts) to execute the self-tests.
"""
from __future__ import annotations
import math
import numpy as np

try:
    import jax
    import jax.numpy as jnp
    from jax.scipy.linalg import solve_triangular
    jax.config.update("jax_enable_x64", True)
    HAVE_JAX = True
except Exception:  # plotting venv has no jax; numpy parts still importable
    HAVE_JAX = False

# ---------------------------------------------------------------- grid FEM
NX, NY = 8, 5
NN = NX * NY
DX = 0.1           # m grid spacing -> panel 0.7 x 0.4 m
M_NODE = 0.05      # kg -> 2.0 kg panel


def node_xy():
    xs = np.arange(NX) * DX
    ys = np.arange(NY) * DX
    X, Y = np.meshgrid(xs, ys, indexing="ij")     # node id = ix*NY + iy
    return np.stack([X.ravel(), Y.ravel()], 1)    # [NN,2]


def graph_incidence():
    """Edge incidence rows for the 4-neighbour grid graph; L = E'E is the graph Laplacian."""
    rows = []
    def nid(ix, iy): return ix * NY + iy
    for ix in range(NX):
        for iy in range(NY):
            if ix + 1 < NX:
                r = np.zeros(NN); r[nid(ix, iy)] = 1; r[nid(ix + 1, iy)] = -1; rows.append(r)
            if iy + 1 < NY:
                r = np.zeros(NN); r[nid(ix, iy)] = 1; r[nid(ix, iy + 1)] = -1; rows.append(r)
    return np.array(rows)


_E = graph_incidence()
_L = _E.T @ _E                      # graph Laplacian, nullspace = constants


def k_bend(d_node):
    """Heterogeneous discrete-biharmonic bending stiffness K = L' diag(d) L (sym PSD)."""
    return _L.T @ np.diag(d_node) @ _L


SUSP_NODES = [0 * NY + (NY - 1), (NX - 1) * NY + (NY - 1)]   # two top corners (cables)


def k_susp(ks_each):
    K = np.zeros((NN, NN))
    for n, k in zip(SUSP_NODES, ks_each):
        K[n, n] += k
    return K


def quadrant_groups():
    g = np.zeros(NN, dtype=int)
    for ix in range(NX):
        for iy in range(NY):
            g[ix * NY + iy] = (ix >= NX // 2) * 2 + (iy >= NY // 2)
    return g                                                    # 0..3


def tune_scales(f1_target=2.2, f4_target=18.0):
    """Pick bending scale alpha and suspension ks so mode1~f1_target, mode4~f4_target."""
    alpha, ks = 1.0, 1.0
    M = np.diag(np.full(NN, M_NODE))
    for _ in range(4):
        K = alpha * k_bend(np.ones(NN)) + k_susp([ks, ks])
        w2 = np.linalg.eigvalsh(np.linalg.solve(M, K))
        f = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)
        alpha *= (f4_target / max(f[3], 1e-9)) ** 2
        ks *= (f1_target / max(f[0], 1e-9)) ** 2
    return alpha, ks


ALPHA, KS = tune_scales()


def build_truth(seed=7):
    """Truth system: smooth stiffness field + soft patch + uneven cables + dashpot + drive mass."""
    rng = np.random.default_rng(seed)
    xy = node_xy()
    x, y = xy[:, 0], xy[:, 1]
    field = 1.0 + 0.18 * np.sin(2 * np.pi * x / x.max()) * np.cos(np.pi * y / y.max()) \
                + 0.10 * (x / x.max() - 0.5)
    patch = np.ones(NN)
    for ix in (5, 6):
        for iy in (1, 2):
            patch[ix * NY + iy] = 0.62                         # local soft region
    d = ALPHA * field * patch
    K = k_bend(d) + k_susp([1.15 * KS, 0.90 * KS])             # uneven cables
    m = np.full(NN, M_NODE)
    drive = 2 * NY + 1                                          # node (2,1)
    m[drive] += 0.008                                           # drive-side mass loading (8 g)
    M = np.diag(m)
    # damping: Rayleigh-ish + local dashpot -> NON-proportional, in-band zeta ~0.5-2.5%
    a0t, a1t = 0.55, 4.0e-5
    C = a0t * M + a1t * K
    dash = 5 * NY + 2                                           # inside the patch
    C[dash, dash] += 1.3
    return dict(K=K, M=M, C=C, drive=drive, d=d)


def nominal_inference_pieces():
    """Nominal inference FEM + projected (BxB) operators for the latent-mode layer."""
    g = quadrant_groups()
    Kg = []
    for q in range(4):
        d = np.where(g == q, ALPHA, 0.0)
        Kg.append(k_bend(d))
    Ks = k_susp([KS, KS])
    M = np.diag(np.full(NN, M_NODE))
    K_nom = sum(Kg) + Ks
    from scipy.linalg import eigh
    w2, V = eigh(K_nom, M)                                      # M-orthonormal modes
    f_nom = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)
    return dict(Kg=Kg, Ks=Ks, M=M, K_nom=K_nom, f_nom=f_nom, Phi=V)


def truth_complex_modes(truth):
    """State-space eig of the truth -> (lam, shapes, f, zeta), positive-imag branch sorted."""
    M, C, K = truth["M"], truth["C"], truth["K"]
    n = M.shape[0]
    A = np.block([[np.zeros((n, n)), np.eye(n)],
                  [-np.linalg.solve(M, K), -np.linalg.solve(M, C)]])
    w, V = np.linalg.eig(A)
    idx = [i for i in range(len(w)) if w[i].imag > 1e-6]
    idx.sort(key=lambda i: abs(w[i].imag))
    lam = np.array([w[i] for i in idx])
    psi = np.array([V[:n, i] for i in idx])
    f = np.abs(lam) / (2 * np.pi)
    z = -lam.real / np.abs(lam)
    return lam, psi, f, z


def direct_frf(K, C, M, drive, rows, freqs_hz):
    """Exact accelerance a_rows / F_drive by direct solves (truth generation)."""
    out = np.zeros((len(freqs_hz), len(rows)), complex)
    for i, f in enumerate(freqs_hz):
        w = 2 * np.pi * f
        Z = K + 1j * w * C - (w ** 2) * M
        h = np.linalg.solve(Z, np.eye(NN)[:, drive])
        out[i] = -(w ** 2) * h[rows]
    return out


def residue_frf_numpy(lam, psi_rows, psi_drive, a, freqs_hz):
    """Complex-mode residue synthesis (numpy): H_disp then accelerance."""
    w = 2 * np.pi * freqs_hz
    iw = 1j * w
    H = np.zeros((len(freqs_hz), psi_rows.shape[1]), complex)
    for m in range(len(lam)):
        Rm = psi_rows[m] * psi_drive[m] / a[m]                  # [rows]
        H += Rm[None, :] / (iw[:, None] - lam[m]) \
           + np.conj(Rm)[None, :] / (iw[:, None] - np.conj(lam[m]))
    return -(w ** 2)[:, None] * H


# ---------------------------------------------------------------- JAX pieces
if HAVE_JAX:
    def residue_frf_jax(lam, psi_rows, psi_drive, a, freqs_hz):
        """lam [Nm] complex, psi_rows [Nm, P], psi_drive [Nm], a [Nm] -> accelerance [nf, P]."""
        w = 2 * jnp.pi * freqs_hz
        iw = 1j * w
        R = psi_rows * (psi_drive / a)[:, None]                 # [Nm, P]
        ker1 = 1.0 / (iw[:, None] - lam[None, :])               # [nf, Nm]
        ker2 = 1.0 / (iw[:, None] - jnp.conj(lam)[None, :])
        H = ker1 @ R + ker2 @ jnp.conj(R)
        return -(w ** 2)[:, None] * H

    def separable_logpdf(X, s, sigma, rho_f, Lz):
        """log N(vec(X) | 0, sigma^2 S (R_f kron R_z) S); X,s [nf,np]; rho_f [nf-1]; Lz chol(R_z)."""
        Xs = X / s
        e0 = Xs[0:1]
        rest = (Xs[1:] - rho_f[:, None] * Xs[:-1]) / jnp.sqrt(1.0 - rho_f ** 2)[:, None]
        Ef = jnp.concatenate([e0, rest], 0)
        E = solve_triangular(Lz, Ef.T, lower=True).T
        n = X.size
        nf, npp = X.shape
        quad = jnp.sum(E * E) / sigma ** 2
        logdet = (2 * jnp.sum(jnp.log(s)) + 2 * n * jnp.log(sigma)
                  + npp * jnp.sum(jnp.log(1.0 - rho_f ** 2))
                  + nf * 2 * jnp.sum(jnp.log(jnp.diag(Lz))))
        return -0.5 * (n * jnp.log(2 * jnp.pi) + logdet + quad)

    def exp_chol(coords, ell, nug=1e-8):
        d = jnp.sqrt(jnp.sum((coords[:, None, :] - coords[None, :, :]) ** 2, -1))
        R = jnp.exp(-d / ell) + nug * jnp.eye(coords.shape[0])
        return jnp.linalg.cholesky(R)


# ---------------------------------------------------------------- self-tests
def _selftest():
    assert HAVE_JAX, "run self-tests in .venv_nuts"
    rng = np.random.default_rng(0)
    print("== self-test 1: separable+scaled logpdf vs dense MVN ==")
    nf, npp = 7, 3
    fgrid = np.cumsum(0.3 + rng.random(nf))
    ell_f = 1.7
    rho = np.exp(-np.diff(fgrid) / ell_f)
    Rf = np.exp(-np.abs(fgrid[:, None] - fgrid[None, :]) / ell_f)
    coords = rng.random((npp, 2))
    dz = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1))
    Rz = np.exp(-dz / 0.4) + 1e-8 * np.eye(npp)
    s = 0.5 + rng.random((nf, npp))
    sigma = 0.37
    X = rng.standard_normal((nf, npp))
    Sd = np.diag(s.reshape(-1))
    cov = sigma ** 2 * Sd @ np.kron(Rf, Rz) @ Sd
    sign, logdet = np.linalg.slogdet(cov)
    x = X.reshape(-1)
    dense = -0.5 * (x.size * np.log(2 * np.pi) + logdet + x @ np.linalg.solve(cov, x))
    Lz = np.linalg.cholesky(Rz)
    fast = float(separable_logpdf(jnp.array(X), jnp.array(s), sigma,
                                  jnp.array(rho), jnp.array(Lz)))
    print(f"   dense {dense:.10f}  fast {fast:.10f}  |diff| {abs(dense-fast):.2e}")
    assert abs(dense - fast) < 1e-7

    print("== self-test 2: residue FRF == direct inversion (full mode set) ==")
    truth = build_truth()
    lam, psi, f, z = truth_complex_modes(truth)
    a = np.array([psi[m] @ ((2 * lam[m] * truth["M"] + truth["C"]) @ psi[m])
                  for m in range(len(lam))])
    rows = [truth["drive"], 17, 33]
    freqs = np.linspace(12.0, 180.0, 41)
    Hd = direct_frf(truth["K"], truth["C"], truth["M"], truth["drive"], rows, freqs)
    Hr = residue_frf_numpy(lam, psi[:, rows], psi[:, truth["drive"]], a, freqs)
    rel = np.linalg.norm(Hd - Hr) / np.linalg.norm(Hd)
    print(f"   full-set relative error {rel:.2e}")
    assert rel < 1e-8

    print("== self-test 3: truncation floor of the in-band modal synthesis ==")
    keep = f <= 250.0
    Hr_t = residue_frf_numpy(lam[keep], psi[keep][:, rows], psi[keep][:, truth["drive"]],
                             a[keep], freqs)
    rel_t = np.linalg.norm(Hd - Hr_t) / np.linalg.norm(Hd)
    print(f"   {keep.sum()} modes <=250 Hz; in-band truncation error {rel_t*100:.2f}% "
          f"(absorbed by the discrepancy; documented)")
    assert rel_t < 0.10

    print("== self-test 4: nominal ladder + groups ==")
    nom = nominal_inference_pieces()
    print("   nominal modes [Hz]:", np.round(nom["f_nom"][:14], 2))
    tf, tz = f[:14], z[:14]
    print("   truth   modes [Hz]:", np.round(tf, 2))
    print("   truth   zeta  [%] :", np.round(100 * tz, 2))
    assert abs(nom["f_nom"][0] - 2.2) < 0.6 and abs(nom["f_nom"][3] - 18.0) < 3.0
    print("ALL SELF-TESTS PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
