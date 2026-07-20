# MODEL-FORM PILOT — human-review packet (Card C, run 2026-07-16/17)

Status source of truth: `checker_report.json` (immutable checker `c26489ae…`, SHA-locked BEFORE any
science, proven RED 0G/0Y/12R on the empty workspace). Nothing below is stronger than checker output.
Replay: `bash run_all.sh` (fully resumable; agent specs preserved verbatim in `out/pending_specs/`).

## 1. Method summary (first, per the Plot/Packet gate)
- **Question.** Two pre-registered falsifiable hypotheses (question_framing.md, verbatim from the card):
  **HQ1** — with stratified proposals across 5 edit classes at equal budget, does an amplitude-compass
  agent beat seeded random on held-out sub-200 Hz per-channel FRF correlation (P1′), all-exact-basis,
  ≥1×paired-fold-SE? **HQ2** — does ANY genuine model-form class (connectivity / mesh density /
  element formulation / geometry — NOT property scaling) beat the A1 baseline ≥1×paired-fold-SE?
- **Model form.** Inherited ShockSat shell FEM (67,683 nodes; 399,510 reduced DOF), 9 group stiffness
  scalings θ (log-normal prior σ=0.25), free-free, viscous modal damping from the measured survey
  (frequency-interpolated; band-median above 257.6 Hz), window-matched forward operator 𝒲.
- **Data usage.** WHOLE-curve log10|H1| per channel (not peak features) over 45–200 Hz (HQ band; the
  200–500 Hz band reported alongside), 4 hammer drives in leave-one-drive-out folds; coherence-masked
  (median ≥ 0.6); ~100–130 channels/drive; single test campaign (no build/test variability available).
  The 5th drive (+XY) is a vault: **never read** (runtime guard: 0 opens).
- **Deterministic likelihood objects; NO SAMPLER** (pre-registered; the study showed this amplitude
  posterior is multimodal/unresolved — a non-converged posterior per candidate adds nothing to model
  RANKING). θ per candidate = S0-form survey MAP (5 deterministic starts; fold-independent by
  construction). Finalists additionally get per-fold amplitude-trained MAPs (train drives only).
- **Scoring rule (the D22/D15 lesson, hard-encoded).** EVERY reported score is EXACT-basis: own-space
  k=200 eigensolve at θ=1 → multi-start θ_MAP → SECOND own-space solve at θ_MAP with θ folded in
  (self-consistency ≤1e-6 %) → score at θ=ones. No reduced-basis screening number exists anywhere in
  the outputs (checker G03 REDs on any key containing "screening").
- **Loop.** 3 rounds × 2 candidates/class × 5 classes × 2 tracks = 60 exact-scored candidates
  (agent: diagnosis→class→edit links in `out/round_summary_r*.md`; random: seeded menus,
  `out/seeds.json`). Duds replaced, never silently skipped (5 total, all with recorded reasons).
- **Validation chain.** New operators V-gated BEFORE any scored use (`out/vgate_*.json`, all PASS; two
  first-run failures fixed + documented, decisions_log D2). Pipeline reproduction: rebuilt the study's
  `wr2_rnd001` end-to-end → matches Card A's exact number to **3.5e-11** (bar 0.01).

## 2. THE CENTERPIECE — exact held-out sub-200 P1′ by class × track (A1 baseline = +0.1137)
Each cell: mean over its 6 candidates (sd) | best candidate. Best-vs-A1 = paired-fold delta of the
POOLED class best (n=12), the HQ2 quantity. All numbers exact-basis; complexity shown per the
pre-registered penalty rule (not-worth-it iff gain <1×SE AND ΔDOF>+10% — zero candidates tripped it,
but the DOF cost differences below are decision-relevant).

| class | AGENT mean (sd) \| best | RANDOM mean (sd) \| best | best-vs-A1 (pooled, ±SE) | HQ2 | mean ΔDOF |
|---|---|---|---|---|---|
| connectivity | +0.1321 (0.015) \| **+0.1445** | +0.1512 (0.031) \| **+0.1778** | **+0.0641 ± 0.0273** (2.3×SE) | **MET** | +0.1–0.2 % |
| mesh density | +0.1690 (0.006) \| **+0.1771** | +0.1656 (0.012) \| **+0.1766** | **+0.0635 ± 0.0214** (3.0×SE) | **MET** | **+8–16 %** |
| element formulation | +0.1459 (0.025) \| **+0.1630** | +0.1375 (0.033) \| **+0.1848** | **+0.0711 ± 0.0120** (5.9×SE) | **MET** | **0 %** |
| geometry | +0.1457 (0.023) \| **+0.1734** | +0.1303 (0.023) \| **+0.1629** | **+0.0597 ± 0.0116** (5.1×SE) | **MET** | 0 % |
| property control | +0.1554 (0.024) \| **+0.1765** | +0.1495 (0.011) \| **+0.1683** | +0.0629 ± 0.0203 (3.1×SE) | control | 0 % |

- **Selection-noise control (pre-registered):** the class MEANS vs A1 confirm the class-level signal —
  mesh +0.0536±0.0186, formulation +0.0280±0.0096, geometry +0.0244±0.0118, connectivity
  +0.0280±0.0176, property +0.0387±0.0203 (all ≥1.6×SE, mesh/formulation ≈3×SE). HQ2 is NOT a
  best-of-12 artifact.
- **Fold stability:** the four genuine-class bests are positive in 15/16 folds (one connectivity fold
  ≈0). The HQ1 primary delta flips sign across folds ([+,−,+,+]) — the stop-condition instability
  applies to the AGENT-vs-RANDOM comparison, not to the class-vs-A1 gains.

