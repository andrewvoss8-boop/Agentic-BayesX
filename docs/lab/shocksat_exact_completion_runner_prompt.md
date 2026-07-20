# Runner card A — EXACT-EVIDENCE COMPLETION for the full-spectrum FRF study (post-review items 1–3)

**Paste-and-run: you are an autonomous runner agent. Execute end-to-end without stopping for approval. A
result that WEAKENS the original study's claims is a valid outcome. Never fabricate; never claim beyond your
checker's output.**

Date issued: 2026-07-16. Author: lead (Claude/Fable), dispatched by Andrew. Est. compute: ~4–6 h detached
(mostly ~28 eigensolves at ~6–10 min each on the 16 GB Mac; run SERIALLY — parallel eigensolves thrash).

Workspace (create): `artifacts/reports/shocksat_fullspec_exact_completion_20260716/`
READ-ONLY (never modify): `artifacts/reports/shocksat_full_spectrum_frf_20260714/` (the study),
`shocksat_fullspec_review_gpt56_20260716/` (the review), `shocksat_full_spectrum_frf_repair_20260716/`
(the repair), every SHA-locked `check.py`, `AGENTS.md`, `CLAUDE.md`.

## 0. Re-ground (mandatory)
Read `AGENTS.md` (every gate), `docs/compute_protocol.md`, then: the study's `findings.md` **including the
2026-07-16 POST-REVIEW CORRECTION box at the top** and `decisions_log.md` D11–D17; the review's `review.md`
+ `out/claim_audit.json`; the repair's `verdicts.json`. Write D0 (goal/next/ambiguities) in YOUR
`decisions_log.md`. If your tool is not Claude Code, verify its compaction/memory behavior first; filesystem
is the source of truth.

## 1. Why this card exists
The review (accepted, D17) left three evidence holes that are cheap to close:
- **Arm C has NO valid exact-basis score** — the original reused fold-1's shape MAP across all 4 folds,
  leaking 3/4 held-out drives (C6, withdrawn).
- **The S2 exact comparison covers only the 2 screening winners, not all 28 loop candidates** (C1) — the
  agent-vs-random conclusion currently rests on screening-selected winners re-scored exactly.
- **The shipped figures/verdicts carry the defective collector output** (NaN stats, invalid F=R; C8) — the
  repair fixed the numbers but not the figures, and no finiteness-hardened verdict artifact exists.

## 2. Tasks (in order; all resumable; every eigensolve logged to your `out/eigensolve_log.jsonl`)

### T1 — Honest arm-C exact score (per-fold refits; ~1–2 h)
For EACH of the 4 LODO folds: refit the shape-field MAP on the ENRICHED basis
(`shocksat_full_spectrum_frf_20260714/data/packages_wide/A0_wide__enr.npz`, θ=ones convention) using ONLY
that fold's 3 TRAIN drives (adapt `code/arm_c_score.py::map_fold` — import the study's code READ-ONLY via
sys.path; write nothing there), then score that fold with ITS OWN MAP via the study's `wscore_wide` +
`arm_c_nuts.shapes_forward` machinery (again read-only imports; your own score log). Multi-start ≥4
(deterministic seeds). Output `out/armC_exact.json`: per-fold P1′ (sub-200, 200–500), fold-mean, paired
delta vs A1-exact (A1-exact folds are in the study's `out/exact_freeze_scores.json`) with the paired-SE
convention (std of per-fold deltas /√4). **The leakage rule is absolute: fold k's MAP must never have seen
drive k. Your checker greps for cross-fold MAP reuse.**

### T2 — Exact re-rank of ALL 28 loop candidates (~3–5 h detached)
For each candidate in the study's `out/query_log.jsonl` (14 agent + 14 random): enrich at its multi-start
θ_MAP (reuse `code/enrich_wide.py::enrich` read-only; θ_MAPs in the study's `out/theta_maps.json`; specs in
`out/candidate_specs/`) and score exactly (θ=ones) on the 4 dev folds, both bands. Resumable per candidate.
Output `out/exact_rerank.json`: the full 28-row table (cid, track, screening sub-200, exact sub-200, exact
folds). Then compute S2 BOTH ways and report both:
  (a) screening-selected winners re-scored exact (the study's convention — should reproduce −0.0017), and
  (b) EXACT-selected winners (best exact per track), paired delta ± SE — the winner's-curse-honest reading.
Also report the Spearman between screening and exact rankings per track (how badly did the θ=1 basis
re-order candidates?) and the top-3 per track under each ranking.

### T3 — Corrected verdicts + figures (~1 h)
- `out/verdicts_final.json`: S1/S2 from the repair + your T1/T2 numbers (S1 rule: ≥+0.05 AND ≥2×paired-SE;
  S2 rule: ≥1×paired-SE, reported under BOTH T2 selection conventions); arm-C exact from T1; S3/S4 =
  CANNOT-VERIFY (pointer to Card B); S5 from the repair (note the prior-width fragility). EVERY number
  asserted finite before writing.
- Figures (read the tufte skill at `.claude/skills/tufte-data-graphics/SKILL.md` first; saved .py; lint +
  legibility QA): (i) corrected arms×bands bar chart (repair + T1 numbers, real fold SEs, NO F=R row, arm-C
  labeled with your refit provenance, arm-B/C worst R-hat 360.6 / ESS 2.0 printed beside any MAP-derived
  bar); (ii) screening-vs-exact scatter for all 28 candidates, tracks distinguished, the two S2 selection
  conventions annotated.

## 3. Pre-registration + checker (BEFORE any science)
Write `priority_deliverables.md` + a short `question_framing.md` (the two pre-registered questions: Q1 "does
an honestly-computed arm-C exact score still beat A1-exact?" and Q2 "does the agent-ties-random conclusion
hold under a full exact re-rank, under both selection conventions?" — either answer is valid). Then write
`check.py`, run on the empty workspace (must be RED science-not-run), SHA-lock (`CHECKER.sha256`), never
edit. The checker MUST encode the lessons from D17: (1) every reported statistic asserted **finite** (NaN/
null = RED); (2) T1 fold-MAP provenance: fold k's MAP file must record train_keys excluding drive k (RED
otherwise); (3) T2 completeness: exactly 28 candidates with exact scores; (4) figures scripted+linted+QA'd;
(5) no file writes outside your workspace (grep your own code for the read-only workspaces' paths followed
by write modes); (6) runtime.json (active ≤ elapsed); (7) checker self-SHA. Hash reused read-only code into
`REUSED_code.sha256`.

## 4. Rules
- NO SAMPLER in this card (deterministic MAP refits + scoring only — state this per the AGENTS Sampler
  Decision; you are completing evidence for existing arms, not making new posterior claims).
- The VAULT (+XY) is NOT touched. Dev drives only. No vault reads, period.
- One global gain per fold; no per-channel/per-mode amplitude LSQ anywhere (checker-grepped).
- Budgets: ~29 eigensolves expected (28 + margin); log each; if a candidate's enrichment fails, record it
  as excluded-with-reason rather than substituting.
- Continuity: append `notes/runs.md` entry + `docs/report/project_log.md` row (status copied from YOUR
  checker); packet-style `findings.md` with plain-English answers to Q1/Q2; `run_all.sh` replay.

## 5. Honest failure modes
Arm-C exact refits may show C beats A1-exact (the withdrawn claim was "C collapses" — your honest number may
revive OR bury it; report either). The exact re-rank may crown different winners than screening — if the
EXACT-selected agent winner beats the exact-selected random winner, say so plainly (it would soften the
review's H2 reading); if random still ties/wins, H2 impotence stands on firmer ground. Do not steer toward
either outcome.
