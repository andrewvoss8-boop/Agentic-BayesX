# Findings — ShockSat FRF-Domain Damping Updating (2026-07-10)

Headline is never stronger than `out/verdicts.json` / `checker_report.json`.

**Pre-registered claim FALSIFIED on all four gates (S1 improvement, S2 intelligence, S3 honesty, S4
attribution).** An FRF-domain agentic loop with a genuine DAMPING action space + FDAC alignment did not
improve the inherited ShockSat FEM's held-out per-sensor FRF prediction.

1. **Damping — the new lever — does not help; it hurts.** The fitted damping baseline A0d scores dev
   P1′ = 0.193, **below** A0's 0.197. S4 damping share = **−0.10** ("improvement is shape/θ; damping unproven").
2. **Mechanism (new, clean):** the 2 Hz distilled FRFs cannot resolve ShockSat's light damping (ζ≈0.3%,
   half-power bands ≤ ~1 frequency line; Gate D2: 27% per-mode ζ error). Fitting damping fits the peak-sampling
   aliasing → ζ pushed to 1.5–2.5% (MAP) / the 5% gate ceiling (NUTS), and does not generalize.
3. **FDAC alignment does not rescue the correlation** on real data (gain ≈ −0.01; θ_MAP already aligns
   frequencies). The tool works on a synthetic 5% shift (Gate F: 0.69→0.997) — there is just nothing to fix.
4. **Shape stays null** (best +0.037 < +0.05 bar, ≪ 2×fold-SE 0.26) and **loses to random search** (S2).
5. **Observability (Gate O):** 93% of measured shape content is reachable (not gross-unobservable), but the
   sensor set aliases some mode pairs (self-MAC 0.997, Fisher rank 36/40).
6. **Cross-validation:** A0_enr raw P3 = 0.2152 reproduces the completed true-remodel run's exact-basis A0.

**Recommendation for the human replace/keep/buy-data decision:** keep the inherited twin; to use damping for
FRF-amplitude correlation, BUY finer frequency resolution (re-distill the NASA raw time histories) — not more
modeling. The completed true-remodel run stands unchanged; this run answers the successor question (damping)
and closes it with a resolution-limited mechanism.
