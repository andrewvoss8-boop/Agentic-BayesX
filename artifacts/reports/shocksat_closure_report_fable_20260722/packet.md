# Packet — ShockSat advisor closure brief, fable revision (2026-07-22)

## What this is

Andrew reviewed the v1 advisor brief docx and left comments C0–C9 plus a rewritten closing paragraph.
This workspace holds the revised brief — `ShockSat_Bayesian_FEM_StatFEM_closure_brief_fable.docx` (and
its Markdown mirror) — built as an adapted copy of the v1 build script. The v1 workspace is untouched
and hash-locked as an immutable input. No new inference, sampling, or scoring was run; every number in
the revised brief still resolves to the frozen Task Card A / study artifacts (34 numeric-trace checks).

## The two required plain statements (now explicit in the brief)

- **The posterior mean does not move enough toward the data because** the only converged likelihood
  sees modal frequencies — no channel-specific amplitude/participation mechanism, and only four of nine
  prior-whitened stiffness combinations are learned — and the discrepancy added afterward was zero-mean
  by construction, so it could only widen bands, never shift the mean. The brief explicitly concedes
  (per comment C3) that a location- and frequency-structured discrepancy MEAN could move the mean and
  was never tested; its failure is not established.
- **The uncertainty bands remain unusably large because** that zero-mean, single-scale marginal
  discrepancy can achieve coverage only by being wide everywhere; parameter-only bands are already
  1.068×/1.215× baseline yet under-cover, so width is the only currency the discrepancy has.

## How each review comment was handled

- C0 → modal likelihood labeled "one formulation of eight," inventory enumerated, ledger cross-referenced.
- C1 → subspace/σf figure moved to Appendix A; §2 leads with the answers.
- C2 → Bayesian question table answers open with bolded direct answers; "what remains unresolved"
  rewritten at whole-project scope.
- C3 → new §2 subsection "Why the mean cannot move — and what could still move it" + PLAIN STATEMENT callout.
- C4 → whole-FRF profile figure deleted; the ~10-local-maxima diagnosis retained as text.
- C5 → six-panel held-out FRF figure; channels selected by a rule preregistered in decisions_log.md F2
  (median |log10(updated median / measured)| over 45–260 Hz; ranks 1, 7, 13, 19, 25, 31 → DAQs 28, 79,
  9, 56, 2, 24; DAQ 24 falls out as the worst, consistent with v1).
- C6 → load table is shear-only; normal-Z moved to Appendix B with its synthetic-only labeling intact.
- C7 → CRPS defined in the terms table and again at first use in §5.
- C8 → evidence comparison expanded: what Bayesian evidence is, what +54.02 means, all three caveats
  spelled out, and why it is not held-out validation.
- C9 → work-products table gained a "Where explained" column with section pointers.
- Closing → Andrew's paragraph kept verbatim under the retained heading.

## Checker output (verbatim)

```
OVERALL YELLOW {GREEN: 10, YELLOW: 1, RED: 0}
[GREEN] G1 required artifacts: all required artifacts present
[GREEN] G2 numeric traceability: 34 spot checks; all source-backed
[GREEN] G3 definitions/data contract: terms used later, score units, counts, and bands defined once; unused internal labels omitted
[GREEN] G4 likelihood direction: measured log frequency is modeled around predicted log frequency
[GREEN] G5 evidence labels: normal-Z is repeatedly and adjacently labeled synthetic-only
[GREEN] G6 compression and future-work scope: pages=10; remodelctl only in future work; PSIS-LOO absent
[GREEN] G7 prior DOCX preservation: six prior DOCX files and the commented v1 brief byte-identical
[GREEN] G8 figure legibility and alt text: 3 high-resolution figures; 3+ descriptive alt texts; visual QA recorded
[GREEN] G9 advisor context and narrative: proposal context and chronological method explanation precede results; advisor-facing status shorthand absent
[GREEN] G10 references and closure request: primary/official references present and four closure questions retained
[YELLOW] Y1 inherited science ceiling: 3/5 variants non-converged; worst R-hat=1.418; min ESS=4.4; intervals labeled not trustworthy
```

The single YELLOW is the inherited scientific caveat from Task Card A (three of five σf prior-sensitivity
variants did not converge); it is stated in the brief and is not a defect of this revision.

## Checker adaptations (documented in decisions_log.md F4)

Filenames gained `_fable`; the figure gate expects 3 figures (was 4) after deleting the profile figure
and moving the modal figure to the appendix; the page cap is ≤10 (was ≤9) to accommodate the appendix;
G7 additionally verifies the commented v1 docx/md hashes; all other gate logic is unchanged.
G10's evidence line says "four closure questions retained" — the actual retained closing is Andrew's
verbatim paragraph under the same heading; the gate checks the heading, not the four questions.

## Replay

`bash run_all.sh` (requires Microsoft Word for the PDF render step; LibreOffice is not installed on
this machine). Known environment note: `run_all.sh`'s render line uses the documents-skill renderer,
which needs `soffice`; the delivered PDF was produced with Word automation instead and the audits were
run directly. Figure QA and pagination evidence: `out/figure_qa.json`, `qa/manual_visual_qa.md`.
