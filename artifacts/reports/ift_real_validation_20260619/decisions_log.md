# decisions_log.md — IFT real-validation study (lead-as-runner)

Workspace: `artifacts/reports/ift_real_validation_20260619/`
Created: 2026-06-19. Lead executing as runner (Card: IFT vs StatFEM apples-to-apples on real ShockSat).

## Re-grounding (§0, 2026-06-19)
- GOAL: stand up a faithful Information-Field-Theory (IFT) twin — physics in the PRIOR with a learned
  inverse-temperature β (trust thermometer) — and score it apples-to-apples vs our StatFEM arms (L5 working
  twin, M2 whole-FRF field arm, optionally L8 Beck) on the REAL ShockSat held-out-sensor QOI.
- LAST DECISION (from the StatFEM run, memory.md D8–D11): the whole-FRF magnitude likelihood is intrinsically
  multimodal/near-singular under real model-form error (NUTS R̂ 104, TMCMC R̂ 129 — M2 FAILS); the modal-feature
  L5 arm CONVERGES (R̂ 1.0015) and gives calibrated-but-wide held-out QOI; the coarse FEM is the binding ceiling.
- NEXT ACTION: build + validate the IFT arm (incl. β) on one split, then the ≥25-split apples-to-apples scorecard.
- OPEN AMBIGUITIES: see D1 (observable/marginalization), D2 (β prior), D3 (non-converged-arm rule) — RESOLVED below.

## Sources read before coding (§0)
- `AGENTS.md` (all gates), this runner prompt.
- StatFEM run `statfem_real_validation_20260617/`: `packet.md`, `phase2_heldout_sensor_qoi_summary.md`,
  `code/{core,score,realfrf,real_arms,heldout_qoi,mc_heldout,modal_feature,tmcmc}.py`.
- Consistency toy `statfem_consistency_toy_20260616/code/nuts_marg.py` (the M-ift construction).

## Verified facts (existence / numbers) — `out/` provenance
- `.venv_nuts` exists (py3.9, numpyro/jax x64). Sibling deps that `realfrf.py` reads via `WS.parent`:
  `statfem_shocksat_eval_20260616/data/V_keep.npy` (256 MB) and `shocksat_fem_modal_twin_20260609/fem_model.npz`
  both present → copied `realfrf.py` resolves unmodified. `measured_frf_cache.npz` (263 MB) present → the
  single-impact measured FRF is reused from cache; the 256 MB raw `.mat` is NOT reprocessed.
- StatFEM L5 baseline (1 split, seed 0, from `phase2_heldout_sensor_qoi_summary.md`): θ+QOI-disc PEAK
  coverage 0.91 / z_std 1.03 / interval 1.44e3 / CRPS 114 / logpd −6.3 / width 34 dB; BAND coverage 0.91 /
  z_std 0.79 / interval 3.6e3. Calibration converged R̂ 1.0015, ESS 1800, 0 div; σ_w2≈4.4%; gain c̄≈6.23
  (×508); σ_QOI≈×2.7. 80 DR-eligible channels (DR≥30), 48 obs / 32 held-out at seed 0.
- StatFEM M2 whole-FRF: NON-CONVERGED (NUTS R̂ 104–115, ESS 2, 0 div = multimodal; TMCMC R̂ 129, σ_d→7.4
  "variance→∞" singularity). This is the field arm IFT is contrasted against.
- L5 ≥25-split MC already computed in the StatFEM run (`out/mc_summary.json`); we re-run L5 in THIS workspace
  on the identical seeds for byte-identical splits.

---

## D0 (HUMAN DECISION, Andrew, 2026-06-19) — the load-bearing call
Lead flagged (review of the DRAFT prompt §2): the prompt claimed the field `u` marginalizes out EXACTLY because
it is Gaussian given (θ,β), but the headline observable is `log|H|`, a NONLINEAR function of `u` (magnitude of a
complex number, then log). For a complex-Gaussian field the marginal of `log|H|` is log-Rician, NOT Gaussian, so
"exact marginalization" is FALSE for this observable. Fork raised: (a) switch to a linear-in-u observable
(complex H) to keep the algebra exact but lose the same-observable apples-to-apples; or (b) keep `log|H|` and use
a documented approximation.

