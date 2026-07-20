# References reviewed — Card G

Inherited methodology references (verified applicable; reused, not re-derived). Where a standard/handbook is relevant
it is named with how it bears on this run (AGENTS Reference & Standards Gate).

## Method / likelihood
- **Girolami et al., StatFEM** (§3.4 statistical FEM; §4.1.5 model/mesh selection by marginal likelihood + Bayes
  factor). Bears on: the discrepancy + held-out-QOI framing; "simpler can win" (Card F Stage-1). Used as the
  evaluation philosophy, not re-implemented here.
- **Kiran et al. 2025, Bayesian FE model updating** (§4.3.1 / Eq 25 modal/eigenvalue likelihood; §5 model-class
  selection). Bears on: `modal_feature.calibrate_modal` (match measured ω² to FEM eigenvalues, NUTS) — the L5 twin
  reused byte-identical. Eq 44 evidence (Card F).
- **Ching & Chen 2007, TMCMC.** Escalation path if the multi-ref amplitude posterior goes multimodal (per the
  convergence gate). Not expected to be needed for the frequency arm (converges).
- **Beck & Katafygiotis / Beck shape inference (L8b).** Free system mode shapes pulled toward measured shapes + a
  Rayleigh-consistency term (`modal_beck_ash.py`). Bears on Part B(c): the shape-field lever, re-run with multi-ref.
- **Das & Debnath / complex (non-proportional) damping.** Per-mode / interface-CBUSH loss-factor attribution
  (`damping_inference.py`, `damping_cbush_gate.py`). Bears on Part B(c): per-mode ζ separation under multi-ref.

## Experimental modal analysis (the multi-reference physics)
- **Poly-reference / multi-reference modal identification (Allemang–Brown; LMS/EMA practice).** The core physics of this
  card: with ≥2 references the drive-participation ratio φ_{d1}/φ_{d2} is reference-invariant and over-determines modal
  damping. Roving-excitation / multi-reference is the textbook cure for the single-reference participation÷damping
  ambiguity — exactly the lever `lessons-learned #6` named. Used as the mechanistic justification for the FIM
  before/after and the drive-shape-ratio diagnostic.
- **Coherence γ²(f) = |S_xy|²/(S_xx·S_yy)**, averaged over independent IMPACTS (not segments of one transient) —
  the data-quality metric. AGENTS Discretization Gate: averaging axis = across hits; H1 estimator; force/exponential
  windows as in `realfrf.py`. The +X single-hit had only a quality-weight surrogate (~0.07); +Z/+Y/900z have ≥4 hits
  → a proper multi-average coherence is now computable.

## Data provenance
- **NASA NESC Academy ShockSat1 public delivery** (`shocksat_statfem_runner_20260609/source_manifest.md`): Test07 +X
  (fetched), Test08 +Z / Test03 +Y(modal) / Test10 900z (downloaded for this card). 128 recorders, 250 kSps, 1.00 s;
  hammer force = Recorder116 ('Ch D20', lb) for impact tests (VERIFY per test). Channel→FEM-grid: `data/channel_map.csv`.
- **Card A `units_gain_forensics.md`**: the residual units-gain is basis-normalization × model-form error, NOT a clean
  units constant; the units-honest protocol (one fixed gain per method, never peak-tuned). Binds every amplitude score.

## Standards considered and scoped out (for this run)
- NASA-HDBK-7005 / SMC-S-016 vibration-test practice: relevant to the *test* but the FRF processing/observable choices
  are already fixed by the inherited Card A pipeline; not re-opened here.
- dB vs linear: amplitude QOIs reported linear (g/lbf) with log-magnitude likelihood, per Card A convention; frequency
  axes log-scaled on FRF figures (AGENTS Plot Gate).
