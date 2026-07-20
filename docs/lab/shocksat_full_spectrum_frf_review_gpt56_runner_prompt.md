# Runner card — ADVERSARIAL REVIEW of the ShockSat FULL-SPECTRUM FRF study (for a GPT-5.6 reviewer agent)

**Paste-and-run: you are an autonomous REVIEW agent. Your job is to find what is wrong, weak, or over-claimed
in a completed study — not to praise it. A well-supported "the study is honest and its conclusions hold" is a
valid outcome; so is "claim X is over-stated, here is the evidence." Do NOT fabricate. Never state a
conclusion your artifact checks do not support. You are a skeptical labmate, not a cheerleader.**

Date issued: 2026-07-16. Author: lead (Claude/Fable), for Andrew. Reviewer model: GPT-5.6.
Study under review (READ-ONLY): `artifacts/reports/shocksat_full_spectrum_frf_20260714/`
Your outputs go ONLY to a NEW workspace you create: `artifacts/reports/shocksat_fullspec_review_gpt56_20260716/`.
Do NOT modify the reviewed workspace, any SHA-locked checker, `AGENTS.md`, `CLAUDE.md`, or any other study.

---

## 0. Cross-tool + re-grounding (mandatory, ~20 min)

You are likely running in Codex/Cursor, not Claude Code. **Verify your own tool's compaction/memory behavior
before relying on it** — Claude-specific mechanisms (`/compact`, CLAUDE.md re-injection, `@import`) do NOT
transfer. Treat the filesystem + git as the source of truth; write decisions to files, not chat.

Read, in order, and take notes to a scratch file as you go:
1. `AGENTS.md` (every gate applies to your review too), `docs/compute_protocol.md`, `docs/agents/roles/reviewer.md`.
2. The study, in this order: `packet.md` → `findings.md` → `decisions_log.md` (D0–D16 — the full trail of
   course-corrections is where the real risk lives) → `question_framing.md` → `assumptions_ledger.md` →
   `quantity_contracts.md` → `check.py` (the SHA-locked checker) → `out/verdicts.json`,
   `out/exact_freeze_scores.json`, `out/identifiability.json`, `out/arms_bands_table.json`,
   `out/spot_checks.json`, `out/overlap_validation.json`, `data/source_register.md`.
3. Skim the reused priors it builds on: `shocksat_true_remodel_loop_20260706/findings.md`,
   `shocksat_resolution_consistent_scoring_20260713/findings.md`,
   `shocksat_composite_bakeoff_20260702/findings.md`.

Write `decisions_log.md` (D0) in YOUR workspace: goal / what you will audit / how you will verify / open
ambiguities, one line each.

## 1. What the study claims (so you know what to attack)

Overall checker: **YELLOW** (11 GREEN / 1 YELLOW = arm-B/C NUTS non-converged / 0 RED). All five pre-registered
success criteria S1–S5 resolved **falsified / not-met**. Headline claims to test:
- **DATA:** all 5 raw modal-hammer drives re-distilled wide-band and validated **bit-identically** vs the
  existing caches WITH live force → "closes the resolution run's Gate W."
- **FEM ceiling:** the twin is credible only to ~640 Hz (dense local-mode forest; 1250 Hz infeasible on a
  16 GB CPU); FRF scoring capped at 500 Hz; 500–1000 Hz is FEM/compute-limited not data-limited.
- **S1 (H1):** no arm cleanly beats baseline A1 on sub-200; shape inference (C) dented the wall (+0.044
  screening) but fails the +0.05/2×SE bar and collapses on the exact basis.
- **S2 (H2):** the amplitude-compass agent led random +0.0138 on the θ=1 SCREENING basis, but the
  exact-at-θ_MAP re-evaluation OVERTURNED it (agent 0.163 vs random 0.165) → agent ties random → H2
  impotence confirmed. This "reduced-basis trap flip" is billed as the study's central methodological result.
