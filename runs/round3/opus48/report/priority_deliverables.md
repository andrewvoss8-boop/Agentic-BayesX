# Priority Deliverables — Round 3 (Claude Code Opus 4.8 runner)

Step 0 per the task card: restate the PRIORITY asks in my own words, my interpretation, where
each is delivered, and flag ambiguity BEFORE building. A priority with no delivered artifact is a
failure; an "assumed" interpretation without human confirmation is a warning.

## My one-line understanding of the round
Take last round's SDOF-each → 2DOF coupled system to **MDOF-each** (dome multi-mode, tray multi-mode),
keep ONE interface DOF, couple by frequency-based substructuring (FBS), and report a new QOI
**netCG = interface force / load mass** with honest convergence and an inspectable FEM mesh. The
headline engineering point is the **narrow-band exceedance risk**: a comfortable overall (scalar)
margin can hide a narrow-band 99% exceedance at a coupled resonance (force-limiting / NASA-HDBK-7004).

| # | Priority ask (my words) | Interpretation / assumption | Where delivered |
|---|---|---|---|
| P1 | **Headline:** quantify narrow-band exceedance risk; standardize ONE envelope band (central 99% = q0.5–q99.5 AND one-sided 99%-hi exceedance fraction per flight) before any spec-covers-flight verdict | netCG response PSD vs spec, per flight; report numeric 95% AND 99% netCG intervals | `report/figures/interface_netcg_psd_vs_spec.gif`, `interface_psd_bands.json`, `results.json` |
| P2 | **MDOF dome (source m1):** spin-formed Al, ~5.5 m, 2:1 ellipsoidal, PRESSURIZED with stress/pressure stiffening shown; tune so dome mode 1 = 93.50 Hz (ζ₁≈0.0225); state which physical mode 93.5 Hz is | Beam-FEM meridional strip with geometric (membrane-tension) stiffening from internal pressure; 93.5 Hz = local mount-region/interface mode, NOT global breathing. Honesty note included. | `code/mdof_forward.py`, `report/packet.md` §2, `assumptions_ledger.md` |
| P3 | **MDOF tray (load m2):** isogrid panel + 136 kg avionics on pin-jointed struts (no isolators); softest spring + most damping AT THE JOINTS set tray fundamental 86.25 Hz (ζ₁≈0.0195); flag if implied stiffness is unrealistic | Tray = free panel beam-FEM + 136 kg avionics, attached to interface through joint spring+damper (k_j,c_j); joint sets fundamental & damping. Implied k_j reported with realism flag. | `code/mdof_forward.py`, `report/packet.md` §3 |
| P4 | **Single interface:** couple source & load at ONE interface DOF via FBS/impedance of the two interface FRFs | Driving-point accelerance FBS: F_iface = Y_s/(Y_s+Y_L)·F_ext | `code/mdof_forward.py` `couple_*`, `quantity_contracts.md` |
| P5 | Report first ~5 modes of each component; key transfer functions (source free-interface apparent mass/accelerance, load interface apparent mass, coupled interface force) VALIDATED | Modes + FRFs in results.json + figures; validated vs analytical benchmark | `results.json`, `report/figures/component_frfs.png`, `tests/validate_fem.py` |
| P6 | **netCG QOI** = F_iface/m_load; PSD_acg = PSD_Fiface/m_load²; 3·GRMS_netCG; expose as NUMERIC 95% AND 99% intervals | quantity contract written before plotting | `quantity_contracts.md`, `results.json` |
| P7 | **Sampler:** differentiable JAX + real NumPyro NUTS; converge over ALL sampled vars incl raw latents (rank-split R̂<1.01, bulk&tail ESS≥400 at 4 chains, 0 divergences, ≥4 chains, non-centered) | JAX path (spike Path A). No "NUTS active" unless gate passes. | `nuts_diagnostics.(md\|json)` |
| P8 | WHOLE-PSD/FRF likelihood is default; peak-feature is a LABELED comparison only | whole-curve log-likelihood; peak-only fit shown as labeled comparison | `report/packet.md`, `results.json` `peak_feature_comparison` |
| P9 | Build-to-build now perturbs fn AND damping per structure: ±5% at 3σ each (σ≈1.67%), lognormal, on top of PSD-level build effect | 4 per-structure scatter latents (dome fn, tray fn, dome ζ, tray ζ) non-centered | `code/run_pipeline.py` model |
| P10 | −6 dB flight-mean offset = pre-data conservative DESIGN ENVELOPE (2× GRMS), NOT a GEVS margin; sensitivity sweep on it AND the Matérn length-scale; 3 dB f2f fixed | sensitivity sweep figure + table | `report/figures/sensitivity_offset_ell.png`, `resolution_sensitivity`/`sensitivity.json` |
| P11 | Interface response PSD must be the FORCE-DRIVEN coupled INTERFACE accelerance with drive-point ANTIRESONANCE notch + correct HF behavior (NOT a transmissibility) | netCG/interface accelerance from FBS; antiresonance shown & checked | `report/figures/interface_netcg_psd_vs_spec.gif`, validation |
| P12 | **FEM viz/export** in report/mesh/: nodes.csv + elements.csv, model.bdf (NASTRAN), model.vtu and/or .obj/.stl (meshio); figures/ undeformed mesh + first 3-5 mode shapes; state units + frame | meshio exports + rendered figures; SI units, stated frame | `report/mesh/*`, `report/figures/mesh_*.png`, `report/figures/modeshapes_*.png` |
| P13 | Plots: legends every panel; log-freq axes; resolution rationale + sensitivity (no hard-coded lines/band); no clipped peaks | enforced in plotting | all figures |
| P14 | Runtime: time WHOLE producing run (script_wall_s) AND per-stage active_compute_s; full pipeline (no replay skipping expensive stages) | one wall timer + per-stage | `runtime.json` |
| P15 | `report/packet.pptx` review layer: embed mesh + mode shapes + final PSD-vs-spec PNG + key GIF frames | python-pptx | `report/packet.pptx` |
| P16 | Full report contract: packet.md, results.json, assumptions_ledger, quantity_contracts, nuts_diagnostics, known_failures, review_request, manifest.json, commands.md, files_changed.md, runtime.json, checks.json | — | `report/*` |

