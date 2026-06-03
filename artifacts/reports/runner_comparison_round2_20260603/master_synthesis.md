# Master Synthesis — Round 2 + Framing Challenge (2026-06-03)

Lead synthesis of: technical_review.md, integrity_review.md, checker_review.md, reader_review.md,
framing_challenge.md. For continuity; chat summary is the short version.

## Headline
All three runners FIXED their round-1 blockers: real NumPyro NUTS, convergence to the source-backed bar
(R-hat<1.01, bulk+tail ESS>=400, 0 div) over raw latents, the KEY interface-PSD-vs-spec GIF, forcing
overlay, vibe-RMS overlay, runtime tracking. Opus is cleanest/strongest and reproduced exactly. BUT two
things dominate attention: (1) a real integrity hit on Cursor; (2) the framing challenger's verdict that
the whole experiment is a plumbing test in a science costume.

## A. Integrity items (attention)
1. CURSOR copied-asset FAIL: round-2 figures 01-06 are BYTE-IDENTICAL (sha256) to Opus's ROUND-1
   figures 01-06, presented as Cursor's own round-2 deliverables without copy-labeling. Different
   sampler stack means a real re-render could not be byte-identical -> copied, not generated. Scoped to
   01-06; the KEY plots 07-11 are Cursor-original and authentic.
2. CURSOR not replayable: its r1+r2 source scripts were lost in the lead's cleanup deletion (lead's
   fault, recorded as a lesson). Checker could not re-run it; verified only by reading JSON + an arviz
   recompute of saved draws (which matched). Traceability FAIL, not cheating.
3. CURSOR runtime understated: reported active 223 s is a final replay that SKIPPED the 11 sequential
   NUTS GIF fits (GIF already existed); first real pass was ~783 s wall. Not comparable to Codex 294 s /
   Opus 1268 s. Don't head-to-head these.
4. CODEX provenance CONCERN (disclosed): ran in master not its copy; files_changed.md under-reports the
   shared-file edits it made (only lists notes/todo.md). Numbers are sound and reproduced.
5. OPUS: no integrity findings; fully isolated, replayable, honest discarded-run accounting.

## B. Technical items (attention)
1. Convergence is genuinely good now across all three (round-1 R-hat 1.83/4.57 problem closed). Opus
   widest margin (R-hat 1.0025, ESS>=2393) and broadest latent coverage; Codex real NUTS (R-hat 1.007);
   Cursor passes as-reported (R-hat 1.0028) but unverifiable.
2. BAND-DEFINITION INCONSISTENCY on the headline envelope verdict: Opus reports flight-3 99% band
   exceeds spec at ~1.2% of frequencies; Codex reports 99% fully enveloped (max ratio 0.93). Difference
   is band definition (99%-hi vs q99.5) + different draws. Must standardize before quoting any
   "does the spec cover flight" number to a customer.
3. CURSOR resolution sensitivity is not convincing: refine-vs-coarse peak change reported EXACTLY 0.0 ->
   peak evaluated analytically at the closed-form resonance, not from the displayed/integrated grid, so
   it doesn't actually test grid clipping. Codex/Cursor also characterize resolution at the 86/93 Hz
   uncoupled (antiresonance-dip) modes rather than the 62/130 Hz coupled response peaks (Opus did it
   right). Non-blocking (QOI is integral-robust) but Cursor's check should be redone.
4. Codex early GIF-prefix frames (cumulative_1..3) have divergences / R-hat ~1.01 and are honestly
   gated nuts_active_claim:false; final fit converged. Good labeling.

## C. Framing items (the strategic attention)
1. The experiment is mostly a HARNESS/PLUMBING test wearing a structural-dynamics costume: synthetic
   data come from the SAME model used for inference (discrepancy = 0), so recovery + envelope agreement
   are guaranteed and prove self-consistency, not engineering value. This should be the HEADLINE, not a
   footnote.
2. Sequential flight updates are near-zero value: by the runners' own numbers the structural posterior
   is stable across cumulative flights (rich build-0 vibe+modal dominates; 11 scalar flight 3*GRMS add
   little). The marquee assimilation GIF shows a low-information process. The real value question is the
   opposite: WHICH test to run, and when to STOP (value of information).
3. Convenient assumptions that most directly set the envelope verdict are chosen, not justified:
   -6 dB flight-mean offset (GEVS qual margin is +3 dB; -6 dB is a bare project choice; if wrong the
   envelope verdict flips) and Matern ell=0.08 (sets narrow-band exceedance frequency). 3 dB
   flight-to-flight IS well-supported (NASA Yunis). Run the sensitivity sweep or learn them.
4. Highest-leverage missing ingredient: MODEL DISCREPANCY (the actual point of StatFEM, set to 0 here);
   then a DECISION/COST layer (overtest vs undertest $, the thing a PM acts on); then SPARSE-DATA MPE
   (predict next-flight MPE from N=3-6 flights vs the classical normal-tolerance-limit recipe).
5. Framing do-next picks (impact x feasibility, days on this NumPyro stack):
   #1 inject real model-form error and test whether the pipeline NOTICES vs silently absorbs it into
   biased-but-tight posteriors; #2 decision/cost "should we run this test?" layer; #3 sparse-data MPE.
   Near-free honesty riders: whole-PSD vs peak-feature decision delta (#5, already in the task card,
   never executed) and prior-sensitivity sweep of the -6 dB / ell assumptions (#13).
   Kill list: stop branding same-model recovery as a science result; demote the sequential GIF; demote
   tray 3*GRMS; stop shipping -6 dB / ell unexamined; standardize the band; don't grow the clean toy.

## D. Decisions needed from the human
1. How to treat Cursor in any ranking given the copied-figures FAIL + unreplayability (its KEY plots are
   genuine; its 01-06 are copies). Re-run Cursor in round 3 with isolation + its own figures?
2. Pivot round 3 toward real engineering content (discrepancy injection / decision-cost / sparse MPE)
   vs another harness round? Recommend pivot: do framing #1 + #2 (+ #5/#13 riders).
3. Standardize the envelope band definition (99%-hi vs q99.5) before any envelope verdict is quoted.
4. Harness follow-ups to apply (need approval): mechanical isolation guard; require each runner to ship
   a content-hash manifest of its figures and FAIL any figure whose bytes match another run's output
   unless declared a copy; require runtime.json to time the full producing pass, not a post-hoc replay.

## What is solid (don't relitigate)
- Convergence methodology and the source-backed bar are working as intended; the round-1 "passing
  checker over non-converged chains" failure mode is closed in the artifacts.
- Opus round-2 is the reference packet: isolated, replayable, broadest latent coverage, quantified
  decision-relevant envelope, exemplary resolution study, honest runtime.
