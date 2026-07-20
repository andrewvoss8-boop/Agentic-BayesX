# priority_deliverables.md — Card A: validate orthogonal-Schneider StatFEM twin on REAL ShockSat

Restating the task card's PRIORITY asks in my own words, my interpretation, and where each will be delivered.
A priority with no delivered artifact is a failure; an "assumed" interpretation without confirmation is a warning.

| # | Priority ask (card §3) | My interpretation | Delivered in (planned) | Status |
|---|---|---|---|---|
| 1 | Real-data held-out evaluation with the orthogonal-Schneider twin (+ naive baseline), every NUTS arm gate-converged or labeled not-yet-converged | Calibrate θ (9 groups) on observed channels of the REAL observable; predict held-out-channel QOIs; M3 orthogonal-Schneider is the method under validation, M0 naive is the contrast; all arms pass the NUTS gate (R̂≤1.05, ESS≥200, div<2% over ALL vars) or are explicitly labeled YELLOW not-yet-converged | `out/cell_*/`, `packet.md`, `checker_report.json` | PENDING (gated on D1 observable) |
| 2 | Sharpness-aware scoring suite for every arm — headline is a PROPER SCORE, not coverage | Per arm/QOI: interval(Winkler) score + CRPS + log predictive density as HEADLINE; PIT + z-scores; coverage+width only SECONDARY; whole-FRF score PEAK-WEIGHTED + coherence-weighted; PLUS a demo that a wide-band config wins coverage but LOSES the proper score | `code/score.py`, `out/scores_*.json`, scoring-suite figure | PENDING |
| 3 | Parameter-count selection study | Compare all-9 vs FIM-downselection vs evidence-based (WAIC/LOO/marginal-lik) vs hierarchical partial-pooling, scored on held-out QOI + θ recovery; tie to strain-energy/FIM gate before any per-parameter claim | `code/paramcount.py`, `out/paramcount.json`, figure | PENDING |
| 4 | Monte-Carlo distributions over impact locations × train/test splits (× hits/realizations) | ≥25–50 configs (reduce + label if needed); scores reported as DISTRIBUTIONS; surface which impact/sensor choices help/hurt (sensor-placement payoff); resumable per config | `code/run_mc.py`, `out/mc_*/`, MC-distribution figure | PENDING |
| 5 | Error-vs-participation FEM graphic (Idea 3 + Idea 1) | Non-spatial scatter, one equal-weight dot per property group: x=modal strain-energy participation %, y=inferred discrepancy/error magnitude, color/size=error×participation; paired equal-weight structure locator; area-disclaimer on any retained spatial map | `code/fig_error_participation.py`, figure | PENDING |
| 6 | Immutable `check.py`, `run_all.sh`, `runtime.json`, tufte packet + actual editable `.pptx` (gated on non-RED) | Checker written FIRST; one-command replay; per-phase runtime; tufte-linted/image-QA'd/overlap-audited packet; python-pptx deck for Ilias | `check.py`, `run_all.sh`, `runtime.json`, `packet.md`, `slides/*.pptx` | PENDING |

## Acceptance criteria (from card §9 gates, restated)
- NUTS gate: ≥4 chains, dense mass, capped tree depth (D12); max R̂≤1.05, min ESS≥200, div-frac<2% over ALL vars.
- Modal/Eigenproblem Identifiability Gate: strain energy + FIM eigen-view at the REALIZED discrepancy floor +
  finite perturbation — BEFORE any per-parameter identifiable/not claim.
- Reference/Standards: NASA modal numbers; statFEM/Plumlee/KOH.
- New GREEN-required: orthogonal-Schneider twin + sharpness suite; wide-band-doesn't-win demo; parameter-count
  comparison; MC distributions ≥25 configs; error-vs-participation figure; matched-path FRF observable validated
  (peak alignment) OR modal-synthesis fallback documented (D1).
- RED triggers: undocumented non-convergence; a score/claim without numbers; invalid SOL111/mismatched-path FRF
  likelihood used; coupled tray used; a scaffold edited in place; missing/fabricated figure; tufte/image-QA/overlap fail.

## Ambiguous / underspecified asks flagged for Andrew (Clarification Gate)
- **Observable resolution (#1 decision):** SURFACED in `decisions_log.md` D1 — matched-path real FRF vs
  modal-synthesis fallback. Recommendation = documented hybrid. **Building is paused until Andrew chooses.**
- **MC config count:** card asks ≥25–50; I will target 25 first (resumable), expand if runtime allows; the
  reduction will be labeled per §11.
- **"Real model-form error" definition** depends on the observable: modal observable → FEM-vs-measured-mode
  (freq+shape) error; real-FRF observable → FEM-vs-measured-|H1| amplitude error. Both documented; verdict
  reported separately so neither hides the other.
