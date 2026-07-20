# Task Card — Representative LV Dome Secondary-Structure Vibe Under Buffet + Acoustics

## Task
Build a representative (public-data, non-proprietary) Terran-R/Falcon-9-class FEM
focused on the dome-mounted secondary structures (avionics tray + COPV), drive it with
best-practice buffet (Corcos convective CSD) and acoustic (diffuse-field) random
pressure, and deliver four interface/response QOIs to 400 Hz with confidence intervals.

## Why This Matters
Supports the engineering decision: what random-vibe / interface-load environment do
dome-mounted secondary structures see during ascent, and what test levels / notching
follow — with intervals that widen honestly where the vehicle model is unknowable
(robust-twin program objective).

## Scope Reframe (Andrew-approved, decisions_log D4/D5)
"Valid to 400 Hz" means: the FINE REGION (dome + load-introduction ring + barrel
section to the first major ring frame + tray + COPV + avionics lumped mass) is
mesh- and truncation-converged to 400 Hz; the far-field stack is CMS-reduced with
residual flexibility and carries a PRIOR (uncertainty-bounded boundary impedance),
never a deterministic 400 Hz claim. Coupling certified by:
(a) truncation-convergence study (grow cut, add modes; QOI shift inside CI),
(b) monolithic-toy cross-check (full solve vs reduced on an affordable model),
(c) CI coverage as the backstop.

## Phases
- **P0** (this card): decisions, priority deliverables, quantity contracts,
  assumptions ledger (every public number confidence-flagged + VERIFY list).
- **P1**: fine-region deterministic build.
  - Step 1 FIRST: forcing-math plumbing validation on an analytic simply-supported
    plate (CSD → joint acceptance → modal force → response PSD) with
    limiting-behavior checks. The genuinely new math gets validated before the FEM.
  - Step 2: fine-region mesh (reuse validated ShockSat `fe_core.py` shells; ADD +
    validate beam/rod for struts), modes to ~800 Hz (2× band margin), boundary =
    parametric far-field placeholder (fixed / mass-loaded bounds bracket it).
  - Step 3: LC1 (liftoff acoustic) + LC2 (max-q buffet) → four QOIs, 20–400 Hz;
    mesh-convergence + coherence-length & damping OAT sensitivities.
- **P2**: far-field CMS wrap + residual flexibility; coupling certification (a)+(b).
- **P3**: CI layer — propagate documented priors (damping, forcing level/coherence,
  mount stiffness, boundary impedance, skin gauge) → interval QOIs. NUTS only if
  real data enters (per AGENTS.md sampler rule); otherwise labeled propagation MC.

## Allowed Work
- Read: whole repo; reuse-validate `artifacts/reports/shocksat_fem_modal_twin_20260609/scripts/fe_core.py`.
- Edit: this workspace only (+ notes/todo/memory/project_log rows per lead role).
- Run: python3/numpy/scipy in-workspace; detached launch for anything near the tool timeout.

## Not Allowed
- Claiming a validated full-vehicle 400 Hz model, or presenting training-knowledge
  vehicle numbers as verified facts.
- Fabricated metrics/figures; checker edits during a trial; porting assembled K/M
  from unrelated models.

## Main Command
`bash run_all.sh` (grows by phase; each stage idempotent; exits non-zero only on RED).

## Required Checks
- `python3 check.py` → `checker_report.json` (green/yellow/red per gate).
- Element-addition validation report (beam/rod) before any strut result.
- Forcing-math validation JSON before any QOI result.

## Expected Files
task_card.md, priority_deliverables.md, decisions_log.md, quantity_contracts.md,
assumptions_ledger.md, scripts/, out/, check.py, checker_report.json, run_all.sh,
runtime.json, packet.md (when results exist), figures/ (Tufte-linted).

## Human Stop Points
- D8 (two load cases) and D9 (internal/external load path) are lead defaults Andrew
  may override.
- Before P3 prior choices become durable standards, and before any publication use.
