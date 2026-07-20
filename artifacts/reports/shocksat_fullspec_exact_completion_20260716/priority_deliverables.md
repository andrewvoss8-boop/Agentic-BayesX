# priority_deliverables — EXACT-EVIDENCE COMPLETION (20260716)

Andrew's priority asks, restated in my own words, with the artifact that delivers each. Written BEFORE any
science (AGENTS Priority Deliverables and Clarification Gate). A priority with no delivered artifact is a
failure; an "assumed" interpretation without confirmation is a warning and is flagged as such.

| # | Priority ask (card §2) | My interpretation | Delivered in | Status |
|---|---|---|---|---|
| P1 | **Honest arm-C exact score** | Arm C currently has NO valid exact-basis number: the study reused fold-1's shape MAP for all 4 folds, so 3/4 exact fold scores saw their held-out drive (review C6, withdrawn). Refit the shape-field MAP **separately for each of the 4 LODO folds** on the ENRICHED (exact-at-θ_MAP) basis using ONLY that fold's 3 TRAIN drives, score each fold with ITS OWN MAP, and report the fold-mean + paired delta vs A1-exact. Either sign is a valid answer. | `out/armC_exact.json`, `findings.md` §Q1 | **DELIVERED** |
| P2 | **Exact re-rank of ALL 28 loop candidates** | The agent-vs-random (S2) conclusion currently rests on 2/28 candidates — the *screening-selected* winners re-scored exactly. Enrich every one of the 28 `query_log.jsonl` candidates at its own θ_MAP and score it exactly on the 4 dev folds, both bands. Report S2 **both ways**: (a) screening-selected winners re-scored exact (study convention; target reproduction −0.0017), and (b) EXACT-selected winners (best exact per track) — the winner's-curse-honest reading. | `out/exact_rerank.json`, `findings.md` §Q2 | **DELIVERED** |
| P3 | **Screening-vs-exact rank agreement** | Per track, the Spearman rank correlation between the screening (θ=1 basis) sub-200 ranking and the exact sub-200 ranking, plus the top-3 per track under each ranking. Answers "how badly did the θ=1 basis re-order candidates?" | `out/exact_rerank.json` → `rank_agreement`, `figures/fig_screening_vs_exact.png` | **DELIVERED** |
| P4 | **Corrected, finiteness-hardened verdicts** | A verdicts artifact that carries the repair's finite S1/S2 numbers + my T1/T2 numbers, with S3/S4 = CANNOT-VERIFY (pointer to Card B) and S5 from the repair incl. its prior-width fragility. **Every asserted number checked finite before writing** (the D17/C8 lesson: the shipped study verdicts were NaN and the checker validated key-presence, not finiteness). No F=R row. | `out/verdicts_final.json` | **DELIVERED** |
| P5 | **Corrected figures** | The shipped study figures carry the defective collector output. Replace with: (i) corrected arms×bands bar chart — repair + T1 numbers, real per-fold SEs, **no F=R row**, arm C labeled with its refit provenance, and arm-B/C worst R-hat 360.6 / ESS 2.0 printed beside any MAP-derived bar; (ii) screening-vs-exact scatter for all 28 candidates, tracks distinguished, both S2 selection conventions annotated. Tufte skill read first, plotting code in saved `.py`, linted, legibility-QA'd. | `figures/fig_arms_bands_corrected.png`, `figures/fig_screening_vs_exact.png`, `out/fig_manifest.json`, `out/tufte_lint.txt`, `out/fig_qa.json` | **DELIVERED** |
| P6 | **Pre-registration + immutable checker** | `priority_deliverables.md` (this file) + `question_framing.md` with the two pre-registered questions, then a `check.py` that is run RED on the empty workspace, SHA-locked, and never edited. It must encode the D17 lessons (finiteness, fold-MAP provenance, T2 completeness, figure QA, no writes outside the workspace, runtime, self-SHA). | `question_framing.md`, `check.py`, `CHECKER.sha256`, `checker_report.json` | **DELIVERED** |
| P7 | **Continuity** | `notes/runs.md` entry, `docs/report/project_log.md` row (status copied verbatim from MY checker, never stronger), packet-style `findings.md` answering Q1/Q2 in plain English, `run_all.sh` one-command replay, `runtime.json`. | `findings.md`, `run_all.sh`, `runtime.json`, repo notes | **DELIVERED** |

## Acceptance criteria I am held to
- **Leakage (absolute):** fold *k*'s shape MAP must never have seen drive *k*. Each saved MAP records its
  `train_keys`; the checker RED-fails if any fold's MAP file lists its own fold key, or if one MAP file is
  reused across folds.
- **Finiteness:** every statistic reported in `verdicts_final.json` is asserted finite at write time; a
  `NaN`/`null` anywhere in an asserted number is RED (not a warning).
- **Completeness:** exactly 28 candidates carry exact scores, or an explicit excluded-with-reason record.
- **No LSQ:** one global gain per fold; no per-channel/per-mode amplitude least-squares anywhere
  (checker greps my code for `lstsq`/`polyfit`/`curve_fit`).
- **Isolation:** zero writes outside this workspace; the read-only workspaces' bytes are hash-verified
  unchanged (`REUSED_code.sha256`).
- **No claim beyond checker output.** A result that WEAKENS the original study's claims is a valid outcome
  and will be reported as such.

## Ambiguities flagged (see `decisions_log.md` D0 for the full text)
- **[ASSUMED, not confirmed]** "All 28" = the 28 rows of `query_log.jsonl`; the 29th spec `wr3_rnd001` is a
  recorded build failure (`random_duds.jsonl`) and is excluded-with-reason.
- **[ASSUMED, not confirmed]** T1 refits the shape field at `θ=ones` on the enriched basis (θ_MAP folded in),
  i.e. shapes are re-optimized against the exact basis while θ stays at the study's MAP.
- **[DECIDED]** Study code is imported read-only; all write targets are monkeypatched into my workspace.

---

## Final status (2026-07-16, after the run; statuses copied from `checker_report.json` = OVERALL GREEN 12G/0Y/0R)
All 7 priorities delivered. **GREEN means the evidence is complete and trustworthy AS STATED — it does NOT
mean the success criteria were met.** The science verdicts are: **S1 NOT MET, S2 NOT MET under both selection
conventions, S5 NOT MET/fragile**; S3/S4 not addressed here (Card B supersedes — see `decisions_log.md` D3).
Both pre-registered questions were answered on the "does not clear the bar" side, which the card and
`question_framing.md` declared a valid outcome in advance.

**Delivered beyond the asked scope (unplanned, artifact-backed):** `out/leak_probe.json` — a counterfactual
decomposition of the study's arm-C defect that reproduces their number exactly and separates it into
leak (+0.0822) vs a **basis mismatch (−0.0847) the review never caught**. This was not requested; it exists
because the card's T1 made the comparison cheap and the result was too load-bearing to leave implicit.

**Warnings carried (per this file's own rule that an "assumed" interpretation is a warning):**
- the three [ASSUMED, not confirmed] interpretations above were never confirmed by a human — all three are
  recorded in `decisions_log.md` D0 and remain open to being overruled;
- **P4 carries a known scope defect:** S3/S4 status is `CANNOT-VERIFY` because my checker was locked on the
  card's assumption before Card B falsified S4. Flagged in D3, surfaced in `findings.md` and in every S3/S4
  block via `superseded_by_card_B`. Do not read my S3/S4 status as current.
