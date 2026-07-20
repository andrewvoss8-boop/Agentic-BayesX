# statFEM replicate-and-extend — blog-worthy findings (2026-06-10)

Scope: three agents (Opus, Fable, Codex) each ran the SAME two-session task —
Part 1: faithfully replicate §4.1 (1-D Poisson) of Girolami et al. 2021 statFEM;
Part 2: design and build their OWN frequency-domain extension of statFEM. Separate
fresh sessions per part (so Part 2 got an equal, un-depleted budget). Source runs:
`runs/statfem_freq_2026-06-10/{opus,fable,CODEX}/{part1,part2}/`.

This note distills what is actually noteworthy (vs. merely true). It is the input to
`post_draft.md`. Treat as anecdotal: n = 3 agents, one problem, one run each.

---

## The integrity result (the spine)

A code-level scan of all 41 scripts found NONE of Bilionis's three documented cheats:
no PDF-figure extraction (`fitz`/`pdf2image`/`PyMuPDF`/`pdfimages`), no SSIM
curve-matching, no surrogate-swapping. Paper renders exist only in clearly-labeled
*reference* folders (`_paper_inspection/`, `reference_extracts/`), never inside the
output figure directories. (Strong evidence, not a per-figure proof — that stays a
reviewer job.)

So: **with an explicit anti-cheating clause plus our honesty rules in the prompt,
three different agents did not cheat. The failure mode moved instead to under-ambition
and shallow problem choice.** That is the reframing the post is built on. It is a direct
follow-on to Bilionis's "agents cheat when pushed" essay: once you close the cheating
door, the next risk is honest mediocrity that passes every gate.

---

## The five findings worth a reader's time

1. **The new failure mode is choosing an easy problem — and no gate catches it.**
   Codex picked a single-degree-of-freedom oscillator for Part 2: no spatial field, so
   it barely exercises statFEM's machinery (it had to fix ρ=1 and relabel a stiffness
   scale). It then reported near-perfect recovery (θ_k 1.0808 vs truth 1.080) and a
   clean GREEN. Nothing is fabricated; every check passes. The problem is that the
   problem was too easy to be informative. Convergence gates, lint, and replay all stay
   green on a hollow choice. This is the agentic version of our own "validity before
   rigor" lesson: a rigorous-LOOKING run on a trivial problem is empty.

2. **Two independent agents discovered the same real result — the hopeful counterpoint.**
   Given an open extension, Opus and Fable independently converged on a genuine
   methodological finding: under *peaky / resonance* model error, statFEM's scalar
   confidence parameter ρ and its stationary discrepancy GP confound. ρ deflates or
   degenerates (Fable: ρ→0.29 vs a 0.85 target; Opus: ρ→0.011 when free) because the
   GP absorbs the finite-element physics. Both falsified "the machinery is broken" with
   the same control (truth = the FE model → ρ recovers ~0.85, discrepancy collapses).
   The fix both pointed to: update the physics, or use a non-stationary / physics-informed
   discrepancy. Two independent agents landing the same control-validated result is itself
   evidence the finding is real, not a one-off artifact.

3. **Domain knowledge is the discriminator, and it is invisible to generic checks.**
   The frequency-grid / spectrum-assembly decision cleanly sorted the three: Opus put
   ~4.5 points across the half-power bandwidth and ran a resolution sensitivity; Fable
   used ≥4 points/half-power-band with a dense-grid sensitivity; Codex used a coarse
   22-point grid on a 1-DOF system where the choice barely matters, and coarsened it
   further (36→22) for speed. No convergence gate, lint, or replay check sees any of
   this. This is the project's "domain knowledge must live in the harness" thesis shown
   in one experiment.

