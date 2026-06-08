# Literature review — Kalman filtering × StatFEM (for the dynamic aerospace digital-twin goals)

*Compiled 2026-06-08 for Agentic BayesX. Audience: beginner–intermediate in ML/stats, advanced in
structural dynamics. Ties to `notes/project_vision.md` (dynamic StatFEM + unknown stochastic forcing +
load QOI + real-time twin/health monitoring).*

## Honesty / verification legend (READ FIRST)
Bibliographic metadata (authors, year, venue, DOI) below were **machine-verified against the Crossref API**
on 2026-06-08 — they are not hand-typed from memory. BUT content summaries differ in trust:
- **[W] = full PDF in workspace, read substantially** — content claims are reliable.
- **[X] = metadata Crossref-verified, full text NOT read here** — the *citation* is solid, but the content
  description is from title/venue + established domain knowledge and **must be confirmed on a full read**
  before being cited in a paper/disclosure. Do not treat [X] content claims as quotations.

No DOIs, page numbers, or findings were invented. Where I am unsure of a paper's internals, I say so.

---

## 0. Why this review (the goal it serves)
project_vision wants to take StatFEM "onto the track": a **dynamic**, physics-identifying,
QOI-propagating digital twin of an assembled aerospace structure, learning from **real** vibration data
under **unknown stochastic forcing**, pushed to a **force-limiting / apparent-mass load QOI**, and
eventually run **online** for flight health status. Kalman filtering (KF) shows up at three distinct
points in that pipeline, and the literature splits cleanly along them:
1. **Dynamic StatFEM = a filtering problem.** Time-dependent statFEM is solved with (extended/ensemble)
   Kalman filters — this is the literal KF×StatFEM bridge (Section B).
2. **Unknown forcing = input-state estimation**, which is a KF-based field of its own (Section C).
3. **Online health monitoring = recursive Bayesian filtering / system ID** (Section D).
Plus the discrepancy/calibration foundations (Section E) and the updating/sampler context (Section F).

---

## A. StatFEM foundations (the "what we are extending")
- **[W] Girolami, Febrianto, Yin, Cirak (2021)** — *The statistical finite element method (statFEM) for
  coherent synthesis of observation data and model predictions.* Comput. Methods Appl. Mech. Engrg.
  375:113533. DOI:10.1016/j.cma.2020.113533.
  - The core paper. Hierarchical generating model `y = P·u + d + e` (FE response `u` + model-misspecification
    GP `d` + noise `e`), each component with its own hyperparameters; Bayes applied level-by-level
    (empirical-Bayes-style). Demonstrated in the **benign static/linear** regime (no physical-parameter ID).
- **[W] Febrianto, Butler, Girolami, Cirak (2022)** — *Digital twinning of self-sensing structures using
  the statistical finite element method.* Data-Centric Engineering 3:e31. DOI:10.1017/dce.2022.28.
  - StatFEM applied to a real self-sensing bridge — the "5 mph parking-lot" demo project_vision references:
    static-ish, model already ~matches data. Our target is the dynamic/identifying regime it does not cover.

## B. THE BRIDGE — dynamic/sequential StatFEM via Kalman & particle filtering (most important section)
This is the direct answer to "KF + StatFEM": when the problem is **time-dependent**, statFEM's level-1
state inference becomes a **filtering/smoothing** recursion, and the Girolami group solves it with Kalman-
type and particle methods.
- **[X] Duffin, Cripps, Stemler, Girolami (2021)** — *Statistical finite elements for misspecified models.*
  PNAS 118 (Crossref issued 2020). DOI:10.1073/pnas.2015006118.
  - Extends statFEM to **time-dependent / dynamical** PDE models; the data-model synthesis is run as a
    **(extended) Kalman-filter** recursion over time, with the discrepancy carried in the state covariance.
    *This is the canonical "dynamic statFEM = KF" reference.* (Internals to confirm on full read.)
- **[X] Duffin, Cripps, Stemler, Girolami (2022)** — *Low-rank statistical finite elements for scalable
  model-data synthesis.* J. Comput. Phys. 463:111261. DOI:10.1016/j.jcp.2022.111261.
  - Makes the dynamic statFEM filter **scalable** via a low-rank covariance representation (the bottleneck
    is propagating a full FE-sized covariance each step) — directly relevant to our tractability concern
    (avoid re-solving/large-covariance cost every posterior step). Ensemble/low-rank KF flavor. [confirm]
- **[X] Akyildiz, Duffin, Sabanis, Girolami (2022)** — *Statistical Finite Elements via Langevin Dynamics.*
  SIAM/ASA J. Uncertainty Quantification 10(4). DOI:10.1137/21m1463094.
  - Sampling-based alternative to the Gaussian-filter approximation (Langevin MCMC for the statFEM
    posterior) — relevant when the Gaussian/EKF assumption is too crude. [confirm internals]
