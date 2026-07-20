# Runner prompt — ShockSat time-domain latent-force damping/residual diagnostic

You are a runner agent in Agentic BayesX. This is a **focused** spin-off of the latent-force/BNN
paper review (Kashyap & Nayek), NOT the generic version in
`artifacts/reports/shocksat_new_papers_review_20260623/runner_prompts/02_latent_force_bnn_shocksat_runner_prompt.md`.
That generic prompt asks whether a latent force improves held-out PSD value in general. THIS prompt
tests one specific, physically-grounded hypothesis the review under-sold.

## The one hypothesis under test

A latent-force model-form-error (MFE) residual is, in plain terms, an extra force we add to a
nominal linear model to soak up whatever the linear physics gets wrong — most importantly
**un-modeled damping and weak nonlinearity**.

ShockSat's prior damping study (`shocksat_modelclass_L5_20260619/out/damping_inference.json`, "D22"
in `notes/memory.md`) found **0 of 9 modes gave an identified damping ratio ζ** because it worked
on a **single windowed FRF** at frequency resolution df = 1.25 Hz. The half-power bandwidth of a
light mode is Δf ≈ 2·ζ·f, which is **sub-bin** (e.g. ζ=0.35% at 138 Hz ⇒ Δf ≈ 0.97 Hz < df), so
frequency-domain damping was unresolvable. The new clean modal caches are even coarser in frequency
(df ≈ 2.03 Hz), so nothing changes in the frequency domain.

BUT damping is a **time-domain decay rate**: τ = 1/(ζ·2π·f). A clean modal-hammer **ringdown**
(~0.5 s of free vibration, coherence 0.9+ at peaks) contains many cycles of measurable decay even
when the mode is sub-bin in an FFT. A time-domain latent-force / decay estimate can therefore
resolve damping (and residual structure) that the windowed FRF could not.

**Hypothesis:** on the clean modal-hammer ringdowns (Test01/02/04/06), a time-domain latent-force
diagnostic resolves per-mode damping ζ (and/or residual MFE structure) that D22 found unidentifiable.

**Why it matters (the bridge to the live program):** the live PSD-envelope win metric
(`shocksat_psd_envelope_twin_20260623/quantity_contracts.md`, Q-D) is
`GRMS(twin 97.5% envelope) / GRMS(FEM+6 dB envelope) < 1`. Envelope GRMS is driven by modal **peak
height**, and peak height ∝ Q = 1/(2ζ). If the nominal FEM is **under-damped** (ζ too light), its
peaks — and so the FEM+6 dB envelope GRMS — are inflated/over-conservative. Replacing the FEM ζ with
a **measured ζ from the clean ringdowns** would lower the twin's peaks and its envelope GRMS, the
"less-conservative-yet-defensible" endpoint. So unlike the cross-channel-scatter QOI (where damping
is channel-common and absorbed by a global gain — see D8, so damping cannot tighten it), **damping is
a genuine lever on the ENVELOPE QOI.** State this distinction explicitly; do not import the
"damping can't help" conclusion from the scatter QOI.

## Re-ground first (read, then restate in one line)

1. `AGENTS.md` — obey every gate, especially: three-tier result standard, NUTS/HMC sampler rule,
   convergence gate, Modal/Eigenproblem Identifiability gate, quantity-contract gate, discretization
   resolution gate, plot/human-review gate, verification gate, runtime accounting gate.
