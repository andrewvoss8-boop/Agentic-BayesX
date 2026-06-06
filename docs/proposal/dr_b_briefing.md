# Stress Testing a Hierarchical Digital Bayesian Twin for Aerospace Structures
**(GUI5, ASDRL 2.0)**

Andrew Voss. Updated 2026-06-06. For Dr. B.

Two parts: a one-page executive summary with my proposed answers to the IP questions, then a
detailed description that works through each point, the framework choice, the data, the experiment,
the literature, and the patent questions in full.

---

# Part 1: Executive summary (one page)

Framing. Traditional aerospace model updating and uncertainty quantification is a PT Cruiser.
StatFEM (Girolami's statistical finite element method) is a track Porsche, but the published work
has only driven it at 5 mph around a parking lot: simple, static problems where the model already
matches the test data. I want to take it onto the track: real dynamic structures, learning the
physics from test data, and pushing the result to a real engineering decision. That requires a few
new methods, which is where a patentable contribution lives.

## What is the big problem/need? What happens if we solve it?

In aerospace, predicting loads and updating models with test and flight data is slow, inconsistent,
and poor at accounting for model error. A launch vehicle fails if any single part is under-designed,
so teams add conservatism everywhere; parts look marginal on paper yet often carry large true
margins. Solve it and structures can be 5 to 10 percent lighter with more confidence, and the
design, test, and verification process becomes consistent and defensible, with risk placed where it
actually is.

## What other people have done to address the problem

- Girolami's group built StatFEM and used it for digital twins, separating model prediction, model
  error, and sensor noise, on simple near-static cases where the model already matched the data.
- Adjacent tools exist separately: Bayesian model updating, substructuring (CMS/FBS), operational
  modal analysis and force identification, sensor placement, and the NASA force-limiting /
  apparent-mass methods used in vibration testing.
- The state-of-the-art review of Bayesian FE updating (Kiran et al., 2025) does not mention StatFEM.
  The two literatures have not met.

## What are the remaining knowledge gaps

Two places StatFEM has not gone:
- A modern aerospace workflow, end to end, to a real load and verification decision.
- The data and system types aerospace uses: random vibration, transient, and shock, and
  assembled-structure methods (component mode synthesis, frequency-based substructuring).

Getting there means solving three problems:
1. Matching data quality and volume to the number of parameters, accounting for the likelihood
   function. Too many parameters for the available, informative data gives an unidentifiable or
   artificially confident result. We have reproduced this failure in a small example.
2. Getting data from the most informative sensor locations and excitation (type, location,
   amplitude).
3. Keeping the computation tractable on full-size models:
   - the number of FEM runs required; reducing model size and runtime;
   - formulating likelihood functions that are computationally tractable and accurate, not
     oversimplified, and that do not artificially collapse the posterior;
   - integrating over the parameter space to get a posterior for the QOI;
   - automating the workflow with agentic engineering.

## My objective is to

Build and validate a dynamic StatFEM digital twin of a realistic aerospace part (a subscale avionics
tray), learn its physical properties from real vibration data, produce an honest estimate of the
load that matters (interface force, net-CG load, force-limiting level), and develop the method that
keeps the inference from collapsing.

## My approach is as follows

- Framework. StatFEM as the backbone: it is the candidate built for calibrated prediction under a
  wrong model, sequential updating, and interpretability (the prior is the FE model; the error term
  says where the model is wrong). Verify this choice against classical modal Bayesian updating on the
  same case rather than assume it. StatFEM alone is not sufficient: unknown forcing needs an
  operational-modal / input-state / force-identification front end; identifiability needs a
  structured error term; build-to-build and flight-to-flight scatter needs hierarchical Bayes.
- New method (candidate patent). Describe model error by structural-part type (joints, welds,
  panels) rather than by location, which lets the math separate real physics from model error.
  Novelty is a hypothesis pending a literature scan and a freedom-to-operate search; no novelty is
  claimed for Bayesian modal or interface updating itself.
- Experiment. A self-funded subscale tray tested at McCallie under different vibration conditions and
  assembly states; the strut-end joints are the uncertain stiffness and damping element; a compliant
  backing plate so the force-limiting notch appears physically.
- Code. An automated workflow that builds the model, runs the updating, and checks trust by holding
  back data and predicting it (held-out coverage), with NUTS convergence gates.
- Data. Public aerospace datasets (F-16 ground vibration test, Vibrationdata flight and static-fire
  histories, NASA Common Research Model FEM, BAE Hawk) to validate, plus the tray for the
  patent-critical demonstration.
- Later add-on. Sensor placement to learn the most about the loads that matter.

## Patent

- The digital twin is the vision and the value. The patent would be one narrow method inside it
  (model error described by structural-part type). Sensor placement and the automation are
  supporting, not the core claim.
- Prior-art read (papers only, not a patent search): error-by-part-type looks the most novel and
  defensible; the cross-experiment and sensor-placement ideas are more crowded; no blocking patents
  surfaced; freedom-to-operate is not cleared.

## Three questions for you, with my answers

1. Ownership under Purdue's student-IP rules. I am getting a written determination from Sponsored
   Programs and will follow it. My intent is to keep the patent-critical work self-funded and off lab
   resources, which under typical student-IP rules supports student ownership. I will not assume that
   until it is in writing.
2. Advise vs co-invent. I prefer that you advise on the science and the experiment without
   contributing the inventive concept (error-by-part-type), so I retain title. I am open to
   co-invention, which makes it Purdue-owned, if you prefer; either way decide up front. We will
   document contributions. This is not legal advice; counsel and Sponsored Programs govern.
3. Self-funding. Yes. Conception, method development, compute, and the McCallie test stay on my own
   equipment and funds. Lab and sponsored resources can support the broader twin and automation work
   that is not the core claim.

## Next steps

1. Get the IP-ownership determination from Sponsored Programs; read the disclosure procedure.
2. Document conception of the method now, with a date.
3. Run the literature scan, then a patent-database search or attorney clearance.
4. Run the StatFEM vs classical updating comparison on the same case.
5. Build the experiment that shows the method works where the standard approach fails.
6. Pick a conference or journal target for a deadline.

---

# Part 2: Detailed description

## 2.1 Problem and objective

The engineering decision is a load and verification decision: given a finite element model that is
known to be wrong (joints, damping, and boundary conditions are never exactly right) and a stream of
test and flight data, produce an honest, trustworthy estimate of the load that matters (interface
force, net-CG load, force-limiting levels) with uncertainty that is neither falsely tight nor
uselessly wide. The objective is to take StatFEM onto the track: build and validate a dynamic
digital twin of a realistic aerospace part (a small-scale avionics tray), learn its physical
properties from real vibration data, push the result to a real load decision, and develop the new
method that keeps the inference from collapsing or diverging.

## 2.2 Why StatFEM over the alternatives, and why it needs friends

Held against the selection criteria (calibrated prediction under a wrong model, honest model-form
error, sequential updating, ability to handle unknown forcing, interpretability for a certification
audience), the candidates from the Bayesian-updating literature line up like this.

Plain-English terms, defined once. A *Gaussian process (GP)* is a flexible probability distribution
over functions, used here as a "where and how is the model wrong" field. *Calibration* means
inferring physical parameters from data. *Discrepancy* or *model-form error* is the gap between even
the best-tuned model and reality. *Confounding* is when the tuning knob and the error term can trade
off freely, so neither is trustworthy.

- **Classical Bayesian FE model updating** (Beck-Katafygiotis lineage; modal, frequency, or
  time-domain likelihoods; sampled with methods like TMCMC) infers parameters and then predicts by
  running the model at those parameters. It is mature and its identifiability theory is worked out.
  Its weakness for us is that it largely assumes the model form is right and folds model error into
  noise, which produces confident, wrong loads when the model is structurally wrong.
- **Kennedy and O'Hagan calibration plus discrepancy** adds an additive GP on the outputs. Better
  predictions, but the parameter and the discrepancy confound, so the physical parameters can become
  meaningless.
- **Plumlee-style orthogonal discrepancy and Brynjarsdottir-O'Hagan** fix the confounding by putting
  structure on the discrepancy. These are techniques, not a full framework.
- **StatFEM** puts the discrepancy GP inside the FE construction and conditions on sensor data to
  produce a posterior over the true response field that coherently fuses the FE prior, parameter
  uncertainty, model-form discrepancy, and sensor noise. Its native output is the calibrated field
  or QOI with honest uncertainty, updated sequentially.

StatFEM wins as the backbone for three real reasons, not taste. First, our QOI is a prediction under
a wrong model, and StatFEM is the only candidate built primarily to deliver that with model-form
error as a first-class field. Second, the sequential, data-assimilation framing matches "update as
we test, as flights accumulate." Third, interpretability is genuine: the prior is your FE model and
the error term is a field that says where the model is wrong, which is auditable in a way a
black-box correction is not. Access to Girolami is an asset but stays out of the merits column.

StatFEM alone is not enough, and the three tests are what expose it. (1) Unknown forcing: vanilla
StatFEM assumes known input and is demonstrated mostly on static, self-sensing cases, so the
unknown-forcing test needs an operational-modal / input-state-estimation / Bayesian force-ID front
end. This is exactly the gap the Kiran review flags as un-researched. (2) Modal-only data: with a
handful of modal parameters, the field-level error term has little to grip, and classical modal
Bayesian updating may be more direct and cheaper; StatFEM earns its keep with spatially distributed
FRF or field data. (3) Discrepancy confounding applies to StatFEM too, so we need a structuring
constraint to keep parameters identifiable. Conclusion: StatFEM as backbone plus a small, named set
of friends (an input-state / force-ID front end for unknown forcing; a structured error term; and,
where flight-to-flight or build-to-build scatter matters, hierarchical Bayes).

We will not marry StatFEM by assertion. Consistent with the test-driving stance, the first
methodological deliverable is a **framework bake-off**: classical modal Bayesian updating vs StatFEM
on the same synthetic modal-plus-FRF case with injected model-form error, judged by held-out
calibration of the QOI. If StatFEM earns its place, we show it; if it does not, we learn that
cheaply. This is far more defensible to you than "we chose StatFEM because we like it."

## 2.3 The candidate novel method, and the honesty caveats

The new method, the thing that keeps the car on the track, is to describe the model's error by the
type of structural part it comes from (joints, welds, panels) rather than by location on the
structure. Concretely, the error term is a GP whose correlation is keyed to part type and element
properties (high correlation for the same property, moderate for the same element type, low
otherwise), entering on the model output and structured so it does not simply soak up the physics we
are trying to learn. That structure is what lets the math separate real physics from model error in
the dynamic, identifiability-poor regime where the naive approach collapses.

Honesty caveats, because we do not overstate. Putting structure on a discrepancy is not new in
general (Plumlee's orthogonality, Brynjarsdottir-O'Hagan, and Schneider et al.'s space-and-frequency
correlated model error all do versions of it). The specific hypothesis here is that part-type
keying, applied inside a dynamic StatFEM taken to aerospace interface loads with unknown forcing,
is what makes the separation work and is narrow and novel enough to defend. That is a hypothesis
pending the #1 literature scan (operational modal analysis, input-state estimation, force-ID, and
complex joint impedance in CMS/FBS) and a real freedom-to-operate search. We claim no novelty in
Bayesian modal, complex-modal, or interface updating itself, which the Kiran review shows is a
mature, well-covered field.

