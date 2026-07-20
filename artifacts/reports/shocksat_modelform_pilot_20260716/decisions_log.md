# decisions_log — MODEL-FORM PILOT (Card C, 2026-07-16)

Runner: Claude (Fable 5), Claude Code session. Card pasted by Andrew 2026-07-16; autonomous
(no mid-run approval), falsification is a valid outcome.

## D0 — re-grounding + tool-compaction verification + card-interpretation assumptions (BEFORE any science)

**Re-grounding done (all read this session):** `AGENTS.md`, `CLAUDE.md`, `docs/compute_protocol.md`;
study `findings.md` POST-REVIEW box + D16/D17 (`shocksat_full_spectrum_frf_20260714`); review C7 +
`next_steps.md` item 6 pilot spec (`shocksat_fullspec_review_gpt56_20260716`); true-remodel loop
`findings.md` + its `femlib.py`/`actions.py`/`mech_gates.py` (`shocksat_true_remodel_loop_20260706`);
Card A `out/exact_rerank.json` (screening→exact Spearman 0.53 agent / 0.64 random; top-1 agent flipped
`wa2_brackets_soft`→`wa2_tbox_xbeam` — the reordering that motivates this card's all-exact scoring rule);
Card B CURRENT STATE (S4 falsified; net-CG twin stands); study code `wide_package/wide_candidates/
wscore_wide/wide_forward/enrich_wide/diag_wide/loop_wide.py`; Card A `_common.py`/`exact_rerank.py`
(the validated exact-scoring reuse path — reproduced study exact numbers to <1e-10).

**Prerequisites verified on disk:** Card A COMPLETE (checker GREEN 12/0/0, `out/exact_rerank.json`
present, 28/28 scored). Card B COMPLETE (GREEN 10/10 integrity; S4 falsified, S3 cannot-verify).

**Tool compaction behavior (verified for THIS tool, Claude Code):** on compaction only the project
rules file (CLAUDE.md) is re-injected; conversation-only instructions are lost. Therefore every
non-obvious decision goes in THIS file before continuing, and the re-grounding routine (re-read card +
this file + pre-registration docs) runs after any compaction. The runner card text itself lives in the
chat only — its operative content is restated across `priority_deliverables.md` / `question_framing.md`
/ `quantity_contracts.md` / `assumptions_ledger.md`, which are the post-compaction source of truth.

**Card-interpretation assumptions (autonomous run — flagged for Andrew to overrule post-hoc):**
1. **HQ1 selection convention.** "An amplitude-compass agent beats seeded random on held-out sub-200
   P1′, evaluated on EXACT bases (≥1×paired-fold-SE)" — with all 60 candidates exact-scored there is no
   screening-selected convention here. Pre-registered PRIMARY = per-track BEST-exact candidates compared
   paired-per-fold (the winner's-curse-honest convention Card A called `exact_selected`, with its
   selection-noise caveat: both tracks max over 30 noisy candidates). SECONDARY = per-track MEAN over all
   30 candidates, paired per fold (the distribution-level question). Both reported; HQ1 "met" requires
   the PRIMARY rule (best-vs-best delta ≥ 1×paired-fold SE).
2. **HQ2 class unit.** "At least one GENUINE model-form edit class produces an exact-basis held-out
   improvement over the A1 baseline ≥1×paired-fold-SE" — the class is the unit, not the proposer:
   per class the BEST exact candidate POOLED over both tracks (n=12/class) vs A1's exact per-fold
   sub-200 scores (study `out/exact_freeze_scores.json`, A1.exact.folds — read-only), paired per fold.
   Class MEAN vs A1 reported alongside as the selection-noise control. GENUINE classes = connectivity,
   mesh_density, element_formulation, geometry (property_control is the control class and cannot
   satisfy HQ2 by definition).
3. **A1 comparator identity.** A1 = the study's window+measured-ζ baseline at its θ_MAP, EXACT basis
   (sub-200 exact 0.1137; folds +0.2738/+0.4982/−0.0020/−0.3153, verified from the study JSON). Same
   forward convention (windowed 𝒲 +
   survey ζ interpolation) is used for every candidate here — apples-to-apples.
4. **Finalist refit meaning.** "top-2 per track get per-fold θ_MAP refits (θ_MAP per fold on train
   drives only)" = an AMPLITUDE-trained θ MAP per fold (deterministic multi-start L-BFGS on the 3 train
   drives' log10|H1|, one global gain per drive, θ log-normal prior σ=0.25 — arm-B likelihood form at
   MAP, no sampler), then a per-fold EXACT enrichment at that fold's θ_MAP, scored on the excluded drive
   only. This is a REINFORCEMENT test reported alongside; HQ1/HQ2 verdicts come from the main
   (survey-θ_MAP, fold-independent) exact table — pre-registered in `question_framing.md` §Decision rule.
5. **Duds and quotas.** Stratification quota = 2 SCORED candidates per class per round per track.
   Build/mech-gate failures are duds logged with reasons (`out/duds.jsonl`), don't count against the
   80-query budget, and are replaced (agent: next proposal from the same diagnosis; random: next seeded
   draw of the same class). This mirrors the study's `random_duds.jsonl` convention.
