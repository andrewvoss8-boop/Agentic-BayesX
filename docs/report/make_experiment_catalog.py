#!/usr/bin/env python3
"""Experiment catalog generator -> docs/report/experiment_catalog.{csv,xlsx}.
Hand-curated from each workspace's packet/findings/checker + project_log/runs.md (status never stronger than
checkers). Publishability ratings (1-5) are LEAD-AGENT PROPOSALS for Andrew to adjust:
5 = literature-contribution candidate as-is · 4 = strong with modest packaging · 3 = solid supporting result /
reusable lesson · 2 = internal value mostly · 1 = scaffolding/scratch. Deck column = a .pptx exists in-folder."""
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
COLS = ["folder (experiment run)", "guiding question", "dataset (synthetic if synthetic)",
        "main finding(s)", "publishability 1-5 (proposed)", "slide deck"]

R = [
 ["bilionis_update_20260702", "Consolidation: 1-paragraph + 2-slide status for Bilionis", "n/a (consolidation)",
  "Update deck: held-out-gated results; agentic remodeling evidence-win fails held-out; Beck per-point champion unsafe for net-CG normal.", 2, True],
 ["shocksat_composite_bakeoff_20260702", "Does {agentic remodeling x MAC-in-likelihood x Beck shape field} + statFEM F(k) beat the proven baseline on HELD-OUT data?", "REAL ShockSat (.ash EMA survey + 5 tap-test drives)",
  "Checker YELLOW 57G/6Y/0R. (1) Evidence-selected remodel (+54 logZ, P=0.72) FAILS held-out (R4) -> evidence != held-out; (2) MAC-as-theta null again; (3) Beck = per-point amplitude champion (CRPS-skill -0.78->-0.34) but under-covers net-CG bands; (4) delivered twin = inherited FEM + F(k) (reaffirms netcg).", 5, False],
 ["plate_test_rehearsal_20260701", "Would the proposed 12-sensor >200 Hz plate test really buy the promised 5.4x->3.5x normal-band reduction?", "SYNTHETIC rehearsal (on the real ShockSat FEM)",
  "Pre-registered promise FALSIFIED (6.2x, no buy-down): theta posterior rotates near-degenerate 246-258 Hz eigenvectors; pinning ALL 12 cluster modes recovers 2.81x -> revised test scope. Checker RED = claim-falsified tier, pipeline intact.", 4, False],
 ["shocksat_netcg_method_selection_20260701", "Which uncertainty formulation should deliver the net-CG force twin (coverage first, then sharpness)?", "REAL ShockSat (5 drives, 122880-pt caches)",
  "Checker GREEN 22/0/0. Winner statFEM F(k): shear 1.51x/2.30x FEM+6dB held-out-drive validated; normal 2.53x covering (data-starved); theta-only disqualified by leave-modes-out (widen=1.00); FEM+6dB incumbent UNDER-covers; discrepancy ~0.9 log-amp but point-wise -> averages out at 1-oct.", 5, False],
 ["project_status_deck_20260701", "Consolidation: project status deck (19 slides)", "n/a (consolidation)",
  "Arc wall->defect->pivot->net-CG delivery; all figures provenance-labeled copies.", 2, True],
 ["shocksat_bilionis_review_20260626", "Consolidation: what is real, what is the wall, what is publishable (Bilionis review)", "n/a (consolidation)",
  "Pinned numbers: FRF corr 0.27-0.34 vs MAC 0.63; CIs ~6x; remesh plateau 0.38; 3 publishable candidates named.", 3, True],
 ["shocksat_psd_envelope_twin_20260623", "Can remodeling+Bayes crack per-point FRF amplitude (PSD-envelope twin)?", "REAL ShockSat (+X hammer, 84 ch)",
  "Three-metric legitimacy ladder: blind 0.27 / held-out-sensor CV 0.44 / oracle 0.70 -> the wall holds at every legitimacy level; remesh helps CV (+0.12) but nothing reaches usable ~0.7; freq-likelihood objective mismatch costs only ~0.03.", 4, False],
 ["shocksat_sequential_statfem_20260623", "Does a sequential (filtering) statFEM update improve the PSD-envelope score?", "REAL ShockSat (4 drives)",
  "Honest negative: best variant GRMS ratio 2.07 vs FEM+6dB, clean-win 18.8%; small-subset NUTS converged.", 2, False],
 ["shocksat_latent_force_damping_20260623", "Do time-domain latent-force residuals reveal damping/model-form structure?", "REAL ShockSat (time histories)",
  "Diagnostic packet on 4 references x 6 hits; residual structure documented; no green improvement claimed.", 2, False],
 ["shocksat_new_papers_review_20260623", "Which of 3 new papers is most applicable to the ShockSat state?", "n/a (review)",
  "Sequential statFEM ranked HIGH (became a runner); latent-force+BNN MODERATE-HIGH; wing-DT MODERATE-LOW.", 2, False],
 ["shocksat_multiref_explore_20260623", "Exploration of multi-reference caches (scratch)", "REAL ShockSat", "Exploratory only; fed the multiref threads.", 1, False],
 ["shocksat_multiref_amplitude_20260622", "Does MULTI-REFERENCE hammer data rescue held-out per-channel amplitude skill?", "REAL ShockSat (4 drives)",
  "NO (two-level why): amplitude skill stays below climatology; shape/participation error dominates, more drives add frequency info not shape.", 3, False],
 ["mpl_twin_iteration_20260620", "Iterate the MPL stand twin against scrappy modal data (deterministic first)", "REAL MPL stand (scrappy taps + LDV-era CSVs)",
  "Rev1-9: pseudo-FRF <1% peak match 50-90 Hz; deterministic tuning 6.13->2.21% median but hits an 11.4 Hz MODEL-FORM floor and tries to breach physical priors = the exact overfit Bayesian robustness guards against (good motivation artifact).", 3, True],
 ["shocksat_modelclass_L5_20260619", "Where does model updating have VALUE (freq vs amplitude), and which model class wins?", "REAL ShockSat + .ash survey",
  "Freq value real (halves FEM freq error, +0.93 CRPS-skill); per-channel amplitude negative skill; Beck shape-field = only amplitude lever (-0.68->-0.25); MAC-in-likelihood null; evidence machinery built (freq-only crowns as-received M0 P=0.906).", 4, True],
 ["shocksat_richmodel_L5_20260619", "Are richer (per-PID split) stiffness parameterizations identifiable/evidence-favored?", "REAL ShockSat",
  "Strain-energy + FIM: richer splits store energy but params do not separate; evidence Ockham-penalizes them (supports 9-group class).", 2, False],
 ["ift_real_validation_20260619", "IFT (physics-in-prior, learned temperature) vs statFEM free discrepancy on REAL data?", "REAL ShockSat (whole-FRF observable)",
  "IFT TMCMC-converges + covers (beta bounded, 246x below beta*) where M2 free-sigma_d DIVERGES (R-hat 63-129) on the same observable; IFT not sharper than L5 (coarse-FEM ceiling). Bounded-regularizer win, not prior-vs-likelihood.", 4, False],
 ["ift_real_validation_20260619_codex", "Codex variant/review of the IFT study (+deck)", "REAL ShockSat", "Cross-agent replication/review of the IFT thread.", 2, True],
 ["shocksat_fem_remesh_20260618", "Can an agent contribute by re-meshing/remodeling where data says the FEM is wrong (Card D)?", "REAL ShockSat + .ash survey",
  "Auditable negative: 0/10 clean improvements; region diagnosis (dish/impact-face/strut-base = true levers, joints already finite+non-identifiable); BOTH historic metric traps discovered here (per-mode amp fitting +0.083; re-pairing churn +0.010).", 3, False],
 ["statfem_pift_collapse_20260617", "Why/when does PIFT collapse (temperature/discrepancy interplay)?", "SYNTHETIC first, then real matched-path",
  "Supporting study for the IFT thread; documents the collapse mechanism and the bounded-temperature cure.", 2, False],
 ["statfem_real_validation_20260617", "Validate a statFEM twin on the REAL ShockSat: identifiability, coverage, gaps (Card A)", "REAL ShockSat",
  "4/9 groups identifiable; 7 channels consistently miss the 95% band (genuine model-form, SNR-uncorrelated); joints-scaling fails to fix amplitude; discrepancy floor quantified -> seeded every later thread.", 4, True],
 ["confidently_wrong_modelform_20260616", "Can a statFEM twin be confidently wrong under model-form error (Bilionis concern)?", "FRF testbed w/ injected model-form error (SYNTHETIC truth)",
  "Naive no-discrepancy arm is confidently wrong; discrepancy arms widen to cover; motivates coverage-first selection gates.", 3, True],
 ["statfem_consistency_toy_20260616", "Does the arbitrary residual-noise knob make Bayes inconsistent (Bilionis/Alberts concern)?", "SYNTHETIC toy",
  "M-lik drifts with arbitrary sigma_r (theta spread 0.084); statFEM(sigma_d) and IFT(beta) remove the knob and are mesh-invariant; NONE recovers theta under model error (shared honest limit).", 4, True],
 ["statfem_shocksat_eval_20260616", "First held-out-QOI statFEM evaluation on ShockSat", "REAL ShockSat",
  "Early eval sweep (~2-3 hr NUTS); superseded by statfem_real_validation.", 2, True],
 ["paper_virtual_sensing_uq_toy_20260613", "Is virtual-sensing target credibility testable (paper review + toys)?", "SYNTHETIC toys",
  "4 experiments; YELLOW 41/2/0; honest-scope flags; supporting material.", 2, False],
 ["papers_statfem_studies_20260612", "Integrate Schneider/Das-Debnath/Yan on ONE replayable real testbed (13 studies)", "REAL suspended-panel LDV",
  "Schneider correlated-FRF discrepancy: 100% in-distribution held-out coverage + ~7x tighter bands where iid FAILS to converge (R-hat 24); iid non-convergence CAUSED by model-form error (control converges); real panel discrepancy measured.", 4, True],
 ["amplitude_dependent_damping_scan_20260612", "Do existing datasets show amplitude-dependent damping/hysteresis?", "REAL (MPL + ShockSat + panel)",
  "MPL weak response-only signs; ShockSat/panel inconclusive (no amplitude sweep) -> motivates purpose-built sweep.", 2, False],
 ["forcing_marginalized_damping_toy_20260612", "Can response-ratio observables cancel unknown forcing and detect amplitude-dependent damping?", "SYNTHETIC 3-DOF",
  "Force cancellation exact (4e-16); NUTS converged; detects high-amplitude damping (P=0.996), covers 6/6; biased equivalent damping documented.", 3, False],
 ["notch_lit_review_20260612", "Where is the open contribution in notching/force-limiting literature?", "n/a (review)",
  "Crowded field; likely-open = sparse 6-DOF empirical/Bayesian limit workflow.", 2, False],
 ["buffet_dome_secondary_20260612", "Representative buffet twin: what loads reach a secondary structure (public data)?", "SYNTHETIC (public-data FEM + Corcos buffet)",
  "58k-DOF fine region; tray punch CI 18/40/87 N; boundary bracketed BC-A/BC-B (6-10%).", 2, False],
 ["notch_multipoint_7004c_20260611", "Is single-point 7004C force-limiting blind to multi-point/6-DOF effects?", "SYNTHETIC/analytic",
  "Single-point blind to rocking (net Fz=0 while feet load); distributed feet = hidden overtest; measured-impedance method replaces coupled FEM exactly (1.8e-12).", 3, True],
 ["mpl_stand_fem_rebuild_20260611", "Parametric K(theta) twin of the MPL stand from the Femap deck", "REAL geometry (no test data yet)",
  "Parse-backed rebuild; mode 1 set by fan-box-on-shield; box mass = #1 data ask. No sampler.", 2, False],
 ["shocksat_tray_coupled_qoi_20260610", "Does calibrating the primary help a coupled tray/CG interface-load QOI?", "REAL ShockSat FEM (QOI study)",
  "Mount-dominated: calibrated primary buys ~nothing if mount unconstrained; VOI = structured honest negative; 14-slide program deck.", 3, True],
 ["statfem_freq_blog_20260610", "Replicate-and-extend Girolami statFEM across 3 agent models (blog experiment)", "SYNTHETIC (Girolami replicate)",
  "Anti-cheat held -> failure became honest under-ambition; 'the critic is the product' (challenger pass caught what authors+gates missed).", 3, False],
 ["shocksat_opus_20260609", "First end-to-end ShockSat continuation run (Opus)", "REAL ShockSat",
  "Early pipeline; superseded by the modal-twin + validation threads.", 1, False],
 ["shocksat_fem_modal_twin_20260609", "From-scratch assembly of the 406k-DOF ShockSat FEM + NUTS modal calibration", "REAL ShockSat free-free modes",
  "Full 18-mode posterior converges (R-hat 1.022); ~4/9 groups identifiable; held-out freq coverage good; the foundational matrices every later thread reuses.", 3, False],
 ["shocksat_statfem_runner_20260609", "Ingest the Test07 impact-hammer archive", "REAL ShockSat raw archive",
  "4 hits averaged; low coherence + grid-convention mismatch documented as honest blockers.", 1, False],
 ["fim_identifiability_opus_20260609", "How many parameters can a scrappy modal test support (pre-test FIM)?", "SYNTHETIC (tray FEM)",
  "Answer: 3 (band-conditional 1->2->3); joints unidentifiable; QOI in the identifiable subspace; sensor/tap placement given. Checker GREEN 15/15.", 3, False],
 ["modeling_freedom_experiment_20260609", "Does modeling freedom invite overfit that gates miss (hidden vault)?", "SYNTHETIC + ShockSat half",
  "Hidden vault caught a gate-passing flexible-model overfit (dev rank != vault rank); ShockSat half hollow = lead-setup lesson.", 3, False],
 ["conical_shell_statfem_ladder_20260608", "Public conical-shell statFEM ladder (sandbox)", "Public FEM modes (no test data)",
  "Modal-only statFEM v1; held-out mode 4 covered; provenance-vs-validation distinction.", 2, False],
 ["fem_phase1_review_20260608", "Review of 3-agent FEM builders (hexapod tray)", "SYNTHETIC", "Cross-agent FEM builds + reviewer/framing passes.", 1, False],
 ["fem_phase1_framing_challenge_20260608", "Framing challenge for FEM phase 1", "n/a", "Framing scaffolding.", 1, False],
 ["agentic_verification_harness_20260608", "What does an agentic verification harness need?", "n/a (methods)",
  "Verification-harness study; fed the Engineering Harness Gates.", 2, False],
 ["blind_round3_stage3_review_20260605", "Blind truth/inference review (round 3 stage 3)", "SYNTHETIC (blind)",
  "Blind split worked; same-space discrepancy confounds; net-CG quantity contract pinned here.", 2, False],
 ["blind_round3_review_20260604", "Blind round-3 review", "SYNTHETIC (blind)", "Review scaffolding for the blind protocol.", 1, False],
 ["stage3_framing_challenge_20260605", "Stage-3 framing challenge", "n/a", "Framing scaffolding.", 1, False],
 ["tmcmc_2dof_identifiability_review_20260605", "TMCMC 2DOF identifiability review", "SYNTHETIC 2DOF", "Identifiability review notes.", 1, False],
 ["context_compaction_lit_review_20260604", "How should agents survive context compaction?", "n/a (review)",
  "Informed the CLAUDE.md/AGENTS.md continuity + re-grounding rules.", 2, False],
 ["mdof_femagent_scoping_20260603", "Scoping reduced-order MDOF transfer functions for agents", "SYNTHETIC", "Scoping notes.", 1, False],
 ["framing_challenge_20260603", "Early framing challenge", "n/a", "Framing scaffolding.", 1, False],
 ["runner_comparison_round2_20260603", "Cross-tool comparison round 2 (Claude/Codex/Cursor)", "SYNTHETIC",
  "Codex round-2 NUTS passed strict all-variable convergence; some arms honestly labeled HMC-not-NUTS = cross-tool sampler-compliance evidence.", 2, False],
 ["runner_comparison_20260602", "Cross-tool comparison round 1", "SYNTHETIC", "First 3-tool comparison.", 2, False],
 ["runner_claude_opus48_20260602", "Sequential twin runner (Claude, r1)", "SYNTHETIC", "Individual runner artifact.", 1, False],
 ["runner_claude_opus48_round2_20260602", "Sequential twin runner (Claude, r2)", "SYNTHETIC", "Individual runner artifact.", 1, False],
 ["runner_codex_gpt55_20260602", "Sequential twin runner (Codex, r1)", "SYNTHETIC", "Individual runner artifact.", 1, False],
 ["runner_codex_gpt55_round2_20260602", "Sequential twin runner (Codex, r2)", "SYNTHETIC", "NUTS strict pass artifact.", 1, False],
 ["runner_cursor_composer25_20260602", "Sequential twin runner (Cursor, r1)", "SYNTHETIC", "Individual runner artifact.", 1, False],
 ["runner_cursor_composer25_round2_20260602", "Sequential twin runner (Cursor, r2)", "SYNTHETIC", "Individual runner artifact.", 1, False],
 ["multi_agent_first_loop_20260602", "First lead/helper multi-agent loop", "SYNTHETIC 2DOF", "Scaffold proven; helper-task packet pattern set.", 1, False],
 ["sequential_vibe_modal_flight_20260602", "Staged vibe/modal/flight twin setup", "SYNTHETIC", "Setup only; NUTS not active.", 1, False],
 ["fresh_2dof_statfem_fbs_20260601", "Question-first 2DOF statFEM/FBS rerun", "SYNTHETIC 2DOF",
  "QOI=3xGRMS tray PSD; 7004C benchmarks; generated many reusable review gates.", 2, False],
 ["gp_error_exploration", "GP error exploration (scratch)", "SYNTHETIC", "Scratch exploration.", 1, False],
 ["sensitivity_assumptions", "Sensitivity/assumptions scratch", "n/a", "Scratch notes.", 1, False],
 ["figures", "Shared figures folder (aux)", "n/a", "Aux asset folder, not an experiment.", 1, False],
]


def main():
    csv_path = HERE / "experiment_catalog.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for row in R:
            w.writerow(row[:4] + [row[4], "TRUE" if row[5] else "FALSE"])
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        wb = openpyxl.Workbook(); ws = wb.active; ws.title = "experiments"
        ws.append(COLS)
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1F4E79")
            c.alignment = Alignment(wrap_text=True, vertical="top")
        for row in R:
            ws.append(row[:5] + ["☑" if row[5] else "☐"])
        widths = [38, 46, 30, 80, 12, 9]
        for i, wdt in enumerate(widths, 1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = wdt
        for r in ws.iter_rows(min_row=2):
            for c in r:
                c.alignment = Alignment(wrap_text=True, vertical="top")
            r[4].alignment = Alignment(horizontal="center", vertical="top")
            r[5].alignment = Alignment(horizontal="center", vertical="top")
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = f"A1:F{len(R)+1}"
        wb.save(HERE / "experiment_catalog.xlsx")
        print("wrote experiment_catalog.xlsx")
    except ImportError:
        print("openpyxl missing; csv only")
    print(f"wrote {csv_path} ({len(R)} rows)")


if __name__ == "__main__":
    main()
