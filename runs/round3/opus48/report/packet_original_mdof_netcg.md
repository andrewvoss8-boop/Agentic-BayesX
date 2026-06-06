# Human-Review Packet — Round 3 (Claude Code Opus 4.8 runner)

MDOF source (dome) + MDOF load (tray), coupled at ONE interface DOF by frequency-based substructuring
(FBS), with the force-limited **netCG** QOI. This packet leads with the method/likelihood summary,
then the headline, then evidence and limitations. Every figure has a legend; FRF/PSD axes are
log-frequency. Read `known_failures.md` and `review_request.md` alongside this.

---

## 0. First-pass method summary (read this first)

- **Decision supported:** does the existing random-vibration TEST SPEC envelope the in-flight coupled
  environment of a 136 kg avionics tray hard-mounted (no isolators) on a pressurized dome — and where
  does the force-limited **netCG** QOI peak relative to the spec? (GEVS/GSFC-STD-7000: spec must
  envelope the flight environment; scalar 3·GRMS is a summary only.)
- **Components (the round-3 change: SDOF→MDOF each, single interface retained):**
  - **Dome (source, m1):** spin-formed Al 2219 (E=73.1 GPa, ρ=2840), 5.5 m dia, 2:1 ellipsoidal cap
    (R=2.75 m, h=1.4 m), **internal pressure 3.5 bar → geometric (stress) stiffening**. Modeled as a
    meridional-strip Euler-Bernoulli beam FEM with internal-pressure membrane tension. Mode 1 = the
    dome's global axisymmetric **bounce / breathing mode** (~110 Hz nominal; **93.50 Hz** as-built =
    0.85×110) — the whole top shell translating/breathing axially, the interface-relevant mode for an
    apex-mounted payload. **CORRECTION:** an earlier draft called this a "local mount mode" with ~1 kg
    effective mass — that was wrong (see known_failures §4). The bounce mode has a LARGE effective mass
    (~150–250 kg, comparable to the load); the code still uses the abstract staged-data value 1.0 kg
    for data-consistency (caveat flagged). My 1-D strip UNDERESTIMATES shell membrane stiffness (raw
    mode 0.79 Hz at p=0 → 17.18 Hz at 3.5 bar), needing a ~30× calibration to reach 93.5 Hz; a proper
    axisymmetric shell would land near ~110 Hz naturally. Pressure stiffening is real and SHOWN.
  - **Tray (load, m2):** isogrid Al-Li 2198 panel (stiff but light: bending t=24 mm, mass t=4.5 mm →
    panel ≈5.95 kg) carrying **136 kg avionics (lumped at centre)**, on pin-jointed struts (no
    isolators). The **strut-end joint is the softest spring AND the dominant damping**: a joint
    spring+damper sets the tray fundamental **86.25 Hz** (ζ₁≈0.0195). Panel flex modes (377 Hz, …) sit
    far above → the joint is unambiguously the softest spring. Implied joint stiffness k_j ≈ 4.17e7 N/m
    total (1.39e7/strut over 3 struts) — ~5× softer than a bare strut EA/L (7e7), i.e. plausible for a
    compliant clevis/rod-end joint (flagged, not fudged).
- **Single-interface coupling (FBS):** F_iface/F_ext = Y_s·M_L/(1+Y_s·M_L), where Y_s = dome
  free-interface accelerance and M_L = tray interface apparent mass. **Verified to reduce EXACTLY to
  the round-2 2DOF** at the first mode (rel L2 < 1e-9, validate_fem.py) — so the model stays consistent
  with the staged 2DOF data; FEM higher modes are added on top for prediction.
- **QOI = netCG** = net CG acceleration of the load = F_interface/m_load, m_load = 141.95 kg (136 +
  panel). PSD_acg = PSD_Finterface/m_load²; 3·GRMS_netCG = 3·√∫PSD_acg df. Force-limited-vibration /
  NASA-HDBK-7004 framing. Numeric 95% AND 99% intervals in results.json. (See quantity_contracts.md
  for the full contract incl. the grounded-dome low-freq caveat and the abstract-force-scale caveat.)