**ANDREW'S DECISION (verbatim intent):** "keep the headline arm on the same log|H| observable using a documented
log-magnitude moment approximation, so the comparison remains honest instead of pretending the algebra is exact
where it is not. fix the issues and run it yourself."

CONSEQUENCE (durable for this study): the IFT headline arm uses the SAME `log|H|` observable as StatFEM M2
(apples-to-apples preserved). The field is marginalized by a **first-two-moments (delta-method / high-SNR)
Gaussian approximation of the log-Rician**, labeled honestly as an approximation everywhere (method_ift.md,
figures, checker). Lead executes as runner (no separate runner spawned).

## D1 (RESOLVED by D0) — the moment-approximation construction
Field u∈ℂ⁷⁴; A(θ,ω)=(1+iη)K(θ)−ω²I, η=2ζ, ζ=0.01; unit force f at the drive DOF (same drive as StatFEM).
- Physics-informed PRIOR (PIFT/Hao-Bilionis): π(u|θ,β) ∝ exp(−(β/2)‖Au−f‖² − (τ0/2)‖u‖²) = CN(μ_u, Σ_u),
  precision Λ=βAᴴA+τ0I, mean μ_u→A⁻¹f = the deterministic FEM response as τ0→0. β = learned inverse-temperature
  = trust in physics.
- Observation H_j(ω) = −ω² obs_V[s_j,:]·u = w_jᴴu is LINEAR in u ⇒ H_j ~ CN(m_j, v_j), m_j = H_j^FEM(θ),
  v_j = w_jᴴΣ_u w_j. Diagonalize K=QΛQᵀ (the eigh already in the forward): AᴴA = Q·diag(D_k)·Qᵀ,
  D_k=(λ_k−ω²)²+(ηλ_k)²; v_j(ω)=ω⁴ Σ_k p_{j,k}²/(βD_k+τ0), p_j=obs_V[s_j]@Q. No extra solve; differentiable
  in θ and β.
- MOMENT APPROX (the documented deviation): log|H_j| with H_j~CN(m_j,v_j) is log-Rician. Approximate its
  field-marginal by a Gaussian matched to its first two moments:
  E[log|H_j|]≈log|m_j|=log|H_j^FEM(θ)|; Var[log|H_j|]≈ v_j/(2|m_j|²). Likelihood:
  **log|H_j^meas|(ω) ~ N( log|H_j^FEM(θ)| + c , σ_meas² + v_j(ω;θ,β)/(2|H_j^FEM(θ)|²) ).**
  σ_meas=0.15 (inherited). c = global units-gain nuisance (Normal(c0,1.5), same as StatFEM D4).
- Scope of the approximation (carried as a YELLOW everywhere): exact at high SNR K_j=|m_j|²/v_j≫1; biased in
  deep antiresonances (low SNR), where v_j/(2|m_j|²) is already large → likelihood near-uninformative → error
  sits where the term is downweighted. Data is DR-eligible (median peak/floor ~147×) so the informative peaks
  are high-SNR. We report per-(channel,freq) SNR and flag low-SNR bins.
- This makes IFT = a log|H| likelihood (SAME observable as M2) whose per-bin variance is PHYSICS-DERIVED and set
  by ONE learned trust scalar β, vs M2's free σ_d²×fixed-length Kronecker discrepancy. β→∞ ⇒ plain log|H|
  likelihood w/ only σ_meas (full physics trust); β→0 ⇒ graceful widening (no trust). Resonance singularity
  (D_k→(ηλ_k)²) = the physical "FRF most uncertain at resonances"; τ0 ridge keeps Σ_u finite. = the
  apples-to-apples test of WHERE the physics/trust lives (IFT prior vs M2 likelihood) on the IDENTICAL observable.