## 2.4 Data we can work with

We have a ranked shortlist of real aerospace vibration, modal, and FEM data (see
[references/aerospace-vibration-data-candidates.md](../../references/aerospace-vibration-data-candidates.md)).
The plan uses public data to de-risk and validate, and the self-funded tray for the patent-critical
demonstration.

- **F-16 ground vibration test benchmark** (4TU / Eindhoven). Real shaker input and acceleration
  outputs, 1 to 60 Hz, with a wingtip payload interface mode near 7.3 Hz and a nonlinear interface.
  Best public match for a primary/secondary substructuring and interface-load example.
- **Vibrationdata flight and static-fire time histories** (Tom Irvine): SR-19 forward dome ignition,
  Pegasus drop transient (body bending near 9 to 10 Hz). Good for flight QOI and for synthesizing a
  realistic shaker input from a measured payload-interface event.
- **NASA Common Research Model FEM/modal files and Vibrationdata NASTRAN examples** for hardening the
  FEM-to-transfer-function harness against known answers.
- **BAE Hawk full-aircraft modal test** (Sheffield; large) and the small processed Hawk support files
  (Zenodo) for graduating beyond low-DOF surrogates.
- **NASA PIMS / ISS acceleration archives**: real operational response with no measured forcing, so
  they belong to the output-only / unknown-input workflow (the friend we have to build anyway).

