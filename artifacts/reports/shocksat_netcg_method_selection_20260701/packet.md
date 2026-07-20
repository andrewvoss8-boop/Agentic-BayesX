# Human-review packet — ShockSat net-CG FORCE method selection

Run: `artifacts/reports/shocksat_netcg_method_selection_20260701/` · replay `bash run_all.sh` · checker `python3 check.py`
Audience: aerospace loads/dynamics (advanced) + Bayesian updating (plain-English on the stats). NUTS = No-U-Turn
Sampler (a gradient-based MCMC that draws from the posterior); R-hat = between/within-chain agreement (want <=1.05);
ESS = effective sample size (want >=200). "Twin" = the updated FEM + its calibrated uncertainty band.

## 1. Method summary (read this first)
- **Decision.** Pick, PER QOI (net-CG SHEAR X/Y, net-CG NORMAL Z on the top tray), the ONE updating method whose
  net-CG force band we can hand a partner: it must COVER (hard gate) and, among covering methods, be SHARPEST —
  and it must NOT falsely sharpen the unmeasured-mode-driven normal QOI (overconfidence disqualifies).
- **Model form.** Reduced FEM `K(theta) = A_fix + sum_g theta_g A_g` (9 stiffness-group multipliers theta, mass
  = I, 74-dim). Modes (eigenvalues/vectors) from `K(theta)`; net-CG force PSD
  `S_F(w) = |sum_i g_i(theta) * w^2 / D_i(w)|^2 * S_input`, `g_i` = uniform-mass tray-region (z>=55 in) modal
  participation on the QOI axis, `D_i = w_i^2 - w^2 + 2i*zeta*w_i*w`.
- **Likelihood (data-usage choice — stated explicitly).** MODAL peak-FREQUENCY feature likelihood (Kiran Eq 25):
  `ln p = -0.5 * sum_r [ (w_hat_r^2 - w_r^2(theta))^2 / sig^2 + log(2*pi*sig^2) ]`, matching FEM eigenvalues to
  MEASURED modal frequencies (extracted from the 5-drive modal-hammer FRFs). This is a FEATURE likelihood (peaks),
  NOT a whole-FRF-magnitude likelihood — chosen because whole-|H| is non-identifiable on this data (R-hat 104,
  prior threads) while the modal-frequency feature converges cleanly.
- **Data counts.** 5 drives (+X/+Z/+XY/+Z@900/+Y). 111 accel channels (4 bad excluded). .ash modal survey 33
  modes x 76 nodes x 3 axes; 20 of 40 in-band FEM modes MAC-matched. Multi-hit averaged per drive (4-6 hits).
  Single build; no flight-to-flight variability modeled.
- **Inferred (NUTS):** theta (9 stiffness groups) + sig (modal-freq error). **Fixed/assumed:** input PSD (flat),
  zeta=1%, tray mass proxy, mode-match MAC, the unmeasured-mode sigma. **Non-inferred latent (the crux):** the
  drumhead mode SHAPES 234-254 Hz — UNMEASURED (perimeter sensors miss the plate center) — carried as an
  amplitude discrepancy tier, NOT resolved by theta.
- **The three methods compared (per QOI):** `baseline_fem`/`FEM+6dB` (incumbent bar); `L5_theta_only` (propagate
  only the theta posterior, nominal amplitudes = SHARP but blind to shape ignorance); `L5_freq_discrep` (theta
  posterior + per-mode tier discrepancy: measured modes tight amp, unmeasured modes wide amp).

## 2. Headline result (best of N=18 configs; 5 formulations; checker-backed)
L5 modal-frequency NUTS CONVERGED (R-hat 1.001, ESS 2646, 0 divergences, 4 chains). **All four
discrepancy-carrying methods COVER + are HUMBLE; only the frequency-only `theta_only` falsely sharpens →
disqualified.** Among covering+humble methods the sharpest wins → **`statFEM F(k)`** (QOI-aware
frequency-correlated output discrepancy):

| QOI | FEM+6dB (incumbent) | L5_theta_only | **statFEM F(k) (WINNER)** | held-out-DRIVE |
|-----|---------------------|---------------|----------------------------|-----------------|
| shear_X | 1.0x, cov 0.86 (leaks) | 1.07x, **overconfident** | **1.51x, cov 0.99, covers+humble** | **5/5 drives cov 1.00** |
| shear_Y | 1.0x, cov 0.71 (leaks) | 1.22x, **overconfident** | **2.30x, cov 0.98, covers+humble** | **4/5** (+Z@900 gap 0.60) |
| normal_Z | 1.0x, cov 0.74 (leaks) | 1.02x, **overconfident** | **2.53x, cov 0.99, covers+humble** | no data answer key |

