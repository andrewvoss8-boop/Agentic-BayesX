#!/usr/bin/env python3
"""Stage 2 bake-off (NUTS): net-CG force method selection on the INHERITED reduced model.

Formulations (per QOI axis: shear_X, shear_Y, normal_Z):
  baseline_fem  = theta=1 nominal + the FEM+6dB incumbent band (the bar).
  L5_theta_only = L5 modal-frequency NUTS posterior over theta, propagated with NOMINAL per-mode amps (SHARP).
  L5_freq_discrep = same theta posterior + per-mode tier discrepancy (measured tight amp / unmeasured wide amp).
Scores: sharpness (95%-band GRMS-force ratio vs FEM+6dB), coverage of the best measured-reconstruction (1-oct),
        leave_modes_out (hide top-K measured QOI modes -> does the band widen to cover plausible truths?).
Selection rule: coverage + leave_modes_out = HARD GATE (overconfidence disqualifies); then sharpest.

Reuses modal_feature.calibrate_modal (proven-converged L5 NUTS, all-variable gate). Writes out/bakeoff_scorecard.json,
out/leave_modes_out.json. Deterministic seeds. Run: python3 bakeoff.py
"""
from __future__ import annotations
import sys, json, time
from pathlib import Path
import numpy as np

WS = Path(__file__).resolve().parent.parent
BASE = WS.parent / "shocksat_psd_envelope_twin_20260623"
sys.path.insert(0, str(BASE / "code"))
sys.path.insert(0, str(WS / "code"))
import realfrf as rf
import modal_feature as MF
import netcg_qoi as NC

OUT = WS / "out"; OUT.mkdir(exist_ok=True)
AXES = [(0, "shear_X"), (1, "shear_Y"), (2, "normal_Z")]
FEM6DB = 10 ** (6 / 20)          # FEM+6 dB incumbent multiplier on the nominal band
# Axis-A formulations (all reuse the SAME converged L5 theta posterior; they differ in the QOI UNCERTAINTY rep):
METHODS = [("theta_only", "L5_theta_only"), ("freq_discrep", "L5_freq_discrep"),
           ("feature_space", "feature_space"), ("statfem_fk", "statfem_Fk"), ("hier_pooled", "hier_pooled")]


def get_theta_posterior():
    cache = OUT / "theta_post_L5.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        return z["theta_post"], json.loads(str(z["diag"])), (z["obs_idx"], z["obs_w"])
    R = rf.load_reduced()
    meas = rf.reprocess_measured(list(range(1, rf.N_ACCEL_RECORDERS + 1)))
    ch = rf.build_channels(R, meas["daq"])
    meas_f, support = MF.extract_measured_modes(meas, ch)
    pairs, _ = MF.match(R, meas_f)
    idx = np.array([p[0] for p in pairs]); wmeas = np.array([p[1] for p in pairs])
    t0 = time.time()
    theta_post, sigma_w2, diag = MF.calibrate_modal(R, idx, wmeas, warmup=1000, samples=1000, chains=4)
    diag["runtime_s"] = round(time.time() - t0, 1)
    np.savez(cache, theta_post=theta_post, diag=json.dumps(diag), obs_idx=idx, obs_w=wmeas)
    return theta_post, diag, (idx, wmeas)


def band_ratio(band_lo, band_hi, ref_band_grms):
    return round(NC.grms(band_hi - band_lo) / (ref_band_grms + 1e-300), 3)


