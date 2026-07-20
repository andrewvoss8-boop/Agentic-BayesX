# Packet — Multi-point / 6-DOF behavior vs the NASA-HDBK-7004C toolbox

Workspace: `artifacts/reports/notch_multipoint_7004c_20260611/` — 2026-06-11,
lead-as-runner (Claude Code lead agent; design judgment delegated by Andrew).
Replay: `bash run_all.sh` (regenerates results, 13 figures, 3 GIFs, the PPTX,
and runs `check.py`). Status: see `checker_report.json` (green/yellow/red per
AGENTS.md; expected overall = YELLOW with two documented, non-fatal yellows).

## 0. Method summary (read this first)

- **No sampler, no Bayes, no measured data.** Everything is deterministic
  frequency-domain linear structural dynamics on small exact matrices
  (decisions_log D1). "Flight" anywhere in EX-D means a **labeled hypothetical
  coupled simulation**. Data count: zero datasets; no test-to-test/flight-to-
  flight variability anywhere; nothing is inferred.
- **Models** (all values in `assumptions_ledger.md`, conventions in
  `quantity_contracts.md`): (A) the handbook's own nondimensional TDOF pair
  (M1=M2=K1=K2=1, Q=50); (B) rigid 6-kg box, inertia from a 0.30×0.24×0.20 m
  uniform box, CG 0.08 m above the foot plane, 4 feet at (±0.09, ±0.07) m,
  foot springs kz=8.52e5, kxy=6.0e5 N/m, hysteretic η=0.04; (C/D) the same box
  on a simply supported 1.0×0.8×0.005 m aluminum plate (analytic modes, modal
  ζ=0.02 i.e. Q=25; variants t=3.5/8 mm and ζ=0.08 i.e. Q≈6), feet transmit
  vertical force only (stated limitation), point-force excitation at
  (0.18, 0.62) m; EX-D adds a 0.03 m CG plan offset.
- **Whole-curve quantities** are computed and compared (no peak-only
  shortcuts); notch detection runs on the loaded/bare **ratio** in matched
  interface combination channels (D8).
- **Verification spine:** 10 numeric anchors from the 7004C PDF text layer;
  impedance method ≡ direct coupled solve (1e-14); closed-form vs numeric
  modes (2e-16); static limit = rigid mass matrix; effective-mass sums (p.56);
  Newton's-law checks (4e-15); 2× modal-truncation refinement.

## 1. Question (from `question_framing.md`)

1. How do the 7004C 2-DOF intuitions change with multiple, geometrically
   spaced mounting points and 6-DOF motion (rocking possible)?
2. How far from a mounting foot can you still see the effect of the notch?
3. First principles, or build/probe a compliant-backing + payload model?

## 2. EX-A — the handbook replicated (the trust anchor)

`code/ex_a_tdof_baseline.py` → `results/ex_a_results.json`,
fig_a1/fig_a2/fig_a3, gif_a.

- All 10 anchors reproduce within **0.86%** worst-case — and that worst case is
  the handbook's own rounding (its "2.64" = 1.62²; the exact lower-coupled-
  frequency value is the golden-ratio 2.618). Most anchors match to 4 digits:
  A(0.62)=51.764 vs 51.76, F(0.62)=84.076 vs 84.08, notch A(1.0)=0.0200.
- The impedance method (Eq 3/4) equals the direct coupled solve to ~1e-14 —
  the notch at r=1 is the source-impedance minimum meeting the load-impedance
  peak (the absorber mechanism, animated in gif_a).
- Scalar force limiting works as advertised here: hard-mount unlimited force
  with the enveloped spec input ≈ 2928 (handbook quotes ~2500 on its coarser
  grid) vs flight peak 84; the semi-empirical limit with C²=2.62 brings the
  test peak to ≈1.00× the flight peak. Notch depth vs spec: ~69 dB.
- Note found while replicating: the handbook's Fig 9 values are read on its
  r-grid (0.62/1.00/1.62); the true damped peak at the exact coupled frequency
  0.618 is ~58.5, higher than the quoted 51.76 — their grid is coarser than
  the resonance width. Harmless for the handbook's purpose; a good reminder of
  the discretization gate.

