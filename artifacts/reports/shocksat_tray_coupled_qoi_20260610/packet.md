# ShockSat × tray coupled QOI — method & coupling comparison (Human-Review Packet)

**Workspace:** `artifacts/reports/shocksat_tray_coupled_qoi_20260610/`
**Replay:** `bash run_all.sh` (resumable stages; delete `out/` for full rerun).
**Checker:** `python3 check.py` → `checker_report.json` (green/yellow/red standard).
**Date:** 2026-06-10. **Scope authority:** predecessor decision D38 + task card.

> **Read this first — honesty banner.** The coupled tray QOI is
> **HYPOTHETICAL**: no tray was ever mounted to ShockSat. This is a **methods
> demonstration**, not a hardware prediction — the tray placement (D3), mount
> stiffness (D4), and base input (D2) are **INVENTED** assumptions, ledgered
> and awaiting Andrew's sign-off. The ShockSat primary IS the validated modal
> twin (predecessor, modal regime); the tray FEM is the pre-test FIM model.
> **NO sampler was run in this task** (D1): this is forward propagation of the
> predecessor's converged NUTS posterior + priors. No convergence claim is
> made because there is nothing here to converge. NASA-HDBK-7004C's
> force-limiting story is the physics backbone throughout.

---

## 0. Method summary (read this before any number)

**Question.** For the net CG interface load (Fx, Fy, Fz) a payload tray
transmits into ShockSat: how much do the **analysis method** (time-history vs
modal-SRS vs PSD/Miles) and the **coupling assumption** (uncoupled fixed-base
vs coupled) change the answer — and is the answer dominated by the
**unidentified mount stiffness**?

**Model form (all linear, all SI at the interface).**
- *Source:* ShockSat free-free 74-mode ROM, `K_r(θ_S) = A_fix + Σ_g θ_g A_g`
  (mass = identity), drive-point accelerance at mount node P (top circular
  plate center, gid 7000072, 6 DOF):
  `Y_S(ω) = Σ_m φ_m(P)φ_m(P)ᵀ(−ω²)/(λ_m − ω² + 2iζ_m√λ_m ω)` over 6 RBM + 74
  elastic modes; snail-inch → SI conversion per contract C8 (verified to
  9×10⁻⁵ against the rigid-body mass matrix, gate V3).
- *Load:* hexapod tray (133 nodes, SI) with all 6 feet rigidly condensed to
  ONE massless base point (single-point 6-DOF condensation, D38), connected
  through the uncertain 6-DOF mount CBUSH. Load apparent mass
  `M_chain(ω) = M_rb + ω²Γᵀ(K̂ − ω²I + iωĈ)⁻¹Γ` with the rank-6 mount dashpot
  handled **exactly** via a Woodbury identity (D8) — verified to 4×10⁻⁶
  against direct dynamic-stiffness evaluation including at peaks (V6).
- *Coupling (LM-FBS, contract C5):*
  `F_cpl(ω) = (I + M_chain Y_S)⁻¹ M_chain a_free(ω)`;
  uncoupled = `F_unc = M_chain a_free` (infinite source impedance — standard
  spec practice). Verified: FBS algebra exact vs direct coupled solve
  (8.8×10⁻¹⁰, V5), Newmark time integration of the assembled coupled system
  matches to 0.6 % peak (V7), 7004C TDOF analytic anchors reproduced (V8).

**Likelihood / data usage.** None — no inference. Uncertainty is **propagated**:
θ_S ~ predecessor NUTS posterior (4000 draws, R-hat 1.022 — the converged
full-data design only), θ_T ~ LogNormal(0, 0.25)⁵ prior (tray untested),
mount k ~ LogNormal(ln k_nom, 1.15)⁶ prior (a joint; deliberately wide), input
seed aleatory (8 records). Model-form discrepancy is NOT propagated — the
predecessor's σ_f ≈ 4.6 % frequency-level discrepancy is a floor under all of
this (§8); QOI bands are parameter+forcing only and therefore likely
under-estimates.

