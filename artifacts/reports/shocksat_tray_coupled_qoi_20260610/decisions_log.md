# Decisions log — shocksat_tray_coupled_qoi_20260610

Runner = Claude Code lead acting as runner (continuing the D9 lead-as-runner
arrangement from the predecessor; Andrew launched this phase directly).
Scope authority: predecessor decision D38 (locked scope) + task card
`docs/lab/shocksat_tray_coupled_qoi_runner_prompt.md`.

- D1 (2026-06-10, session start): Workspace created at
  `artifacts/reports/shocksat_tray_coupled_qoi_20260610/`. Scope per D38:
  QOI = net CG interface load (Fx,Fy,Fz) on the hypothetical tray; single-point
  6-DOF condensation; mount = uncertain 6-DOF CBUSH; methods = time-history
  (reference) + modal-SRS + PSD/Miles (envelope arm); coupling = uncoupled vs
  coupled (LM-FBS); distributed multi-mount arm DROPPED; shock ground-truth
  case SKIPPED (no probe planned — no specific reason exists to run one).
  **SAMPLER DECISION (AGENTS.md gate): NO sampler is run in this task.** This
  is forward uncertainty PROPAGATION (reuse of the predecessor's converged
  NUTS posterior `nuts_full_samples.npz` for theta_S + priors for tray/mount),
  not Bayesian updating — there is no measured data for the tray or mount to
  update against (the coupled QOI is hypothetical). No NUTS claim is made; no
  convergence gate applies. If a future task calibrates the mount from data,
  NUTS/HMC is the default.

- D2 (2026-06-10): **Base input = specified synthetic stationary Gaussian
  random**, NOT the measured strut-base pyro motion. Reasons: (a) D38 puts the
  shock ground-truth case at default SKIP and the card allows "a specified
  moderate random/transient"; (b) using the pyro .mat would touch the vaulted/
  blind held-out data (memory.md: re-vault before any new blind run) for no
  scope benefit; (c) a flat-PSD band-limited input makes the method comparison
  cleanest (Miles consumes the exact analytic PSD — no SRS→PSD conversion knobs
  needed at all). Spec: 3 independent axes, flat 0.01 g^2/Hz over 20–250 Hz
  (1.52 grms/axis), T = 20 s, fs = 2048 Hz, 8 seeds. Rotational base input = 0.
  FLAGGED for Andrew sign-off (cheap parametric rerun if he prefers another
  level/band/signal class).

- D3 (2026-06-10): **Tray placement (INVENTED)** = single mount point at the
  center of ShockSat's Top_Circular_Plate (top deck, z ≈ 57.75 in; exact grid
  id recorded in `out/mount_node.json` once selected by nearest-to-axis
  search). Tray axes aligned with ShockSat global axes (z up = deck normal).
  Honesty note: the tray's physical foot circle (~20.8 in span) is wider than
  the 18-in top plate — physically it would not bolt on as-is. Under
  single-point condensation this does not affect the net-CG-force QOI, but it
  underlines that this is a METHODS DEMO, not a buildable configuration.
  Sensitivity arm: one alternate mount node near the plate edge.

- D4 (2026-06-10): **Mount CBUSH nominal + prior (INVENTED).** Nominal
  k_trans = 2e6 N/m per axis, k_rot = 2e4 N·m/rad per axis. Rationale: puts
  the chain bounce/rock modes at ~95–130 Hz — inside the input band, inside
  the ROM-validated band (<280 Hz), and inside the 120–185 Hz "joint-active"
  band the predecessor flagged as mount-relevant. Prior: independent LogNormal
  on each of the 6 stiffnesses, median = nominal, sigma_ln = 1.15 (95 % range
  ≈ ×/9.5) — deliberately wide because a payload mount is a JOINT and the
  predecessor showed joints are not identified by modal data. Deterministic
  decade sweep (1e5–1e9 N/m common multiplier) regardless of prior. Mount
  damping: viscous, zeta_mount = 5 % referenced to the nominal bounce mode
  (swept 2–10 %). FLAGGED for sign-off.

