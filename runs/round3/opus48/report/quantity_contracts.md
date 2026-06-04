# Quantity Contracts — Round 3 (Claude Code Opus 4.8 runner)

Each named engineering quantity: numerator, denominator, coordinate, excitation, boundary condition,
units, expected limiting/resonance behavior, reference. Written BEFORE plotting/fitting/checking.

## netCG (the QOI)
- **Numerator:** net interface FORCE F_interface(ω) into the load [N].
- **Denominator:** total physical LOAD mass m_load = tray total = 136 kg avionics + isogrid panel
  (~5.95 kg) = **~141.95 kg** [kg].
- **Definition:** netCG = net CG acceleration of the load = F_interface/m_load;
  PSD_acg(f) = PSD_Finterface(f)/m_load² ; 3·GRMS_netCG = 3·√(∫ PSD_acg df).
- **Coordinate:** load CG (single equivalent interface DOF / rigid-body translation of the tray).
- **Excitation:** flight forcing into the source (dome) interface DOF (Matérn-3/2 GP, 3 dB f2f, −6 dB
  mean design envelope).
- **Boundary condition:** single-interface FBS coupling of dome (source) and tray (load); dome base
  ring clamped (grounded).
- **Units:** acceleration; reported as 3·GRMS in **g** (g0 = 9.80665 m/s²).
- **Expected behavior:** this is the force-limited-vibration / apparent-mass framing
  (NASA-HDBK-7004). netCG PEAKS at the coupled resonance where the load apparent mass M_L peaks
  (≈ tray fundamental 86.25 Hz region) and shows a **drive-point ANTIRESONANCE notch**. **Limiting
  note (honest deviation):** the idealized free-free limit netCG→F/m_total at ω→0 assumes a free-free
  vehicle; our model has the dome GROUNDED (k1 to ground, matching the staged 2DOF), so netCG→0 as
  ω→0 (no rigid-body mode). The apparent-mass low-freq limit M_L→m_load IS verified.
- **Forcing (REVERSE-ENGINEERED, physical — deviates from round-2 abstract scaling per human
  direction):** the flat ORIGINAL (+6 dB initial) force PSD is chosen so the DOME-ONLY interface
  response peaks at **0.1 g²/Hz at the bounce mode** (same reverse-engineer process that defined the
  round-2 original force, now applied to the physical bounce-mode dome). This gives original ≈ **987
  N²/Hz**, flight-mean (−6 dB design envelope) ≈ **248 N²/Hz**. With physical masses (dome bounce
  effective mass ≈225 kg, load 142 kg) netCG is now **physically scaled (~0.9 g)**, NOT the earlier
  abstract milli-g.
- **Reference:** NASA-HDBK-7004 force-limited vibration; round-3 task card netCG contract; the 0.1
  g²/Hz dome-response anchor (staged-data Dome FEM Response PSD contract).

## Source (dome) free-interface accelerance  Y_s(ω)
- Numerator: interface acceleration a_iface [m/s²]; Denominator: applied force F [N]. Coordinate:
  dome apex / strut-attach interface DOF. Excitation: unit force at the interface, **tray removed**.
  BC: dome base clamped. Units: (m/s²)/N. Behavior: resonances at the dome modes (93.5 Hz + MDOF
  higher modes), drive-point **antiresonances interlace** between consecutive resonances. Reference:
  modal analysis (drive-point pole/zero interlacing).

## Load (tray) interface apparent mass  M_L(ω)
- Numerator: interface force F [N]; Denominator: interface acceleration a [m/s²]. Coordinate: tray
  interface DOF (through the joint). Excitation: prescribed interface motion. BC: tray free except at
  joint. Units: kg. Behavior: M_L→m_load (low freq, verified), peaks at the tray modes (joint bounce
  86.25 Hz + panel-flex >> joint). Reference: apparent-mass / force-limiting.

## Coupled interface accelerance  H_iface(ω) = a_iface/F_ext  and interface FORCE transfer F_iface/F_ext
- Numerator: interface accel [m/s²] (or interface force [N]); Denominator: applied flight force [N].
  Coordinate: single interface DOF. Excitation: flight force into source. BC: dome+tray coupled (FBS).
  Units: (m/s²)/N for accelerance; dimensionless for force transfer. Behavior: coupled resonances
  (~62, ~119 Hz + MDOF higher) with a drive-point **antiresonance notch**; high-frequency roll-off.
  This is an ACCELERANCE (force-driven), NOT a transmissibility. Reference: FBS/impedance coupling.

## Interface accelerance RESPONSE PSD (headline envelope quantity)
- Numerator: interface acceleration² spectral density [g²/Hz]; Denominator: bandwidth [Hz]. Coordinate:
  source/interface side. Excitation: flight forcing PSD into m1. BC: coupled flight config. Units:
  g²/Hz. Behavior: shaped by |H_iface|²·S_force; compared against the test spec (smoothline). Reference:
  round-2 interface response PSD convention (carried over; now MDOF).

## Tray vibe response PSD / transmissibility (likelihood channel)
- As round-2: base-driven tray transmissibility × smoothline; units g²/Hz; peak at tray fundamental
  86.25 Hz. Reference: staged-data quantity_contracts.md (fresh 2DOF).

## Modal FRFs (dome-only, coupled-interface, coupled-tray) (likelihood channels)
- Reciprocal inertance F/a [kg], log-magnitude used (phase dropped — documented deviation). Notch at
  the corresponding mode. Reference: staged-data quantity_contracts.md.
</content>