- **Likelihood (WHOLE-PSD/FRF, default):** tray vibe PSD (260 bins) + 3 modal FRFs (180 bins each,
  log-magnitude) + 11 flights × 2 scalar 3·GRMS. Uses the data-consistent single-mode reduction
  (== MDOF first mode). A LABELED peak-feature comparison is also reported (results.json).
- **Inferred (NUTS):** f_dome, f_tray, ζ_dome, ζ_tray, σ_sensor, σ_build_dome, σ_build_tray, and
  11×2 non-centered build latents (z_dome, z_tray). **Build-to-build now perturbs fn AND damping per
  structure (±5% @3σ, σ=1.67%)** as a forward generative assumption in the prediction (the 2DOF data
  without replicates cannot identify it). **Fixed:** masses, pressure, geometry, 3 dB f2f, −6 dB
  design-envelope offset, Matérn ℓ=0.08, MDOF mode ratios, g0.
- **Sampler:** NumPyro **NUTS**, 4 chains, 1500 warmup + 2000 draws, non-centered, target_accept 0.99.

```
graphical model (this run):
  priors: log f_dome~N(ln110,.18); log f_tray~N(ln75,.18); log ζ_dome~N(ln.018,.35); log ζ_tray~N(ln.026,.35)
          σ_sensor,σ_build_* ~ HalfNormal
  hierarchy (non-centered): build_dome[b]=σ_bd·z_dome[b]; build_tray[b]=σ_bt·z_tray[b]; z~N(0,1)
  data:  vibe PSD(build0) ← f_tray,ζ_tray,build_tray[0],σ_sensor
         3 modal FRFs(build0) ← f_dome,f_tray,ζ,build[0],σ_sensor
         flight 3GRMS[f] (tray & iface) ← f,ζ,build[f] (+ FIXED forcing σ_q)
  prediction (MDOF/FBS, physical m_load): netCG[f](ω) & interface response PSD[f](ω)
         ← posterior f,ζ + per-structure fn/ζ build scatter + 3 dB forcing GP + build PSD effect
```

---

## 1. HEADLINE (P1): narrow-band exceedance risk

`figures/interface_netcg_psd_vs_spec.gif` (11 frames) + `interface_psd_bands.json` + `results.json`.

- **Quantity:** coupled **INTERFACE accelerance RESPONSE PSD** (g²/Hz) under flight forcing — the
  force-driven response at the interface DOF (drive-point antiresonance notch present), NOT a
  transmissibility.
- **Standardized band (ONE definition, fixed before any verdict):** central 99% = q0.5–q99.5, AND the
  one-sided **99%-hi exceedance fraction** per flight.
- **Finding (the engineering answer):** a **large overall scalar margin coexists with a narrow-band
  99% exceedance.** Yet for **flight 3 (the high-energy build)** the 99%-hi band **exceeds the spec at
  ~1.3% of frequencies** at the coupled resonance (~62–86 Hz); all other 10 flights show **0%**
  exceedance at 99%. A scalar 3·GRMS check would hide this. This is the force-limiting / NASA-HDBK-7004
  insight: control the narrow band, not the scalar.
- **netCG QOI (numeric, PHYSICAL):** overall 3·GRMS q50 = **0.94 g**, 95% **[0.53, 1.67] g**, 99%
  **[0.46, 1.95] g** (per-flight in results.json). The forcing is **reverse-engineered** (per human
  direction) so the dome-only interface response peaks at **0.1 g²/Hz at the bounce mode** under the
  +6 dB initial forcing → original ≈987 N²/Hz, flight (−6 dB) ≈248 N²/Hz; with physical masses (dome
  bounce eff. mass ≈225 kg, load 142 kg) netCG is now physically scaled (~1 g), not abstract milli-g.

## 2. Component models & key transfer functions (P2) — VALIDATED
`figures/component_frfs.png`, `figures/modeshapes_dome.png`, `figures/modeshapes_tray.png`,
`figures/mesh_assembly.png`. First ~5 modes of each component in results.json/validation.json.
- Source free-interface accelerance Y_s (resonances 93.5 Hz + decaying higher modes; antiresonances
  interlace 5/5). Load apparent mass M_L (→0.6 kg low-freq limit verified; peak at 86.25 Hz joint;
  panel modes ≫ joint). Coupled interface accelerance (drive-point antiresonance notch). Coupled
  interface FORCE transfer (netCG numerator).