- D5 (2026-06-10): Method implementation conventions. (1) TIME-HISTORY
  reference = frequency-domain synthesis (FFT of the input, multiply by the
  exact linear FRF, IFFT) — exact for a linear time-invariant model up to
  circular-convolution end effects, which are handled by zero-padding +
  discarding edge segments; verified against direct Newmark time integration
  of the assembled coupled system (cross-check artifact). (2) MODAL-SRS =
  maximax absolute-acceleration SRS (Smallwood ramp-invariant filter),
  per-axis, modal effective mass × SRS at chain fixed-base frequencies, SRSS
  over modes + residual-rigid-mass term, Q swept {10, 25, 50}. (3) PSD/MILES =
  per-mode Miles from the analytic input PSD, RSS over modes + rigid grms
  term, ×3 ("3-sigma") — labeled ENVELOPE arm; the known ~3.9–4.2σ Gaussian
  peak factor for a 20 s record is documented so the 3σ convention's
  under-prediction of true record peaks is expected, not a surprise.

- D7 (2026-06-10, Andrew mid-run ask via notes/todo.md + notes/project_vision.md
  §2.2): ADD a RESPONSE-LIMIT PROXY QOI — industry does little force limiting;
  response limiting is the practical deliverable. Implementation: from the
  coupled model, rank candidate tray accelerometer locations by correlation
  between (m_tray x accel) and the net-CG interface force F_d(t) (the
  physics-backbone QOI), at/near the force-driving chain modes; pick the top
  1-2 per axis; report the scale factor alpha_cd (N per m/s^2) and correlation
  rho, and its robustness across mount/theta draws -> a scaled response limit
  = F_limit/alpha is the force-limit stand-in. Artifacts:
  out/response_limit_proxy.json + figure + packet section. FLAGGED for
  sign-off: net-CG force remains the primary QOI (per D38); the proxy is a
  derived deliverable, NOT a replacement; per-mount loads stay dropped.

- D8 (2026-06-10): Damping representation UPGRADED to exact physics after
  verify.py V6 exposed a 31 % peak-apparent-mass error from the diagonal
  modal-damping approximation at the near-degenerate 75.9/76.0 Hz chain pair
  (the QOI is peak force at exactly these peaks, so the approximation was not
  acceptable). The mount dashpot is rank-6, so the damped enforced-motion
  solution is computed EXACTLY via a Woodbury identity (models.apparent_mass);
  structural damping stays diagonal-modal by definition (A4). All
  mass-carrying chain modes kept (no truncation; the 5 kHz cutoff left a
  0.7 % quasi-static residue). Transfer matrices evaluated only on in-band
  rfft bins (exact, input is zero outside 20-250 Hz by construction).
  verify.py V6a/V6b thresholds tightened from approximation-tolerances to
  exactness-tolerances; V7 Newmark damping assembly rebuilt to the same
  physics (physical dashpot + structural modal damping on relative motion).

- D9 (2026-06-10, session end): Figures visually QA'd via image review and
  REGENERATED where illegible (method-comparison caption duplication + tick
  crowding; force-limiting switched from one seed's jagged spectra to the
  smooth per-unit-input transfer magnitudes |T_unc|,|T_cpl| — the seed
  spectrum lives in fig_th_sample; apparent-mass split into z+x small
  multiples after the z-axis source proved honestly mass-like, contradicting
  the original "source notches" caption — the notch behavior shows in x;
  identifiability SE bars limited to <=160 Hz). out/image_qa.json records the
  review. check.py OVERALL GREEN (22 green / 0 yellow / 0 red). RESULTS
  HEADLINE (artifact-backed, all labeled hypothetical): QOI is
  MOUNT-DOMINATED (mount prior ~= 100 % of joint QOI variance vs <1 % from
  the calibrated ShockSat posterior); force-limiting over-test factor median
  1.12-1.31 (p97.5 up to 2.2); modal-SRS machinery ~unbiased at informed Q
  (0.95-0.98) with the Q assumption swinging x0.7-2.3; Miles 3-sigma
  under-predicts by the predicted ~25 % peak factor; mount WOULD be
  identifiable from mounted-config interface modes (dlnf/dlnk 0.449 >> 4.6 %
  floor, peak 90 % SE); tray-center accel is a near-perfect response-limit
  proxy in-band (rho ~1.000, alpha ~= m_tray) with the band-specific caveat
  stated. Sign-off items remain D2/D3/D4/D7.

