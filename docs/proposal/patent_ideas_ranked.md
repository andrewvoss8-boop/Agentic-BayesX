
6-7-26
Material whose microstructure is naturally attenuating to vibration like hyperstructures.  Developed with BOED.  Using concepts from micromechanics

# Patentable / novel ideas, listed and ranked

Andrew Voss. Created 2026-06-06. Lead agent: Claude Code.

Purpose: one place that lists every patentable or novel idea on this project and ranks them.

Honesty banner. None of these novelty claims are verified. The ranking is provisional and is my
judgment, not a legal opinion. Every "novelty" and "prior-art risk" column is a hypothesis until two
things are done: (1) the white-space literature scan (operational modal analysis, input-state
estimation, Bayesian force identification, complex joint impedance in CMS/FBS, dynamic StatFEM), and
(2) a real patent-database / freedom-to-operate search. Sources for each idea are cited to
notes/research_backlog.md (tags B1 to B5) and notes/project_vision.md (sections 5.0 to 5.4).

> **[Lead-agent comments added 2026-06-06 — see "Lead-agent review comments" at the end of this file.
> They include cross-cutting notes (Sec 101 anchoring, IP vehicle per idea, pipeline triage), per-rank
> sharpenings, and one proposed NEW entry (statFEM-driven topology optimization + the Doehring/ABEMIS
> collaboration path).]**

Ranking criterion: a blend of defensible novelty, value to a real aerospace workflow, how
demonstrable it is with the evidence we can produce, and prior-art risk. Higher rank = stronger
candidate to be (or anchor) the core patent claim.

---

## Ranking table

