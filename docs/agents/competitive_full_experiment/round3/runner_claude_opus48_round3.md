# Round-3 Runner Prompt — Claude Code Opus 4.8 (RUNS FIRST)

Opus runs FIRST this round (before Codex and Cursor). Open a fresh Claude Code session on the master
repo root, model Opus 4.8, launch with `--dangerously-skip-permissions` (your work is confined to your
workspace). Paste the block below.

```text
You are the RUNNER for Agentic BayesX, ROUND 3 (Claude Code Opus 4.8). You run FIRST this round; build
your own model — do not wait for or copy other runners. Runner only, NOT master.

WORKSPACE: your entire workspace is runs/round3/opus48/. Put EVERYTHING you create there:
code/, tests/, report/ (packet.md, figures/, mesh/, *.json), report/packet.pptx, runtime.json,
files_changed.md, priority_deliverables.md, .venv*. Read shared inputs READ-ONLY and write NOTHING
outside your workspace (not notes/, AGENTS.md, CLAUDE.md, other runners' folders, or prior rounds).

READ FIRST:
- AGENTS.md, CLAUDE.md
- docs/agents/competitive_full_experiment/round3/task_card_round3.md   (the full spec — follow it)
- artifacts/reports/mdof_femagent_scoping_20260603/recon_and_scope.md  (tools, netCG QOI, viz/export)
- runs/round3/spike/                                                   (YOUR validated FEM baseline — start here, do NOT re-derive)
- artifacts/reports/sequential_vibe_modal_flight_20260602/             (staged data, conventions, anchors)

STEP 0 — write report/priority_deliverables.md: restate the priority deliverables + acceptance tests in
your own words; flag any ambiguity and your interpretation before building.

BUILD (the only change from round 2 is SDOF -> MDOF; single interface retained):
- MDOF DOME (source, m1): spin-formed aluminum (Al 2219 or Al-Li 2198; state E, rho, nu), ~5.5 m
  diameter (R ~ 2.75 m), 2:1 ellipsoidal cap (~1.4 m), tank PRESSURIZED -> include PRESSURE/STRESS
  STIFFENING (~3-6 bar; F9 ~3-4 bar) and SHOW its effect on the modes. Tune geometry/pressure/thickness
  so dome mode 1 = 93.50 Hz (zeta_1 ~ 0.0225). HONESTY: a real 5.5 m pressurized dome will not naturally
  land mode 1 at 93.50 Hz — treat thickness/pressure/mount-location as tuning knobs and STATE which
  physical mode the 93.50 Hz is (likely a local mount-region / first interface-relevant mode, not the
  global breathing mode).
- MDOF TRAY (load, m2): isogrid aluminum panel carrying ~300 lbm = 136 kg avionics (distributed or
  lumped — state which). Minimally constrained on STRUTS to clevises (rod-end / pin-jointed), NO
  mechanical isolators. SOFTEST SPRING + MOST DAMPING AT THE JOINTS: model the strut-end interfaces
  (strut-to-tray and strut-to-dome clevis/rod-end joints) as the softest springs and the dominant
  damping source (joint compliance + joint loss / dashpot), so the tray fundamental AND its damping are
  set primarily by these joints. Start the tray fundamental at 86.25 Hz (zeta_1 ~ 0.0195); if hitting it
  forces an UNREALISTIC strut/joint stiffness, do NOT fudge — flag it, report the implied stiffness, and
  propose iterating the anchor (the human expects to iterate).
- SINGLE INTERFACE: couple source and load at ONE equivalent interface DOF (strut-to-dome attachment)
  via frequency-based substructuring / impedance of the two components' interface FRFs.
- Report the first ~5 modes of each component; key transfer functions (source free-interface apparent
  mass/accelerance, load interface apparent mass, coupled interface force) VALIDATED.

QOI = netCG = interface force / load mass (load mass = tray total ~136 kg + panel); net CG acceleration;
3*GRMS_netCG = 3*sqrt(integral PSD_{F_iface}/m_load^2 df). Expose netCG as NUMERIC 95% AND 99% intervals.

SAMPLER: default to the differentiable JAX path + real NumPyro NUTS (your spike beam is JAX). TensorMesh
P2 continuum only if you justify needing continuum geometry (then E/rho-factoring for material gradients
+ sparse eigsh). Converge over ALL sampled variables incl raw latents: rank-split R-hat < 1.01, bulk AND
tail ESS >= 100 x chains (>=400 at 4 chains), 0 divergences, >=4 chains, non-centered. Never report
"pass"/"NUTS active" if not converged. (Gradient-free TMCMC/ABC comparison is a FUTURE round — not now.)

ALSO REQUIRED (see task card for the full list):
- WHOLE-PSD/FRF likelihood is the default; peak-feature is a labeled comparison only.
- The interface response PSD is the FORCE-DRIVEN coupled INTERFACE accelerance — it MUST show the
  drive-point ANTIRESONANCE notch and the expected high-frequency behavior (not a transmissibility).
- Build-to-build now perturbs fn AND damping per structure: +-5% at 3-sigma each (sigma ~1.67%).
- -6 dB flight-mean offset = pre-data conservative DESIGN ENVELOPE (2x GRMS), NOT a GEVS margin; run a
  sensitivity sweep on it and the Matern length-scale. 3 dB flight-to-flight is fixed.
- HEADLINE: quantify the narrow-band exceedance risk (a large overall scalar margin coexisting with a
  narrow-band 99% exceedance at a coupled resonance). Standardize ONE band (central 99% q0.5-q99.5 AND
  the one-sided 99%-hi exceedance fraction per flight) before any spec-covers-flight verdict.
- FEM VISUALIZATION/EXPORT in report/mesh/: nodes.csv + elements.csv (card), model.bdf NASTRAN bulk
  data (Femap), model.vtu and/or .obj/.stl (ParaView/Blender) via meshio; report/figures/ rendered
  undeformed mesh + first 3-5 mode shapes; state units + coordinate frame.
- Plots: legends on every panel; log-frequency axes; resolution rationale + sensitivity (no hard-coded
  lines-per-band); no clipped peaks.
- Runtime: time the WHOLE producing run start->end (script_wall_s) AND per-stage active_compute_s; run
  the FULL pipeline (no replay that skips expensive stages).
- report/packet.pptx (review layer): embed mesh + mode shapes + final PSD-vs-spec PNG + key GIF frames.

VALIDATE before claiming success: mode 1 within ~1% of the anchor; first ~5 modes reported; drive-point
antiresonance interlacing shown; FEM benchmarked vs an analytical case (cantilever betaL or lumped
MDOF). You may fail — report blockers with the exact failing command. Do not overstate. Produce the full
report contract, then stop.
```
