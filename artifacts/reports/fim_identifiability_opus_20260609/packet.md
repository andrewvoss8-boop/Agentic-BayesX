# Pre-test identifiability + experiment design on the Opus hexapod tray FEM

**One-line result:** this scrappy modal test can pin down **3 stiffness parameters**
(`strut_EA`, `tray_E`, `strut_EI`) — but only `strut_EA` from the low modes; the count
climbs **1 → 2 → 3** as the resolved band reaches 181 → 371 → 570 Hz. The **two joint
stiffnesses are unidentifiable** from modal data no matter the band or noise. The payload
transmissibility QOI happens to depend only on the identifiable parameters, so for *that*
QOI the test is fit for purpose.

> **What this is / is not.** This is a **Fisher-information (local) + profile-likelihood
> (semi-global) identifiability study** — a pre-test design calculation, **not a posterior
> sampler run**. No NUTS/HMC is run or claimed here. When a real Bayesian update is run on
> this structure, NUTS/HMC remains the default per the project sampler rule. Numbers are an
> **upper bound** on resolvability: this uses the nominal FEM with **no model discrepancy**,
> which can only *reduce* practical identifiability.

---

## Method summary (read this first)

**Goal in plain English.** Before touching hardware, answer two questions with numbers, not
hunches: (1) *how many of our candidate physical parameters can this test actually pin down,
and which are hopeless?* (2) *where should we put the accelerometer(s) and where should we tap
to learn the most?*

**Forward model.** A small vector **θ** (5 dimensionless stiffness multipliers, nominal 1.0;
see `assumptions_ledger.md`) maps through the hexapod-tray finite-element model to the things a
vibration test sees: natural frequencies f_i(θ) and mode-shape components. Because the global
stiffness is **linear** in each θ, we split it into physically-labelled blocks
**K(θ) = Σ_g θ_g K_g + K_fixed**, so the modal sensitivities are **exact** (no finite differences):

- frequency: ∂(ω_i²)/∂θ_g = φ_iᵀ K_g φ_i (mass-normalized modes), ∂f_i = ∂(ω_i²)/(4π√(ω_i²));
- mode shape: Fox–Kapoor modal derivative ∂φ_i/∂θ_g = Σ_{k≠i} [φ_kᵀ K_g φ_i /(ω_i²−ω_k²)] φ_k.

(Validated: at θ=1 the model reproduces the Opus JAX build's modes to **4e-4 Hz**, and the
analytic sensitivities match central finite differences to all digits.)

**Likelihood / information.** Stack the observable features into a Jacobian **J** = ∂(features)/∂θ
with a measurement-noise covariance **Σ** (diagonal). The **Fisher Information Matrix**
**FIM = Jᵀ Σ⁻¹ J** is the inverse of the best-case (Cramér–Rao) parameter covariance the test can
achieve. We analyze three observation designs:

| design | features used | "test rig" |
|---|---|---|
| `freq_only` | 8 modal frequencies | any modal-ID |
| `one_sensor_corner_z` | frequencies + drive-point residues φ_i(s)² | 1 accelerometer (auto-spectrum) |
| `two_sensor_transmissibility` | frequencies + mode-shape ratios φ_i(s₂)/φ_i(s₁) | 2 accelerometers (input cancels) |

**Readouts.** (a) FIM **eigen-decomposition** → stiff vs sloppy parameter *combinations*
(sloppy-models view); (b) prior-regularized **marginal posterior sd per parameter** (honest
per-parameter metric, accounts for correlations); (c) column-pivoted **QR subset selection**
(condition-number ≤ 100) → a maximally-independent observable parameter basis; (d) **profile
likelihood** as a global cross-check of the local FIM; (e) **experiment-design sweeps** over
sensor location (D-optimality = log det FIM) and tap location (modes excited).

**Data count.** No measured data is used (pre-test design). Profile likelihood uses one synthetic
noiseless dataset (structural-identifiability view) plus one noisy realization.

---

## Results

### 1. How many parameters — and which (Fig 1, Fig 3)
The FIM spectrum has **3 large eigenvalues then a ~9-order-of-magnitude cliff** to 2 essentially-zero
ones, in **all three** designs. Per-parameter marginal posterior sd (prior sd = 0.30):

| parameter | freq-only | 1-sensor | 2-sensor | verdict |
|---|---|---|---|---|
| `strut_EA` | 0.012 | 0.011 | 0.012 | learned (~25× tighter than prior) |
| `tray_E`   | 0.030 | 0.020 | 0.025 | learned (~10–15×) |
| `strut_EI` | 0.020 | 0.020 | 0.020 | learned (~15×) |
| `joint_axial`   | 0.300 | 0.300 | 0.300 | **unidentifiable** (≈ prior) |
| `joint_lateral` | 0.300 | 0.300 | 0.300 | **unidentifiable** (exactly null) |

