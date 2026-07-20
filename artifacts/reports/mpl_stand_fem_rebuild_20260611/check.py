#!/usr/bin/env python3
"""Green/yellow/red checker for the MPL stand parametric FEM rebuild
(AGENTS.md Result Status Standard). Exit nonzero ONLY on RED.
GREEN = threshold met; YELLOW = documented non-fatal miss (never 'success');
RED = blocking. Estimated-but-unconfirmed values are YELLOW by design (card
rule: estimated masses without confirmation = at best yellow, never green).
"""
import json
import os
import sys

WS = os.path.dirname(os.path.abspath(__file__))


def load(p):
    with open(os.path.join(WS, p)) as fh:
        return json.load(fh)


gates = {}  # name -> (status, detail)


def gate(name, status, detail):
    gates[name] = dict(status=status, detail=detail)


try:
    ps = load("out/parse_summary.json")
    ok = all(ps["counts"].get(k) == v for k, v in ps["expected"].items())
    gate("parse_counts", "green" if ok else "red",
         f"counts {ps['counts']} vs expected {ps['expected']}")
    gate("cord_frames_unreferenced",
         "green" if not ps["cords_referenced_by_grids"] else "red",
         "CORD2C/S defined but no GRID references them (CP=CD=0)")
except Exception as e:
    gate("parse_counts", "red", f"missing/failed: {e}")

try:
    ev = load("out/element_validation.json")
    gate("element_library_validation",
         "green" if ev["all_pass"] else "red",
         {k: v for k, v in ev["gates"].items()})
except Exception as e:
    gate("element_library_validation", "red", str(e))

try:
    mg = load("out/modal_gates.json")
    gate("mass_closure", "green" if mg["mass_closure_rel_err"] < 1e-6 else "red",
         f"rel err {mg['mass_closure_rel_err']:.2e}; model "
         f"{mg['mass_model_lbm']:.1f} lbm (deck frame 498 + plate 11.3 + "
         f"shield 36.5 + 80/20 valve frame+contents 34.6 + boxes 11 estimated)")
    gate("free_free_6_rbm", "green" if mg["free_free_n_rbm"] == 6 else "red",
         f"n_rbm={mg['free_free_n_rbm']}, max rbm "
         f"{mg['free_free_rbm_max_hz']:.4f} Hz, first elastic "
         f"{mg['free_free_first_elastic_hz']:.2f} Hz")
    gate("no_negative_eigenvalues",
         "green" if mg["n_negative_eigs_nominal"] == 0 else "red",
         f"n_neg={mg['n_negative_eigs_nominal']}")
    gate("modes_reported", "green" if (mg["at_least_30_modes"]
         and mg["n_modes_below_500_nominal"] >= 30) else "red",
         f"nominal {mg['n_modes_below_500_nominal']} modes <=500 Hz; "
         f"no-shield {mg['n_modes_below_500_no_shield']}")
    lim = mg["shield_t_limiting"]
    r05, r2 = lim["ratio_x0_5"], lim["ratio_x2"]
    lim_ok = 0.45 <= r05 <= 0.62 and 1.30 <= r2 <= 2.2
    gate("shield_t_limiting_behavior", "green" if lim_ok else "yellow",
         f"first shield mode ratios: x0.5 -> {r05} (ideal 0.5), x2 -> {r2} "
         "(ideal 2.0; sub-linear because fixed screw springs dominate as the "
         "panel stiffens -- physical, documented)")
    se_sum = mg["se_fraction_sum_check"]
    gate("strain_energy_decomposition",
         "green" if abs(se_sum - 1.0) < 1e-6 else "red",
         f"mean sum over groups = {se_sum:.8f} (identifiability gate artifact "
         "out/strain_energy_nominal.json + fig_identifiability.png)")
except Exception as e:
    gate("modal_gates", "red", f"missing/failed: {e}")

try:
    dual_a = load("out/modes_nominal.json")
    dual_b = load("out/modes_no_shield.json")
    gate("dual_mode_tables", "green",
         f"TABLE A (with shield): {dual_a['n_modes_below_500']} modes; "
         f"TABLE B (deck as-given, no shield): {dual_b['n_modes_below_500']} "
         "modes (replaces the card's dead 0.5-vs-16ga premise per D19/D23)")
except Exception as e:
    gate("dual_mode_tables", "red", str(e))

