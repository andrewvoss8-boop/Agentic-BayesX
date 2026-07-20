# Applicability review - three new papers for ShockSat

Status: YELLOW review packet. The review and prompts are complete, but every proposed application is an exploration. No ShockSat metric has improved until a runner produces held-out scores and checker output.

Plain-English statistical terms used below:
- `statFEM` = statistical finite element method, a way to combine a finite element model, measurement noise, and model-form error in one probabilistic model.
- `Bayesian filtering` = sequential updating: predict the next state from the model, then update that prediction when a new measurement arrives.
- `Gaussian process` or `GP` = a probability model over functions; here it describes smooth-in-time or smooth-in-space uncertainty such as forcing, model misspecification, or latent force.
- `BNN` = Bayesian neural network, a neural network whose weights are uncertain, so the output is a distribution rather than only a point prediction.
- `held-out score` = the test data were not used for fitting; the model predicts them, then we score calibration and sharpness.

## Current ShockSat context used for the review

The live ShockSat thread is no longer "single weak Test07 impact tap only." The best current data are the clean modal-hammer multi-reference tests: Test01 (+X at node 990), Test02 (+Z at 990), Test04 (+XY at 990), and Test06 (+Z at node 900). The current near-term decision quantity is held-out-sensor response PSD, a smooth upper envelope, GRMS, and energy-weighted exceedance against FEM+6 dB.

Important inherited caveat: multi-reference drive data helps the drive side, but prior Card G found that held-out per-channel amplitude is limited by the held-out sensor's own mode-shape participation. Any new method must prove value on held-out sensors or held-out references, not just fit observed channels.

## A. Lu et al. 2026 - multi-level digital twin for wing deformation/stress

### What the paper contributes

This paper is a hierarchical digital-twin architecture for fast deformation and local stress prediction. It is not a Bayesian/statFEM contribution. It decomposes a wing into:
- a global simplified beam/reduced model built from physically consistent homogenization;
- representative-volume or component-level models;
- data-driven local submodels based on POD, where POD means proper orthogonal decomposition, a basis-compression method that represents many high-dimensional stress/displacement fields using a small set of modes;
- integration through FMU/FMI interfaces, where an FMU is a functional mock-up unit and FMI is the standard interface for composing simulation components.

The paper reports a composite wing case study with near-real-time speed, up to about 10 Hz, while keeping regions of interest close to the high-fidelity finite element stress fields. Its own limitations matter for us: accuracy depends on the homogenized lower-order model, complex mechanisms can break the approximation, and real-time performance was limited by data synchronization. The paper says future work should add sensor-assisted calibration and improved hierarchical optimization.

### Applicability to BayesX/ShockSat

Applicability: MODERATE-LOW, but worth a bounded runner.

Why it fits:
- The project vision wants practitioner-usable tools, not only expensive posterior machinery. A fast hierarchical ROM that outputs response/stress envelopes is compatible with the "loads engineer can run it Monday" goal.
- ShockSat already has a high-order FEM and reduced modal machinery. A multi-level architecture could expose fast QOIs: response PSD envelope, modal stress proxy, interface/load proxy, or local component response.
- It could help turn the current ShockSat PSD-envelope work into a deployable twin architecture.

Why it does not directly solve the current problem:
- The paper is not a Bayesian updating method and does not solve model-form discrepancy.
- It is mainly deformation/stress under prescribed loads, while the current ShockSat evidence is modal-hammer FRFs.
- ShockSat has no measured local stress fields in the current dataset, so stress validation would be FEM-vs-FEM or proxy-based unless we define a response QOI.

Runner decision: prompt created as a lower-priority architecture pilot. It should be stopped if it becomes a cosmetic rewrite of existing ROM code without a speed/accuracy/held-out-QOI benefit.

Prompt: `runner_prompts/03_multilevel_rom_submodel_shocksat_runner_prompt.md`.

## B. Kavrakov et al. 2026 - sequential statFEM for solid dynamics

### What the paper contributes

This is the most directly relevant paper. It extends statFEM to transient elastodynamics with a Bayesian filtering formulation. The state of the finite element problem is advanced through a stochastic explicit Newmark-type scheme. At each time step, the prior state distribution is predicted forward and then conditioned on observations. Material properties, forcing, and model misspecification are represented as spatio-temporal Gaussian random fields, with spatial correlation specified through stochastic partial differential equation formulations. The paper estimates model-misspecification hyperparameters by maximizing marginal likelihood, also called empirical Bayes when hyperparameters are optimized rather than fully sampled.

The examples are synthetic: a one-dimensional axially loaded bar and a two-dimensional anti-plane plate with a hole. The paper shows that jointly updating state and material field improves displacement reconstruction relative to treating all error implicitly as forcing. Its caveat is important: the first-order perturbation approximation is generally valid for small variances; larger uncertainty may need more advanced approximations such as polynomial chaos. The paper also demonstrates displacement observations, not ShockSat accelerance FRFs directly.

