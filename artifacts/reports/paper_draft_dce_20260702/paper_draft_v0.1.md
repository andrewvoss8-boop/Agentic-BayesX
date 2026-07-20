# Coverage-first validation of Bayesian finite-element model updating on a real aerospace structure: what held-out data supports — and what it falsifies

**Draft v0.1 — 2026-07-02 — for internal review (Andrew Voss). Target venue: *Data-Centric Engineering* (Cambridge) or similar.**
Authors: Andrew Voss¹, [advisor(s) TBD]. ¹[affiliation].
*AI-assistance disclosure: analyses were executed by an LLM agent workflow under human direction with immutable, pre-registered checkers; all numbers trace to archived, replayable artifacts (see Data & Code Availability).*

---

## Abstract

Bayesian finite-element (FE) model updating is typically demonstrated on simulated or geometrically simple structures, scored in-sample, and reported when it succeeds. We report a systematic, pre-registered validation campaign on a real, professionally correlated aerospace structure — a ~406k-DOF NASA satellite mock-up FEM with a multi-reference modal test campaign — organized around a simple data-centric rule: **a 95% predictive band must cover held-out data (coverage gate), must widen when known information is removed (an overconfidence audit), and only then may sharpness decide** between candidate formulations. Under this rule we obtain one positive and four cautionary results. (1) A statFEM-style, frequency-correlated, quantity-of-interest(QOI)-aware output discrepancy delivers net interface-force bands 1.5–2.5× the width of the industry FEM+6dB envelope while covering five held-out drive points; the FEM+6dB incumbent itself *under-covers* (0.71–0.87). (2) A frequency-only posterior without discrepancy — the sharpest and superficially best-calibrated formulation — is exposed as structurally overconfident by the widening audit (widen ratio exactly 1.00) and disqualified. (3) An analytic test-design curve computed at the posterior MAP promised a 5.4×→3.5× band reduction from a proposed 12-sensor test; a full synthetic rehearsal carrying the θ-posterior falsified the promise (no reduction), because parameter uncertainty rotates near-degenerate eigenvectors. (4) An agentic model-form search (151 candidates, screened through full eigensolves) produced a candidate that decisively won Occam-penalized Bayesian model-class evidence — including with mode-shape information in the likelihood (posterior model probability 0.72, prior-robust) — and then failed to improve held-out prediction at all: **evidence is not held-out validation under model-form error.** (5) Inferring the mode-shape field itself (a Beck-style, mode-matching-free formulation) is the only lever that improved held-out per-point amplitude (CRPS-skill −0.78→−0.34), yet its confident corrected shapes under-cover the derived net-force band precisely where no data can validate them. We argue that coverage-first selection with an explicit overconfidence audit is a practical, transferable discipline for digital-twin validation, and that the negative results — usually unpublished — carry most of the engineering information.

**Keywords:** Bayesian model updating; statFEM; digital twin; model-form error; validation; modal analysis; marginal likelihood; agentic workflows.

---

## 1. Introduction

The Bayesian FE model-updating literature contains many demonstrations that a posterior over stiffness (or mass, or damping) parameters can be sampled and that predictions "improve." Three habits limit the transfer of these demonstrations to engineering practice. First, most are executed on simulated data or on laboratory structures far simpler than flight hardware, where the model family contains something close to the truth. Second, scoring is frequently in-sample: the same frequencies, mode shapes, or FRFs used for calibration are used to declare success. Third, negative results — formulations that diverge, calibrations that add no predictive skill, model-selection criteria that mislead — are rarely reported, although they dominate what a practitioner encounters.

This paper takes the opposite approach. We fix a real structure with real test data and an inherited, professionally correlated FEM; we pre-register questions, candidate formulations, scoring resolutions, and acceptance thresholds *before* running the science (with SHA-locked automated checkers that cannot be edited during a trial); and we score every claim against **held-out data**: held-out sensors, held-out drive points, and a deliberate "leave-modes-out" audit that removes known information and demands the predictive band respond. Falsification of a pre-registered claim is treated as a reportable finding of equal standing with a win.

