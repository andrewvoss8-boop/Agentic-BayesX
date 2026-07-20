# question_framing.md — Confidently-Wrong Model-Form-Error experiment

## The exact concern under test (do not broaden)
Ilias Bilionis's load-bearing concern (Alberts & Bilionis 2023, arXiv:2301.07609; Hao & Bilionis 2024,
arXiv:2306.02150): **a converged, confident Bayesian posterior can be confidently *wrong* under genuine
model-form error, with no signal that the physics is off**, because a standard Bayesian model has no proper
mechanism to express "my physics might be wrong."
Verbatim anchor: *"Bayesian MCMC converges to the maximum likelihood estimator without detecting or accounting
for underlying model form errors … NUTs, which is not aware of the underlying model form error, still produces
confident posteriors."*
Their cure: an inverse-temperature β in the prior that quantifies model-form error and is learned.
Our analog: a learned **output-side discrepancy scale σ_d** + a **held-out trust test** (predict masked
channels we never fit; check whether the truth falls in the band).

## The engineering decision being supported
Can we trust a calibrated digital twin under model-form error — and **does our UQ warn us when we cannot?**
Concretely: given a modal-ROM FRF twin fit to 2 observed channels, can we trust its prediction of 2 held-out
(masked) channels and their peak-amplitude QOI, and does the method flag when the prediction is untrustworthy?

## Success metric / objective
- (a) held-out predictive log-amplitude coverage and held-out peak-amplitude QOI coverage vs nominal 95%;
- (b) σ_d recovery of the injected model-form-error scale δ (monotone thermometer);
- (c) convergence of every NUTS arm at every δ (the malady must be "converged-but-wrong", not "non-converged").

## What the method may choose
Parameters θ = per-mode α (4 stiffness scalings), per-mode β (4 damping scalings), input coupling γ; the
discrepancy scale σ_d; the discrepancy hyperparameters (correlation length over log-frequency for A3).

## What remains human judgment
Whether the injected error classes (smooth correlated log-field; missing-mode/hidden-DOF; coherent peak shift)
are representative of real model-form error; whether the chosen QOI (held-out peak amplitude) is the right one;
whether single-realization synthetic evidence is sufficient to act on.

## What would make this the WRONG question
If a real structure's model-form error is dominated by **coherent** effects that mimic a parameter (e.g. a
peak-frequency shift that is algebraically a stiffness scaling on a mode only the failed sensor sees). Then σ_d
cannot save the parameter — that is the **honest-limit** slide (E-LIMIT), not a pass. The defensible claim stays
predictive/QOI coverage + error detection, NOT universal parameter recovery.
