# Quantity contracts — FIM identifiability analysis

A "quantity contract" pins exactly what each named number means before it is plotted, fit, or
checked, so two nearby conventions don't get silently swapped.

## 1. Modal frequency f_i  (the primary observable feature)
- **Definition:** i-th fixed-base undamped natural frequency, f_i = sqrt(λ_i)/(2π), λ_i = ω_i² the
  i-th eigenvalue of K(θ)φ = λ M φ on the free DOFs.
- **Units:** Hz. **Coordinate/BC:** strut feet fixed (grounded); tray free above. **Excitation:** none (eigenproblem).
- **Limiting behaviour:** stiffer θ ⇒ higher f (monotone). No rigid-body modes (fixed base) ⇒ f_1 > 0 (≈85 Hz nominal).
- **Reference:** reproduces the Opus JAX build modes [84.8, 85.3, 181.3, 291.1, 371.3, 394.8, 541.9, 569.6] Hz to <0.001 Hz.

## 2. Frequency sensitivity  dF[i,g] = ∂f_i/∂θ_g
- **Definition (exact):** ∂λ_i/∂θ_g = φ_iᵀ K_g φ_i with φ mass-normalized (φ_iᵀ M φ_i = 1), where
  K_g = ∂K/∂θ_g is the (constant) group-g stiffness block; ∂f_i = ∂λ_i /(4π√λ_i).
- **Units:** Hz per unit relative change of θ_g (since θ nominal = 1, "per unit" = "per 100% change").
- **Expected:** `joint_lateral` column ≈ 0 (moment-free joints carry no lateral load); `strut_EI` near 0
  for low suspension modes, large only for the 542/570 Hz strut-bending tray-flex modes.

## 3. Mode-shape component / residue (sensor-design observables)
- **1-sensor drive-point residue** r_i = φ_i(s)² at sensor DOF s (mass-normalized) — the modal peak
  height in a drive-point auto-spectrum FRF (response/force, same DOF). Feature used = log r_i. Units: log(–).
- **2-sensor transmissibility ratio** T_i = φ_i(s₂)/φ_i(s₁) near resonance i — the input cancels, so it is
  a pure mode-shape ratio. Units: dimensionless. **Resonance behaviour:** at f_i the ratio → the mode-shape ratio.

## 4. FIM  (Fisher Information Matrix)
- **Definition:** FIM = Jᵀ Σ⁻¹ J (parameters × parameters), J the feature Jacobian, Σ the diagonal
  feature-noise covariance. **Units:** 1/(relative-θ)². **Interpretation:** inverse of the best-case
  (Cramér–Rao) parameter covariance the test can achieve. Eigenvalues = information along eigen-combinations
  of θ; large = stiff (well-constrained), small = sloppy.

## 5. Load QOI — payload acceleration transmissibility peak
- **Numerator:** tray-corner vertical (z) acceleration. **Denominator:** unit uniform vertical base
  acceleration input. **Quantity:** T(ω) = |Σ_i φ_i(out)·Γ_i /(ω_i²−ω²+2iζω_iω)|·ω², Γ_i = φ_iᵀ M r_z the
  modal participation to a rigid vertical base motion r_z; QOI = max_ω T(ω) over a scan near the modes.
- **Units:** dimensionless (output accel / input accel). **BC/excitation:** fixed-base, uniform base-z drive.
- **Damping:** modal ζ = 0.02 (assumed). **Limiting/resonance:** peaks at the lowest suspension resonance;
  → finite Q≈1/(2ζ) amplification at resonance; → input-following (T→1) well below the first mode.
- **Role:** a *prediction* target distinct from the calibration features; we ask whether the test can
  constrain the θ's the QOI depends on (∂QOI/∂θ projected onto identifiable vs sloppy subspaces).
- **Nominal value:** 24.83 (this FEM, ζ=0.02). This is a directional design quantity, not a validated load.
