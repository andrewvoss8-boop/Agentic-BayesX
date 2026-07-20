# Runner Prompt — ShockSat net-CG force: method-selection bake-off & delivery (autonomous)

Status: READY TO DISPATCH (Andrew approved, 2026-07-01). Written by the lead agent for a FRESH runner agent.
Mode: **run autonomously through Stage 0 → Stage 3 without stopping for human approval.** Do not pause for sign-off
between stages. Only HALT if you hit a true blocker (missing data you cannot regenerate, an integrity violation you
cannot avoid, or a durable-rule change would be required) — and then write the blocker to `decisions_log.md` and stop.

---

## 0. FIRST ACT — re-ground before doing anything (do not skip)
You start cold. The file system + git are the source of truth. Read, in order, and restate goal/last-decision/next-
action/open-ambiguities in ONE line before acting:
1. `AGENTS.md` (project root) — the CANONICAL rules and EVERY gate. If anything below conflicts with it, AGENTS.md wins.
2. `CLAUDE.md` — lead/communication/memory rules.
3. `notes/project_vision.md` §4 (QOI fact), §6.1 (robustness-first), §7.1 (the width wall).
4. `notes/memory.md` CURRENT STATE block (the 2026-07-01 delivery-target + method-selection design decisions).
5. `notes/reset_prompt_2026-07-01.md` (§3 research questions RQ2/RQ3/RQ4, §5 experiment matrix, §9 guardrails).
6. This prompt in full.

**Non-negotiables (survive even if you skip a file):** NUTS/HMC is the default sampler and "converged" requires the
all-variable R-hat/ESS/divergence gate, not just that a sampler ran. Held-out is the ONLY trust arbiter; never rank on
in-sample. One unified candidate pool per comparison. Never fabricate plots/metrics, never present reference assets as
generated outputs, never swap methods without labeling. Label every result GREEN/YELLOW/RED per the checker, never
stronger than the checker output. Record non-obvious decisions in `decisions_log.md` BEFORE acting on them.

---

## 1. THE ENGINEERING DECISION (Question & Decision Gate)
An aerospace partner hands us an **inherited (vendor-correlated) ShockSat FEM + a modal-hammer test set**. They want
the **net-CG FORCE on the top tray/plate**, in BOTH directions, with trustworthy uncertainty bands, under a known input:
- **QOI-shear** = in-plane (X and/or Y) net-CG force on the tray. HIGH trust (driven by MEASURED global modes ~114-169 Hz).
- **QOI-normal** = out-of-plane (Z, drumhead) net-CG force on the tray. LOW trust (driven by UNMEASURED plate modes ~234-254 Hz).

**Objective / success metric.** Pick, PER QOI, the ONE updating method (from the array below) that best satisfies the
two-part selection rule (§4), then hand back the shear and normal net-CG force predictions with bands and a trust label.
**What the search may choose:** the updating formulation, the remesh candidate, the parameter/pooling set.
**What stays human judgment:** the input-PSD assumption, the acceptable band width for certification, and whether the
normal-QOI band is delivered as a usable screening bound or flagged "needs new data."
**What would make this the wrong question:** if the partner needs a LOCAL mount response (not the NET tray force) — that
is the ~14.6× wall with no statistical rescue; say so and stop chasing sharpness there.

### Andrew's BINDING design requirement (the heart of the selection rule)
The selected method MUST be **robust to QOIs driven by modes outside its optimal range**: it must NOT get "sucked into"
falsely sharpening the unmeasured-mode-driven (normal) QOI by overfitting the data-rich measured band, and it MUST
communicate the TRUE (wide) uncertainty there. Overconfidence on the normal QOI is a DISQUALIFIER, not a minor demerit.

---

## 2. QUANTITY CONTRACT (do this before plotting/fitting/scoring — Quantity Contract Gate)
- **Quantity:** net-CG force = Σ over the tray's mass the mass-weighted acceleration (equivalently the interface base
  reaction), band-limited. Numerator = force [N or lbf-consistent]; per-frequency form = net-CG force PSD
  `S_F_qoi(ω) = |G(ω)|² · S_input`, where `G(ω)` is the modal-sum transfer to the net-CG force functional and
  `S_input` is the known flat input PSD. Also report the integrated band-RMS (GRMS-force) over 20–2000 Hz.
