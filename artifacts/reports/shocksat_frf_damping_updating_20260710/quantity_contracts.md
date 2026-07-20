# Quantity Contracts — ShockSat FRF-Domain Damping Updating (20260710)

Every named quantity: numerator, denominator, coordinate, excitation, boundary condition, units, limiting and
resonance behavior, reference. Defined BEFORE plotting/fitting/checking (AGENTS Quantity Contract Gate).

## Forward quantity: accelerance FRF H(ω)
- **Definition:** H_sk(ω) = a_s(ω)/F_k(ω), acceleration response at sensor DOF s per unit force at drive DOF k.
- **Numerator/denominator/units:** numerator = acceleration [g, g=386.0886 in/s²]; denominator = force [lbf];
  units **g/lbf** (accelerance). Reused `predict_logH` returns log10|H| in these units (÷ G_IN_S2).
- **Coordinate:** sensor DOF = nearest live translational DOF to the accelerometer (channel_map), drive DOF =
  nearest live translational DOF to the impact point/axis. **Excitation:** roving-hammer H1 estimate.
- **Boundary condition:** free-free (suspension RBM well below first elastic 54.2 Hz; 6 RBMs dropped).
- **Model form:** modal superposition over 80 reduced modes,
  H(ω) = −ω² · Σ_i (U_s,i U_k,i)/D_i(ω), D_i = ωᵢ² − ω² + 2j ζ_i ωᵢ ω  (viscous)
  or D_i = ωᵢ²(1 + j η_i) − ω²  (structural/loss-factor), ζ_i / η_i from the damping action space (below).
- **Limiting behavior:** ω→0 accelerance → 0 like ω² (mass line inverted); ω→∞ → sensor/drive residual.
  **Resonance:** peak at ωᵢ with height ∝ 1/(2ζ_i) (viscous) or 1/η_i (structural); antiresonances between
  co-located peaks. **Reference:** Ewins, *Modal Testing*; matches reused femlib convention (V-gates).

## Correlation metrics (FRF domain)
- **FRAC** (Frequency Response Assurance Criterion; Heylen & Lammens 1996). Per channel s over frequency set Ω:
  FRAC_s = |Σ_ω Hp_s(ω)* Hm_s(ω)|² / [ (Σ_ω |Hp_s|²)(Σ_ω |Hm_s|²) ], ∈[0,1]. We compute it on **log10|H|**
  (mean-removed) so it reduces to Pearson correlation of log-magnitude (weights avoid antiresonance domination;
  literature §2). Numerator = squared cross term; denominator = auto-energy product; dimensionless.
- **FDAC** (Frequency Domain Assurance Criterion; Pascual-Golinval-Razeto 1997). Surface over (ω_a analysis,
  ω_e test) for a channel: FDAC(ω_a,ω_e) = ( Σ_s Hp_s(ω_a) Hm_s(ω_e) ) form, **improved cosine (real inner
  product, phase-sensitive, ∈[−1,1])** to avoid pairing 180°-out-of-phase responses. **Ridge** ω_e*(ω_a) =
  argmax over ω_e = the per-channel frequency-shift map. Used to (i) SELECT updating bands where the ridge is
  clean and away from resonance/antiresonance, (ii) build the alignment warp. **Train-side only.**
- **FRSF** (Frequency Response Scale Factor; MSF analog). At FDAC-aligned matched peaks:
  FRSF_s = (Σ Hm_s* Hp_s)/(Σ |Hp_s|²) (real, complex-MSF form) → magnitude ratio; amplitude/damping scale
  error. Reported as |FRSF−1| and in dB (20·log10 FRSF). FRSF=1 ⇔ perfect amplitude match.

## Scored quantities
- **P1′ (primary) = FDAC-aligned FRAC.** Median over usable channels of FRAC(log10|H_pred warped|, log10|H_meas|)
  AFTER applying the train-side per-channel frequency-alignment warp, over the FDAC-selected band ⊆ [45,260] Hz,
  fold-averaged (4 LODO folds) with per-fold spread. Physics-honest: θ_MAP + train-fit damping (frozen) + ONE
  global gain/fold; NO per-mode/per-channel amplitude or damping fit. Dimensionless ∈[−1,1]. Higher better.
- **P2′ (amplitude/damping) = FRSF error.** Median over channels of |FRSF−1| (and dB) at FDAC-aligned matched
  peaks. Lower better. The direct measure of what damping updating buys.
- **P3 (comparability) = raw log|H| correlation.** The completed run's metric (median per-channel Pearson corr
  of log10|H|, 45–260 Hz, no warp). Reported so this run is comparable to the completed run; **P1′ − P3 = the
  FDAC-alignment gain** (quantified, not assumed).
- **Usable channel:** median in-band coherence ≥ 0.6 (same rule for every candidate incl. A0/A0d).

## Damping action-space parameters (units + physical bounds)
- **Band modal ζ** (dimensionless, fraction of critical). 4 bands (D8). Prior center 0.30% (survey median, D7);
  hard gate bound **[0.2%, 5%]**. Enters as ζ_i = ζ(band containing fᵢ).
- **Rayleigh α [1/s], β [s]** with ζ_i = α/(2ωᵢ) + β ωᵢ/2. 2 params. Same ζ gate applied to the implied ζ_i.
- **Per-joint-group structural loss factor η_g** (dimensionless), localized to joint groups (CBUSH `joints`,
  `contact`). Composite per-mode η_i = Σ_g η_g · SE_{i,g}, SE_{i,g} = (Qᵢᵀ A[g] Qᵢ)/(Qᵢᵀ K(θ) Qᵢ) = modal
  strain-energy fraction in group g. Hard gate bound **η_g ≤ 0.2**. Relation near resonance η ≈ 2ζ.
- **Total damping dimension ≤ 10 per candidate** (checker-enforced). No per-channel/per-mode free damping.

## Secondary QOI: net-CG statFEM F(k)
- Net-CG shear and normal apparent-mass / interface-force bands per the netcg conventions
  (`shocksat_netcg_method_selection_20260701/code/netcg_qoi.py`), reused unchanged. Coverage = fraction of
  measured F(k) inside the predictive band; hard gate ≥ 0.95; energy-weighted exceedance ≤ 0.5 dB. Units per
  netcg (interface force normalized). Reference: the netcg thread + NASA-HDBK-7004C force-limited framing.
