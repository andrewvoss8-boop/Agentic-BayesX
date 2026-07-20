# question_framing — EXACT-EVIDENCE COMPLETION (20260716)

Pre-registered BEFORE any science was run (checker SHA-locked at the same time). **Either answer to either
question is a valid, publishable outcome.** This card exists to close evidence holes, not to defend a
conclusion. A result that WEAKENS the original study is a success of the process.

## Plain-English orientation (ML/stats terms defined on first use)

Some vocabulary, because the two questions below are statistics questions wearing structural-dynamics
clothes:

- **LODO** = "leave-one-drive-out". We have 4 hammer drives (impact locations/directions:
  `m_xpos_990x`, `m_zpos_990z`, `m_ypos_990y`, `m_zpos_900z`). A **fold** is one train/test split: fit on 3
  drives, score on the 4th (the *held-out* drive). 4 folds = each drive gets a turn being held out.
- **Leakage** = when the thing you fit was allowed to see the data you later score on. It makes a model look
  better than it is. *Concrete example:* if I tune a model's mode shapes using drive `+Z(990)` and then
  report how well it predicts drive `+Z(990)`, that score is not a prediction — it's a memory. The study's
  arm-C exact score did exactly this for 3 of its 4 folds (review finding C6).
- **MAP** = "maximum a posteriori" = the single most probable parameter value under the posterior; found here
  by a deterministic optimizer (L-BFGS), NOT by a sampler. A MAP is a **point**, not an uncertainty — it
  cannot tell you how confident to be. **Multi-start** = re-run the optimizer from several starting points
  and keep the best, because the objective has many local optima.
- **P1′** = the study's held-out score: per-channel fractional correlation between predicted and measured
  log₁₀|H| over a frequency band, after a train-side frequency warp, median over channels, mean over folds.
  Higher = better. It is dimensionless (a correlation), and it is **gain-invariant** (one global gain per
  fold cancels out).
- **Screening vs exact basis.** The FEM twin is projected onto a reduced set of modes. If that basis is built
  at θ=1 (all stiffness multipliers = 1) but you then evaluate at θ_MAP ≠ 1 (here joints 0.47, cross_beam
  1.46), the reduced model mispredicts the very modes it is most sensitive to (up to ~3.7% frequency error).
  Those numbers are **screening** — fine for triage, not for a verdict. The **exact** basis re-solves the
  eigenproblem *at* θ_MAP and folds θ_MAP into the projected blocks, so scoring at θ=ones reproduces the full
  solve (self-consistency ~0.0000%). Study D14/D22 established this; the exact check already overturned one
  conclusion (S2), which is why it must now be applied to *all* candidates, not just the winners.
- **Winner's curse** = if you pick the best of many noisy candidates using score A, and then report score A
  for that winner, the winner is flattered: you selected partly on noise. The honest fix is to select and
  report on the same *trustworthy* metric, or to select on one and report on an independent other. Q2 below
  reports S2 **both ways** precisely because the study only ever did the flattered version.
- **Paired SE** = standard error of a paired difference. Because both arms are scored on the *same* 4 folds,
  we take the per-fold difference (arm₁ − arm₂ on fold k), then SE = std(deltas, ddof=1)/√4. Paired is the
  right convention: it cancels fold-to-fold difficulty, which is the dominant variance here.
- **Spearman rank correlation** (ρ_s) = correlation of *ranks* rather than values; +1 = identical ordering,
  0 = unrelated ordering, −1 = reversed. It answers "did the cheap screening metric put the candidates in the
  same order as the trustworthy exact metric?" without caring about the absolute scores.

Structural-dynamics terms (FRF, accelerance, MAC, mode shapes, modal truncation, drive point) are used
without gloss per the project's audience rule.

## The engineering decision being supported

