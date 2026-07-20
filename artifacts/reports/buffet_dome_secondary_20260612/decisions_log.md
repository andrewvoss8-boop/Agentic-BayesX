# Decisions Log — Buffet/Acoustic Dome Secondary-Structure Study (2026-06-12)

Human = Andrew. Lead = Claude (Opus 4.8 session). Decisions recorded same-day, before build.

- **D1 (Andrew):** Objective = the **secondary-structure vibration environment** (trays,
  COPVs, avionics on the dome) under ascent random forcing — NOT whole-vehicle buffet
  loads. The engineering decision supported: deriving the vibe/interface-load environment
  (and downstream test levels / notching) for dome-mounted secondary structure.
- **D2 (Andrew):** Vehicle = **representative, NOT proprietary**, anchored to publicly
  available Terran-R data. LEAD CONSTRAINT: this session has NO live web access, so
  "public data" = training-knowledge values; EVERY such number goes in the assumptions
  ledger with a confidence flag and a `VERIFY` list for a web-capable session. The
  checker treats them as assumptions, not facts.
- **D3 (Andrew):** Forcing = best practice, **buffet AND acoustic** ("include buffet and
  acoustic"). Buffet = convective Corcos-type cross-spectral density (CSD). Acoustic =
  diffuse acoustic field (DAF), sinc(kr) spatial coherence.
- **D4 (Andrew accepted lead reframe):** "Valid to 400 Hz" = the FINE REGION
  (secondary structures + local primary host) is resolved/converged to 400 Hz; the
  far-field vehicle stack is reduced (CMS + residual flexibility) and
  **uncertainty-bounded**, never claimed deterministically valid at 400 Hz.
  Certification = truncation-convergence study + monolithic-toy cross-check + CI
  coverage. A deterministic 400 Hz full-vehicle global model was assessed untenable
  (mid-frequency modal overlap; no public structural detail) and is NOT claimed.
- **D5 (Andrew accepted lead default):** Fine-region cut = **dome + load-introduction
  ring + one barrel section out to the first major ring frame**; the convergence study
  (grow the cut, add far-field modes) confirms the cut is far enough.
- **D6 (Andrew):** QOIs = (1) **strut/attachment loads** (PSD + RMS); (2) **netCG punch
  load** into the dome = net 6-DOF interface resultant per secondary assembly, axial
  (dome-normal) component highlighted — contract reuses the round-3 pinned FBS netCG
  convention; (3) a **representative secondary-structure response metric**; (4)
  **acceleration at a lumped mass on the tray** representing an avionics component
  (PSD, grms, 3 axes).
- **D7 (Andrew):** **CI is key.** Phase 3 = uncertainty layer producing interval-valued
  QOIs (propagation MC over documented priors now; NUTS only when/if real data
  calibrates — per NUTS rule, no sampler claim without diagnostics). Deterministic
  Phase 1 first.
- **D8 (lead tweak, flagged to Andrew in chat 2026-06-12):** TWO load cases, reported
  separately then enveloped — LC1 liftoff (acoustic-dominant), LC2 transonic/max-q
  (buffet-dominant) — because they occur at different flight times; a single combined
  case would overstate. Cheap to change if Andrew objects.
- **D9 (lead tweak, flagged in chat):** Load-path realism — buffet + external acoustics
  act on the barrel OML (exterior); the dome + secondaries sit in an internal
  compartment and receive an internal DAF at reduced level; external fields reach the
  secondaries structurally through the barrel/ring/dome.
- **D10 (lead):** Reuse the VALIDATED ShockSat element library
  (`artifacts/reports/shocksat_fem_modal_twin_20260609/scripts/fe_core.py`: CQUAD4
  QM6+MITC4, CTRIA3 CST+DKT, CBUSH, CONM2, RBE2; `fe_validate_report.json` ALL_OK,
  ≤0.5% vs analytic). A beam/rod element for struts must be ADDED and validated by the
  same standard before use. No porting of assembled K/M between unrelated models.
- **D11 (lead):** Lead executes Phases 0–1 in-session; helper fan-out only for bounded
  subtasks. Phase order: P0 card/assumptions/contracts → P1 fine-region deterministic
  build + forcing + QOIs (incl. forcing-math plumbing validation FIRST on an analytic
  plate) → P2 far-field wrap + coupling certification → P3 CI layer.
- **D12 (Andrew, 2026-06-12, supersedes D8):** "Just maxQ buffet is sufficient for
  now." Production load case = LC2 transonic/max-q Corcos buffet ONLY. The liftoff
  acoustic case (old LC1) and the internal DAF co-driver are DEFERRED — the DAF
  machinery stays validated (S1 G4) for later reactivation. Consequence stated
  honestly: above the buffet roll-off the predicted environment will be LOW relative
  to a real flight (acoustics would co-drive there); every QOI plot/table must carry
  the "buffet-only forcing" caveat.
- **D14 (lead, 2026-06-12 — model fix from image-QA):** fig2 exposed two ~0 Hz
  COPV mechanisms under the FIXED BC: a rigid body on two purely-translational
  mounts can spin freely about the line through the two mount points (real COPV
  cradles resist via strap wrap / clamp friction). FIX: mounts upgraded to
  6-DOF bushings — translational k_mount + rotational k_mount_rot = 1e4 N·m/rad
  (parametric, ledger B6 extension, prior 1e3–1e5). Tray strut inclination is
  now printed + warned on (a soft ~7.4 Hz tray mode flagged a possible
  bipod-splay weakness to inspect — RESOLVED: inclination is 56 deg, well above
  the 25 deg floor, so the soft ~7 Hz mode is legitimate joint-compliance
  suspension, not a splay weakness).
  **D14 UPDATE (evidence from compare_v1_d14.py — the QOI-invisible guess was
  WRONG for the COPV):** tray/strut/avionics RMS moved <=2% (invisible, as
  predicted) BUT COPV punch dropped 14.7% (44.1->37.6 N), COPV Fz -12.4%. The
  rotational mount stiffness is a REAL COPV load path, not just a spurious-mode
  cleanup. CONSEQUENCES: (a) v1 COPV numbers used a non-physical free-spin mount
  and are SUPERSEDED by D14; (b) k_mount_rot PROMOTED to a sensitivity variable
  (krlo 1e3 / krhi 1e5); (c) CI re-run on the D14 basis (COPV bands shift,
  others unchanged); (d) the optimistic hardcoded verdict string was replaced
  with a data-driven one. Honest correction logged rather than buried.
- **D15 (Andrew, 2026-06-13):** "Promote the avionics-accel channel to the
  formal response-limit proxy." DONE (response_limit_proxy.py, S8 GREEN,
  fig7): cross-spectral coherence/gain between avionics accel and the tray
  interface punch. Result: coherence 0.9999 at the 55 Hz controlling mode;
  proxy gain α=15.1 N/(m/s²) invariant to damping (0.06%) and EXACTLY to
  forcing level -> a_limit = F_allow/α is a structural constant (robust-twin
  tie); CG-accel gain = 1.17× assembly mass = 7004C effective-mass relation;
  valid band 32-300 Hz (coherence>0.8) = 77% of punch energy; decouples at the
  avionics-on-tray local mode (honest band-specificity). REFINEMENT logged
  alongside: variant table re-solved D14-consistent -> substructures are
  LARGELY (not perfectly) decoupled — ~15% dome-mediated cross-talk; "decoupled"
  wording corrected in packet + narrative.
