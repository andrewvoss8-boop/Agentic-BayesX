# Fresh-runner prompt — continue Card A: validate the StatFEM twin on the REAL ShockSat (P2→P5)

You are a **runner agent** in **Agentic BayesX**. Lead = Claude Code; human = **Andrew Voss**; advisor objective =
**Ilias Bilionis**: *"evaluate the StatFEM approach… build, evaluate, identify its gaps, and suggest improvements."*
Build for correctness, reproducibility, traceability, continuity. **Plain English**; define every ML/stats/sampling
term/acronym/symbol (with units) on first use; never make a result sound stronger than the files + checker output
support. Structural-dynamics terms (FRF, modal, FEM, damping, mode shapes) need no gloss.

## 0. RE-GROUND FIRST (do before any code; re-do after any compaction)
Read, in order: `AGENTS.md` (every gate binds); then in workspace
`artifacts/reports/statfem_real_validation_20260617/`:
`decisions_log.md` (D0–D11 — the spine; read ALL of it), `references_reviewed.md`, `priority_deliverables.md`,
`question_framing.md`, `phase1_summary.md`, `check.py` (the IMMUTABLE checker — do not edit), and the lead
CURRENT STATE block at the top of `notes/memory.md`. Skim the original task card (Card A) in the lead's hand-off
and the two papers' notes in `references_reviewed.md`. Then restate goal / last decision / next action / open
ambiguities in one line before acting. **A sibling runner owns `artifacts/reports/statfem_pift_collapse_20260617/`
— HANDS OFF.**

## 1. Where things stand (verdict-so-far, all artifact-backed)
- **Observable LOCKED (Andrew, D2): all-REAL-FRF, single impact location.** Truth = single-impact measured |H1|
  [g/lbf] from hit-001 (`shocksat_statfem_runner_20260609/extracted/Test07_ImpactHammer_990x/*001*.mat`), force
  window 2 ms + exponential response window, N=200000, Δf≈1.25 Hz, band 45–260 Hz (173 pts). Drive = nearest kept
  FEM node to impact (9,8,1) in, X axis (node idx 22951). **A global units-gain nuisance ≈ ×100 (c0≈5.6 in
  log)** reconciles the FEM g/lbf scale (D4). 87 mapped channels (DR median 147×). Single-hit quality weight (D5).
- **THE CORE RESULT (D6–D11):** the **whole-|H| MAGNITUDE likelihood is locally-identifiable / near-singular on
  real data** — NUTS R-hat 104 (ESS 2, 0 div = multimodal), and even TMCMC (n=1500×4) R-hat 129 with the σ_d→∞
  "variance singularity" (D10); fixing σ_d / downselecting θ does NOT rescue it (D7). The **MODAL peak-FREQUENCY
  feature likelihood (L5), extracted FROM the same real FRF, CONVERGES** — R-hat 1.002, ESS 2388, 0 div, held-out
  **6/6** modal frequencies, σ_w2≈7% (D11). Gap identified + improvement demonstrated (the Ilias deliverable).
- **Sampler (Andrew APPROVED, D9):** adaptive — run NUTS first (the multimodality DETECTOR); if it shows the
  local-identifiability signature (R-hat≫1.05, ESS small, ~0 div) ESCALATE to **TMCMC** (chosen over BUS-SuS
  because it also returns model EVIDENCE for the param-count study). This USES a non-NUTS sampler with documented
  justification (AGENTS.md NUTS rule permits this) — do NOT edit AGENTS.md. **check.py stays immutable: TMCMC cells
  fill the SAME diag fields** (`max_rhat` from ≥4 INDEPENDENT TMCMC runs, `min_ess`, `div_frac`=0).
- **Sharpness suite (D, `code/score.py`) built + passes the required "wide-band-doesn't-win" demo.** Headline =
  proper scores (interval/Winkler, CRPS, log predictive density); PIT + z; coverage/width SECONDARY; whole-FRF
  score is PEAK-WEIGHTED + quality-weighted.

## 2. Code already built (in `code/`; reuse, don't rewrite)
- COPIED BYTE-IDENTICAL (never edit): `core.py`, `nuts_arms.py`, `predict.py`, `viz.py`, `image_qa.py`.
- New (yours to extend): `realfrf.py` (data layer + `fem_logmag`/`fem_logmag_batch` g/lbf forward + measured-FRF
  reprocess/cache + V_keep→reduced transform T to place ANY FEM DOF), `real_arms.py` (4 NUTS arms M0/M1/M2/M3 +
  global gain + `free_groups` + `fixed_sigma_d`), `run_cell.py`, `diagnose_convergence.py`, `identifiability.py`
  (strain energy 4/9 = plates/bottom_box/top_box/cross_beam; FIM huge-but-multimodal at σ_d0=1.726),
  `tmcmc.py` (validated on a bimodal toy), `run_tmcmc_probe.py`, `score.py`, `modal_feature.py` (L5, CONVERGED).
- Outputs in `out/`: `observable_investigation.json`, `matched_path_sanity.json`, `identifiability.json`,
  `diagnose_convergence.json`, `tmcmc_probe_M3.json`, `modal_feature.json`, `cells/*.json`, `run_config.json`.

