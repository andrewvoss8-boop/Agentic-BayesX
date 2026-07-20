# Decisions Log — notch_multipoint_7004c_20260611

- D1 (sampler decision, AGENTS.md Sampler gate): NO sampler. This is a deterministic
  frequency-domain teaching/analysis study (exact small linear systems); there is no
  Bayesian updating step, so NUTS/HMC does not apply. Nothing here may be described as a
  posterior or calibrated result.
- D2 (scope, delegated by Andrew "I will leave it to your judgement", 2026-06-11 chat):
  four analytical examples EX-A..EX-D as listed in priority_deliverables.md. Rationale:
  A anchors us to the handbook with 9 checkable numbers; B isolates what 6-DOF/multi-foot
  adds with closed-form checks; C answers the "how far from a foot" question on a
  compliant backing (simply supported plate = analytic modes, fully verifiable); D closes
  the loop on the handbook's own practice (net in-axis force limiting, 7004C p.10).
- D3 (reference anchors): 7004C numeric anchors taken from the PDF text layer
  (pages 31-37, 57): Fig 9 values As(1)=50.01, Ms(1)=0.02, Ml(0.618)=1.62, Ml(1)=50.01,
  (Ms+Ml)(1)=50.03, A(0.618)=51.76, A(1)=0.02 (the notch), F(0.618)=84.08,
  F(1.618)=5.25; Fig 8 ordinate 2.64 at M2/M1=1 (handbook rounds 1.62^2; exact golden
  ratio value 2.618); Eq B1/B2; Eq 1a/1b & 2a/2b; Table 1 C^2 ranges. Complex-TDOF
  Appendix C tables are image-only in the PDF and are NOT transcribed; the complex TDOF
  method is described but not numerically replicated (documented gap, yellow-level note,
  not needed for the four examples).
- D4 (model forms): EX-B/D payload = rigid box m=6 kg on 4 feet at (+/-0.09, +/-0.07) m;
  EX-C/D backing = simply supported aluminum plate 1.0 x 0.8 x 0.005 m (analytic modes).
  Plate-coupled payload uses the 3 vertical-plane DOFs (heave z, roll thx, pitch thy);
  feet transmit vertical force only to the plate (plate bending model has no membrane
  DOFs). Full 6-DOF treatment appears in EX-B where all 6 base DOFs are enforced.
  Hysteretic (structural) damping eta=0.04 for foot springs, modal zeta=0.02 (Q=25) for
  plate modes — frequency-domain only.
- D5 (EX-D limit arms): (i) unlimited; (ii) semi-empirical net-Fz limit, C^2 from
  Eq B1/B2 at the total-mass ratio with Q=25, fb = fixed-base bounce frequency, n=1
  (7004C Eq 2a/2b); (iii) arm ii + moment limit |My| enveloped from the coupled "flight"
  analysis (7004C §5.8 FEM-based method, extended to the moment channel). Test spec =
  octave-band peak-hold envelope of flight mean foot acceleration, no extra margin.
  Limiting = per-frequency-line input scaling (linear system => direct notching).
- D6 (GIF tooling): matplotlib PillowWriter (imageio not installed); GIFs embedded in the
  PPTX animate in slideshow mode; a static key frame is also saved for the packet.
- D7 (audience): per CLAUDE.md two-level audience — structural terms used directly,
  any stats/ML concepts (none expected beyond PSD envelope logic) defined plainly.
- D10 (Andrew directive, 2026-06-12): (a) RUN the empirical-reconstruction experiment
  = EX-E; (b) write a literature-review agent prompt; (c) write ALL findings into a
  standing document in this folder for future agents doing notching work. Scope = no new
  data; deterministic. Logged because it sets durable deliverables (the findings doc +
  lit-review prompt are intended to outlive this task).
- D11 (EX-E design): test whether the 7004C IMPEDANCE method (Eq 3/4) used with MEASURED
  interface quantities can replace a coupled forced FEM, and quantify the error of SPARSE
  measurement. Ground truth = full coupled plate+payload forced response (common.py,
  already verified). Reconstructions, all from interface-only quantities (load apparent
  mass Ml, source apparent mass Ms, source free accel A_free at the feet — all computable
  WITHOUT solving the coupled system): (1) FULL 4-foot vertical matrix = exact-coupling
  verification (impedance method ≡ coupled solve); (2) SCALAR single-point condensation
  (7004C RBE2-to-one-node idealization) = bounce/net only, predicts ZERO moment;
  (3) RIGID-3 interface projection (z,θx,θy from ≥3 feet) = bounce+rocking, misses
  warping; (4) DIAGONAL-only (feet treated independent) = the decoupled-foot
  approximation. Sweep = the EX-C regimes (soft/stiff feet × plate Q25/Q6). Part 2 =
  remote-point response proxy: transmissibility from interface to points 1/2/3 foot-
  spacings away, bare-plate-calibrated vs coupled (boundary-dependence), tied to the
  EX-C visibility regime. Metrics in quantity_contracts Q10-Q12. NO sampler (still D1).
- D12 (Andrew directive "document this", 2026-06-12): added §4a "rocking-aware
  response-limit test plan from POOR, FIXED inputs" to
  notching_findings_for_future_agents.md. Captures the conversational method
  (worked out with Andrew over the last exchanges) for producing a defensible
  rocking-aware response-limited test plan when you CANNOT get better data/models
  (outdated primary model + single-point apparent mass + fixed-base Ansys payload
  modes + one near-feet flight accel). Core = predict bounce, BRACKET rocking
  (conservative default = no/shallow notch), INSTRUMENT rocking live in the test
  (≥2 spaced foot sensors + mandatory low-level run; rocking guard as its own
  differential/moment channel). Reasoning template, explicitly NOT checker-backed.
  Logged because it is a non-obvious method decision intended to outlive the chat.
- D8 (EX-C metric evolution, logged mid-run): (a) first pass detected notches as the
  deepest minimum of loaded point spectra -> polluted by bare-plate antiresonances and
  window edges; FIX = detect on the loaded/bare RATIO in the matching interface
  combination channel (mean for bounce, x-/y-differential for rocking). (b) "Deepest
  minimum wins" flipped between two near-tied stable dips (127.7 vs 148.3 Hz) under
  modal refinement; FIX = pick the prominent minimum CLOSEST to the payload fixed-base
  mode and record the whole dip CLUSTER (a finding: multi-point systems carve a cluster,
  not one notch). (c) Visibility metrics: D_change (suppression vs bare) = primary,
  D_dip (single-spectrum dip, no reference needed) = secondary. (d) r_vis (3-dB
  first-crossing) is threshold-sensitive when the median curve hovers near 3 dB (one
  variant flips global<->local under refinement while f_notch moves 0.2% and area_frac
  1.4 pts); convergence is therefore GATED on f_notch and area_frac, with r_vis reported
  as descriptive + caveat. All values in results/ex_c_results.json.
