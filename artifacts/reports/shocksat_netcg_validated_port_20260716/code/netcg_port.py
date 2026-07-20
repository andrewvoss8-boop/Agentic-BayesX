#!/usr/bin/env python3
"""netcg_port — the REUSE layer. Injects (i) the A5b per-mode amplitude tiers and (ii) the finalist
per-mode perturbation into the DELIVERED netcg machinery WITHOUT reimplementing any of it.

Design rule of this card: the study's failure (review C5) came from REIMPLEMENTING the band machinery.
So here nothing is reimplemented. NC.Method.ensemble/band/tiers, NC.QOIModel.spectrum, NC.octave_smooth,
NC.coverage_vs_truth, NC.truth_ensemble, NC.grms, FGRID, ZETA, SD_* are all used BYTE-IDENTICALLY. We inject
through exactly TWO subclass hooks, each of which PROVABLY reduces to the parent at baseline:

  1. TieredMethod._unmeasured_local_frac  -> per-mode amplitude SDs (A5b tier update, S4)
  2. MappedQOIModel.modes / .g_axis       -> per-mode (delta_f, a) finalist perturbation (S3)

--- Hook 1: how a per-mode SD_A vector enters netcg's statFEM F(k) WITHOUT touching ensemble() ------------
netcg's statfem_fk marginal (netcg_qoi.py Method.ensemble) is

    marg(f) = 0.25 + (SD_A_U - 0.25) * ufrac(f),      ufrac(f) = UNMEASURED-mode energy fraction at f

which is ALGEBRAICALLY the contribution-weighted form

    marg(f) = 0.25 + SUM_i (sda_i - 0.25) * w_i(f),   w_i = contrib_i(f)/SUM_i contrib_i(f)

for the netcg tier vector  sda_i = 0.25 (measured) / SD_A_U=0.80 (unmeasured).  [Check: measured modes
contribute (0.25-0.25)*w_i = 0; unmeasured contribute (0.80-0.25)*w_i; dividing by (SD_A_U-0.25) recovers
ufrac exactly.]  So a GENERAL per-mode sda vector can be injected by returning an EFFECTIVE ufrac

    ufrac_eff(f) = SUM_i (sda_i - 0.25) * w_i(f) / (SD_A_U - 0.25)

from the single method netcg already calls. ensemble() then computes marg = 0.25 + (SD_A_U-0.25)*ufrac_eff
= the generalized marginal, with its own code path untouched. With the netcg tier vector, ufrac_eff == ufrac
BITWISE-EQUIVALENTLY -> the baseline reproduces N0 exactly. `assert_reduces_to_netcg()` PROVES this
numerically at runtime (np.allclose vs the parent method) and is called by every consumer script.

NOTE ON THE STUDY'S DIVERGENCE (suspect 2, D3/N0 diagnostic): the study's netcg_wide.py used
`marg = max(0.25, wfrac)` with `wfrac = SUM_i sda_i*w_i` and sda_i=SD_A_M=0.35 for measured. That is a
DIFFERENT functional form (it drops the 0.25 baseline-offset structure) and a different measured tier. We
use netcg's form. We do not "fix" netcg to match the study; the delivered twin is the reference.

--- Hook 2: the finalist mapping (contract quantity_contracts.md Part C) ---------------------------------
MappedQOIModel overrides modes() (scale in-band f by delta_f) and g_axis() (scale tray participation by a).
Because netcg's spectrum(), _unmeasured_local_frac() and drive_part() all route through those two, the
perturbation is applied CONSISTENTLY everywhere with no other edit. netcg fixes `inb` at nominal theta, so
scaling f[inb] is consistent with how netcg already indexes modes. delta_f == 1, a == 1 -> the parent
exactly (baseline-through-mapping = identity BY CONSTRUCTION; stated as a limitation, not sold as a test).
"""
from __future__ import annotations
import sys
from pathlib import Path

import numpy as np

