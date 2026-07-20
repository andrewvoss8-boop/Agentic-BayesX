# question_framing.md — Card B (PIFT collapse / orthogonal-Schneider cure)

## Engineering decision being supported
Whether a StatFEM digital twin's UNCERTAINTY can be TRUSTED as you feed it more observations. Concretely: if we
add frequency points / sensors to the FRF likelihood, does the twin's posterior tighten honestly, or does it
become **confidently wrong by adding data** (the PIFT posterior collapse)? And does a correlated
(orthogonal-Schneider) discrepancy prevent that?

## Objective function / success metric
Two posterior-uncertainty trends vs observation density N (= the PIFT collocation-point count):
1. **σ_d posterior width** (uncertainty about the model-form discrepancy scale) and **identified-θ width**.
2. **Held-out QOI score** — sharpness-aware (interval score / CRPS in dB + coverage + width + PIT), so a "win"
   cannot be faked by widening bands (the companion `lenmis` lesson).
- **Collapse signature** (iid/naive): σ_d-width & θ-width shrink ~monotonically with N while the held-out score
  does NOT improve like the correlated arm (over-tight + biased).
- **Plateau/cure signature** (orthogonal-Schneider): σ_d-width & held-out score plateau past the correlation
  scale (finite effective sample size).

## What the analysis is allowed to choose
- Nothing about the verdict. The N-ladder, ESS accounting, and trend ratios COMPUTE the collapse/cure booleans
  from numbers; they are reported whichever way they fall (card §9).

## What remains human judgment
- The PIFT→StatFEM analogy mapping (where it holds/breaks) — Andrew signed off (`analogy_mapping.md`).
- The observable resolution (synthetic-first, then real matched-path) — Andrew signed off.
- Whether the result warrants the durable claim "correlated discrepancy cures the StatFEM collapse" (lead +
  Andrew + Ilias; the runner only SURFACES the numbers).

## What would make this the WRONG question
- If our StatFEM never reaches the asymptotic regime in the achievable N (the band is physically finite, so
  "N→∞" is densification, not domain growth — analogy caveat #2). Then "collapse" is a finite-N statement and we
  must say so, not extrapolate to a limit we cannot reach.
- If the dominant failure at the N we can run is UNDER-identification (multimodal low-N posterior), not collapse
  — a different pathology. (We observe exactly this at low N; the collapse claim is about the HIGH-N tightening.)
- If the QOI's own grid-resolution dependence (band-GRMS rises as the grid resolves sharp peaks) is mistaken for
  a posterior effect — we evaluate truth and prediction on the SAME per-cell grid and lead with the
  grid-independent σ_d/θ widths to avoid this confound.