`cov` = 1-octave-smoothed weighted coverage of the honest epistemic-truth ensemble; `band ratio` = 95%-band
GRMS-force vs the FEM+6dB envelope. The **incumbent FEM+6dB is tight but UNDER-covers** (0.71-0.86 — it leaks).
`L5_theta_only` passes lenient smoothed coverage BUT the **leave-modes-out test catches its overconfidence**: when
measured modes are hidden its band does **not change (widen ratio = 1.00 exactly** — structurally blind to what it
knows), while every discrepancy method **widens (1.06-1.80)**. The four discrepancy methods agreeing = the
conclusion is robust, not a single-method artifact.

**Held-out-DRIVE validation (real data).** The selected `statFEM F(k)` shear band was checked against each drive's
net-CG force reconstructed from that drive's MEASURED FRFs (independent of the twin's tier model): **shear_X
covered on 5/5** held-out drives; **shear_Y on 4/5**, with one **genuine under-coverage** on the +Z(900) end-drive
(a real cross-axis model-form gap, not a low-signal artifact — surfaced, not hidden).

**RQ3 (pooling).** Hierarchical pooling reaches a tighter normal band (2.00x) but only via an **unverifiable
shared-amplitude-scale assumption over the UNMEASURED drumhead modes** → we deliver the conservative statFEM F(k)
(2.53x) and flag pooling; pooling the normal number needs the >200 Hz test to be justified.

**The one-line answer.** For the inherited ShockSat FEM + modal test, method **statFEM F(k)** gives a
held-out-DRIVE-validated net-CG SHEAR force band (1.51x/2.30x the FEM+6dB envelope; 5/5 drives on X, 4/5 on Y with
one real end-drive gap) and an HONEST wide-but-covering net-CG NORMAL force band (2.53x, driven by UNMEASURED
drumhead modes) that we PROVED (leave-modes-out, robustly across 4 formulations) does not falsely sharpen — and
closing the normal band needs a **>200 Hz top-plate/drumhead modal test**. The frequency-only method that WOULD
falsely sharpen is caught and disqualified.

## 3. Stage-0 QOI trust map (no NUTS) — `figures/fig_stage0_qoi_trust.png`
- SHAPE-trust (share of the net-CG QOI carried by .ash-shape-measured modes): shear_X 96%, shear_Y 94%,
  **normal_Z 45%** (drumhead shape unresolved), mount_response(point) 13% (reproduces the known ~14.6x wall).