- **Arm B/C samplers:** amplitude-trained NUTS is multimodal / non-converged (R-hat 29–360, ESS≈2); the FIM
  (identifiability.json) is used to argue this is MULTIMODALITY, not under-identification; arms are scored at
  labeled deterministic MAPs.
- **S3/S4:** the net-CG QOI reimplementation does NOT reproduce the delivered twin bands (8.2×/3.66×/5.12×
  vs 1.51×/2.30×/2.53×) → declared "not validly assessable"; delivered twin unchanged.
- **S5 (H5):** amplitude-inclusive selection evidence vs held-out ranking Spearman −0.3 → selection ≠ held-out.
- **D16 limitation:** the agent proposed ZERO genuine model-form edits (all thickness/scale/split); the H2
  verdict was amended to say so.

## 2. The high-risk claims to adversarially audit (the core of your job)

For EACH item below: state your verdict (SOUND / OVER-CLAIMED / WRONG / CANNOT-VERIFY), cite the specific
file+number you checked, and if you flag it, say what a corrected statement would be. Do not accept a claim
because it is written confidently — check the artifact.

1. **The exact-basis flip of S2 (most important).** Is the "reduced-basis trap" re-evaluation methodology
   actually correct, or does it beg the question? Specifically: `code/enrich_wide.py` solves K(θ_MAP) fully,
   then FOLDS θ_MAP into the projected blocks so `pkg.modes(ones)` reproduces the exact solve, and reports
   self-consistency 0.0000%. Is 0.0000% a real verification or a tautology (of course a basis reproduces its
   own solve)? Does the exact re-score fairly compare agent vs random (same drives, same warp/gain
   convention, same bands)? Is the −0.0017 agent−random delta robust, or an artifact of best-of-14 winner's
   curse (both tracks are best-of-14)? Would a full exact re-ranking of ALL 28 candidates (not just the two
   screening-winners) change the conclusion? Is it legitimate to report the θ=1 "screening" numbers at all
   given they are inflated?
2. **Multimodality vs under-identification (arm B).** `code/identifiability.py` finite-differences the
   Jacobian and reports FIM eigenvalues 1641–3.6e6, all clearing the prior precision (16), at a 0.73 dex
   discrepancy floor → concludes "multimodal, not under-identified." Is the FIM inflated by resonance-crossing
   (a 2% θ step moving a peak across a 2 Hz bin), and if so does that undercut the "locally over-identified"
   claim? Is scoring a NON-CONVERGED (R-hat 360) posterior at a deterministic MAP defensible, or is it
   laundering a failed sampler? Should TMCMC have been attempted given the compute protocol names it for
   exactly this regime? Is the "YELLOW not-trustworthy" labeling applied consistently on every figure/interval?
3. **"Closes Gate W" / bit-identical validation.** The wide caches match the existing caches at per-channel
   corr 1.000, median |Δlog₁₀|H|| 0.000. Is that an INDEPENDENT verification, or a near-trivial reproduction
   (same hits, same distiller code, same window) that would match by construction? Is "closes the resolution
   run's Gate W" over-claimed? What would a genuinely independent check look like (e.g. a different frame
   length, or force-referenced coherence recomputed from scratch)?
4. **The FEM ceiling call.** `code/filter_basis.py` drops 338 "clamped" modes at 668 Hz and sets the credible
   ceiling to ~640 Hz, then caps scoring at 500 Hz. Is dropping those modes correct (were they truly
   unconverged, or real dense modes discarded for convenience)? Is the 1.25× rule applied honestly? Is the
   "data >1 kHz but FEM ≤640 Hz" framing fair, or does it overstate the data's usable content given only 4–6
   hits per drive and the coherence actually available above 500 Hz?
5. **Net-CG QOI punt (S3/S4).** The reimplementation gives 8.2×/3.66×/5.12× vs the delivered 1.51×/2.30×/2.53×.
   Is "not validly assessable" an acceptable scientific outcome, or a gap that should have been closed by
   reusing the validated `netcg_qoi.py` instead of reimplementing? Does the punt hide a real regression or
   improvement? Is the overconfidence-audit result (shear_y widens 1.23×, others ~1.0) interpreted correctly?