- D10 (2026-06-10 evening, Andrew: "you have the opportunity for an overnight
  run. Go ahead and do whatever makes most sense based on what was found"):
  OVERNIGHT EXPERIMENT = close the loop on findings #1 (QOI mount-dominated)
  and #4 (identifiability gate PREDICTS the mount is recoverable from a
  mounted-config modal test, dlnf/dlnk 0.449 >> 4.6 % floor). Design —
  SYNTHETIC-TRUTH value-of-information experiment:
  (O1) build a differentiable reduced coupled ROM: union basis of full
  coupled modes (<=350 Hz) at mount multipliers {0.05, 0.25, 1, 4, 20}
  spanning the ×/9.5 prior, M-orthonormalized, capped ~160 vectors; stiffness
  is LINEAR in all parameters -> K_red(theta) = B_fix + sum theta_p B_p
  (6 mount axes + 5 tray groups; ShockSat block FIXED at theta_S posterior
  median — see ledger A24); reduction validated vs full eigh at anchors +
  truth point (gate <=0.5 % on modes <=300 Hz).
  (O2) truth + survey data: FULL (unreduced) coupled model at truth params
  drawn ONCE with fixed seeds from the honest priors (mount diag ~ prior;
  tray ~ prior; theta_S_true = a DIFFERENT predecessor-posterior draw than
  the inference uses) PLUS an unmodeled physical feature: 6x6 mount stiffness
  with off-diagonal translation-rotation coupling (rho=0.15 on (tx,ry),
  (ty,rx); 0.05 (tx,ty)) that the (diagonal-CBUSH) inference model CANNOT
  represent -> genuine model-form discrepancy, not just noise. Data = coupled
  modal frequencies <=240 Hz + shapes at ~30 physical accel channels
  (tray channels + 4 ShockSat nodes), frequency noise 0.3 % (predecessor
  replicate floor), one realization. truth params written to truth_lock.json
  (SHA-pinned); the NUTS script reads ONLY survey_data.npz (structural
  self-blinding, documented as imperfect since one agent wrote both).
  Pairing: Hungarian MAC pairing against the best-matching mount-grid anchor
  (the "engineer's coarse pre-match"), calib filter MAC>=0.5, |df|<=12 %.
  (O3) NUTS (pinned .venv_nuts, jax 0.4.30/numpyro 0.15.3, OMP=1, detached,
  resumable): infer 6 mount multipliers (LogNormal(0,1.15)) + 5 tray thetas
  (LogNormal(0,0.25)) + sigma_f (HalfNormal(0.05)); frequency-only
  likelihood (same rationale as predecessor: eigenvector gradients
  ill-conditioned near degeneracies); stop-gradient max-overlap mode
  tracking vs anchor modes; 4 chains x 1000+1000 d8 dense-mass; AUTO-REMEDY:
  if the convergence gate fails, one rerun at 2000+2000 d10 (both kept,
  honestly labeled). Convergence gate applies in full; a non-converged
  result is YELLOW and reported as such.
  (O4) posterior QOI propagation: posterior mount+tray draws x predecessor
  theta_S posterior through the existing QOI pipeline -> AFTER bands vs the
  existing BEFORE (prior-mount) bands; truth QOI from the full truth model
  (off-diagonal mount; apparent_mass_direct generalized to 6x6 K_m);
  value-of-information = interval-width ratios + truth coverage before/after
  + force-limiting-factor tightening + parameter recovery (with the stated
  caveat that the diagonal model's k is an EFFECTIVE stiffness given the
  off-diagonal truth). Scope guard: no multi-mount arm, no shock, no vault
  data — synthetic only, all HYPOTHETICAL/SYNTHETIC labeled.

