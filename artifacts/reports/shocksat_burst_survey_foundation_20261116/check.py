#!/usr/bin/env python3
"""Checker for the burst-survey foundation workspace. Three-tier status per gate
(GREEN met / YELLOW not met but documented / RED blocking); overall = worst gate.
Exit code 1 only on RED. Writes checker_report.json."""
import hashlib
import json
import os
import re
import sys

WS = os.path.dirname(os.path.abspath(__file__))
G, Y, R = "GREEN", "YELLOW", "RED"
gates = []


def gate(name, status, detail):
    gates.append({"gate": name, "status": status, "detail": detail})


def J(p):
    return json.load(open(os.path.join(WS, p)))


def exists(p):
    return os.path.exists(os.path.join(WS, p))


REQUIRED = ["packet.md", "question_framing.md", "priority_deliverables.md", "decisions_log.md", "assumptions_ledger.md",
            "quantity_contracts.md", "references.md", "prereg_gated_analysis.md", "prereg_frozen_inputs.json", "run_all.sh",
            "gated_run.sh", "runtime.json", "out/zip_directory_summary.json", "out/fetch_plan.json", "out/deck_evidence.json",
            "out/nasa_final_correlation.csv", "out/nasa_pretest_sensor_set.csv", "out/frf_wall_pilot.json",
            "out/frozen_project_fem_predictions.npz", "out/rehearsal_burst.json", "qa/zip_tools_unit.json",
            "qa/digitizer_known_answer.json", "qa/adf_probe_unit.json", "qa/tier4_dry_run.json", "qa/tufte_lint.txt",
            "qa/image_legibility.md", "qa/nasa_pch_unit.json", "prereg_lock.json", "figures/fig1_pilot_frf_wall.png", "figures/fig2_burst_resolution.png",
            "data/project_reference_numbers.json", "data/nasa_deck/PROVENANCE.json", "data/zip_tails/PROVENANCE.json"]
miss = [p for p in REQUIRED if not exists(p)]
gate("A0_required_artifacts", R if miss else G, f"missing: {miss}" if miss else f"{len(REQUIRED)} present")

z = J("qa/zip_tools_unit.json")
net = any("PyPI" in r.get("test", "") for r in z["results"])
gate("A1_zip_tools_known_answer", R if z["n_fail"] else G,
     f"{z['n_tests']} tests, {z['n_fail']} failed; live PyPI ranged-download test {'included' if net else 'not run in this replay (NETWORK=1 adds it)'}")

s = J("out/zip_directory_summary.json")
bad = []
for a, r in s["archives"].items():
    c = r["consistency"]
    if c["layout_violations"] or not c["eocd_plus_dir_reaches_eof"] or not c["first_member_at_zero"]:
        bad.append(f"{a}: layout")
    if r["size_bytes_inferred_from_tail"] != r["size_bytes_logged_2026_06_09"]:
        bad.append(f"{a}: size")
    if r["tail_4MiB_sha256_logged_2026_06_09"] and r["tail_4MiB_sha256"] != r["tail_4MiB_sha256_logged_2026_06_09"]:
        bad.append(f"{a}: tail hash")
    if not r["slice_sha256_matches_provenance"]:
        bad.append(f"{a}: slice hash")
    x = r.get("june_full_zip_crosscheck")
    if x and (x["entries_mismatched"] or x["entry_count_june"] != x["entry_count_here"]):
        bad.append(f"{a}: june crosscheck")
gate("A2_archive_listings", R if bad else G, bad or f"{len(s['archives'])} archives: layout, size, June tail hashes and June member sample all consistent")

p = J("out/fetch_plan.json")
tot = sum(t["compressed_bytes"] for t in p["tiers"])
ok = not p["correlation_members_unaccounted"] and tot == p["planned_total"]["compressed_bytes"]
gate("A3_fetch_plan", G if ok else R, f"{p['planned_total']['n_members']} members, {tot/1e6:.1f} MB compressed planned; "
     f"{len(p['correlation_members_unaccounted'])} Correlation members unaccounted")

