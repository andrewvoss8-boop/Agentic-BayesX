# Findings — Resolution-Consistent FRF Scoring (20260713)

Statuses copied from `checker_report.json` (OVERALL RED; RED = Gate W only; YELLOW = S1 falsified, S3 not
confirmed; all integrity/pipeline gates GREEN). Nothing below is stronger than the checker output.

1. **S1 (pre-registered claim) FALSIFIED.** Window-matched + physical-ζ (B2) beats the incumbent naive+1%
   (B0) by +0.0401 dev P1′ (0.1969 → 0.2371) with vault confirmation of direction (0.420 → 0.473), but the
   margin is below the pre-registered 2×fold-SE bar (0.0527); the +Y fold is −0.010. Not a win under the
   noise-floor rule.
2. **S2: the gain is the WINDOW, not the damping.** Window-alone +0.0332; damping-alone −0.0125; interaction
   +0.0193. Once the window is matched, survey ζ vs ERA bands vs flat 1% differ by less than fold noise.
3. **S3 (mechanism tier) NOT confirmed — Gate W FAILED.** The score half passed (B2−B1 = +0.053 ≥ 0.02); the
   raw-data verification did not reach its pre-registered thresholds.
4. **Data discovery: the Test07 raw series has a DEAD force channel in all 4 hits** (~1 lb noise vs
   1000–1900 g impacts) → the card's direct H1 recompute is physically impossible; retro-explains the
   2026-06-09 "Test07 low coherence" finding. Test07 is response-only data.
5. **Window mechanism evidence (short of certification):** distiller source FOUND (exp window end=0.05,
   N=122880 @ 250 kHz; upstream code documents its own added damping ζ_w(f)=1/(2πfτ)); Gate K synthetic
   operator error ≤2%; isolated-peak apparent-ζ fits agree within ±15% on both stored cache and raw spectra;
   no peak is narrower than predicted; Test01↔Test07 shape corr 0.834. Dense peaks defeat the ±3-bin width
   fit at 2 Hz spacing → the quantitative gate misses.
6. **Gate R GREEN:** B0 reproduces the damping run's frozen A0_enr dev P1′ to 1.6e-7 (bit-level pipeline
   continuity); B1<B0 reproduces the addendum deficit.
7. **Corrected assumption (D6):** the card's Hann-kernel picture of the window was wrong — the actual
   exponential window adds ζ_w at EVERY peak width (a ζ=5% peak drops ~16%, not "unchanged").
8. **No sampler used** (declared NO-SAMPLER study; deterministic arms; reused θ_MAP).
9. **Practical close-out:** damping is not recoverable from the 2 Hz caches (window-dominated); the incumbent
   1% convention works because it approximates ζ_w(f). The single cheap decisive follow-up = one raw
   modal-hammer series with live force (Test01/02 class) → direct Gate W + longer-frame re-distillation.
