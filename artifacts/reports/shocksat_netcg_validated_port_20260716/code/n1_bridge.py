#!/usr/bin/env python3
"""n1_bridge — BRIDGE GATE N1 (card B 3.1): drive the netcg machinery on the INHERITED model at the
full-spectrum study's theta_MAP_wide instead of the L5 posterior median, to separate how much of any width
change is the THETA POINT vs the MODEL / implementation. Diagnostic — no threshold (card).

Decomposition (all three use the SAME reused netcg machinery + the SAME MC budget of 60 theta slots x 40
discrepancy draws = 2400 spectra, so nothing here is an MC-noise artifact):

  A  L5 posterior, full spread      = the N0 / DELIVERED band            [theta spread + L5 theta point]
  B  L5 posterior MEDIAN as a point = A minus the theta spread            -> isolates the THETA SPREAD term
  C  study theta_MAP_wide as a point= B with the theta point swapped      -> isolates the THETA POINT term

  (A -> B) = what the theta posterior spread contributes to the delivered width.
  (B -> C) = what moving to the study's theta point does, model and machinery held fixed.
  whatever the study's published widths differ by BEYOND (B->C) is NOT the theta point: it is the model
  reduction / the reimplemented statFEM F(k) / the width convention (see N0 diagnostic).

Group-ordering bridge VALIDATED before use: realfrf.GNAMES == theta_map_wide.json free_names ==
['al_welds','angle_brackets','bottom_box','contact','cross_beam','joints','plates','steel_welds','top_box']
-> theta_MAP_wide's 9-vector maps 1:1 onto the netcg reduced model's 9 stiffness groups. Asserted at runtime.

Point-theta is passed as the SAME point repeated 60x so NC.Method's internal
`idx = linspace(0, len(theta)-1, min(60, len(theta)))` draws the same 60 slots as the posterior case —
identical MC budget, identical seeds. REUSED theta draws; no sampler.

Writes out/n1_bridge.json.
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
STUDY = REPORTS / "shocksat_full_spectrum_frf_20260714"
TWIN = REPORTS / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(TWIN / "code"))
sys.path.insert(0, str(NETCG / "code"))
import realfrf as rf   # noqa: E402
import netcg_qoi as NC  # noqa: E402

AXES = [(0, "shear_X"), (1, "shear_Y"), (2, "normal_Z")]
FEM6DB = 10 ** (6 / 20)
STUDY_PUBLISHED = {"shear_X": 8.225, "shear_Y": 3.660, "normal_Z": 5.117}   # study out/netcg_results.json


def band_ratio(lo, hi, ref):        # VERBATIM netcg bakeoff.py:54-55
    return round(NC.grms(hi - lo) / (ref + 1e-300), 3)


def widths(model, theta_arr, theta_point_for_nom):
    """statfem_Fk width ratio + coverage per axis, netcg conventions, fixed MC budget."""
    out = {}
    for axis, name in AXES:
        nom = model.spectrum(theta_point_for_nom, axis)
        fem6_grms = NC.grms(nom * FEM6DB - nom / FEM6DB)
        truths = NC.truth_ensemble(model, axis, theta_point_for_nom, n=200)
        lo, med, hi = NC.Method(model, axis, theta_arr, kind="statfem_fk", seed=0).band()
        cov = NC.coverage_vs_truth(lo, hi, truths, NC.FGRID)
        out[name] = {"width_ratio_vs_fem6db": band_ratio(lo, hi, fem6_grms),
                     "weighted_coverage": cov["weighted_coverage"],
                     "peak_coverage": cov["peak_coverage"]}
    return out


def main():
    t0 = time.time()
    model = NC.QOIModel()
    z = np.load(NETCG / "out" / "theta_post_L5.npz", allow_pickle=True)
    theta_post = z["theta_post"]
    theta_med = np.median(theta_post, axis=0)

    tm = json.load(open(STUDY / "out" / "theta_map_wide.json"))
    assert list(tm["free_names"]) == list(rf.GNAMES), "GROUP ORDER MISMATCH — bridge invalid"
    theta_wide = np.asarray(tm["theta_map_vec"], float)
    print("group-order bridge OK:", list(rf.GNAMES))

    rep60 = lambda th: np.repeat(np.asarray(th, float)[None, :], 60, axis=0)   # same MC budget as A

    A = widths(model, theta_post, theta_med)                 # = N0 / delivered
    B = widths(model, rep60(theta_med), theta_med)           # L5 median as a POINT
    C = widths(model, rep60(theta_wide), theta_wide)         # study theta_MAP_wide as a POINT

    # theta point difference itself
    dtheta = {n: {"L5_median": round(float(theta_med[i]), 4), "study_theta_MAP_wide": round(float(theta_wide[i]), 4),
                  "ratio": round(float(theta_wide[i] / theta_med[i]), 4)}
              for i, n in enumerate(rf.GNAMES)}
    # in-band mode shift caused by the theta point swap
    f_med, _ = model.modes(theta_med)
    f_wide, _ = model.modes(theta_wide)
    fm_i, fw_i = f_med[model.inb], f_wide[model.inb]
    fshift = fw_i / fm_i

    decomp = {}
    for _, name in AXES:
        a, b, c = A[name]["width_ratio_vs_fem6db"], B[name]["width_ratio_vs_fem6db"], C[name]["width_ratio_vs_fem6db"]
        decomp[name] = {
            "A_L5_posterior_delivered": a,
            "B_L5_median_point": b,
            "C_study_thetaMAPwide_point": c,
            "theta_SPREAD_term_A_minus_B": round(a - b, 3),
            "theta_POINT_term_C_minus_B": round(c - b, 3),
            "study_published_width": STUDY_PUBLISHED[name],
            "residual_NOT_explained_by_theta": round(STUDY_PUBLISHED[name] - c, 3),
            "pct_of_study_gap_explained_by_theta_point": round(
                100.0 * (c - a) / (STUDY_PUBLISHED[name] - a + 1e-300), 1),
        }
        print(f"[{name}] A(delivered)={a}  B(L5 median pt)={b}  C(study theta pt)={c}  "
              f"| study published={STUDY_PUBLISHED[name]}  residual={decomp[name]['residual_NOT_explained_by_theta']}")

    out = {
        "gate": "N1 — bridge (card B 3.1): theta POINT vs MODEL. DIAGNOSTIC, no pass/fail threshold.",
        "theta_source": "REUSED L5 NUTS draws (netcg out/theta_post_L5.npz); study theta_MAP_wide read "
                        "read-only from full_spectrum_frf_20260714/out/theta_map_wide.json. No sampler run.",
        "group_order_bridge": {"validated": True, "names": list(rf.GNAMES),
                               "note": "realfrf.GNAMES == theta_map_wide free_names, asserted at runtime"},
        "mc_budget": "60 theta slots x 40 discrepancy draws = 2400 spectra for every case (A, B, C)",
        "cases": {"A_L5_posterior_delivered": A, "B_L5_median_point": B, "C_study_thetaMAPwide_point": C},
        "decomposition": decomp,
        "theta_points": dtheta,
        "inband_mode_shift_from_theta_swap": {
            "min": round(float(fshift.min()), 4), "max": round(float(fshift.max()), 4),
            "median": round(float(np.median(fshift)), 4),
            "note": "f(theta_MAP_wide)/f(L5 median) over the 40 in-band netcg modes"},
        "active_s": round(time.time() - t0, 1),
    }
    (WS / "out" / "n1_bridge.json").write_text(json.dumps(out, indent=2))
    print("\nwrote out/n1_bridge.json")


if __name__ == "__main__":
    main()