**QOI (contract C1).** Per-axis peak |F_d(t)| over a 20 s record; the
interface force through the massless mount = net force on the tray
= m_tray·a_CG (the inertial-sum identity is also how V5/V7 verify it).

**Environment (contract C7, INVENTED, D2).** 3-axis independent Gaussian,
flat 0.01 g²/Hz over 20–250 Hz (1.52 grms/axis), T = 20 s, fs = 2048 Hz,
8 seeds. Trusted band 20–250 Hz (ROM validated < 280 Hz). The Miles arm
consumes the *analytic* PSD, so the card's "SRS→PSD conversion knobs" are
N/A by construction.

**Methods (contracts C6, C9).**
1. **TIME-HISTORY (reference):** exact linear frequency-domain synthesis
   (periodic-stationary record → FFT multiply → IFFT), coupled and uncoupled.
2. **MODAL-SRS:** maximax absolute-acceleration SRS (Smallwood filter, V4 ✓)
   of the same record; F_d = √(Σ_k [m_eff,k,d·SRS_d(f_k,Q)]² +
   [m_resid·peak|a|]²) — SRSS + residual rigid mass; participation = modal
   effective mass (MMF, per D38); Q ∈ {10, 25, 50, informed} where "informed"
   = per-mode Q_k = 1/(2ζ_k) (the apples-to-apples variant). Inherently
   UNCOUPLED.
3. **PSD/MILES (labeled ENVELOPE arm):** per-mode Miles from the analytic
   PSD, RSS + rigid grms term, ×3 ("3σ"). The true Gaussian 20 s peak factor
   is ~3.9–4.2σ (contract C7), so 3σ is *expected* to under-predict record
   peaks ~25 % — and does (§5).

**Run-specific graphical model:** `figures/fig_graphical_model.png`
(schematic of exactly this propagation; not a borrowed paper figure).

**Verification (all 15 gates GREEN, `out/verification.json`):** tray rebuild
reproduces the FIM fixed-feet modes to 2.6×10⁻¹¹ (V1); chain rigid mass and
participation completeness exact (V2); unit conversion via RBM mass line
9×10⁻⁵ (V3); SRS filter vs analytic SDOF (V4); FBS algebra exact (V5);
exact damped apparent mass (V6); Newmark cross-check 0.6 % (V7); 7004C TDOF
anchors: load M(0.62)=1.624, load M(1)=50.01, source M(1)=0.02 (V8); input
grms/flatness (V9).

---

## 1. Configuration (the invented part — sign-off items)

| item | value | status |
|---|---|---|
| mount node P | ShockSat Top_Circular_Plate center, gid 7000072, z ≈ 57.75 in | INVENTED (D3); alt edge node swept |
| tray axes | aligned to ShockSat global | INVENTED (D3) |
| mount CBUSH nominal | k_t = 2×10⁶ N/m, k_r = 2×10⁴ N·m/rad per axis | INVENTED (D4) |
| mount prior | LogNormal per axis, 95 % ≈ ×/9.5 | the "unconstrained joint" hypothesis |
| base input | flat 0.01 g²/Hz, 20–250 Hz, 1.52 grms/axis | INVENTED (D2); linear-valid |
| damping | tray ζ=1 %, mount ζ=5 % (bounce-ref), ShockSat measured (.ash) | A3–A5, all swept |

Physical footnote: the tray's foot circle (20.8 in) is wider than the 18-in
top plate — it would not physically bolt on as-is. Irrelevant under
single-point condensation for net CG force, but it underlines the
methods-demo label. Mass ratio: tray 3.16 kg on ShockSat 57.96 kg (5.4 %).
Chain fixed-base modes at nominal mount: 75.9, 76.0, 84.5, 84.7 (lateral/
rocking), 88.9 (torsion-ish), **116.2 Hz (z-bounce)**; tray's own elastic
modes start at 457 Hz — outside the input band, so the tray responds
quasi-rigidly on its mount (this matters for §7).

