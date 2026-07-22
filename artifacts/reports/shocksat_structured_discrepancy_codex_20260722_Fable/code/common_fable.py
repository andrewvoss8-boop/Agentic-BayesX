#!/usr/bin/env python3
"""Task Card E `_Fable` — shared data layer, forward model, exact Gaussian machinery, metrics.

Everything in this module is DETERMINISTIC given the frozen inputs. No sampler is used anywhere in Stage 1.

Naming: `_fable` marks this run so it cannot be confused with a parallel runner on the same card.

Key objects
-----------
`load_frozen()`      -> FrozenInputs: reduced FEM model, channels (coords/axes/regions), 5 measured drives,
                        modal-posterior theta draws.
`q_fem(...)`         -> ln(|H1_fem| / H_ref), H_ref = 1 g/lbf  (dimensionless, card quantity contract).
`KronGP`             -> exact solves for  Sigma = su^2 [ r Kf (x) Ix + If (x) Bx ] + se^2 I  on a complete
                        frequency x channel grid, extended by a low-rank theta term with the Woodbury identity.
`gls_fit` / `predict`-> exact universal-kriging conditional with an explicit Gaussian coefficient posterior,
                        keeping E[H* beta | train] and E[u* | train] SEPARATE (card requirement).
`crps_gauss`, `coverage`, `interval_width`, `median_abs_db` -> scoring, all in dB via 20/ln(10) * q.
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# ----------------------------------------------------------------------------------- paths (read-only inputs)
WS = Path(__file__).resolve().parent.parent
REPO = WS.parent.parent.parent
L5 = REPO / "artifacts/reports/shocksat_modelclass_L5_20260619"
NETCG = REPO / "artifacts/reports/shocksat_netcg_method_selection_20260701"
TWIN = REPO / "artifacts/reports/shocksat_fem_modal_twin_20260609"
RVAL = REPO / "artifacts/reports/statfem_real_validation_20260617"
DRIVE_DIR = NETCG / "data/multiref_modal"

OUT = WS / "out"
FIGS = WS / "figures"

# ----------------------------------------------------------------------------------- frozen constants (card)
H_REF_DESC = "1 g/lbf (force-referenced accelerance magnitude)"
DB = 20.0 / np.log(10.0)                 # q (dimensionless log-ratio) -> dB
BAND = (46.79361979166667, 258.38216145833337)   # measured analysis band endpoints [Hz], native cache grid
ZETA_PRIMARY = 0.01                      # decisions_log F1
L_F_HZ = 10.0                            # frozen Schneider-style frequency length scale [Hz]
L_X_IN = 2000.0                          # frozen spatial length scale [in]
R_SPLIT = 0.82                           # frozen additive-kernel split
GUARD_HZ = 10.0                          # frequency-fold guard band
N_SPATIAL_CLUSTERS = 5
N_FREQ_CORES = 5
RANK_TOL = 1e-8                          # deterministic rank-deficiency tolerance, frozen before fitting
PINV_TOL = 1e-10                         # pseudoinverse tolerance for the orthogonality projector

DRIVES = [                               # (key, label, drive axis) — frozen order
    ("m_xpos_990x", "+X (990)", "X"),
    ("m_ypos_990y", "+Y (990)", "Y"),
    ("m_zpos_990z", "+Z (990)", "Z"),
    ("m_zpos_900z", "+Z (900)", "Z"),
    ("m_xy_990xy", "+XY (990)", "XY"),
]

# frozen physical features, copied verbatim from shocksat_modelclass_L5_20260619/code/spatial_reanalysis.py
FEAT_POINTS = {
    "bolted_joint": np.array([9.0, -0.4, 19.1]),
    "strut": np.array([8.7, 0.0, 49.6]),
    "dish": np.array([1.9, 0.0, 57.0]),
}
BULKHEAD_Z = np.array([12.4, 18.4, 30.4])
IMPACT_XYZ = np.array([9.0, 8.0, 1.0])   # tap-impact reference point used by the frozen loader
REGION_NAMES = ["source_face", "bolted_joint", "strut", "dish", "bulkhead"]


def _l5_realfrf():
    """Import the frozen realfrf module WITHOUT modifying it."""
    p = str(L5 / "code")
    if p not in sys.path:
        sys.path.insert(0, p)
    import realfrf as rf     # noqa: E402
    return rf


# ----------------------------------------------------------------------------------- frozen input container
@dataclass
class FrozenInputs:
    rf: object                       # frozen realfrf module
    R: object                        # realfrf.Reduced
    daq: np.ndarray                  # (Nc,) DAQ channel ids, sorted
    coords: np.ndarray               # (Nc,3) inches, frozen ShockSat frame
    axes: list                       # (Nc,) response-axis labels 'X'/'Y'/'Z' (sign stripped)
    axes_signed: list                # (Nc,) raw labels incl. '-X'
    region: np.ndarray               # (Nc,) int index into REGION_NAMES
    rows: np.ndarray                 # (Nc,74) reduced response rows
    freqs: np.ndarray                # (Nf,) Hz
    drive_rows: dict                 # key -> (74,) reduced drive row
    drive_xyz: dict                  # key -> (3,)
    H1: dict                         # key -> (Nf, Nc) complex measured accelerance [g/lbf]
    coh: dict                        # key -> (Nf, Nc) ordinary multi-hit coherence
    n_hits: dict                     # key -> int
    theta_draws: np.ndarray          # (M,9) modal-posterior draws
    gnames: list
    theta0: np.ndarray               # (9,) posterior median

    @property
    def Nf(self):
        return len(self.freqs)

    @property
    def Nc(self):
        return len(self.daq)


def load_frozen(n_theta: int = 200, seed: int = 20260722) -> FrozenInputs:
    rf = _l5_realfrf()
    R = rf.load_reduced()

    c0 = np.load(DRIVE_DIR / f"{DRIVES[0][0]}.npz", allow_pickle=True)
    daq_all = [int(d) for d in c0["daq"]]
    ch = rf.build_channels(R, daq_all)                      # applies BAD_DAQ + coordinate/axis availability
    order = np.argsort(np.asarray(ch.daq))
    daq = np.asarray(ch.daq)[order]
    coords = np.asarray(ch.coords)[order]
    axes_signed = [ch.axes[i] for i in order]
    axes = [a.lstrip("-") for a in axes_signed]
    rows = np.asarray(ch.rows)[order]
    freqs = np.asarray(c0["freqs"], float)

    # region by nearest frozen physical feature (design information only)
    d_imp = np.linalg.norm(coords - IMPACT_XYZ[None, :], axis=1)
    dists = [d_imp]
    for k in ["bolted_joint", "strut", "dish"]:
        dists.append(np.linalg.norm(coords - FEAT_POINTS[k][None, :], axis=1))
    dists.append(np.min(np.abs(coords[:, 2][:, None] - BULKHEAD_Z[None, :]), axis=1))
    region = np.argmin(np.stack(dists, axis=0), axis=0)

    drive_rows, drive_xyz, H1, coh, n_hits = {}, {}, {}, {}, {}
    for key, _lab, ax in DRIVES:
        c = np.load(DRIVE_DIR / f"{key}.npz", allow_pickle=True)
        cdaq = [int(d) for d in c["daq"]]
        idx = np.array([cdaq.index(int(d)) for d in daq])
        assert np.allclose(np.asarray(c["freqs"], float), freqs), f"{key}: frequency grid differs"
        H1[key] = np.asarray(c["H1"])[idx].T                    # (Nf, Nc)
        coh[key] = np.asarray(c["coherence"], float)[idx].T
        n_hits[key] = int(c["n_hits_used"])
        xyz = tuple(float(v) for v in c["xyz"])
        drive_xyz[key] = np.array(xyz)
        # combined +XY drive: frozen convention is the X row (see modal_multiref note); use X and record it
        ax_use = "X" if ax == "XY" else ax
        drive_rows[key], _n, _s = R.reduced_row(xyz, ax_use)

    z = np.load(TWIN / "nuts_full_samples.npz", allow_pickle=True)
    theta_all = np.asarray(z["theta"], float)
    gnames = [str(g) for g in z["gnames"]]
    rng = np.random.default_rng(seed)
    sel = rng.choice(theta_all.shape[0], size=min(n_theta, theta_all.shape[0]), replace=False)
    sel.sort()
    theta_draws = theta_all[sel]
    theta0 = np.median(theta_all, axis=0)

    return FrozenInputs(rf=rf, R=R, daq=daq, coords=coords, axes=axes, axes_signed=axes_signed,
                        region=region, rows=rows, freqs=freqs, drive_rows=drive_rows, drive_xyz=drive_xyz,
                        H1=H1, coh=coh, n_hits=n_hits, theta_draws=theta_draws, gnames=gnames, theta0=theta0)


# ----------------------------------------------------------------------------------- forward model
def q_fem(F: FrozenInputs, drive_key: str, theta: np.ndarray, zeta: float = ZETA_PRIMARY) -> np.ndarray:
    """ln(|H1_fem(d,i,f;theta,zeta)| / H_ref), H_ref = 1 g/lbf. Shape (Nf, Nc), dimensionless."""
    return F.rf.fem_logmag(F.R, F.freqs, theta, F.rows, F.drive_rows[drive_key], zeta=zeta)


def q_fem_zeta_f(F: FrozenInputs, drive_key: str, theta: np.ndarray, zeta_f: np.ndarray) -> np.ndarray:
    """SENS-1 variant: frequency-dependent modal damping. eta_k applied per frequency line."""
    R = F.R
    K = R.A_fix + np.einsum("g,gij->ij", np.asarray(theta), R.A)
    lam, Q = np.linalg.eigh(K)
    lam = np.clip(lam, 1e-9, None)
    Us = F.rows @ Q
    Ud = F.drive_rows[drive_key] @ Q
    w = 2 * np.pi * F.freqs
    eta = 2.0 * np.asarray(zeta_f)                                     # (Nf,)
    g = (1 + 1j * eta)[:, None] * lam[None, :] - (w ** 2)[:, None]
    H = -(w ** 2)[:, None] * np.einsum("sk,k,fk->fs", Us.astype(complex), Ud.astype(complex), 1.0 / g)
    return np.log(np.abs(H) / F.rf.G_IN_S2)


def q_meas(F: FrozenInputs, drive_key: str) -> np.ndarray:
    """ln(|H1_meas| / H_ref), H_ref = 1 g/lbf. Shape (Nf, Nc)."""
    return np.log(np.abs(F.H1[drive_key]) + 1e-300)


def window_zeta(F: FrozenInputs) -> np.ndarray:
    """Exponential-window added damping zeta_w(f) for the frozen processing constants."""
    return F.rf.measured_zeta_w(F.freqs)


# ----------------------------------------------------------------------------------- kernels
def kern_f(f1: np.ndarray, f2: np.ndarray, l_f: float = L_F_HZ) -> np.ndarray:
    d = f1[:, None] - f2[None, :]
    return np.exp(-0.5 * (d / l_f) ** 2)


def kern_x(x1: np.ndarray, x2: np.ndarray, l_x: float = L_X_IN) -> np.ndarray:
    """Spatial correlation. EXPONENTIAL (Ornstein-Uhlenbeck) form, byte-faithful to the frozen
    `schneider_faithful.corr_space` = exp(-|d|/length). NOT squared-exponential (checked, decisions F7)."""
    d = np.linalg.norm(x1[:, None, :] - x2[None, :, :], axis=2)
    return np.exp(-np.abs(d) / l_x)


# ----------------------------------------------------------------------------------- exact Kronecker GP
@dataclass
class KronGP:
    """Sigma = su2 [ r Kf (x) Ix + If (x) Bx ] + se2 I  on a complete (Nf x Nc) grid, plus optional low-rank.

    Vectorisation convention: a field Y with shape (Nf, Nc) flattens C-order, index = f*Nc + c.
    Exact because A (x) I + I (x) B is diagonalised by (U_f (x) U_x).
    """
    Uf: np.ndarray
    af: np.ndarray                # eigenvalues of su2 * r * Kf
    Ux: np.ndarray
    bx: np.ndarray                # eigenvalues of su2 * Bx + se2 I
    G: np.ndarray = field(default=None)     # (n, m) low-rank factor (theta uncertainty), Sigma += G G^T
    _Minv: np.ndarray = field(default=None)

    @property
    def shape(self):
        return (self.Uf.shape[0] * self.Ux.shape[0],) * 2

    @property
    def d(self):
        return self.af[:, None] + self.bx[None, :]        # (Nf, Nc) eigenvalues of the base

    def _base_solve(self, Y):
        """Solve Sigma_base z = y for y given as (Nf, Nc, k). Returns (Nf, Nc, k)."""
        Z = np.einsum("fa,fck->ack", self.Uf, Y)              # rotate frequency axis: Z[a,c,k]
        Z = np.einsum("cb,ack->abk", self.Ux, Z)              # rotate channel axis:   Z[a,b,k]
        Z = Z / self.d[:, :, None]
        Z = np.einsum("fa,abk->fbk", self.Uf, Z)              # back-rotate frequency
        Z = np.einsum("cb,fbk->fck", self.Ux, Z)              # back-rotate channel
        return Z

    def _prep_lowrank(self):
        if self.G is None or self._Minv is not None:
            return
        Nf, Nc = self.Uf.shape[0], self.Ux.shape[0]
        m = self.G.shape[1]
        SG = self._base_solve(self.G.reshape(Nf, Nc, m)).reshape(Nf * Nc, m)
        M = np.eye(m) + self.G.T @ SG
        self._Minv = np.linalg.inv(M)
        self._SG = SG

    def _as_grid(self, Y):
        Nf, Nc = self.Uf.shape[0], self.Ux.shape[0]
        Y = np.asarray(Y)
        if Y.ndim == 3:
            assert Y.shape[:2] == (Nf, Nc), f"grid shape {Y.shape} != ({Nf},{Nc},k)"
            return Y, "grid3"
        if Y.ndim == 2 and Y.shape == (Nf, Nc):
            return Y[:, :, None], "grid2"
        if Y.ndim == 2 and Y.shape[0] == Nf * Nc:
            return Y.reshape(Nf, Nc, Y.shape[1]), "flat2"
        if Y.ndim == 1 and Y.shape[0] == Nf * Nc:
            return Y.reshape(Nf, Nc, 1), "flat1"
        raise ValueError(f"cannot interpret shape {Y.shape} for grid ({Nf},{Nc})")

    def solve(self, Y):
        """Sigma^{-1} y. Y is (Nf,Nc), (Nf,Nc,k), flat (n,) or flat (n,k); same layout returned."""
        Nf, Nc = self.Uf.shape[0], self.Ux.shape[0]
        Yg, kind = self._as_grid(Y)
        Z = self._base_solve(Yg)
        if self.G is not None:
            self._prep_lowrank()
            Zf = Z.reshape(Nf * Nc, -1)
            Zf = Zf - self._SG @ (self._Minv @ (self.G.T @ Zf))
            Z = Zf.reshape(Nf, Nc, -1)
        if kind == "grid3":
            return Z
        if kind == "grid2":
            return Z[:, :, 0]
        if kind == "flat2":
            return Z.reshape(Nf * Nc, -1)
        return Z.reshape(Nf * Nc)

    def logdet(self):
        ld = float(np.sum(np.log(self.d)))
        if self.G is not None:
            self._prep_lowrank()
            sign, val = np.linalg.slogdet(np.eye(self.G.shape[1]) + self.G.T @ self._SG)
            ld += float(val)
        return ld


def build_kron(freqs, coords, su2, se2, nugget, r=R_SPLIT, l_f=L_F_HZ, l_x=L_X_IN, G=None) -> KronGP:
    """nugget: (Nc,) per-channel white-in-frequency variance."""
    Kf = kern_f(freqs, freqs, l_f)
    Bx = (1.0 - r) * kern_x(coords, coords, l_x) + np.diag(np.asarray(nugget) / max(su2, 1e-300))
    af, Uf = np.linalg.eigh(su2 * r * Kf)
    bx, Ux = np.linalg.eigh(su2 * Bx + se2 * np.eye(len(coords)))
    af = np.clip(af, 0.0, None)
    bx = np.clip(bx, 1e-12, None)
    return KronGP(Uf=Uf, af=af, Ux=Ux, bx=bx, G=G)


def cross_cov(f_star, x_star, f_tr, x_tr, su2, r=R_SPLIT, l_f=L_F_HZ, l_x=L_X_IN):
    """K_*T for the additive Schneider-style kernel, on grids (f_star x x_star) vs (f_tr x x_tr).

    Returned as the pair (Af, Bx_) with K_*T = su2 [ r Af (x) I_match + (1-r) I_match (x) Bx_ ] handled by
    `cross_apply`, because the delta structure makes the full dense matrix unnecessary.
    """
    Af = kern_f(f_star, f_tr, l_f)                       # (Ns_f, Nt_f)
    Kx = kern_x(x_star, x_tr, l_x)                       # (Ns_c, Nt_c)
    return Af, Kx


def cross_apply(Af, Kx, f_match, x_match, su2, V, r=R_SPLIT):
    """Apply K_*T to a training-shaped field V (Nt_f, Nt_c, k) -> (Ns_f, Ns_c, k).

    f_match[i, j] = 1 if star frequency i IS training frequency j (exact same line), else 0.
    x_match[a, b] = 1 if star channel a IS training channel b, else 0.
    K((f,x),(f',x')) = su2 [ r kf(f,f') delta_xx' + (1-r) delta_ff' kx(x,x') ].
    """
    sq = V.ndim == 2
    if sq:
        V = V[:, :, None]
    t1 = np.einsum("ij,jbk,ab->iak", Af, V, x_match)           # r * kf * delta_x
    t2 = np.einsum("ij,jbk,ab->iak", f_match, V, Kx)           # (1-r) * delta_f * kx
    out = su2 * (r * t1 + (1.0 - r) * t2)
    return out[:, :, 0] if sq else out


def prior_var_star(su2, nugget_star, se2, r=R_SPLIT):
    """Diagonal of K_** + observation variance at held-out points (kf(0)=kx(0)=1)."""
    return su2 * (r + (1.0 - r)) + np.asarray(nugget_star) + se2


# ----------------------------------------------------------------------------------- metrics
def crps_gauss(y, mu, sd):
    """Closed-form CRPS of a Gaussian predictive distribution. Lower is better. Same units as y."""
    from scipy.stats import norm
    z = (np.asarray(y) - np.asarray(mu)) / np.asarray(sd)
    return np.asarray(sd) * (z * (2 * norm.cdf(z) - 1) + 2 * norm.pdf(z) - 1.0 / np.sqrt(np.pi))


def coverage(y, mu, sd, level=0.90):
    from scipy.stats import norm
    z = norm.ppf(0.5 + level / 2.0)
    lo, hi = mu - z * sd, mu + z * sd
    return float(np.mean((y >= lo) & (y <= hi)))


def interval_width(sd, level=0.90):
    from scipy.stats import norm
    return 2.0 * norm.ppf(0.5 + level / 2.0) * np.asarray(sd)


def median_abs_db(y, mu):
    return float(np.median(np.abs((np.asarray(y) - np.asarray(mu)) * DB)))


# ----------------------------------------------------------------------------------- generic Gaussian GLS
def gls_fit(Xd, y, gp: KronGP, prior_mu, prior_var):
    """Exact Gaussian posterior of coefficients b for  y = Xd b + noise(Sigma=gp),  b ~ N(prior_mu, diag(prior_var)).

    Xd: (n, p) design (flat), y: (n,). Returns (b_hat, Cov_b, Sinv_resid) where Sinv_resid = Sigma^{-1}(y - Xd b_hat).
    """
    n, p = Xd.shape
    SX = gp.solve(Xd)                                    # (n,p)
    Sy = gp.solve(y)
    A = Xd.T @ SX + np.diag(1.0 / np.asarray(prior_var))
    rhs = Xd.T @ Sy + np.asarray(prior_mu) / np.asarray(prior_var)
    Cov_b = np.linalg.inv(A)
    b_hat = Cov_b @ rhs
    resid = y - Xd @ b_hat
    return b_hat, Cov_b, gp.solve(resid)


def drop_rank_deficient(H, tol=RANK_TOL):
    """Deterministic column removal by pivoted-QR-free SVD test. Returns (H_kept, kept_idx)."""
    if H.shape[1] == 0:
        return H, np.arange(0)
    scale = np.maximum(np.linalg.norm(H, axis=0), 1e-300)
    Hs = H / scale
    s = np.linalg.svd(Hs, compute_uv=False)
    if s.size == 0 or s[0] <= 0:
        return H[:, :0], np.arange(0)
    # greedy deterministic: keep columns left-to-right whose addition raises the numerical rank
    kept = []
    for j in range(H.shape[1]):
        trial = kept + [j]
        sv = np.linalg.svd(Hs[:, trial], compute_uv=False)
        if sv[-1] / sv[0] > tol:
            kept = trial
    kept = np.array(kept, dtype=int)
    return H[:, kept], kept
