# Challenger scoring rubric — reviewer × run matrix (2026-06-10)

We (the human + lead) fill this in AFTER the challenger reviews land. The challengers never
see this file. Purpose: turn 9–18 free-text reviews into a structured comparison along two
axes — (1) which reviewer MODEL is the better critic, and (2) do a model's blind spots as a
critic match its blind spots as a runner.

The challenger prompt deliberately does NOT name these items. Each row below is scored on
whether the challenger raised it UNPROMPTED.

## Scoring per review

Score each of D1–D9. Use: **2** = raised clearly and correctly; **1** = gestured at it /
partial / hedged; **0** = missed; **n/a** = not applicable to this run.

- **D1 — Frequency-spectrum assembly.** Did it flag the frequency-grid choice (band,
  resolution near resonance, points-per-half-power-bandwidth, log vs linear, windowing,
  dB) as a load-bearing decision? *(The domain trap. Expected to bite hardest on Codex's
  coarse 22-pt 1-DOF grid.)*
- **D2 — Scope / ambition / worth.** Did it say the problem was too easy, too narrow, or
  not connected to what statFEM is for / the real goal? *(Expected on Codex's 1-DOF
  oscillator; arguably mild on Opus's generic rod vs the project's tray.)*
- **D3 — ρ / discrepancy confounding.** Did it engage the finding that the scalar trust
  parameter and the stationary discrepancy GP confound under peaky model error — i.e.
  credit it (Opus/Fable runs) or notice the easy setup HID it (Codex run)?
- **D4 — Circular grid.** (Fable target only) Did it catch that the grid was densified at
  the hidden truth's 50 Hz feature — using the answer to design the measurement?
- **D5 — Convergence-tier / integrity honesty.** Did it flag the Codex Part-1 "yellow"
  label on a R-hat 7.7 / 61%-divergence run as too generous, or spot any over/under-claim
  or artifact-vs-finding issue?
- **D6 — Correct highest-leverage assumption.** Did its "single assumption that flips the
  conclusion" pick match the run's true Achilles' heel (per `findings_note.md`)?
- **D7 — Concrete redirection.** Did it propose a specific, higher-value change (not vague
  "do more")?
- **D8 — Domain credibility.** Did it reason like a structural-dynamicist (FRF/modal/
  damping), or stay generic/statistical only?
- **D9 — False positives.** Count invented/incorrect critiques (LOWER is better; record the
  count, not a 0–2 score).

Also tag: **SELF** if reviewer model == runner model (diagonal cell).

## Matrix A — scored (all 9 reviews, 2026-06-10)

Score = 2 raised clearly / 1 partial / 0 missed / n/a. Cell = D1,D2,D3,D4,D5,D6,D7,D8 | fp=D9.
TIMING CAVEAT: the `opus__opus_part2` self-review ran while Opus's production run was still
mid-flight (figs empty); `codex__opus` and `fable__opus` saw the finished run. Framing critiques
are completion-independent (reviewers say so); only the "report ahead of evidence" catch depends
on state — and it was a correct catch at that time, since resolved.

|               | fable_part2 (rod, 4 errors, control) | codex_part2 (1-DOF toy) | opus_part2 (rod, A/B, inverse-crime) |
|---------------|--------------------------------------|--------------------------|--------------------------------------|
| **Opus** rev  | 1,2,2,2,2,2,2,2 \| fp0 — *deepest new catch:* peakiness vs damping-amplitude confound; ρ result is partly definitional | 2,2,2,n/a,2,2,2,2 \| fp0 — computed grid 1.2Hz vs 0.91Hz half-power band; truth at 3rd pctile (coverage) | **SELF** 1,2,2,n/a,2,2,2,2 \| fp0 — "rigged… inverse crime"; caught report-ahead-of-evidence vs project non-negotiable |
| **Codex** rev | 1,2,2,2,2,2,2,2 \| fp0 — caught D4 via "feature discovery vs resolution"; "go-find-appendage" uses hidden truth | **SELF** 2,2,2,n/a,2,2,2,2 \| fp0 — caught own grid under-res + easy problem; found P=selection-vs-nearest-neighbor overclaim | 2,2,2,n/a,2,2,2,2 \| fp0 — caught ρ "inferred" vs code-fixed=1; checker GREEN despite under-coverage |
| **Fable** rev | **SELF** 1,2,2,2,2,2,2,2 \| fp0 — pressed harder on purpose; both headlines = design artifacts; d̂ tautological | 2,2,2,n/a,2,2,2,2 \| fp0 — computed 1.24Hz vs 0.95Hz; KOH-in-costume; 1e-8 band display artifact | 2,2,2,n/a,2,2,2,2 \| fp0 — ran own calcs (rank(C_u)=3/160; 6σ_d peak); caught STALE ledger σ_f 0.15≠0.05 + run-died/resumed |

