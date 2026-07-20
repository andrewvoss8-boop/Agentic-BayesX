# ShockSat × Bayesian updating — Bilionis review packet (2026-06-26)

Consolidation packet for a review with Dr. Bilionis. **No new science** — it pulls real numbers
from earlier threads into one deck + written companion. Every headline number traces to a saved
`out/*.json` in a sibling workspace (`out/sources.json` here is the index).

## Read in this order
1. **`slides/shocksat_bilionis_review.pptx`** — the 31-slide deck (the deliverable).
2. **`packet.md`** — written companion: the same story with every number + source + status tag.
3. **`publishable_findings.md`** — the ranked answer to "what is the most potent publishable finding(s)?"
4. **`priority_deliverables.md`** — maps each of Andrew's asks to where it is delivered.

## Replay
```
bash run_all.sh
```
Regenerates the 4 new figures (`code/make_review_figs.py`, tufte-linted), re-copies the reused
figures from sibling workspaces, builds the deck (`code/make_deck.py`), and QAs it
(`code/qa_deck.py` — checks text overflow, table width, bottom-spill; no LibreOffice needed).

## Honesty / status
- **EXPLORATORY** (figures + numbers, no immutable checker yet): the new mean-function metric, the
  remeshing plateau, the wide-CI finding, the θ-movement (all from `shocksat_psd_envelope_twin_20260623`).
- **CHECKER-BACKED** (SHA-locked grader, OVERALL YELLOW honest negatives / GREEN integrity): IFT
  head-to-head, the consistency toy, model-class selection, FEM-remesh Card D, the papers studies.
- Samplers labeled explicitly (NUTS default / TMCMC when NUTS goes multimodal / non-converged flagged).
- Built without changing any durable rule, checker, sampler standard, or project note except the lead
  CURRENT-STATE block in `notes/memory.md`. Items surfaced for Andrew's approval are in `packet.md §14`.