The engineering question is the one an integrator actually asks: *what interface load will a payload mounted on this structure see, with what uncertainty?* — not *can the twin reproduce every accelerometer FRF?* The distinction matters because our per-point results say the second goal is unreachable for this structure with this data (Section 5), while the first is deliverable with honest, validated bands.

Contributions:

1. **A coverage-first selection rule with an overconfidence audit** (Section 4.3): coverage of held-out data is a hard gate; a band must *widen* when measured modes are hidden (widen ratio > 1); only then does sharpness select. The audit catches a failure mode — structural overconfidence — that ordinary coverage checks miss.
2. **A validated delivery** on the real structure (Section 5.1): a statFEM-style frequency-correlated, QOI-aware output discrepancy [Girolami et al.; Schneider et al.] wins across N=18 configurations and 6 further arms; its shear bands cover five held-out drive points. The industry FEM+6dB envelope under-covers the same data.
3. **A falsified test design** (Section 5.2): a rehearsal methodology that carries the full posterior through a proposed instrumentation campaign, which overturned an analytically promised 35% band reduction and identified the mechanism (posterior rotation of near-degenerate eigenvectors) and a corrected test scope.
4. **Evidence ≠ held-out validation** (Section 5.3): a large agentic model-form search whose decisive evidence winner (including shape information; log-Bayes-factor +54) adds zero held-out skill — a concrete, replayable demonstration that marginal-likelihood model selection must be gated by held-out prediction under model-form error.
5. **A characterization of the shape wall** (Sections 3, 5.3): parameter updating, remeshing, richer parameterizations, and MAC-penalized likelihoods all fail to move per-point amplitude skill; the only formulation that moves it (inferring the shape field) is exactly the one whose confidence must be quarantined from QOIs that data cannot validate.

## 2. Structure, data, and inherited model

**Structure and FEM.** ShockSat is a NASA satellite mock-up: a two-tier box structure with a top tray/plate on struts, welded steel lower box, bolted interfaces, and an antenna dish. The inherited FEM (~67,700 nodes, ~406k DOF; shells + CBUSH joint elements) was professionally correlated to a modal survey before we received it: global matched MAC 0.63 across 26 well-paired modes, fundamental (54.2 Hz) MAC 0.97 with +0.75% frequency error. Nine parameter groups scale stiffness blocks (bottom box, welds, top box, brackets, cross-beam, plates, joints, contact); updating operates on a mass-normalized reduced basis (74–80 modes).

**Data.** (i) A 33-mode multi-reference EMA survey (76 instrumented nodes × up to 3 axes) provides measured frequencies and mode shapes — the calibration observable. (ii) Five impact-hammer drive configurations (+X, +Z at two locations, +XY, +Y; hit-averaged H1 FRFs with coherence, 45–260 Hz, ~110 channels each) are **never used for calibration**; they provide the held-out answer keys. No flight/build variability data exist; that axis is documented as absent rather than modeled.

**The wall (prior result, motivates the QOI choice).** Per-channel FRF-amplitude prediction is bounded by shape fidelity: blind log|H| correlation ~0.27, held-out-sensor cross-validated ~0.44, measured-shape *oracle* ~0.70 — and θ-updating, ~50 remesh/model-form edits (plateau ~0.38), and richer parameterizations do not close it. Accordingly the delivered QOI is the **net-CG interface force on the top tray** (NASA-HDBK-7004C apparent-mass convention): in-plane shear X/Y (driven by measured global modes, 114–197 Hz) and out-of-plane normal Z (driven by *unmeasured* drumhead plate modes, 234–258 Hz) — reported separately because their trust differs fundamentally (shape-trust 94–96% vs 45%).

## 3. Methods

### 3.1 Forward model and likelihoods

