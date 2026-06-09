# Prior-Art & FTO Dossier — Session 3 (Substructuring / FBS-CMS + probabilistic 7004C)

Provenance: produced by browser Claude (web search ON) from the project's Session-3 prompt, pasted back by
Andrew 2026-06-08. SCREENING PASS, NOT a clearance opinion. Saved verbatim for traceability. Synthesis +
the claim-framing correction are folded into docs/proposal/patent_ideas_ranked.md (Session-3 fold-in) and
notes/project_vision.md (Sec 5.6).

---

Term key (first use): FBS = frequency-based substructuring (predict an assembled structure's frequency
response by coupling the measured/modeled frequency response functions of its parts at their shared
interface). FRF = frequency response function (output-per-input vs frequency). CMS = component mode
synthesis (reduce each part to a small set of modes so the coupled model is tractable; Craig-Bampton is
the standard). Admittance/impedance = how much an interface moves per unit force (admittance) or how much
force per unit motion (impedance); apparent mass is the force-per-acceleration version used in 7004C.
TPA = transfer path analysis (NVH method that splits a vibration source from a receiver and estimates the
interface loads between them). Blocked force = the interface force a source would produce if its interface
were held still; an invariant source property. NVH = noise, vibration, harshness (automotive discipline).
7004C = NASA-HDBK-7004C, the force-limited vibration testing handbook.

Idea C restated: place a StatFEM-calibrated MODEL-FORM discrepancy at the substructure INTERFACE
ADMITTANCE, and carry it to a PROBABILISTIC, data-updated force-limited interface load (a "Bayesian 7004C")
under unknown operational forcing, validated on held-out data.

## Q1 — StatFEM/Bayesian model-form discrepancy AT a substructure interface (FBS/CMS)?
Found this session (all PAPERS; no patent at this exact intersection):
- Voormeeren, de Klerk & Rixen 2010, "Uncertainty quantification in experimental FBS" [PAPER]. Propagates
  subsystem-FRF uncertainty through coupling via statistical moments. MEASUREMENT/numerical-conditioning
  uncertainty, not a calibrated model-form discrepancy term.
- Trainotti, Haeussler & Rixen 2020, MSSP 144:106846 [PAPER] (covariance-based MEASUREMENT-noise
  propagation in FBS). This is the work to NOT collide with — it propagates random measurement noise; C
  claims a calibrated model-form discrepancy + a load endpoint. Different object, different purpose.
- Covariance framework for correlated FRF uncertainty in DS, ScienceDirect S0888327019307265 [PAPER] —
  again propagation of measurement/bias uncertainty, not Bayesian model-form discrepancy.
How C differs: none places a data-CALIBRATED discrepancy (a learned GP/likelihood correction on the
interface admittance) inside the coupling; they push existing measurement noise forward. C infers the
discrepancy from held-out data and treats it as the model-error object, separable from physics.
Verdict: novelty High, non-obviousness Medium-High. The interface-admittance discrepancy as a CALIBRATED
StatFEM object appears unclaimed in patents found and unpublished as a paper.

## Q2 — Probabilistic / Bayesian force-limited interface load or apparent mass (data-driven 7004C)?
Found this session (all PAPERS / NASA docs; NO patent):
- Marchand, Singhal & O'Grady 2016, "Force Limited Vibration Using the Apparent Mass Method" [PAPER].
  Deterministic full-3D elastic prediction of max in-service interface force. No posterior.
- Kolaini (JPL) 2013, "New Approaches in Force-Limited Vibration Testing" [PAPER, NTRS 20130000123] —
  impedance method, un-correlated interface responses. Deterministic.
- Semi-empirical C^2 / NASA-HDBK-7004B application notes [NASA docs, NTRS 20120014221]. Deterministic
  notch from a dynamic amplification factor.
- Bayesian force work exists but is FORCE RECONSTRUCTION / input-state estimation, NOT a force-limit:
  Sedehi/Papadimitriou/Katafygiotis sequential Bayesian input-state (output-only); Aucejo Bayesian-EM
  joint input-state; Bayesian/Tikhonov force regularization [all PAPERS]. None produces a force-LIMIT
  notch or a posterior apparent mass for a 7004C test.
How C differs: C's endpoint is the force-LIMIT / notch (a test-specification quantity), produced as a
posterior with uncertainty, not a deterministic envelope and not a reconstructed time-history.
Verdict: novelty High, non-obviousness Medium-High. A Bayesian/data-updated 7004C force limit is, in the
records found across three sessions, genuinely unoccupied.