- **[X] Glyn-Davies, Duffin, Kazlauskaite, Girolami (2025)** — *Statistical Finite Elements via Interacting
  Particle Langevin Dynamics.* SIAM/ASA J. Uncertainty Quantification. DOI:10.1137/24m1693593.
  - Newest in the line; particle-based inference for statFEM incl. hyperparameter learning. Useful if our
    nonlinear/non-Gaussian dynamic case breaks the KF Gaussian assumption. [confirm internals]
- **Relevance:** B is the literature for our Section-3 (vision) "dynamic" axis. Take-away: a dynamic StatFEM
  twin is *naturally* a Kalman filter; the open work is (i) **identifying physical parameters** (not just
  the state), (ii) **unknown forcing** (Section C), and (iii) a **load QOI** — none demonstrated here.

## C. Unknown forcing = joint input-state estimation (KF-based) — our novelty axis + its prior art
We measure response, not the input force. The established tool is **joint input-state estimation**: an
augmented Kalman filter that infers the unknown excitation *and* the state from output-only response.
**Honest flag for IP:** this is a mature field → it is **prior art** for "unknown forcing." Our defensible
novelty is the *combination* (dynamic StatFEM discrepancy + unknown forcing + load QOI), not the bare KF.
- **[X] Gillijns & De Moor (2007)** — *Unbiased minimum-variance input and state estimation for linear
  discrete-time systems.* Automatica 43(1). DOI:10.1016/j.automatica.2006.08.002.
  - The control-theory foundation: optimal simultaneous input+state estimator. The math everyone builds on.
- **[X] Lourens, Reynders, De Roeck, Degrande, Lombaert (2012)** — *An augmented Kalman filter for force
  identification in structural dynamics.* Mech. Syst. Signal Process. 27. DOI:10.1016/j.ymssp.2011.09.025.
  - The canonical structural-dynamics augmented-KF: stack unknown forces into the state vector and let the
    KF estimate them. The reference project_vision was pointing at.
- **[X] Maes, Smyth, De Roeck, Lombaert (2016)** — *Joint input-state estimation in structural dynamics.*
  Mech. Syst. Signal Process. 70-71. DOI:10.1016/j.ymssp.2015.07.025.
- **[X] Maes, Gillijns, Lombaert (2018)** — *A smoothing algorithm for joint input-state estimation in
  structural dynamics.* Mech. Syst. Signal Process. 98. DOI:10.1016/j.ymssp.2017.04.047.
  - Filtering vs **smoothing** (use future data too) for better input/state estimates offline.
- **[X] Maes, Lourens, Van Nimmen, Reynders, De Roeck, Lombaert (2015)** — *Design of sensor networks for
  instantaneous inversion of modally reduced order models in structural dynamics.* Mech. Syst. Signal
  Process. 52-53. DOI:10.1016/j.ymssp.2014.07.018.
  - **Observability of input-state estimation** + sensor placement — important: you cannot recover input &
    state from arbitrary sensors. Connects to vision §5.3 QOI-targeted sensor placement.
- **[X] Naets, Cuadrado, Desmet (2015)** — *Stable force identification in structural dynamics using Kalman
  filtering and dummy-measurements.* Mech. Syst. Signal Process. 50-51. DOI:10.1016/j.ymssp.2014.05.042.
  - Fixes the numerical instability/drift of augmented-KF force ID — practical for real deployment.
- **[X] Naets, Pastorino, Cuadrado, Desmet (2013)** — *Online state and input force estimation for
  multibody models employing extended Kalman filtering.* Multibody Syst. Dyn. 32. DOI:10.1007/s11044-013-9381-8.
  - Online EKF joint state+input — the "real-time" flavor for the health-monitoring use case.

