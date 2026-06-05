# netCG Quantity Contract (SHARED, canonical) — round 3

Master-owned. BOTH the truth-author (Codex) and the inference (Opus) MUST compute netCG by this
definition so that any residual difference is genuine model-form error, NOT a definitional mismatch.
This SUPERSEDES any netCG wording in earlier prompts / data_contract. (Round-3 blind run found ~2x of a
4.86x netCG bias was purely this definitional mismatch.)

## Definition
netCG = NET CG ACCELERATION of the LOAD = (transmitted interface force) / (rigid load mass).

- numerator: F_iface(omega) = the axial (z, launch) interface reaction force TRANSMITTED into the load
  in the COUPLED assembly when the flight force F(omega) is applied to the SOURCE.
- denominator: m_load = the rigid TOTAL load mass (isogrid panel + avionics), a CONSTANT. Use the SHARED
  published value (`observations.npz: load_mass_kg`, currently 170 kg = panel + ~136 kg avionics). Both
  sides use the same number.
- netCG(omega) = F_iface(omega) / m_load ; PSD_netCG(f) = PSD_{F_iface}(f) / m_load^2 ;
  3*GRMS_netCG = 3 * sqrt( integral PSD_netCG df ). Units: g (use g0 from the dataset).

## How F_iface MUST be computed (the part that was inconsistent)
F_iface is the DYNAMIC transmitted interface force from FREQUENCY-BASED SUBSTRUCTURING / impedance
coupling of the source and load at the single interface DOF — it RESONATES at the coupled modes.
- Couple the source free-interface apparent mass M_S(omega) and the load interface apparent mass
  M_L(omega) at the interface; apply the flight force F(omega) to the source; solve the coupled system
  for the interface acceleration a_iface(omega).
- F_iface(omega) = M_L(omega) * a_iface(omega)  (load apparent mass x coupled interface acceleration =
  the force flowing into the load). Equivalently the interface reaction force from the FBS coupling.
- netCG(omega) = F_iface(omega)/m_load = [M_L(omega)/m_load] * a_iface(omega).

## Expected / limiting behavior (use as a check)
- f -> 0: M_L -> m_load, M_S -> m_source; the stack moves rigidly; F_iface -> m_load * F/(m_source+m_load)
  and netCG -> F/(m_source+m_load) (rigid-body acceleration of the whole assembly).
- At the COUPLED resonances: F_iface and netCG AMPLIFY (this is the force-limiting "net CG" / residual-
  mass acceleration); the interface apparent-mass ANTIRESONANCE appears. netCG(f) must show resonant
  structure, NOT be a frequency-flat scaling of the forcing.

## EXPLICITLY FORBIDDEN (the two wrong options from the blind run)
- Rigid mass-ratio CONSTANT transmission: F_iface = [m_load/(m_source+m_load)] * F. That is ONLY the
  f->0 limit; it is frequency-flat and misses all coupling dynamics. (This is what the round-3 truth
  used.) Use it only as the f->0 sanity check, never as the QOI.
- Drive-point accelerance: a = F / M_zz(omega) (force / apparent mass). That is the interface
  ACCELERATION, not (interface force)/(rigid mass); M_zz is a dynamic FRF, not the load mass. (This is
  what the round-3 inference used.) Forbidden for netCG.

## Reporting
State the numerator/denominator/units/excitation/BC and show the f->0 rigid limit + the resonant
amplification in the packet. The truth-author seals its netCG scoring key computed this way; the
inference predicts netCG this way; the master scores them on the same definition.