### Applicability to BayesX/ShockSat

Applicability: HIGH.

Why it fits:
- This is a true dynamic statFEM extension, exactly aligned with the project vision of taking statFEM from benign static demonstrations into real structural dynamics.
- It naturally fits raw ShockSat time histories, especially clean modal-hammer ringdowns where force and acceleration are measured in engineering units.
- It gives us a principled way to separate state uncertainty, material/stiffness uncertainty, forcing uncertainty, and model misspecification in a time-domain pipeline.
- It addresses an existing BayesX gap: the current L5 pipeline is modal/frequency-domain and mostly calibrates stiffness from modal frequencies; this paper suggests a sequential response-domain alternative.

Main risks:
- Direct full-FE filtering is too large. A ShockSat runner should start in the existing reduced modal/74-DOF space or a small substructure.
- The paper's examples are synthetic and lower-dimensional; real ShockSat sensor sparsity, acceleration observations, impact forcing, windowing, and mode-shape errors are harder.
- Hyperparameter optimization by marginal likelihood is not a full Bayesian posterior over hyperparameters. The runner must label empirical Bayes honestly unless it wraps hyperparameters in NUTS/HMC.

Runner decision: prompt created as the highest-priority exploration.

Prompt: `runner_prompts/01_sequential_statfem_shocksat_runner_prompt.md`.

## C. Kashyap and Nayek - latent-force plus BNN probabilistic digital twin

### What the paper contributes

This paper treats model-form error as an additive latent force in a nominal linear structural dynamics model. In the diagnosis phase, a Gaussian Process Latent Force Model (GPLFM) estimates states and model-form-error forces from sensor measurements. In the mapping phase, a Bayesian neural network learns a probabilistic state-to-error map. In the prognosis phase, the learned map is not inserted directly into the governing equations. Instead, it generates pseudo-measurements of model-form error, and those pseudo-measurements are assimilated by a Kalman filter. This is meant to avoid unstable trajectories that can happen when a learned nonlinear correction is directly integrated.

The examples include single-degree and multi-degree systems, Bouc-Wen hysteresis, and the Silverbox experimental benchmark. The paper reports good state prediction with uncertainty, but its limitations are central: extrapolation outside the training state range degrades performance; GP hyperparameters are optimized in batch mode, so the current implementation is primarily offline; sparse sensors can make latent-force localization difficult; cost grows with system size and needs reduced-order formulations for large systems.

### Applicability to BayesX/ShockSat

Applicability: MODERATE-HIGH.

Why it fits:
- ShockSat and MPL repeatedly hit model-form error, damping/joint uncertainty, and "linear FEM plus real nonlinear-ish structure" behavior. Treating the residual as a latent force is a plausible way to diagnose what the linear ROM misses.
- The method is naturally time-domain and can use measured force and acceleration from modal-hammer tests.
- It directly connects to the project vision's unknown/uncertain forcing theme, although the paper's examples generally use known inputs during diagnosis/prognosis.
- The pseudo-measurement trick is useful: it may give a stable way to propagate learned residual dynamics without turning a BNN into an unconstrained simulator.

Main risks:
- The method may explain residuals at observed sensors without improving held-out sensors, the same trap as prior ShockSat amplitude work.
- A static state-to-MFE map may not capture history-dependent friction or hysteresis; the paper itself notes this limitation.
- Sparse ShockSat sensors relative to full FEM DOFs make latent-force localization underdetermined unless the runner uses a low-dimensional modal/group latent-force basis and a sparsity/identifiability gate.
- It is offline and moderate-scale; do not call it a real-time twin on ShockSat without runtime evidence.

Runner decision: prompt created as a second-priority exploration, focused on a reduced modal latent-force residual diagnostic and held-out PSD/FRF scoring.

Prompt: `runner_prompts/02_latent_force_bnn_shocksat_runner_prompt.md`.

## Ranking and recommendation

1. Run the sequential statFEM prompt first if the goal is methodological continuity with BayesX/statFEM.
2. Run the latent-force/BNN prompt first if the goal is to attack model-form error and damping/nonlinear residuals in the clean modal-hammer time histories.
3. Run the multi-level ROM prompt only if the goal is deployability and fast QOI architecture, not a new inference method.

Do not merge these into one large runner. They test different hypotheses:
- sequential statFEM asks whether time-domain filtering improves held-out response predictions;
- latent-force/BNN asks whether a learned residual force generalizes across references or excitation levels;
- multi-level ROM asks whether a hierarchical fast surrogate can preserve QOI accuracy and speed.

## Result status

- GREEN: the three papers were reviewed from local PDFs; all three have applicability verdicts; all moderately applicable papers have runner prompts.
- YELLOW: every proposed application remains untested on ShockSat, and two papers are mostly synthetic/offline or architecture-only. The prompts are usable only with their caveats and future checker output.
- RED: none.

Overall: YELLOW.