Whether the ShockSat FEM twin's **remaining held-out FRF error is reachable by any lever we own** — and in
particular whether (a) amplitude-trained *shape inference* (arm C) is worth carrying forward, and (b) an
LLM-agent-driven remodeling loop earns its cost over equal-budget random proposals. Both sub-decisions were
answered by the 2026-07-14 study on evidence that the 2026-07-16 review found partly invalid. This card
supplies the missing evidence so the decision rests on numbers that survive audit.

**What remains human judgment:** whether to fund Card B (net-CG port / S3/S4), whether to reopen the agentic
loop with a compass that can propose genuine model-form edits (study D16), and whether a dented-but-standing
shape wall justifies more shape work. This card supplies numbers, not that call.

## Q1 — Does an honestly-computed arm-C exact score still beat A1-exact?

- **Why it is open:** the study's arm-C exact aggregate (0.157) applied fold-1's shape MAP to all 4 folds
  (`rescore_freeze.py:78`), so 3/4 exact fold scores were leaked. The sentence "on the exact basis C's lead
  collapses (0.189→0.157)" is **withdrawn** (D17/C6). Note the direction is not obvious: a leaked score is
  usually *optimistically* biased, yet the leaked number was *worse* than A1 — because fold-1's MAP is simply
  the wrong MAP for the other 3 folds (a mismatch penalty that can outweigh the leak's flattery). So the
  honest refit could move the number **either way**.
- **Quantity:** arm-C exact P1′, sub-200 Hz [45,200) and 200–500 Hz [200,500), fold-mean over the 4 LODO
  folds, each fold scored with a shape MAP refit on **only that fold's 3 train drives**, on the enriched
  (exact-at-θ_MAP) basis `A0_wide__enr`, scored at θ=ones.
- **Comparator:** A1-exact, the same 4 folds, from the study's `out/exact_freeze_scores.json` (A1 shares the
  same enriched basis `A0_wide__enr`, so the comparison is basis-matched and paired).
- **Pre-registered readings (all valid):**
  - **C REVIVED:** honest C − A1-exact ≥ +0.05 AND ≥ 2× paired-SE → arm C clears the pre-registered S1 bar on
    the trusted basis; the study's "C collapses" would be not merely withdrawn but *reversed*, and the shape
    wall would be **cleared, not merely dented**.
  - **C DENTS:** delta > 0 but misses the S1 bar → the shape wall stands, dented, on honest evidence; the
    study's H1 verdict survives with a corrected number.
  - **C BURIED:** delta ≤ 0 → the withdrawn "C collapses" sentence is *vindicated by honest evidence*, and
    the collapse becomes a real finding rather than an artifact of one reused MAP.
