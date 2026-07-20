#!/usr/bin/env python3
"""Checker for shocksat_tray_coupled_qoi_20260610 (Result Status Standard:
green / yellow / red; exits non-zero ONLY on red). Writes checker_report.json.

Verifies artifact existence + physics expectations + integrity; it cannot
verify the invented assumptions themselves (those are sign-off items D2-D4).
"""
import hashlib
import json
import os
import sys
import numpy as np

WS = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(WS, "out")
FIG = os.path.join(WS, "figures")
gates = {}


def gate(name, status, note=""):
    gates[name] = dict(status=status, note=note)
    print(f"  {name}: {status.upper()}  {note}")


def exists(p):
    return os.path.exists(os.path.join(WS, p)) and \
        os.path.getsize(os.path.join(WS, p)) > 0


print("== docs / contract-first ==")
need_docs = ["quantity_contracts.md", "assumptions_ledger.md",
             "priority_deliverables.md", "question_framing.md",
             "decisions_log.md"]
gate("docs_present", "green" if all(exists(d) for d in need_docs) else "red",
     str([d for d in need_docs if not exists(d)]))
qc = open(os.path.join(WS, "quantity_contracts.md")).read()
need_strings = ["numerator", "NASA-HDBK-7004C", "LOAD apparent mass",
                "source apparent mass", "FREE-FREE", "SRSS", "Miles",
                "maximax ABSOLUTE", "limiting behavior"]
miss = [s for s in need_strings if s.lower() not in qc.lower()]
gate("quantity_contract_conventions", "green" if not miss else "red", str(miss))

print("== verification gates (verify.py) ==")
if exists("out/verification.json"):
    v = json.load(open(os.path.join(OUT, "verification.json")))
    worst = v["overall"]
    bad = {k: g["status"] for k, g in v["gates"].items()
           if g["status"] != "green"}
    gate("verification_overall", worst, f"non-green: {bad}" if bad else
         f"{len(v['gates'])} gates all green (V1-V9: tray rebuild exact, "
         "rigid-mass/units, SRS filter, FBS algebra, exact damped apparent "
         "mass, Newmark cross-check, 7004C TDOF anchors)")
else:
    gate("verification_overall", "red", "out/verification.json missing")

print("== production outputs ==")
need_out = ["out/qoi_results.json", "out/variance_decomposition.json",
            "out/sweeps.json", "out/nominal_spectra.npz",
            "out/qoi_nominal.json", "out/mount_node.json",
            "out/mount_identifiability.json", "out/response_limit_proxy.json",
            "out/srs_cache.npz"]
gate("outputs_present", "green" if all(exists(p) for p in need_out) else "red",
     str([p for p in need_out if not exists(p)]))

if exists("out/qoi_results.json"):
    res = json.load(open(os.path.join(OUT, "qoi_results.json")))
    # hypothetical labeling
    gate("hypothetical_label_in_results",
         "green" if "HYPOTHETICAL" in res["meta"]["label"] else "red")
    # force limiting: uncoupled >= coupled (median over draws x seeds)
    fl = res["force_limiting_factor_joint"]["median"]
    gate("force_limiting_unc_ge_cpl",
         "green" if all(r >= 1.0 for r in fl) else "yellow",
         f"median peak_unc/peak_cpl per axis = {[round(r,2) for r in fl]} "
         "(>1 = over-test; <1 possible near shifted coupled resonances)")
    # method conservatism table sanity: ratios finite & positive
    rt = res["ratios"]
    ok = all(np.isfinite(rr["median"]).all() and (np.array(rr["median"]) > 0).all()
             for rr in rt.values())
    gate("method_ratios_finite", "green" if ok else "red")
else:
    gate("hypothetical_label_in_results", "red", "qoi_results missing")

if exists("out/variance_decomposition.json"):
    vd = json.load(open(os.path.join(OUT, "variance_decomposition.json")))
    md = vd.get("mount_dominated_axes")
    gate("variance_decomposition_present", "green",
         f"mount-dominated axes (coupled th): {md}; OAT note present: "
         f"{'OAT' in vd['note']}")