- **+Y (Test03/990y) distilled** to the canonical N=122880 cache (4 hits, coherence 0.85). Its value is honest
  and modest: it adds FREQUENCY observability at 151.9/152.2/**230.6** Hz (230.6 = a drumhead-band mode no other
  drive saw), tightening the normal band 6.6x->5.7x — but it does NOT resolve the drumhead SHAPE.
- **Sensitivity (load-bearing assumption).** The normal band factor is set almost entirely by the assumed
  unmeasured-mode AMPLITUDE sigma (SD_A_U): 0.40->2.6x, 0.80->5.7x, 1.60->34x (frequency sigma barely matters).
  So the normal width is an ASSUMPTION-dominated quantity; the >200 Hz plate test would REPLACE it with data.

## 4. Axis-B mesh screen (imperfect proxy; does NOT select the twin)
Blind shear-band-weighted matched-mode frequency-RMS + MAC (no amplitude fit -> avoids the in-sample §1.1
artifact). Preliminary (run in progress / see `out/mesh_screen_summary.json`): the **inherited mesh scores best**
(screen +0.44 vs edits <=+0.40) — consistent with the standing finding that box/joint remesh has ~no QOI leverage
(the shear modes are already matched; the drumhead modes are untouched by box edits). Carrying each mesh THROUGH
NUTS needs per-mesh reduced blocks (not cheaply available); the bake-off therefore runs on the inherited reduced
model — a documented deferral, low-risk because remesh does not move the QOI.

## 5. Honest limits (YELLOW / caveats — do not read past these)
- **normal_Z NUMBER is data-starved** (shape-trust 45%; drumhead shape unmeasured). Delivered as a COVERING band
  + trust label, NOT a sharp certified number. The leave-modes-out test validates the MACHINERY (on the shear band
  where measured modes exist) and predicts the wide normal band is honest — it is NOT a validation of the normal
  number itself (its real drumhead truth is unmeasurable without new data).
- **1-octave-smoothed coverage is LENIENT**: frequency jitter fills the octave, so smoothed coverage alone does
  not catch false sharpening — the leave-modes-out WIDENING test is what does. Reported honestly.
- **Mass model** = uniform-mass proxy over the tray region (consistent-mass = a refinement, not the headline).
- **Delivery band 20-2000 Hz (prompt) vs data band 45-260 Hz**: outside 45-260 Hz the twin is prior-only (no
  data). All results are within 45-260 Hz.
- **Bake-off breadth is N=18 (5 formulations: theta-only, freq+discrep, feature_space, statFEM F(k), hier_pooled;
  best of N per QOI).** `beck_shapefield`, `pooled_fullFRF`, and the mesh-through-NUTS axis remain documented
  deferrals (decisions_log D7/D8/D14), not hidden. Winner read as "best of N". The conclusion is robust across the
  4 discrepancy formulations, which reduces (does not eliminate) winner's-curse.
- **1-octave coverage is lenient on POOLING**: hier_pooled's tighter normal band (2.00x) uses a per-mode sigma
  (0.60) narrower than the truth's (0.80); smoothed coverage does not penalize it. We therefore deliver the
  conservative statFEM F(k) (2.53x) for normal and only offer pooling with its assumption flagged.
- **Held-out-drive caught a real shear_Y gap** on the +Z(900) end-drive (cov 0.60): the twin under-predicts the
  net-CG Y-shear peak for a Z-drive at the y~0 end (a cross-axis model-form path). Surfaced; the shear_Y delivery
  carries this caveat.

## 6. References & standards (Reference Gate)
- **NASA-HDBK-7004C** apparent-mass / net-CG force convention: our QOI = interface base reaction = net-CG force =
  mass-weighted acceleration integral (the 7004C apparent-mass convention); band-ratio deliverable is
  input-level-independent. Aligned. Named the two nearby conventions (net FORCE vs net-CG ACCEL/GRMS) in
  `quantity_contracts.md`; we use net FORCE.
- **Kiran Eq 25** (modal eigenvalue likelihood) is the well-posed FE-updating choice used here.
- ShockSat vendor correlation (NASA slides): FEM delivered "correlated" on frequencies + global shapes to ~135 Hz;
  our high shear trust (measured global modes) and low normal trust (unmeasured drumhead >200 Hz) are consistent
  with the vendor's own "shapes >135-200 Hz not great / weld the biggest unknown" caveats.

## 7. Gate coverage
| gate | where | status |
|------|-------|--------|
| Priority deliverables | priority_deliverables.md | P3/P4 DONE; P5 running; P1/P2/P6/P7 delivered (scoped, best-of-N) |
| Question & decision | question_framing.md | done |
| Quantity contract | quantity_contracts.md | done (numerator/denominator/units/limits/2 conventions) |
| Assumptions & uncertainty | assumptions_ledger.md | done (values/units/type/sensitivity; data counts; inferred/fixed/latent) |
| Modal identifiability | stage0_qoi_weights.json (participation) + trust | strain-energy-style participation per QOI + measured/unmeasured split |
| Reference & standards | §6 above | 7004C + Kiran + vendor checked |
| Plot & human-review | fig_stage0 / fig_delivery / fig_graphical_model (Tufte-linted) | done; legibility QA'd |
| Sensitivity | stage0_sensitivity.json + §3 | done (unmeasured-mode sigma = load-bearing) |
| Discretization | freq grid 45-260 Hz, 400 pts; 1-octave smoothing documented | QOI peaks resolved (shear 147/122, normal 252) |
| Verification | check.py (SHA-locked) | GREEN/YELLOW/RED per checker |
| Runtime accounting | runtime.json | active ~191s + detached mesh screen |
| Convergence (NUTS) | bakeoff_scorecard.json | CONVERGED R-hat 1.001 / ESS 2646 / 0 div |

## 7b. Dive-deeper follow-ons (DD1/DD2/DD3) — a coherent, humbling synthesis
- **DD1 (the one caught gap is NOT systematic).** The +Z(900) shear_Y held-out-drive gap localizes to a low
  ~73 Hz mode whose fitted scale for +Z(900) is a ~5x outlier vs the other four drives → a **drive-specific
  reconstruction artifact** (that end-Z drive barely excites the mode), not a systematic FEM error. The shear_Y
  deliverable is reliable across the well-behaved drives. (`out/diag_shearY_gap.json`, `figures/fig_shearY_gap.png`)
- **DD2 + DD3 (two independent routes agree the shear discrepancy is ~0.9, not ~0.3).** DD3 estimates the
  measured-mode amplitude uncertainty from the 5-drive cross-scatter of each mode's fitted participation: robust
  median **0.86** (log-amp), ≫ the assumed 0.35. DD2 puts the statFEM output discrepancy IN the likelihood and
  **infers it with NUTS (converged R-hat 1.001, ESS 2083, 0 div)**: learned marginal σ_d = **0.94** (CI 0.82–1.07),
  agreeing with DD3. (`out/data_anchored_sigma.json`, `out/learned_statfem.json`, `figures/fig_data_sigma.png`,
  `figures/fig_learned_statfem.png`)
- **What this means for the deliverable (precise honesty).** The learned discrepancy is nearly POINT-WISE
  (correlation length 0.10 octaves), so it **averages out under 1-octave smoothing** — which is exactly why the
  held-out-drive coverage (DD #1) PASSED on the smoothed metric. So: **the delivered shear band is trustworthy at
  the 1-octave-smoothed level (held-out-drive validated), but the point-frequency shear amplitude is uncertain to
  ~0.9 log-amp** — do NOT read the smoothed band as point-wise sharp. Data-anchoring widens the *unsmoothed* shear
  bands (shear_X 4.5→6.4×, shear_Y 4.4→12.7×). This quantifies the project's standing "per-node/point FRF
  amplitude fidelity is the binding wall" via two new independent routes.
- **RQ3 pooling, revisited with data.** DD3's pooling ICC = 0.31 (drive scatter dominates) → a shared amplitude
  scale (pooling) IS reasonable for the *measured* modes; the *unmeasured* drumhead modes remain unverifiable
  (only the >200 Hz test resolves them).

## 8. Overall status
Per checker: **OVERALL GREEN 22/0/0** — but read this precisely. The checker certifies pipeline INTEGRITY,
NUTS CONVERGENCE (R-hat 1.001), and that every substantive caveat is HONESTLY FLAGGED (not that the normal number
is certified). Three caveats the reader MUST carry with the deliverable (documented, non-blocking):
1. **normal-QOI NUMBER is data-starved** (drumhead shape unmeasured) → delivered as a covering band + trust
   label, not a certified number; the >200 Hz plate test (§9) buys it from 5.4x down toward a 2.8x floor.
2. **shear_Y has one caught held-out-drive gap** (+Z@900 end-drive, cov 0.60) → shear_Y carries that caveat.
3. **pooling's normal-sharpening (2.00x) is unverifiable** → we deliver the conservative statFEM F(k) (2.53x).
A wide-but-covering, non-overconfident, honestly-caveated band is a SUCCESS of the method under the binding
requirement, not a failure to hide.

## 9. Pre-test design — the >200 Hz plate test (the next test dollar) — `out/pretest_design.json`, `figures/fig_pretest.png`
The single load-bearing assumption (Stage-0) is the unmeasured-mode amplitude sigma that sets the normal band.
The test that replaces it with data: the net-CG NORMAL force is driven by the partial-cancellation drumhead modes
**246/249/254/258 Hz** (net tray-Z participation; NOT the pure 234/252 Hz modes, which cancel in the net). Their
shapes are unmeasured — the current plate has **1 Z-sensor**, off the antinode. **Recommendation:** a deck plate
array (center+rings, >=12 Z accelerometers) driven by a **+Y** deck hit (covers the most drumhead peaks incl the
unique 230.6 Hz; +Z(990)/+XY tie next). **Buy-down:** 12 well-placed plate accels cut the normal band factor
**5.4x → 3.5x (~35%, 73% of the way to the fully-resolved 2.8x floor)**. Honest bounds: even fully resolved the
normal floor is 2.8x (never as tight as shear 1.5x — the drumhead net force is intrinsically less certain); the
246-258 Hz modes have fine spatial structure (worst-mode captured 0.39 at 12 sensors → a denser array helps) and
are not individually separable by point sensors (you measure their net combination = the QOI, which suffices).

## 10. ERRATUM / ADDENDUM (2026-07-02) — §9's 3.5x buy-down is SUPERSEDED
The §9 pre-test buy-down (12 plate accels -> normal band 5.4x->3.5x) was an ANALYTIC curve computed
with theta FROZEN at MAP and lognormal amplitude tiers — i.e., outside the twin's own uncertainty
carriage. A pre-registered, SHA-locked-checker rehearsal (`artifacts/reports/plate_test_rehearsal_20260701/`,
checker OVERALL RED = claim-falsified tier) ran the designed test end-to-end through the ACTUAL joint
NUTS pipeline on synthetic truth: **the buy-down does not survive — 12 sensors deliver 6.20x vs 6.17x
at 1 sensor (20 sensors: 6.20x).** Mechanism: the +/-4% theta posterior rotates the near-degenerate
246-258 Hz drumhead eigenvectors, scattering every band mode's net-Z participation (analytic floor
3.05x -> 4.93x from theta alone; signed-mixture amplitude tails -> ~5.5x). A perfect 4-target test
still leaves ~5.1x. **Revised scope: resolving ALL ~12 drumhead-band modes (228-260 Hz) recovers a
2.81x ORACLE bound — a harder identification job requiring re-optimized sensors/drives and a 12-mode
inference follow-up rehearsal before any number is promised.** What the as-designed test still buys:
per-target amplitude posterior sd 0.80->0.58 (mean within 0.08 of truth), making §2's pooling
assumption (RQ3) checkable. Do NOT quote 3.5x (or 2.8x) to a partner. §9's sensor-placement logic
and drive recommendation remain useful inputs to the revised design; its band-factor curve does not.