## 3. EX-B — what 6-DOF/multi-foot adds (closed-form verified)

`code/ex_b_sixdof.py` → `results/ex_b_results.json`, fig_b1/b2/b3, gif_b.

- The scalar load apparent mass becomes a **6×6 matrix** (quantity contract
  Q4). Verified: ω→0 limit = the exact rigid-body mass matrix about the
  interface point (rel err 5e-7 at 0.05 Hz); 6 numeric modes = closed-form
  eigenvalues to 2e-16 (modes 61.9, 70.6, 103.5, 119.9, 148.0, 151.5 Hz: two
  lateral-rocking pairs, torsion, ONE bounce — the scalar tool sees only the
  bounce).
- Effective masses generalize per 7004C App. A: rocking modes own **rotary
  effective inertia** (kg·m²); per-direction sums equal the rigid totals to
  3e-16 (the p.56 statement, now checker-backed). Consequence: the "M0" in
  C²M0²A is direction-specific; using total mass for a rocking notch is a
  category error.
- **Resultant-force trap** (fig_b3, gif_b): lateral base drive at the 148-Hz
  rocking mode → per-foot vertical force 9.8 N per unit base accel while the
  NET vertical force is exactly zero (antisymmetric cancellation; net/(4·foot)
  < 1e-16) and the interface moment |My| = 3.5 N·m. The quantity the handbook
  p.10 default practice limits — the summed in-axis force — carries no trace
  of the mode that is loading the feet.

## 4. EX-C — notch geography (the "how far" answer)

`code/ex_c_notch_distance.py` → `results/ex_c_results.json`, fig_c1/c2/c2b/
c3/c4, gif_c. 7 variants: feet ×1/×9, plate t=3.5/5/8 mm, plate Q=25/6.

- **The single notch becomes a cluster.** In the mean-feet channel of the
  soft-feet variant the payload carves 5 prominent suppression dips between
  87–184 Hz (deepest −36 to −46 dB). Bounce and rocking notches live in
  DIFFERENT interface combinations (mean vs x-/y-differential): a single
  accelerometer never sees the 2-DOF picture.
- **Notch frequencies shift off the fixed-base modes**: bounce +6%, rock_x
  −11% (soft variant; stiff variants 0–4%). A notch predicted at the shaker
  fixed-base frequency can simply miss the flight notch — directly relevant to
  notching practice and to Sweitzer-style criteria.
- **Visibility is a REGIME question, not a fixed radius** (fig_c2/c3/c4):
  - Low modal overlap in the backing (MOF = half-power bandwidth / modal
    spacing < 1 — the typical aerospace-panel situation at payload
    frequencies): the payload retunes GLOBAL backing modes, and the bounce
    notch is visible essentially everywhere (3-dB suppression to the plate
    boundary, 0.58 m ≈ 6 foot spacings, in 3 of the Q=25 variants).
  - High modal overlap (Q=6 and/or dense modes, MOF ≈ 0.9–3.5): visibility
    contracts to **r ≈ λ/4** around the feet (0.07–0.09 m vs λ/4 =
    0.08–0.10 m at 286–440 Hz) — the first-principles wavelength guess holds
    only in this diffuse regime.
  - Rocking notches are systematically more local (r_vis 0.06–0.34 m) and can
    be **invisible in point spectra** even at a foot (differential absorber);
    one variant (stiff_t8 rock_x) shows interface suppression with <3 dB point
    visibility anywhere — you'd only see it in a differential/moment channel.
- Convergence (2× modal refinement): notch frequencies shift <0.5%, area
  fractions <1.4 pts. The 3-dB radius r_vis is threshold-sensitive when the
  median suppression hovers near 3 dB — one variant flips global↔local under
  refinement (D8) → r_vis is reported as descriptive; f_notch/area-frac are
  the converged metrics. **This is the checker's first documented YELLOW.**