WS = Path(__file__).resolve().parent.parent
REPORTS = WS.parent
NETCG = REPORTS / "shocksat_netcg_method_selection_20260701"
STUDY = REPORTS / "shocksat_full_spectrum_frf_20260714"
TWIN = REPORTS / "shocksat_psd_envelope_twin_20260623"
for p in (TWIN / "code", NETCG / "code"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import netcg_qoi as NC  # noqa: E402   READ-ONLY reuse

FEM6DB = 10 ** (6 / 20)
MARG_FLOOR = 0.25            # netcg's statfem_fk marginal floor (netcg_qoi.py Method.ensemble)
# DEV drives ONLY — the 5th (+XY corner) drive is the VAULT and is deliberately absent from this list.
DEV_DRIVE_KEYS = ["m_xpos_990x", "m_zpos_990z", "m_ypos_990y", "m_zpos_900z"]


# =========================================================== Hook 1: per-mode amplitude tiers (A5b / S4)
class TieredMethod(NC.Method):
    """NC.Method with a per-mode amplitude-SD vector injected through the effective-ufrac identity above.

    sda_vec: (nM,) per-mode amplitude log-SD. If None -> exactly the netcg tiers (identity).
    Everything else (ensemble, band, tiers, seeds, MC budget) is INHERITED UNCHANGED from netcg.
    """

    def __init__(self, *a, sda_vec=None, **kw):
        super().__init__(*a, **kw)
        self.sda_vec = None if sda_vec is None else np.asarray(sda_vec, float)

    def netcg_sda(self):
        """The netcg tier vector that reproduces the delivered band: 0.25 measured / SD_A_U unmeasured."""
        meas = self.m.is_meas & ~self.hidden
        return np.where(meas, MARG_FLOOR, NC.SD_A_U).astype(float)

    def _unmeasured_local_frac(self, th):
        if self.sda_vec is None:
            return super()._unmeasured_local_frac(th)      # untouched netcg path
        f, Q = self.m.modes(th)
        fi = f[self.m.inb]
        g = self.m.g_axis(Q, self.axis)
        wi = 2 * np.pi * fi
        w = 2 * np.pi * NC.FGRID
        D = wi[:, None] ** 2 - w[None, :] ** 2 + 2j * NC.ZETA * wi[:, None] * w[None, :]
        contrib = np.abs((g[:, None] * wi[:, None] ** 2) / D)          # (nM, Nf) — netcg's own weighting
        wgt = contrib / (contrib.sum(0) + 1e-300)
        sda = self.sda_vec.copy()
        sda[self.hidden] = NC.SD_A_U        # hidden modes revert to the wide unmeasured tier (audit path)
        return ((sda[:, None] - MARG_FLOOR) * wgt).sum(0) / (NC.SD_A_U - MARG_FLOOR)


def assert_reduces_to_netcg(model, theta_post, axis=0, atol=1e-12):
    """PROVE hook 1 is a strict generalization: with the netcg tier vector it equals the parent, bitwise-close.
    Called by every consumer script before any A5b number is produced."""
    th = np.median(theta_post, axis=0)
    parent = NC.Method(model, axis, theta_post, kind="statfem_fk", seed=0)
    base = parent._unmeasured_local_frac(th)
    child = TieredMethod(model, axis, theta_post, kind="statfem_fk", seed=0)
    child.sda_vec = child.netcg_sda()
    got = child._unmeasured_local_frac(th)
    err = float(np.max(np.abs(got - base)))
    assert err <= atol, f"TieredMethod does NOT reduce to netcg (max |dufrac| = {err:.3e})"
    return err


# =========================================================== Hook 2: finalist per-mode perturbation (S3)
class MappedQOIModel(NC.QOIModel):
    """netcg QOIModel with per-in-band-mode (delta_f, a_axis) applied. Built by copying an existing model's
    state (no re-load, no re-match) so the reduced model, tray selector, .ash matching and is_meas are the
    DELIVERED ones, bit-for-bit."""

    @classmethod
    def from_base(cls, base: NC.QOIModel, dfreq=None, amp_by_axis=None):
        o = object.__new__(cls)
        o.__dict__.update(base.__dict__)          # same reduced model / tray / is_meas / inb / fnom
        o.dfreq = np.ones(base.nM) if dfreq is None else np.asarray(dfreq, float)
        o.amp_by_axis = {} if amp_by_axis is None else {int(k): np.asarray(v, float)
                                                        for k, v in amp_by_axis.items()}
        return o

    def modes(self, theta):
        f, Q = super().modes(theta)
        f = np.asarray(f).copy()
        f[self.inb] = f[self.inb] * self.dfreq          # per-mode frequency scale (delta_f)
        return f, Q

    def g_axis(self, Q, axis):
        g = super().g_axis(Q, axis)
        a = self.amp_by_axis.get(int(axis))
        return g if a is None else g * a                # per-mode participation scale (a)

    def is_identity(self, tol=1e-3):
        moved_f = float(np.max(np.abs(self.dfreq - 1.0)))
        moved_a = max([float(np.max(np.abs(np.log(np.clip(v, 1e-12, None)))))
                       for v in self.amp_by_axis.values()] or [0.0])
        return (moved_f <= tol and moved_a <= tol), moved_f, moved_a


# =========================================================== shared scoring (netcg conventions, verbatim)
def band_ratio(lo, hi, ref_grms):
    """VERBATIM netcg bakeoff.py:54-55 — the DELIVERED width convention (contract Part B1)."""
    return round(NC.grms(hi - lo) / (ref_grms + 1e-300), 3)


def fem6_ref_grms(model, theta_point, axis):
    nom = model.spectrum(theta_point, axis)
    return NC.grms(nom * FEM6DB - nom / FEM6DB)


def score_band(model, theta_post, axis, theta_point, truths, sda_vec=None, hidden=None):
    """statfem_Fk width ratio + coverage under the netcg conventions. sda_vec=None -> the delivered band."""
    ref = fem6_ref_grms(model, theta_point, axis)
    meth = TieredMethod(model, axis, theta_post, kind="statfem_fk", seed=0,
                        hidden_modes=hidden, sda_vec=sda_vec)
    lo, med, hi = meth.band()
    cov = NC.coverage_vs_truth(lo, hi, truths, NC.FGRID)
    return {"width_ratio_vs_fem6db": band_ratio(lo, hi, ref),
            "weighted_coverage": cov["weighted_coverage"],
            "peak_coverage": cov["peak_coverage"],
            "energy_wtd_pos_dB_exceed": cov["energy_wtd_pos_dB_exceed"],
            "_band_grms": float(NC.grms(hi - lo)), "_lo": lo, "_med": med, "_hi": hi}


def top3_measured_driving(model, theta_point, axis):
    """The overconfidence audit's hidden set — VERBATIM logic from netcg bakeoff.py:102-104."""
    f, Q = model.modes(theta_point)
    gg = model.g_axis(Q, axis)
    meas_idx = np.where(model.is_meas)[0]
    return meas_idx[np.argsort(np.abs(gg[meas_idx]))[::-1][:3]]
