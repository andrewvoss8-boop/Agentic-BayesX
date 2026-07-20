# Findings — ShockSat FULL-SPECTRUM FRF study (2026-07-14/15)

> ## ⚠ POST-REVIEW CORRECTION (dated addendum 2026-07-16; decisions D17 — supersedes the statuses below)
> The adversarial GPT-5.6 review (`artifacts/reports/shocksat_fullspec_review_gpt56_20260716/`, commit
> 9cad98c) found four decision-relevant defects the lead has VERIFIED and ACCEPTS. **The original package
> status is RED, not YELLOW** (undocumented gate misses per the Result Status Standard):
> 1. **Collector/checker defects (C8, RED):** the shipped `out/verdicts.json` S1/S2 numbers are **NaN**
>    (collector propagated a null fold; checker G09 validated key-presence, not finiteness), and the
>    arms-table **F row was invalidly set to the best arm = R (the random control)** instead of following
>    the pre-registered F rule. Corrected, finite numbers live in the ISOLATED REPAIR
>    `artifacts/reports/shocksat_full_spectrum_frf_repair_20260716/` (its own SHA-locked checker, frozen
>    inputs, F=C): **S1 not met (best D−A1 = +0.0497 < +0.05, though > 2×SE 0.0348); S2 not met
>    (D−R = −0.0017 ± 0.0094).** Use the repair's numbers, not this workspace's verdicts.json.
> 2. **Arm C exact aggregate is LEAKY and WITHDRAWN (C6, RED):** `rescore_freeze.py:78` applied fold-1's
>    shape MAP (trained on the other 3 drives) to all 4 folds → 3/4 exact fold scores saw their held-out
>    drive. The "C exact 0.157" number and the "C collapses on the exact basis" sentence are INVALID until
>    per-fold exact refits are run. (The SCREENING C scores used per-fold MAPs and remain leakage-safe.)
> 3. **"Multimodal, not under-identified" was over-claimed (C2):** a LOCAL Fisher information matrix cannot
>    establish global identification; separated θ modes agreeing in data space IS under-identification per
>    AGENTS.md. Corrected statement: the amplitude likelihood is locally stiff (all 9 FIM directions ≫ prior
>    precision, robust to step size), but global identification and posterior uncertainty are UNRESOLVED;
>    the MAP scores are deterministic optimizer results only.
> 4. **Softened claims:** "closes Gate W" → raw provenance + force health closed; independent PROCESSING
>    validation is not (same hits + same distiller ⇒ equality by construction). "S3/S4 not met" →
>    **CANNOT-VERIFY** (the net-CG port failed its reference reproduction; unresolved, not falsified).
>    FEM ceiling: the basis is credible to 639 Hz and the 500 Hz cap is sound, but 1250 Hz was infeasible
>    for THIS 16 GB ARPACK configuration, not in general; the filter summary's clamp count (19) was
>    inconsistent with the 345 modes actually cut at the edge.
> **What survives, per the repair:** S1, S2, S5 NOT MET (S5 fragile across prior widths: −0.3 at σ=0.25,
> +0.14/+0.37 at 0.15/0.40, rand10 absent); the data-phase provenance/force-health results; the 500 Hz cap;
> the D16 model-form limitation (verified: agent 0 genuine model-form edits; random 4; NEITHER track tested
> geometry/element formulation). "Remodeling impotence confirmed" and "global identifiability" claims were
> too strong and are withdrawn in favor of the corrected statements above.
> Everything below this box is the ORIGINAL text, preserved unmodified as the audit record.

Statuses copied from `out/verdicts.json` / `checker_report.json` (OVERALL: see checker; integrity gates
G01–G07,G10–G12 GREEN; G08 YELLOW = arm-B/C posteriors non-converged; the five pre-registered success
criteria S1–S5 all resolve **YELLOW = falsified / not-met — a valid, pre-registered outcome**). Nothing here
is stronger than the checker output. **Primary scoring is the EXACT-basis (enriched at θ_MAP) freeze
numbers; the θ=1 dev scores are SCREENING and were partly inflated (D22).**

## Headline
Every lever we have blamed for past ShockSat failures was given its fair shot at once — amplitude TRAINING
(first ever), measured damping, window-matched scoring, shape inference, an amplitude-compass remodeling
loop, and the extended >258 Hz band. **No lever cleanly beats the resolution-consistent baseline on held-out
per-channel FRF, the agent does not beat equal-budget random, and amplitude-inclusive selection does not
track held-out skill.** The remaining error is not reachable by any lever we own — now shown *with* amplitude
training and the full spectrum. Two levers help the 200–500 Hz band (amplitude-trained θ and remodel edits);
none clears the sub-200 shape wall at the pre-registered noise floor.