Reduced stiffness K(θ) = A_fix + Σ_p θ_p A_p (mass = I), θ_p log-normal, log θ ~ N(0, 0.25²). Three shape-use levels share the same matched-mode observations (one-to-one Hungarian assignment of FEM modes to survey modes on the measured DOFs, MAC ≥ 0.3, **frozen** through all scoring):

- **S0 (frequency only)** — eigenvalue likelihood [Kiran et al., Eq. 25]: ω̂²_r ~ N(λ_kr(θ), (σ_w2 ω̂²_r)²), σ_w2 inferred.
- **S1 (frequency + MAC)** — adds (1 − MAC_r(θ))²/σ_mac² on the survey DOFs. Near-degenerate clusters make eigenvector gradients unstable; we use a documented Tikhonov-regularized first-order shape derivative (frozen θ=1 basis; modal-gap floor δ = half the median eigenvalue gap), which preserves a genuine θ-gradient from well-separated modes while bounding the degenerate denominators.
- **S2 (Beck-style shape field)** — system mode shapes φ are free parameters (φ = φ_FEM + τ·raw, τ=0.3), pulled toward Rayleigh consistency with K(θ) and toward the measured shapes via MAC; no eigen-decomposition in the gradient.

All posteriors: NUTS (numpyro), 4 chains, float64; acceptance requires all-variable R-hat ≤ 1.05, ESS ≥ 200, divergences < 2%. Every posterior reported in this paper passed (worst R-hat 1.0011; a uniform retune policy is pre-declared for failures).

### 3.2 Output discrepancy and QOI forward

Predictive net-force spectra G_d(ω) = Σ_i g_i φ_d,i ω²/D_i(ω) (tray mass-weighted participation g_i, drive participation φ_d,i, ζ = 0.01) are wrapped in a two-part uncertainty representation: (i) per-mode tiers — measured modes tight (1% frequency, 0.35 log-amplitude), unmeasured modes wide (6%, 0.80); (ii) **statFEM F(k)**: a multiplicative log-amplitude discrepancy field, correlated over one octave in frequency, whose marginal ramps from 0.25 to 0.80 exactly where unmeasured modes dominate the response — a QOI-aware, frequency-correlated output-space discrepancy in the statFEM spirit. Independently, *learning* the output discrepancy from cross-drive residuals with NUTS gives σ_d ≈ 0.94 log-amplitude with correlation length ≈ 0.10 octave: large but nearly point-wise, so it averages out under 1-octave smoothing. This is why bands are delivered (and validated) at 1-octave resolution and per-point FRFs are not.

### 3.3 The validation harness (the transferable method)

1. **Pre-registration + locked checker.** Questions, arms, thresholds, and baseline bars are written first; an automated checker is SHA-locked before any science and never edited during the trial; outcomes are three-tier (met / documented-miss / blocking) with "pre-registered claim falsified" explicitly distinguished from "pipeline failure."
2. **Coverage hard gate.** The 95% band must cover the held-out reference (energy-weighted, 1-octave smoothed; narrow exceedances tolerated up to 0.5–1 dB). References: an epistemic truth ensemble; and — decisively — **leave-one-drive-out folds**, where the held-out drive's net force is reconstructed from *its own measured FRFs* (per-mode participation least squares — the only place any per-mode fitting is permitted, because it constructs the answer key identically for every arm).
3. **Leave-modes-out overconfidence audit.** Hide the top-K measured QOI-driving modes from the formulation *and* the truth; an honest band must widen (ratio > 1). This audit is what separates "sharp because informed" from "sharp because blind."
4. **Selection = coverage first, then sharpness**, with every "best" reported as best-of-N.
5. **Metric traps (institutional memory).** Two historically observed score-inflation mechanisms are structurally forbidden: per-mode amplitude/phase fitting inside any selection score (once produced a spurious +0.083 correlation gain), and greedy re-pairing of modes per candidate (spurious +0.010); pairing is by frozen one-to-one assignment.