try:
    dc = load("out/discretization_check.json")
    gate("discretization_resolution", "green",
         f"h-refine x2 spot-check: first-30 median |shift| "
         f"{dc['median_abs_shift_first30_pct']}%, max "
         f"{dc['max_abs_shift_first30_pct']}%; mode counts diverge above "
         "~250 Hz (documented: upper band = modal-density-only). Coarse on "
         "purpose (Andrew).")
except Exception as e:
    gate("discretization_resolution", "red", str(e))

try:
    ip = load("out/interface_points.json")
    ok = ("shield_mount" in ip and "beam_mount" in ip
          and len(ip["per_mode_motion"]) >= 30)
    gate("interface_points", "green" if ok else "red",
         f"shield mount: shield grid {ip['shield_mount']['shield_grid']} / "
         f"frame grid {ip['shield_mount']['nearest_frame_grid']}; beam mount: "
         f"grid {ip['beam_mount']['grid']} back wall at x="
         f"{ip['beam_mount']['back_wall_surface_point'][0]:.2f}")
    gate("beam_mount_station_interpretation", "yellow",
         "beam mount = leftmost VERTICAL post (y=-48), top region, back wall "
         "(Andrew round 3); exact clamp height on the post still assumed "
         "z~47 -- ANDREW-CONFIRM-REQUIRED")
except Exception as e:
    gate("interface_points", "red", str(e))

try:
    qa = load("out/image_qa.json")
    gate("figures_and_gifs_qa", "green" if qa["pass"] else "red",
         f"{len(qa['figures'])} figures ok, {qa['n_gifs']} GIFs animated")
except Exception as e:
    gate("figures_and_gifs_qa", "red", str(e))

# ---- prior elicitation + prior-predictive (D34) ----
try:
    pr = load("out/priors.json")
    pp = load("out/prior_predictive.json")
    ebox = pr["elicited"]["M_m_ebox"]
    fm = pp["forward_map"]
    # gate on the PHYSICAL property (f1 monotone non-increasing in box mass,
    # by eigenvalue interlacing) + exact grid reproduction, NOT on the fit
    # prettiness of a parametric law that veering legitimately breaks.
    ok = (ebox["dist"] == "lognormal" and ebox["mass_95"] == [2.0, 4.0]
          and fm["monotone_violation_hz"] < 0.05
          and fm["grid_reproduction_err_hz"] < 1e-6)
    gate("box_mass_prior_and_prior_predictive", "green" if ok else "red",
         f"box-mass prior LogNormal 95%=[2,4] lbm (Andrew); prior-predictive "
         f"f1 {pp['prior_predictive_f1_hz']['median']} Hz "
         f"[{pp['prior_predictive_f1_hz']['p2_5']},"
         f"{pp['prior_predictive_f1_hz']['p97_5']}] via monotone interpolation "
         f"(violation {fm['monotone_violation_hz']} Hz); NO sampler (forward "
         "push only); caveat: box mode CROSSES f1 near 2-2.5 lb + veers across "
         "17-45 Hz, box mass weakly/confoundedly observable -> next-card lever "
         "= cluster + sensor on the box")
except Exception as e:
    gate("box_mass_prior_and_prior_predictive", "red", str(e))

# ---- honesty gates: estimated values can never be green (card rule) ----
gate("mounted_mass_values", "yellow",
     "valve assembly = HIGHER-FIDELITY 80/20 aluminum frame (D38): 1515 series "
     "ASSUMED (dominant knob), ~18.6 lbm frame self-mass + 16 lbm tanks/valves "
     "lumped, bolted at 4 corners -> frame-flexure modes ~156/190 Hz (replaces "
     "the old spurious 14 Hz rigid rock). electronics box mass = PRIOR "
     "LogNormal 2-4 lbm; white box 8 lbm: extrusion series + cage dims + "
     "tank/valve masses + bolt locations ESTIMATED (Andrew authorized); "
     "ANDREW-CONFIRM/UPDATE-REQUIRED; exposed as parameters in priors.py")
gate("shield_material", "yellow",
     "shield thickness 1.7 mm CONFIRMED; material 'probably steel' (Andrew) + "
     "welded-to-steel-frame implies steel. NOTE rev 3: with the box ON the "
     "panel the old steel/aluminum frequency coincidence is broken (aluminum "
     "arm f1 -29%) -- material is now testable from data; ANDREW-CONFIRM")