d = J("out/deck_evidence.json")
prov = J("data/nasa_deck/PROVENANCE.json")
hok = all(hashlib.sha256(open(os.path.join(WS, "data/nasa_deck", f), "rb").read()).hexdigest() == h for f, h in prov["files"].items())
qok = all(q["found_verbatim"] for q in d["quotes"])
gap = d["final_correlation"]["max_abs_gap_nasa_vs_recomputed_pct_diff"]
gate("A4_nasa_deck_evidence", G if (hok and qok and gap <= 0.06) else R,
     f"extraction hashes {'ok' if hok else 'CHANGED'}; {sum(q['found_verbatim'] for q in d['quotes'])}/{len(d['quotes'])} quotes verbatim; "
     f"recomputed frequency differences within {gap:.3f} percentage points of NASA's printed values")

k = J("qa/digitizer_known_answer.json")
w, t = k["worst"], k["thresholds"]
metric_ok = w["calib_px"] <= t["calib_px"] and w["metric_median_abs_db"] <= t["metric_median_abs_db"] and w["metric_corr"] <= t["metric_corr"]
curve_ok = w["curve_median_db"] <= t["curve_median_db"] and w["curve_p95_db"] <= t["curve_p95_db"]
gate("A5_digitizer_known_answer", (G if curve_ok else Y) if metric_ok else R,
     f"metric errors: median |dB| {w['metric_median_abs_db']:.3f} dB (limit {t['metric_median_abs_db']}), corr {w['metric_corr']:.4f} "
     f"(limit {t['metric_corr']}); calibration {w['calib_px']:.2f} px. Curve-level: median {w['curve_median_db']:.2f} dB "
     f"(pre-set limit {t['curve_median_db']}), p95 {w['curve_p95_db']:.2f} dB" + ("" if curve_ok else " -> curve-level limit missed, metric-level met"))

pl = J("out/frf_wall_pilot.json")
ferr = max(v["frequency_check"]["max_abs_err_hz"] for v in pl["figures"].values())
gate("A6_pilot_frequency_calibration", G if ferr <= 0.2 else R,
     f"digitised peaks of the three well-separated modes (54, 70, 86 Hz) within {ferr:.3f} Hz of NASA's listed frequencies (pixel = 0.36 Hz); "
     "the 70/75 Hz test pair and 73/74 Hz FEM pair are not resolved as separate peaks (0.3-0.6 Hz offsets). Pilot is exploratory (2 curves, post hoc)")

a = J("qa/adf_probe_unit.json")
gate("A7_binary_probe_known_answer", G if a["all_pass"] else R, a["checks"])

t4 = J("qa/tier4_dry_run.json")
gate("A8_tier4_pipeline_dry_run", G if (t4["n_errors"] == 0 and t4["max_abs_err_m1_db"] <= 0.5 and t4["qa_pass_fraction"] == 1.0) else R,
     f"{t4['n_plots']} synthetic plots, max M1 error {t4['max_abs_err_m1_db']:.3f} dB, QA pass {t4['qa_pass_fraction']:.2f}")

fz = J("prereg_frozen_inputs.json")
npz = os.path.join(WS, "out/frozen_project_fem_predictions.npz")
fok = hashlib.sha256(open(npz, "rb").read()).hexdigest() == fz["output_sha256"]
pr = open(os.path.join(WS, "prereg_gated_analysis.md")).read()
gate("A9_preregistration_frozen", G if (fok and fz["array_sha256"] in pr) else R,
     f"{fz['n_curves']} frozen curves; file hash {'matches' if fok else 'CHANGED'}; array hash {'quoted' if fz['array_sha256'] in pr else 'NOT quoted'} in prereg_gated_analysis.md")

rb = J("out/rehearsal_burst.json")
sc = rb["scenarios"]
est_ok = all(sc[k]["median_abs_err_db"] <= 0.5 and sc[k]["peak_abs_err_db_median"] <= 0.25 for k in ("T4s", "T8s", "T16s"))
gate("A10_burst_estimator_rehearsal", G if est_ok else R,
     f"H1 median error {sc['T2s']['median_abs_err_db']:.2f} dB (2 s frames) vs {sc['T8s']['median_abs_err_db']:.2f} dB (8 s); "
     f"median |peak error| {sc['T8s']['peak_abs_err_db_median']:.2f} dB at 8 s, range {sc['T8s']['peak_err_db_min']:+.2f} to {sc['T8s']['peak_err_db_max']:+.2f} dB "
     f"over {sc['T8s']['n_peaks_scored']} modes; tail/burst ratio up to {sc['T2s']['tail_to_burst_rms_max']:.2f} at 2 s vs {sc['T8s']['tail_to_burst_rms_max']:.3f} at 8 s. "
     "Stand-in shakers, 50 % burst, drive-point peaks only")