- Low-frequency sanity: payload rides the feet rigidly at 22 Hz (ratio
  1.004–1.035, finite dynamic amplification expected).

## 5. EX-D — the 7004C practice on a multi-point payload

`code/ex_d_force_limits.py` → `results/ex_d_results.json`, fig_d1/d2.

- Setup: CG offset 0.03 m → uniform shaker drive excites the pitch-rocking
  mode (the p.8 "uniformity of attachment motion" mechanism). Test spec =
  octave peak-hold envelope of the hypothetical-flight mean-foot accel PSD (no
  added margin). Semi-empirical C² = 3.72 (Eq B1/B2 at mass ratio 0.56, Q=25);
  the flight-implied C² is 0.87 — the tool is conservative here, consistent
  with the Table-1 empirical spread (C²<5 covers 80% of cases).
- Worst per-foot overtest (peak PSD ratios in ±10% bands, vs hypothetical
  flight):

  | mode | unlimited | net-F limited (p.10 default) | + moment limit |
  |---|---|---|---|
  | pitch (z–θy lower, 94.1 Hz) | 2107× (33 dB) | **221× (23 dB)** | 32× (15 dB) |
  | bounce (z–θy upper, 132.3 Hz) | 204× (23 dB) | 5.2× (7 dB) | 4.2× (6 dB) |

  Net-force limiting fixes the bounce mode but leaves a 23-dB per-foot
  overtest at the rocking mode (partial force cancellation hides it from the
  net-force channel); a §5.8-style moment limit removes most of it. Residual
  factors trace to the shared envelope conservatism (stated on the figure).
- **Simultaneous undertest:** the roll (θx) channel is excited exactly zero on
  the uniform single-axis shaker (symmetry) while flight drives it to its peak
  near 93 Hz — no force or moment limit can repair a mode the test never
  excites; that needs multi-point/multi-axis excitation.
- Verification: ΣF = m·a_cg and My_cg = Iyy·θ̈y to 4e-15/2e-14; 20-Hz net
  apparent mass = 6.19 kg vs M0 = 6.0 (3.2%, expected finite-frequency
  amplification); limited responses respect their limits to 1.000.
- Table caveat (D9-equivalent, in-code note): test modes 93.1 (θx) and 94.1
  (pitch) are 1% apart; band metrics cannot separate them, so the table
  reports the two separable z–θy modes and θx is handled as the undertest
  finding.

## 5b. EX-E — empirical limiting without a coupled forced FEM

`code/ex_e_empirical_reconstruction.py` → `results/ex_e_results.json`,
fig_e1/e2/e3. Added 2026-06-12 (Andrew directive D10/D11). Question: can you do
response/force limiting from sparse interface data instead of a coupled FEM?

- **The measurement replaces the coupled solve.** The impedance method (7004C
  Eq 3/4) with measured interface quantities — load apparent mass Ml, source
  apparent mass Ms, source free acceleration A_free, all obtainable without
  solving the coupled system — reconstructs the coupled interface loads. With the
  full interface matrix it is **exact** (checker: max rel err < 1e-9 across 4
  regimes). No coupled forced FEM needed.
- **Sparsity is the cost** (soft/low-overlap regime band-peak errors): single-foot
  / single-point condensation → moment error **100%** (predicts zero) and per-foot
  force error **68–91%** at every mode (the resultant trap, quantified); rigid-3
  (≥3 spaced feet) → moment 0–17%, per-foot **3–17%** (rocking recovered);
  diagonal/feet-independent → erratic (cross-impedance matters); full matrix →
  exact. At high frequency (stiff feet, wide spacing) rigid-3 degrades (per-foot to
  ~31%) as the interface warps / feet decouple — the §4 crossover.
- **Remote response proxy** (1–3 foot-spacings away): transmissibility-based
  response limiting is *exact* for a linear system if calibrated in the integrated
  configuration (any distance within the visibility regime); a bare/un-integrated
  calibration is **~100% wrong broadband** because the payload shifts every backing
  mode → operational rule: calibrate the response-limit transmissibility with the
  payload installed.