## D2 (RESOLVED) — β prior (the headline new knob)
β is dimensionful; its scale depends on the operator/units, so we center it on the forward model (NO data):
β* = value making median_{j,ω}[ v_j(θ=1,β)/(2|m_j(θ=1)|²) ] = σ_meas² (computed from the FEM forward at nominal
θ=1 over the eligible channels — a forward-model scaling constant, uses NO measured/held-out data). Default
prior: **log β ~ Normal(log β*, 2.0)** (≈1.7 decades each way; matches the consistency-toy log-sd). Reported as
the model-form-error thermometer + identifiability (toy found β weakly identified above a threshold → test on
real data). SENSITIVITY GATE (§11): prior sd ×{0.33, 3} and center shift; verdict must survive or be flagged
fragile.

## D3 (RESOLVED) — non-converged-arm rule for the scorecard (Fig A / checker)
Any arm failing the all-variable convergence gate (R̂≤1.05, ESS≥200, div<2%, **β included**) on a split is NOT a
trustworthy score: it is drawn flagged (worst-case R̂/ESS annotated, "non-converged" style) and EXCLUDED from the
headline median. M2 is EXPECTED non-converged (StatFEM D7/D10) → its divergence IS the comparison result (the
ROBUSTNESS axis: physics-in-prior converges where physics-in-likelihood diverges), never a per-split QOI win.
The checker encodes this: a non-converged arm presented as a converged score = RED.

## D4 (RESOLVED) — apples-to-apples reuse & provenance
COPY byte-identical into this workspace and sha256-verify (apples-to-apples provenance check): `core.py`,
`score.py`, `realfrf.py` (same forward), plus the StatFEM baselines `heldout_qoi.py`, `mc_heldout.py`,
`modal_feature.py`, `real_arms.py`, `tmcmc.py`, and the data (`reduced_blocks.npz`, `obs_dofs.npy`,
`keep_dofs.npy`, `channel_map.csv`, `groups.json`, `sensor_coords.npz`, `measured_frf_cache.npz`). V_keep.npy /
fem_model.npz are referenced read-only from siblings (recorded in the manifest, not copied). Splits reuse the
EXACT `heldout_qoi.run` RNG (DR_MIN=30, obs_frac=0.6, `np.random.default_rng(seed).permutation(elig)`) so IFT,
L5, M2 share byte-identical splits per seed. The StatFEM run is NEVER edited in place. The scorer is `score.py`
UNCHANGED; the new IFT logic lives only in new files (`ift_arm.py`).

## D5 (RESOLVED) — θ scope for fairness
θ ~ LogNormal(0,0.25) on 9 groups (match StatFEM); comparison restricted to the 4 identifiable groups
(bottom_box/top_box/plates/cross_beam per the FIM/strain-energy gate) for fairness, with full-9 as a sensitivity.

---

## Pre-committed verdict rule (§5; written BEFORE running — do not engineer a win)
Headline = held-out peak-|H| + band-GRMS PROPER scores (interval/CRPS/logpd), median over ≥25 identical splits,
with calibration (coverage, z_std) and all-variable convergence (incl. β) as gates. Outcomes (ALL valid):
- WIN: IFT converges (incl. β) AND beats L5 on headline proper scores at equal-or-better calibration.
- ROBUSTNESS-WIN: IFT does not beat L5 but AVOIDS the M2 whole-FRF failure — converges + widens gracefully
  (β shrinks) where M2 diverged ⇒ physics-in-prior more robust than physics-in-likelihood on the same observable.
- TIE: IFT ≈ L5 within split-to-split spread ⇒ competitive, not better here.
- HONEST NEGATIVE: IFT also hits the coarse-FEM wall (non-converge, or β collapses to a wide regression no
  better than L5+disc) ⇒ physics-in-prior does not rescue a coarse FEM either.
Framing carried up front (honest): the StatFEM run established the coarse FEM as the binding ceiling, so a
SHARPNESS WIN is a-priori unlikely; the live question is robustness/calibration/honesty (IFT prior vs M2
likelihood) on the identical field observable. The verdict STRING is generated from the numbers by `check.py`.