## 2. Headline numbers (joint uncertainty: 128 draws × 8 seeds)

Per-axis peak |F_d| in N — median [2.5 %, 97.5 %] of seed-median over draws
(`out/qoi_results.json`):

| method | Fx | Fy | Fz |
|---|---|---|---|
| **time-history COUPLED (reference)** | **352 [120, 473]** | **308 [173, 437]** | **481 [198, 651]** |
| time-history uncoupled | 456 [138, 694] | 413 [199, 669] | 543 [206, 1278] |
| modal-SRS informed-Q | 436 | 388 | 533 |
| modal-SRS Q=25 | 510 | 478 | 819 |
| Miles 3σ informed-Q | 344 | 305 | 399 |
| Miles 3σ Q=25 | 403 | 381 | 625 |

The parameter-uncertainty band (×2–6 wide) **dwarfs every method-vs-method
difference** — and §6 shows that band is almost entirely the mount prior.

## 3. Method comparison (conservatism vs the reference, same coupling)

Median ratios pooled over draws×seeds (`figures/fig_method_comparison.png`):

| ratio | Fx | Fy | Fz | read |
|---|---|---|---|---|
| modal-SRS informed-Q / TH-unc | 0.96 | 0.95 | 0.98 | the SRS *machinery* (SRSS+residual) is ~unbiased when Q is right |
| modal-SRS Q=10 / TH-unc | 0.73 | 0.78 | 0.97 | assumed Q too low → unconservative for lateral |
| modal-SRS Q=25 / TH-unc | 1.12 | 1.21 | 1.50 | |
| modal-SRS Q=50 / TH-unc | 1.55 | 1.64 | 2.07 | the **Q assumption dominates method error** |
| Miles 3σ informed-Q / TH-unc | 0.75 | 0.75 | 0.74 | the predicted ~25 % peak-factor shortfall (3σ vs true ~4σ), quantitatively confirmed |
| Miles 3σ Q=25 / TH-unc | 0.87 | 0.95 | 1.15 | practice Q partially cancels the peak-factor miss |

**Takeaways.** (1) Method error is **assumption error**: with the true modal
damping, modal-SRS lands within 5 % of the time-history answer; sweeping the
conventional Q from 10→50 swings the answer ×2–3. (2) Miles "3σ" is an
envelope convention, not a peak prediction — it sits ~25 % below true 20-s
record peaks by construction; calling it conservative requires the Q
assumption to do the work. (3) Both shortcut methods are per-axis/uncoupled —
their compound error vs the coupled truth is the method ratio × the §4 gap.

## 4. Uncoupled → coupled gap (force limiting, NASA-HDBK-7004C)

`force_limiting_factor = peak_unc/peak_cpl` per draw×seed
(`figures/fig_force_limiting.png`, `figures/fig_apparent_mass.png`):

| | Fx | Fy | Fz |
|---|---|---|---|
| median | **1.27** | **1.31** | **1.12** |
| 2.5 % | 1.02 | 1.03 | 1.02 |
| 97.5 % | 1.62 | 1.76 | **2.22** |

The uncoupled (test-spec) assumption **over-predicts the interface load by
~12–31 % at the median and up to ~2.2× across the mount prior** — this is the
7004C over-test factor, realized here with a validated source model. The
transfer view shows the classic notch at the chain resonance (×1.3 at 114 Hz
in z at nominal; deeper for lateral/rocking, where source mobility at the top
of the stack is higher). The apparent-mass figure shows the 7004C Fig-9
source/load conventions on our system, with the stated free-free deviation
(source → rigid mass line at low f, not ∞; contract C3) — and an honest
panel note that the z-axis source is mass-like below 250 Hz at this node
because little ShockSat elastic z-motion participates there (the notch
behavior shows in the x axis, where lateral bending modes live).

