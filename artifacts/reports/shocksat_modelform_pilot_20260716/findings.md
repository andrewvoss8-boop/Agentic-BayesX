# Findings — ShockSat MODEL-FORM PILOT (Card C, 2026-07-16/17)

Status source of truth: `checker_report.json` (immutable checker `c26489ae…`). Full detail: `packet.md`.
All scores are EXACT-basis held-out sub-200 Hz per-channel FRF correlation (P1′); A1 baseline +0.1137;
paired-fold SE convention throughout. NO sampler; NO vault read.

1. **HQ2 CONFIRMED — genuine model-form edits DO move held-out FRF here, the first positive result of
   the remodeling arc.** All four genuine classes beat the A1 baseline by ≥2×paired-fold-SE at their
   best (element formulation +0.0711±0.0120; connectivity +0.0641±0.0273; mesh density +0.0635±0.0214;
   geometry +0.0597±0.0116), and the pre-registered selection-noise control agrees: the class MEANS
   over all 12 candidates are also positive at 1.6–2.9×SE. This overturns the standing "model-form
   edits don't move held-out FRF" reading that rested on the random track + the 2026-07-06 loop —
   those tracks had simply never tried element formulation or geometry (study D16 / review C7).

2. **The single best edit ever scored on this structure is a ZERO-COST formulation change.** A random
   draw (`mr2_elem5`): bending-formulation stiffening (bend_ratio ×1.23, transverse shear to the
   Kirchhoff limit) on the center box + cross-beam plate + bracket plate → +0.1848 (vs best-ever
   property edit +0.1765) with 0 added DOF, 0 added mass, 0.8× solve time. Physically it points the
   same direction as the long-standing cross-beam stiffening lever, but through the element
   formulation, at no model-complexity cost.

3. **HQ1 FALSIFIED — the amplitude-compass agent STILL does not beat seeded random, now with genuine
   model-form freedom and enforced stratification.** Best-vs-best −0.0077±0.0177; track means
   +0.0028±0.0056; per-fold signs flip. This closes the D16 gap in the strongest form the review asked
   for: the impotence result is now about the GUIDANCE, not the action space. The mechanism is visible:
   the agent's round means DECLINED (+0.157→+0.150→+0.142) because every attempt to extend its own
   winners backfired (three hill-climbing extensions lost 0.05–0.07 each), while random's stayed flat —
   the diagnosis points at real regions (its Bottom/Top-Box shape-defect signature is stable across
   models) but carries no within-region ranking information at this noise level.

4. **Complexity separates the wins.** Formulation/geometry/connectivity gains come at zero DOF;
   the equally-reliable mesh-refinement gains (the most fold-stable class: agent mean +0.169, sd 0.006)
   cost +8–33 % DOF and up to 3.5× solve time. No candidate tripped the pre-registered not-worth-it
   rule, but a delivery decision should prefer the zero-DOF classes.

5. **The wall stands.** Even +0.185 is far below the ≈0.34 deterministic-update median and ≈0.70
   measured-shapes reference: model-form freedom moves held-out FRF by ≈+0.06–0.07 over A1 — real,
   several-σ, cheap — but does not crack the sub-200 shape wall. The next dollar question is now
   sharper: a formulation/geometry calibration study (deliberate, not random) is justified for the
   first time; blind agentic search over the same space is not.

6. **Byproduct negatives, gate-caught:** refining two randomly-chosen regions is a numerical no-op
   (max mode shift ≤0.0014 % — mesh-convergence evidence via the pre-registered liveness gate);
   single-leg RBE2 spiders are outside the RBE3 operator's domain (3 duds, singular by construction).
   Two new-operator V-gates failed on first run and were fixed pre-science (decisions_log D2) — the
   V-gate discipline did its job.

7. **Finalist reinforcement (per-fold amplitude refits, no cross-fold reuse) STRENGTHENS both
   verdicts.** The formulation winner is the ONLY finalist robust to per-fold amplitude
   recalibration — it improves to +0.1954 (vs A1 +0.0817±0.0296, 2.8×SE) — while the agent's two
   finalists collapse (mesh → +0.013±0.049; property → −0.204±0.223: amplitude refits overfit the
   train drives), and the finalist S-test has random beating the agent by 3.1×SE. Third program-level
   confirmation that amplitude-trained θ transfers worse than survey-fit θ — except for the zero-DOF
   formulation edit, whose gain holds under both conventions.

Checker: **OVERALL GREEN 12G/0Y/0R (integrity/conduct only), exit 0** — with the science block
printed alongside: HQ1 NOT MET, HQ2 MET. GREEN certifies the conduct (pre-registration, exact-basis
rule, V-gate ordering, no vault, no leakage, budgets, verdict consistency), never the outcome.
