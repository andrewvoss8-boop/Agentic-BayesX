# Research Backlog + Notes Synthesis

Living doc. Created 2026-06-06 from Andrew's multi-day notes. Lead = Claude Code.
Purpose: internalize/organize the brain-dump, respond with a take on each, and keep a priority list.
Tags: [DECIDED] settled; [OPEN] needs a decision/work; [TAKE] my recommendation; [ANSWER] factual reply.
Style: plain English; terms defined on first use.

## BURN-DOWN 2026-06-08 (what is now closed / tracked elsewhere / still open)
The detailed checklist below is the original audit trail; this block supersedes its status.

CLOSED or moved to a durable home:
- Novelty candidates (complex interface, param-selection, the method stack, tech-assisted workflow):
  captured + ranked in docs/proposal/patent_ideas_ranked.md. Track there, not here.
- B2 unknown-forcing == OMA; B3 "Bayesian modal updating already done"; "replace freq-ID w/ Bayesian
  updating"; "how did the bridge paper use ambient data": ANSWERED. Bridge paper now cited in
  docs/proposal/dr_b_briefing.md (Argyris/Papadimitriou, Metsovo).
- B5 force-limiting/overtest reframe: DECIDED and reinforced by the framing challenge.
- Compute (bigger compute / Colab GPUs / run-FEM-little): covered by docs/compute_protocol.md. FEM
  Phase 1 confirmed the modal solves are tiny/fast -> the long pole will be NUTS, not the FEM (as
  predicted); profile before optimizing still holds.
- "What to ask Girolami": ANSWERED -> docs/proposal/girolami_questions.md (with an IP guardrail).
- Agent-file bloat: PARTIALLY done (CLAUDE/AGENTS trimmed) but RE-OPENED: notes/memory.md ballooned
  again with the FEM Phase-1 builder/reviewer logs -> owes an archive pass.

UPDATED:
- B1 novelty location: SHARPENED. The framing-challenge web fetch (2026-06-08) found StatFEM HAS now
  gone dynamic/elastodynamic (recent arXiv, ~2026) + a digital-twin bridge paper. So "dynamic StatFEM"
  alone is NOT the novelty. The still-open bundle = unknown/operational stochastic forcing + complex
  lossy joint impedance + force-limiting LOAD QOI (+ tech-assisted workflow). Still a hypothesis;
  lit scan + FTO still required before any claim.
- Problem #3 tractability: partly answered (FEM is not the long pole; see Compute above).

NEW (from the FEM Phase-1 framing challenge, artifacts/reports/fem_phase1_framing_challenge_20260608/):
- BRIDGE EXPERIMENT: swap Opus's rigid joint for ONE compliant + lossy joint + add forcing + an
  interface-force QOI on an independent synthetic truth, with a held-out check. Smallest change that
  makes the model LEARNABLE and finally touches the novelty surface. (Phase 1 deliberately had none.)
- HARNESS-AS-CONTRIBUTION: name/package the cross-agent verification harness that caught the codex
  faked-independence + composer invalid deck. Near-free; already earned; Bilionis-relevant.
- KILL the staged fidelity march on synthetic data (master_plan Stage 0->5) = the textbook drift
  pattern.

STILL OPEN (carried): the lit scan (NOT yet run); QOI-weighted likelihood (B4, not yet built);
real-data run; drive-point/sensing studies (deferred); vibe-to-failure (parked); Bilionis Substack
(disclosure-gated); Relativity lunch-and-learn (when there is a defensible result).

## The spine — your 3 core problems (everything else is an instance of these)
1. **Match data quality+volume to the number of parameters (given the likelihood).** = the
   identifiability / over-counting problem. Full FRFs/mode shapes are highly correlated, so they carry
   far less independent information than their raw point count (we measured n_eff(k_pop)=0.64 vs ~7920
   nominal). Too many free params vs that true information -> ridges/non-convergence (Stage 3); too few
   -> bias. The discrepancy covariance is the SAME lever (it sets how much you over-count). [TAKE]
   handle with: identifiability/sensitivity (Fisher info, profile likelihood) to know what's learnable +
   evidence-based / sparse selection of which params to free + held-out calibration to detect over/under.
2. **Get data from the most informative locations + excitation (type/location/amplitude).** = optimal
   sensor placement (OSP) + optimal excitation design, targeted at the LOAD QOI. [TAKE] this is real and
   valuable but DOWNSTREAM and heavily prior-arted (Papadimitriou QOI-OSP; OMA; sequential design) — do
   the lit scan before building.
3. **Number of FEM runs required.** = computational tractability. [TAKE] for FEMs this simple the long
   pole is almost surely the NUTS sampling (many likelihood evals x eigensolves), not FEM size; levers =
   GP emulator of the forward model (Surer-Plumlee-Wild), reduced-order/modal truncation, vectorized
   GPU chains. Profile before optimizing.