- **Net judgment:** the path is "no coupled forced FEM," not "no model." A coarse/
  uncoupled model serves as a prior (residual mass, rigid-interface reconstruction,
  extrapolation); the scrappy interface measurement + integrated-config
  transmissibility carry the rest; Bayesian uncertainty widens the limit when data
  is sparse. = the robust apparent-mass twin (notes §6.1). Full synthesis +
  practical recipe in `notching_findings_for_future_agents.md`; a literature-review
  agent prompt is in `lit_review_prompt.md`.

## 6. Answers to the three questions

1. **What changes:** apparent mass → 6×6 matrix; one notch → a shifted CLUSTER
   of notches living in mean vs differential interface channels; "M" splits
   into per-direction effective masses including rotary inertia; the net
   in-axis force is structurally blind to rocking (exactly zero in the
   symmetric case); and a uniform shaker simultaneously over-tests coupled
   rocking (23 dB per-foot here even after standard force limiting) and
   under-tests cross rocking (exact zero excitation).
2. **How far from a foot:** not a fixed distance — a modal-overlap regime
   switch. Low overlap (discrete global backing modes): the notch is visible
   structure-wide (~plate boundary, ~6 foot spacings here). High overlap
   (heavy damping/dense modes): r ≈ λ/4 around the feet. Rocking notches are
   more local and can vanish from point spectra entirely.
3. **Method:** first principles delivered the right mechanisms (matrix
   impedance, absorber action, resultant trap) but the wrong distance rule —
   the λ/4 intuition holds only in the diffuse regime; the modal-overlap
   switch, the notch cluster, and the notch-frequency shifts only appeared in
   the (cheap) compliant-backing model. For hardware decisions, use the
   coupled-model thread (ShockSat × tray).

## 7. Sensitivity (AGENTS.md gate)

Varied the assumptions most likely to change the conclusions: backing
stiffness/wavelength (plate t 3.5/5/8 mm), backing damping (Q 25 vs 6 — the
decisive knob: it flips the visibility regime), payload mount stiffness (×1 vs
×9 — moves notches across the modal-density landscape), CG offset (EX-B
symmetric=exact cancellation vs EX-D offset=partial), and modal truncation
(2×). Conclusions that are REGIME statements (global-vs-λ/4, resultant trap,
cluster/shift) survived every variant; the specific numbers (r_vis, overtest
ratios) are illustration-grade, not design values.

## 8. Limitations / manual-review checklist

- Plate carries bending only; no membrane/lateral foot load path on the
  backing (ledger C4). Lateral-rocking interaction with the backing is
  therefore only probed in EX-B (enforced motion).
- Complex-TDOF Appendix C tables not replicated (image-only PDF; D3) —
  **checker YELLOW #2**, methods used are equation-anchored.
- Octave peak-hold envelope with no margin is a simplified spec; real specs
  add margin and smoothing — would scale both arms, not their ratio structure.
- The checker verifies numbers and artifact existence; figure legibility was
  reviewed manually (all 13 figures + 3 GIF stills inspected in-session;
  provenance stamps on every figure per the plot gate).
- Residual risk: notch metrics depend on the chosen interface combination
  weights; weights are the exact rigid-body combinations (Q6/Q7), but a real
  test would estimate them from geometry with error.

## 9. Artifacts

- `7004c_multipoint_notch_summary.pptx` — 14 slides, GIFs animate in
  slideshow mode (numbers pulled from results JSONs by `make_pptx.py`).
- `figures/` — 13 PNGs + 3 GIFs (+3 stills); `results/` — 4 results JSONs +
  `ex_c_fields.npz`; `code/` — common.py + 4 example scripts + gif/pptx
  builders; `check.py`, `checker_report.json`, `run_all.sh`, `runtime.json`,
  `manifest.json`.
- Reference: `references/NASA-HDBK-7004C-Force-Limited-Vibration-Testing.pdf`
  (anchors from pages 30–38, 55–62; quotes from pages 8, 10, 29, 31, 48).
