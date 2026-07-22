# Decisions log — ShockSat advisor progress-and-closure revision

## D1 — 2026-07-21 human correction to the audience and purpose

The prior six-page decision memo is not the requested artifact. Ilias Bilionis has no ShockSat or agentic-remodeling background beyond the original Bayesian FEM updating/statFEM proposal. The replacement report must remove the "Decision requested" and color-coded research-status sections, introduce every project-specific quantity in context, document the methods and Bayesian details, explain why the original industry-use goal was not achieved, explain the model-form/agentic pivot and its results, and close with Andrew's request for help using the final month well and preserving the right personal and laboratory lessons.

The controlling research objective is Ilias's earlier feedback: build and evaluate the statFEM approach, identify its gaps, and suggest improvements; validation is not assumed possible.

No underlying scientific result will be recomputed or strengthened for this editorial revision. The earlier memo and original source document remain preserved as audit artifacts.

## D2 — 2026-07-21 agentic-remodeling and CLI clarification

The advisor report will distinguish three layers:

1. **Discrete model-form remodeling:** the agent chooses a registered change to connectivity/topology, joint representation, missing hardware or mass, geometry idealization, element formulation, or mesh/discretization. Remeshing is one family, not the whole meaning of remodeling.
2. **Continuous Bayesian updating inside a valid class:** stiffness, density/mass, damping, joint coefficients, nuisance quantities, and discrepancy parameters are inferred after the discrete candidate is built. These scalings are not called remodeling.
3. **Verification and feedback:** deterministic code—not the agent—applies the candidate and owns mechanics gates, data splits, thresholds, budgets, exact scoring, and the final checker.

The current ShockSat pilot already has structured candidate specifications, registered operators, deterministic builders, physics V-gates, train/dev/vault separation, equal-budget random controls, and candidate-own exact scoring. The MPL harness adds resumable file-backed state and schemas. The proposed immutable `remodelctl` CLI and versioned JSON feedback envelope are **not yet implemented as one agent-facing interface**; they are the next skill/harness training increment. The report must not imply otherwise.

## D3 — 2026-07-21 Bayesian failure attribution must survive a skeptical prior/likelihood audit

The advisor revision will not attribute limited posterior movement or wide bands to model form by inspection.
It will compare prior width, likelihood data compression, covariance/independence assumptions, discrepancy
confounding, sampler convergence, spectral resolution, forcing observability, and model-form expressiveness
against checker-backed evidence. A method enters the new FRF comparison only if the same physical channel and
frequency grid can be reproduced from stored arrays with an explicit source run and without mixing posterior,
MAP, and deterministic curves under one label. The user-commented DOCX is preserved; the revised deliverable
will be a separate clean file.

## D4 — 2026-07-21 direct Word edits and FRF bands

Andrew reported that direct prose edits in the preserved Word draft were omitted from the later generated
version. The two user editing-session revision IDs are therefore the recovery authority. Every substantive
changed paragraph/run will be restored in the report builder; a user image placeholder will be satisfied with
a sourced NASA ShockSat photograph rather than left as bracketed text.

For Section 5.4, uncertainty will be reconstructed only where stored draws support it. The converged modal
NUTS draws support a parameter-propagation envelope, but the modal likelihood did not model FRF-amplitude
discrepancy, so it is not called a calibrated FRF predictive interval. The whole-FRF draws support a pointwise
posterior-predictive calculation including fitted discrepancy/noise variance, but the fold posterior is
non-converged; its band must be printed as NOT TRUSTWORTHY with worst R-hat/ESS. The Beck run retained no
draws and failed NUTS, so it receives no band. This revision performs no new posterior inference.

## D5 — 2026-07-21 external-review consolidation

The initial external review and its later correction are inputs, not authorities. A criticism is implemented
only when it survives comparison with the latest checker-backed artifact. The report will therefore retain the
valid statistical criticisms while adding an explicit supersession ledger:

- the arm-C leakage and basis mismatch were real, but the later four-fold exact repair is current;
- the incomplete exact rerank was real, but the later 28/28 rerank is current;
- the wide-package net-CG port used the wrong quantity contract, but the later validated port reproduces the
  delivered 1.508/2.301/2.526 reference exactly; S3 remains cannot-verify and S4 is not met;
- the later model-form pilot genuinely tests connectivity, mesh, formulation, and geometry, superseding the
  earlier property-heavy search-space criticism.

The report must still expose the original defects because they are methodological lessons. It must not describe
them as unresolved current science.

## D6 — 2026-07-21 Bayesian and model-form reporting corrections

The whole-FRF NUTS posterior has separated chain solutions/global under-identification. The free-discrepancy M2
target has a boundary-seeking, weakly identified variance scale. The bounded IFT beta target is computationally
reproducible but learns much lower physics trust. These are three different findings and will not be collapsed
into one word such as "multimodal" or "singular."

Model-form results will distinguish selected best-of-12 candidates from class-mean controls. The best values are
exploratory and selection-biased; the class means are the preregistered multiplicity control. The report will add
posterior contraction from the stored converged modal draws, but it will not claim per-parameter identifiability
because the full nine-group strain-energy/Fisher decomposition at the realized discrepancy floor was not completed.

Raw TMCMC samples for the IFT and M2 comparisons were not retained in the reportable artifact set. The revision
will use the stored run summaries and will not fabricate trace or pair plots.

## D7 — 2026-07-22 recover the converged modular predictive twin in Section 5.4

Andrew identified an omitted retained result: the L5 working twin combines a converged modal-frequency NUTS
posterior with a marginal log-amplitude model-discrepancy term estimated on observed channels and transferred
to held-out channels. This is a two-stage or modular predictive construction. It is not evidence that a joint
whole-FRF StatFEM posterior converged. Both facts must appear together.

Figure 5.4 will use the frozen `statfem_real_validation_20260617/out/mc_cache.npz` arrays. It will show two
channels from held-out split seed 10: DAQ 20, selected for improvement from the original FEM, and DAQ 24, which
remains far from the data after updating. Each panel will contain only measured FRF, original FEM, updated
posterior median, the parameter-only 5th–95th percentile envelope, and the total 5th–95th percentile predictive
envelope after adding the observed-channel-estimated discrepancy. The plot will not show hit-quality shading,
a quality axis, failed whole-FRF curves, Beck curves, per-panel diagnostics, or secondary annotations.

The report will call the inner interval a posterior parameter-propagation envelope and the outer interval a
modular posterior-predictive envelope. The failed joint whole-FRF and older Beck-target diagnostics remain in
the method table rather than on the FRF. Prior DOCX files remain immutable; this correction produces a new
revision artifact.