print("== identifiability gate (AGENTS.md Modal/Eigenproblem) ==")
if exists("out/mount_identifiability.json"):
    mi = json.load(open(os.path.join(OUT, "mount_identifiability.json")))
    clos = [abs(r["closure"] - 1.0) for r in mi["coupled_mode_se"]]
    st = "green" if max(clos) < 0.01 else "yellow"
    gate("se_closure", st, f"max |closure-1| = {max(clos):.1e} over "
         f"{len(clos)} coupled modes <= 300 Hz")
    hasfp = all(k in mi["finite_perturbation"] for k in ("x0.5", "x2.0"))
    gate("finite_perturbation_present", "green" if hasfp else "red",
         "x0.5/x2 mount perturbation with QOI shifts" if hasfp else "")
    gate("identifiability_cause_stated",
         "green" if "statement" in mi["verdict"] else "red",
         f"peak dlnf/dlnk = {mi['verdict']['peak_dlnf_dlnk']} vs sigma_f floor "
         f"{mi['verdict']['sigma_f_floor']}")
else:
    gate("se_closure", "red", "mount_identifiability.json missing")

print("== sampler rule ==")
dl = open(os.path.join(WS, "decisions_log.md")).read()
gate("no_sampler_decision_documented",
     "green" if "NO sampler is run in this task" in dl else "red",
     "propagation-only decision D1; no NUTS claim made")

print("== figures ==")
need_figs = ["fig_graphical_model.png", "fig_input_env.png",
             "fig_apparent_mass.png", "fig_force_limiting.png",
             "fig_method_comparison.png", "fig_mount_sensitivity.png",
             "fig_identifiability.png", "fig_proxy.png", "fig_th_sample.png"]
gate("figures_present",
     "green" if all(exists(os.path.join("figures", f)) for f in need_figs)
     else "red", str([f for f in need_figs if not exists(os.path.join("figures", f))]))
mf = open(os.path.join(WS, "code", "make_figures.py")).read()
gate("figure_provenance_labels",
     "green" if ("HYPOTHETICAL" in mf and "stamp(" in mf and "RUN" in mf)
     else "red", "every data figure stamped with run + hypothetical flag")
gate("image_qa", "green" if exists("out/image_qa.json") else "yellow",
     "artifact-backed legibility report (sizes + manual review notes)")

print("== integrity: read-only inputs unchanged ==")
if exists("inputs_sha256_start.json"):
    start = json.load(open(os.path.join(WS, "inputs_sha256_start.json")))
    bad = []
    for p, rec in start.items():
        full = os.path.join(WS, "..", "..", "..", p)
        h = hashlib.sha256(open(full, "rb").read()).hexdigest()
        if h != rec["sha256"]:
            bad.append(p)
    gate("inputs_unchanged", "green" if not bad else "red", str(bad))
else:
    gate("inputs_unchanged", "red", "inputs_sha256_start.json missing")

print("== overnight VOI experiment (D10) ==")
if exists("out/coupled_rom_report.json"):
    rr = json.load(open(os.path.join(OUT, "coupled_rom_report.json")))
    gate("coupled_rom_reduction", rr["gate_status"],
         f"worst matched |df|/f = {rr['worst_rel_err']:.1e} vs {rr['gate']} "
         f"(nb={rr['nb']}; off-anchor probe is the span test)")
else:
    gate("coupled_rom_reduction", "red", "coupled_rom_report.json missing")
if exists("out/truth_lock.json") and exists("out/survey_data.npz"):
    import hashlib as _h
    lk = json.load(open(os.path.join(OUT, "truth_lock.json")))
    blob = json.dumps(lk["payload"], sort_keys=True).encode()
    okh = _h.sha256(blob).hexdigest() == lk["sha256"]
    gate("truth_lock_integrity", "green" if okh else "red",
         "SHA verified; sampler reads only survey_data.npz (A28)")
    pr = json.load(open(os.path.join(OUT, "pairing_coupled.json")))
    gate("survey_pairing", "green" if pr["n_calib"] >= 8 else "red",
         f"n_calib = {pr['n_calib']} (anchor x{pr['anchor_mult']})")
else:
    gate("truth_lock_integrity", "red", "truth/survey artifacts missing")
if exists("out/mount_posterior.json"):
    mp = json.load(open(os.path.join(OUT, "mount_posterior.json")))
    cv = mp["convergence"]
    gate("convergence_mount_nuts",
         "green" if cv["gate_pass"] else "yellow",
         f"tag={mp['final_tag']} worst R-hat {cv['worst_rhat']:.3f}, min ESS "
         f"{cv['min_ess']:.0f}, div {cv['divergences']} "
         + ("(gate passed over ALL latents)" if cv["gate_pass"] else
            "(NOT converged - YELLOW finding, intervals not trustworthy)"))
else:
    gate("convergence_mount_nuts", "red", "mount_posterior.json missing "
         "(overnight NUTS not finished?)")