## The few strategic threads everything reduces to
- **B1 - Where is the novelty? [OPEN, highest-leverage]** After reading Plumlee, orthogonality is his and
  `F(k)` is a base-kernel choice -> modest standalone novelty (vision 5.0). New, possibly-stronger
  candidate from these notes: **complex (frequency-dependent, lossy) JOINT/INTERFACE IMPEDANCE between
  substructures in FBS/CMS** -- the "rattlebasket" nonlinear joint stiffness/damping. This ties together
  (a) Relativity's interest, (b) the StatFEM model-discrepancy lever (the joint is WHERE the model is
  wrong), and (c) unknown forcing (apparent mass M=F/a lives at the interface). Candidate novel bundle:
  *dynamic StatFEM + complex interface impedance + unknown stochastic forcing + force-limiting load QOI*.
  Still a hypothesis; needs lit scan + FTO.
- **B2 - Unknown forcing == Operational Modal Analysis (OMA). [TAKE]** Your "how did the bridge paper get
  mode shapes from AMBIENT forcing?" is exactly OMA: output-only system ID assuming a broadband/~white,
  stationary unknown input, using response cross-spectra/correlations (NExT, SSI, FDD). This is the SAME
  field flagged for the unknown-forcing novelty (Lourens/Maes input-state estimation; Bayesian force ID).
  -> your independent instinct and the lit converge. Scan this field next.
- **B3 - "Bayesian modal-test updating is already done, thoroughly." [DECIDED implication]** So the
  novelty is NOT "Bayesian modal updating." It must be elsewhere: unknown stochastic forcing + a
  force-limiting LOAD QOI + the autonomous/agentic workflow + honest held-out trust. Frame accordingly.