- **Pressure stiffening shown:** dome raw modes p=0 [0.79, 4.93, 13.81,…] vs 3.5 bar [17.18, 51.74,
  86.94,…] Hz — pressure raises fn strongly (membrane-tension dominated).
- **Validation gate (validation.json, ALL pass):** βL cantilever max err 0.0011% (nele40); lumped-2DOF
  closed-form match; **FBS == round-2 2DOF rel L2 < 1e-9**; antiresonance interlacing OK; netCG
  low-freq apparent-mass limit OK; anchors within 0.0% of 93.50/86.25 Hz.

## 3. FEM visualization / export (P12)
`mesh/`: nodes.csv + elements.csv (46 nodes, 45 line elements), model.bdf (NASTRAN, Femap),
model.vtu (ParaView), model.msh (gmsh), model.obj (Blender line geometry). Units **SI metres**; frame
**X radial, Z launch axis, Y=0**. Rendered: mesh_assembly.png + modeshapes_dome/tray.png.

## 4. Convergence (P7) — NUTS active is EARNED
`nuts_diagnostics.json`. Over **ALL 29 sampled scalars incl every raw z latent**: worst
rank-split-R̂ **1.0014** (z_dome[3]), min bulk-ESS **2458**, min tail-ESS **3198**, **0 divergences**,
4 chains, non-centered. Gate (Stan/Vehtari): R̂<1.01, bulk&tail ESS≥400, div<2% → **PASS**.

## 5. Forcing, sensitivity, resolution
- `figures/flight_forcing_overlay.png`: (left) the re-derived physical forcing — +6 dB original ≈987
  N²/Hz, −6 dB flight-mean design envelope ≈248 N²/Hz, 11 Matérn flight draws; (right) the
  reverse-engineering CHECK — dome-only interface response peaks exactly at **0.1 g²/Hz at the 94 Hz
  bounce mode**. The −6 dB offset is a **pre-data conservative DESIGN ENVELOPE (2× GRMS), NOT a GEVS
  +3 dB margin** and NOT a +6 dB/oct slope.
- `figures/sensitivity_offset_ell.png` + `sensitivity.json`: netCG 3·GRMS vs offset
  (−9→0 dB: 0.69→1.96 g, ~2.9× — the dominant decision lever), vs Matérn ℓ (~flat — integrated QOI is
  length-scale-insensitive), and vs **dome bounce effective mass** (particip 0.25/0.40/0.55 →
  141/225/310 kg → netCG 0.76/0.97/1.15 g, only ~1.5× — the force re-derivation partly compensates).
  3 dB f2f fixed.
- `figures/resolution_sensitivity.png` + `resolution_metrics.json`: mode-local refinement (cluster
  widths scale with each mode's half-power bandwidth ~2ζfn; no hard-coded lines/band). The coarse
  global grid clips the 62 Hz peak tip **23.4%**, but the integrated interface 3·GRMS QOI error vs a
  60k-point reference is only **−0.03%** — QOI robust; peak/modal ID needs the refined grid.

## 6. Trust checks
`figures/posterior_recovery.png` (priors centered at nominal 110/75 Hz; posterior recovers truth
93.5/86.25 Hz and ζ). `checks.json` (runner acceptance, all_pass=True). `runtime.json` (active 235.7 s).
Immutable checker hashes verified unchanged (shasum -c manifest.sha256: 4/4 OK). `packet.pptx` = review
layer (mesh + mode shapes + FRFs + final PSD-vs-spec + netCG + sensitivity + GIF frames).

## 7. Limitations (see known_failures.md)
Effective↔physical mass mapping; abstract netCG g-scale; grounded-dome low-freq netCG→0; dome 93.5 Hz =
local mount mode (calibrated); 1-D meridional-strip dome (not a shell); MDOF higher modes are
extrapolation beyond the 2DOF data (likelihood uses the single-mode reduction); log-magnitude modal
likelihood; fn/damping build scatter is fixed-generative; single equivalent interface DOF; one
realization. **One-command replay:** `PYTHONPATH=.pylibs .venv_nuts/bin/python code/run_pipeline.py`.
</content>
