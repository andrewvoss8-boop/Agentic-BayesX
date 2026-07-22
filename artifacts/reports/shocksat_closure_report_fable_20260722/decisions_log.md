# Decisions log — ShockSat advisor closure brief, fable revision

## 2026-07-22 F1 — human review decisions (Andrew, in chat; controlling for this workspace)

Andrew reviewed `shocksat_closure_report_20260722/ShockSat_Bayesian_FEM_StatFEM_closure_brief.docx`
(sha256 e8e04f40bcc69c03634e5c6d94eb5beee64f5ebdcbe13f7882ab09f16ee01a8f, immutable input) and left
comments C0–C9 plus a rewritten closing paragraph. Decisions:

1. **New workspace, `_fable` suffix.** Edit a copy; the v1 workspace and its docx/md are untouched.
2. **Closing paragraph kept verbatim** as Andrew wrote it in the docx (including informal voice).
   The `## Guidance I need for the final month` heading is retained so checker G10 still applies.
3. **Figure expansion (C5) is the lead's choice** → implement a 6-panel held-out FRF grid (rule in F2).
4. **Evidence comparison (C8): EXPAND, do not delete.**
5. **Format: whatever is easiest** → adapted copy of `build_report.py` (same docx styling engine, same
   frozen artifact sources) writing `ShockSat_Bayesian_FEM_StatFEM_closure_brief_fable.docx/.md`.

Andrew also requires the brief to state two things without hedging:
- **Why the posterior mean does not move enough toward the data:** the only converged likelihood sees
  modal frequencies (no channel-specific amplitude/participation mechanism, and only 4 of 9
  prior-whitened directions are learned), AND the added discrepancy was zero-mean by construction, so
  it could only widen bands, never shift the mean. Per Andrew's comment C3, the brief must concede that
  a location- and frequency-structured MEAN discrepancy (e.g., "+X dB for sensors at one location over
  20–80 Hz") could move the mean and WAS NEVER TESTED; its failure is not established.
- **Why the bands remain unusably wide:** a zero-mean, single-scale marginal discrepancy can achieve
  coverage only by being wide everywhere; parameter-only width is near baseline (1.07–1.22×) so
  parameter uncertainty is not the driver.

## 2026-07-22 F2 — pre-registered 6-panel channel-selection rule (declared BEFORE computing)

From frozen `statfem_real_validation_20260617/out/mc_cache.npz`, split seed 10 (31 held-out channels,
same split as the v1 two-panel figure): rank channels by the median over 45–260 Hz of
|log10(updated median / measured)|, ascending. Select ranks 1, 7, 13, 19, 25, 31 (best → worst,
even spread). No substitutions after seeing the panels; DAQ ids fall where they fall, and the caption
states the rule. No new inference, sampling, or scoring — plotting stored arrays only.

## 2026-07-22 F3 — per-comment edit plan

- C0: likelihood-inventory table (8 implemented formulations with status) precedes the boxed modal
  likelihood, which is labeled as one of eight and the only converged one.
- C1: Figure 2 (prior-whitened subspace + σf sweep) moves to Appendix A; §2 leads with the answer.
- C2: Bayesian Q&A table answers begin **Yes/No/Partly**; "what remains unresolved" rewritten at
  research scope (structured-mean discrepancy untested; response-level StatFEM undecided; model-form
  search vs parameter updating), with the three non-converged chains as a limit line.
- C3: new §2 subsection "Why the mean cannot move — and what could still move it" (text per F1).
- C4: Figure 3 (whole-FRF profile) deleted; the ~10-local-maxima diagnosis stays as text.
- C5: Figure expansion per F2.
- C6: load table = shear X/Y only; normal-Z row, reconciliation, and synthetic-only labels move to
  Appendix B (exact strings retained so checker G5 logic is unchanged).
- C7: CRPS defined in the definitions table and at first use in §5, plain English.
- C8: evidence comparison expanded into its own subsection explaining Bayesian evidence, what +54.02
  means, each caveat, and why it is not held-out validation.
- C9: work-completed table gains a "Where explained" column with section pointers.

## 2026-07-22 F5 — KNOWN WORDING DEFECT, correction DEFERRED by Andrew (no artifact changed here)

Found while drafting Task Card D. This brief says the Schneider correlated-error method is not
implemented — brief md lines 86 ("Not implemented in this project"), 94 ("the Schneider surrogate
remain unimplemented future options"), 137 ("relevant future work, not a completed method here [11]"),
built from `code/build_report_fable.py` lines 528 and 572.

That understates the project's own work AND hides a negative result. `shocksat_modelclass_L5_20260619/
code/schneider_faithful.py` implements the correlated frequency×space error model, and it ran as arms
M2/M3 — both non-converged (M2 R-hat 2.577, ESS 0.71, discrepancy scale sigma_w running 1.726 -> 12.37;
M3 Plumlee-orthogonal R-hat 1.112, ESS 17, sigma_w 12.60), stored in
`statfem_real_validation_20260617/out/tmcmc_faithful_M{2,3}_ident4_n8.json`. Only the RATIONAL SURROGATE
half of Schneider's method is genuinely unimplemented; the sentence conflates the two.

**Human decision (Andrew, 2026-07-22): DEFER.** Do not rebuild the docx now; correct it once, together
with Task Card D's result, so the statement is made correctly a single time. Consequence accepted and
recorded here: if this brief is delivered before Card D lands, it ships with a sentence we already know
understates the implemented work and omits the M2/M3 convergence failure. No file in this workspace was
modified by this entry other than this log; the SHA-locked `check.py`, the docx, and the md are untouched.

## 2026-07-22 F4 — checker adaptation (new workspace; v1 check.py untouched)

Adapted in this workspace's `check.py`, logic otherwise identical: deliverable filenames get `_fable`;
G1/G8 figure list becomes 3 figures (method map, 6-panel FRF, appendix modal figure) with ≥3 alt texts;
G6 page cap re-verified against the rendered PDF (target ≤10 with the new appendix); G5 strings now
satisfied from Appendix B; all other gates (numeric trace ≥25 checks, likelihood direction, definitions,
narrative/forbidden-words, references, Y1 non-convergence caveat) unchanged.
