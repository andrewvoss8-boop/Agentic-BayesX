# quantity_contracts.md — StatFEM consistency toy (Experiment A)

AGENTS.md Quantity-Contract gate: every named quantity gets numerator/denominator/coordinate/excitation/BC/
units/expected limiting behaviour/reference, BEFORE plotting or checking it.

## Physical / forward quantities
- **θ (stiffness scale)** — numerator: actual axial rigidity EA; denominator: nominal EA_nom; coordinate:
  scalar (uniform along the rod); units: dimensionless; nominal θ=1, truth θ_true=1.15. Limiting behaviour:
  ω_n ∝ √θ. Reference: standard FE stiffness scaling K(θ)=θK0.
- **ω_n (natural frequency, mode n)** — fixed-free axial rod eigenfrequency; coordinate: modal index n;
  BC: u(0)=0 (fixed), EA u'(L)=0 (free); units: rad/s (nondimensional, c_nom=1 ⇒ ω in rad per unit length-
  time). Analytic no-foundation: ω_n=√θ·(2n−1)π/(2L). With foundation k_f: ω_n=√(θλ_n+k_f),
  λ_n=((2n−1)π/2L)². Limiting/anti-resonance: monotone increasing in n; mode spacing → uniform (2n−1).
  Reference: Rao, *Mechanical Vibrations*, bar/rod eigenproblem; foundation = Winkler model.
- **φ_n(x) (mode shape, mode n)** — mass-normalised displacement shape; coordinate: axial position x∈[0,L];
  units: dimensionless (∫₀ᴸ ρA φ_n² dx = 1 ⇒ φ_n=√(2/ρAL) sin((2n−1)πx/2L)); for the sensor-noise model the
  shapes are rescaled to unit max. Foundation does not change shapes (constant k_f). Reference: same.
- **k_f (Winkler foundation modulus = the model-form error ε)** — numerator: distributed support stiffness
  per unit length; coordinate: uniform; units: nondimensional (adds directly to ω² as +k_f/ρA, here ρA=1).
  ε=0 ⇒ correct model. Reference: elastic-foundation rod (Winkler).
- **D² (discrete 2nd-derivative operator)** — finite-difference Laplacian on an N_c-point grid with fixed-
  free BCs; eigenvalues d_k<0 approximate −λ analytic; coordinate: grid index; expected limiting behaviour:
  d_k → −λ_k as N_c→∞ at ≈ h² rate (h=L/N_c). Reference: standard 2nd-order FD; convergence O(h²).
- **ω0,i(h), φ0,i(h) (FE modal predictions)** — generalised eigenpairs of (K0,M) consistent-mass axial-bar
  FE with n_el elements (h=L/n_el); ω_FE,i(θ;h)=√θ·ω0,i(h); → analytic ω_i as h→0 at ≈ h² rate.

## Inference / statistics quantities
- **σ_r (residual pseudo-noise, M-lik only)** — the FICTITIOUS standard deviation of "residual ≈ 0" pseudo-
  data; units: same as the residual A_iφ_i; NO physical meaning (a numerical knob). Swept on a log grid.
- **β (inverse temperature, M-ift only)** — LEARNED precision weight on the physics term in the PRIOR;
  units: inverse residual-variance; large β ⇒ field forced onto the PDE solution. Inferred, not fixed.
- **σ_d (statFEM discrepancy scale, M-statfem only)** — std of the additive zero-mean model-discrepancy d on
  each modal frequency; units: rad/s; learned. Plays the model-error role for statFEM.
- **σ_ω (frequency measurement noise)** — 1% of ω_i,true per mode; units: rad/s. **σ_φ (shape sensor noise)**
  — 0.03 on unit-max shapes; dimensionless.
- **Posterior θ mean and 95% CI** — central 2.5/50/97.5 percentiles of θ draws; the money quantity.

## Consistency criteria (the deliverable quantities)
- **C1 concentration** — posterior θ mean vs θ_true and posterior θ SD vs replicate count n. Expected for a
  correct method at ε=0: mean→θ_true, SD↓ ~ 1/√n. Units: dimensionless.
- **C2 discretization-sensitivity** — spread = max−min of posterior θ mean across the knob levels (one
  number per construction × knob × ε). Units: dimensionless θ. Smaller = more invariant. There is no
  universal pass threshold; checker compares constructions to each other and to the σ_meas-driven noise
  floor, and reports the number — the verdict is comparative + numeric, not a magic cutoff.
- **C3 held-out coverage** — (# held-out true modal frequencies inside 95% predictive interval) / (# held-
  out frequencies × #cells). Coordinate: held-out modes 4,5,6. Target 0.95. Units: fraction.
- **θ→observable sensitivity** — dω_n/dθ = c²λ_n/(2ω_n) (identifiability); at large k_f the foundation and θ
  both raise ω², so the θ-component of the modal Fisher information shrinks — reported as a weak-
  identifiability flag.