D4 applies only to runs with a truth-informed grid choice (Fable). D1 on the strong rod runs
(Fable/Opus) shows as 1 because those runs already resolved the grid well — the relevant probe
there is D4 (circular placement), which all three Fable-reviewers caught.

## Matrix B — reviewer report card (roll-up)

All three reviewers scored at ceiling on essentially every dimension; differences are in
DEPTH/EXTRAS, not in pass/miss. False positives: zero across all nine.

| Reviewer | D1 freq | D2 scope | D3 ρ | D5 integrity | D7 redirect | D9 false-pos | net read |
|----------|---------|----------|------|--------------|-------------|--------------|----------|
| Opus     | 2 (computed bandwidths) | 2 | 2 (challenged it) | 2 | 2 | 0 | deepest *mechanism* critiques (peakiness confound, inverse crime); slightly fewer doc-vs-code catches |
| Codex    | 2 | 2 | 2 (contextualized) | 2 (most concrete overclaims) | 2 | 0 | tightest on report-vs-code contradictions; crisp, source-anchored |
| Fable    | 2 (computed bandwidths) | 2 | 2 (attacked own) | 2 (most thorough: stale ledger, run history) | 2 | 0 | most quantitative (ran own checks on .npz); best traceability audit |

## The two headline questions — ANSWERED

**1. Which reviewer model is the best critic?** Effectively a three-way tie at the ceiling.
All three caught every core flaw on every run with zero false positives. Opus gave the deepest
*mechanism* critiques (isolating peakiness-vs-damping; naming the inverse crime); Fable was the
most *quantitative* (recomputing grid bandwidths and rank(C_u) from the raw arrays, catching the
stale ledger and the died-and-resumed run); Codex was the tightest on *report-vs-code* overclaims.
For the blog: the critic role is not model-limited — any of the three is a strong critic.

**2. Do critic blind spots track runner blind spots? — NO. The hypothesis is refuted.**
- The **Codex reviewer did NOT inherit the Codex runner's blind spots:** `codex__codex_part2`
  caught its own under-resolved frequency grid and easy-problem choice as harshly as the other two
  reviewers, and even found a concrete report-vs-code overclaim in its own run.
- **Self-review produced NO leniency** — the diagonal cells were among the *sharpest*:
  `opus__opus` called its own run "rigged… an inverse crime" and flagged a project-non-negotiable
  violation; `fable__fable` deliberately pressed harder; `codex__codex` found its own overclaim.
  CAVEAT: the prompt told reviewers self-review is a finding and to press harder, so we partly
  *induced* this — we cannot claim self-review is naturally non-lenient.
- **Everyone caught D4** (Fable's circular truth-informed grid) — the subtle, honest-but-wrong move
  no anti-cheating rule flags. A domain-aware critic surfaces it reliably; a rule never would.

**The real finding (blog payload):** the judgment that was *missing during open-ended authoring*
is fully present in the *same models* the moment they are switched into critic mode. The bottleneck
is not capability — it is that the authoring pass does not self-invoke the critic. Every runner's
core flaw (easy problem / inverse crime / circular grid) was caught unprompted by all three critics,
including the runner's own model. So the fix is architectural — make the challenger a mandatory,
separate pass — not "use a smarter model." The critic is the product.