- **Excitation:** 100%-CERTAIN FLAT input PSD applied at the hammer-impact drive point. **Examine ALL FIVE drive points**
  (+X/Test01, +Z/Test02, +XY/Test04, +Z@900/Test06, and **+Y/Test03/990y — NOW DOWNLOADED 2026-07-01**); the delivery
  prediction is per-drive, and the other drives supply the held-out-DRIVE answer key. +Y is the main observability lever
  for the low-trust NORMAL load (base_shear_Y was the weakest QOI) — verify what higher modes it actually excites/measures.
- **Coordinate / component:** tray-CG translational X, Y (shear) and Z (normal), reported SEPARATELY. Never blend.
- **Units / expected behavior:** state units explicitly; expect resonance peaks at the QOI-driving modes and roll-off
  away from them. Confirm the net-CG functional passes a limiting sanity check (rigid-body / static limit).
- Name both nearby conventions (net interface FORCE vs net-CG ACCELERATION/GRMS) and state you use net-CG FORCE.

---

## 3. THE EXPERIMENT MATRIX (reset §5 — ONE unified candidate pool, ONE harness)
`{remesh} × {parameter/pooling} × {formulation} × {QOI target} × {scoring regime}`

**Axis A — updating formulation (the array of options to choose among):**
0. `baseline_fem` — as-received FEM θ=1 (the bar to beat) AND `fem+6dB` (the incumbent aerospace band).
1. `L5_freq` — modal-frequency-only likelihood (reuse `modal_feature.py`, proven-converged NUTS).
2. `freq_mac` — frequency + MAC (shape-weighted).
3. `feature_space` — per-mode "peak at f0 ± X%, amplitude Y ± Z dB" likelihood.
4. `beck_shapefield` — inferred shape-field (Beck/L8b).
5. `pooled_fullFRF` — smooth-residual full-FRF likelihood WITH hierarchical (partial-)pooling. (RQ3: does pooling rescue
   the otherwise non-identifiable full-FRF likelihood? Un-pooled full-FRF is known non-identifiable, NUTS R-hat 104 —
   do NOT run it un-pooled expecting convergence; the pooled version is the question.)
6. `statfem_Fk` — statFEM orthogonal output-space discrepancy F(k) (absorbs residual model error into a wider band).

**Axis B — remesh (REDESIGNED per Andrew 2026-07-01 — a digital twin has ONE mesh, and "best mesh" is COUPLED to
updating).** Do NOT crown a single mesh up front on a raw/pre-update FRF-correlation score — that is the known §1.1
ARTIFACT (metric-dependent: in-sample vs held-out vs blind each crown a different edit; the blind "best" was WORSE than
the untouched FEM) AND it is pre-update (Bayesian updating reshuffles the ranking). Instead:
1. **Screen** the ~50-edit pool (`correlate_all.py` / `guided_remesh.py`) on a cheap held-out proxy → keep the **top ~3
   candidate meshes** (a hedge; label the screen explicitly as an imperfect PROXY, not the selector).
2. **Carry those ~3 meshes as an axis THROUGH updating** = {`inherited`, `mesh_A`, `mesh_B`, `mesh_C`} — each mesh gets
   updated and scored on the SAME held-out-QOI objective (POST-update), exactly like every other config.
3. **Delivered twin = the single {mesh, formulation, pooling} combination that wins held-out QOI.** ONE mesh, chosen
   post-update, on the real objective — never a pre-update proxy.
One twin serves BOTH loads: rank meshes primarily on the load a mesh can actually move (SHEAR — its modes are measured),
but CHECK the winning mesh does not degrade NORMAL, and REPORT the trade if it does (that trade is itself a finding).

**Axis C — parameter/pooling:** {`fixed_groups` (9-group set), `fim_downselect` (~3 identifiable, per the FIM/strain-
energy analysis), `hier_pooled`}.

**Axis D — QOI target:** {`shear`, `normal`} — scored and reported separately.

