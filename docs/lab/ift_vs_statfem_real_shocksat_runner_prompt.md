# Runner prompt — IFT (physics-in-prior) vs StatFEM on the REAL ShockSat held-out data (apples-to-apples)

Status: DRAFT runner prompt (lead-authored 2026-06-19). Bounded comparison study + honest deck.
Workspace to create: `artifacts/reports/ift_real_validation_20260619/`.
Advisor objective (Ilias Bilionis): a faithful IFT arm, scored on the SAME real data / forward model /
held-out protocol / proper scores as our StatFEM twin. Honest negatives are valid, valuable results.

---

## 0. Re-grounding (do FIRST, before any code)
Read, in order: `AGENTS.md`; this prompt; `notes/memory.md` CURRENT STATE; the StatFEM run we are comparing
against — `artifacts/reports/statfem_real_validation_20260617/packet.md` (esp. §1 method, §2 verdict, §6
held-out QOI, §3 whole-FRF arms) and its `phase2_heldout_sensor_qoi_summary.md`; the IFT reference build
`artifacts/reports/statfem_consistency_toy_20260616/` (the `M-ift` construction in `code/nuts_marg.py`, and its
packet §2/§5 verdict on M-ift). Then write `decisions_log.md` in the new workspace: goal / last decision /
next action / open ambiguities. Re-ground again after any compaction.

## 1. Goal and the apples-to-apples CONTRACT (do not break any of these)
Run an end-to-end **IFT** twin — physics in the PRIOR with a learned inverse-temperature β, as laid out in
**Hao & Bilionis 2024 (arXiv:2306.02150)** and **Alberts & Bilionis 2023 (arXiv:2301.07609)** — and compare it
**apples-to-apples** against our StatFEM twin on the **real ShockSat held-out-sensor QOI**. "Apples-to-apples"
means the IFT arm and the StatFEM arms differ ONLY in WHERE the physics/trust lives; EVERYTHING else is byte-
identical and reused, NOT reimplemented:
- **Same data:** the real single-impact FRF |H₁(ω)| (hit-001, band 45–260 Hz, 173 lines), same bad-channel
  exclusions (ch101, ch29–31), same 80 dynamic-range-eligible mapped channels. Reuse the StatFEM run's
  `data/*.npz`, `channel_map.csv`, `keep_dofs.npy`, `groups.json`.
- **Same forward model:** the reduced dynamic-stiffness accelerance `core.frf_np` / `core.jax_forward_factory`
  (74-dim, M=I, K(θ)=A_fix+Σθ_gA_g, η=2ζ, ζ=0.01, units-gain c). Reuse `core.py` unchanged.
