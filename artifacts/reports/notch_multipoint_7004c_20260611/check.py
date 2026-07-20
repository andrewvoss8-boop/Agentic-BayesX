#!/usr/bin/env python3
"""
Checker for notch_multipoint_7004c_20260611 (AGENTS.md green/yellow/red standard).
GREEN = threshold met; YELLOW = documented non-fatal miss (caveat carried);
RED = blocking. Exit nonzero ONLY on red. Overall = worst tier present.
"""
import json
import os
import sys

WS = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(WS, "results")
FIG = os.path.join(WS, "figures")

gates = []


def gate(name, tier, detail):
    gates.append(dict(name=name, tier=tier, detail=detail))
    print(f"[{tier.upper():6s}] {name}: {detail}")


def load(name):
    with open(os.path.join(RES, name)) as fh:
        return json.load(fh)


def main():
    # ---------- EX-A ----------
    try:
        ra = load("ex_a_results.json")
        worst = max(v["rel_err"] for v in ra["anchors"].values())
        n = len(ra["anchors"])
        gate("ex_a_handbook_anchors",
             "green" if (worst <= 0.02 and n >= 10) else "red",
             f"{n} anchors vs 7004C Fig8/9+AppB, worst rel err {worst*100:.2f}% "
             f"(threshold 2%; incl. handbook's own rounding)")
        iv = max(ra["impedance_vs_direct"].values())
        gate("ex_a_impedance_equals_direct",
             "green" if iv < 1e-10 else "red",
             f"Eq3/4 vs direct coupled solve max rel dev {iv:.2e} (<1e-10)")
    except Exception as e:
        gate("ex_a_results", "red", f"missing/unreadable: {e}")

    # ---------- EX-B ----------
    try:
        rb = load("ex_b_results.json")
        gate("ex_b_modes_match_closed_form",
             "green" if rb["mode_match_max_rel_err"] < 1e-9 else "red",
             f"numeric vs analytic 6 modes, max rel err {rb['mode_match_max_rel_err']:.2e}")
        gate("ex_b_static_limit_rigid_mass",
             "green" if rb["static_limit_vs_rigid_mass_rel_err"] < 1e-4 else "red",
             f"M(w->0) vs rigid-body matrix rel err "
             f"{rb['static_limit_vs_rigid_mass_rel_err']:.2e} (<1e-4; quasi-static at 0.05 Hz)")
        es = rb["effective_mass_table"]["sum_rel_err"]
        gate("ex_b_effective_mass_sums",
             "green" if es < 1e-9 else "red",
             f"sum over modes = rigid totals per direction, rel err {es:.2e} (7004C p.56)")
        tr = rb["resultant_trap"]
        gate("ex_b_resultant_trap",
             "green" if tr["net_over_4foot"] < 1e-6 else "red",
             f"net/(4*foot) = {tr['net_over_4foot']:.2e} at {tr['freq']:.1f} Hz rocking "
             f"(foot {tr['foot_peak']:.1f} N, My {tr['My']:.1f} N*m)")
    except Exception as e:
        gate("ex_b_results", "red", f"missing/unreadable: {e}")

    # ---------- EX-C ----------
    try:
        rc = load("ex_c_results.json")
        rides = [c["ride_along_lowf"] for c in rc["combos"].values()]
        ride_ok = all(abs(r - 1.0) < 0.06 for r in rides)
        gate("ex_c_lowf_ride_along",
             "green" if ride_ok else "red",
             f"payload rides feet rigidly at 22 Hz: ratios {[f'{r:.3f}' for r in rides]} "
             "(within 6%; finite 22-Hz dynamic amplification expected)")
        det = all(n.get("detected") for k in ("soft_t5_Q25", "stiff_t5_Q25")
                  for n in rc["combos"][k]["notches"])
        gate("ex_c_main_notches_detected",
             "green" if det else "red",
             "all 3 notch channels detected on both main variants (ratio-based, "
             "anchored interior minima)")
        fworst, aworst, flips = 0.0, 0.0, []
        for k, cv in rc["convergence"].items():
            for p in cv["pairs"]:
                if "note" in p:
                    flips.append(f"{k}/{p['mode']}: detection differs")
                    continue
                fworst = max(fworst, p["f_notch_shift_pct"])
                aworst = max(aworst, p["area_frac_shift"])
                if p["r_vis_shift_m"] > 0.1:
                    flips.append(f"{k}/{p['mode']}: r_vis shift {p['r_vis_shift_m']:.2f} m")
        gate("ex_c_truncation_convergence_robust_metrics",
             "green" if (fworst < 1.0 and aworst < 0.07 and not any('detection differs' in f for f in flips)) else "red",
             f"2x modal refinement: worst f_notch shift {fworst:.2f}% (<1%), worst "
             f"area-frac shift {aworst:.3f} (<0.07)")
        gate("ex_c_rvis_threshold_sensitivity",
             "yellow" if flips else "green",
             ("DOCUMENTED caveat (decisions_log D8): r_vis is a 3-dB threshold metric; "
              f"flips under refinement: {flips}. Use f_notch/area-frac as converged "
              "metrics; r_vis is descriptive.") if flips else "no r_vis flips")
        sup = [n.get("suppression_at_interface_dB", 0) for n in
               rc["combos"]["soft_t5_Q25"]["notches"] if n.get("detected")]
        gate("ex_c_interface_suppression_deep",
             "green" if min(sup) > 10 else "red",
             f"interface-channel suppression at notches {[f'{s:.0f}' for s in sup]} dB (>10)")
    except Exception as e:
        gate("ex_c_results", "red", f"missing/unreadable: {e}")

    # ---------- EX-D ----------
    try:
        rd = load("ex_d_results.json")
        nw = max(rd["newton_netF_relerr"], rd["newton_My_relerr"])
        gate("ex_d_newton_checks", "green" if nw < 1e-9 else "red",
             f"netF=m*a_cg and My_cg=Iyy*thdd to {nw:.2e}")
        rl = abs(rd["rigid_lowf_netF_per_ab"] / rd["M0"] - 1)
        gate("ex_d_lowf_apparent_mass", "green" if rl < 0.05 else "red",
             f"net F/a_b at 20 Hz = {rd['rigid_lowf_netF_per_ab']:.3f} vs M0={rd['M0']} "
             f"({rl*100:.1f}% — finite 20-Hz amplification expected)")
        lr = max(rd["limited_respects_limit"].values())
        gate("ex_d_limits_respected", "green" if lr <= 1.0 + 1e-9 else "red",
             f"max(limited response / limit) = {lr:.6f} (<=1)")
        rows = rd["overtest_table"]
        kp = [k for k in rows if k.startswith("pitch")][0]
        kb = [k for k in rows if k.startswith("bounce")][0]
        story = (rows[kb]["ii_netF"]["foot_worst"] < 0.1 * rows[kb]["i_unlimited"]["foot_worst"]
                 and rows[kp]["ii_netF"]["foot_worst"] > 3 * rows[kb]["ii_netF"]["foot_worst"]
                 and rows[kp]["iii_netF_plus_My"]["foot_worst"]
                 < 0.5 * rows[kp]["ii_netF"]["foot_worst"])
        gate("ex_d_overtest_structure", "green" if story else "red",
             f"bounce {rows[kb]['i_unlimited']['foot_worst']:.0f}x->"
             f"{rows[kb]['ii_netF']['foot_worst']:.1f}x (netF works); pitch stays "
             f"{rows[kp]['ii_netF']['foot_worst']:.0f}x under netF, ->"
             f"{rows[kp]['iii_netF_plus_My']['foot_worst']:.0f}x with moment limit")
        gate("ex_d_thx_undertest", "green" if rd["thx_undertest"]["test_acc_thx_max"] < 1e-12
             else "red",
             f"test roll accel {rd['thx_undertest']['test_acc_thx_max']:.1e} (exact 0) vs "
             f"flight peak {rd['thx_undertest']['flight_peak_acc_thx']:.2f} rad/s^2/N")
        gate("ex_d_flight_labeled_hypothetical",
             "green" if "HYPOTHETICAL" in rd["labels"]["flight"] else "red",
             rd["labels"]["flight"])
    except Exception as e:
        gate("ex_d_results", "red", f"missing/unreadable: {e}")

    # ---------- EX-E ----------
    try:
        re_ = load("ex_e_results.json")
        fe = max(v["full_recon_max_err"] for v in re_["regimes"].values())
        gate("ex_e_full_impedance_exact", "green" if fe < 1e-9 else "red",
             f"full matrix impedance reconstruction == coupled FEM truth, max rel err "
             f"{fe:.2e} (<1e-9): a measurement CAN replace the coupled solve")
        # scalar single-point must be blind to moment (My err ~100%) and miss per-foot
        soft = re_["regimes"]["soft_Q25"]["mode_err"]
        scal_my = [row["scalar"]["My"]["rel_err"] for row in soft.values()]
        scal_ft = [row["scalar"]["foot"]["rel_err"] for row in soft.values()]
        gate("ex_e_scalar_blind_to_rocking",
             "green" if (min(scal_my) > 0.99 and min(scal_ft) > 0.5) else "red",
             f"single-point: moment err {[f'{v*100:.0f}%' for v in scal_my]} (~100% = "
             f"predicts 0), per-foot err {[f'{v*100:.0f}%' for v in scal_ft]} (>50%)")
        rig_ft = [row["rigid3"]["foot"]["rel_err"] for row in soft.values()]
        gate("ex_e_rigid3_recovers_rocking",
             "green" if max(rig_ft) < 0.25 else "red",
             f"rigid-3 (>=3 feet) per-foot err {[f'{v*100:.0f}%' for v in rig_ft]} "
             "(<25% in the soft/low-overlap regime) = rocking recovered without coupled FEM")
        rp = re_["remote_proxy"]
        mism = [rp[k]["err_off_resonance_med"] for k in rp if isinstance(rp[k], dict)]
        gate("ex_e_remote_proxy_config_mismatch",
             "green" if min(mism) > 0.3 else "red",
             f"bare-config transmissibility proxy err {[f'{v*100:.0f}%' for v in mism]} "
             "(large = must calibrate in the integrated config; in-config is exact)")
    except Exception as e:
        gate("ex_e_results", "red", f"missing/unreadable: {e}")

    # ---------- artifacts ----------
    figs = ["fig_a1_fig9_replication.png", "fig_a2_fig8_replication.png",
            "fig_a3_notch_overtest.png", "fig_b1_apparent_mass_matrix.png",
            "fig_b2_effective_masses.png", "fig_b3_resultant_trap.png",
            "fig_c1_interface_spectra.png", "fig_c2_notch_maps_bounce.png",
            "fig_c2b_notch_maps_rocking.png", "fig_c3_depth_vs_distance.png",
            "fig_c4_rvis_vs_lambda.png", "fig_d1_test_vs_flight.png",
            "fig_d2_overtest_bars.png", "fig_e1_reconstruction_channels.png",
            "fig_e2_error_by_regime.png", "fig_e3_remote_proxy.png"]
    missing = [f for f in figs if not os.path.exists(os.path.join(FIG, f))
               or os.path.getsize(os.path.join(FIG, f)) < 30000]
    gate("figures_exist", "green" if not missing else "red",
         f"{len(figs)-len(missing)}/{len(figs)} figures present & >30kB"
         + (f"; MISSING {missing}" if missing else ""))

    try:
        from PIL import Image
        gif_ok = []
        for g in ["gif_a_tdof_notch_sweep.gif", "gif_b_rocking_trap.gif",
                  "gif_c_notch_field_sweep.gif"]:
            im = Image.open(os.path.join(FIG, g))
            gif_ok.append(getattr(im, "n_frames", 1) >= 30)
        gate("gifs_animate", "green" if all(gif_ok) else "red",
             f"3 GIFs with >=30 frames each: {gif_ok}")
    except Exception as e:
        gate("gifs_animate", "red", f"{e}")

    try:
        from pptx import Presentation
        prs = Presentation(os.path.join(WS, "7004c_multipoint_notch_summary.pptx"))
        ns = len(prs.slides._sldIdLst)
        gate("pptx_built", "green" if ns >= 12 else "red", f"{ns} slides (>=12)")
    except Exception as e:
        gate("pptx_built", "red", f"{e}")

    docs = ["question_framing.md", "priority_deliverables.md", "assumptions_ledger.md",
            "quantity_contracts.md", "decisions_log.md", "packet.md",
            "notching_findings_for_future_agents.md", "lit_review_prompt.md"]
    dmiss = [d for d in docs if not os.path.exists(os.path.join(WS, d))]
    gate("harness_docs", "green" if not dmiss else "red",
         "all harness + handoff docs present" if not dmiss else f"missing {dmiss}")

    # complex-TDOF tables not replicated: documented gap (D3)
    gate("complex_tdof_tables", "yellow",
         "7004C Appendix C complex-TDOF tables NOT replicated (image-only PDF; "
         "documented decisions_log D3) — methods used are equation-anchored instead")

    tiers = [g["tier"] for g in gates]
    overall = "red" if "red" in tiers else ("yellow" if "yellow" in tiers else "green")
    ng = tiers.count("green"); ny = tiers.count("yellow"); nr = tiers.count("red")
    print(f"\nOVERALL: {overall.upper()}  ({ng} green / {ny} yellow / {nr} red)")
    with open(os.path.join(WS, "checker_report.json"), "w") as fh:
        json.dump(dict(overall=overall, green=ng, yellow=ny, red=nr, gates=gates),
                  fh, indent=1)
    print("wrote checker_report.json")
    sys.exit(1 if overall == "red" else 0)


if __name__ == "__main__":
    main()
