#!/usr/bin/env python3
"""Shared core for the virtual-sensing-target credibility toy.

Reproduces the *updating* stage of Yan et al. (2026), "Physics-Informed Digital Twin for
Spacecraft Structures under Sensor Faults" (Aerospace Sci. & Tech.), and extends it with
the uncertainty quantification the paper defers to future work.

Forward model = the paper's modal-ROM FRF with its updating parameterization (Eqs. 4,11,12):
  Mr = I (mass-normalized modes), Kr(alpha)=Sa Kr0 Sa, Cr(beta)=Sb Cr0 Sb, input coupling gamma.
Diagonal reduced matrices => modal-superposition FRF:
  H_c(w; theta) = gamma * sum_i Phi_{c,i} part_i / (alpha_i^2 wi^2 + j w beta_i^2 (2 zeta_i wi) - w^2)
with part_i = (Phi^T Binput)_i.

We DO NOT reimplement the FAU deep network. The FAU "virtual ground truth" is replaced by a
LABELED surrogate (truth FRF + a controlled reconstruction error), calibrated to the paper's
reported masked-channel residual (~8-10 dB). This is a stand-in, not the network.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

# ------------------------------------------------------------------
# Fixed problem geometry (see assumptions_ledger.md A2-A5)
# ------------------------------------------------------------------
GAMMA0 = 0.02  # nominal input-coupling scale (paper gamma ~ 2%)
ALPHA_BOX = (0.5, 1.5)
BETA_BOX = (0.1, 10.0)
GAMMA_BOX = (0.005, 0.05)

# Channel labels: Ch1,Ch2 observed; Ch3,Ch4 masked (the paper's A3 fault).
OBSERVED = np.array([0, 1])
MASKED = np.array([2, 3])


@dataclass
class Modes:
    f: np.ndarray  # natural frequencies [Hz], shape (Nm,)
    zeta: np.ndarray  # modal damping ratios [-], shape (Nm,)
    Phi: np.ndarray  # mode-shape / output matrix, shape (Nc, Nm)
    Binput: np.ndarray  # physical input distribution, shape (Nc,)
    part: np.ndarray = field(init=False)  # modal participation (Phi^T Binput), shape (Nm,)

    def __post_init__(self):
        self.part = self.Phi.T @ self.Binput

    @property
    def nm(self):
        return self.f.shape[0]

    @property
    def nc(self):
        return self.Phi.shape[0]


def default_modes() -> Modes:
    """E1/E2 modes: a low- and a high-frequency mode inside the [5,1000] Hz window."""
    f = np.array([18.0, 95.0, 280.0, 720.0])
    zeta = np.array([0.020, 0.015, 0.020, 0.025])
    # Distinct, channel-coupling mode shapes (every mode appears in every channel).
    Phi = np.array(
        [
            [1.00, 0.85, 0.60, 0.40],
            [0.90, -0.70, 0.95, -0.55],
            [0.70, 0.60, -0.80, 0.90],
            [0.50, -0.95, -0.45, -0.85],
        ]
    )
    Binput = np.array([1.0, 0.6, 0.3, 0.2])
    return Modes(f=f, zeta=zeta, Phi=Phi, Binput=Binput)


def local_mode_modes() -> Modes:
    """Like default_modes, but the high-frequency mode 4 is a LOCAL mode living mostly at the
    failed (masked) sensors Ch3/Ch4 - so its parameters are only weakly observable once those
    channels are masked. Ties identifiability and bias-confounding directly to the sensor fault."""
    f = np.array([18.0, 95.0, 280.0, 760.0])
    zeta = np.array([0.020, 0.015, 0.020, 0.025])
    Phi = np.array(
        [
            [1.00, 0.85, 0.60, 0.04],     # Ch1 (observed): barely sees mode 4
            [0.90, -0.70, 0.95, -0.06],   # Ch2 (observed): barely sees mode 4
            [0.70, 0.60, -0.80, 0.95],    # Ch3 (masked): strong mode 4
            [0.50, -0.95, -0.45, -0.90],  # Ch4 (masked): strong mode 4
        ]
    )
    Binput = np.array([1.0, 0.6, 0.3, 0.2])
    return Modes(f=f, zeta=zeta, Phi=Phi, Binput=Binput)


def freq_grid(n=160, lo=5.0, hi=1000.0):
    return np.geomspace(lo, hi, n)


# ------------------------------------------------------------------
# Forward model (numpy)
# ------------------------------------------------------------------
def frf_np(freqs, alpha, beta, gamma, modes: Modes):
    """Return complex FRF, shape (Nf, Nc)."""
    omega = 2.0 * np.pi * np.asarray(freqs)
    wi = 2.0 * np.pi * modes.f
    alpha = np.asarray(alpha)
    beta = np.asarray(beta)
    D = (
        (alpha**2 * wi**2)[None, :]
        + 1j * omega[:, None] * (beta**2 * (2.0 * modes.zeta * wi))[None, :]
        - (omega**2)[:, None]
    )  # (Nf, Nm)
    modal = modes.Phi * modes.part[None, :]  # (Nc, Nm)
    H = gamma * np.einsum("ci,fi->fc", modal, 1.0 / D)  # (Nf, Nc)
    return H


# ------------------------------------------------------------------
# Forward model (jax) -- imported lazily inside NUTS code
# ------------------------------------------------------------------
def frf_jax_factory():
    import jax.numpy as jnp

    def frf_j(freqs, alpha, beta, gamma, Phi_part, wi, two_zeta_wi):
        omega = 2.0 * jnp.pi * freqs
        D = (
            (alpha**2 * wi**2)[None, :]
            + 1j * omega[:, None] * (beta**2 * two_zeta_wi)[None, :]
            - (omega**2)[:, None]
        )
        H = gamma * jnp.einsum("ci,fi->fc", Phi_part, 1.0 / D)
        return H

    return frf_j


# ------------------------------------------------------------------
# Structured model-form discrepancy (out of the alpha/beta/gamma span)
# ------------------------------------------------------------------
def correlated_logfield(freqs, nc, rng, std_lo, std_hi, corr_logf=0.25, phase_frac=0.5):
    """Smooth complex multiplicative field, correlated over log-frequency, std growing
    from low to high frequency. NOT representable by modal scalings."""
    logf = np.log(freqs)
    g = (logf - logf.min()) / (logf.max() - logf.min())  # 0..1
    std = std_lo + (std_hi - std_lo) * g  # (Nf,)
    # Squared-exponential correlation over log-freq.
    dl = logf[:, None] - logf[None, :]
    Kc = np.exp(-0.5 * (dl / corr_logf) ** 2) + 1e-9 * np.eye(len(freqs))
    L = np.linalg.cholesky(Kc)
    fields = np.zeros((len(freqs), nc), dtype=complex)
    for c in range(nc):
        amp = (L @ rng.standard_normal(len(freqs))) * std
        pha = (L @ rng.standard_normal(len(freqs))) * std * phase_frac
        fields[:, c] = np.exp(amp + 1j * pha)
    return fields


# ------------------------------------------------------------------
# Truth / measurement / reconstruction surrogate
# ------------------------------------------------------------------
def make_truth(freqs, modes, alpha_truth, beta_truth, gamma_truth, rng,
               disc_std_lo=0.05, disc_std_hi=0.30):
    base = frf_np(freqs, np.ones(modes.nm), np.ones(modes.nm), GAMMA0, modes)  # initial FEM
    truth_modal = frf_np(freqs, alpha_truth, beta_truth, gamma_truth, modes)
    disc = correlated_logfield(freqs, modes.nc, rng, disc_std_lo, disc_std_hi)
    truth = truth_modal * disc  # truth = best-modal-fit * un-modeled discrepancy
    return {"baseline": base, "truth_modal": truth_modal, "discrepancy": disc, "truth": truth}


def measure(truth, mask_channels, rng, sigma_meas=0.05, sigma_phase=0.05):
    nf, nc = truth.shape
    noise = np.exp(rng.normal(0, sigma_meas, (nf, nc)) + 1j * rng.normal(0, sigma_phase, (nf, nc)))
    return truth * noise


def reconstruct_virtual(truth, masked, rng, recon_std_lo=0.10, recon_std_hi=0.35,
                        bias_peakshift=0.0, bias_logamp=0.0, modes=None, freqs=None):
    """Surrogate FAU virtual ground truth on masked channels: truth + reconstruction error.
    Optional COHERENT bias (E4): peak-frequency shift and/or systematic log-amplitude bias.
    Returns a full (Nf, Nc) array; only `masked` channels are meaningful."""
    nf, nc = truth.shape
    out = truth.copy()
    err = correlated_logfield(freqs, nc, rng, recon_std_lo, recon_std_hi)
    out = out * err
    if bias_logamp != 0.0:
        out = out * np.exp(bias_logamp)  # systematic amplitude bias (all freq)
    if bias_peakshift != 0.0 and modes is not None and freqs is not None:
        # Coherent peak-frequency shift: resample the magnitude/phase on a stretched axis.
        shifted = np.geomspace(freqs[0], freqs[-1], nf) * (1.0 + bias_peakshift)
        for c in masked:
            mag = np.interp(freqs, shifted, np.abs(out[:, c]))
            pha = np.interp(freqs, shifted, np.unwrap(np.angle(out[:, c])))
            out[:, c] = mag * np.exp(1j * pha)
    return out


# ------------------------------------------------------------------
# Frequency / peak weights for the objective (paper: peak-weighted log-amplitude)
# ------------------------------------------------------------------
def peak_weights(freqs, targets, channels, pamp=2.0, eps=1e-3):
    """Amplitude weighting near resonances, per paper Eq.19 (w = (|H|+eps)^pamp)."""
    w = np.zeros((len(freqs), targets.shape[1]))
    for c in channels:
        mag = np.abs(targets[:, c])
        mag = mag / (np.max(mag) + 1e-12)
        w[:, c] = (mag + eps) ** pamp
    return w


# ------------------------------------------------------------------
# Deterministic updater (paper FAU-Up / Meas-Up / Interp-Up share this engine)
# ------------------------------------------------------------------
def deterministic_update(freqs, modes, targets, channel_weights, rng, use_peak_weight=True):
    from scipy.optimize import least_squares

    nm = modes.nm
    used = np.where(channel_weights > 0)[0]
    wfreq = peak_weights(freqs, targets, used) if use_peak_weight else np.ones((len(freqs), modes.nc))
    logtgt = np.log(np.abs(targets))

    def resid(p):
        alpha = p[:nm]
        beta = p[nm:2 * nm]
        gamma = p[2 * nm]
        H = frf_np(freqs, alpha, beta, gamma, modes)
        r = np.log(np.abs(H)) - logtgt  # (Nf, Nc)
        w = np.sqrt(wfreq * channel_weights[None, :])
        return (w * r)[:, used].ravel()

    p0 = np.concatenate([np.ones(nm), np.ones(nm), [GAMMA0]])
    lo = np.concatenate([np.full(nm, ALPHA_BOX[0]), np.full(nm, BETA_BOX[0]), [GAMMA_BOX[0]]])
    hi = np.concatenate([np.full(nm, ALPHA_BOX[1]), np.full(nm, BETA_BOX[1]), [GAMMA_BOX[1]]])
    sol = least_squares(resid, p0, bounds=(lo, hi), max_nfev=4000)
    alpha = sol.x[:nm]
    beta = sol.x[nm:2 * nm]
    gamma = sol.x[2 * nm]
    return {"alpha": alpha, "beta": beta, "gamma": gamma, "cost": float(sol.cost), "H": frf_np(freqs, alpha, beta, gamma, modes)}


def interp_fill(targets_meas, observed, masked):
    """Interp-Up baseline: spatial interpolation across channel index at each frequency."""
    out = targets_meas.copy()
    nf, nc = targets_meas.shape
    xo = observed.astype(float)
    xm = masked.astype(float)
    for f in range(nf):
        # interpolate magnitude and phase separately across the (few) healthy channels
        mag = np.interp(xm, xo, np.abs(targets_meas[f, observed]))
        pha = np.interp(xm, xo, np.unwrap(np.angle(targets_meas[f, observed])))
        out[f, masked] = mag * np.exp(1j * pha)
    return out


# ------------------------------------------------------------------
# QOI / coverage helpers
# ------------------------------------------------------------------
def band_mask(freqs, lo=10.0, hi=900.0):
    return (freqs >= lo) & (freqs <= hi)


def peak_qoi(H, freqs, channel, bmask):
    mag = np.abs(H[:, channel])[bmask]
    return float(np.max(mag))


def db(x):
    return 20.0 * np.log10(np.maximum(np.abs(x), 1e-12))