- **D16 (Andrew flag 2026-06-15: "modes as low as 7 Hz, not realistic" + fig
  legibility):** TWO fixes. (a) FIGURES: fig4/fig5 BC-A/BC-B direct labels
  collided ("text on top of itself"); replaced with single legends; added a
  generation-time TEXT-OVERLAP AUDITOR (`save_fig` bounding-box check ->
  out/text_overlap.json) because the pixel image-QA falsely passed them.
  (b) MOUNT REALISM: the 7 Hz modes were unphysical, traced to subscale-rig
  mount idealizations. ROOT CAUSES + fixes (all verified by lowest-mode probes):
  (1) 7.4 Hz "tray" mode = the 8 kg avionics CONM2 YAWING on ONE tray node's
  artificial shell-drilling penalty -> fixed with a 4-corner BOLT FOOTPRINT
  (stiff bushings) reacting box yaw/rock through the tray membrane -> tray
  first mode 76 Hz. (2) Soft 32-55 Hz tray suspension = pin-ended axial-only
  thin tubes (cap yaw ~18 Hz even rigid) -> MOMENT-CARRYING BEAM struts
  (mount_beam) + bolted (1e9) joints + thicker (40mm) section + shorter
  standoff. (3) 7.3/18 Hz COPV = a 30 kg vessel on single-node attachments to
  the 5mm dome; STATIC TEST proved the DOME LOCAL POINT STIFFNESS (~1.1e6 N/m),
  not the mount, governs -> DOME-PATCH bracket (12-neighbor stiffener = a
  doubler/boss spreading load) + 3-point cradle near the stiff junction
  (copv_u 60->30) -> COPV ~68 Hz. RESULT: lowest mode now 67.9 Hz (was 7.3).
  Rigid-body machine-zero + mass conserved retained. The D14-soft-mount results
  are SUPERSEDED; full re-run on the D16 model. LESSON: a single-node CONM2 with
  rotational inertia on a shell reacts yaw via the drilling penalty = a spurious
  low mode; always footprint-mount lumped masses. ASSUMPTION NOTE: a heavy COPV
  on a thin dome is genuinely compliance-limited; flight designs spread load via
  wide brackets/boss or mount to frames (modeled here as the dome patch).
- **D13 (Andrew, 2026-06-12 — autonomy directive):** "Do not stop; continue to
  iterate … until meaningful experiments on all project-vision goals, easy-to-understand
  documentation, and stunning visuals interesting to Girolami, Bilionis, and
  traditional aerospace companies." Lead proceeds without per-step approval, BUT:
  durable-rule/checker-standard changes still stop for Andrew (AGENTS.md); every
  increment stays file-checkpointed + checker-backed; honesty gates unchanged
  (no claim past checker output). Vision hooks targeted: robust-twin interval
  widening (boundary bracket), response-limit proxy (avionics accel), netCG/7004C
  effective-mass tie, identifiability-honest CI drivers, coupling trust test
  (monolithic toy = the held-out analogue here).
