# priority_deliverables — MODEL-FORM PILOT (Card C, 2026-07-16)

Restating the card's PRIORITY asks in my own words, with acceptance criteria and delivery locations.
Ambiguities are flagged; since the run is autonomous, each carries a recorded assumption (decisions_log
D0) instead of a mid-run question.

| # | Priority ask (my words) | Acceptance criteria | Delivered where |
|---|---|---|---|
| P1 | Answer HQ1: does an amplitude-compass agent with STRATIFIED proposals across 5 edit classes beat seeded random at equal budget on held-out sub-200 P1′, all-exact-basis? | Pre-registered decision rule (question_framing §4) evaluated from 30-vs-30 exact-scored candidates; paired-fold SE; falsification valid | `out/verdicts.json` HQ1, `findings.md`, `packet.md` centerpiece table |
| P2 | Answer HQ2: does ANY genuine model-form class (connectivity / mesh_density / element_formulation / geometry — NOT property scaling) beat the A1 baseline ≥1×paired-fold-SE on exact-basis held-out sub-200? | Per-class best-pooled-vs-A1 paired deltas + class means; complexity rule applied | `out/verdicts.json` HQ2, class×track table |
| P3 | GENUINE model-form freedom actually exercised: executable operators for element formulation and geometry (never tested by ANY prior track, D16/C7), each validated BEFORE scored use | `out/vgate_*.json` PASS (or documented FAIL + drop); scored candidates in all non-dropped classes; stratification quota enforced by locked checker | `code/mfops.py`, `out/vgate_*.json`, checker G-gates |
| P4 | EVERY scored number exact-basis (own-space k=200 θ=1 solve → ≥5-start deterministic θ_MAP → enrich at θ_MAP → score at ones); no reduced-basis screening number ever reported as a score | Checker gate: every query-log record tagged exact with enrichment self-consistency ≤0.01% and an existing enriched package; forbidden screening keys RED | `out/query_log.jsonl`, checker G03 |
| P5 | Complexity/runtime penalty next to every score: ΔDOF, Δn_params, solve-time ratio; "not-worth-it" label pre-registered (exact gain <1×SE AND ΔDOF >+10%) | `out/complexity.json` complete for all scored cids; final ranking table shows score AND complexity | `out/complexity.json`, packet table, scatter figure |
| P6 | Finalists (top-2/track): per-fold amplitude-trained θ_MAP refits with NO cross-fold reuse of any fitted object + paired-fold S-tests; NO vault read | Fold-provenance recorded per refit (train_keys exclude fold); checker G05/G07; vault guard shows 0 +XY opens | `out/finalists.json`, checker |
| P7 | Pre-registration + SHA-locked checker BEFORE science; RED on empty workspace; never edited | `CHECKER.sha256`, `out/checker_report_empty.json` (RED), G11 self-SHA | this dir |
| P8 | Deliverables: packet (method summary first; class×track centerpiece), findings (plain-English HQ verdicts), ≥5 scripted/linted/QA'd figures, run_all.sh replay, runtime.json, continuity rows | Done criteria in AGENTS.md; figures per Plot Gate; `notes/runs.md` + `docs/report/project_log.md` updated with checker-copied status | workspace root |

**Flagged interpretation points (assumed, not confirmed — see decisions_log D0 for full text):**
HQ1 selection convention (best-vs-best primary / mean secondary); HQ2 class unit (pooled tracks, best +
mean); finalist refit = amplitude-trained per-fold θ_MAP as reinforcement (HQ verdicts from the main
fold-independent table); dud/replacement rule; class-drop rule via failed V-gate only.
