# Round-3 build plan (in-workspace todo)

Architecture decision (documented in packet):
- FEM (real assembled K,M,Kg in JAX) provides the MODE BASIS for each component: mode-freq ratios,
  interface participation/effective masses, mode shapes, mesh, validation. Pressure stiffening (geometric
  Kg) shown on the dome's RAW modes (p=0 vs p_op).
- NUTS INFERENCE uses a modal model anchored to the staged 2DOF data (effective interface modal masses
  m1=1.0, m2=0.6 kg) so it reduces to round-2 and converges; now adds per-structure fn AND damping
  build-to-build scatter (±5% @3σ). Inferred: f_dome1, f_tray1, ζ_dome, ζ_tray, σ_sensor, σ_build_*,
  non-centered per-build fn & damping latents.
- PHYSICAL forward prediction layer (FEM geometry, physical m_load=136+panel) computes netCG QOI and the
  MDOF interface-accelerance response PSD. Effective↔physical mass mapping documented in known_failures.

Steps:
1. [x] Step 0 priority_deliverables.md
2. [x] code/mdof_forward.py  — beam FEM (K,M,Kg), dome+tray modal bases, FBS coupling, netCG
3. [x] tests/validate_fem.py — betaL cantilever + lumped MDOF benchmark; antiresonance interlacing (ALL PASS)
4. [x] code/fem_export.py    — meshio nodes/elements/bdf/vtu/msh/obj + mode-shape & mesh figures
5. [x] code/run_pipeline.py  — NUTS (CONVERGED) + all figures + results.json + diagnostics + sensitivity
6. [x] code/make_pptx.py     — packet.pptx
7. [x] report/*.md docs, manifest, commands, files_changed, runtime, checks
8. [x] run full pipeline, validate, write packet.md

DONE. Key results: NUTS converged (worst R-hat 1.0014, min ESS 2458, 0 div over 29 vars incl raw
latents). Validation ALL PASS (FBS==round2 <1e-9, betaL 0.0011%, anchors 0%). Headline: spec covers
10/11 flights at 99%; flight 3 narrow-band 99% exceedance at 1.75% of freqs while overall scalar
margin ~14x (spec 28.3g vs iface ~2g). netCG q50 0.0041g [95% 0.0024-0.0074, 99% 0.0020-0.0087].
</content>