## 4. Study designs

**Study 1 — formulation bake-off (N=18).** Five uncertainty representations (θ-only; per-mode tier discrepancy; feature-space; statFEM F(k); hierarchical pooling) × three QOIs, all on the same converged frequency posterior, plus the FEM+6dB incumbent. Scored by the Section 3.3 rule; shear additionally by the five leave-one-drive-out folds.

**Study 2 — pre-test rehearsal.** The Study-1 winner's normal-Z band is limited by unmeasured drumhead modes; an analytic design curve promised that 12 plate accelerometers (+Y drive) would buy the band from 5.4× to 3.5× (FEM+6dB units). Before proposing hardware, we rehearsed the *entire* campaign synthetically on the real FEM: simulate test data from an epistemic truth, run the actual inference (36 NUTS runs), deliver the actual band. Six criteria pre-registered; falsification accepted.

**Study 3 — composite bake-off (2×3 matrix + agentic search).** MODEL {M0 inherited; M1 best agent-generated remodel} × SHAPE-USE {S0, S1, S2}, F(k) always on. The M1 track: 151 model-form candidates within allowed families (joint compliance incl. new DOFs, connectivity, weld/contact, per-region stiffness, mass distribution; geometry rebuild forbidden by a prior negative result), generated from a data-driven diagnosis plus a random tranche; screened by an exact-at-nominal Rayleigh–Ritz subspace proxy; top 29 through full 399k-DOF eigensolves; top 10 through Occam-penalized model-class evidence computed on a **shape-inclusive** (frequency + MAC) observable with prior-width sweep. Pre-registered rule R4: an M1 winner is *delivered* only if it beats M0 on evidence **and** on held-out prediction.

## 5. Results

### 5.1 Study 1: the winner, the false sharpener, and the incumbent

**Winner: statFEM F(k).** Shear bands 1.51× (X) and 2.30× (Y) the FEM+6dB width with weighted coverage 0.995/0.982; normal 2.53× with 0.987 — the sharpest formulation that passes both gates. Held-out-drive validation: shear-X covered on 5/5 drives (1.00); shear-Y on 4/5, with the single gap diagnosed as a drive-specific artifact (an end-drive 73 Hz outlier), not systematic error.

**The false sharpener.** θ-only is sharper (1.07×/1.22×/1.02×) with high nominal coverage — and fails the leave-modes-out audit with widen ratio exactly 1.00: its uncertainty is invariant to information removal because it represents no amplitude/shape ignorance at all. It is disqualified *as a method*, including on the normal QOI where the audit cannot be run directly. Every discrepancy-carrying formulation widens (1.42–1.82).

**The incumbent under-covers.** FEM+6dB weighted coverage: 0.87 (shear-X), 0.71 (shear-Y), 0.74 (normal) — the default industry envelope is simultaneously arbitrary and, on this structure, not conservative enough where the data can check it.

### 5.2 Study 2: the rehearsal falsifies the design curve

Rehearsed medians: 6.17× (1 sensor), 6.20× (12 sensors), 6.20× (20 sensors) — **no band reduction**, against the promised 3.5×. The checker returned the pre-registered "claim falsified" outcome with the pipeline itself green (coverage 0.998; 35/36 NUTS runs converged). Post-hoc ablation isolates the mechanism: the analytic curve froze θ at its MAP; carrying the real ±4% θ-posterior *rotates the near-degenerate 246–258 Hz drumhead eigenvectors*, re-scattering each mode's net-Z participation (analytic floor 3.05× → 4.93× from θ alone; heavy-tailed signed mixtures → ~5.5×; even a perfect four-target test → ~5.1×). Constructively: pinning **all twelve** cluster modes recovers 2.81×, redefining the test scope (identify the whole 228–260 Hz cluster); and the as-designed test still buys a checkable quantity (target amplitude posterior sd 0.80 → 0.58). Under a 2× wider truth the pipeline degrades by widening (band ~104×, coverage 1.0) — it never lies. *Lesson: near modal degeneracy, rehearse instrumentation designs against the posterior, not a point estimate.*