**Axis E — scoring regime (label each; NEVER conflate):** `blind` (no amplitude fit) → `sensor_infill_cv` (fit on
measured sensors, predict held-out sensors) → `heldout_drive` (fit on 4 drives, predict the 5th) → `heldout_qoi`
(the net-CG force answer key) → `leave_modes_out` (the humility test, §5).

**SWEEP BROADLY (Andrew 2026-07-01 — no hard count cap).** A wide sweep is informative and its results become the
baseline we test for generalization on OTHER articles (reset RQ5) — that cross-article test, not this single held-out
set, is the real out-of-sample check. So run the full matrix if compute allows. BUT protect the ONE decision the
held-out data must certify, so the sweep stays honest (this does NOT limit how much you sweep):
- **Winner's-curse honesty.** Selecting the best of MANY configs against ONE held-out answer key inflates the champion's
  score (multiple comparisons). Report the FULL scorecard and state N (how many configs competed); read the winner as
  "best of N," never as "expected performance."
- **Use-once final fold.** Reserve ONE drive direction (or a sensor set) used ONLY to confirm the crowned winner — never
  in screening or selection. If the winner's skill holds there = real; if it collapses = artifact caught. Report both.
- **Stage-0 still prunes the WASTEFUL combos** (frequency-only formulations skip amplitude-pooling; a QOI that Stage 0
  says can't discriminate does not get a full grid). Prune the pointless, not the informative.

---

## 4. THE METRIC & SELECTION RULE (Andrew-confirmed)
For each QOI, each method, each scoring regime, compute on the net-CG force spectrum:
- **Coverage (1-octave-smoothed).** Smooth BOTH the twin's 95% band and the held-out-data-reconstructed QOI on 1-OCTAVE
  log-spaced bands, then check the band envelopes the smoothed held-out data. **Narrow exceedances are TOLERATED** —
  report them as energy-weighted positive dB-exceedance (a small poke where the spectrum is already low is negligible);
  require envelope everywhere else. (This is the smoothline/envelope metric from `shocksat_psd_envelope_twin_20260623`
  at 1-octave; reuse and adapt that machinery. State window/spacing in the discretization ledger.)
- **Sharpness.** Band width (e.g. 95%-band GRMS-force ratio vs the FEM+6 dB incumbent, and interval width).
- **Point error.** Median/GRMS error of the mean prediction vs the reconstructed QOI.

**Two-part selection rule, PER QOI:**
1. **Coverage is a HARD GATE.** A method that fails 1-octave-smoothed coverage (beyond the tolerated narrow-exceedance
   allowance) OR that is overconfident on the `leave_modes_out` test is DISQUALIFIED for that QOI — no matter how sharp.
2. **Among methods that cover, prefer the SHARPEST** (then lowest point error). This is where shear earns a tight number
   and normal honestly stays wide.

Report the full scorecard; never hide a disqualified-but-sharp method — its overconfidence IS a result.

### QOI weighting — bias effort to the frequencies & sensors that matter
- **Frequencies:** compute each QOI's modal-participation weight (which modes drive shear vs normal — the Modal
  Identifiability Gate / strain-energy view). Weight the likelihood/residual and the scoring by that participation so a
  method is judged on getting the QOI-driving modes right, not the whole FRF equally.
- **Sensors:** weight each sensor by its contribution to the net-CG functional; do sensor-infill CV on QOI-relevant
  sensors. Reuse the `strut_force_qoi_pilot.py` template (QOI → modal sensitivity → re-grade).

---

## 5. THE LEAVE-MODES-OUT HUMILITY TEST (the unlock for the low-trust QOI)
We cannot measure the drumhead-driven normal-force truth, so we cannot validate the normal NUMBER — but we CAN validate
the uncertainty MACHINERY with a controlled test that HAS a known answer:
- Take modes we DID measure. Deliberately HIDE a subset (treat them as "unmeasured": drop their measured freq/shape/
  amplitude, fall back to prior). Recompute the method's net-CG force band.