## The two hard limits this study established (both card-anticipated)
1. **Data reaches >1 kHz; the FEM twin does not.** All 5 drives were re-distilled wide-band from raw and
   validated **bit-identically** against the existing caches WITH live force (per-channel corr 1.000,
   median |Δlog₁₀|H|| 0.000, forces 207–1083 lbf) — this **closes the resolution run's Gate W** for every
   drive. But the inherited FEM has a dense local-mode forest (40 modes ≤260 Hz, ~215 ≤640); reaching the
   card's 1250 Hz target needs thousands of modes, infeasible on a 16 GB CPU (k=650 thrashed). The credible
   FEM ceiling is ~640 Hz (cross-validated), so by the card's 1.25× rule FRF scoring is capped at **500 Hz**
   and the 500–1000 Hz band the data supports is **FEM/compute-limited, not data-limited** (D8/D9/D11).
2. **The reduced-basis trap is real and it changed the conclusion.** θ_MAP is far from 1 (joints 0.47,
   cross_beam 1.46), so θ=1-basis scores are inflated (A0_wide fails the 0.3% spot check at 3.7%). The
   exact-at-θ_MAP re-evaluation (self-consistency 0.0000%) **overturned the screening result** — see H2.

## Per-H verdicts (numbers; statuses from the checker)

**H1 (the shape wall) — YELLOW (dented, not cleared).** Amplitude-trained shape inference (arm C) is the
first ShockSat shape inference TRAINED ON AMPLITUDES. On screening it improved held-out sub-200 by **+0.044**
(0.145→0.189) — a genuine dent in the wall. But it **fails the pre-registered S1 bar** (≥+0.05 AND ≥2×fold-SE;
the +Z(990) fold goes −0.086), and on the **exact basis C's lead collapses (0.189→0.157)**. No arm cleanly
clears the noise floor on sub-200. Amplitude-trained θ (arm B) does NOT help sub-200 (tied) but helps 200–500
(+0.11 screening / +0.16 exact) — it fixes mid-band amplitude *levels*, not sub-200 *shapes*. **The shape wall
stands, dented.** (S1 YELLOW/falsified.)

**H2 (remodeling impotence) — YELLOW (impotence CONFIRMED, now with the amplitude compass).** The remodel
loop ran 3 rounds with the amplitude-residual compass (the deliverable metric itself), 14 agent + 14 random
seeded queries, diagnosis→proposal links each round (`round_summary_r1/2/3.md`). On **screening** the agent
led random by +0.0138 (1.5×SE) — but the **exact-basis re-evaluation OVERTURNS it: agent D 0.163 vs random
R 0.165, −0.0017**; the vault (+XY) agrees (R 0.455 ≥ A1 0.451 ≥ D 0.438). The agent's screening lead was
reduced-basis inflation. **Agent ties random → H2 impotence confirmed**, reproducing the 2026-07-06 loop even
WITH a correlated compass — a stronger negative result. Round-3 stacking of winners *interfered* (prior-loop
lesson reproduced); the parametric-only control was among the very best. (S2 YELLOW/not-met.)

> **IMPORTANT SCOPE LIMITATION on the H2 verdict (added post-hoc; qualifies the claim).** This study's AGENT
> proposed **zero genuine model-form changes**. All 14 agent candidates (rounds 1–3) were `thickness` (8),
> `scale` (parametric-only, 1+2 in combos), or `split` (1+2 in combos) — physical-property or
> re-parametrization edits on the EXISTING mesh/topology; the winner `brackets_soft` was a pure thickness
> edit. The agent proposed **no** `refine` (mesh subdivision) and **no** `rbe2_soften` (rigid tie → compliant
> springs / connectivity change), because the amplitude compass kept pointing at stiffness/frequency-alignment
> residuals and I steered every proposal accordingly. So H2 here is really *"the agent tied random within a
> mostly-parametric edit space,"* NOT *"the agent tried true geometry/mesh/connectivity edits and they
> failed."* Two mitigations keep the H2 conclusion honest but not over-broad: (a) the RANDOM control DID
> sample genuine model-form changes — ~4 of its 14 candidates included `rbe2_soften` (×3) or `refine` (×2,
> one doing both) — and **none scored competitively**; (b) the 2026-07-06 true-remodel loop put `refine`,
> `rbe2_soften`, and region splits into BOTH tracks and found them null / random-tying. There is thus
> standing evidence that model-form edits don't move held-out FRF here, but it comes from the random track +
> the prior loop, not from this study's agent. Note also the mechanistic link to the reduced-basis trap
> (§H1/S2): thickness/scale/split live in/near the θ-parametrization span, which is exactly why the θ=1
> screening basis could inflate the agent's winner and the exact re-solve collapsed it; genuine model-form
> edits change the DOF space and cannot be inflated that way — but the agent never proposed one. (Counts:
> `out/query_log.jsonl` + `out/candidate_specs/`.)

