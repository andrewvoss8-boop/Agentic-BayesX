# Truth-Author Prompt — Codex GPT-5.5 (independent ground truth)

Paste into Codex GPT-5.5 at the master repo root. Scope is bounded (conserve credits): build a
VALIDATED truth generator, emit a dataset, seal the rest. NO inference, NO NUTS, NO GIFs, NO PPT.

```text
You are the TRUTH-AUTHOR for Agentic BayesX round 3 (Codex GPT-5.5). You author an INDEPENDENT
ground-truth ("as-built reality") model and emit synthetic OBSERVATIONS for a separate inference agent.
You are modeling REALITY, not a clean engineering FEM.

CRITICAL INDEPENDENCE RULE (the point of this task):
- Your ENTIRE workspace is runs/round3/codex_truth/. Write only there.
- You MUST NOT read the inference agent's code or model: do NOT open anything under
  runs/round3/opus48/ (especially code/). Do not look at how the inference parameterizes its forward
  model or its discrepancy term. If you peek, the experiment is invalidated.
- Read ONLY: docs/agents/competitive_full_experiment/round3/blind_handoff_protocol.md (the shared,
  non-secret design assumptions + the folder split), AGENTS.md, CLAUDE.md, and
  docs/agents/competitive_full_experiment/round3/task_card_round3.md for the SHARED physical nominal
  design and conventions (units, PSD-space dB, anchors, forcing model). Treat those as the nominal
  design only.

WHAT TO BUILD (independent, richer, physically faithful):
Author a higher-fidelity coupled source(dome)+load(tray) model, single interface DOF, that starts from
the shared NOMINAL design (dome bounce mode ~93.5 Hz; tray axial mount mode ~86.25 Hz; 6 struts;
~136 kg avionics; pressurized Al dome) but is the AS-BUILT REALITY, i.e. it carries the messy effects
a real such assembly has. Include the effects YOU judge realistic — examples (not a checklist to game):
- azimuthal manufacturing / preload / strut-length variation across the 6 struts (breaks symmetry;
  splits otherwise-degenerate mount-mode pairs);
- frequency-dependent joint stiffness and non-proportional / frequency-dependent damping at the
  clevis/rod-end joints (the joints are the softest spring and the dominant damping);
- mild nonlinearity / amplitude dependence at the joints if you judge it realistic;
- local panel/dome flexibility beyond the nominal modal model (extra modes the coarse design model lacks);
- measurement realities: sensor noise that is frequency-correlated and worse near antiresonances.
Make it RICHER than a coarse linear-symmetric design FEM, but still the SAME physical system (do not
invent a different structure). You decide the specific structure, magnitudes, and which imperfections to
include — that independence is the experiment. Validate your truth FEM against analytical benchmarks
(e.g. Euler-Bernoulli betaL, lumped MDOF, drive-point antiresonance interlacing) so the truth is
physically CORRECT (reality must be right, even though it is richer).

VARIABILITY (so the inference can learn hierarchy + aleatory scatter):
- Generate N_builds = 8 independent AS-BUILT UNITS (each a fresh draw of the as-built imperfections +
  build-to-build scatter in modal frequencies/damping, ~+-5% 3-sigma on the fundamentals, plus your
  spatial/joint variation). 
- Generate N_flights = 11 flights using the SHARED forcing model (mean -6 dB design envelope, Matern
  GP, fixed 3 dB flight-to-flight). 

PUBLISH (consumable by the inference) -> runs/round3/codex_truth/dataset/:
- observations.npz (or .json): the frequency grid (dense reference grid covering ~5-600 Hz with
  mode-dense coverage); per-build COMPLEX 6-DOF diagonal interface APPARENT MASS M_ii(omega),
  i in {x,y,z,rx,ry,rz} (real+imag, translational kg, rotational kg*m^2), WITH sensor noise applied;
  per-flight interface acceleration RESPONSE PSD (g^2/Hz) on the grid AND the scalar netCG 3*GRMS
  (netCG = interface force / load mass). Include the shared forcing-model parameters (not secret).
- data_contract.md: document the schema, units, coordinate frame, DOF order, grid, build/flight counts,
  and the shared forcing model — OBSERVABLES ONLY. It must contain NOTHING about the hidden structure,
  true parameter values, or the kinds/sizes of model-form error.

SEAL (hidden from the inference) -> runs/round3/codex_truth/sealed_truth/:
- the generator code, every true parameter, each build's as-built structure, a written description of
  the model-form imperfections and their sizes, the true sigma_build / sigma_sensor / damping, and a
  scoring key (per-build modal params + the per-flight true netCG and interface PSD without noise) for
  the master to score bias / 95% coverage / held-out calibration later. The inference agent will be
  forbidden to read this folder.

ALSO (in report/): a short validation report (benchmark errors, mode list, apparent-mass figure showing
antiresonances), the FEM visualization/export (nodes.csv + elements.csv card, NASTRAN model.bdf for
Femap, model.vtu/.obj via meshio, mesh + mode-shape PNGs), units + frame, commands.md, runtime.json,
and a decisions_log.md (append-only; re-ground after any compaction from the task card + this prompt).

DO NOT: run inference/NUTS, fit anything, produce GIFs/PPT, read runs/round3/opus48/, or write outside
runs/round3/codex_truth/. Validate the truth, publish observations, seal the rest. Then stop.
```