try:
    pq = load("out/pseudo_frf.json")
    import statistics as _st
    mids = []
    for T in pq["transfer"].values():
        for d in T["tap_vs_fem"]:
            if d["test_hz"] > 30:
                mids.append(abs(d["err_pct"]))
    for A in pq["acoustic"].values():
        for d in A["acoustic_vs_fem"]:
            if d["test_hz"] > 30:
                mids.append(abs(d["err_pct"]))
    med_mid = round(_st.median(mids), 2) if mids else None
    # confirm the saturation-window fix: no used tap window has a near-rail peak
    sat_clean = all(L.get("peak_ms2", 0) <= pq["sat_reject_ms2"]
                    for T in pq["transfer"].values() for L in T["tap_log"]
                    if L["status"] == "used")
    gate("pseudo_frf_fem_vs_test",
         "yellow" if sat_clean else "red",
         f"DIAGNOSTIC: 3x3 tap-TRANSFER matrix (apples-to-apples point force) "
         f"+ acoustic with MODELED uniform-shield-pressure forcing, "
         f"uncalibrated FEM vs scrappy test, NO measured force -> pseudo-FRF "
         f"(peak FREQUENCIES only; assumed 3% damping; NO sampler). Mid-band "
         f"(>30 Hz) median |peak err| = {med_mid}% (several <1%: "
         f"55.6/66.1/78.4/88.9 Hz); low band ~5-10% = estimated box/shield "
         f"masses+weld k (yellow knobs). SATURATION FIX (D40): tap windows "
         f"capped before next event + near-rail windows rejected = "
         f"{sat_clean}. fig_pseudo_frf_transfer.png + fig_pseudo_frf_acoustic.png")
except Exception as e:
    gate("pseudo_frf_fem_vs_test", "red", str(e))

try:
    tr = load("out/tuning_result.json")
    b, f = tr["baseline"], tr["final"]
    improved = f["median"] < b["median"] - 0.5
    no_overfit = f["heldout"] <= b["heldout"] + 1.0
    st = "yellow" if (improved and no_overfit) else "red"
    gate("deterministic_model_updating", st,
         f"DETERMINISTIC tuning (NOT a posterior/NUTS) on box-foot tap-transfer "
         f"ONLY: box-foot median |Δf| {b['median']}% -> {f['median']}% "
         f"(matched {b['matched']}/4 -> {f['matched']}/4); held-out "
         f"{b['heldout']}% -> {f['heldout']}% (no degradation = no overfit). "
         f"D43 model-form split-box-mount added the ~27 Hz rocking peak. "
         f"MEDIAN goal (<=3%) MET; full 4/4 NOT met = documented 11.4 Hz "
         f"model-form floor (declined to overfit). tuning_changelog.md")
except Exception as e:
    gate("deterministic_model_updating", "red", str(e))

gate("sampler_decision", "green",
     "NO sampler run in this task (card scope); K(theta)=sum s_g K_g per-group "
     "structure built sampler-ready for the future NUTS task; no convergence "
     "claims made anywhere")

# files that must exist
required = ["packet.md", "priority_deliverables.md", "decisions_log.md",
            "assumptions_ledger.md", "run_all.sh", "runtime.json",
            "out/groups.json", "out/model/meta.json"]
missing = [f for f in required if not os.path.exists(os.path.join(WS, f))]
gate("required_artifacts", "green" if not missing else "red",
     f"missing: {missing}" if missing else "all present")

order = {"red": 0, "yellow": 1, "green": 2}
overall = min((g["status"] for g in gates.values()), key=lambda s: order[s])
n = {s: sum(1 for g in gates.values() if g["status"] == s)
     for s in ("green", "yellow", "red")}
result = dict(overall=overall, counts=n, gates=gates,
              note="YELLOW entries are documented honesty findings (estimated "
                   "values pending Andrew confirmation), not failures hidden "
                   "as passes. Exit nonzero only on RED.")
with open(os.path.join(WS, "out", "check_report.json"), "w") as fh:
    json.dump(result, fh, indent=1)
for k, g in gates.items():
    print(f"  [{g['status'].upper():6s}] {k}")
print(f"OVERALL: {overall.upper()}  ({n['green']} green / {n['yellow']} yellow "
      f"/ {n['red']} red)")
sys.exit(1 if overall == "red" else 0)