- **B4 - RMS/L2 FRF likelihood treats all errors equally; some matter more. [TAKE, important]** A flat
  RMS likelihood weights every frequency/point the same, but for a force-limiting load the error near the
  QOI-driving resonance dominates the decision. -> use a DECISION-RELEVANT / QOI-WEIGHTED likelihood (or
  Plumlee's weighted-measure loss L(mu), Sec 2.3). This is a clean, defensible methodological move and
  pairs with the "loss defines the parameter" idea.
- **B5 - Reframe around force limiting / overtest. [DECIDED-ish]** The aerospace-defensible decision is
  test level / notch depth (overtest vs undertest), netCG/apparent-mass native (7004c). The 3.1x
  over-prediction we found IS the textbook overtest error. Make this the headline decision.

## Themed checklist (your items, organized, with status + take)

### Novelty / patent / method
- [OPEN] **Complex interface modeling as the patentable kernel?** -> see B1. Strong candidate; may beat
  `F(k)`. Add to vision 5.0 novelty-candidates (pending your OK).
- [OPEN] **Method that picks which params to learn (unidentifiability) / priority param learning.** ->
  problem #1; "learn the params the LOAD is most sensitive to" (QOI-driven selection) is a nice angle;
  established machinery (FIM/subset selection, Bayesian model selection) -> supporting, not spearhead.
- [TAKE] **StatFEM + substructuring + complex joint impedance + model discrepancy** = the method stack.
  Coherent; the novel knot is the complex interface + unknown forcing, not the StatFEM plumbing.

### Experiment design & sensing (problem #2)
- [OPEN] **Everything drive-point, like echolocation?** [TAKE] drive-point FRF (force and response at the
  same DOF) cleanly gives apparent mass/impedance at that point and always shows antiresonances -> very
  information-rich for the interface load. Worth making drive-point the backbone of the test plan;
  "echolocation" = hit-and-listen at the interface. Good instinct; cheap to study.
- [OPEN] **Realistically how many sensors + excitation sources?** -> answerable by an
  info-gain/identifiability study (problem #2) once the model + QOI are fixed; don't guess.
- [OPEN] **Autonomous sequential experiment design for modal test / info gain (excitation type+location)?**
  -> BOED; the agentic angle is the Bilionis-relevant part. Downstream; heavily prior-arted.
- [ANSWER] **Replace freq-ID with maximally-informative Bayesian updating + accel/drive-point placement --
  but hasn't Bayes-in-modal-updating been done? (yes, thoroughly).** Right -> novelty is the WORKFLOW
  (tech-friendly, installed-part, unknown forcing, straight-to-load) + automation, not the Bayesian
  modal updating itself.
- [OPEN] **Equip techs to do freq-ID (where to hit) on installed parts; today it's piecemeal trial-and-
  error between the dynamicist and the RE.** [TAKE] this is a genuinely strong PRACTICAL value story (and
  a real pain point) -> the "autonomous/assisted updating from tech-collected data" workflow is arguably
  the most fundable part; keep it.

### Likelihood / methodology
- [TAKE] **RMS-based FRF likelihood misses consequential errors** -> B4 (QOI-weighted likelihood).
- [ANSWER] **How did the Bayesian bridge paper get mode shapes from ambient forcing?** -> OMA (B2).

### Compute / tractability (problem #3)
- [OPEN] **Script that takes forever locally -> run on bigger compute ("State of the Yard"/cluster).**
  [TAKE] fine; run long jobs in background or on a cluster/Colab. First PROFILE to find the long pole.
- [OPEN] **Colab Pro GPUs faster? Long pole with FEMs this simple?** [TAKE] GPU helps JAX/NumPyro NUTS
  (parallel chains, vectorized linear algebra) more than tiny FEMs; the long pole is likely the
  sampler/eigensolves per step, not the FEM. Emulator + reduced-order are the real levers. (Not profiled
  yet -- honest.)
- [TAKE] **Run the FEM as little as possible, reach a conservative-but-not-too 95% load fast** = the
  practical objective behind problems #1 and #3; emulator + QOI-targeted design + stopping at adequate
  load coverage.

### Real data
- [OPEN] **Use web data (references/aerospace-vibration-data-candidates.md)?** [TAKE] yes -- the cheapest
  first REAL input to expose joint/nonlinear/unknown-forcing error (vision says realistic FEM + real data
  is the trust foundation). Pick ONE record (e.g. a vibrationdata dome-ignition or a GVT set) and run the
  pipeline against it.

### Relativity scope
- [DECIDED] **Focus for Relativity = interface rattlebasket + stiffness/damping nonlinearity; reduce a
  Craig-Bampton (CCB) model of the tray.** Aligns with the complex-joint-impedance novelty (B1).
- [DECIDED] **Initial focus: vibe-driven secondary structures, smooth-line spec, a MAC load; 7004c-style.**
  (MAC load = the enveloping design load; 7004c = NASA force-limited vibration.) Good, concrete.
- [OPEN] **Vibe-test-to-failure (qual-until-it-breaks) to find the limit + weak links.** [TAKE] strong
  industrial idea (margins/weakest-link); a separate testing-philosophy thread, not the StatFEM core --
  park it but keep it (great Relativity talking point).

### Dissemination & people
- [TAKE] **Girolami Data-Centric Engineering (DCE) journal as a backup publication.** Good fit (his
  journal, data+physics fusion). Backup to a conference/structural-dynamics venue.
- [OPEN] **What to ask Girolami (connected on LinkedIn)?** [TAKE] ask the GAP questions, not generic ones:
  has StatFEM been taken to (a) DYNAMIC, (b) UNKNOWN/ambient stochastic forcing, (c) assembled-interface
  (FBS/CMS) loads, with (d) the parameter<->discrepancy identifiability handled? Is the discrepancy-
  confounding (Bryn-O'Hagan/Plumlee) the live blocker he sees? Interest in a dynamic/aerospace
  collaboration? (Keep it specific + show you've read statFEM + the digital-twin paper.)
- [TAKE] **Bilionis delivery = the Substack.** Lead idea = the CHALLENGER AGENT + lit-review pattern;
  supporting = lessons-learned (scope-drift red flag, jargon/communication-style, the blind
  truth/inference split, "blindness proven by the bias"). All disclosure-gated (IP: disclose before
  publishing).
- [OPEN] **Lunch-and-learn for Relativity dynamics / Sanjeev (bring MPL to LA).** Fun + strategic
  (commercial story for the patent). Schedule when there's a defensible result.

### Harness / agent meta
- [ANSWER] **Are the agent files too bloated? hook vs skill vs harness vs AGENTS.md -- best practice?**
  Industry shape: (1) AGENTS.md/CLAUDE.md = ALWAYS-LOADED persistent rules; keep LEAN (<~200 lines) since
  only root is re-injected on compaction -- ours are growing and notes/memory.md is now very long. (2)
  Skills = invocable, task-specific playbooks loaded on demand. (3) Hooks = deterministic, event-
  triggered automation (e.g. run a checker on finish). (4) Subagents = isolated-context workers returning
  a summary. [TAKE] yes, we have bloat: trim CLAUDE.md/AGENTS.md to the load-bearing rules, move the long
  how-to detail into skills/docs, and compress notes/memory.md (archive old CURRENT STATE blocks). Worth a
  dedicated cleanup pass.

## Recommended priority (REVISED 2026-06-08; cheap + decisive first; do NOT over-plan)
1. **BRIDGE EXPERIMENT (Opus): compliant + lossy joint + forcing + interface-force QOI on an
   independent synthetic truth, held-out check.** Smallest change that makes the model learnable and
   first touches the novelty surface. (Framing-challenge fork iii, item A.)
2. **ONE real public dataset, existing pipeline.** First real VALIDATION (not just verification);
   the trust the synthetic work lacks. (references/aerospace-vibration-data-candidates.md; framing item C.)
3. **Lit scan (OMA / input-state / Bayesian force-ID + complex joint impedance in FBS/CMS).** Still
   NOT run; must precede any patent claim. The Girolami questions (docs/proposal/girolami_questions.md)
   partly substitute but do not replace it.
4. **QOI-weighted likelihood (B4)** instead of flat RMS — one clean methodology upgrade.
5. **Name/package the cross-agent verification harness** (framing item D) — near-free, already earned.
6. **Girolami outreach** — questions ready (girolami_questions.md); gated on IP-officer disclosure
   for anything substantive.
- Housekeeping: archive the bloated notes/memory.md CURRENT STATE.
- Defer (until a real result/run is the bottleneck): sensor/excitation-count studies, BOED automation,
  GPU/cluster compute, vibe-to-failure. Capture, don't build yet.
</content>
