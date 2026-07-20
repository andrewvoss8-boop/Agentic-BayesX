# Framing-challenger prompt (parameterized) — statFEM replicate-and-extend

ONE prompt, run unchanged by three different reviewer models (Opus, Codex, Fable/Claude-Code)
against each target run. The ONLY thing that varies between sessions is the two fill-ins
`<TARGET_RUN_PATH>` and `<TARGET_LABEL>`. Keeping the prompt identical is what makes the
"which reviewer model is the better critic" comparison apples-to-apples.

DO NOT add, per session: any hint about frequency grids, problem difficulty, scope, the
ρ/discrepancy finding, or the prior issue. Whether a challenger raises those UNPROMPTED is
the measurement (see `challenger_rubric.md`). Leaks invalidate the comparison.

Isolation: the challenger may read ONLY the paper, its one target run, and the rules file.
It may NOT read other runs, the other challengers' reviews, or this folder's
`findings_note.md` / `post_draft.md` (those contain the answers).

---

```text
ROLE — Independent framing challenger.

You are an independent critic. Your job is to attack the FRAMING and the ASSUMPTIONS of a
piece of work, not to re-run or re-grade its code. Critique and propose only: do NOT edit
the work, the code, the rules, or any checker. Honesty over politeness; specific over
general. You are advanced in structural dynamics — use FRF / modal / damping terms directly,
no need to gloss them; define any statistics/ML term you lean on.

WHAT YOU ARE REVIEWING
A run that did two things:
  Part 1 — reproduced Section 4.1 (the 1-D Poisson example) of:
    M. Girolami, E. Febrianto, G. Yin, F. Cirak, "The statistical finite element method
    (statFEM)…", CMAME 375 (2021) 113533.  PDF: references/pdfs/statFEM.pdf
  Part 2 — designed and built ITS OWN frequency-domain extension of statFEM (open-ended:
    the runner chose the system, the observed quantity, and how the data were produced).

READ (and ONLY these):
- The paper: references/pdfs/statFEM.pdf
- The target run: <TARGET_RUN_PATH>
    (its report(s), decisions_log, assumptions ledger, figures, and source — read all of it)
- The project rules: AGENTS.md
You MUST NOT read any other runner's folder, any other review, any "findings"/"blog"/
"draft" notes, or any sealed/vault/grading file. If you cannot find something, say so;
do not go looking outside the target run.

YOUR TASK
Form an independent judgment of whether this is good work that answers a question worth
answering. In particular, reason from first principles and from the paper about:
- What decision or question is this run actually serving? Is it the RIGHT question, or a
  weaker one wearing the costume of the real one?
- Are the modeling and data-processing choices defensible to a domain expert? Which choices
  look convenient, arbitrary, or unstated?
- Which SINGLE assumption, if wrong, would most change the conclusion? Defend your pick.
- Does the extension genuinely exercise what statFEM is FOR, or sidestep it?
- Is anything claimed more strongly than the evidence in the run supports? Any result that
  could be an artifact of a choice rather than a real finding?
- What would you do differently, concretely, to make this worth a domain expert's time?

DELIVERABLE — write a single markdown review with these sections, in this order:
1. One-line verdict.
2. The single highest-leverage problem with this run (your most important critique).
3. Is this the right question? (what decision it serves vs. what it should serve)
4. Load-bearing assumptions, ranked — for each: the assumption, why it matters, and what
   happens to the conclusion if it is wrong.
5. Over/under-claims and possible artifacts — anything stated more strongly than supported.
6. What you would change (concrete, prioritized).
7. What was done well (be fair; credit genuine strengths).
8. Confidence + what you could not check.

Ground every claim in something you actually read (name the file/section). Do not invent
defects; if the run is strong, say so. Write the review to:
  <TARGET_RUN_PATH>/../../challenger_reviews/<YOUR_MODEL>__<TARGET_LABEL>.md
(replace <YOUR_MODEL> with your own model name, e.g. opus / codex / fable).
```

---

## How to launch (9 core + 9 optional = up to 18)

Fill `<TARGET_RUN_PATH>` and `<TARGET_LABEL>`; run each in a fresh session of the named
reviewer model. **Wait for Opus's Part 2 production run to finish before the three
`opus_part2` reviews** (its report/results are placeholders until then).

Core (judgment lives in Part 2): each of {opus, codex, fable} reviews:
- `runs/statfem_freq_2026-06-10/fable/part2/`   label `fable_part2`
- `runs/statfem_freq_2026-06-10/CODEX/part2/`   label `codex_part2`
- `runs/statfem_freq_2026-06-10/opus/part2/`    label `opus_part2`  (after Opus run finishes)

Optional (Part 1 = replication; less to critique, but carries the prior-fragility beat):
- `.../fable/part1/`, `.../CODEX/part1/`, `.../opus/part1/`  labels `*_part1`

Result: `challenger_reviews/<reviewer>__<target>.md`, e.g. `codex__fable_part2.md`.
The diagonal cells (reviewer model == runner model, e.g. `codex__codex_part2`) are
SELF-REVIEWS — keep them; they are a finding, not a confound.