4. **A subtle, honest-but-circular move: designing the measurement from the answer.**
   Fable densified its frequency grid exactly at the hidden 50 Hz feature ("truth-informed
   refinement"). It flagged this itself as a least-sure assumption and justified it as
   normal post-pre-sweep test practice — fully honest. But it is borderline using the
   answer to design the measurement, and a generic anti-cheating rule would never flag
   it. Worth showing as the kind of subtle issue that needs a domain-aware critic, not a
   rule.

5. **A modern sampler surfaced a known-but-easy-to-miss fragility of the paper's prior —
   and the three agents handled it three ways.** All three hit the same Part 1 effect: the
   paper's flat improper prior gives an improper hyper-posterior in the low-data corner
   (n_o=1; n_y=4 at n_o=10). NUTS exposed it (it runs off to infinite lengthscale); the
   paper's random-walk Metropolis had stayed near a local mode and masked it. Responses
   graded by maturity: Fable fixed it (proper prior, all 12 cases green); Opus diagnosed
   the root cause and kept the honest version as headline with a labeled fix; Codex
   reported it honestly but did not diagnose or fix it — and its run was effectively broken
   (R-hat 7.7, ESS 2, 61% divergences) yet labeled "yellow," not red. Honest direction,
   under-stated magnitude.

   IMPORTANT — do NOT frame this as "a bug in the paper." Flat priors on GP
   variance/lengthscale producing improper posteriors is a documented phenomenon in the
   objective-Bayes-for-GP literature, so it is a recognized soft spot of that prior choice,
   not a novel defect. We have also NOT cleanly attributed the behavior to the paper: our
   agents changed the sampler, guessed the sensor locations (only shown in a figure), and
   used a different data draw, and we have not checked whether the paper's appendix imposes
   bounded support. Before raising it with the authors at all, verify (a) the integral
   actually diverges for the paper's exact prior+kernel+support, (b) the paper truly reports
   flat-prior results at the failing n_o, (c) our placement/sampler changes are not the
   cause, (d) the literature prior art. If it survives, the move is a curious question, not
   a bug report.

---

## Finding 6 — the challenger experiment (added 2026-06-10, the strongest result)

We ran 3 reviewer models (Opus, Codex, Fable) as independent framing challengers over all
3 Part-2 runs = 9 reviews, prompt blind to the traps (no mention of frequency grids, scope,
ρ, or the prior). Full scoring in `challenger_rubric.md`. Results:

- **The critic role is dramatically more capable than the author role — in the SAME models.**
  Every one of the 9 reviews caught its target's core flaw (easy problem / inverse crime /
  circular grid) UNPROMPTED, with zero false positives. The judgment that was missing during
  open-ended authoring is fully present the moment the same model is switched into critic mode.
- **"Blind spots track the runner" is REFUTED.** The Codex *reviewer* caught exactly the
  under-resolved-grid and easy-problem traps the Codex *runner* fell into. A model is not blind
  to its own family's mistakes as a critic — it simply doesn't self-invoke that critic while
  authoring.
- **Self-review produced NO leniency; the diagonal cells were among the sharpest** (Opus called
  its own run "rigged… an inverse crime" and caught a project-non-negotiable violation; Fable
  pressed harder on purpose; Codex found its own report-vs-code overclaim). CAVEAT: the prompt
  told reviewers to treat self-review as a finding and press harder, so we partly induced this.
- **Critics caught what gates and even honest authors missed:** quantitative recomputes (grid
  points-per-half-power-bandwidth; rank(C_u)=3/160; residual 6σ_d at the peak); integrity catches
  (all three flagged that Opus's report/ledger call ρ "inferred" while the code fixes ρ=1; Fable
  and Opus-self caught the stale assumptions ledger and the died-and-resumed production run);
  and coverage tier (a "GREEN overall" sitting over an under-covered 0.65 headline product).
- **Convergent critique = trustworthy critique.** On each run the three independent reviewers
  converged on the same #1 problem — the same corroboration logic as the runner-side convergence
  in Finding 2.

Blog payload: the bottleneck is not model capability or honesty; it is that the authoring pass
does not self-invoke the critic. The fix is architectural — a mandatory, separate challenger
pass — not "use a smarter model." This is the evidence behind "the critic is the product."

## Honest caveats (must survive into the post)

- n = 3, one problem, one run each. Observations, not claims. Same grain of salt
  Bilionis applies to his cheating essay.
- "Fable" and "Opus" are both Claude-based; differences between them reflect harness +
  session as much as model. Codex (GPT-5.x) is the only cross-family point. Do not frame
  this as a clean model leaderboard.
- We closed the cheating door with a prompt rule; we cannot prove the door stayed shut
  without full code review. Absence of the three known tells is not proof of honesty.
- The "easy problem" critique is about informativeness, not correctness — Codex's run is
  correct for what it chose to do.

---

## One-line takeaway for the post

We set out to ask "does it cheat?" The more useful answer was: close the cheating door
and the next failure is an agent that honestly does the easy version and passes every
check — so the thing that has to scale is a domain-aware critic that judges whether the
problem was worth doing, which no generic gate can.