- D11 (2026-06-11 morning, overnight result): NUTS did NOT converge — base
  worst R-hat 5.03 / min ESS 2 / 0 div; auto-remedy (2000+2000 d9) WORSE at
  9.74 (more modes found with more exploration = more multimodality
  evidence). STATUS = YELLOW; nothing labeled converged/"NUTS active".
  DIAGNOSIS (code/diagnose_multimodality.py -> out/multimodality_diagnosis
  .json): genuine under-identification, not a sampler bug — all 4 chains fit
  the 27 survey frequencies equally well (rms log-residual 3.3-3.5 %,
  cross-chain predicted-frequency spread median 0.06 %) while mount params
  differ wildly; sigma_f posterior ~3.7 % >> injected 0.3 % noise = the
  structured discrepancy measured honestly; FIM at that floor: only 2/6
  mount stiffness COMBINATIONS identifiable (k_ry-rocking eig~97, k_tz
  bounce eig~15) vs 5/6 at the noise-only floor -> BINDING CONSTRAINT IS
  MODEL-FORM DISCREPANCY (cross-confirms predecessor joints finding in a
  controlled synthetic setting). Packet section 7 claim SHARPENED, not
  withdrawn: overall mount level identifiable (2 combos), per-axis 6-DOF
  decomposition NOT, from frequencies alone. VOI numbers (width ratios
  0.93/0.38/0.91; truth missed on Fx before AND after) reported YELLOW with
  the NOT-CONVERGED flag on fig_voi. checker overall now YELLOW
  (27 green / 2 yellow [convergence_mount_nuts, voi_truth_coverage] / 0 red)
  — the yellows are the documented honest findings. Refined pre-test lever:
  symmetry-breaking observables (mode shapes / FRF amplitudes / interface
  force gauges) or discrepancy reduction; more frequencies alone will not
  split the mount axes.

- D12 (2026-06-11, Andrew APPROVED "I agree, make the change"): DURABLE
  AGENTS.md edit — extended the Modal/Eigenproblem Identifiability Gate with a
  bullet requiring, for any PER-PARAMETER identifiability claim, the FIM
  eigen-decomposition at the REALIZED discrepancy floor (how many parameter
  COMBINATIONS clear the prior precision + which raw params they mix), in
  addition to the strain-energy table; and noting that a sampler going
  multimodal in parameter space while agreeing in data space is the SAME
  under-identification finding (not a bug). Motivated by D11: the SE gate said
  the mount is identifiable in aggregate, but only the FIM-combination view
  exposed that only 2/6 axes separate at the 3.7% floor. Logged + folded into
  this workspace's narrative.

