# Review Request — Round 3 (Claude Code Opus 4.8 runner)

What a labmate should check to find mistakes quickly. Start with packet.md (method summary up top),
then this list.

## Highest-value audits (where I am most likely wrong)
1. **Effective↔physical mass mapping** (known_failures §1). The likelihood fits the data-consistent
   2DOF reduction (effective masses 1.0/0.6 kg); netCG uses physical m_load=142 kg via the
   mass-scaling-invariant force transfer. Confirm the invariance argument (Y_s·M_L ∝ m2/m1) and that
   netCG denominator is the only place physical mass enters. Decide if this is acceptable.
2. **netCG absolute magnitude is abstract** (known_failures §2). netCG ≈ milli-g because the staged
   force scale is abstract. Confirm you read the headline as SHAPE + RELATIVE narrow-band exceedance,
   not absolute g.
3. **Local-mode residue decay (1/r²)** for the dome interface (known_failures, packet §2). I override
   the free-tip strip-FEM residues (≈flat) with 1/r² decay to represent a LOCAL mount mode (higher
   global modes have low local participation). Without it the response is broadly spiky (~20%
   exceedance); with it the first coupled mode dominates (narrow-band ~1% exceedance). Judge whether
   the local-mode decay is physically justified for your case or an over-correction.
4. **Dome 93.5 Hz = local mount mode, not breathing** (known_failures §4). Raw FEM mode1 ≈17 Hz at
   3.5 bar; a ~30× stiffness calibration maps to 93.5 Hz. Confirm the honesty framing is adequate.
5. **Higher MDOF modes are extrapolation** (known_failures §6) — not in the 2DOF data. Confirm the
   likelihood uses the single-mode reduction and only predictions carry higher modes.

## Convergence (must verify over ALL latents, not headline only)
- `nuts_diagnostics.json`: converged=True, worst rank-split R̂, min bulk & tail ESS over all 29
  monitored scalars INCLUDING every raw z_dome/z_tray latent; 0 divergences; 4 chains; non-centered.
  Recompute from `posterior_samples.npz` if you do not trust the summary.

## References / validation gate
- `validation.json`: betaL cantilever error, lumped-2DOF closed form, FBS==round-2 (rel L2 < 1e-9),
  antiresonance interlacing, netCG low-freq apparent-mass limit, anchors within 1%.

## Headline
- `results.json` → headline_narrowband_exceedance + qoi_netCG_3grms_g (95% AND 99% intervals).
- GIF `figures/interface_netcg_psd_vs_spec.gif` + `interface_psd_bands.json` (per-flight bands).
- Confirm the ONE standardized band (central 99% q0.5–q99.5 + one-sided 99%-hi exceedance fraction)
  is used before any spec-covers-flight verdict, and that a large scalar margin coexists with a
  narrow-band exceedance.

## Mesh (human inspectable)
- `mesh/`: open nodes.csv/elements.csv, model.bdf in Femap, model.vtu in ParaView, model.obj in
  Blender. Figures: mesh_assembly.png, modeshapes_dome.png, modeshapes_tray.png. Units SI metres,
  frame X radial / Z launch axis.

## Runtime / integrity
- `runtime.json` (active_runtime_s vs elapsed_wallclock_s) and `runtime_pipeline.json` (script_wall_s
  + per-stage). Immutable checker hashes verified unchanged (checks.json).
</content>