Honest cautions from the shortlist: most public aerospace datasets are proprietary, huge, PDF-only,
or processed rather than raw; the best physical match (F-16 GVT) sits at much lower frequencies than
the tray; and the operational archives lack measured input, which is precisely the unknown-forcing
problem.

## 2.5 The experiment (subscale tray)

The patent-critical, controlled experiment is a small, self-funded avionics tray, tested at McCallie
under different vibration conditions and assembly states (see
[docs/lab/subscale_tray_test_setup_status.md](../lab/subscale_tray_test_setup_status.md)). Current
status is design and procurement, not yet assembled or instrumented; I am reporting it honestly.

- **Configuration:** a non-isolated 6-strut hexapod (rigid rod-end joints, no elastomeric isolators)
  with the strut-end joints as the uncertain stiffness and damping element. This deliberately differs
  from the isolated flight tray, and that difference is documented, not hidden. The non-isolated,
  joint-governed case is the hard-to-predict regime that makes the inference worth doing.
- **Physical coupled test:** tray on the hexapod mounted to a compliant backing plate so the
  force-limiting notch appears physically (a rigid plate would over-test and suppress the notch).
- **QOI:** the net interface force (sum of strut forces), a net-CG-style metric, the first natural
  frequencies and damping, and the build-to-build reassembly scatter treated as a first-class output.