## 5. The Miles/peak-factor honesty note

For a 20 s stationary Gaussian record band-limited at ~100–250 Hz, the
expected peak is ~3.9–4.2σ. Reporting 3σ as "the peak" is therefore an
under-prediction by construction (×0.74 observed, exactly as the contract
predicted *before* the run). This was written into contract C7/C9 up front so
the envelope arm's miss is a documented property, not a surprise.

## 6. Mount-stiffness sensitivity — the QOI is mount-dominated (hypothesis CONFIRMED)

**Variance decomposition** (OAT main effects / joint variance, coupled
time-history peaks; `out/variance_decomposition.json`,
`figures/fig_mount_sensitivity.png`):

| input group | Fx | Fy | Fz |
|---|---|---|---|
| **mount k (prior)** | **1.02** [0.57, 1.60] | **1.05** [0.67, 1.62] | **0.94** [0.68, 1.27] |
| θ_S (ShockSat posterior) | 0.002 | 0.007 | 0.000 |
| θ_T (tray prior) | 0.105 | 0.066 | 0.006 |
| input seed (aleatory) | 0.087 | 0.096 | 0.068 |

(Mount-row brackets = bootstrap 95 % CI, `out/variance_decomposition.json`.)
**Why a mount value can exceed 1.0:** this is an OAT main-effect ratio —
Var(seed-median QOI | only that group varies, others at nominal/posterior-
median) ÷ Var(QOI | all vary) — NOT a Sobol first-order index (those are ≤1 by
construction). A ratio of two Monte-Carlo variance estimates (n_oat = 64,
n_joint = 128) carries ~22 % relative error, so the Fx/Fy mount ratios (1.02,
1.05) are statistically indistinguishable from 1.0 (CIs span it). The honest
reading is "the mount explains essentially ALL of the variance," not literally
>100 %. A small genuine excess is also possible from non-additivity (the OAT
slice at the nominal point differs from the mount's marginal share in the
joint run), but here it is dominated by MC noise.

The mount prior alone reproduces ~the entire joint QOI variance on all three
axes. The carefully-calibrated ShockSat posterior contributes **< 1 %**. The
predecessor's under-identification finding (joints not identifiable from the
modal data) **propagates directly into the QOI**: knowing the primary
structure well buys almost nothing while the mount is unknown.

**Deterministic decade sweep** (all 6 stiffnesses ×, nominal elsewhere):
peak F_z coupled goes 111 → 633 → 315 N over k_t = 10⁵ → 10⁷ → 10⁹ N/m —
**non-monotonic** (soft mount isolates; k ≈ 10⁷ puts the bounce cluster
mid-band at maximum response; above ~10⁸ the mount is rigid relative to the
tray and the QOI saturates at the fixed-feet-tray answer). The QOI spans
×5–10 over the prior range. Other sensitivities for scale (`out/sweeps.json`):
damping grid (ζ_struct 0.5–2 % × ζ_mount 2–10 %) moves F_z 362–698 N —
**comparable to the method differences**; ShockSat damping ×0.5/×2 moves the
QOI < 1 % (the coupling correction is mass-controlled, not damping-
controlled); alternate edge-node placement ±17 % (Fy) and less elsewhere;
+0.5 kg adapter +6–12 %; halving the record (df 0.05→0.1 Hz) shifts peaks
1–4 % (resolution adequate, Discretization gate).

## 7. Modal Identifiability Gate on the coupled interface modes

(`out/mount_identifiability.json`, `figures/fig_identifiability.png` —
strain-energy decomposition + finite perturbation; **no sampler claim**.)

- The coupled rocking/bounce cluster stores **up to 90 % of its strain energy
  in the mount** (87.1 Hz: 19 % translational + 70 % rotational; 121.6 Hz
  z-bounce: 40 % translational). Closure = 1.0000 per mode.
