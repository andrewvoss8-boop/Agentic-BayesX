#!/usr/bin/env python3
"""n0_reference — GATE N0 (card B §2): reproduce the DELIVERED net-CG twin band widths by driving the
ORIGINAL netcg machinery, its reduced model, and the L5 theta posterior exactly as the netcg run did.

Targets (netcg out/bakeoff_scorecard.json, statfem_Fk = the delivered conservative winner):
    shear_X 1.508 | shear_Y 2.301 | normal_Z 2.526     tolerance +-0.05 each.

REUSED BYTE-IDENTICALLY (nothing here reimplements the QOI):
  - netcg_qoi.QOIModel / Method / truth_ensemble / coverage_vs_truth / octave_smooth / grms / FGRID / ZETA
  - the netcg reduced model via realfrf.load_reduced() (psd_envelope_twin thread)
  - the L5 NUTS theta posterior, REUSED from netcg out/theta_post_L5.npz (no sampler runs here)
  - the width convention band_ratio() replicated from bakeoff.py:54-55 (3 lines, quoted below) because
    bakeoff.py is a __main__ script whose main() rewrites the netcg thread's out/ — importing it would
    WRITE into a read-only workspace. The formula is copied verbatim, not re-derived.

Also emits the N0 DIAGNOSTIC (D3): a quantitative diff of the study's netcg_wide.py conventions against the
netcg ones, computed on the SAME band, to locate the C5 non-reproduction. No constants are "fixed" anywhere.

Writes out/n0_reference.json. Read-only w.r.t. every other workspace.
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

import numpy as np

WS = Path(__file__).resolve().parent.parent
REPORTS = WS.parent
NETCG = REPORTS / "shocksat_netcg_method_selection_20260701"
TWIN = REPORTS / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(TWIN / "code"))
sys.path.insert(0, str(NETCG / "code"))
import netcg_qoi as NC  # noqa: E402   (READ-ONLY reuse of the delivered machinery)

TARGETS = {"shear_X": 1.508, "shear_Y": 2.301, "normal_Z": 2.526}
TOL = 0.05
AXES = [(0, "shear_X"), (1, "shear_Y"), (2, "normal_Z")]
FEM6DB = 10 ** (6 / 20)          # bakeoff.py:30 — FEM+6 dB incumbent multiplier


def band_ratio(band_lo, band_hi, ref_band_grms):
    """VERBATIM from netcg bakeoff.py:54-55 (the delivered width convention; contract Part B1)."""
    return round(NC.grms(band_hi - band_lo) / (ref_band_grms + 1e-300), 3)


def load_theta():
    """REUSED L5 NUTS draws — no sampler is run in this card (card 5)."""
    z = np.load(NETCG / "out" / "theta_post_L5.npz", allow_pickle=True)
    return z["theta_post"], json.loads(str(z["diag"]))


def main():
    t0 = time.time()
    model = NC.QOIModel()
    theta_post, diag = load_theta()
    theta_map = np.median(theta_post, axis=0)      # bakeoff.py:61 — posterior MEDIAN
    print(f"reduced model: nM={model.nM} in-band modes {model.fnom.min():.1f}-{model.fnom.max():.1f} Hz, "
          f"{int(model.is_meas.sum())} measured")
    print(f"L5 posterior (REUSED): {theta_post.shape} draws, converged={diag.get('converged')} "
          f"max_rhat={diag.get('max_rhat')} min_ess={diag.get('min_ess')} div={diag.get('divergences')}")

    rep, detail = {}, {}
    for axis, name in AXES:
        nom = model.spectrum(theta_map, axis)
        fem6_lo, fem6_hi = nom / FEM6DB, nom * FEM6DB
        fem6_grms = NC.grms(fem6_hi - fem6_lo)
        truths = NC.truth_ensemble(model, axis, theta_map, n=200)          # bakeoff.py:78 (seed=7 default)
        meth = NC.Method(model, axis, theta_post, kind="statfem_fk", seed=0)   # the DELIVERED method
        lo, med, hi = meth.band()
        cov = NC.coverage_vs_truth(lo, hi, truths, NC.FGRID)
        r = band_ratio(lo, hi, fem6_grms)
        rep[name] = r
        detail[name] = {"width_ratio_vs_fem6db": r, "target": TARGETS[name],
                        "abs_err": round(abs(r - TARGETS[name]), 4),
                        "weighted_coverage": cov["weighted_coverage"],
                        "peak_coverage": cov["peak_coverage"],
                        "energy_wtd_pos_dB_exceed": cov["energy_wtd_pos_dB_exceed"],
                        "band_grms_width": round(float(NC.grms(hi - lo)), 6),
                        "fem6db_grms_width": round(float(fem6_grms), 6)}
        print(f"[{name}] statfem_Fk width {r:.3f}x vs target {TARGETS[name]} "
              f"(|err| {detail[name]['abs_err']:.4f})  cov {cov['weighted_coverage']:.3f}")

    max_err = max(d["abs_err"] for d in detail.values())
    passed = bool(max_err <= TOL)

    # ---------------- N0 DIAGNOSTIC (D3): why the study's reimplementation did not reproduce -------------
    # Computed on the SAME shear_X band so the conventions are compared like-for-like. This LOCATES the
    # divergence; it does not change any constant.
    axis = 0
    nom = model.spectrum(theta_map, axis)
    fem6_grms = NC.grms(nom * FEM6DB - nom / FEM6DB)
    lo, med, hi = NC.Method(model, axis, theta_post, kind="statfem_fk", seed=0).band()
    netcg_conv = NC.grms(hi - lo) / fem6_grms                                   # bakeoff.py convention
    study_conv = (NC.grms(NC.octave_smooth(NC.FGRID, hi))
                  / NC.grms(NC.octave_smooth(NC.FGRID, lo)))                    # netcg_wide.py:159 convention
    diagnostic = {
        "purpose": "locate the C5 non-reproduction (pre-registered in decisions_log D3 BEFORE this ran)",
        "suspect_1_width_convention": {
            "netcg_bakeoff.band_ratio": "grms(hi-lo)/grms(fem6_hi-fem6_lo)  [normalized WIDTH vs FEM+6dB]",
            "study_netcg_wide.band_width_ratio": "grms(smooth(hi))/grms(smooth(lo))  [upper/lower ENVELOPE "
                                                 "ratio; never references FEM+6dB]",
            "same_band_netcg_convention": round(float(netcg_conv), 3),
            "same_band_study_convention": round(float(study_conv), 3),
            "note": "BOTH computed here from the SAME lo/hi arrays of the SAME delivered statfem_Fk band. "
                    "They are different quantities, so they cannot agree at any calibration."},
        "suspect_2_statfem_marginal": {
            "netcg": "marg = 0.25 + (SD_A_U-0.25)*ufrac ; ufrac = UNMEASURED-mode energy fraction "
                     "(netcg_qoi.py Method.ensemble/statfem_fk)",
            "study": "marg = max(0.25, wfrac) ; wfrac = contribution-weighted MEAN SD_A over ALL modes "
                     "(netcg_wide.py:143-147)",
            "note": "different functional form -> different width even under the same width convention."},
        "suspect_3_theta_ensemble": {
            "netcg": "60 theta draws x n_disc=40 = 2400 spectra (theta uncertainty INSIDE the band)",
            "study": "single theta (theta_MAP_wide) x 400 draws (theta uncertainty ABSENT from the band)",
            "note": "study bands carry no theta spread; see N1 for the theta-point contribution."},
    }

    out = {
        "gate": "N0 — reference reproduction (card B 2, pre-registered)",
        "status": "PASS" if passed else "FAIL",
        "targets": TARGETS, "tolerance": TOL,
        "reproduced": rep, "max_abs_err": round(float(max_err), 4),
        "detail": detail,
        "method": "statfem_Fk (the DELIVERED conservative assumption-light winner)",
        "theta_source": "REUSED L5 NUTS draws from netcg out/theta_post_L5.npz (no sampler run in this card)",
        "theta_diag_inherited": diag,
        "reused_readonly": ["netcg_qoi.py (QOIModel/Method/truth_ensemble/coverage_vs_truth/grms/FGRID)",
                            "realfrf.load_reduced() [psd_envelope_twin]",
                            "theta_post_L5.npz", "bakeoff.py:54-55 band_ratio formula (copied verbatim)"],
        "diagnostic_C5": diagnostic,
        "active_s": round(time.time() - t0, 1),
    }
    (WS / "out").mkdir(exist_ok=True)
    (WS / "out" / "n0_reference.json").write_text(json.dumps(out, indent=2))
    print(f"\nGATE N0: {out['status']}  (max |err| {max_err:.4f} vs tol {TOL})")
    print(f"DIAGNOSTIC same-band: netcg convention {netcg_conv:.3f} vs study convention {study_conv:.3f}")
    print("wrote out/n0_reference.json")
    return passed


if __name__ == "__main__":
    main()