6. **Arm-C exact re-score shortcut.** The exact-basis C number reportedly uses fold-1 shape MAP on the
   enriched basis as a "representative" check rather than per-fold re-fit. Is that a material shortcut that
   could change C's exact score, and is it labeled honestly?
7. **The D16 model-form limitation.** Confirm the count (agent = 0 genuine model-form edits; all
   thickness/scale/split) from `out/query_log.jsonl` + `out/candidate_specs/`. Given the agent never proposed
   refine/rbe2, is the H2-impotence conclusion still supportable from the random control + prior loop, or is
   it now too thin to state at all?
8. **Continuity + integrity mechanics.** Re-run `bash run_all.sh`'s CHECKER only (`python3 check.py`) — it must
   report OVERALL YELLOW, exit 0, and G12 (checker unmodified) GREEN. Verify the checker's own logic is not
   toothless (e.g. does G03's amplitude-LSQ grep actually catch a planted `np.linalg.lstsq` on an amplitude
   fit? does G08 truly force YELLOW on non-convergence?). Spot-check 3–5 headline numbers by recomputing them
   from the raw artifacts, not by trusting the JSON.

## 3. Harness gates you must apply to the REVIEW

- **Result Status Standard:** grade every audited claim GREEN/YELLOW/RED with its caveat and worst-case
  numbers. Overall review status = worst claim.
- **Quantity/verification:** for any number you dispute, recompute it from the source artifact and show both.
- **Sensitivity:** where you suspect fragility (winner's curse, fold noise, basis choice), quantify it, don't
  assert it.
- **Reproducibility:** if you cannot reproduce a claimed number from the files, that is a CANNOT-VERIFY flag,
  not a pass.
- Do NOT run the multi-hour NUTS/eigensolve jobs; audit the CODE and the LOGGED outputs. Re-running the cheap
  checker + a few numpy recomputations is enough.

## 4. Deliverables (in YOUR workspace only)

1. `review.md` — the human-review report: one-paragraph verdict; a table of the ~8 audited claims with
   SOUND/OVER-CLAIMED/WRONG/CANNOT-VERIFY + evidence + a corrected statement where needed; and an explicit
   "does the study's OVERALL YELLOW / all-S1–S5-falsified conclusion hold?" answer.
2. `out/claim_audit.json` — machine-readable {claim_id: {status, file_checked, recomputed_number,
   study_number, note}}.
3. `next_steps.md` — a PRIORITIZED, costed list (cheap→expensive) of what to do next, each tagged with which
   claim it strengthens or which gap it closes. Separate "cheap fixes to the write-up" (e.g. soften an
   over-claim) from "new compute" (e.g. full exact re-ranking of all 28 candidates; validated netcg port;
   1250 Hz eigensolve on a bigger machine; TMCMC for arm B; give the agent refine/rbe2 edits).
4. `decisions_log.md` (D0…) — your audit trail, including any human clarification.
5. Append a one-row entry to `notes/runs.md` and a row to `docs/report/project_log.md` (status = your review
   status, copied from your own report; never stronger than your evidence). Update NOTHING else outside your
   workspace.

## 5. Non-negotiables

- Read `AGENTS.md` and honor every gate. Never fabricate a number, plot, or reproduction.
- Do NOT modify the reviewed workspace, `check.py` (any study's), durable rules, or another study.
- If a claim cannot be verified from the artifacts, say CANNOT-VERIFY — do not guess.
- Communication: plain English; define ML/stats terms on first use; structural-dynamics terms need no gloss.
  Two audiences: ~1-yr ML/stats reader, and an advanced structural-dynamicist. Lead with intuition.
- If you find a genuine RED (fabrication, an integrity gate that doesn't actually gate, a headline number that
  doesn't reproduce), say so plainly and stop for Andrew before drawing broader conclusions.
- Falsifying the lead's own study is a VALID, welcome outcome. So is confirming it. Report what the files
  support — nothing more.
