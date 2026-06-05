# TMCMC 2DOF Identifiability Comparison — fresh Claude Code Opus 4.8 session (master repo root)

Compare OUR 2DOF/MDOF toy findings against the canonical 2DOF identifiability results in Ching & Chen
(2007), especially the attached Fig. 1 (unidentifiable / locally identifiable / globally identifiable).
This is a reader/reviewer task: read the paper, read our findings, compare honestly, cite.

```text
You are a LITERATURE-COMPARISON reviewer for Agentic BayesX (Opus 4.8). Compare our 2DOF/MDOF Bayesian
model-updating findings to Ching & Chen (2007), "Transitional Markov Chain Monte Carlo Method for
Bayesian Model Updating, Model Class Selection, and Model Averaging." Honesty rules: cite the paper by
section/figure/equation/page from the actual PDF (do not cite from memory); distinguish what the paper
SUPPORTS vs what is OUR extension; mark [SPECULATIVE]/[TO-VERIFY]. Write ONLY to
artifacts/reports/tmcmc_2dof_identifiability_review_20260605/review.md. Do not edit any other file.

READ THE PAPER (in repo root):
- 2007-transitional-markov-chain-monte-carlo-method-for-bayesian-model-updating-model-class-selection-and-model-averaging.pdf
  Focus on: (1) the 2DOF example and its structural/likelihood model (the k1,k2 stiffness updating); (2)
  the IDENTIFIABILITY taxonomy and Fig. 1 — "(a) unidentifiable, (b) locally identifiable, (c) globally
  identifiable" — i.e. the posterior in (k1,k2) is a CURVED RIDGE / MANIFOLD (a), discrete MULTIPLE modes
  (b), or a single point (c); (3) WHY TMCMC is proposed — it tempers from prior to posterior to handle
  MULTIMODAL / ridge / peaked posteriors that single-chain Metropolis (and, by extension, single-chain
  HMC/NUTS) struggle with; (4) any model-class-selection / evidence machinery if relevant.

READ OUR FINDINGS:
- artifacts/reports/blind_round3_stage3_review_20260605/review.md  (Stage-3 independent score)
- artifacts/reports/blind_round3_review_20260604/review.md        (Stage 0/1 blind score)
- runs/round3/opus48/report/packet_stage3.md, blind_known_failures.md, decisions_log.md
- artifacts/reports/fresh_2dof_statfem_fbs_20260601/ (our earlier 2DOF StatFEM/FBS: full-vs-peak
  likelihood, parameter identifiability of k1/k2/fn/damping)
- For context only: AGENTS.md / CLAUDE.md (NUTS gate, convergence definition).

COMPARE (the core of the task):
1. MAP OUR POSTERIORS ONTO THEIR TAXONOMY. For each of our key cases, classify it as Fig-1
   unidentifiable (ridge), locally identifiable (multimodal), or globally identifiable (single mode),
   with evidence:
   - frequency-only discrepancy (Stage 0/1): the sigma_d<->sigma_e RIDGE + multimodal non-convergence
     (R-hat 2.41).
   - structure/property-based per-strut discrepancy (Stage 3): the parameter<->discrepancy RIDGE
     (k_pop de-identified, sigma_d->1.33, R-hat 2.85, ESS 4.7) — confounded because the discrepancy sits
     in the SAME parameter space as the per-strut stiffness.
   - per-strut ASYMMETRIC physics alone (Stage 3): CONVERGED (R-hat 1.009) = globally identifiable.
   - our fresh-2DOF full-vs-peak likelihood (peak-feature widened the intervals ~20-27x on fn) — relate
     to identifiability/observability.
   Does our ridge phenomenology MATCH the paper's Fig-1(a) curved (k1,k2) manifold qualitatively?
2. SAMPLER IMPLICATION. The paper's thesis is that TMCMC handles exactly the unidentifiable/multimodal
   cases. Our NUTS FAILED precisely on our ridge/multimodal posteriors (R-hat 2.85, ESS 4.7, n_eff<1,
   starve-data shows the ridge is STRUCTURAL not data-deluge; grid-invariance intractable under the
   ridge). Does the paper SUPPORT trying TMCMC (or another tempering/SMC or ABC) for our confounded/ridge
   cases where single-chain NUTS cannot mix? State precisely what TMCMC would and would NOT fix (it
   samples a ridge/multimodal posterior correctly, but a STRUCTURAL non-identifiability/confounding
   remains non-identifiable regardless of sampler — a better sampler reveals the ridge, it does not
   remove it). This is the evidence base for a possible future "NUTS vs TMCMC/ABC" round.
3. WHAT THE PAPER WOULD PRESCRIBE for our identifiability problems vs what WE prescribed (orthogonal /
   modular-cut discrepancy + higher-fidelity FEM). Are they consistent? Does the paper offer
   model-class-selection / evidence as an alternative lens on our with-d-vs-without-d comparison?
4. HONEST DIFFERENCES. Their 2DOF is a specific stiffness/modal updating problem; ours adds a StatFEM
   discrepancy term, hierarchy (build-to-build), MDOF + complex FRF, and a netCG QOI. Note where the
   analogy holds and where it breaks; do not overclaim equivalence.

OUTPUT: review.md with (a) a short summary of the paper's 2DOF identifiability result + Fig. 1 (cited),
(b) a mapping table (our case -> their taxonomy -> evidence), (c) the sampler implication (does TMCMC
help us, and where it cannot), (d) consistency of prescriptions, (e) honest differences/caveats, and a
sources list with page/section/figure citations. A "they agree", "they partly agree", or "they diverge"
conclusion are all fine if honest.
```
