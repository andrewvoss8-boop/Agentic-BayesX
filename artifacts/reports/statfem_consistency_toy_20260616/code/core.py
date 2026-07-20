#!/usr/bin/env python3
"""Fresh rod-physics core for the StatFEM consistency toy (Experiment A).

Self-contained (no sibling-study imports). Fixed-free axial rod, nondimensional:
    L = 1, rho*A = 1, EA_nom = 1  ->  wave speed c^2 = EA/rhoA = 1.
Governing eigenproblem:  -(EA u')' = omega^2 rhoA u,  u(0)=0 (fixed), EA u'(L)=0 (free).
Stiffness scale theta:   EA = theta * EA_nom  ->  omega_n = sqrt(theta) * (2n-1)*pi/(2L).
Model-form error (TRUTH only): a Winkler elastic foundation k_f = eps adds +k_f to omega^2:
    omega_n,true^2 = theta_true * lambda_n + k_f,   lambda_n = ((2n-1)pi/2L)^2.
Mode shapes are unchanged by a constant foundation: phi_n(x) = sqrt(2) sin((2n-1)pi x / 2L) (ra=L=1).

Provides:
  * analytic eigenfrequencies / mode shapes (the truth),
  * a symmetric finite-difference 2nd-derivative operator D2(N_c) + its eigen-decomposition
    (used by the marginalised M-lik / M-ift likelihoods, eigenbasis form),
  * a consistent-mass axial-bar FE eigensolve (used by M-statfem),
  * synthetic data generation (noisy mode shapes at sensors + noisy frequencies, n replicates),
  * theta->observable sensitivity (identifiability).
All deterministic; numpy/float64. The NUTS likelihoods (nuts_marg.py, statfem.py) consume the
precomputed arrays returned here.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# ---- fixed physical constants (nondimensional) ----------------------------
L = 1.0
RHOA = 1.0
EA_NOM = 1.0
C2 = EA_NOM / RHOA           # = 1
THETA_TRUE = 1.15
SENSORS = np.array([k / 8.0 for k in range(1, 8)])  # 7 interior sensors x = 1/8 .. 7/8
N_MODES_FIT = 3
HELDOUT_MODES = np.array([4, 5, 6])
SIGMA_OMEGA_REL = 0.01      # frequency measurement noise = 1% of true omega (modal context only)

# ---- forced drive-point FRF observable (the inference observable; see decisions_log D11-D13) -------
# Harmonic forced rod: -theta u'' + (k_f - omega^2) u = f(x), u(0)=0, u'(L)=0, with a UNIFORM
# distributed load f(x)=F (F=1). Response u(x;omega,theta) observed at the 7 sensors for several KNOWN
# drive frequencies. Resonances at omega_n = sqrt(theta*lambda_n + k_f). Drive freqs are placed
# BETWEEN resonances so the undamped response is finite.
F_LOAD = 1.0
# Drive frequencies are chosen so that NO discrete resonance omega_n(theta)=sqrt(theta)*(2n-1)pi/2
# crosses a drive frequency for theta in the prior bulk [~0.7, ~1.7]; this keeps the physics-in-
# likelihood (M-lik) marginal UNIMODAL so its sigma_r/N_c drift can be measured cleanly. (Physics-in-
# likelihood ALSO shows spurious resonance-crossing multimodality when the prior spans a crossing --
# a documented secondary pathology; see decisions_log D14 and packet.)
DRIVE_FREQS_FIT = np.array([0.9, 1.2, 2.5, 3.0, 3.5])      # known excitation frequencies (rad/s)
DRIVE_FREQS_HELDOUT = np.array([0.6, 2.8, 6.3])            # held-out FRF points (coverage C3)
SIGMA_U_REL = 0.03          # response sensor noise = 3% of the per-frequency RMS response


def lambda_n(n):
    """Analytic eigenvalue lambda_n = ((2n-1)pi/2L)^2 for fixed-free rod (n=1,2,...)."""
    n = np.asarray(n, dtype=float)
    return ((2 * n - 1) * np.pi / (2 * L)) ** 2


def analytic_omega(theta, k_f, modes):
    """True/analytic natural frequencies: omega = sqrt(theta*lambda_n + k_f)."""
    n = np.asarray(modes, dtype=float)
    return np.sqrt(theta * C2 * lambda_n(n) + k_f)


def mode_shape(n, x, unit_max=True):
    """Analytic mode shape phi_n(x). unit_max=True scales peak |phi|=1 (for the sensor noise model)."""
    n = float(n)
    s = np.sin((2 * n - 1) * np.pi * np.asarray(x) / (2 * L))
    if unit_max:
        return s / np.max(np.abs(s)) if np.max(np.abs(s)) > 0 else s
    return np.sqrt(2.0 / (RHOA * L)) * s  # mass-normalised


def domega_dtheta(theta, k_f, modes):
    """Sensitivity dω/dθ = c^2 lambda_n / (2 omega) (identifiability of theta from frequencies)."""
    n = np.asarray(modes, dtype=float)
    om = analytic_omega(theta, k_f, modes)
    return C2 * lambda_n(n) / (2.0 * om)


# ---- finite-difference operator (M-lik / M-ift) ---------------------------
def fd_operator(N):
    """Symmetric, 2nd-order finite-difference 2nd-derivative D2 on a CELL-CENTERED fixed-free grid.

    Grid x_j = (j-1/2)h, j=1..N, h=L/N (cell centres). Dirichlet u(0)=0 via odd reflection about x=0
    (ghost u(-h/2)=-u(h/2) -> first diagonal -3); Neumann u'(L)=0 via even reflection about x=L
    (ghost u(L+h/2)=u(L-h/2) -> last diagonal -1). Both boundary closures are 2nd-order, so the
    eigenvalues converge O(h^2) to -lambda_k. D2 ~ d^2/dx^2 is symmetric negative-definite. Returns
    (x_nodes, D2, d_k, V) with D2 = V diag(d_k) V^T (d_k < 0 approximate -lambda_k; V orthonormal)."""
    h = L / N
    x = (np.arange(1, N + 1) - 0.5) * h
    main = np.full(N, -2.0)
    main[0] = -3.0   # Dirichlet (odd reflection) at x=0
    main[-1] = -1.0  # Neumann (even reflection) at x=L
    off = np.ones(N - 1)
    D2 = (np.diag(main) + np.diag(off, 1) + np.diag(off, -1)) / (h ** 2)
    D2 = 0.5 * (D2 + D2.T)  # enforce exact symmetry
    d_k, V = np.linalg.eigh(D2)  # ascending; eigenvectors orthonormal
    return x, D2, d_k, V


def fd_eigenfreqs(N, theta, modes):
    """Discrete eigenfrequencies of the theta-scaled rod from the FD operator (no foundation):
    omega^2 = -theta * c^2 * d_k for the modes with the largest (least negative) eigenvalues."""
    _, _, d_k, _ = fd_operator(N)
    # eigenvalues of A0 = theta*c^2*D2 have values theta*c2*d_k; physical omega^2 = -theta*c2*d_k
    om2 = np.sort(-theta * C2 * d_k)  # ascending positive
    om2 = om2[om2 > 1e-12]
    idx = np.asarray(modes, dtype=int) - 1
    return np.sqrt(om2[idx])


def sensor_interp(x_nodes, sensors=SENSORS):
    """Linear-interpolation matrix S (m x N): field at sensors from nodal field values.
    Node 0 (x=0) carries phi=0 (fixed BC) and is not a column; handle x<x_nodes[0] by interpolating
    between the implicit fixed node (value 0 at x=0) and the first grid node."""
    N = len(x_nodes)
    m = len(sensors)
    S = np.zeros((m, N))
    xn = np.concatenate(([0.0], x_nodes))  # include fixed node at x=0 (value 0)
    for i, xs in enumerate(sensors):
        j = np.searchsorted(xn, xs)
        j = min(max(j, 1), N)  # bracket [xn[j-1], xn[j]]
        x0, x1 = xn[j - 1], xn[j]
        w = (xs - x0) / (x1 - x0) if x1 > x0 else 0.0
        # contribution of value at xn[j-1] and xn[j]; xn index k>=1 maps to nodal column k-1
        if j - 1 >= 1:
            S[i, j - 2] += (1 - w)
        # else j-1==0 -> fixed node value 0, contributes nothing
        S[i, j - 1] += w
    return S


def lik_precompute_fd(N):
    """Precompute the constant arrays the marginalised M-lik/M-ift FORCED-BVP likelihoods need at
    resolution N. The discrete dynamic-stiffness operator is A(theta,omega) = -theta*c^2*D2 - omega^2*I,
    symmetric, sharing eigenvectors V with D2: eigenvalue a_k = -theta*c^2*d_k - omega^2. The uniform
    load collocates to f_vec = F*ones(N); its eigen-projection is g = V^T f_vec. Returns d_k, SV=S@V,
    and g so the likelihood is an m x m Gaussian on the sensor response with a forcing-induced mean."""
    x, _, d_k, V = fd_operator(N)
    S = sensor_interp(x)
    SV = S @ V
    g = V.T @ (F_LOAD * np.ones(N))
    return {"N": N, "x": x, "d_k": d_k, "SV": SV, "g": g}


def fd_response(N, theta, k_f, omega, sensors=SENSORS):
    """Discrete forced response at sensors: solve A u = f_vec, A = -theta*c^2*D2 + (k_f - omega^2) I,
    f_vec = F*ones (uniform load collocated). k_f=0 for the (foundation-omitting) model; k_f>0 is the
    truth operator (used only for cross-checking the analytic truth)."""
    x, D2, _, _ = fd_operator(N)
    A = -theta * C2 * D2 + (k_f - omega ** 2) * np.eye(N)
    u = np.linalg.solve(A, F_LOAD * np.ones(N))
    S = sensor_interp(x, sensors)
    return S @ u, x, u


def analytic_response(theta, k_f, omega, x, F=F_LOAD, ntrunc=400):
    """Analytic forced response u(x) = sum_n f_n phi_n(x) / (theta*lambda_n + k_f - omega^2), uniform
    load f=F, mass-normalised phi_n = sqrt(2) sin((2n-1)pi x/2L), f_n = 2*sqrt(2)*L*F/((2n-1)pi)."""
    x = np.atleast_1d(np.asarray(x, dtype=float))
    n = np.arange(1, ntrunc + 1)
    lam = lambda_n(n)
    fn = 2.0 * np.sqrt(2.0) * L * F / ((2 * n - 1) * np.pi)          # modal load
    denom = theta * C2 * lam + k_f - omega ** 2                       # (ntrunc,)
    phi = np.sqrt(2.0) * np.sin((2 * n[None, :] - 1) * np.pi * x[:, None] / (2 * L))  # (len x, ntrunc)
    return phi @ (fn / denom)


def fe_assemble_load(n_el, F=F_LOAD):
    """Consistent nodal load vector for a uniform distributed load f=F on the fixed-free FE mesh."""
    Le = L / n_el
    nn = n_el + 1
    b = np.zeros(nn)
    be = F * Le / 2.0
    for e in range(n_el):
        b[e] += be
        b[e + 1] += be
    return b[1:]  # drop fixed node 0


def fe_response(n_el, theta, omega, sensors=SENSORS):
    """FE forced response at sensors: solve (theta*K0 - omega^2 M) u = b (consistent uniform load)."""
    K0, M, x_nodes = fe_assemble(n_el)
    b = fe_assemble_load(n_el)
    u = np.linalg.solve(theta * K0 - omega ** 2 * M, b)
    xn = np.concatenate(([0.0], x_nodes))
    u_full = np.concatenate(([0.0], u))
    return np.interp(sensors, xn, u_full), x_nodes, u


# ---- consistent-mass axial-bar FE (M-statfem) -----------------------------
def fe_assemble(n_el):
    """Fixed-free axial bar, n_el 2-node linear elements, consistent mass. Returns (K0, M, x_nodes)
    on the free DOFs (node 0 fixed removed). K0 is the theta=1 stiffness (EA_nom)."""
    Le = L / n_el
    nn = n_el + 1
    K = np.zeros((nn, nn))
    M = np.zeros((nn, nn))
    ke = (EA_NOM / Le) * np.array([[1.0, -1.0], [-1.0, 1.0]])
    me = (RHOA * Le / 6.0) * np.array([[2.0, 1.0], [1.0, 2.0]])
    for e in range(n_el):
        idx = [e, e + 1]
        K[np.ix_(idx, idx)] += ke
        M[np.ix_(idx, idx)] += me
    free = np.arange(1, nn)  # remove fixed node 0
    x_nodes = np.arange(nn) * Le
    return K[np.ix_(free, free)], M[np.ix_(free, free)], x_nodes[1:]


def fe_modes(n_el, n_modes):
    """Generalised eigenpairs (K0, M): omega0_i (theta=1) and mass-normalised shapes at the FE nodes.
    Because K(theta)=theta*K0, omega_i(theta) = sqrt(theta)*omega0_i and shapes are theta-independent."""
    K0, M, x_nodes = fe_assemble(n_el)
    # generalised symmetric eigenproblem K0 phi = omega^2 M phi, solved via Cholesky of M (SPD):
    #   M = R^T R ;  B = R^-T K0 R^-1 symmetric ;  eigh(B) -> w2, y ;  phi = R^-1 y.
    R = np.linalg.cholesky(M).T          # upper-triangular, M = R^T R
    Rinv = np.linalg.inv(R)
    B = Rinv.T @ K0 @ Rinv
    B = 0.5 * (B + B.T)
    w2, Y = np.linalg.eigh(B)
    order = np.argsort(w2)
    w2 = w2[order]
    Phi = Rinv @ Y[:, order]             # back-transform to physical modes (M-orthonormal)
    om0 = np.sqrt(np.clip(w2[:n_modes], 0, None))
    Phi = Phi[:, :n_modes]
    return om0, Phi, x_nodes


def fe_shapes_at_sensors(n_el, n_modes, sensors=SENSORS, unit_max=True):
    """FE mode shapes interpolated to sensor locations, sign/scale aligned to the analytic convention
    (peak +1) so they are directly comparable to the data shapes."""
    om0, Phi, x_nodes = fe_modes(n_el, n_modes)
    xn = np.concatenate(([0.0], x_nodes))
    Phi_full = np.vstack([np.zeros((1, n_modes)), Phi])  # add fixed node value 0
    cols = []
    for i in range(n_modes):
        vals = np.interp(sensors, xn, Phi_full[:, i])
        if unit_max and np.max(np.abs(vals)) > 0:
            vals = vals / np.max(np.abs(vals))          # unit-max scale
        # FE eigenvector sign is arbitrary: align to the analytic shape (peak +1 convention)
        ana = mode_shape(i + 1, sensors, unit_max=True)
        if np.dot(vals, ana) < 0:
            vals = -vals
        cols.append(vals)
    return om0, np.array(cols).T  # (m, n_modes)


# ---- synthetic data -------------------------------------------------------
@dataclass
class Data:
    drive_fit: np.ndarray      # (n_freq,) fit drive frequencies (rad/s)
    drive_held: np.ndarray     # (n_freqH,) held-out drive frequencies
    y_u: np.ndarray            # (n_rep, m, n_freq) noisy sensor responses (fit freqs)
    u_true: np.ndarray         # (m, n_freq) clean truth responses (fit freqs)
    sigma_u: np.ndarray        # (n_freq,) per-frequency absolute response noise std
    u_held_true: np.ndarray    # (m, n_freqH) clean truth held-out responses
    sigma_u_held: np.ndarray   # (n_freqH,) held-out per-frequency noise std
    eps: float
    n_rep: int


def make_data(eps, n_rep=1, seed=20260616):
    """Generate n_rep independent noisy drive-point-FRF tests of the TRUE foundation rod
    (theta_true, k_f=eps). Response at the 7 sensors for each KNOWN fit drive frequency, plus the
    clean held-out responses for coverage. Per-frequency noise = SIGMA_U_REL * RMS(response)."""
    rng = np.random.default_rng(seed + int(round(eps * 1e6)) + 7919 * n_rep)
    nf = len(DRIVE_FREQS_FIT)
    u_true = np.column_stack([analytic_response(THETA_TRUE, eps, w, SENSORS) for w in DRIVE_FREQS_FIT])
    sig_u = SIGMA_U_REL * np.sqrt(np.mean(u_true ** 2, axis=0))     # (n_freq,)
    sig_u = np.maximum(sig_u, 1e-6)
    y_u = u_true[None, :, :] + rng.normal(0, 1, (n_rep, len(SENSORS), nf)) * sig_u[None, None, :]
    u_held = np.column_stack([analytic_response(THETA_TRUE, eps, w, SENSORS) for w in DRIVE_FREQS_HELDOUT])
    sig_uh = SIGMA_U_REL * np.sqrt(np.mean(u_held ** 2, axis=0))
    sig_uh = np.maximum(sig_uh, 1e-6)
    return Data(drive_fit=DRIVE_FREQS_FIT.copy(), drive_held=DRIVE_FREQS_HELDOUT.copy(),
                y_u=y_u, u_true=u_true, sigma_u=sig_u, u_held_true=u_held, sigma_u_held=sig_uh,
                eps=float(eps), n_rep=int(n_rep))


def response_dtheta(theta, k_f, omega, x=SENSORS, h=1e-4):
    """Sensitivity du/dtheta of the analytic forced response at sensors (identifiability of theta)."""
    up = analytic_response(theta + h, k_f, omega, x)
    um = analytic_response(theta - h, k_f, omega, x)
    return (up - um) / (2 * h)


def omega_nominal(modes):
    """Nominal (theta=1, no foundation) frequencies, for resonance reference lines."""
    return analytic_omega(1.0, 0.0, modes)
