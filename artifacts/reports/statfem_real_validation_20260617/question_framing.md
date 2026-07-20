# question_framing.md — Card A (Question and Decision Gate)

## Engineering decision being supported
Can a coarse FEM digital twin of the ShockSat primary structure, calibrated with the orthogonal-Schneider
StatFEM discrepancy, give a vibration engineer **trustworthy** held-out-sensor QOI predictions (peak
accelerance, band-GRMS) — intervals that are simultaneously **calibrated** (cover the truth) and **sharp**
(narrow enough to act on) — under the genuine FEM-vs-real model-form error of an actual test article? And
where does it break? The downstream use is a robust live apparent-mass / interface-environment twin
(notes/project_vision §6.1) that widens (and says so) when the model is wrong rather than reporting a confident
wrong number.

## Objective function / success metric
- **Headline = a proper scoring rule** (interval/Winkler score, CRPS, log predictive density) on held-out-channel
  QOIs, which jointly rewards calibration AND sharpness so a method cannot win by inflating bands. Coverage and
  band width are SECONDARY diagnostics shown for the tradeoff.
- Whole-FRF score is PEAK-WEIGHTED and coherence-weighted (missing a peak ≫ missing a valley).
- Secondary: θ recovery vs the identifiable subspace; sensor/impact-placement payoff (which configs help/hurt).

## What the search / calibration is allowed to choose
- The 9 group stiffness multipliers θ_g (or a downselected subset — the parameter-count study), the discrepancy
  scale σ_d, and (in the parameter-count study) how many θ to update and how to pool them.
- The Monte-Carlo design randomizes impact location × observed/held-out split × hit/realization.

## What remains human judgment
- The observable resolution (D1) — matched-path real FRF vs modal-synthesis fallback (SURFACED, §14).
- Any scoring weighting that materially changes the verdict (peak-weighting, coherence-weighting choices).
- Whether a YELLOW result (e.g. partial θ recovery, a not-yet-converged arm, one-hit real-FRF) is acceptable
  for the intended use — reported, not decided by the runner.
- The final verdict's engineering consequence (is the twin good enough to set a vibe-test environment?).

## What would make this the WRONG question
- If the real data cannot exercise genuine model-form error in the QOI band (it can — single-impact reprocess
  shows real resonances aligned with the .ash modes to ~2 Hz; D1).
- If "calibrated + sharp on held-out QOI" is not what the engineer needs — e.g. if they need the *physical*
  parameter values, not the QOI; the Brynjarsdottir–O'Hagan caveat is that QOI can stay calibrated while
  physical-parameter ID degrades to prior. We report both and never claim recovered true physics of a coarse model.
- If coverage were treated as the headline — it is explicitly NOT (a wide-band arm can fake coverage); the
  proper-score suite + the wide-band-doesn't-win demonstration guard against this.
- If the discrepancy were placed in the stiffness (θ) space — that double-counts and biases θ; the orthogonal
  projection (Plumlee / Brynjarsdottir–O'Hagan) is precisely the method under validation.