- **Falsifier / what would make this the wrong question:** if the 4 per-fold refits disagree wildly (e.g. the
  `+Z(990)` fold's −0.086 screening excursion recurs and dominates), the fold-mean is a poor summary and the
  honest answer is "C's benefit is drive-dependent, not a scalar" — I will report the per-fold spread, not
  hide it in the mean. Also: this is a **MAP point** comparison; it says nothing about arm C's posterior
  uncertainty, which is unresolved (fold-1 NUTS R-hat 13.95, ESS 2).

## Q2 — Does the agent-ties-random conclusion hold under a full exact re-rank, under both selection conventions?

- **Why it is open:** the exact-basis S2 number (D−R = −0.0017 ± 0.0094) re-scored only the **2 screening
  winners** out of 28 loop candidates (review C1). Since the whole point of D15 is that the θ=1 screening
  basis **inflates** candidates near the θ-parametrization span, the screening step that *chose* those two
  winners is itself suspect. If screening mis-ordered the candidates, the "winner" of each track is the wrong
  candidate to re-score, and S2 is answering a question about two arbitrary members of each track.
- **Quantity:** exact P1′ (sub-200 and 200–500) on the 4 dev folds for **all 28** candidates in
  `out/query_log.jsonl` (14 agent + 14 random), each enriched at its own multi-start θ_MAP
  (`out/theta_maps.json`) and scored at θ=ones.
- **The two selection conventions, both reported:**
  - **(a) Screening-selected, exact-scored** (the study's convention): take each track's screening winner
    (agent `wa2_brackets_soft`, random `wr2_rnd001`), report their exact scores. **Reproduction target:
    D−R = −0.0017** (if I do not reproduce this to ~1e-3, my pipeline is wrong and I say so).
  - **(b) Exact-selected, exact-scored** (winner's-curse-honest): take each track's **best exact** candidate
    and report that delta ± paired SE. This is the fair "best the agent could do vs best random could do" on
    the trustworthy metric.
- **Pre-registered readings (all valid, none preferred):**
  - **Agent wins under (b):** exact-selected agent − exact-selected random ≥ 1× paired-SE → this **softens
    the review's H2 reading**; the agent's edit space did contain a genuinely better candidate and screening
    simply failed to find it. I will say so plainly.
  - **Random ties/wins under (b):** → H2 impotence stands on **firmer** ground than the study had: not "the
    two screening winners tie" but "the best of 14 agent proposals does not beat the best of 14 random
    proposals on the trusted basis."
  - **Either way,** the D16 scope limitation still binds: the agent proposed **zero** genuine model-form
    edits (all 14 = thickness/scale/split), so any H2 statement remains "within a mostly-parametric edit
    space", NOT "agent-proposed geometry/mesh/connectivity edits failed". Q2 cannot lift that limitation and
    will not be written as if it does.
- **Rank agreement (the mechanism):** Spearman ρ_s between screening and exact sub-200 rankings, per track,
  plus top-3 under each. Low/negative ρ_s = the θ=1 basis genuinely re-ordered the field, which would make
  convention (a) — the study's — a near-arbitrary pick and convention (b) the only meaningful S2. High ρ_s =
  screening was a decent proxy and the study's shortcut was benign. This is the diagnostic that tells us
  *why* (a) and (b) agree or disagree.
- **Falsifier / what would make this the wrong question:** if a candidate's enrichment fails, it is recorded
  **excluded-with-reason**, never substituted — but if several fail non-randomly (e.g. all `split` candidates),
  the "all 28" claim weakens and the re-rank covers a biased subset; I would report the exclusion pattern
  rather than a clean 28-row table. Also: 14 candidates per track is a small field; a per-track *maximum* is
  a high-variance statistic, so convention (b)'s delta carries selection noise in BOTH arms — I report the
  paired SE and refuse to call a sub-SE gap a win for either track.

## Objective function / success metric
Held-out per-channel FRF fractional correlation **P1′**, sub-200 Hz primary (the band the pre-registered S1
bar lives in), 200–500 Hz secondary. Higher is better. Pre-registered decision rules, inherited unchanged
from the study so this card cannot move its own goalposts:
- **S1:** an eligible arm beats A1 by **≥ +0.05 AND ≥ 2× paired-SE**.
- **S2:** agent D beats random R by **≥ 1× paired-SE** (reported under BOTH conventions above).

## What the optimization/search is allowed to choose
Only the shape-field MAP (T1, L-BFGS multi-start on train drives only) and the θ_MAP already fixed by the
study (T2, reused verbatim from `theta_maps.json` — **not re-optimized**, so this card cannot flatter any
candidate by re-tuning it). Selection rules, band definitions, the scoring machinery, and the S1/S2 bars are
**inherited and frozen**; this card chooses none of them.

## What this card explicitly does NOT do
- No sampler (see `decisions_log.md` D0 Sampler Decision) → **no posterior/uncertainty claim**. Every number
  here is a deterministic optimizer point estimate.
- No vault (+XY) read. Dev drives only.
- No S3/S4 resolution — the net-CG port failed its reference reproduction and stays **CANNOT-VERIFY**
  (pointer to Card B). This card must not launder that into "not met".
- No re-litigation of the accepted D17 corrections; the repair's S1/S5 numbers are carried, not recomputed.