- **Same held-out protocol:** channel split, obs_frac 0.6, **≥25 random splits** (reuse `mc_heldout.py`'s split
  logic and `heldout_qoi.py`'s pipeline); QOI = **peak accelerance |H| + band-GRMS [g/lbf]** at held-out sensors.
- **Same scorer:** `score.py` (interval/Winkler + CRPS + log-predictive-density HEADLINE; coverage + z-std
  SECONDARY). Do not write a new scorer.
- **Same convergence gate:** R̂≤1.05, ESS≥200, div-frac<2% on EVERY variable incl. β; NUTS default with the
  StatFEM run's TMCMC-escalation-if-multimodal protocol (documented deviation, same as that run).
Reuse method: COPY the needed files into the new workspace `code/` and `data/`, record a `manifest_sha256.txt`
proving the copied `core.py`, `score.py`, and data are byte-identical to the StatFEM run. NEVER edit the
StatFEM run in place.

## 2. The IFT construction (be faithful to the papers; state every adaptation)
Field-centric, physics-in-prior (the papers' central move). Adapt to ShockSat structural dynamics:
- **Field** = the complex reduced response `u(ω)` (74-dim) at each measured drive frequency.
- **Physics residual** = the dynamic-stiffness equation `R(u;θ,ω) = A(θ,ω)u − f`, `A(θ,ω)=K(θ)−ω²M` with
  hysteretic damping `(1+iη)`, `f` = unit point force at the drive node (same drive as StatFEM).
- **Physics-informed PRIOR over the field** (faithful to PIFT `∝exp(−β∫R²)` and Hao-Bilionis "physics-informed
  prior measure on the function space of system responses"): `π(u|θ,β) ∝ exp(−(β/2)‖A(θ,ω)u − f‖²)` — a
  Gaussian field prior with precision `βAᴴA`. **β = learned inverse-temperature = trust in the physics /
  model-form-error thermometer.**
- **Measurement likelihood** (same observable as StatFEM whole-FRF): observed-channel `log|H|` = noisy
  observation of `u` through the same observation operator S and units-gain c, iid floor σ_meas (use the
  StatFEM run's σ_meas=0.15). Held-out channels are NEVER in the likelihood.
- **Inference (state the deviation honestly):** the field `u` is Gaussian given (θ,β) ⇒ **marginalize it
  analytically** (exact in this linear-field regime) → a marginal posterior over (θ, β, c); sample with
  **NUTS** (reusing the consistency-toy `nuts_marg.py` M-ift machinery + the StatFEM `core` forward). The
  papers use SGLD/VI for NONLINEAR fields; here the field is linear so marginalization is exact and gives the
  SAME posterior — record this as a faithful, tractable equivalence, not a shortcut. If a near-resonance
  multimodality fires (β·AᴴA is near-singular at resonances — physically the FRF is most uncertain there),
  escalate to TMCMC exactly as the StatFEM run does, and report evidence.
- **Held-out prediction:** the IFT posterior field extends to unobserved DOFs by construction; predict held-out
  `u` → peak-|H| + band-GRMS via the SAME `heldout_qoi.py` forward + `score.py`.

State, in `method_ift.md`, the exact prior, likelihood, marginalization, β prior, and every adaptation, with
the two arXiv citations. Minimal re-implementation only; copy NO results from any IFT/PIFT repo.

## 3. The StatFEM baselines to compare against (already computed in the other run — re-score on identical splits)
On the SAME ≥25 splits and SAME QOI/scorer, put the IFT arm head-to-head with:
1. **L5 modal-feature + marginal QOI-discrepancy** — the WORKING StatFEM twin (the bar): peak coverage ≈0.88–0.91,
   z-std≈1, interval ≈1.4e3, calibrated-but-wide (≈×2.7). (`heldout_qoi.py` / `mc_heldout.py`.)
2. **M2 whole-FRF Schneider** — the StatFEM FIELD-likelihood arm that FAILED (R̂ 2.58–129, interval ≈1e17). This
   is the most direct apples-to-apples for a field method: same observable, physics in the LIKELIHOOD vs the
   IFT PRIOR.
3. (If cheap) **Beck mode-matching-free L8** — the sharpened StatFEM twin (interval 671→545).
Re-run or re-load these from the StatFEM workspace so all arms are scored by the identical harness on the
identical splits (record provenance). Do not alter their numbers.

## 4. Priority deliverables & clarification gate (`priority_deliverables.md`)
1. A faithful IFT twin (`method_ift.md` + `code/ift_arm.py`) that runs end-to-end on the real data.
2. The head-to-head **held-out-sensor QOI scorecard** (IFT vs L5 vs M2 [vs L8]) on ≥25 identical splits:
   interval/CRPS/logpd (headline) + coverage/z-std (calibration), per QOI (peak, band).
3. β as a reported model-form-error thermometer (+ its identifiability) and a convergence table (every arm,
   β included).
4. An immutable `check.py` encoding the pre-committed verdict rule (§5) + the apples-to-apples provenance check
   (copied core/score/data are byte-identical), one-command `run_all.sh`, `runtime.json`.
5. A legible, tufte-compliant deck (gated on a non-RED checker; §8) + ≥1 held-out-FRF overlay figure.
If any priority is ambiguous, state the assumption prominently in `decisions_log.md` and proceed.

## 5. Question/decision gate + PRE-COMMITTED verdict rule (write before running)
- Decision supported: is "physics in the prior with a learned trust temperature" (IFT) a better, equal, or worse
  way to build a trustworthy ShockSat twin than our StatFEM (discrepancy / modal-feature) approach, on real
  held-out data?
- Success metric: held-out peak-|H| + band-GRMS **proper scores** (interval/CRPS/logpd), median over ≥25 splits,
  with calibration (coverage, z-std) and convergence as gates.
- **Pre-commit the four honest outcomes (ALL valid; do not engineer a win):**
  - **WIN:** IFT converges (incl. β) AND beats L5 on headline proper scores at equal-or-better calibration.
  - **ROBUSTNESS-WIN:** IFT does not beat L5 but **avoids the M2 whole-FRF failure** — converges and widens
    gracefully (β shrinks) where M2 diverged ⇒ physics-in-prior is more robust than physics-in-likelihood on the
    same field observable. (Directly tests Bilionis's claim on real data.)
  - **TIE:** IFT ≈ L5 within split-to-split spread ⇒ competitive, not better here.
  - **HONEST NEGATIVE:** IFT also hits the coarse-FEM wall (non-converge, or β collapses and it reduces to a
    wide regression no better than L5+disc) ⇒ physics-in-prior does not rescue a coarse FEM either.
- Human judgment: whether the QOI/observable/band is the right one (inherited from the StatFEM card).
- What would make this the wrong question: if the binding constraint is the coarse FEM (it is, per the StatFEM
  run) then NO inference construction sharpens it — the comparison is then about robustness/calibration/honesty,
  not sharpness. Say so up front.

## 6. Assumptions ledger (`assumptions_ledger.md`) — inherit + IFT-specific
- INHERIT the StatFEM run's ledger (band, observable, ζ=0.01, σ_meas=0.15, gain c, bad-channel exclusions,
  channel-split-only validation, single hit/impact) — cite it, do not silently change any value.
- IFT-SPECIFIC, with value+rationale+sensitivity: the field definition; the residual/operator form; the **β
  prior** (state it; β is the headline new knob); the marginalization assumption (linear field → exact);
  resonance-regularization of `βAᴴA`; θ prior (match StatFEM LogNormal(0,0.25), 4 identifiable groups).

## 7. Identifiability gate (required)
- **β identifiability:** report β's posterior + whether it is pinned or weakly identified (the consistency toy
  found β weakly identified above a threshold — test it on real data); if weak, say so and show θ/QOI are (or
  aren't) affected.
- **θ identifiability:** reuse the StatFEM FIM/strain-energy gate (4-of-9 groups clear the floor); confirm the
  IFT arm uses the same identifiable subset so the comparison is fair.

## 8. Discretization-invariance sub-test (the IFT selling point — cheap, do it)
Vary the reduced-basis dimension and/or the frequency-grid density and show whether the IFT θ/QOI posterior is
**invariant** (the IFT promise) vs the StatFEM whole-FRF arm's sensitivity. Echoes the consistency toy's C2
result on real data. One small sweep; report the spread.

## 9. Plot & deck gate (apply the tufte skill; NO text-on-text)
For EVERY figure: write the plotting code to a saved `.py`, run
`python .claude/skills/tufte-data-graphics/scripts/tufte_lint.py <script>.py`, and run the image-legibility +
**text-overlap auditor** (bbox check at save time) — record JSON per figure. Log-frequency axes; linear magnitude
unless dB justified; direct labels over legends; caption carries quantity/units/data-count/synthetic-vs-real and
the takeaway; flag any non-converged arm ON the figure. Required:
- **Fig A (money):** held-out QOI proper-score scorecard, IFT vs L5 vs M2 [vs L8], peak + band, over ≥25 splits
  (show the split-to-split distribution, not just medians).
- **Fig B:** β thermometer (posterior + identifiability) and, if applicable, β vs a model-error proxy.
- **Fig C:** a held-out-channel FRF overlay — measured vs IFT band vs L5 band vs M2 band — showing who places the
  resonances and who widens honestly.
- **Fig D:** discretization-invariance (IFT θ/QOI spread vs the knob) vs the whole-FRF arm.
- **Convergence table** (all arms, β included) as a figure/table.
Deck (`slides/`, gated on non-RED checker, ~8–12 slides, every number traces to a result JSON / checker gate):
the concern → the apples-to-apples setup → Fig A → Fig B → Fig C → Fig D → verdict + scope (which of the four
§5 outcomes, with the numbers). Do NOT build claims the checker did not certify; carry the coarse-FEM ceiling
and the single-hit/split-only YELLOWs.

## 10. Verification gate — immutable `check.py`
Encode GREEN/YELLOW/RED (Result Status Standard) with explicit numbers:
- GREEN requires: IFT arm converged on the headline configuration (R̂≤1.05/ESS≥200/div<2%, β included) OR a
  documented TMCMC escalation; the head-to-head scorecard exists for all arms on identical splits; the verdict
  string is generated from the numbers per §5 (one of WIN/ROBUSTNESS-WIN/TIE/HONEST-NEGATIVE); β identifiability
  reported; **apples-to-apples provenance check passes** (copied core.py/score.py/data byte-identical to the
  StatFEM run via sha256); figures tufte-linted + image-QA + overlap-clean.
- YELLOW (documented, never "success"): single hit/impact, channel-split-only (labeled reduction); single
  realization per split-seed; coarse-FEM ceiling; β weak identifiability if found; NUTS→TMCMC deviation.
- RED: any undocumented non-convergence presented as converged; a score/coverage claim without the numbers; a
  non-identical scorer/data/forward (apples-to-apples broken); the StatFEM run edited in place; a missing or
  fabricated figure; tufte/image-QA failure; any "IFT wins" claim not generated from the proper-score numbers.
Checker exits non-zero only on RED. Also check units/axes/log-frequency, absolute-vs-normalized, method summary,
data/replicate counts, likelihood/prior data-usage statement.

## 11. Sensitivity gate
Vary the assumption most likely to change the verdict: the β prior (does the verdict survive a 3× wider/tighter
β prior?); the observed fraction; the analysis sub-band. Report whether the IFT-vs-StatFEM ranking is robust or
fragile. Separate this from the discretization sub-test (§8).

## 12. Runtime & compute
Write `runtime.json` (`active_runtime_s`, `elapsed_wallclock_s`). float64, `.venv_nuts` (numpyro/jax x64),
`OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`. The ≥25-split × arms NUTS/TMCMC sweep WILL exceed the tool
timeout — launch detached (`nohup … > logs/run.log 2>&1 & disown`), monitor with short until-loops, and make it
**resumable** (skip finished (split,arm) cells on relaunch; write partial results).

## 13. Not allowed / anti-cheating
- Do NOT edit the StatFEM run, the consistency toy, the tufte skill, or any immutable checker; copy what you need.
- Do NOT reimplement the scorer, forward model, splits, or data — reuse them (apples-to-apples is the point).
- Do NOT present a non-converged IFT (or StatFEM) arm as converged; escalate to TMCMC or label YELLOW.
- Do NOT engineer an IFT "win"; the verdict string must be generated from the proper-score numbers.
- Do NOT copy any IFT/PIFT/StatFEM repo results as generated outputs.

## 14. Done criteria
Done only when: artifacts exist; `check.py` passes (non-RED) via `bash run_all.sh`; the head-to-head scorecard +
verdict (one of the four §5 outcomes) is checker-generated; β identifiability + convergence reported; apples-to-
apples provenance verified (sha256); every figure tufte-linted + image-QA + overlap-audited; the deck's every
claim traces to a checker number; `decisions_log.md` complete; and a `docs/report/project_log.md` row is
PROPOSED for the lead (status copied verbatim from the checker — do not edit durable notes yourself).

## Human stop points (lead handles these)
Stop for human approval before changing any durable rule, checker expectation, sampler standard, or the project
notes/vision. This study + its own checker + deck are new artifacts and do not require that stop; the
project_log row, runs.md, and memory.md updates do.
