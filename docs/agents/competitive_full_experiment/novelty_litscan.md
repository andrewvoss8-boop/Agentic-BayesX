# Novelty / White-Space Lit Scan (#1) — fresh Claude Code Opus 4.8 session WITH BROWSING (master repo root)

Goal: map what is ALREADY PUBLISHED across the fields our work touches, so we know what is OWNED vs where
HONEST WHITE SPACE remains for taking StatFEM into real aerospace structural-dynamics workflows. This is
NOT to confirm a pre-chosen novelty; it is to find where novelty can legitimately emerge (and what we'd
merely be duplicating). Reader role: cite, don't claim from memory.

```text
You are the NOVELTY / WHITE-SPACE READER for Agentic BayesX (Opus 4.8), browsing ENABLED. Honesty rules:
cite every external claim with a source you fetched THIS session (title/author/year/venue/URL or DOI);
mark anything you cannot verify [TO-VERIFY]; mark your own inference [OPINION]. Do NOT assert novelty as
fact (no patent/FTO search is in scope). Write ONLY to artifacts/reports/novelty_litscan_20260606/.

STANCE (read notes/project_vision.md S3.5): we are TEST-DRIVING StatFEM and its neighbors on aerospace
structural-dynamics problems Andrew is a genuine expert in; the patentable bit is whatever makes these
tools WORK in a real aerospace workflow, discovered AS we test. Your job is to chart the territory.

START FROM THE IN-REPO PAPERS (now under references/pdfs/; use them as the map, then go outward):
- "review of Bayesian finite element model updating techniques for structural systems copy.pdf"
  (Kiran, Das & Bansal 2025) -- the state-of-the-art map of Bayesian FE model updating. Use its taxonomy
  and reference list as your spine. KEY in-repo findings to verify and build on: (a) Bayesian FE model
  updating is MATURE (likelihoods in time/frequency/modal domains; Beck-Katafygiotis global/local/un-
  identifiability; model-class selection; hierarchical Bayes; TMCMC; complex & incomplete modal data);
  (b) it NEVER mentions StatFEM (Girolami) -> two separate literatures; (c) it states "Bayesian FE model
  updating using OUTPUT-ONLY time-history data has NOT been researched"; (d) Schneider et al. [184] used a
  model error "correlated in both space and frequency".
- statFEM.pdf (Girolami et al.); digital-twinning ... statistical finite element method.pdf;
  Bayesian_calibration_of_inexact_computer_models_Plumlee_2017.pdf; KennedyOHagan_2002.pdf;
  2007 TMCMC (Ching & Chen); "Bayesian parameter updating in linear structural dynamics with frequency
  transformed data using rational surrogate models.pdf"; "equential ... calibration of expensive
  simulation models.pdf" (Surer-Plumlee-Wild 2024).

THEN SCAN THE WEB for the fields NOT covered in repo, and place each on a "OWNED vs OPEN" map:
1. StatFEM extent: has StatFEM (Girolami/Duffin/Akyildiz) been taken to DYNAMIC problems, FRF/modal data,
   assembled-interface (substructuring) loads, or aerospace? Or only static/quasi-static self-sensing?
2. Operational Modal Analysis / output-only system ID: Brincker FDD, Van Overschee & De Moor / Peeters &
   De Roeck SSI, Au's Bayesian operational modal analysis. What does output-only assume about the input
   (broadband/white/stationary) and what breaks for real aerospace random/transient forcing?
3. Joint input-state estimation / unknown-input force identification: Lourens, Maes, Gillijns & De Moor,
   Naets; Bayesian force reconstruction. How is the input/system identifiability handled?
4. Complex JOINT / INTERFACE impedance in FBS/CMS: Craig-Bampton; frequency-based substructuring; nonlinear
   jointed-structure dynamics (Brake "The Mechanics of Jointed Structures"; Allen/Mayes; Iwan/whole-joint
   models; "rattlebasket"/micro-slip damping). Has Bayesian/StatFEM updating been applied to complex joint
   impedance?
5. Force-limited vibration / apparent-mass LOAD QOI: NASA-HDBK-7004 / Scharton; has anyone connected
   Bayesian model updating or StatFEM to a force-limiting / netCG load decision?
6. Model-form discrepancy in DYNAMIC updating: Plumlee orthogonal GP, Brynjarsdottir & O'Hagan, cut/modular
   Bayes, Sargsyan embedded discrepancy, Schneider et al. (space+frequency-correlated error).

DELIVER (to artifacts/reports/novelty_litscan_20260606/):
- sources.md: every source with full citation + URL/DOI + what it covers + what it does NOT (verified vs
  [TO-VERIFY]).
- whitespace_map.md: a table for each of the 6 areas -> "what is OWNED (with citations)" vs "what is OPEN".
  Then a short synthesis: which COMBINATIONS appear genuinely under-addressed (candidate honest novelty),
  e.g. {dynamic StatFEM} x {unknown stochastic forcing / OMA} x {complex joint impedance} x {force-limiting
  load QOI} x {tech-assisted/automated workflow}. For each candidate, name the closest prior work that
  would threaten it. Mark [OPINION] on the "open" judgments; flag what a real patent/FTO search must check.
- A 5-bullet "what to ask Girolami" list grounded in the gaps you actually find.

Be honest: if an area we hoped was open is already well-owned, say so plainly. A "mostly owned, little open"
conclusion is a valid and valuable result.
```
