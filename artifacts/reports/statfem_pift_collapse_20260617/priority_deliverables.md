# priority_deliverables.md — Card B (PIFT collapse / orthogonal-Schneider cure)

Restated in my own words (Priority Deliverables & Clarification Gate). Each priority + interpretation + where it
will be delivered. A priority with no delivered artifact = failure; an "assumed" interpretation = warning.

| # | Priority ask (card §4) | My interpretation | Where delivered | Status |
|---|---|---|---|---|
| 1 | The **collapse sweep** | For a geometric ladder of observation density N (# FRF frequency points, then # sensors, then modal-route # modes), per arm (naive M0 / iid M1 / orthogonal-Schneider M3; M2 optional), record posterior **width of σ_d** and of θ, and a sharpness-aware **held-out score** (interval/CRPS + coverage + width + PIT; peak- & coherence-weighted). Every NUTS run gate-converged OR labeled not-yet-converged (per-N). | `out/sweep_*.json`, `figures/fig_collapse_curves.png` | PENDING |
| 2 | **Effective-sample-size accounting** | Per arm, the effective # of independent observations the likelihood implies: iid → grows ∝ N; correlated (M3) → trace-based DOF of the whitened design = tr(C)²/tr(C²)-style / N over correlation-length-in-points → SATURATES. Explains WHY iid collapses and M3 plateaus. | `out/ess_accounting.json`, `figures/fig_ess_vs_N.png` | PENDING |
| 3 | **The verdict** | Does OUR StatFEM collapse (iid/naive signature: σ_d & θ shrink ~monotonically with N while held-out score DEGRADES)? Does orthogonal-Schneider CURE it (σ_d & score PLATEAU past the correlation scale)? Stated with the **PIFT quote** + the explicit **analogy mapping** (collocation↔observation, fictitious-variance↔σ_meas/σ_d), where it holds/breaks. Verdict reported EITHER WAY; not pre-decided. | `packet.md` verdict section, `analogy_mapping.md` | PENDING (mapping DRAFTED, awaiting sign-off) |
| 4 | Immutable `check.py`, `run_all.sh`, `runtime.json`, tufte packet + an **actual editable `.pptx`** (gated on non-RED) | check.py written FIRST (before results); one-command replay `bash run_all.sh`; per-phase timing; every figure tufte-linted + image-QA + overlap-audited; deck claims trace to checker numbers. | this workspace root + `slides/` | PENDING |

## Acceptance (new GREEN-required gates, card §6)
- Collapse sweep reported WITH NUMBERS (σ_d-width & held-out score vs N, per arm).
- Effective-sample-size accounting present.
- Collapse-vs-plateau verdict stated with the PIFT quote + analogy mapping.
- Synthetic controlled cross-check (known model-form error; iid collapses to the WRONG function as N→∞ while
  orthogonal-Schneider keeps honest uncertainty).
- NUTS gate per N-cell (≥4 chains, dense mass, depth cap per D12; max R-hat ≤1.05, min ESS ≥200, div-frac <2%,
  ALL variables) — convergence may itself change along the ladder; report per N.
- Identifiability gate (strain energy + FIM eigen-view at the realized discrepancy floor).
- Reference gate (PIFT/IFT + statFEM/Plumlee/KOH).

## Scoring-suite anti-foolability note (from the companion `lenmis` lesson)
The companion's synthetic `lenmis` arm scored coverage 1.00 purely by widening σ_d toward the prior (a wide-band
FALSE win). The held-out score here MUST penalize width (sharpness-aware: interval score / CRPS + PIT, not
coverage alone), so a plateau cannot be faked by an arm that simply inflates its bands.

## Phasing (card §8): P1 analogy + low/high-N probe → P2 synthetic collapse sweep → P3 real matched-path sweep
→ P4 ESS accounting + packet + .pptx. `runtime.json` with per-phase timing. Detached + resumable.