| Rank | Idea | Defensible novelty (provisional) | Aerospace value | Demonstrable now | Prior-art risk | Role |
|------|------|----------------------------------|-----------------|------------------|----------------|------|
| 1 | The bundle: dynamic StatFEM + unknown stochastic forcing + complex interface impedance + force-limiting load QOI, in a tech-assisted workflow | Medium-High (as a combination) | High | Partly | Medium (combination less owned than parts) | Recommended independent claim architecture |
| 2 | Orthogonal, part-type / stiffness-indexed GP model-form error (the "F(k)" / error-by-part-type method) in dynamic StatFEM | Medium (orthogonality is Plumlee's; the physical indexing + dynamic/FBS context is the distinguisher) | Medium-High | Yes (planned A/B; failure mode already reproduced) | Medium-High | Most testable spearhead / core method claim |
| 3 | Complex (frequency-dependent, lossy) joint/interface impedance as the StatFEM discrepancy/parameter in FBS/CMS (the "rattlebasket") | High (if it survives the joint-dynamics literature) | High (the load lives at the interface; Relativity-relevant) | Not yet | High (jointed-structure dynamics is a deep field) | Candidate core mechanism inside Rank 1 |
| 4 | Unknown-stochastic-forcing dynamic StatFEM (output-only / ambient) carried to a load QOI | Medium-High (Kiran review flags output-only updating as un-researched) | High | Not yet | Medium-High (OMA / input-state estimation is mature) | Candidate core axis inside Rank 1 |
| 5 | Tech-assisted / autonomous updating from technician-collected data on installed parts | Medium (as a system/workflow) | High (real pain point; most fundable) | Partly (the agentic harness exists) | Medium | Workflow / system claim; commercial story |
| 6 | QOI-weighted / decision-relevant likelihood (weight the fit near the load-driving resonance, not flat RMS) | Low-Medium | Medium | Yes (clean methodological change) | Medium (weighted-loss calibration exists, e.g. Plumlee 2.3) | Dependent claim / paper result |
| 7 | QOI-driven / identifiability-aware parameter selection (learn the parameters the load is most sensitive to) | Low | Medium | Yes | High (Fisher-information / subset selection is standard) | Dependent claim / supporting |
| 8 | QOI-targeted optimal sensor placement + excitation design, including drive-point "echolocation" | Low | Medium-High | Partly | High (BOED, Papadimitriou QOI-OSP) | Supporting / future scope |
| 9 | GP emulator of the forward model + reduced-order modal truncation for tractable QOI-posterior integration | Low | Medium (enables full-size models) | Partly | High (Surer-Plumlee-Wild; standard surrogate methods) | Enabling machinery, not a spearhead |
| 10 | Vibe-test-to-failure (qualify until it breaks) to find limits and weak links | Low (as IP) | Medium-High (industrial) | No | n/a (process, not a method) | Parked; Relativity talking point |
| 11 | Apparent-mass framing (M = F/a, independent of forcing level) used to resolve the input/system ambiguity under unknown forcing | Low (the framing is standard 7004) | Medium (conceptual enabler) | Partly | High | Enabler, not a standalone claim |

Not patentable, listed for completeness: the held-out-calibration trust gate (this is cross-validation,
standard practice; it is our verification method and a strength of the work, not IP).

---

## Detail per idea

### Rank 1. The bundle (recommended claim architecture)
What it is: a method that takes dynamic StatFEM to an assembled aerospace structure under unknown
operational forcing, represents the model error where it physically lives, and outputs a
force-limited load QOI with held-out-validated uncertainty. Source: research_backlog B1/B3/B5;
project_vision 5.0/5.4.
Why ranked first: the individual pieces (Ranks 2 to 4) each face real prior art, but the combination
is what no one has shown end to end, and it is the honest reading of the Kiran review (the two
literatures, StatFEM and Bayesian FE updating, have not met; output-only updating is un-researched).
A patent is usually strongest as one independent claim over the combination plus dependent claims for
the mechanisms. Caveat: a combination claim is only as strong as its novelty over the nearest single
prior-art workflow; that is exactly what the lit scan must establish.

### Rank 2. Orthogonal, part-type / stiffness-indexed model-form error (the F(k) method)
What it is: describe the model error by the type of structural part (joints, welds, panels) or by
element stiffness, as a Gaussian process that enters on the output orthogonally to the calibrated
parameters, so the math can separate real physics from model error. Source: project_vision 5.2;
research_backlog "Novelty/patent".
Why this rank: it is the most demonstrable idea we have. We already reproduced the failure mode (a
same-parameter-space discrepancy confounds and the posterior collapses or will not converge, Stage 3),
and the planned A/B (orthogonal output-space version beats the same-space version on a validated FEM
and real data) is both the thesis result and the non-obviousness evidence. Honest limit:
orthogonality-to-the-gradient is Plumlee (2017), so standalone novelty is modest; the distinguisher is
the physical part-type / stiffness indexing in a dynamic, substructured, load-QOI context. The
orthogonal output-space version is currently UNTESTED.

### Rank 3. Complex interface impedance as the discrepancy lever
What it is: model the joint/interface as a complex, frequency-dependent, lossy impedance (nonlinear
joint stiffness and micro-slip damping, the "rattlebasket") and treat that as the uncertain element
StatFEM learns. Source: research_backlog B1.
Why this rank: highest potential value (the interface is where the load of interest lives and where
the model is most wrong) and possibly the strongest novelty, but it is unproven by us and sits on top
of a deep jointed-structure-dynamics literature (Brake, Allen, Iwan/whole-joint models), so the
prior-art risk is high until the scan. Best treated as the core mechanism inside Rank 1.

### Rank 4. Unknown-stochastic-forcing dynamic StatFEM
What it is: run StatFEM output-only, with the forcing unknown and stochastic (operational/ambient),
which is the same problem as operational modal analysis and joint input-state estimation. Source:
research_backlog B2; project_vision 5.0/5.1.
Why this rank: the Kiran review explicitly says output-only updating has not been researched, which is
real white space, but the adjacent OMA and input-state-estimation field (Brincker, Van Overschee-De
Moor, Au, Lourens, Maes, Gillijns-De Moor) is mature, so the novelty has to be in carrying it into
StatFEM and to a load QOI, not in output-only ID itself. Core axis inside Rank 1.

### Rank 5. Tech-assisted / autonomous updating on installed parts
What it is: equip technicians to collect the right data (where to hit, where to measure) on installed
parts, and have an agentic workflow do the updating and the trust check, replacing piecemeal
trial-and-error between the dynamicist and the responsible engineer. Source: research_backlog
"Experiment design & sensing"; project_vision 5.3.
Why this rank: arguably the most fundable and most practically valuable piece, and the part most
aligned with the lab's autonomous-engineering interest. As IP it is a system/workflow claim, which is
real but generally harder to defend than a specific method, so it supports rather than leads.

### Rank 6. QOI-weighted likelihood
What it is: weight the likelihood by what matters to the load decision (the QOI-driving resonance)
instead of treating every frequency point equally with a flat RMS/L2 fit. Source: research_backlog
B4; project_vision references Plumlee 2.3 (weighted-measure loss).
Why this rank: a clean, defensible methodological improvement that pairs with the "loss defines the
parameter" idea, but it is narrow and weighted-loss calibration already exists, so it is a dependent
claim or a paper result rather than a spearhead.

### Rank 7. QOI-driven parameter selection
What it is: choose which parameters to free based on what the load is most sensitive to, so you do not
ask the data to identify more than it can support. Source: research_backlog problem 1.
Why this rank: valuable for identifiability, but built on standard machinery (Fisher information,
subset selection, Bayesian model selection), so low novelty. Supporting.

### Rank 8. QOI-targeted sensor placement + excitation design (drive-point "echolocation")
What it is: place sensors and choose excitation (type, location, amplitude) to learn the most about
the load QOI; make drive-point measurement (force and response at the same DOF, hit-and-listen at the
interface) the backbone because it is information-rich for apparent mass/impedance. Source:
research_backlog problem 2 and "Experiment design & sensing".
Why this rank: high practical value but heavily prior-arted (Bayesian optimal experiment design,
Papadimitriou QOI-driven optimal sensor placement). Future scope, not a spearhead.

### Rank 9. Emulator + reduced-order for tractable QOI integration
What it is: replace expensive FEM runs with a Gaussian-process emulator and reduce model size with
modal truncation, so integrating over the parameter space to get a QOI posterior is affordable on
full-size models. Source: research_backlog problem 3.
Why this rank: necessary enabling machinery, but standard (Surer-Plumlee-Wild and the broader
surrogate literature), so low novelty.

### Rank 10. Vibe-test-to-failure
What it is: qualify a part until it breaks to find the true limit and the weak links. Source:
research_backlog "Relativity scope".
Why this rank: a strong industrial idea about margins and weakest links, but it is a testing
philosophy, not a method, so it is parked as a Relativity talking point rather than IP.

### Rank 11. Apparent-mass framing as the input-ambiguity bridge
What it is: use M = F/a (a structural property independent of forcing level) to bridge the input/system
ambiguity that appears under unknown forcing. Source: project_vision 5.1.
Why this rank: a useful conceptual enabler, but the apparent-mass framing itself is standard
(NASA-HDBK-7004), so it is an enabler, not a standalone claim.

---

## Recommended claim architecture (provisional, pending the scan and FTO)

- Independent claim: the Rank 1 bundle (dynamic StatFEM + unknown operational forcing + complex
  interface impedance + force-limited load QOI + held-out-validated uncertainty in a tech-assisted
  workflow).
- Dependent claims, strongest first: the orthogonal part-type-indexed model-form error (Rank 2); the
  complex-interface-impedance mechanism (Rank 3); the output-only forcing treatment (Rank 4); the
  QOI-weighted likelihood (Rank 6); the parameter-selection and sensing methods (Ranks 7 to 8) as
  further dependents.
- File a provisional early and keep a dated conception record for the orthogonal part-type method
  (project_vision 5.4 TODO).

## Gating actions before any claim is locked

1. White-space literature scan (the targets above). This can move several ranks.
2. The orthogonal-vs-same-space A/B on a validated FEM and real data (turns Rank 2 from hypothesis to
   evidence).
3. A real patent-database / freedom-to-operate search.
4. Disclose to the Senior IP Officer before any public disclosure (Substack, paper, talk), per the IP
   plan (project_vision 9).

---

## Lead-agent review comments (2026-06-06)

These are my (Claude Code, lead agent) comments on the list above. They are judgment, not legal opinion,
and they inherit the same honesty caveat: every novelty/prior-art read here is a hypothesis until the
literature scan and a real patent-database / freedom-to-operate (FTO) search are done.

### Cross-cutting (apply to the whole list)
1. **Sec 101 / eligibility is the shared threat.** Every Rank 1-9 idea is algorithm-flavored, so it faces
   the US abstract-idea (Alice) hurdle: "a method of computing a posterior" can be rejected. Anchor every
   spearhead claim to a physical structure/process/article — e.g. "a method of TESTING / UPDATING a model
   of / DETERMINING a design margin for a physical structure, comprising ... [the inventive step] ... and
   producing [a load estimate / test profile / manufactured article]." You can also write apparatus/system
   claims (sensors + actuator + processor configured to ...) WITHOUT building hardware — an enabling
   written description is a "constructive reduction to practice." Suggest adding a one-line "Sec 101 anchor"
   to each of Ranks 1-3.
2. **Decide the IP VEHICLE per idea — the doc doesn't yet.** Who owns/files each is not stated. Options:
   Purdue/PRF (they pay/prosecute, you are named inventor + ~1/3 share), Doehring/ABEMIS (existing patent
   machine; see the new entry below), Relativity (needs a contract), or solo (you pay, you own). Different
   ideas want different homes; sort ownership UP FRONT and keep the disclose-before-publish discipline.
3. **These are pipeline candidates, not commitments.** Run cheap novelty triage (Lens.org / Google Patents
   / Espacenet — the patent databases the lit reads could NOT reach) on the top 3 BEFORE investing. Your
   bottleneck is triage + specificity + finishing ONE, not generating more ideas.
4. **"Demonstrable now" is honest only for Ranks 2/6/7/9.** Ranks 1, 3, 4 are hypotheses; per
   project_vision the patent exists only if the methods actually work. Consider relabeling 1/3/4 as
   "Demonstrable: No (hypothesis)" so the table doesn't read stronger than the evidence.
5. **Enforceability footnote.** A method run inside a private engineering workflow is hard to detect/
   enforce (less important to you since you are not commercializing, but it affects whether a company or
   Doehring would spend filing dollars). Apparatus/ARTICLE claims (a manufactured optimized structure) are
   far easier to detect — another reason the design-side / topology track below is attractive.

### Per-rank
- **Rank 1 (bundle):** sharpen the novelty caveat. project_vision flags Schneider et al. (Kiran ref [184]):
  a multiplicative model error correlated in both SPACE and FREQUENCY already exists. So the combination's
  defensible novelty must rest on **unknown/output-only forcing + the load QOI + the StatFEM<->Bayesian-FE-
  updating bridge**, NOT on discrepancy-correlation itself. Add this to the Rank-1 caveat.
- **Rank 2 (F(k) method):** agree it is the spearhead, but "Demonstrable now: Yes" is optimistic — the
  same-parameter-space version is reproduced as a FAILURE (Stage 3); the ORTHOGONAL output-space version
  (the actual claim) is UNTESTED. The A/B IS the gating non-obviousness evidence; until it runs this is
  "demonstrable in principle." Keep at #2.
- **Rank 8 (sensor placement / echolocation):** re the robotic-OED-device idea discussed 2026-06-06 — a
  physical robot would help Sec 101 but WORSEN novelty (robotics + OED + modal testing is crowded) and
  explode scope (a "bigger plan" red flag vs the simple-objective steer). Cure Sec 101 via apparatus claims
  on paper instead; keep the robot as future/vision, not a build.

### Proposed NEW entry (adjacent DESIGN-SIDE track — deliberately not slotted into the updating table)
**statFEM-discrepancy-driven / uncertainty-aware topology optimization.** Optimize or attenuate a structure
against a StatFEM posterior that INCLUDES the calibrated model-form discrepancy (especially the Rank-2
part-type / interface discrepancy), instead of against a deterministic nominal FE model. Plain version:
"design this lattice/tray to attenuate vibration while accounting for the fact that the joints/interfaces
have a calibrated, uncertain error we learned from test data."
- Defensible novelty (provisional): **Medium-High.** The topology-optimization CORE is 30+ years crowded,
  but the *uncertainty-aware-with-a-data-CALIBRATED-discrepancy* intersection looks sparse (papers-only
  read): robust/stochastic TO propagates INPUT uncertainty through a TRUSTED model; StatFEM has not been
  fed into a design loop.
- Aerospace value: Medium-High (ties your calibration work to a real design decision — lighter trays /
  attenuation; Relativity- and Doehring-relevant). Demonstrable now: No. Prior-art risk: Medium for the
  intersection, HIGH for the TO core + heavy unseen industrial NVH/AM filing.
- Role / vehicle: a SIBLING track and your clearest COLLABORATION path. Per a 2026-06-06 web read (papers
  + Google Patents hits, NOT independently FTO-verified here), Doehring/ABEMIS holds a mesh-to-lattice-
  generation + additive-manufacturing patent family (US10585420B2 / US11327465B2 / US12111630B2) that does
  NOT claim dynamic/attenuation objectives, plus "AI provisionals" pending. Your discrepancy-aware design
  objective sits ADJACENT TO BUT CLEAR OF his geometry claims -> a real co-invention opportunity with an
  existing patent machine and attorney relationships. An ARTICLE claim (the optimized manufactured
  structure) also sidesteps Sec 101 cleanly.
- Action before investing: ask Doehring what the "AI provisionals" cover, to scope clear of his pending
  art. Confirm everything with a real patent search; the white-space read is papers-not-patents.

### One strategic note
Even if the summer study yields no patent, the Rank-2 discrepancy work is the INPUT to this design-side
track and to Ranks 3/4 — so the capability compounds. Treat the patent as a byproduct of finding what makes
StatFEM actually work in your domain, not as a target to steer the research toward.