- D13 (2026-06-11, Andrew: "keep running until you can provide a meaningful
  slide deck ... for Dr. Bilionis and Girolami and Yunis (ShockSat creator).
  Use figures and gifs ... and the tufte skill. Categorize findings 1 (utter
  failure) to 5 (smashing success)"): build a shareable program-level deck.
  Audiences: Bilionis (SciML/UQ/BOED), Girolami (StatFEM author), Yunis
  (ShockSat hardware). Deliverables: slides/shocksat_program_deck.pptx +
  PNG figures (tufte-linted) + supplementary GIFs (animations, NOT embedded in
  pptx). Findings scored 1-5 with explicit honest criteria. No new physics
  claims beyond the artifact-backed results; the overnight honest-negative is
  presented AS a finding, not hidden.

- D14 (2026-06-12, Andrew deck-review questions): (a) Slide 7 lacked context →
  rebuilt the force-limiting deck figure as a 2-panel small-multiple (lateral x
  vs vertical z) with notch@fixed-base / peak@coupled-resonance annotations, and
  rewrote slide 7 to state the excitation (flat random PSD run through the
  transfer), why z is SDOF-like (only the 116 Hz bounce carries z; effective
  mass = full tray), why the peak shifts right (notch at load fixed-base, peak
  at coupled resonance), and why the z notch is small (source≫load apparent
  mass in z: ~103 vs 33 kg) vs lateral deep ×3.5 (21 vs 55 kg, comparable).
  (b) Slide 9 ">100% variance": added code/variance_ci.py → bootstrap 95% CIs
  into variance_decomposition.json; the figure now carries CI whiskers + a
  footnote (OAT main-effect ratio, NOT a Sobol index, so a dominant group can
  read >1; Fx/Fy mount = 1.02/1.05 with CI [0.6,1.6] = statistically 100% =
  MC noise). Packet variance section updated. (c) "Which mount?" → it is THE
  single 6-DOF CBUSH at point P (gid 7000072, top-plate centre) joining the
  ShockSat FEM to the tray FEM (the tray's 6 feet condensed to that one point);
  the tray's internal joints are separate. Built code/make_coupled_image.py →
  to-scale (metres, equal-aspect) coupled-FEM image (fig_coupled_assembly.png)
  + new deck slide 7/15. Deck now 15 slides; check.py gates updated.

- D15 (2026-06-12, Andrew slide-11 questions): (a) SENSORS — the synthetic
  survey has 33 channels, 21 ON the tray (center/corner/midedge/3 apexes/base
  point x 3 axes) + 4 ShockSat nodes; but shapes were used for PAIRING only,
  the likelihood is FREQUENCY-only (eigenvalues are sensor-location-blind) —
  that IS the mechanism of the x/y non-separability; slide 11 updated to say
  so. (b) "Response to real modal data" — none exists for the coupled system;
  real test data enters only through Y_S (theta_S posterior + measured modal
  damping), which carries <1 % of QOI variance; survey data is synthetic and
  labeled. (c) POOLING (Andrew: "6 down to 3 without much trouble") — ran
  pooled FIM (code/pooled_fim.py -> out/pooled_fim.json) at the realized
  3.7 % floor: 6->4 still 2/4; best 6->3 (t_all, r_lat, r_z) = 2/3 with the
  third eigenvalue 0.74 vs prior precision 0.76 (AT the boundary, marginal);
  6->2 (t_all, r_all) FULLY separable (eig 14, 100). At the 0.3 % noise-only
  floor all of Andrew's 3 would separate — the discrepancy floor eats the
  third axis. Sampler confirmation launched (code/run_nuts_pooled.py, tags
  p2 + p3b, pinned venv, detached): FIM predicts p2 converges cleanly, p3b
  borderline. Pooled truth refs are EFFECTIVE geometric means (truth is
  asymmetric + off-diagonal -> pooling adds deliberate model-form error
  absorbed by sigma_f; documented in the script header).

- D16 (2026-06-12, pooled sampler results): NUTS ladder confirms the FIM
  ordering (6-param R-hat 5.03 -> p3b 1.52 -> p2 1.24; 0 div everywhere) but
  even p2 (t_all, r_all) MISSES the gate at 4x(1000+1000) d8. Diagnosis
  (code/pooled_diagnosis.py -> out/pooled_diagnosis.json): (a) STIFF-SIDE
  SATURATION - above ~5x nominal the mount is rigid relative to the tray,
  frequencies pin (f1 -> 84.8 Hz) and the likelihood flattens -> t_all upper
  tail prior-dominated (samples 0.05-39); one-sided identifiability; (b)
  t_all <-> r_all ridge (corr(log) -0.74) from CG-offset rocking pricing a
  combination of the two; (c) mount<->tray correlations weak (<=0.17) - my
  initial confounding hypothesis was WRONG, corrected by measurement; (d) the
  prior-whitened JOINT local FIM at nominal says p2 is fine -> local-vs-
  global lesson, reinforcing the D12 gate's profile/posterior companion
  requirement. Remedy run launched (p2r, 4x(2000+2000) d9) to separate slow
  ridge-mixing from true multimodality. Packet section 10a + slide 11
  updated; pooled artifacts gated in check.py.

- D17 (2026-06-12, p2 remedy verdict): 4x(2000+2000) d9 made R-hat WORSE
  (1.24 -> 2.22, min ESS 3, 0 div) — chain1 lived entirely in the saturated
  stiff tail (t_all 2.6-38.8) where the likelihood is flat; chains 0/2/3 near
  x1. Settles slow-mixing vs structure: t_all non-identifiability is
  STRUCTURAL and ONE-SIDED (lower bound ~x0.4 only; no upper bound possible
  from frequencies). r_all IS pinned across chains (~0.9-1.07). Caveat noted:
  a stiffness lower bound does not bound the load (QOI non-monotonic in k).
  Packet 10a finalized; pooled_diagnosis.json carries p2r; checker yellow
  note updated. Third instance of the program's compute-escalation lesson
  (more draws on a flat/multimodal posterior explore more, never converge).

- D6 (2026-06-10): Quantity contract written BEFORE any number/plot (gate).
  Conventions judged unambiguous after re-reading
  `docs/lab/apparent-mass-convention-postmortem.md` + NASA-HDBK-7004C notes
  (source vs load apparent mass pinned; our source is FREE-FREE ShockSat, so
  its apparent mass tends to the rigid mass line at low frequency instead of
  the grounded-source ∞ growth in the 7004C Fig 9 cartoon — stated in the
  contract). The three INVENTED values (D2 input, D3 placement, D4 mount) are
  prominently flagged for Andrew's sign-off in the chat summary and packet;
  work proceeds because the pipeline is parametric and a value change is a
  cheap rerun, while the contract/conventions themselves are not ambiguous.