- **Biggest practical risk:** instrumentation. We have one accelerometer and no force channel today.
  Closing the loop needs a borrowed instrumented modal hammer (roving-hammer mode shapes) and bonded
  strain sensors on the struts calibrated as load cells, with IEPE conditioning. We are pursuing a
  borrow from LASIR (Vanderbilt) and UTC before paying for rental.

## 2.6 The agentic workflow and the trust gate

The code is an automated ("agentic") workflow that builds the model, runs the Bayesian updating, and
checks the result is trustworthy by holding back data and predicting it. This automation is also the
piece most useful to the lab's broader autonomous-engineering interests.

The trust gate is non-negotiable and is the same at every stage. Held-out calibration is the primary
test: hide whole builds and whole frequency bands, predict them, and check that the 95 percent
intervals actually contain the truth about 95 percent of the time. A tight posterior that fails
held-out coverage is collapse, not success. Supporting checks are a starve-the-data sweep (use very
little data to make overconfidence visible), the effective-vs-nominal sample count (how many truly
independent points the correlated data carries), and a with-vs-without-discrepancy comparison.
Sampling uses NUTS (the modern Hamiltonian Monte Carlo sampler) with at least 4 chains, R-hat below
1.01, adequate effective sample size over all latents including the error-term coefficients and
every hierarchical per-build or per-flight latent, divergences under 2 percent, and a non-centered
parameterization. We do not call the sampler "converged" or the result "honest" unless these pass.

## 2.7 The staged plan (condensed)

The build is staged, each stage with an exit gate (full version in the runner master plan).

- **Stage 0:** trust harness and an honest baseline read of the current model (measure held-out
  coverage; quantify any collapse or bias) before adding anything.
- **Stage 1:** learn all hyperparameters (error-term scale and length-scale, build-to-build scatter,
  sensor noise) instead of fixing them by hand; show the parameter-vs-error-term trade-off is
  controlled.
- **Stage 2:** add real physical parameters (dome and panel stiffness, per-part strut-group
  stiffness, damping) and re-run the identifiability checks.
- **Stage 3:** the novel error-by-part-type term; test whether it catches spatial error the
  frequency-only term cannot, with held-out coverage as the judge.
- **Stage 4:** higher-fidelity FEM (flexible panel, struts with bending, shell dome), kept
  differentiable and fast enough for NUTS, and justified only if the fidelity changes the decision.
- **Stage 5:** one coherent, sequentially updated run that mimics a qualification and loads workflow
  end to end (a fleet of builds and flights), carrying parameter, build/flight, and model-form
  uncertainty into the load decision.

## 2.8 Literature review of the key papers

Read-status reflects what Andrew has read with his own eyes; please correct the "queued" rows. Items
marked agent-read were read in full by the project's reading agent; that is not the same as your
having read them. Where a paper is not in the repo, I give the role and mark the exact citation
[to confirm] rather than guess author or venue.