6. **Class-drop rule (locked into the checker).** A NEW operator that fails its V-gate is dropped with
   documentation. If BOTH operators of a class become unavailable the class is dropped ONLY via
   `out/dropped_classes.json` naming the failed V-gate — the checker then enforces quotas over the
   remaining classes. connectivity cannot be dropped (rbe2_soften is pre-validated); property_control,
   mesh_density cannot be dropped (existing validated ops).
7. **No vault.** Zero +XY reads (would be the program's 4th; needs Andrew's explicit pre-registration —
   default NO per the card). Encoded as checker gate + runtime guard.
8. **Sampler declaration (AGENTS Sampler Decision).** NO SAMPLER anywhere in this card: deterministic
   multi-start MAPs + exact eigensolves + scoring. Reason (per card §5): the study established the
   amplitude posterior is multimodal/unresolved; a non-converged posterior per candidate adds nothing to
   a model-ranking pilot. NUTS/HMC remains the project default for Bayesian updating; no posterior claim
   is made here. Follow-up posterior work on a winner = TMCMC per the compute protocol, separate card.
9. **Compute.** 16 GB Mac CPU, float64, serial eigensolves, ONE candidate per python process (Card A D4
   swap-thrash lesson), detached (`nohup … & disown`) with resumable per-candidate partials. Expected
   ~120 scoring eigensolves at ~500–950 s each (Card A observed mean 950 s at 399,510 DOF, k=200) →
   17–32 h wall detached; the card authorizes this ("the cost of not repeating the trap").

## D2 — V-gate first-run failures for the two geometry sub-operators (2026-07-16, pre-science;
## evidence preserved in logs/vgates_full.log) and the fixes
- **warp_panel patch known-answer FAILED on first run** — the gate reported warped "fundamentals"
  14.01/27.93/55.21 Hz (flat: 194.75), scaling ~LINEARLY with warp amplitude. Diagnosis: those are NOT
  drumhead modes; they are RIGID-ROTATION modes leaking stiffness ∝ amp² — the facet-shell formulation
  (mean-plane projection in quad_local_frames) is not rigid-rotation invariant on warped elements, so a
  near-rigid mode crossed the 10 Hz "rigid" cut and the gate's naive "first mode ≥ 10 Hz" pick grabbed
  it. FIX (gate logic, not physics): identify the drumhead mode by excluding modes whose shape is >95%
  explained by a best-fit rigid field, then take the lowest w-dominant survivor; ADDITIONALLY record the
  leaked-RBM frequency vs the drumhead as an explicit leak check. The FULL-MODEL warp checks passed on
  the first run (6 RBMs < 10 Hz, liveness 1.44%, max edge slope 3.4e-4) because per-element warp there
  is orders smaller than on the coarse patch; the per-candidate mech gates (n_rbm==6 + quality caps)
  bound this leak for every scored geometry candidate. The failed gate JSON was regenerated after the
  fix — BEFORE any scored use (checker G04 timestamps prove ordering); the first-run failure is
  preserved in the log and here.
- **joint_offset CRASHED its gate** — hard-cutoff translation of the node set inverted boundary quads
  (corner det J ≤ 0: a 0.22 in in-plane shift across one 0.28 in element edge). FIX (operator design,
  the purpose of a V-gate): displacement now BLENDS smoothly from the full vector inside R_JOINT=0.75 in
  to zero at R_BLEND=3.0 in (cosine taper), so distortion spreads over ~2.25 in instead of one element.
  Ledger operator spec updated with a dated note. Cap |vec| ≤ 0.35 in unchanged.

## D1 — workspace + reuse-base decisions
- All study/loop code reused READ-ONLY via a `_common.py`-style shim (Card A pattern): every write
  target (package dir, eigensolve log, score log) rebound into THIS workspace before any study module
  runs; study base packages reached via symlinks in `data/packages_mf/`. Reused bytes hashed in
  `REUSED_code.sha256`; checker re-verifies per run.
- NEW operators (rbe3_convert, formulation, warp_panel, joint_offset) implemented in `code/mfops.py` in
  THIS workspace; they extend (never edit) the validated grammar. All candidates flow through a
  T-builder `build_T_mf` (copy of femlib.build_T + RBE3 dependency rows); V-gate `vgate_tbuilder`
  requires it to reproduce femlib.build_T EXACTLY (same sparsity, max|ΔT|=0) on the baseline model
  before ANY scored use, protecting the validated classes from my extension.

## D3 — run_queue.sh driver bug (2026-07-17, mid-round-2; no science impact)
The queue driver's completion check (`tail -5` of the SHARED queue.log) matched round 1's "ALL DONE"
line and exited after scoring only the first round-2 candidate; the box then idled. Fixed to inspect
only the current iteration's stdout; relaunched. No candidate result was affected (per-candidate
partials are the ground truth; the driver only sequences work) — cost is wall-clock only.