## 3. NEXT ACTIONS (priority order; each detached + resumable; write a 1-screen summary per phase)
1. **Extend L5 to the card's held-out-SENSOR QOI** (peak |H| and band-GRMS at held-out CHANNELS, not just
   held-out modes): from the L5-calibrated θ posterior, synthesize the modal-superposition FRF g/lbf at held-out
   channels (use `obs_V`/the reduced mode shapes + damping + the global gain), form predictive QOI ensembles,
   score with `score.py`. This puts the converged method on the card's primary QOI. (Refine the crude ≤12%
   nearest-frequency matching with MAC using the mode shapes — flag as an assumption either way.)
2. **Faithful Schneider sweep under TMCMC** (the reference-gate fix, D8): implement L2 = Schneider complex
   multiplicative (magnitude+phase) with the **ADDITIVE** correlation r·(R_ff⊗I)+(1−r)(I⊗R_zz) and **LEARNED**
   hyperparameters (l_freq, l_space, split r, σ_w, σ_θ) + an **informative** σ_d/σ_w prior (Schneider used
   lognormal mean ~0.1 — to kill the variance singularity); L3 = same + orthogonal projection; L4 = complex
   additive (Fathi/Zhang Eq 20). Test: does faithful Schneider TAME the whole-FRF pathology, and does M3
   orthogonal STARVE the discrepancy vs M2 (the sharpened headline question)? Use larger TMCMC (n≥4000) if needed.
3. **Quality threshold τ as a SWEPT VARIABLE** (Andrew, D9): sweep band/peak-keep level (e.g. full band, w>0.3,
   w>0.5, top-K peaks) and report which τ maximizes held-out proper-score (the "how much to keep/trust" knob).
4. **Parameter-count by EVIDENCE** (TMCMC log-evidence; Kiran §5 Ockham): 9-group vs a parsimonious global
   parameterization; tie to the strain-energy/FIM 4/9 identifiability BEFORE any per-parameter claim.
5. **Monte-Carlo ≥25 splits** on the converged configuration(s) (split axis only — 1 impact / 1 hit, labeled
   reduction, D2); report score DISTRIBUTIONS + which sensor/mode choices help/hurt.
6. **Figures** (each: saved `.py` + read `.claude/skills/tufte-data-graphics/SKILL.md` + run `tufte_lint.py` +
   image-QA + save-time text-overlap audit; log-frequency axes; provenance + not-yet-converged flags ON figure):
   scoring-suite comparison; held-out-FRF bands (L5 / orthogonal-Schneider / naive, REAL measured truth overlaid,
   coherence/quality shaded); θ / param-count; MC distributions; **error-vs-participation FEM graphic** (one
   equal-weight dot per group: x=strain-energy participation %, y=inferred error, size=error×participation; paired
   equal-weight structure locator; "area=footprint NOT error" disclaimer on any spatial map); method/observable
   schematic.
7. **Packet** (3-audience, method summary + likelihood eqns + data-count up front) + **actual editable `.pptx`**
   (python-pptx in base `python3`, gated on non-RED) + `runtime.json` (per-phase). Run `bash run_all.sh` → `check.py`
   to non-RED; every deck claim traces to a checker number.

## 4. Hard constraints / honesty (non-negotiable)
- `check.py` is IMMUTABLE during the trial — never weaken it; make samplers fill its existing fields. Plain
  ShockSat ONLY (no coupled tray). No SOL111 / no mismatched-path FRF likelihood. COPY-never-edit the inherited
  scaffolds. NUTS retained as the diagnostic that exposes multimodality; TMCMC for the multimodal posteriors with
  documented justification (do NOT edit AGENTS.md).
- Compute: pin `OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`, float64, `.venv_nuts` (py3.9.6, numpyro/jax x64);
  launch long jobs detached (`nohup … & disown`) + resumable + short until-loop monitoring; kill only your own
  strays; watch for the sibling runner's procs (leave them).
- Do NOT report an arm as failing if it merely didn't converge — diagnose first. Do NOT let coverage-by-wide-band
  masquerade as success (the proper-score suite + the wide-band demo guard this). Do NOT pre-decide the verdict.
- SURFACE to the lead/Andrew (do NOT self-apply): the `docs/report/project_log.md` row + any `notes/*` updates
  (status copied straight from the checker), any durable rule/sampler-standard/checker change, and **any scoring
  weighting that materially changes the verdict**. The MAC-matching refinement and any new likelihood are study
  artifacts and need no stop.

## 5. One-line restate template (fill before acting)
GOAL: validate the orthogonal-Schneider StatFEM twin on the real ShockSat (calibrated+sharp held-out QOI; find
gaps/fixes). LAST DECISION: D11 — modal-feature likelihood converges (R-hat 1.002, 6/6) where whole-FRF magnitude
fails (NUTS 104 / TMCMC 129). NEXT ACTION: extend L5 to held-out-SENSOR QOI, then faithful-Schneider+τ+param-count
+MC+figures+packet. OPEN: MAC vs nearest-freq matching; whether faithful Schneider tames the whole-FRF pathology.
