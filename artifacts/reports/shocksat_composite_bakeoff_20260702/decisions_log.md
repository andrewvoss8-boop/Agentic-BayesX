# decisions_log — shocksat_composite_bakeoff_20260702
(every non-obvious choice, written BEFORE continuing; task card = docs/lab/composite_remodel_beck_runner_prompt.md)

- **D1 (2026-07-02, setup) — Measured-frequency set for the likelihoods.** The proven theta_post_L5.npz
  (netcg) was fit on the L5 consensus peak set from the +X single-impact FRF (modal_feature.extract_measured_modes)
  — that is what "baseline A (proven)" means, so M0S0 REUSES that posterior unchanged. S1/S2 arms and all
  M1 tier-3 NUTS runs use the SAME matched-mode machinery with the FULL in-band matched set (never pruned),
  with .ash survey shapes as the shape-truth source (multi-reference retest per card §2). Rationale: keeps
  baseline A exactly the proven artifact; adds shape info through the pre-registered axes only.
- **D2 (2026-07-02, setup) — Metric-trap #1 vs the held-out answer key.** The leave-one-drive-out answer key
  necessarily LSQ-fits per-mode participation FROM THE HELD-OUT drive's measured FRFs (heldout_drive.py
  machinery). That is reconstruction of the truth from data, NOT a fit of the candidate model to data, and is
  identical for every arm — so it cannot advantage any arm. Pre-registered: LSQ appears ONLY in answer-key
  construction; any per-mode amplitude/phase fit inside an arm's own score or the screen/evidence scores = RED.
  Global gain: ONE scalar per (arm, fold), fit on observed channels only.
- **D3 (2026-07-02, setup) — Card's Beck bar provenance.** Card cites "CRPS −0.68→−0.25". Single-seed
  modal_beck_ash.json shows −1.17→−0.40 (seed 2); the card numbers are the 3-seed MEAN in
  shapefield_lever.json (fem −0.68, inferred −0.25). Pinned the 3-seed mean as the pre-registered bar and
  recorded both in question_framing.md.
- **D4 (2026-07-02, setup) — Tier-1 screen design.** Cheap screen = Rayleigh-Ritz on the nominal 80-mode
  basis: per candidate assemble sparse ΔK (and ΔM) with the remodel.py machinery, project to 80x80
  (Ṽ=V_keep), solve the small generalized eigenproblem, pair to .ash by one-to-one assignment, score
  freq-RMS + MAC over the FULL matched in-band set. Documented as an imperfect proxy (assumptions A11):
  it cannot create modes outside the nominal span — hedge = top ~30 go to FULL eigensolves (tier 2).
  This choice follows the card's approved compute default.
- **D5 (2026-07-02, setup) — Workspace + reuse discipline.** New workspace only; all source workspaces
  imported read-only (sys.path imports, never edited). REUSED_code.sha256 records the hashes of every
  imported source file at lock time, so any later drift in the sources is detectable.

- **D6 (2026-07-02, tier-2 selection) — Family-diversity hedge.** Tier-2 = top 27 by tier-1 screen score +
  the best of any allowed family not already represented (cap 30 M1 + the M0 baseline through the SAME full
  path). Rationale: the tier-1 proxy (A11) is blind to modes outside the nominal span, which biases against
  exactly the connectivity/joint candidates that create new local physics; one-per-family insurance keeps the
  funnel honest at negligible cost. Pre-registered before tier-2 ran.
- **D7 (2026-07-02, tier-2) — M0 through the identical path.** The M0 baseline package (candidate id
  'baseline') is re-solved through the same tier-2 code so every downstream arm (M0 and M1) uses identical
  conventions (basis, pairing, selectors). The netcg theta_post_L5.npz is still reused for the S0 posterior
  (D1); the netcg QOIModel numbers remain the pinned bars.
- **D8 (2026-07-02, matrix design; AMENDS D1) — One frequency-data source for all six arms.** D1 would have
  left M0S0 on the +X consensus-peak frequencies while S1/S2 use .ash survey modes — that confounds the S-axis
  (frequency set AND shape term would change together). Amended: ALL six arms are calibrated on the SAME
  observations = the .ash survey matched-mode frequencies (frozen Hungarian pairing per model, full in-band
  set); S1 adds the MAC block on the same pairs; S2 = Beck free-shape field on the same pairs. The proven
  theta_post_L5.npz (+X peaks) stays as the pinned EXTERNAL reference bar, clearly labeled, not an arm.
  Bonus: the .ash survey is a separate EMA campaign, so ALL five tap-test drives are genuinely held out for
  every arm (clean leave-one-drive-out).
- **D9 (2026-07-02, R1 design) — Non-leaky sigma for R1.** The historical Beck numbers computed sigma_QOI from
  HELD-OUT residuals (modal_beck_ash predict()); that is leaky for interval width. This run computes the
  QOI-level discrepancy sigma from OBSERVED-channel residuals only (non-leaky) for every arm. Consequence:
  R1 absolute levels are not strictly comparable to the historical bar (-0.68 -> -0.25), which remains
  directional context; the DECISIVE R1 contrast is between arms inside this run (identical convention).
- **D10 (2026-07-02, compute incident) — Tier-2 launch hardening.** Two failed launch modes: (i) `nohup … &`
  inside a foreground tool command that then hit the tool timeout -> SIGTERM to the process group killed the
  child; (ii) the tool's background-task wrapper was stopped and the child died ~6 min later mid-eigensolve
  (no traceback). Fix: double-fork `nohup bash -c 'exec python3 …' & disown` from a fast-returning command
  (child reparents to launchd, immune to tool signals) + a separate polling monitor for completion
  notification. Tier-2 is resumable, so no work was lost (3/29 preserved). No science impact.
- **D11 (2026-07-02, NUTS incident — S1 eigenvector-gradient pathology; A7 risk realized).** M0S1 attempt-1
  (freq+MAC via jnp.linalg.eigh differentiating EIGENVECTORS) took ~45 min and landed R-hat 1.086 (near-miss);
  the uniform retune (warmup2000/ta0.95/tree10) then ran ~2 h with NO progress = the documented degenerate
  246-258 Hz drumhead eigenvector-gradient blow-up (dphi/dtheta ~ 1/(lambda_i - lambda_j)). Killed both the
  hung run and the orchestrator. FIX (card §5 "freeze bases / use subspace-projected forms and DOCUMENT";
  AGENTS Sampler Decision "document the smoothing/relaxation used"): S1 now uses (i) eigvalsh (eigenVALUES only,
  stable at degeneracy) for the frequency term, and (ii) a REGULARIZED FIRST-ORDER shape derivative for the MAC
  term — phi_k(theta) = phi0_k + Phi0 @ [reg_jk * <phi0_j, dK phi0_k>], reg_jk = D0/(D0^2 + delta^2),
  D0 = lam0_k - lam0_j from the FROZEN theta=1 basis, delta = 0.5*median modal gap (=1.6e4 (rad/s)^2). The
  Tikhonov floor delta CAPS the near-degenerate denominators so the gradient is bounded, while keeping a REAL
  theta-gradient from the well-separated modes (so S1 still genuinely tests MAC-as-theta, not collapsed to S0).
  Smoke: S1 now 25s, R-hat 1.0008, ESS 581, 0 div, sigma_mac 0.42. S2 (Beck) already avoids eigh (free shapes +
  Rayleigh) so it was never affected. No science pre-judged; the fix is a documented sampler-stability change,
  not a result change. M0S0 (converged, cached) reused; arms stage resumes.