## 3. Verdicts (recomputed independently by checker G12)
- **HQ1 — FALSIFIED (NOT MET).** Primary (best-vs-best, paired folds): agent `ma3_mesh_covers`
  +0.1771 vs random `mr2_elem5` +0.1848 → Δ = **−0.0077 ± 0.0177**. Secondary (track means, 30 vs 30):
  +0.0028 ± 0.0056. The agent ties random under BOTH conventions — reproducing the study/loop
  impotence result, now WITH genuine model-form freedom and stratification. Mechanism visible in the
  round trajectory: the agent's round means DECLINED (r1 +0.157 → r2 +0.150 → r3 +0.142) because
  extending its own winners backfired every time (joint-offset extension +0.1734→+0.1061; wall
  softening 0.8→0.75 +0.1557→+0.0964; property perturbation +0.1765→+0.1080), while random stayed flat.
  The residual-field compass points at real regions but does not order candidates within them.
- **HQ2 — MET, by ALL FOUR genuine classes.** The strongest: **element formulation +0.0711 ± 0.0120
  (5.9×SE)** from `mr2_elem5` — bending-formulation stiffening (bend_ratio ×1.233 + Kirchhoff-limit
  transverse shear ts_t 5/6→5.0) on the center box (601), cross-beam plate (401), and bracket plate
  (302): a **zero-added-DOF, zero-added-mass, zero-topology-change** edit that beats every property
  edit ever scored on this structure (best property exact = +0.1765). Geometry (+0.0597±0.0116, a
  0.25 in bottom-box joint-interface offset) and connectivity (+0.0641±0.0273, joint softening) also
  clear the bar with zero DOF cost; mesh refinement clears it (+0.0635±0.0214) but at +8–33 % DOF and
  up to 3.5× solve time — the complexity table separates the cheap wins from the expensive one.
- **Caveats carried:** best-of-n selection noise (mitigated by the class-mean control above); the
  tested operator RANGES bound every claim (a null/positive is within-range only); single campaign,
  4 folds; sub-200 Hz band only (200–500 reported, no rule attached).

## 4. Finalist reinforcement test (per-fold amplitude refits; the C6 no-cross-fold-reuse standard)
Top-2 per track; per fold: θ refit on the 3 TRAIN drives only (5 deterministic starts, σ_e=0.5 dex,
lognormal prior σ=0.25 on θ_total) → fresh per-fold EXACT enrichment → held-out drive scored.
This is a REINFORCEMENT probe (pre-registered as such); the HQ verdicts stand on the main
fold-independent table.

| finalist | main exact | refit mean | refit vs A1 (±SE) | reading |
|---|---|---|---|---|
| `mr2_elem5` (random, formulation) | +0.1848 | **+0.1954** | **+0.0817 ± 0.0296** (2.8×SE) | **SURVIVES AND IMPROVES** — the winner's gain is robust to per-fold amplitude recalibration |
| `mr1_conn0` (random, connectivity) | +0.1778 | +0.1460 | +0.0323 ± 0.0155 (2.1×SE) | survives, reduced |
| `ma3_mesh_covers` (agent, mesh) | +0.1771 | +0.1270 | +0.0133 ± 0.0490 (0.3×SE) | collapses to noise under refit |
| `ma1_prop_tboxxbeam` (agent, property) | +0.1765 | −0.0903 | −0.2040 ± 0.2229 | BREAKS — amplitude refits overfit the train drives catastrophically for this candidate |

- **Finalist S-test (top-1 agent vs top-1 random, paired refit folds): −0.0684 ± 0.0218** — under the
  strictest treatment the random finalist beats the agent finalist by 3.1×SE. HQ1's null SHARPENS.
- **A program-level pattern confirmed a third time:** per-fold amplitude-TRAINED θ generalizes worse
  than the fold-independent survey-fit θ for 3 of 4 finalists (echoes the 2026-07-06 loop's
  "better survey-fit ⇒ worse held-out" cascade and the study's arm-B sub-200 result). The exception —
  and it is the important one — is the zero-DOF formulation winner, which is the only candidate whose
  gain is robust under BOTH θ conventions.

## 5. Honest limitations
- The FRF wall context stands: even the best candidate (+0.185) remains far below the ≈0.34
  deterministic-update median and ≈0.70 measured-shapes reference — model-form edits MOVE the score
  (HQ2) but do not crack the sub-200 shape wall.
- 3 of 5 duds were random RBE3 draws hitting single-leg spiders (singular by construction — an operator
  domain restriction, documented, not a physics failure); 2 were refines of regions where refinement is
  a numerical no-op (max mode shift ≤0.0014 % — fresh mesh-convergence evidence from the liveness gate).
- The checker's OVERALL is integrity/conduct ONLY; the science verdicts print in their own block
  (the Card-B D7 reporting-trap fix). Falsified HQ1 is a valid, pre-registered outcome.

## 6. Artifacts
`out/query_log.jsonl` (60 exact records) · `out/results_table.json` · `out/verdicts.json` ·
`out/complexity.json` · `out/finalists.json` · `out/vgate_*.json` (5, PASS) · `out/repro_check.json`
(3.5e-11) · `out/seeds.json` · `out/duds.jsonl` (5) · `out/round_summary_r{1,2,3}.md` ·
`out/diagnosis_mf_r{1,2,3}.json` · `out/vault_guard.json` (0 +XY opens) · `figures/` (6, scripted +
linted + QA'd) · `out/eigensolve_log.jsonl` (~130 logged solves) · `runtime.json` · `decisions_log.md`.