### 5.3 Study 3: evidence is not held-out validation; the shape lever cuts both ways

**All six arms converged** (worst R-hat 1.0011, 0 divergences). Headline numbers (held-out):

| arm | R1 per-point CRPS-skill / σ | R2 sharpness (X/Y/Z, × FEM+6dB) | R2 covers 0.95 gate? | R3 widen>1? |
|---|---|---|---|---|
| M0S0 freq (baseline) | −0.78 / 1.08 | 1.84 / 1.98 / 2.54 | yes | yes (marginal on Z: 1.01, still covering 0.993) |
| M0S1 freq+MAC | −0.77 / 1.08 | 1.72 / 2.06 / 2.34 | yes | yes |
| M0S2 Beck field | **−0.34 / 0.89** | 1.78 / 2.25 / 1.82 | **no** (0.70/0.57/0.32) | yes |
| M1S0 remodel+freq | −0.75 / 1.10 | 1.94 / 1.66 / 2.42 | yes | yes |
| M1S1 remodel+MAC | −0.71 / 1.08 | 1.71 / 1.51 / 2.50 | yes | yes |
| M1S2 remodel+Beck | **−0.37 / 0.91** | 1.60 / 2.18 / 1.57 | **no** | yes |

**Evidence ≠ held-out.** The agentic search's evidence winner beat the inherited FEM by **+54 log-evidence units** (posterior model probability 0.72; top rank robust across prior widths 0.15–0.40) on the shape-inclusive observable — and improved *nothing* held-out. Under this much model-form error, marginal likelihood — Occam penalty and shape block notwithstanding — rewards absorbing calibration residuals into the wrong structure. The pre-registered gate correctly reported it and refused delivery. (A labeled frequency-only evidence column would have crowned the same candidate; the shape block did not re-rank, so the failure is not repaired by "more informative evidence.")

**MAC-as-constraint is null (third replication).** S1 ≈ S0 on every held-out metric.

**The shape field cuts both ways.** Beck arms halve the per-point CRPS-skill deficit (−0.78 → −0.34/−0.37) and sharpen σ (1.08 → 0.89) — the only formulation that moves the wall, consistent with an earlier three-seed result (−0.68 → −0.25). But their confident corrected shapes **under-cover** the derived net-force band (0.23–0.70 vs 0.95). An anti-circularity check matters here: on the *arm-independent* held-out-drive keys, Beck covers shear-X perfectly (1.00) — part of the shear "miss" is an artifact of a truth reference built from the FEM shapes Beck corrects. For normal-Z, however, no data key exists (the drumhead shapes are unmeasured), and Beck's confidence there is unvalidatable. *Rule extracted: use inferred-shape formulations where sensors can validate them; quarantine their confidence from QOIs the data cannot check.*

**Delivered twin.** Inherited FEM + frequency(+MAC) likelihood + statFEM F(k), for both QOIs — Study 1's delivery reaffirmed through a 6-arm gauntlet. (The nominal selection of the MAC variant over the frequency-only variant rests on a marginal audit threshold — widen 1.01 vs 1.03 while still covering 0.993 — and is flagged as such, not claimed as a MAC win.)

## 6. Discussion

**For practitioners.** (i) Coverage-first with a widening audit is cheap to implement and catches the two failure modes that matter: sharp-but-blind formulations and confident-but-unvalidatable shape corrections. (ii) Deliver at the resolution the discrepancy structure supports: here σ_d ≈ 0.9 log-amplitude but ℓ ≈ 0.1 octave means 1-octave bands are defensible while per-point FRFs are not. (iii) Marginal likelihood is a ranking heuristic, not a validation; gate it. (iv) Rehearse instrumentation investments against the posterior; MAP-frozen design curves overpromise near degeneracy. (v) Expect the incumbent (FEM+XdB) to fail its own implicit coverage claim — measuring that failure is itself a deliverable.