The joints are unidentifiable for a physical reason, not a numerical one: the joints are modeled
near-rigid (1e9 N/m), so making an already-rigid joint stiffer barely moves any frequency
(`joint_axial`), and the joints are **moment-free spherical**, so lateral joint stiffness carries
**no load** at all (`joint_lateral` sensitivity is **exactly 0** — see the zero column in Fig 2).

### 2. Band dependence — the headline as a curve (Fig 4)
The count is **conditional on the resolved band**:

| highest resolved mode | identifiable params | which |
|---|---|---|
| ≤181 Hz (3 modes) | **1** | strut_EA |
| ≤371 Hz (5 modes) | **2** | + tray_E |
| ≤570 Hz (8 modes) | **3** | + strut_EI |

`strut_EI` (strut bending) is invisible to the low modes but has a **283 Hz/unit** sensitivity in
the 570 Hz tray-flex mode — so resolving the 540–570 Hz band is the price of the 3rd parameter.
The count is **robust to frequency noise** (stays 3 across ×0.5–×4): the joints are *structurally*
unidentifiable, not merely noise-limited.

### 3. 1 sensor vs 2 sensors (transmissibility)
**Same headline** (3 identifiable) for both. Adding mode-shape information (residues or
transmissibility ratios) sharpens the *amplitudes* and changes the sloppy-direction structure, but
does **not** rescue the joints — they are blind spots of *modal* data, not of a particular sensor count.

### 4. QR subset downselect
Column-pivoted QR (cond ≤ 100) selects, in order, **strut_EA → strut_EI → tray_E** as the maximally
independent observable basis and drops both joints — consistent with the eigenvalue cliff.

### 5. QOI vs data — can the test calibrate what the prediction needs? (Fig 6)
The load QOI (payload acceleration transmissibility peak, nominal **24.8**, ζ=0.02) has gradient
∂QOI/∂θ concentrated on `strut_EA`, `tray_E`, `strut_EI` and **negligible on the joints**. So the
**fraction of QOI sensitivity lying in the sloppy (unconstrainable) subspace = 0.0** — the test can
calibrate everything *this* QOI needs. Caveat: this is QOI-specific; a micro-vibration or joint-loss
QOI that depended on joint compliance would fall in the sloppy subspace and would *not* be
calibratable from these modes.

### 6. Experiment design (Fig 5)
- **Where to measure (1 accelerometer, z):** best at a near-center offset node (x≈63, y≈28 mm); the
  log-det FIM spans **20.9** between best and worst placement (~10⁹× in information volume) — placement
  matters a lot for the joint-amplitude information, though the *count* of 3 is placement-robust.
- **Where to hit:** a **corner tap** (e.g. −150, −150 mm) excites **all 8** modes >20% of their peak
  (corners avoid the node lines of the low modes); center taps miss the anti-symmetric modes.

### 7. Profile-likelihood confirmation (Fig 7)
Fixing each θ on a ±30% grid and re-optimizing the others: `strut_EA`, `tray_E`, `strut_EI` give
sharp χ² valleys with implied sd ≈ the FIM marginals (0.02–0.03); **both joints are flat**
(Δχ² < 1 across the whole range) → globally unidentifiable. The local FIM and the global profile
**agree**, so the conclusion is robust, not a linearization artifact.

---

## Limits / honesty
- **Pre-test, nominal FEM, no discrepancy.** Real model-form error only *lowers* practical
  identifiability; treat the 3 as an upper bound. The real referee is held-out coverage on hardware.
- **Stiffness-only, mass fixed.** Density/thickness parameters would add coupling; out of scope here.
- **Joint result is conditional on the near-rigid moment-free joint model.** If the real joints are
  compliant (lower k) or moment-carrying, joint identifiability would change — itself a useful thing
  to flag before the test (consider a deliberately joint-flexible build to make joints observable).
- **QOI is directional**, not a validated load (ζ assumed). It is a design quantity for the
  data-vs-prediction comparison, with a full contract in `quantity_contracts.md`.

## Reproduce
`bash run_all.sh` → `run_fim.py` (FIM + design) → `profile_likelihood.py` → `make_figures.py` →
`check.py`. Inputs are read-only (`inputs/`, SHA256 in `inputs/INPUT_SHA256.txt` and re-checked by
`check.py`). Checker gates and pass/fail in `checker_report.json`.

## Figures
1. `fig1_fim_eigenspectrum.png` — FIM spectrum, 3 stiff + cliff, all 3 designs.
2. `fig2_sensitivity_heatmap.png` — per-mode frequency sensitivity (zero joint-lateral column; strut_EI only in 542/570 Hz modes).
3. `fig3_param_identifiability.png` — prior vs posterior sd per parameter, 3 designs.
4. `fig4_band_sensitivity.png` — identifiable count and per-parameter sd vs resolved band.
5. `fig5_experiment_design.png` — where to measure (D-optimality) and where to hit (modes excited).
6. `fig6_qoi_vs_data.png` — QOI need vs data constraint per parameter.
7. `fig7_profile_likelihood.png` — profile χ² per parameter (flat joints = unidentifiable).
