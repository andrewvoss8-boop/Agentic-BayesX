"""
Shared style + helpers for the Schneider et al. (2022) teaching deck.

Schneider, Papaioannou, Straub, Winter, Mueller (2022),
"Bayesian parameter updating in linear structural dynamics with frequency
transformed data using rational surrogate models", MSSP 166:108407.

EVERYTHING produced here is a SYNTHETIC / CONCEPTUAL teaching illustration.
It is NOT a reproduction of the paper's cross-laminated-timber (CLT) results.
Where public values from the paper are reused (e.g. the shell-model
eigenfrequencies in Fig. C.10), that is stated on the figure.
"""
from __future__ import annotations
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FIG = BASE / "figures"
GIF = BASE / "gifs"
FIG.mkdir(parents=True, exist_ok=True)
GIF.mkdir(parents=True, exist_ok=True)

# ---- palette ---------------------------------------------------------------
C_TRUTH = "#15314b"   # deep navy   -> "truth" / measured
C_SURR = "#e07b39"    # orange      -> surrogate
C_POLY = "#9b59b6"    # purple      -> plain polynomial (PCE numerator only)
C_ERR = "#c0392b"     # red         -> error
C_ACC = "#2e8b57"     # green       -> accepted / posterior
C_PRIOR = "#95a5a6"   # grey        -> prior
ACCENT = "#2980b9"    # blue accent
C_MAG = "#1f3a5f"
C_PHA = "#2e8b57"

plt.rcParams.update({
    "figure.dpi": 120,
    "savefig.dpi": 150,
    "font.size": 11,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.grid": True,
    "grid.alpha": 0.22,
    "axes.axisbelow": True,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "legend.framealpha": 0.9,
    "legend.fontsize": 9,
})

STAMP = ("Teaching illustration - synthetic / conceptual data, "
         "NOT the paper's CLT results")

# Public eigenfrequencies of the paper's shell model (Fig. C.10), Hz.
PAPER_SHELL_EIGENFREQS = [30.8, 64.7, 87.0, 87.7, 105.0, 155.0]


def stamp(fig):
    fig.text(0.005, 0.004, STAMP, fontsize=6.5, color="#9a9a9a",
             ha="left", va="bottom")


def save(fig, name, rect=(0, 0.025, 1, 0.99)):
    fig.tight_layout(rect=rect)
    stamp(fig)
    p = FIG / name
    fig.savefig(p)
    plt.close(fig)
    print("  wrote", p.relative_to(BASE))
    return p


def gif_path(name):
    return GIF / name


# ---- physics helpers -------------------------------------------------------
def modal_frf(f, fr, zeta, A, accel=False):
    """Receptance (or acceleration) FRF as a modal sum -> naturally rational in w.

    H(w) = sum_r  A_r / (wr^2 - w^2 + i 2 zeta_r wr w),  w = 2 pi f
    With accel=True multiply by -w^2 (cf. Eq. 2 of the paper).
    f may be an array; fr, zeta, A are length-R sequences.
    """
    f = np.asarray(f, dtype=float)
    w = 2 * np.pi * f
    wr = 2 * np.pi * np.asarray(fr, dtype=float)
    zeta = np.asarray(zeta, dtype=float)
    A = np.asarray(A, dtype=float)
    den = (wr[None, :] ** 2 - w[:, None] ** 2
           + 1j * 2.0 * zeta[None, :] * wr[None, :] * w[:, None])
    H = (A[None, :] / den).sum(axis=1)
    if accel:
        H = -(w ** 2) * H
    return H


def hysteretic_frf_vs_param(f0, k, fr0, eta, A):
    """Complex FRF at a FIXED frequency f0 as a function of a stiffness scale k.

    Hysteretic-style damping (cf. Eq. 29): stiffness term carries (1 + i eta),
    so H is a genuine RATIONAL function of the parameter k (sum of simple poles
    in k). This mirrors why the paper's surrogate is rational in the PARAMETERS.

        H(k) = sum_r  A_r / ( k * wr0^2 (1 + i eta_r) - w0^2 )
    """
    k = np.atleast_1d(np.asarray(k, dtype=float))
    w0 = 2 * np.pi * float(f0)
    wr0 = 2 * np.pi * np.asarray(fr0, dtype=float)
    eta = np.asarray(eta, dtype=float)
    A = np.asarray(A, dtype=float)
    den = (k[:, None] * wr0[None, :] ** 2 * (1 + 1j * eta[None, :]) - w0 ** 2)
    return (A[None, :] / den).sum(axis=1)


# ---- Hermite-PCE helpers (probabilists', normalized) -----------------------
def hermite_norm(xi, degree):
    """Matrix [N x (degree+1)] of normalized probabilists' Hermite polys He_n/sqrt(n!).

    These are the orthonormal basis for a standard-normal input -> exactly the
    1-D building blocks of the paper's multivariate Psi_i (Eq. 3) in 1 dimension.
    """
    import math
    xi = np.asarray(xi, dtype=float)
    cols = []
    for n in range(degree + 1):
        c = np.zeros(n + 1)
        c[n] = 1.0
        He = np.polynomial.hermite_e.hermeval(xi, c)
        cols.append(He / math.sqrt(math.factorial(n)))
    return np.column_stack(cols)


def fit_poly_pce(Psi, M):
    """Plain (numerator-only) complex PCE: least-squares  Psi p ~ M."""
    p, *_ = np.linalg.lstsq(Psi, M, rcond=None)
    return p


def fit_rational_pce(Psi_P, Psi_Q, M):
    """Linearized rational regression -- Eqs. (6)-(9) of the paper.

    Build the (np+nq)x(np+nq) Hermitian system A (Eq. 8) and take r=[p;q] as the
    minimum-norm null vector (smallest right singular vector), ||r||=1 (Eq. 9).
    """
    M = np.asarray(M)
    dM = np.diag(M)
    dMc = np.diag(np.conjugate(M))
    dMM = np.diag(M * np.conjugate(M))
    A11 = Psi_P.conj().T @ Psi_P
    A12 = -Psi_P.conj().T @ dM @ Psi_Q
    A21 = -Psi_Q.conj().T @ dMc @ Psi_P
    A22 = Psi_Q.conj().T @ dMM @ Psi_Q
    A = np.block([[A11, A12], [A21, A22]])
    # smallest singular vector of A -> argmin ||A r|| s.t. ||r||=1
    _, _, Vh = np.linalg.svd(A)
    r = Vh.conj().T[:, -1]
    npc = Psi_P.shape[1]
    p = r[:npc]
    q = r[npc:]
    # fix scale/sign so that the mean prediction has a sensible magnitude
    return p, q


def eval_rational(Psi_P, Psi_Q, p, q):
    return (Psi_P @ p) / (Psi_Q @ q)


if __name__ == "__main__":
    print("common.py OK; figures ->", FIG)
