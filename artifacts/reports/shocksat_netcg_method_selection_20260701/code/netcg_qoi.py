#!/usr/bin/env python3
"""Stage 1 harness — net-CG FORCE forward + scores (coverage 1-oct / sharpness / point) + leave-modes-out.

net-CG force PSD:  S_F(w) = |G_qoi(w)|^2 * S_input,  G_qoi(w) = sum_i g_i * w^2 / D_i(w),
  g_i = uniform-mass tray-region modal participation on the QOI axis (Stage-0 definition), D_i = w_i^2 - w^2 + 2i z w_i w.
Input S_input flat (=1); all reported metrics are band-RATIOS -> input level cancels.

A "method" = an ENSEMBLE of net-CG force spectra reflecting its uncertainty representation:
  - theta_only:      spectra over theta draws (NUTS); per-mode amplitude fixed = nominal 1. SHARP; blind to
                     unmeasured-shape ignorance -> predicted to FALSELY sharpen the normal QOI.
  - freq_discrep:    spectra over theta draws x per-mode tier perturbations (freq + AMPLITUDE); unmeasured/hidden
                     modes get wide amplitude (SD_A_U) -> honest widening where the shape is unknown.
Scores vs a reference band on 1-OCTAVE log-spaced bands: coverage (band envelopes ref, narrow exceedance tolerated
as energy-weighted +dB), sharpness (95%-band GRMS-force ratio), point (GRMS error of the median vs ref).

Reused: realfrf (load_reduced), shape_borrow_diag (.ash match), modal_feature.calibrate_modal (L5 NUTS). float64.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np

WS = Path(__file__).resolve().parent.parent
BASE = WS.parent / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(BASE / "code"))
import realfrf as rf
import shape_borrow_diag as SB

BAND = (45.0, 260.0); ZETA = 0.01
TRAY_Z = 55.0
SD_F_M, SD_A_M = 0.01, 0.35
SD_F_U, SD_A_U = 0.06, 0.80
FGRID = np.linspace(BAND[0], BAND[1], 400)          # net-CG force freq grid (linear; 1-oct smoothing below)


class QOIModel:
    """Tray-region net-CG force forward on the reduced model; modes recomputed per theta."""
    def __init__(self):
        self.R = rf.load_reduced()
        keep_arr = np.empty(len(self.R.keeprow), np.int64)
        for dof, row in self.R.keeprow.items():
            keep_arr[row] = dof
        node_of = keep_arr // 6
        axis_of = keep_arr % 6
        U = np.asarray(self.R.vk[:, :80], np.float64) @ self.R.T   # (Ndof, 74) full-field basis
        z_of = self.R.xyz[node_of, 2]
        tray = z_of >= TRAY_Z
        # PRECOMPUTE the tray-region uniform-mass SUM selector per axis (a 74-vector) ONCE:
        #   g_axis(Q) = sum_{tray DOFs on axis} (U @ Q)[dof] = (sum_{tray,axis} U) @ Q  -> tiny per-theta matmul.
        self.Utray = {a: U[tray & (axis_of == a)].sum(0) for a in (0, 1, 2)}   # each (74,)
        # nominal modes + in-band + .ash match (measured modes)
        K1 = self.R.A_fix + self.R.A.sum(0)
        w2, Q = np.linalg.eigh(K1)
        f = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)
        self.inb = np.where((f >= BAND[0]) & (f <= BAND[1]))[0]
        self.fnom = f[self.inb]
        D = SB.build_dofs(self.R); _, pairs = SB.match_modes(D, Q)
        matched_f = {int(k): float(D["mfr"][r]) for (r, k, mc) in pairs}
        self.is_meas = np.array([int(k) in matched_f for k in self.inb])
        self.meas_f = np.array([matched_f.get(int(k), self.fnom[j]) for j, k in enumerate(self.inb)])
        self.nM = len(self.inb)

    def g_axis(self, Q, axis):
        return self.Utray[axis] @ Q[:, self.inb]     # (nM,) uniform-mass tray participation on this axis

    def drive_part(self, Q, drive_xyz, drive_axis):
        """(nM,) modal participation of the DRIVE point (per-drive net-CG force = phi_drive * g_tray / D)."""
        if drive_axis == "XY":                       # combined-corner drive: sum X and Y drive rows
            rx, _, _ = self.R.reduced_row(drive_xyz, "X"); ry, _, _ = self.R.reduced_row(drive_xyz, "Y")
            row = rx + ry
        else:
            row, _, _ = self.R.reduced_row(drive_xyz, drive_axis)
        return row @ Q[:, self.inb]

    def spectrum_drive(self, theta, axis, drive_xyz, drive_axis, amp=None, fscale=None):
        """PER-DRIVE net-CG force |G_d|(FGRID): includes the drive-point modal participation phi_drive,i."""
        f, Q = self.modes(theta)
        fi = f[self.inb].copy()
        if fscale is not None:
            fi = fi * fscale
        g = self.g_axis(Q, axis) * self.drive_part(Q, drive_xyz, drive_axis)
        if amp is not None:
            g = g * amp
        wi = 2 * np.pi * fi; w = 2 * np.pi * FGRID
        D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :]
        return np.abs(((g[:, None] * wi[:, None] ** 2) / D).sum(0))

    def modes(self, theta):
        K = self.R.A_fix + np.einsum("g,gij->ij", np.asarray(theta), self.R.A)
        w2, Q = np.linalg.eigh(K)
        f = np.sqrt(np.clip(w2, 0, None)) / (2 * np.pi)
        return f, Q

    def spectrum(self, theta, axis, amp=None, fscale=None):
        """net-CG force |S_F|(FGRID) for one theta, optional per-mode amp / freq-scale (len nM)."""
        f, Q = self.modes(theta)
        fi = f[self.inb].copy()
        if fscale is not None:
            fi = fi * fscale
        g = self.g_axis(Q, axis)
        if amp is not None:
            g = g * amp
        wi = 2 * np.pi * fi; w = 2 * np.pi * FGRID
        D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :]
        G = ((g[:, None] * wi[:, None] ** 2) / D).sum(0)      # (Nf,)
        return np.abs(G)                                       # |G|; S_F = |G|^2 (ratios identical)


# ---------------- 1-octave smoothing + coverage/sharpness/point ----------------
_SMOOTH_CACHE = {}


def _smooth_matrix(fgrid, frac):
    """Row-normalized 1-octave averaging operator W: octave_smooth(y) = exp(W @ log(y))."""
    key = (id(fgrid), frac)
    W = _SMOOTH_CACHE.get(key)
    if W is None:
        n = len(fgrid); W = np.zeros((n, n))
        for k, fc in enumerate(fgrid):
            m = (fgrid >= fc * 2 ** (-frac / 2)) & (fgrid <= fc * 2 ** (frac / 2))
            W[k, m] = 1.0 / m.sum()
        _SMOOTH_CACHE[key] = W
    return W


def octave_smooth(fgrid, y, frac=1.0):
    """geometric-mean smoothing on 1-octave (frac=1) log bands (vectorized via a cached averaging matrix)."""
    W = _smooth_matrix(fgrid, frac)
    return np.exp(W @ np.log(np.asarray(y) + 1e-300))


def grms(y):
    return float(np.sqrt(np.mean(y ** 2)))


def coverage_vs_truth(lo, hi, truths, fgrid, frac=1.0):
    """Honest coverage: fraction of the epistemic TRUTH ensemble the method band [lo,hi] covers, 1-octave
    smoothed, aggregated with QOI ENERGY weighting so the QOI-driving PEAKS dominate (a miss at a low-energy
    bin is negligible; a miss at the resonance is not). Also the energy-weighted positive-dB under-coverage
    (truth above the upper band). A calibrated 95% band -> weighted coverage ~0.95 at the peaks."""
    los, his = octave_smooth(fgrid, lo, frac), octave_smooth(fgrid, hi, frac)
    Ts = np.array([octave_smooth(fgrid, t, frac) for t in truths])          # (n_truth, Nf)
    inside = (Ts >= los[None, :] * 0.999) & (Ts <= his[None, :] * 1.001)    # (n_truth, Nf)
    cov_f = inside.mean(0)                                                   # pointwise coverage per bin
    ref_energy = np.median(Ts, 0) ** 2                                      # where the QOI has energy
    w = ref_energy / (ref_energy.sum() + 1e-300)
    wcov = float(np.sum(w * cov_f))
    # under-coverage: truth above the band upper edge (positive dB), energy-weighted, ensemble-median
    over_db = np.clip(20 * np.log10((Ts + 1e-300) / (his[None, :] + 1e-300)), 0, None)
    ew_over_db = float(np.sum(w * np.median(over_db, 0)))
    # coverage AT the top-energy bins (the peaks) — the locally-sensitive number
    peak_bins = np.argsort(ref_energy)[::-1][:max(3, int(0.05 * len(fgrid)))]
    peak_cov = float(cov_f[peak_bins].mean())
    return {"weighted_coverage": round(wcov, 3), "peak_coverage": round(peak_cov, 3),
            "energy_wtd_pos_dB_exceed": round(ew_over_db, 3), "n_truth": int(len(truths))}


def truth_ensemble(model, axis, theta_map, extra_hidden=None, n=200, seed=7):
    """Epistemic net-CG truth ensemble: measured modes tier-0 (freq 1%/amp 0.35), unmeasured modes tier-2
    (freq 6%/amp 0.80). extra_hidden = measured-mode indices DEMOTED to unmeasured (the leave-modes-out truth:
    their true amplitude is now genuinely uncertain)."""
    rng = np.random.default_rng(seed)
    meas = model.is_meas.copy()
    if extra_hidden is not None:
        meas[np.asarray(extra_hidden)] = False
    sdf = np.where(meas, SD_F_M, SD_F_U); sda = np.where(meas, SD_A_M, SD_A_U)
    out = []
    for _ in range(n):
        amp = np.exp(rng.normal(0, 1, model.nM) * sda)
        fsc = 1 + rng.normal(0, 1, model.nM) * sdf
        out.append(model.spectrum(theta_map, axis, amp=amp, fscale=fsc))
    return np.array(out)


class Method:
    """Builds a net-CG force ENSEMBLE + 95% band for a formulation on a QOI axis."""
    def __init__(self, model: QOIModel, axis, theta_post, hidden_modes=None, kind="freq_discrep",
                 n_disc=40, seed=0):
        self.m = model; self.axis = axis; self.kind = kind
        self.theta = theta_post
        self.hidden = np.zeros(model.nM, bool)
        if hidden_modes is not None:
            self.hidden[hidden_modes] = True
        self.rng = np.random.default_rng(seed); self.n_disc = n_disc

    def tiers(self):
        # tier 0 measured (tight amp), tier 2 unmeasured/hidden (wide amp)
        meas = self.m.is_meas & ~self.hidden
        return np.where(meas, 0, 2)

    def _unmeasured_local_frac(self, th):
        """per-FGRID fraction of |G| energy from UNMEASURED modes (for the QOI-aware statFEM F(k) discrepancy)."""
        f, Q = self.m.modes(th); fi = f[self.m.inb]; g = self.m.g_axis(Q, self.axis)
        wi = 2 * np.pi * fi; w = 2 * np.pi * FGRID
        D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * ZETA * wi[:, None] * w[None, :]
        contrib = np.abs((g[:, None] * wi[:, None] ** 2) / D)          # (nM, Nf)
        unm = ~(self.m.is_meas & ~self.hidden)
        tot = contrib.sum(0) + 1e-300
        return contrib[unm].sum(0) / tot

    def ensemble(self):
        specs = []
        idx = np.linspace(0, len(self.theta) - 1, min(60, len(self.theta))).astype(int)
        tiers = self.tiers()
        sdf = np.where(tiers == 0, SD_F_M, SD_F_U)
        # amplitude-tier sigma depends on the formulation (how each represents shape/amplitude uncertainty):
        if self.kind == "feature_space":                # per-mode "peak f0+-X%, amp Y+-Z dB": measured amp PINNED tighter
            sda = np.where(tiers == 0, 0.20, SD_A_U)
        else:
            sda = np.where(tiers == 0, SD_A_M, SD_A_U)
        # 1-octave-correlated smoothing kernel over FGRID (for statFEM F(k))
        for s in idx:
            th = self.theta[s]
            if self.kind == "theta_only":
                specs.append(self.m.spectrum(th, self.axis))          # nominal amps/freqs; only theta moves
            elif self.kind == "statfem_fk":
                base = self.m.spectrum(th, self.axis)
                ufrac = self._unmeasured_local_frac(th)               # QOI-aware: wide where unmeasured modes drive
                marg = 0.25 + (SD_A_U - 0.25) * ufrac                 # marginal log-sd ramps to SD_A_U on drumhead
                for _ in range(self.n_disc):
                    z = self.rng.normal(0, 1, len(FGRID))
                    zc = octave_smooth(FGRID, np.exp(z), 1.0)         # frequency-CORRELATED (smooth) field
                    zc = np.log(zc); zc = (zc - zc.mean()) / (zc.std() + 1e-9)
                    specs.append(base * np.exp(marg * zc))
            elif self.kind == "hier_pooled":                          # partial pooling: shared amp scale + per-mode resid
                tau = 0.25                                            # pooled hyper-scale (shared across modes)
                sda_p = np.where(tiers == 0, 0.15, 0.55)              # shrunk per-mode residual (borrows strength)
                for _ in range(self.n_disc):
                    z0 = self.rng.normal(0, 1)
                    amp = np.exp(z0 * tau + self.rng.normal(0, 1, self.m.nM) * sda_p)
                    fsc = 1 + self.rng.normal(0, 1, self.m.nM) * sdf
                    specs.append(self.m.spectrum(th, self.axis, amp=amp, fscale=fsc))
            else:                                                     # freq_discrep (baseline honest) + feature_space
                for _ in range(self.n_disc):
                    amp = np.exp(self.rng.normal(0, 1, self.m.nM) * sda)
                    fsc = 1 + self.rng.normal(0, 1, self.m.nM) * sdf
                    specs.append(self.m.spectrum(th, self.axis, amp=amp, fscale=fsc))
        return np.array(specs)

    def band(self):
        E = self.ensemble()
        lo = np.percentile(E, 2.5, axis=0); hi = np.percentile(E, 97.5, axis=0)
        med = np.percentile(E, 50, axis=0)
        return lo, med, hi