- Mount modal sensitivity d ln f/d ln k peaks at **0.449** — ~**10× above**
  the predecessor's σ_f ≈ 4.6 % discrepancy floor. **Contrast with the
  bare-ShockSat joints (3 % < 4.6 % floor, unidentified):** a modal test of
  the MOUNTED configuration would identify the mount stiffness easily; the
  interface modes are exactly where its information lives.
- Finite perturbation (in-load-path check): mount ×0.5 → QOI −24…−29 %;
  ×2 → +11…+31 %; coupled bounce/rock frequencies move accordingly.
- **Pre-test lever (the actionable conclusion):** since the QOI is
  mount-dominated (§6) and the mount is identifiable from coupled interface
  modes, a cheap mounted-configuration modal survey (or a force-gauge
  measurement of M_chain peaks) collapses most of the QOI uncertainty.
  Calibrating the primary further does not.

## 8. Response-limit proxy QOI (D7 / vision §2.2)

(`out/response_limit_proxy.json`, `figures/fig_proxy.png`.) Industry
response-limits rather than force-limits. Best 1–2 channels per axis, ranked
by |corr(F_d, accel)| in the force-driving 60–130 Hz band, worst-case over 32
joint draws:

| axis | best channel | ρ (band, worst) | ρ (full record) | α [N/(m/s²)] (cv) |
|---|---|---|---|---|
| Fx | tray_center_x | 0.9999 | 1.000 | 3.13 (0.3 %) |
| Fy | tray_center_y | 0.9999 | 1.000 | 3.14 (0.3 %) |
| Fz | tray_center_z | 1.0000 | 1.000 | 3.16 (0.3 %) |

α ≈ m_tray = 3.156 kg on every axis: **in this band the tray rides its mount
quasi-rigidly** (its own elastic modes start at 457 Hz, above the 250 Hz
input band), so one well-placed accel × tray mass IS the net CG force, and a
response limit = F_limit/α is an excellent force-limit stand-in.
**Scope caveat (do not over-generalize):** this near-perfect proxy is a
property of this band/configuration. With input content exciting tray elastic
modes (> 450 Hz here), or for per-mount loads/moments (dropped per D38),
single-accel proxies degrade — corner/apex channels already show ρ as low as
0.3–0.7 (full table in the JSON). Net-CG force remains the physics-backbone
QOI; the proxy is the test-floor expression of it. FLAGGED for sign-off (D7).

## 9. Limitations / what would change the conclusions

- **Everything coupled is hypothetical** (D2/D3/D4 invented); the value is the
  method/coupling/mount-dominance structure, not the Newtons.
- **Model discrepancy not propagated**: the predecessor twin carries
  σ_f ≈ 4.6 % frequency discrepancy (model-form, not noise). QOI bands here
  are parameter+seed only → under-estimates. A discrepancy-aware propagation
  is future work.
- **Free-free source** (validated config). A flight-mounted ShockSat changes
  Y_S below ~50 Hz (C3); conclusions are configuration-specific there.
- **Rotational base input = 0** (A6); moments/per-mount loads out of scope (D38).
- **Damping is the next-biggest lever after the mount** (×1.9 on F_z across
  the swept grid) and is assigned, not identified.
- **OAT variance decomposition** ignores interactions (fractions need not sum
  to 1); adequate here because one effect is ~100 %.
- Linear regime throughout; no pyro/shock claim of any kind (shock case
  SKIPPED per D38 — no probe was run).

## 10. Overnight experiment (D10): does one mounted-config modal survey buy
## back the QOI? — a structured HONEST NEGATIVE (status: YELLOW)

