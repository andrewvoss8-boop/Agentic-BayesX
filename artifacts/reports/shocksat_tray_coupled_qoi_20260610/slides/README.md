# Program deck — ShockSat × payload-tray coupled load study

**File:** `shocksat_program_deck.pptx` (14 slides, 16:9). Audiences: Prof. Mark
Girolami (StatFEM), Dr. Ilias Bilionis (SciML/UQ), Dr. Yunis (ShockSat).

Built by `code/make_deck.py` from `slides/figs/*.png` (built by
`code/make_deck_figs.py`, tufte-linted). Every number is read from `out/*`
artifacts — nothing is hand-typed into the figures. Rebuild: `bash run_all.sh`
(stage builds figs + gifs + deck) or `python3 code/make_deck.py`.

## Supplementary GIFs (in `gifs/` — deliberately NOT embedded in the pptx)
- `force_limiting_sweep.gif` — uncoupled vs coupled interface-force transfer as
  the mount stiffness sweeps the prior; the 7004C notch appears and moves.
- `mode_walk_qoi.gif` — chain modes walking through the input band and the
  (non-monotonic) peak-Fz QOI vs mount stiffness.
- `multimodality.gif` — the overnight NUTS chains agreeing in DATA space while
  scattering in PARAMETER space = the honest under-identification negative.

## Honesty status
The ShockSat PRIMARY twin is validated against real NASA test modes. The
COUPLED tray QOI is HYPOTHETICAL (methods demo, no tray was ever mounted);
the base input, tray placement, and mount stiffness are invented assumptions,
all swept. Overall checker status for this study: YELLOW (documented honest
negatives — the overnight survey is not converged and is labelled as such on
its figure).

## Findings scorecard (1 = utter failure … 5 = smashing success)
| # | finding | score |
|---|---|---|
| 1 | From-scratch ShockSat FEM reproduces NASA NX (2.5pp) & real test modes | **5** |
| 2 | NUTS twin converges on full modal set (R-hat 1.022, ESS 232) | **4** |
| 3 | StatFEM discrepancy is real on a real structure (σ_f 4.6% ≫ noise) | **4** |
| 4 | Bayesian-7004C force limiting quantified (over-test ×1.1–2.2) | **4** |
| 5 | Load QOI is mount-dominated (mount ~100% of variance, primary <1%) | **5** |
| 6 | Response-limit proxy works in-band (ρ≈1.0, α≈mass) | **4** |
| 7 | One modal survey recovers the full 6-DOF mount | **2** (honest negative) |
| 8 | Honesty harness catches our OWN overclaim (SE "yes" → FIM "2/6") | **5** |

Median 4/5.

## Per-slide talk track
1. **Title** — set the frame: a validated twin of real hardware; the coupled
   payload question is a methods demo. Name the three audiences.
2. **Why** — the weakest-link/conservatism mass problem; StatFEM "onto the
   track"; one line each for Girolami / Bilionis / Yunis.
3. **Arc** — the whole program left-to-right; the discrepancy lever is the
   spine; the right-hand negative tells us what to measure.
4. **Validated twin** — from-scratch FEM = NASA NX to 2.5pp; calibrated on 33
   REAL modes; full posterior converges (R-hat 1.022); identification partial.
5. **Discrepancy is real** (Girolami) — σ_f 4.6% ≫ noise = model-form error
   caps identifiability; the KOH/Brynjarsdottir warning, on real data.
6. **Coupled question** — net-CG interface load; method × coupling; mount =
   uncertain joint; forward UQ only; hypothetical.
7. **Force limiting** (Yunis + novelty) — uncoupled over-test ×1.1–2.2 with a
   validated source; the Bayesian-7004C thread. (play force_limiting_sweep.gif)
8. **Method = assumption** — SRS unbiased at true damping; Q swings it ×0.7–2.3;
   Miles 3σ under-predicts ~25% by construction.
9. **Mount dominance** (the headline) — mount ~100% of QOI variance, primary
   <1%; calibrate the JOINT, not the primary.
10. **Honest negative** — simulated the obvious fix (a modal survey); only 2/6
    mount axes separate; R-hat 5–10 is under-identification, not a bug; refined
    lever = shapes/FRF/force, not more frequencies. (play multimodality.gif)
11. **Harness** (Bilionis) — green/yellow/red, quantity contracts, the
    identifiability gate; it caught our own overclaim.
12. **Scorecard** — 1–5; median 4; the two 5s and the one 2.
13. **Next + asks** — symmetry-breaking survey; one question for each of you.
14. **Backup** — replay, validation gates, invented assumptions, artifacts.
