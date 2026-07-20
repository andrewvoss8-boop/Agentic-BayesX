# Quantity Contracts (pinned BEFORE plotting/fitting/checking — AGENTS.md gate)

All spectra single-sided in Hz unless stated; band of record 20–400 Hz; modes solved to
~800 Hz for truncation margin. Frequency axis log-scaled on all plots; linear magnitude
(no dB) unless explicitly justified per plot.

## Q1 — Strut / attachment load
- Quantity: internal force in each tray strut (axial, local strut axis) and each COPV
  mount bracket (3 translational components, mount local frame).
- Form: PSD `S_F(f)` [N²/Hz] + RMS [N] over 20–400 Hz, per load case (LC1, LC2).
- Excitation: pressure-field CSD (Q5/Q6) applied per D9; BC: fine-region boundary per
  task card (parametric placeholder in P1, CMS far-field in P2).
- Limiting behavior: f → 0 (below first suspension mode) load → quasi-static pressure
  resultant share; resonant peaks at coupled tray/COPV-on-mount modes; roll-off above
  local modal cluster unless dome modes re-inject.
- Reference: NASA-HDBK-7005 (random vibe practice); 7004C for force-limit context.

## Q2 — netCG "punch" load into the dome
- Quantity: NET interface resultant transmitted by a secondary assembly (tray incl.
  avionics lump; separately the COPV) into the dome = vector sum of all its attachment
  interface forces (+ moments about the assembly CG), expressed in dome-local frame;
  "punch" = dome-normal (axial) component, highlighted.
- Form: PSD [N²/Hz] (+ moment N²m²/Hz) + RMS, per load case.
- Convention: REUSES the round-3 pinned FBS netCG contract (dynamic FBS interface
  force; net force / assembly mass = CG acceleration in the rigid band). Sanity tie:
  below the first elastic mode of the assembly, `S_Fnet(f) ≈ (m_assy)² · S_aCG(f)`
  (effective-mass argument, NASA-HDBK-7004C). The checker tests this tie.
- Trap (logged 7004C study): net Fz can be ~0 while individual feet carry large
  opposing loads — Q1 and Q2 are BOTH reported, never one as proxy for the other.

## Q3 — Representative secondary-structure response metric
- Quantity: spatial-maximum and spatial-median acceleration PSD over the tray plate
  nodes and over the COPV shell nodes (out-of-plane / radial respectively), plus the
  band RMS [g RMS]. Chosen as the "good representative" because it feeds straight
  into a response-limit proxy (project D7 response-limiting decision, 2026-06-10).
- Form: PSD [g²/Hz] + gRMS, per load case; report which node realizes the max.
- Limiting behavior: mass-law-like floor between modes; peaks at local plate/shell
  modes; max/median ratio exposes spatial concentration.

## Q4 — Avionics lumped-mass acceleration
- Quantity: absolute acceleration at the lumped avionics mass node on the tray
  (CONM2-style attachment), 3 axes in tray-local frame.
- Form: PSD [g²/Hz] + gRMS per axis, per load case; this is the "specific location"
  ask and the future response-limit channel.
- Limiting behavior: follows tray base below first tray mode; amplifies Q≈1/η at the
  avionics-on-tray mode; isolates above (mass-spring roll-off) unless higher tray
  modes re-excite.

## Q5 — Buffet pressure field (forcing, not response)
- Quantity: fluctuating wall-pressure cross-spectral density on the barrel OML,
  `S_pp(x, x', f)` [Pa²/Hz], homogeneous Corcos form:
  `S_pp = Φ_p(f) · exp(−α_x·2πf|ξ|/Uc) · exp(−α_y·2πf|η|/Uc) · exp(+i·2πf·ξ/Uc)`,
  ξ = streamwise (vehicle-axial) separation [m], η = circumferential separation [m],
  Uc = convection speed [m/s], α_x ≈ 0.12 streamwise decay, α_y ≈ 0.72 lateral decay
  (dimensionless; values = documented assumptions w/ sensitivity).
- `Φ_p(f)` [Pa²/Hz]: broadband level set by rms Cp · q̄ with a documented spectrum
  shape; energy concentrated low (full-scale buffet rolls off well above ~O(10²) Hz)
  — this is WHY acoustics co-drives the top of the band (D3/D8).
- Limiting behavior: coherence length L(f) ≈ Uc/(α·2πf) shrinks with f (Andrew's
  "varied correlations based on length scale/frequency"); fully-correlated limit as
  f→0 over small apertures; phase term = downstream convection.
- Reference class: Corcos 1963; launch-vehicle buffet practice (NASA SP-8001-era);
  values are representative, NOT vehicle-verified.

## Q6 — Acoustic pressure field (forcing)
- Quantity: diffuse acoustic field CSD, `S_pp = Φ_a(f) · sinc(k r)`, k = 2πf/c air,
  r = |x−x'| (3-D separation) [m]; real, no convection phase.
- `Φ_a(f)` from an OASPL + octave shape (assumptions ledger): external liftoff level
  on the barrel OML (LC1), reduced internal-compartment level direct on dome +
  secondaries (both LCs, D9).
- Limiting behavior: sinc → 1 fully-correlated at low f / small r; first zero at
  r = c/(2f); at 400 Hz c/(2f) ≈ 0.43 m → patch correlation matters at tray scale.

## Q7 — Fine-region boundary / interface impedance (coupling object)
- Quantity: driving-point + transfer dynamic stiffness (equivalently apparent mass
  [kg]) at the fine-region cut DOF set, 0–400 Hz.
- P1: bracketed by two parametric placeholder BCs (fixed vs mass-loaded) — QOI spread
  between brackets is REPORTED as boundary-condition uncertainty, not hidden.
- P2: CMS far-field with residual flexibility + prior. Contract per
  apparent-mass-convention-postmortem.md: numerator/denominator/BC stated on every
  apparent-mass plot; source vs load apparent mass never conflated.