**H3 (damping unusable at 2 Hz) — YELLOW.** Window-matched + measured survey ζ was the standard convention
for every arm (except A0). On the exact bases the window's sub-200 benefit over naive+1% shrank to ~noise
(A1 0.114 vs A0 0.112). Consistent with the resolution run: the processing/window is the lever, damping
refinement at 2 Hz is not. (Anchored to S1.)

**H4 (the unmeasured >200 Hz cluster) — YELLOW (measured, but QOI not validly reassessable).** The wide
re-distillation makes the 234–367 Hz cluster measured data: 11 cross-drive peaks (254/275/296/342/354/367…
Hz) match FEM frequencies to <0.5% (`extended_peaks.json`), and the tier table was updated (ledger A5b). BUT
the wide-package net-CG QOI band reimplementation **does not reproduce the delivered twin's calibrated bands**
(8.2×/3.66×/5.12× vs delivered 1.51×/2.30×/2.53× — a marginal-calibration difference in the reimplemented
statFEM F(k), NOT a real widening). So **S4 cannot be validly assessed** and the delivered net-CG twin stands
unchanged; no arm is demonstrated to improve or degrade it. (S3/S4 YELLOW; honest reimplementation caveat in
`netcg_results.json`.)

**H5 (selection scores are not validation) — YELLOW (CONFIRMED).** Amplitude-inclusive Laplace evidence vs
held-out sub-200 ranking over 11 candidates gives **Spearman −0.3** (σ_prior 0.25) — the selection score does
NOT track held-out skill (even slightly negative). Reproduces the composite bakeoff's evidence≠held-out
result, now with the amplitude-inclusive likelihood. (S5 YELLOW/not-met.)

## Samplers (honest status)
Arm B (amplitude-trained θ) and arm C (shape field) NUTS posteriors are **multimodal / non-converged**
(arm B R-hat 29–360, ESS≈2; arm C fold-1 R-hat 13.95). The required identifiability analysis
(`identifiability.json`, sampler-independent) shows this is **multimodality, not under-identification**: at
the realized 0.73 dex model-form-discrepancy floor all 9 θ combinations clear the prior precision (FIM
1641–3.6e6) — log|H| has huge near-resonance gradients and many θ align different resonances comparably. This
is the ridged/multimodal regime the compute protocol names for TMCMC. Per the AGENTS Sampler Decision, the
posteriors are reported YELLOW (not-trustworthy, worst R-hat/ESS on the figures) and the arms are scored at
labeled deterministic multi-start MAPs. TMCMC/GPU not used (compute protocol: un-validated multimodal twin).

## Arms × bands table (exact basis; `out/arms_bands_table.json`)
| arm | sub-200 (exact) | 200–500 (exact) | 500–ceiling |
|---|---|---|---|
| A0 | 0.112 | 0.050 | not certified (FEM ≤640 Hz) |
| A1 (baseline) | 0.114 | 0.033 | not certified |
| B (amp-θ) | 0.154 | 0.197 | not certified |
| C (shape) | 0.157 | 0.022 | not certified |
| D (agent) | 0.163 | 0.188 | not certified |
| R (random) | 0.165 | 0.188 | not certified |
(θ=1 SCREENING sub-200: A0 .131, A1 .145, B .142, C .189, D .179, R .166 — partly inflated, D22.)

## What would change these conclusions
A machine that can eigensolve the inherited FEM to ~1250 Hz would let the >500 Hz amplitude data (already in
hand, validated) actually test the twin. A validated net-CG QOI port to the wide package would make S3/S4
assessable. Neither changes H2 (agent ties random) or H5 (selection ≠ held-out), which are basis-robust.

## Deliverable
Unchanged: the inherited FEM + statFEM honest-band twin (netcg thread) remains the ShockSat twin. Amplitude
training, shape inference, and agentic remodeling did not beat it at the pre-registered bars. This closes the
"amplitude training + agentic remodeling will crack this" hypothesis — exactly the claim Andrew wanted
challenged before the lab commits to it.
