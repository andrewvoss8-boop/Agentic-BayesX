# Deck outline — IFT vs StatFEM on the real ShockSat (~10 slides)

Gated on a non-RED checker (§9). Every number traces to `out/scorecard.json` / per-split cells / `check.py`.
Carry the coarse-FEM ceiling + single-hit/split-only YELLOWs on the relevant slides. Build to pptx via
`code/make_pptx.py` (reuses the StatFEM deck pattern) once the 5 figures + checker exist.

---

### Slide 1 — Title / the concern
**Does it matter WHERE the physics lives — in the prior or the likelihood — for a trustworthy ShockSat twin?**
Sub: a faithful Information-Field-Theory (IFT) twin scored apples-to-apples against our StatFEM twin on the REAL
ShockSat held-out-sensor QOI. Honest negatives are valid. (Advisor: Ilias Bilionis.)

### Slide 2 — The apples-to-apples contract
One picture: IFT, M2, L5 differ ONLY in where physics/trust lives; everything else byte-identical and REUSED
(same data, forward `realfrf`/`core`, split RNG, scorer `score.py`) — proven by `manifest_sha256.txt` (15 files,
re-verified by `check.py`). IFT = physics in the PRIOR (β); M2 = physics in the LIKELIHOOD (σ_d); L5 = modal-
feature bar (different, unimodal observable). Carry: 1 impact / 1 hit / channel-split-only (YELLOW).

### Slide 3 — The IFT construction + the one honest deviation
Physics-informed prior π(u|θ,β) ∝ exp(−(β/2)‖A(θ,ω)u−f‖²); β = learned inverse-temperature = trust thermometer.
Observable kept = log|H| (SAME as M2). Because log|H| is log-Rician (not Gaussian), the field is marginalized by
a DOCUMENTED log-magnitude moment approximation (Andrew's call): log|H| ~ N(log|H^FEM(θ)|+c, σ_meas² +
v_j(θ,β)/(2|H^FEM|²)) — a log|H| likelihood whose per-bin variance is PHYSICS-DERIVED and set by ONE learned β.
(method_ift.md.)

### Slide 4 — Fig A (money): the held-out QOI scorecard
`figA_scorecard.png`. Peak + band proper scores (interval/CRPS/logpd), split distributions, IFT vs L5 vs M2.
Takeaway: **IFT beats L5 on the peak QOI (interval 980 vs 2026, CRPS 76 vs 170, logpd −6.05 vs −6.59, coverage
0.97 vs 0.87); loses on band-GRMS (1.12e5 vs 5527); M2 non-converged → flagged.** The coarse FEM is the ceiling.

### Slide 5 — Fig convergence table: the robustness mechanism
`fig_convergence_table.png`. Both whole-FRF arms multimodal under NUTS (IFT R̂ 264, M2 R̂ 104/63). Under TMCMC,
**IFT reproduces (cross-run R̂ 1.000–1.001, β bounded) but M2 does NOT (R̂ 129, σ_d→∞ singularity).** =
physics-in-prior is more robust than physics-in-likelihood on the identical observable.

### Slide 6 — Fig B: the β thermometer
`figB_beta.png`. β collapses ~246× below nominal (consistent across 5 splits, bounded) = the twin quantitatively
reporting strong distrust of the coarse FEM; β well-identified here. The trust-side measure of the model-form
error the StatFEM run found qualitatively (4.4% freq error, ×2 amplitude).

### Slide 7 — Fig C: held-out FRF overlay
`figC_heldout_frf_overlay.png`. Measured |H| at an unseen sensor vs IFT band vs L5 band vs M2 band. Who places
the resonance, who widens honestly. M2 band flagged non-converged.

### Slide 8 — Fig D: discretization invariance (the IFT selling point)
`figD_discretization.png`. IFT θ/QOI/β posterior ≈ invariant to the analysis-grid density (re-fit at full/½/¼),
echoing the consistency-toy C2 result on real data.

### Slide 9 — Sensitivity (§11)
β-prior 3× wider/tighter: does the IFT-vs-L5 ranking survive? (out/sensitivity.json.) Report robust vs fragile.

### Slide 10 — Verdict + scope (the four pre-committed outcomes)
**ROBUSTNESS-WIN, with a clean partial sharpness WIN on the peak QOI** (checker-generated from the numbers).
- WIN? No — loses band-GRMS to L5 (coarse-FEM ceiling).
- ROBUSTNESS-WIN? **Yes** — converges + bounded + calibrated where M2 diverges.
- Peak QOI: IFT genuinely sharper AND better-calibrated than L5.
Scope/honesty: coarse-FEM ceiling binds; 1 hit/1 impact/split-only; moment approximation; NUTS→TMCMC
escalation. Recommendation: physics-in-prior (β thermometer) is the more robust field-likelihood twin; L5 remains
the sharpest band-GRMS twin; the lever for real sharpening is better data / the modal-feature observable, not the
inference construction.