**What ran** (Andrew authorized "do whatever makes most sense"): a
SYNTHETIC-TRUTH value-of-information experiment on the §6/§7 findings.
Truth = the full coupled model at prior draws **plus a 6×6 mount with
translation–rotation off-diagonal coupling the diagonal inference model
cannot represent** (structured model-form discrepancy, A21) + 0.3 %
frequency noise. Survey = 27 calib-filtered coupled modal frequencies
≤ 240 Hz. Inference = NUTS on 12 latents (6 mount multipliers, 5 tray θ,
σ_f), frequency-only likelihood, on a reduced coupled ROM validated to
3.6×10⁻⁴ off-anchor (`out/coupled_rom_report.json`). Truth was SHA-locked and
never read by the sampler (A28). Auto-remedy ran as designed.

**Result 1 — the sampler does NOT converge, and the diagnosis is physics,
not a bug** (`out/multimodality_diagnosis.json`, gate = YELLOW):
base 4×(1000+1000) d8: worst R-hat **5.03**, min ESS 2, **0 divergences**;
remedy 4×(2000+2000) d9: worst R-hat 9.74. All four chains fit the data
EQUALLY well (rms log-residual 3.3–3.5 %; cross-chain predicted-frequency
spread median **0.06 %**) while their mount parameters differ wildly —
data-space agreement + parameter-space disagreement = a sloppy/multimodal
ridge, the same signature as the predecessor's band/LOMO designs.

**Result 2 — why: only 2 of 6 mount stiffness COMBINATIONS are identifiable
at the realized discrepancy floor.** The posterior honestly reports
σ_f ≈ **3.7 %** ≫ the injected 0.3 % noise — that is the structured
discrepancy (off-diagonal mount + θ_S median-vs-draw + condensation) being
measured. A FIM eigen-decomposition of dlnf/dlnk at that floor gives
eigenvalues [97, 15, 0.74, 0.44, 0.02, 0.0] vs prior precision 0.76: the
**k_ry-dominated lateral-rocking combination** and **k_tz (z-bounce)** are
strongly identified; k_rz is marginal; the k_tx/k_ty/k_rx splits are
prior-dominated. Counterfactual: at the 0.3 % noise floor alone, **5 of 6**
combinations would be identifiable ⇒ **the binding constraint is model-form
discrepancy** — the same wall as the predecessor's σ_f = 4.6 % joints
finding, now reproduced in a controlled synthetic setting.

**Reconciliation with §7 (no claim is withdrawn, one is sharpened).** The §7
gate statement — the OVERALL mount level is identifiable (dlnf/dlnk = 0.449 ≫
floor) — HOLDS: two combinations are pinned far tighter than the prior. What
the overnight run adds is that the **per-axis 6-DOF decomposition is NOT
recoverable from frequencies alone** at a realistic discrepancy floor.
Pre-test lever, refined: to actually collapse the mount uncertainty you need
observables that break the lateral/rocking symmetry — **mode shapes, FRF
amplitudes, or interface force gauges — not more frequencies**; or a
discrepancy reduction; or an honest symmetric (fewer-parameter) mount
parameterization.

**Result 3 — QOI-level value of information: suggestive but NOT trustworthy
(YELLOW).** Propagating the (non-converged, pooled-chain) posterior:
95 % width ratios after/before = 0.93/0.38/0.91 (Fx/Fy/Fz, coupled
time-history); truth covered on Fy/Fz, **missed on Fx both before and after**
(truth 479.8 N vs band edge ≈ 473 N before — a ~1 % exceedance that is partly
the diagonal model family being unable to reach the off-diagonal truth's
coupled response, and partly MC tail resolution at 128 draws). Force-limiting
factor bands: `figures/fig_voi.png` (figure carries the NOT-CONVERGED flag
and worst R-hat/ESS per the figure-invalidity gate). **None of these
intervals may be quoted as credible intervals.**

