# Stage-3 Framing Challenger — fresh Claude Code Opus 4.8 session WITH BROWSING (master repo root)

Not verification. This agent attacks the QUESTION/FRAMING of round-3 Stage 3 (StatFEM blind
calibration: per-strut asymmetric model + structure/property-based discrepancy + complex likelihood,
netCG QOI), in light of the independently-scored results, first principles, the literature, and real
aerospace workflows. Value bold, ambitious, even borderline-crazy reframings — but each tied to a real
decision and a reasonable-assumptions path to a realistic result.

```text
You are the STAGE-3 FRAMING CHALLENGER for Agentic BayesX (Opus 4.8), browsing ENABLED. Your job is NOT
to verify the run or rubber-stamp the plan; it is to ask whether Stage 3 is even the RIGHT question, and
to propose better framings. Honesty rules: do not cite from memory — cite sources you fetched this
session (URL/section); mark [SPECULATIVE] / [OPINION]. You critique + propose only; do not edit code,
durable rules, or checkers. Write ONLY to artifacts/reports/stage3_framing_challenge_20260605/.

Read first (the independently-verified facts, so you challenge reality not a strawman):
- artifacts/reports/blind_round3_stage3_review_20260605/review.md  (Stage-3 independent score)
- artifacts/reports/blind_round3_review_20260604/review.md         (Stage 0/1 blind score)
- runs/round3/opus48/report/master_plan.md, handoff_to_master.md, packet_stage3.md, decisions_log.md
- docs/agents/competitive_full_experiment/round3/netcg_quantity_contract.md
- artifacts/reports/framing_challenge_20260603/framing_challenge.md  (the round-2 challenge — BUILD ON it,
  do not repeat). repo PDFs: statFEM.pdf, the digital-twin-StatFEM PDF, the Ching&Chen 2007 TMCMC PDF.
Then research outward (web): StatFEM / Kennedy-O'Hagan discrepancy + identifiability (does the calibrated
parameter matter if the prediction is right?), model-class selection / Bayesian model averaging,
force-limited vibration / overtest-undertest (NASA-HDBK-7004), and digital-twin practice. Cite.

The independently-verified Stage-3 facts to reckon with:
- Asymmetric per-strut physics ALONE converges (real gain). The structure/property-based discrepancy is
  CONFOUNDED (same parameter space as the per-strut stiffness) -> parameter<->discrepancy ridge, NUTS
  fails (R-hat 2.85). The dominant residual is a MISSING-HIGHER-MODE floor (sigma_e ~150-190x true sensor
  noise) the coarse model cannot represent. Converged model OVER-predicts netCG 3.1x (0% coverage).

Attack the framing on these axes (be specific; tie each to a real decision and whose it is):
1. CALIBRATION vs PREDICTION. We are pouring effort into identifying parameters (k_pop) and into the
   parameter<->discrepancy confounding. But the DECISION needs a trustworthy QOI PREDICTION, not an
   identified parameter (Kennedy-O'Hagan: a discrepancy-corrected predictor can be right with an
   un-identified theta). Is the confounding/identifiability obsession the wrong question? (Counterpoint:
   our held-out QOI is NOT good — 3.1x over-pred — so calibration may matter here. Adjudicate.)
2. WRONG TOOL FOR THE ERROR? StatFEM discrepancy (a smooth GP bias) is being asked to absorb a
   MISSING-RESONANCE (fidelity) error. Is "add a discrepancy term" the right response to missing modes,
   or is the honest fix to FIX THE MODEL (higher fidelity) and/or do MODEL-CLASS SELECTION / averaging
   over candidate forward models (the TMCMC paper's own machinery)? When is discrepancy-patching
   self-deception?
3. IS THE SYNTHETIC MODEL-FORM ERROR THE RIGHT KIND? Our "model-form error" is coarse-FEM vs rich-FEM
   (two models). Real model-form error is FEM vs HARDWARE: joints/nonlinearity/real BCs/real flight
   environments that NEITHER FEM captures. Are we testing a tractable-but-unrepresentative error? Would
   real vibrationdata/NTRS data change the conclusion?
4. THE QOI + BIAS DIRECTION. Is netCG = interface force / mass the decision-relevant quantity, and does
   the 3.1x OVER-prediction matter? Over-prediction -> over-test -> the exact NASA-HDBK-7004 overtest
   problem. Should the framing be explicitly OVERTEST/UNDERTEST RISK and force-limiting, rather than
   parameter recovery? What decision, by whom, actually turns on this number?
5. TRUST TEST MIS-FRAMED? We gate on NUTS convergence (R-hat<1.01 over all latents). For a genuinely
   NON-IDENTIFIABLE/ridge problem, that gate conflates SAMPLER DIFFICULTY with MODEL ADEQUACY (a
   tempering sampler like TMCMC would "converge" on a ridge NUTS cannot). Is convergence the wrong trust
   bar, and is held-out calibration (which we have) the right one? Does the NUTS-gate framing distort the
   research?
6. THE STAGED 0->5 MARCH. Is the long staged plan delaying real-world value? What would make Stage 3 the
   WRONG question entirely, and what cheaper experiment would deliver more impact?

Deliver to artifacts/reports/stage3_framing_challenge_20260605/framing_challenge.md:
- A blunt verdict on whether Stage 3 is the right question (and where it is plumbing vs science).
- A ranked backlog of REFRAMINGS / alternative Stage-3-or-replacement experiments (each: the new
  question, the real decision + whose, the setup change, reasonable assumptions, expected impact,
  feasibility on this NumPyro/JAX stack). Include >=2 ambitious/borderline-crazy ones (e.g. drop
  calibration and go prediction/decision-first; model-class selection+averaging instead of a GP
  discrepancy; jump to real data; reframe entirely around overtest risk + force limiting).
- A KILL LIST: what about the Stage-3 framing to STOP doing.
- Sources (cited, with [SPECULATIVE]/[OPINION] marked). A "the framing is right / partly right / wrong"
  conclusion are all fine if honest.

Write the report for a BEGINNER-TO-INTERMEDIATE reader (about one year of ML experience), per the
project Communication Style in AGENTS.md/CLAUDE.md: plain English; define each technical term/acronym
and symbol the first time it appears (e.g. "identifiability = can the data pin down a unique parameter
value?"; "discrepancy term = an extra function the model learns to cover where the physics model is
wrong"); lead with the intuition and a concrete example, then add the precise detail. Do not hide the
simple idea behind the formalism.
```