## D. KF for Bayesian system identification / SHM (the online health-status piece)
- **[X] Huang & Yuen (2023)** — *System Identification Using Kalman Filter and Extended Kalman Filter*, ch.
  in *Bayesian Real-Time System Identification* (Springer). DOI:10.1007/978-981-99-0593-5_2.
  - Textbook treatment tying KF/EKF to Bayesian real-time system ID (Yuen's line). Good orientation; pair
    with Yuen's 2010 book *Bayesian Methods for Structural Dynamics and Civil Engineering* (verify ed./DOI).
- **[X] Capellari, Azam, Mariani (2015)** — *Towards real-time health monitoring of structural systems via
  recursive Bayesian filtering.* Int. J. Sustainable Materials and Structural Systems.
  DOI:10.1504/ijsmss.2015.078355.
  - Recursive Bayesian (KF-family) state/parameter estimation for **online SHM** — the damage-detection
    framing (review's L1–L3) via filter innovations.

## E. Calibration / discrepancy foundations (the identifiability lever)
- **[W] Kennedy & O'Hagan (2001)** — *Bayesian Calibration of Computer Models.* J. R. Stat. Soc. B 63(3):
  425-464. DOI:10.1111/1467-9868.00294. (Workspace file misnamed "2002".) The original physics+discrepancy
  confounding problem.
- **[W] Plumlee (2017)** — *Bayesian Calibration of Inexact Computer Models.* J. Am. Stat. Assoc. 112(519):
  1274-1285. DOI:10.1080/01621459.2016.1211016. Orthogonality-to-parameter-gradient (our core method's
  basis); assumes a **known controlled input** (we don't have that → the gap).
- **[W] Sürer, Plumlee, Wild (2024)** — *Sequential Bayesian experimental design for calibration of
  expensive simulation models.* (Technometrics; verify vol/DOI.) Designs which **simulation runs** to make
  (emulator/tractability), distinct from physical sensor placement.

## F. Updating / sampler context (the established Bayesian-FE-updating world)
- **[W] Kiran, Das, Bansal (2025)** — *A state-of-the-art review of Bayesian finite element model updating
  techniques for structural systems.* Probabilistic Engineering Mechanics 80:103761.
  DOI:10.1016/j.probengmech.2025.103761. Note: the review **never mentions StatFEM** (separate literature)
  and lists "output-only time-history BU not researched" as a gap — both points support our positioning.
- **[W] Ching & Chen (2007)** — *Transitional Markov Chain Monte Carlo Method for Bayesian Model Updating,
  Model Class Selection, and Model Averaging.* J. Eng. Mech. 133(7):816. DOI:10.1061/(asce)0733-9399(2007)133:7(816).
- **[W] Schneider, Papaioannou, Straub, Winter, Müller (2022)** — *Bayesian parameter updating in linear
  structural dynamics with frequency transformed data using rational surrogate models.* Mech. Syst. Signal
  Process. 166:108407. DOI:10.1016/j.ymssp.2021.108407. (Multiplicative model error correlated in space &
  frequency + rational surrogate + adaptive BUS-SuS.)

---

## Synthesis for our goals
1. **A dynamic StatFEM twin is, by construction, a Kalman filter** (Section B). So "KF vs StatFEM" is a
   false choice — KF is *how dynamic statFEM is computed*. The offline batch NUTS work (our project) and the
   online KF view are two faces of the same model: NUTS for careful full-posterior calibration of physics +
   discrepancy hyperparameters; KF for the online state/forcing recursion once those are fixed.
2. **Proposed architecture (consistent with the literature):** OFFLINE — NUTS/StatFEM on ground-test/real
   data to learn physical params, discrepancy structure, and variances (with uncertainty). ONLINE —
   augmented/joint input-state KF (Section C) reusing those params as the model and the learned variances
   as Q/R (or carrying discrepancy as an explicit bias state), assimilating flight response under unknown
   forcing for load-QOI tracking + innovation-based health status (Section D).
3. **Identifiability caveats carry over.** Sections C–D do not dissolve the physics-vs-discrepancy
   confounding (Section E); a naive KF can bury model-form error in Q/R (the σ_e-inflation trap). Want an
   adaptive KF or an explicit discrepancy state; and input-state estimation has its own **observability**
   conditions (Maes 2015) → sensor placement matters.
4. **IP honesty:** the offline→online and input-state pieces are **established prior art**. Defensible
   novelty (per vision §5.0) is the *combination* in the dynamic-aerospace, unknown-forcing, load-QOI
   setting with the orthogonal `F(k)` discrepancy — NOT KF or input-state estimation themselves.

## Gaps / open questions (what the literature does NOT yet do for us)
- StatFEM that **identifies physical parameters** (not just reconstructs the state) in the **dynamic** regime.
- StatFEM under **unknown stochastic forcing** (statFEM papers assume known forcing/BCs; input-state papers
  don't carry a model-form discrepancy) — the two literatures have **not been merged**. This is the gap.
- Propagation to an **aerospace force-limiting / apparent-mass load QOI** — absent from all of the above.
- **Nonlinear/non-Gaussian** dynamic statFEM at scale on real assembled-interface hardware (rattlebasket
  joints) — particle/interacting-Langevin variants (Section B) are the candidate tools; untested for us.

## Reading priority (suggested)
1. **Duffin et al. 2020 (PNAS)** — the dynamic-statFEM = KF foundation. [download/read full]
2. **Duffin et al. 2022 (JCP, low-rank)** — scalability/tractability for the dynamic filter. [download/read]
3. **Lourens et al. 2012** + **Maes et al. 2016** — the augmented/joint input-state KF for unknown forcing.
4. **Maes et al. 2015** — observability + sensor placement for input-state (ties to our OSP/QOI work).
5. **Glyn-Davies et al. 2025** / **Akyildiz et al. 2022** — if/when the Gaussian-KF assumption breaks.

## TODO to harden this (could not be done here)
- Full-text read of all **[X]** entries to replace title/venue-level content with verified summaries.
- Confirm Sürer–Plumlee–Wild vol/DOI and the Yuen (2010) book edition/DOI.
- A real patent/FTO search (NOT done; Crossref is literature only) before any novelty/IP claim.