**Relation to statFEM and related work.** The winning formulation is an output-space, frequency-correlated multiplicative discrepancy — statFEM's central idea specialized to modal/spectral QOIs with a QOI-aware variance ramp. Companion experiments (not detailed here) show the same data resist alternatives symmetrically: with a *free* discrepancy variance on a whole-FRF observable the posterior diverges, while a bounded physics-in-prior temperature (PIFT-style) converges and covers — evidence that the regularization structure, not the Bayes/frequentist split, is what matters under severe model-form error.

**Limitations.** One structure, one lab campaign; ζ fixed at 0.01; tier σ values assumed (with sensitivity swept: the unmeasured-amplitude σ drives the normal band 2.6×→34× over 0.4→1.6); truth ensembles for the normal QOI are model-based because no >200 Hz shape data exist — precisely the gap the (rehearsal-revised) plate test would close; the agentic search covered five model-form families but not geometry rebuild (previously shown unproductive here). Build-to-build variability is absent from the data and therefore from the model.

## 7. Conclusion

On a real, correlated aerospace structure, the honest answer to "can Bayesian model updating deliver?" is: **yes, at the QOI level, with coverage-validated bands 1.5–2.5× a (non-covering) industry envelope — and no, not at the per-point level, and not via the levers the literature most often celebrates.** Evidence-based model-class selection, MAC-penalized likelihoods, agent-generated model-form candidates, and analytic test-design curves each failed a pre-registered held-out test that was designed to let them win. The methodological core — pre-registration, locked checkers, coverage-first selection, and an overconfidence audit — transfers to any digital-twin claim, and we believe the falsifications reported here are at least as useful to the field as the delivery.

## Data & Code Availability
All studies are archived as replayable workspaces (one-command replay; SHA-locked checkers; per-decision logs): net-CG method selection (checker 22 green/0/0), plate-test rehearsal (28/3/1 — the red being the pre-registered falsification tier), composite bake-off (57/6/0). [Repository/DOI to be arranged.]

## Acknowledgments
[Advisor discussions: I. Bilionis (validation-under-model-form-error framing); D. Gibert (TBD). NASA ShockSat dataset provenance TBD/permissions.]

## References (to be completed)
- Girolami, M. et al. — The statistical finite element method (statFEM).
- Schneider, F. et al. — Bayesian FRF updating with correlated discrepancy (basis for the F(k) form).
- Beck, J.L. & Katafygiotis, L.S.; Yuen, K.-V. — Bayesian modal updating without mode matching.
- Kiran, R. et al. — Bayesian FE updating, eigenvalue likelihood (Eq. 25) and evidence (Eq. 43–44).
- Allemang, R. — The Modal Assurance Criterion.
- Fox, R.L. & Kapoor, M.P. — Rates of change of eigenvalues and eigenvectors.
- NASA-HDBK-7004C — Force limited vibration testing.
- [Prior-registration/holdout-validation methodology references; PIFT reference; TBD.]

---
### Figure plan (existing artifacts; to be re-rendered for publication)
1. Structure + 9-group parameterization (fig_param_locations) + data summary.
2. The wall: measured-vs-FEM FRF grid + the 0.27/0.44/0.70 ladder.
3. Harness schematic: coverage gate + leave-modes-out audit + drive folds (redraw of fig_graphmodel).
4. Study 1: delivered bands vs FEM+6dB (fig_delivery_netcg_bands); widen-ratio table.
5. Study 1: learned vs assumed discrepancy (fig_learned_statfem).
6. Study 2: promised vs rehearsed buy-down (fig_buydown_rehearsed) + mechanism panel.
7. Study 3: matrix money figure (fig_matrix_money).
8. Study 3: evidence vs held-out (fig_evidence + R1/R2 contrast).