- **Known correct answer:** the band MUST WIDEN to cover the contribution of the now-hidden modes. Quantify the required
  widening (the hidden modes' QOI participation) and check the method's band actually grows to include the full-data
  truth. A method that stays narrow (still "confident" without the hidden modes) FAILS the humility test → disqualified.
- Run this for both QOIs. It is the honest analogue of the real unmeasured-drumhead-mode situation and predicts which
  methods degrade gracefully (feature-space / hier-pooled / structured-statFEM) vs which falsely sharpen (free-amplitude
  full-FRF). Reporting that prediction confirmed/refuted is a first-class deliverable (RQ3).

---

## 6. STAGED PLAN — run straight through (autonomy rules baked in)

### Stage 0 — QOI sensitivity + VALIDITY GATE + MESH SCREEN (cheap, NO NUTS; the reset's "validity before rigor")
- Compute per-QOI mode weights and sensor weights (§4). Reuse `qoi_trust_table.py` / `strut_force_qoi_pilot.py`.
- **Re-run the trust table WITH +Y (Test03) folded in** — quantify whether +Y lifts the NORMAL/base_shear_Y trust and
  whether it gives any real observability of the ~234-254 Hz modes (it may raise normal from "extrapolation-only").
- **Sensitivity sweep on the assumed unmeasured-mode σ** (`SD_F_U`, `SD_A_U` in `qoi_trust_table.py` are hand-chosen:
  ±6% / 0.80). Vary each up/down ~2× and report how the normal-QOI band factor (the ~14.6×) and coverage move. This
  bounds how load-bearing those assumptions are (they must be surfaced with a sensitivity result per the guardrails).
- **MESH SCREEN (Axis B step 1).** Score the ~50-edit pool on a cheap held-out proxy; keep the **top ~3 candidate meshes**
  as the mesh axis for Stage 2. Label the screen EXPLICITLY as an imperfect proxy (it does NOT select the twin — the
  post-update held-out-QOI bake-off does). Record the screen ranking + the 3 kept meshes in `decisions_log.md`.
- **Validity gate, PER QOI:** "does held-out data exist that can DISCRIMINATE methods for this QOI?" Expected:
  shear = PASS (driving modes measured across drives); normal = likely DATA-STARVED for the number (re-check after +Y)
  but PASS for the `leave_modes_out` mechanism test. Write the verdict per QOI to `decisions_log.md`.
- **Autonomy rule:** if a QOI's number is data-starved (normal, even after +Y), do NOT stop — record that its deliverable
  is a covering band + a "next test dollar" recommendation (>200 Hz plate test), and CONTINUE. Only the `leave_modes_out`
  mechanism must pass to keep that QOI in the bake-off.

### Stage 1 — build the ONE held-out harness + immutable checker
- Define the net-CG force functional, the answer-key reconstruction (from held-out sensors / held-out drive), and the
  three scores (coverage 1-oct, sharpness, point). One harness used by ALL methods.
- Write `check.py` and SHA-LOCK it (record its SHA in the workspace; do not modify it after locking during the run).
- The checker exits non-zero ONLY on RED (integrity violation, missing artifact, claim stronger than evidence, undocumented
  gate miss); documented YELLOW findings do not abort replay.

### Stage 2 — the bake-off (NUTS; sweep broadly, prune only the wasteful)
- Run Axis-A methods × {inherited + the ~3 screened meshes} × {pooling} on the QOIs, QOI-weighted, on `heldout_drive`
  (fit on 4 drives, predict the 5th — now 5 drives with +Y) + `sensor_infill_cv` + `leave_modes_out`. Each mesh is
  UPDATED and scored on held-out QOI here (post-update) — the mesh is NOT pre-crowned. The delivered twin's mesh is
  whichever {mesh,formulation,pooling} wins held-out QOI. NUTS/HMC default; ≥4 chains; non-centered for hierarchical
  variance; report
  R-hat + ESS over ALL sampled variables (incl. raw latents) + divergence fraction. Non-converged = YELLOW, label the
  worst-case R-hat/ESS next to any interval, NEVER call it "NUTS active".
- **Compute (Detached-launch gate):** any NUTS/eigensolve/sweep expected to exceed the tool timeout MUST be launched
  detached (`nohup … > logs/x.log 2>&1 & disown`) and monitored with short until-loops; make jobs RESUMABLE (write
  partial results, skip finished work on relaunch). Pin `OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1` for small dense
  eigh/posterior math. float64 only. Follow `docs/compute_protocol.md`.
- **Autonomy rule:** if a method fails to converge after a reasonable retry (more warmup/chains, non-centered, tighter
  step), record it YELLOW-non-converged and MOVE ON — do not stall the whole run on one formulation.

### Stage 3 — pick + deliver
- Apply the two-part selection rule per QOI → name the winning method for shear and for normal.
- Produce the delivery: shear net-CG force prediction + band (expect sharp, trusted); normal net-CG force covering band
  + trust label + the "one test that fixes it" recommendation. Include the QOI trust map.
- Assemble the human-review packet (§8).

---

## 7. GATES YOU MUST SATISFY (from AGENTS.md — do not skip)
- **Priority Deliverables & Clarification Gate:** write `priority_deliverables.md` (each priority ask → interpretation →
  where delivered). A priority with no artifact = failure.
- **Assumptions & Uncertainty Gate:** `assumptions_ledger.md` with values/units/rationale/source/sensitivity-priority
  for: input PSD (flat, level), σ_d/discrepancy, priors, damping ζ, boundary conditions, the assumed unmeasured-mode σ,
  data counts (single-hit vs multi-hit; # drives; # sensors). Distinguish parameter / observation-noise / model-
  discrepancy / forcing / QOI uncertainty. Show assumptions graphically where possible.
- **Modal / Eigenproblem Identifiability Gate:** report the parameter→mode strain-energy fractions AND, for any per-
  parameter identifiability claim, the FIM eigen-decomposition at the realized discrepancy floor. Tie every "identifiable
  / not" claim to physical mechanism + a finite-perturbation check.
- **Reference & Standards Gate:** compare against NASA-HDBK-7004C (apparent-mass / net-CG force convention) and the
  ShockSat vendor correlation report where relevant; document alignment or why not applicable.
- **Plot & Human-Review Gate:** BEFORE any figure, read `.claude/skills/tufte-data-graphics/SKILL.md` and run
  `scripts/tufte_lint.py` on each saved `.py` plotting script (no inline heredoc plots). Log-frequency axes for FRF/PSD;
  state linear/dB explicitly; every data figure names its run/dataset and flags invalidity (non-converged → print worst
  R-hat/ESS on the figure). Include a run-specific graphical-model/likelihood diagram; do not copy a paper figure.
- **Sensitivity Gate:** vary the assumptions most likely to change the decision (input-PSD shape, σ_d, the unmeasured-
  mode σ, prior widths); separate synthetic / posterior / decision sensitivity; report where conclusions are fragile.
- **Discretization Resolution Gate:** document the frequency grid (range/spacing/log), the 1-octave smoothing window, and
  show the QOI-driving peaks are resolved; give a resolution sensitivity result.
- **Verification Gate:** checker-backed acceptance for every artifact; check units/axes/duplicate-channels/convention/
  limiting behavior/image legibility; state the likelihood's data-usage (whole-FRF vs feature vs band) explicitly.
- **Runtime Accounting Gate:** `runtime.json` with `active_runtime_s` and `elapsed_wallclock_s`.
- **Done Criteria:** artifacts exist; checks pass; assumptions/limits documented; one-command replay (`run_all.sh`);
  references checked/ruled-out; sensitivity run; packet exposes enough numeric+graphical evidence for a reviewer to find
  mistakes; update `docs/report/project_log.md` row with status copied straight from the checker (never stronger).

---

## 8. DELIVERABLES (in a NEW workspace `artifacts/reports/shocksat_netcg_method_selection_<YYYYMMDD>/`)
- `priority_deliverables.md`, `decisions_log.md`, `question_framing.md`, `quantity_contracts.md`, `assumptions_ledger.md`
- `code/` (all saved `.py`, Tufte-linted plotting scripts; REUSE from `shocksat_psd_envelope_twin_20260623/code/` and
  record reused-file SHAs in `REUSED_code.sha256`)
- `out/` (per-method per-QOI scorecards JSON; Stage-0 validity + sensitivity JSON)
- `figures/` (QOI mode/sensor-weight map; scorecard bake-off; leave-modes-out humility panel; shear delivery band;
  normal covering band + trust label; likelihood/graphical-model diagram)
- `check.py` (SHA-locked), `run_all.sh` (one-command replay, resumable), `runtime.json`
- `packet.md` (method summary near top: model form, likelihood equation, data counts, whole-vs-feature likelihood choice,
  inferred vs fixed vs non-inferred variables; then results, scorecard, honest GREEN/YELLOW/RED per checker)
- `findings.md` (the selected method per QOI; the two-problem delivery; the leave-modes-out prediction confirmed/refuted;
  the honest limits and the "next test dollar" recommendation)

---

## 9. DATA & MACHINERY INVENTORY (verify from files; do not assume)
- **Canonical multi-reference modal caches (HAVE):**
  `artifacts/reports/shocksat_psd_envelope_twin_20260623/data/multiref_modal/{m_xpos_990x, m_zpos_990z, m_xy_990xy,
  m_zpos_900z}.npz` — hit-averaged, band-limited per-channel H1 + coherence, 4 drive directions.
  **+ +Y/Test03/990y (DOWNLOADED 2026-07-01) = the 5th drive** — LOCATE it (Andrew fetched it; find/verify the raw or
  distilled file, distill it to the same cache format as the other four, and back up all caches before heavy work).
- **FEM:** `artifacts/reports/shocksat_fem_modal_twin_20260609/fem_model.npz`.
- **Reusable machinery (base = `shocksat_psd_envelope_twin_20260623/code/`):** `realfrf.py` (reduced-model loader
  `load_reduced`), `modal_feature.py` (L5 modal-frequency NUTS — proven converged), `score.py` (Winkler/CRPS/CRPS-skill/
  PIT/coverage), `qoi_trust_table.py` (per-QOI modal-trust + MC band), `shape_borrow_diag.py` (mode matching / shape
  borrow), `strut_force_qoi_pilot.py` (QOI → modal-sensitivity re-grade template), `heldout_qoi.py` (held-out-sensor QOI).
- **NOT downloaded (fetch ONLY if an experiment needs it — surface to Andrew first):** Test08/10 (+Z impact),
  Test_Data_Parametric (3.33 GB force-level). Back up the caches before heavy work.
- **Env:** py3.9, jax0.4.30 / numpyro0.19, scipy1.13 (per prior ShockSat runs). Verify before relying on it.

---

## 10. GUARDRAILS — what you may and may NOT do autonomously
- MAY: create/modify files ONLY inside your new workspace + append to your `decisions_log.md`; launch detached compute;
  reuse and adapt existing code (record SHAs); iterate through all four stages without asking.
- MUST NOT (STOP and write to `decisions_log.md` instead): change any durable rule (`AGENTS.md`, `CLAUDE.md`, sampler
  standard, convergence gate), modify a SHA-locked checker after locking, edit another workspace's files, edit
  `notes/*` or `docs/report/project_log.md` beyond appending your own project_log ROW at the end with checker-exact
  status, fetch large new data (Test03/08/10/Parametric) without surfacing, or claim a novelty/patent conclusion.
- HONESTY (cardinal): never fabricate a plot/metric; never present a reference asset as a generated output; never swap a
  method without labeling; never call a non-converged sampler "NUTS active"; a documented honest negative or a wide-but-
  covering band is a SUCCESS of the method, not a failure to hide. Convergence ≠ trust — the held-out + leave-modes-out
  gates decide. If you cannot do something honestly, say so and label it low-confidence.
- Keep `decisions_log.md` current BEFORE each risky step; the chat is a cache that can be lost.

## 11. THE ONE-LINE ANSWER YOU ARE BUILDING TOWARD
"For the inherited ShockSat FEM + modal test, method **M_shear** gives a SHARP, held-out-validated net-CG SHEAR force
band; method **M_normal** gives an HONEST, wide-but-covering net-CG NORMAL force band that we PROVED (leave-modes-out)
does not falsely sharpen — and closing the normal band needs [specific >200 Hz plate test]. Here is the per-QOI trust
map." Deliver that, backed by the checker — nothing stronger.