## D6 (FINDING + pre-authorized escalation, 2026-06-19) — IFT-under-NUTS hits the whole-FRF multimodality wall
The full 4-chain seed-0 convergence probe (`out/ift_cells/ift_seed00.json`) is **NON-CONVERGED**: max R̂ 264.9,
ESS 2, **0 divergences** (per-var: log_theta 264.9, log_beta 21.9, gain 12.2). 0 divergences = MULTIMODALITY
(chains stuck in separated basins), NOT bad geometry — the SAME pattern the StatFEM whole-FRF M2 arm showed
(NUTS R̂ 104; D7/D8). ROOT CAUSE: the IFT moment-approx likelihood MEAN is still the oscillatory FEM log|H(θ)|,
which many θ fit (the project's recurring whole-FRF magnitude multimodality) — so putting the physics in the
PRIOR with β does NOT, by itself, cure the θ-multimodality. KEY DIFFERENCE from M2 (the potential robustness
edge): β COLLAPSED to 0.17 vs β*≈42.8 (data wants lower physics-trust → wider) but stayed **bounded** — NO
σ_d-style "variance→∞" runaway (M2's σ_d→7–9.8 singularity). The non-converged NUTS predictive was
calibrated-but-very-wide (peak cover 0.94 / interval 8.68e3; band cover 1.0 / interval 4.05e6) and did NOT
explode to M2's ~1e17.
DECISION (pre-authorized by the card §2/§5 and StatFEM D9/D10 — NUTS→TMCMC on multimodality; NOT a durable
sampler-standard change): escalate the whole-FRF IFT arm to **TMCMC** (the multimodal-capable sampler, copied
byte-identical `tmcmc.py`, bimodal self-test validated). The decision-relevant test: does IFT-TMCMC give a
REPRODUCIBLE (cross-run-converged) multimodal posterior with BOUNDED β + calibrated held-out QOI — where
M2-TMCMC did NOT (StatFEM cross-run R̂ 129 from the σ_d singularity)? If yes → ROBUSTNESS-WIN (physics-in-prior
more robust than physics-in-likelihood on the same observable); if IFT-TMCMC is also useless → HONEST-NEGATIVE.
The L5 modal-feature arm (a DIFFERENT, unimodal observable) remains the converged 25-split sharpness bar.
COMPUTE NOTE: TMCMC is ~30–60 min/split → a 25-split IFT-TMCMC sweep is 12–25 h. So IFT-TMCMC (and M2-TMCMC) are
characterized on a LABELED SUBSET (the robustness/convergence axis), while L5 carries the full ≥25-split
sharpness distribution. Same treatment the StatFEM run gave its non-converged whole-FRF arms.

## Running log
- 2026-06-19: workspace + D0 + design D1–D5; copied 15 assets byte-identical + manifest (provenance GREEN);
  method_ift / priority_deliverables / question_framing / assumptions_ledger written; `ift_arm.py`
  (smoke-verified); immutable `check.py` (baseline RED, provenance GREEN, exits non-zero); `run_sweep.py`.
- 2026-06-19: seed-0 4-chain NUTS probe NON-CONVERGED (R̂ 264.9, multimodal, 0 div) → D6 finding + TMCMC
  escalation. `ift_tmcmc.py` built (IFT log-posterior into copied `tmcmc.py`).

## D7 (KEYSTONE FINDING, 2026-06-19) — IFT-TMCMC CONVERGES (reproducible) + bounded β where M2 diverged
`out/ift_tmcmc_cells/ift_tmcmc_seed00.json` (n=1500 × 4 independent runs, ~30 min): **cross-run R̂ 1.0008**
(all 6 dims 1.000–1.001), **ESS 1371**, log-evidence −18208.2 **± 0.22** (runs agree). So TMCMC reproducibly
characterizes the multimodal posterior → CONVERGED in the documented TMCMC sense (the SAME cross-run criterion
the StatFEM run used; AGENTS.md TMCMC escalation). **β_med 0.168 vs β* 42.8 = 255× below nominal = the
thermometer reads STRONG distrust of the coarse FEM**, but **bounded (no σ_d-style runaway)**. Held-out QOI:
PEAK cover 1.00 / interval 7331 / CRPS 77.8 / logpd −5.9; BAND cover 1.00 / interval 1.12e5 / CRPS 1697.
**vs L5 bar (seed0): PEAK cover 0.91 / interval 1.44e3 / CRPS 114; BAND cover 0.91 / interval 3.6e3.** READ:
IFT does NOT beat L5 on sharpness (wider, esp. band; over-covers) — consistent with the pre-committed
coarse-FEM ceiling — but is competitive on peak CRPS/logpd AND, crucially, **CONVERGES + stays bounded +
calibrated where M2 (same observable, physics-in-LIKELIHOOD) does NOT** (StatFEM D10: M2-TMCMC cross-run R̂ 129,
σ_d→7.4 "variance→∞", interval ~1e17). EMERGING VERDICT = **ROBUSTNESS-WIN** (§5): physics-in-prior with a
bounded learned β is more robust than physics-in-likelihood with a free σ_d, on the identical field observable;
the β thermometer quantifies (255×) the model-form error the StatFEM run found qualitatively (σ_w2 4.4%,
amplitude ×2). NOT YET FINAL — needs (a) IFT-TMCMC on seeds 1–4 to confirm convergence+calibration across splits
(not a seed-0 fluke), (b) M2 divergence + QOI explosion on the IDENTICAL splits (apples-to-apples), then the
checker generates the verdict from the numbers. L5 25-split sweep DONE (25 cells, all converged R̂ 1.004–1.006).
- 2026-06-19: IFT-TMCMC seeds 0–4 ALL converged (cross-run R̂ 1.000–1.001); L5 25-split done; M2 seed0 confirmed
  NON-CONVERGED on the identical split (R̂ 63.3, 0 div, multimodal — the divergence contrast). m2_arm.py =
  Kronecker-efficient M2 verified == dense real_arms.M2 to 2e-15. scorecard.json built (IFT 5 / L5 25 / M2 1).
  figA + figB rendered + QA-clean. figlib caption/overlap layout fixed.

## D8 (FINAL RESULTS + MACHINE BLOCKER, 2026-06-19)
**RESULTS ARE FINAL (out/scorecard.json):** IFT vs L5 medians — PEAK: interval 980/2026, CRPS 75.7/170, logpd
−6.05/−6.59, cover 0.97/0.87 → **IFT BEATS L5 on the peak QOI on all 3 proper scores + calibration.** BAND:
interval 1.12e5/5527, CRPS 1491/520 → L5 wins band (IFT over-wide from β-collapse). M2 (same observable,
physics-in-likelihood): NON-CONVERGED (R̂ 63 NUTS identical-split; R̂ 129 + σ_d→∞ + interval ~1e17 cited from
StatFEM TMCMC). IFT-TMCMC converges (R̂ 1.000–1.001) + β bounded, collapsed ~246× (well-identified, not weak).
**VERDICT (to be emitted by check.py from these numbers) = ROBUSTNESS-WIN + partial peak-QOI sharpness WIN.**
**BLOCKER:** the laptop is intermittently SLEEPING/stalling — it kills detached jobs AND hangs even trivial
matplotlib renders (aggregate + figA/figB ran during awake windows; figC/figD/fig_convergence/M2-extra splits
keep dying). NOT a code bug (figconv rewritten without the auto_set_column_width hang; a trivial 3-point render
also hangs → machine, not code). REMAINING (all gated on a STABLE/awake machine, all code written + resumable):
(1) render fig_convergence_table (code ready); (2) run `code/extras.py all` → frf_overlay.npz (figC) +
discretization.json (figD) + sensitivity.json (§11), each n=600×2run short; (3) render figC/figD; (4) `python
check.py` → should go non-RED (verdict generated); (5) build pptx from slides/deck_outline.md; (6) PROPOSE
project_log/runs rows (packet §10). TO FINISH: keep the machine awake (`caffeinate -dimsu`) and run
`bash run_all.sh` (resumable — skips the done IFT/L5/M2 cells, just runs extras + figures + checker). NO
durable-rule/checker/project_log/runs edits made (only this workspace + the lead memory CURRENT STATE block).