| # | Shorthand | Role for us | Andrew read-status |
|---|-----------|-------------|--------------------|
| 1 | StatFEM (Girolami et al.) | The backbone: rigorous separation of model prediction, discrepancy, noise | Read |
| 2 | StatFEM digital twin | Closest precedent: StatFEM on a real monitored structure | Read |
| 3 | Joint paper | A simple, replicable interface/joint Bayesian update | Read |
| 4 | Bridge paper | CMS plus modal likelihoods plus real ambient (output-only) data | Read |
| 5 | ABC (Approximate Bayesian Computation) | Fallback when the likelihood is hard to defend | Partially read |
| 6 | Kiran review | The map of Bayesian FE updating; positions our work | Queued (agent-read in full) |
| 7 | Supporting set (KOH, Plumlee, Brynjarsdottir-O'Hagan, TMCMC, rational surrogate, sequential design, force-limited vibration, OMA/input-state lineage) | Techniques and standards we build on or must out-position | Mixed (agent-read; several on Andrew's queue) |

Detail:

1. **StatFEM** (Girolami, Febrianto, Yin, Cirak, "The statistical finite element method (statFEM)
   for coherent synthesis of observation data and model predictions," Comput. Methods Appl. Mech.
   Eng., 2021; in repo as statFEM.pdf). Contribution: a Bayesian construction of the FE method that
   cleanly separates model prediction, a GP model-form discrepancy on the solution field, and sensor
   noise, giving a posterior over the true field. Limitation for us: demonstrated on static or
   near-static, known-forcing problems where the model already matches the data. This is the 5-mph
   parking-lot regime we want to leave. **Role: backbone.**

2. **StatFEM digital twin** ("Digital twinning of self-sensing structures using the statistical
   finite element method," Data-Centric Engineering, Cambridge, 2021; in repo; exact author list
   [to confirm]). Contribution: applies StatFEM to a physically monitored, self-sensing structure
   with sequential assimilation. Limitation: still relatively simple and near-static, model close to
   data. **Role: the closest published precedent to our digital twin, and the high-water mark we
   intend to pass by going dynamic and pushing to a load decision.**

3. **Joint paper** (Jalali, Haddad Khodaparast, Madinei, Friswell, "Stochastic modelling and
   updating of a joint contact interface," Mechanical Systems and Signal Processing, 2019; Swansea
   University). Role: a clean, reproducible template for stochastically modelling and Bayesian-style
   updating of a joint contact interface (preload, surface roughness, contact variability), and
   evidence that interface/joint updating itself is published, so it is not our novelty. We use it
   as a method template and a novelty boundary.

4. **Bridge paper** (Argyris, Papadimitriou, Panetsos, Tsopelas, "Bayesian Model-Updating Using
   Features of Modal Data: Application to the Metsovo Bridge," Journal of Sensor and Actuator
   Networks, 2020). Role: one of the closest published things to what we want, since it does
   Bayesian model updating using features of modal data on a real bridge (Papadimitriou's group,
   operational/ambient context). It therefore sets a novelty boundary on modal-feature updating of
   real structures and must be read carefully against our combination in the #1 scan.

5. **ABC, Approximate Bayesian Computation** (Ben Abdessalem, Dervilis, Wagg, et al., "Model
   updating and model selection for structural systems via Approximate Bayesian Computation,"
   Mechanical Systems and Signal Processing, vol. 245, 113836, 2025/2026; Sheffield group). Role:
   the fallback when we cannot write down a defensible likelihood, for example when the comparison
   is on non-Gaussian FRF features or peaks rather than the whole response. Directly relevant to our
   whole-FRF vs feature-likelihood choice, and it covers model selection too. **Partially read.**