**The honest headline.** Finding #4's promise ("a cheap mounted modal survey
collapses most of the QOI uncertainty") is **NOT confirmed as stated**: a
frequencies-only survey at a realistic discrepancy floor pins the bounce and
one rocking combination, leaves the posterior multimodal, and buys only a
modest, not-yet-trustworthy QOI narrowing. The experiment was designed so a
negative would be informative, and it is: it localizes exactly WHAT extra
measurement is needed (symmetry-breaking observables) and reproduces the
program's recurring result that **model-form discrepancy, not sensitivity,
caps identifiability**.

### 10a. Pooling the mount axes (D15/D16 — Andrew's "6 → 3" suggestion)

Pooling was run, FIM-first then sampler (`out/pooled_fim.json`,
`out/pooled_posterior.json`, `out/pooled_diagnosis.json`):

| parameterization | FIM @ 3.7 % floor | NUTS 4×(1000+1000) d8 |
|---|---|---|
| 6 (full) | 2/6 identifiable | R-hat **5.03** (multimodal) |
| 4 (t_lat, t_z, r_lat, r_z) | 2/4 | — |
| 3 (t_all, r_lat, r_z) | 2/3 — 3rd eig 0.74 ≈ prior precision 0.76 (boundary) | R-hat **1.52** |
| 2 (t_all, r_all) | 2/2 "fully separable" (local) | R-hat **1.24** — still misses the gate |

The sampler ladder confirms the FIM ordering, but even 2 pooled parameters do
not pass, for two reasons the LOCAL FIM cannot see (`pooled_diagnosis.json`):
(1) **stiff-side saturation** — above ~5× nominal the mount is rigid relative
to the tray, frequencies pin (sweep: f1 → 84.8 Hz) and the likelihood goes
flat, so t_all's upper tail is prior-dominated (samples span 0.05–39, the
whole prior) — one-sided identifiability; (2) a **t_all ↔ r_all ridge**
(corr(log) = −0.74): the CG-offset rocking modes price a *combination* of
lateral translation and rotation stiffness. The prior-whitened **joint**
(mount+tray) FIM at nominal says p2 should be fine and the tray θ_T sit
cleanly at prior — the sampler disagrees away from nominal, a textbook
local-vs-global identifiability lesson and exactly why the D12 gate names
profile-likelihood/posterior analysis as the FIM's companion.

**Remedy verdict (p2r, 4×(2000+2000) d9): WORSE — R-hat 2.22, ESS 3, 0 div.**
One chain spent its whole run in the saturated stiff tail (t_all 2.6–38.8,
median 10) where the likelihood is flat, while the other three sat near ×1 —
the same more-compute-finds-more-flat-region signature as the 6-param remedy.
This settles slow-mixing vs structure: the t_all non-identifiability is
STRUCTURAL and one-sided. What frequencies DO deliver even here: **r_all is
pinned across all chains (≈0.9–1.07)** and **t_all gets a LOWER bound
(≳ ×0.4)** — engineering-useful ("the mount is at least this stiff") but
never an upper bound, and note the QOI is non-monotonic in k (peaks at
~×5 nominal), so a stiffness lower bound does NOT by itself bound the load.
Conclusion: **pooling is necessary but not sufficient** at this discrepancy
floor; the symmetry-breaking-observable lever stands, with the addendum that
saturation puts a hard one-sided limit on what any frequency data can say
about a stiff mount.

## 11. Checker and replay

`bash run_all.sh` replays everything (stages skip finished outputs; MC
checkpoints every 16 draws). `python3 check.py` reports per-gate
green/yellow/red and exits non-zero only on red; see `checker_report.json`.
Read-only upstream inputs are SHA-pinned (`inputs_sha256_start.json`) and
re-verified by the checker. Runtime: `runtime.json` (active 1587 s ≈ 26 min
of compute; wallclock includes interactive review).

**Sign-off requests for Andrew (D2/D3/D4/D7):** input spec (level/band/class),
tray placement node, mount nominal+prior, and whether the response-limit
proxy should be promoted alongside (not replacing) the net-CG-force QOI.
All four are cheap parametric reruns if changed.
