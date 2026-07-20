# assumptions_ledger.md — StatFEM consistency toy (Experiment A)

AGENTS.md Assumptions-and-Uncertainty gate. Numerical value, units, rationale, source, sensitivity priority.
All quantities nondimensional unless stated.

## Physical truth (data-generating)
| symbol | value | units | rationale / source | sensitivity priority |
|---|---|---|---|---|
| L | 1.0 | length | unit rod | low (rescales) |
| ρA | 1.0 | mass/length | nondim | low |
| EA_nom | 1.0 | force | c_nom²=EA/ρA=1 | low |
| θ_true | 1.15 | – | truth 15% stiffer than nominal; off-centre so "concentrate on θ_true" is a real test | HIGH (the target) |
| ε = k_f | {0.0, 0.3} | Winkler modulus (nondim) | 0 = no-error control (consistency MUST hold); 0.3 = model-form error the inference OMITS | HIGH (the controlled error) |
| n_modes (fit) | 3 | count | first 3 modes used for calibration | medium |
| held-out modes | 4,5,6 | – | coverage C3 band, never fit | medium |
| m (sensors) | 7 | count | interior sensors at x=k/8, k=1..7 (mode shapes) | medium |
| σ_ω | 1% of ω_i,true | rad/s | modal frequencies are measured precisely | medium |
| σ_φ | 0.03 | – | shape sensor noise on unit-max shapes | medium |
| n (replicate tests) | {1,4,16,64} | count | data-growth axis for C1; single realization per replicate | HIGH (drives concentration) |

## Numerical knobs (the independent variable — Discretization-Resolution gate)
| knob | construction | levels | log/linear | rationale |
|---|---|---|---|---|
| N_c (collocation/grid pts) | M-lik, M-ift | {8,16,32,64,128} | ~log2 | field/operator resolution; carries NO real info |
| σ_r (residual pseudo-noise) | M-lik | {1e-3,1e-2,5e-2,2e-1,1.0} | log | FICTITIOUS noise on "residual≈0"; carries NO real info |
| h = L/n_el (mesh) | M-statfem | n_el∈{4,8,16,32,64} | ~log2 | FE mesh; refine toward analytic |

## Inference settings
| symbol | value | units | rationale | priority |
|---|---|---|---|---|
| θ prior | LogNormal(ln 1, 0.30) | – | wide, centred at nominal 1 (not at truth) | medium |
| ω_i prior | LogNormal(ln ω_i,nom, 0.15) | rad/s | centred on nominal modal freq, keeps mode ordering | medium |
| τ (field prior std, M-lik) | 1.0 | shape units | vague field prior | LOW (checked) |
| τ_0 (ridge, M-ift) | 1e-3 | – | makes physics-prior proper | LOW (checked) |
| β prior (M-ift) | LogNormal(ln 1e3, 2.0) | – | wide; learned inverse-temperature | HIGH (the self-calibration) |
| σ_d prior (M-statfem) | HalfNormal(0.3·ω_1) | rad/s | additive statFEM discrepancy scale | HIGH (absorbs model error) |
| NUTS | 4 chains, 1000 warmup, 1000 draws, target_accept 0.9 | – | AGENTS.md sampler gate | – |
| float64; OMP/VECLIB threads | on; =1 | – | AGENTS.md compute | – |

## Uncertainty taxonomy (kept distinct)
- **Parameter uncertainty**: θ posterior (the headline).
- **Observation noise**: σ_ω, σ_φ (iid Gaussian, known).
- **Model discrepancy / model-form error**: the omitted foundation k_f=ε. Represented in inference by
  σ_r (M-lik, fixed knob), β (M-ift, learned prior weight), σ_d (M-statfem, learned discrepancy). This is
  the SAME physical error seen through three different statistical lenses — the experiment.
- **Discretization error**: N_c, h (the independent variable; bounded by the solver-validation gate).
- **Aleatory / build-to-build / flight-to-flight**: NOT modeled (single synthetic structure). Flagged.

## Data count (explicit)
One synthetic structure (one θ_true, one foundation per ε). For C1, n replicate noisy modal tests are drawn
with distinct seeds. For the knob sweeps, n=8 fixed. No flight-to-flight or build-to-build variability.
Single-realization cells are flagged YELLOW (realization-dependent).

## Known limitations (honest)
- The model-form error is a SURROGATE (Winkler foundation), not a measured real-structure discrepancy.
- One spatial parameter (scalar θ); a real calibration has many — identifiability is easier here.
- The marginalised-Gaussian likelihoods for M-lik/M-ift are the field-integrated form of the residual-as-
  fictitious-data model; an explicit latent-field NUTS run is used only as a verification cross-check.
- Verdicts are for THIS toy; they evaluate the CONSTRUCTIONS' behaviour, not a universal proof.