6. **Kiran review** (Kiran, R. P.; Das; Bansal, "A state-of-the-art review of Bayesian finite
   element model updating techniques for structural systems," 2025; in repo). Contribution: the map
   of the field (time, frequency, and modal likelihoods; global/local/un-identifiability; model-class
   selection; hierarchical Bayes; complex and incomplete modal data; TMCMC). Three facts position
   our work: it never mentions StatFEM (we bridge two literatures), it states that output-only
   updating has not been researched (our unknown-forcing friend is open space), and it shows the
   modal and interface updating we are not claiming is mature. **Queued for Andrew; agent-read in
   full.**

7. **Supporting set.** Kennedy and O'Hagan, "Bayesian calibration of computer models," J. R. Stat.
   Soc. B, 2001 (in repo; the canonical calibration-plus-discrepancy paper that the whole field,
   including StatFEM, builds on, and the source of the parameter-vs-discrepancy confounding we keep
   fighting); Brynjarsdottir and O'Hagan, 2014 (you need structure on the discrepancy or you get
   garbage parameters); Plumlee, 2017 (make the discrepancy orthogonal to the model's parameter
   sensitivity); Schneider, Papaioannou, Straub, Winter, and Muller, "Bayesian parameter updating in
   linear structural dynamics with frequency transformed data using rational surrogate models,"
   Mechanical Systems and Signal Processing 166:108407, 2022 (TU Munich; fast frequency-domain
   likelihoods via rational-function FRF surrogates, directly relevant to making a whole-FRF
   likelihood affordable, and the same Schneider line that used a space-and-frequency-correlated
   model error); Ching and Chen, 2007 (TMCMC, the sampler much of this field uses);
   Surer-Plumlee-Wild, 2024 (sequential design of expensive simulation runs to build an emulator, a
   tractability tool, not physical sensor placement); force-limited vibration (NASA-HDBK-7004 /
   Scharton, the load decision our QOI feeds); and the operational-modal and input-state lineage
   (Brincker FDD; Van Overschee and De Moor / Peeters SSI; Au's Bayesian OMA; Lourens, Maes,
   Gillijns-De Moor input-state estimation), the unknown-forcing friend. These are the targets of
   the #1 white-space scan, and several are still on the queue rather than read.

## 2.9 Patent, IP, and the three questions in detail

The split is clean: the digital twin is the vision and the value; the patent would be one narrow,
novel method inside it (error-by-part-type discrepancy) that makes the hard part work. Sensor
placement and the agentic automation are supporting, not the core claim. The quick prior-art read
was papers only, so it is not a cleared freedom-to-operate search.

1. **Ownership under Purdue's student-IP rules.** I am obtaining a written determination from
   Sponsored Programs and will follow it. My working intent is to keep the patent-critical work
   self-funded and off lab resources, which under typical student-IP rules supports student
   ownership, but I will not treat that as settled until it is in writing. I will also read the
   invention-disclosure procedure so we both know the process.

2. **Advise vs co-invent.** My preferred arrangement is that you advise on the digital-twin science
   and the experiment, which is real value to me, while not contributing the specific inventive
   concept (error-by-part-type), so I can retain title. If you would prefer to co-invent, that makes
   the invention Purdue-owned; I am open to that, but I want it decided up front and transparently
   rather than discovered later. Inventorship is a legal determination based on who contributed to
   the claims, so we will keep a contemporaneous record of contributions. I am not offering legal
   advice; counsel and Sponsored Programs govern the final answer.

3. **Self-funding the patent-critical work.** Yes. I want the conception, the method development, the
   compute, and the McCallie test on my own equipment and funds, to keep a clean ownership story.
   Lab and sponsored resources are welcome on the broader digital-twin and automation work that is
   not the core claim.

## 2.10 Risks and what would make this the wrong question

- **Identifiability and confounding** are the central scientific risk: a flexible error term can
  hide the physics. Mitigations are informative priors, reporting all posteriors, the structured
  error term, and modular/cut updating if needed. If the error-by-part-type structure does not
  improve held-out coverage, the method does not work, and we report that.
- **Compute** can blow up with more parameters, GP coefficients, and finer FEM. Mitigations are
  reduced-order modal models, adaptive grids, and staged runs.
- **The framing could be wrong** if, in the regime aerospace cares about, model-form error so
  dominates that no amount of honest calibration narrows the load enough to change a design decision,
  or if a fair bake-off shows classical updating does the job at lower cost. Either outcome is worth
  knowing early, which is why the bake-off and the held-out trust gate come first.
- **Freedom-to-operate is not cleared.** The novelty claims are hypotheses until the #1 literature
  scan and a real patent-database search are done.

## 2.11 Next steps and sequence

1. Get the IP-ownership determination from Sponsored Programs and read the disclosure procedure.
2. Document conception of the error-by-part-type method now, with a date.
3. Run the #1 white-space literature scan (operational modal / input-state / force-ID and complex
   joint impedance in CMS/FBS), then a real patent-database search or attorney clearance.
4. Run the framework bake-off (classical modal Bayesian updating vs StatFEM on the same case).
5. Build the subscale experiment that shows the method works where the standard approach fails, the
   science and the non-obviousness evidence at once.
6. Pick a conference or journal target so the work has a deadline and a deliverable.