def main():
    model = NC.QOIModel()
    theta_post, diag, (obs_idx, obs_w) = get_theta_posterior()
    theta_map = np.median(theta_post, axis=0)
    print(f"L5 NUTS: converged={diag['converged']} R-hat={diag['max_rhat']:.3f} ESS={diag['min_ess']:.0f} "
          f"div={diag['divergences']} ({diag['runtime_s']}s)")

    scorecard = {"sampler": "NUTS (L5 modal-frequency, Kiran Eq25)", "convergence": diag,
                 "n_configs_compared": 0, "qois": {}}
    lmo_out = {"design": "hide top-K measured QOI-driving modes; band must widen to cover plausible truths "
                         "(hidden-mode amplitudes ~ LogNormal(0,SD_A_U)). PASS=covers, FAIL=falsely narrow.",
               "K_hidden": 3, "qois": {}}
    n_cfg = 0

    COV_GATE, EXCEED_GATE = 0.90, 1.0    # weighted coverage >=0.90 and energy-wtd +dB under-coverage <=1.0 dB
    for axis, name in AXES:
        nom = model.spectrum(theta_map, axis)
        fem6_lo, fem6_hi = nom / FEM6DB, nom * FEM6DB
        fem6_grms = NC.grms(fem6_hi - fem6_lo)
        # honest epistemic truth ensemble (measured tight / unmeasured wide) -> the coverage answer key
        truths = NC.truth_ensemble(model, axis, theta_map, n=200)

        qcard = {}
        for kind, label in METHODS:
            meth = NC.Method(model, axis, theta_post, kind=kind, seed=0)
            lo, med, hi = meth.band()
            cov = NC.coverage_vs_truth(lo, hi, truths, NC.FGRID)
            covers = cov["weighted_coverage"] >= COV_GATE and cov["energy_wtd_pos_dB_exceed"] <= EXCEED_GATE
            qcard[label] = {
                "sharpness_band_grms_ratio_vs_fem6db": band_ratio(lo, hi, fem6_grms),
                "weighted_coverage": cov["weighted_coverage"], "peak_coverage": cov["peak_coverage"],
                "energy_wtd_pos_dB_exceed": cov["energy_wtd_pos_dB_exceed"],
                "covers_hard_gate": bool(covers)}
            n_cfg += 1
        # baseline incumbent (FEM+6dB) coverage of the same truth ensemble
        cov6 = NC.coverage_vs_truth(fem6_lo, fem6_hi, truths, NC.FGRID)
        qcard["baseline_fem+6dB"] = {"sharpness_band_grms_ratio_vs_fem6db": 1.0,
                                     "weighted_coverage": cov6["weighted_coverage"],
                                     "peak_coverage": cov6["peak_coverage"],
                                     "energy_wtd_pos_dB_exceed": cov6["energy_wtd_pos_dB_exceed"]}
        n_cfg += 1
        scorecard["qois"][name] = qcard

        # --- leave-modes-out: demote top-K measured QOI-driving modes in the TRUTH (their true amp now uncertain)
        f, Q = model.modes(theta_map); gg = model.g_axis(Q, axis)
        meas_idx = np.where(model.is_meas)[0]
        topK = meas_idx[np.argsort(np.abs(gg[meas_idx]))[::-1][:lmo_out["K_hidden"]]]
        # participation fraction the hidden (measured) modes carry -> how DISCRIMINATING the test is for this QOI
        part = np.abs(gg) / (np.abs(gg).sum() + 1e-30)
        hidden_part = float(part[topK].sum())
        truths_lmo = NC.truth_ensemble(model, axis, theta_map, extra_hidden=topK, n=200, seed=11)
        lmo_qcard = {"hidden_modes_hz": [round(float(model.fnom[i]), 1) for i in topK],
                     "hidden_modes_participation_frac": round(hidden_part, 3),
                     "test_discriminating": bool(hidden_part >= 0.10)}
        for kind, label in METHODS:
            # the method also loses those modes as measured -> hidden_modes in the Method tiers
            m_hide = NC.Method(model, axis, theta_post, hidden_modes=topK, kind=kind, seed=2)
            lo, med, hi = m_hide.band()
            cov = NC.coverage_vs_truth(lo, hi, truths_lmo, NC.FGRID)
            m_no = NC.Method(model, axis, theta_post, kind=kind, seed=2)
            lo0, _, hi0 = m_no.band()
            w0, w1 = NC.grms(hi0 - lo0), NC.grms(hi - lo)
            widen = w1 / (w0 + 1e-30)
            # §5: a humble method's band RESPONDS (widens) when measured modes are hidden. theta_only is EXACTLY
            # 1.000 by construction (it ignores amplitude tiers -> uncertainty invariant to information = the
            # overconfidence signature); any amplitude/shape-carrying method exceeds 1.0. Threshold 1.03 just
            # separates "responds" from that structural-1.0 / numerical noise (NOT a tuned decision boundary).
            verdict = ("PASS_humble" if (widen >= 1.03 and cov["weighted_coverage"] >= 0.85)
                       else "FAIL_overconfident")
            lmo_qcard[label] = {"peak_coverage_after_hiding": cov["peak_coverage"],
                                "weighted_coverage_after_hiding": cov["weighted_coverage"],
                                "band_grms_before": round(w0, 4), "band_grms_after": round(w1, 4),
                                "widen_ratio": round(widen, 2), "verdict": verdict}
        lmo_out["qois"][name] = lmo_qcard
        print(f"[{name}] " + " | ".join(
            f"{label.split('_',1)[-1] if label.startswith('L5') else label}: "
            f"{qcard[label]['sharpness_band_grms_ratio_vs_fem6db']}x cov{qcard[label]['weighted_coverage']} "
            f"{lmo_qcard[label]['verdict'][:4]}" for _, label in METHODS))

    scorecard["n_configs_compared"] = n_cfg
    # METHOD-LEVEL humility: overconfidence is a method property, demonstrated on the QOIs where the leave-modes-out
    # test is DISCRIMINATING (hidden modes carry real participation = the shear band). A method that never widens
    # there is overconfident everywhere (incl. the already-unmeasured normal QOI, which cannot be tested directly).
    method_humble = {}
    for _, label in METHODS:
        tested = [lmo_out["qois"][name][label]["verdict"] for axis, name in AXES
                  if lmo_out["qois"][name]["test_discriminating"]]
        method_humble[label] = bool(tested) and all(v == "PASS_humble" for v in tested)
    scorecard["method_humility"] = {"humble": method_humble,
        "basis": "leave-modes-out widening on QOIs where hidden measured modes carry >=10% participation (shear); "
                 "overconfidence is a method property that also disqualifies it on the untestable normal QOI"}

    # two-part selection rule per QOI: coverage (hard gate) + method not overconfident, then sharpest (best of N)
    selection = {}
    for axis, name in AXES:
        q = scorecard["qois"][name]
        winners = []
        for _, label in METHODS:
            if q[label]["covers_hard_gate"] and method_humble[label]:
                winners.append((label, q[label]["sharpness_band_grms_ratio_vs_fem6db"]))
        winner = min(winners, key=lambda x: x[1])[0] if winners else "none_pass_hard_gate"
        # HONESTY: for a low-shape-trust QOI (unmeasured-driven), a sharper winner whose sharpness comes from a
        # POOLING assumption over UNMEASURED modes is assumption-dependent (unverifiable w/o the >200 Hz test).
        # Report the assumption-light CONSERVATIVE winner too (sharpest covering method that does NOT pool
        # unmeasured amplitudes -> excludes hier_pooled).
        shape_trust = {"shear_X": 96, "shear_Y": 94, "normal_Z": 45}[name]
        cons = [w for w in winners if w[0] != "hier_pooled"]
        conservative = min(cons, key=lambda x: x[1])[0] if cons else winner
        caveat = None
        if winner == "hier_pooled" and shape_trust < 60:
            caveat = ("sharpest winner rests on a POOLING (shared-amplitude-scale) assumption over UNMEASURED "
                      "drumhead modes = unverifiable without the >200 Hz plate test; the assumption-light "
                      f"conservative choice is {conservative} at "
                      f"{q[conservative]['sharpness_band_grms_ratio_vs_fem6db']}x.")
        selection[name] = {"winner": winner, "n_compared": len(METHODS) + 1,
                           "candidates_passing_gate": sorted(winners, key=lambda x: x[1]),
                           "band_ratio_vs_fem6db": (q[winner]["sharpness_band_grms_ratio_vs_fem6db"]
                                                    if winner in q else None),
                           "conservative_assumption_light_winner": conservative,
                           "conservative_band_ratio": q[conservative]["sharpness_band_grms_ratio_vs_fem6db"],
                           "caveat": caveat,
                           "note": "coverage(hard) + method-humility(leave-modes-out) gate, then sharpest (best of N)"}
    scorecard["selection"] = selection
    scorecard["method_humility"]["humble"] = method_humble

    (OUT / "bakeoff_scorecard.json").write_text(json.dumps(scorecard, indent=2))
    (OUT / "leave_modes_out.json").write_text(json.dumps(lmo_out, indent=2))
    print("\nSELECTION:", json.dumps(selection, indent=2))
    print("wrote bakeoff_scorecard.json, leave_modes_out.json")


if __name__ == "__main__":
    main()