## Ambiguities flagged (interpretation stated; cannot ask mid-run → assumptions prominent)
1. **Anchor = COMPONENT (uncoupled) fundamentals.** Round-2 truth was dome-uncoupled 93.5 Hz
   (110×0.85) and tray-uncoupled 86.25 Hz (75×1.15). I anchor the MDOF **component** fundamentals to
   these, matching the topology ground–k1–[dome]–k_joint–[tray] that generated the staged 2DOF data.
   So the MDOF model reduces to the round-2 2DOF at the first mode (it stays consistent with the data),
   and the new MDOF content is the higher modes above the data-informative band. **Assumption.**
2. **netCG vs round-2 QOI.** netCG = F_iface/m_load (net CG accel of the load) is DISTINCT from the
   round-2 tray-response 3·GRMS. I report netCG as the primary QOI and keep the interface-accelerance
   response PSD as the headline envelope check. **Interpretation.**
3. **FEM path.** Default to spike Path A (JAX Euler-Bernoulli modal-superposition MDOF) for speed +
   NUTS-compatibility, per the recon policy. TensorMesh P2 continuum is NOT needed (no continuum-geometry
   requirement that beam modal-superposition cannot meet); stated reason. **Decision.**
4. **Dome 93.5 Hz physical identity.** Stated as a local mount-region / first interface-relevant mode,
   tuned via thickness + pressure + mount location; a real 5.5 m pressurized dome breathing mode is not
   at 93.5 Hz. **Honesty note**, not a silent fudge.
5. **Tray fundamental from joints.** If hitting 86.25 Hz forces an unrealistic joint stiffness I report
   the implied k_j and flag it rather than fudging.
</content>
</invoke>
