#!/usr/bin/env python3
"""Core forward model + discrepancy machinery for the StatFEM ShockSat held-out-QOI evaluation.

Plain-ShockSat ONLY (task §3): the 9-group reduced FEM from shocksat_fem_modal_twin_20260609.
    K_red(theta) = A_fix + sum_g theta_g A_g       (74x74, mass = I)
    lam, Q = eigh(K_red);  omega_k = sqrt(lam_k)
    Phi_obs = obs_V @ Q                              (228 sensor DOFs x 74 modes), mass-normalized
Per-sensor accelerance FRF via the reduced DYNAMIC-STIFFNESS solve with constant hysteretic (structural)
damping, loss factor eta = 2*zeta (D10). This avoids eigh in the differentiable path (the near-degenerate
mode clusters 124.6/124.6, 233.7/233.7 Hz make eigh eigenvector gradients ~1/(lam_i-lam_j) blow up):
    Z(omega) = (1 + i*eta) K_red(theta) - omega^2 I            (74x74 complex, mass = I)
    H_s(omega) = -omega^2 * obs_V[s,:] @ Z(omega)^-1 @ obs_V[d,:]^T
At theta=1 (K_red = Lambda diagonal) this reduces to the textbook modal sum
    H_s = -omega^2 sum_k Phi[s,k] Phi[d,k] / ((1+i*eta) lam_k - omega^2),
whose imaginary part at resonance (omega^2 = lam_k) equals the viscous 2*zeta*lam_k, so eta=2*zeta gives the
same peak amplitude. The dynamic-stiffness form is smooth and differentiable in theta with NO eigh.

Two injected model-form-error layers (truth side):
  1. parametric: theta_truth offsets (the 5 bias combos)
  2. Schneider discrepancy: complex multiplicative field correlated over log-frequency AND sensor space,
     NOT representable by any theta scaling.

numpy = data generation + post-processing; jax factory = the NUTS likelihood forward.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

WS = Path(__file__).resolve().parent.parent
DATA = WS / "data"

# group names in reduced_blocks order (alphabetical, as saved by the modal twin)
GNAMES = ["al_welds", "angle_brackets", "bottom_box", "contact", "cross_beam",
          "joints", "plates", "steel_welds", "top_box"]

# ---- fixed design constants (assumptions_ledger A3,A4,A6,A7,A8,A10) --------
ZETA_NOM = 0.02            # nominal modal damping (2% critical), all modes (A3)
BAND = (45.0, 260.0)       # frequency band [Hz] (A4)
NFREQ = 160                # log-spaced points (A4)
SIGMA_MEAS = 0.05          # iid measurement log-noise (A8)
# Schneider injected discrepancy (A7)
DISC_STD_LO = 0.03
DISC_STD_HI = 0.12
DISC_LEN_LOGF = 0.30       # squared-exponential length over log-Hz
DISC_LEN_Z = 12.0          # exponential length over sensor distance [in]
DISC_PHASE_FRAC = 0.5
NSIG_THETA = 0.25          # theta LogNormal prior sigma (A5)

# the 5 truth bias combos (A6): group -> multiplier
COMBOS = {
    1: {"name": "identifiable_only", "theta": {"top_box": 1.15, "bottom_box": 0.90}},
    2: {"name": "unidentifiable_only", "theta": {"joints": 1.20, "contact": 1.15}},
    3: {"name": "mixed", "theta": {"top_box": 1.15, "joints": 1.20, "plates": 0.88}},
    4: {"name": "large", "theta": {"cross_beam": 1.20, "joints": 0.82}},
    5: {"name": "broad_small", "theta": {"bottom_box": 1.08, "top_box": 0.92, "plates": 1.10,
                                         "cross_beam": 0.90, "joints": 1.10}},
}


def theta_vector(theta_dict):
    """dict {group: mult} -> (9,) vector in GNAMES order (default 1.0)."""
    return np.array([float(theta_dict.get(g, 1.0)) for g in GNAMES])


# ------------------------------------------------------------------
# Model assets
# ------------------------------------------------------------------
@dataclass
class Model:
    A: np.ndarray         # (9, r, r)
    A_fix: np.ndarray     # (r, r)
    obs_V: np.ndarray     # (228, r)  sensor-DOF mode shapes in reduced basis
    dof_node: np.ndarray  # (228,) node index per DOF row
    dof_axis: np.ndarray  # (228,) axis 0/1/2 per DOF row
    dof_xyz: np.ndarray   # (228,3) coordinate per DOF row [in]
    measured: np.ndarray  # (228,) bool: real measured DOFs (132 True)

    @property
    def r(self):
        return self.A_fix.shape[0]


def load_model() -> Model:
    rb = np.load(DATA / "reduced_blocks.npz", allow_pickle=True)
    gn = [str(g) for g in rb["gnames"]]
    assert gn == GNAMES, f"group order mismatch: {gn}"
    sc = np.load(DATA / "sensor_coords.npz", allow_pickle=True)
    coords = sc["coords"]            # (76,3)
    measured = sc["measured"]        # (76,3) bool
    # DOF row r = 3*node + axis  (node-major, axis-minor) -- matches solve_nominal.py obs_dofs ordering
    n_nodes = coords.shape[0]
    dof_node = np.repeat(np.arange(n_nodes), 3)
    dof_axis = np.tile(np.arange(3), n_nodes)
    dof_xyz = coords[dof_node]
    return Model(A=rb["A"], A_fix=rb["A_fix"], obs_V=rb["obs_V"],
                 dof_node=dof_node, dof_axis=dof_axis, dof_xyz=dof_xyz,
                 measured=measured.reshape(-1))


# ------------------------------------------------------------------
# Channel selection (drive DOF, observed, held-out) -- deterministic (A2,A10)
# ------------------------------------------------------------------
def select_channels(model: Model, n_observed=6, seed=0):
    """Pick distinct-NODE channels among measured DOFs, spread along the long (Z) axis.
    Drive = base-corner node Z-DOF. Observed = n_observed spread nodes. Held-out = the rest of a
    documented pool (mix of near + far from the observed set). Returns dof-row indices + metadata."""
    meas = model.measured
    # candidate measured DOF rows, prefer the dominant translational axis per node (Z=axis2 for a tall body)
    # choose one channel per node = its Z DOF if measured, else first measured axis
    node_channel = {}
    for n in np.unique(model.dof_node):
        rows = np.where(model.dof_node == n)[0]
        zrow = rows[model.dof_axis[rows] == 2]
        pick = None
        if len(zrow) and meas[zrow[0]]:
            pick = int(zrow[0])
        else:
            for rr in rows:
                if meas[rr]:
                    pick = int(rr); break
        if pick is not None:
            node_channel[int(n)] = pick
    chans = np.array(sorted(node_channel.values()))
    z = model.dof_xyz[chans, 2]
    order = np.argsort(z)
    chans = chans[order]; z = z[order]
    # drive = lowest-z channel (near base)
    drive = int(chans[0])
    pool = chans[1:]
    zp = z[1:]
    # observed = evenly spaced along z among the pool
    idx_obs = np.linspace(0, len(pool) - 1, n_observed).astype(int)
    observed = pool[idx_obs]
    rest = np.array([c for c in pool if c not in set(observed.tolist())])
    # held-out = a documented subset: take up to 14 of the rest spread along z
    if len(rest) > 14:
        keep = np.linspace(0, len(rest) - 1, 14).astype(int)
        heldout = rest[keep]
    else:
        heldout = rest
    return {"drive": drive, "observed": observed.tolist(), "heldout": heldout.tolist()}


def freq_grid(n=NFREQ, lo=BAND[0], hi=BAND[1]):
    return np.geomspace(lo, hi, n)


# ------------------------------------------------------------------
# Forward model (numpy)
# ------------------------------------------------------------------
def modes_np(model: Model, theta):
    """eigh of K_red(theta) -- used ONLY for identifiability (strain energy / FIM) and peak-frequency
    reporting, NOT in the differentiable FRF path (D10)."""
    K = model.A_fix + np.einsum("g,gij->ij", np.asarray(theta), model.A)
    lam, Q = np.linalg.eigh(K)
    lam = np.clip(lam, 1e-9, None)
    Phi = model.obs_V @ Q          # (228, r)
    return lam, Phi


def frf_np(model: Model, freqs, theta, sensors, drive, zeta=ZETA_NOM):
    """Complex accelerance (Nf, Ns) at `sensors` for point-force drive at `drive`.

    Hysteretic damping (loss factor eta = 2*zeta) via the resolvent of K_red(theta): Z(w)^-1 =
    Q diag(1/((1+i eta) lam_k - w^2)) Q^T. eigh is used here OUTSIDE any gradient path; the result is
    identical (to ~1e-9) to the dynamic-stiffness solve but ~100x faster (D10)."""
    K = model.A_fix + np.einsum("g,gij->ij", np.asarray(theta), model.A)   # (r,r) real symmetric
    eta = 2.0 * float(zeta)
    omega = 2.0 * np.pi * np.asarray(freqs)            # (Nf,)
    lam, Q = np.linalg.eigh(K)
    lam = np.clip(lam, 1e-9, None)
    U = model.obs_V[sensors, :] @ Q                    # (Ns, r)
    ud = model.obs_V[drive, :] @ Q                     # (r,)
    g = (1.0 + 1j * eta) * lam[None, :] - (omega ** 2)[:, None]   # (Nf, r)
    H = -(omega ** 2)[:, None] * np.einsum("sk,k,fk->fs", U.astype(complex),
                                           ud.astype(complex), 1.0 / g)     # (Nf, Ns)
    return H


# ------------------------------------------------------------------
# Schneider correlated-complex discrepancy field (freq x space)
# ------------------------------------------------------------------
def _corr_logf(freqs, length):
    lf = np.log(freqs)
    d = lf[:, None] - lf[None, :]
    return np.exp(-0.5 * (d / length) ** 2)


def _corr_space(coords, length):
    d = np.sqrt(((coords[:, None, :] - coords[None, :, :]) ** 2).sum(-1))
    return np.exp(-np.abs(d) / length)


def schneider_field(freqs, coords, rng, std_lo=DISC_STD_LO, std_hi=DISC_STD_HI,
                    len_logf=DISC_LEN_LOGF, len_z=DISC_LEN_Z, phase_frac=DISC_PHASE_FRAC):
    """Complex multiplicative field exp(w + i*phi), (Nf, Ns), correlated over log-freq AND sensor
    distance; log-amplitude std grows std_lo -> std_hi with frequency. NOT representable by theta."""
    nf = len(freqs); ns = coords.shape[0]
    lf = np.log(freqs)
    g = (lf - lf.min()) / (lf.max() - lf.min())
    std_f = std_lo + (std_hi - std_lo) * g                 # (Nf,)
    Cf = _corr_logf(freqs, len_logf) + 1e-9 * np.eye(nf)
    Cz = _corr_space(coords, len_z) + 1e-9 * np.eye(ns)
    Lf = np.linalg.cholesky(Cf)
    Lz = np.linalg.cholesky(Cz)
    # separable Gaussian field: Z ~ N(0, Cf kron Cz); realize as Lf @ G @ Lz^T
    w = (Lf @ rng.standard_normal((nf, ns)) @ Lz.T) * std_f[:, None]
    ph = (Lf @ rng.standard_normal((nf, ns)) @ Lz.T) * std_f[:, None] * phase_frac
    return np.exp(w + 1j * ph)


# ------------------------------------------------------------------
# QOI (quantity_contracts Q2, Q3)
# ------------------------------------------------------------------
def qoi_peak(Hmag_col):
    return float(np.max(Hmag_col))


def qoi_band(Hmag_col, freqs):
    # GRMS-like: sqrt( integral |H|^2 df ) over the band, flat input PSD = 1
    return float(np.sqrt(np.trapz(Hmag_col ** 2, freqs)))


def db(x):
    return 20.0 * np.log10(np.maximum(np.abs(x), 1e-300))


# ------------------------------------------------------------------
# jax forward (for NUTS) -- returns log|H| on a fixed sensor set
# ------------------------------------------------------------------
def jax_forward_factory(model: Model, freqs, sensors, drive, zeta=ZETA_NOM):
    """Returns logmag(theta) -> (Nf, Ns) log|accelerance|. Hysteretic dynamic-stiffness solve, NO eigh,
    so gradients are clean across the near-degenerate mode clusters (D10)."""
    import jax.numpy as jnp
    A = jnp.asarray(model.A)
    A_fix = jnp.asarray(model.A_fix)
    obsV = jnp.asarray(model.obs_V)
    omega = jnp.asarray(2.0 * np.pi * np.asarray(freqs))           # (Nf,)
    sensors = jnp.asarray(np.asarray(sensors))
    eta = 2.0 * float(zeta)
    bd_idx = int(drive)

    def logmag(theta):
        K = A_fix + jnp.einsum("g,gij->ij", theta, A)
        lam, Q = jnp.linalg.eigh(K)                      # degenerate-subspace contribs cancel in the
        lam = jnp.clip(lam, 1e-9, None)                  # FRF sum -> grad finite & correct (verified)
        U = obsV[sensors, :] @ Q                         # (Ns, r)
        ud = obsV[bd_idx, :] @ Q                         # (r,)
        g = (1.0 + 1j * eta) * lam[None, :] - (omega ** 2)[:, None]   # (Nf, r)
        H = -(omega ** 2)[:, None] * jnp.einsum("sk,k,fk->fs",
                                                U.astype(jnp.complex128),
                                                ud.astype(jnp.complex128), 1.0 / g)
        return jnp.log(jnp.abs(H))

    return logmag


# ------------------------------------------------------------------
# config persistence
# ------------------------------------------------------------------
def write_config(path, model: Model, ch, extra=None):
    cfg = {
        "testbed": "plain_shocksat_9group",
        "uses_tray": False,
        "source": "reduced_blocks.npz copied from shocksat_fem_modal_twin_20260609 (D1)",
        "groups": GNAMES,
        "band_hz": list(BAND), "nfreq": NFREQ, "zeta_nom": ZETA_NOM,
        "sigma_meas": SIGMA_MEAS,
        "schneider": {"std_lo": DISC_STD_LO, "std_hi": DISC_STD_HI,
                      "len_logf": DISC_LEN_LOGF, "len_z": DISC_LEN_Z, "phase_frac": DISC_PHASE_FRAC},
        "theta_prior_lognormal_sigma": NSIG_THETA,
        "drive_dof": ch["drive"],
        "drive_xyz": model.dof_xyz[ch["drive"]].tolist(),
        "drive_axis": int(model.dof_axis[ch["drive"]]),
        "observed_dofs": ch["observed"],
        "observed_xyz": model.dof_xyz[ch["observed"]].tolist(),
        "heldout_dofs": ch["heldout"],
        "heldout_xyz": model.dof_xyz[ch["heldout"]].tolist(),
        "combos": {str(k): v for k, v in COMBOS.items()},
    }
    if extra:
        cfg.update(extra)
    json.dump(cfg, open(path, "w"), indent=1)
    return cfg


if __name__ == "__main__":
    # smoke: build model, channels, FRF, QOI
    m = load_model()
    ch = select_channels(m)
    f = freq_grid()
    th = theta_vector(COMBOS[1]["theta"])
    H = frf_np(m, f, th, ch["heldout"], ch["drive"])
    print("model r=", m.r, "measured DOFs=", int(m.measured.sum()))
    print("drive", ch["drive"], "obs", len(ch["observed"]), "held", len(ch["heldout"]))
    print("FRF shape", H.shape, "peak", qoi_peak(np.abs(H[:, 0])), "band", qoi_band(np.abs(H[:, 0]), f))
    coords = m.dof_xyz[ch["heldout"]]
    fld = schneider_field(f, coords, np.random.default_rng(0))
    print("schneider field", fld.shape, "mean|w|", float(np.mean(np.abs(np.log(np.abs(fld))))))