gate("A11_damping_estimator_coverage", Y,
     f"half-power damping attempted on the {sc['T8s']['n_isolated_modes']} isolated modes; only 88 Hz gives an estimate (54.6 Hz never does at the stand-in drive points); {rb['modes_in_band'] - rb['isolated_modes_in_band']} of "
     f"{rb['modes_in_band']} FEM modes in 45-200 Hz are clustered and need a polyreference estimator (not built). "
     f"Estimator-free resolvability reported instead (lines across half-power width)")

lint = open(os.path.join(WS, "qa/tufte_lint.txt")).read()
leg = open(os.path.join(WS, "qa/image_legibility.md")).read()
gate("A12_figures_lint_and_legibility", G if ("WARN" not in lint and "PASS" in leg) else Y,
     "tufte_lint: no WARN; legibility review recorded" if "WARN" not in lint else "lint WARN present")

pu = J("qa/nasa_pch_unit.json")
gate("A7b_nasa_punch_parser_known_answer", G if pu["all_pass"] else R, f"{pu['checks']} (synthetic file in the June parser's layout; real files not yet in hand)")
lk = J("prereg_lock.json")
lbad = [p for p, h in lk["sha256"].items() if hashlib.sha256(open(os.path.join(WS, p), "rb").read()).hexdigest() != h]
gate("A16_preregistration_lock", R if lbad else G, f"{len(lk['sha256'])} locked files unchanged" if not lbad else f"changed after lock: {lbad}")
gs = J("logs/gate_status.json") if exists("logs/gate_status.json") else {"status": "NOT_RUN"}
gate("A13_nasa_data_gate", Y if gs["status"] != "FETCHED" else G,
     f"{gs['status']} at {gs.get('checked_utc', '?')}: burst files not yet fetched or parsed" if gs["status"] != "FETCHED" else "fetched")
t4 = J("out/tier4_results.json")["aggregate"] if exists("out/tier4_results.json") else None
bg = exists("out/burst_gates.json")
done = t4 is not None and not t4.get("exploratory", True) and t4.get("verdict") in ("SUPPORTED", "NOT_SUPPORTED", "INCONCLUSIVE") and bg
gate("A14_foundation_question", G if done else Y,
     "OPEN: pre-registered tier-4 test and burst-file gates F1-F5 are staged but not run (network gate)" if t4 is None else
     f"tier-4 verdict {t4.get('verdict')} ({t4.get('verdict_reason')}); burst gates {'evaluated' if bg else 'NOT yet evaluated'}")

rt = J("runtime.json")
# Expected non-zero exits: digitizer_test (curve-level limit missed, surfaced as A5 YELLOW)
# and nasa_gate (host blocked, surfaced as A13). Any other failed step is RED.
EXPECTED = {"digitizer_test", "nasa_gate"}
unexpected = sorted(set(rt.get("failed_step_names", [])) - EXPECTED)
ok_t = rt["active_runtime_s"] <= rt["elapsed_wallclock_s"]
gate("A15_runtime_and_replay", R if (unexpected or not ok_t) else G,
     f"active {rt['active_runtime_s']} s <= elapsed {rt['elapsed_wallclock_s']} s; non-zero exits {rt.get('failed_step_names', [])} "
     f"(expected: {sorted(EXPECTED)}); unexpected {unexpected}")

order = {G: 0, Y: 1, R: 2}
overall = max((g["status"] for g in gates), key=lambda s: order[s])
cnt = {s: sum(g["status"] == s for g in gates) for s in (G, Y, R)}
rep = {"overall": overall, "summary": f"{cnt[G]}G/{cnt[Y]}Y/{cnt[R]}R",
       "claim_ceiling": "GREEN gates certify tooling, provenance and pre-registration. They do not answer the foundation question, "
                        "which stays open until NASA's files are fetched (A13, A14).", "gates": gates}
json.dump(rep, open(os.path.join(WS, "checker_report.json"), "w"), indent=1)
for g in gates:
    print(f"{g['status']:6} {g['gate']}: {g['detail'] if isinstance(g['detail'], str) else json.dumps(g['detail'])[:160]}")
print("OVERALL", overall, rep["summary"])
sys.exit(1 if overall == R else 0)