## Q3 — Bayesian/stochastic/interval substructuring patents (the likely NVH reservoir)
Found this session:
- US8731868B2 "Transfer Path Analysis" [PATENT], assignee Siemens Industry Software (orig. LMS), ACTIVE,
  expires ~2030. Characterizes interface LOADS by fitting a PARAMETRIC model (e.g. single-DOF mount,
  point-mobility) to operational input/response data and the system FRFs. This is the closest NVH patent
  to C. BUT: deterministic point estimate, simple physical mount models, no Bayesian posterior, no
  model-form discrepancy term, no force-limit/apparent-mass endpoint, classified G01H17/00. FTO: it claims
  parametric LOAD characterization from operational data — draft C's claims to require (a) a calibrated
  model-form discrepancy at the interface admittance and (b) a probabilistic force-LIMIT output, both
  absent here, to stay clear.
  References inside it: US5360080 (engine-mount load-ratio tabulation) and JP-A-06033981 (actuator
  vibration reduction) [PATENTS, older, deterministic control] — not blocking for C.
- Bayesian NVH metamodeling (surrogate for full-vehicle NVH dispersion) [PAPER, ResearchGate 340632165] —
  design-space surrogate, not an interface model-form discrepancy.
Verdict: white space for C survives Q3, but NVH is still the highest FTO risk. US8731868B2 is active and
assignee-strong (Siemens); a professional search must claim-chart against it and its family.

## Q4 — Multi-point (e.g. 6-point) experimental FBS WITH Bayesian UQ?
Found this session (PAPERS):
- Virtual Point Transformation lineage and multi-point experimental FBS appear via VIBES.technology and
  TUM/BMW theses [PAPERS/industry]. Trainotti/Haeussler/Rixen handle multi-point FBS but with
  measurement-noise UQ, not Bayesian model-form calibration.
- Meggitt et al. 2020, covariance uncertainty in TPA (classical/blocked-force/component) [PAPER] — again
  propagation, multi-path, not Bayesian model-form discrepancy.
How C differs: a 6-point (matching your hexapod/Stewart interface) experimental FBS with a CALIBRATED
Bayesian discrepancy on the 6-DOF interface admittance, carried to a force limit, is not found.
Verdict: novelty High for the specific combination. [SPECULATIVE] the 6-point + held-out-validation +
force-limit endpoint is a strong, concrete dependent-claim cluster.

## Is C's white space real or occupied?
[OPINION] Real, with one active patent to design around. Across three sessions:
- Q1 (interface discrepancy in FBS/CMS): unoccupied in records found.
- Q2 (Bayesian 7004C force limit): unoccupied in records found.
- Q3 (substructuring patents): one active blocker-adjacent patent, US8731868B2 (Siemens/LMS TPA),
  deterministic and load-characterization-only — designed around by the discrepancy + probabilistic-limit
  features.
- Q4 (multi-point Bayesian FBS): unoccupied for the specific combination.
The "Bayesian 7004C via a calibrated interface-admittance discrepancy" framing is the cleanest claim. It
also nests with idea A/D (force-limited load QOI) — C is the substructuring-native mechanism for A/D.

## 101 anchor for C
Claim an interface-force TEST process / instrumented apparatus: a method of CONDUCTING a force-limited
vibration test in which the force limit (notch) is computed from a data-calibrated posterior over the
interface admittance, with measured interface forces and shaker notching. Tie to physical hardware
(force gauges/accelerometers at the 6-DOF interface, shaker controller) so it reads as a concrete
measurement-and-test process, not abstract math. The manufactured/operational test article + the physical
notch action are the Alice anchors.

## Claim-differentiators for C
- A CALIBRATED model-form discrepancy term on the interface admittance/impedance (learned from held-out
  data), distinct from measurement-noise propagation (Trainotti/Rixen) and from deterministic parametric
  load models (US8731868B2).
- A PROBABILISTIC force-limit / apparent-mass output (posterior notch with uncertainty) for a 7004C test,
  versus deterministic envelopes (Marchand, Kolaini, semi-empirical C^2).
- Output-only / unknown-operational-forcing operation carried to the interface LOAD, optionally at a
  6-DOF (multi-point) interface, with held-out validation as an acceptance criterion.

## What still needs a PROFESSIONAL search (C)
- Full claim-chart vs US8731868B2 and its INPADOC family (Siemens/LMS), plus US8306793 (related, cited).
- Assignee deep-dives: Siemens, AVL, Bosch, Hyundai/Kia, plus aerospace primes and defense filings, in
  G01H, G01M7/02, F16F, G06F30/15-20-23 — NVH/defense are where a probabilistic-interface-load patent
  could hide un-indexed by these keywords.
- Non-English families (DE/JP automotive, CN) not covered here.
- VIBES.technology / TUM patents specifically (virtual-point and blocked-force FBS may be patented).
