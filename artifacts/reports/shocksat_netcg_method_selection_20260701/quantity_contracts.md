# quantity_contracts — Quantity Contract Gate (do before plotting/fitting/scoring)

## QOI: net-CG FORCE on the top tray/plate
- **Definition (numerator).** Net-CG force = Σ_i m_i a_i over the tray's mass = the mass-weighted acceleration
  integral = equivalently the interface base reaction of the tray as a payload. Per frequency:
  `S_F_qoi(ω) = |G_qoi(ω)|² · S_input`, where `G_qoi(ω)` is the modal-sum transfer from the flat input to the
  net-CG force functional and `S_input` is the known flat input PSD (level = human judgment; cancels in all
  band-RATIO metrics, so the delivery ratios are input-level-independent).
- **Modal form.** `G_qoi(ω) = Σ_modes ω² · (Σ_{tray DOFs on axis a} m_i φ_{i}) / D_i(ω)`, with
  `D_i(ω)=ω_i²−ω²+2iζω_iω`. Uniform-mass proxy over the tray region (documented; consistent-mass = sensitivity).
- **Denominator / reference.** Reported as (i) 95%-band GRMS-force RATIO vs the FEM+6 dB incumbent envelope, and
  (ii) interval width. Also the integrated band-RMS (GRMS-force).
- **Coordinate / component.** Tray-CG translational X, Y (SHEAR, in-plane) and Z (NORMAL, out-of-plane), reported
  SEPARATELY, never blended.
- **Tray region.** FEM nodes with z >= 55 in (top plate; 4646 kept-node DOFs). Struts z 45-55; box z<45.
- **Excitation.** 100%-certain FLAT input PSD applied at the hammer-impact drive point. Examine ALL FIVE drives
  (+X/Test01, +Z/Test02, +XY/Test04, +Z@900/Test06, +Y/Test03) — per-drive prediction; the other drives supply
  the held-out-DRIVE answer key. +Y is the main observability lever for the low-trust NORMAL load.
- **Boundary condition.** Free-free modal survey basis (as measured); FEM reduced model K(θ)=A_fix+Σθ_g A_g,
  mass = I (mass-normalized reduced basis).
- **Units.** Force consistent with input (N or lbf); band metrics are dimensionless RATIOS. Frequencies Hz.
- **Band.** Data/FEM band 45-260 Hz (where measured modes + coherence live). The prompt's 20-2000 Hz DELIVERY
  band is wider than the data band; outside 45-260 Hz the twin is prior-only — flagged (assumptions_ledger A?).
- **Expected limiting behavior.** Static/rigid-body limit: as ω->0 the net-CG force -> input × total tray mass
  (rigid-body sanity check). Resonance peaks at the QOI-driving modes; roll-off away from them.
- **Expected resonance behavior.** SHEAR peaks at the measured global box modes (~114-197 Hz); NORMAL peaks at
  the drumhead plate modes (~234-254 Hz).

## Two nearby conventions (named; which we use)
- **net interface FORCE** (apparent-mass / base-reaction convention; NASA-HDBK-7004C) — **USED**.
- **net-CG ACCELERATION / GRMS** (response convention) — NOT used as the deliverable, but the band-RATIO is the
  same up to the (cancelling) tray mass, so GRMS-ratio and force-ratio coincide.

## Answer-key reconstruction (held-out)
- **heldout_drive:** fit the per-mode amplitudes on 4 drives, predict the 5th drive's net-CG force spectrum; the
  5th drive's MEASURED-mode reconstruction is the answer key the twin band must envelope (well-posed for SHEAR;
  for NORMAL the drumhead SHAPE is unmeasured -> the answer key is itself uncertain -> normal falls back to
  leave_modes_out).
- **leave_modes_out:** hide a subset of MEASURED modes, recompute the band; the KNOWN correct answer is that the
  band MUST widen to cover the hidden modes' QOI contribution. A method that stays narrow FAILS (false sharpening).