2. `notes/memory.md` CURRENT STATE block (the live PSD-envelope thread + this prompt's entry).
3. `artifacts/reports/shocksat_modelclass_L5_20260619/out/damping_inference.json` and
   `code/damping_inference.py` — the D22 frequency-domain damping result you are re-testing. Reproduce
   its headline number (0/9 identified) as your integrity baseline before claiming any improvement.
4. `artifacts/reports/shocksat_psd_envelope_twin_20260623/quantity_contracts.md`,
   `decisions_log.md`, `priority_deliverables.md`, and `out/modal_cache_summary.json` (the clean modal
   set: Test01 +X@990, Test02 +Z@990, Test04 +XY@990, Test06 +Z@900; df ≈ 2.03 Hz; band 45–260 Hz;
   coherence at-peaks 0.90–0.97; samples already in g and lbf).
5. Source paper PDF:
   `references/pdfs/probabilistic digital twin for misspecified structural dynamical systems via latent force.pdf`.

Restate: goal, inherited data/QOI decision, next action, open ambiguities.

## Data

The clean modal caches in `shocksat_psd_envelope_twin_20260623` are **band-limited FRFs** (frequency
domain). This runner needs **raw time histories** (force in lbf + acceleration in g vs time) of the
ringdowns. Source the raw modal-hammer `.mat` from the root-level zips (`Test01_ModalHammer_990x.zip`,
`Test02_ModalHammer_990z.zip`, `Test04_ModalHammer_990xy.zip`, `Test06_ModalHammer_900z.zip`).

- The modal records are **pre-triggered**: the impact lands at sample ≈ 125,009 (≈ 500 ms), with a
  ~0.5 s ringdown after. Use the post-impact ringdown for decay estimation; document the exact window.
- Sampling fs ≈ 250 kSps; force = single Dytran 5850B (the force channel). Confirm per-channel
  acceleration calibration is already applied (samples in g) per the TestLog xlsx (D2 in memory).
- **Disk discipline (mandatory):** extract only the hits you need, build small time-domain caches
  (`.npz`), and delete the raw `.mat` and zips. Pin BLAS threads for dense math
  (`OMP_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1`).

## Method (three layers, run in order; stop early if a layer fails its gate)

**Layer 1 — direct time-domain damping re-test (headline, cheap, run first).**
For each clean union modal peak, estimate the decay rate from the ringdown with at least one
transparent method (band-pass + analytic-signal log-decrement, OR a modal SDOF state-space decay fit,
OR matrix-pencil/ERA on the ringdown). Report per-mode ζ with uncertainty and compare against:
(a) D22 windowed-FRF result (0/9 identified — the bar you must beat to claim anything);
(b) NASA `.ash` modal ζ (0.25–0.44%);
(c) the ζ the nominal FEM/L5 forward currently assumes.
This layer alone answers Andrew's hypothesis. If it cleanly resolves ζ where D22 could not, that is a
real GREEN methodological finding even before any envelope value claim.

**Layer 2 — latent-force diagnosis (the paper's actual contribution).**
Build a reduced modal nominal ROM (reuse `shocksat_psd_envelope_twin_20260623/code` machinery,
byte-identical, with a SHA manifest). Estimate state + a **low-dimensional latent MFE force** in
modal/group coordinates from one reference's measured force+accel ringdown, using a GP latent-force
model (GPLFM) or an equivalent Kalman smoother. Then **decompose the latent force**: how much is
explained by a pure damping correction (parsimonious) versus genuine residual nonlinear/structural
MFE? This is the diagnostic value — it separates "the FEM just has the wrong ζ" from "the FEM is
missing physics." Do NOT put an independent latent force at every DOF/sensor; use a low-dimensional
modal/group basis and report which directions are observable from the chosen sensors.

**Layer 3 — held-out envelope value (the hard bar, secondary).**
Does a measured-ζ-corrected twin (and/or a latent-force-informed twin) lower the inherited
**97.5th-percentile PSD-envelope GRMS** versus FEM+6 dB on a held-out reference/sensor, while still
enveloping the held-out measured PSD (energy-weighted exceedance per Q-E)? Reuse the inherited QOI,
smoothline algorithm, and contracts **byte-identical** so this is comparable to the live program.
Start with the same 90% validity probe before any 50→90% sweep. Honest negative is a valid result.

## Gates (in addition to all AGENTS gates)

- **Damping-resolvability gate (adapt the Modal/Eigenproblem Identifiability gate to ζ):** for each
  mode report decay time-constant τ vs ringdown length T, cycles-of-decay observed, SNR at that
  frequency, and the half-power Δf vs the FFT df = 2.03 Hz. SHOW that time-domain decay resolves ζ
  where the FFT bin cannot. Include a **finite-perturbation check**: a realistic change in ζ must
  visibly move the modal peak height / envelope QOI; if it does not, ζ is not a lever here — say so.
- **Discretization gate (this is the crux, document loudly):** the time-domain estimate deliberately
  dodges the df = 2.03 Hz frequency-bin floor. Document fs, the pre-trigger offset (≈500 ms / sample
  125,009), the ringdown window length, any band-pass, and the resulting effective ζ resolution. Do
  not silently mix a frequency-domain df with a time-domain decay claim.
- **Sampler labeling gate (NUTS/HMC rule):** the GPLFM/Kalman state estimate is an exact
  linear-Gaussian **filter** — label it as filtering, NOT NUTS, NOT a posterior over physical
  parameters. Damping ζ enters the dynamics nonlinearly; **any Bayesian posterior over ζ or over GP
  hyperparameters must use NUTS/HMC** with all-variable R-hat ≤ 1.05 (prefer ≤ 1.01), min ESS ≥ 200,
  divergence fraction < 2%, ≥ 4 chains. If you optimize hyperparameters by marginal likelihood, label
  it **empirical Bayes**, not a posterior.
- **Leakage gate:** held-out sensors/references may not enter decay fitting, latent-force estimation,
  GP/BNN training, scaler fitting, hyperparameter optimization, or display tuning.
- **History-dependence / nonlinearity gate:** if the residual depends on prior state (hysteresis), the
  paper's static state→MFE map is violated — report it; do not hide it.
- **Plot gate:** all numeric figures from saved `.py` scripts, Tufte-linted
  (`.claude/skills/tufte-data-graphics/SKILL.md` + `scripts/tufte_lint.py`) and image-QA'd;
  log-scaled frequency axes for FRF/PSD; each figure states run/dataset and any invalidity (e.g.
  non-converged ζ posterior with worst-case R-hat/ESS printed next to intervals).
- **Verification gate:** `check.py` (immutable during the run, SHA-locked) must FAIL RED if the packet
  claims damping was "resolved/identified" without the per-mode ζ posteriors and the resolvability
  table, or claims an envelope win without the held-out GRMS ratio + energy-weighted exceedance.

## Deliverables — new workspace `artifacts/reports/shocksat_latent_force_damping_YYYYMMDD/`

Files: `priority_deliverables.md`, `decisions_log.md`, `question_framing.md`, `quantity_contracts.md`
(reuse/point to the inherited PSD contracts byte-identical; add a damping/decay contract: ζ as
fraction-of-critical, units, expected resonance/decay behavior, reference), `assumptions_ledger.md`,
`REUSED_code.sha256`, `run_all.sh` (one-command replay), `check.py`, `runtime.json`
(`active_runtime_s` + `elapsed_wallclock_s`), `packet.md`, and all saved plotting scripts + figures.

## Result interpretation (three-tier; honest negative is a real outcome)

- **GREEN:** Layer 1 cleanly resolves per-mode ζ where D22 could not (posterior CI < half prior width,
  interior, with a passed resolvability table), AND/OR Layer 3 shows a held-out envelope-GRMS win with
  no energy-significant exceedance — with the checker confirming it and no leakage.
- **YELLOW:** ζ resolved on observed references but does not move the held-out envelope QOI; or the
  latent force absorbs residual but is history-dependent/empirical-Bayes-only; or the ringdown is too
  short/noisy to resolve light modes (itself a useful pre-test finding — report the resolvability
  floor). Yellow carries its caveat; it is never reported as a win.
- **RED:** data leakage, per-held-out tuning, an unstable/over-flexible latent force hidden from the
  report, mismatched units/gain, a damping "identified" claim without the posteriors/resolvability
  evidence, or any claim stronger than the held-out numbers.

## Stop conditions (stop early with a YELLOW packet)

- Raw time histories or the force channel cannot be loaded with verified units (g, lbf).
- The ringdown is too short/noisy to resolve even the heaviest expected mode (report the floor).
- ζ is resolved but a finite-perturbation check shows it does not move the envelope QOI (no lever).
- The latent force explains everything and makes ζ / model-form attribution uninterpretable.

The goal is to learn whether the clean ringdowns + a time-domain latent-force view genuinely unlock
damping/residual information that the single windowed FRF could not — and whether that information
buys a less-conservative-yet-defensible PSD envelope. A rigorous honest negative is a win.