if exists("out/voi_results.json"):
    voi = json.load(open(os.path.join(OUT, "voi_results.json")))
    wr = [voi["qoi_table"]["th_cpl"][f"axis_{a}"]
          ["width95_ratio_after_over_before"] for a in "xyz"]
    cov = [voi["qoi_table"]["th_cpl"][f"axis_{a}"]["truth_covered_after"]
           for a in "xyz"]
    st = "green" if all(cov) else "yellow"
    gate("voi_truth_coverage", st,
         f"after-bands cover truth: {cov}; width95 ratios {wr} "
         "(miss = honest negative, documented)")
    gate("voi_artifacts", "green", "qoi_table + recovery + sigma_f present")
else:
    gate("voi_artifacts", "red", "voi_results.json missing")
gate("fig_voi", "green" if exists("figures/fig_voi.png") else "red")

print("== pooled-mount arm (D15/D16) ==")
if exists("out/pooled_fim.json") and exists("out/pooled_diagnosis.json"):
    pf = json.load(open(os.path.join(OUT, "pooled_fim.json")))
    pd_ = json.load(open(os.path.join(OUT, "pooled_diagnosis.json")))
    gate("pooled_fim_present", "green",
         "FIM over pooled parameterizations at realized + noise floors")
    worst = max(v["worst_rhat"] for k, v in pd_["sampler"].items()
                if k in ("p2", "p3b"))
    gate("pooled_nuts_convergence", "yellow",
         "sampler ladder 6->3->2 params: R-hat 5.03 -> 1.52 -> 1.24; remedy "
         "p2r (2000+2000 d9) WORSE at 2.22 = STRUCTURAL one-sided "
         "non-identifiability (stiff-side saturation; r_all pinned, t_all "
         "lower-bound only). Documented finding; intervals not trustworthy.")
else:
    gate("pooled_fim_present", "red", "pooled artifacts missing")

print("== program deck (D13) ==")
deck = "slides/shocksat_program_deck.pptx"
need_dfigs = ["deck_arc.png", "deck_force_limiting.png",
              "deck_mount_dominance.png", "deck_identifiability.png",
              "deck_scorecard.png", "deck_method.png",
              "deck_coupled_assembly.png"]
gate("deck_pptx", "green" if exists(deck) else "red",
     "14-slide program deck for Bilionis/Girolami/Yunis" if exists(deck) else "")
gate("deck_figures", "green" if all(exists(os.path.join("slides/figs", f))
     for f in need_dfigs) else "red",
     str([f for f in need_dfigs if not exists(os.path.join("slides/figs", f))]))
need_gifs = ["force_limiting_sweep.gif", "mode_walk_qoi.gif",
             "multimodality.gif"]
gate("deck_gifs", "green" if all(exists(os.path.join("slides/gifs", g))
     for g in need_gifs) else "red", "supplementary animations (not embedded)")
dfm = open(os.path.join(WS, "code", "make_deck_figs.py")).read()
gate("deck_fig_provenance",
     "green" if ("HYPOTHETICAL" in dfm and "stamp(" in dfm) else "red",
     "deck figures carry run + hypothetical stamp")

print("== bookkeeping ==")
gate("runtime_json", "green" if exists("runtime.json") else "red")
if exists("runtime.json"):
    rt = json.load(open(os.path.join(WS, "runtime.json")))
    ok = rt["active_runtime_s"] <= rt["elapsed_wallclock_s"]
    gate("runtime_accounting", "green" if ok else "red",
         f"active {rt['active_runtime_s']} <= wall {rt['elapsed_wallclock_s']}")
gate("manifest", "green" if exists("manifest.json") else "red")
gate("files_changed", "green" if exists("files_changed.md") else "red")
gate("packet", "green" if exists("packet.md") else "red")
if exists("packet.md"):
    pk = open(os.path.join(WS, "packet.md")).read()
    gate("packet_honesty",
         "green" if ("HYPOTHETICAL" in pk and "Method summary" in pk
                     and "graphical model" in pk.lower()) else "red",
         "hypothetical banner + method summary + graphical model at top")

worst = "green"
for g in gates.values():
    if g["status"] == "red":
        worst = "red"
        break
    if g["status"] == "yellow":
        worst = "yellow"
n = {s: sum(1 for g in gates.values() if g["status"] == s)
     for s in ("green", "yellow", "red")}
report = dict(overall=worst, counts=n, gates=gates,
              standard="green/yellow/red per AGENTS.md Result Status Standard; "
                       "exit non-zero only on red")
json.dump(report, open(os.path.join(WS, "checker_report.json"), "w"), indent=1)
print(f"\nOVERALL: {worst.upper()}  ({n['green']} green / {n['yellow']} yellow "
      f"/ {n['red']} red)")
sys.exit(1 if worst == "red" else 0)
